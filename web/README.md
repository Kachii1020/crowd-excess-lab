# Crowd Excess Research Workbench

Read-only React client for the local Crowd Excess research API.

```bash
# terminal 1, from the repository root
uv run crowd-excess-api

# terminal 2
cd web
pnpm dev
```

The client reads `/api/v1`; Vite proxies that path to `127.0.0.1:8000`. It never reads CSV files,
credentials, or absolute local paths directly. Test fixtures under `src/test/` are explicitly
synthetic and are never bundled as research results.

The selected system combines a dense three-pane research-terminal layout with a light
institutional palette. Product copy is English. Theme values remain semantic variables in
`src/index.css`; feature components do not contain theme colors.
