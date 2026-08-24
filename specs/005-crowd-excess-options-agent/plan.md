# Implementation Plan: Crowd Excess Options Agent

**Spec**: [spec.md](spec.md)

## Summary

Extend the existing Python/FastAPI and React/Vite application with a paper-only agent core,
strict external adapters, append-only Supabase storage, read-only public projections, and a
judge-facing Agent Console. Reuse `httpx` instead of adding heavyweight SDKs to the Vercel bundle.

## Technical context

- Python 3.12, Pydantic, FastAPI, `httpx`, pytest, Ruff.
- React 19, TypeScript, TanStack Query, Recharts, Vitest, Playwright.
- OpenAI Responses REST, Alpaca CLI plus paper Trading REST, NAVER API HUB, Supabase REST.
- GitHub Actions runner; Vercel read-only public application.

## Design

- `agent/domain.py`: immutable records and fixed strategy/risk configuration.
- `agent/signals.py`: complete-day NAVER attention, market dislocation, and residual scoring.
- `agent/evidence.py`: strict OpenAI request/response boundary.
- `agent/risk.py`: option selection validation, portfolio limits, freeze, and idempotency.
- `agent/alpaca.py`: CLI reads and explicit paper REST multi-leg submission.
- `agent/store.py`: in-memory tests and Supabase append/read projections.
- `agent/orchestrator.py`: auditable stage ordering; storage succeeds before paper submission.
- `agent_cli.py`: credentialed `probe`, `run`, and `strategy` commands.
- Existing FastAPI gains read-only `/api/v1/agent/*`, `/portfolio`, and `/strategy` routes.

Data flow: sources → timestamp validation → OpenAI evidence → residual score → deterministic
trade intent → risk decision → persist pre-execution audit → optional Alpaca paper submission →
persist receipt/portfolio → public projection.

## Quality and operations

- No live endpoint setting exists; exact paper host and competition account are mandatory.
- Secret values are `SecretStr`, omitted from diagnostics, and unavailable to the frontend.
- Supabase service role writes only in the runner; anon reads only sanitized public views.
- Scheduler is safe under duplicate/delayed invocation and market-closed conditions.
- Rollback is `AGENT_MODE=shadow` plus disabling the scheduled workflow.

## Governance check

| Rule | Result |
|---|---|
| No fabricated observations | Pass; fixtures stay in tests and are labelled synthetic |
| No NAVER post scraping | Pass; Search Trend only |
| Chronological inputs | Pass; complete-day cutoffs and explicit `as_of` |
| Model cannot bypass risk | Pass; typed output is advisory evidence only |
| No live trading | Pass; paper host/account invariants and negative tests |
