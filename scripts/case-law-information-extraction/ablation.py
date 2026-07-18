"""Pre-registered ablation + holdout evaluation of the no-headnote rule-extraction
method (config at evaluation/runs/caselaw-ablation-v1/config.json).

Why this exists: before spending credits on the full ~3,179 no-headnote run, we
must SHOW the method works and compare it against alternatives — not assert it.
This harness answers, on frozen stratified samples:
  * ablation: 8B+naive vs 8B+cue-window vs 8B+full vs 70B+full (4 arms).
  * holdout : the frozen best arm on a fresh disjoint 100-case set.
  * judge   : a 70B LLM-as-judge PROXY over accepted holdout rules (non-authoritative).
  * metrics : per-arm/holdout numbers + a blank lawyer-labelling pack.

Grounding is treated as NECESSARY-NOT-SUFFICIENT. The independent grounding check
here is a *token-level* verifier deliberately implemented differently from
validate.quote_match (which is char/whitespace based), so it is a genuine second
opinion, not a re-run of the gate.

Resumable: every model result is appended to raw-responses.jsonl keyed by
(stage,arm,case_id); re-running skips completed keys. Deterministic given the seed
(sampling); note that hosted model outputs are NOT bit-reproducible even at
temperature 0, which is exactly why raw responses are frozen to disk.

Usage:
  python ablation.py sample     # freeze stratified samples (0 credits)
  python ablation.py ablation   # 4 arms x 30 cases  (~120 logical calls)
  python ablation.py holdout    # frozen best arm x 100 cases
  python ablation.py judge      # 70B judge over accepted holdout rules
  python ablation.py metrics    # compute metrics.json + lawyer-labels.csv (0 credits)
"""

from __future__ import annotations

import argparse
import collections
import csv
import difflib
import hashlib
import json
import re
import sys
import time
from pathlib import Path

import config
import catalogue
import validate as V
import windowing
import extract_case_rules as X
from llm_client import chat_json, usage_summary, HTTP_ATTEMPTS

RUN = config.ROOT / "evaluation" / "runs" / "caselaw-ablation-v1"
RAW = RUN / "raw-responses.jsonl"
CFG = json.loads((RUN / "config.json").read_text(encoding="utf-8"))
SEED = CFG["seed"]
ARMS = CFG["stages"]["ablation"]["arms"]
N_ABL = CFG["stages"]["ablation"]["n_cases"]
N_HOLD = CFG["stages"]["holdout"]["n_cases"]
JUDGE_MODEL = CFG["stages"]["judge"]["model"]

HEAD, TAIL, MAXC = config.WINDOW_HEAD_CHARS, config.WINDOW_TAIL_CHARS, config.WINDOW_MAX_CHARS


# ----------------------------------------------------------------- sampling
def _rng(seed: int):
    """Tiny deterministic LCG — avoids depending on random module global state."""
    state = {"x": (seed * 2654435761 + 1) & 0xFFFFFFFF}

    def nxt() -> float:
        state["x"] = (1103515245 * state["x"] + 12345) & 0x7FFFFFFF
        return state["x"] / 0x7FFFFFFF
    return nxt


def _read_text(case: dict) -> str:
    p = Path(case.get("text_path", ""))
    for cand in (config.ROOT / p, p):
        if cand.exists():
            return cand.read_text(encoding="utf-8", errors="replace").strip()
    return ""


def _naive_window(text: str) -> str:
    if len(text) <= MAXC:
        return text
    return text[:HEAD] + "\n\n[...]\n\n" + text[-TAIL:]


def _full_window(text: str) -> str:
    return text[:config.FULL_TEXT_MAX_CHARS]


def _window(strategy: str, text: str) -> str:
    if strategy == "naive_head_tail":
        return _naive_window(text)
    if strategy == "cue_aware":
        return windowing.build_window(text)
    if strategy == "full_text":
        return _full_window(text)
    raise ValueError(strategy)


