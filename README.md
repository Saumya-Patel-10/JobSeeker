# JobSeeker (v1.3)

An **AI-powered job discovery and application platform** combining a supervised local-first automation console with intelligent resume tailoring, multi-board scraping, and unified cloud workflows. Runs on your machine with local LLMs (LM Studio, Ollama) or cloud providers, automates form filling, and provides full human-in-the-loop control.

> **Status:** v1.3 — Google Chrome automation on **your own Chrome profile** (auto-selected by your signed-in Google account), guided login CLI, multi-company API discovery (Greenhouse/Lever/Ashby/Workday/SmartRecruiters), internship-tuned defaults, master resume PDF upload, and unified JobSeeker branding.

## What's new in v1.3

- **Chrome replaces Firefox.** The automation engine is now `chromium` with `channel: chrome`, launching your installed Google Chrome.
- **Use your own Chrome profile.** `profile_source: system` attaches automation to your real Chrome profile — including existing logins on LinkedIn, Indeed, and company career sites. The profile signed in with `browser.account_email` is selected automatically.
- **Guided login.** `jobassist browser-login` opens Chrome with the configured profile and prompts you to sign in once; `browser-check-login` verifies the session later.
- **Internship-oriented defaults.** Intern/co-op keywords, hourly salary expectations (25-30/hr) with correct hourly-annual salary normalization in the discovery filter, and citizenship/clearance exclusions that drop ineligible defense postings before LLM scoring.
- **Safety default restored.** `allow_auto_submit` is `false` again — every submission requires explicit approval in the Review Queue.
- **Master resume upload.** Upload your master resume PDF from the Resume Studio (`POST /profile/master-resume/upload`).
- **Dead sources removed.** Indeed/Glassdoor/L3Harris/TI stub adapters are gone from the default configuration.

## What it does

1. **Discover** jobs automatically from multiple boards (Greenhouse, Lever, LinkedIn, Raytheon, Ashby, SmartRecruiters, Workday) via the unified `SourceOrchestrator`, or ingest individual posting URLs.
2. **Score** each job against your profile + resume using a local LLM — fit score, skill overlap, seniority alignment, and more.
3. **Tailor** your master resume to the job: re-ranks skills, rewrites bullets, renders DOCX + PDF.
4. **Cover letter** generation in your voice — no clichés, no invented experience.
5. **Auto-fill** the application form (Playwright, deterministic), then **stop for human review** by default. An explicit `--auto` flag + config toggle is required to submit autonomously.
6. **Approval queue** — every prepared application lands in `awaiting_approval`; approve (and optionally submit) via the UI or CLI.
7. **Track** everything in a local SQLite database. Question/answer memory in ChromaDB.
8. **Control Center UI** — start/pause/stop the job hunt, monitor live pipeline stage, review the approval queue, manage blacklist suggestions, and watch a live browser feed — all from a Next.js dashboard at `http://localhost:3000`.

Reasoning is delegated to a local LLM. Browser interaction is deterministic Playwright code. The AI never clicks random buttons.

---

## Quickstart

### Preferred (unified runtime)

```bash
pnpm bootstrap    # install deps, Playwright Firefox, init DB
pnpm dev          # start backend + frontend together with health checks
```

or with npm:

```bash
npm run bootstrap
npm run dev
```

### Available `npm` / `pnpm` / `make` commands

| Command | Purpose |
|---------|--------|
| `bootstrap` | Install backend + frontend deps, install Playwright browsers, init DB |
| `dev` | Start backend + frontend with health checks |
| `backend` | Start only the FastAPI backend |
| `frontend` | Start only the Next.js frontend |
| `doctor` | Run runtime diagnostics |
| `install` | Install backend/frontend dependencies only |
| `lint` | Run backend (Ruff) + frontend (ESLint) checks |
| `test` | Run backend pytest + frontend TypeScript checks |
| `fmt` | Format Python files with Black |
| `type` | Run mypy type checks |
| `clean` | Remove build/cache artefacts |

