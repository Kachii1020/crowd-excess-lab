import type { ReactNode } from 'react'
import { label } from '../lib/format.ts'

export function StatusBadge({ status, children }: { status: string, children?: ReactNode }) {
  return <span className="status-badge" data-status={status}>{children ?? label(status)}</span>
}
