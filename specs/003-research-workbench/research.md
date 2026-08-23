# Research: Crowd Excess Research Workbench

## Visual references

Seven DESIGN.md candidates from Refero Styles, Free DESIGN.md, and the MIT-licensed Awesome
DESIGN.md collection were rendered through the same sample screen. Three product-specific concept
images were then generated and retained outside app source.

Recommendation: Concept B, Signal Dark. It most directly satisfies the terminal request while
using one functional accent and keeping missing outcomes prominent. Concept A is the strongest
low-fatigue alternative; Concept C is denser but risks implying execution functionality.

## Frontend stack

- Vite supports a React/TypeScript template and fast local iteration without adding server-rendering
  complexity that a single-user research tool does not need.
- TanStack Query v5 provides an explicit cache/loading/error layer for promise-based GET endpoints.
- A semantic HTML table is sufficient for 40–50 events; virtualization is deferred until measured.
- Playwright CLI is installed for token-efficient interactive QA; Playwright Test remains the
  repeatable CI-grade browser check.

## Backend stack

FastAPI fits the existing Pydantic models, produces an inspectable OpenAPI contract, and keeps the
HTTP adapter small. The repository layer is deliberately independent so the current file store can
later be replaced by SQLite/Postgres/DuckDB without altering the API or frontend.

## Storage decision

Do not migrate the current pilot into a database yet. The run directories are immutable, hashed,
and already auditable. A database is justified only when cross-run queries, larger event families,
scheduled ingestion, or multiple users become real requirements.
