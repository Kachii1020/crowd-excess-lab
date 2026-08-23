# Feature Specification: 40-Disclosure Mini Event Study

**Status**: Implemented; live price completion blocked by the missing Public Data Portal key
**Input**: Use the Financial Services Commission public-data price API to complete a
30–50 disclosure mini event study before KRX OpenAPI approval.

## Problem and outcome

The feasibility spike proved that OpenDART and NAVER Search Trend credentials work, but
it has not produced a fixed real-event sample or post-disclosure return labels. The next
outcome is a reproducible pilot dataset for 40 single-sales/supply-contract disclosures,
with objective contract magnitude, relative search attention, daily stock prices, and
conservative post-disclosure returns.

The pilot is descriptive, in-sample research. It must not be described as a validated
signal or a tradable strategy.

## Scope

### In scope

- Select 40 recent original KOSPI/KOSDAQ single-sales/supply-contract disclosures from
  the official OpenDART list API.
- Keep an audit row for every inspected disclosure, including corrections, subsidiary
  notices, malformed documents, and explicit inclusion/exclusion reasons.
- Download and hash official OpenDART source-document ZIP files, then parse contract
  amount, recent revenue, and the reported sales ratio from the labelled disclosure table.
- Collect a single NAVER Search Trend window per selected event and compute a transparent
  attention-excess measure from baseline and event subwindows in that same request.
- Collect official-origin FSC daily stock prices from the Public Data Portal and, when
  available under the same configured key, KOSPI/KOSDAQ index observations.
- Assign the first observed trading day after the OpenDART receipt date as the decision
  day because the official list response lacks an intraday timestamp.
- Produce raw and market-adjusted post-disclosure returns at fixed horizons, a joined CSV,
  an audit CSV, raw-source hashes, and a descriptive Markdown report.
- Resume an interrupted run from immutable raw snapshots without fabricating data.

### Non-goals

- Intraday event timing or execution-price claims.
- Investor-type flow analysis before an official dataset is available.
- Community-post collection or sentiment classification.
- Statistical significance, hyperparameter search, trading rules, or profitability claims.
- Quiet substitution of an unofficial price source when the public API is unavailable.

## User scenarios

### US1 — Build an auditable real disclosure sample (P1)

**Independent verification**: A live run produces exactly 40 selected disclosure rows and
an audit row for every inspected candidate, while tests parse representative source XML.

1. **Given** recent OpenDART exchange disclosures, **When** sample collection runs, **Then**
   it includes only original listed-company single-sales/supply-contract notices and records
   why every other inspected candidate was excluded.
2. **Given** a selected disclosure document, **When** it is parsed, **Then** the original ZIP
   is hashed and the contract amount, recent revenue, reported ratio, and computed ratio are
   retained without silently replacing missing values.
3. **Given** fewer than 40 eligible records in the requested range, **When** collection ends,
   **Then** the run is marked incomplete with the actual count and no synthetic rows.

### US2 — Collect official daily outcomes safely (P1)

**Independent verification**: Mocked official responses produce validated price/index rows,
and authentication or schema failures reveal no key and write no fabricated observations.

1. **Given** a configured Public Data Portal key, **When** prices are requested, **Then** the
   provider paginates, validates six-digit tickers and OHLCV bounds, preserves market and
   market-cap fields, and stores a hashed raw response.
2. **Given** no key or no permission, **When** a study run starts, **Then** disclosure and
   attention collection may complete but the price stage is explicitly `blocked`, not filled
   from another source.
3. **Given** index data are unavailable, **When** outcomes are calculated, **Then** raw returns
   remain available and abnormal returns stay missing with an explicit reason.

### US3 — Measure attention and event returns without look-ahead (P1)

**Independent verification**: Deterministic tests prove subwindow boundaries and that every
entry day is strictly after the disclosure receipt date.

1. **Given** one NAVER response spanning baseline and event dates, **When** attention excess
   is computed, **Then** the report retains coverage, baseline median, event mean, and the
   formula result; ratios from separate requests are never compared.
2. **Given** stock prices around a receipt date, **When** outcomes are calculated, **Then** the
   entry is the first available open strictly after the receipt date and horizons use the
   ordered trading-day sequence.
3. **Given** matching market-index observations, **When** a horizon return is calculated,
   **Then** abnormal return equals stock return minus same-market index return over the same
   entry/horizon dates.

### US4 — Inspect a restrained pilot report (P2)

**Independent verification**: The generated report states sample completion, missingness,
source lineage, and descriptive group summaries without using words that assert an edge.

1. **Given** a complete joined dataset, **When** reporting runs, **Then** it shows coverage and
   medians by preregistered attention-excess groups.
