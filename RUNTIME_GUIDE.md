# Runtime Guide

## Unified commands

From repository root:

- `pnpm bootstrap` - full first-time setup
- `pnpm dev` - run backend + frontend with health checks
- `pnpm doctor` - runtime diagnostics
- `pnpm backend` - backend only
- `pnpm frontend` - frontend only
- `pnpm lint` - lint checks
- `pnpm test` - tests and type checks

PowerShell/Bash wrappers are also available:

- `./run.ps1` (Windows)
- `./run.sh` (macOS/Linux)

## Startup flow (`pnpm dev`)

1. Verifies dependency state.
2. Ensures Playwright Firefox runtime exists.
3. Initializes local DB/data directories.
4. Starts backend and frontend concurrently.
5. Polls health endpoints and prints service URLs.
6. Handles graceful shutdown on Ctrl+C.

## Health endpoints

- Backend coarse health: `GET /status`
- Browser session health: `GET /browser/health`
- Automation activity: `GET /automation/overview`
- AI activity summary: `GET /ai/summary`

## Runtime validation

Use:

```bash
python -m app.runtime.validator
```

or:

```bash
python -m app.runtime.validator --json
```

## Troubleshooting

- If backend fails at startup, run `pnpm doctor`.
- If browser sessions are not reused, verify active profile at `/settings/browser`.
- If LLM is offline, start LM Studio/Ollama and re-run `pnpm doctor`.
