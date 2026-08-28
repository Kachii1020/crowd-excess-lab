# Hackathon Submission Package

This document contains the public submission copy and the evidence checklist for Crowd Excess
Agent. Public claims must distinguish paper execution, shadow decisions, pre-kickoff verification,
and synthetic test fixtures. Account identifiers and credentials must never appear in this
repository, screenshots, slides, or recordings.

## Project identity

**Title:** Crowd Excess Agent

**Tagline:** Attention outruns evidence. Risk decides.

**Short description (under 255 characters):**

> An auditable AI agent that detects when attention and price outrun objective news, then expresses
> a controlled contrarian view with defined-risk Alpaca paper option spreads.

**Long description:**

> Crowd Excess Agent tests a simple market intuition: investor attention can move faster than the
> objective evidence behind a price move. It combines complete-day NAVER cross-border search
> attention with Alpaca price, SPY benchmark, volume, news, and option-chain data. OpenAI evaluates
> only the direction, materiality, and confidence of supplied news through a strict structured
> schema. A deterministic engine calculates the remaining Crowd Excess residual, ranks a fixed
> five-symbol universe, constructs a 14–30 DTE debit vertical, and enforces liquidity, account,
> loss, exposure, and idempotency gates. The agent may abstain, and every decision is recorded in
> an append-only audit trail. The public dashboard lets judges replay evidence, intent, risk gates,
> Alpaca paper receipts, and honest paper P&L. Live trading and naked options are structurally
> unavailable.

## Verified public evidence — August 28, 2026

