# Generator for M001 research-agent-A outputs (issue-map.json, candidate-authorities.json,
# legal-map.draft.json). Every excerpt below was copied verbatim from the repo file named
# next to it; hashes were computed with sha256sum on 2026-09-05. Re-running rewrites the
# three JSON files in this folder only.
import json, os

OUT = os.path.dirname(os.path.abspath(__file__)) + os.sep
RUN = "2026-09-05-pilot-01"
AG = "research-agent-A"

# ---------------------------------------------------------------- hashes (sha256sum)
H = {
    "SRC004_JSON": "f46d137c514267f2b8cb730f2db3192e95d80807ed234e032eac71ebc53fbf0d",
    "SRC021_JSON": "b52bd0df348f6d67d2da51f9e9a376d4f3c32faff66c836f106209438cb06f41",
    "SRC001_JSON": "33e39fd241dee89b92e67268f9405c0fe8113599d35018f342e5d47d3fb5a604",
    "SRC024_JSON": "0bb9d7642e254e3af1ce15fa09a1e4ba23a7542202482219a2972804aeac0bbe",
    "AM21_2018_JSON": "10594e46ae449691dc5153aea194987592e13366713956f7efde0b5cdcaa4dcd",
    "SRC004_HTML": "f457777cfa26d8edbf50289d3d18bfa3757c8c9b6a94de6acbd3db961c4d1e4d",
    "SRC001_HTML": "6ef80685d25307d0a315392ff6b6308082c359f19172a008582803189b99fa30",
    "SRC021_PDF": "4a2ba74446d2130e0b7c6602b961d9d2f9db5b2ea1de09b59305502251e39dd4",
    "SRC004_PDF": "47c992a86d24a750501ea27ee8360576b83ed60fd9c43af1e58727e49bccdf34",
    "SRC022_PDF": "00d6274e0c87d6e5512b4262aa27386f0c187527b91d0ec993f4e938f414aff6",
    "SRC022_OCR": "75108b299e4787e2f89b3f4ea34f3be82da8bbd4bf95f4fae17741c8e3b87518",
    "CASE_1922_75": "400b1c1aeaf1636e6f5b267490c1f196fab204780e3cc439a76a130361ad7444",
    "CASE_1907_15": "6d30296e6753de529a3e3577117167b31d6f40fc6112cb2dd7d786e42ea04e88",
    "CASE_1955_69": "eae5e991f1a056447bc5dd82ede1d3555b15fedbef3be133a1969f9e17968cdc",
    "SECTION_VERSIONS": "1604c26d139002f1ea5195adf445c59b6fb8b7d4b830bb3dbe0e4367bfc18c27",
    "AMENDMENT_CHAINS": "72ea4441a852069f46b10d3e0eb218d2eda49f25601c29ebd94f1b800929359a",
    "COMMENCEMENT": "1ce7612fe4a14e7adda276b0142ef2b9ba2ad59884b022deb8368c943b0d49ff",
    "ACTIONS": "7ecd5a41e090c481e377136031e3d4ba174d7f9e934a0326c2fc379508a8efb8",
    "CASE_LINKS": "58cfd0344a9fab4c6c6d643c0eb56b19c74cab2975d01265d828223f807ad119",
    "RULES": "42de75d38c3a4c1936001f4543d0c1a38b4d5c6b2c3e74babee01c6a1c494529",
    "CASES_JSONL": "224b3c813e4070dbc18b87df22f9291fb4fd0f82f044d697d184991ecf74f0d6",
    "SRC027_PARSED": "7fcd1733973d809dbb25c9cfc8979dc3e13e35e6b2ef6cd69c708b985add6f50",
    "SRC027_PDF": "1fb6eff0e46372a5c6e0a62ef3c60e503848293e21c4c407d2e7037b3a932f4b",
    "REGISTRY": "d4349bf242a84e290e9d86004960f9b2976f8e3cd3de4f46abbdc61b7fa946ee",
}
P = {
    "SRC004_JSON": "data/processed/canonical-statutes/SRC004-15-1876.json",
    "SRC021_JSON": "data/processed/canonical-statutes/SRC021-38-2014.json",
    "SRC001_JSON": "data/processed/canonical-statutes/SRC001-7-1840.json",
    "SRC024_JSON": "data/processed/canonical-statutes/SRC024-21-1844.json",
    "AM21_2018_JSON": "data/processed/canonical-amendments/21-2018.json",
    "SRC004_HTML": "data/legal-sources/library/statutes/HTML/15-1876-matrimonial-rights-and-inheritance-ordinance.html",
    "SRC001_HTML": "data/legal-sources/library/statutes/HTML/7-1840-prevention-of-frauds-ordinance.html",
    "SRC021_PDF": "data/legal-sources/library/statutes/38-2014-land-restrictions-on-alienation-act-consolidated-2024.pdf",
    "SRC004_PDF": "data/legal-sources/library/statutes/15-1876-matrimonial-rights-and-inheritance-ordinance.pdf",
    "SRC022_PDF": "data/legal-sources/library/amendments/21-2018-land-restrictions-on-alienation-amendment-act.pdf",
    "SRC022_OCR": "data/legal-sources/library/amendments/ocr/21-2018-land-restrictions-on-alienation-amendment.txt",
    "CASE_1922_75": "data/processed/docs/case-law/commonlii/LKCA/1922/75.md",
    "CASE_1907_15": "data/processed/docs/case-law/commonlii/LKCA/1907/15.md",
    "CASE_1955_69": "data/processed/docs/case-law/commonlii/LKCA/1955/69.md",
    "SECTION_VERSIONS": "data/processed/section_versions.jsonl",
    "AMENDMENT_CHAINS": "data/processed/amendment-chains.csv",
    "COMMENCEMENT": "data/processed/statute_commencement.csv",
    "ACTIONS": "data/processed/actions.csv",
    "CASE_LINKS": "data/processed/case_statute_section_links.csv",
    "RULES": "scripts/case-law-information-extraction/output/rules.csv",
    "CASES_JSONL": "data/processed/cases.jsonl",
    "SRC027_PARSED": "data/legal-sources/library/statutes/parsed/21-1977-partition-law.json",
    "SRC027_PDF": "data/legal-sources/library/statutes/21-1977-partition-law.pdf",
    "REGISTRY": "data/legal-sources/manifests/source-registry.csv",
}


def sp(key, pointer=None):
    s = P[key]
    if pointer:
        s += "#" + pointer
    return s + " sha256:" + H[key]


# ---------------------------------------------------------------- verbatim excerpts
X = {
    "s21_1": "(1) Inheritance ab interstate to the immovable property in Sri Lanka of a person deceased shall be governed and regulated by the following provisions of this Ordinance wherever such person may have or have had his actual or matrimonial domicile. Inheritance to movable property to be governed by the law of domicile.",
    "s22": "22. When any person shall die intestate as to any of his or her property, leaving a spouse surviving, the surviving spouse shall inherit one-half of the property of such person.",
    "s23": "23. Subject to the right of the surviving spouse in the preceding section mentioned, the right of inheritance is divided in the following order as respects (a) descendants, (b) ascendants, (c) collaterals.",
    "s24": "24. Children, grandchildren, and remoter descendants are preferent to all others in the estate of the parents; all the children take equally per capita, but the children or remoter issue of a deceased child take per stirpes or by representation.",
    "s25": "25. The children and remoter descendants failing, the inheritance of the deceased goes to his father and mother in case they are both alive; but if only one of the parents be alive, the surviving parent takes half, and the brothers and sisters of the deceased of the full blood, and the issue of any deceased brother or sister of the full blood, by representation, and the brothers and sisters of the half-blood who are related to the intestate by the side of the deceased parent, and the issue of any such deceased brother or sister of the half-blood, by representation, take the other half. In case there is no full or half-brother or sister alive at the death of the deceased, the surviving parent inherits the whole, although there may be children or other issue of deceased brothers or sisters.",
    "s26": "26. Father and mother both failing, the property of the intestate goes to his brothers and sisters, whether of the whole or balf-blood, and their children and other issue by representation.",
    "s27": "The inheritance is divided into two parts ; the one-half the full brothers and sisters and the issue of such as are deceased by representation divide with the half-brothers and sisters of the father's side and the issue of such as are deceased by representation ; and the other half they divide with those of the mother's side and the issue of such as are deceased by representation ; but if there are only half-brothers and sisters or such issue of one side, the full brothers and sisters and the issue of deceased full brothers and sisters by representation, take then in the first place one-half of the property, and divide the other half with the half-brothers and sisters and their issue by representation.",
    "s33": "33. Illegitimate children inherit the property of their intestate mother, but not that of their father or that of the relatives of their mother. Where an illegitimate person leaves no surviving spouse or descendants, his or her property will go to the heirs of the mother, so as to exclude the State.",
    "s36": "36. In all questions relating to the distribution of the property of an intestate, if the present Ordinance is silent, the rules of the Roman-Dutch law as it prevailed in North Holland are to govern and be followed.",
    "s2_mrio": "2. Whenever a woman marries, after the proclamation of this Ordinance, a man of different race or nationality from her own, she shall be taken to be of the same race and nationality as her husband for all the purposes of this Ordinance, so long as the marriage subsists and until she marries again. Save as aforesaid, this Ordinance shall not apply to Kandyans or Muslims, or to Tamils of the Northern Province who are or may become subject to the Tesawalamai.",
    "lra_s1_2": "(2) The provisions of this Act shall be deemed to have come into operation with effect from January 1, 2013.",
    "lra_s2_1": "(1) Notwithstanding any provision to the contrary in any other written law, the transfer of title of any land situated in Sri Lanka, shall be prohibited if such transfer is-",
    "lra_s2_1a": "(a) to a foreigner; or",
    "lra_s2_2b_ii": "(ii) the death of a shareholder of such company and the shares of the deceased shareholder devolving, in accordance with the applicable laws of succession of Sri Lanka, on his next of kin who is a foreigner, the transfer of land referred to therein shall be void and shall have no effect in law, with effect from the date of increase of the foreign shareholding: Provided however, where a company referred to in paragraph (a),-",
    "lra_s3_1": "(1) The provisions of section 2 shall not apply to-",
    "lra_s3_1d_tree": "(d) any land the title of which is transferred by intestacy, gift or testamentary disposition to a next of kin (who is a foreigner) of the accordance with the applicable law of succession of Sri Lanka;",
    "lra_s3_1d_pdf": "(d) any land the title of which is transferred by intestacy, gift or\n                         testamentary disposition to a next of kin (who is a foreigner) of\n                         the\n\fowner of such land, in accordance with the applicable law of succession\nof Sri Lanka;",
    "lra_s3_1e": "(e) any land the title of which is transferred to a dual citizen of Sri Lanka within the meaning of the Citizenship Act;",
    "lra_s3_4": "(4) Where the transfer of title of a land is effected in terms of this section, the provisions of this Act shall also apply to every subsequent transfer of title of such land or part thereof.",
    "lra_s18": "18. Any alienation of land effected in contravention of the provisions of this Act, shall be void and shall have no effect in law.",
    "def_foreigner": "'foreigner' means a person who is not a citizen of Sri Lanka;",
    "def_citizen": "'citizen of Sri Lanka' means a citizen of Sri Lanka in terms of Citizenship Act;",
    "def_transfer": "'transfer' means any sale, donation, gift or any conveyance by or under which the title of such land passes to another person;",
    "def_land": "'land' means any State or private land and includes-",
    "def_land_a": "(a) any interest in the land;",
    "def_alienation": "'alienation' means transfer, lease or mortgage of lands situated within Sri Lanka;",
    "am_s1": "1. This Act may be cited as the Land (Restrictions on Alienation) (Amendment) Act, No. 21 of 2018 and shall be deemed to have come into operation on April 1. 2018.",
    "am_s2": "2. Section 3 of the Land (Restrictions on Alienation) cnactment\") is hereby amended in subsection (1) (a) by the repeal of paragraph (b) of that subsection and the substitution therefor of the following paragraph:- \"(b) a condominium parcel specified under the Apartment Ownership Law: Provided that, the entire value shall be paid upfront through an inward foreign remittance prior to the execution of the relevant deed of transfer;\"; (b) in paragraph (h) of that subsection by the substitution for the words \"transfer of such land.\" of the words \"transfer of such land; and\"; (c) immediately after paragraph (ht) of that subsection by the addition of the following new paragraph:- \"() any land, the title of which is transferred on or after April 1, 2018. to a company referred to in paragraph (b) of subsection (1)of section 2, listedin the Colombo Stock Exchange.\" \".",
    "pl_s48_1": "(1) Save as provided in subsection (5) of this section, the interlocutory decree entered under section 26 and the final decree of partition entered under section 36 shall, subject to the decision on any appeal which may be preferred therefrom, and in the case of an interlocutory decree, subject also to the provisions of subsection (4) of this section, be good and sufficient evidence of the title of any person as to any right, share or interest awarded therein to him and be final and conclusive for all purposes against all persons whomsoever, whatever right, title or interest they have, or claim to have, to or in the land to which such decree relates and notwithstanding any omission or defect of procedure or in the proof of title adduced before the court or the fact that all persons concerned are not parties to the partition action; and the right, share or interest awarded by any such decree shall be free from all encumbrances whatsoever other than those specified in that decree.",
    "pfo_s2": "2. No sale, purchase, transfer, assignment, or mort gage of land or other immovable property, and no promise, bargain, contract, or agreement for effecting any such object, or for establishing any security, interest, or incumbrance affecting land or other immovable property (other than a lease at will, or for any period not exceeding one month), nor any contract or agreement for the future sale or purchase of any land or other immovable property, and no notice, given under the provisions of the Thesawalamai Pre-emption Ordinance, of an intention or proposal to sell any undivided share or interest in land held in joint or common ownership, shall be of force or avail in law unless the same shall be in writing and signed by the party making the same, or by some person lawfully authorized by him or her in the presence of a licensed notary public and two or more witnesses present at the same time, and unless the execution of such writing, deed, or instrument be duly attested by such notary and witnesses.",
    "wills_s7": "7. And for the avoiding of all doubts and questions as to the respective rights of persons jointly holding landed property situated within certain districts of Sri Lanka, it is further enacted and declared that all landed property situated in Sri Lanka which shall belong to two or more persons jointly, whether the same shall have come to them by grant, purchase, descent, or otherwise, is and shall be deemed and taken to be held by them in common, and upon the decease of any of such persons the said property so jointly possessed shall not remain or belong to the survivor, but all the right, share, and interest of the person so dying in and to the property so jointly possessed as aforesaid shall form part of his estate",
    "fern_head": "Where a property was gifted by a father and mother to their child \" subject to the life interest of us both donors.\" Held , that on the death of the mother a half share of the property became the absolute property of the donee, and that the surviving parent was not entitled to take the life interest of the half share",
    "fern_body": "No such express provision is found in the deed in the present case, and in view of the terms of section 20 of Ordinance No. 21 of 1844, I find it difficult to hold that we can imply any such condition. The-Ordinance expressly provides that where a person jointly holds land, they shall be deemed to hold in common, unless the instrument under which the property is jointly held expressly provides that the survivor shall become entitled to the whole estate on the decease of one of them. In the circumstances I am of opinion that the decree appealed from is right.",
    "uduma": "A donation inter vivos is in its nature irrevocable once it is accepted; and in that respect it differs from a last will, which the testator may revoke at any time he likes.",
    "silva": "Where a landlord donates the rented premises reserving a life-interest in his favour, the donee is entitled to claim the rent from the tenant on the death of the donor; it is not open to the tenant to continue to remain in possession and refuse to pay rent to the new owner on the pretext that he never attorned to the new owner.",
}

