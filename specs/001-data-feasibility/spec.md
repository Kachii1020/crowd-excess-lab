# Feature Specification: Korean Crowd Excess Data Feasibility

**Status**: Implemented
**Input**: Test whether community reaction that is excessive relative to an objective
corporate-event magnitude can become a measurable Korean-equity research signal.

## Problem and outcome

The motivating observation is subjective but falsifiable: Korean investing communities
sometimes appear to react more strongly than the underlying numerical change warrants.
Before building a model, the project must establish whether timestamped event, market,
attention, and permitted community data can be joined without look-ahead bias.

The outcome of this milestone is a reproducible capability report, validated input
contracts, and transparent prototype measurements. It is not a trading strategy.

## Scope

### In scope

- Official OpenDART disclosure-list access and supply-contract report discovery.
- Official KRX CSV import for daily prices and investor flows.
- Current NAVER API HUB Search Trend access as an attention-only proxy.
- A canonical, privacy-minimised CSV contract for permitted community observations.
- A source-policy registry that marks prohibited automated collection explicitly.
- Supply-contract magnitude, community heat, and residual Crowd Excess prototypes.
- Chronological walk-forward split generation.
- Mocked unit tests that require no credentials or network.

### Non-goals

- Naver Finance message-board scraping.
- Automated sentiment inference from copyrighted post text.
- Broad coverage of every disclosure type.
- A return-prediction claim, backtest result, portfolio, broker, or order submission.
- Parameter optimisation using future data.

## User scenarios

### US1 — Inspect data capability honestly (P1)

**Independent verification**: The capability command reports `available`,
`credential_required`, `manual_export_required`, or `blocked_by_policy` for every source
without exposing secrets.

1. **Given** no `.env` and no local files, **When** the command runs offline, **Then** it
   completes and identifies every missing credential or export.
2. **Given** a mocked successful API, **When** a live probe runs, **Then** the result
   includes source, access method, timestamp, and semantic limitation.
3. **Given** a source whose terms prohibit automated collection, **When** capabilities
   are reported, **Then** it is marked `blocked_by_policy` and no request is attempted.

### US2 — Validate research inputs (P1)

**Independent verification**: Canonical example CSVs load successfully and malformed,
naive-time, or disallowed-provenance rows fail with actionable errors.

1. **Given** an official KRX export normalized to the documented columns, **When** it is
   loaded, **Then** numeric values, six-digit tickers, dates, and source hashes are kept.
2. **Given** a permitted community CSV, **When** it is loaded, **Then** timestamps are
   converted to UTC and no raw user identifier is required.
3. **Given** `scraped_without_permission`, **When** a community row is loaded, **Then**
   validation rejects it.

### US3 — Quantify the hypothesis without claiming validation (P2)

**Independent verification**: Deterministic tests show the same inputs produce the same
fundamental magnitude, heat components, Crowd Excess residual, and time splits.

1. **Given** contract amount and prior annual revenue, **When** shock magnitude is
   computed, **Then** the ratio and log-scaled magnitude are returned with denominators.
2. **Given** event-window and baseline community aggregates, **When** heat is computed,
   **Then** every component and preregistered weight is inspectable.
3. **Given** historical event rows, **When** the baseline model is fitted, **Then** Crowd
   Excess equals actual heat minus predicted normal heat.
4. **Given** dated events, **When** validation splits are built, **Then** every training
   row precedes every test row.

## Edge cases and failure behavior

- OpenDART status `013` means a valid empty result, not fabricated data.
- API authentication, quota, maintenance, and schema errors are sanitized capability
  results and never include secret-bearing URLs or headers.
- Corrected disclosures remain distinct records through their receipt numbers and names.
- Zero or negative revenue cannot produce a supply-contract magnitude.
- A community baseline with zero dispersion cannot silently create an infinite z-score.
- Duplicate observations remain measurable through a duplicate ratio.
- Missing price or investor-flow days remain missing; they are not forward-filled here.

## Requirements

- **FR-001**: The system MUST classify access for OpenDART, KRX price, KRX investor flow,
  NAVER API HUB Search Trend, permitted community CSV, and Naver user posts.
- **FR-002**: The system MUST never automatically collect Naver user posts without
  documented permission.
- **FR-003**: The system MUST keep secrets out of logs, reports, fixtures, and Git.
- **FR-004**: Every imported dataset MUST expose source lineage and a SHA-256 file hash.
- **FR-005**: Community observations MUST have timezone-aware timestamps, hashed IDs,
  derived labels, and an allowed collection basis.
- **FR-006**: KRX price and investor-flow inputs MUST be type-checked without silent
  forward filling.
- **FR-007**: Supply-contract shock magnitude MUST retain its numerator and denominator.
- **FR-008**: Community heat MUST expose component scores and fixed starting weights.
- **FR-009**: Crowd Excess MUST be calculated as actual heat minus baseline-predicted heat.
- **FR-010**: Validation utilities MUST use chronological splits only.
- **FR-011**: Tests MUST run without live credentials or network.
- **FR-012**: Reports MUST distinguish measured facts, proxies, blocked sources, and
  unvalidated hypotheses.

## Key entities

- **DisclosureRecord**: OpenDART receipt metadata and disclosure timing.
- **KrxPriceRow**: One official daily OHLCV observation with lineage.
- **InvestorFlowRow**: Daily retail, foreign, and institutional net values with lineage.
- **CommunityObservation**: Privacy-minimised, permitted post-level derived observation.
- **TrendPoint**: Relative NAVER search-interest ratio for a keyword group and period.
- **CapabilityResult**: Evidence about whether and how a source can be used.
- **CommunityHeat**: Transparent component measurements for an event window.
- **CrowdExcessResult**: Actual heat, normal predicted heat, and their residual.

## Success criteria

- **SC-001**: All automated tests and Ruff checks pass without credentials.
- **SC-002**: An offline capability report covers all six declared sources.
- **SC-003**: Example KRX and community CSVs pass their validators.
- **SC-004**: Disallowed community provenance and naive timestamps fail validation.
- **SC-005**: The same feature input produces byte-for-byte equivalent JSON output.
- **SC-006**: No code path can submit a trade or scrape Naver user content.

## Assumptions and dependencies

- The user will obtain OpenDART and NAVER API HUB credentials for live checks.
- KRX data starts with manually downloaded official exports because this milestone does
  not rely on an undocumented private endpoint.
- NAVER search trend is an attention proxy only; it cannot replace sentiment labels.
- The first real sample will use single sales/supply contract disclosures, then expand
  only after the measurement contract is stable.
