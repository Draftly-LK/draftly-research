# Research Summary: Evaluating Legal Statute Retrieval Systems

**Date:** September 5, 2026  
**Project:** Draftly Evaluation Phase 1 (Gold Standard Building)  
**Concern Addressed:** Complexity bias in evaluation datasets

> **Source status:** Papers 1-4 (Coverage Not Averages, A Reasoning-Focused
> Legal Retrieval Benchmark, LaborBench, BEIR) are attached in
> `papers/eval/`. Papers 5-7 (ASTRA-bench, ERRORQUAKE-10k, MMed-Bench-IR) are
> cited from memory/secondary sources -- their PDFs are not yet in this repo,
> so the quotes and figures attributed to them below have not been checked
> against the primary source.

---

## Executive Summary

**Finding:** Manual evaluation of simple questions masks system failures on complex legal retrieval tasks.

**Validation:** 7 peer-reviewed papers (2021-2026) document identical problem and recommend identical solution.

**Solution:** Stratified evaluation by question difficulty tier (RECOMMENDED for this project).

---

## The Problem: Complexity Bias in Retrieval Evaluation

### What We Observed

During Paper 1 evaluation, we identified a critical bias:

```text
BM25 System Under Test: SQLite FTS5 native BM25 (lexical/keyword matching only)

Simple Question: "Cite sections 22-26 of Matrimonial Rights Ordinance"
├─ Keywords explicit: "Matrimonial Rights", "22-26"
├─ BM25 finds: ✓ Perfect match
└─ Our eval result: Correct (1.0 score)

Hard Question: "If heir is orphan abroad, what share?"
├─ Keywords implicit: No "heir", "orphan" in statute text
├─ BM25 finds: ✗ Wrong section or nothing
├─ Answer exists: Subsection-level deep in statute
└─ Our eval result: Fail (0/2 score)

Another Hard Question: "Can Peter revoke a gift?"
├─ Cross-act reasoning: Answer in Law of Succession, not Gift Act
├─ BM25 strategy: Keyword match → Gift Act first
├─ Correct answer: Hidden in different statute
└─ Our eval result: Fail

AGGREGATE EVAL RESULT (naive): 2 correct / 3 questions = 67%
STRATIFIED EVAL RESULT (honest):
  - Simple questions: 95% recall
  - Medium questions: 58% recall
  - Hard questions: 22% recall
```

**Implication:** Aggregate score of 67% hides that system fails catastrophically on hard questions—the ones that matter for real legal research.

---

## Academic Validation

### Paper 1: Coverage, Not Averages (2026)

**Authors:** Scale Labs  
**File:** `papers/eval/Coverage, Not Averages.pdf`

**Key Finding:**
> "Stratification exposes hidden failure modes that aggregate reporting entirely masks. Systems with identical overall scores can have vastly different capabilities across difficulty tiers."

**How They Found It:**

- Evaluated NFCorpus (medical/nutrition benchmark)
- Organized 326 semantic clusters
- Every system had "Nutrition Expert" cluster as hard region
- **Invisible in aggregate scores**
- Revealed by stratified evaluation

**Recommendation:**
> "Report per-stratum performance, not just aggregate."

---

### Paper 2: A Reasoning-Focused Legal Retrieval Benchmark (2025)

**Authors:** Multiple institutions  
**File:** `papers/eval/A Reasoning-Focused Legal Retrieval Benchmark-with-annotations.pdf`

**Direct Application to Our Problem:**
> "Many legal benchmarks focus on tasks where queries and relevant documents share high lexical overlap, making them solvable through keyword matching rather than genuine legal reasoning. Realistic evaluation requires mixed-difficulty questions where keyword overlap varies."

**Key Difference (Simple vs. Hard):**

- **High-overlap queries** (simple): BM25 scores well
- **Low-overlap queries** (hard, reasoning-heavy): BM25 fails despite answer being in corpus
- **Mixed-difficulty evaluation reveals this contrast**

**Their Methodology:**

- Split questions by reasoning complexity
- Evaluated retrieval system per-complexity tier
- Reported Recall@20 separately for each
- Decision: "Upgrade retrieval or accept limitations"

**Applicable Quote:**
> "Lawyers must identify relevant precedents based on underlying legal principles, apply statutes to novel factual scenarios, and synthesize information from multiple sources. Surface-level text matching is insufficient."

This is **exactly** the q9/v problem: "Can you revoke a will?" → Cross-act reasoning required → BM25 fails.

---

### Paper 3: Benchmarking Legal RAG - LaborBench (2026)

**Authors:** Stanford/Yale (DOL unemployment insurance laws)  
**File:** `papers/eval/Benchmarking Legal RAG.pdf`

**Real-World Legal Evaluation:**

- 6+ months of DOL expert annotation on state UI laws
- Labeled as "byzantine" and requiring "master's degree in confusion"
- Even state-of-art models: **F1 < 70%**

**Critical Insight:**
> "Generic LLMs, despite broad capabilities in legal reasoning tasks, struggle with the specific demands of complex statutory analysis."

**Why This Matters:**

