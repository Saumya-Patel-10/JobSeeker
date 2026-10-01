# JobSeeker (v1.1)

An **AI-powered job discovery and application platform** combining a supervised local-first automation console with intelligent resume tailoring, multi-board scraping, and unified cloud workflows. Runs on your machine with local LLMs (LM Studio, Ollama) or cloud providers, automates form filling, and provides full human-in-the-loop control.

> **Status:** v1.1 — Integrated Command Center dashboard, multi-source ingestion (Greenhouse, Lever, LinkedIn, Indeed), deterministic Playwright automation, tailored resume/cover letter generation, and unified API runtime.

## What it does

1. **Ingest** a job posting from a URL (Greenhouse, Lever, LinkedIn, or any
   company page via the generic fallback).
2. **Score** the job against your profile + resume using a local LLM,
   producing a fit score, skill overlap, seniority alignment, and more.
3. **Tailor** your master resume to the job: re-ranks skills, rewrites
   bullets, renders DOCX + PDF.
4. **Cover letter** generation in your voice — no clichés, no invented
   experience.
5. **Auto-fill** the application form (Playwright, deterministic), then stop
   for human review by default. Opt-in `--auto` requires an explicit
   config flag.
6. **Track** everything in a local SQLite database. Question/answer memory
   in ChromaDB.

Reasoning is delegated to a local LLM. Browser interaction is deterministic
Playwright code. The AI never clicks random buttons.

## Quickstart

### Preferred (unified runtime)

```bash
pnpm bootstrap
pnpm dev
```

or:

```bash
npm run bootstrap
npm run dev
```

This starts backend + frontend together and performs health checks.

### Manual bootstrap scripts (legacy)

### 1. Bootstrap

Windows:

```powershell
.\scripts\bootstrap.ps1
```

macOS / Linux:

```bash
bash scripts/bootstrap.sh
```

Or manually:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m playwright install firefox
python -m app.cli.main init
```

### 2. Edit your data

- `config/profile.yaml` — your name, contact, work auth, salary, etc.
- `config/resume_master.json` — your real career data.
- `config/preferences.yaml` — LLM provider, scoring weights, browser config.

### 3. Start a local LLM

- LM Studio: Developer mode → Start server on port 1234 → load any chat
  model (7B+ instruct works well).
- OR Ollama: `ollama pull llama3.1:8b-instruct`; set `provider: ollama` and
  `base_url: http://localhost:11434` in `preferences.yaml`.

### 4. Verify

```powershell
python -m app.cli.main doctor
```

### 5. Try it

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

### 6. Launch the operations console (frontend)

```powershell
cd frontend
copy .env.local.example .env.local
npm install
npm run dev
```

Open `http://localhost:3000`.

## CLI reference

| Command | Purpose |
| --- | --- |
| `init` | Create data directories + SQLite database. Idempotent. |
| `doctor` | Run health checks: Python, configs, DB, LLM, Playwright. |
| `search [--limit N]` | Pull jobs from every enabled source in `job_sources.yaml`. |
| `ingest-url <url>` | Ingest a single posting. |
| `analyze <job_id>` | Score an ingested job with the LLM. |
| `generate-resume <job_id> [--no-cover-letter]` | Tailor + render DOCX/PDF. |
| `dry-run <job_id>` | Open the page, detect fields, screenshot — never fill. |
| `apply <job_id> [--mode human_review\|auto\|dry_run] [--auto]` | Fill (+ optionally submit) an application. |
| `review [--approve N] [--reject N]` | List or update applications awaiting review. |
| `list-applications [--status STATUS] [-n N]` | Show recent applications. |
| `export [--format json\|csv] [-o file]` | Dump applications for record keeping. |

## FastAPI inspection layer

```powershell
python -m uvicorn app.api.main:app --reload
```

OpenAPI docs at `http://127.0.0.1:8000/docs`. Routes:

- `GET /status` — health + provider reachability.
- `GET /jobs`, `GET /jobs/{id}` — list/detail.
- `GET /applications`, `GET /applications/{id}`, `PATCH /applications/{id}` — read + status updates.
- `GET /resumes/job/{id}`, `GET /resumes/{id}/download/{docx|pdf}` — list and download.
- `GET /profile`, `PUT /profile` — read/update validated profile.
- `GET /scoring/{job_id}`, `POST /scoring/{job_id}/rescore` — fetch or recompute.
- `GET /jobs/{id}/workspace` — combined job analysis workspace.
- `GET /settings`, `PUT /settings/{section}` — editable config APIs.
- `GET /automation/*` — automation sessions/events/screenshots.
- `GET /ai/activity`, `GET /ai/summary` — AI trace stream + metrics.
- `GET /analytics/summary` — funnel + source effectiveness analytics.
- `GET /browser/profiles`, `GET /browser/health` — Firefox profile management and runtime session health.
- `POST /browser/profiles/clone`, `PUT /browser/active` — clone/select active Firefox profiles.

## Architecture

See [`docs/architecture.md`](docs/architecture.md) for the full component
map and pipeline flow. Short version:

```
CLI / API → Pipelines → (ATS adapters | LLM provider | resume engine | DB)
                            │
                  Playwright (deterministic actions, persistent profile)
                            │
              LM Studio / Ollama (reasoning only, structured JSON)
```

## Documentation

- [`FIREFOX_SETUP.md`](FIREFOX_SETUP.md) - Firefox profile/session reuse setup.
- [`UserManual.MD`](UserManual.MD) - step by step user operations guide.
- [`docs/setup.md`](docs/setup.md) — installation, prerequisites, verification.
- [`docs/configuration.md`](docs/configuration.md) — every YAML/JSON setting.
- [`docs/architecture.md`](docs/architecture.md) — component diagram + module responsibilities.
- [`docs/development.md`](docs/development.md) — layout, commands, testing.
- [`docs/troubleshooting.md`](docs/troubleshooting.md) — common gotchas.
- [`docs/adapter_guide.md`](docs/adapter_guide.md) — write a new ATS adapter.

## Safety / non-goals

- **LinkedIn is assist-only.** The adapter fills the Easy Apply form and
  stops before Submit. Auto-submitting on LinkedIn violates their ToS.
  This is enforced in code, not just a setting.
- **Auto-submit is opt-in twice.** It requires both
  `apply.allow_auto_submit: true` in `preferences.yaml` AND the `--auto`
  flag on the CLI invocation. Either alone falls back to human review.
- **No captcha bypass.** If an application page presents a captcha, the
  adapter stops and screenshots so you can complete it manually.
- **Quality follows your model.** A 3B model will write worse bullets than
  a 70B model. Pick the largest model your machine can run.

## Tech stack

- Python 3.12+
- FastAPI + Uvicorn
- Pydantic 2 + Pydantic-Settings
- SQLAlchemy 2 (async) + aiosqlite
- Playwright
- Typer + Rich
- structlog (JSON file logs + colored console)
- LM Studio (OpenAI-compatible) + Ollama
- ChromaDB (with bundled MiniLM)
- python-docx + reportlab
- httpx + tenacity
- pytest + pytest-asyncio + respx

## License

MIT. See `pyproject.toml`.
