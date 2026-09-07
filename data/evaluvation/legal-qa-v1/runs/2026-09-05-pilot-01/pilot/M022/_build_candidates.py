"""Generator for M022 candidate-authorities.json.

Every excerpt is pulled verbatim from the repository file at the recorded pointer
and asserted to be a substring of that file, so nothing is retyped from memory.
Run from the repo root:  python <this file>
"""
import json, hashlib, re

R = 'data/evaluvation/legal-qa-v1/runs/2026-09-05-pilot-01/pilot/M022/'


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def load(p):
    return json.load(open(p, encoding='utf-8'))


def node(t, ptr):
    n = t
    for p in ptr.strip('/').split('/'):
        n = n[int(p)] if p.isdigit() else n[p]
    return n


def fulltext(n):
    out = [n.get('raw_text', '')]
    for c in n.get('children') or []:
        out.append(fulltext(c))
    return ' '.join(x for x in out if x)


NOT = 'data/processed/canonical-statutes/SRC014-1-1907.json'
POF = 'data/processed/canonical-statutes/SRC001-7-1840.json'
CA = 'data/processed/canonical-statutes/SRC031-7-2007.json'
NOTPDF = 'data/legal-sources/library/statutes/1-1907-notaries-ordinance.pdf'
POFPDF = 'data/legal-sources/library/statutes/7-1840-prevention-of-frauds-ordinance.pdf'
CAPDF = 'data/legal-sources/library/statutes/7-2007-companies-act.pdf'
A22 = 'data/processed/docs/amendments/src015-notaries-amendment-act.md'
A24 = 'data/processed/docs/amendments/src016-notaries-amendment-act.md'
A22PDF = 'data/legal-sources/library/amendments/31-2022-notaries-amendment-act.pdf'
A24PDF = 'data/legal-sources/library/amendments/6-2024-notaries-amendment-act.pdf'
tn = load(NOT); tp = load(POF); tc = load(CA)
H = {p: sha(p) for p in [NOT, POF, CA, NOTPDF, POFPDF, CAPDF, A22, A24, A22PDF, A24PDF]}

RUN = '2026-09-05-pilot-01'; AG = 'research-agent-B'; M = 'M022'; Q1 = 'M022-Q01'; Q2 = 'M022-Q02'
TEMP_NOT = (
    "TEMPORAL: tree edition is the lankalaw copy of the 1980 Revised Legislative Enactments (Cap. 110) text; header lists amendments up to Act 12 of 2005 (which data/processed/lankalaw-catalogue.csv identifies as the Increase of Fines Act). "
    "section_versions.jsonl gives SRC014 s31/s32 a single version v1 (valid_from 1907-03-27, amendment_history 'unknown'); actions.csv has no SRC014 rows. "
    "Notaries (Amendment) Act No. 31 of 2022 (SRC015) and No. 6 of 2024 (SRC016) post-date the October 2020 exam and are NOT incorporated in the tree text. "
    "However the 2022 Act quotes pre-2022 wording of rule 16(a) ('the assessment number and the name, if any, of the street') and rule 30 ('registered power of attorney') that differs from the tree text, so at least one pre-2022 amendment is missing from this consolidation; "
    "the October 2020 wording of any s.31 rule therefore cannot be confirmed from repo files -> applicable_version_for_matter_date should be 'history_unknown' unless the verifier can source the 2005-2020 text.")

auths = []


def add(aid, atype, title, enact, section, subsection, paths, methods, scores, reason, qids, nec, case_cit=None, court=None, date=None):
    auths.append({
        "authority_id": aid, "authority_type": atype, "title": title, "enactment_number": enact, "section": section, "subsection": subsection,
        "case_citation": case_cit, "court": court, "decision_date": date, "candidate_source_paths": paths, "retrieval_methods": methods,
        "retrieval_scores": scores, "candidate_reason": reason, "proposed_by_agent": AG, "benchmark_question_ids": qids,
        "necessity_claimed": nec, "verification_status": "candidate", "verification": None})


EX = {}


