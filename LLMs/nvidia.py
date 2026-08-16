"""NVIDIA NIM client manager and model-discovery CLI.

NVIDIA's hosted NIM API is OpenAI-compatible. This module keeps API keys out of
source code, supports numbered keys such as ``NVIDIA_API_KEY_1``, and rotates
logical requests across the configured clients.

Examples::

    uv run python LLMs/nvidia.py models
    uv run python LLMs/nvidia.py models --contains llama
    uv run python LLMs/nvidia.py models --json
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import http.client
import json
import os
import re
import threading
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any, Protocol

from dotenv import load_dotenv
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    OpenAI,
    RateLimitError,
)

DEFAULT_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_CATALOG_URL = "https://build.nvidia.com"
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODELS_FILE = Path(__file__).resolve().with_name("nvidia-models.json")
_NUMBERED_KEY = re.compile(r"^NVIDIA_API_KEY_(\d+)$")
_TEXT_RECORD = re.compile(r"(?:^|\n)([0-9a-f]+):T([0-9a-f]+),$", re.I)
_USER_AGENT = "Draftly-NVIDIA-Model-Catalog/1.0"


class _ModelsAPI(Protocol):
    def list(self) -> Any: ...


class _Client(Protocol):
    models: _ModelsAPI
    chat: Any


def load_api_keys(environ: Mapping[str, str] | None = None) -> list[str]:
    """Return unique NVIDIA keys without ever logging their values.

    Numbered keys are preferred and ordered numerically. ``NVIDIA_API_KEYS``
    (comma-separated) and the legacy ``NVIDIA_API_KEY`` are also supported.
    """

    source = os.environ if environ is None else environ
    numbered: list[tuple[int, str]] = []
    for name, value in source.items():
        match = _NUMBERED_KEY.match(name)
        if match and value.strip():
            numbered.append((int(match.group(1)), value.strip()))

    candidates = [value for _, value in sorted(numbered)]
    if not candidates:
        candidates = [
            value.strip()
            for value in source.get("NVIDIA_API_KEYS", "").split(",")
            if value.strip()
        ]
    if not candidates:
        legacy = source.get("NVIDIA_API_KEY", "").strip()
        if legacy:
            candidates.append(legacy)

    # dict preserves order while preventing one key from being used twice.
    return list(dict.fromkeys(candidates))


def _retryable(exc: Exception) -> bool:
    if isinstance(
        exc,
        (
            AuthenticationError,
            RateLimitError,
            APIConnectionError,
            APITimeoutError,
        ),
    ):
        return True
    return isinstance(exc, APIStatusError) and exc.status_code >= 500


class NvidiaManager:
    """Round-robin NVIDIA NIM clients with per-request key failover."""

    def __init__(
        self,
        api_keys: Sequence[str],
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 60.0,
        client_factory: Callable[..., _Client] = OpenAI,
    ) -> None:
        keys = list(dict.fromkeys(key.strip() for key in api_keys if key.strip()))
        if not keys:
            raise ValueError(
                "No NVIDIA API key found. Set NVIDIA_API_KEY_1 (and optionally "
                "NVIDIA_API_KEY_2, ...), or NVIDIA_API_KEY."
            )
        self._clients = [
            client_factory(base_url=base_url.rstrip("/"), api_key=key, timeout=timeout)
            for key in keys
        ]
        self._next_client = 0
        self._lock = threading.Lock()

    @classmethod
    def from_env(
        cls,
        *,
        env_file: str | Path | None = REPO_ROOT / ".env",
        environ: Mapping[str, str] | None = None,
        **kwargs: Any,
    ) -> "NvidiaManager":
        if env_file is not None:
            load_dotenv(Path(env_file), override=False)
        source = os.environ if environ is None else environ
        base_url = source.get("NVIDIA_BASE_URL", DEFAULT_BASE_URL)
        return cls(load_api_keys(source), base_url=base_url, **kwargs)

    @property
    def key_count(self) -> int:
        """Number of distinct configured keys (values are never exposed)."""

        return len(self._clients)

    def _client_order(self) -> list[_Client]:
        with self._lock:
            start = self._next_client
            self._next_client = (self._next_client + 1) % len(self._clients)
        return self._clients[start:] + self._clients[:start]

    def _call(self, operation: Callable[[_Client], Any]) -> Any:
        last_error: Exception | None = None
        for client in self._client_order():
            try:
                return operation(client)
            except Exception as exc:  # The SDK has several transport subclasses.
                if not _retryable(exc):
                    raise
                last_error = exc
        assert last_error is not None
        raise last_error

    def list_model_records(self) -> list[dict[str, Any]]:
        """Return the complete records advertised by NVIDIA's models endpoint."""

        page = self._call(lambda client: client.models.list())
        records: dict[str, dict[str, Any]] = {}
        for item in page.data:
            if hasattr(item, "model_dump"):
                record = item.model_dump(mode="json")
            else:
                record = {
                    key: getattr(item, key)
                    for key in ("id", "object", "created", "owned_by")
                    if hasattr(item, key)
                }
            model_id = str(record["id"])
            records[model_id] = record
        return sorted(records.values(), key=lambda record: record["id"].casefold())

    def list_models(self) -> list[str]:
        """Return model IDs currently advertised by NVIDIA, sorted by provider."""

        return [record["id"] for record in self.list_model_records()]

    def create_chat_completion(self, **kwargs: Any) -> Any:
        """Create a chat completion using round-robin selection and failover."""

        return self._call(lambda client: client.chat.completions.create(**kwargs))


