import { AlertTriangle, DatabaseZap, LoaderCircle } from 'lucide-react'
import type { ReactNode } from 'react'

export function LoadingState({ label = 'Loading research data' }: { label?: string }) {
  return <div className="state-panel" role="status"><LoaderCircle className="spin" aria-hidden="true" /><p>{label}</p></div>
}

export function EmptyState({ title, children }: { title: string, children?: ReactNode }) {
  return <div className="state-panel"><DatabaseZap aria-hidden="true" /><h2>{title}</h2>{children}</div>
}

export function ErrorState({ error, retry }: { error: Error, retry?: () => void }) {
  return (
    <div className="state-panel state-panel--error" role="alert">
      <AlertTriangle aria-hidden="true" />
      <h2>Research data could not be loaded</h2>
      <p>{error.message}</p>
      {retry && <button className="button" type="button" onClick={retry}>Try again</button>}
    </div>
  )
}
