import { ArrowRight, Ban, Database, FileCheck2, RadioTower, TrendingUp } from 'lucide-react'
import { Link, useOutletContext } from 'react-router-dom'
import { useEvents, useLineage, useRun } from '../api/queries.ts'
import type { WorkspaceContext } from '../components/AppShell.tsx'
import { EmptyState, ErrorState, LoadingState } from '../components/States.tsx'
import { MetricCard } from '../components/MetricCard.tsx'
import { PageHeader } from '../components/PageHeader.tsx'
import { StatusBadge } from '../components/StatusBadge.tsx'
import { format, label } from '../lib/format.ts'

export function OverviewPage() {
  const { runId } = useOutletContext<WorkspaceContext>()
  const run = useRun(runId)
  const events = useEvents(runId, { sort: 'received_date', order: 'desc', limit: 5 })
  const lineage = useLineage(runId)

  if (!runId) return <EmptyState title="No research run has been created"><p>Run <code>uv run crowd-excess-study --target 40</code> to create the first cohort.</p></EmptyState>
  if (run.isLoading || events.isLoading || lineage.isLoading) return <LoadingState />
  if (run.error) return <ErrorState error={run.error} retry={() => void run.refetch()} />
  if (!run.data) return null

  const counts = run.data.counts
  const selected = counts.selected_events ?? 0
  const attention = counts.attention_observed ?? 0
  const outcomes = counts.abnormal_h1_observed ?? 0

  return (
    <div className="page page--overview">
      <PageHeader eyebrow="MARKET RESEARCH / KOREA" title="Research Dashboard" description="Track whether crowd attention moves beyond the objective magnitude of a corporate disclosure." actions={<Link className="button button--primary" to="/events">Open Event Monitor <ArrowRight /></Link>} />

      <section className="metric-grid" aria-label="Research data summary">
        <MetricCard label="Selected Disclosures" value={format.integer(selected)} detail={`Target ${format.integer(run.data.target_events)} events`} state={selected ? 'ok' : 'neutral'} icon={<FileCheck2 />} />
        <MetricCard label="Attention Observed" value={`${format.integer(attention)} / ${format.integer(selected)}`} detail="NAVER search-trend proxy" state={attention === selected ? 'ok' : 'warning'} icon={<RadioTower />} />
        <MetricCard label="H1 Abnormal Return" value={`${format.integer(outcomes)} / ${format.integer(selected)}`} detail={outcomes ? 'Market-adjusted return' : 'Awaiting price and index inputs'} state={outcomes ? 'ok' : 'blocked'} icon={<TrendingUp />} />
        <MetricCard label="Raw Snapshots" value={format.integer(lineage.data?.total ?? 0)} detail={`${format.integer(lineage.data?.groups.length ?? 0)} data providers`} state="neutral" icon={<Database />} />
      </section>

      <div className="overview-grid">
        <section className="panel pipeline-panel">
          <div className="panel-heading"><div><p className="eyebrow">PIPELINE READINESS</p><h2>Collection and Calculation</h2></div><span className="mono muted">SCHEMA v{run.data.schema_version}</span></div>
          <ol className="pipeline-list">
            {Object.entries(run.data.stages).map(([stage, status], index) => (
              <li key={stage}>
                <span className="step-index">{String(index + 1).padStart(2, '0')}</span>
                <div><strong>{label(stage)}</strong><small>{stage}</small></div>
                <StatusBadge status={status} />
              </li>
            ))}
          </ol>
        </section>

        <section className="panel blocker-panel">
          <div className="panel-heading"><div><p className="eyebrow">NEXT BLOCKER</p><h2>Current Constraint</h2></div><Ban aria-hidden="true" /></div>
          {run.data.blockers.length ? (
            <>
              <p className="big-copy">Fixed-horizon outcomes can resume as soon as official stock-price and market-index inputs are available.</p>
              <ul className="plain-list">{run.data.blockers.map((blocker) => <li key={blocker}>{blocker}</li>)}</ul>
            </>
          ) : <p className="big-copy">No pipeline stage is currently blocked.</p>}
          <Link className="text-link" to="/settings">Review data connections <ArrowRight /></Link>
        </section>
      </div>

      <section className="panel">
        <div className="panel-heading"><div><p className="eyebrow">LATEST DISCLOSURES</p><h2>Recent Selected Events</h2></div><Link className="text-link" to="/events">View all {format.integer(events.data?.total ?? 0)} <ArrowRight /></Link></div>
        <div className="compact-events">
          {events.data?.items.map((event) => (
            <Link key={event.receipt_number} to={`/events/${event.receipt_number}`}>
              <time>{format.date(event.received_date)}</time>
              <span><strong>{event.corporation_name}</strong><small>{event.ticker} · {event.report_name}</small></span>
              <span className="numeric"><small>Contract / Revenue</small><strong>{format.percent(event.contract_revenue_ratio)}</strong></span>
              <StatusBadge status={event.attention_group} />
              <ArrowRight aria-hidden="true" />
            </Link>
          ))}
        </div>
      </section>
    </div>
  )
}
