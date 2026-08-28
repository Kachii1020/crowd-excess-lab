import { z } from 'zod'
import {
  agentRunDetailSchema,
  agentRunSchema,
  agentStatusSchema,
  capabilitySchema,
  eventSchema,
  eventsResponseSchema,
  lineageSchema,
  portfolioHistorySchema,
  portfolioSchema,
  runSchema,
  signalSnapshotSchema,
  strategySchema,
  type EventFilters,
} from './schemas.ts'

export class ApiError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function fetchParsed<T>(path: string, schema: z.ZodType<T>): Promise<T> {
  const response = await fetch(path, { headers: { Accept: 'application/json' } })
  if (!response.ok) {
    let message = `The request could not be completed (${response.status})`
    try {
      const payload = await response.json() as { detail?: string }
      if (payload.detail) message = payload.detail
    } catch {
      // Keep the safe status-based message when the response is not JSON.
    }
    throw new ApiError(message, response.status)
  }
  return schema.parse(await response.json())
}

function queryString(filters: EventFilters): string {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== '') params.set(key, String(value))
  })
  const encoded = params.toString()
  return encoded ? `?${encoded}` : ''
}

export const api = {
  agentStatus: () => fetchParsed('/api/v1/agent/status', agentStatusSchema),
  agentRuns: () => fetchParsed('/api/v1/agent/runs', z.array(agentRunSchema)),
  agentRun: (runId: string) => fetchParsed(`/api/v1/agent/runs/${runId}`, agentRunDetailSchema),
  agentSignals: () => fetchParsed('/api/v1/agent/signals', z.array(signalSnapshotSchema)),
  portfolio: () => fetchParsed('/api/v1/portfolio', portfolioSchema.nullable()),
  portfolioHistory: (limit = 90) => {
    const safeLimit = Math.min(90, Math.max(1, Number.isFinite(limit) ? Math.trunc(limit) : 90))
    return fetchParsed(`/api/v1/portfolio/history?limit=${safeLimit}`, portfolioHistorySchema)
  },
  strategy: () => fetchParsed('/api/v1/strategy', strategySchema),
  runs: () => fetchParsed('/api/v1/runs', z.array(runSchema)),
  run: (runId: string) => fetchParsed(`/api/v1/runs/${runId}`, runSchema),
  events: (runId: string, filters: EventFilters = {}) =>
    fetchParsed(`/api/v1/runs/${runId}/events${queryString(filters)}`, eventsResponseSchema),
  event: (runId: string, receiptNumber: string) =>
    fetchParsed(`/api/v1/runs/${runId}/events/${receiptNumber}`, eventSchema),
  lineage: (runId: string) => fetchParsed(`/api/v1/runs/${runId}/lineage`, lineageSchema),
  capabilities: () => fetchParsed('/api/v1/capabilities', z.array(capabilitySchema)),
}
