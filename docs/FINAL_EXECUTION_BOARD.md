# Crowd Excess — Final Execution Board

Status timestamp: **2026-09-01 JST**

Internal submission cutoff: **2026-09-04 20:00 JST**

Public event window: **2026-08-28 through 2026-09-04**

Frozen production release: `3413c66` on `main`

## 1. Objective

Submit one truthful, reproducible judge path:

```text
Overview
  -> latest sampled market-open run
  -> evidence and Crowd Excess residual
  -> deterministic stop / risk boundary
  -> no-order or real Alpaca paper receipt
  -> verified portfolio state
```

The baseline submission does not require a trade. A natural paper receipt is a score-upside branch,
not a completion dependency.

## 2. Freeze contract

Allowed before submission:

- collect a second independent market session;
- update fact counts, screenshots, deck, video, and form copy from real audit records;
- fix only a release-critical security, duplicate-order, or public-availability defect;
- perform read-only monitoring and submission QA.

Not allowed:

- threshold changes;
- forced paper dispatch;
- universe, strategy, signal, model-role, or option-structure changes;
- new providers, crawlers, backtests, or UI redesign;
- synthetic production evidence;
- retroactive mutation of immutable audit rows.

## 3. Current gates

| Gate | State | Evidence |
|---|---|---|
| Code and CI | GO | Clean `main`; exact-HEAD CI passed |
| Production | GO | All judge routes work logged out |
| Public redaction | GO | Zero public account identifier keys |
| First market session | GO | Seven real five-symbol shadow scans on 2026-08-28 |
| Submission assets | GO | Cover, screenshots, fact-locked PPTX/PDF, copy, and 4:08 MP4 ready |
| Second market session | GO | Ten additional five-symbol sampled scans on 2026-08-31 |
| Fact lock | GO | 17 sampled runs, 85 signals, 78 model assessments, two market dates, no-order branch |
| Submission portal | OPERATOR REQUIRED | Exact cutoff, uploads, private account field, and confirmation unverified |
| Monday automation | CONDITIONAL GO | Watchdog healthy; Mac sleep prevention required |

Readiness is tracked in two ways:

- technical release readiness: **100%**;
- actual submission-package readiness: **about 96%** because only portal upload and final confirmation remain.

## 4. Active work plan

| Order | Work | Owner | Intensity | Active time | Dependency | Done evidence |
|---:|---|---|---|---:|---|---|
| 1 | Confirm project/team registration and exact portal cutoff | User + agent browser support | L4 | 20 min | Logged-in portal | Screenshot or note with exact cutoff and project state |
| 2 | Rehearse the AI-narrated no-order video once; test audio and browser tab order | User | L3 | 45–60 min | Current production | 30-second audio test and one unedited rehearsal |
| 3 | Rehearse Monday operational checks without dispatching | Agent | L4 | 20 min | Mac available | launchd, auth, production, portfolio, and power checks understood |
| 4 | Capture the second independent session | Agent automation + user monitor | L4 | Complete | 2026-08-31 session | Ten full five-symbol sampled runs recorded |
| 5 | Generate the sanitized post-session fact lock and select the no-order or receipt branch | Agent | L4 | Complete | Session evidence | `submission/fact-lock-final.json` passed the two-date gate |
| 6 | Record and edit final 4:00–4:20 MP4 | Agent + user review | L4 | Complete | Fact lock | 4:08 H.264 1080p MP4 with captions; audio/visual QA passed |
| 7 | Update only changed counts/frames in docs or deck | Agent | L3 | Complete | Fact lock | 17 runs, 85 signals, and 78 assessments synchronized |
| 8 | Upload and submit | User + agent browser support | L4 | 45–60 min | Final MP4 | All files reopen; private account ID only in private field; confirmation captured |
| 9 | Optional verified social posts | User | L2 | 20–30 min | Fact lock | Public links recorded; not a submission blocker |

Expected remaining active work:

- agent-side: **2.5–3.5 hours**;
- user-side: **3–4 hours**, primarily recording and portal actions;
- market-session monitoring: **about 1 hour active**, plus elapsed wait.

## 5. Weekend preparation window

Complete by **2026-08-30 20:00 JST**:

1. Open the logged-in lablab project page.
2. Confirm the team/project exists, the exact submission cutoff, accepted file formats, and whether
   the Alpaca account ID has a private field.
3. Do not submit yet; save the draft fields from `docs/HACKATHON_SUBMISSION.md`.
4. Arrange clean browser tabs in this order:
   - `/agent`;
   - stable sampled run `20260828T193701Z-b404b62a`;
   - failure run `20260828T174442Z-d761e38b`;
   - `/portfolio`;
   - public GitHub repository.
5. The deck aggregate is fact-locked to `85 signal snapshots · 78 model assessments` across 17
   sampled runs and two US market dates.
6. Record one short AI-narration/video rehearsal using `docs/VIDEO_SCRIPT.md` and
   `docs/VIDEO_EDIT_SPEC.md`.
7. Lock this business-value statement:

> Crowd Excess is an audit workspace for quant researchers, risk reviewers, and autonomous-agent
> operators. It makes evidence and fixed risk gates inspectable before capital is exposed, and
> preserves a reproducible no-trade record when inputs are weak. A commercial path is a read-only
> oversight SaaS/API for paper-agent research and model-risk review; no market-size or traction
> claim is made in this prototype.

