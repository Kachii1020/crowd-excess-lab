# Implementation Plan: Crowd Excess Research Workbench

**Spec**: [spec.md](spec.md)

## Summary

Add a read-only FastAPI adapter over immutable study outputs and a separately built React/Vite
client. Keep research code independent from HTTP and UI concerns. The client uses a versioned API,
feature-oriented modules, semantic tokens, URL-owned filters, and explicit blocked/missing states.

## Technical context

- Backend: Python 3.12, FastAPI, Pydantic v2, existing CSV/manifest models, pytest.
- Frontend: React with TypeScript on Vite, TanStack Query for server state, TanStack Table for the
  event grid, a small chart layer, Vitest/Testing Library, and Playwright.
- Storage: existing immutable raw snapshots and normalized run CSV/JSON files.
- Serving: separate dev servers; same-origin static serving may be added only for a packaged local
  release.
- Browser baseline: modern evergreen browsers; desktop first.

## Existing-system findings

- The current 40-event run already has a stable manifest, audited/selected events, attention rows,
  outcomes rows, and 390 raw-source lineage entries.
- Price and index CSV files legitimately contain headers with zero rows while the API key is absent.
- Study models currently live in `study.py`; the HTTP adapter can reuse them without changing the
  collection pipeline.
- There is no frontend or database, so route, token, state, and test conventions must be established
  before feature growth.
- Generated concepts and DESIGN.md candidates live outside app source under
  `outputs/design-research/crowd-excess-terminal/`.

## Design

### Backend boundaries

- `api/app.py`: FastAPI application factory, versioned router, safe exception mapping.
- `api/schemas.py`: stable response-only API contracts distinct from collection models.
- `api/repository.py`: validated run discovery, CSV joins, source aggregation, and in-memory cache
  keyed by manifest modification time.
- `api/routes/`: health, runs, events, and lineage endpoints.
- No endpoint mutates a run or receives a secret.

### Frontend boundaries

- `web/src/app/`: providers, router, route-level error/loading shells.
- `web/src/api/`: generated-or-hand-checked API types, fetch client, query keys.
- `web/src/features/overview/`, `events/`, `research/`, `lineage/`, `settings/`: independently
  testable vertical slices.
- `web/src/components/`: data table primitives, evidence drawer, chart frame, status, empty state,
  command bar, app shell.
- `web/src/styles/`: semantic tokens, selected theme values, density, reset, and component layers.

### Data flow

```text
OpenDART/NAVER/FSC collectors
  -> immutable run artifacts
  -> StudyRepository (validation + join + safe projection)
  -> /api/v1 read-only JSON
  -> TanStack Query cache
  -> URL-filtered feature screens
```

### Error and recovery behavior

- Missing root or run: safe 404/empty state.
- Invalid/corrupt artifact: per-run `unreadable` result with sanitized detail; other runs remain
  browseable.
- Frontend fetch failure: persistent retry action and last selected route; no fabricated fallback.
- Blocked stage: render blocked state and the required external action, not an error chart.

## Interface contracts

See [contracts/http-api.md](contracts/http-api.md). API schemas are versioned independently from
the research manifest and never expose storage paths.

## Requirement mapping

| Requirement | Design element | Verification |
|---|---|---|
| FR-301–305 | versioned GET router, repository path guard, response schemas | API contract/security tests |
| FR-306–307 | typed client, TanStack Query, URL-owned filters | frontend route/query tests |
| FR-308–309 | accessible table and chart frame | unit + Playwright + accessibility audit |
| FR-310–311 | semantic token layer and responsive shell | theme contract + viewport screenshots |
| FR-312–314 | nav/action scope and disclaimer | content assertions + repository scan |
| FR-315 | real-run adapter | local operational verification |

## Data and compatibility

- Manifest schema v1 is accepted. Unknown future manifest fields are ignored by Pydantic; unknown
  schema versions are reported as unsupported instead of guessed.
- API v1 uses ISO dates/timestamps and JSON numbers or null. Percent fields are named explicitly as
  ratios or percentage points.
- The frontend never depends on CSV column order.
- A future database may implement the same repository protocol and API without changing screens.

## Quality and operations

- Security/privacy: strict run ID grammar and root containment; no secrets or absolute paths;
  read-only routes; same-origin default.
- Accessibility: semantic headings/landmarks, roving or grid keyboard behavior, visible focus,
  reduced motion, chart summaries, contrast gates.
- Performance: manifest-mtime cache; route-level code splitting; table virtualization only after
  measured need; current 40-event cohort renders without it.
- Observability: request ID, duration, response status, run ID, and artifact state; never log query
  credentials because no credential endpoint exists.
- Rollout: local dev first. A later packaged release may mount built assets under the API process.
- Rollback: remove `api/` and `web/`; research pipeline artifacts remain unchanged.

## Alternatives and decisions

| Decision | Choice | Reason | Rejected alternative |
|---|---|---|---|
| Client | React/Vite SPA | rich desktop interaction, fast local iteration, framework-light | Next.js SSR without a public web requirement |
| API | FastAPI adapter | reuses Python models and produces OpenAPI | browser reading CSV files directly |
| Storage now | immutable run files | already auditable and sufficient for 40 events | premature database migration |
| Server state | TanStack Query | explicit loading/error/cache behavior | ad-hoc component fetches |
| Table | semantic table first | 40 rows need accessibility more than virtualization | canvas grid |
| Themes | semantic role tokens | final palette remains maintainable | hard-coded component colors |
| Default concept | B layout + A palette | explicitly selected for the hackathon | pure B dark theme or pure A layout |
| Product language | English-only UI | hackathon judging and broader legibility | mixed Korean/English interface |

## Governance check

| Rule/gate | Result | Evidence or exception |
|---|---|---|
| Research-only, no orders | Pass target | non-goals + GET-only API |
| No fabricated observations | Pass target | repository reads persisted rows only |
| Source lineage visible | Pass target | lineage endpoint and inspector |
| No restricted collection | Pass | UI adds no collector |
| No secrets | Pass target | schema/path/security tests |
| Chronological semantics | Pass target | UI exposes existing fixed horizons only |
