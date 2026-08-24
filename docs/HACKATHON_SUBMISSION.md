# Hackathon Submission Package

All public claims must distinguish real paper execution, shadow decisions, and synthetic demo
fixtures. Replace bracketed fields only after verifying them in a logged-out browser.

## Project identity

**Title:** Crowd Excess Agent

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

## One-page implementation write-up

### AI logic

OpenAI receives normalized, timestamped price context and Alpaca headlines. With `store=false`, it
returns only strict `EvidenceAssessment` fields: direction, materiality, confidence, rationale,
cited supplied headline IDs, and an abstention reason. Invalid, refused, or unavailable output
causes abstention. The model never sees an order tool and cannot select quantity or contracts.

### Signal and risk

Crowd Excess combines signed SPY-adjusted movement with NAVER attention heat, then subtracts news
direction × materiality × confidence. A positive residual means upside enthusiasm appears
excessive; a negative residual means downside pessimism appears excessive. The deterministic
engine trades contrarian only after attention, move, confidence, liquidity, option shape, account,
exposure, loss, and freeze gates pass. It permits one new defined-risk debit spread per day with a
maximum debit of 1% of equity and total premium risk of 3%.

### Alpaca implementation

Alpaca CLI is the primary account, clock, and position boundary. Official market/news/options APIs
provide normalized facts. Multi-leg paper orders use the official Trading API only after exact
paper-host and competition-account verification. Every order uses a deterministic client order ID;
retries query that ID before submission. Supabase records sanitized append-only events, while the
public FastAPI/Vercel app holds only anonymous read access.

## Five-minute presentation

1. **0:00–0:30 — Thesis:** attention and price can outrun objective news.
2. **0:30–1:10 — Honest data boundary:** NAVER is search attention, not sentiment.
3. **1:10–2:20 — Live decision trace:** heat → market/news → residual → ranked candidate.
4. **2:20–3:20 — Risk and Alpaca:** defined-risk legs, failed/passed gates, deterministic ID.
5. **3:20–4:10 — Receipt and portfolio:** real paper receipt and honest P&L or abstention.
6. **4:10–5:00 — Architecture and learning:** append-only audit, failure safety, limitations.

## Asset checklist

- [ ] Public GitHub URL: `[verify]`
- [ ] Logged-out Vercel URL: `[verify]`
- [ ] Fresh $100,000 Alpaca paper account ID: `[submit securely]`
- [ ] At least one real end-to-end paper option order: `[verify receipt]`
- [ ] At least two full autonomous sessions: `[list run IDs]`
- [ ] 16:9 PNG/JPG cover: title, residual concept, Alpaca paper label
- [ ] Maximum five-minute MP4 presentation
- [ ] PDF pitch deck
- [ ] Final title and descriptions
- [ ] Up to five X/LinkedIn build-in-public links
- [ ] All visible copy is English
- [ ] Logged-out direct reload works for `/agent`, `/portfolio`, `/strategy`, and one run trace
- [ ] No fixture is represented as real execution
- [ ] No profitability claim; negative P&L remains visible if applicable

Internal submission cutoff: **September 4, 2026 at 20:00 JST**.
