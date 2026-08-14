"""Score completed runs. Spends nothing, so it is safe to re-run constantly.

    uv run python ocr-benchmark/score.py

Writes per-run metrics.json and predictions.csv under runs/<variantId>/ (gitignored,
they carry values), and aggregate-only artifacts under reports/ (tracked).

Scoring rules that matter:
  * Critical identifiers are exact-match only. Never fuzzy. 00030085091 against
    00030085090 is a failure whatever the string similarity says.
  * Two normalizers are reported. `platform` is byte-identical to the platform's
    eval_extraction._norm, so the headline number is comparable to production's own
    golden-set figure. `strict` keeps case and punctuation, because stripping commas
    is right for money and wrong for a cadastral number.
  * A prediction that arrived as a JSON number is an error, not a value: "0021"
    decoding to 21 would silently pass a fuzzy check and be legally wrong.
  * Fields with no expectation are `no_label`, never scored as an expected empty.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import config
import normalize

CRITICAL = json.loads((config.SCHEMAS / "critical-fields.json").read_text(encoding="utf-8"))
CRITICAL_KEYS: set[str] = set(CRITICAL["critical"])

OUTCOMES = ("correct", "wrong", "missing", "no_label", "unlabelled_extra")


# ── loading ──────────────────────────────────────────────────────────────────
def load_expected() -> dict[str, dict[str, Any]]:
    if not config.EXPECTED_FIELDS.is_file():
        return {}
    return json.loads(config.EXPECTED_FIELDS.read_text(encoding="utf-8"))


def load_runs() -> dict[str, dict[str, Any]]:
    """Every run directory that has a manifest, keyed by variantId."""
    runs: dict[str, dict[str, Any]] = {}
    for manifest_path in sorted(config.RUNS.glob("*/config.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        results_path = manifest_path.parent / "results.jsonl"
        docs = []
        if results_path.is_file():
            for line in results_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    docs.append(json.loads(line))
        runs[manifest["variantId"]] = {"manifest": manifest, "docs": docs,
                                       "dir": manifest_path.parent}
    return runs


def load_labels(kind: str) -> dict[str, Any]:
    """Opportunistically load human annotations if they exist."""
    out: dict[str, Any] = {}
    folder = config.LABELS / kind
    if not folder.is_dir():
        return out
    for path in sorted(folder.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        out[payload.get("docId", path.stem)] = payload
    return out


# ── field scoring ────────────────────────────────────────────────────────────
def classify_outcome(expected: str | None, predicted: Any, ambiguous: bool = False
                     ) -> tuple[str, dict[str, bool]]:
    """One field's outcome plus per-normalizer match flags."""
    if isinstance(predicted, (int, float)) and not isinstance(predicted, bool):
        # Never silently accept a number: leading zeros are already gone.
        return "wrong", {"platform": False, "strict": False, "type_error": True}
    value = normalize.null_collapse(predicted)
    if ambiguous:
        return "ambiguous", {"platform": False, "strict": False}
    if expected is None:
        return ("unlabelled_extra" if value is not None else "no_label"), {
            "platform": False, "strict": False
        }
    if value is None:
        return "missing", {"platform": False, "strict": False}
    flags = {
        "platform": normalize.platform_norm(value) == normalize.platform_norm(expected),
        "strict": normalize.strict_norm(value) == normalize.strict_norm(expected),
    }
    return ("correct" if flags["platform"] else "wrong"), flags