TEMPORAL_NOTE_SRC004 = ("section_versions.jsonl: SRC004:s{n}:v1 valid_from_year 1876, valid_to_year null, is_current true, text_available true, amendment_history 'unknown', status unverified. "
                        "actions.csv has no rows for SRC004. amendment-chains.csv lists Ordinance 2 of 1889 as amending SRC004 while the canonical tree header lists Ordinance 18 of 1923 (discrepancy, unverified). "
                        "statute_commencement.csv: SRC004 commencement 1876-06-29 (srilankalaw, unverified). Only the current consolidated text is held; the versions applicable at the 1995, 2022 and 2023 deaths cannot be independently confirmed from the corpus.")
TEMPORAL_NOTE_SRC021 = ("section_versions.jsonl: SRC021:s{n}:v1 valid_from_date 2013-01-01, valid_to_year null, is_current true, text_available true, amendment_history 'unknown', status unverified. "
                        "actions.csv has no rows for SRC021. amendment-chains.csv lists Act 3 of 2017 and Act 21 of 2018 as amending SRC021 (unverified). statute_commencement.csv: SRC021 commencement 2013-01-01. "
                        "Tree verification_status 'structurally_verified'; text is a 2024 consolidated reprint, not the Act as enacted. Suresh died 1995-12-10, before the Act's deemed operation; Rakitha (2022) and Muditha (2023) died after it and after the 2018 amendment.")


def auth(aid, atype, title, enact, sec, subsec, paths, methods, scores, reason, qids, necessity, case_cit=None, court=None, date=None, vstatus="candidate"):
    return {
        "authority_id": aid, "authority_type": atype, "title": title, "enactment_number": enact,
        "section": sec, "subsection": subsec, "case_citation": case_cit, "court": court, "decision_date": date,
        "candidate_source_paths": paths, "retrieval_methods": methods, "retrieval_scores": scores,
        "candidate_reason": reason, "proposed_by_agent": AG, "benchmark_question_ids": qids,
        "necessity_claimed": necessity, "verification_status": vstatus, "verification": None,
    }


MRIO = "Matrimonial Rights and Inheritance Ordinance"
MRIO_NO = "Ordinance No. 15 of 1876"
LRA = "Land (Restrictions on Alienation) Act"
LRA_NO = "Act No. 38 of 2014"

