# Crowd Excess Lab — Permanent Rules

## Research boundary

- This repository is an empirical research tool, not an investment adviser or an
  order-execution system.
- Do not add broker integration or order submission until a separately approved
  milestone demonstrates an out-of-sample signal after costs.
- Never describe a backtest, fixture, or in-sample result as a profitable strategy.

## Data integrity

- Never invent observations. Synthetic rows are allowed only inside tests and must
  be obviously labelled as synthetic.
- Preserve source, collection method, original timestamp, collection timestamp, and
  a source-file hash for every imported dataset.
- Store timestamps as timezone-aware UTC values. Keep the original source timezone
  in metadata when it is available.
- Corrections, duplicate disclosures, suspended stocks, price limits, delistings,
  and missing observations must remain visible rather than being silently dropped.
- A feature may use only information available at its declared decision timestamp.

## Community data

- Do not scrape a community when its terms prohibit automated collection.
- Naver user posts must not be automatically collected without prior permission.
- Accept community observations only from an official API, a licensed export, a
  consented dataset, or a documented manual observation workflow.
- Do not store raw user IDs. Hash identifiers before import. Avoid storing post text
  when derived labels are sufficient.

## Secrets and logging

- Secrets belong only in a local `.env`; never commit or print them.
- Capability reports may say whether a credential is configured, but must never
  contain credential values, request headers, or credential-bearing URLs.

## Modeling and validation

- The initial event family is `SINGLE_SALES_SUPPLY_CONTRACT` only.
- Separate positive euphoria, negative panic, and disagreement/volatility hypotheses.
- Use chronological walk-forward evaluation. Random train/test splits are forbidden.
- Compare every community model with a fundamentals-and-market-only baseline.
- Include transaction costs and an explicit decision timestamp before discussing
  economic usefulness.
- Keep preregistered starting weights separate from weights learned from data.

## Engineering

- Target Python 3.12 with type hints, small modules, pytest, and Ruff.
- Unit tests must run without network access or live credentials.
- A live endpoint failure is a capability result, not a reason to insert fake data.
- Update the active spec, plan, tasks, and feasibility report when an external API or
  data assumption changes.
