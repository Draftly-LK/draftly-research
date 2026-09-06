# Lookup Helper - Usage Guide

**Fast candidate section finder. You do the judgment.**

---

## What It Does

1. **Builds an index** of ALL statute nodes (sections, subsections, paragraphs)
   - Includes full text (not truncated)
   - Fast local search (no API calls)

2. **Lets you search by:**
   - Act ID
   - Keywords
   - Combination

3. **You review results** and decide which ones answer your question

---

## One-Time Setup

```powershell
cd c:\Users\ASUS\Desktop\DSEP\Draftly\scripts\paper-eval

# Build the index (takes ~2 seconds)
python lookup_helper.py --build
```

Output:
```
✓ Index built
Stats:
  7-1840: 25 nodes
  43-1982: 18 nodes
  11-1973: 181 nodes
  21-1844: 45 nodes
  21-1998: 137 nodes
  38-2014: 32 nodes
  ...

Total: 4,523 searchable nodes
Saved to: statute_index.json
```

Done! Now use it for Paper 2.

---

## Usage: Paper 2

```powershell
python lookup_helper.py --paper 2
```

Interactive session:

```
PAPER 2 LOOKUP HELPER
===================

Q1/III: "Can Samantha become entitled to estate? Discuss Land Restriction Act."

> both 38-2014 citizen foreigner alien

Found 8 matches

1. 38-2014/section-3/subsection-1/paragraph-d
   Type: paragraph
   Heading: Restrictions on foreign nationals
   Text: A foreigner without permanent resident status shall not...

2. 38-2014/section-3/subsection-1/paragraph-a
   Type: paragraph
   Heading: Ownership restrictions
   Text: No person of non-citizen nationality...

3. 38-2014/section-5
   Type: section
   Heading: Alienation restrictions
   Text: Land cannot be transferred to...

> show 38-2014/section-3/subsection-1/paragraph-d

38-2014/section-3/subsection-1/paragraph-d
Heading: Restrictions on foreign nationals
Full text:
A foreigner who does not have permanent resident status shall not be 
entitled to acquire, own, hold or dispose of any land in Sri Lanka. 
Exceptions apply for diplomatic personnel and registered non-resident 
investors under section 12.

✓ This answers the question → Copy: 38-2014/section-3/subsection-1/paragraph-d
```

---

## Commands

### **Search one act**
```
> act 21-1998

Found 137 matches (showing first 20)
```

### **Search by keywords**
```
> keyword intestate heir succession

Found 12 matches
```

### **Search act + keywords**
```
> both 21-1998 class title possessory

Found 4 matches
1. 21-1998/section-14/paragraph-b
2. 21-1998/section-14/paragraph-c
3. 21-1998/section-45/subsection-1
4. 21-1998/section-46
```

### **Show full text of a node**
```
> show 21-1998/section-14/paragraph-b

21-1998/section-14/paragraph-b
Heading: Second Class Title
Full text: [full provision text, not truncated]
```

### **Exit**
```
> quit
```

---

## Workflow For Paper 2

For each question:

1. **Read the question**
   ```
   Q6/i: "What class of title would Kamal be eligible?" 
         (has prescriptive rights since 1980)
   ```

2. **Identify the act**
   ```
   Act: Registration of Title Act (21-1998)
   Concepts: class, title, possessory, prescription
   ```

3. **Search**
   ```
   > both 21-1998 class possessory prescription
   ```

4. **Review results** (full text, not truncated!)
   ```
   ✓ 21-1998/section-14/paragraph-b — YES, this is it
   ✗ 21-1998/section-12 — no, this is about registration
   ```

5. **Write to worksheet**
   ```
   gold_provisions: 21-1998/section-14/paragraph-b
   ```

6. **Move to next question**

---

## Time Estimate

- **Build index:** 2 seconds (one time only)
- **Per question:** 1-2 minutes
  - 30 sec: search + review results
  - 30 sec: show full text + confirm
- **Per paper (35 questions):** ~1 hour (same as Paper 1, but faster searching)

---

## Advanced Searches

### **Search without act (find across all acts)**
```
> keyword testamentary freedom

Found 23 matches across all acts
- 21-1844/section-2: [Wills Ordinance]
- 7-1840/section-4: [Prevention of Frauds Ordinance]
- ...
```

**This catches the cross-act patterns** (like Wills vs Prevention of Frauds)

### **Boolean keywords (all must match)**
```
> keyword registration instrument days

Found 4 matches (all must have registration AND instrument AND days)
```

### **Get all nodes from an act**
```
> act 11-1973

Found 181 nodes from Apartment Ownership Law
(useful for understanding the structure)
```

---

## What It Preserves

✅ **Full text** (no 500-char truncation)
✅ **Subsections + paragraphs** (not just top-level sections)
✅ **All acts** (can search across acts to catch cross-references)
✅ **Zero API cost**
✅ **Your judgment** (you decide which sections match)
✅ **Context accumulation** (you learn the corpus as you go)

---

## Compare to Claude Script

| Feature | Lookup Helper | Claude Script |
|---------|---|---|
| **Subsections** | ✅ Included | ❌ Dropped |
| **Full text** | ✅ Full | ❌ 500 chars |
| **Override cases** | ✅ Can search cross-act | ❌ Blind to them |
| **Cost** | $0 | ~$5-10 |
| **Speed** | Fast (local) | Slow (API) |
| **Accuracy** | Your judgment | Claude guesses |

---

## Example: Paper 2, Q2/IV

**Question:** "Where do you pay stamp duty? Mode of payment? Within how many days?"

**Observation:** No statute named (override case)

**Search:**
```
> keyword stamp duty payment days mode

Found 18 matches across all acts

43-1982/section-6/subsection-1
  Heading: Time and mode of paying stamp duty
  Text: Stamp duty shall be paid in cash or electronic transfer...
        within fourteen days of execution...

43-1982/section-6/subsection-3
  Heading: Payment office
  Text: Payment shall be made at the office of...

> show 43-1982/section-6/subsection-1

[Shows full text covering "mode" + "days" but NOT "where"]

> show 43-1982/section-6/subsection-3

[Shows full text with "where" (payment office)]
```

**Your judgment:**
```
Results:
✓ 43-1982/section-6/subsection-1 (mode + days)
✓ 43-1982/section-6/subsection-3 (where)
⚠ PARTIAL — s6/subsection-1 covers 2/3 of question, s6/subsection-3 covers 1/3

Write to worksheet:
bucket = A-retrievable
gold_provisions = 43-1982/section-6/subsection-1; 43-1982/section-6/subsection-3
corpus_coverage = complete
notes = Partial answer: subsection-1 covers mode+days, subsection-3 covers location
```

---

## Ready?

```powershell
# Build once
python lookup_helper.py --build

# Use for Paper 2
python lookup_helper.py --paper 2
```

Then follow the interactive prompts. Takes 1 hour for 35 questions (faster than Paper 1 because searching is quicker).

---