authorities = [
    auth("AUTH-M001-001", "statute_provision", MRIO, MRIO_NO, "21", "1",
         [sp("SRC004_JSON", "/body/2/children/1/children/0"), sp("SRC004_HTML"), sp("SRC004_PDF") + " (pdftotext -layout page 4)", sp("SECTION_VERSIONS") + " version_id SRC004:s21:v1"],
         ["bm25", "dense", "graph_expansion", "hierarchical_act_section"], {"search_q06_rank": "not in top 4 for s21 query; located by direct tree read", "search_q23_rank": "SRC004 ss22-25 top 4"},
         "Located excerpt (tree raw_text, s.21(1)): \"" + X["s21_1"] + "\" -- Establishes that intestate succession to immovable property in Sri Lanka is governed by Part III of this Ordinance, which grounds the application of ss.22-27 to Lot A. Note the tree reads 'ab interstate' where the PDF (page 4) reads 'ab intestato'. " + TEMPORAL_NOTE_SRC004.format(n=21),
         ["M001-Q01", "M001-Q02", "M001-Q03"], "supporting"),
    auth("AUTH-M001-002", "statute_provision", MRIO, MRIO_NO, "22", None,
         [sp("SRC004_JSON", "/body/2/children/2"), sp("SRC004_HTML"), sp("SRC004_PDF") + " (pdftotext -layout page 4: 'inherit one-half of the property of such')", sp("SECTION_VERSIONS") + " version_id SRC004:s22:v1"],
         ["bm25", "dense", "graph_expansion", "hierarchical_act_section"], {"search_q01_score": 0.1360, "search_q01_rank": 1, "search_q02_score": 0.0664, "search_q02_rank": 1},
         "Located excerpt (tree raw_text): \"" + X["s22"] + "\" -- The surviving-spouse half share: applied to Kanthi on Suresh's death (1995) and to Ann on Rakitha's death (2022). " + TEMPORAL_NOTE_SRC004.format(n=22),
         ["M001-Q01", "M001-Q02"], "indispensable"),
    auth("AUTH-M001-003", "statute_provision", MRIO, MRIO_NO, "23", None,
         [sp("SRC004_JSON", "/body/2/children/3"), sp("SRC004_HTML"), sp("SRC004_PDF") + " (pdftotext -layout page 5)", sp("SECTION_VERSIONS") + " version_id SRC004:s23:v1"],
         ["bm25", "dense", "graph_expansion", "hierarchical_act_section"], {"search_q01_score": 0.1326, "search_q01_rank": 3, "search_q03_rank": 1},
         "Located excerpt (tree raw_text): \"" + X["s23"] + "\" -- Order of devolution (descendants, ascendants, collaterals) subject to the spouse's half; frames why Muditha's share goes to ascendant/collaterals. " + TEMPORAL_NOTE_SRC004.format(n=23),
         ["M001-Q01", "M001-Q02"], "supporting"),
    auth("AUTH-M001-004", "statute_provision", MRIO, MRIO_NO, "24", None,
         [sp("SRC004_JSON", "/body/2/children/4"), sp("SRC004_HTML"), sp("SRC004_PDF") + " (pdftotext -layout page 5: 'take per stirpes or by representation')", sp("SECTION_VERSIONS") + " version_id SRC004:s24:v1"],
         ["bm25", "dense", "graph_expansion", "hierarchical_act_section"], {"search_q01_score": 0.1307, "search_q01_rank": 4, "search_q04_rank": 1},
         "Located excerpt (tree raw_text): \"" + X["s24"] + "\" -- Children take per capita: Rakitha, Muditha and Samantha share the other half of Suresh's estate equally; issue of a deceased child (if Rakitha left children) take by representation. " + TEMPORAL_NOTE_SRC004.format(n=24),
         ["M001-Q01", "M001-Q02"], "indispensable"),
    auth("AUTH-M001-005", "statute_provision", MRIO, MRIO_NO, "25", None,
         [sp("SRC004_JSON", "/body/2/children/5"), sp("SRC004_HTML"), sp("SRC004_PDF") + " (pdftotext -layout page 5)", sp("SECTION_VERSIONS") + " version_id SRC004:s25:v1"],
         ["bm25", "dense", "graph_expansion", "hierarchical_act_section"], {"search_q01_score": 0.1337, "search_q01_rank": 2, "search_q05_rank": 1},
         "Located excerpt (tree raw_text): \"" + X["s25"] + "\" -- Governs Muditha's share (no spouse, no descendants; surviving parent Kanthi takes half; full-blood and half-blood siblings take the other half) and the non-spousal half of Rakitha's share if he left no issue. Samantha is a half-blood sister 'related to the intestate by the side of the deceased parent' (Suresh). " + TEMPORAL_NOTE_SRC004.format(n=25),
         ["M001-Q01", "M001-Q02"], "indispensable"),
    auth("AUTH-M001-006", "statute_provision", MRIO, MRIO_NO, "26", None,
         [sp("SRC004_JSON", "/body/2/children/6"), sp("SRC004_HTML"), sp("SRC004_PDF") + " (pdftotext -layout page 5)", sp("SECTION_VERSIONS") + " version_id SRC004:s26:v1"],
         ["bm25", "dense", "graph_expansion", "hierarchical_act_section"], {"search_q01_score": 0.1303, "search_q01_rank": 5},
         "Located excerpt (tree raw_text): \"" + X["s26"] + "\" -- Alternative branch if Kanthi has predeceased Rakitha or Muditha: the whole of the non-spousal share goes to siblings of whole or half blood and their issue. Source text reads 'balf-blood' (typo preserved). " + TEMPORAL_NOTE_SRC004.format(n=26),
         ["M001-Q01", "M001-Q02"], "supporting"),
    auth("AUTH-M001-007", "statute_provision", MRIO, MRIO_NO, "27", None,
         [sp("SRC004_JSON", "/body/2/children/7/children/0"), sp("SRC004_HTML"), sp("SRC004_PDF") + " (pdftotext -layout page 5)", sp("SECTION_VERSIONS") + " version_id SRC004:s27:v1 (not printed; s27 row exists in file)"],
         ["hierarchical_act_section", "manual_corpus_browse", "bm25"], {"search_q01_score": 0.0496, "search_q01_rank": 6},
         "Located excerpt (tree closing_text under s.27, heading 'Division in case of half-brothers and sisters.'): \"" + X["s27"] + "\" -- Division rule where full-blood (Muditha for Rakitha's estate) and half-blood on one side only (Samantha via Suresh) concur; drives the arithmetic in Q02. Whether this rule applies inside s.25 (one parent surviving) or only under s.26 needs legal review. " + TEMPORAL_NOTE_SRC004.format(n=27),
         ["M001-Q02"], "indispensable"),
    auth("AUTH-M001-008", "statute_provision", MRIO, MRIO_NO, "33", None,
         [sp("SRC004_JSON", "/body/2/children/13"), sp("SRC004_HTML"), sp("SRC004_PDF") + " (pdftotext -layout page 5-6)", sp("SECTION_VERSIONS") + " version_id SRC004:s33:v1"],
         ["hierarchical_act_section", "bm25"], {"search_q08_result": "s33 not in top 10 for 'illegitimate children inherit mother' (lexical noise); located by tree read"},
         "Located excerpt (tree raw_text): \"" + X["s33"] + "\" -- Relevant only to the unresolved fact whether Samantha is a legitimate child of Suresh's first marriage; if illegitimate she would not inherit from her father. " + TEMPORAL_NOTE_SRC004.format(n=33),
         ["M001-Q02", "M001-Q03"], "supporting"),
    auth("AUTH-M001-009", "statute_provision", MRIO, MRIO_NO, "36", None,
         [sp("SRC004_JSON", "/body/2/children/16"), sp("SRC004_HTML"), sp("SRC004_PDF") + " (pdftotext -layout page 6: 'North Holland')", sp("SECTION_VERSIONS") + " version_id SRC004:s36:v1"],
         ["hierarchical_act_section", "bm25"], {"search_q07_result": "s36 not in top 4 for 'Roman-Dutch law North Holland' query; located by tree read"},
         "Located excerpt (tree raw_text): \"" + X["s36"] + "\" -- Gateway to Roman-Dutch law for matters on which the Ordinance is silent (e.g. whether a predeceased sibling's widow can take: she is not enumerated). " + TEMPORAL_NOTE_SRC004.format(n=36),
         ["M001-Q01", "M001-Q02"], "supporting"),
    auth("AUTH-M001-010", "statute_provision", MRIO, MRIO_NO, "2", None,
         [sp("SRC004_JSON", "/body/0/children/1"), sp("SRC004_HTML"), sp("SECTION_VERSIONS") + " (s2 row not individually printed)"],
         ["hierarchical_act_section", "manual_corpus_browse"], {},
         "Located excerpt (tree raw_text): \"" + X["s2_mrio"] + "\" -- Scope limit: the Ordinance does not apply to Kandyans, Muslims or Tamils subject to Tesawalamai; the facts give no personal-law indicator, so the general law is assumed and this must be flagged. " + TEMPORAL_NOTE_SRC004.format(n=2),
         ["M001-Q01", "M001-Q02"], "supporting"),
    auth("AUTH-M001-011", "statute_provision", LRA, LRA_NO, "2", "1",
         [sp("SRC021_JSON", "/body/1/children/0"), sp("SRC021_JSON", "/body/1/children/0/children/0"), sp("SRC021_PDF") + " (pdftotext -layout page 2, lines 3-6)", sp("SECTION_VERSIONS") + " version_id SRC021:s2:v1"],
         ["named_in_question", "bm25", "dense", "graph_expansion", "direct_citation_lookup"], {"search_q09_score": 0.1860, "search_q09_rank": 1, "search_q24_score": 0.1348, "search_q24_rank": 1},
         "Located excerpt (tree raw_text s.2(1) and (a)): \"" + X["lra_s2_1"] + "\" \"" + X["lra_s2_1a"] + "\" -- The prohibition the question asks about; whether devolution on intestacy is a 'transfer' at all is arguable, but s.3(1)(d) makes the point moot. " + TEMPORAL_NOTE_SRC021.format(n=2),
         ["M001-Q03"], "indispensable"),
    auth("AUTH-M001-012", "statute_provision", LRA, LRA_NO, "3", "1(d)",
         [sp("SRC021_JSON", "/body/2/children/0/children/3"), sp("SRC021_PDF") + " (pdftotext -layout page 3 last lines to page 4 first lines)", sp("SECTION_VERSIONS") + " version_id SRC021:s3:v1"],
         ["named_in_question", "bm25", "dense", "graph_expansion", "direct_citation_lookup"], {"search_q10_score": 0.1842, "search_q10_rank": 1},
         "Located excerpt (tree raw_text): \"" + X["lra_s3_1d_tree"] + "\" -- PDF text (pages 3-4) reads: \"" + X["lra_s3_1d_pdf"].replace("\n", " ").replace("\f", " ") + "\". The tree drops the words 'the owner of such land, in' at the page break (see source_conflicts). This is the exemption that lets a foreigner next of kin take land by intestacy, gift or will; it is original 2014 text (the 2018 amendment touched only paras (b), (h), (i) per the tree's amendment_events). " + TEMPORAL_NOTE_SRC021.format(n=3),
         ["M001-Q03"], "indispensable"),
    auth("AUTH-M001-013", "statute_provision", LRA, LRA_NO, "3", "1(e)",
         [sp("SRC021_JSON", "/body/2/children/0/children/4"), sp("SRC021_PDF") + " (pdftotext -layout page 4: 'dual citizen of Sri')", sp("SECTION_VERSIONS") + " version_id SRC021:s3:v1"],
         ["named_in_question", "bm25", "dense", "direct_citation_lookup"], {"search_q11_result": "s3 rank 1 (0.1343)"},
         "Located excerpt (tree raw_text): \"" + X["lra_s3_1e"] + "\" -- Alternative exemption if Samantha is a dual citizen of Sri Lanka (unresolved fact). " + TEMPORAL_NOTE_SRC021.format(n=3),
         ["M001-Q03"], "supporting"),
    auth("AUTH-M001-014", "statute_definition", LRA, LRA_NO, "25", None,
         [sp("SRC021_JSON", "/body/25/children/8"), sp("SRC021_JSON", "/body/25/children/4"), sp("SRC021_JSON", "/body/25/children/16"), sp("SRC021_JSON", "/body/25/children/14"), sp("SRC021_JSON", "/body/25/children/0"), sp("SRC021_PDF") + " (pdftotext -layout page 15: \"'foreigner' means a person who is not a citizen of Sri Lanka;\")", sp("SECTION_VERSIONS") + " version_id SRC021:s25:v1"],
         ["named_in_question", "bm25", "direct_citation_lookup", "hierarchical_act_section"], {"search_q13_s25_score": 0.0276, "search_q13_s25_rank": 2},
         "Located excerpts (tree definition nodes): \"" + X["def_foreigner"] + "\" \"" + X["def_citizen"] + "\" \"" + X["def_transfer"] + "\" \"" + X["def_land"] + " " + X["def_land_a"] + "\" \"" + X["def_alienation"] + "\" -- Samantha (US citizen) is a 'foreigner' unless she is also a Sri Lankan citizen; 'transfer' is defined by sale, donation, gift or conveyance, which bears on whether intestate devolution is a 'transfer'; 'land' includes any interest in land (an undivided share). " + TEMPORAL_NOTE_SRC021.format(n=25),
         ["M001-Q03"], "indispensable"),
    auth("AUTH-M001-015", "statute_provision", LRA, LRA_NO, "1", "2",
         [sp("SRC021_JSON", "/body/0/children/1"), sp("SRC021_PDF") + " (pdftotext -layout page 2: 'operation with effect from January 1, 2013')", sp("COMMENCEMENT") + " row SRC021 2013-01-01", sp("SECTION_VERSIONS") + " version_id SRC021:s1:v1"],
         ["named_in_question", "amendment_metadata", "hierarchical_act_section"], {},
         "Located excerpt (tree raw_text): \"" + X["lra_s1_2"] + "\" -- Temporal point: Suresh died on 10 December 1995, so the devolution of his estate on Samantha occurred before the Act's deemed date of operation; only the 2022 and 2023 accretions fall within the Act's period. " + TEMPORAL_NOTE_SRC021.format(n=1),
         ["M001-Q03"], "indispensable"),
    auth("AUTH-M001-016", "statute_provision", LRA, LRA_NO, "18", None,
         [sp("SRC021_JSON", "/body/18"), sp("SRC021_PDF") + " (pdftotext -layout page 13: 'shall be void and shall have no effect')", sp("SECTION_VERSIONS") + " version_id SRC021:s18:v1"],
         ["bm25", "hierarchical_act_section"], {"search_q13_result": "s18 not returned in top 10 for its own words (lexical noise); located by tree read"},
         "Located excerpt (tree raw_text): \"" + X["lra_s18"] + "\" -- Consequence if the prohibition applied and no exemption did: the alienation would be void. Supporting context for the yes/no answer. " + TEMPORAL_NOTE_SRC021.format(n=18),
         ["M001-Q03"], "supporting"),
    auth("AUTH-M001-017", "statute_provision", LRA, LRA_NO, "3", "4",
         [sp("SRC021_JSON", "/body/2/children/3"), sp("SRC021_PDF") + " (page 4-5, not line-located)", sp("SECTION_VERSIONS") + " version_id SRC021:s3:v1"],
         ["hierarchical_act_section", "manual_corpus_browse"], {},
         "Located excerpt (tree raw_text): \"" + X["lra_s3_4"] + "\" -- If Samantha takes under the s.3 exemption, any later transfer by her of that land remains subject to the Act. " + TEMPORAL_NOTE_SRC021.format(n=3),
         ["M001-Q03"], "supporting"),
    auth("AUTH-M001-018", "statute_provision", LRA, LRA_NO, "2", "2(b)(ii)",
         [sp("SRC021_JSON", "/body/1/children/1/children/1/children/1"), sp("SRC021_PDF") + " (pdftotext -layout page 2: 'of succession of Sri Lanka, on his next of kin who is a foreigner')"],
         ["hierarchical_act_section", "manual_corpus_browse"], {},
         "Located excerpt (tree raw_text): \"" + X["lra_s2_2b_ii"] + "\" -- Shows the Act itself contemplates devolution 'in accordance with the applicable laws of succession of Sri Lanka' on a foreigner next of kin (company-shareholding context); contextual support only for reading s.3(1)(d). " + TEMPORAL_NOTE_SRC021.format(n=2),
         ["M001-Q03"], "supporting"),
    auth("AUTH-M001-019", "amendment", "Land (Restrictions on Alienation) (Amendment) Act", "Act No. 21 of 2018", "1; 2", None,
         [sp("AM21_2018_JSON", "/body/0"), sp("AM21_2018_JSON", "/body/1"), sp("SRC022_OCR"), sp("SRC022_PDF") + " (4-page scan, no text layer; pdftotext not usable)", sp("SRC021_JSON", "/body/2") + " amendment_events", sp("AMENDMENT_CHAINS") + " row SRC021 / Act 21 of 2018"],
         ["named_in_question", "amendment_metadata", "bm25"], {"search_q14_SRC022_s2_score": 0.1339, "search_q14_rank": 1, "search_q15_rank": 1},
         "Located excerpts (amendment tree raw_text, parsed from OCR, carries OCR errors): \"" + X["am_s1"] + "\" and \"" + X["am_s2"] + "\". The amendment (deemed operative 1 April 2018) replaced s.3(1)(b), amended s.3(1)(h) and added s.3(1)(i); the tree's known_ocr_defects note '(ht)' should read '(h)' and the missing paragraph letter is '(i)'. It did not touch s.3(1)(d) or (e) or the s.25 definition of 'foreigner'. The question names this Act, so its (non-)effect on the succession exemption must be stated. Tree verification_status 'unverified'; LankaLaw HTML edition is incomplete per quality_notes.",
         ["M001-Q03"], "indispensable"),
    auth("AUTH-M001-020", "statute_provision", "Partition Law", "Law No. 21 of 1977", "48", "1",
         [sp("SRC027_PARSED", "/sections/50 (section_number 48)"), sp("SRC027_PDF") + " (parsed page_start 29)", sp("SECTION_VERSIONS") + " version_ids SRC027:s48:v1 (1977-1997, text_available false) and SRC027:s48:v2 (1997-, is_current true)"],
         ["bm25", "manual_corpus_browse"], {"search_q18_s48_score": 0.0164, "search_q18_s48_rank": 2, "search_q19_s48_rank": 4},
         "Located excerpt (parsed JSON text, s.48(1), heading 'Finality of interlocutory decrees of partition. [21, 17 of 1997]'): \"" + X["pl_s48_1"] + "\" -- Root-of-title step for the pedigree: the 1985 final decree allotting Lot A to Gamini is conclusive evidence of his title. TEMPORAL FLAG: the corpus holds only the text as amended by Act 17 of 1997; the version in force at the 1985 decree (SRC027:s48:v1) is not held (text_available false). SRC027 has no canonical tree (index/parsed JSON only); parsed file verification_status 'unverified'; registry markdown path does not exist on disk.",
         ["M001-Q01"], "supporting"),
    auth("AUTH-M001-021", "statute_provision", "Prevention of Frauds Ordinance", "Ordinance No. 7 of 1840", "2", None,
         [sp("SRC001_JSON", "/body/1"), sp("SRC001_HTML"), sp("SECTION_VERSIONS") + " version_ids SRC001:s2:v1-v4 (current v4 from 2024, text_available true; earlier versions text not held)"],
         ["bm25", "dense", "graph_expansion", "hierarchical_act_section"], {"search_q20_score": 0.1857, "search_q20_rank": 1},
         "Located excerpt (tree raw_text): \"" + X["pfo_s2"] + "\" -- Formal validity: Deed of Gift No. 515 and Deed of revocation No. 525 are stated to be notarially attested, satisfying the writing/notary/witness requirement for instruments affecting land. TEMPORAL FLAG: section_versions records four versions of s.2 (1840, 1947, 2022, 2024); only the 2024 text is held, so the 1986/1991 wording is not independently confirmable. Tree verification_status 'unverified'.",
         ["M001-Q01"], "supporting"),
    auth("AUTH-M001-022", "case", "Fernando v. Fernando", None, None, None,
         [sp("CASE_1922_75") + " (headnote, line 3, char offset ~590-900; ratio at 'ENNIS- J.-')", sp("RULES") + " rule_id draftly-rule-commonlii-LKCA-1922-75-1", sp("CASES_JSONL") + " case_id commonlii-LKCA-1922-75"],
         ["extracted_holding", "case_fulltext_search"], {"rules_csv_scope": "ratio", "rules_csv_status": "unverified", "rules_csv_method": "llm-extract"},
         "Opened judgment. Headnote (verbatim from judgment file): \"" + X["fern_head"] + "\". Ratio (Ennis J.): \"" + X["fern_body"] + "\" -- Directly analogous: a gift to a child 'subject to the life interest of us both donors'; on the death of one donor (here Gamini, 1990) the donee took a half share absolutely and the surviving donor's life interest did not extend to that half. Explains the 1990-1991 position before Vinitha's revocation. Court of Appeal (CommonLII LKCA database), 3 February 1922, Ennis and Porter JJ. The judgment cites 'section 20 of Ordinance No. 21 of 1844' (survivorship provision), which appears in the current consolidated Wills Ordinance tree as s.7 (see AUTH-M001-025); the renumbering is not verified.",
         ["M001-Q01"], "supporting", case_cit="(1922) 24 NLR 138; [1922] LKCA 75", court="Supreme Court of Ceylon (CommonLII database: Court of Appeal of Sri Lanka, LKCA)", date="1922-02-03"),
    auth("AUTH-M001-023", "case", "Uduma Levvai v. Mayatin Vava et al.", None, None, None,
         [sp("CASE_1907_15") + " (line 3, char offset 8517)", sp("RULES") + " rule_id draftly-rule-commonlii-LKCA-1907-15-1", sp("CASES_JSONL") + " case_id commonlii-LKCA-1907-15"],
         ["extracted_holding", "case_fulltext_search"], {"rules_csv_scope": "ratio", "rules_csv_status": "unverified"},
         "Opened judgment. Verbatim passage: \"" + X["uduma"] + "\" -- Supports the step that the 1986 deed of gift, once accepted, passed a present and irrevocable right to Suresh, with enjoyment postponed by the reserved life interests. Acceptance by Suresh is not stated in the facts (unresolved). Case context is a Muslim donation; the stated principle is general Roman-Dutch law on donation inter vivos, but applicability needs legal review.",
         ["M001-Q01"], "supporting", case_cit="(1907) 10 NLR 347; [1907] LKCA 15", court="Supreme Court of Ceylon (CommonLII database: LKCA)", date="1907-10-15"),
    auth("AUTH-M001-024", "case", "Silva et al. v. Muniamma", None, None, None,
         [sp("CASE_1955_69") + " (headnote, line 3, char offset 740)", sp("RULES") + " rule_id draftly-rule-commonlii-LKCA-1955-69-1", sp("CASES_JSONL") + " case_id commonlii-LKCA-1955-69"],
         ["extracted_holding", "case_fulltext_search"], {"rules_csv_scope": "ratio", "rules_csv_status": "unverified"},
         "Opened judgment. Headnote (verbatim): \"" + X["silva"] + "\" -- Illustrates that where premises are donated reserving a life interest to the donor, the donee is treated as the 'new owner' whose full enjoyment opens on the donor's death; supports the pedigree step that Suresh's ownership became unencumbered on the ending of the life interests. Headnote-level support only (Sansoni J., Court of Requests appeal).",
         ["M001-Q01"], "supporting", case_cit="(1955) 56 NLR 357; [1955] LKCA 69", court="Supreme Court of Ceylon (CommonLII database: LKCA)", date="1955-01-24"),
    auth("AUTH-M001-025", "statute_provision", "Wills Ordinance", "Ordinance No. 21 of 1844", "7", None,
         [sp("SRC024_JSON", "/body/6")],
         ["manual_corpus_browse", "case_statute_link"], {},
         "Located excerpt (tree raw_text, truncated at the node boundary shown): \"" + X["wills_s7"] + "\" -- The 'no survivorship' rule Fernando v. Fernando relied on (cited there as s.20 of Ordinance 21 of 1844) to hold that the surviving donor's life interest did not extend to the deceased donor's half. Included only as the statutory basis of AUTH-M001-022; the section-number correspondence is unverified. Tree verification_status 'unverified' (LankaLaw consolidated edition).",
         ["M001-Q01"], "supporting"),
    auth("AUTH-M001-026", "common_law_principle", "Roman-Dutch law: effect of a life-interest (usufruct) holder's renunciation or revocation on the dominus's ownership -- NOT LOCATED IN CORPUS", None, None, None,
         [],
         ["bm25", "dense", "graph_expansion", "extracted_holding", "manual_corpus_browse"], {"search_q16_top": "SRC034:s71 (Stamp Duty), SRC033:s5 (Land Reform Law) -- irrelevant", "rules_csv": "344 keyword hits reviewed; none states the renunciation principle"},
         "NOT LOCATED. The pedigree step 'Vinitha's Deed of revocation No. 525 (1991) extinguished her life interest so that Suresh held Lot A free of encumbrance' requires a rule that a life interest/usufruct is extinguished by the holder's renunciation and merges in the dominium. No statute in the 57-statute corpus states this, and no extracted case rule in rules.csv or case_statute_section_links.csv does so (searches recorded in negative_retrieval). SRC004 s.36 (AUTH-M001-009) points to Roman-Dutch law but supplies no text. This placeholder exists so the dependent claim can be marked inferential/unverified; the verifier must source it or the step stays blocked.",
         ["M001-Q01"], "indispensable"),
]

