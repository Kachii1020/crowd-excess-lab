# Data Model: Crowd Excess Research Workbench

## ResearchRunSummary

- `run_id`: timestamp identifier.
- `schema_version`: source manifest version.
- `created_at`, `updated_at`: UTC timestamps.
- `disclosure_start_date`, `disclosure_end_date`.
- `target_events`.
- `stages`: named stage states.
- `counts`: persisted exact counts.
- `interpretation`: research limitation.
- `readable`: whether required normalized artifacts validated.

## EventObservation

- Identity: `receipt_number`, `ticker`, `corporation_name`, `market_class`, `received_date`.
- Objective magnitude: contract amount, recent revenue, reported/computed ratio, difference.
- Attention: baseline median, event mean, excess, group, coverage, missing reason.
- Timing: decision date.
- Outcomes: raw, market, and abnormal H0/H1/H3/H5, each nullable.
- Missingness: price and index reasons.
- Evidence: OpenDART document and attention snapshot hashes.

The API must not round numeric fields. Formatting belongs to the client.

## SourceGroupSummary

- `source`: provider/source name.
- `snapshot_count`.
- `byte_count`.
- `first_collected_at`, `last_collected_at`.
- `retained_count`, `missing_count`.

## SourceSnapshotView

- `source`.
- `relative_path`: path relative to the run's raw root only.
- `sha256`.
- `byte_count`.
- `collected_at`.
- `retained`.

## WorkbenchPreferences

Stored only in browser local storage and not sent to the research API:

- `theme`: selected visual direction.
- `density`: comfortable or compact.
- `left_nav_collapsed`.
- `evidence_panel_width`.

No research result or credential may be stored in this preference object.
