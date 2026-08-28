import { CircleDollarSign, Gauge, ShieldCheck, WalletCards } from 'lucide-react'
import {
  Area, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip,
  XAxis, YAxis,
} from 'recharts'
import { usePortfolio, usePortfolioHistory, useStrategy } from '../api/queries.ts'
import type { Portfolio } from '../api/schemas.ts'
import { MetricCard } from '../components/MetricCard.tsx'
import { PageHeader } from '../components/PageHeader.tsx'
import { ErrorState, LoadingState } from '../components/States.tsx'
import { format } from '../lib/format.ts'

const usd = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
const signedUsd = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0, signDisplay: 'always' })
const percentage = new Intl.NumberFormat('en-US', { style: 'percent', maximumFractionDigits: 1 })
const compactUsd = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', notation: 'compact', maximumFractionDigits: 1 })

function boundedRatio(value: number, maximum: number) {
  if (!Number.isFinite(value) || !Number.isFinite(maximum) || maximum <= 0) return 0
  return Math.min(Math.max(value / maximum, 0), 1)
}

function UtilizationBar({ label, value, limit, detail }: { label: string, value: number, limit: number, detail: string }) {
  const ratio = boundedRatio(value, limit)
  return (
    <div className="utilization-row" data-utilization={ratio >= 1 ? 'blocked' : ratio >= 0.75 ? 'warning' : 'safe'}>
      <div><strong>{label}</strong><span>{usd.format(value)} / {usd.format(limit)}</span></div>
      <progress max={1} value={ratio} aria-label={`${label}: ${percentage.format(ratio)} of declared limit`} />
      <p>{percentage.format(ratio)} utilized · {detail}</p>
    </div>
  )
}

function PortfolioHistoryChart({ history }: { history: Portfolio[] }) {
  const chartData = history.map((snapshot) => ({
    ...snapshot,
    observedLabel: new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }).format(new Date(snapshot.observed_at)),
    drawdownPercent: snapshot.drawdown * 100,
  }))
  const latest = history.at(-1)
  return (
    <section className="panel portfolio-history-panel">
      <div className="panel-heading"><div><p className="eyebrow">ACCOUNT HISTORY</p><h2>Equity, P&amp;L, and drawdown</h2></div><span>{history.length} {history.length === 1 ? 'snapshot' : 'snapshots'}</span></div>
      {history.length > 1 ? (
        <>
          <div className="portfolio-chart" role="img" aria-label={`Paper account history across ${history.length} snapshots. Latest equity ${latest ? usd.format(latest.equity) : 'not observed'}, total P and L ${latest ? signedUsd.format(latest.total_pnl) : 'not observed'}, and drawdown ${latest ? percentage.format(latest.drawdown) : 'not observed'}.`}>
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={chartData} margin={{ top: 14, right: 12, bottom: 4, left: 2 }}>
                <CartesianGrid stroke="var(--border-subtle)" vertical={false} />
                <XAxis dataKey="observedLabel" minTickGap={42} tickLine={false} axisLine={false} />
                <YAxis yAxisId="money" tickFormatter={(value: number) => compactUsd.format(value)} width={62} tickLine={false} axisLine={false} />
                <YAxis yAxisId="percent" orientation="right" tickFormatter={(value: number) => `${value.toFixed(1)}%`} width={45} tickLine={false} axisLine={false} />
                <Tooltip formatter={(value, name) => name === 'Drawdown' ? `${Number(value).toFixed(2)}%` : usd.format(Number(value))} />
                <Area yAxisId="money" type="monotone" dataKey="equity" name="Equity" stroke="var(--accent)" fill="var(--accent-wash)" strokeWidth={2} />
                <Line yAxisId="money" type="monotone" dataKey="total_pnl" name="Total P&L" stroke="var(--text-secondary)" strokeWidth={1.5} dot={false} />
                <Line yAxisId="percent" type="monotone" dataKey="drawdownPercent" name="Drawdown" stroke="var(--warning)" strokeDasharray="4 4" strokeWidth={1.5} dot={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
          <p className="chart-note">Snapshots are displayed in recorded time order. Changes describe the paper account; they are not evidence of strategy profitability.</p>
        </>
      ) : (
        <div className="portfolio-history-empty"><strong>History begins with the first snapshot</strong><p>A trend requires at least two recorded portfolio observations. The latest verified account values remain visible above.</p></div>
      )}
    </section>
  )
}

