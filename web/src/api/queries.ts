import { useQuery } from '@tanstack/react-query'
import { api } from './client.ts'
import type { EventFilters } from './schemas.ts'

export const queryKeys = {
  agentStatus: ['agent', 'status'] as const,
  agentRuns: ['agent', 'runs'] as const,
  agentRun: (runId: string) => ['agent', 'runs', runId] as const,
  agentSignals: ['agent', 'signals'] as const,
  portfolio: ['portfolio'] as const,
  portfolioHistory: (limit: number) => ['portfolio', 'history', limit] as const,
  strategy: ['strategy'] as const,
  runs: ['runs'] as const,
  run: (runId: string) => ['runs', runId] as const,
  events: (runId: string, filters: EventFilters) => ['runs', runId, 'events', filters] as const,
  event: (runId: string, receiptNumber: string) => ['runs', runId, 'events', receiptNumber] as const,
  lineage: (runId: string) => ['runs', runId, 'lineage'] as const,
  capabilities: ['capabilities'] as const,
}

export function useAgentStatus() {
  return useQuery({ queryKey: queryKeys.agentStatus, queryFn: api.agentStatus, refetchInterval: 30_000 })
}

export function useAgentRuns() {
  return useQuery({ queryKey: queryKeys.agentRuns, queryFn: api.agentRuns, refetchInterval: 30_000 })
}

export function useAgentRun(runId: string) {
  return useQuery({
    queryKey: queryKeys.agentRun(runId),
    queryFn: () => api.agentRun(runId),
    enabled: Boolean(runId),
  })
}

export function useAgentSignals() {
  return useQuery({ queryKey: queryKeys.agentSignals, queryFn: api.agentSignals, refetchInterval: 30_000 })
}

export function usePortfolio() {
  return useQuery({ queryKey: queryKeys.portfolio, queryFn: api.portfolio, refetchInterval: 30_000 })
}

export function usePortfolioHistory(limit = 90) {
  const safeLimit = Math.min(90, Math.max(1, Number.isFinite(limit) ? Math.trunc(limit) : 90))
  return useQuery({
    queryKey: queryKeys.portfolioHistory(safeLimit),
    queryFn: () => api.portfolioHistory(safeLimit),
    refetchInterval: 30_000,
  })
}

export function useStrategy() {
  return useQuery({ queryKey: queryKeys.strategy, queryFn: api.strategy })
}

export function useRuns() {
  return useQuery({ queryKey: queryKeys.runs, queryFn: api.runs })
}

export function useRun(runId: string) {
  return useQuery({ queryKey: queryKeys.run(runId), queryFn: () => api.run(runId), enabled: Boolean(runId) })
}

export function useEvents(runId: string, filters: EventFilters = {}) {
  return useQuery({
    queryKey: queryKeys.events(runId, filters),
    queryFn: () => api.events(runId, filters),
    enabled: Boolean(runId),
  })
}

export function useEvent(runId: string, receiptNumber: string) {
  return useQuery({
    queryKey: queryKeys.event(runId, receiptNumber),
    queryFn: () => api.event(runId, receiptNumber),
    enabled: Boolean(runId && receiptNumber),
  })
}

export function useLineage(runId: string) {
  return useQuery({ queryKey: queryKeys.lineage(runId), queryFn: () => api.lineage(runId), enabled: Boolean(runId) })
}

export function useCapabilities() {
  return useQuery({ queryKey: queryKeys.capabilities, queryFn: api.capabilities })
}
