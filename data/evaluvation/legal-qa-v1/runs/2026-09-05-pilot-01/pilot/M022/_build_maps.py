"""Generator for M022 issue-map.json and legal-map.draft.json.
Rule-claim excerpts are read from _excerpts.json (written by _build_candidates.py,
each asserted verbatim against the source file). Run from the repo root."""
import json

R = 'data/evaluvation/legal-qa-v1/runs/2026-09-05-pilot-01/pilot/M022/'
EX = json.load(open(R + '_excerpts.json', encoding='utf-8'))
RUN = '2026-09-05-pilot-01'; AG = 'research-agent-B'; M = 'M022'; Q1 = 'M022-Q01'; Q2 = 'M022-Q02'
NOT = 'data/processed/canonical-statutes/SRC014-1-1907.json'


def sub(text, start, end=None):
    """Return the verbatim substring of `text` from `start` up to and including `end`."""
    i = text.index(start)
    if end is None:
        return text[i:]
    j = text.index(end, i) + len(end)
    return text[i:j]


BG = ("Anil Fernando is a Notary practising in Colombo. A company named Cyril & Cyril (Private) Limited wishes to lease out a warehouse situated in Galle. "
      "The company wants Anil Fernando to attest its Lease Agreement. Anil Fernando knows the directors of the said company but he does not know the owner of the warehouse, namely Mr. Russel Perera. "
      "Mr.Russel Perera wants his Notary Ruwan Perera who is practising in Galle to draft and attest the Lease Agreement. Russel Perera does not want to come to Colombo.")

AMBIG = ("Scenario ambiguity: the company 'wishes to lease out' the warehouse, yet the owner is stated to be Russel Perera. Either (i) the company is the lessee taking the warehouse from Russel Perera (the natural reading of 'the company wants Anil Fernando to attest its Lease Agreement' together with Russel Perera wanting his own notary), or (ii) the company already holds the warehouse from Russel Perera and is sub-letting, with Russel Perera joining to consent. The source does not say. The execution mechanics answered below do not depend on which party is lessor, but the description of the parties in the instrument does.")

