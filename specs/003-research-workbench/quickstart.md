# Quickstart: Research Workbench

## Backend

```bash
uv sync --dev
uv run crowd-excess-api
```

The API reads runs below `STUDY_OUTPUT_ROOT` and never exposes `.env` values.

## Frontend

```bash
cd web
pnpm install
pnpm dev
```

The Vite development server proxies `/api` to the local Python API.

## Verification

```bash
uv run pytest
uv run ruff check .
cd web
pnpm test
pnpm typecheck
pnpm lint
pnpm build
pnpm e2e
```

The final visual pass also runs the installed Vercel Web Interface Guidelines review and uses
Playwright CLI to inspect keyboard behavior, console errors, and desktop/tablet/mobile renders.
