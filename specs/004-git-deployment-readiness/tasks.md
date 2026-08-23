# Tasks: Git and Deployment Readiness

## Dependencies

- T404 depends on T401–T403.
- T406 depends on T404–T405.
- T407 depends on every implementation and verification task.

## Specification and repository foundation

- [x] T401 Define deployment scope, publication boundary, requirements, and architecture under
  `specs/004-git-deployment-readiness/` — covers FR-401–408.
- [x] T402 Add runtime pins, repository attributes, ignore rules, and GitHub Actions CI — covers
  FR-401–403.

## CI-safe browser verification

- [x] T403 Add a clearly synthetic E2E run under `tests/fixtures/e2e_runs/` and point Playwright at
  it — covers FR-402–403.

## Vercel preview preparation

- [x] T404 Add `api/index.py`, `vercel.json`, and `.vercelignore` for same-origin Vite and FastAPI
  deployment — covers FR-404–405.
- [x] T405 Add a gated normalized snapshot exporter and two-mode deployment preflight with tests —
  covers FR-406–407.
- [x] T406 Document GitHub/Vercel setup, preview smoke tests, promotion, and rollback — covers
  FR-401, FR-405–408.

## Verification and Git

- [x] T407 Run all backend/frontend/browser/preflight checks, audit staged files, and create the
  initial local commit — covers SC-401–405.