negative = [
    {"query": "life interest usufruct gift subject to life interest donor", "method": "uv run python -m draftly.retrieval search --limit 10 (bm25+dense+graph)", "corpus": "statutes (57 statutes + 18 amendments)", "result": "Top hits SRC034:s71 (Stamp Duty Act interpretation), SRC033:s5 (Land Reform Law usufruct), SRC035:s48, SRC037:s3 -- none states the law of life interests or their termination. No statutory source for Roman-Dutch law of usufruct/life interest exists in the corpus.", "benchmark_question_ids": ["M001-Q01"]},
    {"query": "revocation of deed of gift donation irrevocable", "method": "uv run python -m draftly.retrieval search --limit 10", "corpus": "statutes", "result": "Only SRC037 (Revocation of Irrevocable Deeds of Gift on the Ground of Gross Ingratitude Act No. 5 of 2017) returned; it concerns revocation of gifts for ingratitude, not revocation/renunciation of a reserved life interest. Not relevant.", "benchmark_question_ids": ["M001-Q01"]},
    {"query": "renunciation / revocation of life interest by holder; extinction of usufruct", "method": "grep of scripts/case-law-information-extraction/output/rules.csv statements (regex: life[- ]interest|usufruct|renounc|revocation)", "corpus": "cases (extracted rules, 4161 rows)", "result": "344 keyword hits reviewed; none states that a life-interest holder's renunciation vests full ownership in the dominus. Closest are Fernando v. Fernando (1922) 24 NLR 138 (death of one life-interest holder) and Silva v. Muniamma (1955) 56 NLR 357 (donee becomes owner on donor's death), both recorded as candidates.", "benchmark_question_ids": ["M001-Q01"]},
    {"query": "Roman-Dutch law North Holland to be followed where Ordinance silent", "method": "uv run python -m draftly.retrieval search --source-id SRC004 --limit 10", "corpus": "statutes", "result": "SRC004:s36 not in top 4 (returned s16, s1, s25, s24); located instead by reading the canonical tree directly. Retrieval miss recorded.", "benchmark_question_ids": ["M001-Q01", "M001-Q02"]},
    {"query": "illegitimate children inherit mother", "method": "uv run python -m draftly.retrieval search --source-id SRC004 --limit 10", "corpus": "statutes", "result": "SRC004:s33 not returned in top 10 (s34, s17, s12, s7 returned); located by tree read. Retrieval miss recorded.", "benchmark_question_ids": ["M001-Q02"]},
    {"query": "alienation of land in contravention of this Act to be void", "method": "uv run python -m draftly.retrieval search --source-id SRC021 --limit 10", "corpus": "statutes", "result": "SRC021:s18 not returned in top 10 despite verbatim wording (s10, s25, s6, s5 returned); located by tree read. Retrieval miss recorded.", "benchmark_question_ids": ["M001-Q03"]},
    {"query": "Partition Law final decree of partition conclusive", "method": "uv run python -m draftly.retrieval search (with and without --source-id SRC027)", "corpus": "statutes", "result": "SRC027 s26, s48, s52A, s75, s36 returned. SRC027 has no canonical tree in data/processed/canonical-statutes/ (index and parsed JSON only). section_versions.jsonl shows s48 v1 (1977-1997) text_available false, so the text in force at the 1985 decree is not held. Registry local_markdown_path for SRC027 does not exist on disk.", "benchmark_question_ids": ["M001-Q01"]},
    {"query": "Land (Restrictions on Alienation) (Amendment) Act 21 of 2018 -- PDF text", "method": "pdftotext -layout (poppler, PowerShell) on data/legal-sources/library/amendments/21-2018-land-restrictions-on-alienation-amendment-act.pdf", "corpus": "amendments", "result": "Registry local_pdf_path for SRC022 ('...-amendment.pdf') does not exist; actual file is '...-amendment-act.pdf'. It is a 4-page scan without a text layer, so no page-located verbatim text; only the offline OCR reading (ocr/21-2018-...txt) and the OCR-derived tree (canonical-amendments/21-2018.json, 'unverified', known_ocr_defects) are available.", "benchmark_question_ids": ["M001-Q03"]},
    {"query": "case law on SRC021 ss.2, 3, 25 (foreigner inheriting land; Land (Restrictions on Alienation) Act)", "method": "filter of data/processed/case_statute_section_links.csv (14665 rows) on source_id SRC021; grep of rules.csv for 'Restrictions on Alienation|foreigner|citizen'", "corpus": "cases", "result": "Zero rows link any case to SRC021. No extracted rule mentions the Act, 'foreigner' or citizenship in a land-alienation sense. No case authority available for Q03 in the corpus.", "benchmark_question_ids": ["M001-Q03"]},
    {"query": "case law on SRC004 ss.22-25 (surviving spouse half; per capita / per stirpes; descendants failing)", "method": "filter of case_statute_section_links.csv on SRC004 s20-s26, s33, s36; rules.csv rows with statute_section SRC004-s22..s25", "corpus": "cases", "result": "Links found only for s20, s21, s24, s26 and are Thesawalamai/Jaffna-Ordinance or fidei commissum contexts (e.g. Murugupillai v. Poothatamby 20 NLR 204 on s24 is a Tesawalamai case; Samaradiwakara v. De Saram 13 NLR 353 on s26 concerns 'lawful heirs' under a will). Only rule with statute_section SRC004-s24 (LKCA-1969-30) is about a deed condition, irrelevant. No general-law case applying ss.22-27 to a fact pattern like this one was found; the statutory text stands alone.", "benchmark_question_ids": ["M001-Q01", "M001-Q02"]},
    {"query": "widow of predeceased child inherits share of husband / spouse of predeceased sibling taking by representation", "method": "uv run python -m draftly.retrieval search --limit 10; rules.csv grep 'representation'", "corpus": "both", "result": "Statute search returned SRC004:s24, s22 and Jaffna Ordinance (SRC045) sections; nothing addresses a predeceased sibling's widow. rules.csv 'representation' hits are estoppel or fidei commissum contexts. The conclusion that Ann takes nothing from Muditha rests on the enumeration in ss.25-27 (which names issue, not spouses, as taking by representation) and is marked inferential.", "benchmark_question_ids": ["M001-Q02"]},
    {"query": "Trusts Ordinance life interest beneficiary", "method": "uv run python -m draftly.retrieval search --limit 10", "corpus": "statutes", "result": "SRC059 s3, s20, s29, s9 returned; none concerns a reserved life interest in a deed of gift. SRC059 has a canonical tree but its registry PDF is a 1980 Legislative Enactments volume (Trusts from PDF page 311); not pursued further as not relevant.", "benchmark_question_ids": ["M001-Q01"]},
    {"query": "acceptance of a deed of gift by the donee (validity of the 1986 gift)", "method": "rules.csv grep 'acceptance'", "corpus": "cases", "result": "Several extracted rules (e.g. LKCA-1913-1 on notarial acceptance; LKCA-1910-1 on acceptance inferred from circumstances) exist but the judgments were not opened for this matter; acceptance is treated as an unresolved fact rather than a researched issue. Not cited.", "benchmark_question_ids": ["M001-Q01"]},
    {"query": "actions.csv rows for SRC004 / SRC021 (which amending Act touched ss.21-27 or ss.2, 3, 25)", "method": "grep '^SRC004,|^SRC021,' data/processed/actions.csv", "corpus": "amendment metadata", "result": "Zero rows for either statute. Amendment history for the cited sections is therefore 'unknown' in the corpus (matches section_versions.jsonl amendment_history 'unknown').", "benchmark_question_ids": ["M001-Q01", "M001-Q02", "M001-Q03"]},
]

