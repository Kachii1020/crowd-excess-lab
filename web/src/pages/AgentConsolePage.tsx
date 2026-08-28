import {
  Activity, ArrowRight, Bot, BrainCircuit, CheckCircle2, CircleDashed, Gauge,
  GitCompareArrows, Newspaper, ShieldCheck, WalletCards,
} from 'lucide-react'
import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  useAgentRun, useAgentRuns, useAgentSignals, useAgentStatus, usePortfolio, useStrategy,
} from '../api/queries.ts'
import type { AgentRunDetail, SignalSnapshot } from '../api/schemas.ts'
import { ErrorState, LoadingState } from '../components/States.tsx'
import { StatusBadge } from '../components/StatusBadge.tsx'
import { format } from '../lib/format.ts'

const UNIVERSE = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'QQQ']
const usd = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
const percent = new Intl.NumberFormat('en-US', { style: 'percent', maximumFractionDigits: 0 })

function signed(value: number | null | undefined, digits = 2) {
  if (value === null || value === undefined) return '—'
  return `${value >= 0 ? '+' : ''}${value.toFixed(digits)}`
}

function signalFor(symbol: string, signals: SignalSnapshot[]) {
  return signals.find((signal) => signal.symbol === symbol)
}

function topSignal(detail: AgentRunDetail | undefined) {
  return [...(detail?.signals ?? [])]
    .sort((a, b) => Math.abs(b.crowd_excess_score) - Math.abs(a.crowd_excess_score))[0]
}

function signedUsd(value: number | null | undefined) {
  if (value === null || value === undefined) return '—'
  return `${value >= 0 ? '+' : '−'}${usd.format(Math.abs(value))}`
}

function numericDelta(
  primary: number | null | undefined,
  secondary: number | null | undefined,
  digits = 2,
) {
  if (primary === null || primary === undefined || secondary === null || secondary === undefined) return '—'
  return `B − A ${signed(secondary - primary, digits)}`
}

function currencyDelta(primary: number | null | undefined, secondary: number | null | undefined) {
  if (primary === null || primary === undefined || secondary === null || secondary === undefined) return '—'
  return `B − A ${signedUsd(secondary - primary)}`
}

function confidenceDelta(primary: number | null | undefined, secondary: number | null | undefined) {
  if (primary === null || primary === undefined || secondary === null || secondary === undefined) return '—'
  const difference = Math.round((secondary - primary) * 100)
  return `B − A ${difference >= 0 ? '+' : ''}${difference} pp`
}

