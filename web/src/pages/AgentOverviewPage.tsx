import {
  Activity, ArrowRight, CheckCircle2, CircleDashed, Clock3, Database,
  Gauge, Newspaper, ShieldCheck, WalletCards,
} from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  useAgentRun, useAgentRuns, useAgentStatus, usePortfolio, useStrategy,
} from '../api/queries.ts'
import type { AgentRunDetail, SignalSnapshot } from '../api/schemas.ts'
import { ErrorState, LoadingState } from '../components/States.tsx'
import { StatusBadge } from '../components/StatusBadge.tsx'
import { format } from '../lib/format.ts'

const usd = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
const signedUsd = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0, signDisplay: 'always' })

function topSignal(signals: SignalSnapshot[]) {
  return [...signals].sort((a, b) => Math.abs(b.crowd_excess_score) - Math.abs(a.crowd_excess_score))[0]
}

function latestNarrative(detail: AgentRunDetail | undefined) {
  const signal = topSignal(detail?.signals ?? [])
  const risk = detail?.risk_decision
  const receipt = detail?.receipt
  if (!signal) return 'Evidence was not sampled → no candidate reached risk evaluation → the agent placed no order.'
  const evidence = signal.evidence.abstention_reason
    ? `${signal.symbol} evidence abstained: ${signal.evidence.abstention_reason.replaceAll('_', ' ')}`
    : `${signal.symbol} evidence confidence ${Math.round(signal.evidence.confidence * 100)}%`
  const control = risk ? (risk.approved ? 'risk gates approved the candidate' : `risk gates abstained: ${risk.denial_reason || 'a required gate failed'}`) : 'no option candidate reached risk evaluation'
  const outcome = receipt ? `Alpaca paper receipt is ${receipt.state.replaceAll('_', ' ')}` : 'no order was submitted'
  return `${evidence} → ${control} → ${outcome}.`
}

