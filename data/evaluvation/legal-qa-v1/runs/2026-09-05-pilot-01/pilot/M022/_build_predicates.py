"""Generate predicates.json for benchmark matter M022.

Every predicate is derived from the verified law in verified-authorities.json
(verified / partially_verified only) and the scenario in source.json. No
authority is added; the gold answer is not changed. Re-running this script
produces byte-identical output.

    uv run python data/evaluvation/legal-qa-v1/runs/2026-09-05-pilot-01/pilot/M022/_build_predicates.py
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
MATTER = "M022"
RUN_ID = "2026-09-05-pilot-01"
Q1 = "M022-Q01"
Q2 = "M022-Q02"

TEMPORAL = (
    "Temporal warning: the Notaries Ordinance s.31 rule text relied on is the 1980 "
    "revised-edition consolidation (applicable_version_for_matter_date = history_unknown); "
    "the October 2020 wording is unconfirmed from repo files, with low residual risk per the "
    "verifier (no 2005-2020 instrument held in the repo touches this rule)."
)

_rows: list[dict] = []


def add(
    predicate: str,
    description: str,
    *,
    qs: list[str],
    expected: bool | None,
    ptype: str,
    necessity: str,
    polarity: str = "positive",
    auth: list[str],
    status: str,
    counterfactual: str,
    decisive: bool,
    notes: str | None = None,
) -> None:
    _rows.append(
        {
            "predicate_id": f"PR-{MATTER}-{len(_rows) + 1:03d}",
            "benchmark_question_ids": qs,
            "predicate": predicate,
            "description": description,
            "expected_value": expected,
            "predicate_type": ptype,
            "necessity": necessity,
            "polarity": polarity,
            "authority_ids": auth,
            "supporting_fact_ids": [],
            "evidence_document_ids": [],
            "status": status,
            "counterfactual_effect": counterfactual,
            "potentially_decisive": decisive,
            "notes": notes,
        }
    )


# ---------------------------------------------------------------------------
# Q01 - formal requirement and scenario facts
# ---------------------------------------------------------------------------

add(
    "instrument_is_lease_of_immovable_property",
    "The instrument to be executed is a Lease Agreement over a warehouse situated in Galle, "
    "i.e. an agreement establishing an interest affecting land or other immovable property "
    "within Prevention of Frauds Ordinance s.2.",
    qs=[Q1],
    expected=True,
    ptype="fact",
    necessity="indispensable",
    auth=["AUTH-M022-017"],
    status="observed",
    counterfactual=(
        "If the subject matter were movable property or a mere licence, s.2 would not require "
        "notarial execution and the whole two-notary execution procedure would be optional rather "
        "than required; the gold answer would change."
    ),
    decisive=True,
    notes=(
        "Source: 'lease out a warehouse situated in Galle'. PoF s.2 excerpt is the pre-2022 tree "
        "text (current_text_superseded_since_event); both versions keep the notary-plus-two-witnesses "
        "requirement and the lease-at-will / one-month exception."
    ),
)

add(
    "lease_term_exceeds_one_month_and_is_not_at_will",
    "The lease is neither a lease at will nor a lease for a period not exceeding one month, so it "
    "falls outside the bracketed exception in Prevention of Frauds Ordinance s.2.",
    qs=[Q1],
    expected=True,
    ptype="fact",
    necessity="indispensable",
    auth=["AUTH-M022-017"],
    status="synthetic_needed",
    counterfactual=(
        "If the term were one month or less (or at will), s.2 would not require notarial execution; "
        "the answer's rule step ('must be in writing signed before a licensed notary') would no longer "
        "apply as a legal requirement, although the parties could still choose notarial execution."
    ),
    decisive=True,
    notes=(
        "Scenario does not state the term. A synthetic Lease Agreement fixing any term above one month "
        "(e.g. a multi-year commercial warehouse lease) is neutral: the gold answer already assumes a "
        "lease requiring notarial execution (CL-M022-Q01-011), so fixing the value does not change the "
        "answer. Flagged decisive because the opposite value would alter the rule step."
    ),
)

add(
    "lease_must_be_notarially_executed_before_two_witnesses",
    "As a lease of immovable property outside the s.2 exception, the Lease Agreement must be in "
    "writing, signed by the party (or a person lawfully authorised) in the presence of a licensed "
    "notary public and two or more witnesses present at the same time, and duly attested by them.",
    qs=[Q1],
    expected=True,
    ptype="legal_status",
    necessity="indispensable",
    auth=["AUTH-M022-017"],
    status="inferred",
    counterfactual=(
        "If notarial execution were not required, the question of how two notaries in different "
        "towns can execute one deed would not arise as a legal necessity."
    ),
    decisive=True,
    notes="Follows from PR-M022-001 and PR-M022-002; the question itself presupposes attestation.",
)

add(
    "both_anil_fernando_and_ruwan_perera_are_licensed_notaries",
    "Anil Fernando (Colombo) and Ruwan Perera (Galle) are each licensed notaries public able to "
    "attest a deed under PoF s.2.",
    qs=[Q1, Q2],
    expected=True,
    ptype="fact",
    necessity="supporting",
    auth=["AUTH-M022-017"],
    status="observed",
    counterfactual=(
        "If either were not a licensed notary, he could not attest his party's signature and the "
        "two-notary procedure with those two persons would fail."
    ),
    decisive=True,
    notes="Source: 'Anil Fernando is a Notary practising in Colombo'; 'his Notary Ruwan Perera who is practising in Galle'.",
)

add(
    "russel_perera_refuses_to_travel_to_colombo",
    "The warehouse owner Russel Perera will not come to Colombo and wants his own notary in Galle "
    "to draft and attest the Lease Agreement.",
    qs=[Q1],
    expected=True,
    ptype="fact",
    necessity="supporting",
    auth=[],
    status="observed",
    counterfactual=(
        "If Russel Perera were willing to come to Colombo, all executants could sign before Anil "
        "Fernando at one sitting (subject to r.9 identification) and no second notary would be needed."
    ),
    decisive=True,
    notes="Source: 'Russel Perera does not want to come to Colombo.' This is the factual driver of PR-M022-006.",
)

add(
    "parties_do_not_sign_at_same_time_and_place",
    "The executants (Russel Perera in Galle; the company's directors in Colombo) will not sign the "
    "deed at the same time and place, bringing the deed within Notaries Ordinance s.32(2).",
    qs=[Q1, Q2],
    expected=True,
    ptype="fact",
    necessity="indispensable",
    auth=["AUTH-M022-004"],
    status="observed",
    counterfactual=(
        "If all parties signed at one time and place, s.32(2) would not apply, a single notary "
        "would attest, and the allocation of first/second notary duties would disappear."
    ),
    decisive=True,
    notes="s.32(2) is recorded as current_text_applicable (not touched by any amending instrument in the repo).",
)

add(
    "notaries_authorised_for_different_areas",
    "Anil Fernando practises in Colombo and Ruwan Perera in Galle; the two notaries are authorised "
    "to practise in different areas.",
    qs=[Q1],
    expected=True,
    ptype="fact",
    necessity="indispensable",
    auth=["AUTH-M022-008"],
    status="observed",
    counterfactual=(
        "If both notaries were authorised for the same area, rule (22) would not force the Galle and "
        "Colombo signings to be attested by different notaries; the two-notary route would rest on "
        "the parties' wishes alone."
    ),
    decisive=True,
    notes=(
        "The scenario gives only the towns ('practising in Colombo' / 'practising in Galle'); the "
        "precise authorised area/zone on each notary's warrant is not stated. " + TEMPORAL
    ),
)

add(
    "each_notary_attests_only_within_own_authorised_area",
    "Each notary attests only the signatures taken within the area in which he is authorised to "
    "practise: Ruwan Perera attests Russel Perera's signature in Galle and Anil Fernando attests "
    "the directors' signatures in Colombo.",
    qs=[Q1],
    expected=True,
    ptype="procedural_condition",
    necessity="indispensable",
    auth=["AUTH-M022-008"],
    status="inferred",
    counterfactual=(
        "If Anil Fernando attested a signing in Galle (or Ruwan Perera one in Colombo) he would breach "
        "rule (22); the gold procedure assigns each signing to the local notary precisely to avoid this."
    ),
    decisive=True,
    notes=TEMPORAL,
)

add(
    "single_notary_can_attest_both_parties_at_one_sitting",
    "One notary could lawfully attest both Russel Perera's and the directors' signatures at a "
    "single sitting.",
    qs=[Q1],
    expected=False,
    ptype="legal_status",
    necessity="supporting",
    polarity="negative",
    auth=["AUTH-M022-008", "AUTH-M022-004"],
    status="inferred",
    counterfactual=(
        "If this were true (parties in one place before one notary), the answer would be ordinary "
        "single-notary execution and rules (25) and (28) would not be engaged."
    ),
    decisive=True,
    notes=(
        "Negative predicate: derived from PR-M022-005 to PR-M022-008 (refusal to travel, different "
        "areas, rule (22)). It is the absence of this option that makes the two-notary route the answer."
    ),
)

add(
    "each_notary_authorised_for_language_of_deed",
    "Each attesting notary is authorised to practise in the language in which the Lease Agreement "
    "is drawn (rule (22) second and third limbs).",
    qs=[Q1],
    expected=True,
    ptype="procedural_condition",
    necessity="supporting",
    auth=["AUTH-M022-008"],
    status="unresolved",
    counterfactual=(
        "If either notary were not authorised for the deed's language he could not attest it and a "
        "different notary would be needed for that party."
    ),
    decisive=True,
    notes="Language of the deed and of each notary's warrant are not stated in the scenario. " + TEMPORAL,
)

# ---------------------------------------------------------------------------
# Q01 - identification of executants (rules 9 and 10)
# ---------------------------------------------------------------------------

add(
    "russel_perera_known_to_anil_fernando",
    "The warehouse owner Russel Perera is personally known to the Colombo notary Anil Fernando.",
    qs=[Q1],
    expected=False,
    ptype="fact",
    necessity="indispensable",
    polarity="negative",
    auth=["AUTH-M022-006", "AUTH-M022-007"],
    status="observed",
    counterfactual=(
        "If Anil Fernando knew Russel Perera, rule (9) would no longer be a reason for Russel Perera to "
        "sign before his own notary; the two-notary conclusion would still follow from rule (22) and "
        "the refusal to travel, so the conclusion stands but reasoning step 4 falls away."
    ),
    decisive=False,
    notes="Source: 'he does not know the owner of the warehouse, namely Mr. Russel Perera'. " + TEMPORAL,
)

add(
    "russel_perera_known_to_ruwan_perera_or_to_two_attesting_witnesses",
    "Russel Perera is known to Ruwan Perera, or failing that to at least two attesting witnesses "
    "who sign the rule (9) declaration, so that Ruwan Perera may attest his signature.",
    qs=[Q1, Q2],
    expected=True,
    ptype="fact",
    necessity="indispensable",
    auth=["AUTH-M022-006", "AUTH-M022-007"],
    status="inferred",
    counterfactual=(
        "If Russel Perera were unknown both to Ruwan Perera and to the witnesses, rule (10) would bar "
        "Ruwan Perera from attesting and the Galle leg of the procedure would fail."
    ),
    decisive=True,
    notes=(
        "Inferred from 'his Notary Ruwan Perera'; the scenario does not say in terms that Ruwan Perera "
        "knows him. For Q02 this feeds the rule (20)(b) statement. " + TEMPORAL
    ),
)

add(
    "company_directors_known_to_anil_fernando",
    "The directors of Cyril & Cyril (Private) Limited who will sign for the company are known to "
    "Anil Fernando.",
    qs=[Q1],
    expected=True,
    ptype="fact",
    necessity="supporting",
    auth=["AUTH-M022-006"],
    status="observed",
    counterfactual=(
        "If the directors were unknown to him, Anil Fernando would need two witnesses who know them "
        "(rule (9)); the two-notary procedure itself would be unchanged."
    ),
    decisive=False,
    notes="Source: 'Anil Fernando knows the directors of the said company'.",
)

# ---------------------------------------------------------------------------
# Q01 - the company's mode of execution
# ---------------------------------------------------------------------------

add(
    "party_executing_in_colombo_is_a_company",
    "One party to the Lease Agreement, Cyril & Cyril (Private) Limited, is a body corporate that "
    "can sign only through natural persons.",
    qs=[Q1],
    expected=True,
    ptype="fact",
    necessity="indispensable",
    auth=["AUTH-M022-019"],
    status="observed",
    counterfactual=(
        "If the Colombo party were a natural person, Companies Act s.19(1)(a) would not apply and the "
        "'two directors sign under the company's name' step would be replaced by personal signature."
    ),
    decisive=True,
    notes="Source: 'A company named Cyril & Cyril (Private) Limited'.",
)

add(
    "company_executes_by_two_directors_signing_under_company_name",
    "The company enters into the notarially attested obligation in writing signed under the "
    "company's name by two directors, and the deed is notarially executed (Companies Act "
    "s.19(1)(a)(i)).",
    qs=[Q1],
    expected=True,
    ptype="procedural_condition",
    necessity="indispensable",
    auth=["AUTH-M022-019"],
    status="inferred",
    counterfactual=(
        "If the company instead signed by its sole director, by persons authorised under its articles, "
        "or by an attorney (s.19(1)(a)(ii)-(iv)), the persons appearing before Anil Fernando would "
        "differ but the deed would still be notarially executed in Colombo; conclusion unchanged."
    ),
    decisive=False,
    notes=(
        "The gold answer adopts the two-director route because the scenario refers to 'the directors' "
        "(plural) whom Anil Fernando knows. Number of directors and any article-based signing "
        "authority are not stated (issue-map unresolved fact)."
    ),
)

add(
    "company_has_at_least_two_directors",
    "The company has two or more directors available to sign under s.19(1)(a)(i).",
    qs=[Q1],
    expected=True,
    ptype="fact",
    necessity="supporting",
    auth=["AUTH-M022-019"],
    status="observed",
    counterfactual=(
        "If the company had a single director, that director would sign alone under s.19(1)(a)(ii); "
        "the procedure and conclusion are otherwise unchanged."
    ),
    decisive=False,
    notes="Source uses the plural 'the directors of the said company'; the exact number is not stated.",
)

add(
    "company_role_in_lease_is_lessee_rather_than_sublessor",
    "The company is the lessee taking the warehouse from its owner Russel Perera (rather than a "
    "head-lessee sub-letting with the owner joining to consent).",
    qs=[Q1],
    expected=None,
    ptype="fact",
    necessity="supporting",
    auth=[],
    status="unresolved",
    counterfactual=(
        "Either reading leaves the execution mechanics unchanged: Russel Perera still executes in "
        "Galle before Ruwan Perera and the company still executes in Colombo before Anil Fernando. "
        "Only the description of the parties in the instrument would differ."
    ),
    decisive=False,
    notes=(
        "Scenario ambiguity recorded in issue-map.json: the company 'wishes to lease out' the warehouse "
        "yet Russel Perera is 'the owner'. Left unresolved deliberately; not to be fixed by a synthetic "
        "document without lawyer sign-off."
    ),
)

# ---------------------------------------------------------------------------
# Q01 - execution before more than one notary (rule 25, s.32(2))
# ---------------------------------------------------------------------------

add(
    "deed_executed_before_more_than_one_notary",
    "The Lease Agreement is one deed executed before two notaries (Ruwan Perera in Galle, Anil "
    "Fernando in Colombo), engaging Notaries Ordinance s.31 rule (25).",
    qs=[Q1, Q2],
    expected=True,
    ptype="legal_status",
    necessity="indispensable",
    auth=["AUTH-M022-001", "AUTH-M022-004"],
    status="inferred",
    counterfactual=(
        "If the deed were executed before a single notary, rule (25) would not apply and there would "
        "be no first/second notary allocation; Q02 would collapse into the ordinary rule (20) attestation."
    ),
    decisive=True,
    notes=TEMPORAL,
)

add(
    "ruwan_perera_is_first_attesting_notary",
    "Ruwan Perera attests the deed first (Russel Perera signs in Galle before the directors sign in "
    "Colombo), so Anil Fernando is the second notary.",
    qs=[Q1, Q2],
    expected=True,
    ptype="fact",
    necessity="indispensable",
    auth=["AUTH-M022-001"],
    status="observed",
    counterfactual=(
        "If Anil Fernando attested first, the rule (25)/(28) duties would swap: Anil Fernando would give "
        "the full rule (20) attestation, keep the protocol and transmit the duplicate (with a rule (29) "
        "cross-district copy, the land being in Galle); Q02 would then concern Anil Fernando's attestation."
    ),
    decisive=True,
    notes=(
        "Q02 stipulates this ('If Ruwan Perera is the first Notary'); for Q01 it is the sequence the "
        "gold answer adopts because Ruwan Perera drafts the deed and holds the executant who will not "
        "travel. " + TEMPORAL
    ),
)

add(
    "only_russel_perera_signs_before_ruwan_perera",
    "Russel Perera is the only executant who signs before Ruwan Perera; the company's directors "
    "sign later before Anil Fernando.",
    qs=[Q1, Q2],
    expected=True,
    ptype="fact",
    necessity="indispensable",
    auth=["AUTH-M022-004"],
    status="inferred",
    counterfactual=(
        "If the directors also signed before Ruwan Perera in Galle, one notary would attest every "
        "signature, no second notary would be needed (Q01 changes) and Ruwan Perera's attestation "
        "would record all executants (Q02 changes)."
    ),
    decisive=True,
    notes=(
        "Under s.32(2)(ii) the deed is deemed executed before Ruwan Perera for rules (18) and (20) "
        "whenever a party signs before him, so his attestation records only that signing."
    ),
)

add(
    "russel_perera_signs_before_ruwan_perera_and_two_witnesses_in_mutual_presence",
    "Russel Perera and two attesting witnesses sign the Lease Agreement in Galle in Ruwan Perera's "
    "presence and in the presence of one another, and Ruwan Perera signs in their presence.",
    qs=[Q1, Q2],
    expected=True,
    ptype="procedural_condition",
    necessity="indispensable",
    auth=["AUTH-M022-009", "AUTH-M022-017"],
    status="inferred",
    counterfactual=(
        "If the executant and witnesses did not sign in one another's presence, rule (12) and PoF s.2 "
        "would be breached and Ruwan Perera could not truthfully make the rule (20)(a) statement."
    ),
    decisive=True,
    notes="Availability of two suitable witnesses in Galle is assumed; the scenario does not name them. " + TEMPORAL,
)

add(
    "directors_sign_before_anil_fernando_and_two_witnesses_in_mutual_presence",
    "The two directors and two attesting witnesses sign in Colombo in Anil Fernando's presence and "
    "in the presence of one another, and Anil Fernando signs in their presence.",
    qs=[Q1],
    expected=True,
    ptype="procedural_condition",
    necessity="indispensable",
    auth=["AUTH-M022-009", "AUTH-M022-017"],
    status="inferred",
    counterfactual=(
        "If the Colombo signing did not satisfy rule (12) and PoF s.2, the company's execution would "
        "be defective and the deed would not be validly executed by both parties."
    ),
    decisive=True,
    notes=TEMPORAL,
)

add(
    "first_notary_complies_with_all_requirements_of_rule_20",
    "As the notary who first attests, Ruwan Perera must comply with all the requirements of rule "
    "(20), including the stamp statement in paragraph (f).",
    qs=[Q1, Q2],
    expected=True,
    ptype="procedural_condition",
    necessity="indispensable",
    auth=["AUTH-M022-001", "AUTH-M022-002"],
    status="inferred",
    counterfactual=(
        "If the first notary were subject only to the reduced (a)-(e) and (g) list, the Q02 answer "
        "would omit the stamp statement and the distinction between the two attestations would vanish."
    ),
    decisive=True,
    notes=TEMPORAL,
)

add(
    "second_notary_complies_only_with_rule_20_a_to_e_and_g",
    "Anil Fernando, as the other attesting notary, complies with paragraphs (a) to (e) of rule (20) "
    "and with paragraph (g) only as to erasures, alterations and interpolations in the signatures "
    "he attests or in his serial number.",
    qs=[Q1, Q2],
    expected=True,
    ptype="procedural_condition",
    necessity="supporting",
    auth=["AUTH-M022-001"],
    status="inferred",
    counterfactual=(
        "If the second notary also had to give the full attestation, the description of Anil Fernando's "
        "reduced attestation in the gold answer would be wrong, but the execution route would stand."
    ),
    decisive=False,
    notes=TEMPORAL,
)

add(
    "each_notary_numbers_deed_in_own_consecutive_series",
    "Each attesting notary gives the Lease Agreement a number in his own consecutive series under "
    "rule (23), as required by rule (25)(b).",
    qs=[Q1, Q2],
    expected=True,
    ptype="procedural_condition",
    necessity="supporting",
    auth=["AUTH-M022-001", "AUTH-M022-010"],
    status="inferred",
    counterfactual=(
        "Omitting a notary's serial number would breach rules (23) and (25)(b) but would not change "
        "how the deed is executed or what the attestation must state."
    ),
    decisive=False,
    notes="Under s.32(2)(i) the deed is deemed executed at the first signing for rule (23) purposes. " + TEMPORAL,
)

add(
    "first_notary_preserves_protocol_and_second_keeps_certified_copy",
    "Ruwan Perera preserves the rule (24) draft or copy as his protocol; Anil Fernando supplies "
    "himself with a certified copy of the deed as his protocol (rule (25)(c)).",
    qs=[Q1, Q2],
    expected=True,
    ptype="procedural_condition",
    necessity="supporting",
    auth=["AUTH-M022-001", "AUTH-M022-011"],
    status="inferred",
    counterfactual=(
        "Reversing the protocol allocation would follow only if the order of attestation reversed "
        "(PR-M022-019); it does not alter the execution route."
    ),
    decisive=False,
    notes=TEMPORAL,
)

add(
    "deed_executed_in_duplicate",
    "The Lease Agreement is drawn and executed in duplicate as PoF s.16 requires of every deed "
    "that must be attested by a notary.",
    qs=[Q1],
    expected=True,
    ptype="procedural_condition",
    necessity="supporting",
    auth=["AUTH-M022-018"],
    status="inferred",
    counterfactual=(
        "Without a duplicate there would be nothing for the first notary to transmit under rule (28) "
        "and no duplicate stamps to state under rule (20)(f); the execution route is otherwise unchanged."
    ),
    decisive=False,
    notes="PoF s.16 excerpt is the pre-2022 tree text (current_text_superseded_since_event).",
)

add(
    "first_notary_transmits_duplicate_to_registrar_of_lands",
    "Ruwan Perera, as the notary who first attests, delivers or transmits the duplicate to the "
    "Registrar of Lands of the district in which he resides; Anil Fernando need not transmit one.",
    qs=[Q1, Q2],
    expected=True,
    ptype="procedural_condition",
    necessity="supporting",
    auth=["AUTH-M022-005"],
    status="inferred",
    counterfactual=(
        "If the transmitting duty fell on Anil Fernando instead (only if he attested first), the "
        "rule (29) cross-district copy would also be required; the execution route is unchanged."
    ),
    decisive=False,
    notes=TEMPORAL,
)

add(
    "land_situated_outside_first_notary_district_of_residence",
    "The warehouse lies in a district other than that in which the transmitting notary (Ruwan "
    "Perera) resides, so that rule (29) would require a certified copy to the Registrar of Lands of "
    "the land's district.",
    qs=[Q1],
    expected=False,
    ptype="fact",
    necessity="supporting",
    polarity="negative",
    auth=["AUTH-M022-013", "AUTH-M022-005"],
    status="inferred",
    counterfactual=(
        "If Ruwan Perera resided outside the Galle district, he would additionally have to send a "
        "certified copy and a Form F list to the Galle Registrar of Lands; the execution route is unchanged."
    ),
    decisive=False,
    notes=(
        "Scenario says Ruwan Perera is 'practising in Galle' and the warehouse is 'situated in Galle'; "
        "his district of residence is not stated, so the negative value is inferred. " + TEMPORAL
    ),
)

add(
    "deed_drawn_by_notary_other_than_second_attesting_notary",
    "The Lease Agreement is drawn by Ruwan Perera, not by Anil Fernando who also attests it.",
    qs=[Q1],
    expected=True,
    ptype="fact",
    necessity="supporting",
    auth=["AUTH-M022-016"],
    status="observed",
    counterfactual=(
        "If Anil Fernando drew the deed himself, rule (2) would not require a drafting certificate for "
        "his attestation (but would for Ruwan Perera's); the execution route is unchanged."
    ),
    decisive=False,
    notes="Source: Russel Perera 'wants his Notary Ruwan Perera ... to draft and attest'. AUTH-M022-016 is partially_verified (tree text scrambled; RGD PDF supports the proposition).",
)

add(
    "drafting_notary_certificate_endorsed_on_deed",
    "A certificate signed by Ruwan Perera certifying that he drew the deed is endorsed on it before "
    "Anil Fernando attests (rule (2)).",
    qs=[Q1],
    expected=True,
    ptype="procedural_condition",
    necessity="supporting",
    auth=["AUTH-M022-016"],
    status="inferred",
    counterfactual=(
        "Without the certificate Anil Fernando could not lawfully attest a deed drawn by another; the "
        "remedy is to endorse the certificate, so the execution route is unchanged."
    ),
    decisive=False,
    notes=(
        "AUTH-M022-016 is partially_verified (source conflict: tree wording scrambled, RGD PDF reads "
        "'certifying that such deed or instrument has been drawn by himself'); kept supporting. " + TEMPORAL
    ),
)

add(
    "russel_perera_executes_through_attorney_before_colombo_notary",
    "Russel Perera appoints an attorney to sign the Lease Agreement on his behalf in Colombo before "
    "Anil Fernando instead of signing personally before Ruwan Perera.",
    qs=[Q1],
    expected=False,
    ptype="fact",
    necessity="supporting",
    polarity="negative",
    auth=["AUTH-M022-014", "AUTH-M022-017"],
    status="observed",
    counterfactual=(
        "If he did execute through an attorney in Colombo, a single notary (Anil Fernando) could attest "
        "the whole deed, keeping a copy of the power of attorney with his protocol (rule (30)); the "
        "two-notary answer would become the alternative rather than the primary route."
    ),
    decisive=True,
    notes=(
        "Scenario: he 'wants his Notary Ruwan Perera ... to draft and attest', so the attorney route is "
        "not taken. AUTH-M022-014 is partially_verified: the 2022 Act describes the pre-2022 rule (30) as "
        "reading 'registered power of attorney', which the 1980 text lacks; October 2020 wording uncertain."
    ),
)

# ---------------------------------------------------------------------------
# Q02 - contents of the first notary's attestation (rule 20)
# ---------------------------------------------------------------------------

add(
    "attestation_made_without_delay_and_signed_and_sealed",
    "Ruwan Perera attests the deed without delay after Russel Perera signs before him, and signs "
    "and seals the attestation.",
    qs=[Q2],
    expected=True,
    ptype="procedural_condition",
    necessity="indispensable",
    auth=["AUTH-M022-002"],
    status="inferred",
    counterfactual=(
        "An unsigned or unsealed attestation would not satisfy rule (20); the list of statements "
        "would be incomplete without the signing-and-sealing requirement."
    ),
    decisive=True,
    notes=(
        "Case law (AUTH-M022-022, partially_verified) treats 'attestation' as covering both the notary's "
        "signature and the attestation clause; cited in notes only because it is not fully verified. " + TEMPORAL
    ),
)

add(
    "attestation_states_deed_signed_in_notary_presence_and_in_presence_of_one_another",
    "The attestation states that the deed was signed by Russel Perera and the witnesses in Ruwan "
    "Perera's presence and in the presence of one another (rule (20)(a)).",
    qs=[Q2],
    expected=True,
    ptype="procedural_condition",
    necessity="indispensable",
    auth=["AUTH-M022-002", "AUTH-M022-009"],
    status="inferred",
    counterfactual="Omitting this statement would leave the attestation non-compliant with rule (20)(a) and the gold list short one item.",
    decisive=True,
    notes=TEMPORAL,
)

add(
    "attestation_states_whether_executant_and_witnesses_known_to_notary",
    "The attestation states whether Russel Perera and the attesting witnesses (specifying which "
    "witnesses) were known to Ruwan Perera (rule (20)(b)).",
    qs=[Q2],
    expected=True,
    ptype="procedural_condition",
    necessity="indispensable",
    auth=["AUTH-M022-002", "AUTH-M022-006"],
    status="inferred",
    counterfactual="Omitting this statement would breach rule (20)(b); the gold list would be short one item.",
    decisive=True,
    notes=(
        "Rule (20)(b) was rewritten by the Notaries (Amendment) Act No. 31 of 2022 without quoting the "
        "old words; the October 2020 text rests on the 1980 edition alone. " + TEMPORAL
    ),
)

add(
    "attestation_states_date_place_and_witness_names_and_residences",
    "The attestation states the day, month and year on which and the place (Galle) where Russel "
    "Perera executed the deed, and the full names and residences of the attesting witnesses "
    "(rule (20)(c)); the date and place are also inserted in the deed in letters (rule (18)).",
    qs=[Q2],
    expected=True,
    ptype="procedural_condition",
    necessity="indispensable",
    auth=["AUTH-M022-002", "AUTH-M022-012", "AUTH-M022-004"],
    status="inferred",
    counterfactual=(
        "Omitting date, place or witness particulars would breach rule (20)(c). Under s.32(2)(ii) the "
        "relevant date and place are those of Russel Perera's signing, not of the later Colombo signing."
    ),
    decisive=True,
    notes=TEMPORAL,
)

add(
    "attestation_states_whether_deed_read_over_or_read_and_explained",
    "The attestation states whether the deed was read over by Russel Perera, or read and explained "
    "by Ruwan Perera to him in the presence of the attesting witnesses (rule (20)(d)).",
    qs=[Q2],
    expected=True,
    ptype="procedural_condition",
    necessity="indispensable",
    auth=["AUTH-M022-002"],
    status="inferred",
    counterfactual="Omitting this statement would breach rule (20)(d); the gold list would be short one item.",
    decisive=True,
    notes=TEMPORAL,
)

add(
    "attestation_states_whether_consideration_paid_in_notary_presence_and_amount",
    "The attestation states whether any money was paid or not in Ruwan Perera's presence as the "
    "consideration or part of it and, if paid, the actual amount in local currency (rule (20)(e)).",
    qs=[Q2],
    expected=True,
    ptype="procedural_condition",
    necessity="indispensable",
    auth=["AUTH-M022-002"],
    status="inferred",
    counterfactual="Omitting this statement would breach rule (20)(e); the gold list would be short one item.",
    decisive=True,
    notes=(
        "Diyes Singho v. Herath (AUTH-M022-023, partially_verified) holds the statement is not itself "
        "proof of payment; noted only, not relied on. Rule (20)(e) was rewritten in 2022 without quoting "
        "the old words. " + TEMPORAL
    ),
)

add(
    "attestation_states_number_and_value_of_stamps_on_deed_and_duplicate",
    "The attestation states the number and value of the adhesive stamps affixed to, or the value of "
    "the impressed stamps on, the deed and its duplicate (rule (20)(f)) - the item that only the "
    "first notary must state.",
    qs=[Q2],
    expected=True,
    ptype="procedural_condition",
    necessity="indispensable",
    auth=["AUTH-M022-002", "AUTH-M022-001"],
    status="inferred",
    counterfactual=(
        "If Ruwan Perera were the second notary this item would drop out under rule (25)(a); its "
        "presence is what distinguishes the first notary's attestation in the gold answer."
    ),
    decisive=True,
    notes=(
        "Rex v. Seenytamby (AUTH-M022-024, verified) confirms that a knowingly false stamp statement in "
        "the attestation is an offence. " + TEMPORAL
    ),
)

add(
    "attestation_specifies_erasures_alterations_and_interpolations",
    "The attestation specifically states the erasures, alterations and interpolations in the deed, "
    "whether they were made before it was read over, and any made in the signatures, the serial "
    "number and the writing on the stamps (rule (20)(g)).",
    qs=[Q2],
    expected=True,
    ptype="procedural_condition",
    necessity="indispensable",
    auth=["AUTH-M022-002"],
    status="inferred",
    counterfactual="Omitting this statement would breach rule (20)(g); the gold list would be short one item.",
    decisive=True,
    notes="Rule (20)(g) was amended by the Notaries (Amendment) Act No. 6 of 2024, after the matter date. " + TEMPORAL,
)

add(
    "attestation_substantially_in_form_e_and_legibly_signed_in_deed_language",
    "The attestation is substantially in Form E of the Second Schedule, legibly signed in the "
    "language of the deed (and with the notary's usual signature if different), with any erasure, "
    "alteration or interpolation in the attestation authenticated by his initials (rule (21)).",
    qs=[Q2],
    expected=True,
    ptype="procedural_condition",
    necessity="supporting",
    auth=["AUTH-M022-003"],
    status="inferred",
    counterfactual=(
        "A departure from Form E or an unsigned attestation would breach rule (21) but would not alter "
        "the list of rule (20) statements the question asks for."
    ),
    decisive=False,
    notes="Form E (1980 revised edition) was replaced by the 2022 amending Act, after the matter date. " + TEMPORAL,
)

add(
    "russel_perera_signature_differs_from_name_given",
    "Russel Perera's signature differs from the full name he gives to the notary, so that rule (14) "
    "requires the attestation to describe him by both names.",
    qs=[Q2],
    expected=None,
    ptype="fact",
    necessity="supporting",
    auth=["AUTH-M022-015"],
    status="unresolved",
    counterfactual=(
        "If true, one extra statement (both names) is added to the attestation; if false, nothing "
        "changes. Either way the core rule (20) list is unaffected."
    ),
    decisive=False,
    notes="Not stated in the scenario. " + TEMPORAL,
)

add(
    "russel_perera_reads_deed_himself",
    "Russel Perera reads the deed over himself rather than having Ruwan Perera read and explain it "
    "to him in the witnesses' presence.",
    qs=[Q2],
    expected=None,
    ptype="fact",
    necessity="supporting",
    auth=["AUTH-M022-002"],
    status="unresolved",
    counterfactual=(
        "Whichever is true, rule (20)(d) requires the attestation to state which occurred; the value "
        "changes the wording of the statement, not the requirement to make it."
    ),
    decisive=False,
    notes="Literacy / language of the executant not stated (issue-map unresolved fact).",
)

add(
    "consideration_paid_in_ruwan_perera_presence",
    "Rent, premium or other consideration is paid in Ruwan Perera's presence at the Galle signing.",
    qs=[Q2],
    expected=None,
    ptype="fact",
    necessity="supporting",
    auth=["AUTH-M022-002"],
    status="unresolved",
    counterfactual=(
        "If paid, the attestation must state the actual amount in local currency; if not, it must state "
        "that none was paid in his presence. The requirement to make the statement is unaffected."
    ),
    decisive=False,
    notes="Not stated in the scenario (issue-map unresolved fact).",
)

add(
    "stamp_type_and_value_on_deed_and_duplicate_determined",
    "The number and value of adhesive stamps, or the value of impressed stamps, on the deed and its "
    "duplicate are known at the time of Ruwan Perera's attestation.",
    qs=[Q2],
    expected=None,
    ptype="fact",
    necessity="supporting",
    auth=["AUTH-M022-002"],
    status="unresolved",
    counterfactual=(
        "The values only fill in the rule (20)(f) statement; the requirement to state them is unaffected. "
        "Stamp duty computation is outside the verified authorities."
    ),
    decisive=False,
    notes="Not stated in the scenario (issue-map unresolved fact).",
)

add(
    "attesting_witnesses_known_to_ruwan_perera",
    "The two attesting witnesses at the Galle signing are known to Ruwan Perera.",
    qs=[Q2],
    expected=None,
    ptype="fact",
    necessity="supporting",
    auth=["AUTH-M022-002", "AUTH-M022-006"],
    status="unresolved",
    counterfactual=(
        "Rule (20)(b) requires the attestation to say whether the witnesses were known and, if so, "
        "which; the value changes the wording, not the requirement. If Russel Perera were unknown to "
        "the notary, at least two witnesses would have to know him (rule (9))."
    ),
    decisive=False,
    notes="Witnesses are not identified in the scenario.",
)

# ---------------------------------------------------------------------------
# Temporal scope (both questions)
# ---------------------------------------------------------------------------

add(
    "post_october_2020_amendments_excluded_from_answer",
    "The Notaries (Amendment) Acts No. 31 of 2022 and No. 6 of 2024 (which rewrote rule (20)(b), (e) "
    "and (g) and replaced Form E) post-date the October 2020 matter reference date and are excluded "
    "from the answer.",
    qs=[Q1, Q2],
    expected=True,
    ptype="legal_status",
    necessity="supporting",
    auth=["AUTH-M022-020", "AUTH-M022-021"],
    status="observed",
    counterfactual=(
        "If the matter were dated after the 2022/2024 Acts came into force, the contents of rule (20)(b), "
        "(e) and (g), rule (30) and Form E would differ and the Q02 list would have to be restated."
    ),
    decisive=True,
    notes=(
        "Matter reference date 2020-10 (Sri Lanka Law College Conveyancing LW 307, October 2020 session); "
        "the scenario itself is undated. Commencement dates of the 2022/2024 Acts are not held in the repo."
    ),
)


def main() -> None:
    out = {
        "benchmark_matter_id": MATTER,
        "run_id": RUN_ID,
        "produced_by_agent": "predicate-derivation-agent (Claude) via _build_predicates.py",
        "predicates": _rows,
    }
    path = HERE / "predicates.json"
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {path} ({len(_rows)} predicates)")


if __name__ == "__main__":
    main()