def notary_rule(key, aid, ptr, sec, sub, qids, nec, why, pdfpage, extra_temporal, methods, scores):
    n = node(tn, ptr); ex = fulltext(n); EX[key] = ex
    reason = (f"Notaries Ordinance s.{sec}{'(' + sub + ')' if sub else ''}. LOCATED. Tree: {NOT} (sha256 {H[NOT]}), json_pointer {ptr}, node type={n.get('type')} number={n.get('number')}. "
              f"Registry PDF (official RGD): {NOTPDF} (sha256 {H[NOTPDF]}), pdftotext -layout page {pdfpage}. "
              f"VERBATIM EXCERPT (raw_text of node and its children, joined with single spaces): \"{ex}\" WHY: {why} {TEMP_NOT} {extra_temporal}")
    add(aid, "statute_provision", "Notaries Ordinance", "Ordinance No. 1 of 1907", sec, sub,
        [NOT, NOTPDF, 'data/processed/docs/statutes/src014-notaries-ordinance.md'], methods, scores, reason, qids, nec)


notary_rule('r25', "AUTH-M022-001", "/body/30/children/24", "31", "25", [Q1, Q2], "indispensable",
            "Governs a deed 'executed or acknowledged before more than one notary': (a) the notary who first attests complies with ALL of rule (20) while every other attesting notary complies with paragraphs (a)-(e) and (g) (signatures/serial number); (b) each notary numbers the deed; (c) first notary keeps the protocol, others a certified copy; (d) each complies as far as possible with the rest of s.31. This is the direct answer to both questions.",
            "9-10 (marginal note 'Deeds executed before more than one notary.')",
            "2022 Act s.16 (items 1-14) and 2024 Act s.3 (items 1-10) as read in the repo texts do not mention rule (25).",
            ["manual_corpus_browse", "hierarchical_act_section", "bm25"],
            {"bm25_query_more_than_one_notary_first_attests": "not in top 10 (SRC014:s30, s41, s26 returned)", "tree_browse": "located by heading scan of section 31"})
notary_rule('r20', "AUTH-M022-002", "/body/30/children/19", "31", "20", [Q2, Q1], "indispensable",
            "Lists what a notary must state in his attestation: (a) signed in his presence and in presence of one another; (b) whether executant or witnesses known to him (specifying which witnesses); (c) day, month, year, place, full names and residences of witnesses; (d) read over / read and explained; (e) whether consideration paid in his presence and amount; (f) number and value of stamps on deed and duplicate; (g) erasures, alterations, interpolations. Rule (25)(a) makes the first notary comply with all of it.",
            "8-9 (paragraphs (d)-(g) confirmed on page 9 with marginal note 'Form of attestation' beside rule 21)",
            "2022 Act s.16(11) repealed and replaced paragraphs (b) and (e) and added (h) (wills); 2024 Act s.3(7) substituted paragraph (g). Both post-date October 2020. The 2022 Act's edit to (g) ('affixed thereto.' -> 'affixed thereto; and') matches the tree's closing words, consistent with the tree (g) being the pre-2022 text.",
            ["manual_corpus_browse", "hierarchical_act_section", "bm25", "case_statute_link"],
            {"bm25_query_attestation_shall_state": "SRC014:s35 rank 1, SRC015:s31 rank 2; section 31 node not surfaced", "case_statute_section_links": "LKCA-1954-80, LKCA-1962-72, LKCA-1960-2 link to 30(20)/31(2)(e) (old numbering)"})
notary_rule('r21', "AUTH-M022-003", "/body/30/children/20", "31", "21", [Q2], "supporting",
            "Attestation must be substantially in Form E of the Second Schedule, legibly signed in the language of the deed and with usual signature; erasures in the attestation authenticated with initials. Form E itself is NOT present in the tree (schedules []).",
            "9", "2022 Act s.22(2) repealed and substituted Form E (post-dates matter). Form E text as at 2020 not located in repo.", ["manual_corpus_browse"], {})
n32 = node(tn, "/body/31/children/1"); EX['s32'] = fulltext(n32)
add("AUTH-M022-004", "statute_provision", "Notaries Ordinance", "Ordinance No. 1 of 1907", "32", "2", [NOT, NOTPDF], ["manual_corpus_browse", "bm25"],
    {"bm25_query_section_32_two_or_more_parties_not_same_time_place": "SRC014:s32 rank 4 (score 0.097679)"},
    f"Notaries Ordinance s.32(2). LOCATED. Tree {NOT} (sha256 {H[NOT]}) json_pointer /body/31/children/1 (subsection 2 with subparagraphs i-iii at /children/0..2). RGD PDF {NOTPDF} (sha256 {H[NOTPDF]}) page 12. VERBATIM EXCERPT: \"{EX['s32']}\" WHY: expressly contemplates a deed 'to be executed by two or more parties, both or all of whom ... do not sign the deed or instrument at the same time and place' and fixes how rules (6),(7),(23),(25) [first signing] and rules (18),(20) [each signing] apply - the statutory basis for the lessor signing in Galle and the company in Colombo before different notaries. {TEMP_NOT} Neither the 2022 nor the 2024 Act text in the repo mentions section 32.",
    [Q1, Q2], "indispensable")
