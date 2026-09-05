# Paper 1 Evaluation Scripts

Complete workflow for reviewing and filling worksheet.csv for Paper 1 (34 rows).

## Quick Start

```bash
cd scripts/paper-eval/paper01
python run_all.py
```

This will:
1. Extract all sections from statute.jsonl for acts used in Paper 1
2. Create fill-in templates for Phase 2, 3, 4
3. Validate node_ids exist
4. Output instructions for filling worksheet

## Scripts

### `00_extract_sections.py`
Extract all sections from statute.jsonl that appear in Paper 1 questions.

**Use this to:** See what sections are available in each act

```bash
python 00_extract_sections.py
```

**Output:** Lists all sections for:
- Land Restriction Act (38-2014) — for q1/iii
- Registration of Title Act (21-1998) — for q6/i-iv
- Apartment Ownership Law (11-1973) — for q8/i-iii
- Wills Ordinance (21-1844) — for q9/ii

---

### `01_phase2_template.py`
Create the fill-in template for Phase 2 rows (9 straightforward A rows).

**Use this to:** Get a guided template showing exactly what to fill for each row

```bash
python 01_phase2_template.py
```

**Output:** For each of the 9 rows, shows:
- Question text
- Act sections available
- Which sections you should pick
- Template to copy-paste into worksheet

---

### `02_validate_nodeids.py`
Verify that node_ids you choose actually exist in statute.jsonl.

**Use this to:** Check before filling worksheet (catches typos)

```bash
python 02_validate_nodeids.py
```

**Input:** Reads your answers from a temp file
**Output:** "✓ All node_ids valid" or "✗ These don't exist: [list]"

---

### `03_phase3_quick.py`
Quick template for Phase 3 (9 B rows — evidence absent).

**Use this to:** See exactly what to write for missing statutes

```bash
python 03_phase3_quick.py
```

**Output:** Pre-filled template for all 9 B rows

---

### `04_phase4_quick.py`
Quick template for Phase 4 (8 C rows — not retrieval).

**Use this to:** Confirm C rows and add verification

```bash
python 04_phase4_quick.py
```

**Output:** Pre-filled template for all 8 C rows

---

### `run_all.py`
Master script that runs steps 1-4 in sequence.

```bash
python run_all.py
```

---

## Workflow

### Step 1: Extract Sections
```bash
python 00_extract_sections.py > phase2_sections.txt
```

**Read the output.** For each act (38-2014, 21-1998, 11-1973, 21-1844), you'll see all available sections with headings and snippets.

---

### Step 2: Decide Which Sections Answer Each Question

For each Phase 2 row, think:
- "Which of these sections DIRECTLY answer this question?"
- Don't pick sections that just mention the topic — pick ones that STATE THE RULE

**Example:**
```
Q6/I: "What class of title would Kamal be eligible?" (has prescriptive rights)

Available sections:
  21-1998/section-4     | Classes of Title
  21-1998/section-7     | Possessory Title

Answer: section-4 (explains what classes exist) + section-7 (prescriptive = possessory)
Copy: 21-1998/section-4; 21-1998/section-7
```

---

### Step 3: Fill Worksheet

For each row in worksheet.csv, fill:
- **bucket:** A (Phase 2), B (Phase 3), or C (Phase 4)
- **gold_provisions:** The node_ids you picked (semicolon-separated)
- **citations:** Human-readable reference
- **verified_by:** Your name
- **verified_date:** Today's date

---

### Step 4: Validate

```bash
python 02_validate_nodeids.py
```

**If all valid:** Move to Step 5
**If errors:** Fix typos in worksheet and re-run

---

### Step 5: Build & Score

```bash
cd ../../../  # Go back to Draftly root
uv run python experiments/HiREC-inspired-retrieval/pastpaper_triage.py build
uv run python experiments/HiREC-inspired-retrieval/validate_dataset.py --questions ... --gold ...
uv run python experiments/HiREC-inspired-retrieval/run_hierarchy_ceiling.py --questions ... --run-name pastpaper-r0-k20
uv run python experiments/HiREC-inspired-retrieval/hirec_evaluate.py --run-name pastpaper-r0-k20 --gold ...
```

---

## Time Estimate

- Extract + review sections: 10 min
- Phase 2 (9 rows, find sections): 1 hour 30 min
- Phase 3 (9 rows, note missing): 15 min
- Phase 4 (8 rows, confirm): 5 min
- Validate + build + score: 10 min

**Total: ~2 hours 30 min for Paper 1**

---

## If You Get Stuck

1. **"I can't find the right sections"**
   → Run `python 00_extract_sections.py` again
   → Read the section HEADINGS and TEXT more carefully
   → If still unsure, mark row as `notes: UNSURE`

2. **"Which sections should I pick?"**
   → Pick ones that STATE THE RULE for this question
   → If multiple sections could fit, pick ALL that apply
   → Precision is OK (prefer 1 right section over 5 maybes)

3. **"Node_id says section-7 but I only see section-6 and section-8"**
   → That section might not be in statute.jsonl
   → Run `python 02_validate_nodeids.py` to check
   → If missing, mark row as `notes: UNSURE`

---

## Output Files

After running scripts, you'll have:
- `phase2_sections.txt` — All available sections for Phase 2 acts
- `phase2_template.txt` — Fill-in template for Phase 2
- `phase3_template.txt` — Pre-filled template for Phase 3
- `phase4_template.txt` — Pre-filled template for Phase 4
- `worksheet_filled_template.csv` — Template to copy into worksheet.csv

