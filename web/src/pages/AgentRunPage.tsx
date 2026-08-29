import { useState } from 'react'
import { ArrowLeft, Bot, BrainCircuit, CheckCircle2, CircleDashed, Copy, ShieldCheck, WalletCards } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'
import { useAgentRun, useAgentRuns } from '../api/queries.ts'
import { ErrorState, LoadingState } from '../components/States.tsx'
import { StatusBadge } from '../components/StatusBadge.tsx'
import { format } from '../lib/format.ts'

export function AgentRunPage() {
  const { runId = '' } = useParams()
  const query = useAgentRun(runId)
  const runsQuery = useAgentRuns()
  const [copyStatus, setCopyStatus] = useState('')
  if (query.isLoading) return <LoadingState label="Reconstructing the decision trace" />
  if (query.error) return <ErrorState error={query.error} retry={() => void query.refetch()} />
  if (!query.data) return null
  const { run, signals, risk_decision: risk, exit_intent: exitIntent, receipt, portfolio } = query.data
  const runIndex = runsQuery.data?.findIndex((candidate) => candidate.run_id === run.run_id) ?? -1
  const previousRun = runIndex >= 0 ? runsQuery.data?.[runIndex + 1] : undefined
  const comparisonSymbol = [...signals]
    .sort((a, b) => Math.abs(b.crowd_excess_score) - Math.abs(a.crowd_excess_score))[0]?.symbol
  const compareParams = previousRun
    ? new URLSearchParams({
        run: run.run_id,
        compare: previousRun.run_id,
        ...(comparisonSymbol ? { symbol: comparisonSymbol } : {}),
      })
    : null
  const backParams = new URLSearchParams({
    run: run.run_id,
    ...(comparisonSymbol ? { symbol: comparisonSymbol } : {}),
  })
  const hasExecutionReceipt = Boolean(receipt && receipt.state !== 'shadow')
  const focusStage = hasExecutionReceipt || receipt
    ? 'receipt'
    : run.status === 'abstained' || (risk && !risk.approved)
      ? 'risk'
      : 'signals'
  const riskSummary = exitIntent
    ? `${exitIntent.reason.replaceAll('_', ' ')} triggered at ${(exitIntent.pnl_ratio * 100).toFixed(1)}%`
    : risk
      ? (risk.approved ? 'Approved by deterministic controls' : `Abstained — ${risk.denial_reason}`)
      : run.status === 'abstained'
        ? `Abstained — ${run.summary || run.error || 'No candidate reached risk evaluation'}`
        : 'No candidate reached risk evaluation'

  const copyRunLink = async () => {
    try {
      if (!navigator.clipboard) throw new Error('Clipboard unavailable')
      await navigator.clipboard.writeText(window.location.href)
      setCopyStatus('Run link copied')
    } catch {
      setCopyStatus('Copy unavailable. Use the browser address bar.')
    }
  }

  return (
    <div className="page agent-run-page">
      <Link className="back-link" to={`/decisions?${backParams.toString()}`}><ArrowLeft />Back to Market Scan</Link>
      <header className="run-detail-head">
        <div><p className="eyebrow">IMMUTABLE DECISION TRACE</p><h1>{run.run_id}</h1><p>{run.summary || 'Agent run audit.'}</p></div>
        <div>
          <StatusBadge status={run.status} />
          <span className="mode-chip"><ShieldCheck />{run.mode.toUpperCase()} ONLY</span>
          {compareParams && <Link className="mode-chip" to={`/decisions?${compareParams.toString()}`}>Compare with previous</Link>}
          <button className="mode-chip" type="button" onClick={() => void copyRunLink()} aria-describedby="copy-run-status"><Copy aria-hidden="true" />Copy run link</button>
          <span className="sr-only" id="copy-run-status" aria-live="polite">{copyStatus}</span>
        </div>
      </header>

      <section className="trace-meta">
        <div><span>STARTED</span><strong>{format.dateTime(run.started_at)}</strong></div>
        <div><span>MODEL</span><strong>{run.model}</strong></div>
        <div><span>CONFIG</span><strong>{run.config_version}</strong></div>
        <div><span>SOURCE HASHES</span><strong>{Object.keys(run.source_hashes).length}</strong></div>
        {run.failure_stage && <div><span>FAILURE STAGE</span><strong>{run.failure_stage.replaceAll('_', ' ')}</strong></div>}
        {run.failure_code && <div><span>FAILURE CODE</span><strong>{run.failure_code}</strong></div>}
        {run.market_clock && <div><span>MARKET AT CHECK</span><strong>{run.market_clock.is_open ? 'OPEN' : 'CLOSED'} · {format.dateTime(run.market_clock.observed_at)}</strong></div>}
      </section>

      <div className="audit-timeline">
        <article>
          <div className="timeline-marker"><span>01</span><Bot aria-hidden="true" /></div>
          <section><details className="audit-disclosure" open={focusStage === 'signals'}><summary><span>Signal snapshots</span><strong>{signals.length} symbols observed</strong></summary><div className="audit-disclosure-body"><h2 className="sr-only">Signal snapshots</h2>{signals.length > 0 ? <div className="audit-signal-grid">{signals.map((signal) => <div key={signal.symbol}><strong>{signal.symbol}</strong><span>Attention {signal.attention_z?.toFixed(2) ?? '—'}</span><span>Move {signal.move_z.toFixed(2)}</span><b>{signal.crowd_excess_score >= 0 ? '+' : ''}{signal.crowd_excess_score.toFixed(2)}</b></div>)}</div> : <p>No market inputs were sampled for this run. {run.summary}</p>}</div></details></section>
        </article>
        <article>
          <div className="timeline-marker"><span>02</span><BrainCircuit aria-hidden="true" /></div>
          <section><details className="audit-disclosure"><summary><span>Evidence assessment</span><strong>{signals[0] ? 'Structured assessment recorded' : 'Not sampled'}</strong></summary><div className="audit-disclosure-body"><h2>{signals[0]?.evidence.rationale ?? 'No complete evidence assessment'}</h2><p>Structured output only. The model assessed news direction, materiality, and confidence; it did not select contracts or size.</p>{signals[0]?.evidence_headlines.map((headline) => <div className="headline-row" key={headline.id}><span>{headline.source}</span><strong>{headline.headline}</strong></div>)}</div></details></section>
        </article>
        <article>
          <div className="timeline-marker"><span>03</span><ShieldCheck aria-hidden="true" /></div>
          <section><details className="audit-disclosure" open={focusStage === 'risk'}><summary><span>{exitIntent ? 'Exit policy' : 'Risk decision'}</span><strong>{riskSummary}</strong></summary><div className="audit-disclosure-body"><h2 className="sr-only">{exitIntent ? 'Exit policy' : 'Risk decision'}</h2>{risk?.gates.length ? <div className="full-gate-list">{risk.gates.map((gate) => <div data-pass={gate.passed} key={gate.code}>{gate.passed ? <CheckCircle2 aria-hidden="true" /> : <CircleDashed aria-hidden="true" />}<span><strong>{gate.code.replaceAll('_', ' ')}</strong><small>{gate.detail}</small></span></div>)}</div> : <p>{run.summary || 'No candidate reached deterministic risk evaluation.'}</p>}</div></details></section>
        </article>
        <article>
          <div className="timeline-marker"><span>04</span><WalletCards aria-hidden="true" /></div>
          <section><details className="audit-disclosure" open={focusStage === 'receipt'}><summary><span>Execution receipt</span><strong>{receipt ? `${receipt.action.toUpperCase()} · ${receipt.state.toUpperCase()}` : 'No order submitted'}</strong></summary><div className="audit-disclosure-body"><h2 className="sr-only">Execution receipt</h2>{receipt ? <dl className="receipt-detail"><div><dt>Client order ID</dt><dd>{receipt.client_order_id}</dd></div><div><dt>Alpaca order ID</dt><dd>{receipt.alpaca_order_id ?? 'Shadow mode'}</dd></div><div><dt>{receipt.action === 'close' ? 'Limit credit' : 'Limit debit'}</dt><dd>${(receipt.limit_credit ?? receipt.limit_debit).toFixed(2)}</dd></div><div><dt>Filled / requested</dt><dd>{receipt.filled_quantity} / {receipt.quantity}</dd></div></dl> : <p>A no-trade result is an expected agent outcome when any gate fails.</p>}</div></details></section>
        </article>
        <article>
          <div className="timeline-marker"><span>05</span><WalletCards aria-hidden="true" /></div>
          <section><details className="audit-disclosure"><summary><span>Portfolio after decision</span><strong>{portfolio ? `$${portfolio.equity.toLocaleString('en-US')}` : 'No portfolio snapshot'}</strong></summary><div className="audit-disclosure-body"><h2 className="sr-only">Portfolio after decision</h2>{portfolio ? <p>Daily P&amp;L ${portfolio.daily_pnl.toLocaleString('en-US')} · open premium risk ${portfolio.open_premium_risk.toLocaleString('en-US')} · {portfolio.open_spread_count} open spreads.</p> : <p>No portfolio snapshot was recorded for this run.</p>}</div></details></section>
        </article>
      </div>
    </div>
  )
}