### Manual bootstrap (legacy scripts)

**Windows:**
```powershell
.\scripts\bootstrap.ps1
```

**macOS / Linux:**
```bash
bash scripts/bootstrap.sh
```

**Or step-by-step:**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
# Chrome is launched via the installed Google Chrome (channel: chrome).
# Optional: install Playwright's bundled Chromium as a fallback if you ever
# remove channel: chrome from preferences.yaml.
python -m playwright install chromium
python -m app.cli.main init
```

---

## Configuration

Edit these three files (created automatically from `config/*.example` templates on first run — they are **git-ignored**):

| File | Purpose |
|------|--------|
| `config/profile.yaml` | Name, contact, work auth, salary, location preferences |
| `config/resume_master.json` | Real career data (the source of truth for tailoring) |
| `config/preferences.yaml` | LLM provider, scoring weights, browser config, auto-submit toggle |


### Start a local LLM

- **LM Studio**: Developer mode → Start server on port `1234` → load any chat model (7B+ instruct recommended).
- **Ollama**: `ollama pull llama3.1:8b-instruct`; set `provider: ollama` and `base_url: http://localhost:11434` in `preferences.yaml`.

### Verify setup

```powershell
python -m app.cli.main doctor
```

### Quick try

```powershell
# Ingest one job
python -m app.cli.main ingest-url "https://boards.greenhouse.io/example/jobs/12345"

# Score it
python -m app.cli.main analyze 1

# Generate tailored resume + cover letter
python -m app.cli.main generate-resume 1

# Open the application page in the browser and inspect (no filling)
python -m app.cli.main dry-run 1

# Fill the form and STOP for human review (default)
python -m app.cli.main apply 1

# Approve a filled application after reviewing in the browser
python -m app.cli.main review --approve 1
```

Open `http://localhost:3000` for the full Control Center UI.

## CLI reference

```powershell
python -m app.cli.main --help
# or the installed entry-points:
jobassist --help
jobseeker --help
```

| Command | Purpose |
|---------|--------|
| `init` | Create data directories + SQLite database. Idempotent. |
| `doctor` | Health checks: Python, configs, DB, LLM, Playwright. |
| `search [--limit N]` | Pull jobs from every enabled source in `job_sources.yaml`. |
| `ingest-url <url>` | Ingest a single posting. |
| `analyze <job_id>` | Score an ingested job with the LLM. |
| `generate-resume <job_id> [--no-cover-letter]` | Tailor + render DOCX/PDF. |
| `dry-run <job_id>` | Open the page, detect fields, screenshot — never fill. |
| `apply <job_id> [--mode human_review\|auto\|dry_run] [--auto]` | Fill (+ optionally submit) an application. |
| `review [--approve N] [--reject N]` | List or update applications awaiting review. |
| `list-applications [--status STATUS] [-n N]` | Show recent applications. |
| `export [--format json\|csv] [-o file]` | Dump applications for record keeping. |
| `runtime-check` | Verify automation runtime and browser session health. |
| `browser-chrome-profiles` | List your real Google Chrome profiles (display name, signed-in account, last-used). |
| `browser-chrome-activate [dir]` | Point automation at one of your own Chrome profiles; omit the argument to auto-select the profile signed in with `account_email`. |
| `browser-login` | Open Chrome with the configured profile and prompt you to sign in (Google, LinkedIn); the session persists for future runs. |
| `browser-check-login` | Verify the configured Chrome profile is still signed in to Google. |
| `browser-profiles` | List Firefox profiles (legacy, only relevant when `engine: firefox`). |
| `browser-clone <name>` | Clone a Firefox profile (legacy). |
| `browser-activate <name>` | Set the active Firefox profile (legacy). |

### Browser automation (Chrome)

Automation runs in **Google Chrome** via Playwright (`engine: chromium`, `channel: chrome`). Two profile modes:

| `profile_source` | Behaviour |
|------------------|-----------|
| `system` (default) | Uses **your own Chrome profile** with your existing logins. The profile is chosen by `chrome_profile`, else by the profile signed in with `account_email`, else Chrome's last-used profile. **Close all Chrome windows before running automation** — Chrome cannot share a running profile, and the app fails fast with a clear message if it is locked. |
| `managed` | Uses an isolated automation profile under `data/browser_profiles/`. Sign in once via `jobassist browser-login`; cookies persist across runs. |

Recommended first-run flow: `jobassist browser-chrome-profiles` to see your profiles, `jobassist browser-chrome-activate` to pick one (or rely on `account_email` auto-selection), then `jobassist browser-login` once.

## FastAPI backend

### Start

```powershell
python -m uvicorn app.api.main:app --reload
```

OpenAPI docs at `http://127.0.0.1:8000/docs`.

### Core routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/status` | Health + LLM/DB/browser reachability |
| GET/POST | `/jobs`, `/jobs/{id}` | List / ingest / detail |
| GET/PATCH | `/applications`, `/applications/{id}` | Read + status updates |
| GET | `/resumes/job/{id}`, `/resumes/{id}/download/{docx\|pdf}` | List and download |
| GET/PUT | `/profile` | Read / update validated profile |
| POST | `/profile/master-resume/upload` | Upload the master resume PDF |
| GET | `/profile/master-resume/info` | Master resume metadata |
| GET/POST | `/scoring/{job_id}`, `/scoring/{job_id}/rescore` | Fetch or recompute score |
| GET | `/jobs/{id}/workspace` | Combined job analysis workspace |
| GET/PUT | `/settings`, `/settings/{section}` | Editable config APIs |
| GET | `/automation/*` | Automation sessions / events / screenshots |
| GET | `/ai/activity`, `/ai/summary` | AI trace stream + metrics |
| GET | `/analytics/summary` | Funnel + source effectiveness analytics |
| GET | `/browser/profiles`, `/browser/health` | Firefox profile list + runtime health |
| POST/PUT | `/browser/profiles/clone`, `/browser/active` | Clone / select active Firefox profile |
| GET | `/sources` | Job source configuration |
| GET | `/blacklist/suggestions` | AI-generated blacklist suggestions |
| POST | `/blacklist/suggestions/{id}/approve\|reject` | Approve or dismiss blacklist suggestions |

### Orchestrator routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/orchestrator/status` | Full `OrchestratorStatus` (stage, queue, stats) |
| POST | `/orchestrator/start` | Start supervised hunt loop |
| POST | `/orchestrator/pause` | Pause loop |
| POST | `/orchestrator/resume` | Resume loop |
| POST | `/orchestrator/stop` | Stop loop |

### Control Center routes (UI aliases)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/control-center/job-hunt/status` | Same as orchestrator status |
| POST | `/control-center/job-hunt/start\|pause\|resume\|stop` | Hunt lifecycle |
| POST | `/control-center/search` | Discovery + ingest only |
| POST | `/control-center/ingest` | Manual URL ingest |

### Approvals & submission

| Method | Path | Description |
|--------|------|-------------|
| GET | `/approvals/pending` | Pending checkpoints |
| POST | `/approvals/{id}/approve?submit=true` | Approve + optionally submit |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| `GET /ws/events` | Live event stream — browser actions, screenshots, pipeline progress |

### SaaS API layer (`/api/v1`)

An optional SaaS-ready API layer loaded dynamically (skipped gracefully if dependencies are absent):

| Prefix | Description |
|--------|-------------|
| `/api/v1/auth` | JWT authentication (register / login / refresh) |
| `/api/v1/users` | User management |
| `/api/v1/resumes` | Per-user resume management |
| `/api/v1/jobs` | Per-user job management |
| `/api/v1/applications` | Per-user application management |
| `/api/v1/subscriptions` | Stripe subscription management |
| `/ws/v1` | Per-user WebSocket events |

## Frontend (Next.js 16 / React 19)

Starts at `http://localhost:3000`. Pages:

| Route | Description |
|-------|-------------|
| `/dashboard` | Overview — recent jobs, application funnel, quick stats |
| `/jobs` | Job board — list, filter, ingest, and score jobs |
| `/control-center` | Start / pause / stop the hunt; live pipeline stage; source health |
| `/live-browser` | Real-time browser screenshot feed + action log over WebSocket |
| `/review-queue` | Approval checkpoints — review and approve/reject before submit |
| `/resume-studio` | Tailored resume previewer + download (DOCX / PDF) |
| `/ai-console` | AI activity log, trace stream, metrics |
| `/analytics` | Funnel charts, source effectiveness, application trends |
| `/profile` | Edit profile and resume master data |
| `/settings` | Edit app preferences and LLM config |

---

## Job Sources

The `SourceOrchestrator` (`app/sources/`) dispatches discovery across all registered sources:

| Source | Status | Notes |
|--------|--------|-------|
| Greenhouse (multi-board) | ✅ Full | API-based; no browser required; 60+ companies |
| Lever (multi-board) | ✅ Full | API-based; 25+ startups |
| Ashby (multi-org) | ✅ Full | GraphQL API; modern startups |
| Workday | ✅ Full | Semi-public API; FAANG + enterprise |
| SmartRecruiters | ✅ Full | Public REST API |
| LinkedIn | ✅ Browser | Search via your Chrome profile; Easy Apply assist only — never auto-submits (ToS) |
| Raytheon | ⏸ Disabled | Real browser adapter, but most roles require US citizenship — keep the citizenship `excluded_keywords` if you enable it |
| Manual URL list | ✅ Full | Paste specific job URLs in `config/job_sources.yaml` |
| Generic fallback | ✅ Full | Handles arbitrary company pages |

Removed in v1.3: the Indeed, Glassdoor, L3Harris, and Texas Instruments stub adapters no longer ship in the default configuration.

Configure active sources in `config/job_sources.yaml`.

---

## ATS Adapters

Form-fill adapters (`app/ats/`):

| Adapter | Supported board |
|---------|-----------------|
| `GreenhouseAdapter` | boards.greenhouse.io |
| `LeverAdapter` | jobs.lever.co |
| `LinkedInAdapter` | linkedin.com/jobs (assist only) |
| `GenericAdapter` | Any company page (heuristic field detection) |

---

## Orchestrator Pipeline

The `JobApplicationOrchestrator` runs a supervised, multi-stage loop:

```
Discover → Filter → Score → Tailor → Prepare (fill) → STOP (approval) → Submit (if approved)
```

See [`ORCHESTRATOR.md`](ORCHESTRATOR.md) for the full flowchart and API reference.

---

## Background Workers (Celery — optional / SaaS mode)

For higher-throughput or multi-user deployments, Celery workers distribute tasks:

| Worker | Queue | Role |
|--------|-------|------|
| `celery_ai_worker` | `ai_queue` | Resume tailoring, cover letter, LLM calls (4 concurrent) |
| `celery_bot_worker` | `bot_queue` | Playwright browser automation (2 concurrent) |
| `celery_beat` | — | Cron scheduler — job discovery every 30 min, daily credit reset |
| Flower | — | Web monitoring dashboard at `:5555` |

Requires **Redis** (broker + result backend) — configured via `REDIS_URL` in `.env`.

---

## Docker Compose (SaaS / cloud mode)

For a fully containerised deployment with PostgreSQL, Redis, and Celery:

```bash
cp .env.example .env   # fill in secrets
docker compose up
```

Services: `db` (PostgreSQL 16), `redis` (7), `api` (FastAPI), `celery_ai_worker`, `celery_bot_worker`, `celery_beat`, `flower`.

See [`.env.example`](.env.example) for all required environment variables (database, Redis, OpenAI, AWS S3, Stripe, SMTP, CORS).

---

## Architecture

```
CLI / API → JobApplicationOrchestrator
                │
    ┌───────────┼──────────────┐
    │           │              │
SourceOrchestrator  Pipelines  ApprovalService
(app/sources/*)  (ingest/score/  (pre-submit gate)
                  tailor/apply)
                │
     ┌──────────┼──────────┐
     │          │          │
  ATS adapters  LLM     Resume engine
  (Playwright)  provider  (DOCX + PDF)
                │
          SQLite + ChromaDB
```

See [`docs/architecture.md`](docs/architecture.md) for the full component map and pipeline diagram.

## Documentation

| File | Description |
|------|-------------|
| [`ORCHESTRATOR.md`](ORCHESTRATOR.md) | Orchestrator architecture, API endpoints, migration guide |
| [`FIREFOX_SETUP.md`](FIREFOX_SETUP.md) | Legacy Firefox profile setup (only relevant when `engine: firefox`) |
| [`UserManual.MD`](UserManual.MD) | Step-by-step user operations guide |
| [`docs/setup.md`](docs/setup.md) | Installation, prerequisites, verification |
| [`docs/configuration.md`](docs/configuration.md) | Every YAML/JSON setting |
| [`docs/architecture.md`](docs/architecture.md) | Component diagram + module responsibilities |
| [`docs/development.md`](docs/development.md) | Repo layout, commands, testing |
| [`docs/troubleshooting.md`](docs/troubleshooting.md) | Common gotchas |
| [`docs/adapter_guide.md`](docs/adapter_guide.md) | Write a new ATS adapter |
| [`docs/browser-automation.md`](docs/browser-automation.md) | Playwright browser automation internals |

## Safety & non-goals

- **LinkedIn is assist-only.** The adapter fills the Easy Apply form and stops before Submit. Auto-submitting on LinkedIn violates their ToS — this is enforced in code, not just a config flag.
- **Auto-submit is opt-in twice.** Requires both `apply.allow_auto_submit: true` in `preferences.yaml` **and** the `--auto` CLI flag. Either alone falls back to human review.
- **Approval checkpoint.** Every application lands in `awaiting_approval` before any submission attempt. The UI/CLI must explicitly approve it.
- **No captcha bypass.** If an application page shows a captcha, the adapter stops and screenshots so you can complete it manually.
- **Quality follows your model.** A 3B model will write worse bullets than a 70B model. Pick the largest model your machine can run.
- **Blacklist suggestions are user-approved.** The AI may suggest adding a company to the blacklist; it only takes effect after you approve it in the Control Center.

## Tech stack

**Backend**
- Python 3.12+
- FastAPI + Uvicorn
- Pydantic v2 + Pydantic-Settings
- SQLAlchemy 2 (async) + aiosqlite
- Playwright (Google Chrome / Chromium, persistent profiles)
- Typer + Rich (CLI)
- structlog (JSON file logs + colored console)
- LM Studio (OpenAI-compatible) + Ollama
- ChromaDB + bundled MiniLM (question memory / vector search)
- python-docx + reportlab (DOCX/PDF rendering)
- httpx + tenacity (resilient HTTP)
- BeautifulSoup4 + lxml + selectolax (HTML parsing)
- Celery + Redis (optional background workers)
- pytest + pytest-asyncio + respx (testing)

**Frontend**
- Next.js 16 + React 19 + TypeScript
- Tailwind CSS v4 + shadcn/ui
- Framer Motion (animations)
- TanStack Query v5 + Zustand
- TanStack Table v8 + Recharts
- React Hook Form + Zod
- Lucide React + Sonner

## License

MIT. See `pyproject.toml`.
