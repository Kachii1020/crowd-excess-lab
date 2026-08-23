# Crowd Excess Lab

`Crowd Excess Lab` tests a specific observation about the Korean equity market:

> Does community attention or emotion that is unusually strong relative to the
> measurable size of a corporate event predict short-lived continuation, reversal,
> or volatility?

This repository is a data-feasibility and measurement tool. It does **not** place orders,
scrape restricted communities, or claim that a tradable edge exists.

## Current scope

- Query official OpenDART disclosure metadata with a user-provided API key.
- Probe the current NAVER API HUB Search Trend API as a legal attention proxy.
- Build an audited 30–50 event sample of original single-sales/supply-contract notices.
- Collect official-origin FSC stock and market-index prices through the Public Data Portal.
- Compute conservative next-trading-day event returns at fixed 0, +1, +3, and +5 horizons.
- Validate official KRX CSV exports for prices and investor flows.
- Validate privacy-minimised community observations obtained by an allowed method.
- Compute transparent starting measurements:
  - supply-contract size relative to annual revenue;
  - community activity, participation, extremity, disagreement, and duplication;
  - residual `Crowd Excess` after fitting an explainable baseline model.
- Provide chronological walk-forward split utilities for the next research milestone.

## Quick start

```bash
cp .env.example .env
uv sync --dev
uv run pytest
uv run ruff check .
uv run crowd-excess-check --report docs/DATA_FEASIBILITY_REPORT.local.md
```

Without credentials or local CSV files, the capability command still runs and reports
which inputs are missing. Add `--live` only when you want to call configured APIs.

See [`specs/001-data-feasibility/quickstart.md`](specs/001-data-feasibility/quickstart.md)
for the input contracts and exact live-check workflow.

## Mini event study

Enable both `금융위원회_주식시세정보` and `금융위원회_지수시세정보` for the same
Public Data Portal key, then keep the key in the ignored `.env` as
`DATA_GO_KR_API_KEY`.

```bash
uv run crowd-excess-study --target 40
```

An interrupted or credential-blocked run can be continued without repeating completed
OpenDART and NAVER stages:

```bash
uv run crowd-excess-study --resume data/processed/mini_event_study/<run-id>
```

See [`specs/002-mini-event-study/quickstart.md`](specs/002-mini-event-study/quickstart.md)
for the exact cohort, windows, outputs, and resume behavior.

## Research workbench

The repository now includes a read-only local API and a desktop-first research interface. It
shows exact run coverage, filters all selected events, exposes per-event calculation evidence,
compares preregistered horizons, and audits source lineage without exposing local credentials.

```bash
# terminal 1
uv run crowd-excess-api

# terminal 2
cd web
pnpm dev
```

See [`specs/003-research-workbench/quickstart.md`](specs/003-research-workbench/quickstart.md) and
[`docs/WORKBENCH_HANDOFF.md`](docs/WORKBENCH_HANDOFF.md) before extending the UI or data layer.

## Git and preview deployment

The repository is prepared for credential-free GitHub Actions verification and a single Vercel
preview containing the Vite workbench plus the read-only FastAPI application. Local research data
and raw provider responses remain excluded. A public preview requires an explicitly reviewed export
of normalized artifacts; configuration CI never publishes test fixtures or local runs.

```bash
uv run python scripts/deploy_preflight.py --mode configuration
```

See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for the publication gate, private GitHub setup,
preview smoke tests, promotion, and rollback workflow.

## Interpretation boundary

Search interest is an **attention proxy**, not community sentiment. A community heat
score is a preregistered measurement recipe, not a validated trading signal. Any claim
about return predictability must survive a chronological holdout, a fundamentals-only
baseline, a shuffled-time placebo, and estimated trading costs.
