# Claude-Assisted Verification - Quick Start

**Verify all 16 papers in ~1.5-2 hours using Claude API**

---

## Prerequisites

```powershell
# 1. Install dependencies
pip install anthropic

# 2. Set API key
$env:ANTHROPIC_API_KEY = "sk-your-api-key-here"

# 3. Navigate to scripts
cd "c:\Users\ASUS\Desktop\DSEP\Draftly\scripts\paper-eval"
```

---

## Option A: Single Paper (Test First)

Test with Paper 2 to see how it works:

```powershell
# Step 1: Claude verifies sections
python claude_verify.py --paper 2

# Step 2: Auto-fill worksheet
python auto_fill_worksheet.py --paper 2

# Done! Takes ~5-10 minutes
```

**What to expect:**
- Claude reads each question
- Claude suggests statute sections (Yes/No/Partial)
- You review each suggestion (confirm/override)
- Worksheet auto-fills

---

## Option B: All Papers (2-16)

Batch process everything:

```powershell
python batch_all_papers.py
```

**What happens:**
- Paper 2: Claude verifies → you confirm (5 min) → auto-fill
- Paper 3: Claude verifies → you confirm (5 min) → auto-fill
- ... continues through Paper 16

**Total time:** ~75 minutes (15 papers × 5 min)

**Then:**
```powershell
cd ../..  # Go to Draftly root

# Build + validate
uv run python experiments/HiREC-inspired-retrieval/pastpaper_triage.py build

uv run python experiments/HiREC-inspired-retrieval/validate_dataset.py `
    --questions data/evaluvation/pastpaper-triage/pastpaper_questions.jsonl `
    --gold data/evaluvation/pastpaper-triage/pastpaper_gold.jsonl

# Score
uv run python experiments/HiREC-inspired-retrieval/run_hierarchy_ceiling.py `
    --questions data/evaluvation/pastpaper-triage/pastpaper_questions.jsonl `
    --run-name pastpaper-all-papers --seed-top-k 20

uv run python experiments/HiREC-inspired-retrieval/hirec_evaluate.py `
    --run-name pastpaper-all-papers `
    --gold data/evaluvation/pastpaper-triage/pastpaper_gold.jsonl
```

**Total time end-to-end:** ~2 hours

---

## How Claude Verification Works

For each question, Claude:

1. **Reads the question:**
   ```
   "Can Samantha become entitled to the estate? 
    Discuss with Land Restriction Act No. 38 of 2014"
   ```

2. **Reads candidate statute sections:**
   ```
   38-2014/section-3: "A foreigner without permanent residence..."
   38-2014/section-5: "Restrictions on alienation..."
   38-2014/section-7: "Succession rules..."
   ```

3. **Gives verdict for each section:**
   ```
   ✓ YES: section-3 (directly answers: who can own land)
   ⚠ PARTIAL: section-7 (about succession, partial match)
   ✗ NO: section-5 (about alienation, not inheritance)
   ```

4. **You review:**
   ```
   Accept Claude's suggestion? (yes/partial/no/manual): yes
   ✓ Confirmed
   ```

---

## What If Claude Gets It Wrong?

You always override:

```powershell
Accept Claude's suggestion? (yes/partial/no/manual): manual

Enter correct node_ids (semicolon-separated): 
> 38-2014/section-3; 38-2014/section-7
```

---

## Troubleshooting

**API key not set:**
```
Error: Could not reach Claude API
```
→ Set it: `$env:ANTHROPIC_API_KEY = "sk-..."`

**No sections found:**
→ Mark as UNSURE (Claude will flag it for review)

**Claude suggests wrong section:**
→ Override with `manual` option

---

## Expected Workflow Output

```
Paper 2 verification:

Question q1/iii:
  Claude: YES → 38-2014/section-3
  You: Confirm ✓

Question q6/i:
  Claude: YES → 21-1998/section-14, PARTIAL → 21-1998/section-45
  You: Accept both ✓

... repeat for all 35 questions ...

✓ Paper 2 complete
```

---

## Files

After running, you'll have:

```
paper-eval/
├── paper_02_claude_results.json    ← Claude's verification results
├── paper_03_claude_results.json
├── ...
└── worksheet.csv (updated)         ← Your filled worksheet
```

---

## Cost Estimate

- **API calls:** ~35 questions × 16 papers = 560 questions
- **Cost per question:** ~0.01 USD (reading + verification)
- **Total API cost:** ~$5-10

---

## Start Now

```powershell
cd "c:\Users\ASUS\Desktop\DSEP\Draftly\scripts\paper-eval"

# Test with Paper 2
python claude_verify.py --paper 2
```

Then follow the prompts. Takes 5-10 minutes.

---

## Questions?

See `CLAUDE_WORKFLOW.md` for full documentation.

Good luck! 🚀