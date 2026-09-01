# Hackathon Submission Package

This file contains final English submission copy grounded in the public audit trail. Crowd Excess
Agent completed two real sampled market sessions but did not create a paper order. That no-order
result is part of the submission, not a gap to hide with a fixture.

## Submission form copy

**Title:** Crowd Excess Agent

**Tagline:** Attention outruns evidence. Risk decides.

**Short description (173 characters):**

> An auditable AI agent that detects when attention and price outrun objective news, then expresses
> a controlled contrarian view with defined-risk Alpaca paper option spreads.

**Long description:**

> Crowd Excess Agent tests whether investor attention and price can move further than objective
> news evidence supports. It combines complete-day NAVER cross-border search attention with Alpaca
> prices, SPY-relative movement, volume, news, and option-chain data. OpenAI evaluates only the
> direction, materiality, and confidence of supplied headlines through a strict structured schema;
> deterministic code owns scoring, option construction, sizing, and risk. Seventeen real
> five-symbol sampled shadow scans ran across two US market dates on August 28 and 31, 2026. They
> produced 85 signal snapshots and 78 model assessments. No candidate passed every gate, so
> the account remained at $100,000 equity with zero P&L, drawdown, open risk, decisions, receipts,
> and positions. The public audit trail exposes source hashes, model response metadata, token
> usage, evidence, scores, failure-safe behavior, and the honest no-order outcome. Live trading,
> naked options, and browser-initiated execution do not exist.

**Suggested tags:** `AI Agents`, `FinTech`, `Alpaca`, `Options`, `Risk Management`, `Auditability`

**Public demo:** https://crowd-excess-lab.vercel.app/agent

**Public source:** https://github.com/Kachii1020/crowd-excess-lab

### Concise form answers

**What problem does it solve?**

> It separates attention-driven market movement from the objective news evidence available at the
> decision time, while making every abstention or paper action independently inspectable.

**How is AI used?**

> OpenAI receives normalized market context and supplied Alpaca headlines, then returns strict
> evidence direction, materiality, confidence, cited headline IDs, rationale, and an abstention
> reason. It cannot select contracts, size positions, bypass risk rules, or place orders.

**How is Alpaca used?**

> Alpaca supplies the market clock, prices, SPY benchmark data, volume, headlines, option chains,
> portfolio state, and the paper-only execution boundary. Missing or inconsistent Alpaca data
> fails closed before an order can exist.

**What was the verified result?**

> Seventeen real five-symbol sampled shadow scans completed across two US market dates. They
> produced 85 signal snapshots and 78 model assessments. The latest run preserved four complete
> model assessments and one explicit fail-closed evidence record; a separate provider-failure
> run suppressed request details and created no order. Portfolio equity remained $100,000, with
> zero P&L, drawdown, open premium risk, decisions, receipts, and positions.

## Verified evidence — August 28–September 1, 2026

