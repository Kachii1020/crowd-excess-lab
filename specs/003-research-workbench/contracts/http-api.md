# HTTP API Contract v1

Base path: `/api/v1`

All endpoints are read-only. Dates use ISO 8601. KRW amounts and high-precision source ratios use
decimal strings; derived return and attention values use JSON numbers. Missing observations are
JSON `null` with a separate reason where applicable. Errors use `{ "detail": "safe message" }`.

## `GET /health`

Returns service state and API version. It does not probe external providers.

## `GET /runs`

Returns newest-first `ResearchRunSummary[]`. Invalid run directories are omitted from the normal
list and may be reported in a sanitized diagnostics count.

## `GET /runs/{run_id}`

Returns one run summary plus exact artifact coverage.

`run_id` must match `^[0-9]{8}T[0-9]{6}Z$`. The resolved directory must remain below the configured
study output root.

## `GET /runs/{run_id}/events`

Query parameters:

- `q`: corporation name or exact/partial ticker.
- `market`: `Y` or `K`.
- `attention_group`: `lower_attention`, `neutral_attention`, `higher_attention`, or `missing`.
- `outcome_state`: `observed`, `partial`, or `missing`.
- `sort`: one of the documented response fields.
- `order`: `asc` or `desc`.
- `offset`: non-negative integer.
- `limit`: 1–100.

Returns `{ items, total, offset, limit }` and never silently discards missing values.

## `GET /runs/{run_id}/events/{receipt_number}`

Returns one `EventObservation` including objective values, attention calculation, outcomes,
missing reasons, and hashes. Receipt number must contain exactly 14 digits.

## `GET /runs/{run_id}/lineage`

Returns provider-grouped coverage and optionally paginated snapshot records. Paths are relative to
the run raw directory and never absolute.

## Compatibility

- Breaking response changes require `/api/v2`.
- Additive optional fields may be introduced in v1.
- The client treats unknown enum strings as `unknown` and keeps the raw string available for
  diagnostics.
