from lawchain.generation import summarize
from lawchain.models import LawchainHit


def test_summarize_cites_only_provided_sections() -> None:
    hits = [
        LawchainHit(
            section_id="SRC001:s2",
            source_id="SRC001",
            title="Prevention of Frauds Ordinance",
            heading="Deeds affecting immovable property",
            excerpt="No sale...shall be in writing...",
            score=0.95,
        ),
        LawchainHit(
            section_id="SRC001:s3",
            source_id="SRC001",
            title="Prevention of Frauds Ordinance",
            heading="Certain contracts...",
            excerpt="The provisions of section 2...",
            score=0.85,
        ),
    ]

    answer = summarize("What must be in writing?", hits)

    evidence_ids = {hit.section_id for hit in hits}
    for claim in answer.claims:
        assert claim.section_id in evidence_ids, f"Claim cited {claim.section_id}, not in evidence {evidence_ids}"


def test_summarize_with_no_hits_returns_no_claims() -> None:
    answer = summarize("irrelevant question", [])
    assert answer.claims == []
    assert answer.hits == []