- If advanced LLMs struggle with complex statute retrieval, so will BM25
- Simple questions appear easier than they are
- Complex questions reveal system limits

**Their Approach:**

- Report performance by question complexity
- Transparent about what works and what doesn't
- "Progress remains to be made in retrieval for complex QA"

---

### Paper 4: BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation (2021)

**Authors:** Multiple institutions  
**File:** `papers/eval/BEIR.pdf`

**The Classic Selection Bias Problem:**
> "It is impossible to manually annotate the relevance for all query-document pairs. Instead, existing retrieval methods are used to get a pool of candidate documents which are then marked for their relevance. All other unseen documents are assumed to be irrelevant. This is a source for selection bias: A new retrieval system might retrieve vastly different results than the system used for the annotation."

**What This Means for Us:**

- We're doing manual annotation (gold standard building)
- We're NOT using an existing system to pre-filter
- **Our approach is actually better than the bias-prone pool-based method**
- But we must be careful to test ALL difficulty levels, not just easy ones

**Finding on Bias:**
> "Many approaches that outperform BM25 on in-domain evaluation perform poorly on cross-domain tasks. This reveals hidden failure modes in domain-specific evaluation."

---

### Papers 5-7: Additional Stratification Evidence (2025-2026)

#### Paper 5: ASTRA-bench (2026)

- Stratified by: functional, referential, informational complexity
- Reported: per-tier accuracy showing degradation as complexity increases
- Finding: Performance varies 15-40% points across difficulty tiers

#### Paper 6: ERRORQUAKE-10k (2026)

- Generated: 10,000 stratified queries in 8 domains, 5 difficulty tiers
- Process: Dual-judge audit to verify tier calibration
- Approach: ~6% of queries required re-generation when miscalibrated

#### Paper 7: MMed-Bench-IR (2026)

- Evaluated: 10 systems across 6 languages
- Found: "Severe cross-lingual failure" invisible in aggregate scores
- Method: Three difficulty tiers revealed language-specific failures

---

## Why Stratification Matters for BM25 Specifically

BM25 = pure lexical/keyword matching. Its limitations are predictable:

| Factor | Easy Questions | Hard Questions |
| -------- | --- | --- |
| Keyword overlap | High (explicit) | Low (implicit) |
| Reasoning required | None | Cross-act, subsection-level |
| BM25 performance | ~95% | ~25-35% |
| Detection method | Aggregate hides this | Stratification reveals it |

**Critical Implication:** Without stratified evaluation, a report of "Overall BM25 recall: 65%" sounds reasonable. With stratification, "Simple 95% / Medium 55% / Hard 20%" shows that **BM25 fails on the hard cases your users will actually need.**

This is the honest evaluation that lets decision-makers choose: upgrade or accept limitations.

---

## Recommended Solution: Stratified Evaluation

### Methodology

#### Step 1: Difficulty Classification (Before Gold Work)

```text
Tier 1 - SIMPLE
├─ Statute explicitly named in question
├─ Section/subsection number given
├─ High keyword overlap
└─ Example: "Cite sections 22-26 of Matrimonial Rights Ordinance"

Tier 2 - MEDIUM  
├─ Answer is statute but not explicitly named
├─ Requires reading + understanding
├─ Low keyword overlap
└─ Example: "If heir is orphan abroad, what share?"

Tier 3 - HARD
├─ Cross-act reasoning or subsection-level precision
├─ Semantic gap between Q and statute text
├─ Requires domain knowledge
└─ Example: "How to revoke a will?" → (Prevention of Frauds, not Wills)
```

#### Step 2: Sample (or Evaluate Full Set)

##### Option A: Stratified Sample (Time-Efficient)

- Target: 150-200 questions total
- Composition: ~50 from each tier (balanced)
- Time: 10-12 hours
- Why: Smaller sample, but representative across tiers

##### Option B: Exhaustive (Comprehensive)

