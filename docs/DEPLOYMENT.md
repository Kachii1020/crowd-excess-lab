# Git and Preview Deployment

This repository is prepared for a private GitHub repository and a Vercel preview. The deployed
application is a read-only research workbench. Data collection remains local: never configure
OpenDART, NAVER, Public Data Portal, KRX, or community-data credentials in Vercel.

## Publication boundary

Git and Vercel exclude `.env`, `data/`, tests, local environments, browser artifacts, and raw
provider responses. A deployable research run contains only:

- `selected_events.csv`
- `attention.csv`
- `outcomes.csv`
- `manifest.json`, with source hashes and collection metadata but no raw files
- `publication.json`, recording the explicit publication acknowledgement

The UI reports public source snapshots as `0/N · Metadata only`. This is deliberate: lineage is
preserved, while the underlying provider payloads remain private.

## 1. Verify the repository

From the repository root:

```bash
uv sync --locked --dev
uv run ruff check .
uv run pytest -q
pnpm --dir web install --frozen-lockfile
pnpm --dir web exec playwright install chromium
pnpm --dir web test:run
pnpm --dir web typecheck
pnpm --dir web lint
pnpm --dir web build
pnpm --dir web e2e
uv run python scripts/deploy_preflight.py --mode configuration
```

Configuration preflight can pass without credentials, local research data, a linked Vercel
project, or a public snapshot.

## 2. Review and export one public run

Do not run this step until every row in the normalized CSV files has been reviewed for public
display and licensing/privacy concerns. The current local run is intentionally not exported by
repository setup.

```bash
uv run python scripts/export_public_snapshot.py \
  --source data/processed/mini_event_study/<run-id> \
  --acknowledge-publication

uv run python scripts/deploy_preflight.py --mode release
```

The exporter refuses to run without the acknowledgement flag, excludes `raw/`, removes private
collection errors, normalizes artifact names, rejects secret-like values and local absolute paths,
and refuses synthetic test observations. It also refuses to overwrite an existing export unless
`--replace` is explicitly provided.

The export directory is ignored by default. After reviewing its diff, deliberately add exactly one
run:

```bash
git add -f deploy/research_snapshot/<run-id>
git diff --cached --stat
git diff --cached -- deploy/research_snapshot/<run-id>
```

## 3. Create the private GitHub remote

The current local Git history does not create or modify any remote repository. Authenticate, then
create a private repository when ready:

```bash
gh auth login --hostname github.com
gh auth status --hostname github.com
gh repo create crowd-excess-lab --private --source=. --remote=origin --push
```

Keep the repository private until the normalized research rows and third-party data terms have
been reviewed. GitHub Actions runs the full credential-free verification suite on pushes and pull
requests.

## 4. Create a Vercel preview

The root project builds the Vite client from `web/` and routes same-origin `/api/*` requests to the
FastAPI function in `api/index.py`. Python 3.12 and Node.js 24 are pinned by the repository.

```bash
uv run python scripts/deploy_preflight.py --mode release
vercel link
vercel deploy
```

Do not add provider credentials to the Vercel project. After the preview URL is returned, smoke
test:

- `/api/v1/health` returns `{"status":"ok","api_version":"v1"}`.
- `/api/v1/runs` lists the one reviewed run.
- `/events` renders and a direct reload of `/events?q=<ticker>` remains on the SPA route.
- The footer retains the research-only, descriptive/in-sample disclaimer.
- Data Provenance shows lineage metadata without claiming the raw snapshots are retained.

Vercel's Python runtime packages each function with a 500 MB uncompressed limit. Check the preview
build output before promotion because scientific Python dependencies contribute to that bundle.

## 5. Promote or roll back

Promote only the exact preview that passed the smoke checks:

```bash
vercel deploy --prod
```

If a release is wrong, use the Vercel dashboard to roll back to the preceding healthy deployment,
or redeploy the preceding Git commit. Keep the failing deployment available until its logs and data
bundle have been inspected.

## External references

- [Vercel FastAPI guide](https://vercel.com/docs/frameworks/backend/fastapi)
- [Vercel Python runtime](https://vercel.com/docs/functions/runtimes/python)
- [Vercel Vite routing](https://vercel.com/docs/frameworks/frontend/vite)
- [Vercel Node.js versions](https://vercel.com/docs/functions/runtimes/node-js/node-js-versions)
- [GitHub CLI repository creation](https://cli.github.com/manual/gh_repo_create)
