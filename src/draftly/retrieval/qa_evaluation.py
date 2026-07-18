from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .question_analysis import ExamQuestionBlock, analyze_question, parse_question_file


JsonObject = dict[str, Any]
RetrievalCallable = Callable[[str], Any]
AnswerCallable = Callable[[str], Any]


def run_qa_evaluation(
    questions: str | Path | Iterable[str | ExamQuestionBlock | Mapping[str, Any]],
    output_dir: str | Path,
    retrieve: RetrievalCallable,
    answer: AnswerCallable | None = None,
    *,
    mode: str | None = None,
    gold_labels: Mapping[str, Any] | Iterable[Mapping[str, Any]] | None = None,
    config: Mapping[str, Any] | None = None,
    resume: bool = False,
) -> JsonObject:
    """Run retrieval or full-answer evaluation through injected callables.

    The runner measures execution and, when section labels are supplied, exact
    retrieval overlap. It does not infer or claim substantive legal correctness.
    """

    selected_mode = _normalize_mode(mode, answer)
    if selected_mode == "full_answer" and answer is None:
        raise ValueError("Full-answer mode requires an answer callable.")

    question_rows = _coerce_questions(questions)
    labels = _normalize_labels(gold_labels)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    checkpoint_path = destination / "results.partial.jsonl"
    existing = _read_jsonl(checkpoint_path) if resume and checkpoint_path.exists() else []
    existing_by_id = {str(record.get("question_id")): record for record in existing}
    if not resume and checkpoint_path.exists():
        checkpoint_path.unlink()

    records: list[JsonObject] = []
    retrieval_calls = 0
    answer_calls = 0
    for index, row in enumerate(question_rows, start=1):
        question_id = _question_id(row, index)
        if question_id in existing_by_id:
            record = existing_by_id[question_id]
            records.append(record)
            retrieval_calls += len(record.get("retrieval", []))
            answer_calls += int(selected_mode == "full_answer" and record.get("answer") is not None)
            continue
        text = _question_text(row)
        analysis = analyze_question(text)
        record: JsonObject = {
            "schema_version": 1,
            "question_id": question_id,
            "question": text,
            "exam": _exam_metadata(row),
            "analysis": analysis.to_dict(),
            "mode": selected_mode,
            "retrieval": [],
            "answer": None,
            "errors": [],
        }

        for subquery in analysis.subqueries:
            retrieval_calls += 1
            try:
                output = retrieve(subquery)
                record["retrieval"].append(
                    {"subquery": subquery, "output": _to_jsonable(output), "error": None}
                )
            except Exception as exc:  # Each question remains inspectable after a callable failure.
                error = _error_payload("retrieval", exc, subquery=subquery)
                record["retrieval"].append({"subquery": subquery, "output": None, "error": error})
                record["errors"].append(error)

        if selected_mode == "full_answer":
            answer_calls += 1
            try:
                record["answer"] = _to_jsonable(answer(text))  # type: ignore[misc]
            except Exception as exc:
                error = _error_payload("answer", exc)
                record["errors"].append(error)
                record["answer"] = {"error": error}

        label = labels.get(question_id)
        if label is not None:
            record["gold_label"] = _to_jsonable(label)
            record["retrieval_label_metrics"] = _score_retrieval(record, label)
        records.append(record)
        _write_jsonl(checkpoint_path, records)

    metrics = _build_metrics(
        records,
        mode=selected_mode,
        retrieval_calls=retrieval_calls,
        answer_calls=answer_calls,
        labels=labels,
    )
    run_config: JsonObject = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": selected_mode,
        "questions": len(records),
        "retrieve_callable": _callable_name(retrieve),
        "answer_callable": _callable_name(answer) if answer else None,
        "gold_labels_supplied": bool(labels),
        "legal_correctness_policy": (
            "This runner does not infer legal correctness. Any correctness value must come from supplied gold labels."
        ),
        "user_config": _to_jsonable(dict(config or {})),
    }

    _write_jsonl(destination / "results.jsonl", records)
    _write_json(destination / "metrics.json", metrics)
    _write_json(destination / "config.json", run_config)
    checkpoint_path.unlink(missing_ok=True)
    return metrics


def run_evaluation(
    questions: str | Path | Iterable[str | ExamQuestionBlock | Mapping[str, Any]],
    output_dir: str | Path,
    retrieve: RetrievalCallable,
    answer: AnswerCallable | None = None,
    **kwargs: Any,
) -> JsonObject:
    """Compatibility alias for callers that use the generic runner name."""

    return run_qa_evaluation(questions, output_dir, retrieve, answer, **kwargs)


