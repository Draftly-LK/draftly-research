# Claude-Assisted Verification Workflow

**For Papers 2-16 (Paper 1 done manually)**

Reduces verification time from **30 min/paper to 5 min/paper**.

---

## How It Works

### **3-Step Process Per Paper**

```
Step 1: Claude reads question + statute sections → "Yes/No/Partial"
Step 2: You review Claude's suggestions (5 min)
Step 3: Auto-fill worksheet.csv
```

---

## Setup (One Time)

### **Install Dependencies**

```bash
cd c:\Users\ASUS\Desktop\DSEP\Draftly
pip install anthropic
```

### **Set API Key**

```powershell
$env:ANTHROPIC_API_KEY = "your-api-key-here"
```

---

## Workflow: Single Paper

### **Paper 2 (as example)**

```powershell
cd c:\Users\ASUS\Desktop\DSEP\Draftly\scripts\paper-eval

# Step 1: Claude verifies sections
python claude_verify.py --paper 2
```

**What happens:**
- Claude reads all questions from Paper 2
- For each question, Claude reads candidate statute sections
- Claude says: "Yes this answers it" / "No" / "Partial"
- Presents results to you

**Example output:**
```
Question: q6/i
"What class of title would Kamal be eligible?"

Claude's Analysis:
---
✓ YES: 21-1998/section-14/paragraph-b
  Heading: Second Class Title — Possessory Title
  Reason: Directly defines possessory title for prescription cases

✗ NO: 21-1998/section-12/subsection-3
  Heading: Application for registration
  Reason: Procedural, doesn't define title classes

Summary:
✓ YES sections: 21-1998/section-14/paragraph-b
⚠ PARTIAL sections: 21-1998/section-45/subsection-1
```

### **Step 2: Review + Confirm**

Claude asks:
```
Accept Claude's suggestion? (yes/partial/no/manual): 
```

**Options:**
- **yes** → Accept YES + PARTIAL sections
- **partial** → Accept only YES sections
- **no** → Enter your own node_ids
- **manual** → Enter node_ids manually

**Example:**
```
Accept Claude's suggestion? (yes/partial/no/manual): yes
✓ Confirmed: auto
  Node_ids: 21-1998/section-14/paragraph-b; 21-1998/section-45/subsection-1
```

### **Step 3: Auto-Fill Worksheet**

```powershell
python auto_fill_worksheet.py --paper 2
```

**What it does:**
- Takes Claude's verified results
- Fills worksheet.csv with:
  - bucket = A-retrievable / B-evidence-absent / C-not-retrieval
  - gold_provisions = node_ids (verified by Claude + you)
  - verified_by = Praveen De Silva
  - verified_date = today
  - notes = verification method (auto/manual/unsure)

**Output:**
```
✓ Paper 2 auto-filled!
  Updated 35 rows

Next steps:
  1. Review worksheet.csv for any unexpected results
  2. Run: uv run python pastpaper_triage.py build
```

---

## Workflow: All Papers (2-16)

For speed, batch process all papers:

```powershell
cd c:\Users\ASUS\Desktop\DSEP\Draftly\scripts\paper-eval

# Run Claude verification for Papers 2-16 (with your review)
python batch_all_papers.py
```

**What happens:**
1. Paper 2: Claude verifies → you confirm (5 min) → auto-fill
2. Paper 3: Claude verifies → you confirm (5 min) → auto-fill
3. ... continues through Paper 16

**Time estimate:**
- 15 papers × 5 min = 75 minutes = ~1.25 hours
- Plus build + score = ~2 hours total

---

## How Claude Verification Works

### **Claude Reads:**

1. **Question:** "Can Samantha become entitled to intestate estate? Discuss with Land Restriction Act."

2. **Candidate Sections:** All sections from Land Restriction Act (38-2014)
   ```
   38-2014/section-3/subsection-1/paragraph-d:
   "A foreigner without permanent resident status shall not own land"
   
   38-2014/section-5:
   "Restrictions on alienation: Land cannot be transferred to..."
   
   38-2014/section-7:
   "Rules for succession of restricted land..."
   ```

3. **Claude's Verdict:**
   ```
   ✓ YES: section-3/paragraph-d (directly answers: who CAN own)
   ⚠ PARTIAL: section-7 (about succession, partial match)
   ✗ NO: section-5 (about alienation restrictions, not inheritance)
   ```

### **Claude's Confidence**

Claude returns:
- **Yes** = Directly answers the question
- **Partial** = Answers part of the question
- **No** = Tangential or doesn't apply

**You decide** if you agree. If not, override manually.

---

## What If Claude Gets It Wrong?

Claude may miss sections or misidentify them. **You always have override:**

```
Claude's Analysis:
✓ YES: 21-1998/section-14
⚠ PARTIAL: 21-1998/section-45

Accept Claude's suggestion? (yes/partial/no/manual): no

Enter correct node_ids (semicolon-separated, or 'UNSURE'): 
> 21-1998/section-14; 21-1998/section-20; 21-1998/section-45

✓ Confirmed: manual
  Node_ids: 21-1998/section-14; 21-1998/section-20; 21-1998/section-45
```

