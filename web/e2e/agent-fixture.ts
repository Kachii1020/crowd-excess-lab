import type { Page } from '@playwright/test'

const RUN_ID = '20260831T150000Z-1234abcd'
const CLOSED_RUN_ID = '20260831T110000Z-c10ced00'
const QUOTE_RUN_ID = '20260831T151000Z-90a7e123'
const POST_SAMPLE_FAILURE_RUN_ID = '20260831T153000Z-fa11ed00'

const signalInputs = [
  { symbol: 'AAPL', attentionExcess: 0.82, attentionZ: 2.35, move: 0.028, moveZ: 1.74, volumeZ: 1.22, residual: 0.37, eligible: true, hash: 'a' },
  { symbol: 'MSFT', attentionExcess: 0.31, attentionZ: 1.08, move: -0.009, moveZ: -0.72, volumeZ: 0.44, residual: -0.16, eligible: false, hash: 'b' },
  { symbol: 'NVDA', attentionExcess: 0.48, attentionZ: 1.42, move: 0.012, moveZ: 0.91, volumeZ: 0.76, residual: 0.19, eligible: false, hash: 'c' },
  { symbol: 'TSLA', attentionExcess: -0.12, attentionZ: -0.64, move: -0.015, moveZ: -1.08, volumeZ: 1.04, residual: -0.21, eligible: false, hash: 'd' },
  { symbol: 'QQQ', attentionExcess: 0.09, attentionZ: 0.38, move: 0.004, moveZ: 0.29, volumeZ: -0.18, residual: 0.06, eligible: false, hash: 'e' },
]

const quoteSignals = signalInputs.map((input) => ({
  symbol: input.symbol,
  decision_at: '2026-08-31T15:00:00Z',
  source_as_of: '2026-08-31T15:00:00Z',
  attention_excess: input.attentionExcess,
  attention_z: input.attentionZ,
  market_adjusted_move: input.move,
  move_z: input.moveZ,
  volume_z: input.volumeZ,
  evidence: {
    direction: 0,
    materiality: 0.1,
    confidence: input.symbol === 'AAPL' ? 0.91 : 0.82,
    rationale: input.symbol === 'AAPL'
      ? 'Synthetic five-symbol fixture: supplied headlines do not explain the observed AAPL move.'
      : `Synthetic five-symbol fixture: ${input.symbol} evidence remained non-material.`,
    cited_headline_ids: [`fixture-news-${input.symbol.toLowerCase()}`],
    abstention_reason: '',
  },
  evidence_headlines: [{
    id: `fixture-news-${input.symbol.toLowerCase()}`,
    headline: `Synthetic ${input.symbol} headline for the immutable test trace`,
    summary: 'Clearly labelled synthetic fixture; never represented as execution.',
    created_at: '2026-08-31T14:30:00Z',
    source: 'fixture',
  }],
  evidence_response_id: `resp_fixture_${input.symbol.toLowerCase()}`,
  evidence_model: 'gpt-5.6-terra',
  evidence_input_sha256: input.hash.repeat(64),
  evidence_input_tokens: 240,
  evidence_output_tokens: 84,
  crowd_excess_score: input.residual,
  trade_direction: input.eligible ? 'bearish' : null,
  eligible: input.eligible,
  missing_reason: input.eligible ? '' : 'Synthetic fixture: the fixed signal threshold was not met.',
}))
const signals = quoteSignals.map((signal) => ({
  ...signal,
  evidence: {
    ...signal.evidence,
    confidence: 0,
    rationale: 'OpenAI structured evidence was unavailable; this signal abstained.',
    cited_headline_ids: [],
    abstention_reason: 'openai_evidence_unavailable',
  },
  evidence_headlines: [],
  evidence_response_id: '',
  evidence_input_sha256: null,
  evidence_input_tokens: 0,
  evidence_output_tokens: 0,
  trade_direction: null,
  eligible: false,
  missing_reason: 'openai_evidence_unavailable',
}))

