# Implementation Plan: Git and Deployment Readiness

**Spec**: [spec.md](spec.md)

## Summary

Keep local research collection private, make verification independent of that private state, and
prepare a single Vercel project that builds the Vite client and exposes the existing FastAPI app as
a Python function. Require a reviewed normalized snapshot before any release deployment.

## Technical context

- Runtime: Python 3.12, Node.js 24.x, pnpm 11.19.0.
- Backend: FastAPI created by `crowd_excess_lab.api.app.create_app`.
- Frontend: React 19, TypeScript, Vite 8.
- Data: immutable file runs; local runs remain Git-ignored.
- Verification: pytest, Ruff, Vitest, Oxlint, TypeScript, Vite build, Playwright.

## Existing-system findings

- The repository is on `main`, has no commit, and has no remote.
- `.env` and `data/processed/*` are correctly ignored.
- Current E2E tests depend on the ignored real 40-event run and therefore are not CI-safe.
- The browser calls same-origin `/api/v1`, which is compatible with a same-domain Vercel function.
- GitHub CLI is installed but its stored token is invalid; Vercel CLI 59.1.4 is installed.

## Design

- Add repository runtime pins, formatting attributes, and a GitHub Actions CI workflow.
- Commit one explicit synthetic E2E study run under `tests/fixtures/e2e_runs/`.
- Point Playwright's API server to the test-only fixture.
- Export the production ASGI application from `api/index.py`; package source and a future reviewed
  `deploy/research_snapshot/` directory with the function.
- Build `web/` to `web/dist` and route SPA pages separately from `/api/*`.
- Keep `deploy/research_snapshot/` ignored by default. A deliberate export command and force-add are
  required after the user reviews the normalized rows.
- Use two preflight modes: `configuration` for CI and `release` for a real preview.

## Requirement mapping

| Requirement | Design element | Verification |
|---|---|---|
| FR-401, FR-408 | `.gitignore`, `.vercelignore`, staged-tree audit | `git check-ignore`, staged scan |
| FR-402, FR-403 | `.github/workflows/ci.yml`, E2E fixture | local full suite, workflow syntax review |
| FR-404, FR-405 | `api/index.py`, `vercel.json` | API import test, Vercel config preflight |
| FR-406 | `scripts/export_public_snapshot.py` | exporter unit tests and raw-path rejection |
| FR-407 | `scripts/deploy_preflight.py` | configuration pass / release fail-before-export |

## Data and compatibility

No research schema changes. Exported public snapshots retain the existing manifest and normalized
CSV contracts. Raw provider files are intentionally absent, so deployed lineage correctly marks
those source files as not retained in the public bundle.

## Quality and operations

- Security/privacy: no client secrets in Vercel; no live API credentials required; deploy is read-only.
- Performance: the API function includes only project source and the reviewed normalized snapshot.
- Observability: `/api/v1/health` remains the smoke-test endpoint.
- Rollout: preview deployment first; promote only after API and deep-link smoke checks.
- Rollback: Vercel deployment rollback or redeploy the previous Git commit.

## Alternatives and decisions

| Decision | Choice | Reason | Rejected alternative |
|---|---|---|---|
| Preview host | Vercel | Existing CLI, same-origin Vite + Python support | Add a database or new host now |
| Demo data | Reviewed normalized snapshot | Real, small, transparent | Synthetic product data or live build-time collection |
| Raw evidence | Do not publish | Minimizes licensing/privacy risk | Commit all provider responses |
| CI browser data | Synthetic test fixture | Reproducible and explicitly test-only | Depend on ignored local 40-event run |

## Governance check

| Rule/gate | Result | Evidence or exception |
|---|---|---|
| No fabricated product observations | Pass | Synthetic rows are isolated to `tests/fixtures/` |
| No secrets in Git | Pass target | Ignore rules plus staged secret scan |
| Preserve lineage | Pass | Snapshot metadata retained; missing raw files remain visible |
| No orders or profit claims | Pass | Existing read-only API and interface are unchanged |
