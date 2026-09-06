# Paper 1 Evaluation Scripts - Index

Location: `Draftly/scripts/paper-eval/paper01/`

## Quick Start

```bash
cd scripts/paper-eval/paper01
python run_all.py
```

This runs all scripts below in the correct order.

---

## Scripts

### 📋 `README.md`
Full documentation of the workflow, time estimates, and instructions.

**Read this first!**

---

### 🔍 `00_extract_sections.py`
**Purpose:** Extract all relevant sections from statute.jsonl for Phase 2 acts.

**When to run:** First step
```bash
python 00_extract_sections.py
```

**Output:** Prints all sections from:
- Land Restriction Act (38-2014)
- Registration of Title Act (21-1998)
- Apartment Ownership Law (11-1973)
- Wills Ordinance (21-1844)

**What you do:** Read the output, identify which sections answer each question.

---

### 📝 `01_phase2_template.py`
**Purpose:** Create a fill-in template for Phase 2 (9 straightforward A rows).

**When to run:** After 00_extract_sections.py, when you've read the sections.

```bash
python 01_phase2_template.py
```

**Output:**
- Prints template to console
- Saves to `PHASE2_TEMPLATE.txt`

**What you do:** For each row, decide which node_ids to pick and enter when prompted.

---

### ✅ `02_validate_nodeids.py`
**Purpose:** Verify that node_ids you chose actually exist in statute.jsonl.

**When to run:** After filling Phase 2 rows in worksheet.csv.

```bash
python 02_validate_nodeids.py
```

**Interactive:** Prompts you to enter node_ids for each Phase 2 row.

**Output:**
- ✓ All valid → ready to build
- ✗ Some invalid → fix and re-run

---

### 📋 `03_phase3_template.py`
**Purpose:** Generate template for Phase 3 (9 B rows - evidence absent).

**When to run:** While filling worksheet rows for Phase 3.

```bash
python 03_phase3_template.py
```

**Output:** For each B row, shows:
- Question
- Missing statute
- What to fill in worksheet

**What you do:** Copy-paste the template entries into worksheet.csv.

---

### 📋 `04_phase4_template.py`
**Purpose:** Generate template for Phase 4 (8 C rows - not retrieval).

**When to run:** While confirming C rows.

```bash
python 04_phase4_template.py
```

**Output:** For each C row, shows:
- Question
- Why it's not retrieval
- What to fill in worksheet

**What you do:** Review, confirm, add verified_by and verified_date.

---

### 🚀 `run_all.py`
**Purpose:** Master script that runs all scripts above in sequence.

**When to run:** First time, to see entire workflow.

```bash
python run_all.py
```

**Output:** Runs 00, 01, 03, 04 in order, then prompts next steps.

---

## Workflow Summary

```
START
  ↓
00_extract_sections.py
  ↓ [Read output, decide which sections]
  ↓
01_phase2_template.py → [Prints template]
  ↓ [Fill worksheet for Phase 2]
  ↓
02_validate_nodeids.py → [Checks your entries]
  ↓ [If valid: continue; if invalid: fix]
  ↓
03_phase3_template.py → [Prints Phase 3 template]
  ↓ [Fill worksheet for Phase 3]
  ↓
04_phase4_template.py → [Prints Phase 4 template]
  ↓ [Confirm Phase 4 rows]
  ↓
WORKSHEET COMPLETE (34 rows filled)
  ↓
cd ../../.. (go to Draftly root)
  ↓
uv run python pastpaper_triage.py build
  ↓
uv run python validate_dataset.py ...
  ↓
uv run python run_hierarchy_ceiling.py ...
  ↓
uv run python hirec_evaluate.py ...
  ↓
END (Paper 1 scored)
```

---

## Time Estimate

| Step | Time | Script |
|------|------|--------|
| Extract sections | 5 min | 00_extract_sections.py |
| Review + decide Phase 2 | 30 min | (manual) |
| Find Phase 2 sections | 30 min | (manual in statute.jsonl) |
| Create Phase 2 template | 5 min | 01_phase2_template.py |
| Fill worksheet Phase 2 | 30 min | (manual in Excel) |
| Validate Phase 2 | 5 min | 02_validate_nodeids.py |
| Fill worksheet Phase 3 | 15 min | 03_phase3_template.py |
| Fill worksheet Phase 4 | 10 min | 04_phase4_template.py |
| Build + validate | 10 min | (uv run commands) |
| Score | 5 min | (uv run commands) |
| **TOTAL** | **2.5 hrs** | |

---

## File Outputs

After running scripts, you'll have:

```
scripts/paper-eval/paper01/
├── README.md                          (this file)
├── INDEX.md                           (this index)
├── PHASE2_TEMPLATE.txt                (from 01_phase2_template.py)
├── .phase2_results.json               (temp from 02_validate_nodeids.py)
├── 00_extract_sections.py
├── 01_phase2_template.py
├── 02_validate_nodeids.py
├── 03_phase3_template.py
├── 04_phase4_template.py
└── run_all.py
```

---

## Troubleshooting

### "Script won't run"
Make sure you're in the right directory:
```bash
cd c:\Users\ASUS\Desktop\DSEP\Draftly\scripts\paper-eval\paper01
python 00_extract_sections.py
```

### "Can't find statute.jsonl"
Script looks for it at:
```
Draftly/experiments/koblex-inspired-retrieval/data/statute.jsonl
```

If you moved it, edit the path in each script (line ~10):
```python
STATUTE_FILE = DRAFTLY_ROOT / "path/to/statute.jsonl"
```

### "Node_id validation keeps failing"
Double-check:
1. Are you copying (not typing) node_ids?
2. Is the format correct? `act-id/section-N` (e.g., `21-1998/section-7`)
3. Run `00_extract_sections.py` again to see all valid IDs

---

## Next Steps

After Paper 1 is complete (all 34 rows filled + scored):

1. Copy this entire `paper01/` directory to `paper02/`
2. Update references in scripts (change act_ids, question formats)
3. Repeat workflow for Papers 2-16

Or: Ask for a `paper-batch/` script that automates this for all 16 papers.

---