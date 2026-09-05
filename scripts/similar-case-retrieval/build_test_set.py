"""Build the 20-query similar-case-retrieval test set from src/questions.md.

`src/questions.md` holds 18 top-level exam questions (73 numbered sub-parts)
across two Sri Lanka Law College Conveyancing past papers (April 2026,
October 2025). None of them are written as case-law queries -- they are
exam fact patterns. This script selects 20 sub-parts by hand (not "the
first 20") that are fact-driven and case-law-answerable, and writes each as
a query: the question's fact-pattern preamble + the specific sub-question
text, so `find_similar()` sees the same kind of input a lawyer would submit
for a real matter.

Selection deliberately skips sub-parts that are pure arithmetic (stamp duty
calculations) or pure statutory-note recitation with no scenario to match
against precedent -- those have no similar-case answer to check. Coverage
favors the topics already dense in the conveyancing corpus (partition,
prescription, notarial liability, deeds/gifts, succession).

Usage:
    python scripts/similar-case-retrieval/build_test_set.py
"""

from __future__ import annotations

import json
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent
QUESTIONS_MD = Path(__file__).resolve().parents[2] / "src" / "questions.md"

# Each entry: exam paper, question number, sub-part number, the fact-pattern
# preamble (verbatim from questions.md), the specific sub-question text
# (verbatim), and a one-line reason this sub-part was picked.
SELECTED_QUERIES: list[dict[str, str]] = [
    {
        "paper": "April 2026",
        "question": "Q1",
        "part": "1",
        "preamble": (
            "Gamini Perera was allotted Lot A depicted in Partition Plan No. 2525 dated "
            "2 February 1981 by a final decree of a partition case entered in the "
            "District Court of Homagama. Gamini Perera, by Deed of Gift No. 515 dated "
            "10 March 1986, gifted Lot A absolutely and irrevocably to his son, Suresh "
            "Perera, subject to the life interest of Gamini Perera and his wife Vinitha. "
            "Gamini Perera died in 1990. Vinitha revoked her life interest by Deed of "
            "Revocation in 1991. Suresh Perera married Kanthi and had two children, "
            "Rakitha and Muditha. Muditha died in 2023 unmarried and issueless. Rakitha "
            "married Ann and died in 2022. Suresh Perera died in 1995 intestate, and had "
            "an offspring named Samantha from his first marriage."
        ),
        "sub_question": (
            "Draw up the pedigree showing the devolution of title from Gamini Perera up "
            "to the present owners in relation to the land."
        ),
        "reason": "partition decree + gift with life interest + intestate succession chain",
    },
    {
        "paper": "April 2026",
        "question": "Q1",
        "part": "3",
        "preamble": (
            "Suresh Perera died on 10 December 1995 intestate. Suresh Perera had an "
            "offspring named Samantha from his first marriage, who is a citizen of the "
            "United States of America."
        ),
        "sub_question": (
            "Can Samantha become entitled to the intestate estate of Suresh Perera? "
            "Discuss with reference to the provisions of the Land (Restrictions on "
            "Alienation) Act No. 38 of 2014, as amended."
        ),
        "reason": "foreign-citizen heir vs. land alienation restrictions",
    },
    {
        "paper": "April 2026",
        "question": "Q3",
        "part": "2",
        "preamble": (
            "Herath intends to mortgage his land situated in Anuradhapura, which is held "
            "under the Land Development Ordinance and is subject to the Land Development "
            "(Amendment) Act No. 11 of 2022, to a commercial bank for Rs. 10,000,000."
        ),
        "sub_question": "Does Herath require approval from the Divisional Secretary to mortgage the land?",
        "reason": "LDO land mortgage approval requirement",
    },
    {
        "paper": "April 2026",
        "question": "Q3",
        "part": "3",
        "preamble": (
            "Herath intends to mortgage his land, which is held under the Land "
            "Development Ordinance and is subject to the Land Development (Amendment) "
            "Act No. 11 of 2022."
        ),
        "sub_question": "What are the instances in which the President of Sri Lanka could cancel a grant?",
        "reason": "LDO grant cancellation grounds",
    },
    {
        "paper": "April 2026",
        "question": "Q3",
        "part": "4",
        "preamble": (
            "Herath passed away after the mortgage was settled and released in 2023. He "
            "failed to appoint a successor to the land."
        ),
        "sub_question": (
            "Who are the groups of relatives entitled to the land under the Third "
            "Schedule of the amended Land Development Ordinance?"
        ),
        "reason": "LDO intestate succession without an appointed successor",
    },
    {
        "paper": "April 2026",
        "question": "Q5",
        "part": "1",
        "preamble": (
            "Somar, a Notary holding a licence to practise in the Judicial Zone of "
            "Colombo, is employed by a legal/real-estate company. Somar's employer "
            "instructs him to execute a Deed of Transfer of an urgent land transaction."
        ),
        "sub_question": (
            "Can Somar execute the deed without checking the title at the Land Registry? "
            "Explain with reference to the Notaries Ordinance."
        ),
        "reason": "notary duty to verify title before attestation -- matches recurring 'careless attestation' catchwords",
    },
    {
        "paper": "April 2026",
        "question": "Q5",
        "part": "4",
        "preamble": "Somar's relative/wife is in Kurunegala and intends to sell a property.",
        "sub_question": (
            "Explain the procedure to be followed under the Notaries Ordinance where a "
            "Notary has an interest in the transaction."
        ),
        "reason": "notary conflict-of-interest procedure",
    },
    {
        "paper": "April 2026",
        "question": "Q6",
        "part": "3",
        "preamble": (
            "A deed affecting land is executed, but the instrument is not presented for "
            "registration within the prescribed period."
        ),
        "sub_question": "Is registration mandatory, and what is the legal consequence of non-registration?",
        "reason": "consequence of failing to register an instrument in time",
    },
    {
        "paper": "April 2026",
        "question": "Q9",
        "part": "1",
        "preamble": (
            "Martin Perera wants to dispose of his house after his death to Siripala, "
            "who is his helper, by a Last Will, and appoints his driver Nihal as the "
            "executor of the Last Will. He does not dispose of anything to his children "
            "by the Will."
        ),
        "sub_question": "Can Martin Perera execute the Will without assigning any reason?",
        "reason": "will validity when disinheriting children",
    },
    {
        "paper": "October 2025",
        "question": "Q1",
        "part": "1",
        "preamble": (
            "By a Final Decree dated 5 May 2018, Ajith Silva was allotted Lot 2 of a "
            "partitioned property in Nugegoda. Ajith Silva, by Deed of Gift No. 515 "
            "dated 10 December 2018, gifted Lot 2 to Prabash Silva, his elder son, "
            "subject to the life interest of the donor, and subject to a condition that "
            "Prabash shall not sell, mortgage or otherwise deal with the land during his "
            "lifetime; on Prabash's death the property devolves free of conditions to "
            "Subash. Ajith had three children by his second marriage and another "
            "daughter, Kushani, from his first marriage. Ajith Silva died intestate in "
            "2019, and Prabash Silva died intestate later that year. Prabash had "
            "children by two marriages, some of whom later died intestate or issueless."
        ),
        "sub_question": (
            "Draw up the pedigree showing the devolution of title from Ajith Silva up to "
            "the present owners."
        ),
        "reason": "partition decree + conditional gift + successive intestate deaths",
    },
    {
        "paper": "October 2025",
        "question": "Q2",
        "part": "2",
        "preamble": "A donor makes an irrevocable gift of land to a donee.",
        "sub_question": (
            "Can an irrevocable gift be revoked? If so, under which law is this "
            "provided, and what procedure should be followed?"
        ),
        "reason": "revocability of an irrevocable donation -- a recurring donation catchword in the corpus",
    },
    {
        "paper": "October 2025",
        "question": "Q3",
        "part": "1",
        "preamble": "Wimala intends to purchase land in Galle but is unable to come to Sri Lanka to sign the Deed of Transfer.",
        "sub_question": (
            "Advise Wimala according to the latest amendments relating to the "
            "Prevention of Frauds Ordinance No. 7 of 1840."
        ),
        "reason": "executing a deed while the party is abroad",
    },
    {
        "paper": "October 2025",
        "question": "Q3",
        "part": "2",
        "preamble": (
            "Sarath wishes to purchase a portion of a coconut estate situated in "
            "Kurunegala and requests a Notary licensed to practise in Colombo to attest "
            "the deed."
        ),
        "sub_question": "What steps should the Notary take before drafting the deed?",
        "reason": "pre-attestation due-diligence steps, notary practising outside their own district",
    },
    {
        "paper": "October 2025",
        "question": "Q4",
        "part": "2",
        "preamble": (
            "Romani, who intends to go to New Zealand, wants to file a caveat in respect "
            "of her property situated in Battaramulla."
        ),
        "sub_question": (
            "Can Romani file a caveat in respect of her property? Who can file a caveat "
            "under the Registration of Documents Ordinance, as amended?"
        ),
        "reason": "capacity to lodge a caveat before travelling abroad",
    },
    {
        "paper": "October 2025",
        "question": "Q5",
        "part": "3",
        "preamble": (
            "Mala intends to visit her son in Australia. Mala gave a Special Power of "
            "Attorney to her daughter Visaka in 2017 to sell her house in Colombo. Mala "
            "also intends to lease the house to Sheela."
        ),
        "sub_question": (
            "Can Visaka execute the lease agreement with Sheela on behalf of Mala if "
            "Mala travels to Australia? Advise Mala on how to execute the lease "
            "agreement in her absence."
        ),
        "reason": "power of attorney authority scope (sale vs. lease)",
    },
    {
        "paper": "October 2025",
        "question": "Q6",
        "part": "4",
        "preamble": (
            "Nimal is the caretaker of a land parcel in Homagama. The property belongs "
            "to Kamal, who is working in Australia and visits Sri Lanka annually. Nimal "
            "has prepared a Deed of Declaration and intends to claim prescriptive rights "
            "over Kamal's property."
        ),
        "sub_question": (
            "Discuss whether Nimal can claim prescriptive rights, stating the relevant "
            "provisions of the Registration of Title Act."
        ),
        "reason": "caretaker/possessor claiming prescription against an absentee owner -- prescription is one of the corpus's densest topics",
    },
    {
        "paper": "October 2025",
        "question": "Q7",
        "part": "1",
        "preamble": (
            "There are four parties to a Deed of Partition relating to a property in "
            "Tangalle, to be executed before a Notary licensed to practise in Colombo. "
            "One party resides in Tangalle and is unable to come to Colombo; the other "
            "three reside in Colombo."
        ),
        "sub_question": "Discuss how all parties may sign the Deed of Partition.",
        "reason": "execution logistics for a multi-party partition deed",
    },
    {
        "paper": "October 2025",
        "question": "Q9",
        "part": "3",
        "preamble": "A minor owns property that needs to be sold on the minor's behalf.",
        "sub_question": (
            "Could the father of a minor child sell property on behalf of the minor? "
            "What is the procedure for selling a minor's property? What would happen to "
            "the consideration paid?"
        ),
        "reason": "guardian's authority to sell a minor's property",
    },
    {
        "paper": "October 2025",
        "question": "Q9",
        "part": "4",
        "preamble": "A minor wishes to purchase land.",
        "sub_question": "Can a minor purchase land? Who may sign the Deed of Transfer on behalf of the minor when purchasing property for the minor?",
        "reason": "capacity of a minor to take title by transfer",
    },
    {
        "paper": "October 2025",
        "question": "Q9",
        "part": "5",
        "preamble": (
            "The children of a testator inquire from the Notary who attested the Last "
            "Will whether their father has executed a Will. The testator is alive."
        ),
        "sub_question": "Should the Notary divulge the information? Discuss.",
        "reason": "notary's duty of confidentiality over an unrevealed will",
    },
]


def main() -> None:
    if not QUESTIONS_MD.exists():
        raise FileNotFoundError(QUESTIONS_MD)
    if len(SELECTED_QUERIES) != 20:
        raise RuntimeError(f"Expected exactly 20 selected queries, found {len(SELECTED_QUERIES)}.")

    records = []
    for index, item in enumerate(SELECTED_QUERIES, start=1):
        query_text = f"{item['preamble']} {item['sub_question']}"
        records.append(
            {
                "query_id": f"scr-{index:02d}",
                "source_paper": item["paper"],
                "source_question": item["question"],
                "source_part": item["part"],
                "selection_reason": item["reason"],
                "query_text": query_text,
            }
        )

    out_path = OUT_DIR / "test_queries.jsonl"
    with out_path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} test queries to {out_path}")


if __name__ == "__main__":
    main()