def score_run(variant_id: str, run: dict[str, Any], expected_all: dict[str, dict[str, Any]],
              field_labels: dict[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    outcomes: Counter[str] = Counter()
    critical_outcomes: Counter[str] = Counter()
    strict_correct = 0
    strict_total = 0
    invented = 0
    predicted_count = 0
    provenance: Counter[str] = Counter()
    kind_hits = 0
    kind_total = 0
    page_texts: dict[tuple[str, int], str] = {}

    for doc in run["docs"]:
        doc_id = doc["doc_id"]
        expected_doc = expected_all.get(doc_id, {})
        expected_fields: dict[str, str] = expected_doc.get("fields", {}) or {}
        labelled = field_labels.get(doc_id, {})
        ambiguous_keys = {
            f["key"] for f in labelled.get("fields", []) if f.get("ambiguous")
        }

        if expected_doc.get("kind"):
            kind_total += 1
            if doc.get("routing", {}).get("kind") == expected_doc["kind"]:
                kind_hits += 1

        for page in doc.get("pages", []):
            page_texts[(doc_id, page["page_no"])] = page.get("text", "")

        predicted = {f["key"]: f for f in doc.get("fields", [])}
        keys = set(expected_fields) | set(predicted)
        for key in sorted(keys):
            field = predicted.get(key)
            value = field.get("value") if field else None
            outcome, flags = classify_outcome(
                expected_fields.get(key), value, ambiguous=key in ambiguous_keys
            )
            outcomes[outcome] += 1
            if key in CRITICAL_KEYS:
                critical_outcomes[outcome] += 1
            if key in expected_fields and value is not None and outcome != "ambiguous":
                strict_total += 1
                strict_correct += int(flags.get("strict", False))
            if value is not None:
                predicted_count += 1
                if field and field.get("verbatim_in_page_text") is False:
                    invented += 1
                provenance[field.get("provenance_level", "none") if field else "none"] += 1
            rows.append(
                {
                    "variant_id": variant_id,
                    "doc_id": doc_id,
                    "key": key,
                    "critical": key in CRITICAL_KEYS,
                    "expected": expected_fields.get(key, ""),
                    "predicted": "" if value is None else value,
                    "outcome": outcome,
                    "match_platform": flags.get("platform", False),
                    "match_strict": flags.get("strict", False),
                    "type_error": flags.get("type_error", False),
                    "page": (field or {}).get("page_no", ""),
                    "provenance": (field or {}).get("provenance_level", "none"),
                    "verbatim_in_page": (field or {}).get("verbatim_in_page_text", ""),
                    "box_contains_value": (field or {}).get("box_contains_value", ""),
                    "validator_ok": (field or {}).get("validator_ok", ""),
                    "engine": (field or {}).get("engine", ""),
                }
            )

    # A run that never got a usable response is FAILED, not 0% accurate. Reporting
    # a provider outage as a score would make a broken run look like a bad model,
    # and reports/metrics.json is committed.
    provider_errors = sum(
        len(d.get("provider_metadata", {}).get("errors", []) or []) for d in run["docs"]
    )
    status = run["manifest"].get("status")
    failed = predicted_count == 0 and provider_errors > 0
    if failed:
        status = "failed"

    scored = outcomes["correct"] + outcomes["wrong"] + outcomes["missing"]
    crit_scored = (
        critical_outcomes["correct"] + critical_outcomes["wrong"] + critical_outcomes["missing"]
    )
    low, high = normalize.wilson_interval(critical_outcomes["correct"], crit_scored)

    metrics = {
        "variantId": variant_id,
        "runId": run["manifest"].get("runId"),
        "status": status,
        "reason": _first_error(run) if failed else run["manifest"].get("reason", ""),
        "providerErrors": provider_errors,
        "docs": len(run["docs"]),
        "pages": sum(len(d.get("pages", [])) for d in run["docs"]),
        "fieldAccuracy": {
            "scored": 0 if failed else scored,
            "correct": 0 if failed else outcomes["correct"],
            "exactMatchPlatform": None if failed else _ratio(outcomes["correct"], scored),
            "exactMatchStrict": None if failed else _ratio(strict_correct, strict_total),
        },
        "criticalFieldAccuracy": {
            "scored": 0 if failed else crit_scored,
            "correct": 0 if failed else critical_outcomes["correct"],
            "exactMatch": None if failed else _ratio(critical_outcomes["correct"], crit_scored),
            "wilson95": None if failed else [round(low, 4), round(high, 4)],
        },
        "outcomes": {k: outcomes[k] for k in OUTCOMES if outcomes[k]},
        "ambiguousExcluded": outcomes["ambiguous"],
        "omissionRate": _ratio(outcomes["missing"], scored),
        "inventedValueRate": _ratio(invented, predicted_count),
        "coverage": _ratio(predicted_count, scored) if scored else None,
        "provenance": dict(provenance),
        "kindAccuracy": _ratio(kind_hits, kind_total),
        "cost": {
            "calls": sum(d.get("provider_metadata", {}).get("calls", 0) for d in run["docs"]),
            "estimatedUsd": round(
                sum(d.get("provider_metadata", {}).get("estimated_usd", 0.0)
                    for d in run["docs"]), 6
            ),
            "latencyMsTotal": round(
                sum(d.get("provider_metadata", {}).get("latency_ms", {}).get("total", 0.0)
                    for d in run["docs"]), 1
            ),
        },
        "textMetrics": text_metrics(page_texts, load_labels("ocr-region")),
    }
    return {"metrics": metrics, "rows": rows, "page_texts": page_texts}


def _ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 4) if denominator else None


def _first_error(run: dict[str, Any]) -> str:
    """The first provider error, so a failed run explains itself in the report."""
    for doc in run["docs"]:
        errors = doc.get("provider_metadata", {}).get("errors") or []
        if errors:
            return str(errors[0])[:160]
    return "no provider response"


# ── transcript metrics ───────────────────────────────────────────────────────
def text_metrics(page_texts: dict[tuple[str, int], str],
                 region_labels: dict[str, Any]) -> dict[str, Any]:
    """CER/WER against human transcripts, by language and text type.

    Returns status "no-ground-truth" until labels exist. Reporting an honest
    absence beats reporting a number computed against another model's output.
    """
    if not region_labels:
        return {"status": "no-ground-truth",
                "note": "add labels under ocr-benchmark/labels/ocr-region/"}

    buckets: dict[str, list[tuple[float, float]]] = defaultdict(list)
    pages_scored = 0
    for doc_id, payload in region_labels.items():
        page_no = payload.get("page")
        hypothesis = page_texts.get((doc_id, page_no))
        if hypothesis is None:
            continue
        full = payload.get("fullPageTranscript")
        if full:
            pages_scored += 1
            value_cer = normalize.cer(full, hypothesis)
            value_wer = normalize.wer(full, hypothesis)
            if value_cer is not None and value_wer is not None:
                buckets["page"].append((value_cer, value_wer))
        for region in payload.get("regions", []):
            reference = region.get("verbatimText") or ""
            if not reference or region.get("ambiguous"):
                continue
            # Region-level CER needs the hypothesis text for that region; without
            # a box-aware reader the best available proxy is presence in the page.
            value_cer = 0.0 if normalize.value_in_text(reference, hypothesis) else 1.0
            label = f"{region.get('language', 'unknown')}/{region.get('textType', 'unknown')}"
            buckets[label].append((value_cer, value_cer))

    return {
        "status": "ok",
        "pagesScored": pages_scored,
        "byBucket": {
            label: {
                "n": len(pairs),
                "cer": round(sum(p[0] for p in pairs) / len(pairs), 4),
                "wer": round(sum(p[1] for p in pairs) / len(pairs), 4),
            }
            for label, pairs in sorted(buckets.items())
        },
    }


# ── cross-run agreement ──────────────────────────────────────────────────────
def agreement_matrix(scored: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Pairwise field agreement between runs.

    This is the one strong signal available with no ground truth at all, and the
    fastest way to pick which pages are worth annotating first.
    """
    values: dict[str, dict[tuple[str, str], str | None]] = {}
    for variant_id, payload in scored.items():
        values[variant_id] = {
            (row["doc_id"], row["key"]): (row["predicted"] or None)
            for row in payload["rows"]
        }

    variants = sorted(values)
    matrix: dict[str, dict[str, Any]] = {}
    for left in variants:
        matrix[left] = {}
        for right in variants:
            shared = set(values[left]) & set(values[right])
            comparable = [
                k for k in shared
                if values[left][k] is not None and values[right][k] is not None
            ]
            if not comparable:
                matrix[left][right] = None
                continue
            same = sum(
                normalize.platform_norm(values[left][k]) == normalize.platform_norm(values[right][k])
                for k in comparable
            )
            matrix[left][right] = {"n": len(comparable), "agreement": round(same / len(comparable), 4)}
    return matrix


def agreement_vs_truth(scored: dict[str, dict[str, Any]]) -> dict[str, int]:
    """Does agreement predict correctness? Answerable on the labelled fields only.

    If agree-and-wrong is large, agreement is not a usable proxy for accuracy and
    the ensemble's confidence signal cannot be trusted.
    """
    per_field: dict[tuple[str, str], list[tuple[str, bool, bool]]] = defaultdict(list)
    for variant_id, payload in scored.items():
        for row in payload["rows"]:
            if row["outcome"] not in ("correct", "wrong"):
                continue
            per_field[(row["doc_id"], row["key"])].append(
                (variant_id, bool(row["predicted"]), bool(row["match_platform"]))
            )

    tally = Counter()
    for entries in per_field.values():
        if len(entries) < 2:
            continue
        correct = [e[2] for e in entries]
        all_same = len({e[1] for e in entries}) == 1
        if all(correct):
            tally["all_correct"] += 1
        elif not any(correct):
            tally["all_wrong"] += 1
        elif all_same:
            tally["agree_but_split"] += 1
        else:
            tally["disagree_some_correct"] += 1
    return dict(tally)


# ── writing ──────────────────────────────────────────────────────────────────
def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    """utf-8 with newline="" - required for Sinhala on Windows."""
    if not rows:
        return
    fields = list(rows[0])
    normalize.assert_no_raw_values(path, fields)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    runs = load_runs()
    if not runs:
        print(f"no runs found under {config.RUNS}; run runner.py first")
        return 1
    expected_all = load_expected()
    field_labels = load_labels("fields")

    scored: dict[str, dict[str, Any]] = {}
    for variant_id, run in sorted(runs.items()):
        # A run may ship its own ground truth (the synthetic fixture does), which
        # takes precedence over the bundle's expectations for its documents.
        expected = dict(expected_all)
        local = run["dir"] / "expected-fields.json"
        if local.is_file():
            expected.update(json.loads(local.read_text(encoding="utf-8")))
        result = score_run(variant_id, run, expected, field_labels)
        scored[variant_id] = result
        (run["dir"] / "metrics.json").write_text(
            json.dumps(result["metrics"], indent=2), encoding="utf-8"
        )
        write_csv(run["dir"] / "predictions.csv", result["rows"])
        write_csv(
            run["dir"] / "mismatches.csv",
            [r for r in result["rows"] if r["outcome"] in ("wrong", "missing")],
        )
        metrics = result["metrics"]
        crit = metrics["criticalFieldAccuracy"]
        print(
            f"{variant_id:22s} status={metrics['status']:9s} "
            f"critical={_fmt(crit['exactMatch'])} ({crit['correct']}/{crit['scored']})  "
            f"all={_fmt(metrics['fieldAccuracy']['exactMatchPlatform'])}  "
            f"invented={_fmt(metrics['inventedValueRate'])}  "
            f"${metrics['cost']['estimatedUsd']:.4f}"
        )

    # reports/ is tracked, so it gets aggregates only - never a field value.
    summary = {
        "datasetId": config.DATASET_ID,
        "runs": {v: s["metrics"] for v, s in scored.items()},
        "agreementMatrix": agreement_matrix(scored),
        "agreementVsTruth": agreement_vs_truth(scored),
    }
    (config.REPORTS / "metrics.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(f"\nwrote {config.REPORTS / 'metrics.json'}")
    return 0


def _fmt(value: float | None) -> str:
    return "  n/a" if value is None else f"{value:5.1%}"


if __name__ == "__main__":
    raise SystemExit(main())
