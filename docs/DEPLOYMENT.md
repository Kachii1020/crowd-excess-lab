# Public Deployment and Rollback

Vercel hosts the English read-only agent dashboard and FastAPI projection. GitHub Actions owns
NAVER, OpenAI, Alpaca, and Supabase write credentials. The browser and Vercel function never receive
an order credential or service-role key.

## Publication boundary

Allowed Vercel environment variables:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `ALPACA_COMPETITION_ACCOUNT_ID` (optional public identifier)

Forbidden in Vercel: `OPENAI_API_KEY`, NAVER secrets, Alpaca key/secret, and
`SUPABASE_SERVICE_ROLE_KEY`. Public endpoints are GET-only:

- `/api/v1/agent/status`
- `/api/v1/agent/runs`
- `/api/v1/agent/runs/<run-id>`
- `/api/v1/agent/signals`
- `/api/v1/portfolio`
- `/api/v1/strategy`

Existing Korean research is an explicitly disclosed pre-hackathon artifact. A deployable research
snapshot contains only reviewed normalized CSV/manifest files; `raw/`, credentials, local paths,
and synthetic fixtures are excluded.

## 1. Verify before any public push

```bash
uv sync --locked --dev --no-editable
uv run --no-sync ruff check .
uv run --no-sync pytest -q
pnpm --dir web install --frozen-lockfile
pnpm --dir web test:run
pnpm --dir web typecheck
pnpm --dir web lint
pnpm --dir web build
PLAYWRIGHT_HTML_OPEN=never pnpm --dir web e2e
uv run --no-sync python scripts/security_preflight.py
uv run --no-sync python scripts/deploy_preflight.py --mode configuration
```

The secret-history scan is a hard public-repository gate. Review the Git diff, generated bundle,
dependency licences, and `PRE_HACKATHON_BASELINE.md`. Do not publish until provider data terms and
the retained research snapshot have been reviewed.

## 2. Optional reviewed Korean research snapshot

```bash
uv run --no-sync python scripts/export_public_snapshot.py \
  --source data/processed/mini_event_study/<run-id> \
  --acknowledge-publication
uv run --no-sync python scripts/deploy_preflight.py --mode release
git add -f deploy/research_snapshot/<run-id>
git diff --cached -- deploy/research_snapshot/<run-id>
```

The exporter rejects raw payloads, secret-like values, absolute local paths, and synthetic test
observations. If no research snapshot is published, configuration preflight may still pass and the
agent UI reports its honest empty state.

## 3. GitHub and agent credentials

Create or connect the GitHub repository only after the security gate passes. Configure the
`alpaca-paper` environment and secrets described in `docs/AGENT_OPERATIONS.md`. Keep the GitHub
variable `AGENT_MODE=shadow` until the paper-promotion checklist passes.

The scheduled workflow is competition-date bounded, checks Alpaca's market clock, and has no live
mode. A manual workflow dispatch is the safest first run.

## 4. Vercel preview

The project pins Node 24 and pnpm 11.19.0. Vite routes `/api/*` to the FastAPI function and all
other direct paths to the SPA.

```bash
vercel link
vercel deploy
```

Configure only the allowed public environment variables. In a logged-out browser, verify:

- `/api/v1/health` returns the v1 health response.
- `/api/v1/agent/status` returns a connected or explicit unconfigured state.
- `/agent`, `/portfolio`, `/strategy`, `/research`, and `/lineage` load directly and on refresh.
- A recorded `/agent/runs/<run-id>` shows evidence, risk gates, and a shadow/paper label.
- There is no scan/order button and POST requests to agent/order paths fail.
- The footer says paper-only and makes no profitability claim.
- Browser source and network payloads contain no write credential.

## 5. Production and rollback

Promote only the exact preview that passed logged-out smoke checks:

```bash
vercel deploy --prod
```

If the release is wrong, roll back to the prior healthy Vercel deployment or redeploy the prior Git
commit. Preserve the failing deployment logs for diagnosis. If Supabase public reads fail, the API
returns a safe `503`; do not add service credentials to restore the public app. Correct database
permissions with a forward migration.

## External references

- [Vercel FastAPI guide](https://vercel.com/docs/frameworks/backend/fastapi)
- [Alpaca CLI](https://docs.alpaca.markets/us/docs/alpacas-cli)
- [Alpaca options trading](https://docs.alpaca.markets/us/docs/options-trading)
- [OpenAI Responses API](https://developers.openai.com/api/reference/resources/responses/methods/create)
