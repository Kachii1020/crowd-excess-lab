import {
  Activity, ArrowRight, Bot, BrainCircuit, CheckCircle2, CircleDashed, Gauge,
  Newspaper, ShieldCheck, WalletCards,
} from 'lucide-react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  useAgentRun, useAgentRuns, useAgentSignals, useAgentStatus, usePortfolio, useStrategy,
} from '../api/queries.ts'
import type { SignalSnapshot } from '../api/schemas.ts'
import { ErrorState, LoadingState } from '../components/States.tsx'
import { StatusBadge } from '../components/StatusBadge.tsx'
import { format } from '../lib/format.ts'

const UNIVERSE = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'QQQ']
const usd = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })

function signed(value: number | null | undefined, digits = 2) {
  if (value === null || value === undefined) return '—'
  return `${value >= 0 ? '+' : ''}${value.toFixed(digits)}`
}

function signalFor(symbol: string, signals: SignalSnapshot[]) {
  return signals.find((signal) => signal.symbol === symbol)
}

export function AgentConsolePage() {
  const status = useAgentStatus()
  const runs = useAgentRuns()
  const signals = useAgentSignals()
  const portfolio = usePortfolio()
  const strategy = useStrategy()
  const latestRunId = status.data?.last_run?.run_id ?? ''
  const detail = useAgentRun(latestRunId)
  const [searchParams, setSearchParams] = useSearchParams()

  if (status.isLoading || runs.isLoading || signals.isLoading || portfolio.isLoading || strategy.isLoading) {
    return <LoadingState label="Loading the agent audit" />
  }
  const error = status.error || runs.error || signals.error || portfolio.error || strategy.error
  if (error) return <ErrorState error={error} retry={() => window.location.reload()} />

  const availableSignals = signals.data ?? []
  const requested = searchParams.get('symbol')?.toUpperCase()
  const fallback = [...availableSignals].sort((a, b) => Math.abs(b.crowd_excess_score) - Math.abs(a.crowd_excess_score))[0]?.symbol ?? 'AAPL'
  const selectedSymbol = requested && UNIVERSE.includes(requested) ? requested : fallback
  const selected = signalFor(selectedSymbol, availableSignals)
  const risk = detail.data?.risk_decision
  const receipt = detail.data?.receipt
  const runStatus = status.data?.last_run?.status ?? 'pending'
  const lastRunSummary = status.data?.last_run?.summary ?? ''
  const marketClosedNotSampled = runStatus === 'abstained'
    && availableSignals.length === 0
    && /market(?: clock)? is closed|market closed/i.test(lastRunSummary)
  const noSignals = availableSignals.length === 0

  return (
    <div className="agent-console">
      <header className="agent-console-head">
        <div>
          <p className="eyebrow">READ-ONLY DECISION AUDIT / US EQUITIES</p>
          <h1>Decision Workbench</h1>
          <p>Inspect how attention, market movement, evidence, and fixed risk controls produced the latest paper-only decision.</p>
        </div>
        <div className="console-state">
          <span className={status.data?.configured ? 'signal-dot' : 'signal-dot signal-dot--off'} />
          <div><strong>{status.data?.configured ? 'Audit connected' : 'Setup pending'}</strong><small>{status.data?.mode.toUpperCase()} MODE · NO LIVE PATH</small></div>
          <StatusBadge status={runStatus} />
        </div>
      </header>

      <section className="decision-flow" aria-label="Agent decision flow">
        <div><Activity aria-hidden="true" /><span><small>01 / ATTENTION</small><strong>Cross-border search</strong></span></div><ArrowRight aria-hidden="true" />
        <div><Newspaper aria-hidden="true" /><span><small>02 / EVIDENCE</small><strong>Price + news</strong></span></div><ArrowRight aria-hidden="true" />
        <div><BrainCircuit aria-hidden="true" /><span><small>03 / RESIDUAL</small><strong>Crowd Excess</strong></span></div><ArrowRight aria-hidden="true" />
        <div><ShieldCheck aria-hidden="true" /><span><small>04 / CONTROL</small><strong>Risk gates</strong></span></div><ArrowRight aria-hidden="true" />
        <div><WalletCards aria-hidden="true" /><span><small>05 / RECEIPT</small><strong>Alpaca paper</strong></span></div>
      </section>

      <section className="agent-kpi-strip" aria-label="Current agent metrics" aria-live="polite" aria-atomic="true">
        <div><span>ACCOUNT EQUITY</span><strong>{portfolio.data ? usd.format(portfolio.data.equity) : '—'}</strong><small>{portfolio.data ? `${signed(portfolio.data.daily_pnl, 0)} today` : 'Awaiting paper account'}</small></div>
        <div><span>TOP RESIDUAL</span><strong>{selected ? signed(selected.crowd_excess_score) : '—'}</strong><small>{selected ? selected.symbol : 'No completed scan'}</small></div>
        <div><span>OPEN RISK</span><strong>{portfolio.data ? usd.format(portfolio.data.open_premium_risk) : '—'}</strong><small>{portfolio.data ? `${portfolio.data.open_spread_count} / ${strategy.data?.max_open_spreads} spreads` : 'No portfolio snapshot'}</small></div>
        <div><span>LAST DECISION</span><strong>{status.data?.last_run ? status.data.last_run.status.toUpperCase() : 'WAITING'}</strong><small>{status.data?.last_run ? format.dateTime(status.data.last_run.started_at) : 'No autonomous run yet'}</small></div>
        <div><span>MODEL ROLE</span><strong>EVIDENCE</strong><small>{strategy.data?.version ?? 'Fixed strategy'} · never sizes orders</small></div>
      </section>

      {!status.data?.configured && (
        <section className="setup-banner">
          <CircleDashed aria-hidden="true" />
          <div><strong>Live audit data is not connected yet.</strong><p>The public interface is ready. Connect the Supabase anonymous reader after the first sanitized shadow run; no fixture is presented as execution.</p></div>
        </section>
      )}

      <div className="agent-terminal-grid">
        <section className="terminal-block run-tape">
          <div className="block-head"><h2><Bot aria-hidden="true" />RUN TAPE</h2><small>{runs.data?.length ?? 0} RECORDED</small></div>
          <div className="run-list">
            {runs.data?.map((run) => (
              <Link to={`/agent/runs/${run.run_id}`} key={run.run_id}>
                <span className="run-time">{format.dateTime(run.started_at)}</span>
                <strong>{run.status.toUpperCase()}</strong>
                <small>{run.summary || 'Decision trace recorded.'}</small>
                <StatusBadge status={run.mode} />
              </Link>
            ))}
            {!runs.data?.length && <div className="terminal-empty"><CircleDashed /><strong>No runs recorded</strong><p>The first market-window shadow scan will appear here.</p></div>}
          </div>
        </section>

        <section className="terminal-block signal-matrix">
          <div className="block-head"><h2><Gauge aria-hidden="true" />CROWD EXCESS MATRIX</h2><small>{noSignals ? 'NOT SAMPLED · LATEST CHECK' : 'SPY-ADJUSTED · LATEST SCAN'}</small></div>
          {noSignals ? (
            <div className="terminal-empty" role="status" aria-live="polite">
              <CircleDashed aria-hidden="true" />
              <strong>{marketClosedNotSampled ? 'Market closed — not sampled' : 'No completed scan recorded'}</strong>
              <p>{marketClosedNotSampled ? lastRunSummary : 'The audit store does not contain a complete five-symbol market scan yet.'}</p>
              {status.data?.last_run && <p>Observed {format.dateTime(status.data.last_run.started_at)}. No market, news, options, or evidence inputs were treated as current.</p>}
              <p>{marketClosedNotSampled ? 'Return during the next US regular market window to inspect a complete five-symbol scan. No order was attempted.' : 'Return after the next eligible US-market automation check. Missing inputs are never treated as zero.'}</p>
            </div>
          ) : (
            <>
              <div className="signal-table-wrap">
                <table className="signal-table">
                  <thead><tr><th>Symbol</th><th>Attention Z</th><th>Move Z</th><th>Volume Z</th><th>Evidence</th><th>Residual</th><th>Action</th></tr></thead>
                  <tbody>
                    {UNIVERSE.map((symbol) => {
                      const signal = signalFor(symbol, availableSignals)
                      const active = symbol === selectedSymbol
                      return (
                        <tr data-active={active} key={symbol}>
                          <td><button type="button" aria-pressed={active} onClick={() => setSearchParams({ symbol })}><strong>{symbol}</strong><small>{active ? 'INSPECTING' : 'UNIVERSE'}</small></button></td>
                          <td>{signed(signal?.attention_z)}</td>
                          <td className={(signal?.move_z ?? 0) >= 0 ? 'positive' : 'negative'}>{signed(signal?.move_z)}</td>
                          <td>{signed(signal?.volume_z)}</td>
                          <td>{signal ? `${Math.round(signal.evidence.confidence * 100)}%` : '—'}</td>
                          <td className={(signal?.crowd_excess_score ?? 0) >= 0 ? 'positive' : 'negative'}><strong>{signed(signal?.crowd_excess_score)}</strong></td>
                          <td>{signal?.eligible ? <StatusBadge status={signal.trade_direction ?? 'eligible'} /> : <StatusBadge status="abstain" />}</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
              <div className="matrix-legend"><span><i className="legend-up" /> Positive residual: excessive upside enthusiasm</span><span><i className="legend-down" /> Negative residual: excessive downside pessimism</span><span>Trade direction is contrarian.</span></div>
            </>
          )}
        </section>

        <aside className="terminal-block decision-inspector">
          <div className="block-head"><h2><BrainCircuit aria-hidden="true" />DECISION TRACE</h2><small>{selectedSymbol}</small></div>
          <section>
            <p className="eyebrow">STRUCTURED EVIDENCE</p>
            <h2>{selected ? selected.evidence.rationale : 'Awaiting first complete scan'}</h2>
            <dl>
              <div><dt>Direction</dt><dd>{selected ? signed(selected.evidence.direction) : '—'}</dd></div>
              <div><dt>Materiality</dt><dd>{selected ? `${Math.round(selected.evidence.materiality * 100)}%` : '—'}</dd></div>
              <div><dt>Confidence</dt><dd>{selected ? `${Math.round(selected.evidence.confidence * 100)}%` : '—'}</dd></div>
              <div><dt>Model</dt><dd>{selected?.evidence_model || '—'}</dd></div>
            </dl>
            {selected?.evidence_headlines.slice(0, 2).map((headline) => <div className="headline-row" key={headline.id}><span>{headline.source}</span><strong>{headline.headline}</strong></div>)}
          </section>
          <section>
            <p className="eyebrow">DETERMINISTIC RISK</p>
            <div className="gate-summary"><strong>{risk ? `${risk.gates.filter((gate) => gate.passed).length}/${risk.gates.length}` : '—'}</strong><span>gates passed</span>{risk && (risk.approved ? <CheckCircle2 /> : <CircleDashed />)}</div>
            <ul className="gate-mini-list">
              {risk?.gates.slice(0, 6).map((gate) => <li data-pass={gate.passed} key={gate.code}>{gate.passed ? <CheckCircle2 /> : <CircleDashed />}<span>{gate.code.replaceAll('_', ' ')}</span></li>)}
              {!risk && <li data-pass="false"><CircleDashed /><span>No candidate reached option construction</span></li>}
            </ul>
          </section>
          <section className="receipt-summary">
            <p className="eyebrow">ALPACA RECEIPT</p>
            <strong>{receipt ? receipt.state.toUpperCase() : 'NO ORDER'}</strong>
            <small>{receipt ? `${receipt.filled_quantity}/${receipt.quantity} spread units filled · ${receipt.alpaca_order_id ?? receipt.message}` : status.data?.last_run?.summary ?? 'A no-trade decision is valid.'}</small>
            {latestRunId && <Link className="text-link" to={`/agent/runs/${latestRunId}`}>Open full audit trace <ArrowRight /></Link>}
          </section>
        </aside>
      </div>
    </div>
  )
}
