# Tasks: Korean Crowd Excess Data Feasibility

## Dependencies

- T003 depends on T001 and T002.
- T005–T008 depend on T003.
- T009 depends on T005–T008.
- T010 depends on all implementation tasks.

## Setup and shared foundation

- [x] T001 Define `spec.md`, `plan.md`, data model, research decisions, and checklist —
  covers FR-001–FR-012 through reviewable contracts.
- [x] T002 Create `AGENTS.md`, `pyproject.toml`, `.env.example`, `.gitignore`, and README —
  establishes secret, data, tooling, and scope governance.
- [x] T003 Implement settings, domain models, capability statuses, and safe reporting in
  `src/crowd_excess_lab/` — verifies FR-001 and FR-003.

## US1 — Inspect data capability honestly

- [x] T004 [US1] Add mocked capability/report tests in `tests/test_capabilities.py` —
  covers FR-001–FR-003 and FR-011–FR-012.
- [x] T005 [US1] Implement OpenDART and NAVER API HUB clients plus static source-policy
  results in `providers/` — pass T004.
- [x] T006 [US1] Implement `cli.py` and `scripts/check_data_access.py` — produce an offline
  six-source report and optional safe live probes.

## US2 — Validate research inputs

- [x] T007 [US2] Add canonical CSV examples and provider tests — covers FR-004–FR-006.
- [x] T008 [US2] Implement KRX and permitted-community CSV loaders in `providers/` —
  retain hashes, reject unsafe provenance, and avoid imputation.

## US3 — Quantify the hypothesis

- [x] T009 [US3] Add feature/model/split tests and implement `features/` plus
  `validation.py` — covers FR-007–FR-010.

## Cross-cutting verification

- [x] T010 Run pytest and Ruff, generate an offline feasibility report, reconcile all
  artifacts, and record exact commands in `quickstart.md`.
