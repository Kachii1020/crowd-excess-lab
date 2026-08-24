import type { Page } from '@playwright/test'

const RUN_ID = '20260831T150000Z-1234abcd'
const evidence = {
  direction: 0,
  materiality: 0.1,
  confidence: 0.91,
  rationale: 'Synthetic judge-path headlines do not explain the observed move.',
  cited_headline_ids: ['fixture-news-1'],
  abstention_reason: '',
}
const signal = {
  symbol: 'AAPL',
  decision_at: '2026-08-31T15:00:00Z',
  source_as_of: '2026-08-31T15:00:00Z',
  attention_excess: 0.82,
  attention_z: 2.35,
  market_adjusted_move: 0.028,
  move_z: 1.74,
  volume_z: 1.22,
  evidence,
  evidence_headlines: [{ id: 'fixture-news-1', headline: 'Synthetic headline for the judge-path fixture', summary: 'Clearly labelled fixture.', created_at: '2026-08-31T14:30:00Z', source: 'fixture' }],
  evidence_response_id: 'resp_fixture_only',
  evidence_model: 'gpt-5.6-terra',
  evidence_input_sha256: 'a'.repeat(64),
  evidence_input_tokens: 240,
  evidence_output_tokens: 84,
  crowd_excess_score: 0.37,
  trade_direction: 'bearish',
  eligible: true,
  missing_reason: '',
}
const legs = [
  { symbol: 'AAPL260918P00200000', side: 'buy', position_intent: 'buy_to_open', ratio_qty: 1, strike: 200, delta: -0.52 },
  { symbol: 'AAPL260918P00190000', side: 'sell', position_intent: 'sell_to_open', ratio_qty: 1, strike: 190, delta: -0.28 },
]
const intent = {
  symbol: 'AAPL', direction: 'bearish', option_type: 'put', expiration: '2026-09-18',
  quantity: 2, limit_debit: 2.9, max_loss: 580, client_order_id: 'ce-fixture-judge-path',
  legs, rationale: 'Synthetic fixture: contrarian bearish debit spread.',
}
const risk = {
  approved: true,
  evaluated_at: '2026-08-31T15:00:00Z',
  gates: [
    { code: 'paper_endpoint', passed: true, detail: 'Exact Alpaca paper host is required.' },
    { code: 'competition_account', passed: true, detail: 'Dedicated competition account matched.' },
    { code: 'signal_eligible', passed: true, detail: 'Signal thresholds passed.' },
    { code: 'contract_family', passed: true, detail: 'Defined-risk option family passed.' },
    { code: 'quote_width', passed: true, detail: 'Quote width passed.' },
    { code: 'total_risk', passed: true, detail: 'Total risk remained under three percent.' },
  ],
  intent,
  denial_reason: '',
}
const portfolio = {
  account_id: 'fixture-paper-account', observed_at: '2026-08-31T15:00:00Z', equity: 100250,
  buying_power: 96500, daily_pnl: 250, total_pnl: 250, drawdown: 0, open_premium_risk: 580,
  open_spread_count: 1, new_positions_today: 1, positions: [],
}
const run = {
  run_id: RUN_ID, mode: 'shadow', config_version: '2026-08-hackathon-v1', model: 'gpt-5.6-terra',
  status: 'completed', started_at: '2026-08-31T15:00:00Z', completed_at: '2026-08-31T15:00:04Z',
  source_hashes: { naver_aapl: 'b'.repeat(64), alpaca_market_aapl: 'c'.repeat(64) },
  summary: 'Synthetic judge-path shadow intent recorded.', error: '',
}
const receipt = {
  client_order_id: 'ce-fixture-judge-path', alpaca_order_id: null, state: 'shadow',
  submitted_at: '2026-08-31T15:00:00Z', filled_at: null, limit_debit: 2.9, quantity: 2,
  legs, response_status: null, message: 'Synthetic fixture: no order was submitted.',
  action: 'open', symbol: 'AAPL', direction: 'bearish', parent_client_order_id: '',
  exit_reason: null, limit_credit: null,
}
const strategy = {
  version: '2026-08-hackathon-v1', universe: ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'QQQ'], benchmark: 'SPY',
  competition_account_id: 'fixture-paper-account', paper_base_url: 'https://paper-api.alpaca.markets',
  min_attention_z: 1.25, attention_weight: 1, min_move_z: 1, min_evidence_confidence: 0.6, max_event_materiality: 0.85, min_crowd_excess: 0.2,
  min_dte: 14, max_dte: 30, max_quote_width_pct: 0.15, max_market_data_age_seconds: 120, min_open_interest: 100,
  max_position_risk_pct: 0.01, max_total_risk_pct: 0.03, daily_loss_limit_pct: 0.015,
  max_open_spreads: 3, max_new_positions_per_day: 1, freeze_at: '2026-09-03T20:00:00Z',
}

async function jsonRoute(page: Page, path: string, body: unknown) {
  await page.route(`**${path}`, (route) => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(body),
  }))
}

export async function installAgentFixture(page: Page) {
  await jsonRoute(page, '/api/v1/agent/status', {
    configured: true, mode: 'shadow', scheduler: 'Synthetic test scheduler', last_run: run,
    sources: { naver_aapl: true, alpaca_market_aapl: true },
    message: 'Synthetic Playwright fixture; not a real execution.',
  })
  await jsonRoute(page, '/api/v1/agent/runs', [run])
  await jsonRoute(page, `/api/v1/agent/runs/${RUN_ID}`, {
    run, signals: [signal], risk_decision: risk, exit_intent: null, receipt, portfolio,
  })
  await jsonRoute(page, '/api/v1/agent/signals', [signal])
  await jsonRoute(page, '/api/v1/portfolio', portfolio)
  await jsonRoute(page, '/api/v1/strategy', strategy)
}

export { RUN_ID }