export function PortfolioPage() {
  const portfolio = usePortfolio()
  const history = usePortfolioHistory(90)
  const strategy = useStrategy()
  if (portfolio.isLoading || strategy.isLoading) return <LoadingState label="Loading paper portfolio" />
  if (portfolio.error || strategy.error) return <ErrorState error={portfolio.error ?? strategy.error ?? new Error('Portfolio data is unavailable.')} retry={() => window.location.reload()} />
  const data = portfolio.data
  const config = strategy.data!
  const equity = data?.equity ?? 0
  const spreadRisk = data?.open_spread_count ? data.open_premium_risk / data.open_spread_count : 0
  const perPositionLimit = equity * config.max_position_risk_pct
  const totalPremiumLimit = equity * config.max_total_risk_pct
  const dailyLoss = Math.max(-(data?.daily_pnl ?? 0), 0)
  const dailyLossLimit = equity * config.daily_loss_limit_pct

  return (
    <div className="page portfolio-page">
      <PageHeader eyebrow="VERIFIED ALPACA PAPER ACCOUNT" title="Paper Portfolio" description="Every value comes from the dedicated competition account. The public interface cannot place, change, or cancel an order." />
      <section className="metric-grid portfolio-metrics" aria-live="polite">
        <MetricCard label="Equity" value={data ? usd.format(data.equity) : '—'} detail={data ? `Observed ${format.dateTime(data.observed_at)}` : 'Awaiting first account snapshot'} state={data ? 'ok' : 'neutral'} icon={<WalletCards />} />
        <MetricCard label="Daily P&L" value={data ? signedUsd.format(data.daily_pnl) : '—'} detail="Shown honestly; no profitability claim" state={(data?.daily_pnl ?? 0) >= 0 ? 'ok' : 'blocked'} icon={<CircleDollarSign />} />
        <MetricCard label="Open Premium Risk" value={data ? usd.format(data.open_premium_risk) : '—'} detail={`Hard cap ${(config.max_total_risk_pct * 100).toFixed(0)}% of equity`} state={(data?.open_premium_risk ?? 0) === 0 ? 'ok' : (data?.open_premium_risk ?? 0) > totalPremiumLimit ? 'blocked' : 'warning'} icon={<Gauge />} />
        <MetricCard label="Open Spreads" value={data ? `${data.open_spread_count} / ${config.max_open_spreads}` : '—'} detail="Defined-risk debit verticals only" state="neutral" icon={<ShieldCheck />} />
        <MetricCard label="Drawdown" value={data ? percentage.format(data.drawdown) : '—'} detail="Measured from the $100,000 competition start" state={(data?.drawdown ?? 0) > config.daily_loss_limit_pct ? 'warning' : 'neutral'} icon={<Gauge />} />
      </section>

      {history.isLoading
        ? <section className="panel portfolio-history-empty" role="status"><strong>Loading account history</strong><p>The current verified snapshot remains available while earlier observations are requested.</p></section>
        : history.error
        ? <section className="panel portfolio-history-empty" role="status"><strong>Account history is temporarily unavailable</strong><p>The current verified snapshot is still shown. No missing history point is interpolated.</p></section>
        : <PortfolioHistoryChart history={history.data ?? []} />}

      <section className="panel utilization-panel">
        <div className="panel-heading"><div><p className="eyebrow">RISK UTILIZATION</p><h2>Distance from declared limits</h2></div><ShieldCheck aria-hidden="true" /></div>
        {data ? (
          <div className="utilization-grid">
            <UtilizationBar label={data.open_spread_count > 1 ? 'Average position risk' : 'Position risk'} value={spreadRisk} limit={perPositionLimit} detail={data.open_spread_count > 1 ? 'Average open premium risk; per-spread max loss is inspected in its decision trace.' : 'Maximum 1% of current equity per spread.'} />
            <UtilizationBar label="Total premium risk" value={data.open_premium_risk} limit={totalPremiumLimit} detail="Maximum 3% of current equity across open spreads." />
            <UtilizationBar label="Daily-loss proximity" value={dailyLoss} limit={dailyLossLimit} detail="Opening new positions stops at the declared daily-loss gate." />
          </div>
        ) : <p>No portfolio snapshot is available, so risk utilization cannot be calculated.</p>}
      </section>

      <div className="portfolio-layout">
        <section className="panel positions-panel">
          <div className="panel-heading"><div><p className="eyebrow">OPEN POSITIONS</p><h2>Alpaca position snapshot</h2></div><span className="mono muted">READ ONLY</span></div>
          {data?.positions.length ? (
            <>
              <div className="positions-table-wrap desktop-positions-table"><table><thead><tr><th scope="col">Contract</th><th scope="col">Quantity</th><th scope="col">Market value</th><th scope="col">Unrealized P&amp;L</th></tr></thead><tbody>{data.positions.map((position) => <tr key={position.symbol}><th scope="row"><strong>{position.symbol}</strong></th><td>{format.integer(position.quantity)}</td><td>{usd.format(position.market_value)}</td><td className={position.unrealized_pnl >= 0 ? 'positive' : 'negative'}>{signedUsd.format(position.unrealized_pnl)}</td></tr>)}</tbody></table></div>
              <div className="mobile-position-list" aria-label="Open option positions">{data.positions.map((position) => <article className="mobile-position-card" key={position.symbol}><header><strong>{position.symbol}</strong><span>{format.integer(position.quantity)} contracts</span></header><dl><div><dt>Market value</dt><dd>{usd.format(position.market_value)}</dd></div><div><dt>Unrealized P&amp;L</dt><dd className={position.unrealized_pnl >= 0 ? 'positive' : 'negative'}>{signedUsd.format(position.unrealized_pnl)}</dd></div></dl></article>)}</div>
            </>
          ) : data && data.open_premium_risk === 0 && data.open_spread_count === 0 ? (
            <div className="no-open-risk"><ShieldCheck aria-hidden="true" /><div><strong>No open risk</strong><p>The latest Alpaca snapshot contains no open option positions or premium at risk.</p></div></div>
          ) : data ? (
            <div className="no-open-risk"><Gauge aria-hidden="true" /><div><strong>Risk record awaiting position reconciliation</strong><p>The snapshot records {usd.format(data.open_premium_risk)} of premium risk but no open contract rows. No zero-risk claim is made.</p></div></div>
          ) : (
            <div className="no-open-risk"><Gauge aria-hidden="true" /><div><strong>Positions not observed</strong><p>A verified portfolio snapshot has not been recorded yet.</p></div></div>
          )}
        </section>
        <aside className="panel risk-budget-panel"><div className="panel-heading"><div><p className="eyebrow">FIXED RISK BUDGET</p><h2>Predeclared limits</h2></div><ShieldCheck aria-hidden="true" /></div><dl><div><dt>Per position</dt><dd>{percentage.format(config.max_position_risk_pct)}</dd></div><div><dt>Total premium</dt><dd>{percentage.format(config.max_total_risk_pct)}</dd></div><div><dt>Daily loss gate</dt><dd>−{percentage.format(config.daily_loss_limit_pct)}</dd></div><div><dt>New positions / day</dt><dd>{config.max_new_positions_per_day}</dd></div><div><dt>Live trading</dt><dd>Unavailable</dd></div></dl></aside>
      </div>
    </div>
  )
}
