"""Shared correction-lifecycle scenario for the agent-memory spike.

One fixed matter replayed against each candidate memory system
(see docs/memory-system-evaluation.md). All names are invented.

The scenario mirrors a real matter session: ingest document summaries,
write session notes, then CORRECT a fact. The probes test whether the
correction wins, whether history survives, and whether provenance holds.
"""

from datetime import datetime, timezone

MATTER_ID = "matter-M-2026-014"

# Each event: (name, body, source_description, reference_time)
EVENTS = [
    (
        "doc-summary-deed-2015",
        "Document 1 (deed of transfer No. 4521, dated 2015-03-12, attested by "
        "Notary K. Weerasinghe): A. B. Silva transfers Lot 12 in Plan No. 4021 "
        "to C. D. Perera for Rs. 4,500,000. The deed schedule describes the "
        "land extent as two roods and fifteen perches (2R 15P).",
        "extraction summary of uploaded document 1 (unverified)",
        datetime(2026, 7, 14, 9, 30, tzinfo=timezone.utc),
    ),
    (
        "doc-summary-survey-2012",
        "Document 2 (survey plan No. 4021, dated 2012-08-02, licensed surveyor "
        "R. Jayasuriya): depicts Lot 12, a land called Ketakelagahawatta in "
        "Gampaha district. Extent given as two roods and fifteen perches "
        "(2R 15P).",
        "extraction summary of uploaded document 2 (unverified)",
        datetime(2026, 7, 14, 9, 35, tzinfo=timezone.utc),
    ),
    (
        "doc-summary-prior-deed-1998",
        "Document 3 (deed of transfer No. 1187, dated 1998-11-20): E. F. "
        "Fernando transfers the same Lot 12 to A. B. Silva. Chain of title "
        "for the matter therefore runs Fernando (1998) to Silva (2015) to "
        "Perera.",
        "extraction summary of uploaded document 3 (unverified)",
        datetime(2026, 7, 14, 9, 40, tzinfo=timezone.utc),
    ),
    (
        "session-note-jul-14",
        "Agent session note, 14 July 2026: chain of title verified by the "
        "lawyer back to the 1998 deed. Open issue: the client mentioned a "
        "newer survey exists, so the extent stated in the 2015 deed schedule "
        "may be outdated. Next step: obtain the newer survey plan and "
        "confirm the extent before drafting.",
        "agent working note (not verified authority)",
        datetime(2026, 7, 14, 11, 5, tzinfo=timezone.utc),
    ),
    (
        "fact-correction-extent",
        "Lawyer correction, 16 July 2026: the correct extent of Lot 12 is one "
        "rood and twenty perches (1R 20P), per the newer survey plan No. 5530 "
        "dated 2024-05-30 by licensed surveyor P. Gunawardena. This supersedes "
        "the extent of two roods and fifteen perches stated in the 2015 deed "
        "schedule and the 2012 survey plan; a road-widening acquisition in "
        "2019 reduced the land. Fact verified by the lawyer.",
        "lawyer-verified correction entered through the review table",
        datetime(2026, 7, 16, 14, 20, tzinfo=timezone.utc),
    ),
]

# (probe_id, question, what a passing answer must contain)
PROBES = [
    (
        "P1-correction-wins",
        "What is the extent of the land in this matter?",
        "1 rood 20 perches (1R 20P) per survey plan 5530, NOT 2R 15P",
    ),
    (
        "P2-history-survives",
        "What extent did the 2015 deed schedule state, and is that value "
        "still current?",
        "2R 15P, marked superseded/invalid by the 16 July correction",
    ),
    (
        "P3-provenance",
        "Who corrected the extent, when, and on what basis?",
        "lawyer correction on 16 July 2026, basis survey plan 5530 (2024)",
    ),
    (
        "P4-resume",
        "What were we working on in the last session and what is the next "
        "step?",
        "chain of title verified to 1998; obtain/confirm newer survey, "
        "then draft",
    ),
]