notary_rule('r28', "AUTH-M022-005", "/body/30/children/27", "31", "28", [Q1, Q2], "supporting",
            "Where a deed is executed by two or more parties before more than one notary, the duplicate is transmitted by the notary who first attests to the Registrar of Lands of his district; other notaries need not transmit a duplicate.",
            "10 (marginal note 'Transmission to the Registrar of Lands of deeds executed before different notaries.')",
            "Node carries amendment_events [10, Law 20 of 1976] (operation unknown). Not mentioned in the 2022/2024 Act texts.", ["manual_corpus_browse", "amendment_metadata"], {})
notary_rule('r9', "AUTH-M022-006", "/body/30/children/8", "31", "9", [Q1, Q2], "indispensable",
            "Notary may not attest unless the executant is known to him or to at least two attesting witnesses (with a declaration by the witnesses). Scenario: Anil Fernando does not know Russel Perera; Ruwan Perera is Russel's own notary - a reason the lessor executes before Ruwan.",
            "8 (not confirmed by page grep; rule falls between rules 8 and 11 on pages 8-9)",
            "2022 Act s.16(6) substituted the opening words of rule (9) (identity by NIC/passport/licence) and 2024 Act s.3(3) further amended it; both post-date October 2020.", ["manual_corpus_browse"], {})
notary_rule('r10', "AUTH-M022-007", "/body/30/children/9", "31", "10", [Q1], "supporting",
            "Absolute bar where both executant and witnesses are unknown to the notary.", "8 (not confirmed by page grep)",
            "2024 Act s.3(4) REPEALED rule (10) (post-dates October 2020, so the rule was in force at the matter date subject to the unknown 2005-2020 history).", ["manual_corpus_browse"], {})
notary_rule('r22', "AUTH-M022-008", "/body/30/children/21", "31", "22", [Q1], "indispensable",
            "A notary may not attest in any area other than that in which he is authorized to practise: Anil Fernando (Colombo) cannot attest in Galle and Ruwan Perera (Galle) cannot attest in Colombo, so each party's signature must be attested by the notary of the place where it is given.",
            "9 (marginal note 'Deed not to be attested outside notary's jurisdiction...')", "Not mentioned in the 2022/2024 Act texts.", ["manual_corpus_browse"], {})
notary_rule('r12', "AUTH-M022-009", "/body/30/children/11", "31", "12", [Q1, Q2], "supporting",
            "Executant and witnesses must sign in the notary's presence and in the presence of one another, and the notary in theirs - the fact the attestation paragraph (a) records.",
            "8 (not confirmed by page grep)", "Not mentioned in the 2022/2024 Act texts.", ["manual_corpus_browse"], {})
notary_rule('r23', "AUTH-M022-010", "/body/30/children/22", "31", "23", [Q2], "supporting",
            "Consecutive numbering; rule (25)(b) requires every attesting notary to number the deed under this rule, and rule (20)(g)/(25)(a) refer to erasures in 'his serial number'.",
            "9", "Not mentioned in the 2022/2024 Act texts.", ["manual_corpus_browse"], {})
notary_rule('r24', "AUTH-M022-011", "/body/30/children/23", "31", "24", [Q1], "supporting",
            "Protocol duty; rule (25)(c) places it on the first attesting notary, the other notary keeping a certified copy.", "9",
            "Not mentioned in the 2022/2024 Act texts.", ["manual_corpus_browse"], {})
notary_rule('r18', "AUTH-M022-012", "/body/30/children/17", "31", "18", [Q2], "supporting",
            "Day, month, year and place of execution to be inserted in letters and signed; s.32(2)(ii) applies this rule to each separate signing.",
            "8 (not confirmed by page grep)", "Not mentioned in the 2022/2024 Act texts.", ["manual_corpus_browse"], {})