def _at_risk(text: str) -> bool:
    """True if a ruling cue exists ONLY in the omitted middle (naive window misses it)."""
    if len(text) <= MAXC:
        return False
    naive = re.sub(r"\s+", " ", _naive_window(text))
    lo, hi = HEAD, len(text) - TAIL
    for m in windowing._RULING_CUE.finditer(text):
        if lo < m.start() < hi:
            probe = re.sub(r"\s+", " ", text[m.start():m.start() + 180]).strip()
            if probe and probe not in naive:
                return True
    return False


def _strata(case: dict, text: str) -> tuple:
    y = int(re.sub(r"\D", "", str(case.get("year") or "0")) or 0)
    ybucket = "pre1950" if y < 1950 else "1950-1999" if y < 2000 else "2000+"
    n = len(text)
    lbucket = "short" if n < 12000 else "mid" if n < 30000 else "long"
    return (case.get("court", "?"), _at_risk(text), ybucket, lbucket)


def _population() -> list[dict]:
    no_head = set()
    for cf in config.CACHE.glob("commonlii-*.json"):
        try:
            if json.loads(cf.read_text(encoding="utf-8")).get("status") == "no-headnote":
                no_head.add(cf.stem)
        except Exception:
            pass
    pop = []
    for c in X.load_cases():
        if c["case_id"] in no_head:
            t = _read_text(c)
            if t:
                c["_text"] = t
                pop.append(c)
    return pop


def _order(avail: list[dict], seed: int) -> list[dict]:
    return sorted(avail, key=lambda c: hashlib.sha256((str(seed) + c["case_id"]).encode()).hexdigest())


def _coverage_sample(pop: list[dict], n: int, exclude: set[str], seed: int,
                     min_at_risk: int, min_lksc: int) -> list[dict]:
    """For the ABLATION: deliberately guarantee coverage of the comparison-relevant
    strata (at-risk cases, where naive vs cue-window diverge; and LKSC), then fill the
    rest deterministically. This is for method DISCRIMINATION, not representativeness —
    the holdout (proportional) is what the precision estimate is computed on."""
    order = _order([c for c in pop if c["case_id"] not in exclude], seed)
    chosen, used = [], set()

    def take(pred, cap):
        got = 0
        for c in order:
            if got >= cap:
                break
            if c["case_id"] not in used and pred(c):
                chosen.append(c); used.add(c["case_id"]); got += 1
    take(lambda c: _at_risk(c["_text"]), min_at_risk)
    take(lambda c: c.get("court") == "LKSC", min_lksc)
    take(lambda c: True, n - len(chosen))  # fill remainder
    return chosen[:n]


def _stratified(pop: list[dict], n: int, exclude: set[str], seed: int) -> list[dict]:
    """Representative proportional allocation across strata (used for the HOLDOUT)."""
    avail = [c for c in pop if c["case_id"] not in exclude]
    groups: dict[tuple, list[dict]] = {}
    for c in avail:
        groups.setdefault(_strata(c, c["_text"]), []).append(c)
    # deterministic shuffle within each group
    for g in groups.values():
        g.sort(key=lambda c: hashlib.sha256((str(seed) + c["case_id"]).encode()).hexdigest())
    keys = sorted(groups)
    # proportional allocation, then round-robin to fill any remainder
    total = len(avail)
    chosen, cursors = [], {k: 0 for k in keys}
    alloc = {k: min(len(groups[k]), round(n * len(groups[k]) / total)) for k in keys}
    for k in keys:
        chosen.extend(groups[k][:alloc[k]])
        cursors[k] = alloc[k]
    i = 0
    while len(chosen) < n and any(cursors[k] < len(groups[k]) for k in keys):
        k = keys[i % len(keys)]
        if cursors[k] < len(groups[k]):
            chosen.append(groups[k][cursors[k]])
            cursors[k] += 1
        i += 1
    return chosen[:n]


