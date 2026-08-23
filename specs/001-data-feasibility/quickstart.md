# Quickstart: Data Feasibility Spike

## 1. Install and verify offline

```bash
uv sync --dev
uv run pytest
uv run ruff check .
uv run crowd-excess-check --report docs/DATA_FEASIBILITY_REPORT.local.md
```

The last command does not call external services unless `--live` is supplied.

## 2. Add credentials locally

```bash
cp .env.example .env
```

Populate an OpenDART key and current NAVER API HUB credentials. Do not use the legacy
NAVER Developers endpoint for a newly registered application.

## 3. Export official KRX files

Download daily price and individual-issue investor trading data from KRX Data Marketplace.
Normalize the exported headers to the templates in `examples/` without altering values,
then save the files at the paths configured in `.env`.

No missing day should be forward-filled. Keep the original exports alongside a documented
normalization step outside Git.

## 4. Prepare permitted community observations

Copy `examples/community_observations.template.csv`. Use only an official API, licensed
export, consented dataset, or documented manual observations. Hash post and author IDs and
do not add raw text unless a later protocol explicitly requires and permits it.

## 5. Run live capability checks

```bash
uv run crowd-excess-check --live --report docs/DATA_FEASIBILITY_REPORT.local.md
```

The report records status and limitations, not secret values. A missing or forbidden
endpoint must remain unavailable rather than being replaced with fabricated observations.
