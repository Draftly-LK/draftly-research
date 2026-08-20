# -*- coding: utf-8 -*-
"""Draftly mid-evaluation deck - slides 15 to the end."""
from kit import *
from deck_part1 import (TEAM, stat_card, numbered_card, bullet_block, chip,
                        arrow, flow, divider)
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR


def build(prs, p):
    # ------------------------------------------------------- 15 approaches
    p += 1
    s = new_slide(prs)
    chrome(s, "Retrieval engine", p, TEAM)
    title(s, "Retrieval approaches under investigation")
    approaches = [
        ("Lexical", "Exact legal terminology, section numbers and citations."),
        ("Semantic", "Conceptually related provisions and judgments."),
        ("Hybrid fusion", "Lexical and semantic results fused by rank."),
        ("Metadata filtering", "Statute, section, court, date and topic."),
        ("Structure-aware", "Judgment sections and holdings, not flat chunks."),
        ("Citation graph", "Statute-to-case and case-to-case relationships."),
        ("Authority ranking", "Court hierarchy and precedential weight."),
        ("Temporal retrieval", "The version in force on the relevant date."),
        ("Evidence verification", "Claims checked against retrieved text "
                                  "before an answer is shown."),
    ]
    cwd = (CW - 2 * 0.36) / 3
    for i, (head, body) in enumerate(approaches):
        x = ML + (i % 3) * (cwd + 0.36)
        y = 3.42 + (i // 3) * 1.88
        rect(s, x, y, cwd, 1.68, fill=CARD, radius=0.14)
        textbox(s, x + 0.42, y + 0.30, cwd - 0.84, head, size=23, color=INK,
                line=1.15)
        textbox(s, x + 0.42, y + 0.86, cwd - 0.84, body, size=17, color=BRONZE,
                line=1.32)
    textbox(s, ML, 9.05, CW,
            "These are candidates being compared, not a shipped design. "
            "The current prototype fuses a lexical channel, a dense channel "
            "and a statute graph.",
            size=19, color=BRONZE, font=ITAL, italic=True, line=1.3,
            tag="s15-foot")

    # ------------------------------------------------------- 16 process
    p += 1
    s = new_slide(prs)
    chrome(s, "Retrieval engine", p, TEAM)
    title(s, "How a question becomes a cited answer")
    flow(s, 3.45, ["User question", "Query analysis",
                   "Lexical and semantic retrieval", "Metadata and date filter",
                   "Authority-aware reranking", "Evidence verification",
                   "Cited answer or abstention"],
         h=1.55, size=16, gap=0.30)
    hline(s, ML, 5.55, CW, color=RULE, weight=1.0)
    lw = (CW - 0.80) / 2
    kicker(s, ML, 5.90, "The ranking considers", w=lw, size=24)
    bullet_block(s, ML, 6.60, lw, [
        "Court hierarchy and precedential authority",
        "Whether a decision binds or merely persuades",
        "Whether it has been followed or distinguished",
        "Amendment and effective dates against the question date",
    ], size=19, gap=7, tag="s16-l")
    kicker(s, ML + lw + 0.80, 5.90, "Every answer carries", w=lw, size=24)
    bullet_block(s, ML + lw + 0.80, 6.60, lw, [
        "The applicable statute, section and version",
        "The relevant case citation and legal principle",
        "The supporting passage and where it sits in the source",
        "A verification status, or an abstention",
    ], size=19, gap=7, tag="s16-r")

    # ------------------------------------------------------- 17 papers
    p += 1
    s = new_slide(prs)
    chrome(s, "Retrieval engine", p, TEAM)
    title(s, "The research this is built on")
    papers = [
        ("Section-Weighted Hybrid Case Retrieval",
         "Segmentation, BM25, dense ANN, rank fusion, section-weighted "
         "reranking."),
        ("LexPath: Multi-Path Article Retrieval",
         "Statute and section retrieval with legal hierarchy."),
        ("IL-PCSR: Prior Case and Statute Retrieval",
         "Retrieves statutes and precedents jointly, as our model does."),
        ("Temporal Misgrounding in Legal RAG",
         "Why retrieval must select the law in force on the date."),
        ("LeSICiN: Heterogeneous Graph for Statutes",
         "Case text plus the citation network predicts the legislation."),
        ("Legal Structure in Retrieval-Augmented Generation",
         "Authority-aware ranking from hierarchy, citations and PageRank."),
        ("DoSSIER: Dense Retrieval, Summarisation Reranking",
         "Long judgments via paragraph retrieval and summary reranking."),
    ]
    y0, pitch = 3.55, 0.80
    for i, (name, why) in enumerate(papers):
        y = y0 + i * pitch
        textbox(s, ML, y, 0.60, "%02d" % (i + 1), size=17, font=BOLD, bold=True,
                color=BRONZE, line=1.2)
        textbox(s, ML + 0.68, y, 7.35, name, size=18, color=INK, line=1.26)
        textbox(s, 9.45, y, 9.43, why, size=18, color=BRONZE, line=1.26)
        hline(s, ML, y + 0.56, CW, color=RULE, weight=1.0)

    # ------------------------------------------------------- 18 divider
    p += 1
    divider(prs, "03", "The drafting platform",
            "Where the retrieved law turns into checks, prescribed forms and "
            "a reviewable draft.", p)

    # ------------------------------------------------------- 19 regimes
    p += 1
    s = new_slide(prs)
    chrome(s, "Platform scope", p, TEAM)
    title(s, "Four registration contexts, one starting point")
    regimes = ["Registration of Documents Ordinance",
               "Registration of Title Act", "Apartment ownership",
               "Special-area registration"]
    for i, r in enumerate(regimes):
        y = 3.40 + i * 1.25
        chosen = (i == 1)
        rect(s, ML, y, 7.30, 1.10, fill=(INK if chosen else CARD), radius=0.12)
        textbox(s, ML + 0.45, y, 5.4, r, size=21,
                color=(CREAM if chosen else INK), line=1.24, h=1.10,
                anchor=MSO_ANCHOR.MIDDLE)
        if chosen:
            textbox(s, ML + 5.95, y, 0.9, "V1", size=20, font=BOLD, bold=True,
                    color=BRONZE, line=1.2, h=1.10, anchor=MSO_ANCHOR.MIDDLE,
                    align=PP_ALIGN.RIGHT)
    textbox(s, ML, 8.60, 7.30,
            "Each regime differs in ownership effect, documents, forms, "
            "verification and registration process.",
            size=18, color=BRONZE, font=ITAL, italic=True, line=1.32,
            tag="s19-l")
    kicker(s, 9.30, 3.45, "Why we start with the Registration of Title Act "
           "No. 21 of 1998", w=9.58, size=24)
    bullet_block(s, 9.30, 4.85, 9.58, [
        "The workflow is statute-driven and structured",
        "It uses prescribed forms published in the gazette",
        "The scope is comparatively self-contained",
        "Its documents are generally more machine-readable",
        "Practitioners are often unfamiliar with its procedures",
        "It is a manageable domain to build and evaluate against",
    ], size=20, gap=9, tag="s19-r")

    # ------------------------------------------------------- 20 functions
    p += 1
    s = new_slide(prs)
    chrome(s, "Platform scope", p, TEAM)
    title(s, "Six notarial functions, four in scope")
    funcs = [("01", "Examination of title", True), ("02", "Drafting", True),
             ("03", "Execution", True), ("04", "Stamping", False),
             ("05", "Attestation", True), ("06", "Registration", False)]
    cwf = (CW - 5 * 0.30) / 6
    for i, (n, name, inscope) in enumerate(funcs):
        x = ML + i * (cwf + 0.30)
        rect(s, x, 3.45, cwf, 2.30, fill=(INK if inscope else CARD), radius=0.14)
        textbox(s, x + 0.35, 3.78, cwf - 0.7, n, size=20, font=BOLD, bold=True,
                color=BRONZE, line=1.1)
        textbox(s, x + 0.35, 4.32, cwf - 0.7, name, size=21,
                color=(CREAM if inscope else INK), line=1.22)
        textbox(s, x + 0.35, 5.28, cwf - 0.7,
                "in scope" if inscope else "later", size=16,
                color=(BRONZE if inscope else BRONZE), font=ITAL, italic=True,
                line=1.2)
    hline(s, ML, 6.25, CW, color=RULE, weight=1.0)
    lw = (CW - 0.80) / 2
    kicker(s, ML, 6.60, "In the first version", w=lw, size=24)
    bullet_block(s, ML, 7.30, lw, [
        "Post-certificate RTA transactions",
        "Retrieval of the applicable statutes and regulations",
        "Prescribed forms, transaction-specific workflows",
        "Document verification, draft generation, lawyer review",
    ], size=19, gap=7, tag="s20-l")
    kicker(s, ML + lw + 0.80, 6.60, "Deliberately outside it", w=lw, size=24)
    bullet_block(s, ML + lw + 0.80, 7.30, lw, [
        "Initial title compilation and title-settlement disputes",
        "Company, probate, power-of-attorney and co-owner cases",
        "Part-parcel dealings, subdivision and condominium",
        "Anything with a live dispute or court notice",
    ], size=19, gap=7, tag="s20-r")

    # ------------------------------------------------------- 21 title exam
    p += 1
    s = new_slide(prs)
    chrome(s, "Platform workflow", p, TEAM)
    title(s, "Examination of title, as the lawyer described it")
    steps = ["Search the relevant land records", "Identify the present owner",
             "Trace the chain of title",
             "Check mortgages, charges and encumbrances",
             "Verify local-authority documents",
             "Confirm the identities of the parties",
             "Identify inconsistencies and risks", "Prepare the title report"]
    cws = (CW - 0.60) / 2
    for i, st in enumerate(steps):
        col, row = i // 4, i % 4
        x = ML + col * (cws + 0.60)
        y = 3.45 + row * 1.24
        dot(s, x, y + 0.22, 0.34)
        textbox(s, x, y + 0.22, 0.34, "%d" % (i + 1), size=15, font=BOLD,
                bold=True, color=CREAM, align=PP_ALIGN.CENTER, line=1.0,
                h=0.34, anchor=MSO_ANCHOR.MIDDLE)
        textbox(s, x + 0.62, y + 0.16, cws - 0.62, st, size=21, color=INK,
                line=1.28)
        if row < 3:
            hline(s, x, y + 1.02, cws, color=RULE, weight=1.0)
    rect(s, ML, 8.45, CW, 1.05, fill=CARD, radius=0.12)
    textbox(s, ML + 0.45, 8.45, CW - 0.90,
            "At every step the retrieval engine supplies the applicable legal "
            "requirement and the cautionary case-law principle that goes with "
            "it.",
            size=20, color=INK, line=1.30, h=1.05, anchor=MSO_ANCHOR.MIDDLE)

    # ------------------------------------------------------- 22 rule pack
    p += 1
    s = new_slide(prs)
    chrome(s, "Platform build", p, TEAM)
    title(s, "The RTA rule pack, versioned and governed")
    textbox(s, ML, 3.15, 15.5,
            "The legal content the platform runs on is data, not code paths. "
            "Version 1.0.0 holds:",
            size=21, color=BRONZE, line=1.3)
    packs = [("9", "transaction families"), ("33", "prescribed subtypes"),
             ("145", "checklist requirements"), ("23", "checklist modules"),
             ("25", "deterministic checks"), ("52", "document classes"),
             ("32", "form templates"), ("25", "routing questions")]
    cwp = (CW - 3 * 0.34) / 4
    for i, (num, lab) in enumerate(packs):
        x = ML + (i % 4) * (cwp + 0.34)
        y = 3.85 + (i // 4) * 2.30
        rect(s, x, y, cwp, 2.05, fill=CARD, radius=0.14)
        textbox(s, x + 0.42, y + 0.32, cwp - 0.84, num, size=52, font=BOLD,
                bold=True, color=BRONZE, line=1.05)
        textbox(s, x + 0.42, y + 1.28, cwp - 0.84, lab, size=19, color=INK,
                line=1.28)
    textbox(s, ML, 8.60, CW,
            "Every requirement records its source class, so the interface can "
            "say whether something is required by the Act, by a gazetted "
            "regulation, by current registry practice, or only by prudent "
            "professional practice. Ten governed sources back the pack.",
            size=19, color=INK, line=1.36, tag="s22-foot")

    # ------------------------------------------------------- 23 architecture
    p += 1
    s = new_slide(prs)
    chrome(s, "Platform build", p, TEAM)
    title(s, "What is standing up on the platform side")
    domains = [
        ("Identity and access", "auth  ·  billing"),
        ("Matter and parties", "matter  ·  party  ·  task  ·  obligations"),
        ("Documents", "document  ·  storage  ·  processing  ·  verification"),
        ("Legal content", "content governance  ·  corpus governance  ·  "
                          "library  ·  research  ·  memory"),
        ("Output and control", "check  ·  draft  ·  approval  ·  export  ·  "
                               "notarial register"),
        ("Platform services", "audit  ·  retention  ·  notification  ·  voice"),
    ]
    cwa = (CW - 2 * 0.36) / 3
    for i, (head, names) in enumerate(domains):
        x = ML + (i % 3) * (cwa + 0.36)
        y = 3.42 + (i // 3) * 2.12
        rect(s, x, y, cwa, 1.88, fill=CARD, radius=0.14)
        textbox(s, x + 0.40, y + 0.28, cwa - 0.80, head, size=22, color=INK,
                line=1.18)
        textbox(s, x + 0.40, y + 0.85, cwa - 0.80, names, size=17, color=BRONZE,
                line=1.30)
    rect(s, ML, 7.82, CW, 1.55, fill=INK, radius=0.14)
    textbox(s, ML + 0.50, 8.05, 8.4,
            "24 services in a modular monolith, each with a written design "
            "doc, a contract entry and a CI check that fails if the two drift.",
            size=19, color=CREAM, line=1.34)
    textbox(s, ML + 9.60, 8.05, 8.2,
            "A Next.js front end with 25 routes, including the matter "
            "workspace: documents, facts, checks, workflow, drafts, activity.",
            size=19, color=CREAM, line=1.34)

    # ------------------------------------------------------- 24 pipeline
    p += 1
    s = new_slide(prs)
    chrome(s, "Platform build", p, TEAM)
    title(s, "The document-processing pipeline")
    flow(s, 3.50, ["Upload, split and classify",
                   "OCR, layout analysis or OCR-free extraction",
                   "Structured legal-information extraction",
                   "Cross-document linking and chain of title",
                   "Consistency and legal-rule checks",
                   "Draft, then lawyer verification"],
         h=1.60, size=17, gap=0.34)
    hline(s, ML, 5.65, CW, color=RULE, weight=1.0)
    lw = (CW - 0.80) / 2
    kicker(s, ML, 6.00, "Approaches being compared", w=lw, size=24)
    bullet_block(s, ML, 6.70, lw, [
        "Production-scale OCR and LLM microservices",
        "Document splitting with multimodal extraction",
        "OCR-free document understanding",
        "Multi-agent processing with human validation",
        "Reconstruction-based extraction verification",
    ], size=19, gap=6, tag="s24-l")
    kicker(s, ML + lw + 0.80, 6.00, "Our own OCR benchmark", w=lw, size=24)
    textbox(s, ML + lw + 0.80, 6.70, lw,
            "We compare a hosted model against an open-source engine and "
            "preprocessing variants on scanned Sri Lankan conveyancing "
            "documents, using one shared field schema.",
            size=19, color=INK, line=1.36)
    textbox(s, ML + lw + 0.80, 8.25, lw,
            "A synthetic run must score 100% and 0.00 character error. If it "
            "does not, the harness is broken and no other result is trusted.",
            size=18, color=BRONZE, font=ITAL, italic=True, line=1.34,
            tag="s24-r")

    # ------------------------------------------------------- 25 end to end
    p += 1
    s = new_slide(prs)
    chrome(s, "Platform workflow", p, TEAM)
    title(s, "An RTA transfer, end to end")
    steps = [
        "The lawyer selects a transfer.",
        "The system asks for the documents it needs.",
        "Party and property details are extracted.",
        "Identity and jurisdiction are checked.",
        "The governing provisions and forms are retrieved.",
        "The correct order of the transaction is laid out.",
        "Missing information and inconsistencies are flagged.",
        "The draft is generated, watermarked as a draft.",
        "Every requirement is linked back to its authority.",
        "The lawyer reviews, corrects and approves.",
    ]
    cwe = (CW - 0.60) / 2
    for i, st in enumerate(steps):
        col, row = i // 5, i % 5
        x = ML + col * (cwe + 0.60)
        y = 3.50 + row * 1.06
        textbox(s, x, y + 0.04, 0.70, "%02d" % (i + 1), size=20, font=BOLD,
                bold=True, color=BRONZE, line=1.15)
        textbox(s, x + 0.78, y, cwe - 0.78, st, size=20, color=INK, line=1.30)
        if row < 4:
            hline(s, x, y + 0.74, cwe, color=RULE, weight=1.0)
    textbox(s, ML, 8.62, CW,
            "Nothing reaches step 10 automatically. Owner, party identity, "
            "title number, extent, encumbrance status and the exact form all "
            "need explicit lawyer confirmation first.",
            size=19, color=BRONZE, font=ITAL, italic=True, line=1.32,
            tag="s25-foot")

    # ------------------------------------------------------- 26 lawyer loop
    p += 1
    s = new_slide(prs)
    chrome(s, "Design principle", p, TEAM)
    title(s, "Draftly does not replace the lawyer")
    lw = (CW - 0.60) / 2
    rect(s, ML, 3.35, lw, 5.35, fill=CARD, radius=0.16)
    kicker(s, ML + 0.50, 3.78, "The system", w=lw - 1.0, size=24)
    bullet_block(s, ML + 0.50, 4.50, lw - 1.0, [
        "Organises the evidence",
        "Retrieves the applicable authorities",
        "Suggests the workflow steps",
        "Detects potential problems",
        "Produces a reviewable draft",
        "Records the evidence behind every output",
    ], size=20, gap=8, tag="s26-l")
    rect(s, ML + lw + 0.60, 3.35, lw, 5.35, fill=INK, radius=0.16)
    kicker(s, ML + lw + 1.10, 3.78, "The lawyer", w=lw - 1.0, size=24,
           color=BRONZE)
    bullet_block(s, ML + lw + 1.10, 4.50, lw - 1.0, [
        "Reviews the extracted information",
        "Confirms the legal interpretation",
        "Corrects what the system got wrong",
        "Approves the final document",
        "Remains responsible for professional judgment",
    ], size=20, color=CREAM, gap=8, tag="s26-r")
    textbox(s, ML, 9.00, CW,
            "No scan, OCR result or model confidence score is allowed to "
            "record that a physical original was seen. Only a person can.",
            size=21, color=INK, font=ITAL, italic=True, align=PP_ALIGN.CENTER,
            line=1.3, tag="s26-foot")

    # ------------------------------------------------------- 27 evaluation
    p += 1
    s = new_slide(prs)
    chrome(s, "Evaluation", p, TEAM)
    title(s, "How we intend to measure this")
    textbox(s, ML, 3.15, 15.5,
            "Against a gold dataset reviewed by a lawyer. It is being built "
            "now; it does not exist yet.",
            size=21, color=BRONZE, line=1.3)
    cols = [
        ("Retrieval", ["Statute and section recall", "Relevant-case recall",
                       "Precision at k", "Mean reciprocal rank",
                       "Authority-ranking accuracy",
                       "Applicable-version accuracy"]),
        ("Answers", ["Citation correctness",
                     "Faithfulness to retrieved evidence",
                     "Legal completeness", "Unsupported-claim rate",
                     "Abstention accuracy"]),
        ("Workflow", ["Missing-document detection",
                      "Consistency-check accuracy", "Draft completeness",
                      "Time saved against manual work",
                      "Lawyer correction effort"]),
    ]
    cwv = (CW - 2 * 0.42) / 3
    for i, (head, items) in enumerate(cols):
        x = ML + i * (cwv + 0.42)
        rect(s, x, 3.85, cwv, 5.05, fill=(INK if i == 0 else CARD), radius=0.16)
        textbox(s, x + 0.48, 4.25, cwv - 0.96, head, size=26,
                color=(BRONZE if i == 0 else INK), line=1.18)
        bullet_block(s, x + 0.48, 5.05, cwv - 0.96, items, size=19,
                     color=(CREAM if i == 0 else INK), gap=8,
                     tag="s27-%d" % i)

    # ------------------------------------------------------- 28 status
    p += 1
    s = new_slide(prs)
    chrome(s, "Status", p, TEAM)
    title(s, "Where we actually are")
    lw = (CW - 0.60) / 2
    kicker(s, ML, 3.30, "Done", w=lw, size=26)
    bullet_block(s, ML, 4.05, lw, [
        "Three lawyer consultations, scope defined and written up",
        "Statutory corpus built, indexed and reproducible from scripts",
        "Reported case law processed, rules recovered deterministically",
        "Statute links graded and temporally checked against judgment years",
        "RTA rule pack v1 authored, versioned and exported",
        "24 backend services designed; front end and matter workspace built",
    ], size=19, gap=9, tag="s28-l")
    rect(s, ML + lw + 0.60, 3.12, lw, 6.15, fill=INK, radius=0.16)
    kicker(s, ML + lw + 1.10, 3.50, "Not done, and we are saying so",
           w=lw - 1.0, size=26, color=BRONZE)
    bullet_block(s, ML + lw + 1.10, 4.25, lw - 1.0, [
        "Nothing is scored: the gold set has zero rows.",
        "Unreported SC and CoA extraction has not run; the pilot stopped on "
        "an authentication error.",
        "The section parser finds 103 Civil Procedure Code sections; the "
        "section index finds 801.",
        "22 statutes are held as index only, with no text and no official PDF.",
        "397 statute links cite a section that changed after the court spoke.",
        "Every backend service is still at the earliest maturity level.",
    ], size=17, color=CREAM, gap=7, tag="s28-r")

    # ------------------------------------------------------- 29 contributions
    p += 1
    s = new_slide(prs)
    chrome(s, "Contribution", p, TEAM)
    title(s, "Contributions, and what comes next")
    lw = (CW - 0.60) / 2
    kicker(s, ML, 3.30, "Contributions", w=lw, size=26)
    bullet_block(s, ML, 4.05, lw, [
        "A structured Sri Lankan legal corpus with recorded provenance",
        "Modelled relationships between topics, statutes, sections and cases",
        "A version-aware statutory retrieval model",
        "Authority-aware case-law ranking",
        "Evidence-grounded answers that abstain rather than guess",
        "A retrieval-powered conveyancing workflow with a lawyer-review gate",
        "A domain-expert evaluation framework",
    ], size=19, gap=8, tag="s29-l")
    kicker(s, ML + lw + 0.60, 3.30, "Next, in order of what unblocks what",
           w=lw, size=26)
    bullet_block(s, ML + lw + 0.60, 4.05, lw, [
        "Fix the section parser against the Civil Procedure Code and add a "
        "build assertion so a thin index fails loudly",
        "Build the lawyer-reviewed gold set, which blocks every measurement "
        "we want to report",
        "Run the unreported-judgment extraction behind the quote-grounding "
        "gate",
        "Obtain official PDFs for the 22 index-only statutes",
        "Score the retrieval engine and publish the first real numbers",
    ], size=19, gap=8, tag="s29-r")

    # ------------------------------------------------------- 30 close
    p += 1
    s = new_slide(prs, bg=INK)
    rect(s, 0, 0, 0.30, SH, fill=BRONZE, shape=MSO_SHAPE.RECTANGLE)
    textbox(s, ML, EYEBROW_Y, 9.0, "DRAFTLY  |  MID-EVALUATION", size=18,
            font=BOLD, bold=True, color=BRONZE, line=1.05, caps_spacing=0.6)
    textbox(s, ML - 0.10, 3.10, 12.5, "Thank you", size=120, color=CREAM,
            line=1.05)
    hline(s, ML, 5.55, 5.2, color=BRONZE, weight=1.5)
    textbox(s, ML, 5.95, 12.4,
            "Draftly does not begin by generating a deed. It begins by "
            "finding and verifying the law that must govern the deed.",
            size=30, color=CARD, line=1.34)
    textbox(s, 13.89, 8.06, 4.99, "TEAM A", size=24, font=BOLD, bold=True,
            color=BRONZE, align=PP_ALIGN.RIGHT, line=1.05)
    textbox(s, 13.89, 8.55, 4.99, ["Himath Nimpura", "Lahiru", "Praveen"],
            size=21, color=CREAM, align=PP_ALIGN.RIGHT, line=1.42)
    return p