const legs = [
  { symbol: 'AAPL260918P00200000', side: 'buy', position_intent: 'buy_to_open', ratio_qty: 1, strike: 200, delta: -0.52 },
  { symbol: 'AAPL260918P00190000', side: 'sell', position_intent: 'sell_to_open', ratio_qty: 1, strike: 190, delta: -0.28 },
]
const intent = {
  symbol: 'AAPL', direction: 'bearish', option_type: 'put', expiration: '2026-09-18',
  quantity: 2, limit_debit: 2.9, max_loss: 580, client_order_id: 'ce-fixture-five-symbol',
  legs, rationale: 'Synthetic fixture: contrarian bearish debit spread candidate.',
}
const risk = {
  approved: false,
  evaluated_at: '2026-08-31T15:00:02Z',
  gates: [
    { code: 'paper_endpoint', passed: true, detail: 'Exact Alpaca paper host is required.' },
    { code: 'competition_account', passed: true, detail: 'Dedicated competition account matched.' },
    { code: 'signal_eligible', passed: true, detail: 'The synthetic AAPL signal thresholds passed.' },
    { code: 'contract_family', passed: true, detail: 'Defined-risk option family passed.' },
    { code: 'quote_width', passed: false, detail: 'Synthetic quote width exceeded the declared 15% maximum.' },
    { code: 'total_risk', passed: true, detail: 'Total risk remained under three percent.' },
  ],
  intent,
  denial_reason: 'quote_width: synthetic spread exceeded the declared liquidity limit',
}

const history = [
  {
    account_id: 'fixture-paper-account', observed_at: '2026-08-31T14:00:00Z', equity: 100000,
    buying_power: 100000, daily_pnl: 0, total_pnl: 0, drawdown: 0, open_premium_risk: 0,
    open_spread_count: 0, new_positions_today: 0, positions: [],
  },
  {
    account_id: 'fixture-paper-account', observed_at: '2026-08-31T14:30:00Z', equity: 99980,
    buying_power: 99980, daily_pnl: -20, total_pnl: -20, drawdown: 0.0002, open_premium_risk: 0,
    open_spread_count: 0, new_positions_today: 0, positions: [],
  },
  {
    account_id: 'fixture-paper-account', observed_at: '2026-08-31T15:00:00Z', equity: 100025,
    buying_power: 100025, daily_pnl: 25, total_pnl: 25, drawdown: 0, open_premium_risk: 0,
    open_spread_count: 0, new_positions_today: 0, positions: [],
  },
]
const portfolio = history.at(-1)!
const closedPortfolio = history[0]

const sourceHashes = Object.fromEntries(signalInputs.flatMap(({ symbol, hash }) => {
  const key = symbol.toLowerCase()
  return [
    [`naver_${key}`, hash.repeat(64)],
    [`alpaca_market_${key}`, hash.repeat(64)],
  ]
}))
const quoteSourceHashes = {
  ...sourceHashes,
  ...Object.fromEntries(signalInputs.map(({ symbol, hash }) => [`openai_evidence_${symbol.toLowerCase()}`, hash.repeat(64)])),
  alpaca_options_aapl: 'f'.repeat(64),
}

