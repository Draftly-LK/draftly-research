"""Fill the lawyer annotation workbook from the proposed-gold benchmark.

Takes the hand-made template workbook (four sheets: Questions, Provisions,
Claims, Missing provisions) and writes one populated copy with every
proposed-gold question, every provision the agents attached to it, and every
answer claim. Header rows, colours, dropdowns and the per-row "Review Status"
formula are carried over from the template; the row ranges are extended to
fit the data. Two read-only columns are added to Provisions (Agent Rationale,
Verifier Note) and one to Claims (Agent Verification) because the lawyer
cannot judge a provision without knowing why the agent chose it.

Nothing in the output is lawyer validated. The yellow columns are written
empty; the script never fills a lawyer field.

    uv run python scripts/statutory-qa/export_lawyer_workbook.py
    uv run python scripts/statutory-qa/export_lawyer_workbook.py --matters M001 M022 --out pilot.xlsx
    uv run python scripts/statutory-qa/export_lawyer_workbook.py --extended     # main + legal-review questions
"""

from __future__ import annotations

import argparse
import copy
import csv
import sys
from pathlib import Path

import openpyxl
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sq_common as C  # noqa: E402

TEMPLATE = C.ROOT / "data" / "evaluvation" / "Statutory_QA_Lawyer_Annotation_Pilot.xlsx"
OUT_DIR = C.REVIEW_DIR / "lawyer-workbook"
REGISTRY = C.ROOT / "data" / "legal-sources" / "manifests" / "source-registry.csv"
FIRST_DATA_ROW = 6
HEADER_ROW = 5
MISSING_ROWS_PER_QUESTION = 3

YELLOW = "FFFFF2CC"
GREY = "FFE7E6E6"
GREEN = PatternFill("solid", fgColor="FFC6EFCE")
AMBER = PatternFill("solid", fgColor="FFFFEB9C")

LABELS = {"indispensable": "Indispensable", "supporting": "Supporting", "background": "Background"}
TEMPORAL = {True: "Current on reference date", False: "Unclear", None: "Unclear"}


# --------------------------------------------------------------------------- #
# sheet specs: header -> role. "id" grey/locked, "info" read-only, "lawyer" yellow
# --------------------------------------------------------------------------- #
QUESTIONS_COLS = [
    ("Matter ID", "id"), ("Question ID", "id"), ("Reference Date", "info"),
    ("Original Question", "info"), ("Enriched Facts", "info"),
    ("Added Facts Plausible?", "lawyer"), ("Added Facts Neutral?", "lawyer"),
    ("Issues Complete?", "lawyer"), ("Statute-only?", "lawyer"), ("Other Law Needed", "lawyer"),
    ("Overall Verdict", "lawyer"), ("Reviewer ID", "lawyer"), ("Review Date", "lawyer"),
    ("Minutes Spent", "lawyer"), ("Confidence (1-5)", "lawyer"), ("Corrections / Notes", "lawyer"),
    ("Review Status", "status"),
]
PROVISIONS_COLS = [
    ("Question ID", "id"), ("Provision ID", "id"), ("Act / Instrument", "info"), ("Section / Rule", "info"),
    ("Reference Date", "info"), ("Temporal Status", "info"), ("Verbatim Excerpt", "info"), ("Source Link", "info"),
    ("Agent Proposed Label", "info"), ("Agent Rationale", "info"), ("Verifier Note", "info"),
    ("Lawyer Label", "lawyer"), ("Corrected Act / Instrument", "lawyer"), ("Corrected Section / Rule", "lawyer"),
    ("Reviewer Notes", "lawyer"), ("Reviewer ID", "lawyer"), ("Review Status", "status"),
]
CLAIMS_COLS = [
    ("Question ID", "id"), ("Claim ID", "id"), ("Draft Answer Claim", "info"), ("Linked Provision IDs", "info"),
    ("Agent Verification", "info"),
    ("Lawyer Judgment", "lawyer"), ("Corrected Claim / Notes", "lawyer"),
    ("Case Law / Common Law Required?", "lawyer"), ("Authority / Citation Needed", "lawyer"),
    ("Reviewer ID", "lawyer"), ("Review Status", "status"),
]
MISSING_COLS = [
    ("Question ID", "id"), ("Missing Provision ID", "id"), ("Act / Instrument", "lawyer"), ("Section / Rule", "lawyer"),
    ("Importance", "lawyer"), ("Why Required", "lawyer"), ("Source Link", "lawyer"), ("Reviewer ID", "lawyer"),
    ("Notes", "lawyer"), ("Review Status", "status"),
]

