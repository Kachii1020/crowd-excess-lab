# Data Feasibility Report

**Status**: Real 40-event disclosure/attention pilot complete; price stage blocked on a
Public Data Portal key.
**Generated live report**: `DATA_FEASIBILITY_REPORT.local.md` (ignored by Git)

## Current evidence

| Source | Access design | Current conclusion | Research use |
|---|---|---|---|
| OpenDART | Official REST API + key | Live-validated; 40-event cohort built | Disclosure metadata and source documents |
| KRX prices | Official user-exported CSV | Manual export required | Returns and liquidity |
| KRX investor flow | Official user-exported CSV | Manual export required | Retail/foreign/institution controls |
| NAVER API HUB Search Trend | Official REST API + key | Live-validated; 40/40 event windows observed | Relative attention proxy only |
| FSC stock prices | Public Data Portal API + key | Key/permission required; current stage blocked | Daily stock outcomes |
| FSC market index | Public Data Portal API + key | Key/permission required; current stage blocked | KOSPI/KOSDAQ adjustment |
| Permitted community CSV | Allowed-method import | Dataset required | Direction, intensity, disagreement |
| Naver user posts | No collector | Blocked without prior permission | Not used |

## Live pilot evidence

- Window: 2026-05-13 through 2026-08-10.
- Audited OpenDART rows: 889; selected exact original KOSPI/KOSDAQ
  `단일판매ㆍ공급계약체결` events: 40.
- NAVER attention observations: 40/40. The fixed attention-excess median is 0.1475;
  groups contain 4 lower, 25 neutral, and 11 higher-attention events.
- Contract/revenue ratio median: 10.53%; range: 2.52%–298.90%.
- Raw snapshots retained and manifest-linked: 390/390, with zero missing files and zero
  SHA-256 mismatches at verification time.
- Stock price, decision day, and return coverage: 0/40 because no
  `DATA_GO_KR_API_KEY` is configured. No unofficial fallback or imputation was used.

## What is not yet established

- Price and index permission/coverage from the Public Data Portal services.
- A permitted community dataset large enough for event-time analysis.
- Any predictive or economically tradable Crowd Excess effect.

## Milestone exit decision

The disclosure and attention parts of the mini pilot have passed. Resume the existing run
after enabling the two FSC Public Data Portal services. Treat the study as complete only if
price coverage reaches the preregistered threshold; otherwise retain the observed missingness
as a feasibility result. KRX investor-flow work and permitted post-level community data remain
separate future inputs.

## Verification evidence

- Offline unit suite: 55 tests covering secrets, capabilities, API contracts, document
  parsing, pagination, sanitized failures, snapshot provenance, feature determinism,
  event returns, and chronological splits.
- Ruff lint and format checks: passed.
- Live OpenDART/NAVER collection: passed for the fixed 40-event cohort.
- Public Data Portal price/index stage: attempted and explicitly blocked because the key is
  absent.
- Real KRX exports and permitted post-level community data: not supplied.
