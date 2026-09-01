# Crowd Excess Agent — 3:58 No-Order Presentation

This is the rehearsal script for the current public state. Before final recording, regenerate
`submission/fact-lock-final.json`, update only changed facts, and follow `docs/VIDEO_EDIT_SPEC.md`.
It does not imply that an option order or position exists.

## 0:00–0:24 — Thesis

**Shot:** Full-screen cover, then open the product-first Overview at
https://crowd-excess-lab.vercel.app/agent. Pause on the definition, formula, and primary action.

**Voice-over:**

> Markets react to facts, but they also react to attention. Crowd Excess asks whether attention and
> price have moved further than the objective news evidence supports. It is a pre-trade market
> reaction filter: the agent advances a controlled contrarian candidate only when deterministic
> liquidity and risk rules agree.

## 0:24–0:57 — Market Scan inputs

**Shot:** Select `Review Latest Market Scan`, then show the five-symbol workbench and source status.

**Voice-over:**

> The latest Market Scan places Apple, Microsoft, Nvidia, Tesla, and QQQ on one comparable surface,
> with SPY as the benchmark. Attention Z measures cross-border search heat. Move Z measures
> volatility-normalized, market-adjusted reaction. Volume Z shows dislocation, while Evidence
> records how strongly supplied news explains the move. The residual is Crowd Excess. Raw sentiment
> or price direction alone is not the thesis.

## 0:57–1:28 — Crowd Excess residual

**Shot:** Enlarge the Market Scan matrix, then the evidence panel.

**Voice-over:**

> Crowd Excess equals signed market-adjusted move times attention heat, minus news direction,
> materiality, and confidence. A positive residual means upside enthusiasm may be excessive. A
> negative residual means downside pessimism may be excessive. OpenAI assesses only supplied
> headlines. It cannot choose contracts, size positions, bypass a gate, or place an order.
> Deterministic code decides whether a contrarian view is even eligible.

## 1:28–2:05 — Latest real market-open run

**Shot:** Use `Review Latest Market Scan`, then open:
https://crowd-excess-lab.vercel.app/agent/runs/20260831T195329Z-97994d47. Pause on the five signals,
four model assessments, TSLA fail-closed evidence, and outcome.

**Voice-over:**

> This latest run was captured at 19:53 UTC on August 31 while the US market was open. Apple had
> attention Z of minus 0.28, move Z of minus 0.52, and 58 percent evidence confidence, leaving no
> residual. Tesla moved more sharply, with move Z above 2.2, but its attention was cold and
> structured evidence was unavailable, so it failed closed. QQQ had 91 percent evidence confidence,
> but its movement and attention still did not pass the signal gates. Five names were observed. No
> candidate reached option construction.

## 2:05–2:33 — Closest candidate and failure safety

**Shot:** Open the failure-safety trace:
https://crowd-excess-lab.vercel.app/agent/runs/20260828T174442Z-d761e38b. Highlight the sanitized
summary and empty execution state.

**Voice-over:**

> An earlier market-open run shows the closest candidate. Apple passed the attention, movement,
> evidence, and residual gates and became eligible for a bearish reversal. Required Alpaca option
> data then became unavailable before risk approval. The run stopped, suppressed request details,
> and created no order or position. Missing liquidity evidence is a reason to abstain, never
> permission to invent a spread.

## 2:33–2:57 — Honest portfolio result

**Shot:** Open `/portfolio`; pause on equity, P&L, drawdown, open risk, and positions.

**Voice-over:**

> Across two market dates, seventeen sampled scans produced eighty-five signal snapshots and
> seventy-eight model assessments. Equity remains exactly one hundred thousand dollars. Profit and
> loss, drawdown, open premium risk, and positions remain zero. No candidate cleared every evidence,
> liquidity, and risk gate. This is a verified no-order result, not evidence of profitability.

## 2:57–3:32 — Deterministic risk authority

**Shot:** Show the execution-authority slide with fixed risk limits.

**Voice-over:**

> Risk owns the order. Only fourteen-to-thirty day call or put debit verticals are eligible. Maximum
> position debit is one percent of equity, total premium risk is capped at three percent, and missing
> quotes, Greeks, open interest, volume, account identity, or storage means abstain. Every order uses
> a deterministic client order ID. A timeout triggers lookup by that same ID, never a blind retry. A
> watchdog requests shadow analysis only when the public audit is stale.

## 3:32–3:58 — Differentiation and close

**Shot:** Return to the cover with the public demo and repository URLs.

**Voice-over:**

> Crowd Excess is not another news signal. It measures the reaction left unexplained after
> cross-border attention, market-adjusted price movement, and supplied news are reconciled.
> Seventeen sampled scans, eighty-five signals, seventy-eight model assessments, zero receipts, and
> no forced trade. Attention outruns evidence. Risk decides.

## Shot list

1. Cover image.
2. `/agent` product definition, formula, latest sampled verdict, and primary action.
3. `/decisions?run=<verified-run-id>` five-symbol Market Scan.
4. Enlarged Crowd Excess matrix and evidence panel.
5. Latest run `20260831T195329Z-97994d47`: AAPL, TSLA, and QQQ evidence comparisons.
6. Failure run `20260828T174442Z-d761e38b`: eligible AAPL signal, no execution.
7. `/portfolio`: $100,000 equity; all risk and outcome values at zero.
8. Execution-authority slide: 1%, 3%, one attempt, 14–30 DTE.
9. Differentiation slide and cover.

## Conditional receipt swap

If a real paper order later appears, do not add time to this cut. Replace the 2:55–3:25 no-order
segment with the public execution trace and exact updated portfolio values. State the broker status
exactly—accepted, partial, filled, rejected, or canceled—and retain the short-sample/no-profitability
qualification. If no receipt appears, use the script above unchanged.

## Recording checklist

### Before recording

- [ ] Reopen both run links and `/portfolio`; confirm all values still match this script.
- [ ] Verify `/agent`, `/portfolio`, `/strategy`, `/lineage`, and GitHub while logged out.
- [ ] Use only public routes; hide credentials, personal tabs, emails, and private dashboards.
- [ ] Capture at 1920×1080 or 2560×1440, 30 fps, with browser zoom fixed before the first take.
- [ ] Arrange tabs in shot-list order and record a ten-second audio test.

### During recording

- [ ] Show the deployed domain and both production run IDs clearly.
- [ ] Pause on evidence metadata, abstention summary, empty execution state, and portfolio zeros.
- [ ] Call NAVER `cross-border search attention`, never community sentiment.
- [ ] Say `shadow`, `no-order result`, and `not evidence of profitability` clearly.
- [ ] Keep the final edit below the five-minute platform limit.

### After recording

- [ ] Watch the MP4 once with audio and once muted for visual legibility.
- [ ] Confirm no secret, personal identifier, notification, or private URL appears in any frame.
- [ ] Check every spoken count, timestamp, and portfolio value against production.
- [ ] Export H.264 MP4 at 1080p and retain the editable source separately.