WIDTHS = {
    "Questions": [12, 16, 14, 60, 60, 18, 18, 17, 14, 20, 20, 16, 14, 14, 16, 42, 15],
    "Provisions": [16, 20, 30, 18, 14, 26, 60, 30, 20, 60, 50, 20, 30, 22, 38, 16, 15],
    "Claims": [16, 20, 58, 40, 50, 26, 48, 26, 38, 16, 15],
    "Missing provisions": [16, 24, 32, 18, 18, 48, 30, 16, 38, 15],
}

INSTRUCTIONS = {
    "Questions": "Complete one row per question. Yellow cells require lawyer input. Grey ID cells and the white "
                 "columns are system fields generated from the agents' legal maps; do not edit them. Read the matter "
                 "background and the enriched facts, then judge the added facts, the issue list and whether the "
                 "question is answerable from statute alone.",
    "Provisions": "Label every proposed provision. The agent's label, rationale and the verifier's note are shown "
                  "for context; your label in the yellow column is the one that counts. Use Wrong citation only "
                  "when the legal proposition may be relevant but the cited Act or section is incorrect; then "
                  "complete both corrected-citation columns.",
    "Claims": "Review each answer claim independently. If the claim needs case law or common law, mark that "
              "field even when the wording is otherwise correct.",
    "Missing provisions": "Add one row for every legally necessary provision the agents omitted. Three blank rows "
                          "are provided per question; add more rows if needed, using the question ID exactly as "
                          "shown in the other sheets.",
}

# dropdowns per sheet: header -> list
DROPDOWNS = {
    "Questions": {
        "Added Facts Plausible?": '"Yes,No,Unclear,Not applicable"',
        "Added Facts Neutral?": '"Yes,No,Unclear,Not applicable"',
        "Issues Complete?": '"Yes,No,Unclear"',
        "Statute-only?": '"Yes,No,Unclear"',
        "Other Law Needed": '"None,Case law,Common law,Regulations,Forms / practice,Multiple sources"',
        "Overall Verdict": '"Approved,Corrections required,Rejected"',
    },
    "Provisions": {
        "Temporal Status": '"Current on reference date,Repealed before reference date,Amended after reference date,Unclear"',
        "Lawyer Label": '"Indispensable,Supporting,Background,Not relevant,Wrong citation"',
    },
    "Claims": {
        "Lawyer Judgment": '"Correct,Incorrect,Misstated,Needs case law / common law,Outside my expertise"',
        "Case Law / Common Law Required?": '"Yes,No,Unclear"',
    },
    "Missing provisions": {"Importance": '"Indispensable,Supporting,Background"'},
}


def col_index(cols, header) -> int:
    return next(i for i, (h, _) in enumerate(cols) if h == header) + 1


def L(cols, header) -> str:
    return get_column_letter(col_index(cols, header))


def status_formula(sheet: str, cols, r: int) -> str:
    c = lambda h: f"{L(cols, h)}{r}"  # noqa: E731
    if sheet == "Questions":
        req = ["Added Facts Plausible?", "Added Facts Neutral?", "Issues Complete?", "Statute-only?",
               "Overall Verdict", "Reviewer ID", "Review Date", "Confidence (1-5)"]
        return f'=IF({c("Question ID")}="","",IF(AND({",".join(f"{c(h)}<>\"\"" for h in req)}),"Complete","Pending"))'
    if sheet == "Provisions":
        return (f'=IF(OR({c("Question ID")}="",{c("Provision ID")}=""),"",IF(AND({c("Lawyer Label")}<>"",{c("Reviewer ID")}<>"",'
                f'IF({c("Lawyer Label")}="Wrong citation",AND({c("Corrected Act / Instrument")}<>"",{c("Corrected Section / Rule")}<>""),TRUE)),'
                f'"Complete","Pending"))')
    if sheet == "Claims":
        return (f'=IF(OR({c("Question ID")}="",{c("Claim ID")}=""),"",IF(AND({c("Lawyer Judgment")}<>"",'
                f'{c("Case Law / Common Law Required?")}<>"",{c("Reviewer ID")}<>""),"Complete","Pending"))')
    if sheet == "Missing provisions":
        filled = ["Missing Provision ID", "Act / Instrument", "Section / Rule", "Importance", "Why Required", "Source Link", "Reviewer ID", "Notes"]
        req = ["Question ID", "Act / Instrument", "Section / Rule", "Importance", "Why Required", "Reviewer ID"]
        return (f'=IF(AND({",".join(f"{c(h)}=\"\"" for h in filled)}),"",'
                f'IF(AND({",".join(f"{c(h)}<>\"\"" for h in req)}),"Complete","Pending"))')
    raise ValueError(sheet)