def _write_sample_csv(path: Path, cases: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["case_id", "citation", "court", "year", "chars",
                    "at_risk", "year_bucket", "length_bucket"])
        for c in cases:
            court, atr, yb, lb = _strata(c, c["_text"])
            w.writerow([c["case_id"], c.get("citation"), c.get("court"),
                        c.get("year"), len(c["_text"]), atr, yb, lb])


def cmd_sample() -> None:
    pop = _population()
    # ablation: guarantee at-risk + LKSC coverage so arm differences are detectable
    abl = _coverage_sample(pop, N_ABL, set(), SEED, min_at_risk=12, min_lksc=3)
    # holdout: representative (proportional) — this is what the precision estimate uses
    hold = _stratified(pop, N_HOLD, {c["case_id"] for c in abl}, SEED + 1)
    _write_sample_csv(RUN / "sample_ablation.csv", abl)
    _write_sample_csv(RUN / "sample_holdout.csv", hold)
    print(f"population={len(pop)}  ablation={len(abl)}  holdout={len(hold)}  (disjoint)")
    print(f"wrote {RUN/'sample_ablation.csv'} and {RUN/'sample_holdout.csv'}")


# ----------------------------------------------------------------- extraction
def _load_sample(name: str) -> list[dict]:
    ids = []
    with (RUN / name).open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            ids.append(row["case_id"])
    by_id = {c["case_id"]: c for c in X.load_cases()}
    out = []
    for cid in ids:
        c = by_id.get(cid)
        if c:
            c["_text"] = _read_text(c)
            out.append(c)
    return out


def _done_keys() -> set[tuple]:
    done = set()
    if RAW.exists():
        for line in RAW.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
                done.add((r["stage"], r.get("arm", ""), r["case_id"]))
            except Exception:
                pass
    return done


def _append_raw(rec: dict) -> None:
    with RAW.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def independent_grounded(quote: str, text: str, thresh: float = 0.9) -> bool:
    """Second-opinion grounding: TOKEN-level longest contiguous run >= thresh of the
    quote's tokens. Deliberately NOT validate.quote_match (which is char/whitespace)."""
    def toks(s: str) -> list[str]:
        return re.findall(r"\w+", s.lower())
    q, t = toks(quote), toks(text)
    if len(q) < 4:
        return False
    m = difflib.SequenceMatcher(None, q, t, autojunk=False).find_longest_match(0, len(q), 0, len(t))
    return m.size >= max(4, int(thresh * len(q)))


def _extract(case: dict, model: str, strategy: str, links: list[str]) -> dict:
    win = _window(strategy, case["_text"])
    user = X.USER_EXTRACT.format(
        citation=case.get("citation", ""), court=case.get("court", ""),
        year=case.get("year", ""), catalogue=catalogue.catalogue_lines(),
        linked=", ".join(links) if links else "(none recorded)", text=win)
    prompt_sha = hashlib.sha256((X.SYS_EXTRACT + "\n" + user).encode("utf-8")).hexdigest()[:16]
    j = chat_json(X.SYS_EXTRACT, user, model)

    rec = {"case_id": case["case_id"], "citation": case.get("citation"),
           "court": case.get("court"), "year": case.get("year"),
           "model": model, "window_strategy": strategy, "window_chars": len(win),
           "text_chars": len(case["_text"]), "prompt_sha": prompt_sha,
           "cue_in_window": bool(windowing._RULING_CUE.search(win)),
           "at_risk": _at_risk(case["_text"]), "raw": j}
    if j is None:
        rec.update(status="llm-error", rule=None, match_type=None, indep_grounded=None)
    elif j.get("rule") in (None, "null"):
        rec.update(status="abstained", rule=None, match_type=None, indep_grounded=None)
    else:
        ok, cleaned, why = V.validate_rule(j["rule"], case["_text"], allow_fuzzy=False)
        if ok:
            rec.update(status="ok", rule=cleaned, match_type=cleaned["match_type"],
                       indep_grounded=independent_grounded(cleaned["supporting_quote"], case["_text"]))
        else:
            rec.update(status="reject:" + why, rule=None, match_type=None, indep_grounded=None)
    return rec


