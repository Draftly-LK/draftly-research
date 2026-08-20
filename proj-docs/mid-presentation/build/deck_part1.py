# -*- coding: utf-8 -*-
"""Draftly mid-evaluation deck - slides 1-14."""
from kit import *
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

TEAM = "Himath  |  Lahiru  |  Praveen"


# ------------------------------------------------------------------ helpers
def stat_card(slide, x, y, w, h, number, label, *, fill=CARD, num_color=BRONZE,
              txt_color=INK, num_size=60, lab_size=19, note=None):
    rect(slide, x, y, w, h, fill=fill, radius=0.14)
    textbox(slide, x + 0.45, y + 0.38, w - 0.9, number, size=num_size,
            font=BOLD, bold=True, color=num_color, line=1.05)
    textbox(slide, x + 0.45, y + 0.38 + num_size * 1.05 / 72.0 + 0.18, w - 0.9,
            label, size=lab_size, color=txt_color, line=1.32)
    if note:
        textbox(slide, x + 0.45, y + h - 0.52, w - 0.9, note, size=15,
                color=BRONZE, font=ITAL, italic=True, line=1.2)


def numbered_card(slide, x, y, w, h, num, head, body, *, fill=CARD,
                  head_size=22, body_size=18, txt=INK, acc=BRONZE):
    rect(slide, x, y, w, h, fill=fill, radius=0.14)
    textbox(slide, x + 0.42, y + 0.34, 1.6, num, size=20, font=BOLD, bold=True,
            color=acc, line=1.05)
    textbox(slide, x + 0.42, y + 0.86, w - 0.84, head, size=head_size,
            color=txt, line=1.22)
    if body:
        textbox(slide, x + 0.42, y + 0.86 + head_size * 1.22 / 72.0 + 0.20,
                w - 0.84, body, size=body_size, color=txt, line=1.36)


def bullet_block(slide, x, y, w, items, *, size=20, color=INK, gap=8, tag=""):
    return textbox(slide, x, y, w, items, size=size, color=color, line=1.34,
                   space=gap, bullet=True, tag=tag)


def chip(slide, x, y, w, h, text, *, fill=CARD, color=INK, size=16, line_col=None):
    rect(slide, x, y, w, h, fill=fill, line=line_col, radius=0.12)
    textbox(slide, x + 0.16, y, w - 0.32, text, size=size, color=color,
            align=PP_ALIGN.CENTER, line=1.22, h=h, anchor=MSO_ANCHOR.MIDDLE)


def arrow(slide, x, y, w=0.30, color=BRONZE):
    sp = slide.shapes.add_shape(MSO_SHAPE.ISOSCELES_TRIANGLE, Inches(x),
                                Inches(y), Inches(w), Inches(w))
    sp.rotation = 90
    sp.fill.solid()
    sp.fill.fore_color.rgb = color
    sp.line.fill.background()
    sp.shadow.inherit = False
    return sp


def flow(slide, y, labels, *, h=1.25, x0=ML, total=CW, size=16,
         fill=CARD, color=INK, gap=0.46, arrow_size=0.26):
    n = len(labels)
    w = (total - gap * (n - 1)) / n
    for i, lab in enumerate(labels):
        x = x0 + i * (w + gap)
        chip(slide, x, y, w, h, lab, fill=fill, color=color, size=size)
        if i < n - 1:
            arrow(slide, x + w + (gap - arrow_size) / 2,
                  y + h / 2 - arrow_size / 2, arrow_size)
    return w


