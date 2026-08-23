import { Check, Copy, TriangleAlert } from 'lucide-react'
import { useState } from 'react'
import type { EventObservation } from '../api/schemas.ts'
import { format, label } from '../lib/format.ts'
import { StatusBadge } from './StatusBadge.tsx'

function EvidenceRow({ term, value, missing = false }: { term: string, value: string, missing?: boolean }) {
  return <div className="evidence-row"><dt>{term}</dt><dd className={missing ? 'muted' : ''}>{value}</dd></div>
}

function HashValue({ value }: { value: string }) {
  const [copied, setCopied] = useState(false)
  const copy = async () => {
    await navigator.clipboard.writeText(value)
    setCopied(true)
    window.setTimeout(() => setCopied(false), 1400)
  }
  return (
    <button className="hash-button" type="button" onClick={() => void copy()} title={value}>
      <code>{format.shortHash(value)}</code>{copied ? <Check aria-hidden="true" /> : <Copy aria-hidden="true" />}
      <span className="sr-only">Copy full hash</span>
    </button>
  )
}

export function EvidenceView({ event }: { event: EventObservation }) {
  return (
    <div className="evidence-layout">
      <section className="panel evidence-hero">
        <div>
          <p className="eyebrow">{event.ticker} / {label(event.market_class)}</p>
          <h2>{event.corporation_name}</h2>
          <p>{event.report_name}</p>
        </div>
        <StatusBadge status={event.outcome_state}>Outcome {label(event.outcome_state)}</StatusBadge>
      </section>

      <section className="panel">
        <div className="panel-heading"><div><p className="eyebrow">OBJECTIVE MAGNITUDE</p><h2>Disclosure Magnitude</h2></div></div>
        <dl className="evidence-grid">
          <EvidenceRow term="Disclosure date" value={format.date(event.received_date)} />
          <EvidenceRow term="Receipt number" value={event.receipt_number} />
          <EvidenceRow term="Contract value" value={format.krw(event.contract_amount_krw)} />
          <EvidenceRow term="Recent revenue" value={format.krw(event.recent_revenue_krw)} />
          <EvidenceRow term="Reported ratio" value={`${event.reported_revenue_ratio_percent}%`} />
          <EvidenceRow term="Recomputed ratio" value={`${event.computed_revenue_ratio_percent}%`} />
          <EvidenceRow term="Ratio difference" value={`${event.ratio_difference_percentage_points}%p`} />
        </dl>
      </section>

      <section className="panel">
        <div className="panel-heading"><div><p className="eyebrow">ATTENTION MEASUREMENT</p><h2>Attention Calculation</h2></div><StatusBadge status={event.attention_group} /></div>
        <dl className="evidence-grid">
          <EvidenceRow term="Baseline days" value={event.baseline_observed_days?.toString() ?? 'Missing'} missing={event.baseline_observed_days === null} />
          <EvidenceRow term="Event days" value={event.event_observed_days?.toString() ?? 'Missing'} missing={event.event_observed_days === null} />
          <EvidenceRow term="Baseline median" value={format.ratio(event.baseline_median_ratio)} missing={event.baseline_median_ratio === null} />
          <EvidenceRow term="Event mean" value={format.ratio(event.event_mean_ratio)} missing={event.event_mean_ratio === null} />
          <EvidenceRow term="Attention Excess" value={format.ratio(event.attention_excess)} missing={event.attention_excess === null} />
        </dl>
        {event.attention_missing_reason && <p className="inline-warning"><TriangleAlert aria-hidden="true" />{event.attention_missing_reason}</p>}
      </section>

      <section className="panel">
        <div className="panel-heading"><div><p className="eyebrow">FIXED HORIZON OUTCOMES</p><h2>Market Response</h2></div><StatusBadge status={event.outcome_state} /></div>
        <div className="horizon-grid" aria-label="Fixed-horizon abnormal returns">
          {(['h0', 'h1', 'h3', 'h5'] as const).map((horizon) => {
            const value = event[`abnormal_return_${horizon}`]
            return <div key={horizon}><span>{horizon.toUpperCase()}</span><strong className={value === null ? 'muted' : ''}>{format.percent(value)}</strong><small>Abnormal return</small></div>
          })}
        </div>
        {(event.price_missing_reason || event.index_missing_reason) && (
          <div className="blocked-callout"><TriangleAlert aria-hidden="true" /><div><strong>Return not computed</strong><p>{event.price_missing_reason || event.index_missing_reason}</p></div></div>
        )}
      </section>

      <section className="panel">
        <div className="panel-heading"><div><p className="eyebrow">PROVENANCE</p><h2>Source Evidence</h2></div></div>
        <dl className="evidence-grid">
          <div className="evidence-row"><dt>Disclosure SHA-256</dt><dd><HashValue value={event.source_document_sha256} /></dd></div>
          <div className="evidence-row"><dt>Attention snapshot SHA-256</dt><dd>{event.attention_source_snapshot_sha256 ? <HashValue value={event.attention_source_snapshot_sha256} /> : <span className="muted">Missing</span>}</dd></div>
        </dl>
      </section>
    </div>
  )
}
