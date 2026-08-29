# Crowd Excess Agent — Fact-Locked Build-in-Public Posts

Each theme has a compact X draft and an expanded LinkedIn draft. These versions match the public
August 28 market-open shadow session and can be published without implying an order or profit.

## Post 1 — Architecture and safety

### X

> Crowd Excess Agent combines NAVER attention, Alpaca market/news/options data, and strict OpenAI
> evidence. Deterministic code owns risk and paper-only debit spreads. Every result is auditable;
> the public app cannot place orders. https://crowd-excess-lab.vercel.app/agent

### LinkedIn

> I built Crowd Excess Agent for the Alpaca AI Trading Agents Hackathon.
>
> The thesis: price and investor attention can outrun objective news evidence.
>
> NAVER measures complete-day cross-border search attention. Alpaca supplies the market clock,
> prices, SPY-relative movement, volume, news, options, and paper portfolio state. OpenAI assesses
> only evidence direction, materiality, confidence, and cited supplied headlines through a strict
> schema. Deterministic code owns scoring, contract construction, sizing, and every risk gate.
>
> The system is paper-only, supports defined-risk debit verticals, and may abstain. Public visitors
> can replay the audit trail but cannot initiate a scan or order.
>
> Demo: https://crowd-excess-lab.vercel.app/agent
> Code: https://github.com/Kachii1020/crowd-excess-lab
>
> No live trading. No profitability claim. Evidence first; risk decides.

## Post 2 — First autonomous market-open session

### X

> First session: 7 real market-open five-symbol shadow scans; all abstained. Stable trace: source
> hashes + OpenAI response IDs/tokens, with no risk decision or receipt. Fixed thresholds.
> https://crowd-excess-lab.vercel.app/agent/runs/20260828T193701Z-b404b62a

### LinkedIn

> Crowd Excess Agent completed seven real five-symbol shadow scans during one open US market
> session on August 28.
>
> All seven abstained. The stable run preserved five NAVER inputs, five Alpaca market snapshots,
> five structured OpenAI evidence assessments, source hashes, response IDs, model name, token
> counts, and evidence-input hashes.
>
> Its result was simple: no symbol passed the attention, movement, evidence, and market gates. No
> persisted risk decision, execution receipt, or position was created, and no threshold was
> relaxed to force a demo trade.
>
> Stable public trace:
> https://crowd-excess-lab.vercel.app/agent/runs/20260828T193701Z-b404b62a
>
> Paper-only shadow evidence, not a profitability claim.

## Post 3 — Honest result and failure safety

### X

> Honest result after 7 shadow scans: $100k equity; P&L, drawdown and open risk $0; no positions. An
> Alpaca data failure safely abstained; the watchdog dispatched stale work and skipped a duplicate.
> https://crowd-excess-lab.vercel.app/agent/runs/20260828T174442Z-d761e38b

### LinkedIn

> Honest Crowd Excess Agent result after seven real market-open shadow scans:
>
> • Equity: $100,000
> • Total P&L: $0
> • Drawdown: 0
> • Open premium risk: $0
> • Persisted risk decisions: 0
> • Execution receipts: 0
> • Positions: 0
>
> One run encountered unavailable Alpaca market data. It abstained, suppressed request details,
> and created no order or position:
> https://crowd-excess-lab.vercel.app/agent/runs/20260828T174442Z-d761e38b
>
> GitHub's hosted cron was also delayed. A local fail-closed watchdog complemented it by dispatching
> stale shadow work and later skipping a duplicate when the production audit was fresh. It cannot
> place or promote an order.
>
> What worked: real inputs, structured evidence, append-only audit, and safe abstention.
> What remains uncertain: seven scans cannot establish alpha, and no candidate passed every gate.
> Next: continue chronological market sessions without weakening the preregistered thresholds.
>
> No forced trade, no hidden fixture, no profitability claim.

## Publication guardrails

- Use the stable trace for the autonomous-run post and the failure trace for the safety post.
- Preserve the counts and zero portfolio values until the public audit actually changes.
- If a real paper order later appears, replace the no-order counts with exact public receipt and
  portfolio facts; do not delete or relabel earlier abstentions.
- Never use a synthetic receipt, private dashboard, credential, or personal identifier in a post.
- Describe NAVER as `cross-border search attention`, never community sentiment.
