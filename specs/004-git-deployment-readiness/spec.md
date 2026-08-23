# Feature Specification: Git and Deployment Readiness

**Status**: Implemented and locally verified; release remains publication-gated
**Input**: Prepare the hackathon repository for Git and deployment.

## Problem and outcome

The application runs locally, but the repository has no first commit, no remote, no CI contract,
and no deploy-safe source of research data. The desired outcome is a reproducible repository that
can be pushed to GitHub and deployed as a Vercel preview without exposing credentials, local paths,
raw provider responses, or synthetic observations as product data.

## Scope

### In scope

- Reproducible Python, Node.js, pnpm, and lockfile contracts.
- Git hygiene and a read-only GitHub Actions verification workflow.
- Browser tests that use an explicitly synthetic, test-only run instead of ignored local data.
- A Vercel-compatible Vite build and read-only FastAPI function entrypoint.
- An explicit export step for a normalized public research snapshot.
- A release preflight that fails when secrets, raw provider data, or the public snapshot are missing.
- One local initial commit after all checks pass.

### Non-goals

- Creating or pushing a GitHub repository while GitHub authentication is unavailable.
- Publishing a preview or production deployment in this preparation step.
- Committing `.env`, raw OpenDART/NAVER responses, KRX files, or community observations.
- Automatically publishing the current normalized research run without user review.
- Adding live collection, background jobs, orders, or broker integration to the deployed app.

## User scenarios

### US1 — Clone and verify the repository (P1)

**Independent verification**: A clean checkout can install locked dependencies and pass backend,
frontend, and browser checks without API credentials or private research files.

1. **Given** a clean checkout, **When** CI runs, **Then** it uses pinned major runtimes and locked
   Python and pnpm dependencies.
2. **Given** no local study run, **When** browser tests run, **Then** they use only the clearly
   labelled synthetic E2E fixture.

### US2 — Prepare a Vercel preview (P1)

**Independent verification**: Configuration preflight and the production frontend build pass
without a linked Vercel project, while release preflight refuses an empty or unsafe deployment.

1. **Given** the repository configuration, **When** configuration preflight runs, **Then** the SPA
   build, Python entrypoint, routing contract, and ignore rules are valid.
2. **Given** no reviewed public snapshot, **When** release preflight runs, **Then** it fails with a
   concrete next step instead of deploying an empty or synthetic app.
3. **Given** a reviewed normalized run, **When** the export command is invoked with the explicit
   publication acknowledgement, **Then** it copies only required normalized artifacts and lineage
   metadata, never raw snapshots.

### US3 — Prevent accidental disclosure (P1)

**Independent verification**: The staged Git tree and deployment bundle contain no credential
values, `.env`, local absolute paths, or raw provider payloads.

1. **Given** local credentials and ignored research files, **When** the repository is staged,
   **Then** neither is included.
2. **Given** a public snapshot, **When** release preflight runs, **Then** it rejects raw directories,
   malformed artifacts, or credential-like content.

## Edge cases and failure behavior

- An invalid or expired GitHub login remains a visible external blocker; local Git work continues.
- An unlinked Vercel CLI is not treated as a code failure.
- A missing public snapshot blocks release deployment but not CI or local development.
- Public snapshot export refuses an existing destination unless replacement is explicitly requested.
- The deployed API remains read-only and returns an empty run list if invoked without a snapshot.
- Synthetic E2E fixtures are stored only below `tests/fixtures/` and are named as synthetic data.

## Requirements

- **FR-401**: Git MUST ignore credentials, virtual environments, build output, test artifacts, local
  research runs, and generated public snapshots by default.
- **FR-402**: CI MUST run offline-capable backend tests and frontend unit, lint, type, build, and
  browser checks with locked dependencies.
- **FR-403**: Browser CI MUST NOT depend on `data/processed/` or any live credential.
- **FR-404**: The Vercel entrypoint MUST expose only the existing read-only `/api/v1` application.
- **FR-405**: SPA routes MUST resolve to the frontend while `/api/*` resolves to FastAPI.
- **FR-406**: Public snapshot export MUST exclude raw snapshots, secret values, and absolute paths.
- **FR-407**: Release preflight MUST fail closed when no reviewed public snapshot is present.
- **FR-408**: The initial commit MUST contain only reviewed, non-ignored repository files.

## Success criteria

- **SC-401**: `git status --ignored` proves `.env`, private runs, raw data, and build output are ignored.
- **SC-402**: Backend tests/lint, frontend tests/lint/type/build, and Playwright pass from the final tree.
- **SC-403**: Configuration preflight exits zero and release preflight exits non-zero before data
  publication is approved.
- **SC-404**: Secret scanning of staged content reports zero credential values or private keys.
- **SC-405**: A local initial commit exists on `main`; no remote push or deployment has occurred.

## Assumptions and dependencies

- Vercel is the default hackathon preview target; GitHub will be the eventual remote.
- Node.js 24 and Python 3.12 are supported deployment runtimes.
- The current normalized run may be publicly shareable, but publication requires explicit user review.
- Vercel CLI 59.1.4 is installed locally; GitHub CLI authentication is currently invalid.
