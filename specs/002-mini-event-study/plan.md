# Implementation Plan: 40-Disclosure Mini Event Study

**Spec**: [spec.md](spec.md)

## Summary

Extend the offline-first package with a resumable study pipeline. It will select and audit
real OpenDART events, parse objective values from hashed official source documents, measure
within-request NAVER attention excess, obtain official-origin FSC stock/index rows, and
calculate conservative next-trading-day event outcomes. Generated research data stays outside
Git and reports remain explicitly descriptive.

## Technical context

- Runtime/tooling: Python 3.12, Pydantic v2, httpx, pandas, NumPy, pytest, Ruff, `uv`.
- Existing integrations: OpenDART list API and NAVER API HUB Search Trend.
- New integrations: OpenDART document ZIP, FSC stock-price and market-index APIs on
  `apis.data.go.kr`.
- Storage: immutable raw responses plus normalized CSV/JSON manifest in an ignored run folder.
- Constraints: no unofficial fallback; no intraday timestamp; no community-post collection.

## Existing-system findings

- The current OpenDART client reads only the first list page and its broad title match also
  catches unrelated `유동성공급계약` notices.
- Real OpenDART source documents are ZIP files containing XML tables whose labelled rows expose
  `계약금액(원)`, `최근매출액(원)`, and `매출액대비(%)`.
- The FSC stock service is a separate official-origin API requiring a Public Data Portal key;
  the current environment has no such key configured.
- Existing price models cover core OHLCV but not market, listed shares, or market cap.
- NAVER ratios are normalized within one request, so event/baseline comparison must share a
  single query window.

## Design

- `providers/opendart.py`: add exact report classification, list pagination parameters, and a
  source-document download method returning bytes only after ZIP validation.
- `providers/opendart_document.py`: parse labelled table rows and return audited contract fields.
- `providers/public_data.py`: sanitize/paginate stock and index JSON, expose capability probing,
  and preserve source fields.
- `snapshot.py`: atomically write credential-free response bytes and return SHA-256 lineage.
- `features/attention.py`: calculate fixed-window coverage and attention excess.
- `event_study.py`: select a strictly post-receipt decision day and calculate stock/index
  horizon returns without filling missing dates.
- `study.py`: stage orchestration, resume behavior, CSV/manifest/report outputs, and stage status.
- `study_cli.py`: explicit live command with target/date/output arguments and safe progress text.

## Requirement mapping

| Requirement | Design element | Verification |
|---|---|---|
| FR-201–203 | exact selector and audit disposition | selector tests + real audit count |
| FR-204–207 | snapshot writer, document/public-data providers | hash, schema, secret tests |
| FR-208–210 | event-study calculator | deterministic date/return tests |
| FR-211 | attention feature | boundary and zero-baseline tests |
| FR-212–213 | run writer and Markdown renderer | integration test with mocked clients |
| FR-214–215 | dependency-injected HTTP and scope governance | full offline suite + repository scan |

## Data and compatibility

- Existing canonical KRX CSV models remain unchanged. New FSC models are distinct because their
  source fields and lineage differ.
- Raw snapshots are immutable per run. Re-running with the same run directory reuses valid
  snapshots and never silently overwrites a different hash.
- Processed CSV headers are versioned in [data-model.md](data-model.md). Schema changes require a
  new run manifest schema version.

## Quality and operations

- Security/privacy: `SecretStr`; keys only in request construction; errors exclude URLs/headers.
- Integrity: SHA-256 for every source response; audit exclusions; no imputation or fake rows.
- Performance: bounded target (30–50), one request per event/source window, controlled pagination.
- Observability: stage states, counts, missingness, snapshot hashes, and sanitized failure reasons.
- Rollback: remove the generated ignored run directory; no remote mutations beyond API quota use.

## Alternatives and decisions

| Decision | Choice | Reason | Rejected alternative |
|---|---|---|---|
| Pilot size | 40 by default, bounded 30–50 | matches requested size and stays reviewable | unbounded backfill |
| Event timing | next observed trading-day open | no unsupported intraday assumption | receipt-date close |
| Event family | exact original contract notices | homogeneous numeric denominator | broad title substring |
| Source values | parse labelled official XML rows | auditable objective magnitude | LLM extraction |
| Price bridge | FSC Public Data Portal | official-origin and auto-approved development access | unofficial scraper |
| Benchmark | KOSPI/KOSDAQ index when permitted | same-market descriptive adjustment | silently assume zero market return |
| Attention | one request, fixed subwindows | ratios remain comparable | separately normalized queries |
| Analysis | fixed horizons and descriptive groups | avoids pilot overfitting | parameter search |

## Governance check

| Rule/gate | Result | Evidence or exception |
|---|---|---|
| No fabricated evidence | Pass target | incomplete stages remain incomplete |
| Source lineage | Pass target | raw bytes + SHA-256 manifest entries |
| No look-ahead | Pass target | decision day strictly after receipt date |
| No restricted collection | Pass | NAVER trend only; no user posts |
| No trading scope | Pass | descriptive returns only |
| Secret safety | Pass target | sanitized provider and snapshot tests |