---# Paper 1 Evaluation Scripts

Complete workflow for reviewing and filling worksheet.csv for Paper 1 (34 rows).

## Quick Start

```bash
cd scripts/paper-eval/paper01
python run_all.py
```

This will:
1. Extract all sections from statute.jsonl for acts used in Paper 1
2. Create fill-in templates for Phase 2, 3, 4
3. Validate node_ids exist
4. Output instructions for filling worksheet

## Scripts

### `00_extract_sections.py`
Extract all sections from statute.jsonl that appear in Paper 1 questions.

**Use this to:** See what sections are available in each act

```bash
python 00_extract_sections.py
```

**Output:** Lists all sections for:
- Land Restriction Act (38-2014) — for q1/iii
- Registration of Title Act (21-1998) — for q6/i-iv
- Apartment Ownership Law (11-1973) — for q8/i-iii
- Wills Ordinance (21-1844) — for q9/ii

---

### `01_phase2_template.py`
Create the fill-in template for Phase 2 rows (9 straightforward A rows).

**Use this to:** Get a guided template showing exactly what to fill for each row

```bash
python 01_phase2_template.py
```

**Output:** For each of the 9 rows, shows:
- Question text
- Act sections available
- Which sections you should pick
- Template to copy-paste into worksheet

---

### `02_validate_nodeids.py`
Verify that node_ids you choose actually exist in statute.jsonl.

**Use this to:** Check before filling worksheet (catches typos)

```bash
python 02_validate_nodeids.py
```

**Input:** Reads your answers from a temp file
**Output:** "✓ All node_ids valid" or "✗ These don't exist: [list]"

---

### `03_phase3_quick.py`
Quick template for Phase 3 (9 B rows — evidence absent).

**Use this to:** See exactly what to write for missing statutes

```bash
python 03_phase3_quick.py
```

**Output:** Pre-filled template for all 9 B rows

---

### `04_phase4_quick.py`
Quick template for Phase 4 (8 C rows — not retrieval).

**Use this to:** Confirm C rows and add verification

```bash
python 04_phase4_quick.py
```

**Output:** Pre-filled template for all 8 C rows

---

### `run_all.py`
Master script that runs steps 1-4 in sequence.

```bash
python run_all.py
```

---

## Workflow

### Step 1: Extract Sections
```bash
python 00_extract_sections.py > phase2_sections.txt
```

**Read the output.** For each act (38-2014, 21-1998, 11-1973, 21-1844), you'll see all available sections with headings and snippets.

---

### Step 2: Decide Which Sections Answer Each Question

For each Phase 2 row, think:
- "Which of these sections DIRECTLY answer this question?"
- Don't pick sections that just mention the topic — pick ones that STATE THE RULE

**Example:**
```
Q6/I: "What class of title would Kamal be eligible?" (has prescriptive rights)

Available sections:
  21-1998/section-4     | Classes of Title
  21-1998/section-7     | Possessory Title

Answer: section-4 (explains what classes exist) + section-7 (prescriptive = possessory)
Copy: 21-1998/section-4; 21-1998/section-7
```

---

### Step 3: Fill Worksheet

For each row in worksheet.csv, fill:
- **bucket:** A (Phase 2), B (Phase 3), or C (Phase 4)
- **gold_provisions:** The node_ids you picked (semicolon-separated)
- **citations:** Human-readable reference
- **verified_by:** Your name
- **verified_date:** Today's date

---

### Step 4: Validate

```bash
python 02_validate_nodeids.py
```

**If all valid:** Move to Step 5
**If errors:** Fix typos in worksheet and re-run

---

### Step 5: Build & Score

```bash
cd ../../../  # Go back to Draftly root
uv run python experiments/HiREC-inspired-retrieval/pastpaper_triage.py build
uv run python experiments/HiREC-inspired-retrieval/validate_dataset.py --questions ... --gold ...
uv run python experiments/HiREC-inspired-retrieval/run_hierarchy_ceiling.py --questions ... --run-name pastpaper-r0-k20
uv run python experiments/HiREC-inspired-retrieval/hirec_evaluate.py --run-name pastpaper-r0-k20 --gold ...
```

---

## Time Estimate

- Extract + review sections: 10 min
- Phase 2 (9 rows, find sections): 1 hour 30 min
- Phase 3 (9 rows, note missing): 15 min
- Phase 4 (8 rows, confirm): 5 min
- Validate + build + score: 10 min

**Total: ~2 hours 30 min for Paper 1**

---

## If You Get Stuck

1. **"I can't find the right sections"**
   → Run `python 00_extract_sections.py` again
   → Read the section HEADINGS and TEXT more carefully
   → If still unsure, mark row as `notes: UNSURE`

2. **"Which sections should I pick?"**
   → Pick ones that STATE THE RULE for this question
   → If multiple sections could fit, pick ALL that apply
   → Precision is OK (prefer 1 right section over 5 maybes)

3. **"Node_id says section-7 but I only see section-6 and section-8"**
   → That section might not be in statute.jsonl
   → Run `python 02_validate_nodeids.py` to check
   → If missing, mark row as `notes: UNSURE`

---

## Output Files

After running scripts, you'll have:
- `phase2_sections.txt` — All available sections for Phase 2 acts
- `phase2_template.txt` — Fill-in template for Phase 2
- `phase3_template.txt` — Pre-filled template for Phase 3
- `phase4_template.txt` — Pre-filled template for Phase 4
- `worksheet_filled_template.csv` — Template to copy into worksheet.csv

---