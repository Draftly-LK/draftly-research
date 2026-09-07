# M011 research notes (statutory-qa-v1, unverified)

Both Tier A questions are `blocked_missing_authority` /
`mixed_statute_and_case`. 13 provisions: 11 from the Matrimonial Rights and
Inheritance Ordinance No. 15 of 1876, plus 2 background entries that only
prove the missing authority exists.

Deed of Gift No 515 of 2018 reserved a life interest to Ajith, barred Prabash
from selling, mortgaging or dealing, and gave the land over to Subash on
Prabash's death. That is a fideicommissary clause. If it operates, Subash owns
the whole and every later death is a distractor; if not, Prabash took
absolutely and the three later intestacies control. The corpus cannot choose:
the Abolition of Fideicommissa and Entails Act No. 20 of 1972 is absent, and
MRIO s 36 sends the rest to Roman-Dutch law, also absent.

Queries: `acts`; `toc 15-1876`; `show --full` on 15-1876 ss 3, 20-32, 35, 36;
`grep fideicommiss`, `"life interest"`, `usufruct`, `entail`; `defs 15-1876`;
`edges 15-1876/s24` and `/s25` (both empty); `show 9-1917/s3`, `1-1972/s13`,
`7-1840/s2`. All 13 excerpts pass `check`.

Rejected: Prevention of Frauds Ordinance s 2 (deed validity not in issue, and
the corpus text is the post-2022/2024 substitution, not the 2018 text); Wills
Ordinance, Kandyan and Muslim succession and Jaffna MRIO (no fact points to a
personal law); Revocation of Irrevocable Deeds of Gift Act No. 5 of 2017 (no
ingratitude); MRIO s 35 collation (the land never re-entered a parent's
estate).

## For the verifier, in order

1. The 1972 Act; if it enters the corpus both questions may become
   `statute_only` and the branch below becomes the gold answer.
2. Check the arithmetic: Prabash's estate Linda 1/2, each child 1/8; Brian's
   1/8 splits Sara 1/16, Linda 1/32, Rian 1/48, Sunali and Bimali 1/192 each;
   Sunali's 25/192 splits Bimali 3/4, Rian 1/4. Final Linda 408/768,
   Bimali 175/768, Rian 137/768, Sara 48/768.
3. Two scenario defects, both in `block_reason`: the background never says how
   Prabash's marriage to Sheela ended, so Linda's status under s 22 is
   assumed; and one daughter is called Sunali, then Sonali. Sheela's 2019
   death has no effect on this land.
4. Transcription errors quoted verbatim: "ab interstate" (s 21) and
   "balf-blood" (s 26).
