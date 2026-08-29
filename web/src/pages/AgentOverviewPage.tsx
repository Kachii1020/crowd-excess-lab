import {
  Activity, ArrowRight, CircleAlert, CircleDashed, Clock3, Database,
  Gauge, ShieldCheck, WalletCards,
} from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  useAgentRun, useAgentRuns, useAgentStatus, usePortfolio, useStrategy,
} from '../api/queries.ts'
import type { AgentRun, SignalSnapshot } from '../api/schemas.ts'
import { StatusBadge } from '../components/StatusBadge.tsx'
import { format } from '../lib/format.ts'

const usd = new Intl.NumberFormat('en-US', {
  style: 'currency', currency: 'USD', maximumFractionDigits: 0,
})
const signedUsd = new Intl.NumberFormat('en-US', {
  style: 'currency', currency: 'USD', maximumFractionDigits: 0, signDisplay: 'always',
})

const scanSteps = [
  { title: 'Measure the Reaction', detail: 'Search attention, price and volume' },
  { title: 'Test the Explanation', detail: 'OpenAI assesses supplied headlines only' },
  { title: 'Decide or Abstain', detail: 'Deterministic option, liquidity and risk gates decide' },
]

function scanVerdict(run: AgentRun | null | undefined, signals: SignalSnapshot[]) {
  if (!run) {
    return {
      title: 'Waiting for the First Market Scan',
      description: 'The first completed US-market scan will appear here with its evidence, gates and outcome.',
    }
  }
  if (run.status === 'failed' || run.failure_stage) {
    return {
      title: 'Scan Stopped Safely',
      description: 'The scan stopped before a safe decision could advance. Review the immutable trace for the recorded boundary and outcome.',
    }
  }
  const allowedNoTradeReasons = new Set(['', 'signal_thresholds_not_met', 'evidence_abstained'])
  const incompleteSignal = signals.length !== 5 || signals.some((signal) => (
    signal.evidence.abstention_reason === 'openai_evidence_unavailable'
    || signal.missing_reason.split(',').some((reason) => !allowedNoTradeReasons.has(reason))
  ))
  if (incompleteSignal) {
    return {
      title: 'Scan Stopped Safely',
      description: 'A required provider observation was unavailable, so the scan preserved the no-trade boundary instead of inferring missing evidence.',
    }
  }
  if (run.status === 'completed') {
    return {
      title: 'Candidate Advanced to Risk Review',
      description: 'A candidate passed the market scan and advanced to deterministic risk review. Inspect the trace for the final decision and any paper receipt.',
    }
  }
  return {
    title: 'No Tradable Crowd Excess Found',
    description: 'Across all monitored names, no candidate met the thresholds for unexplained market reaction after accounting for news evidence and passing liquidity and risk checks.',
  }
}

function runWasClosed(run: AgentRun | null | undefined) {
  if (!run) return false
  if (run.market_clock) return !run.market_clock.is_open
  return /market(?: clock)? (?:is )?closed|outside.*market|outside.*window/i.test(
    `${run.summary} ${run.error}`,
  )
}

