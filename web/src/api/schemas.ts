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

export type ResearchRun = z.infer<typeof runSchema>
export type EventObservation = z.infer<typeof eventSchema>
export type EventsResponse = z.infer<typeof eventsResponseSchema>
export type LineageResponse = z.infer<typeof lineageSchema>
export type Capability = z.infer<typeof capabilitySchema>
export type StageStatus = z.infer<typeof stageStatusSchema>

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
