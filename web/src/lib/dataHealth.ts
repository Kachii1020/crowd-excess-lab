export type HealthState = 'Ready' | 'Not sampled' | 'Stale' | 'Error'

function isOlderThan(value: string | null, milliseconds: number, now: number) {
  if (!value) return false
  const observed = new Date(value).getTime()
  return Number.isFinite(observed) && now - observed > milliseconds
}

export function healthState(
  sampled: boolean,
  observedAt: string | null,
  error: boolean,
  now = Date.now(),
): HealthState {
  if (error) return 'Error'
  if (!sampled) return 'Not sampled'
  return isOlderThan(observedAt, 24 * 60 * 60 * 1000, now) ? 'Stale' : 'Ready'
}
