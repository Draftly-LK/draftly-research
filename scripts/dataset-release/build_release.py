"""Build local, unpublished Hugging Face staging packages from frozen sources."""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import datetime
import hashlib
import json
import shutil
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from evaluate import read_jsonl, score, validate_split

ROOT = Path(__file__).resolve().parents[2]
BENCH = ROOT / "data/evaluvation/statutory-qa-v1"
PAPERS = ROOT / "data/evaluvation/parsed-pastpapers"
REGISTRY = ROOT / "data/legal-sources/manifests/source-registry.csv"
VERSION = "v1.0-paper-provisional"


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean_quotes(value):
    if isinstance(value, list):
        return [clean_quotes(x) for x in value]
    if isinstance(value, dict):
        return {k: clean_quotes(v) for k, v in value.items() if k not in {"quote", "source_quote"}}
    return value


def build_benchmark(out: Path) -> dict:
    source = BENCH / "benchmark"
    inputs = read_jsonl(source / "public-input.jsonl")
    gold = {x["benchmark_question_id"]: x for x in read_jsonl(source / "private-gold.jsonl")}
    split_ids = {split: set(json.loads((source / f"{file}-ids.json").read_text(encoding="utf-8"))["questions"])
                 for split, file in (("development", "development"), ("test", "test"))}
    if split_ids["development"] & split_ids["test"] or set(gold) != split_ids["development"] | split_ids["test"]:
        raise ValueError("frozen split IDs do not partition the reference labels")
    rows = []
    for inp in inputs:
        qid = inp["benchmark_question_id"]
        g = gold[qid]
        if g["lawyer_validation_status"] != "pending":
            raise ValueError(f"unexpected lawyer status: {qid}")
        section_statuses = sorted({(p["section_id"], p["verification_status"])
                                   for p in g["indispensable_provisions"]})
        rows.append({
            **inp,
            "source_atomic_id": g["atomic_id"],
            "split": "development" if qid in split_ids["development"] else "test",
            "indispensable_section_ids": g["indispensable_section_ids"],
            "indispensable_section_statuses": [{"section_id": sid, "verification_status": status}
                                                 for sid, status in section_statuses],
            "reference_label_status": "provisional",
            "lawyer_validation_status": "pending",
        })
    validate_split(rows)
    if len(rows) != 50 or sum(r["split"] == "development" for r in rows) != 10:
        raise ValueError("main benchmark count changed")
    for split in ("development", "test"):
        write_jsonl(out / "benchmark_v1" / f"{split}.jsonl", [r for r in rows if r["split"] == split])
    write_jsonl(out / "benchmark_v1" / "lineage.jsonl", [
        {"benchmark_question_id": r["benchmark_question_id"], "source_atomic_id": r["source_atomic_id"],
         "paper_no": r["paper_no"]} for r in rows])

    source_rows = []
    for path in sorted((PAPERS / "questions").glob("paper-*.questions.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        source_rows.append(clean_quotes({k: doc[k] for k in ("schema_version", "paper_no", "session", "subject", "code", "pdf_pages", "questions")}))
    if len(source_rows) != 16:
        raise ValueError("expected 16 structured past papers")
    write_jsonl(out / "source_papers" / "data.jsonl", source_rows)

    allowed = ("atomic_id", "part_uid", "paper_no", "question_no", "part_id", "item_id", "matter_id",
               "compulsory", "stem", "shared_background", "shared_background_origin", "group_background",
               "group_lead", "prior_background", "own_background", "question", "question_kind", "marks",
               "part_marks", "pdf_page", "split_method", "needs_review")
    atomic = [{k: row.get(k) for k in allowed} for row in read_jsonl(PAPERS / "atomic/atomic-questions.jsonl")]
    if len(atomic) != 667:
        raise ValueError("expected 667 atomic questions")
    write_jsonl(out / "atomic_question_pool" / "data.jsonl", atomic)

    (out / "evaluation").mkdir(exist_ok=True)
    shutil.copy2(Path(__file__).with_name("evaluate.py"), out / "evaluation" / "evaluate.py")
    shutil.copy2(Path(__file__).with_name("prediction.schema.json"), out / "evaluation" / "prediction.schema.json")
    development = [r for r in rows if r["split"] == "development"]
    example = [{"benchmark_question_id": r["benchmark_question_id"],
                "ranked_section_ids": r["indispensable_section_ids"]} for r in development]
    write_jsonl(out / "evaluation" / "example-predictions.jsonl", example)
    (out / "evaluation" / "example-expected.json").write_text(
        json.dumps(score(development, example), indent=2) + "\n", encoding="utf-8")
    return {"questions": len(rows), "matters": len({r["benchmark_matter_id"] for r in rows}),
            "development": len(split_ids["development"]), "test": len(split_ids["test"]),
            "source_papers": len(source_rows), "atomic_questions": len(atomic)}


def build_index(out: Path) -> dict:
    acts = read_jsonl(BENCH / "corpus/acts.jsonl")
    manifest = json.loads((BENCH / "corpus/manifest.json").read_text(encoding="utf-8"))
    with REGISTRY.open(encoding="utf-8-sig", newline="") as stream:
        registry = list(csv.DictReader(stream))
    rows = []
    for act in acts:
        doc = json.loads((ROOT / act["source_file"]).read_text(encoding="utf-8"))
        direct = doc.get("source_url") or ""
        source_row = next((r for r in registry if r["source_id"] == act.get("source_id")), None)
        url = direct or (source_row or {}).get("preferred_source_url", "")
        candidates = [r for r in registry if act["kind"] == "amendment" and r["source_type"] == "amendment"
                      and r["act_or_ordinance_no"] == str(act["number"]) and r["year"] == str(act["year"])]
        candidate = candidates[0]["preferred_source_url"] if len(candidates) == 1 else ""
        rows.append({
            "act_id": act["act_id"], "title": act["title"], "number": act["number"], "year": act["year"],
            "kind": act["kind"], "amends_act_id": act["amends_act_id"], "edition_kind": act["edition_kind"],
            "edition_publisher": act["edition_publisher"], "source_id": act["source_id"],
            "source_url": url, "source_host": urlparse(url).netloc if url else "",
            "candidate_source_url": candidate if not url else "",
            "url_match_status": "source_record_unchecked" if url else "candidate_unchecked" if candidate else "missing",
            "url_check_date": None, "corpus_fingerprint": manifest["corpus_fingerprint"],
            "in_paper_corpus": True,
        })
    if len(rows) != 112 or len({r["act_id"] for r in rows}) != 112:
        raise ValueError("paper corpus Act count changed")
    write_jsonl(out / "acts" / "data.jsonl", rows)
    return {"documents": len(rows), "source_urls_unchecked": sum(bool(r["source_url"]) for r in rows),
            "candidate_urls_unchecked": sum(bool(r["candidate_source_url"]) for r in rows),
            "missing_urls": sum(not r["source_url"] and not r["candidate_source_url"] for r in rows),
            "corpus_fingerprint": manifest["corpus_fingerprint"]}


def check_link(url: str) -> dict:
    headers = {"User-Agent": "Draftly-source-link-check/1.0"}
    for method in ("HEAD", "GET"):
        try:
            request = Request(url, headers=headers, method=method)
            with urlopen(request, timeout=15) as response:
                return {"status": response.status, "final_url": response.url,
                        "content_type": response.headers.get("Content-Type", "")}
        except HTTPError as error:
            if method == "HEAD" and error.code in (403, 405, 501):
                continue
            return {"status": error.code, "final_url": url, "content_type": ""}
        except (URLError, TimeoutError, OSError) as error:
            return {"status": None, "final_url": url, "content_type": "",
                    "error_type": type(error).__name__}
    return {"status": None, "final_url": url, "content_type": ""}


def check_index_links(out: Path) -> dict:
    path = out / "acts/data.jsonl"
    rows = read_jsonl(path)
    urls = sorted({url for row in rows for url in (row["source_url"], row["candidate_source_url"]) if url})
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        results = dict(zip(urls, executor.map(check_link, urls)))
    today = datetime.date.today().isoformat()
    for row in rows:
        url = row["source_url"] or row["candidate_source_url"]
        if url:
            row["url_check_date"] = today
            row["url_http_status"] = results[url]["status"]
            row["url_final_url"] = results[url]["final_url"]
            row["url_content_type"] = results[url]["content_type"]
            row["url_reachability"] = "reachable" if results[url]["status"] and results[url]["status"] < 400 else "unreachable"
        else:
            row["url_http_status"] = None
            row["url_final_url"] = ""
            row["url_content_type"] = ""
            row["url_reachability"] = "missing"
    write_jsonl(path, rows)
    return {"checked_urls": len(urls), "reachable_rows": sum(r["url_reachability"] == "reachable" for r in rows),
            "unreachable_rows": sum(r["url_reachability"] == "unreachable" for r in rows)}


def manifest(out: Path, counts: dict) -> None:
    files = {str(path.relative_to(out)).replace("\\", "/"): sha(path) for path in sorted(out.rglob("*"))
             if path.is_file() and path.name != "release-manifest.json"}
    (out / "release-manifest.json").write_text(json.dumps({"version": VERSION, "status": "local_review_only",
        "counts": counts, "sha256": files}, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "tmp/hf-release")
    parser.add_argument("--check-urls", action="store_true", help="Check URL reachability; does not verify edition identity")
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    benchmark = out / "draftly-statutory-retrieval"
    index = out / "draftly-sri-lanka-act-sources"
    for folder in (benchmark, index):
        folder.mkdir(exist_ok=True)
    b = build_benchmark(benchmark)
    a = build_index(index)
    if args.check_urls:
        a["link_check"] = check_index_links(index)
    shutil.copy2(Path(__file__).with_name("benchmark-card.md"), benchmark / "README.md")
    shutil.copy2(Path(__file__).with_name("act-index-card.md"), index / "README.md")
    manifest(benchmark, b)
    manifest(index, a)
    print(json.dumps({"benchmark": b, "act_index": a, "output": str(out)}, indent=2))


if __name__ == "__main__":
    main()