issue_map = {
    "benchmark_matter_id": M, "run_id": RUN, "produced_by_agent": AG,
    "matter_summary": ("Two notaries practise in different towns: Anil Fernando in Colombo and Ruwan Perera in Galle. A private company, Cyril & Cyril (Private) Limited, wants a Lease Agreement over a warehouse in Galle attested by Anil Fernando, who knows the company's directors but not the warehouse owner, Russel Perera. "
                       "Russel Perera wants his own notary, Ruwan Perera of Galle, to draft and attest the Lease Agreement and will not travel to Colombo. The questions ask how the Lease Agreement can be executed in these circumstances, and, if Ruwan Perera is the first notary, what his attestation must state. " + AMBIG),
    "parties": [
        {"party_ref": "PTY01", "name_as_in_source": "Anil Fernando", "role": "Notary practising in Colombo; asked by the company to attest its Lease Agreement", "legal_capacity": "notary public (natural person)",
         "capacity_uncertainties": ["Area/judicial zone in which he is authorised to practise is stated only as 'Colombo'.", "He knows the company's directors but not Russel Perera."]},
        {"party_ref": "PTY02", "name_as_in_source": "Ruwan Perera", "role": "Notary practising in Galle; Russel Perera's notary, to draft and attest the Lease Agreement", "legal_capacity": "notary public (natural person)",
         "capacity_uncertainties": ["Area/judicial zone stated only as 'Galle'.", "Whether he knows the company's directors is not stated."]},
        {"party_ref": "PTY03", "name_as_in_source": "Cyril & Cyril (Private) Limited", "role": "Company that 'wishes to lease out' the warehouse and wants Anil Fernando to attest its Lease Agreement", "legal_capacity": "private limited company (body corporate); contracts through its directors or authorised persons",
         "capacity_uncertainties": ["Whether the company is lessee or (sub-)lessor is unresolved (see matter_summary).", "Number of directors and any article-based signing authority not stated.", "The directors are unnamed; they are the natural persons who would sign for the company."]},
        {"party_ref": "PTY04", "name_as_in_source": "the directors of the said company", "role": "Persons who would sign the Lease Agreement on the company's behalf; known to Anil Fernando", "legal_capacity": "directors of PTY03 (natural persons, unnamed, number unknown)",
         "capacity_uncertainties": ["Number of directors not stated."]},
        {"party_ref": "PTY05", "name_as_in_source": "Mr. Russel Perera", "role": "Owner of the warehouse in Galle; wants his own notary Ruwan Perera; will not come to Colombo", "legal_capacity": "natural person, owner of immovable property; presumptively lessor",
         "capacity_uncertainties": ["Whether he is lessor to the company or a head-lessor consenting to a sub-lease is unresolved.", "Whether he is literate / able to read the deed is not stated (relevant to what the attestation must say about reading over)."]}
    ],
    "relevant_dates": [
        {"date_as_in_source": "(none stated)", "iso_date": None, "event": "The scenario gives no dates. Matter reference date taken from the exam session: Sri Lanka Law College Conveyancing LW 307, October 2020.",
         "legal_significance": "Law must be assessed as at October 2020. The Notaries (Amendment) Acts No. 31 of 2022 and No. 6 of 2024 and the Prevention of Frauds (Amendment) Acts of 2022 and 2024 post-date the matter and must be excluded."}
    ],
    "questions": [
        {"benchmark_question_id": Q1,
         "primary_issue": "How a notarially executed Lease Agreement over immovable property in Galle can be validly executed when one party (the company, acting through directors in Colombo) wants a Colombo notary and the other party (the owner in Galle) wants his own Galle notary and will not travel: whether the deed may be executed before two notaries at different times and places, and how the company itself executes.",
         "secondary_issues": [
             "Whether a lease of a warehouse must be notarially executed at all (formal requirements for leases of immovable property).",
             "How a private limited company signs a notarially executed instrument (who signs under the company's name).",
             "Whether a notary may attest outside the area in which he is authorised to practise (why Anil Fernando cannot simply attest in Galle).",
             "The 'known to the notary' requirement given that Anil Fernando does not know Russel Perera.",
             "Whether a notary may attest a deed drawn by another notary (Ruwan Perera drafts, Anil Fernando also attests).",
             "Consequential duties when two notaries attest: numbering, protocol, which notary transmits the duplicate, and the land being in a different district from the Colombo notary.",
             "Alternative: execution by the owner through an attorney under a power of attorney."],
         "legal_domain": "notarial_execution_and_attestation",
         "required_legal_conclusion": "A procedure: the sequence by which the lessor's signature is taken and attested in Galle and the company's signatures are taken and attested in Colombo, identifying the statutory basis for executing one deed before two notaries and the company's mode of execution.",
         "answer_format": "procedure",
         "relevant_transaction_or_event": "Execution and notarial attestation of a Lease Agreement (immovable property: warehouse in Galle) between a company and an individual owner, with the parties in different towns.",
         "relevant_dates": ["October 2020 (exam session; scenario undated)"],
         "authority_type_expected": "statute",
         "answer_depends_on_unresolved_facts": True,
         "unresolved_fact_dependencies": [
             "Term of the lease: if it is a lease at will or for a period not exceeding one month, notarial execution is not required at all; the question presupposes a notarially attested lease.",
             "Whether the company is lessee or sub-lessor (affects the parties' descriptions, not the mechanics).",
             "Number of directors / any article-based signing authority (affects who signs for the company).",
             "Whether Russel Perera would be willing to execute through an attorney instead of before Ruwan Perera."],
         "research_queries": [
             {"query": "Notaries Ordinance rules where a deed is executed or acknowledged before more than one notary", "corpus": "statutes", "named_in_question": False},
             {"query": "Notaries Ordinance deed executed by two or more parties who do not sign at the same time and place", "corpus": "statutes", "named_in_question": False},
             {"query": "Notaries Ordinance notary not to attest outside the area in which he is authorised to practise", "corpus": "statutes", "named_in_question": False},
             {"query": "Notaries Ordinance executant must be known to the notary or to two witnesses", "corpus": "statutes", "named_in_question": False},
             {"query": "Prevention of Frauds Ordinance lease of immovable property executed before notary and two witnesses; lease not exceeding one month exception", "corpus": "statutes", "named_in_question": False},
             {"query": "Companies Act method of contracting: obligations requiring notarial attestation signed by two directors", "corpus": "statutes", "named_in_question": False},
             {"query": "Notaries Ordinance duplicate transmitted by the notary who first attests; land situated in another district", "corpus": "statutes", "named_in_question": False},
             {"query": "case law on a deed attested by two notaries / execution before more than one notary", "corpus": "cases", "named_in_question": False},
             {"query": "case law on execution of a lease by a company before a notary", "corpus": "cases", "named_in_question": False}],
         "status": "issue_mapped"},
        {"benchmark_question_id": Q2,
         "primary_issue": "The statutory contents of the attestation of the notary who first attests a deed executed before more than one notary: what Ruwan Perera, as first notary, must state in his attestation of the Lease Agreement.",
         "secondary_issues": [
             "Whether the first notary's attestation must satisfy the full list of attestation particulars or only the reduced list that applies to the other notary.",
             "The prescribed form of attestation and the language/signature requirements.",
             "How the attestation particulars (date, place, presence, witnesses, reading over, consideration, stamps, alterations) apply when only one party signs before that notary.",
             "First-notary duties adjacent to the attestation (numbering, protocol, transmitting the duplicate) that the examiner may expect to be mentioned."],
         "legal_domain": "notarial_execution_and_attestation",
         "required_legal_conclusion": "A list: the items the first notary must state in his attestation, drawn from the statutory attestation rule and the multi-notary rule, applied to a lessor signing alone in Galle.",
         "answer_format": "list",
         "relevant_transaction_or_event": "Attestation by the first of two notaries of a Lease Agreement executed by the lessor in Galle.",
         "relevant_dates": ["October 2020 (exam session; scenario undated)"],
         "authority_type_expected": "statute",
         "answer_depends_on_unresolved_facts": True,
         "unresolved_fact_dependencies": [
             "Whether Russel Perera is literate / requires the deed to be read over (affects the 'read over or read and explained' statement).",
             "Whether any rent or premium is paid in the notary's presence (affects the consideration statement).",
             "Whether the deed bears adhesive or impressed stamps and their value (affects the stamp statement).",
             "Whether Russel Perera signs with a mark or in a language other than the notary's (affects additional statements)."],
         "research_queries": [
             {"query": "Notaries Ordinance what the notary shall state in his attestation", "corpus": "statutes", "named_in_question": False},
             {"query": "Notaries Ordinance first notary to comply with all requirements of the attestation rule where deed executed before more than one notary", "corpus": "statutes", "named_in_question": False},
             {"query": "Notaries Ordinance form of attestation Second Schedule Form E", "corpus": "statutes", "named_in_question": False},
             {"query": "case law on contents of a notary's attestation clause (known to notary, consideration paid in presence, stamps, alterations)", "corpus": "cases", "named_in_question": False}],
         "status": "issue_mapped"}
    ]
}
json.dump(issue_map, open(R + 'issue-map.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)

# ---------------- legal map -----------------
r25 = EX['r25']; r20 = EX['r20']; s32 = EX['s32']; r22 = EX['r22']; r9 = EX['r9']; pof2 = EX['pof2']; ca19 = EX['ca19']
LOC = lambda ptr: {"source_path": NOT, "json_pointer": ptr}


def claim(cid, text, ctype, aids, excerpts, strength, basis=None):
    c = {"claim_id": cid, "claim_text": text, "claim_type": ctype, "supporting_authority_ids": aids,
         "supporting_excerpts": excerpts, "support_strength": strength, "verification_status": "unverified"}
    if strength == "scenario_fact":
        c["scenario_fact_basis"] = basis
    else:
        c["scenario_fact_basis"] = basis
    return c


TEMPORAL_CAVEAT = ("All Notaries Ordinance excerpts are from the 1980-revision consolidation held in the repo; the October 2020 wording could not be confirmed (an unlisted pre-2022 amendment is evidenced by the 2022 Act's own quotations), and the 2022/2024 amendments are excluded as post-dating the matter. Prevention of Frauds Ordinance excerpts are the pre-2022 tree text, which differs from the 2024 consolidated PDF in the library.")

q1_claims = [
    claim("CL-M022-Q01-001", "The Lease Agreement concerns a warehouse, i.e. immovable property, and (unless it is a lease at will or for a period not exceeding one month) it is an agreement establishing an interest affecting immovable property that must be in writing signed by the party before a licensed notary public and two or more witnesses present at the same time, and attested by them.",
          "rule", ["AUTH-M022-017"], [{"authority_id": "AUTH-M022-017", "excerpt": sub(pof2, "No sale, purchase", "attested by such notary and witnesses."), "locator": {"source_path": "data/processed/canonical-statutes/SRC001-7-1840.json", "json_pointer": "/body/1"}}], "direct"),
    claim("CL-M022-Q01-002", "Because the parties are in different towns and Russel Perera will not travel, the deed cannot be signed by all parties at one time and place; the Ordinance expressly provides for a deed 'to be executed by two or more parties, both or all of whom ... do not sign the deed or instrument at the same time and place'.",
          "rule", ["AUTH-M022-004"], [{"authority_id": "AUTH-M022-004", "excerpt": sub(s32, "(2) In the case of any deed", "at the same time and place-"), "locator": LOC("/body/31/children/1")}], "direct"),
    claim("CL-M022-Q01-003", "A deed may be executed or acknowledged before more than one notary; where it is, the notary who first attests complies with all of rule (20), every other attesting notary complies with paragraphs (a) to (e) and (g) of that rule, each notary numbers the deed, the first notary keeps the protocol and the other supplies himself with a certified copy as his protocol, and each complies as far as possible with the rest of section 31.",
          "rule", ["AUTH-M022-001"], [{"authority_id": "AUTH-M022-001", "excerpt": r25, "locator": LOC("/body/30/children/24")}], "direct"),
    claim("CL-M022-Q01-004", "A notary may not attest a deed in any area other than that in which he is authorised to practise, so Anil Fernando (Colombo) cannot attest Russel Perera's signature in Galle and Ruwan Perera (Galle) cannot attest the directors' signatures in Colombo.",
          "rule", ["AUTH-M022-008"], [{"authority_id": "AUTH-M022-008", "excerpt": r22, "locator": LOC("/body/30/children/21")}], "direct"),
    claim("CL-M022-Q01-005", "A notary may not attest a deed unless the executant is known to him or to at least two of the attesting witnesses; Anil Fernando does not know Russel Perera, whereas Ruwan Perera is Russel Perera's own notary, so the lessor's signature is appropriately attested by Ruwan Perera.",
          "application", ["AUTH-M022-006", "AUTH-M022-007"], [{"authority_id": "AUTH-M022-006", "excerpt": sub(r9, "(9) He shall not", "attesting witnesses thereto;"), "locator": LOC("/body/30/children/8")}, {"authority_id": "AUTH-M022-007", "excerpt": EX['r10'], "locator": LOC("/body/30/children/9")}], "combined"),
    claim("CL-M022-Q01-006", "The company executes through natural persons: an obligation which a natural person must sign and have notarially attested may be entered into on behalf of the company in writing signed under the company's name by two directors (or the sole director, or persons authorised by the articles, or attorneys appointed by the company) and be notarially executed.",
          "rule", ["AUTH-M022-019"], [{"authority_id": "AUTH-M022-019", "excerpt": sub(ca19, "(a) an obligation which", "and be notarially executed;"), "locator": {"source_path": "data/processed/canonical-statutes/SRC031-7-2007.json", "json_pointer": "/body/1/children/4/children/0/children/0/children/0"}}], "direct"),
    claim("CL-M022-Q01-007", "Procedure: Ruwan Perera drafts the Lease Agreement (in duplicate); Russel Perera signs it in Galle before Ruwan Perera and two witnesses, all signing in one another's presence, and Ruwan Perera attests as the first notary; the deed then goes to Colombo where two directors sign under the company's name before Anil Fernando and two witnesses, and Anil Fernando attests as the second notary (complying with paragraphs (a)-(e) and (g) of rule (20)). Each notary numbers the deed in his own series; Ruwan Perera keeps the protocol and Anil Fernando a certified copy.",
          "application", ["AUTH-M022-001", "AUTH-M022-004", "AUTH-M022-009", "AUTH-M022-018", "AUTH-M022-019"],
          [{"authority_id": "AUTH-M022-001", "excerpt": sub(r25, "(a) the notary who first attests", "in his serial number;"), "locator": LOC("/body/30/children/24/children/0")},
           {"authority_id": "AUTH-M022-009", "excerpt": EX['r12'], "locator": LOC("/body/30/children/11")},
           {"authority_id": "AUTH-M022-018", "excerpt": EX['pof16'], "locator": {"source_path": "data/processed/canonical-statutes/SRC001-7-1840.json", "json_pointer": "/body/15"}}], "combined"),
    claim("CL-M022-Q01-008", "Because Ruwan Perera draws the deed and Anil Fernando also attests it, the deed should carry a certificate signed by Ruwan Perera that he drew it, since a notary may not attest a deed drawn in Sri Lanka by another person without such an endorsed certificate.",
          "application", ["AUTH-M022-016"], [{"authority_id": "AUTH-M022-016", "excerpt": EX['r2'], "locator": LOC("/body/30/children/1")}], "direct"),
    claim("CL-M022-Q01-009", "Consequential duties: the duplicate is transmitted to the Registrar of Lands by the notary who first attests (Ruwan Perera), and the other notary need not transmit one; the first signing fixes the execution date for the stamping and numbering rules while each signing is a separate execution for the date/place and attestation rules.",
          "application", ["AUTH-M022-005", "AUTH-M022-004"], [{"authority_id": "AUTH-M022-005", "excerpt": EX['r28'], "locator": LOC("/body/30/children/27")}, {"authority_id": "AUTH-M022-004", "excerpt": sub(s32, "(i) the deed or instrument shall", "at the same time and place; and"), "locator": LOC("/body/31/children/1/children/0")}], "combined"),
    claim("CL-M022-Q01-010", "An alternative route exists: Russel Perera could appoint an attorney to sign in Colombo before Anil Fernando, in which case the attesting notary must preserve a copy of the power of attorney with his protocol and forward a like copy with the duplicate; but the scenario indicates he wants his own notary, so the two-notary route is the answer the question invites.",
          "application", ["AUTH-M022-014"], [{"authority_id": "AUTH-M022-014", "excerpt": EX['r30'], "locator": LOC("/body/30/children/29")}], "inferential"),
    claim("CL-M022-Q01-011", "The question presupposes a lease requiring notarial execution (i.e. not a lease at will or for one month or less) and that Russel Perera is the party executing in Galle while the company's directors execute in Colombo.",
          "scenario_inference", [], [], "scenario_fact", "Background: 'Lease Agreement' over a warehouse; 'The company wants Anil Fernando to attest its Lease Agreement'; 'Anil Fernando knows the directors'; 'Russel Perera wants his Notary Ruwan Perera who is practising in Galle to draft and attest'; 'Russel Perera does not want to come to Colombo'. Term of lease not stated."),
]

q2_claims = [
    claim("CL-M022-Q02-001", "Where a deed is executed before more than one notary, the notary who first attests must comply with ALL the requirements of rule (20) (the other notary only with paragraphs (a) to (e) and (g)).",
          "rule", ["AUTH-M022-001"], [{"authority_id": "AUTH-M022-001", "excerpt": sub(r25, "(25) Where any deed", "in his serial number;"), "locator": LOC("/body/30/children/24")}], "direct"),
    claim("CL-M022-Q02-002", "Rule (20) requires the notary without delay to attest every deed executed before him, to sign and seal the attestation, and to state in it: (a) that the deed was signed by the party and the witnesses in his presence and in the presence of one another; (b) whether the executant or the attesting witnesses (specifying which) were known to him; (c) the day, month and year on which and the place where it was executed, and the full names and residences of the attesting witnesses; (d) whether it was read over by the executant, or read and explained by the notary to him in the presence of the witnesses; (e) whether any money was paid in his presence as the consideration or part of it and, if so, the actual amount in local currency; (f) the number and value of the adhesive stamps affixed to, or the value of the impressed stamps on, the deed and its duplicate; (g) specifically the erasures, alterations and interpolations in the deed, whether made before it was read over, and any made in the signatures, the serial number or the writing on the stamps.",
          "rule", ["AUTH-M022-002"], [{"authority_id": "AUTH-M022-002", "excerpt": r20, "locator": LOC("/body/30/children/19")}], "direct"),
    claim("CL-M022-Q02-003", "The attestation must be substantially in Form E of the Second Schedule and legibly signed in the language of the deed (and with the notary's usual signature if different); every erasure, alteration or interpolation in the attestation itself must be authenticated with the notary's initials. (Form E as in force in October 2020 was not located in the repository.)",
          "rule", ["AUTH-M022-003"], [{"authority_id": "AUTH-M022-003", "excerpt": EX['r21'], "locator": LOC("/body/30/children/20")}], "direct"),
    claim("CL-M022-Q02-004", "Because only Russel Perera signs before Ruwan Perera, the deed is deemed executed before Ruwan Perera when Russel Perera signs, and Ruwan Perera's attestation therefore records that signing: Russel Perera and the two witnesses signed in his presence and in one another's presence; whether Russel Perera and/or the witnesses (naming which) were known to him; the date and place (Galle) of that signing and the witnesses' full names and residences; whether Russel Perera read the deed himself or Ruwan Perera read and explained it to him in the witnesses' presence; whether any rent, premium or other consideration was paid in his presence and its amount in rupees; the stamps on the original and duplicate; and any erasures, alterations or interpolations and whether they were made before reading over.",
          "application", ["AUTH-M022-002", "AUTH-M022-004", "AUTH-M022-012"],
          [{"authority_id": "AUTH-M022-004", "excerpt": sub(s32, "(ii) the deed or instrument shall", "at the same time and place; and"), "locator": LOC("/body/31/children/1/children/1")},
           {"authority_id": "AUTH-M022-012", "excerpt": EX['r18'], "locator": LOC("/body/30/children/17")},
           {"authority_id": "AUTH-M022-002", "excerpt": sub(r20, "(a) that the said deed", "were known to him;"), "locator": LOC("/body/30/children/19/children/0")}], "combined"),
    claim("CL-M022-Q02-005", "If Russel Perera's signature differs from the name he gives, the attestation must describe him by both names; and (as first notary) Ruwan Perera also numbers the deed in his own series, preserves the protocol, and transmits the duplicate to the Registrar of Lands - duties adjacent to, though not statements within, the attestation.",
          "application", ["AUTH-M022-015", "AUTH-M022-010", "AUTH-M022-011", "AUTH-M022-005", "AUTH-M022-001"],
          [{"authority_id": "AUTH-M022-015", "excerpt": EX['r14'], "locator": LOC("/body/30/children/13")},
           {"authority_id": "AUTH-M022-001", "excerpt": sub(r25, "(b) every notary attesting", "for the purposes of that rule; and"), "locator": LOC("/body/30/children/24/children/1")},
           {"authority_id": "AUTH-M022-005", "excerpt": sub(EX['r28'], "the duplicate of such deed", "the district in which he resides;"), "locator": LOC("/body/30/children/27")}], "combined"),
    claim("CL-M022-Q02-006", "Case law treats the 'attestation' as including both the notary's signature and the attestation clause, and has applied the attestation rules on consideration and stamps strictly (a false stamp statement in the attestation was held an offence).",
          "rule", ["AUTH-M022-022", "AUTH-M022-023", "AUTH-M022-024"],
          [{"authority_id": "AUTH-M022-022", "excerpt": EX['c1954'], "locator": "data/processed/docs/case-law/commonlii/LKCA/1954/80.md (headnote)"},
           {"authority_id": "AUTH-M022-023", "excerpt": EX['c1962'], "locator": "data/processed/docs/case-law/commonlii/LKCA/1962/72.md (judgment, p. 494-495 of 64 NLR)"},
           {"authority_id": "AUTH-M022-024", "excerpt": EX['c1924'], "locator": "data/processed/docs/case-law/commonlii/LKCA/1924/1.md (headnote)"}], "combined"),
    claim("CL-M022-Q02-007", "The question stipulates that Ruwan Perera is the first notary, i.e. Russel Perera signs before him in Galle before the directors sign before Anil Fernando in Colombo.",
          "scenario_inference", [], [], "scenario_fact", "Question text: 'If Ruwan Perera is the first Notary'; background: Ruwan Perera practises in Galle and is to draft and attest; Russel Perera will not come to Colombo."),
]

legal_map = {
    "benchmark_matter_id": M, "run_id": RUN, "produced_by_agent": AG, "status": "needs_legal_review",
    "questions": [
        {"benchmark_question_id": Q1,
         "issues": ["Formal requirement of notarial execution for a lease of immovable property",
                    "Execution of one deed before two notaries at different times and places",
                    "Territorial limit on each notary's power to attest",
                    "Identification of the executant unknown to the Colombo notary",
                    "Mode of execution by a private limited company",
                    "Certificate where the deed is drawn by another notary; numbering, protocol and duplicate duties; attorney alternative",
                    AMBIG],
         "indispensable_authority_ids": ["AUTH-M022-017", "AUTH-M022-004", "AUTH-M022-001", "AUTH-M022-008", "AUTH-M022-019", "AUTH-M022-006"],
         "supporting_authority_ids": ["AUTH-M022-007", "AUTH-M022-009", "AUTH-M022-018", "AUTH-M022-016", "AUTH-M022-005", "AUTH-M022-011", "AUTH-M022-013", "AUTH-M022-014", "AUTH-M022-020", "AUTH-M022-021"],
         "legal_hop_count": 5,
         "hop_count_basis": "Counted: (1) lease of immovable property must be notarially executed (PoF s.2); (2) the Ordinance permits parties to sign at different times and places (s.32(2)); (3) and before more than one notary, allocating duties between first and other notary (s.31 r.25); (4) each notary is confined to his own area, which is why two notaries are needed (s.31 r.22); (5) the company signs through two directors and the deed is notarially executed (Companies Act s.19(1)(a)). The 'known to notary' rule (r.9/10) explains the choice of notary for Russel Perera but is not a separate hop; r.2, r.12, r.28, r.29, r.30 and PoF s.16 are consequential/supporting.",
         "reasoning_chain": [
             {"step": 1, "text": "The Lease Agreement over the Galle warehouse (assumed to exceed one month) must be in writing, signed before a licensed notary and two witnesses present at the same time, and attested.", "authority_ids": ["AUTH-M022-017"], "relies_on_scenario_fact_ids": ["CL-M022-Q01-011"]},
             {"step": 2, "text": "The company can only sign through natural persons: two directors (or sole director / persons under the articles / attorneys) sign under the company's name and the deed is notarially executed.", "authority_ids": ["AUTH-M022-019"]},
             {"step": 3, "text": "Each notary may attest only within the area in which he is authorised to practise, so the Colombo notary attests the directors' signatures in Colombo and the Galle notary attests Russel Perera's signature in Galle.", "authority_ids": ["AUTH-M022-008"]},
             {"step": 4, "text": "Anil Fernando does not know Russel Perera; the 'known to the notary or to two witnesses' rule is met by Russel Perera signing before his own notary Ruwan Perera.", "authority_ids": ["AUTH-M022-006", "AUTH-M022-007"]},
             {"step": 5, "text": "The Ordinance permits parties to sign at different times and places and the deed to be executed before more than one notary; rule (25) allocates the duties: first notary full attestation and protocol, second notary reduced attestation and certified copy, both number the deed.", "authority_ids": ["AUTH-M022-004", "AUTH-M022-001", "AUTH-M022-010", "AUTH-M022-011"]},
             {"step": 6, "text": "Sequence: Ruwan Perera drafts (in duplicate) and endorses a certificate that he drew the deed; Russel Perera signs in Galle before Ruwan Perera and two witnesses, all in one another's presence, and Ruwan Perera attests first; the deed and duplicate are sent to Colombo; two directors sign before Anil Fernando and two witnesses; Anil Fernando attests second.", "authority_ids": ["AUTH-M022-016", "AUTH-M022-009", "AUTH-M022-018", "AUTH-M022-001"]},
             {"step": 7, "text": "Ruwan Perera, as first notary, transmits the duplicate to the Registrar of Lands; since the land is in Galle no cross-district copy is needed from him, but rule (29) would apply if the Colombo notary were the transmitting notary.", "authority_ids": ["AUTH-M022-005", "AUTH-M022-013"]},
             {"step": 8, "text": "Alternative (not preferred on the facts): Russel Perera appoints an attorney to sign before Anil Fernando in Colombo; the attesting notary keeps and forwards a copy of the power of attorney.", "authority_ids": ["AUTH-M022-014"]},
         ],
         "gold_answer_draft": {
             "issue": "How can a Lease Agreement over a warehouse in Galle be executed when the company (through its directors in Colombo) wants Anil Fernando, a Colombo notary, to attest, while the owner Russel Perera insists on his own Galle notary Ruwan Perera and will not travel to Colombo?",
             "rule": "A lease of immovable property (other than a lease at will or for one month or less) must be in writing signed before a licensed notary public and two witnesses and attested (Prevention of Frauds Ordinance s.2). A company enters into such an obligation in writing signed under its name by two directors (or its sole director, persons authorised by the articles, or its attorneys) and notarially executed (Companies Act No. 7 of 2007 s.19(1)(a)). A notary may not attest outside the area in which he is authorised to practise (Notaries Ordinance s.31 r.22) and may not attest unless the executant is known to him or to two witnesses (r.9, r.10). The Ordinance allows a deed to be executed by two or more parties who do not sign at the same time and place (s.32(2)) and before more than one notary (s.31 r.25): the notary who first attests complies with all of r.20 and keeps the protocol; every other notary complies with r.20(a)-(e) and (g) and keeps a certified copy; each numbers the deed (r.23); the first notary transmits the duplicate (r.28). A notary may not attest a deed drawn by another unless a certificate that the drafter drew it is endorsed (r.2).",
             "application": "Ruwan Perera drafts the Lease Agreement in duplicate (PoF s.16) and endorses his certificate that he drew it. Russel Perera signs in Galle before Ruwan Perera and two witnesses, all present together and signing in one another's presence (r.12); Ruwan Perera, who knows him, attests as first notary. The deed is then taken to Colombo, where two directors sign under the company's name before Anil Fernando (who knows the directors) and two witnesses, and Anil Fernando attests as second notary, stating the r.20(a)-(e) and (g) matters for the signatures he attests. Each notary gives the deed his own serial number; Ruwan Perera keeps the protocol and transmits the duplicate to the Registrar of Lands; Anil Fernando keeps a certified copy. Alternatively Russel Perera could sign through an attorney before Anil Fernando (r.30), but he wants his own notary.",
             "conclusion": "The Lease Agreement can be executed as one deed before two notaries: Russel Perera executes before Ruwan Perera in Galle (first notary) and the company, by two directors, executes before Anil Fernando in Colombo (second notary), each notary attesting within his own area and complying with rule (25). " + TEMPORAL_CAVEAT},
         "answer_claims": q1_claims,
         "confidence": 0.6,
         "status": "needs_legal_review",
         "blocking_reason": "Not blocked, but two caveats for the verifier: (1) temporal - the repo holds no confirmed October 2020 text of Notaries Ordinance s.31/s.32 (see candidate_reason TEMPORAL notes; applicable_version_for_matter_date likely 'history_unknown'); (2) scenario ambiguity over whether the company is lessee or sub-lessor (does not change the execution mechanics)."},
        {"benchmark_question_id": Q2,
         "issues": ["Which notary must give the full attestation where a deed is executed before more than one notary",
                    "The statutory list of matters the attestation must state (rule 20) and its prescribed form (rule 21 / Form E)",
                    "Application of those matters to a single-party signing in Galle (s.32(2)(ii))",
                    "Adjacent first-notary duties (numbering, protocol, duplicate)"],
         "indispensable_authority_ids": ["AUTH-M022-001", "AUTH-M022-002"],
         "supporting_authority_ids": ["AUTH-M022-003", "AUTH-M022-004", "AUTH-M022-012", "AUTH-M022-015", "AUTH-M022-010", "AUTH-M022-005", "AUTH-M022-009", "AUTH-M022-006", "AUTH-M022-022", "AUTH-M022-023", "AUTH-M022-024", "AUTH-M022-020", "AUTH-M022-021"],
         "legal_hop_count": 3,
         "hop_count_basis": "Counted: (1) rule (25)(a) - the first notary must comply with all of rule (20); (2) rule (20) - the enumerated matters (a)-(g) plus signing and sealing; (3) s.32(2)(ii)/rule (21) - the attestation relates to the signing before him and must be substantially in Form E. Cases and rules 14/23/24/28 are supporting.",
         "reasoning_chain": [
             {"step": 1, "text": "Ruwan Perera is the first notary, so rule (25)(a) requires his attestation to comply with all the requirements of rule (20); the second notary's attestation is the reduced one.", "authority_ids": ["AUTH-M022-001"], "relies_on_scenario_fact_ids": ["CL-M022-Q02-007"]},
             {"step": 2, "text": "Rule (20): attest without delay, sign and seal the attestation, and state matters (a) presence and mutual presence, (b) whether executant/witnesses known to him and which, (c) date, place, witnesses' full names and residences, (d) read over or read and explained, (e) consideration paid in his presence and amount, (f) stamps on deed and duplicate, (g) erasures, alterations and interpolations.", "authority_ids": ["AUTH-M022-002"]},
             {"step": 3, "text": "Because only Russel Perera signs before him, the deed is deemed executed before Ruwan Perera when Russel Perera signs (s.32(2)(ii)); the attestation is therefore about that signing in Galle, on that date, before those witnesses.", "authority_ids": ["AUTH-M022-004", "AUTH-M022-012", "AUTH-M022-009"]},
             {"step": 4, "text": "The attestation must be substantially in Form E and legibly signed in the language of the deed; alterations in the attestation are initialled. If Russel Perera's signature differs from his name, both names are given.", "authority_ids": ["AUTH-M022-003", "AUTH-M022-015"]},
             {"step": 5, "text": "As first notary he also numbers the deed, preserves the protocol and transmits the duplicate - duties the examiner may expect to be mentioned alongside the attestation.", "authority_ids": ["AUTH-M022-010", "AUTH-M022-001", "AUTH-M022-005"]},
             {"step": 6, "text": "Case law confirms the attestation comprises the signature and the attestation clause and applies the consideration and stamp statements strictly.", "authority_ids": ["AUTH-M022-022", "AUTH-M022-023", "AUTH-M022-024"]},
         ],
         "gold_answer_draft": {
             "issue": "If Ruwan Perera is the first notary to attest the Lease Agreement, what must he state in his attestation?",
             "rule": "Where a deed is executed before more than one notary, the notary who first attests must comply with all the requirements of rule (20) of s.31 of the Notaries Ordinance (r.25(a)). Rule (20) requires him without delay to attest the deed, sign and seal the attestation, and state: (a) that the deed was signed by the party and the witnesses in his presence and in the presence of one another; (b) whether the executant or the attesting witnesses (specifying which witnesses) were known to him; (c) the day, month and year on which and the place where the deed was executed, and the full names and residences of the attesting witnesses; (d) whether the deed was read over by the executant, or read and explained by the notary to him in the presence of the witnesses; (e) whether any money was paid in his presence as the consideration or part of it and, if so, the actual amount in local currency; (f) the number and value of the adhesive stamps affixed to, or the value of the impressed stamps on, the deed and its duplicate; (g) specifically the erasures, alterations and interpolations in the deed, whether made before it was read over, and any made in the signatures, the serial number and the writing on the stamps. The attestation must be substantially in Form E of the Second Schedule and legibly signed in the language of the deed (r.21).",
             "application": "Ruwan Perera's attestation, given in Galle, should therefore state that the Lease Agreement was signed by Russel Perera and the two witnesses in his presence and in the presence of one another; that Russel Perera is known to him (and whether the witnesses are known to him, naming which); the day, month, year and place (Galle) of the signing and the full names and residences of the two witnesses; that the deed was read over by Russel Perera, or read and explained by Ruwan Perera to him in the witnesses' presence; whether any rent, premium or other consideration was paid in his presence and, if so, how much in rupees (or that none was paid in his presence); the number and value of the stamps on the original and the duplicate; and any erasures, alterations or interpolations and whether they were made before reading over. He signs and seals the attestation in Form E, describing Russel Perera by both names if his signature differs from his name. As first notary he also gives the deed his serial number, preserves the protocol and transmits the duplicate to the Registrar of Lands; the second notary (Anil Fernando) will later state only the r.20(a)-(e) and (g) matters for the directors' signatures.",
             "conclusion": "Ruwan Perera, as first notary, must give the full rule (20) attestation - items (a) to (g) above, signed and sealed, substantially in Form E - in respect of Russel Perera's execution before him in Galle. " + TEMPORAL_CAVEAT + " Rule 20(b) and (e) were rewritten by the 2022 Act and 20(g) by the 2024 Act; those later versions must not be used for this October 2020 matter."},
         "answer_claims": q2_claims,
         "confidence": 0.65,
         "status": "needs_legal_review",
         "blocking_reason": "Not blocked. Caveats: October 2020 text of rule (20)/(25) not confirmable from repo (history_unknown); Form E as in force in 2020 not located in the repository, so the answer describes the form only as rule (21) describes it."}
    ]
}
json.dump(legal_map, open(R + 'legal-map.draft.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
print("written issue-map.json and legal-map.draft.json")
