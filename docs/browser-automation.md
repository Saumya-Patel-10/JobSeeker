# Browser automation (supervised)

The assistant uses **Playwright Firefox** with **persistent profiles** for session reuse.

## Architecture

- `AutomationRuntime` — pause/stop, manual control, telemetry
- `BrowserSessionManager` — long-lived sessions (not per-job teardown)
- `EventBus` → WebSocket `/ws/events` for live UI

## Human override

From **Live Browser** or API:

- `POST /automation/runtime/pause` — pause AI
- `POST /automation/runtime/manual-control` — take manual control (session preserved)
- `POST /automation/runtime/return-to-ai` — resume automation

## Screenshots

During automation, screenshots are written to `data/screenshots/` and exposed at:

`GET /automation/runtime/screenshots/{filename}`

## Approval safety

No `adapter.submit()` runs without an approved `pre_submit` checkpoint (except LinkedIn assist-only, which never auto-submits).