# --------------------------------------------------------------------------- #
# data
# --------------------------------------------------------------------------- #
def load_sources() -> tuple[dict, dict]:
    acts = {a["act_id"]: a for a in C.read_jsonl(C.CORPUS_DIR / "acts.jsonl")}
    registry = {}
    if REGISTRY.exists():
        with REGISTRY.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                registry[row["source_id"]] = row
    return acts, registry


def source_link(act_id: str, acts: dict, registry: dict) -> str:
    a = acts.get(act_id)
    if not a:
        return ""
    src = registry.get(a.get("source_id") or "")
    if src and src.get("preferred_source_url"):
        return src["preferred_source_url"]
    return a.get("source_file", "")


def act_label(p: dict) -> str:
    title, ny = p["formal_title"], p.get("number_and_year") or ""
    return title if not ny or ny in title else f"{title} {ny}"


def cite(p: dict) -> str:
    sec = f"s.{p['section']}"
    if p.get("subsection"):
        sec += f" {p['subsection']}" if p["subsection"].startswith(("rule", "definition", "(")) else f"({p['subsection']})"
    return sec


def build_rows(gold_rows, matters, acts, registry):
    q_rows, p_rows, c_rows, m_rows = [], [], [], []
    for g in gold_rows:
        qid, mid = g["benchmark_question_id"], g["benchmark_matter_id"]
        m = matters[mid]
        src = next(q for q in m["questions"] if q["benchmark_question_id"] == qid)
        lm = C.read_json(C.MATTERS_DIR / mid / "legal-map.json")
        provs = {p["provision_id"]: p for p in lm["provisions"]}
        lq = next(q for q in lm["questions"] if q["benchmark_question_id"] == qid)
        ref = g["matter_reference_date"]

        background = m["matter_background"]["normalized"] or src.get("effective_background_normalized") or ""
        original = f"BACKGROUND\n{background}\n\nQUESTION\n{src['question_normalized']}".strip()
        enr = g["enrichment"]
        if enr.get("applied"):
            facts = "\n".join(f"- {f['fact_id']} [{f['origin']}]: {f['fact']}" for f in enr.get("added_facts", []))
            enriched = f"ENRICHED BACKGROUND\n{enr.get('enriched_background') or ''}\n\nADDED FACTS\n{facts}".strip()
        else:
            enriched = "(no enrichment; the original background is used as is)"
        issues = "\n".join(f"- {i['issue_id']}: {i['issue']}" for i in g["legal_issues"])
        q_rows.append({
            "Matter ID": mid, "Question ID": qid, "Reference Date": ref,
            "Original Question": original + f"\n\nAGENT ISSUE LIST\n{issues}\n\nAGENT AUTHORITY VIEW: {g['authority_requirement']}",
            "Enriched Facts": enriched,
        })

        for role in ("indispensable", "supporting", "background"):
            for pid in lq[f"{role}_provision_ids"]:
                p = provs[pid]
                rationale = p.get("why_relevant") or ""
                if p.get("temporal_note"):
                    rationale += f"\n\nTEMPORAL: {p['temporal_note']}"
                p_rows.append({
                    "Question ID": qid, "Provision ID": pid,
                    "Act / Instrument": act_label(p),
                    "Section / Rule": cite(p), "Reference Date": ref,
                    "Temporal Status": TEMPORAL.get(p.get("applicable_to_matter_date")),
                    "Verbatim Excerpt": p["relevant_excerpt"], "Source Link": source_link(p["act_id"], acts, registry),
                    "Agent Proposed Label": LABELS[role], "Agent Rationale": rationale,
                    "Verifier Note": f"[{p['verification_status']}] {p.get('verifier_note') or ''}".strip(),
                })

        for cl in g["answer_claims"]:
            linked = "\n".join(f"{pid}: {provs[pid]['formal_title']} {cite(provs[pid])}" for pid in cl["supporting_provision_ids"] if pid in provs)
            if cl.get("supporting_fact_ids"):
                linked += ("\n" if linked else "") + "Facts: " + ", ".join(cl["supporting_fact_ids"])
            c_rows.append({
                "Question ID": qid, "Claim ID": cl["claim_id"],
                "Draft Answer Claim": f"[{cl['claim_type']}] {cl['claim_text']}", "Linked Provision IDs": linked,
                "Agent Verification": f"[{cl['verification_status']}, support {cl['support_strength']}] {cl.get('verifier_note') or ''}".strip(),
            })

        for k in range(1, MISSING_ROWS_PER_QUESTION + 1):
            m_rows.append({"Question ID": qid, "Missing Provision ID": f"MISS-{qid}-{k:02d}"})
    return {"Questions": q_rows, "Provisions": p_rows, "Claims": c_rows, "Missing provisions": m_rows}