notary_rule('r29', "AUTH-M022-013", "/body/30/children/28", "31", "29", [Q1], "supporting",
            "Where the land lies in a district other than the transmitting notary's, a certified copy and list go to the Registrar of Lands of the district where the land is situated (warehouse in Galle).",
            "10-11", "2024 Act s.3(9) changed 'Form F' to 'Form F 1' in this rule (post-dates matter).", ["manual_corpus_browse"], {})
notary_rule('r30', "AUTH-M022-014", "/body/30/children/29", "31", "30", [Q1], "supporting",
            "Recognises execution 'by means of an attorney' - an alternative route if Russel Perera will not travel and does not want a second notary. The Powers of Attorney Ordinance itself was not opened for this matter.",
            "11 (not confirmed by page grep)",
            "2022 Act s.16(13) and 2024 Act s.3(10) substituted the closing words; the 2022 Act quotes the pre-2022 words as 'registered power of attorney', which differ from this tree's 'power of attorney' - evidence the tree is not the October 2020 text.",
            ["manual_corpus_browse", "bm25"], {"bm25_query_power_of_attorney_execute_deed": "SRC019:s3A rank 1; SRC014 rule 30 not surfaced"})
notary_rule('r14', "AUTH-M022-015", "/body/30/children/13", "31", "14", [Q2], "supporting",
            "Notary must ascertain full names before signing and, if the signature differs from the name given, describe the party/witness by both names in the attestation.",
            "8 (not confirmed by page grep)", "2022 Act s.16(7) substituted rule (14) (corporate seal, board resolution) - post-dates matter.", ["manual_corpus_browse"], {})
notary_rule('r2', "AUTH-M022-016", "/body/30/children/1", "31", "2", [Q1], "supporting",
            "A notary may not attest a deed drawn in Sri Lanka by another person unless a certificate signed by a notary that he drew it is endorsed: relevant because Ruwan Perera drafts and Anil Fernando also attests.",
            "7-8 (not confirmed by page grep)", "Not mentioned in the 2022/2024 Act texts.", ["manual_corpus_browse"], {})

# Prevention of Frauds Ordinance
EX['pof2'] = fulltext(node(tp, "/body/1"))
add("AUTH-M022-017", "statute_provision", "Prevention of Frauds Ordinance", "Ordinance No. 7 of 1840", "2", None, [POF, POFPDF], ["bm25", "dense", "manual_corpus_browse"],
    {"bm25_query_lease_before_notary_two_witnesses": "SRC001:s2 rank 1 (score 0.135768)"},
    f"Prevention of Frauds Ordinance s.2. LOCATED. Tree {POF} (sha256 {H[POF]}, edition lankalaw 1980 revision HTML, verification_status unverified) json_pointer /body/1; node amendment_events [2, 60 of 1947]. VERBATIM EXCERPT: \"{EX['pof2']}\" WHY: a lease of immovable property (other than a lease at will or not exceeding one month) is a 'contract or agreement ... for establishing any ... interest ... affecting land' and must be in writing signed before a licensed notary and two witnesses and attested. TEMPORAL: amendment-chains.csv lists 16/1852, 11/1896, 60/1947, Act 30/2022, Act 4/2024; the registry PDF {POFPDF} (sha256 {H[POFPDF]}, LankaLaw consolidated 2024) page 1 shows the s.2 text AS AMENDED by 30/2022 and 4/2024 (subsections (1)(a),(b),(2)), which differs from the tree; the tree wording (last event 60 of 1947) is the candidate October 2020 wording but is unverified.",
    [Q1], "indispensable")
EX['pof16'] = fulltext(node(tp, "/body/15"))
add("AUTH-M022-018", "statute_provision", "Prevention of Frauds Ordinance", "Ordinance No. 7 of 1840", "16", None, [POF, POFPDF], ["bm25", "manual_corpus_browse"],
    {"bm25_query_more_than_one_notary": "SRC001:s16 rank 4"},
    f"Prevention of Frauds Ordinance s.16. LOCATED. Tree {POF} (sha256 {H[POF]}) json_pointer /body/15. VERBATIM EXCERPT: \"{EX['pof16']}\" WHY: deeds required to be notarially executed must be in duplicate - the duplicate is what rule (28) makes the first notary transmit. TEMPORAL: registry PDF {POFPDF} page 6 shows the section as amended by Act 30 of 2022 to read 'triplicate' (marginal '[5, 30 of 2022]'); the tree's 'duplicate' wording is the pre-2022 (candidate October 2020) text, unverified.",
    [Q1], "supporting")