export function AgentOverviewPage() {
  const [renderedAt] = useState(() => Date.now())
  const status = useAgentStatus()
  const runs = useAgentRuns()
  const portfolio = usePortfolio()
  const strategy = useStrategy()
  const latestRun = status.data?.last_run ?? runs.data?.[0]
  const latestSampledRun = status.data?.latest_sampled_run
  const detail = useAgentRun(latestRun?.run_id ?? '')

  if (status.isLoading || runs.isLoading || portfolio.isLoading || strategy.isLoading || detail.isLoading) {
    return <LoadingState label="Loading the daily audit summary" />
  }
  const error = status.error || runs.error || portfolio.error || strategy.error || detail.error
  if (error) return <ErrorState error={error} retry={() => window.location.reload()} />

  const sampledSignals = detail.data?.signals ?? []
  const sampled = sampledSignals.length > 0
  const latestText = `${latestRun?.summary ?? ''} ${latestRun?.error ?? ''} ${status.data?.message ?? ''}`.toLowerCase()
  const closedWindow = !sampled && (latestRun?.market_clock
    ? !latestRun.market_clock.is_open
    : /(market.*closed|outside.*market|outside.*window|market window)/.test(latestText))
  const latestTitle = !latestRun
    ? 'No automation check recorded'
    : sampled
      ? `${sampledSignals.length} symbols sampled in the latest check`
      : closedWindow ? 'Market window was closed at the latest check' : 'No providers were sampled in the latest check'
  const latestCause = !latestRun
    ? 'The read-only audit store will show the first scheduled run after it is recorded.'
    : sampled
      ? latestRun.summary || 'The completed observations are available in the decision workbench.'
      : `${latestRun.summary || 'The run ended before market, news, or option data was collected.'} This is a past check result, not a claim about the market right now.`
  const nextAction = !latestRun
    ? 'Wait for the first scheduled US-market scan, then return to inspect its inputs.'
    : !sampled
      ? latestRun?.market_clock?.next_open
        ? `The recorded market clock reported its next open at ${format.dateTime(latestRun.market_clock.next_open)}. Return after a new eligible scan; no missing values are treated as zero.`
        : 'Return after the next eligible US-market scan; no missing values are treated as zero.'
      : detail.data?.receipt
        ? 'Open the full trace to verify the order receipt and every input timestamp.'
        : 'Open the decision workbench to inspect the residual and the gate that caused abstention.'
  const sourceKeys = Object.keys(detail.data?.run.source_hashes ?? latestRun?.source_hashes ?? {})
  const sourceReady = (prefix: string) => sourceKeys.some((key) => key.startsWith(prefix))
  const observedValue = latestRun?.market_clock?.observed_at ?? latestRun?.completed_at ?? latestRun?.started_at
  const observedAt = observedValue ? format.dateTime(observedValue) : 'Not observed'
  const stale = observedValue ? renderedAt - new Date(observedValue).getTime() > 24 * 60 * 60 * 1000 : false
  const evidenceFailed = sampledSignals.some((signal) => Boolean(signal.evidence.abstention_reason))
  const health = [
    { name: 'NAVER', state: sourceReady('naver_') ? stale ? 'Stale' : 'Ready' : 'Not sampled', detail: 'Cross-border search attention' },
    { name: 'Alpaca Market', state: sourceReady('alpaca_market_') ? stale ? 'Stale' : 'Ready' : 'Not sampled', detail: 'Market, volume, and news context' },
    { name: 'OpenAI', state: evidenceFailed ? 'Error' : sampledSignals.some((signal) => Boolean(signal.evidence_response_id)) ? stale ? 'Stale' : 'Ready' : 'Not sampled', detail: 'Structured news evidence' },
    { name: 'Risk Engine', state: detail.data?.risk_decision ? 'Ready' : 'Not sampled', detail: 'Deterministic execution gates' },
    { name: 'Audit Store', state: status.data?.configured ? 'Ready' : 'Error', detail: 'Sanitized read-only records' },
  ]

  return (
    <div className="page agent-overview">
      <header className="overview-hero">
        <div>
          <p className="eyebrow">US OPTIONS AGENT / READ-ONLY AUDIT</p>
          <h1>Today at a glance</h1>
          <p>Understand the latest autonomous check, current paper risk, and why the system acted—or safely did not.</p>
        </div>
        <div className="overview-mode"><span className={status.data?.configured ? 'signal-dot' : 'signal-dot signal-dot--off'} /><div><strong>{status.data?.configured ? 'Audit connected' : 'Audit not connected'}</strong><small>{status.data?.mode.toUpperCase() ?? 'SHADOW'} ONLY · NO LIVE PATH</small></div></div>
      </header>

      <section className="overview-metrics" aria-label="Current paper account summary" aria-live="polite">
        <div><WalletCards aria-hidden="true" /><span>Account equity</span><strong>{portfolio.data ? usd.format(portfolio.data.equity) : 'Not observed'}</strong><small>Latest paper snapshot</small></div>
        <div><Activity aria-hidden="true" /><span>Daily P&amp;L</span><strong data-tone={(portfolio.data?.daily_pnl ?? 0) >= 0 ? 'positive' : 'negative'}>{portfolio.data ? signedUsd.format(portfolio.data.daily_pnl) : 'Not observed'}</strong><small>No profitability claim</small></div>
        <div><ShieldCheck aria-hidden="true" /><span>Open risk</span><strong>{portfolio.data ? usd.format(portfolio.data.open_premium_risk) : 'Not observed'}</strong><small>{portfolio.data ? `${portfolio.data.open_spread_count} / ${strategy.data?.max_open_spreads ?? 3} spreads` : 'No portfolio snapshot'}</small></div>
        <div><Gauge aria-hidden="true" /><span>Latest outcome</span><strong>{latestRun?.status.toUpperCase() ?? 'WAITING'}</strong><small>{latestRun ? format.dateTime(latestRun.started_at) : 'No autonomous run yet'}</small></div>
      </section>

      <div className="overview-primary-grid">
        <section className="panel latest-check-card">
          <div className="panel-heading"><div><p className="eyebrow">LATEST CHECK</p><h2>{latestTitle}</h2></div>{sampled ? <CheckCircle2 aria-hidden="true" /> : <Clock3 aria-hidden="true" />}</div>
          <div className="latest-check-body">
            <p>{latestCause}</p>
            <div className="decision-sentence"><Newspaper aria-hidden="true" /><p><strong>Evidence → Risk → Outcome</strong><span>{latestNarrative(detail.data)}</span></p></div>
            <div className="next-action"><strong>What to do next</strong><p>{nextAction}</p></div>
            <div className="overview-actions">
              {latestSampledRun ? (
                <Link
                  aria-label="Open Decision Workbench for latest sampled run"
                  className="button button--primary"
                  to={`/decisions?run=${latestSampledRun.run_id}`}
                >
                  Open latest sampled run <ArrowRight aria-hidden="true" />
                </Link>
              ) : (
                <Link className="button button--primary" to="/decisions">Open Decision Workbench <ArrowRight aria-hidden="true" /></Link>
              )}
              {latestRun && <Link className="button" to={`/agent/runs/${latestRun.run_id}`}>Open Full Trace</Link>}
            </div>
          </div>
        </section>

        <section className="panel recent-runs-card">
          <div className="panel-heading"><div><p className="eyebrow">RECENT ACTIVITY</p><h2>Last three runs</h2></div><small>{runs.data?.length ?? 0} recorded</small></div>
          <div className="overview-run-list">
            {runs.data?.slice(0, 3).map((run) => (
              <Link to={`/agent/runs/${run.run_id}`} key={run.run_id}>
                <time>{format.dateTime(run.started_at)}</time><StatusBadge status={run.status} />
                <strong>{run.summary || 'Decision trace recorded.'}</strong><ArrowRight aria-hidden="true" />
              </Link>
            ))}
            {!runs.data?.length && <div className="overview-empty"><CircleDashed aria-hidden="true" /><strong>No runs recorded</strong><p>The first scheduled audit will appear here.</p></div>}
          </div>
        </section>
      </div>

      <section className="panel data-health-summary">
        <div className="panel-heading"><div><p className="eyebrow">DATA HEALTH</p><h2>What the latest check actually observed</h2></div><span><Database aria-hidden="true" /> {observedAt}</span></div>
        <div className="health-source-grid">
          {health.map((source) => {
            const state = source.state
            const statusKey = state.toLowerCase().replace(' ', '_')
            return <div key={source.name} data-state={statusKey.replace('_', '-')}><span>{state === 'Ready' ? <CheckCircle2 aria-hidden="true" /> : <CircleDashed aria-hidden="true" />}<strong>{source.name}</strong></span><StatusBadge status={statusKey}>{state}</StatusBadge><p>{source.detail}</p></div>
          })}
        </div>
      </section>
    </div>
  )
}
