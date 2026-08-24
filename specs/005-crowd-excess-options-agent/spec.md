# Feature Specification: Crowd Excess Options Agent

**Status**: Implemented locally; credentialed acceptance pending
**Input**: Implement the approved Alpaca AI Trading Agents hackathon plan.

## Problem and outcome

The existing product measures Korean-market disclosure attention but cannot satisfy the
hackathon's Alpaca, autonomous-agent, or options requirements. The outcome is an English,
auditable agent that treats NAVER Search Trend as cross-border attention, asks OpenAI to assess
objective news evidence, applies deterministic risk gates, and may submit only defined-risk
Alpaca paper option spreads.

## Scope

### In scope

- AAPL, MSFT, NVDA, TSLA, and QQQ with SPY as benchmark.
- Complete-day NAVER attention measurements and Alpaca market/news/options inputs.
- Strict OpenAI evidence output, explainable residual score, shadow mode, and paper mode.
- Append-only Supabase audit records and read-only public API/UI projections.
- GitHub Actions scheduling, submission documentation, and public deployment readiness.

### Non-goals

- Live trading, naked options, stock orders, deposits, withdrawals, or public order endpoints.
- Describing search attention as sentiment or a paper result as real-money profitability.
- Replacing the existing Korean-market research artifacts.

## User scenarios

### US1 — Inspect an auditable agent decision (P1)

**Independent verification**: A visitor can trace timestamped source measurements through the
evidence assessment, score, risk decision, and execution receipt without credentials.

1. **Given** a completed agent run, **When** a visitor opens its detail route, **Then** every
   decision stage and abstention reason is visible in English.

### US2 — Run safely in shadow or paper mode (P1)

**Independent verification**: A credentialed runner produces an idempotent paper intent or a
specific abstention; a non-paper endpoint can never receive an order.

1. **Given** valid inputs and a passing candidate, **When** the runner is in shadow mode, **Then**
   it records the complete would-submit receipt without an external order.
2. **Given** any failed safety gate, **When** the runner evaluates an intent, **Then** no order is
   submitted and the failed gate is stored.

### US3 — Monitor paper performance (P2)

**Independent verification**: The public portfolio route displays sanitized account equity,
paper P&L, drawdown, positions, and last synchronization time.

## Edge cases and failure behavior

- Missing, stale, future-dated, or incomplete source data produces `ABSTAIN`.
- Invalid/refused/timed-out model responses produce `ABSTAIN`, never free-text fallback.
- Closed markets, duplicate invocations, excessive spread width, insufficient open interest,
  missing Greeks, exceeded loss/risk limits, and competition freeze all block new orders.
- Storage failure blocks paper submission because an unaudited order is forbidden.
- Partial/rejected/cancelled orders remain visible and are never rewritten as fills.

## Requirements

- **FR-501**: All trading code MUST reject non-paper Alpaca endpoints and account mismatches.
- **FR-502**: The model MUST return a strict evidence schema and MUST NOT size or execute orders.
- **FR-503**: The deterministic engine MUST compute the Crowd Excess score from only timestamp-valid inputs.
- **FR-504**: Only 14–30 DTE call/put debit verticals passing liquidity and risk gates MAY be submitted.
- **FR-505**: Client order IDs MUST be deterministic and duplicate-safe.
- **FR-506**: Runs, signals, intents, risk decisions, receipts, and portfolio snapshots MUST be append-only and sanitized.
- **FR-507**: Public APIs MUST be read-only and return explicit unconfigured/empty states.
- **FR-508**: The primary UI MUST provide the 90-second judge path from attention to paper P&L.
- **FR-509**: Existing Korean research MUST remain accessible and explicitly labelled pre-hackathon research.
- **FR-510**: CI MUST cover backend, frontend, deployment configuration, and paper-boundary failures without live credentials.

## Success criteria

- **SC-501**: Offline tests prove all specified abstention and order-boundary cases.
- **SC-502**: A shadow run can complete end to end with deterministic fixture inputs.
- **SC-503**: Logged-out users can load every public route without receiving a secret or mutation control.
- **SC-504**: Credential-dependent live probes remain clearly reported as blocked until configured.

## Assumptions and dependencies

- NAVER is a daily attention proxy, not community sentiment.
- OpenAI, Alpaca paper, and Supabase credentials are supplied only through secret stores.
- The user creates the fresh $100,000 paper account and enrols the solo team at kickoff.
