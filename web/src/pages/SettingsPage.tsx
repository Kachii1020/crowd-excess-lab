import { CircleHelp, ExternalLink, KeyRound, ShieldCheck } from 'lucide-react'
import { useCapabilities } from '../api/queries.ts'
import { PageHeader } from '../components/PageHeader.tsx'
import { ErrorState, LoadingState } from '../components/States.tsx'
import { StatusBadge } from '../components/StatusBadge.tsx'
import { format } from '../lib/format.ts'

export function SettingsPage() {
  const capabilities = useCapabilities()
  if (capabilities.isLoading) return <LoadingState label="Checking data-source capabilities" />
  if (capabilities.error) return <ErrorState error={capabilities.error} retry={() => void capabilities.refetch()} />

  return (
    <div className="page">
      <PageHeader eyebrow="CAPABILITIES" title="Data Connections" description="Show availability and constraints without exposing key values or credential-bearing URLs in the browser." />
      <section className="security-callout"><ShieldCheck aria-hidden="true" /><div><strong>Read-only boundary</strong><p>This screen cannot view or edit secrets and cannot trigger external collection. Environment configuration stays on the local server.</p></div></section>
      <section className="capability-grid">
        {capabilities.data?.map((capability) => (
          <article className="panel capability-card" key={capability.source}>
            <div className="panel-heading"><div className="source-title"><KeyRound aria-hidden="true" /><div><p className="eyebrow">DATA SOURCE</p><h2>{capability.source}</h2></div></div><StatusBadge status={capability.status} /></div>
            <dl>
              <div><dt>Access method</dt><dd>{capability.access_method}</dd></div>
              <div><dt>Current state</dt><dd>{capability.detail}</dd></div>
              <div><dt>Constraint</dt><dd>{capability.limitation || 'No declared constraint'}</dd></div>
              <div><dt>Checked</dt><dd>{format.dateTime(capability.checked_at)}</dd></div>
            </dl>
          </article>
        ))}
      </section>
      <section className="panel boundary-panel">
        <div className="panel-heading"><div><p className="eyebrow">RESEARCH BOUNDARY</p><h2>Deliberate Non-Goals</h2></div><CircleHelp aria-hidden="true" /></div>
        <ul className="boundary-list"><li>Automated collection from restricted stock forums</li><li>Order, broker, or position integration</li><li>Presenting in-sample results as profitability</li><li>Storing author identifiers from raw community data</li></ul>
        <a className="text-link" href="https://opendart.fss.or.kr/" target="_blank" rel="noreferrer">OpenDART official site <ExternalLink /></a>
      </section>
    </div>
  )
}