function comparisonRows(primary: AgentRunDetail, secondary: AgentRunDetail) {
  const aSignal = topSignal(primary)
  const bSignal = topSignal(secondary)
  const aFailedGate = primary.risk_decision?.gates.find((gate) => !gate.passed)
  const bFailedGate = secondary.risk_decision?.gates.find((gate) => !gate.passed)
  const evidence = (signal: SignalSnapshot | undefined) => signal
    ? `${signed(signal.evidence.direction)} dir · ${percent.format(signal.evidence.materiality)} mat · ${percent.format(signal.evidence.confidence)} conf`
    : 'Not sampled'

  return [
    { label: 'Status', a: primary.run.status.toUpperCase(), b: secondary.run.status.toUpperCase(), delta: primary.run.status === secondary.run.status ? 'Same state' : 'Different states' },
    { label: 'Observed', a: format.dateTime(primary.run.started_at), b: format.dateTime(secondary.run.started_at), delta: 'Timestamp context' },
    { label: 'Top symbol', a: aSignal?.symbol ?? 'Not sampled', b: bSignal?.symbol ?? 'Not sampled', delta: aSignal?.symbol === bSignal?.symbol ? 'Same symbol' : 'Different symbols' },
    { label: 'Attention Z', a: signed(aSignal?.attention_z), b: signed(bSignal?.attention_z), delta: numericDelta(aSignal?.attention_z, bSignal?.attention_z) },
    { label: 'Move Z', a: signed(aSignal?.move_z), b: signed(bSignal?.move_z), delta: numericDelta(aSignal?.move_z, bSignal?.move_z) },
    { label: 'Evidence', a: evidence(aSignal), b: evidence(bSignal), delta: confidenceDelta(aSignal?.evidence.confidence, bSignal?.evidence.confidence) },
    { label: 'Residual', a: signed(aSignal?.crowd_excess_score), b: signed(bSignal?.crowd_excess_score), delta: numericDelta(aSignal?.crowd_excess_score, bSignal?.crowd_excess_score) },
    { label: 'First failed gate', a: aFailedGate?.code.replaceAll('_', ' ') ?? 'None recorded', b: bFailedGate?.code.replaceAll('_', ' ') ?? 'None recorded', delta: aFailedGate?.code === bFailedGate?.code ? 'Same gate result' : 'Different gate results' },
    { label: 'Receipt state', a: primary.receipt?.state.replaceAll('_', ' ').toUpperCase() ?? 'NO ORDER', b: secondary.receipt?.state.replaceAll('_', ' ').toUpperCase() ?? 'NO ORDER', delta: primary.receipt?.state === secondary.receipt?.state ? 'Same receipt state' : 'Different receipt states' },
    { label: 'Equity', a: primary.portfolio ? usd.format(primary.portfolio.equity) : 'Not recorded', b: secondary.portfolio ? usd.format(secondary.portfolio.equity) : 'Not recorded', delta: currencyDelta(primary.portfolio?.equity, secondary.portfolio?.equity) },
    { label: 'Daily P&L', a: signedUsd(primary.portfolio?.daily_pnl), b: signedUsd(secondary.portfolio?.daily_pnl), delta: currencyDelta(primary.portfolio?.daily_pnl, secondary.portfolio?.daily_pnl) },
    { label: 'Open risk', a: primary.portfolio ? usd.format(primary.portfolio.open_premium_risk) : 'Not recorded', b: secondary.portfolio ? usd.format(secondary.portfolio.open_premium_risk) : 'Not recorded', delta: currencyDelta(primary.portfolio?.open_premium_risk, secondary.portfolio?.open_premium_risk) },
  ]
}