def _coerce_questions(
    questions: str | Path | Iterable[str | ExamQuestionBlock | Mapping[str, Any]],
) -> list[str | ExamQuestionBlock | Mapping[str, Any]]:
    if isinstance(questions, Path):
        return list(parse_question_file(questions))
    if isinstance(questions, str):
        possible_path = Path(questions)
        if possible_path.suffix.lower() in {".md", ".markdown"} and possible_path.is_file():
            return list(parse_question_file(possible_path))
        return [questions]
    return list(questions)


def _question_id(row: str | ExamQuestionBlock | Mapping[str, Any], index: int) -> str:
    if isinstance(row, ExamQuestionBlock):
        return row.question_id
    if isinstance(row, Mapping):
        value = row.get("question_id") or row.get("id")
        if value:
            return str(value)
    return f"q{index:04d}"


def _question_text(row: str | ExamQuestionBlock | Mapping[str, Any]) -> str:
    if isinstance(row, str):
        return row
    if isinstance(row, ExamQuestionBlock):
        return row.text
    value = row.get("question") if "question" in row else row.get("text")
    if value is None:
        raise ValueError("Question mappings require a 'question' or 'text' field.")
    return str(value)


def _exam_metadata(row: str | ExamQuestionBlock | Mapping[str, Any]) -> JsonObject | None:
    if isinstance(row, ExamQuestionBlock):
        return {
            "year": row.year,
            "session": row.session,
            "question_number": row.question_number,
        }
    if isinstance(row, Mapping):
        values = {key: row.get(key) for key in ("year", "session", "question_number") if row.get(key) is not None}
        return values or None
    return None


def _normalize_mode(mode: str | None, answer: AnswerCallable | None) -> str:
    if mode is None:
        return "full_answer" if answer is not None else "retrieval_only"
    normalized = mode.strip().lower().replace("-", "_")
    aliases = {
        "retrieval": "retrieval_only",
        "retrieval_only": "retrieval_only",
        "answer": "full_answer",
        "full": "full_answer",
        "full_answer": "full_answer",
    }
    if normalized not in aliases:
        raise ValueError("mode must be 'retrieval_only' or 'full_answer'.")
    return aliases[normalized]


def _normalize_labels(
    labels: Mapping[str, Any] | Iterable[Mapping[str, Any]] | None,
) -> dict[str, Any]:
    if labels is None:
        return {}
    if isinstance(labels, Mapping):
        return {str(key): value for key, value in labels.items()}
    result: dict[str, Any] = {}
    for row in labels:
        question_id = row.get("question_id") or row.get("id")
        if not question_id:
            raise ValueError("Each gold-label row requires 'question_id' or 'id'.")
        result[str(question_id)] = dict(row)
    return result


def _score_retrieval(record: Mapping[str, Any], label: Any) -> JsonObject:
    expected = _expected_sections(label)
    retrieved = _retrieved_sections(record.get("retrieval", []))
    if not expected:
        return {
            "status": "not_scored",
            "reason": "No expected section identifiers were present in this gold label.",
        }
    expected_set = set(expected)
    retrieved_set = set(retrieved)
    overlap = expected_set & retrieved_set
    return {
        "status": "scored",
        "expected_sections": expected,
        "retrieved_sections": retrieved,
        "matched_sections": sorted(overlap),
        "recall": len(overlap) / len(expected_set),
        "all_expected_retrieved": expected_set.issubset(retrieved_set),
    }


def _expected_sections(label: Any) -> list[str]:
    if not isinstance(label, Mapping):
        return []
    value = label.get("expected_sections", label.get("expected_section_ids", []))
    if isinstance(value, str):
        items = value.replace(",", ";").split(";")
    elif isinstance(value, Sequence):
        items = value
    else:
        return []
    return list(dict.fromkeys(str(item).strip() for item in items if str(item).strip()))


def _retrieved_sections(retrieval_rows: Any) -> list[str]:
    section_ids: list[str] = []
    for row in retrieval_rows if isinstance(retrieval_rows, list) else []:
        _collect_section_ids(row.get("output") if isinstance(row, Mapping) else row, section_ids)
    return list(dict.fromkeys(section_ids))


def _collect_section_ids(value: Any, result: list[str]) -> None:
    if isinstance(value, Mapping):
        section_id = value.get("section_id")
        if section_id:
            result.append(str(section_id))
        for child in value.values():
            _collect_section_ids(child, result)
    elif isinstance(value, list):
        for child in value:
            _collect_section_ids(child, result)


