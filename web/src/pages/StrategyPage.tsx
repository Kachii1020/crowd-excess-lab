import { Bot, Braces, CheckCircle2, Database, ShieldCheck, Split } from 'lucide-react'
import { useStrategy } from '../api/queries.ts'
import { ErrorState, LoadingState } from '../components/States.tsx'
import { PageHeader } from '../components/PageHeader.tsx'

export function StrategyPage() {
  const strategy = useStrategy()
  if (strategy.isLoading) return <LoadingState label="Loading declared strategy" />
  if (strategy.error || !strategy.data) return <ErrorState error={strategy.error ?? new Error('Strategy configuration is unavailable.')} retry={() => void strategy.refetch()} />
  const config = strategy.data
  return (
    <div className="page strategy-page">
      <PageHeader eyebrow="DECLARED BEFORE PAPER EXECUTION" title="Strategy & Risk" description="A transparent, falsifiable hypothesis: when attention and price outrun objective news evidence, a controlled contrarian option spread may capture mean reversion." />
      <section className="strategy-formula"><span>signed market-adjusted move</span><b>×</b><span>attention heat</span><b>−</b><span>news direction × materiality</span><b>=</b><strong>Crowd Excess</strong></section>
      <div className="strategy-grid">
        <details className="panel strategy-section" open>
          <summary className="panel-heading"><div><p className="eyebrow">SIGNAL</p><h2>What the agent measures</h2></div><Braces aria-hidden="true" /></summary>
          <ol><li><span>01</span><div><strong>Cross-border search attention</strong><p>NAVER daily relative search ratios. Recent t−2 to t−1 versus median t−14 to t−3, then a robust trailing 60-day z-score.</p></div></li><li><span>02</span><div><strong>Market-adjusted movement</strong><p>Underlying intraday return minus SPY, normalized by twenty-day volatility, with volume dislocation.</p></div></li><li><span>03</span><div><strong>Objective news evidence</strong><p>OpenAI structured output scores direction, materiality, and confidence from normalized Alpaca headlines.</p></div></li></ol>
        </details>
        <details className="panel strategy-section" open>
          <summary className="panel-heading"><div><p className="eyebrow">OPTIONS</p><h2>How the view is expressed</h2></div><Split aria-hidden="true" /></summary>
          <ul className="declared-list"><li><CheckCircle2 aria-hidden="true" /><span><strong>Bullish reversal</strong>Call debit spread</span></li><li><CheckCircle2 aria-hidden="true" /><span><strong>Bearish reversal</strong>Put debit spread</span></li><li><CheckCircle2 aria-hidden="true" /><span><strong>Expiry</strong>{config.min_dte}–{config.max_dte} DTE</span></li><li><CheckCircle2 aria-hidden="true" /><span><strong>Long delta</strong>0.45–0.60 absolute</span></li><li><CheckCircle2 aria-hidden="true" /><span><strong>Short delta</strong>0.20–0.35 absolute</span></li><li><CheckCircle2 aria-hidden="true" /><span><strong>Liquidity</strong>OI ≥ {config.min_open_interest}; quote width ≤ {(config.max_quote_width_pct * 100).toFixed(0)}%</span></li></ul>
        </details>
        <details className="panel strategy-section" open>
          <summary className="panel-heading"><div><p className="eyebrow">AUTHORITY</p><h2>AI and deterministic controls</h2></div><Bot aria-hidden="true" /></summary>
          <div className="authority-split"><div><strong>OpenAI may</strong><p>Assess whether supplied headlines justify the move and cite only supplied headline IDs.</p></div><div><strong>OpenAI may not</strong><p>Select contracts, choose quantity, submit an order, override a gate, or generate free-form execution commands.</p></div><div><strong>Risk engine owns</strong><p>Contract structure, liquidity, sizing, account identity, endpoint verification, daily limits, and idempotency.</p></div></div>
        </details>
        <details className="panel strategy-section" open>
          <summary className="panel-heading"><div><p className="eyebrow">BOUNDARIES</p><h2>Structural prohibitions</h2></div><ShieldCheck aria-hidden="true" /></summary>
          <ul className="boundary-checks"><li>Live Alpaca endpoint does not exist in configuration.</li><li>Naked option legs are rejected by the domain model.</li><li>Public API exposes GET endpoints only.</li><li>Missing OpenAI, Greeks, quotes, volume, or storage means ABSTAIN.</li><li>Duplicate scans reuse one deterministic client order ID.</li><li>Paper account must match the dedicated competition ID.</li></ul>
        </details>
      </div>
      <section className="lineage-explainer"><Database /><div><p className="eyebrow">PROVENANCE</p><h2>Research origin remains visible</h2><p>The Korean OpenDART/KRX prototype is retained as pre-hackathon research lineage. It is not represented as US execution data or work created during the competition.</p></div><span>CONFIG {config.version}</span></section>
    </div>
  )
}
