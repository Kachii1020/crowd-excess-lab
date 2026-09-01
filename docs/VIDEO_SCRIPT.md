# Crowd Excess Agent — 4:15 No-Order Presentation

This is the rehearsal script for the current public state. Before final recording, regenerate
`submission/fact-lock-final.json`, update only changed facts, and follow `docs/VIDEO_EDIT_SPEC.md`.
It does not imply that an option order or position exists.

## 0:00–0:20 — Thesis

**Shot:** Full-screen cover, then open the product-first Overview at
https://crowd-excess-lab.vercel.app/agent. Pause on the definition, formula, and primary action.

**Voice-over:**

> Markets react to facts, but they also react to attention. Crowd Excess asks whether attention and
> price have moved further than the objective news evidence supports. It is a pre-trade market
> reaction filter: the agent advances a controlled contrarian candidate only when deterministic
> liquidity and risk rules agree.

## 0:20–0:50 — Honest data boundary

**Shot:** Select `Review Latest Market Scan`, then show the five-symbol workbench and source status.

**Voice-over:**

> The fixed universe is Apple, Microsoft, Nvidia, Tesla, and QQQ, with SPY as the benchmark. NAVER
> supplies complete-day cross-border search attention—not sentiment. Alpaca supplies the market
> clock, prices, volume, news, options, and portfolio state. Every source is timestamped, and
> incomplete future days are excluded.

## 0:50–1:25 — AI evidence, deterministic execution

**Shot:** Show the evidence fields and then `/strategy` (`How It Works`).

**Voice-over:**

> OpenAI receives normalized market context and only the supplied Alpaca headlines. It returns a
> strict evidence assessment with direction, materiality, confidence, cited headline IDs,
> rationale, and an abstention reason. The model cannot select contracts, size positions, bypass a
> gate, or place an order. Invalid or unavailable output means abstain; deterministic code owns the
> financial decision.

## 1:25–2:20 — Latest real market-open run

**Shot:** Use `Review Latest Market Scan`, then open:
https://crowd-excess-lab.vercel.app/agent/runs/20260831T195329Z-97994d47. Pause on the five signals,
four model assessments, TSLA fail-closed evidence, and outcome.

**Voice-over:**

> This is the latest sampled run from 19:53 UTC on August 31, captured while the US market was open.
> It is one of seventeen real five-symbol scans across two market dates. Four symbols retain OpenAI
> response IDs, model metadata, token counts, and input hashes. Structured evidence for Tesla was
> unavailable, so that symbol failed closed. The final result was abstention: no symbol passed every
> attention, movement, evidence, and market gate. There is no risk decision or execution record.

## 2:20–2:55 — Failure safety

**Shot:** Open the failure-safety trace:
https://crowd-excess-lab.vercel.app/agent/runs/20260828T174442Z-d761e38b. Highlight the sanitized
summary and empty execution state.

**Voice-over:**

> This earlier market-open run proves the failure path. Alpaca market data became unavailable, the
> system suppressed request details, marked the run as abstained, and created no order or position.
> Provider failure is treated as a reason to stop, not as permission to invent data or fall back to
> an unsafe decision.

## 2:55–3:25 — Honest portfolio result

**Shot:** Open `/portfolio`; pause on equity, P&L, drawdown, open risk, and positions.

**Voice-over:**

> After seventeen sampled shadow scans across two market dates, equity remains exactly one hundred
> thousand dollars. Total
> P&L is zero, drawdown is zero, open premium risk is zero, and there are no positions. Those zeros
> are expected because the system produced zero persisted decisions and zero receipts. This is a
> verified no-order result, not evidence of profitability.

## 3:25–3:55 — Automation and duplicate safety

**Shot:** Show the architecture slide or repository workflow and watchdog files, without opening a
terminal or private service page.

**Voice-over:**

> GitHub Actions targets four scans per market hour, but hosted cron was delayed. A local fail-closed
> watchdog complements it by checking the production audit, market hours, active workflows, and a
> cooldown. It dispatched one stale shadow scan and then skipped a duplicate when the audit was
> fresh. It can request shadow analysis only; it cannot directly promote or place a paper order.
> The workflow still has to pass its independent evidence, account, liquidity, and risk gates.

## 3:55–4:15 — Close

**Shot:** Return to the cover with the public demo and repository URLs.

**Voice-over:**

> Crowd Excess Agent asks AI to assess evidence, code to enforce risk, and public audit records to
> make failure as legible as success. Seventeen sampled scans, zero receipts, no forced trade.
> Attention outruns evidence. Risk decides.

## Shot list

1. Cover image.
2. `/agent` product definition, formula, latest sampled verdict, and primary action.
3. `/decisions?run=<verified-run-id>` five-symbol Market Scan.
4. `/strategy` evidence and execution boundaries.
5. Latest run `20260831T195329Z-97994d47`: five signals, four model assessments, one fail-closed
   evidence record, abstention.
6. Failure run `20260828T174442Z-d761e38b`: sanitized provider failure, no execution.
7. `/portfolio`: $100,000 equity; all risk and outcome values at zero.
8. Architecture/repository reliability view: GitHub schedule plus local shadow watchdog.
9. Cover with public demo and source URLs.

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
- [ ] Keep the final edit between 4:00 and 4:20 and below the five-minute platform limit.

### After recording

- [ ] Watch the MP4 once with audio and once muted for visual legibility.
- [ ] Confirm no secret, personal identifier, notification, or private URL appears in any frame.
- [ ] Check every spoken count, timestamp, and portfolio value against production.
- [ ] Export H.264 MP4 at 1080p and retain the editable source separately.