EX['ca19'] = fulltext(node(tc, "/body/1/children/4/children/0"))
add("AUTH-M022-019", "statute_provision", "Companies Act", "Act No. 7 of 2007", "19", "1(a)", [CA, CAPDF], ["bm25", "hierarchical_act_section"],
    {"bm25_query_companies_act_s19": "SRC031:s19 rank 1 (score 0.066393)"},
    f"Companies Act s.19(1)(a). LOCATED. Tree {CA} (sha256 {H[CA]}, verification_status structurally_verified, amendments none_listed_in_source_header) json_pointer /body/1/children/4/children/0 (Part 'COMPANY CONTRACTS ETC.'). Official DRC PDF {CAPDF} (sha256 {H[CAPDF]}) pdftotext page 42. VERBATIM EXCERPT: \"{EX['ca19']}\" WHY: an obligation that a natural person must sign and have notarially attested may be entered into on behalf of the company in writing signed under the company's name by two directors (or the sole director, persons under the articles, or attorneys) 'and be notarially executed' - the mechanics of the company's execution. TEMPORAL: Act of 2007 pre-dates matter; actions.csv and amendment-chains.csv have no SRC031 rows; companies-act-amendments-english.pdf in the library has no hit for section 19.",
    [Q1], "indispensable")

# post-matter amendments (temporal context)
a22 = open(A22, encoding='utf-8').read(); a24 = open(A24, encoding='utf-8').read()
i = a22.find('(11) in rule (20) thereof'); ex22 = a22[i:a22.find('(c) in paragraph (g) thereof', i)].strip(); assert ex22 and ex22 in a22
EX['a22'] = ex22
add("AUTH-M022-020", "amendment", "Notaries (Amendment) Act", "Act No. 31 of 2022", "16", "11", [A22, A22PDF], ["amendment_metadata", "bm25"],
    {"bm25_query_attestation_shall_state": "SRC015:s31 rank 2"},
    f"Notaries (Amendment) Act No. 31 of 2022 s.16(11) (amending s.31 rule 20) and s.22(2) (new Form E). LOCATED in OCR text {A22} (sha256 {H[A22]}; converter docling+rapidocr, OCR errors present) from registry PDF {A22PDF} (sha256 {H[A22PDF]}, image-only, pdftotext returns nothing). EXCERPT (OCR, 'Page 13' block of the md): \"{ex22}\" WHY: POST-DATES the October 2020 matter (certified 2022). Recorded so the verifier can see that paragraphs (b) and (e) of rule (20) and Form E were changed after the matter date; rules (25), (28) and s.32 are not mentioned in this Act. Necessity: temporal context only.",
    [Q2, Q1], "supporting")
i = a24.find('in rule (20) thereof'); ex24 = a24[i:i + 420].strip(); assert ex24 and ex24 in a24
EX['a24'] = ex24
add("AUTH-M022-021", "amendment", "Notaries (Amendment) Act", "Act No. 6 of 2024", "3", "7", [A24, A24PDF], ["amendment_metadata", "bm25"],
    {"bm25_query_duplicate_first_attests": "SRC016:s31 rank 1"},
    f"Notaries (Amendment) Act No. 6 of 2024 s.3(7) (substitutes rule 20(g)) and s.3(4) (repeals rule 10). LOCATED in {A24} (sha256 {H[A24]}) from registry PDF {A24PDF} (sha256 {H[A24PDF]}, text layer present; pages 3-4). EXCERPT: \"{ex24}\" WHY: POST-DATES the October 2020 matter (certified 31 January 2024). Temporal context only: shows rule 20(g) and rule 10 wording changed after the matter date; rules (25), (28) and s.32 not touched.",
    [Q2, Q1], "supporting")


