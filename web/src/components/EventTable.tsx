import { ArrowDown, ArrowUp, ArrowUpDown, ExternalLink } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'
import type { EventObservation } from '../api/schemas.ts'
import { format, label } from '../lib/format.ts'
import { StatusBadge } from './StatusBadge.tsx'

type SortField = 'received_date' | 'corporation_name' | 'contract_revenue_ratio' | 'attention_excess' | 'abnormal_return_h1'

function SortButton({ field, current, order, onSort, children }: {
  field: SortField
  current: string
  order: string
  onSort: (field: SortField) => void
  children: string
}) {
  const Icon = current === field ? order === 'asc' ? ArrowUp : ArrowDown : ArrowUpDown
  return (
    <button type="button" className="sort-button" onClick={() => onSort(field)}>
      {children}<Icon aria-hidden="true" />
    </button>
  )
}

function sortDirection(field: SortField, current: string, order: string) {
  return field === current ? order === 'asc' ? 'ascending' as const : 'descending' as const : 'none' as const
}

export function EventTable({ events, sort, order, onSort, selectedReceipt, onSelect }: {
  events: EventObservation[]
  sort: string
  order: string
  onSort: (field: SortField) => void
  selectedReceipt?: string
  onSelect?: (receiptNumber: string) => void
}) {
  const location = useLocation()
  return (
    <div className="table-wrap terminal-table-wrap">
      <table className="data-table event-table">
        <thead>
          <tr>
            <th aria-sort={sortDirection('received_date', sort, order)}><SortButton field="received_date" current={sort} order={order} onSort={onSort}>Date</SortButton></th>
            <th aria-sort={sortDirection('corporation_name', sort, order)}><SortButton field="corporation_name" current={sort} order={order} onSort={onSort}>Security</SortButton></th>
            <th className="numeric" aria-sort={sortDirection('contract_revenue_ratio', sort, order)}><SortButton field="contract_revenue_ratio" current={sort} order={order} onSort={onSort}>Contract / Revenue</SortButton></th>
            <th className="numeric" aria-sort={sortDirection('attention_excess', sort, order)}><SortButton field="attention_excess" current={sort} order={order} onSort={onSort}>AE Score</SortButton></th>
            <th><span className="th-label">Group</span></th>
            <th className="numeric" aria-sort={sortDirection('abnormal_return_h1', sort, order)}><SortButton field="abnormal_return_h1" current={sort} order={order} onSort={onSort}>AR +1</SortButton></th>
            <th><span className="sr-only">Evidence</span></th>
          </tr>
        </thead>
        <tbody>
          {events.map((event) => (
            <tr key={event.receipt_number} data-selected={selectedReceipt === event.receipt_number}>
              <td className="mono muted">{format.date(event.received_date)}</td>
              <td>
                <button className="company-button" type="button" onClick={() => onSelect?.(event.receipt_number)} aria-pressed={selectedReceipt === event.receipt_number}>
                  <strong>{event.corporation_name}</strong><span>{event.ticker} · {label(event.market_class)}</span>
                </button>
              </td>
              <td className="numeric"><strong>{format.percent(event.contract_revenue_ratio)}</strong></td>
              <td className="numeric">{format.ratio(event.attention_excess)}</td>
              <td><StatusBadge status={event.attention_group} /></td>
              <td className="numeric"><span className={event.abnormal_return_h1 === null ? 'muted' : ''}>{format.percent(event.abnormal_return_h1)}</span></td>
              <td><Link className="icon-link" to={`/events/${event.receipt_number}`} state={{ from: `${location.pathname}${location.search}` }} aria-label={`Open full evidence for ${event.corporation_name}`}><ExternalLink /></Link></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
