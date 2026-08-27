# Crowd Excess Options Agent

## Status

- `DELIVERY_PENDING_EXTERNAL`: core paper-only agent, audit API, scheduler, and public UI implemented; external
  credentials, database migration, actual paper order, and deployment remain pending.
- `LEARNING_PENDING_TEACH_BACK`: `SEEN`; teach-back and operator exercise remain pending.

## Delivery

The Korean research thesis was converted into a fixed-universe US options agent. It records
timestamp-safe NAVER attention, Alpaca market/news/options evidence, strict OpenAI assessment,
deterministic risk, paper receipts, and portfolio state without adding a live-trading path.

## Learning contract

- Mode: deep (orders, secrets, RLS, deployment, and recovery).
- Concepts: AI authority boundary; idempotent paper submission; Supabase read/append separation.
- Delivery evidence: backend, frontend, build, and desktop/mobile judge-path tests.
- Learning evidence: one prediction, teach-back, and safe negative-permission exercise.

## System flow

- [Structured evidence](../../../src/crowd_excess_lab/agent/evidence.py) validates model output.
- [Deterministic risk](../../../src/crowd_excess_lab/agent/risk.py) owns contracts and quantity.
- [Paper submission](../../../src/crowd_excess_lab/agent/alpaca.py) verifies account and idempotency.
- [Exit projection](../../../src/crowd_excess_lab/agent/exits.py) distinguishes working quantity from
  terminal filled exposure and closes only observable spread units.
- [Audit migration](../../../supabase/migrations/202608240001_agent_audit.sql) separates public reads
  from runner writes and blocks mutation.
- [Orchestrator](../../../src/crowd_excess_lab/agent/orchestrator.py) persists the risk decision
  before any external order call.

Invariant: an order may occur only after a sanitized risk event is durably appended, on the exact
paper endpoint and account, with a deterministic client order ID. Any uncertain model/data/storage
state fails closed.

## Decisions and tradeoffs

- Direct official REST adapters keep payloads explicit; Alpaca CLI still owns account, clock, and
  position reads as required by the challenge.
- OpenAI is evidence-only. This reduces agent freedom but makes sizing and safety reproducible.
- Audit records are append-only events rather than mutable run rows. Public reconstruction costs
  more reads, but preserves the actual decision history and failure state.
- Session option volume is fetched after delta-based pair selection so it remains a real liquidity
  gate without downloading bars for the full chain.

Failure/rollback: model or provider failures abstain; database failure blocks submission; uncertain
Alpaca submission is recovered by client-order-ID lookup; Vercel rolls back by deployment/commit;
database corrections use a forward migration rather than weakening RLS.

Partial-fill rule: each Alpaca receipt preserves requested and filled spread units. A working partial
entry stays visible and blocks unsafe quantity assumptions; once the entry becomes terminal, only the
filled units supported by both option-leg positions may become a close intent.

## Verification evidence

- Python: 105 tests passed; Ruff passed.
- Frontend: 5 Vitest tests, TypeScript, oxlint, and Vite production build passed.
- Browser: desktop/mobile Playwright suite passed, including the clearly labelled synthetic judge
  path from Agent Console through audit, portfolio, and strategy.
- External paper order and Supabase permission probe: pending real credentials and kickoff account.
- Partial-fill boundary tests preserve `filled_qty`, retain working risk, wait for terminal quantity,
  and close only the filled spread units.

## Teach-back

Pending user response: explain why a valid OpenAI assessment is still insufficient to place an
order, and name the checks that must succeed after it.

Prediction prompt: if Alpaca accepted an order but the runner timed out before receiving the
response, what prevents a duplicate on the next scheduled run?

User response, 2026-08-24: immediately resubmitting after a timeout can cause an incorrect trade.
Review: directionally correct. To reach `EXPLAIN`, the response still needs the missing causal link:
the first order may already exist at Alpaca even though the client never received its response, so
the deterministic client order ID must be looked up before any retry to prevent a duplicate spread.

Partial-fill response, 2026-08-27: placing the close first is risky because the price may change
before execution. Review: price movement is a valid execution risk, but the task-specific missing
link is that the original entry order remains live and may fill additional spread units after the
close. The entry must first reach a terminal state; then its final `filled_qty` and both leg
positions determine the close quantity.

Partial-fill follow-up, 2026-08-27: predicted four remaining spreads and proposed confirming the
close state. Review: the answer correctly recognized that order state matters, but counted trade
events rather than net holdings. One entry fill minus one close plus two later entry fills leaves
two open spreads. The state that must become terminal before sizing the close is the original entry
order, not the close order.

## Contribution split

- User decisions: original crowd-overreaction thesis; clean terminal direction; English hackathon
  product; Alpaca paper options; approved limits and schedule.
- AI proposal/implementation: domain contracts, adapters, scoring/risk orchestration, audit schema,
  public API/UI, workflow, tests, and runbooks.
- Independently verified: offline failure boundaries, builds, API contracts, and Playwright paths.
  External provider behavior and paper fills are not yet independently verified.

## Next practice

After Supabase setup, run a transaction-wrapped permission probe: predict anonymous SELECT/INSERT
and service-role INSERT/UPDATE results, execute them without printing keys, then explain which of
table grants, RLS policy, and trigger produced each result.
