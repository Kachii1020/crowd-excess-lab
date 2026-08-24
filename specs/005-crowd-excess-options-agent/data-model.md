# Data Model: Crowd Excess Options Agent

All timestamps are timezone-aware UTC. Raw secrets and full news bodies are never stored.

- **AgentRun**: run ID, mode, configuration version, status, timestamps, model, source hashes,
  summary, and sanitized error.
- **SignalSnapshot**: symbol, decision timestamp, data timestamp, attention excess/z-score,
  benchmark-adjusted move, volume z-score, evidence fields, residual score, and eligibility.
- **EvidenceAssessment**: direction `[-1,1]`, materiality/confidence `[0,1]`, short rationale,
  cited headline IDs, and abstention reason.
- **TradeIntent**: contrarian direction, two unique option legs, quantity, limit debit, maximum
  loss, DTE, and deterministic client order ID.
- **RiskDecision**: ordered gate results, approval, calculated risk totals, and denial reason.
- **ExecutionReceipt**: shadow or Alpaca order ID, state, legs, submitted/fill timestamps, and
  sanitized response metadata.
- **PortfolioSnapshot**: equity, buying power, daily/total P&L, drawdown, open premium risk,
  open spread count, and synchronization time.

The Supabase migration creates append-only tables with service-role writes and anonymous SELECT
only. Update/delete privileges and policies are omitted.