conflicts = [
    {"authority_id": "AUTH-M001-012", "description": "Section 3(1)(d) wording: the canonical tree drops the words at the PDF page 3/4 break ('the owner of such land, in'), reading 'to a next of kin (who is a foreigner) of the accordance with'; the PDF text layer reads 'of the owner of such land, in accordance with'.",
     "versions": [
         {"source_path": P["SRC021_JSON"] + "#/body/2/children/0/children/3", "source_hash": H["SRC021_JSON"], "excerpt": X["lra_s3_1d_tree"]},
         {"source_path": P["SRC021_PDF"] + " (pdftotext -layout, page 3 last lines and page 4 first lines)", "source_hash": H["SRC021_PDF"], "excerpt": X["lra_s3_1d_pdf"]},
     ], "resolution": "unresolved_requires_legal_review"},
    {"authority_id": "AUTH-M001-001", "description": "Section 21(1): tree (from LankaLaw HTML) reads 'Inheritance ab interstate'; the LankaLaw PDF text layer (page 4) reads 'Inheritance ab intestato'. Typographical variance only, but the tree text is what is quoted.",
     "versions": [
         {"source_path": P["SRC004_JSON"] + "#/body/2/children/1/children/0", "source_hash": H["SRC004_JSON"], "excerpt": X["s21_1"]},
         {"source_path": P["SRC004_PDF"] + " (pdftotext -layout page 4)", "source_hash": H["SRC004_PDF"], "excerpt": "21. (1) Inheritance ab intestato to the Inheritance to"},
     ], "resolution": "unresolved_requires_legal_review"},
    {"authority_id": "AUTH-M001-001", "description": "Amendment history of SRC004: amendment-chains.csv lists 'Ordinance 2 of 1889' as the amending instrument; the canonical tree header lists 'Ordinance 18 of 1923'. Both unverified.",
     "versions": [
         {"source_path": P["AMENDMENT_CHAINS"], "source_hash": H["AMENDMENT_CHAINS"], "excerpt": "SRC004,Matrimonial Rights and Inheritance Ordinance,Ordinance,2,1889,amending,1,unverified"},
         {"source_path": P["SRC004_JSON"] + "#/amendments", "source_hash": H["SRC004_JSON"], "excerpt": "[{'type': 'Ordinance', 'number': 18, 'year': 1923}]"},
     ], "resolution": "unresolved_requires_legal_review"},
]

cand = {
    "benchmark_matter_id": "M001", "run_id": RUN, "stage": "authorities_candidate", "produced_by_agent": AG,
    "matter_reference_date": "2026-04",
    "matter_reference_date_basis": "Exam session April 2026 (Sri Lanka Law College, Conveyancing LW 307); questions ask for 'present owners' and 'shares presently owned'. Events span 1981-2023; statutes are held only as current consolidated text (LRA to 2024; MRIO LankaLaw consolidation), so version drift at the 1985, 1986, 1991, 1995, 2022 and 2023 event dates is flagged per authority and cannot be resolved from the corpus.",
    "authorities": authorities, "negative_retrieval": negative, "source_conflicts": conflicts,
}

# ---------------------------------------------------------------- legal map draft
def claim(cid, text, ctype, auths, excerpts, strength, sfb=None):
    c = {"claim_id": cid, "claim_text": text, "claim_type": ctype, "supporting_authority_ids": auths,
         "supporting_excerpts": excerpts, "support_strength": strength, "verification_status": "unverified"}
    if strength == "scenario_fact":
        c["scenario_fact_basis"] = sfb
    return c


def ex(aid, excerpt, loc):
    return {"authority_id": aid, "excerpt": excerpt, "locator": loc}