const run = {
  run_id: RUN_ID, mode: 'shadow', config_version: '2026-08-hackathon-v1', model: 'gpt-5.6-terra',
  status: 'abstained', started_at: '2026-08-31T15:00:00Z', completed_at: '2026-08-31T15:00:04Z',
  market_clock: {
    observed_at: '2026-08-31T15:00:00Z', is_open: true,
    next_open: null, next_close: '2026-08-31T20:00:00Z',
  },
  source_hashes: sourceHashes,
  summary: 'No symbol passed complete evidence validation; five signals abstained before option construction.',
  error: '',
}
const closedRun = {
  run_id: CLOSED_RUN_ID, mode: 'shadow', config_version: '2026-08-hackathon-v1', model: 'gpt-5.6-terra',
  status: 'abstained', started_at: '2026-08-31T11:00:00Z', completed_at: '2026-08-31T11:00:01Z',
  source_hashes: {},
  summary: 'Market closed; outside the configured US market window.', error: '',
  // Deliberately no market_clock: this is the immutable pre-clock compatibility row.
}
const quoteRun = {
  run_id: QUOTE_RUN_ID, mode: 'shadow', config_version: '2026-08-hackathon-v1', model: 'gpt-5.6-terra',
  status: 'abstained', started_at: '2026-08-31T15:10:00Z', completed_at: '2026-08-31T15:10:04Z',
  market_clock: {
    observed_at: '2026-08-31T15:10:00Z', is_open: true,
    next_open: null, next_close: '2026-08-31T20:00:00Z',
  },
  source_hashes: quoteSourceHashes,
  summary: 'Synthetic five-symbol scan abstained at the deterministic quote-width gate.',
  error: '',
}
const postSampleFailureRun = {
  ...quoteRun,
  run_id: POST_SAMPLE_FAILURE_RUN_ID,
  status: 'failed',
  started_at: '2026-08-31T15:30:00Z',
  completed_at: '2026-08-31T15:30:04Z',
  market_clock: {
    observed_at: '2026-08-31T15:30:00Z', is_open: true,
    next_open: null, next_close: '2026-08-31T20:00:00Z',
  },
  summary: 'Synthetic post-sampling audit failure; no order was attempted.',
  error: 'Synthetic failure after provider and risk records were persisted.',
}

const strategy = {
  version: '2026-08-hackathon-v1', universe: ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'QQQ'], benchmark: 'SPY',
  competition_account_id: 'fixture-paper-account', paper_base_url: 'https://paper-api.alpaca.markets',
  min_attention_z: 1.25, attention_weight: 1, min_move_z: 1, min_evidence_confidence: 0.6, max_event_materiality: 0.85, min_crowd_excess: 0.2,
  min_dte: 14, max_dte: 30, max_quote_width_pct: 0.15, max_market_data_age_seconds: 120, min_open_interest: 100,
  max_position_risk_pct: 0.01, max_total_risk_pct: 0.03, daily_loss_limit_pct: 0.015,
  max_open_spreads: 3, max_new_positions_per_day: 1, freeze_at: '2026-09-03T20:00:00Z',
}

async function jsonRoute(page: Page, path: string, body: unknown, status = 200) {
  await page.route(`**${path}`, (route) => route.fulfill({
    status,
    contentType: 'application/json',
    body: JSON.stringify(body),
  }))
}

async function installShared(page: Page, options: {
  latestRun: typeof run | typeof closedRun | typeof quoteRun | typeof postSampleFailureRun,
  runs: Array<typeof run | typeof closedRun | typeof quoteRun | typeof postSampleFailureRun>,
  details: Array<{ runId: string, body: unknown }>,
  latestSignals: unknown[],
  currentPortfolio: typeof portfolio,
  portfolioHistory: typeof history,
  sources: Record<string, boolean>,
  message: string,
}) {
  await jsonRoute(page, '/api/v1/agent/status', {
    configured: true,
    mode: 'shadow',
    scheduler: 'Synthetic test scheduler',
    last_run: options.latestRun,
    sources: options.sources,
    message: options.message,
  })
  await jsonRoute(page, '/api/v1/agent/runs', options.runs)
  for (const detail of options.details) {
    await jsonRoute(page, `/api/v1/agent/runs/${detail.runId}`, detail.body)
  }
  await jsonRoute(page, '/api/v1/agent/signals', options.latestSignals)
  await jsonRoute(page, '/api/v1/portfolio', options.currentPortfolio)
  await jsonRoute(page, '/api/v1/portfolio/history?limit=90', options.portfolioHistory)
  await jsonRoute(page, '/api/v1/strategy', strategy)
}

