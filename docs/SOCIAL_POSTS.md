# Crowd Excess Agent — Build-in-Public Posts

Each theme has a compact X draft and an expanded LinkedIn draft. Replace every bracketed field with
a verified public fact before publishing. Never include the Alpaca account ID, credentials,
screenshots of private dashboards, or unverified P&L.

## Post 1 — Architecture and safety (ready after public GitHub verification)

### X

> Building Crowd Excess Agent: NAVER attention + Alpaca market/news/options + strict OpenAI
> evidence, with deterministic risk and paper-only debit spreads. Every decision is auditable; the
> public app cannot place orders. Demo: https://crowd-excess-lab.vercel.app/agent

### LinkedIn

> I’m building Crowd Excess Agent for the Alpaca AI Trading Agents Hackathon.
>
> The thesis: price + attention can outrun objective news evidence.
>
> NAVER measures cross-border search attention. Alpaca supplies market, news, options, and paper
> execution data. OpenAI scores only evidence direction, materiality, and confidence through a
> strict schema. Deterministic code owns contract selection, position sizing, liquidity checks,
> and every risk gate.
>
> The system is paper-only, uses defined-risk debit verticals, and may abstain. Every decision is
> stored as a replayable audit trace; the public app has no order endpoint.
>
> Demo: https://crowd-excess-lab.vercel.app/agent
> Code: [PUBLIC_GITHUB_URL]
>
> No live trading. No profitability claim. Building the evidence trail first.

## Post 2 — First autonomous market-open run (publish only after verification)

### X

> First autonomous market-open run: [RUN_URL]
> Decision: [TRADE/ABSTAIN]. Reason: [REASON]. Alpaca paper state: [STATE]. Thresholds stayed fixed;
> the trace shows inputs, AI evidence, risk gates, and any broker response. No profitability claim.

### LinkedIn

> Crowd Excess Agent completed its first competition-period autonomous market-open run.
>
> Run: [PUBLIC_RUN_URL]
> Inputs: 5-symbol attention + Alpaca price/SPY/volume/news/options
> Decision: [TRADE INTENT OR ABSTAIN]
> Primary reason: [ONE VERIFIED SENTENCE]
> Alpaca paper state: [SHADOW / ACCEPTED / PARTIALLY_FILLED / FILLED / REJECTED / NO ORDER]
>
> The important part is not whether the agent traded. It is that the same public trace shows the
> timestamped inputs, strict AI evidence assessment, Crowd Excess residual, every deterministic
> risk gate, and the broker response if an order was attempted.
>
> We did not loosen thresholds to manufacture a demo result. Paper trading only; this is not a
> claim of profitability.

## Post 3 — Honest result or failure analysis (publish after at least two sessions)

### X

> Honest update after [N] sessions: [ATTEMPTS] paper attempts, [FILLS] fills, P&L [VALUE], max
> drawdown [VALUE]. Main failure/abstention: [REASON]. Small competition sample—not evidence of
> durable alpha. Audit: [PUBLIC_SUMMARY_URL]

### LinkedIn

> Honest update after [NUMBER] autonomous Crowd Excess Agent sessions:
>
> • Runs: [RUN IDS OR PUBLIC SUMMARY LINK]
> • Paper order attempts: [COUNT]
> • Filled spreads: [COUNT]
> • Paper P&L: [EXACT VALUE]
> • Maximum drawdown: [EXACT VALUE]
> • Abstentions/failures: [COUNT + PRIMARY VERIFIED REASON]
>
> What worked: [ONE VERIFIED OBSERVATION].
> What failed or stayed uncertain: [ONE VERIFIED OBSERVATION].
> What I would test next: [ONE CHRONOLOGICAL VALIDATION STEP].
>
> This is a small competition sample, not evidence of durable alpha. Negative outcomes and
> no-trade decisions remain visible because an auditable agent should make failure as legible as
> success.
>
> Public demo: https://crowd-excess-lab.vercel.app/agent
> Code: [PUBLIC_GITHUB_URL]

## Publication guardrails

- Do not publish Post 1 until the GitHub URL works while logged out.
- Do not publish Post 2 from the pre-kickoff run `20260828T095104Z-cabc99f1`; that run is a real
  closed-market abstention used only to verify deployment and safety behavior.
- Do not publish Post 3 until every count and financial value can be read from the public audit
  trail or Alpaca paper portfolio snapshot.
- If there is no real order, write `NO ORDER` and explain the failed gate; do not substitute a
  fixture receipt.
- Preserve negative P&L, rejected orders, partial fills, and infrastructure failures exactly as
  observed.
