import { Copy, ExternalLink, FileCheck2 } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { EventObservation } from '../api/schemas.ts'
import { format, label } from '../lib/format.ts'
import { StatusBadge } from './StatusBadge.tsx'

function InspectorRow({ label: rowLabel, value, missing = false }: { label: string, value: string, missing?: boolean }) {
  return <div className="inspector-row"><span>{rowLabel}</span><strong className={missing ? 'muted' : ''}>{value}</strong></div>
}

export function EvidenceInspector({ event }: { event?: EventObservation }) {
  if (!event) return <aside className="evidence-inspector"><div className="inspector-empty"><FileCheck2 aria-hidden="true" /><p>Select an event to inspect its evidence.</p></div></aside>

  return (
    <aside className="evidence-inspector" aria-label="Selected event evidence">
      <div className="terminal-pane-heading"><div><h2>Evidence</h2><span className="info-label">Selected event</span></div><Link className="icon-link" to={`/events/${event.receipt_number}`} aria-label="Open full event evidence"><ExternalLink /></Link></div>
      <header className="inspector-security">
        <p className="eyebrow">{event.ticker} / {label(event.market_class)}</p>
        <h3>{event.corporation_name}</h3>
        <p>{event.report_name}</p>
        <div><time>{format.date(event.received_date)}</time><StatusBadge status={event.outcome_state} /></div>
      </header>
      <section className="inspector-section">
        <h3>Objective Magnitude</h3>
        <InspectorRow label="Contract value" value={format.krw(event.contract_amount_krw)} />
        <InspectorRow label="Recent revenue" value={format.krw(event.recent_revenue_krw)} />
        <InspectorRow label="Reported ratio" value={format.percentValue(event.reported_revenue_ratio_percent)} />
        <InspectorRow label="Recomputed ratio" value={format.percentValue(event.computed_revenue_ratio_percent)} />
      </section>
      <section className="inspector-section">
        <h3>Attention Measurement</h3>
        <InspectorRow label="Baseline days" value={event.baseline_observed_days?.toString() ?? 'Missing'} missing={event.baseline_observed_days === null} />
        <InspectorRow label="Event days" value={event.event_observed_days?.toString() ?? 'Missing'} missing={event.event_observed_days === null} />
        <InspectorRow label="Baseline median" value={format.ratio(event.baseline_median_ratio)} missing={event.baseline_median_ratio === null} />
        <InspectorRow label="Event mean" value={format.ratio(event.event_mean_ratio)} missing={event.event_mean_ratio === null} />
        <InspectorRow label="Attention Excess" value={format.ratio(event.attention_excess)} missing={event.attention_excess === null} />
      </section>
      <section className="inspector-section inspector-provenance">
        <h3>Source Evidence</h3>
        <button type="button" onClick={() => void navigator.clipboard.writeText(event.source_document_sha256)} title={event.source_document_sha256}><span>Disclosure SHA-256</span><code>{format.shortHash(event.source_document_sha256)}</code><Copy aria-hidden="true" /></button>
        {event.attention_source_snapshot_sha256 && <button type="button" onClick={() => void navigator.clipboard.writeText(event.attention_source_snapshot_sha256 ?? '')} title={event.attention_source_snapshot_sha256}><span>Attention SHA-256</span><code>{format.shortHash(event.attention_source_snapshot_sha256)}</code><Copy aria-hidden="true" /></button>}
      </section>
    </aside>
  )
}