# cases (opened; excerpt asserted verbatim)
def case(key, aid, path, title, cit, court, date, regex, qids, why, nec):
    t = open(path, encoding='utf-8').read(); m = re.search(regex, t, re.S); assert m, aid
    ex = m.group(0); assert ex in t; EX[key] = ex
    add(aid, "case", title, None, None, None, [path], ["case_statute_link", "case_fulltext_search"], {"case_statute_section_links.csv": "linked to SRC014"},
        f"Judgment text OPENED at {path} (sha256 {sha(path)}; cases.jsonl status unverified; text is a CommonLII NLR transcription). VERBATIM EXCERPT: \"{ex}\" WHY: {why} The section numbers cited in the judgment follow the older Chapter numbering (s.30/s.29), not the current s.31; the mapping to s.31 is the agent's inference, not stated in the judgment.",
        qids, nec, case_cit=cit, court=court, date=date)


case('c1954', "AUTH-M022-022", 'data/processed/docs/case-law/commonlii/LKCA/1954/80.md', "Edwin De Silva v. Karunadasa De Silva", "(1954) 56 NLR 1",
     "Supreme Court of Ceylon (reported in NLR; CommonLII database LKCA)", "1954-08-04",
     r"The term \" attestation \" in section 162 \(1\) includes both the subscription of the signature and the attestation clause\.", [Q2],
     "Headnote: 'attestation' includes both the notary's signature and the attestation clause; the judgment relies on the Notaries Ordinance side-note 'Attestation' beside the rule beginning 'He shall without delay duly attest every deed or instrument ... and shall sign and seal such attestation' (then s.30(20)). Supports the proposition that the first notary's attestation is the clause in which the rule (20) matters are stated.", "supporting")
case('c1962', "AUTH-M022-023", 'data/processed/docs/case-law/commonlii/LKCA/1962/72.md', "Diyes Singho v. Herath", "(1962) 64 NLR 492",
     "Supreme Court of Ceylon (reported in NLR; CommonLII database LKCA)", "1962-06-21",
     r"Section 31 enacts that \" it is and shall be the duty of every notary strictly to observe and act in conformity with \"certain specified rules, one of which is \(see section 31 \(2\) \(e\)\) that he shall in the attestation of every deed or instrument state whether any money was paid or not in his presence as the consideration of the deed or instrument\.", [Q2],
     "Judicial paraphrase of the attestation rule on consideration (rule 20(e)); the court also holds that the notary's statement is not itself proof that consideration passed (dicta relevant to a lease where rent may be acknowledged).", "supporting")
case('c1924', "AUTH-M022-024", 'data/processed/docs/case-law/commonlii/LKCA/1924/1.md', "Rex v. Seenytamby", "(1924) 26 NLR 367",
     "Supreme Court of Ceylon (reported in NLR; CommonLII database LKCA)", "1924-12-17",
     r"Where a notary, who attested a deed stated in the attestation clause, as required by law, that stamps of the value of Rs\. 42 were affixed to the duplicate deed, and where on receipt of the duplicate by the Registrar of Lands it was ascertained that only one stamp of the value of Rs\. 2 was affixed to it\. Held, that the notary was guilty of having knowingly and wilfully made a false statement in the attestation to the deed within the meaning of section 33 \(d\) of the Notaries Ordinance\.", [Q2],
     "Illustrates the stamp statement required in the attestation (rule 20(f)) and the criminal consequence of a false statement in it.", "supporting")

