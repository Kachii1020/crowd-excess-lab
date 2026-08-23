import { ArrowLeft } from 'lucide-react'
import { Link, useLocation, useOutletContext, useParams } from 'react-router-dom'
import { useEvent } from '../api/queries.ts'
import type { WorkspaceContext } from '../components/AppShell.tsx'
import { EvidenceView } from '../components/EvidenceView.tsx'
import { PageHeader } from '../components/PageHeader.tsx'
import { EmptyState, ErrorState, LoadingState } from '../components/States.tsx'

export function EventEvidencePage() {
  const { runId } = useOutletContext<WorkspaceContext>()
  const { receiptNumber = '' } = useParams()
  const location = useLocation()
  const event = useEvent(runId, receiptNumber)
  const from = (location.state as { from?: string } | null)?.from ?? '/events'

  if (!runId) return <EmptyState title="No research run is available" />
  if (event.isLoading) return <LoadingState label="Reconciling event evidence" />
  if (event.error) return <ErrorState error={event.error} retry={() => void event.refetch()} />
  if (!event.data) return null

  return (
    <div className="page">
      <PageHeader eyebrow="EVENT EVIDENCE" title="Observation Evidence" description="Inspect the inputs, missingness reasons, and immutable source hashes behind every displayed value." actions={<Link className="button" to={from}><ArrowLeft />Event Monitor</Link>} />
      <EvidenceView event={event.data} />
    </div>
  )
}