- The [public decision audit](https://crowd-excess-lab.vercel.app/agent) and
  [public repository](https://github.com/Kachii1020/crowd-excess-lab) work without authentication.
- Seventeen real sampled shadow scans covered AAPL, MSFT, NVDA, TSLA, and QQQ across the August 28
  and August 31 US market dates. Together they recorded 85 signal snapshots and 78 model
  assessments, with seven fail-closed evidence-unavailable records.
- The latest sampled run,
  [`20260831T195329Z-97994d47`](https://crowd-excess-lab.vercel.app/agent/runs/20260831T195329Z-97994d47),
  recorded five signals while the market clock was open. Four symbols retained OpenAI response IDs
  and input hashes; TSLA failed closed when structured evidence was unavailable. The run abstained
  and created no risk decision or receipt.
- The stable run,
  [`20260828T193701Z-b404b62a`](https://crowd-excess-lab.vercel.app/agent/runs/20260828T193701Z-b404b62a),
  completed five signal snapshots and preserved NAVER, Alpaca market, and OpenAI evidence hashes.
  Every symbol also has an OpenAI response ID, model name, input/output token counts, and input hash.
- Its exact summary is: `No symbol passed attention, move, evidence, and market gates.` No persisted
  risk decision or execution receipt exists.
- The failure-safety run,
  [`20260828T174442Z-d761e38b`](https://crowd-excess-lab.vercel.app/agent/runs/20260828T174442Z-d761e38b),
  abstained when Alpaca market data became unavailable, suppressed request details, and created no
  order or position.
- The verified portfolio snapshot is **$100,000 equity, $0 total P&L, 0 drawdown, $0 open premium
  risk, 0 open spreads, and 0 positions**.
- GitHub's scheduled workflow was delayed during the session. A local fail-closed watchdog
  complemented, rather than replaced, the cron: it dispatched a stale shadow scan and later skipped
  a duplicate when fresh audit activity was present. It cannot directly place or promote an order;
  the workflow's independent evidence, account, liquidity, and risk gates still control promotion.

## One-page implementation write-up

### Thesis and data boundary

Crowd Excess asks whether investor attention and price have moved further than supplied objective
news evidence supports. NAVER Search Trend is used only as **cross-border search attention**—never
as community sentiment. The fixed universe is AAPL, MSFT, NVDA, TSLA, and QQQ, with SPY as the
benchmark. Complete historical days and timestamped source snapshots prevent look-ahead use.

### AI evidence layer

OpenAI receives normalized price context and supplied Alpaca headlines. With `store=false`, strict
`EvidenceAssessment` output records direction, materiality, confidence, rationale, cited supplied
headline IDs, and an abstention reason. Invalid, refused, timed-out, or unavailable output causes
abstention. The model has no order tool and cannot choose contracts or quantity.

The stable public run proves the evidence boundary with response IDs, model name, token counts, and
input hashes for all five symbols. These are audit metadata, not claims that the model predicted a
profitable trade.

### Signal and deterministic risk

The score combines signed SPY-adjusted movement with attention heat, then subtracts news direction
× materiality × confidence. A positive residual represents potentially excessive upside
enthusiasm; a negative residual represents potentially excessive downside pessimism. A contrarian
intent can proceed only after attention, movement, evidence, freshness, liquidity, option shape,
account, exposure, loss, and competition-window gates pass.

Only 14–30 DTE call or put debit verticals are eligible. Maximum debit is 1% of equity, aggregate
premium at risk is capped at 3%, and at most one new attempt is allowed per day. Missing quotes,
Greeks, volume, open interest, storage, or exact paper-account identity means no order.

### Execution, automation, and auditability

Alpaca is the market-data, portfolio, and paper-execution boundary. Each eligible intent receives a
deterministic client order ID. A submission timeout triggers a lookup by that same ID before any
further action, preventing ambiguous network state from becoming duplicate exposure.

GitHub Actions targets four shadow scans per market hour, but hosted cron timing is best-effort. The
local watchdog checks production audit freshness, competition dates, regular market hours, active
workflow runs, and a local cooldown. It can request one shadow workflow when the audit is stale and
otherwise skips or fails closed. It never bypasses GitHub, account, signal, or risk gates.

Supabase stores sanitized append-only runs, signals, evidence, optional risk decisions, optional
execution records, and portfolio snapshots. The public application is read-only. In the verified
sessions the optional decision and execution records remained absent, accurately reflecting the
verified no-order outcome.

### Safety and limitations

This is a competition paper-trading system, not investment advice. It has no live-trading mode,
naked-option path, or profitability claim. Search attention is an imperfect cross-border proxy;
headline assessment can abstain; option liquidity may invalidate a candidate; provider and
scheduler failures can delay scans; and 17 sampled runs across two market dates cannot establish
durable alpha.

## Nine-slide narrative

1. **Opening:** Attention outruns evidence. Risk decides.
2. **Thesis:** the opportunity is the unexplained residual, not raw sentiment.
3. **Data boundary:** what NAVER, Alpaca, and OpenAI do—and do not—measure.
4. **Signal:** attention heat + market-adjusted movement - objective news evidence.
5. **Product:** Overview leads directly to the latest sampled immutable decision trace.
6. **Execution authority:** defined-risk spreads, fixed limits, paper-only account boundary.
7. **Verified result:** 17 five-symbol scans across two dates, $100,000 equity, and no forced trade.
8. **Reliability:** strict evidence, idempotent orders, watchdog, and tested option-stage diagnostics.
9. **Business value:** audit before exposure and reproducible abstention when inputs are weak.

## Submission checklist

### Verified

- [x] Public Vercel application and public GitHub repository work without authentication.
- [x] Dedicated Alpaca paper account is active with exactly $100,000 equity.
- [x] Seventeen five-symbol sampled shadow runs across two US market dates are publicly recorded.
- [x] Stable and failure-safety run links are fixed in the submission narrative.
- [x] OpenAI response metadata and source hashes are visible for the stable run.
- [x] Current zero-decision, zero-receipt, zero-position, and zero-P&L state is explicit.
- [x] 16:9 cover and nine-slide PDF deck exist; editable deck source is retained.
- [x] Final 4:08 English AI-narrated H.264 MP4 exists with burned-in captions.
- [x] Sanitized two-session fact lock is retained with the submission assets.
- [x] Final title, descriptions, form answers, tags, video script, and social copy are English.
- [x] No fixture, abstention, or paper result is represented as profitable execution.

### Final operator actions

- [ ] Publish the three fact-locked build-in-public posts in `docs/SOCIAL_POSTS.md`.
- [ ] Recheck all public links in a logged-out browser immediately before submission.
- [ ] If a real paper receipt appears later, replace—not append to—the no-order video segment and
      update all counts from the public trace.
- [ ] Submit title, copy, tags, cover, video, deck, source, and demo before the internal cutoff.

Internal submission cutoff: **September 4, 2026 at 20:00 JST**.
