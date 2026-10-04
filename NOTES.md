# NOTES (P1): differences between brief and real SDK / verified behavior

Verified with sarvamai 0.1.35 and a live Sarvam API run.

## Digitise

- Digitise jobs are submitted normally.
- Completed Digitise output is retrieved using `get_download_url()`.
- The downloaded ZIP contains Markdown output and per-page metadata JSON.
- Page metadata contains `page_num` and OCR `blocks`.
- Each block contains text, reading order, layout information, and bounding boxes.
- P1 reconstructs page-level text from the blocks in reading order.
- Full Markdown output is also retained as `full_text`.

## Extract

- Extract jobs are submitted normally.
- Results are retrieved using `get_results()`.
- The live run successfully returned the expected six-term schema.
- Extracted values were successfully verified against Digitise OCR text.

## Verification

Live test agreement:

- monthly_rent: verified, score 100.0, page 2
- security_deposit: verified, score 100.0, page 2
- deposit_refund_period: verified, score 100.0, page 2
- lock_in_period: verified, score 100.0, page 3
- notice_period: verified, score 100.0, page 3
- maintenance_charges: verified, score 99.4, page 2

## Cache

- Agreement IDs are based on SHA256 of the source PDF.
- A second run on the same PDF produces a cache hit and makes zero Sarvam API calls.

## Rate limiting / retries

- P1 uses a 9-calls/minute limiter to stay below the 10 req/min API limit.
- 429 and 503 responses are retried with exponential backoff.

## Remaining items

- Page-count limit (10) is not pre-checked locally; the API will reject longer files.
- Additional document types and photographed/scanned stress-test cases still need evaluation.
