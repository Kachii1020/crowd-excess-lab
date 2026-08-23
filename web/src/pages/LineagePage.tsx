import { CheckCircle2, Copy, Database, HardDrive, XCircle } from 'lucide-react'
import { useOutletContext, useSearchParams } from 'react-router-dom'
import { useLineage } from '../api/queries.ts'
import type { WorkspaceContext } from '../components/AppShell.tsx'
import { PageHeader } from '../components/PageHeader.tsx'
import { EmptyState, ErrorState, LoadingState } from '../components/States.tsx'
import { format } from '../lib/format.ts'

export function LineagePage() {
  const { runId } = useOutletContext<WorkspaceContext>()
  const lineage = useLineage(runId)
  const [params, setParams] = useSearchParams()
  const source = params.get('source') ?? ''
  const setSource = (value: string) => setParams((current) => {
    const next = new URLSearchParams(current)
    if (value) next.set('source', value)
    else next.delete('source')
    return next
  }, { replace: true })

  if (!runId) return <EmptyState title="No research run is available for audit" />
  if (lineage.isLoading) return <LoadingState label="Validating raw snapshot lineage" />
  if (lineage.error) return <ErrorState error={lineage.error} retry={() => void lineage.refetch()} />
  if (!lineage.data) return null

  const items = source ? lineage.data.items.filter((item) => item.source === source) : lineage.data.items

  return (
    <div className="page">
      <PageHeader eyebrow="DATA LINEAGE" title="Source Lineage" description="Trace every displayed measure to its provider, immutable snapshot, and content hash." />
      <section className="source-grid" aria-label="Data provider summary">
        {lineage.data.groups.map((group) => (
          <button className="source-card" data-active={source === group.source} type="button" key={group.source} onClick={() => setSource(source === group.source ? '' : group.source)}>
            <span><Database aria-hidden="true" />{group.source}</span>
            <strong>{format.integer(group.snapshot_count)}</strong>
            <small>{format.bytes(group.byte_count)} · retained {group.retained_count}/{group.snapshot_count}</small>
          </button>
        ))}
      </section>
      <section className="panel table-panel">
        <div className="table-toolbar"><p><HardDrive aria-hidden="true" /><strong>{format.integer(items.length)}</strong> snapshots</p>{source && <button className="text-button" type="button" onClick={() => setSource('')}>Clear filter</button>}</div>
        <div className="table-wrap">
          <table className="data-table lineage-table">
            <thead><tr><th>Provider</th><th>Relative path</th><th>Collected</th><th className="numeric">Size</th><th>SHA-256</th><th>Retained</th></tr></thead>
            <tbody>{items.map((item) => (
              <tr key={`${item.source}:${item.relative_path}`}>
                <td><strong>{item.source}</strong></td>
                <td><code className="path-code">{item.relative_path}</code></td>
                <td className="mono muted">{format.dateTime(item.collected_at)}</td>
                <td className="numeric">{format.bytes(item.byte_count)}</td>
                <td><button className="hash-button" type="button" onClick={() => void navigator.clipboard.writeText(item.sha256)} title={item.sha256}><code>{format.shortHash(item.sha256)}</code><Copy aria-hidden="true" /><span className="sr-only">Copy full hash</span></button></td>
                <td>{item.retained ? <span className="retained"><CheckCircle2 aria-hidden="true" />Retained</span> : <span className="missing"><XCircle aria-hidden="true" />Missing</span>}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
