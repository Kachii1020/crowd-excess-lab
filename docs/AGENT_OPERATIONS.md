# Agent Operations Runbook

This runbook is the only supported path from local verification to an autonomous Alpaca paper
run. It does not authorize live trading. Commands and logs must never print secret values.

## 1. Kickoff-only external setup

Complete these steps after the competition begins on August 29, 2026 JST:

1. Enrol on lablab.ai and create the one-person team.
2. Create a **fresh Alpaca paper account with exactly $100,000**.
3. Store the dedicated paper-account identifier in the runner-only
   `ALPACA_COMPETITION_ACCOUNT_ID`; never expose its value in source or public artifacts.
4. Create a dedicated OpenAI API project and a dedicated Supabase project.
5. Record any sponsor requirement announced at kickoff before enabling the scheduler.

The repository tag `pre-hackathon-research` identifies the pre-event baseline. Existing Korean
research must not be described as competition-period work.

## 2. Apply the append-only database boundary

Review and apply `supabase/migrations/202608240001_agent_audit.sql` to the dedicated project. The
expected catalog change is one table, two indexes, one public SELECT policy, and a trigger that
blocks UPDATE and DELETE.

Verify in the Supabase SQL editor using a disposable test row and a transaction:

```sql
begin;
select has_table_privilege('anon', 'public.agent_audit_events', 'select');
select has_table_privilege('anon', 'public.agent_audit_events', 'insert');
select has_table_privilege('service_role', 'public.agent_audit_events', 'insert');
rollback;
```

Expected results: `true`, `false`, `true`. Also verify that an anonymous REST `POST`, `PATCH`, and
`DELETE` are rejected. Never paste the service-role key into a browser, issue, social post, or
Vercel client variable.

Forward-fix rule: migrations are append-only during the event. If the migration is wrong, add a
new corrective migration; do not rewrite an already-applied migration or disable RLS.

## 3. Configure secret stores

GitHub Actions environment: `alpaca-paper`.

Required GitHub secrets:

- `OPENAI_API_KEY`
- `NAVER_API_HUB_CLIENT_ID`
- `NAVER_API_HUB_CLIENT_SECRET`
- `ALPACA_API_KEY`
- `ALPACA_SECRET_KEY`
- `ALPACA_COMPETITION_ACCOUNT_ID`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

GitHub variable `AGENT_MODE` starts as `shadow`. Vercel receives only:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`

Paper-account identity remains runner-side. Do not configure Alpaca, NAVER, OpenAI, or Supabase
service-role secrets in Vercel.

## 4. Local and CI gates

```bash
uv sync --locked --dev --no-editable
uv run --no-sync ruff check .
uv run --no-sync pytest -q
pnpm --dir web test:run
pnpm --dir web typecheck
pnpm --dir web lint
pnpm --dir web build
PLAYWRIGHT_HTML_OPEN=never pnpm --dir web e2e
uv run --no-sync python scripts/security_preflight.py
uv run --no-sync python scripts/deploy_preflight.py --mode configuration
```

The secret-history scan must pass before the repository becomes public. The frontend licence
inventory runs through `scripts/license_preflight.py`; also review Python dependency metadata.

## 5. Shadow activation

1. Run `crowd-excess-agent feasibility`; retain NAVER as core only if at least four symbols have
   80% coverage. Otherwise set `AGENT_ATTENTION_WEIGHT=0.20`; price/news becomes primary and the
   runner skips the core-attention gate.
2. Keep `AGENT_MODE=shadow`.
3. Run `crowd-excess-agent probe`; confirm the returned ID equals the competition account.
4. Run `crowd-excess-agent run` during a regular US market session.
5. Inspect the Supabase event order: `run_started`, all `signal` rows, `risk_decision` when a
   candidate exists, optional `execution`, `portfolio`, then `run_completed`.
6. Open `/agent/runs/<run-id>` logged out and verify timestamps, hashes, evidence, failed gates,
   outcome, and portfolio snapshot. An abstention must not fabricate or imply an execution receipt.

A no-trade result is valid. Never loosen a threshold just to manufacture a demo order.

## 6. Scheduler reliability and local watchdog

GitHub Actions targets four scans per market hour, but hosted cron timing is best-effort and may be
delayed. `scripts/agent_watchdog.py` is a local, fail-closed complement for shadow coverage only. It
checks the competition window, regular market hours, production audit freshness, active workflow
runs, and a local cooldown before requesting one GitHub shadow dispatch.

The watchdog must skip when the audit is fresh, a workflow is active, or its cooldown applies. It
reserves cooldown state before dispatch so ambiguous network state cannot create a duplicate. It
cannot run the agent locally, set paper mode, approve promotion, or submit an order.

## 7. Paper promotion

Promote only when all checks are true:

- Account ID matches the fresh $100,000 account.
- API host is exactly `https://paper-api.alpaca.markets`.
- NAVER, Alpaca market/news/options, OpenAI structured output, and Supabase writes are healthy.
- At least one complete shadow candidate has passed every gate.
- Repeating the same candidate returns the same `client_order_id` and no duplicate order.
- Public routes have no mutation control and logged-out access works.

Set the GitHub variable to `AGENT_MODE=paper`, then manually dispatch once. Scheduled runs target
four starts per market hour but are not guaranteed to start on time. Alpaca's market clock and the
competition date/freeze gates remain final; the local watchdog continues to request shadow only.

## 8. Incident and recovery matrix

| Symptom | Safe behavior | Operator action |
|---|---|---|
| OpenAI timeout/refusal/schema error | Symbol abstains | Inspect sanitized status; do not add free-text fallback |
| NAVER or Alpaca market data stale/missing | No candidate/order | Confirm provider status and next scheduled retry |
| Missing Greek, OI, quote, or option volume | Risk rejection | Do not substitute estimated liquidity |
| Supabase append fails before order | No order | Restore database access, then rerun; idempotency protects retry |
| Order request times out after submission | State uncertain | Query by deterministic client order ID before any retry |
| Partial fill or rejection | Receipt remains visible | Inspect Alpaca; never rewrite the event as filled |
| Account ID or host mismatch | Immediate hard failure | Correct secrets/configuration; never bypass the check |
| Daily loss, risk cap, or freeze reached | No new position | Preserve the gate result and monitor existing positions |

If public deployment is wrong, roll back Vercel to the preceding verified commit. If audit storage
is unavailable, the public API returns a safe `503`; paper submission cannot proceed past a failed
pre-execution append.

## 9. Competition freeze

No new position may open at or after `2026-09-03T20:00:00Z`. Stop scheduled paper openings after
the September 3 US close. Reconcile remaining positions under the predeclared exit policy and
preserve the final portfolio snapshot. Do not backfill or alter prior audit events.