neg = [
    {"query": "deed executed or acknowledged before more than one notary first attests", "method": "uv run python -m draftly.retrieval search --limit 10 (BM25+dense+graph RRF)", "corpus": "statutes",
     "result": "Top 10 = SRC014:s30, SRC001:s15, SRC014:s41, SRC001:s16, SRC014:s26, SRC014:s35, SRC050:s163, SRC002:s16, SRC014:s40, SRC015:s26. The section-31 node containing rule (25) was NOT surfaced; located instead by browsing the tree.", "benchmark_question_ids": [Q1, Q2]},
    {"query": "notary attestation shall state signed by the party and witnesses in his presence known to him", "method": "draftly.retrieval search --limit 10", "corpus": "statutes",
     "result": "Top hits SRC014:s35, SRC015:s31, SRC003:s4, SRC014:s30 ...; SRC014 section 31 rule (20) not surfaced (index appears to chunk s.31 under other section ids).", "benchmark_question_ids": [Q2]},
    {"query": "Notaries Ordinance section 31 rule 25", "method": "draftly.retrieval search --limit 10", "corpus": "statutes",
     "result": "SRC015:s28, SRC016:s28, SRC014:s26 top; SRC014:s32 rank 8. Rule 25 node not returned.", "benchmark_question_ids": [Q1, Q2]},
    {"query": "duplicate transmitted by the notary who first attests Registrar of Lands", "method": "draftly.retrieval search --limit 10", "corpus": "statutes",
     "result": "SRC016:s31, SRC014:s11, SRC014:s26 ...; rule (28) not surfaced by the engine.", "benchmark_question_ids": [Q1]},
    {"query": "power of attorney execute deed on behalf of principal notary attest", "method": "draftly.retrieval search --limit 10", "corpus": "statutes",
     "result": "SRC019:s3A, SRC020:s2, SRC015:s28, SRC017:s2 (Interpretation) ...; no operative Powers of Attorney Ordinance execution provision surfaced; SRC017 not opened further for this matter.", "benchmark_question_ids": [Q1]},
    {"query": "more than one notary|two notaries|second notary|first notary|other notary", "method": "grep -rlE over data/processed/docs/case-law/ (all judgment markdown)", "corpus": "cases",
     "result": "8 files hit (LKCA 1910/76 King v. Fernando; 1919/26 Alim Will Case; 1949/4 Public Trustee v. Uduruwana; 1963/58 Ponnupillai v. Kumaravetpillai; 2007/3 Ranjith Wanigaratne v. Kaggoda Arachchi; LKSC 1898/2; LKSC 1927/3 Dinohamy v. Balahamy; courts/sc/sc-chc-appeal-62-2012). Each opened: all use the phrase in a different sense (a different notary drew/attested another deed, or a notary refused to act). None concerns a single deed attested by two notaries under rule (25). Not cited.", "benchmark_question_ids": [Q1, Q2]},
    {"query": "two notaries|more than one notary|first notary|second notary|attestation clause|attesting notary|before more than one|first attests", "method": "grep -iE scripts/case-law-information-extraction/output/rules.csv", "corpus": "cases",
     "result": "No extracted rule on multi-notary execution. Only tangential rules (LKCA-1969-46 signatures on blank forms; LKCA-1985-34 protocol as secondary evidence; LKCA-2000-48 read over and explained to donee) - not opened, not cited.", "benchmark_question_ids": [Q1, Q2]},
    {"query": "SRC014 sections 30-32 in scripts/case-law-statute-linking/output/resolved_links.csv", "method": "grep", "corpus": "cases",
     "result": "No rows for SRC014 sections 30-32 in resolved_links.csv.", "benchmark_question_ids": [Q1, Q2]},
    {"query": "case_statute_section_links.csv filtered SRC014 (185 rows)", "method": "awk filter + manual review", "corpus": "cases",
     "result": "Rows for 30(20)/30(21)/31/31(2)/30(25) led to LKCA-1954-80, 1962-72, 1957-40, 1960-2, 1956-37, 1963-28, 1924-1. Opened 1954-80, 1962-72, 1924-1 (cited); 1963-28 (Dingiri Appu v. Mohottihamy, 68 NLR 40) and 1956-37 (Sabaratnam v. Kandavanam, 60 NLR 35) opened but concern proof of due execution by duplicate/certified copy, not the attestation contents or multi-notary execution - not cited. No linked case addresses rule (25) or rule (28).", "benchmark_question_ids": [Q1, Q2]},
    {"query": "Form E (Second Schedule) text as in force October 2020", "method": "tree schedules[] + RGD PDF page grep 'Form E'", "corpus": "statutes",
     "result": "Tree has schedules [] (schedules_referenced only). RGD PDF page grep found 'form E' only inside rule (21) text; the schedule form itself was not located in the repo for the pre-2022 period. Only the 2022 replacement Form E (post-dates matter) is available in the SRC015 OCR text.", "benchmark_question_ids": [Q2]},
    {"query": "Notaries Ordinance amendments between the 1980 revised edition and 2020 (e.g. Act 12 of 2005 or any other)", "method": "grep actions.csv, amendment-chains.csv, lankalaw-catalogue.csv, library/amendments/", "corpus": "statutes",
     "result": "actions.csv: 0 SRC014 rows. amendment-chains.csv lists 15 amending instruments ending Law 20 of 1976 (tree header adds Act 12 of 2005); lankalaw-catalogue.csv identifies 12 of 2005 as the Increase of Fines Act. No text of any 1976-2020 Notaries amendment is in the library (only 6-1951, 31-2022, 6-2024). The 2022 Act quotes pre-2022 wording of rules 16(a) and 30 that differs from the tree, so an unlisted pre-2022 amendment exists; October 2020 wording cannot be established from repo files.", "benchmark_question_ids": [Q1, Q2]},
    {"query": "pdftotext of 31-2022-notaries-amendment-act.pdf", "method": "pdftotext -layout (PowerShell, poppler)", "corpus": "statutes",
     "result": "Empty output: PDF is image-only (pdffonts lists no fonts). Used the repo's docling+rapidocr OCR markdown data/processed/docs/amendments/src015-notaries-amendment-act.md instead; OCR errors present.", "benchmark_question_ids": [Q1, Q2]},
]