- **Public application:** [crowd-excess-lab.vercel.app](https://crowd-excess-lab.vercel.app)
  has been verified without authentication.
- **Agent console:** [crowd-excess-lab.vercel.app/agent](https://crowd-excess-lab.vercel.app/agent)
  is the primary judge path.
- **Public source:** [github.com/Kachii1020/crowd-excess-lab](https://github.com/Kachii1020/crowd-excess-lab)
  is available without authentication and retains the pre-hackathon provenance boundary.
- **Alpaca paper account:** a dedicated account has been privately verified as `ACTIVE` with
  exactly **$100,000** starting equity. Its account ID is intentionally excluded from public
  artifacts and must be entered only in the official submission form.
- **Pre-kickoff verification:** run
  [`20260828T095104Z-cabc99f1`](https://crowd-excess-lab.vercel.app/agent/runs/20260828T095104Z-cabc99f1)
  is a real credentialed **closed-market abstention** recorded before the competition window. It
  proves the deployed audit path and safe market-hours gate; it is not an options trade, a full
  market-session result, or P&L evidence.
- **Market-open autonomous run:** `TBD — add verified competition-period run ID and link`.
- **Alpaca paper receipt:** `TBD — add only after a real order attempt is recorded`.
- **Paper P&L and drawdown:** `TBD — report exact values after the required market sessions`.

## One-page implementation write-up

### Thesis and data boundary

Crowd Excess asks whether investor attention and price have moved further than the objective news
evidence supports. NAVER Search Trend is used only as **cross-border search attention**—never as
community sentiment. The fixed decision universe is AAPL, MSFT, NVDA, TSLA, and QQQ, with SPY as
the market benchmark. Complete historical days and timestamped inputs prevent look-ahead use.

### AI logic

OpenAI receives normalized, timestamped price context and supplied Alpaca headlines. With
`store=false`, it returns strict `EvidenceAssessment` fields: direction, materiality, confidence,
rationale, cited supplied headline IDs, and an abstention reason. Invalid, refused, timed-out, or
unavailable output causes abstention. The model never receives an order tool and cannot select
contracts, determine quantity, or bypass a risk gate.

### Signal and deterministic risk

Crowd Excess combines signed SPY-adjusted movement with attention heat, then subtracts news
direction × materiality × confidence. A positive residual represents potentially excessive upside
enthusiasm; a negative residual represents potentially excessive downside pessimism. The agent
takes the opposite view only after attention, move, confidence, freshness, liquidity, option
shape, account, exposure, loss, and competition-window gates pass.

Only 14–30 DTE call or put debit verticals are eligible. Maximum debit is 1% of account equity,
total premium at risk is capped at 3%, and no more than one new position may be attempted per day.
Missing quotes, Greeks, option volume, open interest, storage, or exact account identity results in
`ABSTAIN`.

### Alpaca execution and auditability

Alpaca is the account, market-data, options, and paper-execution boundary. Multi-leg paper orders
are submitted only after exact paper-host and dedicated-account verification. Every intent uses a
deterministic client order ID. If submission times out, the runner queries that same ID before any
further action, preventing a network timeout from becoming a duplicate trade.

Supabase stores sanitized append-only runs, signals, evidence assessments, risk decisions,
receipts, and portfolio snapshots. The public FastAPI/Vercel application has read-only access;
scans and orders cannot be initiated from the browser. This produces a judge-readable chain from
timestamped inputs to model evidence, deterministic risk, Alpaca response, and honest portfolio
outcome.

### Safety and limitations

This is a competition paper-trading system, not investment advice. It contains no live-trading
mode, naked-option path, or profitability claim. Search attention is an imperfect cross-border
proxy, structured news assessment can abstain, option liquidity can invalidate a candidate, and a
small competition sample cannot establish durable alpha. A no-trade decision is a valid outcome.

## Nine-slide pitch deck outline

1. **Thesis:** Attention outruns evidence. Risk decides.
2. **Data boundary:** NAVER attention, Alpaca market/news/options, and what each source does not say.
3. **Signal:** attention heat + market-adjusted movement − objective news evidence.
4. **Architecture:** provider inputs → structured evidence → deterministic engine → append-only audit.
5. **Decision trace:** one verified market-open run from facts to ranked candidate or abstention.
6. **Risk:** defined-risk debit vertical, liquidity checks, 1%/3% caps, and one attempt per day.
7. **Receipt and portfolio:** real Alpaca paper response plus exact P&L/drawdown, once available.
8. **Reliability:** strict schemas, paper/account lock, deterministic IDs, and timeout reconciliation.
9. **Limitations and learning:** honest sample size, failures, abstentions, and next validation step.

## Submission checklist

### Verified now

- [x] Public Vercel application works without authentication.
- [x] Dedicated Alpaca paper account is `ACTIVE` with exactly $100,000 starting equity; ID withheld
      from public artifacts.
- [x] A real pre-kickoff closed-market abstention trace is publicly replayable and accurately
      labelled.
- [x] Final title, tagline, short description, long description, and implementation write-up exist.
- [x] All current public product copy is English.
- [x] No fixture is represented as real execution.
- [x] No profitability claim is made.

### Verify before final recording and submission

- [x] Public GitHub repository works in a logged-out browser.
- [ ] At least one competition-period market-open autonomous run: `TBD — add run ID`.
- [ ] Real Alpaca paper option receipt, if a candidate passes every gate: `TBD — add trace link`.
- [ ] At least two full autonomous sessions: `TBD — list run IDs and outcomes`.
- [ ] Exact paper P&L and drawdown are shown, including negative values if applicable.
- [x] 16:9 PNG cover uses the tagline and clearly says `ALPACA PAPER OPTIONS`.
- [ ] Final MP4 is 4:30 or shorter and follows `docs/VIDEO_SCRIPT.md`.
- [x] Nine-slide PDF pitch deck follows the outline above; editable PPTX is retained.
- [ ] Three build-in-public posts use verified facts from `docs/SOCIAL_POSTS.md`.
- [ ] Logged-out direct reload works for `/agent`, `/portfolio`, `/strategy`, and the selected run.
- [ ] Submission form contains the paper account ID, but no public artifact exposes it.
- [ ] Every placeholder in this document, the deck, video, and social posts has been removed.

Internal submission cutoff: **September 4, 2026 at 20:00 JST**.
