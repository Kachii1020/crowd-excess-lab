# Crowd Excess Agent — 4:30 Presentation Script

This is the final recording structure. Bracketed fields are recording blockers and must be
replaced only with verified production facts. Do not show the Alpaca account ID, credentials,
private dashboards, terminal environment variables, or synthetic fixtures.

## 0:00–0:25 — The thesis

**On screen:** Title card, then the public `/agent` console.

**Voice-over:**

> Markets do not react only to facts. They also react to attention. Crowd Excess Agent asks one
> question: when attention and price move faster than objective news evidence, is the reaction
> excessive? It turns that residual into a controlled, contrarian paper-options decision—only when
> deterministic risk rules agree.

## 0:25–0:55 — The honest data boundary

**On screen:** Source indicators and fixed AAPL, MSFT, NVDA, TSLA, QQQ universe.

**Voice-over:**

> The agent combines complete-day NAVER Search Trend, Alpaca prices, SPY-relative movement, volume,
> news, and option-chain data. NAVER is labelled cross-border search attention—not sentiment and
> not community opinion. Every input is timestamped, and incomplete future days are excluded.
> This boundary matters because a convincing signal is useless if it leaks unavailable data.

## 0:55–1:35 — AI evidence, not AI execution

**On screen:** Evidence assessment, then the architecture or lineage view.

**Voice-over:**

> OpenAI receives normalized market context and only the supplied Alpaca headlines. It returns a
> strict evidence assessment: direction, materiality, confidence, citations to those headlines,
> and an abstention reason. The model cannot choose contracts, size a position, or submit an order.
> Invalid, refused, timed-out, or unavailable output becomes abstention. This keeps language-model
> judgment narrow while deterministic code owns financial risk.

## 1:35–2:15 — The Crowd Excess decision

**On screen:** Open the verified competition-period run and move through signal snapshots and the
ranked decision matrix.

**Recording blocker:** `[MARKET_OPEN_RUN_URL]` and `[RUN_OUTCOME]`.

**Voice-over:**

> Here is run [MARKET_OPEN_RUN_ID], captured during the competition window. The agent combines
> attention heat with signed SPY-adjusted movement, then subtracts news direction, materiality, and
> confidence. The remaining value is the Crowd Excess residual. In this run, [STATE THE VERIFIED
> OUTCOME IN ONE SENTENCE: candidate and direction, or the exact abstention reason]. No threshold
> was relaxed to force a trade.

## 2:15–3:05 — Options construction and risk gates

**On screen:** Trade intent and every passed/failed risk gate.

**Voice-over:**

> A valid contrarian view can use only a 14-to-30-day call or put debit vertical. Both legs must
> have the same expiry and option type, the liquidity and Greek requirements must pass, and maximum
> debit is capped at one percent of equity. Total premium at risk is capped at three percent, with
> one new attempt per trading day. The runner also verifies the exact paper endpoint, dedicated
> active account, market hours, daily loss limit, and competition window. Any missing fact means no
> order.

## 3:05–3:45 — Alpaca receipt and honest portfolio outcome

**On screen:** Execution receipt, then `/portfolio`.

**Recording blockers:** `[RECEIPT_STATE]`, `[EXACT_PAPER_PNL]`, and `[EXACT_DRAWDOWN]`.

**Voice-over — use only after a real paper attempt:**

> Alpaca returned [RECEIPT_STATE] for the deterministic client order ID shown in this sanitized
> trace. If submission times out, the agent queries that same ID instead of immediately resending,
> which prevents duplicate exposure. After [NUMBER] autonomous sessions, paper P&L is [EXACT VALUE]
> and maximum drawdown is [EXACT VALUE]. These are short competition-period observations, not a
> profitability claim.

**Approved no-order alternative:**

> No candidate passed every gate during the recorded sessions, so there is no paper receipt or
> trading P&L to claim. The audit trail shows each abstention and its failed gate. We chose a
> truthful no-trade result instead of weakening the strategy for the demo.

## 3:45–4:15 — Reliability and auditability

**On screen:** Run lineage, provenance, and public read-only route behavior.

**Voice-over:**

> Every run records source timestamps and hashes, structured evidence, the final score, every risk
> decision, Alpaca responses, and portfolio snapshots in an append-only audit store. The public
> application is read-only: visitors can replay decisions but cannot initiate scans or orders.
> Live trading, naked options, and browser-side execution do not exist in the product.

## 4:15–4:30 — Close

**On screen:** Title, public app URL, and public GitHub URL.

**Voice-over:**

> Crowd Excess Agent does not ask AI to predict everything. It asks AI to evaluate evidence, code
> to enforce risk, and Alpaca paper trading to make every outcome verifiable. Attention outruns
> evidence. Risk decides.

## Recording checklist

### Before recording

- [ ] Replace every bracketed blocker with a verified production fact.
- [ ] Use only a competition-period market-open run for the main trace.
- [ ] Decide between the real-receipt paragraph and the approved no-order alternative; delete the
      unused paragraph.
- [ ] Verify `/agent`, selected `/agent/runs/:id`, `/portfolio`, `/strategy`, and GitHub while logged
      out.
- [ ] Confirm that receipt state, P&L, drawdown, run count, and timestamps match the public trace.
- [ ] Hide bookmarks, notifications, personal tabs, account IDs, credentials, and private dashboards.
- [ ] Use a clean 16:9 capture at 1920×1080 or 2560×1440, 30 fps, with browser zoom set before the
      first take.
- [ ] Prepare the exact tabs in narration order; do not type secret-bearing URLs on camera.
- [ ] Record a ten-second audio test and confirm speech is clear without clipping or room echo.

### During recording

- [ ] Keep the deployed domain visible at least once and show the production run ID.
- [ ] Pause briefly on the residual, failed/passed gates, receipt, and portfolio values.
- [ ] Call NAVER `cross-border search attention`, never community sentiment.
- [ ] Say `paper`, `short competition sample`, and `not a profitability claim` when discussing results.
- [ ] Do not show fixtures or imply that the pre-kickoff closed-market run was a trade.
- [ ] Keep the final cut at 4:30 or shorter; never exceed the five-minute submission limit.

### After recording

- [ ] Watch the exported MP4 end to end with audio and again muted for visual legibility.
- [ ] Verify no credential, account ID, email, notification, or private URL appears in any frame.
- [ ] Check that every spoken number and state still matches production.
- [ ] Confirm direct links work in a fresh logged-out browser before upload.
- [ ] Export H.264 MP4 at 1080p and retain the editable source separately.