def _flight_chunks(page_html: str) -> list[str]:
    """Decode the text chunks embedded in a Next.js React Flight response."""

    chunks: list[str] = []
    prefix = "self.__next_f.push("
    for body in re.findall(r"<script>(.*?)</script>", page_html, flags=re.S):
        body = body.strip()
        if not body.startswith(prefix) or not body.endswith(")"):
            continue
        try:
            record = json.loads(body[len(prefix) : -1])
        except json.JSONDecodeError:
            continue
        if (
            isinstance(record, list)
            and len(record) > 1
            and record[0] == 1
            and isinstance(record[1], str)
        ):
            chunks.append(record[1])
    return chunks


def _text_records(chunks: Sequence[str]) -> dict[str, str]:
    """Resolve React Flight ``$id`` references that point to text records."""

    records: dict[str, str] = {}
    for index, chunk in enumerate(chunks):
        match = _TEXT_RECORD.search(chunk)
        if not match:
            continue
        expected_bytes = int(match.group(2), 16)
        payload = bytearray()
        for following in chunks[index + 1 :]:
            payload.extend(following.encode("utf-8"))
            if len(payload) >= expected_bytes:
                break
        try:
            records[match.group(1).lower()] = bytes(payload[:expected_bytes]).decode(
                "utf-8"
            )
        except UnicodeDecodeError:
            continue
    return records


def _json_fields(chunks: Sequence[str], field: str) -> list[Any]:
    marker = f'"{field}":'
    decoder = json.JSONDecoder()
    values: list[Any] = []
    for chunk in chunks:
        start = chunk.find(marker)
        while start >= 0:
            try:
                value, _ = decoder.raw_decode(chunk[start + len(marker) :])
            except json.JSONDecodeError:
                pass
            else:
                values.append(value)
            start = chunk.find(marker, start + len(marker))
    return values


def _json_field(chunks: Sequence[str], field: str) -> Any | None:
    values = _json_fields(chunks, field)
    return values[0] if values else None


def _artifact_state(chunks: Sequence[str]) -> dict[str, Any]:
    marker = '{"initialState":{"artifact":'
    decoder = json.JSONDecoder()
    for chunk in chunks:
        marker_at = chunk.find(marker)
        if marker_at < 0:
            continue
        payload_at = chunk.rfind("[", 0, marker_at)
        if payload_at < 0:
            continue
        try:
            payload, _ = decoder.raw_decode(chunk[payload_at:])
            state = payload[3]["initialState"]
        except (json.JSONDecodeError, IndexError, KeyError, TypeError):
            continue
        if isinstance(state, dict) and isinstance(state.get("artifact"), dict):
            return state

    # Some established catalogue pages use the older component layout without
    # an ``initialState`` wrapper. Their artifact and OpenAPI data are still
    # embedded as ordinary React Flight fields.
    artifact = _json_field(chunks, "artifact")
    if isinstance(artifact, dict) and artifact.get("artifactType"):
        return {
            "artifact": artifact,
            "openApiSpec": _json_field(chunks, "openAPISpec")
            or _json_field(chunks, "openApiSpec")
            or {},
        }
    raise ValueError("NVIDIA catalogue metadata was not present in the page")


def parse_model_card_page(page_html: str, *, url: str) -> dict[str, Any]:
    """Extract structured metadata and full Markdown from an NVIDIA model card."""

    chunks = _flight_chunks(page_html)
    state = _artifact_state(chunks)
    artifact = state["artifact"]
    text_records = _text_records(chunks)

    def resolve_text(value: Any) -> Any:
        if isinstance(value, str) and re.fullmatch(r"\$[0-9a-f]+", value, re.I):
            return text_records.get(value[1:].lower())
        return value

    description = resolve_text(artifact.get("description"))

    attributes = {
        str(item["key"]): item.get("value")
        for item in artifact.get("attributes", [])
        if isinstance(item, dict) and "key" in item
    }
    labels = artifact.get("labels")
    if not isinstance(labels, list):
        labels = next(
            (
                value
                for value in _json_fields(chunks, "labels")
                if isinstance(value, list)
                and all(isinstance(item, str) for item in value)
            ),
            [],
        )
    openapi_spec = state.get("openApiSpec")
    openapi_info = (
        openapi_spec.get("info", {}) if isinstance(openapi_spec, dict) else {}
    )
    return {
        "status": "available",
        "url": url,
        "artifact_type": artifact.get("artifactType"),
        "publisher": artifact.get("publisher"),
        "artifact_name": artifact.get("name"),
        "display_name": artifact.get("displayName"),
        "short_description": artifact.get("shortDescription"),
        "description_markdown": description,
        "labels": labels,
        "attributes": attributes,
        "specifications": _json_field(chunks, "specifications"),
        "capabilities": _json_field(chunks, "modelCapability"),
        "model_card_subcards": {
            name: resolve_text(artifact.get(name))
            for name in ("bias", "explainability", "privacy", "safetyAndSecurity")
            if artifact.get(name) is not None
        },
        "created_at": artifact.get("createdDate"),
        "updated_at": artifact.get("updatedDate"),
        "logo_url": artifact.get("logo"),
        "public": artifact.get("isPublic"),
        "guest_download_allowed": artifact.get("canGuestDownload"),
        "api_reference": openapi_info.get("description"),
        "license": openapi_info.get("license"),
        "terms_of_service": openapi_info.get("termsOfService"),
    }


