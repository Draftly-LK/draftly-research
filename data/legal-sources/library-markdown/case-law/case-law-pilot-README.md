# Case-Law Pilot README

## Source

- Parsed digest: <https://www.lawlanka.com/lal_v2/relatedCases?chapterId=2001Y5V117C&subjectName=registration+of+documents>
- Subject filter: `registration of documents`
- Primary intended source: LawNet PDFs, but the pilot could not fetch them reliably.

## Counts

- Digest row-level entries seen: 76
- Unique case citations seen: 51
- Entries matched by conveyancing filter: 76
- Registration of Documents sections represented: 10, 11, 12, 13, 14, 15, 151, 16, 17, 18, 22, 26, 30, 31, 32, 33, 36, 38, 39, 4, 6, 7, 8, 9, subject

## Outputs

- Citation CSV: `data/legal-sources/manifests/case-law-citations.csv`
- Sample node: `data/legal-sources/library-markdown/case-law/registration-of-documents/nodes/de-silva-v-weerappa-chettiar.md`
- Sample node: `data/legal-sources/library-markdown/case-law/registration-of-documents/nodes/rev-maussagolle-dharmarakkitha-thero-and-another-v-registrar-of-lands-and-others.md`
- Sample node: `data/legal-sources/library-markdown/case-law/registration-of-documents/nodes/registrar-general-v-sangarapillai.md`

## LawNet Fetch Notes

LawNet HTTPS failed certificate verification during this pilot; the uploads directory also returned 404 when retried without verification.

- <https://lawnet.gov.lk/wp-content/uploads/> TLS fetch failed: URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Hostname mismatch, certificate is not valid for 'lawnet.gov.lk'. (_ssl.c:1010)>
- <https://lawnet.gov.lk/wp-content/uploads/> insecure retry failed: HTTP 404
- <https://www.lawnet.gov.lk/wp-content/uploads/> TLS fetch failed: URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Hostname mismatch, certificate is not valid for 'www.lawnet.gov.lk'. (_ssl.c:1010)>
- <https://www.lawnet.gov.lk/wp-content/uploads/> insecure retry failed: HTTP 404

## Garbled Or Uncertain Extraction

- LawNet HTTPS certificate verification failed for `lawnet.gov.lk` and `www.lawnet.gov.lk`.
- LawNet `/wp-content/uploads/` returned 404 when retried without TLS verification.
- The digest page says `Showing 1-25 of 25`, but the parsed table contains more row-level references because cases are repeated under multiple Registration of Documents sections.
- Some party-name casing/punctuation is inconsistent in the digest, for example `VS` versus `v.` and names ending in `et al.,`; those are preserved or lightly normalized, not silently corrected.

## Verification Rule

Every row is `unverified` until the underlying NLR/SLR report text is
checked. Do not copy headnotes or legal propositions into public docs from
this pilot alone.
