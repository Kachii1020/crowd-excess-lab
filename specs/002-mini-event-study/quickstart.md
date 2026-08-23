# Quickstart: Mini Event Study

## Credentials

Keep all values in the ignored `.env`:

```text
OPENDART_API_KEY=...
NAVER_API_HUB_CLIENT_ID=...
NAVER_API_HUB_CLIENT_SECRET=...
DATA_GO_KR_API_KEY=...
```

Enable both official Public Data Portal services for a benchmark-adjusted run:

- [금융위원회_주식시세정보](https://www.data.go.kr/data/15094808/openapi.do)
- [금융위원회_지수시세정보](https://www.data.go.kr/data/15094807/openapi.do)

The same decoded or URL-encoded key is accepted. Never paste it into a report or chat.

## Offline verification

```bash
uv run pytest
uv run ruff check .
```

## Live pilot

```bash
uv run crowd-excess-study --target 40
```

The command creates a timestamped ignored directory under
`data/processed/mini_event_study/`. If the Public Data Portal key is missing, the run still
persists the audited OpenDART cohort and NAVER stage, then marks price outcomes blocked.

Use the reported run directory to resume instead of spending API quota again:

```bash
uv run crowd-excess-study --resume data/processed/mini_event_study/<run-id>
```

If a prior run wrote empty price files while the key was missing, resume detects the blocked
manifest state and retries those two stages after the key is configured.
