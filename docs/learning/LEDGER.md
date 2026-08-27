# Learning Ledger

This ledger tracks the operator knowledge required to run the paper agent safely. Delivery tests
show system behavior; they do not prove the user's independent understanding.

| Concept | Status | Evidence | Last reviewed | Next step |
|---|---|---|---|---|
| AI evidence vs deterministic trading authority | SEEN | [Options agent checkpoint](checkpoints/2026-08-24-crowd-excess-options-agent.md) | 2026-08-24 | Explain why invalid model output must abstain instead of falling back to prose. |
| Deterministic order idempotency | SEEN | [Options agent checkpoint](checkpoints/2026-08-24-crowd-excess-options-agent.md): user correctly identified immediate retry as an unsafe trade risk; the accepted-but-unacknowledged duplicate path remains to be stated | 2026-08-24 | Explain how client-order-ID lookup prevents a second spread when the first order was accepted before the timeout. |
| Partial-fill reconciliation | SEEN | [Options agent checkpoint](checkpoints/2026-08-24-crowd-excess-options-agent.md): user recognized that order state must be confirmed, but counted executions rather than net position and selected the close instead of the live entry order | 2026-08-27 | Recalculate the net position and name the original entry order's required terminal state before closing. |
| Supabase grants, RLS, and append-only trigger | SEEN | [Options agent checkpoint](checkpoints/2026-08-24-crowd-excess-options-agent.md) | 2026-08-24 | Explain which layer blocks anonymous INSERT and which blocks service-role UPDATE. |
| Paper-only endpoint and account boundary | SEEN | [Options agent checkpoint](checkpoints/2026-08-24-crowd-excess-options-agent.md) | 2026-08-24 | Run the kickoff probe and verify the fresh account ID without exposing credentials. |
