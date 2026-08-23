import { useQuery } from '@tanstack/react-query'
import { api } from './client.ts'
import type { EventFilters } from './schemas.ts'

export const queryKeys = {
  runs: ['runs'] as const,
  run: (runId: string) => ['runs', runId] as const,
  events: (runId: string, filters: EventFilters) => ['runs', runId, 'events', filters] as const,
  event: (runId: string, receiptNumber: string) => ['runs', runId, 'events', receiptNumber] as const,
  lineage: (runId: string) => ['runs', runId, 'lineage'] as const,
  capabilities: ['capabilities'] as const,
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