L = {  # locators
    "s21": P["SRC004_JSON"] + "#/body/2/children/1/children/0", "s22": P["SRC004_JSON"] + "#/body/2/children/2",
    "s23": P["SRC004_JSON"] + "#/body/2/children/3", "s24": P["SRC004_JSON"] + "#/body/2/children/4",
    "s25": P["SRC004_JSON"] + "#/body/2/children/5", "s26": P["SRC004_JSON"] + "#/body/2/children/6",
    "s27": P["SRC004_JSON"] + "#/body/2/children/7/children/0", "s33": P["SRC004_JSON"] + "#/body/2/children/13",
    "s36": P["SRC004_JSON"] + "#/body/2/children/16", "s2m": P["SRC004_JSON"] + "#/body/0/children/1",
    "l1_2": P["SRC021_JSON"] + "#/body/0/children/1", "l2_1": P["SRC021_JSON"] + "#/body/1/children/0",
    "l2_1a": P["SRC021_JSON"] + "#/body/1/children/0/children/0", "l3_1d": P["SRC021_JSON"] + "#/body/2/children/0/children/3",
    "l3_1e": P["SRC021_JSON"] + "#/body/2/children/0/children/4", "l3_4": P["SRC021_JSON"] + "#/body/2/children/3",
    "l18": P["SRC021_JSON"] + "#/body/18", "def_f": P["SRC021_JSON"] + "#/body/25/children/8",
    "def_t": P["SRC021_JSON"] + "#/body/25/children/16", "def_l": P["SRC021_JSON"] + "#/body/25/children/14",
    "am1": P["AM21_2018_JSON"] + "#/body/0", "am2": P["AM21_2018_JSON"] + "#/body/1",
    "pl48": P["SRC027_PARSED"] + "#/sections/50", "pfo2": P["SRC001_JSON"] + "#/body/1",
    "fern": P["CASE_1922_75"] + " line 3 (headnote)", "fernb": P["CASE_1922_75"] + " line 3 (Ennis J.)",
    "uduma": P["CASE_1907_15"] + " line 3 offset 8517", "silva": P["CASE_1955_69"] + " line 3 offset 740",
    "w7": P["SRC024_JSON"] + "#/body/6",
}

FACTS = "source.matter-record.json matter_background.normalized"

q1_claims = [
    claim("CL-M001-Q01-001", "Gamini Perera became owner of Lot A (Plan No 2525, No 20 Flower Road, Homagama, 10 perches) by the final decree in partition case No 111/P, DC Homagama, dated 2 February 1985.", "scenario_inference", [], [], "scenario_fact", FACTS + ": first sentence (allotment by final decree)."),
    claim("CL-M001-Q01-002", "A final decree of partition is good and sufficient evidence of the title of the person to whom a lot is awarded and is final and conclusive against all persons; the 1985 decree is therefore the root of title for the pedigree.", "rule", ["AUTH-M001-020"], [ex("AUTH-M001-020", X["pl_s48_1"], L["pl48"])], "direct"),
    claim("CL-M001-Q01-003", "By Deed of Gift No. 515 of 10 March 1986 (R Liyanage NP) Gamini gifted Lot A absolutely and irrevocably to Suresh subject to the life interest of Gamini and his wife Vinitha; the deed being notarially attested satisfies the formal requirement for an instrument transferring land.", "application", ["AUTH-M001-021"], [ex("AUTH-M001-021", X["pfo_s2"], L["pfo2"])], "direct"),
    claim("CL-M001-Q01-004", "An accepted donation inter vivos is irrevocable and gives the donee a present right to the property; a gift may validly be made subject to a reserved life interest, the donee becoming the owner whose full enjoyment opens when the life interest ends. Suresh therefore held the dominium of Lot A from 1986, burdened by the two life interests (acceptance by Suresh is assumed, not stated).", "rule", ["AUTH-M001-023", "AUTH-M001-024"], [ex("AUTH-M001-023", X["uduma"], L["uduma"]), ex("AUTH-M001-024", X["silva"], L["silva"])], "combined"),
    claim("CL-M001-Q01-005", "On Gamini's death on 12 June 1990 his life interest ended; where property is gifted 'subject to the life interest of us both donors', the death of one donor frees a half share absolutely in the donee and the surviving donor's life interest does not extend to that half. From 12 June 1990 Suresh held one half of Lot A free and the other half subject to Vinitha's life interest.", "rule", ["AUTH-M001-022", "AUTH-M001-025"], [ex("AUTH-M001-022", X["fern_head"], L["fern"]), ex("AUTH-M001-022", X["fern_body"], L["fernb"]), ex("AUTH-M001-025", X["wills_s7"], L["w7"])], "combined"),
    claim("CL-M001-Q01-006", "Vinitha revoked (renounced) her life interest by Deed of revocation No. 525 of 25 February 1991 (S Sapumal NP), a notarially attested instrument; on that renunciation the life interest was extinguished and Suresh held the whole of Lot A free of encumbrance. The renunciation rule itself is a Roman-Dutch law principle for which no source was located in the corpus.", "application", ["AUTH-M001-026", "AUTH-M001-021", "AUTH-M001-009"], [ex("AUTH-M001-021", X["pfo_s2"], L["pfo2"]), ex("AUTH-M001-009", X["s36"], L["s36"])], "inferential"),
    claim("CL-M001-Q01-007", "Suresh Perera died intestate on 10 December 1995 leaving (on the facts) his wife Kanthi and three children: Rakitha and Muditha (by Kanthi) and Samantha (by his first marriage). Intestate succession to immovable property in Sri Lanka is governed by Part III of the Matrimonial Rights and Inheritance Ordinance (general law assumed; not Kandyan, Muslim or Tesawalamai).", "rule", ["AUTH-M001-001", "AUTH-M001-010"], [ex("AUTH-M001-001", X["s21_1"], L["s21"]), ex("AUTH-M001-010", X["s2_mrio"], L["s2m"])], "combined"),
    claim("CL-M001-Q01-008", "On Suresh's intestacy the surviving spouse Kanthi inherited one-half of Lot A, and the children Rakitha, Muditha and Samantha took the other half equally per capita (one-sixth each), Samantha being an heir provided she is a legitimate child.", "application", ["AUTH-M001-002", "AUTH-M001-004", "AUTH-M001-008"], [ex("AUTH-M001-002", X["s22"], L["s22"]), ex("AUTH-M001-004", X["s24"], L["s24"]), ex("AUTH-M001-008", X["s33"], L["s33"])], "combined"),
    claim("CL-M001-Q01-009", "Rakitha died on 2 July 2022 (presumed intestate) leaving his wife Ann; if he left no children, Ann took one-half of his one-sixth and the other half passed, descendants failing, to his surviving parent Kanthi (one half) and to his full sister Muditha and half-sister Samantha (the other half). If Rakitha left children they take his whole non-spousal half by representation and the collateral branch does not arise.", "application", ["AUTH-M001-002", "AUTH-M001-005", "AUTH-M001-007", "AUTH-M001-004"], [ex("AUTH-M001-002", X["s22"], L["s22"]), ex("AUTH-M001-005", X["s25"], L["s25"]), ex("AUTH-M001-007", X["s27"], L["s27"]), ex("AUTH-M001-004", X["s24"], L["s24"])], "combined"),
    claim("CL-M001-Q01-010", "Muditha died on 5 June 2023 unmarried and issueless (presumed intestate); descendants and spouse failing, the surviving parent Kanthi took one half of Muditha's holding and the half-blood sister Samantha (related through the deceased parent Suresh) took the other half, Rakitha having predeceased without (known) issue. If Kanthi had predeceased, the whole would go to Samantha and any issue of Rakitha by representation.", "application", ["AUTH-M001-005", "AUTH-M001-006", "AUTH-M001-007"], [ex("AUTH-M001-005", X["s25"], L["s25"]), ex("AUTH-M001-006", X["s26"], L["s26"]), ex("AUTH-M001-007", X["s27"], L["s27"])], "combined"),
    claim("CL-M001-Q01-011", "Present owners at April 2026 (primary scenario: Kanthi alive; Rakitha left no children; Rakitha and Muditha died intestate; Samantha legitimate): Kanthi, Ann and Samantha. Pedigree: Gamini (final decree 111/P, 1985) -> Deed of Gift 515 (1986) -> Suresh (life interests of Gamini and Vinitha ended 1990 and 1991) -> intestacy 1995: Kanthi 1/2, Rakitha 1/6, Muditha 1/6, Samantha 1/6 -> Rakitha's intestacy 2022: Ann, Kanthi, Muditha, Samantha -> Muditha's intestacy 2023: Kanthi, Samantha.", "conclusion", [], [], "scenario_fact", FACTS + ": dates of death and family relationships; conclusion aggregates the applications above and is conditional on the listed unresolved facts."),
]

q2_claims = [
    claim("CL-M001-Q02-001", "On Suresh's death (1995) Kanthi took 1/2 of Lot A as surviving spouse.", "arithmetic", ["AUTH-M001-002"], [ex("AUTH-M001-002", X["s22"], L["s22"])], "arithmetic_from_rule"),
    claim("CL-M001-Q02-002", "The other 1/2 was divided per capita among the three children: Rakitha 1/6, Muditha 1/6, Samantha 1/6.", "arithmetic", ["AUTH-M001-004"], [ex("AUTH-M001-004", X["s24"], L["s24"])], "arithmetic_from_rule"),
    claim("CL-M001-Q02-003", "On Rakitha's death (2022), assuming intestacy and no children: Ann (spouse) took 1/2 of 1/6 = 1/12.", "arithmetic", ["AUTH-M001-002"], [ex("AUTH-M001-002", X["s22"], L["s22"])], "arithmetic_from_rule"),
    claim("CL-M001-Q02-004", "The remaining 1/12 of Rakitha's share passed, descendants failing and one parent surviving: Kanthi 1/2 of 1/12 = 1/24; the sibling half (1/24) between full sister Muditha and half-sister Samantha. On a literal reading of the half-blood division rule (full-blood sibling takes one half first and divides the other half with the half-blood), Muditha took 1/48 + 1/96 = 1/32 and Samantha 1/96. Alternative equal division would give 1/48 each; this point needs legal review.", "arithmetic", ["AUTH-M001-005", "AUTH-M001-007"], [ex("AUTH-M001-005", X["s25"], L["s25"]), ex("AUTH-M001-007", X["s27"], L["s27"])], "arithmetic_from_rule"),
    claim("CL-M001-Q02-005", "Muditha's holding at death (2023) was 1/6 + 1/32 = 19/96. No spouse or descendants: Kanthi (surviving parent) took 1/2 = 19/192; the other 19/192 went to the surviving sibling Samantha (half-blood, through Suresh), Rakitha having predeceased without known issue.", "arithmetic", ["AUTH-M001-005", "AUTH-M001-007"], [ex("AUTH-M001-005", X["s25"], L["s25"]), ex("AUTH-M001-007", X["s27"], L["s27"])], "arithmetic_from_rule"),
    claim("CL-M001-Q02-006", "Ann, as widow of the predeceased brother Rakitha, takes nothing from Muditha's estate: the Ordinance lets only the issue of a deceased sibling take by representation, and where it is silent Roman-Dutch law governs; no authority extending representation to a sibling's spouse was located.", "application", ["AUTH-M001-005", "AUTH-M001-009"], [ex("AUTH-M001-005", X["s25"], L["s25"]), ex("AUTH-M001-009", X["s36"], L["s36"])], "inferential"),
    claim("CL-M001-Q02-007", "Present shares (primary scenario; fractions of Lot A): Kanthi 1/2 + 1/24 + 19/192 = 123/192 (= 41/64); Ann 1/12 (= 16/192); Samantha 1/6 + 1/96 + 19/192 = 53/192. Total 192/192. Under the alternative equal-division reading of the sibling half: Kanthi 61/96, Ann 8/96, Samantha 27/96.", "arithmetic", ["AUTH-M001-002", "AUTH-M001-004", "AUTH-M001-005", "AUTH-M001-007"], [ex("AUTH-M001-002", X["s22"], L["s22"]), ex("AUTH-M001-004", X["s24"], L["s24"]), ex("AUTH-M001-005", X["s25"], L["s25"]), ex("AUTH-M001-007", X["s27"], L["s27"])], "arithmetic_from_rule"),
    claim("CL-M001-Q02-008", "If Rakitha left children, they take his non-spousal 1/12 by representation (Kanthi, Muditha and Samantha take nothing from him), and on Muditha's death they take Rakitha's place among the siblings by representation; the shares must then be recomputed. If Kanthi has died, her accumulated share passes on her own intestacy (outside the facts given).", "application", ["AUTH-M001-004", "AUTH-M001-005", "AUTH-M001-006"], [ex("AUTH-M001-004", X["s24"], L["s24"]), ex("AUTH-M001-005", X["s25"], L["s25"]), ex("AUTH-M001-006", X["s26"], L["s26"])], "combined"),
]