# --------------------------------------------------------------------------- #
# workbook
# --------------------------------------------------------------------------- #
def fill_sheet(ws, cols, rows, sheet: str) -> None:
    header_style = copy.copy(ws.cell(HEADER_ROW, 1)._style)
    sample_grey = copy.copy(ws.cell(FIRST_DATA_ROW, 1)._style)
    # locate a yellow and a plain white sample cell in the template's first data row
    yellow_style = white_style = None
    for c in ws[FIRST_DATA_ROW]:
        rgb = c.fill.fgColor.rgb if c.fill and c.fill.fill_type else None
        if rgb == YELLOW and yellow_style is None:
            yellow_style = copy.copy(c._style)
        elif rgb not in (YELLOW, GREY) and white_style is None and c.column > 2:
            white_style = copy.copy(c._style)
    yellow_style = yellow_style or sample_grey
    white_style = white_style or sample_grey

    ncols = len(cols)
    ws.delete_rows(HEADER_ROW, ws.max_row)
    ws.conditional_formatting = type(ws.conditional_formatting)()
    ws.data_validations = type(ws.data_validations)()
    for rng in list(ws.merged_cells.ranges):
        ws.unmerge_cells(str(rng))
    ws.cell(2, 1).value = f"Statutory QA Lawyer Review - {sheet}"
    ws.cell(3, 1).value = INSTRUCTIONS[sheet]
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=ncols)
    ws.merge_cells(start_row=3, start_column=1, end_row=3, end_column=ncols)
    ws.cell(3, 1).alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[3].height = 48

    for i, (h, _) in enumerate(cols, start=1):
        cell = ws.cell(HEADER_ROW, i, h)
        cell._style = copy.copy(header_style)
        ws.column_dimensions[get_column_letter(i)].width = WIDTHS[sheet][i - 1]

    last = FIRST_DATA_ROW + max(len(rows), 1) - 1
    for r_off, row in enumerate(rows):
        r = FIRST_DATA_ROW + r_off
        for i, (h, role) in enumerate(cols, start=1):
            cell = ws.cell(r, i)
            if role == "status":
                cell.value = status_formula(sheet, cols, r)
                cell._style = copy.copy(white_style)
            else:
                cell.value = row.get(h)
                cell._style = copy.copy({"id": sample_grey, "info": white_style, "lawyer": yellow_style}[role])
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    for h, options in DROPDOWNS[sheet].items():
        dv = DataValidation(type="list", formula1=options, allow_blank=True)
        dv.add(f"{L(cols, h)}{FIRST_DATA_ROW}:{L(cols, h)}{last}")
        ws.add_data_validation(dv)
    if sheet == "Questions":
        for h, lo, hi in (("Minutes Spent", 0, 1440), ("Confidence (1-5)", 1, 5)):
            dv = DataValidation(type="whole", operator="between", formula1=str(lo), formula2=str(hi), allow_blank=True)
            dv.add(f"{L(cols, h)}{FIRST_DATA_ROW}:{L(cols, h)}{last}")
            ws.add_data_validation(dv)

    st = f"{L(cols, 'Review Status')}{FIRST_DATA_ROW}:{L(cols, 'Review Status')}{last}"
    ws.conditional_formatting.add(st, CellIsRule(operator="equal", formula=['"Complete"'], fill=GREEN))
    ws.conditional_formatting.add(st, CellIsRule(operator="equal", formula=['"Pending"'], fill=AMBER))
    ws.freeze_panes = f"C{FIRST_DATA_ROW}"
    ws.auto_filter.ref = f"A{HEADER_ROW}:{get_column_letter(ncols)}{last}"


