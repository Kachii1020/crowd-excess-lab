import { z } from 'zod'

export const stageStatusSchema = z.enum([
  'pending',
  'running',
  'complete',
  'blocked',
  'incomplete',
  'failed',
])

export const runSchema = z.object({
  run_id: z.string(),
  schema_version: z.number(),
  created_at: z.string(),
  updated_at: z.string(),
  disclosure_start_date: z.string(),
  disclosure_end_date: z.string(),
  target_events: z.number(),
  stages: z.record(z.string(), stageStatusSchema),
  counts: z.record(z.string(), z.number()),
  interpretation: z.string(),
  blockers: z.array(z.string()),
  readable: z.boolean(),
})

export const eventSchema = z.object({
  receipt_number: z.string(),
  ticker: z.string(),
  corporation_name: z.string(),
  report_name: z.string(),
  market_class: z.string(),
  received_date: z.string(),
  contract_amount_krw: z.string(),
  recent_revenue_krw: z.string(),
  reported_revenue_ratio_percent: z.string(),
  computed_revenue_ratio_percent: z.string(),
  ratio_difference_percentage_points: z.string(),
  contract_revenue_ratio: z.number(),
  baseline_observed_days: z.number().nullable(),
  event_observed_days: z.number().nullable(),
  baseline_median_ratio: z.number().nullable(),
  event_mean_ratio: z.number().nullable(),
  attention_excess: z.number().nullable(),
  attention_group: z.string(),
  attention_missing_reason: z.string(),
  decision_date: z.string().nullable(),
  raw_return_h0: z.number().nullable(),
  raw_return_h1: z.number().nullable(),
  raw_return_h3: z.number().nullable(),
  raw_return_h5: z.number().nullable(),
  market_return_h0: z.number().nullable(),
  market_return_h1: z.number().nullable(),
  market_return_h3: z.number().nullable(),
  market_return_h5: z.number().nullable(),
  abnormal_return_h0: z.number().nullable(),
  abnormal_return_h1: z.number().nullable(),
  abnormal_return_h3: z.number().nullable(),
  abnormal_return_h5: z.number().nullable(),
  price_missing_reason: z.string(),
  index_missing_reason: z.string(),
  outcome_state: z.enum(['observed', 'partial', 'missing']),
  source_document_sha256: z.string(),
  attention_source_snapshot_sha256: z.string().nullable(),
})

export const eventsResponseSchema = z.object({
  items: z.array(eventSchema),
  total: z.number(),
  offset: z.number(),
  limit: z.number(),
})

export const lineageSchema = z.object({
  groups: z.array(z.object({
    source: z.string(),
    snapshot_count: z.number(),
    byte_count: z.number(),
    first_collected_at: z.string(),
    last_collected_at: z.string(),
    retained_count: z.number(),
    missing_count: z.number(),
  })),
  items: z.array(z.object({
    source: z.string(),
    relative_path: z.string(),
    sha256: z.string(),
    byte_count: z.number(),
    collected_at: z.string(),
    retained: z.boolean(),
  })),
  total: z.number(),
})

export const capabilitySchema = z.object({
  source: z.string(),
  status: z.string(),
  access_method: z.string(),
  detail: z.string(),
  limitation: z.string(),
  checked_at: z.string(),
})

export const evidenceAssessmentSchema = z.object({
  direction: z.number(),
  materiality: z.number(),
  confidence: z.number(),
  rationale: z.string(),
  cited_headline_ids: z.array(z.string()),
  abstention_reason: z.string(),
})

export const signalSnapshotSchema = z.object({
  symbol: z.string(),
  decision_at: z.string(),
  source_as_of: z.string(),
  attention_excess: z.number().nullable(),
  attention_z: z.number().nullable(),
  market_adjusted_move: z.number(),
  move_z: z.number(),
  volume_z: z.number(),
  evidence: evidenceAssessmentSchema,
  evidence_headlines: z.array(z.record(z.string(), z.string())),
  evidence_response_id: z.string(),
  evidence_model: z.string(),
  evidence_input_sha256: z.string().nullable(),
  evidence_input_tokens: z.number(),
  evidence_output_tokens: z.number(),
  crowd_excess_score: z.number(),
  trade_direction: z.enum(['bullish', 'bearish']).nullable(),
  eligible: z.boolean(),
  missing_reason: z.string(),
})

export const optionLegSchema = z.object({
  symbol: z.string(),
  side: z.string(),
  position_intent: z.string(),
  ratio_qty: z.number(),
  strike: z.number(),
  delta: z.number(),
})

export const tradeIntentSchema = z.object({
  symbol: z.string(),
  direction: z.enum(['bullish', 'bearish']),
  option_type: z.enum(['call', 'put']),
  expiration: z.string(),
  quantity: z.number(),
  limit_debit: z.number(),
  max_loss: z.number(),
  client_order_id: z.string(),
  legs: z.tuple([optionLegSchema, optionLegSchema]),
  rationale: z.string(),
})