q3_claims = [
    claim("CL-M001-Q03-001", "The Act prohibits the transfer of title of any land in Sri Lanka to a foreigner.", "rule", ["AUTH-M001-011"], [ex("AUTH-M001-011", X["lra_s2_1"] + " " + X["lra_s2_1a"], L["l2_1"])], "direct"),
    claim("CL-M001-Q03-002", "'Foreigner' means a person who is not a citizen of Sri Lanka; 'transfer' means any sale, donation, gift or any conveyance by or under which title passes; 'land' includes any interest in land.", "rule", ["AUTH-M001-014"], [ex("AUTH-M001-014", X["def_foreigner"], L["def_f"]), ex("AUTH-M001-014", X["def_transfer"], L["def_t"]), ex("AUTH-M001-014", X["def_land"] + " " + X["def_land_a"], L["def_l"])], "direct"),
    claim("CL-M001-Q03-003", "Samantha, a citizen of the USA, is a 'foreigner' under the Act unless she is also a citizen of Sri Lanka (dual citizenship is not stated).", "application", [], [], "scenario_fact", FACTS + ": 'Samantha ... who is a citizen of USA'; definition applied in CL-M001-Q03-002."),
    claim("CL-M001-Q03-004", "Section 2 does not apply to any land the title of which is transferred by intestacy, gift or testamentary disposition to a next of kin (who is a foreigner) of the owner of such land, in accordance with the applicable law of succession of Sri Lanka.", "rule", ["AUTH-M001-012"], [ex("AUTH-M001-012", X["lra_s3_1d_tree"], L["l3_1d"]), ex("AUTH-M001-012", X["lra_s3_1d_pdf"], P["SRC021_PDF"] + " pdftotext pages 3-4")], "direct"),
    claim("CL-M001-Q03-005", "Section 2 also does not apply to land transferred to a dual citizen of Sri Lanka within the meaning of the Citizenship Act.", "rule", ["AUTH-M001-013"], [ex("AUTH-M001-013", X["lra_s3_1e"], L["l3_1e"])], "direct"),
    claim("CL-M001-Q03-006", "The Act is deemed to have come into operation on 1 January 2013; the Amendment Act No. 21 of 2018 is deemed operative from 1 April 2018 and amended only s.3(1)(b), (h) and (i) (condominium parcels and listed companies) and s.5A; it did not alter the intestacy exemption in s.3(1)(d), the dual-citizen exemption in s.3(1)(e) or the definition of 'foreigner'.", "rule", ["AUTH-M001-015", "AUTH-M001-019"], [ex("AUTH-M001-015", X["lra_s1_2"], L["l1_2"]), ex("AUTH-M001-019", X["am_s1"], L["am1"]), ex("AUTH-M001-019", X["am_s2"], L["am2"])], "combined"),
    claim("CL-M001-Q03-007", "Suresh died on 10 December 1995; Samantha's entitlement as a child arose then, before the Act existed, so the 1995 devolution is not caught by the prohibition on its own terms; the later accretions on Rakitha's (2022) and Muditha's (2023) intestacies occurred under the Act but are likewise devolutions 'by intestacy' to a next of kin within s.3(1)(d).", "application", ["AUTH-M001-015", "AUTH-M001-012"], [ex("AUTH-M001-015", X["lra_s1_2"], L["l1_2"]), ex("AUTH-M001-012", X["lra_s3_1d_tree"], L["l3_1d"])], "combined"),
    claim("CL-M001-Q03-008", "Whether Samantha is an heir at all is determined by the law of succession (a legitimate child takes per capita with the other children); the Act does not add a citizenship requirement to heirship.", "application", ["AUTH-M001-004", "AUTH-M001-008", "AUTH-M001-012"], [ex("AUTH-M001-004", X["s24"], L["s24"]), ex("AUTH-M001-008", X["s33"], L["s33"]), ex("AUTH-M001-012", X["lra_s3_1d_tree"], L["l3_1d"])], "combined"),
    claim("CL-M001-Q03-009", "Yes: Samantha can become entitled to (her share of) Suresh Perera's intestate estate. The prohibition in s.2(1)(a) on transfers to foreigners does not defeat her because (i) the devolution by intestacy to a next of kin who is a foreigner is expressly exempted by s.3(1)(d), which the 2018 amendment left untouched; (ii) alternatively she is exempt under s.3(1)(e) if she is a dual citizen; and (iii) the 1995 devolution predates the Act's deemed operation. Any later transfer by her of that land remains subject to the Act (s.3(4)), and an alienation in contravention would be void (s.18).", "conclusion", ["AUTH-M001-011", "AUTH-M001-012", "AUTH-M001-013", "AUTH-M001-015", "AUTH-M001-019", "AUTH-M001-017", "AUTH-M001-016"], [ex("AUTH-M001-012", X["lra_s3_1d_tree"], L["l3_1d"]), ex("AUTH-M001-017", X["lra_s3_4"], L["l3_4"]), ex("AUTH-M001-016", X["lra_s18"], L["l18"])], "combined"),
]

