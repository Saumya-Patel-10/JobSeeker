# JobSeeker - User Manual

This manual explains how to install, configure, start, and operate the project end to end.
It is written for day to day use, not just development.

For architecture details, see `ORCHESTRATOR.md`.

## Quick start (3 commands)

```powershell
pnpm bootstrap
pnpm dev
# Open http://127.0.0.1:3000/control-center
```

If `pnpm` is not installed, use `npm run` instead.

Then click **Start Job Hunt** in Control Center. You do not need the CLI for normal daily use.

## 1) What this project is

JobSeeker is a **local, supervised** AI workflow for job applications.

It helps you:
- Discover jobs from configured sources (API boards, browser adapters, manual URLs).
- Score job fit against your profile and master resume.
- Generate tailored resumes (DOCX and PDF) and cover letters.
- Fill applications with Playwright (Firefox, persistent profiles).
- Stop for your approval before any submission.
- Keep a local history of applications and events in SQLite.

It runs fully on your machine.
No mandatory cloud services are required.

## 2) How the system works (one pipeline)

All entry points (Control Center, CLI, API) use the same **Job Application Orchestrator**:

1. **Discover** — unified `SourceOrchestrator` (Greenhouse, Lever, LinkedIn, Raytheon, url_list, etc.)
2. **Filter** — keywords, companies, locations, blacklist, score threshold
3. **Score** — AI fit analysis
4. **Tailor** — resume + cover letter
5. **Prepare** — Playwright fills the form (no submit yet)
6. **STOP** — pre-submit approval checkpoint
7. **Submit** — only after you approve, via `submit_application_if_approved` (if allowed)

You will see the current **stage** in Control Center (for example `discovering`, `scoring`, `preparing`, `awaiting_approval`).

## 3) Safety model (read this first)

- **Control Center is the primary control surface** — start hunts, approve applications, review blacklist suggestions.
- Every prepared application creates a **pre-submit approval checkpoint** before any submit can occur.
- Default apply mode is `human_review` (fill and stop).
- Auto submit requires **all** of:
  - Job hunt mode **Autonomous apply**
  - `apply.allow_auto_submit: true` in `config/preferences.yaml`
  - An **approved** checkpoint (and **Approve & submit** in the UI, or CLI `--submit`)
- You **cannot** mark an application `submitted` via the API `PATCH` endpoint or by bypassing approvals.
- **LinkedIn** is assist-only:
  - The adapter can fill and stop.
  - It never auto-submits (even in autonomous mode).
- **Blacklist**: the AI may only **suggest** entries. `blacklist.yaml` is updated only when you approve a suggestion in Control Center.

### Live supervision

- **Live Browser** (`/live-browser`) — current URL, task, form step, screenshots, action log, pause/resume.
- **WebSocket** `ws://127.0.0.1:8000/ws/events` — orchestrator progress, browser events, approvals (used by the UI).
- Screenshots are taken on key steps and about every 8 seconds while a Firefox session is active.

## 4) Prerequisites

- Python 3.12+
- Node.js 20+
- Local LLM runtime:
  - LM Studio (default), OR
  - Ollama
- Internet access for job sources and browser automation pages.
- Enough disk space for Playwright Firefox install.

## 5) Install and bootstrap (one time)

Recommended (cross platform):

```powershell
pnpm bootstrap
```

If `pnpm` is not installed:

```powershell
npm run bootstrap
```

Windows PowerShell script:

```powershell
.\scripts\bootstrap.ps1
```

macOS/Linux script:

```bash
bash scripts/bootstrap.sh
```

What bootstrap does:
- Creates `.venv`
- Installs backend + frontend dependencies
- Installs Playwright Firefox
- Initializes the database and data folders
- Runs runtime checks

## 6) Start the full stack (one command)

From the repo root:

```powershell
pnpm dev
```

Alternatives:

```powershell
.\run.ps1
```

```bash
./run.sh
```

```bash
make dev
```

What `dev` does:
- Starts backend (FastAPI) and frontend (Next.js) together
- Runs health checks
- Prints service URLs
- Handles graceful shutdown on Ctrl+C

URLs after startup:
- Frontend: `http://127.0.0.1:3000`
- Control Center: `http://127.0.0.1:3000/control-center`
- Live Browser: `http://127.0.0.1:3000/live-browser`
- Review Queue: `http://127.0.0.1:3000/review-queue`
- Backend: `http://127.0.0.1:8000`
- API docs: `http://127.0.0.1:8000/docs`