export function AgentOverviewPage() {
  const [renderedAt] = useState(() => Date.now())
  const status = useAgentStatus()
  const runs = useAgentRuns()
  const portfolio = usePortfolio()
  const strategy = useStrategy()
  const latestRun = status.data?.last_run ?? runs.data?.[0] ?? null
  const latestSampledRun = status.data?.latest_sampled_run
    ?? runs.data?.find((run) => Object.keys(run.source_hashes).length > 0)
    ?? null
  const sampledDetail = useAgentRun(latestSampledRun?.run_id ?? '')

  const scanLoading = status.isLoading || runs.isLoading
    || (Boolean(latestSampledRun) && sampledDetail.isLoading)
  const scanError = status.error || runs.error || sampledDetail.error
  const accountLoading = portfolio.isLoading || strategy.isLoading
  const accountError = portfolio.error || strategy.error
  const sampledRun = sampledDetail.data?.run ?? latestSampledRun
  const sampledSignals = sampledDetail.data?.signals ?? []
  const verdict = scanError
    ? {
        title: 'Market Scan Status Unavailable',
        description: 'The public audit could not be read. No market inputs, risk decision or order state is inferred while the trace is unavailable.',
      }
    : scanLoading
      ? {
          title: 'Loading Market Scan Status',
          description: 'The product definition remains available while the latest read-only audit trace is loading.',
        }
      : scanVerdict(sampledRun, sampledSignals)
  const verdictDescription = scanLoading || scanError
    ? verdict.description
    : sampledRun?.summary || verdict.description
  const newerAutomationCheck = Boolean(
    latestRun
    && latestRun.run_id !== sampledRun?.run_id
  )
  const automationContext = runWasClosed(latestRun)
    ? 'Market closed at the latest automation check. Showing the most recent completed market scan.'
    : `A newer ${latestRun?.status ?? 'unsampled'} automation check is recorded${latestRun?.summary ? `: ${latestRun.summary}` : '.'} Showing the most recent completed market scan.`
  const observedValue = sampledRun?.market_clock?.observed_at
    ?? sampledRun?.completed_at
    ?? sampledRun?.started_at
  const observedAt = observedValue ? format.dateTime(observedValue) : 'Not observed'
  const stale = observedValue
    ? renderedAt - new Date(observedValue).getTime() > 24 * 60 * 60 * 1000
    : false
  const sourceKeys = Object.keys(sampledRun?.source_hashes ?? {})
  const sourceReady = (prefix: string) => sourceKeys.some((key) => key.startsWith(prefix))
  const evidenceFailed = sampledSignals.some(
    (signal) => signal.evidence.abstention_reason === 'openai_evidence_unavailable',
  )
  const health = [
    { name: 'NAVER', state: sourceReady('naver_') ? stale ? 'Stale' : 'Ready' : 'Not sampled', detail: 'Cross-border search attention' },
    { name: 'Alpaca Market', state: sourceReady('alpaca_market_') ? stale ? 'Stale' : 'Ready' : 'Not sampled', detail: 'Market, volume, and news context' },
    { name: 'OpenAI', state: evidenceFailed ? 'Error' : sampledSignals.some((signal) => Boolean(signal.evidence_response_id)) ? stale ? 'Stale' : 'Ready' : 'Not sampled', detail: 'Structured news evidence' },
    { name: 'Risk Engine', state: sampledDetail.data?.risk_decision ? 'Ready' : 'Not sampled', detail: 'Deterministic execution gates' },
    { name: 'Audit Store', state: status.data?.configured ? 'Ready' : 'Error', detail: 'Sanitized read-only records' },
  ]
  const sampledScanReadable = !scanLoading && !scanError && Boolean(sampledRun)
  const primaryScanUrl = sampledScanReadable ? `/decisions?run=${sampledRun?.run_id}` : '/decisions'

  return (
    <div className="page agent-overview">
      <header className="overview-product-hero">
        <p className="eyebrow">MARKET REACTION FILTER / PAPER OPTIONS</p>
        <h1>Find When Market Attention Outruns the Evidence</h1>
        <p className="overview-definition">Crowd Excess compares cross-border search attention and SPY-adjusted price moves with the news that could explain them. It flags possible overreactions, then blocks any option trade that fails liquidity or risk checks.</p>
        <p className="overview-formula">CROWD EXCESS = (PRICE MOVE × ATTENTION) − NEWS EVIDENCE</p>
        <p className="overview-formula-definition">The residual shows how much of the market reaction remains unexplained.</p>
        <ol className="overview-scan-flow" aria-label="How Crowd Excess reaches a decision">
          {scanSteps.map((step, index) => (
            <li key={step.title}>
              <span aria-hidden="true">{index + 1}</span>
              <div><strong>{step.title}</strong><small>{step.detail}</small></div>
            </li>
          ))}
        </ol>
      </header>

      <section className="overview-latest-scan" aria-labelledby="latest-market-scan-title" aria-live="polite" data-state={scanError ? 'error' : scanLoading ? 'loading' : 'ready'}>
        <p className="eyebrow">LATEST COMPLETED SCAN</p>
        <div className="overview-verdict-grid">
          <div className="overview-verdict">
            <div className="overview-verdict-title">
              <CircleAlert aria-hidden="true" />
              <h2 id="latest-market-scan-title">{verdict.title}</h2>
            </div>
            <p>{verdictDescription}</p>
            {!scanLoading && !scanError && <span className="overview-observed"><small>OBSERVATION TIME</small>{observedAt}</span>}
          </div>
          {newerAutomationCheck && (
            <aside className="overview-automation-context">
              <Clock3 aria-hidden="true" />
              <p>{automationContext}</p>
            </aside>
          )}
          <div className="overview-actions">
            <Link className="button button--primary" to={primaryScanUrl}>
              {sampledScanReadable ? 'Review Latest Market Scan' : 'View Market Scan Status'}
              <ArrowRight aria-hidden="true" />
            </Link>
            <Link className="button" to="/strategy">See How It Works <ArrowRight aria-hidden="true" /></Link>
          </div>
        </div>
      </section>

      {!scanLoading && !scanError && <><section className="overview-account-risk" aria-labelledby="paper-account-risk-title">
        <h2 className="eyebrow" id="paper-account-risk-title">Paper Account &amp; Risk</h2>
        {(accountLoading || accountError) && <p className="overview-secondary-status" role={accountError ? 'alert' : 'status'}>{accountError ? 'Paper account metrics are temporarily unavailable. The market scan remains readable.' : 'Loading paper account metrics…'}</p>}
        <div className="overview-metrics" aria-label="Current paper account and risk" aria-live="polite">
          <div><WalletCards aria-hidden="true" /><span>Account Equity</span><strong>{portfolio.data ? usd.format(portfolio.data.equity) : 'Not observed'}</strong><small>Latest paper snapshot</small></div>
          <div><Activity aria-hidden="true" /><span>Daily P&amp;L</span><strong data-tone={(portfolio.data?.daily_pnl ?? 0) >= 0 ? 'positive' : 'negative'}>{portfolio.data ? signedUsd.format(portfolio.data.daily_pnl) : 'Not observed'}</strong><small>No profitability claim</small></div>
          <div><ShieldCheck aria-hidden="true" /><span>Open Risk</span><strong>{portfolio.data ? usd.format(portfolio.data.open_premium_risk) : 'Not observed'}</strong><small>{portfolio.data ? `${portfolio.data.open_spread_count} / ${strategy.data?.max_open_spreads ?? 3} spreads` : 'No portfolio snapshot'}</small></div>
          <div><Gauge aria-hidden="true" /><span>Latest Outcome</span><strong>{latestRun?.status.toUpperCase() ?? 'WAITING'}</strong><small>{latestRun ? format.dateTime(latestRun.started_at) : 'No automation check yet'}</small></div>
        </div>
      </section>

      <section className="overview-recent-scans" aria-labelledby="recent-market-scans-title">
        <header>
          <h2 className="eyebrow" id="recent-market-scans-title">Recent Market Scans</h2>
          <Link className="text-link" to="/decisions">View all scans <ArrowRight aria-hidden="true" /></Link>
        </header>
        <div className="overview-run-list">
          {runs.data?.slice(0, 3).map((run) => (
            <Link to={`/agent/runs/${run.run_id}`} key={run.run_id}>
              <time>{format.dateTime(run.started_at)}</time><StatusBadge status={run.status} />
              <strong>{run.summary || 'Market scan trace recorded.'}</strong><ArrowRight aria-hidden="true" />
            </Link>
          ))}
          {!runs.data?.length && <div className="overview-empty"><CircleDashed aria-hidden="true" /><strong>No market scans recorded</strong><p>The first scheduled US-market scan will appear here.</p></div>}
        </div>
      </section>

      <section className="panel data-health-summary">
        <div className="panel-heading"><div><p className="eyebrow">DATA HEALTH</p><h2>What the latest completed scan actually observed</h2></div><span><Database aria-hidden="true" /> {observedAt}</span></div>
        <div className="health-source-grid">
          {health.map((source) => {
            const state = source.state
            const statusKey = state.toLowerCase().replace(' ', '_')
            return <div key={source.name} data-state={statusKey.replace('_', '-')}><span>{state === 'Ready' ? <ShieldCheck aria-hidden="true" /> : <CircleDashed aria-hidden="true" />}<strong>{source.name}</strong></span><StatusBadge status={statusKey}>{state}</StatusBadge><p>{source.detail}</p></div>
          })}
        </div>
      </section></>}
    </div>
  )
}
