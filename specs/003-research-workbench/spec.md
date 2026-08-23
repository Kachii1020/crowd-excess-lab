# Feature Specification: Crowd Excess Research Workbench

**Status**: Implemented and verified
**Input**: Build the long-lived front/backend frame now, with a clean Bloomberg-like research
interface and no order functionality.

## Problem and outcome

The repository can collect and normalize disclosure, attention, price, and lineage artifacts,
but a researcher must inspect CSV and Markdown files manually. The desired outcome is a
desktop-first research workbench that makes event selection, measurement, missingness, outcomes,
and source evidence inspectable without turning the project into a trading terminal.

The architecture must survive additional event families and datasets without forcing a frontend
rewrite, while the first delivered slice remains read-only and limited to the existing
single-sales/supply-contract study.

## Scope

### In scope

- A versioned, read-only HTTP API over local study-run artifacts.
- A React/TypeScript desktop-first application shell and typed data client.
- Overview, Event Monitor, Event Evidence, Research Matrix, Data Lineage, and Settings/Capability
  information architecture.
- URL-persisted filters, keyboard navigation, loading/error/empty/blocked states, responsive
  behavior, and accessible data representations.
- Semantic design tokens with one selected default theme and the ability to swap a theme without
  rewriting components.
- Use of actual run artifacts when present and explicit no-data states otherwise.
- Automated backend, frontend, and browser-level verification.

### Non-goals

- Order entry, broker integration, portfolio positions, or trade recommendations.
- Real-time quotes, websocket streaming, or intraday event timing.
- Triggering live data collection or revealing/editing API keys from the browser.
- Community-post scraping or raw user content.
- Claiming predictive power, causality, profitability, or production readiness.
- Multi-user authentication in the local research milestone.

## User scenarios

### US1 — Understand research readiness (P1)

**Independent verification**: Opening the workbench shows the latest run, stage status, data
coverage, fixed research limitations, and next blocker without opening a file.

1. **Given** a completed or partial run, **When** the overview loads, **Then** it reports exact
   selected, attention, price, outcome, and lineage coverage.
2. **Given** a blocked price stage, **When** the overview loads, **Then** the UI says outcomes are
   unavailable and never renders synthetic return values.
3. **Given** no run, **When** the workbench loads, **Then** it provides a safe empty state and the
   local command needed to create a run without exposing secrets.

### US2 — Scan and inspect events (P1)

**Independent verification**: A user can filter, sort, keyboard-select, deep-link, and inspect all
40 current events while retaining exact reported/computed values and missingness.

1. **Given** a run with events, **When** filters or sort order change, **Then** URL state and the
   visible result count update together.
2. **Given** a selected row, **When** the evidence panel opens, **Then** it shows disclosure
   magnitude, attention calculation, available returns, missing reasons, and source hashes.
3. **Given** keyboard-only use, **When** the user traverses the table and inspector, **Then** focus
   stays visible and no required action depends on hover.

### US3 — Explore fixed research comparisons (P1)

**Independent verification**: The Research screen presents only preregistered variables and
horizons and pairs every visualization with an exact textual summary.

1. **Given** observed outcomes, **When** a horizon is selected, **Then** the plot and table use
   H0/H1/H3/H5 fields already present in the study output.
2. **Given** missing price or index data, **When** the screen loads, **Then** unavailable series
   remain absent and their reasons stay visible.
3. **Given** attention groups, **When** comparisons are viewed, **Then** group sizes and observed
   counts appear beside descriptive medians.

### US4 — Audit sources and run lineage (P1)

**Independent verification**: Every API-exposed aggregate can be traced to a run artifact and raw
snapshot entry without displaying a secret or credential-bearing request.

1. **Given** a run manifest, **When** Data Lineage opens, **Then** sources are grouped by provider
   with counts, collection time range, hashes, and retained-file state.
2. **Given** an invalid run ID or path-like input, **When** the API receives it, **Then** it returns
   a safe not-found response and never reads outside the configured study root.

### US5 — Work across screen sizes and preferences (P2)

**Independent verification**: Desktop supports the full workspace; narrower widths preserve core
research access without overlapping controls or hiding state.

1. **Given** a 1280–1600 px viewport, **When** an event is selected, **Then** navigation, table,
   evidence, and provenance can remain visible together.
2. **Given** a tablet viewport, **When** an event is selected, **Then** evidence moves into a
   full-width strip below the table and analysis panes.
3. **Given** a mobile viewport, **When** the app loads, **Then** it provides a read-only run summary
   and event list rather than compressing the full matrix.
4. **Given** reduced-motion or keyboard preferences, **When** the UI renders, **Then** motion and
   focus behavior respect platform accessibility settings.