def divider(prs, num, heading, sub, page):
    s = new_slide(prs, bg=INK)
    rect(s, 0, 0, 0.30, SH, fill=BRONZE, shape=MSO_SHAPE.RECTANGLE)
    textbox(s, ML, EYEBROW_Y, 9.0, "SECTION", size=18, font=BOLD, bold=True,
            color=BRONZE, line=1.05, caps_spacing=0.6)
    textbox(s, MR - 5.0, EYEBROW_Y, 5.0, "Draftly  |  Mid-evaluation", size=18,
            font=BOLD, bold=True, color=BRONZE, align=PP_ALIGN.RIGHT, line=1.05)
    textbox(s, ML, 3.05, 6.0, num, size=132, font=BOLD, bold=True, color=BRONZE,
            line=1.02)
    textbox(s, ML, 5.55, 15.0, heading, size=60, color=CREAM, line=1.12)
    hline(s, ML, 7.35, 6.0, color=BRONZE, weight=1.5)
    textbox(s, ML, 7.75, 13.0, sub, size=22, color=CARD, line=1.38)
    textbox(s, 13.89, PAGE_Y, 4.99, str(page), size=16, color=CARD,
            align=PP_ALIGN.RIGHT, line=1.05)
    return s


# ------------------------------------------------------------------ build
def build(prs):
    p = 0

    # ---------------------------------------------------------------- 1 cover
    p += 1
    s = new_slide(prs)
    rect(s, 0, 0, 0.30, SH, fill=BRONZE, shape=MSO_SHAPE.RECTANGLE)
    textbox(s, ML, EYEBROW_Y, 9.0, "MID-EVALUATION  |  2026", size=18, font=BOLD,
            bold=True, color=BRONZE, line=1.05, caps_spacing=0.6)
    textbox(s, ML - 0.10, 2.72, 11.93, "Draftly", size=132, color=INK, line=1.05)
    textbox(s, ML, 4.98, 11.4,
            "An authority-aware legal retrieval and document-drafting "
            "platform for Sri Lankan conveyancing.",
            size=32, color=INK, line=1.30)
    hline(s, ML, 6.90, 5.2, color=BRONZE, weight=1.5)
    textbox(s, ML, 7.30, 11.4,
            "Connecting legal questions, statutory provisions, case law "
            "and professional workflows.",
            size=22, color=BRONZE, font=ITAL, italic=True, line=1.34)
    textbox(s, 13.89, 8.06, 4.99, "TEAM A", size=24, font=BOLD, bold=True,
            color=BRONZE, align=PP_ALIGN.RIGHT, line=1.05)
    textbox(s, 13.89, 8.55, 4.99, ["Himath Nimpura", "Lahiru", "Praveen"],
            size=21, color=INK, align=PP_ALIGN.RIGHT, line=1.42)

    # ---------------------------------------------------------------- 2 agenda
    p += 1
    s = new_slide(prs)
    chrome(s, "Agenda", p, TEAM)
    title(s, "What we will cover")
    items = [
        ("01", "The problem",
         "Why Sri Lankan conveyancing research is slow, and what three lawyer "
         "consultations told us."),
        ("02", "The retrieval engine",
         "The corpus we built, how retrieval is designed, and the research it "
         "rests on."),
        ("03", "The drafting platform",
         "Scope under the Registration of Title Act, the governed rule pack, "
         "and the services behind it."),
        ("04", "Evaluation and status",
         "How we intend to measure this, and what is honestly not done yet."),
    ]
    cw = (CW - 3 * 0.42) / 4
    for i, (n, head, desc) in enumerate(items):
        x = ML + i * (cw + 0.42)
        textbox(s, x, 3.95, cw, n, size=44, font=BOLD, bold=True, color=BRONZE,
                line=1.05)
        hline(s, x, 4.90, cw, color=RULE, weight=1.2)
        textbox(s, x, 5.15, cw, head, size=26, color=INK, line=1.22)
        textbox(s, x, 6.15, cw, desc, size=18, color=INK, line=1.38,
                tag="agenda-" + n)
    rect(s, ML, 7.90, CW, 1.35, fill=INK, radius=0.14)
    textbox(s, ML + 0.55, 7.90, CW - 1.10,
            "One engine, two products: a legal research surface, and a "
            "governed drafting workflow that calls the same engine.",
            size=24, color=CREAM, line=1.30, h=1.35,
            anchor=MSO_ANCHOR.MIDDLE)

    # ---------------------------------------------------------------- 3 divider
    p += 1
    divider(prs, "01", "The problem and domain validation",
            "What a conveyancer has to establish before a single line of a "
            "deed is drafted.", p)

    # ---------------------------------------------------------------- 4 risk
    p += 1
    s = new_slide(prs)
    chrome(s, "The problem", p, TEAM)
    title(s, "A typical conveyancing risk")
    textbox(s, ML, 3.12, 14.0,
            "Before drafting a property-transfer deed, a notary has to settle "
            "all six of these.",
            size=21, color=BRONZE, line=1.3)
    qs = [
        ("01", "Ownership", "Whether the seller legally owns the property."),
        ("02", "Identification",
         "Whether the land is correctly and unambiguously identified."),
        ("03", "Encumbrances",
         "Whether mortgages, charges or other burdens exist."),
        ("04", "Provisions and forms",
         "Which provisions and prescribed forms govern it."),
        ("05", "Case law",
         "Whether any judgment affects how the transaction must be handled."),
        ("06", "Execution",
         "Whether every execution and attestation requirement is satisfied."),
    ]
    cw = (CW - 2 * 0.36) / 3
    for i, (n, head, body) in enumerate(qs):
        x = ML + (i % 3) * (cw + 0.36)
        y = 3.80 + (i // 3) * 2.45
        numbered_card(s, x, y, cw, 2.30, n, head, body, head_size=23,
                      body_size=18)
    textbox(s, ML, 8.95, CW,
            "One overlooked issue can make the transaction invalid, and the "
            "professional consequences land on the notary.",
            size=22, color=INK, font=ITAL, italic=True, line=1.3, tag="s4-foot")

    # ---------------------------------------------------------------- 5 landscape
    p += 1
    s = new_slide(prs)
    chrome(s, "The problem", p, TEAM)
    title(s, "Sri Lanka's legal information landscape")
    textbox(s, ML, 3.30, 8.4, "The law that governs one deed is spread across:",
            size=21, color=BRONZE, line=1.3)
    sources = ["Statutes and Ordinances", "Amendments",
               "Regulations and gazettes", "Court judgments",
               "Common-law and equitable principles", "Prescribed forms",
               "Registration rules", "Administrative procedures"]
    for i, srcname in enumerate(sources):
        y = 4.00 + i * 0.62
        dot(s, ML + 0.03, y + 0.11, 0.15)
        textbox(s, ML + 0.46, y, 7.6, srcname, size=21, color=INK, line=1.25)
    rect(s, 10.40, 3.30, 8.48, 5.35, fill=INK, radius=0.16)
    textbox(s, 10.95, 3.95, 7.38,
            "None of it exists in one unified, searchable source.",
            size=38, color=CREAM, line=1.24)
    hline(s, 10.95, 6.15, 3.2, color=BRONZE, weight=1.5)
    textbox(s, 10.95, 6.50, 7.38,
            "A practitioner assembles the answer by hand, from several "
            "publishers, in several formats, with no guarantee that the "
            "version in front of them is the one that applied on the relevant "
            "date.",
            size=20, color=CARD, line=1.40, tag="s5-panel")

    # ---------------------------------------------------------------- 6 search
    p += 1
    s = new_slide(prs)
    chrome(s, "The problem", p, TEAM)
    title(s, "Why ordinary legal search is not enough")
    lw = (CW - 0.60) / 2
    rect(s, ML, 3.30, lw, 5.30, fill=CARD, radius=0.16)
    kicker(s, ML + 0.50, 3.72, "What keyword search gives you", w=lw - 1.0,
           size=23)
    bullet_block(s, ML + 0.50, 4.45, lw - 1.0, [
        "Documents that contain your words",
        "Ranking by term frequency, not legal authority",
        "No idea which version of a section was in force",
        "No link between a judgment and the section it interprets",
    ], size=20, tag="s6-left")
    rect(s, ML + lw + 0.60, 3.30, lw, 5.30, fill=INK, radius=0.16)
    kicker(s, ML + lw + 1.10, 3.72, "What a conveyancer needs", w=lw - 1.0,
           size=23, color=BRONZE)
    bullet_block(s, ML + lw + 1.10, 4.45, lw - 1.0, [
        "The topic resolved to the correct statutory section",
        "Aliases and historical statute names resolved",
        "The version of the provision that applied on the date",
        "Cases ranked by court hierarchy and precedential weight",
        "The legal principle pulled out of the judgment",
        "An answer that abstains when the evidence is thin",
    ], size=20, color=CREAM, tag="s6-right")
    textbox(s, ML, 8.95, CW,
            "The problem is not finding documents. It is finding the correct, "
            "applicable and authoritative legal rule.",
            size=24, color=INK, font=ITAL, italic=True, align=PP_ALIGN.CENTER,
            line=1.3, tag="s6-foot")

    # ---------------------------------------------------------------- 7 validation
    p += 1
    s = new_slide(prs)
    chrome(s, "Domain validation", p, TEAM)
    title(s, "We checked the problem with practitioners")
    rect(s, ML, 3.35, 6.30, 5.95, fill=INK, radius=0.16)
    textbox(s, ML + 0.55, 3.78, 5.2, "3", size=132, font=BOLD, bold=True,
            color=BRONZE, line=1.02)
    textbox(s, ML + 0.55, 5.95, 5.2,
            "consultations with practising lawyers and legal experts",
            size=24, color=CREAM, line=1.32)
    hline(s, ML + 0.55, 7.30, 3.0, color=BRONZE, weight=1.5)
    textbox(s, ML + 0.55, 7.62, 5.2,
            "The main consultation was with a practising lawyer and notary who "
            "also lectures at Sri Lanka Law College.",
            size=18, color=CARD, line=1.34, tag="s7-panel")
    kicker(s, 8.30, 3.35, "What they gave us", w=10.5, size=24)
    bullet_block(s, 8.30, 4.10, 10.58, [
        "The complete conveyancing workflow, end to end",
        "The mistakes and professional risks that actually occur",
        "Real checklists and sample documents",
        "How the different registration regimes differ",
        "The information a notary needs at each step",
        "A defensible initial scope for the system",
        "The shape of a lawyer-review process",
    ], size=20, gap=9, tag="s7-right")

    # ---------------------------------------------------------------- 8 findings
    p += 1
    s = new_slide(prs)
    chrome(s, "Domain validation", p, TEAM)
    title(s, "What the consultations exposed")
    findings = [
        "Registration does not establish valid ownership the same way under "
        "every regime.",
        "Fraudulent deeds and impersonation can go undetected.",
        "The notary carries the duty to verify identity, title, encumbrances "
        "and jurisdiction.",
        "Procedural rules are distributed across several legal sources.",
        "Junior notaries lack knowledge that normally takes years of practice "
        "to build.",
        "General AI tools generate text that does not follow the required Sri "
        "Lankan structure.",
        "Practitioners want workflow guidance, not exam-style legal answers.",
    ]
    cw2 = (CW - 0.60) / 2
    for i, f in enumerate(findings):
        col, row = i // 4, i % 4
        x = ML + col * (cw2 + 0.60)
        y = 3.45 + row * 1.42
        textbox(s, x, y, 0.80, "%02d" % (i + 1), size=22, font=BOLD, bold=True,
                color=BRONZE, line=1.15)
        textbox(s, x + 0.90, y, cw2 - 0.90, f, size=20, color=INK, line=1.34)
        hline(s, x, y + 1.16, cw2, color=RULE, weight=1.0)
    textbox(s, ML, 9.15, CW,
            "Each of these became a design constraint, not a feature request.",
            size=21, color=BRONZE, font=ITAL, italic=True, line=1.3,
            tag="s8-foot")

    # ---------------------------------------------------------------- 9 divider
    p += 1
    divider(prs, "02", "The retrieval engine",
            "The corpus, the retrieval design, and the research it is built "
            "on.", p)

    # ---------------------------------------------------------------- 10 chain
    p += 1
    s = new_slide(prs)
    chrome(s, "Retrieval engine", p, TEAM)
    title(s, "Draftly's core solution")
    textbox(s, ML, 3.20, 15.5,
            "Draftly is built around an authority-aware legal retrieval engine "
            "for Sri Lankan law. It connects:",
            size=21, color=BRONZE, line=1.3)
    flow(s, 4.05, ["Legal question", "Topic", "Statute", "Section",
                   "Applicable version", "Relevant cases", "Legal principle",
                   "Supporting evidence"],
         h=1.35, size=16, gap=0.34)
    hline(s, ML, 6.20, CW, color=RULE, weight=1.0)
    cw3 = (CW - 0.80) / 2
    kicker(s, ML, 6.60, "Independent legal research", w=cw3, size=24)
    textbox(s, ML, 7.35, cw3,
            "A lawyer asks a question and gets back the statutes, sections, "
            "cases and legal principles that govern it, each with the passage "
            "it came from.",
            size=20, color=INK, line=1.40, tag="s10-l")
    kicker(s, ML + cw3 + 0.80, 6.60, "Evidence-grounded drafting", w=cw3,
           size=24)
    textbox(s, ML + cw3 + 0.80, 7.35, cw3,
            "The drafting workflow calls the same engine to find the rules "
            "that govern each professional step. Retrieval is the foundation, "
            "not a side feature.",
            size=20, color=INK, line=1.40, tag="s10-r")

    # ---------------------------------------------------------------- 11 model
    p += 1
    s = new_slide(prs)
    chrome(s, "Retrieval engine", p, TEAM)
    title(s, "The legal relationship model")
    row1 = ["Legal topic", "Statute", "Section", "Applicable version"]
    w1 = flow(s, 3.95, row1, h=1.40, size=20, gap=0.52)
    x_last = ML + 3 * (w1 + 0.52)
    vline(s, x_last + w1 / 2, 5.35, 0.95, color=BRONZE, weight=1.5)
    arrow(s, x_last + w1 / 2 - 0.13, 6.20, 0.26)
    row2 = ["Professional workflow", "Legal principle", "Judgment"]
    n2 = len(row2)
    w2 = (CW - 0.52 * (n2 - 1)) / n2
    for i, lab in enumerate(row2):
        x = ML + i * (w2 + 0.52)
        chip(s, x, 6.55, w2, 1.40, lab, fill=INK, color=CREAM, size=20)
        if i > 0:
            a = arrow(s, x - (0.52 + 0.26) / 2, 6.55 + 0.70 - 0.13, 0.26)
            a.rotation = 270
    textbox(s, ML, 8.55, CW,
            "Modelling the relationships, rather than storing isolated text "
            "chunks, is what lets the system answer with connected evidence: "
            "this section, in this version, as this court read it.",
            size=21, color=INK, line=1.40, tag="s11-foot")

    # ---------------------------------------------------------------- 12 sources
    p += 1
    s = new_slide(prs)
    chrome(s, "Retrieval engine", p, TEAM)
    title(s, "Where the legal data comes from")
    lw = (CW - 0.60) / 2
    rect(s, ML, 3.30, lw, 5.55, fill=CARD, radius=0.16)
    kicker(s, ML + 0.50, 3.72, "In the corpus today", w=lw - 1.0, size=23)
    bullet_block(s, ML + 0.50, 4.45, lw - 1.0, [
        "Statutes and Ordinances  —  parliament.lk",
        "Amendments and historical provisions  —  LawLanka",
        "Reported judgments with editor headnotes  —  CommonLII",
        "Unreported Supreme Court and Court of Appeal judgments",
        "Commencement dates harvested from srilankalaw.lk",
    ], size=19, gap=10, tag="s12-l")
    rect(s, ML + lw + 0.60, 3.30, lw, 5.55, fill=INK, radius=0.16)
    kicker(s, ML + lw + 1.10, 3.72, "Planned", w=lw - 1.0, size=23, color=BRONZE)
    bullet_block(s, ML + lw + 1.10, 4.45, lw - 1.0, [
        "Regulations and gazettes",
        "Prescribed legal forms, taken from the gazettes",
        "Sri Lanka Law Reports",
        "Lawyer-provided checklists and practice materials",
        "Official PDFs for the 22 statutes we hold as index only",
    ], size=19, color=CREAM, gap=10, tag="s12-r")
    textbox(s, ML, 9.10, CW,
            "Every source is registered with its provenance and rights status "
            "before anything downstream is allowed to use it.",
            size=19, color=BRONZE, font=ITAL, italic=True, line=1.3,
            tag="s12-foot")

    # ---------------------------------------------------------------- 13 corpus
    p += 1
    s = new_slide(prs)
    chrome(s, "Retrieval engine", p, TEAM)
    title(s, "The corpus as it stands")
    stats = [
        ("57 + 18", "statutes and amendments converted to markdown"),
        ("5,770", "sections indexed across 66 statutes"),
        ("872", "amendment actions, one per amending instrument"),
        ("3,703", "reported CommonLII judgments with headnotes"),
        ("5,474", "unreported Supreme Court and Court of Appeal judgments"),
        ("14,665", "case-to-statute mentions, all still unverified"),
    ]
    cw4 = (CW - 2 * 0.36) / 3
    for i, (num, lab) in enumerate(stats):
        x = ML + (i % 3) * (cw4 + 0.36)
        y = 3.45 + (i // 3) * 2.55
        stat_card(s, x, y, cw4, 2.32, num, lab, num_size=54, lab_size=19)
    textbox(s, ML, 8.75, CW,
            "A snapshot, not a final figure. Nothing in this table has been "
            "signed off by a lawyer, so everything downstream carries "
            "status = unverified.",
            size=20, color=BRONZE, font=ITAL, italic=True, line=1.34,
            tag="s13-foot")

    # ---------------------------------------------------------------- 14 recovery
    p += 1
    s = new_slide(prs)
    chrome(s, "Retrieval engine", p, TEAM)
    title(s, "Recovering the rule from reported judgments")
    rect(s, ML, 3.35, 6.90, 5.60, fill=INK, radius=0.16)
    textbox(s, ML + 0.55, 3.85, 5.8, "95.1%", size=96, font=BOLD, bold=True,
            color=BRONZE, line=1.02)
    textbox(s, ML + 0.55, 5.55, 5.8,
            "3,521 of 3,703 judgments yield a legal rule, read straight off "
            "the NLR / SLR headnote layout.",
            size=22, color=CREAM, line=1.34)
    hline(s, ML + 0.55, 7.35, 3.0, color=BRONZE, weight=1.5)
    textbox(s, ML + 0.55, 7.70, 5.8,
            "Deterministic and verbatim. The 182 that abstain fall through to "
            "a bounded LLM track with a quote-grounding gate.",
            size=18, color=CARD, line=1.34, tag="s14-panel")
    rows = [
        ("11,739", "distinct catchword terms indexed, covering 3,461 cases"),
        ("2,512", "graded statute links, each carrying a confidence grade"),
        ("531", "section bundles: every judgment held to turn on one section"),
        ("810 → 94", "links that failed for want of an index entry"),
    ]
    for i, (num, lab) in enumerate(rows):
        y = 3.35 + i * 1.28
        textbox(s, 8.85, y, 3.20, num, size=34, font=BOLD, bold=True,
                color=BRONZE, line=1.10)
        textbox(s, 12.25, y + 0.10, 6.63, lab, size=19, color=INK, line=1.34)
        if i < 3:
            hline(s, 8.85, y + 1.06, 10.03, color=RULE, weight=1.0)
    textbox(s, 8.85, 8.35, 10.03,
            "Bundles invert the corpus from “what does this case say?” "
            "to “what have the courts held about this section?”, which "
            "is the question a conveyancer actually asks.",
            size=19, color=BRONZE, font=ITAL, italic=True, line=1.36,
            tag="s14-foot")

    return p