def cmd_ablation() -> None:
    sample = _load_sample("sample_ablation.csv")
    links = X.load_links()
    done = _done_keys()
    todo = [(arm, c) for arm in ARMS for c in sample if ("ablation", arm, c["case_id"]) not in done]
    print(f"ablation: {len(sample)} cases x {len(ARMS)} arms; {len(todo)} to run "
          f"({len(sample)*len(ARMS)-len(todo)} cached)")
    for i, (arm, c) in enumerate(todo, 1):
        spec = ARMS[arm]
        rec = _extract(c, spec["model"], spec["window"], links.get(c["case_id"], []))
        rec.update(stage="ablation", arm=arm)
        _append_raw(rec)
        if i % 10 == 0:
            print(f"  {i}/{len(todo)} | http_attempts={HTTP_ATTEMPTS['count']}")
        time.sleep(config.DELAY_S)
    print(f"[done] usage={json.dumps(usage_summary())}")


def _best_arm() -> str:
    """Frozen selection rule (deterministic). The mass run deploys the CHEAP (8B)
    tier — 70B is reserved for escalation and validated elsewhere — so the holdout
    validates the best DEPLOYABLE 8B arm. Arm D (70B) stays in the ablation as the
    ceiling reference but is NOT eligible to be the holdout method. Among eligible
    arms with 100% independent grounding, pick the highest accept-rate; tie -> arm
    letter. Written to best_method.json."""
    rows = _raw_rows(stage="ablation")
    by_arm: dict[str, list[dict]] = {}
    for r in rows:
        if "8b" in ARMS.get(r["arm"], {}).get("model", ""):  # deployable tier only
            by_arm.setdefault(r["arm"], []).append(r)
    scored = []
    for arm, rs in by_arm.items():
        acc = [r for r in rs if r["status"] == "ok"]
        gnd = [r for r in acc if r.get("indep_grounded")]
        grounding = (len(gnd) / len(acc)) if acc else 0.0
        accept = len(acc) / len(rs) if rs else 0.0
        cheap = 0 if "8b" in ARMS[arm]["model"] else 1
        scored.append((round(grounding, 3) >= 1.0, round(accept, 3), -cheap, arm, ARMS[arm]))
    scored.sort(key=lambda s: (s[0], s[1], s[2], -ord(s[3][0])), reverse=True)
    best = scored[0][3]
    (RUN / "best_method.json").write_text(
        json.dumps({"arm": best, **ARMS[best],
                    "ranking": [{"arm": s[3], "grounding_ok": s[0], "accept_rate": s[1]} for s in scored]},
                   indent=2), encoding="utf-8")
    return best


def cmd_holdout() -> None:
    best = _best_arm()
    spec = ARMS[best]
    print(f"holdout: frozen best arm = {best} ({spec['model']} / {spec['window']})")
    sample = _load_sample("sample_holdout.csv")
    links = X.load_links()
    done = _done_keys()
    todo = [c for c in sample if ("holdout", best, c["case_id"]) not in done]
    print(f"holdout: {len(sample)} cases; {len(todo)} to run ({len(sample)-len(todo)} cached)")
    for i, c in enumerate(todo, 1):
        rec = _extract(c, spec["model"], spec["window"], links.get(c["case_id"], []))
        rec.update(stage="holdout", arm=best)
        _append_raw(rec)
        if i % 10 == 0:
            print(f"  {i}/{len(todo)} | http_attempts={HTTP_ATTEMPTS['count']}")
        time.sleep(config.DELAY_S)
    print(f"[done] usage={json.dumps(usage_summary())}")