# --------------------------------------------------------------------------- #
# flat layout: one sheet; each question is a block of rows so every text is visible
# --------------------------------------------------------------------------- #
FLAT_COLS = ["Matter", "Matter background",
             "Question", "Is the question OK?",
             "Draft answer", "Is the answer correct?",
             "Provisions", "Is this provision correct?", "Comment on this provision",
             "Are the provisions correct overall?",
             "Your overall notes", "Your name", "Date", "Status",
             "Added facts (for reference)"]
FLAT_WIDTHS = [10, 60, 50, 24, 80, 24, 90, 24, 40, 26, 45, 16, 14, 12, 70]
ANSWER_PARTS = (("conclusion", "ANSWER"), ("rule", "THE LAW"), ("application", "HOW IT APPLIES HERE"))
# block-level dropdowns (one per question, merged down the block)
BLOCK_DROPDOWNS = {
    "Is the question OK?": '"Yes - question is fine,Facts need fixing,Needs case law,Reject this question"',
    "Is the answer correct?": '"Yes - correct,Partly wrong,Wrong,Needs case law"',
    "Are the provisions correct overall?": '"Yes - all correct,Some are wrong,Some are missing,Wrong and missing"',
}
# per-provision dropdown (one per provision row)
PROV_DROPDOWN = '"Yes - correct,Not needed,Wrong section,Not sure"'
BLOCK_LAWYER_COLS = tuple(BLOCK_DROPDOWNS) + ("Your overall notes", "Your name", "Date")
LINE_PT = 15.0          # Calibri 11 line height in points
CHARS_PER_WIDTH = 1.15  # average characters that fit per Excel width unit
MAX_ROW_PT = 409.0      # Excel hard limit on row height
LAWYER_ROW_PT = 48.0