def _build_metrics(
    records: list[JsonObject],
    *,
    mode: str,
    retrieval_calls: int,
    answer_calls: int,
    labels: Mapping[str, Any],
) -> JsonObject:
    successful = sum(not record["errors"] for record in records)
    scored = [
        record["retrieval_label_metrics"]
        for record in records
        if record.get("retrieval_label_metrics", {}).get("status") == "scored"
    ]
    metrics: JsonObject = {
        "schema_version": 1,
        "mode": mode,
        "questions": len(records),
        "questions_succeeded": successful,
        "questions_with_errors": len(records) - successful,
        "retrieval_calls": retrieval_calls,
        "answer_calls": answer_calls,
        "gold_label_questions": sum(record["question_id"] in labels for record in records),
        "retrieval_relevance": {
            "status": "scored" if scored else "not_scored",
            "scored_questions": len(scored),
            "mean_recall": (sum(item["recall"] for item in scored) / len(scored)) if scored else None,
            "all_expected_retrieved_rate": (
                sum(bool(item["all_expected_retrieved"]) for item in scored) / len(scored) if scored else None
            ),
        },
        "answer_quality": _answer_quality_metrics(records),
        "legal_correctness": _legal_correctness_metrics(records),
    }
    return metrics


def _answer_quality_metrics(records: list[JsonObject]) -> JsonObject:
    outcomes: dict[str, int] = {}
    fallback_reasons: dict[str, int] = {}
    claims = 0
    verified_claims = 0
    parts_requested = 0
    parts_with_claims: set[tuple[str, str]] = set()
    for record in records:
        analysis = record.get("analysis") or {}
        subquestions = analysis.get("subquestions") if isinstance(analysis, Mapping) else []
        parts_requested += len(subquestions) if isinstance(subquestions, list) else 0
        answer = record.get("answer")
        if not isinstance(answer, Mapping):
            continue
        outcome = str(answer.get("outcome") or "unknown")
        outcomes[outcome] = outcomes.get(outcome, 0) + 1
        fallback = answer.get("fallback_reason")
        if fallback:
            key = str(fallback)
            fallback_reasons[key] = fallback_reasons.get(key, 0) + 1
        answer_claims = answer.get("claims")
        if not isinstance(answer_claims, list):
            continue
        claims += len(answer_claims)
        for claim in answer_claims:
            if not isinstance(claim, Mapping):
                continue
            verified_claims += int(claim.get("verified") is True)
            part = str(claim.get("part") or "").strip()
            if part:
                parts_with_claims.add((str(record.get("question_id")), part))
    return {
        "status": "machine_checks_only",
        "outcomes": dict(sorted(outcomes.items())),
        "fallback_reasons": dict(sorted(fallback_reasons.items())),
        "claims": claims,
        "verified_claims": verified_claims,
        "parts_requested": parts_requested,
        "parts_with_verified_claims": len(parts_with_claims),
        "part_coverage": (len(parts_with_claims) / parts_requested) if parts_requested else None,
        "scope": "Citation and execution checks only; this is not a legal-correctness score.",
    }


def _legal_correctness_metrics(records: list[JsonObject]) -> JsonObject:
    labelled_values: list[bool] = []
    for record in records:
        label = record.get("gold_label")
        if isinstance(label, Mapping) and isinstance(label.get("legal_correct"), bool):
            labelled_values.append(label["legal_correct"])
    if not labelled_values:
        return {
            "status": "not_evaluated",
            "labelled_answers": 0,
            "reason": "No explicit gold legal_correct labels were supplied; no legal correctness claim is made.",
        }
    return {
        "status": "reported_from_gold_labels",
        "labelled_answers": len(labelled_values),
        "accuracy": sum(labelled_values) / len(labelled_values),
        "reason": "Values are aggregated from supplied gold labels, not inferred by this runner.",
    }


def _to_jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "to_dict") and callable(value.to_dict):
        if hasattr(value, "raw_response"):
            return _to_jsonable(value.to_dict(include_raw=True))
        try:
            return _to_jsonable(value.to_dict(include_text=False))
        except TypeError:
            return _to_jsonable(value.to_dict())
    if is_dataclass(value):
        return _to_jsonable(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_to_jsonable(item) for item in value]
    return repr(value)


def _error_payload(stage: str, error: Exception, **context: Any) -> JsonObject:
    return {
        "stage": stage,
        "type": type(error).__name__,
        "message": str(error),
        **context,
    }


def _callable_name(function: Callable[..., Any] | None) -> str | None:
    if function is None:
        return None
    module = getattr(function, "__module__", "")
    name = getattr(function, "__qualname__", getattr(function, "__name__", type(function).__name__))
    return f"{module}.{name}".strip(".")


def _write_jsonl(path: Path, records: list[JsonObject]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def _read_jsonl(path: Path) -> list[JsonObject]:
    records: list[JsonObject] = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                records.append(json.loads(line))
    return records


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


__all__ = ["run_evaluation", "run_qa_evaluation"]