# ----------------------------------------------------------------- judge (proxy)
SYS_JUDGE = """You are a senior Sri Lankan lawyer auditing an automatically extracted \
case-law rule. You are given the judgment text and a candidate rule (a paraphrased \
STATEMENT plus a verbatim SUPPORTING_QUOTE copied from the judgment). Judge STRICTLY and \
only from the provided text. Return JSON with boolean fields and one short reason:
{"statement_correct": bool,   // the statement accurately reflects what the court decided
 "quote_supports": bool,      // the quote actually supports the statement (not just present)
 "is_ratio": bool,            // it is the ratio/holding, not obiter, a submission, or cited precedent
 "qualifications_ok": bool,   // no material qualification/exception is dropped
 "statute_correct": bool,     // the statute_section (if any) is the one actually construed; true if none claimed
 "usable": bool,              // overall: safe to show a lawyer as this case's rule
 "reason": "one sentence"}
Be skeptical: if the quote is a party's argument or a quotation of another case, is_ratio=false."""

USER_JUDGE = """JUDGMENT (may be truncated):
{judgment}

CANDIDATE RULE
STATEMENT: {statement}
SUPPORTING_QUOTE: {quote}
STATUTE_SECTION: {section}

Return only the JSON object."""


def cmd_judge() -> None:
    rows = [r for r in _raw_rows(stage="holdout") if r["status"] == "ok" and r.get("rule")]
    # disclosed cap: 70B endpoint latency makes judging all rows infeasible; take a
    # deterministic seeded subset. Lawyer labels (authoritative) still cover ALL rows.
    cap = CFG["stages"]["judge"].get("max_rules", len(rows))
    rows_sorted = sorted(rows, key=lambda r: hashlib.sha256((str(SEED) + r["case_id"]).encode()).hexdigest())
    judged_subset = rows_sorted[:cap]
    done = _done_keys()
    todo = [r for r in judged_subset if ("judge", "", r["case_id"]) not in done]
    print(f"judge: {len(rows)} accepted holdout rules; judging {len(judged_subset)} (cap={cap}); "
          f"{len(todo)} to score (model={JUDGE_MODEL}, PROXY only, ~110s/call at current latency)")
    for i, r in enumerate(todo, 1):
        case = next((c for c in _load_sample("sample_holdout.csv") if c["case_id"] == r["case_id"]), None)
        text = case["_text"] if case else ""
        ru = r["rule"]
        user = USER_JUDGE.format(judgment=text[:config.FULL_TEXT_MAX_CHARS],
                                 statement=ru["statement"], quote=ru["supporting_quote"],
                                 section=ru.get("statute_section") or "(none)")
        j = chat_json(SYS_JUDGE, user, JUDGE_MODEL)
        _append_raw({"stage": "judge", "arm": "", "case_id": r["case_id"],
                     "model": JUDGE_MODEL, "verdict": j})
        if i % 10 == 0:
            print(f"  {i}/{len(todo)} | http_attempts={HTTP_ATTEMPTS['count']}")
        time.sleep(config.DELAY_S)
    print(f"[done] usage={json.dumps(usage_summary())}")


# ----------------------------------------------------------------- metrics
def _raw_rows(stage: str) -> list[dict]:
    out = []
    if RAW.exists():
        for line in RAW.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
                if r.get("stage") == stage:
                    out.append(r)
            except Exception:
                pass
    return out


def _wilson_lower(k: int, n: int, z: float = 1.96) -> float:
    if n == 0:
        return 0.0
    p = k / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    return max(0.0, (centre - margin) / denom)