## Edge cases and failure behavior

- Partial, interrupted, and old manifest schema versions remain visible and are labelled.
- Empty CSV files with headers are valid blocked-stage artifacts, not corrupt data.
- Duplicate corporation names are disambiguated by ticker and receipt number.
- Alphanumeric or missing raw ticker values may appear in the audit but cannot enter the selected
  price-event endpoint.
- Monetary amounts and high-precision source ratios use decimal strings so JavaScript cannot lose
  precision; derived return/attention values use JSON numbers. Presentation formatting never
  alters either representation.
- Unavailable abnormal returns must not be inferred from raw returns.
- Unknown enum values degrade to an explicit `unknown` badge rather than breaking the page.
- Hashes may be shortened visually but copying exposes the complete hash.
- Table virtualization must preserve screen-reader access and keyboard row selection.
- API responses never contain local absolute paths, `.env` values, or provider credentials.

## Requirements

- **FR-301**: The backend MUST expose only versioned `GET /api/v1` research endpoints in this
  milestone.
- **FR-302**: Run identifiers MUST match the timestamp format and resolve inside the configured
  study root.
- **FR-303**: Event responses MUST retain receipt number, ticker, market, dates, objective
  magnitude, reported/computed ratio, attention measurement, fixed-horizon outcomes, missing
  reasons, and source hashes when available.
- **FR-304**: The API MUST distinguish observed, missing, blocked, incomplete, and failed states.
- **FR-305**: The API and UI MUST NOT expose secret values, credential-bearing URLs, or absolute
  filesystem paths.
- **FR-306**: The frontend MUST use a typed API boundary and MUST NOT parse research CSVs directly.
- **FR-307**: Filter and selection state MUST be deep-linkable in the browser URL.
- **FR-308**: Primary data tables MUST support keyboard navigation, visible focus, sortable column
  semantics, and tabular numerals.
- **FR-309**: Every chart MUST have an accessible text summary and explicit observed/missing count.
- **FR-310**: Theme colors, typography, spacing, radii, and data-series colors MUST be semantic
  tokens rather than hard-coded component values.
- **FR-311**: Desktop, tablet, and mobile layouts MUST follow the behavior in US5.
- **FR-312**: The default interface MUST never contain buy/sell, position, P&L, or order actions.
- **FR-313**: Tests MUST run offline using temporary or checked-in fixtures clearly marked as test
  data.
- **FR-314**: The browser UI MUST preserve the project disclaimer that results are descriptive and
  in-sample.
- **FR-315**: A selected real run MUST display current 40-event and lineage counts exactly as
  persisted, without invented completion percentages.
- **FR-316**: All user-visible application copy MUST be English for the hackathon presentation.
- **FR-317**: The primary Event Monitor MUST use a desktop three-pane layout with the event table,
  attention/outcome analysis, and selected-event evidence visible together when space permits.
- **FR-318**: The selected visual system MUST combine concept B's terminal information architecture
  with concept A's light institutional palette as defined in the repository `DESIGN.md`.

## Key entities

- **ResearchRun**: One immutable study output directory and its stage/count summary.
- **EventObservation**: One selected disclosure joined to attention and available outcomes.
- **EventEvidence**: Objective fields, computation inputs, missing reasons, and source hashes for an
  event.
- **SourceSnapshotSummary**: Provider-grouped lineage counts and collection-time range.
- **CapabilityState**: Whether a source is available, configured, blocked, or missing.
- **WorkbenchPreferences**: Local-only visual theme, density, and panel-layout preferences.

## Success criteria

- **SC-301**: The latest real run and all 40 selected events are accessible through the API.
- **SC-302**: No API response or rendered screen includes an API key or local absolute path.
- **SC-303**: Event filters, sorting, selection, and deep links pass automated browser tests.
- **SC-304**: Desktop 1440×900, tablet 1024×768, and mobile 390×844 have no horizontal page
  overflow or covered focus targets.
- **SC-305**: Automated accessibility checks find no critical violations in primary screens.
- **SC-306**: Backend pytest, frontend unit/type/lint/build checks, and Playwright smoke tests pass.
- **SC-307**: A theme can be switched by changing token values without editing feature components.

## Assumptions and dependencies

- The first deployment is a local, single-user web application.
- Python remains the research and API runtime; React/TypeScript is the interaction layer.
- The existing ignored run directory remains the source of truth until a later explicit database
  migration.
- Visual direction is selected: concept B layout with concept A light institutional palette.
- English is the canonical product language for the hackathon build.
- Public Data Portal price access remains an external dependency and does not block workbench
  architecture or missing-state implementation.
