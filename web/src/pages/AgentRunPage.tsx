import { ArrowLeft, Bot, BrainCircuit, CheckCircle2, CircleDashed, ShieldCheck, WalletCards } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'
import { useAgentRun } from '../api/queries.ts'
import { ErrorState, LoadingState } from '../components/States.tsx'
import { StatusBadge } from '../components/StatusBadge.tsx'
import { format } from '../lib/format.ts'

export function AgentRunPage() {
  const { runId = '' } = useParams()
  const query = useAgentRun(runId)
  if (query.isLoading) return <LoadingState label="Reconstructing the decision trace" />
  if (query.error) return <ErrorState error={query.error} retry={() => void query.refetch()} />
  if (!query.data) return null
  const { run, signals, risk_decision: risk, exit_intent: exitIntent, receipt, portfolio } = query.data

  return (
    <div className="page agent-run-page">
      <Link className="back-link" to="/agent"><ArrowLeft />Back to Agent Console</Link>
      <header className="run-detail-head">
        <div><p className="eyebrow">IMMUTABLE DECISION TRACE</p><h1>{run.run_id}</h1><p>{run.summary || 'Agent run audit.'}</p></div>
        <div><StatusBadge status={run.status} /><span className="mode-chip"><ShieldCheck />{run.mode.toUpperCase()} ONLY</span></div>
      </header>

      <section className="trace-meta">
        <div><span>STARTED</span><strong>{format.dateTime(run.started_at)}</strong></div>
        <div><span>MODEL</span><strong>{run.model}</strong></div>
        <div><span>CONFIG</span><strong>{run.config_version}</strong></div>
        <div><span>SOURCE HASHES</span><strong>{Object.keys(run.source_hashes).length}</strong></div>
      </section>

      <div className="audit-timeline">
        <article><div className="timeline-marker"><span>01</span><Bot /></div><section><p className="eyebrow">SIGNAL SNAPSHOTS</p><h2>{signals.length} symbols observed</h2><div className="audit-signal-grid">{signals.map((signal) => <div key={signal.symbol}><strong>{signal.symbol}</strong><span>Attention {signal.attention_z?.toFixed(2) ?? '—'}</span><span>Move {signal.move_z.toFixed(2)}</span><b>{signal.crowd_excess_score >= 0 ? '+' : ''}{signal.crowd_excess_score.toFixed(2)}</b></div>)}</div></section></article>
        <article><div className="timeline-marker"><span>02</span><BrainCircuit /></div><section><p className="eyebrow">EVIDENCE ASSESSMENT</p><h2>{signals[0]?.evidence.rationale ?? 'No complete evidence assessment'}</h2><p>Structured output only. The model assessed news direction, materiality, and confidence; it did not select contracts or size.</p>{signals[0]?.evidence_headlines.map((headline) => <div className="headline-row" key={headline.id}><span>{headline.source}</span><strong>{headline.headline}</strong></div>)}</section></article>
        <article><div className="timeline-marker"><span>03</span><ShieldCheck /></div><section><p className="eyebrow">{exitIntent ? 'EXIT POLICY' : 'RISK DECISION'}</p><h2>{exitIntent ? `${exitIntent.reason.replaceAll('_', ' ')} triggered at ${(exitIntent.pnl_ratio * 100).toFixed(1)}%` : risk ? (risk.approved ? 'Approved by deterministic controls' : `Abstained — ${risk.denial_reason}`) : 'No candidate reached risk evaluation'}</h2><div className="full-gate-list">{risk?.gates.map((gate) => <div data-pass={gate.passed} key={gate.code}>{gate.passed ? <CheckCircle2 /> : <CircleDashed />}<span><strong>{gate.code.replaceAll('_', ' ')}</strong><small>{gate.detail}</small></span></div>)}</div></section></article>
        <article><div className="timeline-marker"><span>04</span><WalletCards /></div><section><p className="eyebrow">EXECUTION RECEIPT</p><h2>{receipt ? `${receipt.action.toUpperCase()} · ${receipt.state.toUpperCase()}` : 'No order submitted'}</h2>{receipt ? <dl className="receipt-detail"><div><dt>Client order ID</dt><dd>{receipt.client_order_id}</dd></div><div><dt>Alpaca order ID</dt><dd>{receipt.alpaca_order_id ?? 'Shadow mode'}</dd></div><div><dt>{receipt.action === 'close' ? 'Limit credit' : 'Limit debit'}</dt><dd>${(receipt.limit_credit ?? receipt.limit_debit).toFixed(2)}</dd></div><div><dt>Quantity</dt><dd>{receipt.quantity}</dd></div></dl> : <p>A no-trade result is an expected agent outcome when any gate fails.</p>}</section></article>
        <article><div className="timeline-marker"><span>05</span><WalletCards /></div><section><p className="eyebrow">PORTFOLIO AFTER DECISION</p><h2>{portfolio ? `$${portfolio.equity.toLocaleString('en-US')}` : 'No portfolio snapshot'}</h2>{portfolio && <p>Daily P&amp;L ${portfolio.daily_pnl.toLocaleString('en-US')} · open premium risk ${portfolio.open_premium_risk.toLocaleString('en-US')} · {portfolio.open_spread_count} open spreads.</p>}</section></article>
      </div>
    </div>
  )
}
