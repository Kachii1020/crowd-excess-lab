# Research Workbench Handoff

## What exists now

The workbench is a local, read-only projection of immutable mini-event-study runs. The Python API
is the sole boundary between research files and the browser. The client never parses CSV files and
never receives an absolute local path or secret value.

| Concern | Stable location | Extension rule |
|---|---|---|
| API response contracts | `src/crowd_excess_lab/api/schemas.py` | Add optional v1 fields; use v2 for breaking changes. |
| Artifact projection | `src/crowd_excess_lab/api/repository.py` | Validate every path below the configured run root. |
| HTTP routes | `src/crowd_excess_lab/api/app.py` | Keep this milestone GET-only. |
| Browser schemas | `web/src/api/schemas.ts` | Parse every response before it reaches a feature. |
| Query cache | `web/src/api/queries.ts` | Put new server reads behind stable query keys. |
| Feature screens | `web/src/pages/` | Consume typed API values; do not read research files. |
| Shared UI | `web/src/components/` | Keep domain-free primitives reusable across event families. |
| Visual tokens | `web/src/index.css` | Theme changes happen here, not inside feature components. |

## Current routes

- `/` — redirects to the primary Event Monitor.
- `/events` — three-pane, URL-persisted search/filter/sort/selection over all current events.
- `/dashboard` — exact run coverage, stage state, blocker, and recent selected events.
- `/events/:receiptNumber` — objective magnitude, attention inputs, outcomes, missing reasons,
  and source hashes.
- `/research` — fixed H0/H1/H3/H5 descriptive matrix and magnitude-versus-attention plot.
- `/lineage` — provider groups and individual immutable snapshots.
- `/settings` — sanitized source capability and research-boundary state.

## Adding a second event family

1. Normalize it to a new versioned research model without changing the existing supply-contract
   artifact.
2. Add an explicit event-family discriminator to an additive API contract.
3. Extend repository projection and its temporary-run tests first.
4. Add the family as an API filter and preserve URL state.
5. Reuse the evidence sections only where the input meaning is identical; create a family-specific
   evidence block for different objective magnitude definitions.
6. Keep comparison horizons and missing-state rules preregistered in the study layer.

## Later persistence migration

Do not introduce a database merely to serve the current 40 rows. If run volume or cross-run queries
make files insufficient, implement a repository with the same response models, compare its output
against immutable file runs, and switch the application factory dependency only after parity tests
pass. This prevents a database migration from forcing a frontend rewrite.

## Selected visual system

The product uses concept B's three-pane research-terminal information architecture with concept
A's light institutional palette. The canonical rules live in `DESIGN.md`; the generated hybrid
reference and verified desktop/mobile captures live outside app source under
`outputs/design-research/crowd-excess-terminal/`. Product copy is English for the hackathon.
Preserve semantic tokens and the read-only research boundary when extending the interface.

## Known external blocker

The persisted run has 40 selected disclosures and 40 attention observations, but zero price and
index observations. `DATA_GO_KR_API_KEY` is not currently declared in `.env`, so H0/H1/H3/H5
returns remain explicitly missing. Adding that environment variable and resuming the same run is
the shortest path to completing the mini event study; KRX approval is not required for that step.

## Verification contract

```bash
uv run pytest
uv run ruff check .
cd web
pnpm test:run
pnpm typecheck
pnpm lint
pnpm build
pnpm e2e
```

Browser checks cover the real 40-event run, URL search, desktop keyboard focus, mobile overflow,
responsive navigation, and console errors. Unit fixtures are explicitly marked test-only and are
never used as displayed research results.
