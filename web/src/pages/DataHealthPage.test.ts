import { describe, expect, it } from 'vitest'
import { healthState } from '../lib/dataHealth.ts'

const NOW = Date.parse('2026-08-31T16:00:00Z')

describe('data-health state mapping', () => {
  it('distinguishes ready, not sampled, stale, and error without treating absence as zero', () => {
    expect(healthState(true, '2026-08-31T15:00:00Z', false, NOW)).toBe('Ready')
    expect(healthState(false, null, false, NOW)).toBe('Not sampled')
    expect(healthState(true, '2026-08-29T15:00:00Z', false, NOW)).toBe('Stale')
    expect(healthState(false, null, true, NOW)).toBe('Error')
  })
})