---

## Handling Edge Cases

### **If Claude Finds No Sections**

```
Summary:
✗ No good sections found
```

**You decide:**
- **Option A:** Mark as UNSURE → leave bucket blank
- **Option B:** Manually enter node_ids
- **Option C:** Leave bucket blank → treat as B (evidence absent)

### **If No Statute Named in Question**

Claude skips it automatically (no act to search).

**Bucket:** C-not-retrieval (probably)

**You can override:** If you know it's really an A row, enter node_ids manually.

### **If Partial Match Only**

Example: Stamp Duty Act s6 answers "mode of payment" + "when due" but NOT "where to pay".

**Claude:** ⚠ PARTIAL
**You choose:**
- **yes** → Accept it as partial match
- **partial** → Only take YES, not PARTIAL
- **manual** → Enter your own verdict

---

## Scripts

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `claude_verify.py` | Ask Claude to verify sections | --paper N | Verification results JSON |
| `auto_fill_worksheet.py` | Fill worksheet from Claude results | --paper N | Updated worksheet.csv |
| `batch_all_papers.py` | Run both for Papers 2-16 | --start / --end | Completed worksheets for all papers |

---

## Batch Processing: Full Pipeline

After all papers are auto-filled:

```powershell
cd c:\Users\ASUS\Desktop\DSEP\Draftly

# 1. Build dataset
uv run python experiments/HiREC-inspired-retrieval/pastpaper_triage.py build

# 2. Validate
uv run python experiments/HiREC-inspired-retrieval/validate_dataset.py `
    --questions data/evaluvation/pastpaper-triage/pastpaper_questions.jsonl `
    --gold data/evaluvation/pastpaper-triage/pastpaper_gold.jsonl

# 3. Run tests (k=20, k=50, k=200)
uv run python experiments/HiREC-inspired-retrieval/run_hierarchy_ceiling.py `
    --questions data/evaluvation/pastpaper-triage/pastpaper_questions.jsonl `
    --run-name pastpaper-all-papers --seed-top-k 20

# 4. Score
uv run python experiments/HiREC-inspired-retrieval/hirec_evaluate.py `
    --run-name pastpaper-all-papers `
    --gold data/evaluvation/pastpaper-triage/pastpaper_gold.jsonl
```

---

## Estimated Timeline

| Step | Papers | Time |
|------|--------|------|
| Claude verification (Papers 2-16) | 15 | 75 min |
| Auto-fill worksheet | 15 | 5 min |
| Build + validate | All 16 | 10 min |
| Score | All 16 | 5 min |
| **TOTAL** | **16 papers** | **~1.5-2 hours** |

---

## Quality Check

After auto-fill, spot-check a few rows:

```powershell
# Open worksheet.csv in Excel
# Check Papers 2, 5, 10 (random sample)
# Look for:
#   ✓ bucket filled (A/B/C)
#   ✓ gold_provisions has node_ids (or empty for B/C)
#   ✓ verified_by = "Praveen De Silva"
#   ✓ verified_date filled
```

If anything looks wrong, you can:
- **Manually edit worksheet.csv**
- **Re-run `auto_fill_worksheet.py`**
- **Re-run `claude_verify.py` for that paper**

---

## Troubleshooting

### **Claude API Error**
```
Error: Could not reach Claude API
```
**Solution:** Check API key
```powershell
$env:ANTHROPIC_API_KEY = "sk-..."
```

### **JSON Parse Error**
```
⚠ Could not parse Claude's JSON response
```
**Solution:** Claude's response was not valid JSON. Try again:
```powershell
python claude_verify.py --paper 2
```

### **Worksheet Not Updating**
```
ERROR: worksheet.csv not found
```
**Solution:** Script expects worksheet at:
```
Draftly/data/evaluvation/pastpaper-triage/worksheet.csv
```

If path is different, edit auto_fill_worksheet.py line ~15.

---

## Next Steps

1. **Fix KNOWN_ABSENT list** (15 min):
   - Edit `pastpaper_triage.py`
   - Remove: Prevention of Frauds, Mortgage Act, Stamp Duty Act, State Lands Ordinance

2. **Run Claude verification for Paper 2**:
   ```powershell
   python claude_verify.py --paper 2
   ```

3. **Review Claude's suggestions** (5 min)

4. **Auto-fill**:
   ```powershell
   python auto_fill_worksheet.py --paper 2
   ```

5. **Repeat for Papers 3-16** (can batch with `batch_all_papers.py`)

6. **Build + Score** all 16 papers

---

## Final Result

All 36 papers (16×35 rows + Paper 1 extra) → Complete gold standard dataset → Scores for your retrieval engine.

Estimated completion: **~1 day (including breaks)**.

Good luck! 🚀