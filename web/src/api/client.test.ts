import { afterEach, describe, expect, it, vi } from 'vitest'
import { api, ApiError } from './client.ts'
import { TEST_EVENT, TEST_RUN } from '../test/fixtures.ts'

afterEach(() => vi.unstubAllGlobals())

describe('typed API client', () => {
  it('parses run contracts and preserves exact count values', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify([TEST_RUN]), { status: 200 })))
    const result = await api.runs()
    expect(result[0].counts.selected_events).toBe(1)
  })

  it('encodes event filters without leaking undefined values', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ items: [TEST_EVENT], total: 1, offset: 0, limit: 50 }), { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)
    await api.events(TEST_RUN.run_id, { q: 'Test Corporation', market: '', limit: 50 })
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/runs/20260101T000000Z/events?q=Test+Corporation&limit=50',
      expect.anything(),
    )
  })

  it('surfaces only the API safe error message', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: 'research run was not found' }), { status: 404 })))
    await expect(api.run(TEST_RUN.run_id)).rejects.toEqual(new ApiError('research run was not found', 404))
  })
})
