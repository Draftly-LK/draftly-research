"""Execute benchmark runs. This is the module that spends money.

    uv run python ocr-benchmark/runner.py stub              # offline, free
    uv run python ocr-benchmark/runner.py A --dry-run       # plan and cost only
    uv run python ocr-benchmark/runner.py A --limit 1       # one document
    uv run python ocr-benchmark/runner.py A B D             # the smoke comparison
    uv run python ocr-benchmark/runner.py A --ablation dpi  # expand an axis

Resumable: completed (variant_id, doc_id) pairs are skipped on re-run, following
the raw-responses.jsonl checkpoint pattern in
scripts/case-law-information-extraction/ablation.py.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

import yaml

import config
import engines
import normalize
import render
from contract import (
    AdapterOutput,
    Block,
    FieldValue,
    PageResult,
    ProviderMetadata,
    Routing,
    bbox_apply,
    bbox_contains,
    dataset_fingerprint,
    iou,
    sha256_file,
    sha256_text,
)
from engines import EngineUnavailable, PageReading

REGISTRY = json.loads((config.SCHEMAS / "registry-fields.json").read_text(encoding="utf-8"))
KIND_FIELDS: dict[str, list[dict[str, Any]]] = REGISTRY["kinds"]
CRITICAL = json.loads((config.SCHEMAS / "critical-fields.json").read_text(encoding="utf-8"))
CRITICAL_KEYS: set[str] = set(CRITICAL["critical"])

FIELD_LABELS: dict[str, str] = {
    f["key"]: f["label"] for fields in KIND_FIELDS.values() for f in fields
}
FIELD_VALIDATORS: dict[str, str | None] = {
    f["key"]: f.get("validator") for fields in KIND_FIELDS.values() for f in fields
}


# ── config expansion ─────────────────────────────────────────────────────────
def load_spec() -> dict[str, Any]:
    return yaml.safe_load(config.RUNS_YAML.read_text(encoding="utf-8"))


def resolve(spec: dict[str, Any], run_id: str) -> dict[str, Any]:
    if run_id not in spec["runs"]:
        raise SystemExit(f"unknown run {run_id!r}; known: {sorted(spec['runs'])}")
    return {**spec["defaults"], **spec["runs"][run_id], "runId": run_id}


def expand(spec: dict[str, Any], run_id: str, ablation: str | None) -> list[tuple[str, dict]]:
    """Yield (variant_id, resolved_config). An ablation is an override, not a pipeline."""
    base = resolve(spec, run_id)
    if not ablation:
        return [(run_id, base)]
    axis_spec = spec.get("ablations", {}).get(ablation)
    if not axis_spec:
        raise SystemExit(f"unknown ablation {ablation!r}; known: {sorted(spec.get('ablations', {}))}")
    if run_id not in axis_spec.get("apply", []):
        raise SystemExit(f"ablation {ablation!r} does not apply to run {run_id!r}")
    axis = axis_spec["axis"]
    out = []
    for value in axis_spec["values"]:
        cfg = {**base, axis: value}
        if axis_spec.get("docs"):
            cfg["docs"] = axis_spec["docs"]
        if axis_spec.get("maxPagesPerDoc"):
            cfg["maxPagesPerDoc"] = axis_spec["maxPagesPerDoc"]
        out.append((f"{run_id}@{axis}={value}", cfg))
    return out


# ── documents ────────────────────────────────────────────────────────────────
def expected_fields() -> dict[str, dict[str, Any]]:
    """Expectations across every matter, keyed by "<matter>/<filename>".

    Only some matters are labelled. An unlabelled matter is not an error: those
    documents still feed cross-run agreement, transcript metrics and cost, they
    just do not contribute a field score.
    """
    out: dict[str, dict[str, Any]] = {}
    for case in config.case_dirs():
        path = config.expected_fields_path(case)
        if not path.is_file():
            continue
        for name, payload in json.loads(path.read_text(encoding="utf-8")).items():
            out[f"{case.name}/{name}"] = payload
    return out


def doc_id_for(path: Path) -> str:
    """Matter-qualified id, because two matters both contain 'source-001-...'."""
    return f"{path.parent.name}/{path.name}"


def input_docs(selector: str | None = None, case_filter: str | None = None) -> list[Path]:
    docs: list[Path] = []
    for case in config.case_dirs():
        if case_filter and case_filter.lower() not in case.name.lower():
            continue
        docs.extend(config.case_documents(case))

    if selector == "subset":
        # One document per kind per matter keeps the ablation grids cheap.
        labelled = expected_fields()
        seen: set[tuple[str, str]] = set()
        chosen: list[Path] = []
        for doc in docs:
            kind = labelled.get(doc_id_for(doc), {}).get("kind", "other")
            marker = (doc.parent.name, kind)
            if marker in seen:
                continue
            seen.add(marker)
            chosen.append(doc)
        return chosen
    return docs


def field_keys_for(kind: str) -> list[str]:
    return [f["key"] for f in KIND_FIELDS.get(kind, [])]


# ── shared post-processing ───────────────────────────────────────────────────
def annotate(fields: Iterable[FieldValue], page_text: str, blocks: Sequence[Block]) -> None:
    """Fill in the grounding signals that need no ground truth."""
    for value_field in fields:
        value = value_field.value
        if value is None:
            continue
        value_field.verbatim_in_page_text = normalize.value_in_text(value, page_text)
        validator = FIELD_VALIDATORS.get(value_field.key)
        if validator and validator in normalize.VALIDATORS:
            value_field.validator_ok = normalize.VALIDATORS[validator](value)
        if value_field.bbox is not None:
            # Does the claimed box actually contain text matching the value?
            hit = next(
                (
                    b
                    for b in blocks
                    if b.page_no == value_field.page_no
                    and iou(b.bbox, value_field.bbox) > 0.1
                    and normalize.value_in_text(value, b.text)
                ),
                None,
            )
            if hit is not None:
                value_field.box_contains_value = True
            else:
                covering = next(
                    (
                        b
                        for b in blocks
                        if b.page_no == value_field.page_no
                        and bbox_contains(value_field.bbox, b.bbox, tol=0.02)
                        and normalize.value_in_text(value, b.text)
                    ),
                    None,
                )
                value_field.box_contains_value = covering is not None


def merge_fields(existing: list[FieldValue], incoming: Iterable[FieldValue]) -> list[FieldValue]:
    """First non-null reading of a key wins; later pages only fill gaps.

    Documents repeat their identifiers across pages, and a later page's partial
    view should not overwrite a clean earlier read.
    """
    by_key = {f.key: f for f in existing}
    for candidate in incoming:
        current = by_key.get(candidate.key)
        if current is None or (current.value is None and candidate.value is not None):
            by_key[candidate.key] = candidate
    return list(by_key.values())


def accumulate(meta: ProviderMetadata, reading: PageReading) -> None:
    meta.calls += reading.calls
    meta.http_attempts += reading.http_attempts
    meta.prompt_tokens += reading.prompt_tokens
    meta.completion_tokens += reading.completion_tokens
    meta.errors.extend(reading.errors)


# ── detectors (box-producing engines) ────────────────────────────────────────
def detect_blocks(page: render.RenderedPage, detector: str) -> tuple[list[Block], PageReading]:
    """Region proposals from a box-producing engine.

    `surya` is the configured default but is GPL-3.0 and unavailable here;
    `rapidocr` is Apache-2.0 and already installed, and its detection boxes are
    what runs E/F actually need since Gemini does the reading. See README.
    """
    if detector == "surya":
        ok, why = engines.surya_available()
        if not ok:
            raise EngineUnavailable(why)
        return _surya_blocks(page)
    if detector == "rapidocr":
        ok, why = engines.rapidocr_available()
        if not ok:
            raise EngineUnavailable(why)
        return _rapidocr_blocks(page)
    raise EngineUnavailable(f"unknown detector {detector!r}")


def _surya_blocks(page: render.RenderedPage) -> tuple[list[Block], PageReading]:
    from surya.detection import DetectionPredictor  # type: ignore

    predictor = DetectionPredictor()
    result = predictor([page.image])[0]
    width, height = page.size
    from contract import bbox_from_pixels

    blocks = []
    for index, box in enumerate(getattr(result, "bboxes", [])):
        bbox = bbox_from_pixels(box.bbox, width, height)
        blocks.append(
            Block(
                block_id=f"p{page.page_no}-b{index:03d}",
                page_no=page.page_no,
                text="",
                bbox=bbox,
                bbox_original=bbox_apply(bbox, page.transform_to_original),
                confidence=getattr(box, "confidence", None),
                source="surya-det",
            )
        )
    return blocks, PageReading()


def _rapidocr_blocks(page: render.RenderedPage) -> tuple[list[Block], PageReading]:
    import numpy as np
    from rapidocr import RapidOCR

    from contract import bbox_from_polygon

    engine = RapidOCR()
    result = engine(np.asarray(page.image.convert("RGB")))
    width, height = page.size
    blocks: list[Block] = []
    boxes = getattr(result, "boxes", None) or []
    texts = getattr(result, "txts", None) or []
    scores = getattr(result, "scores", None) or []
    lines: list[str] = []
    for index, polygon in enumerate(boxes):
        bbox = bbox_from_polygon(polygon, width, height)
        text = str(texts[index]) if index < len(texts) else ""
        lines.append(text)
        blocks.append(
            Block(
                block_id=f"p{page.page_no}-b{index:03d}",
                page_no=page.page_no,
                text=text,
                bbox=bbox,
                bbox_original=bbox_apply(bbox, page.transform_to_original),
                confidence=float(scores[index]) if index < len(scores) else None,
                source="rapidocr-det",
                script=normalize.script_of(text),
            )
        )
    reading = PageReading(text="\n".join(lines), blocks=blocks)
    return blocks, reading


# ── pipelines ────────────────────────────────────────────────────────────────
def _render(doc: Path, cfg: dict) -> list[render.RenderedPage]:
    """Render honouring the per-document page cap that keeps ablation grids cheap."""
    cap = cfg.get("maxPagesPerDoc")
    return render.render_doc(
        doc,
        dpi=cfg["dpi"],
        variant=cfg["variant"],
        page_limit=int(cap) if cap else None,
    )


def pipeline_stub(doc: Path, cfg: dict, out: AdapterOutput) -> None:
    """Read the synthetic fixture, which carries its own perfect ground truth.

    The fixture's expectations are written into the run directory so the scorer
    treats this run exactly like a real one. With noise=0 the result must be
    100% accuracy and 0.00 CER; anything else is a harness bug rather than a
    model result, which is what makes this the keystone of the offline path.
    """
    pages = render.synthetic_doc(pages=2)
    noise = float(cfg.get("stubNoise", 0.0))
    truth_fields: dict[str, str] = {}
    for index, (image, truth) in enumerate(pages, start=1):
        page = render.RenderedPage(index, image, cfg["dpi"], "original", render.IDENTITY, False)
        reading = engines.stub_read_page(page, truth, noise=noise, seed=index)
        for row in truth:
            truth_fields.setdefault(str(row["key"]), str(row["verbatimValue"]))
        out.pages.append(_page_result(page, reading, "stub"))
        out.blocks.extend(reading.blocks)
        out.fields = merge_fields(out.fields, reading.fields)
    out.routing = Routing(kind="synthetic", kind_confidence=1.0, kind_source="fixture")
    path = run_dir(out.variant_id) / "expected-fields.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({out.doc_id: {"kind": "synthetic", "fields": truth_fields}}, indent=2),
        encoding="utf-8",
    )


def _page_result(page: render.RenderedPage, reading: PageReading, engine: str) -> PageResult:
    width, height = page.size
    return PageResult(
        page_no=page.page_no,
        dpi=page.dpi,
        render_variant=page.variant,
        width_px=width,
        height_px=height,
        text=reading.text,
        engine=engine,
        engine_confidence=reading.confidence,
        blank=page.blank,
        transform_to_original=page.transform_to_original,
    )


def _classify(pages: Sequence[render.RenderedPage], cfg: dict, out: AdapterOutput) -> str:
    """Classify from page 1, exactly as production does."""
    kind, confidence, reading = engines.gemini_classify_page(
        pages[0], model=cfg["classifyModel"], temperature=cfg["temperature"]
    )
    accumulate(out.provider_metadata, reading)
    engines.record_usage(cfg["classifyModel"], reading, f"{out.variant_id}:{out.doc_id}:classify")
    out.routing = Routing(
        kind=kind,
        kind_confidence=confidence,
        kind_source="gemini-classify",
        page_kinds={"1": kind},
    )
    return kind


def pipeline_gemini_page(doc: Path, cfg: dict, out: AdapterOutput) -> None:
    pages = _render(doc, cfg)
    kind = _classify(pages, cfg, out)
    keys = field_keys_for(kind)
    for page in pages:
        if page.blank:
            out.pages.append(_page_result(page, PageReading(), "skipped-blank"))
            continue
        reading = engines.gemini_read_page(
            page, keys, model=cfg["extractModel"], temperature=cfg["temperature"]
        )
        engines.record_usage(
            cfg["extractModel"], reading, f"{out.variant_id}:{out.doc_id}:p{page.page_no}"
        )
        accumulate(out.provider_metadata, reading)
        annotate(reading.fields, reading.text, reading.blocks)
        out.pages.append(_page_result(page, reading, "gemini"))
        out.blocks.extend(reading.blocks)
        out.fields = merge_fields(out.fields, reading.fields)


def pipeline_gemini_page_plus_crops(doc: Path, cfg: dict, out: AdapterOutput) -> None:
    pipeline_gemini_page(doc, cfg, out)
    pages = {p.page_no: p for p in _render(doc, cfg)}
    target = CRITICAL_KEYS if cfg.get("cropKeys") == "critical" else set(FIELD_LABELS)
    for value_field in out.fields:
        if value_field.key not in target or value_field.bbox is None:
            continue
        page = pages.get(value_field.page_no or 0)
        if page is None:
            continue
        reread, reading = engines.gemini_read_crop(
            page,
            value_field.key,
            FIELD_LABELS.get(value_field.key, value_field.key),
            value_field.bbox,
            model=cfg["extractModel"],
            temperature=cfg["temperature"],
            pad=float(cfg.get("cropPad", 0.02)),
        )
        engines.record_usage(
            cfg["extractModel"], reading, f"{out.variant_id}:{out.doc_id}:crop:{value_field.key}"
        )
        accumulate(out.provider_metadata, reading)
        value_field.agreement_sources = ["gemini-page", "gemini-crop"]
        if reread is not None:
            # The crop is the closer look, so it wins; the page value is kept in
            # agreement_sources so the notebook can measure how often they differ.
            if reread != value_field.value:
                out.provider_metadata.errors.append(
                    f"crop-disagreement:{value_field.key}"
                )
            value_field.value = reread
            value_field.engine = "gemini-crop"
            value_field.provenance_level = "region"


def pipeline_boxes_page(doc: Path, cfg: dict, out: AdapterOutput) -> None:
    """Box engine reads the page end to end. No Gemini, so no field extraction."""
    pages = _render(doc, cfg)
    detector = cfg.get("detector", "rapidocr")
    for page in pages:
        if page.blank:
            out.pages.append(_page_result(page, PageReading(), "skipped-blank"))
            continue
        blocks, reading = detect_blocks(page, detector)
        out.pages.append(_page_result(page, reading, detector))
        out.blocks.extend(blocks)
    out.routing = Routing(kind="unknown", kind_source=detector, outcome="manual_review",
                          reasons=["box-engine-does-not-classify"])


def pipeline_boxes_plus_gemini_crops(doc: Path, cfg: dict, out: AdapterOutput) -> None:
    """Detector proposes regions; Gemini reads each region. Local grounding."""
    pages = _render(doc, cfg)
    detector = cfg.get("detector", "rapidocr")
    kind = _classify(pages, cfg, out)
    keys = field_keys_for(kind)
    max_regions = int(cfg.get("maxRegionsPerPage", 25))
    for page in pages:
        if page.blank:
            out.pages.append(_page_result(page, PageReading(), "skipped-blank"))
            continue
        blocks, det_reading = detect_blocks(page, detector)
        out.blocks.extend(blocks)
        # Read the whole page once with the detector's boxes as context, then let
        # Gemini assign values. Reading every region separately would cost one
        # call per line, which the spend cap will not allow on a 16-page document.
        reading = engines.gemini_read_page(
            page, keys, model=cfg["extractModel"], temperature=cfg["temperature"]
        )
        engines.record_usage(
            cfg["extractModel"], reading, f"{out.variant_id}:{out.doc_id}:p{page.page_no}"
        )
        accumulate(out.provider_metadata, reading)
        # Snap each field's box to the detector region it overlaps most: that is
        # the "local spatial grounding" this run exists to test.
        for value_field in reading.fields:
            if value_field.bbox is None:
                continue
            best = max(blocks, key=lambda b: iou(b.bbox, value_field.bbox), default=None)
            if best is not None and iou(best.bbox, value_field.bbox) > 0.1:
                value_field.bbox = best.bbox
                value_field.bbox_original = best.bbox_original
                value_field.block_ids = [best.block_id]
                value_field.agreement_sources = ["gemini", detector]
        combined = det_reading.text or reading.text
        annotate(reading.fields, combined, blocks or reading.blocks)
        out.pages.append(_page_result(page, reading, f"gemini+{detector}"))
        out.fields = merge_fields(out.fields, reading.fields)


def pipeline_reconcile(doc: Path, cfg: dict, out: AdapterOutput) -> None:
    """Gemini and the box engine both read; disagreements are flagged and re-read."""
    pages = _render(doc, cfg)
    detector = cfg.get("detector", "rapidocr")
    kind = _classify(pages, cfg, out)
    keys = field_keys_for(kind)
    for page in pages:
        if page.blank:
            out.pages.append(_page_result(page, PageReading(), "skipped-blank"))
            continue
        blocks, det_reading = detect_blocks(page, detector)
        reading = engines.gemini_read_page(
            page, keys, model=cfg["extractModel"], temperature=cfg["temperature"]
        )
        engines.record_usage(
            cfg["extractModel"], reading, f"{out.variant_id}:{out.doc_id}:p{page.page_no}"
        )
        accumulate(out.provider_metadata, reading)
        out.blocks.extend(blocks)
        for value_field in reading.fields:
            if value_field.value is None:
                continue
            agrees = normalize.value_in_text(value_field.value, det_reading.text or "")
            value_field.agreement_sources = ["gemini"] + ([detector] if agrees else [])
            if not agrees and value_field.bbox is not None:
                reread, crop_reading = engines.gemini_read_crop(
                    page,
                    value_field.key,
                    FIELD_LABELS.get(value_field.key, value_field.key),
                    value_field.bbox,
                    model=cfg["extractModel"],
                    temperature=cfg["temperature"],
                )
                engines.record_usage(
                    cfg["extractModel"],
                    crop_reading,
                    f"{out.variant_id}:{out.doc_id}:adjudicate:{value_field.key}",
                )
                accumulate(out.provider_metadata, crop_reading)
                if reread is not None:
                    value_field.value = reread
                    value_field.engine = "gemini-adjudicated"
        annotate(reading.fields, reading.text + "\n" + (det_reading.text or ""),
                 blocks or reading.blocks)
        out.pages.append(_page_result(page, reading, f"reconcile:{detector}"))
        out.fields = merge_fields(out.fields, reading.fields)


PIPELINES = {
    "stub": pipeline_stub,
    "gemini_page": pipeline_gemini_page,
    "gemini_page_plus_crops": pipeline_gemini_page_plus_crops,
    "boxes_page": pipeline_boxes_page,
    "boxes_plus_gemini_crops": pipeline_boxes_plus_gemini_crops,
    "reconcile": pipeline_reconcile,
}


# ── run artifacts ────────────────────────────────────────────────────────────
def run_dir(variant_id: str) -> Path:
    safe = variant_id.replace("@", "_at_").replace("=", "-")
    return config.RUNS / safe


def done_docs(variant_id: str) -> set[str]:
    path = run_dir(variant_id) / "results.jsonl"
    if not path.is_file():
        return set()
    done = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            done.add(json.loads(line)["doc_id"])
        except (json.JSONDecodeError, KeyError):
            continue
    return done


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_manifest(variant_id: str, cfg: dict, docs: Sequence[Path], status: str,
                   reason: str, started: str, counts: dict) -> None:
    prompts = {
        "page": sha256_text(engines._PAGE_PROMPT)[:12],
        "classify": sha256_text(engines._CLASSIFY_PROMPT)[:12],
        "crop": sha256_text(engines._CROP_PROMPT)[:12],
    }
    manifest = {
        "variantId": variant_id,
        "runId": cfg["runId"],
        "pipeline": cfg["pipeline"],
        "schemaVersion": config.SCHEMA_VERSION,
        "datasetId": config.DATASET_ID,
        "datasetVersion": dataset_fingerprint(docs) if docs else "",
        # Fingerprint of every matter's expectations, so a label edit is visible
        # in the manifest without the values themselves appearing anywhere.
        "expectedFieldsVersion": sha256_text(
            json.dumps(expected_fields(), sort_keys=True)
        )[:16],
        "matters": sorted({d.parent.name for d in docs}),
        "models": {"classify": cfg.get("classifyModel"), "extract": cfg.get("extractModel")},
        "detector": cfg.get("detector"),
        "temperature": cfg.get("temperature"),
        "renderDpi": cfg.get("dpi"),
        "renderVariant": cfg.get("variant"),
        "cropKeys": cfg.get("cropKeys"),
        "promptId": cfg.get("promptId"),
        "promptVersion": prompts,
        "preprocessingVersion": sha256_file(Path(render.__file__))[:12],
        "codeCommit": config.code_commit(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "startedAt": started,
        "finishedAt": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "reason": reason,
        "counts": counts,
        "capabilities": engines.capabilities(),
    }
    path = run_dir(variant_id) / "config.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def execute(variant_id: str, cfg: dict, limit: int | None, dry_run: bool,
            resume: bool = True) -> None:
    started = datetime.now(timezone.utc).isoformat()
    pipeline = PIPELINES[cfg["pipeline"]]
    docs = (
        []
        if cfg.get("docs") == "synthetic"
        else input_docs(cfg.get("docs"), cfg.get("caseFilter"))
    )
    if limit is not None:
        docs = docs[:limit]

    # Capability gate: report, do not crash.
    for requirement in cfg.get("requires", []):
        ok, why = {"surya": engines.surya_available, "gemini": engines.gemini_available}[
            requirement
        ]()
        if not ok:
            print(f"[{variant_id}] SKIPPED: {why}")
            write_manifest(variant_id, cfg, docs, "skipped", why, started,
                           {"docs": 0, "pages": 0})
            return

    if dry_run:
        pages = _count_pages(docs, cfg.get("maxPagesPerDoc"))
        print(f"[{variant_id}] plan: {len(docs) or 'synthetic'} docs, {pages} pages, "
              f"pipeline={cfg['pipeline']}, dpi={cfg['dpi']}, variant={cfg['variant']}")
        return

    targets: list[Path | None] = list(docs) if docs else [None]
    already = done_docs(variant_id) if resume else set()
    results = run_dir(variant_id) / "results.jsonl"
    raw = run_dir(variant_id) / "raw-responses.jsonl"
    if not resume:
        # These files are append-only checkpoints. Without truncating, a re-run
        # writes a second record for every document and the scorer counts each
        # field twice.
        for stale in (results, raw):
            stale.unlink(missing_ok=True)
    total_pages = 0
    processed = 0

    for doc in targets:
        doc_id = doc_id_for(doc) if doc else "synthetic"
        if doc_id in already:
            print(f"[{variant_id}] {doc_id}: cached")
            continue
        out = AdapterOutput(
            schema_version=config.SCHEMA_VERSION,
            run_id=cfg["runId"],
            variant_id=variant_id,
            doc_id=doc_id,
            doc_sha256=sha256_file(doc)[:16] if doc else "",
            provider_metadata=ProviderMetadata(
                engines=[cfg["pipeline"]],
                models={"classify": cfg.get("classifyModel", ""),
                        "extract": cfg.get("extractModel", "")},
                temperature=float(cfg.get("temperature", 0.0)),
            ),
        )
        began = time.time()
        try:
            pipeline(doc, cfg, out)  # type: ignore[arg-type]
        except EngineUnavailable as exc:
            print(f"[{variant_id}] SKIPPED: {exc}")
            write_manifest(variant_id, cfg, docs, "skipped", str(exc), started,
                           {"docs": processed, "pages": total_pages})
            return
        out.provider_metadata.latency_ms["total"] = round((time.time() - began) * 1000, 1)
        out.provider_metadata.estimated_usd = engines.estimate_usd(
            cfg.get("extractModel", ""),
            out.provider_metadata.prompt_tokens,
            out.provider_metadata.completion_tokens,
        )
        # Raw provider payload first, before any normalization, per the
        # reproducibility requirement.
        append_jsonl(raw, {"doc_id": doc_id, "variant_id": variant_id,
                           "pages": [p.text for p in out.pages]})
        append_jsonl(results, json.loads(out.model_dump_json()))
        total_pages += len(out.pages)
        processed += 1
        print(f"[{variant_id}] {doc_id}: {len(out.pages)} pages, "
              f"{len(out.fields)} fields, {out.provider_metadata.calls} calls, "
              f"${out.provider_metadata.estimated_usd:.4f}")

    write_manifest(variant_id, cfg, docs, "completed", "", started,
                   {"docs": processed, "pages": total_pages, **engines.usage_summary()})
    print(f"[{variant_id}] done: {processed} docs, {total_pages} pages")


def _count_pages(docs: Sequence[Path], cap: int | None = None) -> int:
    import pypdfium2 as pdfium

    total = 0
    for doc in docs:
        if doc.suffix.lower() != ".pdf":
            total += 1  # a photographed page is one page
            continue
        pdf = pdfium.PdfDocument(doc)
        try:
            total += min(len(pdf), int(cap)) if cap else len(pdf)
        finally:
            pdf.close()
    return total


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runs", nargs="+", help="run ids from runs.yaml, e.g. A B D stub")
    parser.add_argument("--ablation", help="expand an ablation axis, e.g. dpi")
    parser.add_argument("--limit", type=int, help="first N documents only")
    parser.add_argument("--case", help="only matters whose folder name contains this")
    parser.add_argument("--dry-run", action="store_true", help="plan and cost, no calls")
    parser.add_argument("--no-resume", action="store_true", help="re-read cached documents")
    parser.add_argument("--stub-noise", type=float, default=0.0,
                        help="corruption rate for the stub engine")
    args = parser.parse_args(argv)

    config.assert_inputs_private()
    print("capabilities:", engines.capabilities())
    for run_id in args.runs:
        spec = load_spec()
        for variant_id, cfg in expand(spec, run_id, args.ablation):
            if args.stub_noise:
                cfg["stubNoise"] = args.stub_noise
            if args.case:
                cfg["caseFilter"] = args.case
            execute(variant_id, cfg, args.limit, args.dry_run, resume=not args.no_resume)
    return 0


if __name__ == "__main__":
    sys.exit(main())