2. **Given** incomplete price, index, or trend coverage, **When** reporting runs, **Then** the
   missing counts and limitations remain visible.

## Edge cases and failure behavior

- Unicode variants of the middle dot in the Korean report title are normalized only for
  classification; original names remain unchanged.
- Corrections and subsidiary disclosures remain in the audit file and are not selected for
  the initial 40-event cohort.
- A labelled contract field containing `-`, an ambiguous unit, multiple values, or a
  non-numeric value causes an explicit parse failure for that candidate.
- The computed contract/revenue ratio is checked against the reported percentage with a
  documented rounding tolerance; disagreement is visible.
- NAVER baseline values that are all zero produce a missing excess with a reason, not infinity.
- Holidays and suspensions are represented by missing dates. The first actual stock row after
  the receipt date defines the decision day; prices are never forward-filled.
- Public Data Portal `endBasDt` is treated according to its documented exclusive boundary.
- API errors, quota errors, and malformed payloads are sanitized and never include credentials.

## Requirements

- **FR-201**: The system MUST target 40 selected events by default and allow only 30–50.
- **FR-202**: Every inspected disclosure MUST have a selected/excluded audit disposition.
- **FR-203**: Only original KOSPI/KOSDAQ `단일판매ㆍ공급계약체결` notices MAY enter the pilot.
- **FR-204**: OpenDART document bytes and every API response dataset MUST be saved with a
  SHA-256 hash and collection timestamp, without credential-bearing URLs or headers.
- **FR-205**: Contract amount, recent revenue, reported percentage, and computed percentage
  MUST remain separately inspectable.
- **FR-206**: Public Data Portal credentials MUST stay in local secret settings and sanitized
  errors MUST not expose them.
- **FR-207**: Price rows MUST preserve source date, ticker, market, OHLCV, trading value,
  listed shares, and market capitalization with no imputation.
- **FR-208**: The conservative decision day MUST be strictly after the disclosure receipt date.
- **FR-209**: Return horizons MUST be fixed at decision-day close and 1, 3, and 5 subsequent
  trading-day closes, all entered from the decision-day open.
- **FR-210**: Market adjustment MUST use the matching KOSPI/KOSDAQ index over identical dates;
  unavailable index observations MUST yield missing abnormal returns.
- **FR-211**: Attention excess MUST compare dates from one NAVER response using baseline
  `[-14,-3]` calendar days and event `[0,+2]` calendar days around the receipt date.
- **FR-212**: The run MUST write an event audit CSV, selected-event CSV, trend CSV, price CSV,
  outcome CSV, run manifest, and Markdown report under an ignored run directory.
- **FR-213**: The report MUST label all findings descriptive and in-sample and show missingness.
- **FR-214**: Automated tests MUST require no credentials or network.
- **FR-215**: The system MUST NOT add community scraping, orders, or broker integration.

## Key entities

- **DisclosureAuditRow**: Every inspected OpenDART disclosure and its cohort disposition.
- **SupplyContractEvent**: Selected disclosure plus parsed objective contract magnitude.
- **ApiSnapshot**: Credential-free raw response artifact with source, collection time, and hash.
- **PublicStockPriceRow**: Official-origin FSC daily stock-price observation.
- **MarketIndexRow**: Official-origin KOSPI/KOSDAQ daily index observation.
- **AttentionWindowResult**: Within-request baseline and event attention measurement.
- **MiniEventStudyRow**: One selected event joined to attention and fixed-horizon outcomes.
- **StudyRunManifest**: Run parameters, stage states, counts, artifacts, and source hashes.

## Success criteria

- **SC-201**: A credential-free test suite verifies selection, document parsing, pagination,
  price validation, attention windows, decision-day assignment, and return calculations.
- **SC-202**: With OpenDART and NAVER credentials, the run persists a real 40-event selection
  or explicitly reports that fewer were eligible.
- **SC-203**: With Public Data Portal permissions, at least 90% of selected events have an
  entry price and one-day outcome; lower coverage is reported rather than hidden.
- **SC-204**: Every persisted raw API artifact has a matching SHA-256 entry in the manifest.
- **SC-205**: No generated report, log, snapshot filename, or Git-tracked file contains a key.
- **SC-206**: Pytest and Ruff pass without network access.

## Assumptions and dependencies

- OpenDART and NAVER API HUB credentials are already configured and live-tested.
- The user must separately enable the Financial Services Commission stock-price API and,
  for benchmark adjustment, the market-index API in the Public Data Portal.
- Public Data Portal observations are end-of-day and update after the source business date;
  this pilot does not require real-time data.
- Receipt-date-only timing justifies next-trading-day-open entry, even though that sacrifices
  some signal immediacy.
