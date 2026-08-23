const integer = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 })
const decimal = new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 })
const date = new Intl.DateTimeFormat('en-CA', { year: 'numeric', month: '2-digit', day: '2-digit' })
const dateTime = new Intl.DateTimeFormat('en-GB', {
  year: '2-digit', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
})

export const format = {
  integer: (value: number) => integer.format(value),
  decimal: (value: number) => decimal.format(value),
  percentValue: (value: string | number) => `${decimal.format(Number(value))}%`,
  percent: (value: number | null) => value === null ? 'Missing' : `${decimal.format(value * 100)}%`,
  ratio: (value: number | null) => value === null ? 'Missing' : `${decimal.format(value)}×`,
  date: (value: string) => date.format(new Date(`${value}T00:00:00`)),
  dateTime: (value: string) => dateTime.format(new Date(value)),
  krw: (value: string) => `KRW ${integer.format(BigInt(value))}`,
  bytes: (value: number) => value < 1024 ? `${value} B` : value < 1024 ** 2
    ? `${decimal.format(value / 1024)} KB`
    : `${decimal.format(value / 1024 ** 2)} MB`,
  shortHash: (value: string) => `${value.slice(0, 8)}…${value.slice(-6)}`,
}

const labels: Record<string, string> = {
  opendart_sample: 'Disclosure Sample',
  naver_attention: 'Attention Measurement',
  fsc_stock_prices: 'Stock Prices',
  fsc_market_indices: 'Market Index',
  outcomes: 'Event Outcomes',
  complete: 'Complete',
  blocked: 'Blocked',
  incomplete: 'Incomplete',
  pending: 'Pending',
  running: 'Running',
  failed: 'Failed',
  observed: 'Observed',
  partial: 'Partial',
  missing: 'Missing',
  lower_attention: 'Lower Attention',
  neutral_attention: 'Neutral Attention',
  higher_attention: 'Higher Attention',
  Y: 'KOSPI',
  K: 'KOSDAQ',
}

export function label(value: string): string {
  return labels[value] ?? value
}