legal_map = {
    "benchmark_matter_id": "M001", "run_id": RUN, "produced_by_agent": AG, "status": "needs_legal_review",
    "questions": [
        {"benchmark_question_id": "M001-Q01",
         "issues": ["Root of title: conclusiveness of the 1985 partition final decree", "Gift of dominium subject to two reserved life interests; irrevocability of an accepted donation", "Effect of the death of one life-interest holder (1990)", "Effect of the holder's revocation/renunciation of the remaining life interest (1991) -- authority not located", "Intestate devolution on Suresh's death (1995): spouse and three children", "Intestate devolution on Rakitha's death (2022)", "Intestate devolution on Muditha's death (2023)", "Applicability of the general law"],
         "indispensable_authority_ids": ["AUTH-M001-002", "AUTH-M001-004", "AUTH-M001-005", "AUTH-M001-026"],
         "supporting_authority_ids": ["AUTH-M001-001", "AUTH-M001-003", "AUTH-M001-006", "AUTH-M001-007", "AUTH-M001-008", "AUTH-M001-009", "AUTH-M001-010", "AUTH-M001-020", "AUTH-M001-021", "AUTH-M001-022", "AUTH-M001-023", "AUTH-M001-024", "AUTH-M001-025"],
         "legal_hop_count": 6,
         "hop_count_basis": "Counted indispensable legal steps: (1) final decree as root of title; (2) gift passes dominium subject to life interests; (3) death of Gamini ends his life interest; (4) Vinitha's revocation frees the remainder (authority missing); (5) Suresh's intestacy: spouse half + children per capita; (6) Rakitha's and Muditha's intestacies via ss.22/25/27 (counted as one composite step). Identification of the parties and dates is factual, not counted.",
         "reasoning_chain": [
             {"step": 1, "text": "Gamini is root owner of Lot A under the 1985 final decree, which is conclusive evidence of title.", "authority_ids": ["AUTH-M001-020"], "relies_on_scenario_fact_ids": ["final decree 111/P 1985-02-02"]},
             {"step": 2, "text": "Deed of Gift 515 (1986, notarially attested) passed dominium to Suresh, subject to the life interests of Gamini and Vinitha; an accepted donation is irrevocable.", "authority_ids": ["AUTH-M001-021", "AUTH-M001-023", "AUTH-M001-024"], "relies_on_scenario_fact_ids": ["deed of gift 515 1986-03-10"]},
             {"step": 3, "text": "Gamini's death (1990) ended his life interest; on Fernando v. Fernando the survivor's life interest did not extend to his half.", "authority_ids": ["AUTH-M001-022", "AUTH-M001-025"], "relies_on_scenario_fact_ids": ["death of Gamini 1990-06-12"]},
             {"step": 4, "text": "Vinitha's Deed of revocation 525 (1991) extinguished her life interest; Suresh held Lot A unencumbered. Renunciation principle not located in corpus (blocking).", "authority_ids": ["AUTH-M001-026", "AUTH-M001-021", "AUTH-M001-009"], "relies_on_scenario_fact_ids": ["deed of revocation 525 1991-02-25"]},
             {"step": 5, "text": "Suresh's intestacy (1995): Kanthi 1/2; Rakitha, Muditha, Samantha 1/6 each (Samantha if legitimate; general law assumed).", "authority_ids": ["AUTH-M001-001", "AUTH-M001-002", "AUTH-M001-004", "AUTH-M001-008", "AUTH-M001-010"], "relies_on_scenario_fact_ids": ["death of Suresh intestate 1995-12-10", "family relationships"]},
             {"step": 6, "text": "Rakitha's intestacy (2022): Ann 1/2 of his share; other half to Kanthi and siblings (or to his issue if any). Muditha's intestacy (2023): Kanthi and Samantha.", "authority_ids": ["AUTH-M001-002", "AUTH-M001-005", "AUTH-M001-006", "AUTH-M001-007"], "relies_on_scenario_fact_ids": ["death of Rakitha 2022-07-02", "death of Muditha 2023-06-05 unmarried and issueless"]},
             {"step": 7, "text": "Present owners at April 2026 (primary scenario): Kanthi, Ann, Samantha.", "authority_ids": [], "relies_on_scenario_fact_ids": ["all of the above; conditional on unresolved facts"]},
         ],
         "gold_answer_draft": {
             "issue": "Trace the devolution of title to Lot A, No 20 Flower Road, Homagama, from Gamini Perera to the present owners.",
             "rule": "A partition final decree is conclusive evidence of the allottee's title. A notarially executed gift of land passes the dominium to the donee, and an accepted gift is irrevocable, even where the donor reserves life interests; the donee's full enjoyment opens as each life interest ends by death (Fernando v. Fernando: the death of one of two donor life-tenants frees that donor's half absolutely in the donee) or by the holder's renunciation (Roman-Dutch law principle; no corpus authority located). On intestacy the surviving spouse takes one-half and the children the other half per capita, the issue of a deceased child taking by representation; where a person dies without spouse or descendants leaving one parent, that parent takes half and the brothers and sisters of the full and half blood (the half-blood through the deceased parent) take the other half.",
             "application": "Gamini (final decree 111/P, 1985) gifted Lot A to Suresh by Deed 515 (1986) subject to his and Vinitha's life interests. Gamini's death (1990) and Vinitha's revocation (1991) freed Suresh's title. Suresh died intestate (1995): Kanthi 1/2; Rakitha, Muditha and Samantha 1/6 each. Rakitha died (2022) leaving Ann: Ann 1/12; the other 1/12 to Kanthi (1/24) and to Muditha and Samantha. Muditha died (2023) unmarried and issueless: her holding to Kanthi (half) and Samantha (half).",
             "conclusion": "Pedigree: Gamini Perera -> (Deed of Gift 515, 1986; life interests ended 1990/1991) Suresh Perera -> (intestacy 1995) Kanthi, Rakitha, Muditha, Samantha -> (Rakitha's intestacy 2022) Ann, Kanthi, Muditha, Samantha -> (Muditha's intestacy 2023) Kanthi, Samantha. Present owners (April 2026): Kanthi, Ann and Samantha, subject to: whether Rakitha left children; whether Rakitha and Muditha died intestate; whether Kanthi is alive; whether Suresh's first marriage was dissolved and Samantha is legitimate; acceptance of the 1986 gift; and the general law applying.",
         },
         "answer_claims": q1_claims, "confidence": 0.55, "status": "blocked_missing_authority",
         "blocking_reason": "No repository source states the Roman-Dutch law rule that a life-interest (usufruct) holder's renunciation/revocation extinguishes the interest and vests unencumbered ownership in the dominus (step 4, CL-M001-Q01-006). Placeholder AUTH-M001-026 has no located source. Also: the Partition Law text in force at the 1985 decree (s.48 pre-1997 version) is not held; only the current text is."},
        {"benchmark_question_id": "M001-Q02",
         "issues": ["Spouse's half on Suresh's intestacy", "Per capita division among three children incl. child of first marriage", "Devolution of Rakitha's share: spouse half; descendants failing -> parent and siblings", "Division between full-blood and half-blood siblings", "Devolution of Muditha's share: parent and half-blood sister", "Whether a predeceased sibling's widow (Ann) takes by representation", "Aggregation of fractions"],
         "indispensable_authority_ids": ["AUTH-M001-002", "AUTH-M001-004", "AUTH-M001-005", "AUTH-M001-007"],
         "supporting_authority_ids": ["AUTH-M001-001", "AUTH-M001-003", "AUTH-M001-006", "AUTH-M001-008", "AUTH-M001-009", "AUTH-M001-010"],
         "legal_hop_count": 4,
         "hop_count_basis": "Counted: (1) spouse half (s.22) applied twice; (2) children per capita (s.24); (3) descendants failing -> parent half + siblings half (s.25); (4) full/half-blood division (s.27). Arithmetic aggregation not counted as a legal hop.",
         "reasoning_chain": [
             {"step": 1, "text": "1995: Kanthi 1/2; Rakitha 1/6; Muditha 1/6; Samantha 1/6.", "authority_ids": ["AUTH-M001-002", "AUTH-M001-004"], "relies_on_scenario_fact_ids": ["Suresh died intestate 1995-12-10 leaving Kanthi and three children"]},
             {"step": 2, "text": "2022 (Rakitha, no issue assumed): Ann 1/12; Kanthi 1/24; sibling half 1/24 split Muditha 1/32, Samantha 1/96 on the literal s.27 reading (or 1/48 each).", "authority_ids": ["AUTH-M001-002", "AUTH-M001-005", "AUTH-M001-007"], "relies_on_scenario_fact_ids": ["Rakitha married Ann; died 2022-07-02"]},
             {"step": 3, "text": "2023 (Muditha, unmarried, issueless): holding 19/96 -> Kanthi 19/192, Samantha 19/192; Ann takes nothing.", "authority_ids": ["AUTH-M001-005", "AUTH-M001-007", "AUTH-M001-009"], "relies_on_scenario_fact_ids": ["Muditha died 2023-06-05 unmarried and issueless"]},
             {"step": 4, "text": "Totals: Kanthi 123/192 (41/64); Ann 16/192 (1/12); Samantha 53/192.", "authority_ids": ["AUTH-M001-002", "AUTH-M001-004", "AUTH-M001-005", "AUTH-M001-007"], "relies_on_scenario_fact_ids": ["primary scenario assumptions"]},
         ],
         "gold_answer_draft": {
             "issue": "What fractional share of Lot A does each heir presently own?",
             "rule": "Surviving spouse inherits one-half (s.22); children take the balance equally per capita, issue of a deceased child by representation (s.24); descendants failing, a sole surviving parent takes half and full- and half-blood siblings (half-blood through the deceased parent) and issue of deceased siblings by representation take the other half (s.25); division between full and half blood per s.27; where the Ordinance is silent Roman-Dutch law governs (s.36).",
             "application": "Suresh (1995): Kanthi 1/2, Rakitha 1/6, Muditha 1/6, Samantha 1/6. Rakitha (2022, assumed intestate, no children): Ann 1/12; Kanthi 1/24; Muditha 1/32 and Samantha 1/96 (literal s.27) or 1/48 each. Muditha (2023): 19/96 -> Kanthi 19/192, Samantha 19/192.",
             "conclusion": "Primary scenario: Kanthi 123/192 (= 41/64), Ann 1/12 (= 16/192), Samantha 53/192 (sum 1). Alternative equal-division reading: Kanthi 61/96, Ann 8/96, Samantha 27/96. Both are conditional on Rakitha having left no children, Rakitha and Muditha having died intestate, Kanthi being alive, and Samantha being a legitimate child; if Rakitha left children the shares must be recomputed with them taking by representation.",
         },
         "answer_claims": q2_claims, "confidence": 0.5, "status": "needs_legal_review",
         "blocking_reason": None},
        {"benchmark_question_id": "M001-Q03",
         "issues": ["Prohibition on transfer of land to a foreigner (s.2(1)(a))", "Meaning of 'foreigner', 'transfer', 'land' (s.25)", "Exemption for devolution by intestacy, gift or will to a foreigner next of kin (s.3(1)(d))", "Dual-citizen exemption (s.3(1)(e))", "Temporal scope: deemed operation 1 January 2013 vs death in 1995; 2022/2023 accretions", "Effect of the 2018 amendment", "Consequences: subsequent transfers (s.3(4)); void alienations (s.18)"],
         "indispensable_authority_ids": ["AUTH-M001-011", "AUTH-M001-012", "AUTH-M001-014", "AUTH-M001-015", "AUTH-M001-019"],
         "supporting_authority_ids": ["AUTH-M001-013", "AUTH-M001-016", "AUTH-M001-017", "AUTH-M001-018", "AUTH-M001-004", "AUTH-M001-008"],
         "legal_hop_count": 4,
         "hop_count_basis": "Counted: (1) prohibition + definition of foreigner applied to a US citizen; (2) exemption for intestacy to foreign next of kin; (3) temporal point (1995 death predates deemed operation; later accretions within the Act); (4) the 2018 amendment did not alter the exemption. Dual-citizen alternative and consequences are supporting.",
         "reasoning_chain": [
             {"step": 1, "text": "Samantha, a US citizen, is a 'foreigner' (unless also a Sri Lankan citizen); transfers of land to foreigners are prohibited by s.2(1)(a).", "authority_ids": ["AUTH-M001-011", "AUTH-M001-014"], "relies_on_scenario_fact_ids": ["Samantha is a citizen of USA"]},
             {"step": 2, "text": "Section 3(1)(d) exempts land whose title is transferred by intestacy, gift or testamentary disposition to a next of kin who is a foreigner, in accordance with Sri Lankan succession law.", "authority_ids": ["AUTH-M001-012"], "relies_on_scenario_fact_ids": []},
             {"step": 3, "text": "Suresh died in 1995, before the Act's deemed operation (1 January 2013); the 2022 and 2023 accretions fall within the Act but are also intestate devolutions within s.3(1)(d).", "authority_ids": ["AUTH-M001-015", "AUTH-M001-012"], "relies_on_scenario_fact_ids": ["Suresh died 1995-12-10", "Rakitha died 2022-07-02", "Muditha died 2023-06-05"]},
             {"step": 4, "text": "Act 21 of 2018 (operative 1 April 2018) amended s.3(1)(b), (h), (i) and s.5A only; s.3(1)(d), (e) and the definition of foreigner are unchanged.", "authority_ids": ["AUTH-M001-019"], "relies_on_scenario_fact_ids": []},
             {"step": 5, "text": "If Samantha is a dual citizen, s.3(1)(e) independently exempts her. Any later transfer by her remains subject to the Act (s.3(4)); a contravening alienation is void (s.18).", "authority_ids": ["AUTH-M001-013", "AUTH-M001-017", "AUTH-M001-016"], "relies_on_scenario_fact_ids": ["dual citizenship not stated"]},
         ],
         "gold_answer_draft": {
             "issue": "Can Samantha, a US citizen, become entitled to Suresh Perera's intestate estate having regard to the Land (Restrictions on Alienation) Act No. 38 of 2014 as amended by Act No. 21 of 2018?",
             "rule": "Section 2(1)(a) prohibits the transfer of title of land in Sri Lanka to a foreigner, i.e. a person who is not a citizen of Sri Lanka (s.25). Section 3(1)(d) excludes from s.2 any land the title of which is transferred by intestacy, gift or testamentary disposition to a next of kin (who is a foreigner) of the owner, in accordance with the applicable law of succession of Sri Lanka; s.3(1)(e) excludes transfers to dual citizens. The Act is deemed operative from 1 January 2013 (s.1(2)); the 2018 amendment (operative 1 April 2018) altered only s.3(1)(b), (h), (i) and s.5A.",
             "application": "Samantha is a foreigner (absent dual citizenship). Her entitlement arises by intestacy as Suresh's child (per capita with the other children, if legitimate). That devolution falls squarely within s.3(1)(d); it also occurred in 1995, before the Act's deemed operation. Her further accretions on Rakitha's and Muditha's intestacies (2022, 2023) are equally devolutions by intestacy to a next of kin and are exempt. The 2018 amendment did not narrow the exemption.",
             "conclusion": "Yes. Samantha can become entitled to her share of Suresh Perera's intestate estate; the Act's prohibition does not apply to land passing by intestacy to a foreigner next of kin (s.3(1)(d)), and alternatively she is exempt if a dual citizen (s.3(1)(e)). Any later voluntary transfer of that land by her would be subject to the Act (s.3(4)) and a contravening alienation would be void (s.18). Conditional on Samantha being a legitimate child (heirship) and on the current consolidated text matching the text in force at each event date.",
         },
         "answer_claims": q3_claims, "confidence": 0.7, "status": "needs_legal_review",
         "blocking_reason": None},
    ],
}

json.dump(cand, open(OUT + "candidate-authorities.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
json.dump(legal_map, open(OUT + "legal-map.draft.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("wrote candidate-authorities.json and legal-map.draft.json")
