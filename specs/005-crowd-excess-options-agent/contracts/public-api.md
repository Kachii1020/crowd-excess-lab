# Public API Contract

All routes are `GET` under `/api/v1`; no public mutation route exists.

- `/agent/status`: configuration state, mode, last run, scheduler state, and source readiness.
- `/agent/runs`: newest-first sanitized run summaries.
- `/agent/runs/{run_id}`: one run with signals, intent, risk decision, and receipt.
- `/agent/signals`: latest per-symbol signal snapshots.
- `/portfolio`: latest sanitized paper portfolio snapshot.
- `/strategy`: immutable public strategy/risk configuration and interpretation boundaries.

If Supabase is not configured, endpoints return successful explicit empty/unconfigured responses
rather than fixture data or a credential-bearing error.