## 7) Control Center (recommended daily workflow)

Open: `http://127.0.0.1:3000/control-center`

### One-button supervised hunt

1. **Configure discovery** (optional but recommended):
   - Paste job URLs, and/or
   - Set keywords, companies, locations, remote preference
   - Enable **Use configured sources** to run all enabled entries in `config/job_sources.yaml`
2. **Choose a job hunt mode**:
   - **Manual review** — discover → score → tailor → fill → **stop for approval** (default)
   - **Assisted apply** — discover → score → tailor only (no browser fill)
   - **Autonomous apply** — full pipeline; may submit after approval if `allow_auto_submit` is on
   - **LinkedIn assist-only** — same as manual for LinkedIn; never auto-submit
3. **Run schedule**: “Run once” (one pass per click) or set an interval for repeated runs.
4. Click **Start Job Hunt**.
5. Watch the **stage badge**, **current job**, **job queue**, and stats (seen / ingested / scored / prepared).
6. Use **Pause** / **Resume** / **Stop** as needed.

The header shows **live** when WebSocket events are connected; otherwise the UI falls back to polling.

### Other Control Center actions

| Action | What it does |
|--------|----------------|
| **Ingest Jobs** | Ingest pasted URLs only (no score/apply) |
| **Discover & ingest** | Run unified source discovery + ingest (same sources as the hunt; no score/apply) |
| **Approval queue** | Approve, **Approve & submit**, reject, or open in browser |
| **Source health** | Status of each configured source adapter |
| **Suggested blacklist candidates** | Approve or dismiss AI suggestions (never silent YAML edits) |
| **Firefox profile** | Select system or managed profile; clone system → managed |
| **Automation settings** | Daily limit, cooldown, headless, allow auto-submit |

### Approval queue

When the orchestrator reaches **preparing**, it fills the form and creates a checkpoint. The application moves to **awaiting_approval**.

- **Approve** — marks the checkpoint approved; you complete submit manually in Firefox if needed (LinkedIn, assist-only).
- **Approve & submit** — approves and calls the single submit gateway (blocked for LinkedIn or if `allow_auto_submit` is false).
- **Reject** — skips submission for that checkpoint.
- **Open in browser** — focus the automation session for manual review.

The dedicated **Review Queue** page (`/review-queue`) shows the same pending checkpoints with more detail.

### Live Browser

Open `http://127.0.0.1:3000/live-browser` while a hunt or apply is running to see:
- Current URL and page title
- Current automation task and form step
- Latest screenshot (updates via WebSocket)
- Recent browser actions and queued actions
- Pause / resume / manual control

## 8) CLI (power users and scripting)

The CLI uses the **same orchestrator and approval rules** as the UI. Use it when you want terminal control or automation scripts.

### Unified discovery

```powershell
python -m app.cli.main search --limit 25
```

Runs `SourceOrchestrator` discovery + ingest for all enabled sources (including browser adapters when configured).

### Full pipeline per job (manual steps)

If you are not using **Start Job Hunt**, you can run steps yourself:

```powershell
python -m app.cli.main ingest-url "https://boards.greenhouse.io/example/jobs/12345"
python -m app.cli.main analyze 1
python -m app.cli.main generate-resume 1
python -m app.cli.main dry-run 1
python -m app.cli.main apply 1
```

`apply` **prepares** the application (fill + checkpoint). It does **not** submit unless you explicitly approve and use `--submit`.

### Approvals (checkpoint IDs, not application IDs)

List pending checkpoints:

```powershell
python -m app.cli.main review
```

Approve checkpoint 42:

```powershell
python -m app.cli.main review --approve 42
```

Approve and submit (only if policy allows):

```powershell
python -m app.cli.main review --approve 42 --submit
```

Reject:

```powershell
python -m app.cli.main review --reject 42
```

### List and export

```powershell
python -m app.cli.main list-applications
python -m app.cli.main export --format json
python -m app.cli.main export --format csv
```

## 9) First time configuration

Edit these files before your first hunt:

| File | Purpose |
|------|---------|
| `config/profile.yaml` | Personal info, work authorization, skills, standard answers |
| `config/resume_master.json` | Master resume content for tailoring |
| `config/preferences.yaml` | LLM, browser, apply safety, scoring weights |
| `config/job_sources.yaml` | Enabled discovery sources (Greenhouse, Lever, LinkedIn, etc.) |
| `config/blacklist.yaml` | Companies/domains/keywords to skip (edit directly or via approved suggestions) |