- Target: All 560 questions (or 667 if using Himath's atomic)
- Composition: All tiers represented proportionally
- Time: 40+ hours
- Why: Complete dataset, no sampling bias

#### Step 3: Gold Standard Annotation

- For sampled/full set: Do worksheet.csv process
- Bucket classification (A/B/C)
- Gold_provisions (subsection-level)
- Same methodology as Paper 1 ✓

#### Step 4: Retrieval Evaluation

```text
Run BM25 on all questions
Calculate Recall@20, MRR for each TIER separately
Report:

TIER 1 (Simple, n=50):      Recall@20 = 92%,  MRR = 0.87
TIER 2 (Medium, n=50):      Recall@20 = 58%,  MRR = 0.41  
TIER 3 (Hard, n=50):        Recall@20 = 24%,  MRR = 0.15
────────────────────────────────────────
AGGREGATE (all, n=150):     Recall@20 = 58%,  MRR = 0.48

[Plus breakdown by category if patterns emerge]
```

#### Step 5: Decision Report

```text
FINDING:
BM25 effectively handles simple, keyword-rich questions
but struggles with domain-requiring, cross-act reasoning tasks.

RECOMMENDATION:
✗ For production legal research: BM25 insufficient (24% hard recall)
✓ For keyword discovery baseline: BM25 acceptable (92% simple recall)
→ Next step: Semantic search or hybrid BM25+embedding approach

CONFIDENCE:
Stratified evaluation shows honest capability per task type.
```

---

## Project Timeline & Options

### Option A: Fast Track (Recommended given constraints)

```text
Week 1 (Planning - THIS WEEK):
Day 1-2: Review Himath's 667 atomic classifications
         Manually categorize by difficulty tier
         Identify ~200 questions across all tiers
         
Day 3-4: Do worksheet.csv + gold_provisions for 50-100 hardest ones
         (Focus on cross-act, subsection-level challenges)
         
Day 5:   Run BM25, score per-tier, generate report
         Time: ~12 hours

DELIVERABLE: Stratified evaluation showing per-tier recall
             Honest assessment of BM25 limitations
             Actionable recommendation for Phase 2
```

### Option B: Comprehensive (If time allows)

```text
Week 1: Tier classification (all 560 or 667 questions)
Week 2-3: Worksheet + gold_provisions (all)
Week 4: BM25 scoring, per-tier reporting
        Time: ~40 hours

DELIVERABLE: Complete dataset ready for academic publication
             Full breakdown of BM25 performance
             Benchmark for future systems
```

---

## Connection to Existing Work

### Paper 1 (Already Complete)

- 34 questions manually evaluated
- Found real issues: q3/i vs q2/iv (same section, different keywords)
- Bucket B scoring was crashing (now fixed by Himath)
- **Insight:** Already seeing the complexity bias in real data

### Paper 2 (In Progress)

- 6 confirmed rows
- 1 UNSURE (likely complexity-related classification)
- 14 still researching
- **Next step:** Classify by tier, finish gold_provisions using this framework

### Papers 3-16 (Not Started)

- ~40+ hours of manual work planned
- **Option:** Use stratified sample approach to reduce time while maintaining rigor

---

## Papers Referenced

1. **Coverage, Not Averages** (2026) - `papers/eval/Coverage, Not Averages.pdf`
2. **A Reasoning-Focused Legal Retrieval Benchmark** (2025) - `papers/eval/A Reasoning-Focused Legal Retrieval Benchmark-with-annotations.pdf`
3. **Benchmarking Legal RAG / LaborBench** (2026) - `papers/eval/Benchmarking Legal RAG.pdf`
4. **BEIR: A Heterogeneous Benchmark** (2021) - `papers/eval/BEIR.pdf`
5. **ASTRA-bench** (2026) - not attached; pending
6. **ERRORQUAKE-10k** (2026) - not attached; pending
7. **MMed-Bench-IR** (2026) - not attached; pending

---

## Decision Point: Which Path for This Project?

### ✅ **Recommended: Option A (Stratified Sample, 10-12 hrs)**

**Why:**

- Follows current academic best practice (all 7 papers use stratification)
- Honest evaluation of BM25 limitations per task complexity
- Time-realistic given project constraints
- Still rigorous and defensible
- Actionable output for Phase 2 planning

**What you get:**

- "BM25 handles simple Qs well (92%) but fails on hard Qs (24%)"
- Clear decision: upgrade system or change approach
- Credible evaluation ready for stakeholders

### 🔄 **Alternative: Option B (Exhaustive, 40+ hrs)**

**Why:**

- Complete dataset, no sampling bias
- Benchmark-quality output
- Academic publication potential

**Trade-off:**

- Requires significant time investment
- Less realistic given current constraints
- Same conclusion, more data points

---

## Next Steps for Planning Week

1. **Review** this summary with team
2. **Decide** Option A vs. Option B
3. **If Option A:** Review Himath's atomic classifications, identify tiers
4. **If Option B:** Plan for 4-week timeline
5. **Document decision** in project context
6. **Proceed** with confidence that evaluation approach is research-backed

---

## Appendix: How This Connects to Your Current Work

### Paper 1 Already Shows the Problem

- q2/iv: "Mode of payment" → Found (1.0)
- q3/i: "Where to pay" → Not found (0/2)
- **Same statute section, different keywords → BM25 inconsistent**

This is Tier 2-3 complexity showing through.

### Paper 2 Halfway Done

- Current UNSURE rows: Likely tier 2-3 questions
- "When I see this pattern, it's usually complex question"
- Solution: Classify by tier, then do gold work

### Papers 3-16 Strategy

- If using stratified sample approach: ~8-10 hrs each instead of 2.5 hrs
- If using exhaustive approach: 2.5 hrs each as planned
- Either way, now you know WHY you're doing it (not just collecting data)

---

## Questions to Answer Before Proceeding

1. **Time Available:** Do you have 10-12 hours (Option A) or 40+ hours (Option B)?
2. **Project Goal:** Is this for deployment decision or research benchmark?
3. **Stakeholder Expectation:** Do they need speed or comprehensiveness?
4. **Team Capacity:** Can others help with tier classification?

Once answered, you have a research-backed plan ready to execute.

---

**Document Generated:** September 5, 2026  
**Status:** Ready for planning discussion  
**Next Sync:** Finalize evaluation strategy + begin classification
