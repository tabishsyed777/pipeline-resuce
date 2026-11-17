# Repair the order-event pipeline

Fix `/app/pipeline.py`. Only this file is your submission; do not add dependencies. Python standard library is available. Invoke:

```sh
python /app/pipeline.py --input events.csv --output report.json
```

Input is UTF-8 CSV with exactly these unique header names (in any order):
`event_id,order_id,event_time,status,amount,currency`.

Rules:

- Every field is required. IDs must be nonempty strings without leading/trailing whitespace. Do not modify ID contents.
- `event_time` is an ISO timestamp with `T`, seconds, optional fractional seconds, and an explicit `Z` or `±HH:MM` timezone. Convert to UTC before date grouping and comparisons.
- Status is exactly `paid`, `refunded`, or `cancelled`. Currency is exactly three uppercase ASCII letters.
- Amount is a nonnegative decimal matching `[0-9]+(\.[0-9]{1,2})?`. Convert to integer cents exactly. Reject exponents, signs, NaN, infinity, extra fractional digits, and whitespace.
- Duplicate event IDs with identical raw CSV fields are ignored. Conflicting records sharing an event ID invalidate the entire input.
- Per order, select the latest event by UTC timestamp; break ties by lexicographically greatest event ID. Input order must not affect the result.
- Only orders whose selected status is `paid` contribute. Group by the selected event's **UTC date** and currency. Count each selected paid order once and sum its amount in integer cents. Do not combine currencies. Omit groups with no paid orders.
- Empty CSV with valid headers produces `{"rows":[]}`. Missing/duplicate/unknown headers, missing/extra fields, invalid values, and an input path equal to the output path must fail with a nonzero exit code.

Write JSON with exactly one key, `rows`, containing objects with exactly `day` (YYYY-MM-DD), `currency`, `orders` (integer), and `revenue_cents` (integer). Sort rows ascending by `(day, currency)`. Formatting/whitespace are not graded.

On any invalid input, do not create the output or alter an existing output. On success, replace the output atomically using a temporary file in the output directory and a filesystem rename. The output parent directory already exists. Do not silently skip invalid input rows.

A small public sample is in `/app/sample.csv`. With this sample the expected total is 30 cents for two USD orders on 2025-01-01. Evaluation includes additional fixtures not present in the agent image.
