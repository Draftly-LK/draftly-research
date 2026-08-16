"""Build HTML layout fingerprints for the complete CommonLII LKSC archive.

The generated category and confidence are heuristic outputs. Scoring is
series-gated: the report series (NLR/SLR) routes almost all score mass to its
own layout pair, and a steep sigmoid over the one feature that separates that
pair (br-per-paragraph for NLR, font-per-paragraph for SLR) splits the pair.
Both features are normalized by paragraph count, so long judgments do not
accumulate raw tag counts into a false layout signal, and both are strongly
bimodal in this archive, so most files score above 0.9;
scores near 0.5 mark genuinely ambiguous pages. The confidence is still not a
calibrated model probability.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from bs4 import BeautifulSoup


LAYOUTS = (
    "paragraph_nlr",
    "dense_br_nlr",
    "structured_slr",
    "late_slr_font",
)


# Both discriminating features are normalized by paragraph count so long
# judgments do not accumulate raw tag counts into a false layout signal.
# NLR br_per_paragraph is bimodal: paragraph-led pages sit below 0.5, br-led
# pages above 1.5, with a near-empty gap around 1.0. SLR font_per_paragraph is
# bimodal too: stray tags on long pages stay below 0.06, genuinely font-led
# pages sit above 0.61 (about one <font> per paragraph).
BR_MIDPOINT = 1.0
BR_STEEPNESS = 4.0
FONT_MIDPOINT = 0.3
FONT_STEEPNESS = 15.0
# Mass routed to the layout pair matching the detected report series. The
# residual keeps cross-series scores nonzero so a misdetected series still
# surfaces as a low-confidence file instead of a hard zero.
SERIES_PRIOR = 0.92


def sigmoid(value: float) -> float:
    return float(1.0 / (1.0 + np.exp(-value)))


def layout_scores(report_series: str, fingerprint: dict) -> dict[str, float]:
    """Return four heuristic scores (summing to 1) for one HTML fingerprint.

    The series gates which layout pair gets the score mass; a steep sigmoid
    over that pair's discriminating feature splits it within the pair.
    """
    br_evidence = sigmoid(
        BR_STEEPNESS * (fingerprint["br_per_paragraph"] - BR_MIDPOINT)
    )
    font_evidence = sigmoid(
        FONT_STEEPNESS * (fingerprint["font_per_paragraph"] - FONT_MIDPOINT)
    )

    if report_series == "NLR":
        nlr_mass, slr_mass = SERIES_PRIOR, 1.0 - SERIES_PRIOR
    elif report_series == "SLR":
        nlr_mass, slr_mass = 1.0 - SERIES_PRIOR, SERIES_PRIOR
    else:
        nlr_mass = slr_mass = 0.5

    return {
        "paragraph_nlr": nlr_mass * (1.0 - br_evidence),
        "dense_br_nlr": nlr_mass * br_evidence,
        "structured_slr": slr_mass * (1.0 - font_evidence),
        "late_slr_font": slr_mass * font_evidence,
    }


def report_series(soup: BeautifulSoup, html: str) -> str:
    """Identify NLR or SLR from the case heading and report-source comment."""
    heading = soup.find("h2")
    heading_text = heading.get_text(" ", strip=True).upper() if heading else ""
    source_text = f"{heading_text} {html[:8000].upper()}"
    if re.search(r"\b(?:SLR|SRI\s*LR)\b", source_text):
        return "SLR"
    if re.search(r"\bNLR\b", source_text):
        return "NLR"
    return "UNKNOWN"


def judgment_nodes(soup: BeautifulSoup) -> list:
    """Return tags after the case heading and before the CommonLII footer rule."""
    heading = soup.find("h2")
    if heading is None:
        raise ValueError("no <h2> case heading")

    nodes = []
    for node in heading.find_all_next(True):
        if node.name == "hr":
            break
        nodes.append(node)
    return nodes


def fingerprint_html(path: Path, root: Path) -> dict:
    html = path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html, "lxml")
    nodes = judgment_nodes(soup)
    tag_counts = {tag: 0 for tag in ("p", "br", "font", "strong", "b", "em", "i")}
    for node in nodes:
        if node.name in tag_counts:
            tag_counts[node.name] += 1

    heading = soup.find("h2")
    marker_text = " ".join(
        node.get_text(" ", strip=True)
        for node in nodes
        if node.name in {"p", "div", "center", "td"}
    )
    marker_text = re.sub(r"\s+", " ", marker_text)
    paragraph_count = tag_counts["p"]
    br_count = tag_counts["br"]
    font_count = tag_counts["font"]
    char_count = len(marker_text)

    fingerprint = {
        "paragraph_count": paragraph_count,
        "char_count": char_count,
        "br_count": br_count,
        "br_per_paragraph": round(br_count / max(paragraph_count, 1), 6),
        "br_per_1000_chars": round(br_count / max(char_count, 1) * 1000, 6),
        "font_count": font_count,
        "font_per_paragraph": round(font_count / max(paragraph_count, 1), 6),
        "font_per_1000_chars": round(font_count / max(char_count, 1) * 1000, 6),
        # Treat legacy semantic equivalents as formatting evidence too.
        "strong_count": tag_counts["strong"] + tag_counts["b"],
        "em_count": tag_counts["em"] + tag_counts["i"],
        "has_held": bool(re.search(r"\bHeld\b", marker_text, re.I)),
        "has_cases_referred": bool(
            re.search(r"\bCases?\s+referred\s+to\b", marker_text, re.I)
        ),
        "has_cur_adv_vult": bool(
            re.search(r"\bCur\.?\s*adv\.?\s*vult\.?", marker_text, re.I)
        ),
        "has_agreement": bool(
            re.search(r"\b(?:I|We)\s+agree\b|\bagreed\b", marker_text, re.I)
        ),
        "has_explicit_result": bool(
            re.search(
                r"\b(?:appeal|application|petition)\s+(?:is\s+)?"
                r"(?:allowed|dismissed|refused)\b|"
                r"\b(?:conviction|order)\s+(?:is\s+)?"
                r"(?:affirmed|set\s+aside|quashed)\b",
                marker_text,
                re.I,
            )
        ),
    }
    series = report_series(soup, html)
    scores = layout_scores(series, fingerprint)
    category = max(scores, key=scores.get)

    relative = path.relative_to(root)
    return {
        "file": relative.as_posix(),
        "year": int(path.parent.name),
        "report_series": series,
        "page_title": heading.get_text(" ", strip=True) if heading else None,
        "category": category,
        "confidence": round(scores[category], 6),
        "layout_scores": {name: round(value, 6) for name, value in scores.items()},
        "fingerprint": fingerprint,
    }


def build_report(input_dir: Path) -> dict:
    html_files = sorted(
        input_dir.glob("*/*.html"),
        key=lambda path: (int(path.parent.name), int(path.stem)),
    )
    pdf_files = list(input_dir.glob("*/*.pdf"))
    if not html_files:
        raise ValueError(f"no HTML files found below {input_dir}")

    records = []
    errors = []
    for path in html_files:
        try:
            records.append(fingerprint_html(path, input_dir))
        except Exception as exc:  # retain the file-level failure in the report
            errors.append(
                {
                    "file": path.relative_to(input_dir).as_posix(),
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_directory": input_dir.as_posix(),
        "html_files_found": len(html_files),
        "html_files_fingerprinted": len(records),
        "pdf_files_skipped": len(pdf_files),
        "errors": errors,
        "files": records,
    }


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=repo_root / "data" / "commonlii" / "raw" / "LKSC",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=repo_root / "data" / "commonlii" / "layout-categories.json",
    )
    args = parser.parse_args()

    input_dir = args.input.resolve()
    output_path = args.output.resolve()
    report = build_report(input_dir)
    if report["errors"]:
        raise RuntimeError(
            f"fingerprinting failed for {len(report['errors'])} HTML file(s)"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary.write_text(json.dumps(report, indent=2), encoding="utf-8")
    temporary.replace(output_path)

    print(
        f"Fingerprinted {report['html_files_fingerprinted']} HTML files; "
        f"skipped {report['pdf_files_skipped']} PDFs; wrote {output_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