const runDetail = {
  run, signals, risk_decision: null, exit_intent: null, receipt: null, portfolio,
}
const closedRunDetail = {
  run: closedRun, signals: [], risk_decision: null, exit_intent: null, receipt: null, portfolio: closedPortfolio,
}
const quoteRunDetail = {
  run: quoteRun, signals: quoteSignals, risk_decision: risk, exit_intent: null, receipt: null, portfolio,
}
const postSampleFailureDetail = {
  run: postSampleFailureRun, signals: quoteSignals, risk_decision: risk, exit_intent: null, receipt: null, portfolio,
}

export async function installAgentFixture(page: Page) {
  await installShared(page, {
    latestRun: run,
    runs: [run, closedRun],
    details: [
      { runId: RUN_ID, body: runDetail },
      { runId: CLOSED_RUN_ID, body: closedRunDetail },
    ],
    latestSignals: signals,
    currentPortfolio: portfolio,
    portfolioHistory: history,
    sources: { naver_aapl: true, alpaca_market_aapl: true, alpaca_options_aapl: false, openai_evidence_aapl: false },
    message: 'Production-shaped five-symbol kickoff abstention fixture; all evidence assessments were unavailable.',
  })
}

export async function installOneRunFixture(page: Page) {
  await installShared(page, {
    latestRun: run,
    runs: [run],
    details: [{ runId: RUN_ID, body: runDetail }],
    latestSignals: signals,
    currentPortfolio: portfolio,
    portfolioHistory: history,
    sources: { naver_aapl: true, alpaca_market_aapl: true, alpaca_options_aapl: false, openai_evidence_aapl: false },
    message: 'Production-shaped one-run fixture; comparison is unavailable.',
  })
}

export async function installClosedMarketFixture(page: Page) {
  await installShared(page, {
    latestRun: closedRun,
    runs: [closedRun],
    details: [{ runId: CLOSED_RUN_ID, body: closedRunDetail }],
    latestSignals: [],
    currentPortfolio: closedPortfolio,
    portfolioHistory: [closedPortfolio],
    // Status sources are intentionally cumulative from an earlier sampled run. The
    // latest clockless run itself has no hashes and must still render Not sampled.
    sources: { naver_aapl: true, alpaca_market_aapl: true, alpaca_options_aapl: true, openai_evidence_aapl: true },
    message: 'Synthetic closed-market fixture after an earlier sampled run; no provider was sampled in the latest run.',
  })
}

export async function installQuoteWidthFixture(page: Page) {
  await installShared(page, {
    latestRun: quoteRun,
    runs: [quoteRun],
    details: [{ runId: QUOTE_RUN_ID, body: quoteRunDetail }],
    latestSignals: quoteSignals,
    currentPortfolio: portfolio,
    portfolioHistory: history,
    sources: { naver_aapl: true, alpaca_market_aapl: true, alpaca_options_aapl: true, openai_evidence_aapl: true },
    message: 'Clearly labelled synthetic quote-width risk fixture; no order was attempted.',
  })
}

export async function installPostSampleFailureFixture(page: Page) {
  await installShared(page, {
    latestRun: postSampleFailureRun,
    runs: [postSampleFailureRun],
    details: [{ runId: POST_SAMPLE_FAILURE_RUN_ID, body: postSampleFailureDetail }],
    latestSignals: quoteSignals,
    currentPortfolio: portfolio,
    portfolioHistory: history,
    sources: { naver_aapl: true, alpaca_market_aapl: true, alpaca_options_aapl: true, openai_evidence_aapl: true },
    message: 'Synthetic failed run after provider records persisted; provider health remains independently attributable.',
  })
}

export { CLOSED_RUN_ID, POST_SAMPLE_FAILURE_RUN_ID, QUOTE_RUN_ID, RUN_ID }