export const riskDecisionSchema = z.object({
  approved: z.boolean(),
  evaluated_at: z.string(),
  gates: z.array(z.object({ code: z.string(), passed: z.boolean(), detail: z.string() })),
  intent: tradeIntentSchema.nullable(),
  denial_reason: z.string(),
})

export const executionReceiptSchema = z.object({
  client_order_id: z.string(),
  alpaca_order_id: z.string().nullable(),
  state: z.enum(['shadow', 'accepted', 'partially_filled', 'filled', 'cancelled', 'rejected']),
  submitted_at: z.string(),
  filled_at: z.string().nullable(),
  limit_debit: z.number(),
  quantity: z.number(),
  legs: z.tuple([optionLegSchema, optionLegSchema]),
  response_status: z.number().nullable(),
  message: z.string(),
  action: z.enum(['open', 'close']),
  symbol: z.string(),
  direction: z.enum(['bullish', 'bearish']).nullable(),
  parent_client_order_id: z.string(),
  exit_reason: z.enum(['take_profit', 'stop_loss', 'signal_reversal', 'competition_freeze']).nullable(),
  limit_credit: z.number().nullable(),
})

export const exitIntentSchema = z.object({
  symbol: z.string(),
  quantity: z.number(),
  limit_credit: z.number(),
  client_order_id: z.string(),
  parent_client_order_id: z.string(),
  reason: z.enum(['take_profit', 'stop_loss', 'signal_reversal', 'competition_freeze']),
  pnl_ratio: z.number(),
  legs: z.tuple([optionLegSchema, optionLegSchema]),
})

export const portfolioSchema = z.object({
  account_id: z.string(),
  observed_at: z.string(),
  equity: z.number(),
  buying_power: z.number(),
  daily_pnl: z.number(),
  total_pnl: z.number(),
  drawdown: z.number(),
  open_premium_risk: z.number(),
  open_spread_count: z.number(),
  new_positions_today: z.number(),
  positions: z.array(z.object({
    symbol: z.string(),
    quantity: z.number(),
    market_value: z.number(),
    unrealized_pnl: z.number(),
  })),
})

export const agentRunSchema = z.object({
  run_id: z.string(),
  mode: z.enum(['shadow', 'paper']),
  config_version: z.string(),
  model: z.string(),
  status: z.enum(['running', 'completed', 'abstained', 'failed']),
  started_at: z.string(),
  completed_at: z.string().nullable(),
  source_hashes: z.record(z.string(), z.string()),
  summary: z.string(),
  error: z.string(),
})

export const agentRunDetailSchema = z.object({
  run: agentRunSchema,
  signals: z.array(signalSnapshotSchema),
  risk_decision: riskDecisionSchema.nullable(),
  exit_intent: exitIntentSchema.nullable(),
  receipt: executionReceiptSchema.nullable(),
  portfolio: portfolioSchema.nullable(),
})

export const agentStatusSchema = z.object({
  configured: z.boolean(),
  mode: z.enum(['shadow', 'paper']),
  scheduler: z.string(),
  last_run: agentRunSchema.nullable(),
  sources: z.record(z.string(), z.boolean()),
  message: z.string(),
})

export const strategySchema = z.object({
  version: z.string(),
  universe: z.array(z.string()),
  benchmark: z.string(),
  competition_account_id: z.string(),
  paper_base_url: z.string(),
  min_attention_z: z.number(),
  attention_weight: z.number(),
  min_move_z: z.number(),
  min_evidence_confidence: z.number(),
  max_event_materiality: z.number(),
  min_crowd_excess: z.number(),
  min_dte: z.number(),
  max_dte: z.number(),
  max_quote_width_pct: z.number(),
  max_market_data_age_seconds: z.number(),
  min_open_interest: z.number(),
  max_position_risk_pct: z.number(),
  max_total_risk_pct: z.number(),
  daily_loss_limit_pct: z.number(),
  max_open_spreads: z.number(),
  max_new_positions_per_day: z.number(),
  freeze_at: z.string(),
})

export type ResearchRun = z.infer<typeof runSchema>
export type EventObservation = z.infer<typeof eventSchema>
export type EventsResponse = z.infer<typeof eventsResponseSchema>
export type LineageResponse = z.infer<typeof lineageSchema>
export type Capability = z.infer<typeof capabilitySchema>
export type StageStatus = z.infer<typeof stageStatusSchema>
export type AgentStatus = z.infer<typeof agentStatusSchema>
export type AgentRun = z.infer<typeof agentRunSchema>
export type AgentRunDetail = z.infer<typeof agentRunDetailSchema>
export type SignalSnapshot = z.infer<typeof signalSnapshotSchema>
export type Portfolio = z.infer<typeof portfolioSchema>
export type Strategy = z.infer<typeof strategySchema>

export type EventFilters = {
  q?: string
  market?: string
  attention_group?: string
  outcome_state?: string
  sort?: string
  order?: string
  offset?: number
  limit?: number
}
