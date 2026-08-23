import { Filter, RefreshCw, RotateCcw, Search } from 'lucide-react'
import { useOutletContext, useSearchParams } from 'react-router-dom'
import { useEvents } from '../api/queries.ts'
import type { EventFilters } from '../api/schemas.ts'
import type { WorkspaceContext } from '../components/AppShell.tsx'
import { EventAnalyticsPanel } from '../components/EventAnalyticsPanel.tsx'
import { EventTable } from '../components/EventTable.tsx'
import { EvidenceInspector } from '../components/EvidenceInspector.tsx'
import { EmptyState, ErrorState, LoadingState } from '../components/States.tsx'
import { format } from '../lib/format.ts'

type SortField = 'received_date' | 'corporation_name' | 'contract_revenue_ratio' | 'attention_excess' | 'abnormal_return_h1'

export function EventsPage() {
  const { runId } = useOutletContext<WorkspaceContext>()
  const [params, setParams] = useSearchParams()
  const filters: EventFilters = {
    q: params.get('q') ?? '',
    market: params.get('market') ?? '',
    attention_group: params.get('attention') ?? '',
    outcome_state: params.get('outcome') ?? '',
    sort: params.get('sort') ?? 'received_date',
    order: params.get('order') ?? 'desc',
    limit: 50,
  }
  const events = useEvents(runId, filters)

  const setFilter = (key: string, value: string) => {
    setParams((current) => {
      const next = new URLSearchParams(current)
      if (value) next.set(key, value)
      else next.delete(key)
      return next
    }, { replace: true })
  }
  const onSort = (field: SortField) => {
    const sameField = filters.sort === field
    setParams((current) => {
      const next = new URLSearchParams(current)
      next.set('sort', field)
      next.set('order', sameField && filters.order === 'desc' ? 'asc' : 'desc')
      return next
    }, { replace: true })
  }
  const selectEvent = (receiptNumber: string) => setFilter('event', receiptNumber)

  if (!runId) return <EmptyState title="No research run is available" />
  if (events.isLoading) return <LoadingState label="Building the event monitor" />
  if (events.error) return <ErrorState error={events.error} retry={() => void events.refetch()} />

  const items = events.data?.items ?? []
  const total = events.data?.total ?? 0
  const requestedReceipt = params.get('event')
  const selected = items.find((event) => event.receipt_number === requestedReceipt) ?? items[0]

  return (
    <div className="terminal-page">
      <section className="event-pane">
        <div className="terminal-pane-heading event-pane-title">
          <div><h1>Event Monitor</h1><span>{format.integer(total)} {total === 1 ? 'event' : 'events'}</span></div>
          <button className="icon-button" type="button" aria-label="Refresh event data" title="Refresh event data" onClick={() => void events.refetch()}><RefreshCw aria-hidden="true" /></button>
        </div>
        <section className="terminal-filters" aria-label="Event filters">
          <label className="filter-search"><Search aria-hidden="true" /><span className="sr-only">Search securities</span><input name="security-search" autoComplete="off" spellCheck={false} value={filters.q} onChange={(event) => setFilter('q', event.target.value)} placeholder="Security name or six-digit ticker…" /></label>
          <label><span>Market</span><select name="market" value={filters.market} onChange={(event) => setFilter('market', event.target.value)}><option value="">All markets</option><option value="Y">KOSPI</option><option value="K">KOSDAQ</option></select></label>
          <label><span>Attention</span><select name="attention" value={filters.attention_group} onChange={(event) => setFilter('attention', event.target.value)}><option value="">All groups</option><option value="higher_attention">Higher attention</option><option value="neutral_attention">Neutral attention</option><option value="lower_attention">Lower attention</option><option value="missing">Missing</option></select></label>
          <label><span>Outcome</span><select name="outcome" value={filters.outcome_state} onChange={(event) => setFilter('outcome', event.target.value)}><option value="">All outcomes</option><option value="observed">Observed</option><option value="partial">Partial</option><option value="missing">Missing</option></select></label>
          <button className="icon-button" type="button" aria-label="Reset filters" title="Reset filters" onClick={() => setParams({})}><RotateCcw aria-hidden="true" /></button>
        </section>
        <div className="event-count"><span><Filter aria-hidden="true" /><strong>{format.integer(total)}</strong> matching {total === 1 ? 'observation' : 'observations'}</span><span>Click a row to inspect evidence</span></div>
        {items.length
          ? <EventTable events={items} sort={filters.sort ?? ''} order={filters.order ?? ''} onSort={onSort} selectedReceipt={selected?.receipt_number} onSelect={selectEvent} />
          : <EmptyState title="No events match these filters"><button className="button" type="button" onClick={() => setParams({})}>Reset filters</button></EmptyState>}
        <footer className="pane-footer"><span>Showing {items.length} of {format.integer(total)}</span><span>Read-only research data</span></footer>
      </section>
      <EventAnalyticsPanel events={items} selected={selected} />
      <EvidenceInspector event={selected} />
    </div>
  )
}
