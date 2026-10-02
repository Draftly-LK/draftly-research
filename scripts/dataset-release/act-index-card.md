---
pretty_name: Draftly Sri Lankan Act Source Index
language:
  - en
configs:
  - config_name: paper_corpus_acts
    data_files:
      - split: sources
        path: acts/data.jsonl
---

# Draftly Sri Lankan Act Source Index

This first index covers the 112 enactment documents used by the paper: 52 principal enactments and 60 amending Acts. It contains metadata and source URLs only. It does not contain Act PDFs or extracted statutory text.

`source_url` comes from the recorded source edition. A `candidate_source_url` is a possible registry match by enactment number and year; its title and edition still need checking. Empty URLs mean no source link has been established. The `url_reachability`, HTTP status, final URL and check date describe whether a link responded during an automated check. They do not verify that the linked edition matches the paper corpus. Some recorded editions come from third-party publishers; the publisher and edition kind are shown per row.

At the first automated check, 58 rows had reachable links, 10 had unreachable links and 44 had no link. Sixteen of the linked rows use unconfirmed registry candidates. These counts may change as source sites move. Missing or broken links are retained to show coverage gaps rather than replaced with guessed editions.

The link index is a discovery aid, not the frozen text corpus used to calculate the paper's retrieval scores. External URLs can move or point to a different edition. The corpus fingerprint ties these rows to the paper's internal snapshot. A later index version may add other Sri Lankan Acts, with paper-corpus membership kept explicit. No blanket licence over linked third-party content is asserted.