cand = {
    "benchmark_matter_id": M, "run_id": RUN, "stage": "authorities_candidate", "produced_by_agent": AG,
    "matter_reference_date": "2020-10",
    "matter_reference_date_basis": "Sri Lanka Law College Conveyancing LW 307 examination, October 2020 session (paper 11, question 4); the scenario itself states no dates.",
    "authorities": auths, "negative_retrieval": neg,
    "source_conflicts": [
        {"authority_id": "AUTH-M022-017",
         "description": "Prevention of Frauds Ordinance s.2: the canonical tree (1980 revision, last event 60 of 1947) and the registry PDF (LankaLaw consolidated 2024, incorporating Acts 30 of 2022 and 4 of 2024) carry different texts. The tree text is the candidate October 2020 wording; the PDF is post-matter.",
         "versions": [{"source_path": POF, "source_hash": H[POF], "excerpt": EX['pof2']},
                      {"source_path": POFPDF, "source_hash": H[POFPDF], "excerpt": "2. (1) No sale, purchase, transfer, assignment, or mortgage of land or other immovable property, ... shall be in force or avail in law unless - (a) the relevant deed or instrument shall be in writing, signed by every executant or by any person duly authorised by such executant and the witnesses in the presence of a licenced notary public present at the same time and in the presence of one another, and the same shall be attested by such notary; and (b) the left or right thumb impression of every such executant ... [pdftotext -layout pages 1-2; marginal notes [2, 4 of 2024] [2, 30 of 2022] [2, 60 of 1947]; ellipses mark omitted text]"}],
         "resolution": "unresolved_requires_legal_review"},
        {"authority_id": "AUTH-M022-018",
         "description": "Prevention of Frauds Ordinance s.16: tree says 'in duplicate'; registry PDF page 6 (as amended by Act 30 of 2022, marginal [5, 30 of 2022]) says 'in triplicate'. Tree = candidate pre-2022 wording.",
         "versions": [{"source_path": POF, "source_hash": H[POF], "excerpt": EX['pof16']},
                      {"source_path": POFPDF, "source_hash": H[POFPDF], "excerpt": "16. Every deed or other instrument, except any will, testament, or codicil ... to be attested by a notary, shall be executed, acknowledged, or attested in triplicate. [pdftotext -layout page 6, two-column layout re-joined; marginal 'Deeds to be ... Triplicate. [5, 30 of 2022]']"}],
         "resolution": "unresolved_requires_legal_review"},
        {"authority_id": "AUTH-M022-014",
         "description": "Notaries Ordinance s.31 rule (30): tree reads 'he shall preserve a true copy of the power of attorney with his protocol'; the 2022 amending Act (s.16(13)) describes the words it replaces as 'he shall preserve a true copy of the registered power of attorney with his protocol'. The tree therefore does not reflect the immediately pre-2022 text; which text applied in October 2020 is unknown.",
         "versions": [{"source_path": NOT, "source_hash": H[NOT], "excerpt": EX['r30']},
                      {"source_path": A22, "source_hash": H[A22], "excerpt": "(13) by the substitution in rule (30) thereof, from the words\n\"he shall preserve a true copy of the registered power\nof attorney with his protocol\" to the end of that rule,"}],
         "resolution": "unresolved_requires_legal_review"}]}
assert cand["source_conflicts"][2]["versions"][1]["excerpt"] in a22
json.dump(cand, open(R + 'candidate-authorities.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
json.dump(EX, open(R + '_excerpts.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print("written; authorities:", len(auths))
