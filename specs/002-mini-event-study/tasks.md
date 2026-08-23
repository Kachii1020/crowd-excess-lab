# Tasks: 40-Disclosure Mini Event Study

## Dependencies

- T203 depends on T201–T202.
- T205 depends on T204.
- T207 depends on T203, T205, and T206.
- T208–T209 depend on T207.

## Specification and contracts

- [x] T201 Define `spec.md`, `plan.md`, `tasks.md`, research decisions, data model, and
  checklist — covers FR-201–FR-215.
- [x] T202 Add failing contract tests for OpenDART selection/document parsing, public-data
  pagination, snapshot lineage, attention windows, and event returns under `tests/`.

## US1 — Auditable disclosure sample

- [x] T203 [US1] Implement exact OpenDART pagination, candidate audit, source ZIP snapshots,
  and labelled contract parsing in `src/crowd_excess_lab/providers/` — covers FR-201–205.

## US2 — Official daily outcomes

- [x] T204 [US2] Add Public Data Portal secret settings and capability state in `config.py`,
  `capabilities.py`, and `.env.example` — covers FR-206.
- [x] T205 [US2] Implement stock and index clients in `providers/public_data.py` with strict
  schema parsing, pagination, snapshots, and sanitized errors — covers FR-204 and FR-206–207.

## US3 — Leakage-resistant features and outcomes

- [x] T206 [US3] Implement fixed NAVER attention windows and next-trading-day raw/benchmark
  outcomes in `features/attention.py` and `event_study.py` — covers FR-208–211.

## US4 — Reproducible pilot run

- [x] T207 [US4] Implement run orchestration, manifests, CSVs, and report generation in
  `study.py` — covers FR-212–213.
- [x] T208 [US4] Add `crowd-excess-study` CLI, quickstart instructions, and README entry —
  makes the live/resume workflow observable without exposing credentials.

## Cross-cutting verification

- [ ] T209 Run the full offline test/lint/format suite, execute the live OpenDART/NAVER stages,
  attempt the FSC stage, reconcile all artifacts, and record exact evidence.
  - Offline verification and live OpenDART/NAVER stages passed; 40/40 events and attention
    rows were persisted with complete snapshot lineage.
  - FSC stock/index completion remains blocked until `DATA_GO_KR_API_KEY` has both service
    permissions; the run is resumable without repeating completed stages.
