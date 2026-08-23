# Implementation Plan: Korean Crowd Excess Data Feasibility

**Spec**: [spec.md](spec.md)

## Summary

Build an offline-first Python package with safe official API probes, strict CSV import
contracts, transparent prototype features, and chronological validation helpers. Live
credentials and real datasets are user-supplied; unit verification is fully mocked.

## Technical context

- Runtime: Python 3.12, Pydantic v2, httpx, pandas, NumPy.
- Integrations: OpenDART REST, NAVER API HUB Search Trend, official KRX CSV exports.
- Storage: local CSV files ignored by Git; no database in this milestone.
- Tooling: pytest and Ruff, managed with `uv`.
- Constraint: no automated collection from Naver user-post surfaces.

## Existing-system findings

- This is a greenfield repository.
- OpenDART documents `GET /api/list.json`, requires a 40-character key, limits a
  no-company search to three months, and returns structured status codes.
- KRX Data Marketplace exposes official price and investor-type trading downloads, but
  this milestone found no supported public REST contract to depend on.
- NAVER's terms prohibit collecting user IDs/posts with automated tools without prior
  permission.
- The new NAVER API HUB exposes Search Trend at
  `/search-trend/v1/search`; the legacy Developers service is in migration.

## Design

- `config.py`: secret-safe environment settings and local input paths.
- `capabilities.py`: normalized source status and report rendering.
- `providers/opendart.py`: disclosure metadata client with sanitized failures.
- `providers/naver_trend.py`: current API HUB client; labels ratios as relative.
- `providers/krx_csv.py`: canonical official-export import and source hashing.
- `providers/community_csv.py`: allowed-provenance, no-raw-ID import contract.
- `features/`: fundamental magnitude, robust community heat, and linear residual model.
- `validation.py`: strict chronological walk-forward indices.
- `cli.py`: offline-first capability report; network calls require `--live`.

## Requirement mapping

| Requirement | Design element | Verification |
|---|---|---|
| FR-001–003 | capability registry, safe settings, static policy block | capability/config tests |
| FR-004–006 | KRX/community loaders and SHA-256 lineage | CSV provider tests |
| FR-007–009 | feature modules and residual model | deterministic feature tests |
| FR-010 | walk-forward splitter | ordering/property tests |
| FR-011–012 | mocked HTTP and report renderer | full pytest + report snapshot assertions |

## Data and compatibility

All timestamps become UTC. Canonical CSV schemas are versioned in `examples/`. Source
files stay unchanged; normalized data is returned in memory. A future Parquet layer must
add an explicit schema version and migration rather than silently changing columns.

## Quality and operations

- Security/privacy: Pydantic `SecretStr`; no raw author IDs; no restricted crawler.
- Performance: CSV/pandas is sufficient for the feasibility sample; streaming is deferred.
- Observability: every capability result includes a checked-at time and limitation text.
- Rollback: remove the repository; no external state is mutated except optional API quota.

## Alternatives and decisions

| Decision | Choice | Reason | Rejected alternative |
|---|---|---|---|
| Community access | allowed CSV + official aggregate API | compliant and reproducible | Naver board scraping |
| KRX access | official manual CSV | stable source contract | undocumented web endpoint |
| First event | supply contract | self-contained numeric denominator | mixed event taxonomy |
| Heat recipe | fixed transparent weights | auditable preregistration | opaque LLM score |
| Excess model | explainable linear residual | tests the exact hypothesis | end-to-end return black box |
| Validation | chronological walk-forward | avoids future leakage | random split |

## Governance check

| Rule/gate | Result | Evidence or exception |
|---|---|---|
| No fabricated evidence | Pass | only test rows are synthetic |
| No automated restricted collection | Pass | policy source is static blocked |
| No trading/order scope | Pass | no broker dependency or order model |
| Secret safety | Pass target | settings and error sanitization tests |
| Time-aware research | Pass target | UTC validators and walk-forward tests |