def _card_url_candidates(model_id: str) -> list[str]:
    publisher, name = model_id.split("/", maxsplit=1)
    slugs = list(dict.fromkeys((name.replace(".", "_"), name)))
    return [
        f"{DEFAULT_CATALOG_URL}/{publisher}/{slug}/modelcard" for slug in slugs
    ]


def fetch_model_card(model_id: str, *, timeout: float = 30.0) -> dict[str, Any]:
    """Fetch one official NVIDIA catalogue model card."""

    if "/" not in model_id:
        return {
            "status": "unavailable",
            "url": None,
            "error": "Model ID has no publisher prefix",
        }

    errors: list[str] = []
    for url in _card_url_candidates(model_id):
        request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        for attempt in range(2):
            try:
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    page_html = response.read().decode("utf-8")
                card = parse_model_card_page(page_html, url=url)
                publisher = str(card.get("publisher") or "")
                if (
                    publisher
                    and publisher.casefold()
                    != model_id.split("/", 1)[0].casefold()
                ):
                    raise ValueError(
                        f"Catalogue page belongs to publisher {publisher!r}"
                    )
                return card
            except (
                http.client.IncompleteRead,
                OSError,
                UnicodeError,
                ValueError,
                urllib.error.HTTPError,
            ) as exc:
                if attempt == 1:
                    errors.append(f"{url}: {type(exc).__name__}: {exc}")

    return {
        "status": "unavailable",
        "url": _card_url_candidates(model_id)[0],
        "error": " | ".join(errors),
    }


def build_model_catalog(
    records: Sequence[dict[str, Any]],
    *,
    workers: int = 8,
    fetch_card: Callable[[str], dict[str, Any]] = fetch_model_card,
) -> dict[str, Any]:
    """Enrich NVIDIA API model records with their official catalogue cards."""

    cards: dict[str, dict[str, Any]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = {
            pool.submit(fetch_card, str(record["id"])): str(record["id"])
            for record in records
        }
        for completed, future in enumerate(
            concurrent.futures.as_completed(futures), start=1
        ):
            model_id = futures[future]
            try:
                cards[model_id] = future.result()
            except Exception as exc:  # Keep one broken card from losing the catalogue.
                cards[model_id] = {
                    "status": "unavailable",
                    "url": None,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            print(f"[{completed}/{len(futures)}] {model_id}: {cards[model_id]['status']}")

    models = []
    for record in records:
        model_id = str(record["id"])
        provider, _, name = model_id.partition("/")
        models.append(
            {
                **record,
                "provider": provider,
                "name": name,
                "model_card": cards[model_id],
            }
        )

    enriched_count = sum(
        model["model_card"]["status"] == "available" for model in models
    )
    return {
        "schema_version": 1,
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "sources": {
            "models_api": f"{DEFAULT_BASE_URL}/models",
            "model_cards": DEFAULT_CATALOG_URL,
        },
        "model_count": len(models),
        "enriched_count": enriched_count,
        "unenriched_count": len(models) - enriched_count,
        "models": models,
    }


def save_model_catalog(catalog: Mapping[str, Any], output: Path) -> None:
    """Atomically replace the saved catalogue with formatted UTF-8 JSON."""

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(output)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Use NVIDIA's hosted NIM API.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    models = subparsers.add_parser("models", help="list currently available models")
    models.add_argument(
        "--contains",
        default="",
        help="only show model IDs containing this text (case-insensitive)",
    )
    models.add_argument("--json", action="store_true", help="emit a JSON array")
    models.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_MODELS_FILE,
        help=f"catalogue output path (default: {DEFAULT_MODELS_FILE})",
    )
    models.add_argument(
        "--workers",
        type=int,
        default=8,
        help="parallel model-card requests (default: 8)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    manager = NvidiaManager.from_env()

    if args.command == "models":
        records = manager.list_model_records()
        catalog = build_model_catalog(records, workers=args.workers)
        save_model_catalog(catalog, args.output)
        models = [record["id"] for record in records]
        if args.contains:
            needle = args.contains.casefold()
            models = [model for model in models if needle in model.casefold()]
        if args.json:
            print(json.dumps(models, indent=2))
        else:
            print(f"NVIDIA models ({len(models)}), using {manager.key_count} key(s):")
            print("\n".join(models))
        print(
            f"Saved {catalog['model_count']} models "
            f"({catalog['enriched_count']} model cards) to {args.output.resolve()}"
        )
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