def cmd_metrics() -> None:
    metrics = {"code_commit": CFG["code_commit"], "go_criteria": CFG["go_criteria"], "arms": {}}
    # ---- ablation per-arm ----
    abl = _raw_rows(stage="ablation")
    by_arm: dict[str, list[dict]] = {}
    for r in abl:
        by_arm.setdefault(r["arm"], []).append(r)
    for arm in sorted(by_arm):
        rs = by_arm[arm]
        acc = [r for r in rs if r["status"] == "ok"]
        verb = [r for r in acc if r.get("match_type") == "verbatim"]
        gnd = [r for r in acc if r.get("indep_grounded")]
        cue = [r for r in rs if r.get("cue_in_window")]
        atrisk = [r for r in rs if r.get("at_risk")]
        atrisk_cue = [r for r in atrisk if r.get("cue_in_window")]
        metrics["arms"][arm] = {
            "spec": ARMS.get(arm, {}), "n": len(rs),
            "accept_rate": round(len(acc) / len(rs), 3) if rs else 0,
            "verbatim_rate": round(len(verb) / len(acc), 3) if acc else 0,
            "independent_grounding_rate": round(len(gnd) / len(acc), 3) if acc else 0,
            "cue_in_window_rate": round(len(cue) / len(rs), 3) if rs else 0,
            "at_risk_cue_recovered": f"{len(atrisk_cue)}/{len(atrisk)}",
            "abstained": sum(1 for r in rs if r["status"] == "abstained"),
            "rejected": sum(1 for r in rs if str(r["status"]).startswith("reject")),
            "llm_errors": sum(1 for r in rs if r["status"] == "llm-error"),
        }
    best_path = RUN / "best_method.json"
    metrics["best_method"] = json.loads(best_path.read_text(encoding="utf-8")) if best_path.exists() else None

    # ---- holdout + judge ----
    hold = [r for r in _raw_rows(stage="holdout")]
    acc = [r for r in hold if r["status"] == "ok" and r.get("rule")]
    judged = {r["case_id"]: r.get("verdict") for r in _raw_rows(stage="judge")}
    dims = ["statement_correct", "quote_supports", "is_ratio", "qualifications_ok",
            "statute_correct", "usable"]
    scored = [(cid, judged[cid]) for cid in (r["case_id"] for r in acc)
              if isinstance(judged.get(cid), dict)]
    judge_metrics = {"n_accepted": len(acc), "n_judged": len(scored)}
    for d in dims:
        k = sum(1 for _, v in scored if v.get(d) is True)
        n = len(scored)
        judge_metrics[d] = {"rate": round(k / n, 3) if n else None,
                            "ci95_lower": round(_wilson_lower(k, n), 3) if n else None,
                            "k": k, "n": n}
    metrics["holdout"] = {
        "n": len(hold),
        "accept_rate": round(len(acc) / len(hold), 3) if hold else 0,
        "independent_grounding_rate": round(
            sum(1 for r in acc if r.get("indep_grounded")) / len(acc), 3) if acc else 0,
        "judge_proxy": judge_metrics,
        "judge_note": CFG["stages"]["judge"]["note"],
    }
    # credits counted from frozen raw-responses.jsonl (1 row = 1 logical model attempt),
    # since USAGE/usage_summary() is per-process and this metrics pass makes no calls.
    allrows = _raw_rows("ablation") + _raw_rows("holdout") + _raw_rows("judge")
    by_model = collections.Counter(r.get("model", "?") for r in allrows)
    metrics["credits"] = {
        "total_logical_calls": sum(by_model.values()),
        "logical_calls_by_model": dict(by_model),
        "note": "Counted from raw-responses.jsonl. Billable HTTP attempts (llm_client."
                "HTTP_ATTEMPTS) were logged live per run and equal logical calls except "
                "when chat_json retried/fell back (rare here); they are not persisted per-row.",
    }

    # ---- Claude-subagent judge (STRONGER proxy than the llama-70b judge) ----
    cdir = RUN / "judge-claude"
    crows = []
    if cdir.exists():
        for pf in sorted(cdir.glob("part-*.jsonl")):
            for line in pf.read_text(encoding="utf-8").splitlines():
                try:
                    crows.append(json.loads(line))
                except Exception:
                    pass
    cj = {"n": len(crows), "model": "claude-opus-4-8 (subagent)", "authoritative": False}
    for d in dims:
        k = sum(1 for v in crows if v.get(d) is True)
        n = len(crows)
        cj[d] = {"rate": round(k / n, 3) if n else None,
                 "ci95_lower": round(_wilson_lower(k, n), 3) if n else None, "k": k, "n": n}
    metrics["holdout"]["judge_claude"] = cj

    # ---- provisional verdict (advisory; lawyer labels are authoritative) ----
    # Base the checks on the stronger Claude proxy when available, else the llama judge.
    gc = CFG["go_criteria"]
    src = cj if crows else judge_metrics
    metrics["holdout"]["provisional_judge_source"] = "judge_claude" if crows else "judge_llama"
    usable = src.get("usable", {})
    statute = src.get("statute_correct", {})
    checks = {
        "strict_quote_grounding": metrics["holdout"]["independent_grounding_rate"] >= gc["strict_quote_grounding"],
        "judge_usable>=90%": (usable.get("rate") or 0) >= gc["lawyer_legal_precision"],
        "usable_ci95_lower>=80%": (usable.get("ci95_lower") or 0) >= gc["precision_ci95_lower_bound"],
        "statute>=90%": (statute.get("rate") or 0) >= gc["statute_link_accuracy"],
    }
    metrics["provisional_verdict"] = {
        "checks": checks,
        "all_pass": all(checks.values()),
        "authoritative": False,
        "note": "PROVISIONAL — based on the LLM-judge proxy. The GO decision requires the human lawyer labels in lawyer-labels.csv.",
    }
    (RUN / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    # ---- predictions.csv (rebuilt from raw) ----
    with (RUN / "predictions.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["stage", "arm", "case_id", "citation", "model", "window_strategy",
                    "status", "match_type", "indep_grounded", "cue_in_window", "at_risk",
                    "statement", "supporting_quote", "statute_section"])
        for r in abl + hold:
            ru = r.get("rule") or {}
            w.writerow([r.get("stage"), r.get("arm"), r["case_id"], r.get("citation"),
                        r.get("model"), r.get("window_strategy"), r.get("status"),
                        r.get("match_type"), r.get("indep_grounded"), r.get("cue_in_window"),
                        r.get("at_risk"), ru.get("statement", ""),
                        ru.get("supporting_quote", ""), ru.get("statute_section", "")])

    # ---- lawyer-labels.csv (blank pack: accepted holdout rules for blind labelling) ----
    with (RUN / "lawyer-labels.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["case_id", "citation", "statement", "supporting_quote", "statute_section",
                    "statement_correct(y/n)", "quote_supports(y/n)", "is_ratio(y/n)",
                    "qualifications_ok(y/n)", "statute_correct(y/n)", "usable(y/n)", "notes"])
        for r in acc:
            ru = r["rule"]
            w.writerow([r["case_id"], r.get("citation"), ru["statement"], ru["supporting_quote"],
                        ru.get("statute_section", ""), "", "", "", "", "", "", ""])
    print(f"wrote metrics.json, predictions.csv, lawyer-labels.csv ({len(acc)} rows) -> {RUN}")
    print(json.dumps({"ablation_arms": {a: metrics['arms'][a]['accept_rate'] for a in metrics['arms']},
                      "best": metrics.get("best_method", {}).get("arm"),
                      "holdout_accept": metrics["holdout"]["accept_rate"],
                      "provisional_all_pass": metrics["provisional_verdict"]["all_pass"]}, indent=2))


def cmd_all() -> None:
    """Resumable end-to-end driver: each stage skips already-completed work."""
    for name, fn in (("ablation", cmd_ablation), ("holdout", cmd_holdout),
                     ("judge", cmd_judge), ("metrics", cmd_metrics)):
        print(f"\n===== stage: {name} =====")
        fn()


CMDS = {"sample": cmd_sample, "ablation": cmd_ablation, "holdout": cmd_holdout,
        "judge": cmd_judge, "metrics": cmd_metrics, "all": cmd_all}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=list(CMDS))
    args = ap.parse_args()
    CMDS[args.cmd]()