export function AgentConsolePage() {
  const status = useAgentStatus()
  const runs = useAgentRuns()
  const signals = useAgentSignals()
  const portfolio = usePortfolio()
  const strategy = useStrategy()
  const [searchParams, setSearchParams] = useSearchParams()
  const [mobileCompareFocus, setMobileCompareFocus] = useState<'primary' | 'secondary'>('primary')
  const recordedRuns = runs.data ?? []
  const requestedPrimaryRunId = searchParams.get('run') ?? ''
  const primaryRunId = recordedRuns.some((run) => run.run_id === requestedPrimaryRunId)
    ? requestedPrimaryRunId
    : status.data?.last_run?.run_id ?? recordedRuns[0]?.run_id ?? ''
  const requestedCompareRunId = searchParams.get('compare') ?? ''
  const compareRunId = requestedCompareRunId !== primaryRunId
    && recordedRuns.some((run) => run.run_id === requestedCompareRunId)
    ? requestedCompareRunId
    : ''
  const detail = useAgentRun(primaryRunId)
  const compareDetail = useAgentRun(compareRunId)

  const updateSearch = (updates: Record<string, string | null>) => {
    const next = new URLSearchParams(searchParams)
    Object.entries(updates).forEach(([key, value]) => {
      if (value) next.set(key, value)
      else next.delete(key)
    })
    setSearchParams(next)
  }

  const selectPrimaryRun = (runId: string) => {
    updateSearch({ run: runId, compare: compareRunId === runId ? null : compareRunId })
  }

  const selectCompareRun = (runId: string) => {
    if (runId === primaryRunId || recordedRuns.length < 2) return
    updateSearch({ run: primaryRunId, compare: runId })
    setMobileCompareFocus('secondary')
  }

  if (status.isLoading || runs.isLoading || signals.isLoading || portfolio.isLoading || strategy.isLoading || (Boolean(primaryRunId) && detail.isLoading)) {
    return <LoadingState label="Loading the agent audit" />
  }
  const error = status.error || runs.error || signals.error || portfolio.error || strategy.error || detail.error
  if (error) return <ErrorState error={error} retry={() => window.location.reload()} />

  const latestRunId = status.data?.last_run?.run_id ?? ''
  const availableSignals = detail.data?.signals
    ?? (primaryRunId === latestRunId ? signals.data ?? [] : [])
  const requested = searchParams.get('symbol')?.toUpperCase()
  const fallback = [...availableSignals].sort((a, b) => Math.abs(b.crowd_excess_score) - Math.abs(a.crowd_excess_score))[0]?.symbol ?? 'AAPL'
  const selectedSymbol = requested && UNIVERSE.includes(requested) ? requested : fallback
  const selected = signalFor(selectedSymbol, availableSignals)
  const risk = detail.data?.risk_decision
  const receipt = detail.data?.receipt
  const runStatus = detail.data?.run.status ?? status.data?.last_run?.status ?? 'pending'
  const lastRunSummary = detail.data?.run.summary ?? status.data?.last_run?.summary ?? ''
  const marketClosedNotSampled = runStatus === 'abstained'
    && availableSignals.length === 0
    && /market(?: clock)? is closed|market closed/i.test(lastRunSummary)
  const noSignals = availableSignals.length === 0
  const compareRows = detail.data && compareDetail.data
    ? comparisonRows(detail.data, compareDetail.data)
    : []
  const compareAvailable = recordedRuns.length >= 2
  const primaryRunIndex = recordedRuns.findIndex((run) => run.run_id === primaryRunId)
  const suggestedCompareRun = recordedRuns[primaryRunIndex + 1]
    ?? recordedRuns.find((run) => run.run_id !== primaryRunId)
  const observedRun = detail.data?.run ?? status.data?.last_run

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
        <div><span>SELECTED DECISION</span><strong>{detail.data?.run ? detail.data.run.status.toUpperCase() : status.data?.last_run ? status.data.last_run.status.toUpperCase() : 'WAITING'}</strong><small>{detail.data?.run ? format.dateTime(detail.data.run.started_at) : status.data?.last_run ? format.dateTime(status.data.last_run.started_at) : 'No autonomous run yet'}</small></div>
        <div><span>MODEL ROLE</span><strong>EVIDENCE</strong><small>{strategy.data?.version ?? 'Fixed strategy'} · never sizes orders</small></div>
      </section>

      {!status.data?.configured && (
        <section className="setup-banner">
          <CircleDashed aria-hidden="true" />
          <div><strong>Live audit data is not connected yet.</strong><p>The public interface is ready. Connect the Supabase anonymous reader after the first sanitized shadow run; no fixture is presented as execution.</p></div>
        </section>
      )}

      <section className="terminal-block run-comparison" aria-labelledby="run-comparison-title">
        <div className="block-head">
          <h2 id="run-comparison-title"><GitCompareArrows aria-hidden="true" />RUN COMPARISON</h2>
          <small>{compareRunId ? 'A / B AUDIT VIEW' : 'OPTIONAL · READ ONLY'}</small>
        </div>
        {!compareAvailable ? (
          <div className="terminal-empty" role="status">
            <CircleDashed aria-hidden="true" />
            <strong>Comparison needs two recorded runs</strong>
            <p>{recordedRuns.length === 0 ? 'No runs are available.' : 'Only one run is available.'} A/B controls will unlock after the next autonomous check is stored.</p>
          </div>
        ) : !compareRunId ? (
          <div className="comparison-prompt">
            <div>
              <strong>Run A is selected. Choose any other run as B.</strong>
              <p>Use the A/B controls in Run Tape. The URL will preserve both immutable run IDs and the inspected symbol.</p>
            </div>
            <button type="button" onClick={() => selectCompareRun(suggestedCompareRun?.run_id ?? '')}>
              Compare with previous <ArrowRight aria-hidden="true" />
            </button>
          </div>
        ) : detail.isLoading || compareDetail.isLoading ? (
          <div className="comparison-loading" role="status" aria-live="polite">Loading both immutable run traces…</div>
        ) : detail.error || compareDetail.error ? (
          <div className="terminal-empty" role="alert">
            <CircleDashed aria-hidden="true" />
            <strong>One comparison trace could not be loaded</strong>
            <p>The selected run IDs remain in the URL. Retry after the audit API is available.</p>
          </div>
        ) : compareRows.length > 0 ? (
          <>
            <div className="compare-mobile-switch" role="group" aria-label="Visible comparison run on mobile">
              <button type="button" aria-pressed={mobileCompareFocus === 'primary'} onClick={() => setMobileCompareFocus('primary')}>Run A</button>
              <button type="button" aria-pressed={mobileCompareFocus === 'secondary'} onClick={() => setMobileCompareFocus('secondary')}>Run B</button>
            </div>
            <div className="comparison-delta-summary" aria-label="Run difference summary">
              <span>Differences are B minus A.</span>
              <strong><small>Residual</small>{compareRows.find((row) => row.label === 'Residual')?.delta}</strong>
              <strong><small>Daily P&amp;L</small>{compareRows.find((row) => row.label === 'Daily P&L')?.delta}</strong>
              <small>Direction only — no quality or profitability ranking is implied.</small>
            </div>
            <div className="run-comparison-table-wrap" data-mobile-focus={mobileCompareFocus}>
              <table className="run-comparison-table">
                <caption className="sr-only">Side-by-side comparison of selected agent runs A and B</caption>
                <thead><tr><th scope="col">Metric</th><th scope="col" className="compare-primary">Run A</th><th scope="col" className="compare-secondary">Run B</th><th scope="col" className="compare-delta">B − A</th></tr></thead>
                <tbody>
                  {compareRows.map((row) => (
                    <tr key={row.label}>
                      <th scope="row">{row.label}</th>
                      <td className="compare-primary">{row.a}</td>
                      <td className="compare-secondary">{row.b}</td>
                      <td className="compare-delta">{row.delta}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        ) : null}
      </section>

      <div className="agent-terminal-grid">
        <section className="terminal-block run-tape">
          <div className="block-head"><h2><Bot aria-hidden="true" />RUN TAPE</h2><small>{runs.data?.length ?? 0} RECORDED</small></div>
          <div className="run-list">
            {runs.data?.map((run) => (
              <div className="run-tape-entry" data-primary={run.run_id === primaryRunId} data-compare={run.run_id === compareRunId} key={run.run_id}>
                <Link className="run-tape-link" to={`/agent/runs/${run.run_id}`}>
                  <span className="run-time">{format.dateTime(run.started_at)}</span>
                  <strong>{run.status.toUpperCase()}</strong>
                  <small>{run.summary || 'Decision trace recorded.'}</small>
                  <StatusBadge status={run.mode} />
                </Link>
                <div className="run-select-actions" role="group" aria-label={`Compare run ${run.run_id}`}>
                  <button
                    type="button"
                    aria-label={`Use ${run.run_id} as run A`}
                    aria-pressed={run.run_id === primaryRunId}
                    onClick={() => selectPrimaryRun(run.run_id)}
                  >A</button>
                  <button
                    type="button"
                    aria-label={`Use ${run.run_id} as run B`}
                    aria-pressed={run.run_id === compareRunId}
                    disabled={!compareAvailable || run.run_id === primaryRunId}
                    title={run.run_id === primaryRunId ? 'Run B must be different from run A' : !compareAvailable ? 'Record a second run to compare' : 'Use as run B'}
                    onClick={() => selectCompareRun(run.run_id)}
                  >B</button>
                </div>
              </div>
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
              {observedRun && <p>Observed {format.dateTime(observedRun.started_at)}. No market, news, options, or evidence inputs were treated as current.</p>}
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
                          <td><button type="button" aria-pressed={active} onClick={() => updateSearch({ symbol })}><strong>{symbol}</strong><small>{active ? 'INSPECTING' : 'UNIVERSE'}</small></button></td>
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
            <small>{receipt ? `${receipt.filled_quantity}/${receipt.quantity} spread units filled · ${receipt.alpaca_order_id ?? receipt.message}` : detail.data?.run.summary ?? status.data?.last_run?.summary ?? 'A no-trade decision is valid.'}</small>
            {primaryRunId && <Link className="text-link" to={`/agent/runs/${primaryRunId}`}>Open full audit trace <ArrowRight /></Link>}
          </section>
        </aside>
      </div>
    </div>
  )
}
