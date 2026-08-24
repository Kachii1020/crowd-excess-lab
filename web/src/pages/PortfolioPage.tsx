import { CircleDollarSign, Gauge, ShieldCheck, WalletCards } from 'lucide-react'
import { usePortfolio, useStrategy } from '../api/queries.ts'
import { MetricCard } from '../components/MetricCard.tsx'
import { PageHeader } from '../components/PageHeader.tsx'
import { ErrorState, LoadingState } from '../components/States.tsx'
import { format } from '../lib/format.ts'

const usd = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })

export function PortfolioPage() {
  const portfolio = usePortfolio()
  const strategy = useStrategy()
  if (portfolio.isLoading || strategy.isLoading) return <LoadingState label="Loading paper portfolio" />
  if (portfolio.error || strategy.error) return <ErrorState error={portfolio.error ?? strategy.error ?? new Error('Portfolio data is unavailable.')} retry={() => window.location.reload()} />
  const data = portfolio.data

  return (
    <div className="page portfolio-page">
      <PageHeader eyebrow="VERIFIED ALPACA PAPER ACCOUNT" title="Paper Portfolio" description="Every value comes from the dedicated competition account. The public interface cannot place, change, or cancel an order." />
      <section className="metric-grid portfolio-metrics">
        <MetricCard label="Equity" value={data ? usd.format(data.equity) : '—'} detail={data ? `Observed ${format.dateTime(data.observed_at)}` : 'Awaiting first account snapshot'} state={data ? 'ok' : 'neutral'} icon={<WalletCards />} />
        <MetricCard label="Daily P&L" value={data ? usd.format(data.daily_pnl) : '—'} detail="Shown honestly; no profitability claim" state={(data?.daily_pnl ?? 0) >= 0 ? 'ok' : 'blocked'} icon={<CircleDollarSign />} />
        <MetricCard label="Open Premium Risk" value={data ? usd.format(data.open_premium_risk) : '—'} detail={`Hard cap ${(strategy.data!.max_total_risk_pct * 100).toFixed(0)}% of equity`} state="warning" icon={<Gauge />} />
        <MetricCard label="Open Spreads" value={data ? `${data.open_spread_count} / ${strategy.data!.max_open_spreads}` : '—'} detail="Defined-risk debit verticals only" state="neutral" icon={<ShieldCheck />} />
        <MetricCard label="Drawdown" value={data ? `${(data.drawdown * 100).toFixed(2)}%` : '—'} detail="Measured from the $100,000 competition start" state={(data?.drawdown ?? 0) > 0.015 ? 'warning' : 'neutral'} icon={<Gauge />} />
      </section>
      <div className="portfolio-layout">
        <section className="panel positions-panel"><div className="panel-heading"><div><p className="eyebrow">OPEN POSITIONS</p><h2>Alpaca position snapshot</h2></div><span className="mono muted">READ ONLY</span></div><div className="positions-table-wrap"><table><thead><tr><th>Contract</th><th>Quantity</th><th>Market value</th><th>Unrealized P&amp;L</th></tr></thead><tbody>{data?.positions.map((position) => <tr key={position.symbol}><td><strong>{position.symbol}</strong></td><td>{position.quantity}</td><td>{usd.format(position.market_value)}</td><td className={position.unrealized_pnl >= 0 ? 'positive' : 'negative'}>{usd.format(position.unrealized_pnl)}</td></tr>)}{!data?.positions.length && <tr><td colSpan={4} className="empty-table">No open option positions.</td></tr>}</tbody></table></div></section>
        <aside className="panel risk-budget-panel"><div className="panel-heading"><div><p className="eyebrow">FIXED RISK BUDGET</p><h2>Predeclared limits</h2></div><ShieldCheck /></div><dl><div><dt>Per position</dt><dd>{(strategy.data!.max_position_risk_pct * 100).toFixed(0)}%</dd></div><div><dt>Total premium</dt><dd>{(strategy.data!.max_total_risk_pct * 100).toFixed(0)}%</dd></div><div><dt>Daily loss gate</dt><dd>−{(strategy.data!.daily_loss_limit_pct * 100).toFixed(1)}%</dd></div><div><dt>New positions / day</dt><dd>{strategy.data!.max_new_positions_per_day}</dd></div><div><dt>Live trading</dt><dd>Unavailable</dd></div></dl></aside>
      </div>
    </div>
  )
}