## 6. Monday session runbook

Monday, **2026-08-31**, is a normal NYSE session. Regular hours are **22:30 JST Monday to 05:00 JST
Tuesday**. August 31 is also an MSCI index-rebalance date, so close-session price and volume are a
potential confound and must not be described as pure crowd behavior.

### 21:45 JST — pre-open

1. Connect the Mac to AC power and remain logged in and online.
2. Prevent sleep for 7.5 hours:

   ```bash
   /usr/bin/caffeinate -is -t 27000
   ```

3. Verify the sleep assertion, launchd enabled state, watchdog last exit `0`, fresh log, empty error
   log, GitHub authentication, active Agent workflow, production status `200/configured`, and a
   `$100,000` zero-exposure portfolio.
4. Confirm `AGENT_MODE=shadow` and `AUTO_PAPER_ON_APPROVED_SHADOW=true`.
5. Do not delete watchdog state and do not manually dispatch while the system is healthy.

### 22:30–22:50 JST — first open run

Healthy watchdog outcomes are `dispatched`, `workflow_already_active`, `audit_is_fresh`, or
`local_cooldown_active`.

By 22:50, verify:

- `market_clock.is_open=true`;
- exactly five signal snapshots if providers succeed;
- strict OpenAI evidence IDs and hashes;
- a portfolio snapshot;
- either an honest abstention or a risk/receipt trace.

### During the session

- Check again near 23:30 JST; target three full scans but require only one.
- Do not loosen gates or create a duplicate manual run.
- If automatic paper promotion occurs, stop manual actions and inspect the deterministic client ID,
  spread legs, maximum loss, gates, and receipt.
- A timeout means lookup by the same client ID, never a new submission.
- Preserve partial, rejected, canceled, and negative outcomes exactly as observed.

### 05:15 JST — post-session

- Confirm the watchdog returns to `outside_regular_market_hours`.
- Confirm there is no active workflow.
- Record all market-open run IDs and separately pin the last actual market-open run.
- Record signals, abstention/order, equity, P&L, drawdown, open risk, receipt state, and
  `fail_closed` count.
- A delayed closed-market cron run must not replace the market-open demo entry.

## 7. Failure branches

| Failure | Action |
|---|---|
| Mac slept or log is stale | Restore AC/awake/login/network, check for an active workflow, then wait up to five minutes for the next watchdog tick |
| Audit/Supabase unavailable | No paper action; wait for read recovery |
| GitHub auth unavailable | Reauthenticate interactively; never put a token in the plist |
| Dispatch result ambiguous | Cooldown is already reserved; query GitHub and do not retry immediately |
| Active run exceeds 15 minutes | Inspect the existing job; do not start a second run |
| Workflow succeeds but audit is missing | Inspect the sanitized storage boundary; do not paper-retry |
| OpenAI/NAVER/Alpaca fails | Accept the abstention and wait for the next cycle |
| Alpaca clock says closed | Alpaca clock wins; never override it |
| More than one non-shadow receipt appears | Disable automatic promotion before any further run and investigate |

## 8. Post-session content branch

### Baseline: no order

Use:

> No candidate passed every evidence, liquidity, and risk gate. The agent made no trade and
> preserved the paper account without lowering thresholds.

### Stretch: natural receipt

Replace only the declared conditional segment with the exact deterministic ID, legs, maximum loss,
gate results, broker state, and updated portfolio facts. Never call accepted, partial, rejected, or
canceled an executed fill.

Historical run `20260828T174442Z-d761e38b` predates `failure_stage` and `failure_code`. Do not claim
those fields were observed in that row. They are implemented and tested; production evidence exists
only if a new run records them naturally.

## 9. Submission-day timeline

| Time | Gate |
|---|---|
| Sep 2, 20:00 JST | Target: final MP4, PDF, cover, copy, and links ready |
| Sep 3, 20:00 JST | Logged-out rehearsal and uploaded-file dry check complete |
| Sep 4, 16:00 JST | Hard freeze on code, schema, deck structure, and strategy claims |
| Sep 4, 18:00 JST | All portal fields and files loaded; second-person-style fact pass |
| Sep 4, 20:00 JST | Internal submission cutoff; confirmation page and timestamp captured |

The portal's exact official cutoff overrides this internal schedule after it is confirmed in the
logged-in project page.

## 10. Final release gate

Submission is complete only when all are true:

- second-session result is either recorded or explicitly documented as externally unavailable;
- final MP4 opens, is under five minutes, and has correct audio;
- cover, PDF, repository, and app URL open from the portal;
- every number matches the immutable audit;
- no public account identifier, credential, fixture, or fabricated result appears;
- private Alpaca account ID exists only in the designated private portal field;
- logged-out GitHub and Vercel paths work;
- submission confirmation and timestamp are saved.

## 11. Sources

- Event and submission requirements: https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon
- NYSE hours and calendar: https://www.nyse.com/trade/hours-calendars
- Production: https://crowd-excess-lab.vercel.app/agent
- Repository: https://github.com/Kachii1020/crowd-excess-lab
