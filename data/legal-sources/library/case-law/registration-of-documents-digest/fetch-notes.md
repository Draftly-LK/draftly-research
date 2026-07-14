# Registration of Documents Case-Law Fetch Notes

## LawNet Status

LawNet HTTPS failed certificate verification during this pilot; the uploads directory also returned 404 when retried without verification.

- <https://lawnet.gov.lk/wp-content/uploads/> TLS fetch failed: URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Hostname mismatch, certificate is not valid for 'lawnet.gov.lk'. (_ssl.c:1010)>
- <https://lawnet.gov.lk/wp-content/uploads/> insecure retry failed: HTTP 404
- <https://www.lawnet.gov.lk/wp-content/uploads/> TLS fetch failed: URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Hostname mismatch, certificate is not valid for 'www.lawnet.gov.lk'. (_ssl.c:1010)>
- <https://www.lawnet.gov.lk/wp-content/uploads/> insecure retry failed: HTTP 404

## Fallback Digest Used

- Source: <https://www.lawlanka.com/lal_v2/relatedCases?chapterId=2001Y5V117C&subjectName=registration+of+documents>
- Subject: `registration of documents`
- Status: digest page fetched and parsed; individual law-report PDFs were not fetched.
