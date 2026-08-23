import type { ReactNode } from 'react'

export function MetricCard({ label, value, detail, state = 'neutral', icon }: {
  label: string
  value: ReactNode
  detail: string
  state?: string
  icon?: ReactNode
}) {
  return (
    <section className="metric-card" data-state={state}>
      <div className="metric-label">{label}{icon}</div>
      <strong>{value}</strong>
      <p>{detail}</p>
    </section>
  )
}
