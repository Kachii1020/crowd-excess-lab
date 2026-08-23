import { AlertTriangle, Info } from 'lucide-react'
import { useMemo } from 'react'
import {
  Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import type { EventObservation } from '../api/schemas.ts'
import { format } from '../lib/format.ts'
import { StatusBadge } from './StatusBadge.tsx'

function percentile(values: number[], point: number): number | null {
  if (!values.length) return null
  const ordered = [...values].sort((a, b) => a - b)
  const index = Math.min(ordered.length - 1, Math.max(0, Math.round((ordered.length - 1) * point)))
  return ordered[index]
}

function histogram(values: number[], binCount = 9) {
  if (!values.length) return []
  const min = Math.min(...values)
  const max = Math.max(...values)
  const width = max === min ? 1 : (max - min) / binCount
  return Array.from({ length: binCount }, (_, index) => {
    const low = min + index * width
    const high = index === binCount - 1 ? max : low + width
    return {
      low,
      high,
      label: `${format.decimal(low)}`,
      count: values.filter((value) => value >= low && (index === binCount - 1 ? value <= high : value < high)).length,
    }
  })
}

export function EventAnalyticsPanel({ events, selected }: { events: EventObservation[], selected?: EventObservation }) {
  const observed = useMemo(() => events.flatMap((event) => event.attention_excess === null ? [] : [event.attention_excess]), [events])
  const bins = useMemo(() => histogram(observed), [observed])
  const selectedValue = selected?.attention_excess ?? null
  const selectedBin = bins.findIndex((bin, index) => selectedValue !== null && selectedValue >= bin.low && (index === bins.length - 1 ? selectedValue <= bin.high : selectedValue < bin.high))
  const rank = selectedValue === null || !observed.length ? null : observed.filter((value) => value <= selectedValue).length / observed.length
  const outcomes = selected ? [selected.abnormal_return_h0, selected.abnormal_return_h1, selected.abnormal_return_h3, selected.abnormal_return_h5] : []
  const outcomeObserved = outcomes.some((value) => value !== null)

  return (
    <section className="analytics-pane" aria-label="Attention Excess analysis">
      <div className="terminal-pane-heading">
        <div><h2>Attention Excess</h2><span className="info-label">Observed proxy <Info aria-hidden="true" /></span></div>
      </div>
      <div className="selected-metric">
        <span>Selected event</span>
        <strong className={selectedValue === null ? 'muted' : ''}>{format.ratio(selectedValue)}</strong>
        <small>{selected ? selected.corporation_name : 'No event selected'}</small>
        <div>{selected && <StatusBadge status={selected.attention_group} />}{rank !== null && <span>Percentile {format.integer(rank * 100)}</span>}</div>
      </div>
      <div className="distribution-heading"><span>Distribution</span><span>n = {observed.length}</span></div>
      <div className="histogram" role="img" aria-label={`Attention Excess distribution for ${observed.length} observed events.`}>
        {bins.length ? (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={bins} margin={{ top: 10, right: 8, bottom: 2, left: -22 }}>
              <CartesianGrid vertical={false} stroke="var(--border-subtle)" />
              <XAxis dataKey="label" tickLine={false} axisLine={false} interval={2} />
              <YAxis allowDecimals={false} tickLine={false} axisLine={false} />
              <Tooltip formatter={(value) => [value, 'Events']} labelFormatter={(value) => `AE bin from ${value}`} />
              <Bar dataKey="count" radius={0}>
                {bins.map((bin, index) => <Cell key={bin.label} fill={index === selectedBin ? 'var(--positive)' : 'var(--data-muted)'} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : <span className="muted">No observed attention values</span>}
      </div>
      <div className="percentile-grid">
        <div><span>P10</span><strong>{format.ratio(percentile(observed, .1))}</strong></div>
        <div><span>Median</span><strong>{format.ratio(percentile(observed, .5))}</strong></div>
        <div><span>P90</span><strong>{format.ratio(percentile(observed, .9))}</strong></div>
      </div>

      <div className="outcome-section">
        <div className="terminal-pane-heading"><div><h2>Event-Time Return</h2><span className="info-label">Fixed horizons</span></div></div>
        <div className="compact-horizons">
          {(['H0', 'H1', 'H3', 'H5'] as const).map((horizon, index) => (
            <div key={horizon}><span>{horizon}</span><strong className={outcomes[index] === null || outcomes[index] === undefined ? 'muted' : ''}>{format.percent(outcomes[index] ?? null)}</strong></div>
          ))}
        </div>
        {!outcomeObserved && (
          <div className="outcome-pending"><AlertTriangle aria-hidden="true" /><div><strong>Outcome pending</strong><p>Price and market-index inputs are not observed. Missing values are not replaced with zero.</p></div></div>
        )}
      </div>
      <p className="chart-summary">Summary: {observed.length}/{events.length} filtered events have an observed attention measure. The distribution is descriptive and in-sample.</p>
    </section>
  )
}
