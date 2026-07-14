"""Transcribe Draftly discussion recordings with Google Cloud Speech-to-Text V2."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from dotenv import load_dotenv
from google.api_core.client_options import ClientOptions
from google.cloud import storage
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech


DISCUSSIONS_DIR = Path(__file__).resolve().parent
REPO_ROOT = DISCUSSIONS_DIR.parent
RECORDINGS_DIR = DISCUSSIONS_DIR / "recordings"
TRANSCRIPTS_DIR = DISCUSSIONS_DIR / "transcripts"
VOCABULARY_FILE = DISCUSSIONS_DIR / "vocabulary.txt"

SUPPORTED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm"}
GCS_PREFIX = "draftly-discussions"


@dataclass(frozen=True)
class Settings:
    project_id: str
    bucket_name: str
    region: str
    model: str
    language: str
    timeout_seconds: int


@dataclass(frozen=True)
class TranscriptPaths:
    text: Path
    markdown: Path
    json: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transcribe recordings from discussions/recordings with Google Chirp 2."
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Transcribe one recording instead of every supported file in discussions/recordings.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reprocess files even when transcript outputs already exist.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned work without uploading audio or calling Google.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=3600,
        help="Maximum seconds to wait for each Google batch operation. Default: 3600.",
    )
    return parser.parse_args()


def load_settings(timeout_seconds: int, *, dry_run: bool) -> Settings:
    load_dotenv(REPO_ROOT / ".env")

    settings = Settings(
        project_id=os.getenv("GOOGLE_CLOUD_PROJECT", "").strip(),
        bucket_name=os.getenv("GOOGLE_STT_BUCKET", "").strip(),
        region=os.getenv("GOOGLE_STT_REGION", "asia-southeast1").strip(),
        model=os.getenv("GOOGLE_STT_MODEL", "chirp_2").strip(),
        language=os.getenv("GOOGLE_STT_LANGUAGE", "si-LK").strip(),
        timeout_seconds=timeout_seconds,
    )

    if dry_run:
        return settings

    missing = []
    if not settings.project_id:
        missing.append("GOOGLE_CLOUD_PROJECT")
    if not settings.bucket_name:
        missing.append("GOOGLE_STT_BUCKET")
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip():
        missing.append("GOOGLE_APPLICATION_CREDENTIALS")
    if missing:
        joined = ", ".join(missing)
        raise SystemExit(f"Missing required .env setting(s): {joined}")

    return settings


def find_recordings(single_file: Path | None) -> list[Path]:
    if single_file is not None:
        path = single_file if single_file.is_absolute() else REPO_ROOT / single_file
        if not path.exists():
            raise SystemExit(f"Recording not found: {path}")
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise SystemExit(f"Unsupported audio extension: {path.suffix}")
        return [path]

    if not RECORDINGS_DIR.exists():
        return []

    return sorted(
        path
        for path in RECORDINGS_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def transcript_paths(audio_path: Path) -> TranscriptPaths:
    safe_stem = sanitize_name(audio_path.stem)
    return TranscriptPaths(
        text=TRANSCRIPTS_DIR / f"{safe_stem}.transcript.txt",
        markdown=TRANSCRIPTS_DIR / f"{safe_stem}.transcript.md",
        json=TRANSCRIPTS_DIR / f"{safe_stem}.transcript.json",
    )


def sanitize_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    return cleaned.strip("-._") or "recording"


def read_vocabulary() -> list[str]:
    if not VOCABULARY_FILE.exists():
        return []

    terms: list[str] = []
    for line in VOCABULARY_FILE.read_text(encoding="utf-8").splitlines():
        term = line.strip()
        if term and not term.startswith("#"):
            terms.append(term)
    return terms


def build_recognition_config(settings: Settings, vocabulary_terms: list[str]) -> cloud_speech.RecognitionConfig:
    features = cloud_speech.RecognitionFeatures(
        enable_automatic_punctuation=True,
        enable_word_confidence=True,
        enable_word_time_offsets=True,
    )

    config = cloud_speech.RecognitionConfig(
        auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
        language_codes=[settings.language],
        model=settings.model,
        features=features,
    )

    if vocabulary_terms:
        phrase_set = cloud_speech.PhraseSet(
            phrases=[
                cloud_speech.PhraseSet.Phrase(value=term, boost=15.0)
                for term in vocabulary_terms
            ],
            boost=10.0,
        )
        config.adaptation = cloud_speech.SpeechAdaptation(
            phrase_sets=[
                cloud_speech.SpeechAdaptation.AdaptationPhraseSet(
                    inline_phrase_set=phrase_set
                )
            ]
        )

    return config


def upload_audio(storage_client: storage.Client, bucket_name: str, audio_path: Path) -> str:
    bucket = storage_client.bucket(bucket_name)
    object_name = f"{GCS_PREFIX}/input/{utc_run_id()}-{sanitize_name(audio_path.name)}"
    blob = bucket.blob(object_name)
    blob.upload_from_filename(str(audio_path))
    return f"gs://{bucket_name}/{object_name}"


def utc_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def transcribe_recording(
    speech_client: SpeechClient,
    storage_client: storage.Client,
    settings: Settings,
    audio_path: Path,
    outputs: TranscriptPaths,
    vocabulary_terms: list[str],
) -> None:
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

    gcs_audio_uri = upload_audio(storage_client, settings.bucket_name, audio_path)
    output_prefix = f"gs://{settings.bucket_name}/{GCS_PREFIX}/output/{sanitize_name(audio_path.stem)}-{utc_run_id()}/"

    recognizer = (
        f"projects/{settings.project_id}/locations/{settings.region}/recognizers/_"
    )
    config = build_recognition_config(settings, vocabulary_terms)
    request = cloud_speech.BatchRecognizeRequest(
        recognizer=recognizer,
        config=config,
        files=[cloud_speech.BatchRecognizeFileMetadata(uri=gcs_audio_uri)],
        recognition_output_config=cloud_speech.RecognitionOutputConfig(
            gcs_output_config=cloud_speech.GcsOutputConfig(uri=output_prefix)
        ),
    )

    print(f"Uploading and transcribing: {audio_path.name}")
    print(f"  audio: {gcs_audio_uri}")
    print(f"  output: {output_prefix}")
    operation = speech_client.batch_recognize(request=request)
    response = operation.result(timeout=settings.timeout_seconds)

    result_payload, result_uri = get_result_payload(
        response=response,
        storage_client=storage_client,
        gcs_audio_uri=gcs_audio_uri,
    )
    transcript_data = parse_transcript_result(result_payload)

    write_outputs(
        audio_path=audio_path,
        outputs=outputs,
        settings=settings,
        gcs_audio_uri=gcs_audio_uri,
        gcs_result_uri=result_uri,
        vocabulary_terms=vocabulary_terms,
        transcript_data=transcript_data,
        raw_result=result_payload,
    )

    print(f"  wrote: {outputs.text}")
    print(f"  wrote: {outputs.markdown}")
    print(f"  wrote: {outputs.json}")


def get_result_payload(
    *,
    response: cloud_speech.BatchRecognizeResponse,
    storage_client: storage.Client,
    gcs_audio_uri: str,
) -> tuple[dict, str]:
    response_dict = cloud_speech.BatchRecognizeResponse.to_dict(response)
    results = response_dict.get("results", {})

    if gcs_audio_uri in results:
        payload = result_entry_payload(results[gcs_audio_uri], storage_client)
        if payload is not None:
            return payload

    for result in results.values():
        payload = result_entry_payload(result, storage_client)
        if payload is not None:
            return payload

    raise RuntimeError(
        f"Google batch response did not include transcript data or a result URI: {response_dict}"
    )


def result_entry_payload(
    result: dict,
    storage_client: storage.Client,
) -> tuple[dict, str] | None:
    error = result.get("error")
    if error:
        raise RuntimeError(f"Google batch recognition failed for one file: {error}")

    transcript = result.get("transcript")
    if transcript:
        return transcript, "inline:transcript"

    inline_result = result.get("inlineResult", {})
    inline_transcript = inline_result.get("transcript")
    if inline_transcript:
        return inline_transcript, "inline:inlineResult.transcript"

    cloud_storage_result = result.get("cloudStorageResult", {})
    uri = cloud_storage_result.get("uri") or result.get("uri")
    if uri:
        return download_json_from_gcs(storage_client, uri), uri

    return None


def download_json_from_gcs(storage_client: storage.Client, uri: str) -> dict:
    bucket_name, blob_name = split_gcs_uri(uri)
    blob = storage_client.bucket(bucket_name).blob(blob_name)
    last_error: Exception | None = None
    for attempt in range(1, 13):
        try:
            content = blob.download_as_text(encoding="utf-8")
            return json.loads(content)
        except Exception as exc:
            last_error = exc
            if attempt == 12:
                break
            time.sleep(5)
    raise RuntimeError(f"Could not download Google STT result JSON at {uri}") from last_error


def split_gcs_uri(uri: str) -> tuple[str, str]:
    if not uri.startswith("gs://"):
        raise ValueError(f"Expected a gs:// URI, got: {uri}")
    without_scheme = uri.removeprefix("gs://")
    bucket_name, _, blob_name = without_scheme.partition("/")
    if not bucket_name or not blob_name:
        raise ValueError(f"Invalid GCS URI: {uri}")
    return bucket_name, blob_name


def parse_transcript_result(raw_result: dict) -> dict:
    transcript_parts: list[str] = []
    alternatives_payload: list[dict] = []
    confidences: list[float] = []

    for result in raw_result.get("results", []):
        alternatives = result.get("alternatives", [])
        if not alternatives:
            continue
        best = alternatives[0]
        transcript = best.get("transcript", "").strip()
        if transcript:
            transcript_parts.append(transcript)
        if "confidence" in best:
            confidences.append(float(best["confidence"]))
        alternatives_payload.append(best)

    text = "\n\n".join(transcript_parts).strip()
    average_confidence = (
        sum(confidences) / len(confidences) if confidences else None
    )

    return {
        "text": text,
        "average_confidence": average_confidence,
        "segments": alternatives_payload,
    }


def write_outputs(
    *,
    audio_path: Path,
    outputs: TranscriptPaths,
    settings: Settings,
    gcs_audio_uri: str,
    gcs_result_uri: str,
    vocabulary_terms: list[str],
    transcript_data: dict,
    raw_result: dict,
) -> None:
    generated_at = datetime.now(timezone.utc).isoformat()

    outputs.text.write_text(transcript_data["text"] + "\n", encoding="utf-8")

    markdown = build_markdown(
        audio_path=audio_path,
        settings=settings,
        generated_at=generated_at,
        gcs_audio_uri=gcs_audio_uri,
        gcs_result_uri=gcs_result_uri,
        vocabulary_count=len(vocabulary_terms),
        transcript_data=transcript_data,
    )
    outputs.markdown.write_text(markdown, encoding="utf-8")

    payload = {
        "metadata": {
            "generated_at": generated_at,
            "source_audio": str(audio_path),
            "gcs_audio_uri": gcs_audio_uri,
            "gcs_result_uri": gcs_result_uri,
            "project_id": settings.project_id,
            "region": settings.region,
            "model": settings.model,
            "language": settings.language,
            "vocabulary_terms": vocabulary_terms,
        },
        "transcript": transcript_data,
        "google_result": raw_result,
    }
    outputs.json.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build_markdown(
    *,
    audio_path: Path,
    settings: Settings,
    generated_at: str,
    gcs_audio_uri: str,
    gcs_result_uri: str,
    vocabulary_count: int,
    transcript_data: dict,
) -> str:
    confidence = transcript_data.get("average_confidence")
    confidence_text = f"{confidence:.3f}" if confidence is not None else "not provided"
    transcript = transcript_data["text"] or "_No transcript text returned._"

    return (
        f"# {audio_path.stem} Transcript\n\n"
        "## Metadata\n\n"
        f"- Source audio: `{audio_path}`\n"
        f"- Generated at: `{generated_at}`\n"
        f"- Language: `{settings.language}`\n"
        f"- Model: `{settings.model}`\n"
        f"- Region: `{settings.region}`\n"
        f"- Vocabulary terms: `{vocabulary_count}`\n"
        f"- Average confidence: `{confidence_text}`\n"
        f"- GCS audio: `{gcs_audio_uri}`\n"
        f"- GCS result: `{gcs_result_uri}`\n\n"
        "## Transcript\n\n"
        f"{transcript}\n"
    )


def planned_items(recordings: Iterable[Path], *, force: bool) -> list[tuple[Path, TranscriptPaths, bool]]:
    items: list[tuple[Path, TranscriptPaths, bool]] = []
    for recording in recordings:
        outputs = transcript_paths(recording)
        exists = outputs.text.exists() or outputs.markdown.exists() or outputs.json.exists()
        should_process = force or not exists
        items.append((recording, outputs, should_process))
    return items


def main() -> int:
    args = parse_args()
    settings = load_settings(args.timeout, dry_run=args.dry_run)
    recordings = find_recordings(args.file)
    vocabulary_terms = read_vocabulary()
    items = planned_items(recordings, force=args.force)

    if not items:
        print(f"No supported recordings found in {RECORDINGS_DIR}.")
        print(f"Supported extensions: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")
        return 0

    print(f"Recordings folder: {RECORDINGS_DIR}")
    print(f"Transcripts folder: {TRANSCRIPTS_DIR}")
    print(f"Language/model/region: {settings.language} / {settings.model} / {settings.region}")
    print(f"Vocabulary terms: {len(vocabulary_terms)}")

    if args.dry_run:
        for recording, outputs, should_process in items:
            status = "process" if should_process else "skip existing"
            print(f"[{status}] {recording}")
            print(f"  text: {outputs.text}")
            print(f"  markdown: {outputs.markdown}")
            print(f"  json: {outputs.json}")
        return 0

    client_options = ClientOptions(
        api_endpoint=f"{settings.region}-speech.googleapis.com"
    )
    speech_client = SpeechClient(client_options=client_options)
    storage_client = storage.Client(project=settings.project_id)

    skipped = 0
    processed = 0
    for recording, outputs, should_process in items:
        if not should_process:
            skipped += 1
            print(f"Skipping existing transcript: {recording.name}")
            continue
        transcribe_recording(
            speech_client=speech_client,
            storage_client=storage_client,
            settings=settings,
            audio_path=recording,
            outputs=outputs,
            vocabulary_terms=vocabulary_terms,
        )
        processed += 1

    print(f"Done. Processed: {processed}. Skipped: {skipped}.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        raise SystemExit(130)
