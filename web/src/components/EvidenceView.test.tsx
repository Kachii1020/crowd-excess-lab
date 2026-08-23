import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { TEST_EVENT } from '../test/fixtures.ts'
import { EvidenceView } from './EvidenceView.tsx'

describe('event evidence', () => {
  it('renders unavailable returns as missing instead of a synthetic zero', () => {
    render(<EvidenceView event={TEST_EVENT} />)
    expect(screen.getAllByText('Missing').length).toBeGreaterThan(0)
    expect(screen.getByText('Return not computed')).toBeInTheDocument()
    expect(screen.queryByText('0%')).not.toBeInTheDocument()
  })

  it('preserves the read-only research boundary', () => {
    render(<EvidenceView event={TEST_EVENT} />)
    expect(screen.queryByRole('button', { name: /buy|sell|order/i })).not.toBeInTheDocument()
  })
})
