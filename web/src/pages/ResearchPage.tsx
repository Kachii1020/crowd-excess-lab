import { useMemo } from 'react'
import { AlertTriangle, FlaskConical } from 'lucide-react'
import { ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis, ZAxis } from 'recharts'
import { useOutletContext, useSearchParams } from 'react-router-dom'
import { useEvents } from '../api/queries.ts'
import type { EventObservation } from '../api/schemas.ts'
import type { WorkspaceContext } from '../components/AppShell.tsx'
import { PageHeader } from '../components/PageHeader.tsx'
import { EmptyState, ErrorState, LoadingState } from '../components/States.tsx'
import { StatusBadge } from '../components/StatusBadge.tsx'
import { format, label } from '../lib/format.ts'

type Horizon = 'h0' | 'h1' | 'h3' | 'h5'
const horizons: Horizon[] = ['h0', 'h1', 'h3', 'h5']
const groups = ['lower_attention', 'neutral_attention', 'higher_attention']

function median(values: number[]): number | null {
  if (!values.length) return null
  const ordered = [...values].sort((a, b) => a - b)
  const middle = Math.floor(ordered.length / 2)
  return ordered.length % 2 ? ordered[middle] : (ordered[middle - 1] + ordered[middle]) / 2
}

function observedReturn(event: EventObservation, horizon: Horizon): number | null {
  return event[`abnormal_return_${horizon}`]
}

export function ResearchPage() {
  const { runId } = useOutletContext<WorkspaceContext>()
  const [params, setParams] = useSearchParams()
  const requestedHorizon = params.get('horizon')
  const horizon: Horizon = horizons.includes(requestedHorizon as Horizon) ? requestedHorizon as Horizon : 'h1'
  const setHorizon = (value: Horizon) => setParams((current) => {
    const next = new URLSearchParams(current)
    next.set('horizon', value)
    return next
  }, { replace: true })
  const events = useEvents(runId, { limit: 100, sort: 'received_date', order: 'asc' })

  const scatter = useMemo(() => events.data?.items.flatMap((event) => event.attention_excess === null ? [] : [{
    company: event.corporation_name,
    magnitude: event.contract_revenue_ratio * 100,
    attention: event.attention_excess,
  }]) ?? [], [events.data])

  if (!runId) return <EmptyState title="No research run is available" />
  if (events.isLoading) return <LoadingState label="Computing the research matrix" />
  if (events.error) return <ErrorState error={events.error} retry={() => void events.refetch()} />

  const items = events.data?.items ?? []
  const observed = items.filter((event) => observedReturn(event, horizon) !== null)

  return (
    <div className="page">
      <PageHeader eyebrow="RESEARCH MATRIX" title="Hypothesis Explorer" description="Describe in-sample relationships using only preregistered variables and H0/H1/H3/H5 horizons." />
      <section className="research-strip">
        <div><span>Sample</span><strong>{format.integer(items.length)}</strong></div>
        <div><span>Attention Observed</span><strong>{format.integer(scatter.length)}</strong></div>
        <div><span>{horizon.toUpperCase()} Outcomes</span><strong>{format.integer(observed.length)}</strong></div>
        <div className="hypothesis"><FlaskConical aria-hidden="true" /><span>Is attention beyond disclosure magnitude associated with subsequent market response?</span></div>
      </section>

      <div className="research-grid">
        <section className="panel chart-panel">
          <div className="panel-heading"><div><p className="eyebrow">MAGNITUDE × ATTENTION</p><h2>Disclosure Magnitude and Attention Excess</h2></div><span className="mono muted">n={scatter.length}</span></div>
          {scatter.length ? (
            <>
              <div className="chart-frame" role="img" aria-label={`Scatter plot of contract-to-revenue ratio and Attention Excess for ${scatter.length} observations.`}>
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart margin={{ top: 16, right: 16, bottom: 8, left: 0 }}>
                    <XAxis type="number" dataKey="magnitude" name="Contract / Revenue" unit="%" tickLine={false} axisLine={false} />
                    <YAxis type="number" dataKey="attention" name="Attention Excess" unit="×" tickLine={false} axisLine={false} width={52} />
                    <ZAxis range={[48, 48]} />
                    <Tooltip cursor={{ strokeDasharray: '3 3' }} formatter={(value, name) => [`${format.decimal(Number(value))}${name === 'Contract / Revenue' ? '%' : '×'}`, name]} labelFormatter={(_, payload) => payload?.[0]?.payload?.company ?? ''} />
                    <Scatter data={scatter} fill="var(--data-primary)" />
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
              <p className="chart-summary">Summary: {scatter.length} disclosures show contract-to-revenue magnitude against the event-to-baseline attention ratio. This chart does not establish prediction or causality.</p>
            </>
          ) : <EmptyState title="No attention observations are available" />}
        </section>

        <section className="panel outcome-panel">
          <div className="panel-heading">
            <div><p className="eyebrow">FIXED HORIZON</p><h2>Abnormal Return by Attention Group</h2></div>
            <div className="segmented" aria-label="Select outcome horizon">{horizons.map((item) => <button key={item} type="button" aria-pressed={horizon === item} onClick={() => setHorizon(item)}>{item.toUpperCase()}</button>)}</div>
          </div>
          <div className="group-matrix">
            {groups.map((group) => {
              const members = items.filter((event) => event.attention_group === group)
              const values = members.flatMap((event) => {
                const value = observedReturn(event, horizon)
                return value === null ? [] : [value]
              })
              return (
                <div key={group}>
                  <StatusBadge status={group} />
                  <strong className={values.length ? '' : 'muted'}>{format.percent(median(values))}</strong>
                  <span>Median</span>
                  <small>{values.length} / {members.length} observed</small>
                </div>
              )
            })}
          </div>
          {!observed.length && <div className="blocked-callout"><AlertTriangle aria-hidden="true" /><div><strong>Awaiting price and index data</strong><p>Returns are missing, not zero. Only observed values will populate this research contract.</p></div></div>}
          <p className="chart-summary">Summary: {observed.length}/{items.length} {horizon.toUpperCase()} abnormal returns are observed. Each cell is the in-sample median for {groups.map(label).join(', ')}.</p>
        </section>
      </div>
    </div>
  )
}