def text_height(text: str | None, width: float) -> float:
    """Points needed to show `text` wrapped in a column of `width` units."""
    if not text:
        return LINE_PT
    per_line = max(int(width * CHARS_PER_WIDTH), 8)
    lines = 0
    for para in str(text).split("\n"):
        lines += max(1, -(-len(para) // per_line))
    return lines * LINE_PT + 6


def flat_rows(gold_rows, matters, acts, registry):
    """Return matter blocks: (mid, background, [question dicts]).

    Each question dict has `question` (list of text chunks), `answer` (list of
    four chunks) and `provisions` (list, one string per provision); each list
    item becomes its own spreadsheet row so nothing is hidden inside a cell.
    """
    blocks = []
    for g in gold_rows:
        qid, mid = g["benchmark_question_id"], g["benchmark_matter_id"]
        m = matters[mid]
        src = next(q for q in m["questions"] if q["benchmark_question_id"] == qid)
        lm = C.read_json(C.MATTERS_DIR / mid / "legal-map.json")
        provs = {p["provision_id"]: p for p in lm["provisions"]}
        lq = next(q for q in lm["questions"] if q["benchmark_question_id"] == qid)

        question = [f"{qid}\n\n{src['question_normalized']}"]
        enr = g["enrichment"]
        enriched = bool(enr.get("applied") and enr.get("enriched_background"))
        added_facts = ""
        if enriched:
            tag = {"synthetic_decisive": "changes the answer", "synthetic_neutral": "detail only"}
            added_facts = "Facts added to the exam scenario so it has one clear answer:\n\n" + "\n\n".join(
                f"- {f['fact']}\n  ({tag.get(f['origin'], f['origin'])})" for f in enr.get("added_facts", []))

        ans = g["gold_answer_draft"]
        answer = [f"{label}\n{ans[key]}" for key, label in ANSWER_PARTS]

        provisions = []
        for role in ("indispensable", "supporting", "background"):
            for pid in lq[f"{role}_provision_ids"]:
                p = provs[pid]
                note = f"\nVerifier: {p['verifier_note']}" if p.get("verifier_note") else ""
                provisions.append(
                    f"{LABELS[role].upper()}  {pid}\n{act_label(p)} {cite(p)}  [{p['verification_status']}]\n"
                    f"\"{p['relevant_excerpt']}\"\nWhy: {p.get('why_relevant') or ''}{note}\n{source_link(p['act_id'], acts, registry)}")

        if enriched:
            background = enr["enriched_background"]
        else:
            background = m["matter_background"]["normalized"] or src.get("effective_background_normalized") or ""
        background = f"{m['exam_session']} (law as at {g['matter_reference_date']})\n\n{background}"
        w = dict(zip(FLAT_COLS, FLAT_WIDTHS))
        qd = {"background": background, "added_facts": added_facts,
              "question": split_to_fit(question, w["Question"]),
              "answer": split_to_fit(answer, w["Draft answer"]),
              "provisions": split_to_fit(provisions, w["Provisions"])}
        if blocks and blocks[-1][0] == mid:
            blocks[-1][2].append(qd)
        else:
            blocks.append((mid, background, [qd]))
    return blocks


def split_to_fit(chunks: list[str], width: float) -> list[str]:
    """Break any chunk taller than Excel's row limit into pieces at paragraph, then sentence, boundaries."""
    import re

    out = []
    for text in chunks:
        if text_height(text, width) <= MAX_ROW_PT:
            out.append(text)
            continue
        units = [u for para in text.split("\n") for u in (re.split(r"(?<=[.;:])\s+", para) or [para])]
        cur = ""
        for u in units:
            cand = f"{cur}\n{u}" if cur else u
            if cur and text_height(cand, width) > MAX_ROW_PT:
                out.append(cur)
                cur = "(cont.) " + u
            else:
                cur = cand
        if cur:
            out.append(cur)
    return out


def _distribute(ws, rows: list[int], needed: float) -> None:
    """Grow rows (evenly) until their total height covers `needed` points."""
    total = sum(ws.row_dimensions[r].height or LINE_PT for r in rows)
    if total >= needed:
        return
    extra = (needed - total) / len(rows)
    for r in rows:
        ws.row_dimensions[r].height = min(MAX_ROW_PT, (ws.row_dimensions[r].height or LINE_PT) + extra)


def write_flat(blocks, out: Path) -> dict:
    from openpyxl.styles import Border, Font, Side

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Review"
    header_fill = PatternFill("solid", fgColor="FF17365D")
    yellow = PatternFill("solid", fgColor=YELLOW)
    grey = PatternFill("solid", fgColor=GREY)
    thin = Side(style="thin", color="FFBFBFBF")
    thick = Side(style="medium", color="FF17365D")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    top = Alignment(wrap_text=True, vertical="top")
    col = {h: i + 1 for i, h in enumerate(FLAT_COLS)}
    width = {h: FLAT_WIDTHS[i] for i, h in enumerate(FLAT_COLS)}

    ws["A1"] = "Statutory QA lawyer review"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = ("HOW TO REVIEW\n"
                "1. Read the matter background and the question. Choose an answer in the yellow \"Is the question OK?\" cell. "
                "Where the exam scenario was too thin, the background shown is the fuller version; the facts we added are listed in the last column.\n"
                "2. Read the draft answer (the answer first, then the law, then how it applies). Choose an answer in the yellow \"Is the answer correct?\" cell.\n"
                "3. For EACH provision row, choose an answer in the yellow \"Is this provision correct?\" cell. "
                "Add a comment beside it if you like.\n"
                "4. Choose an answer in \"Are the provisions correct overall?\". If anything is missing, name it in \"Your overall notes\".\n"
                "5. Put your name and the date.\n"
                "Only yellow cells need input. White and grey cells are for reading only. "
                "The Status cell turns green when the question is done.")
    ws["A2"].alignment = top
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=len(FLAT_COLS))
    ws.row_dimensions[2].height = 130
    for i, h in enumerate(FLAT_COLS, start=1):
        c = ws.cell(4, i, h)
        c.fill, c.font, c.border = header_fill, Font(bold=True, color="FFFFFFFF"), border
        c.alignment = Alignment(wrap_text=True, vertical="center")
        ws.column_dimensions[get_column_letter(i)].width = FLAT_WIDTHS[i - 1]

    PV, PC = "Is this provision correct?", "Comment on this provision"
    r = 5
    n_q = 0
    block_cells: dict[str, list[str]] = {h: [] for h in BLOCK_DROPDOWNS}
    prov_cells = []
    for mid, background, qs in blocks:
        m_start = r
        for q in qs:
            n_q += 1
            n = max(len(q["question"]), len(q["answer"]), len(q["provisions"]))
            agent_rows = list(range(r, r + n))
            end = r + n - 1
            for rr in agent_rows:
                for h, ci in col.items():
                    c = ws.cell(rr, ci)
                    c.alignment, c.border = top, border
                    if h in (PV, PC, "Status"):
                        c.fill = grey
                ws.row_dimensions[rr].height = LINE_PT
            for h, items in (("Question", q["question"]), ("Draft answer", q["answer"]), ("Provisions", q["provisions"])):
                for k, text in enumerate(items):
                    ws.cell(r + k, col[h], text)
                    need = min(MAX_ROW_PT, text_height(text, width[h]))
                    ws.row_dimensions[r + k].height = max(ws.row_dimensions[r + k].height, need)
                if len(items) < n:
                    ws.merge_cells(start_row=r + len(items) - 1, start_column=col[h], end_row=r + n - 1, end_column=col[h])
                    _distribute(ws, list(range(r + len(items) - 1, r + n)), text_height(items[-1], width[h]))
            # one yellow dropdown + comment per provision; a split "(cont.)" chunk shares its provision's cells
            groups: list[list[int]] = []
            for k, text in enumerate(q["provisions"]):
                if text.startswith("(cont.)") and groups:
                    groups[-1].append(r + k)
                else:
                    groups.append([r + k])
            if groups and n > len(q["provisions"]):
                groups[-1].extend(range(r + len(q["provisions"]), r + n))
            for rows in groups:
                for h in (PV, PC):
                    ws.cell(rows[0], col[h]).fill = yellow
                    if len(rows) > 1:
                        ws.merge_cells(start_row=rows[0], start_column=col[h], end_row=rows[-1], end_column=col[h])
                prov_cells.append(f"{get_column_letter(col[PV])}{rows[0]}")
            n_prov = len(groups)
            # per-question read-only cells merged down the block: background (enriched if any) and added facts
            for h, val in (("Matter background", q["background"]), ("Added facts (for reference)", q["added_facts"])):
                c = ws.cell(r, col[h], val or None)
                c.fill, c.alignment = grey, top
                if end > r:
                    ws.merge_cells(start_row=r, start_column=col[h], end_row=end, end_column=col[h])
                if val:
                    _distribute(ws, list(range(r, end + 1)), text_height(val, width[h]))
            # block-level lawyer cells: yellow, merged down the whole question block
            for h in BLOCK_LAWYER_COLS + ("Status",):
                c = ws.cell(r, col[h])
                c.fill = yellow if h != "Status" else grey
                c.alignment = Alignment(wrap_text=True, vertical="center" if h != "Your overall notes" else "top")
                if end > r:
                    ws.merge_cells(start_row=r, start_column=col[h], end_row=end, end_column=col[h])
                if h in BLOCK_DROPDOWNS:
                    block_cells[h].append(f"{get_column_letter(col[h])}{r}")
            L_ = {k: get_column_letter(col[k]) for k in FLAT_COLS}
            ws.cell(r, col["Status"]).value = (
                f'=IF(AND({L_["Is the question OK?"]}{r}<>"",{L_["Is the answer correct?"]}{r}<>"",'
                f'{L_["Are the provisions correct overall?"]}{r}<>"",{L_["Your name"]}{r}<>"",'
                f'COUNTA({L_[PV]}{r}:{L_[PV]}{end})>={n_prov}),"Complete","Pending")')
            for ci in range(1, len(FLAT_COLS) + 1):
                c = ws.cell(end, ci)
                c.border = Border(left=thin, right=thin, top=c.border.top, bottom=thick)
            r = end + 1
        m_end = r - 1
        c = ws.cell(m_start, col["Matter"], mid)
        c.fill, c.alignment, c.font = grey, top, Font(bold=True)
        if m_end > m_start:
            ws.merge_cells(start_row=m_start, start_column=col["Matter"], end_row=m_end, end_column=col["Matter"])
    last = r - 1

    for options, refs in [(PROV_DROPDOWN, prov_cells)] + [(BLOCK_DROPDOWNS[h], block_cells[h]) for h in BLOCK_DROPDOWNS]:
        dv = DataValidation(type="list", formula1=options, allow_blank=True, showDropDown=False)
        dv.error, dv.errorTitle = "Please pick one of the options from the list.", "Choose from the list"
        for ref in refs:
            dv.add(ref)
        ws.add_data_validation(dv)
    st = get_column_letter(col["Status"])
    ws.conditional_formatting.add(f"{st}5:{st}{last}", CellIsRule(operator="equal", formula=['"Complete"'], fill=GREEN))
    ws.conditional_formatting.add(f"{st}5:{st}{last}", CellIsRule(operator="equal", formula=['"Pending"'], fill=AMBER))
    ws.freeze_panes = "C5"
    ws.sheet_view.zoomScale = 90
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    return {"out": C.rel(out), "matters": len(blocks), "questions": n_q, "provisions": len(prov_cells), "rows": last}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--template", type=Path, default=TEMPLATE)
    ap.add_argument("--out", type=Path, default=None, help="output .xlsx (default review/lawyer-workbook/statutory-qa-v1-lawyer-review[-pilot|-extended].xlsx)")
    ap.add_argument("--matters", nargs="*", default=None, help="restrict to these matter IDs (e.g. M001 M022)")
    ap.add_argument("--extended", action="store_true", help="use private-gold-extended.jsonl (main + legal-review questions)")
    ap.add_argument("--flat", action="store_true", help="one sheet: Matter | Background | Question | Answer | Provisions, two rows per question (agent row + lawyer row)")
    args = ap.parse_args(argv)

    gold_file = C.BENCHMARK_DIR / ("private-gold-extended.jsonl" if args.extended else "private-gold.jsonl")
    gold = C.read_jsonl(gold_file)
    if args.matters:
        keep = set(args.matters)
        gold = [g for g in gold if g["benchmark_matter_id"] in keep]
        missing = keep - {g["benchmark_matter_id"] for g in gold}
        if missing:
            print(f"warning: no gold questions for {sorted(missing)}", file=sys.stderr)
    gold.sort(key=lambda g: (g["benchmark_matter_id"], g["benchmark_question_id"]))

    matters = {m["benchmark_matter_id"]: m for m in C.read_jsonl(C.CANDIDATES_DIR / "matters.jsonl")}
    acts, registry = load_sources()
    if args.flat:
        if args.out is None:
            suffix = "-pilot" if args.matters else ("-extended" if args.extended else "")
            args.out = OUT_DIR / f"statutory-qa-v1-lawyer-review-flat{suffix}.xlsx"
        print(write_flat(flat_rows(gold, matters, acts, registry), args.out))
        return 0
    data = build_rows(gold, matters, acts, registry)

    wb = openpyxl.load_workbook(args.template)
    for sheet, cols in (("Questions", QUESTIONS_COLS), ("Provisions", PROVISIONS_COLS),
                        ("Claims", CLAIMS_COLS), ("Missing provisions", MISSING_COLS)):
        fill_sheet(wb[sheet], cols, data[sheet], sheet)

    if args.out is None:
        suffix = "-pilot" if args.matters else ("-extended" if args.extended else "")
        args.out = OUT_DIR / f"statutory-qa-v1-lawyer-review{suffix}.xlsx"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(args.out)
    counts = {k: len(v) for k, v in data.items()}
    print({"out": C.rel(args.out), "gold_file": gold_file.name, "questions": counts["Questions"],
           "matters": len({g["benchmark_matter_id"] for g in gold}), "provisions": counts["Provisions"],
           "claims": counts["Claims"], "missing_rows": counts["Missing provisions"]})
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
