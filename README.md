# Crowd Excess Agent

Crowd Excess Agent is an auditable, paper-only US options agent for the Alpaca AI Trading
Agents Hackathon.

> It identifies when investor attention and price movement outrun objective news evidence,
> then expresses a controlled mean-reversion view through defined-risk Alpaca option spreads.

![Crowd Excess Agent — attention outruns evidence, risk decides](submission/crowd-excess-cover.png)

The product began as a Korean-equity research tool. That pre-hackathon origin remains visible
under `/research` and `/lineage`; it is not represented as US execution data or competition-period
work. NAVER Search Trend is labelled **cross-border search attention**, never sentiment.

## Safety boundary

- Alpaca paper trading only; the live endpoint is rejected during configuration and execution.
- Call or put debit verticals only; naked options and public order endpoints do not exist.
- OpenAI assesses normalized news evidence through strict structured output. It cannot select
  contracts, size a position, bypass a gate, or submit an order.
- The deterministic risk engine enforces the dedicated account ID, 14–30 DTE, delta shape,
  liquidity, 1% position debit, 3% aggregate premium risk, one new trade per day, and daily loss.
- Missing model output, market data, Greeks, option volume, storage, or account identity means
  `ABSTAIN`.
- Every submitted intent receives a deterministic `client_order_id` and an append-only audit trace.

No real-money mode or profitability claim exists.

## System

```text
NAVER complete-day attention ─┐
Alpaca price / SPY / volume ──┼─> Crowd Excess residual ─> deterministic risk ─> Alpaca paper
Alpaca headlines -> OpenAI ───┘             │                        │              │
                                            └──────── Supabase append-only audit ──┘
                                                               │
                                           FastAPI GET-only projection -> Vercel UI
```

Fixed universe: `AAPL`, `MSFT`, `NVDA`, `TSLA`, and `QQQ`; `SPY` is the benchmark.

Core implementation:

- `src/crowd_excess_lab/agent/`: signal, evidence, option selection, risk, audit, and runner.
- `supabase/migrations/`: public-read/service-append audit schema with update/delete trigger.
- `.github/workflows/agent.yml`: 15-minute competition-window scheduler with Alpaca clock gate.
- `web/src/pages/AgentConsolePage.tsx`: judge-facing decision console.
- `specs/005-crowd-excess-options-agent/`: scope, contracts, data model, and traceable tasks.

## Local verification

Python 3.12, Node 24, pnpm 11.19.0, and `uv` are expected.

```bash
uv sync --locked --dev --no-editable
uv run --no-sync ruff check .
uv run --no-sync pytest -q
pnpm --dir web install --frozen-lockfile
pnpm --dir web test:run
pnpm --dir web typecheck
pnpm --dir web lint
pnpm --dir web build
pnpm --dir web e2e
uv run --no-sync python scripts/security_preflight.py
uv run --no-sync python scripts/deploy_preflight.py --mode configuration
```

Run the read-only application:

```bash
# terminal 1
uv run --no-sync crowd-excess-api

# terminal 2
pnpm --dir web dev
```

The default `/agent` route renders an honest setup state without credentials or fabricated
orders. The Korean research fixture remains available at `/events` for local development.

## Credentialed operation

Copy `.env.example` to ignored `.env`, then configure NAVER API HUB, OpenAI, a dedicated Alpaca
paper account, and Supabase. Do not place a service-role key in Vercel or browser configuration.

```bash
uv run --no-sync crowd-excess-agent status
uv run --no-sync crowd-excess-agent probe
uv run --no-sync crowd-excess-agent strategy
uv run --no-sync crowd-excess-agent feasibility  # 180-day chronological NAVER gate
uv run --no-sync crowd-excess-agent run  # AGENT_MODE defaults to shadow
```

Paper promotion requires the exact operator checklist in
[`docs/AGENT_OPERATIONS.md`](docs/AGENT_OPERATIONS.md). Account creation, secret registration,
database migration, and a real paper order are deliberately not simulated by this repository.

## Documentation

- [`PRE_HACKATHON_BASELINE.md`](PRE_HACKATHON_BASELINE.md): provenance boundary and baseline tag.
- [`docs/AGENT_OPERATIONS.md`](docs/AGENT_OPERATIONS.md): account, Supabase, GitHub, runbook, recovery.
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md): logged-out Vercel publication and rollback.
- [`docs/HACKATHON_SUBMISSION.md`](docs/HACKATHON_SUBMISSION.md): submission copy and asset checklist.
- [`docs/learning/LEDGER.md`](docs/learning/LEDGER.md): operator learning evidence.

## Submission assets

- [Public Agent Console](https://crowd-excess-lab.vercel.app/agent)
- [`submission/crowd-excess-cover.png`](submission/crowd-excess-cover.png): 16:9 project cover.
- [`submission/crowd-excess-pitch-deck.pdf`](submission/crowd-excess-pitch-deck.pdf): verified nine-slide pitch deck.
- [`submission/crowd-excess-pitch-deck.pptx`](submission/crowd-excess-pitch-deck.pptx): editable deck source.
- [`docs/VIDEO_SCRIPT.md`](docs/VIDEO_SCRIPT.md): 4:30 presentation script and recording checklist.
- [`docs/SOCIAL_POSTS.md`](docs/SOCIAL_POSTS.md): fact-gated build-in-public drafts.

The real pre-kickoff run `20260828T095104Z-cabc99f1` is a closed-market abstention that verifies
the audit path; it is not represented as competition-period performance or P&L.

## Licence

MIT. Provider data and APIs remain subject to their respective terms; raw third-party payloads and
credentials are excluded from Git and the public deployment.