Important `preferences.yaml` keys:
- `apply.allow_auto_submit` — default `false`; set `true` only if you want **Approve & submit** / autonomous submit to work on non-LinkedIn boards
- `apply.daily_limit` — cap applications created per day
- `apply.require_min_score` — jobs below this composite score are skipped
- `browser.headless` — `false` is easier to debug; `true` runs Firefox without a visible window
- `browser.persistent_profile` — reuse logins via `data/browser_profiles/`

Optional:
- Copy `config/.env.example` to `.env` at project root for log level or overrides.

### Enabling job sources

In `config/job_sources.yaml`, set `enabled: true` on each source you want. Examples:
- **greenhouse** / **lever** — API boards (`board_token`, `site_id`, etc.)
- **linkedin** / **raytheon** — browser-based discovery (requires Firefox profile with login)
- **url_list** — static list of URLs under `config.urls` or pasted in Control Center

Control Center **Discover & ingest** and **Start Job Hunt** both use this same registry.

## 10) Start your local LLM

### LM Studio (default)

1. Open LM Studio.
2. Load an instruct/chat model.
3. Enable the local API server at `http://localhost:1234/v1`.
4. Keep LM Studio running while using analyze/tailor/apply AI features.

### Ollama (optional)

1. Install and start Ollama.
2. Pull a model, for example:

```powershell
ollama pull llama3.1:8b-instruct
```

3. Update `config/preferences.yaml`:
   - `llm.provider: "ollama"`
   - `llm.base_url: "http://localhost:11434"`
   - `llm.chat_model: "llama3.1:8b-instruct"` (or your model)

## 11) Health checks and diagnostics

Recommended:

```powershell
pnpm doctor
```

Other options:

```powershell
python -m app.cli.main doctor
python -m app.runtime.validator
```

Expected checks:
- Python version
- Config validation
- Database access
- LLM reachability
- Playwright browser availability

If LLM is WARN/FAIL, start LM Studio or Ollama and rerun.

## 12) Firefox session reuse (important)

The project uses persistent browser profiles in:
- `data/browser_profiles/<profile_name>/`

You can reuse existing Firefox logins in two ways:
- **System profile**: select your real Firefox profile from Control Center or Browser Settings.
- **Managed profile**: clone a system profile into `data/browser_profiles/`.

If the system profile is locked by a running Firefox instance, the app can clone it
automatically when `clone_system_profile_on_lock` is enabled.

CLI helpers:

```powershell
python -m app.cli.main browser-profiles
python -m app.cli.main browser-clone "<system-profile-name>" --target-name my-managed
python -m app.cli.main browser-activate my-managed --source managed
```

One session manager reuses the profile across discovery, apply, and Live Browser.

## 13) Full CLI command reference

| Command | Description |
|---------|-------------|
| `init` | Create data directories and initialize SQLite DB |
| `doctor` | Validate runtime and connectivity |
| `search --limit N` | Unified discovery + ingest from enabled sources |
| `ingest-url <url>` | Ingest one job posting |
| `analyze <job_id>` | Run scoring pipeline |
| `generate-resume <job_id> [--no-cover-letter]` | Tailor master resume and render outputs |
| `dry-run <job_id>` | Inspect apply page without filling/submitting |
| `apply <job_id> [--mode dry_run\|human_review\|auto] [--auto] [--submit]` | Prepare application (fill + checkpoint); `--submit` only after approve |
| `review [--approve CHECKPOINT_ID] [--reject CHECKPOINT_ID] [--submit]` | Manage approval checkpoints |
| `list-applications [--status STATUS] [--limit N]` | View applications |
| `export [--format json\|csv] [--output path]` | Export local records |
| `browser-profiles` / `browser-clone` / `browser-activate` | Firefox profile management |

Generated resumes are saved under `data/resumes/generated/job_<id>/`.

## 14) Using the API

Start API server only:

```powershell
pnpm backend
```

Open docs: `http://127.0.0.1:8000/docs`

### Orchestrator (canonical)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/orchestrator/status` | Stage, queue, stats, current job |
| POST | `/orchestrator/start` | Start supervised hunt |
| POST | `/orchestrator/pause` | Pause |
| POST | `/orchestrator/resume` | Resume |
| POST | `/orchestrator/stop` | Stop |

Control Center uses equivalent paths under `/control-center/job-hunt/*`.

### Control Center helpers

| Method | Path | Description |
|--------|------|-------------|
| POST | `/control-center/search` | Discover + ingest only |
| POST | `/control-center/ingest` | Manual URL ingest |
| GET | `/control-center/activity` | Activity feed |

### Jobs, applications, approvals

| Method | Path | Description |
|--------|------|-------------|
| GET | `/status` | API health |
| GET | `/jobs`, `GET /jobs/{id}` | Job list and detail |
| GET | `/applications`, `GET /applications/{id}` | Application list and detail |
| PATCH | `/applications/{id}` | Update status (**not** `submitted` — returns 403) |
| GET | `/approvals/pending` | Pending checkpoints |
| POST | `/approvals/{id}/approve?submit=true` | Approve (+ optional submit) |
| GET | `/blacklist/suggestions` | Pending blacklist suggestions |

### WebSocket

Connect to `ws://127.0.0.1:8000/ws/events` for live events (`orchestrator.*`, `job_hunt.*`, `browser.*`, `approval.*`).

## 15) Files and data you will interact with most

### Config files
- `config/profile.yaml`
- `config/preferences.yaml`
- `config/job_sources.yaml`
- `config/prompts.yaml`
- `config/resume_master.json`
- `config/blacklist.yaml`

### Runtime data directories
- `data/jobs/`
- `data/applications/`
- `data/resumes/generated/`
- `data/logs/`
- `data/cache/`
- `data/browser_profiles/`
- `data/screenshots/`
- `data/jobassist.db`

## 16) Troubleshooting quick guide

### LLM not reachable
- Ensure LM Studio API server is running (`localhost:1234/v1`) or Ollama is up.
- Recheck `config/preferences.yaml` provider/base URL/model.

### Playwright missing browser

```powershell
python -m playwright install firefox
```

### Config validation errors
- Run `doctor` and read exact schema mismatch.
- Fix the reported key/type in YAML or JSON.

### No results from search or job hunt
- Ensure at least one source has `enabled: true` in `job_sources.yaml`.
- Verify source-specific values (`board_token`, `site_id`, etc.).
- For LinkedIn/Raytheon, confirm Firefox profile has an active login.
- In Control Center, enable **Use configured sources** or paste URLs.

### Hunt stuck on awaiting_approval
- Expected in manual modes. Open **Approval queue** or Review Queue and approve.
- Use **Approve & submit** only when auto-submit is intentionally enabled.

### Submit blocked after approve
- LinkedIn always requires manual submit in Firefox.
- Check `apply.allow_auto_submit` in `preferences.yaml`.
- Check application is not marked assist-only in checkpoint payload.

### Apply failed on dynamic pages
- Use `dry-run` first and inspect screenshots in `data/screenshots/`.
- Open **Live Browser** during the run.
- Retry with `browser.headless: false` in `preferences.yaml`.

### Playwright `NotImplementedError` on Windows (Python 3.12+)
- Caused by `uvicorn --reload` using an event loop without asyncio subprocess support.
- `pnpm dev` **disables backend hot reload on Windows** so Playwright works.
- Restart with `pnpm dev` after pulling updates. Verify with:
  `python scripts/check_playwright_async.py`
- On Windows, restart the backend manually after code changes (no auto-reload).

## 17) Updating dependencies and running checks

```powershell
pnpm install
pnpm lint
pnpm test
```

Backend only checks:

```powershell
python -m pip install -e ".[dev]"
python -m black app tests
python -m ruff check app tests
python -m mypy app
python -m pytest
```

## 18) FAQ

### Do I need the CLI?
No. For normal use, open Control Center and click **Start Job Hunt**.

### Does this submit automatically everywhere?
No. Default is human review with an approval checkpoint. LinkedIn never auto-submits.

### Can I mark an application submitted in the API?
No. `PATCH` with status `submitted` is rejected. Use approve + submit flow.

### Can I use it without any cloud account?
Yes. LM Studio/Ollama are local.

### Where are my application records stored?
In local SQLite at `data/jobassist.db` plus artifacts under `data/`.

### What is the difference between Discover & ingest and Start Job Hunt?
- **Discover & ingest** — finds and stores jobs only.
- **Start Job Hunt** — full pipeline through score, tailor, prepare, and approval.

### Can I add a new ATS adapter?
Yes. Follow `docs/adapter_guide.md`.

## 19) Related docs

- `README.md`
- `ORCHESTRATOR.md` — architecture, API map, migration notes
- `docs/setup.md`
- `docs/configuration.md`
- `docs/architecture.md`
- `docs/development.md`
- `docs/troubleshooting.md`
- `docs/adapter_guide.md`
