# Job Finding Assistant — Status Report

**Audit date:** 2026-05-27  
**Method:** Codebase review of backend (`app/`), frontend (`frontend/src/`), config (`config/`), CLI (`app/cli/`), and tests (`tests/`).  
**Scope:** What is implemented and callable today—not roadmap intent.

---

## 1. Project overview

### What the system actually does today

This is a **local-first job application assistant** that:

1. **Ingests** job postings from URLs (and from some configured “sources”).
2. **Scores** jobs against your profile/resume using a **local LLM** (LM Studio or Ollama).
3. **Generates** tailored resumes (DOCX/PDF) and optional cover letters via LLM.
4. **Fills** application forms in **Firefox via Playwright**, with ATS-specific adapters where implemented.
5. **Blocks automated submission** behind approval checkpoints in the apply pipeline (with documented bypasses—see §7).
6. Exposes a **Next.js operations UI** and a **FastAPI REST/WebSocket API** for monitoring and control.

It does **not** yet provide a single polished, end-to-end “press one button and safely apply to jobs on LinkedIn/Indeed/etc.” experience without manual setup, enabled sources, LLM, and Firefox login.

### Entry points

| Entry | How to run | Role |
|--------|------------|------|
| **CLI** | `python -m app.cli.main <command>` (also `jobassist` if installed) | Primary historical workflow: ingest → analyze → generate-resume → apply |
| **API** | `uvicorn app.api.main:app` (typical dev: `pnpm dev` starts API + UI) | REST + WebSocket; used by the UI |
| **UI** | Next.js at `http://127.0.0.1:3000` | Control Center, jobs, review, live browser, settings |

**Config:** YAML/JSON under `config/` (`profile.yaml`, `preferences.yaml`, `job_sources.yaml`, `blacklist.yaml`, `prompts.yaml`, `resume_master.json`) plus SQLite at `data/jobassist.db`.

---

## 2. Working features (confirmed implemented)

Features below have real pipeline/service code and are invocable without mock data in the UI.

### Job ingest (single URL)

- **What:** Detects ATS from URL, scrapes job, applies **blacklist at ingest**, upserts to SQLite.
- **Trigger:** CLI `ingest-url <url>`; API `POST /control-center/ingest`; job hunt loop; source poll (orchestrator).
- **Inputs:** Public job URL; browser profile for LinkedIn/generic scrape.
- **Outputs:** `Job` row in DB; logs; may create **blacklist suggestion** row (does not auto-edit YAML).

### Job ingest — Greenhouse / Lever (HTTP APIs)

- **What:** `GreenhouseAdapter` / `LeverAdapter` scrape via public board APIs (no browser for scrape).
- **Trigger:** Ingest URL or enabled `greenhouse_board` / `lever_board` in `job_sources.yaml` via search/hunt/CLI `search`.
- **Inputs:** Valid `board_token` / `site_id` in config; optional keyword/department filters.
- **Outputs:** Job URLs → ingest → DB.

### Job scoring (fit analysis)

- **What:** `score_pipeline` calls LLM with `job_match` prompt; persists `job_scores` with rationale, skills, composite.
- **Trigger:** CLI `analyze <job_id>`; API `POST /scoring/{id}/rescore`; **JobHuntManager** auto-scores during hunt.
- **Inputs:** Ingested job; `config/profile.yaml`, `resume_master.json`, LLM running.
- **Outputs:** Score row; visible in UI Jobs/Scoring.

### Resume tailoring + rendering

- **What:** LLM tailors resume JSON; renders DOCX/PDF; optional cover letter; stores `resume_versions`.
- **Trigger:** CLI `generate-resume <job_id>`; hunt loop when modes include tailor.
- **Inputs:** Scored job; master resume; LLM.
- **Outputs:** Files under generated resumes path; DB row.

### Apply — fill forms (human review default)

- **What:** Opens Firefox (persistent profile via `AutomationRuntime` → `BrowserSessionManager`), runs ATS adapter `fill_application`, screenshots, sets application `awaiting_review`, creates **`approval_checkpoints` row**.
- **Trigger:** CLI `apply <job_id>`; hunt in `manual_review` / `linkedin_assist` / `autonomous_apply`; API indirectly via hunt.
- **Inputs:** Job with tailored resume; browser config; LLM for generic adapter.
- **Outputs:** `Application` row, fill report, screenshots on disk, pending approval checkpoint.

### Apply — dry run

- **What:** Inspects form fields without full submit flow.
- **Trigger:** CLI `dry-run <job_id>`.
- **Outputs:** `DryRunReport`, application events.

### Apply — auto submit (restricted)

- **What:** After fill, can call `adapter.submit()` **only if** `allow_auto_submit` + `allow_auto` + approval wait succeeds + not LinkedIn.
- **Trigger:** CLI `apply --auto` with `preferences.apply.allow_auto_submit: true`; hunt `autonomous_apply` mode.
- **Outputs:** `SubmitReport`; status `submitted` if adapter succeeds.
- **Note:** Default config has `allow_auto_submit: false`.

### Job hunt orchestration (in-process)

- **What:** `JobHuntManager` async loop: discover URLs (via `SourceOrchestrator.discover_all` when `run_search`), ingest, filter, score, tailor, optionally apply; pause/resume/stop; emits `job_hunt.*` events.
- **Trigger:** API `POST /control-center/job-hunt/start` (+ pause/resume/stop); Control Center “Start AI Job Hunt”.
- **Inputs:** `JobHuntStartRequest` (mode, discovery, interval).
- **Outputs:** `JobHuntStatus` stats; DB side effects.

### Blacklist enforcement (ingest)

- **What:** `Blacklist.is_blocked()` on companies/keywords/domains from `blacklist.yaml`.
- **Trigger:** Every `ingest_url`.
- **Outputs:** `ScrapeError` if blocked.

### Blacklist suggestions (advisory → user approve)

- **What:** On ingest, if title matches excluded-title patterns (defaults in code if YAML empty), inserts `blacklist_suggestions` pending row; **approve** appends company to `blacklist.yaml`.
- **Trigger:** Automatic on ingest/hunt; API `GET/POST /blacklist/suggestions/*`.
- **Outputs:** DB rows; YAML update only after user approve.

### Firefox profile management

- **What:** Discover system/managed profiles, clone, activate, health checks.
- **Trigger:** CLI `browser-profiles`, `browser-clone`, `browser-activate`; API `/browser/*`; UI Browser Settings + Control Center panel.
- **Outputs:** Updated `preferences.yaml` browser section.

### SQLite persistence

- **What:** Jobs, companies, scores, resumes, applications, events, generated answers, approval checkpoints, blacklist suggestions.
- **Trigger:** Pipelines and API; `init` / API startup `init_db()`.

### REST API + OpenAPI

- **What:** Routers for status, jobs, applications, resumes, profile, scoring, settings, analytics, automation (DB-backed monitor), control center, approvals, sources health, blacklist, browser, runtime control, AI activity, WebSocket events.
- **Trigger:** FastAPI app (`app/api/main.py`).

### WebSocket event stream

- **What:** `WS /ws/events` broadcasts `EventBus` messages; connect sends `runtime.snapshot`; server ping every 30s.
- **Trigger:** UI `useEventWebSocket` on **Live Browser** page only (see §8).

### Unit / integration tests (limited)

- **What:** Tests for blacklist, adapters detect, greenhouse/lever ingest (mocked HTTP), DB roundtrip, firefox profiles, approval service, match filters, config loader, scoring, renderers, etc.
- **Evidence:** `tests/unit/`, `tests/integration/`.

---

## 3. Partially implemented features

| Feature | What exists | What is missing / broken |
|--------|-------------|-------------------------|
| **Discovery scheduler** | `DiscoveryScheduler`, API `POST /control-center/discovery/start|pause|resume|stop`, CLI `search` uses `SourceOrchestrator.poll_all` | **Not wired in Control Center UI** (no Start Discovery / Pause Discovery buttons). UI “Start AI Search” uses **legacy** `collect_source_urls` only—**does not run LinkedIn/Raytheon browser discovery**. |
| **Source orchestrator vs control-center search** | `SourceOrchestrator` with `discover_all` / `poll_all`; job hunt uses `discover_all` | `POST /control-center/search` still calls `collect_source_urls` from `job_sources.py` (Greenhouse/Lever/url_list only). |
| **LinkedIn discovery** | `LinkedInSourceAdapter` with Playwright search + health check | Fragile DOM selectors; requires logged-in Firefox; disabled by default in YAML; not used by UI search button. |
| **Raytheon discovery** | `RaytheonCareersSourceAdapter` with Playwright listing scrape | Site-specific selectors; **uncertain** production reliability without live testing; disabled by default. |
| **Approval queue (UI)** | DB checkpoints, `/approvals/*`, Review Queue + Control Center panels | **Approve + submit from UI** does not complete browser submit: `submit_after_approval()` **raises** `AdapterError`. Approve with `submit=true` returns `submit_error`. User must submit manually in browser for assist flows. |
| **Auto mode approval wait** | `wait_for_checkpoint()` blocks apply pipeline until approve/reject | Works only while apply process is **still running** and blocked; approving from UI after pipeline returned does not resume submit. |
| **Live Browser** | Runtime API, screenshots endpoint, WS hook, override buttons | **No periodic screenshot stream** (only on explicit `screenshot()` calls). Queued-action Approve/Reject buttons in UI are **not wired** to API. Control Center imports `useEventWebSocket` but **does not use it** (activity still HTTP polling). |
| **Preferences: excluded titles / salary** | Schema fields + `job_filters.matches_filters()` | **Not present** in shipped `config/preferences.yaml`; excluded titles fall back to **hardcoded defaults** in `blacklist_suggestions.get_excluded_title_patterns()`. |
| **Question memory** | `QuestionMemory` (ChromaDB) class | **Not referenced** by apply pipeline (`memory_lookup=[]` in `ApplicationContext`). |
| **Agents package** | `app/agents/__init__.py` docstring only | No agent implementations. |
| **Concurrent sessions** | `automation.max_concurrent_sessions` in config | UI notes “enforced sequentially”; manager exists but practical use is single-session. |
| **Job hunt `assisted_apply`** | Stops before apply after tailor | By design partial—no apply step. |

---

## 4. Not implemented / placeholder systems

| Item | Evidence |
|------|----------|
| **Indeed / Glassdoor / L3Harris / TI discovery** | `ScaffoldSourceAdapter`: `health()` → `not_implemented`, `discover()` → `[]`. |
| **RSS job source** | Type in schema; `resolve_urls_for_source` returns `[]` for unknown types. |
| **`app/agents/`** | Empty package stub. |
| **`submit_after_approval`** | Always raises; planned “approve then submit” not built. |
| **Periodic browser screenshot telemetry** | No throttle/interval code in `browser.py`. |
| **Control Center blacklist review UI** | API exists (`/blacklist/suggestions`); **no panel** in Control Center (only Settings YAML editor for blacklist). |
| **Discovery scheduler UI controls** | API exists; **no dedicated UI** for start/pause/stop discovery scheduler. |
| **Pipeline stepper on Dashboard** | `PipelineStepper current={1}` **hardcoded**—not tied to hunt/runtime state. |
| **Topbar notifications bell** | Non-functional (no handler). |
| **CLI `init --force`** | Documented as unused placeholder. |
| **Embeddings / Chroma for Q&A in apply** | Service exists; pipeline does not call it. |

---

## 5. Job source adapter status

| Source | Implemented | Auth required | Scraping / discovery method | Actually functional? |
|--------|-------------|---------------|----------------------------|----------------------|
| **LinkedIn** (discovery) | **Partial** | **Yes** (Firefox session / cookies) | Playwright: jobs search page, collect `/jobs/view/` links | **Conditional**—only if profile logged in and DOM matches; not used by UI “Start AI Search”. Ingest/apply via `LinkedInAdapter` separate. |
| **LinkedIn** (ingest/apply) | **Yes** (assist) | **Yes** | Playwright scrape + Easy Apply fill; **submit refused in code** | **Partial**—fill works if logged in; user must submit manually. |
| **Indeed** | **No** (scaffold) | Unknown | None | **No** — returns no URLs. |
| **Glassdoor** | **No** (scaffold) | Unknown | None | **No**. |
| **Raytheon Careers** | **Partial** | **No** for public careers pages | Playwright on `careers.rtx.com` search/listing links | **Uncertain** — code present, selectors may break; disabled by default; not in UI search path. |
| **L3Harris Careers** | **No** (scaffold) | Unknown | None | **No**. |
| **Texas Instruments Careers** | **No** (scaffold) | Unknown | None | **No**. |
| **Greenhouse board** | **Yes** | No (public API) | `boards-api.greenhouse.io` JSON | **Yes** when `enabled: true` and valid `board_token`. |
| **Lever board** | **Yes** | No (public API) | `api.lever.co` JSON | **Yes** when enabled + valid `site_id`. |
| **url_list** | **Yes** | No | Static URLs from YAML | **Yes** if URLs listed (`manual-urls` enabled but **empty** in default YAML). |
| **Generic / unknown URLs** | **Yes** (fallback) | Often yes (browser) | Playwright + LLM field classification | **Variable**—depends on page complexity and LLM. |

**Default `config/job_sources.yaml`:** Only `manual-urls` is `enabled: true` with **empty** `urls`—so out-of-the-box **automated discovery finds nothing** until you enable sources and/or add URLs.

---

## 6. Browser automation status

### Playwright setup

- **Implemented:** `BrowserSession` uses `async_playwright()`, default `engine: firefox` in `preferences.yaml`.
- **Requires:** `playwright install firefox` (documented in setup docs); not verified in this audit run.

### Firefox integration

- **Implemented:** Persistent context (`launch_persistent_context`), system or managed profiles, clone-on-lock, profile discovery (`firefox_profiles.py`).
- **API:** `/browser/profiles`, `/browser/health`, `/browser/active`.

### Session persistence

- **Implemented:** `BrowserSessionManager` keeps sessions open across steps within a run; `AutomationRuntime.get_browser_session()` used by ingest (browser adapters) and apply.
- **Shutdown:** API lifespan calls `automation_runtime.shutdown()` → `close_all()`.

### Automation capabilities (real code paths)

| Capability | Status |
|------------|--------|
| **Navigation** | Yes — `page.goto`, `framenavigated` → `browser.navigate` events + runtime URL/title |
| **Clicks / fills** | Yes — in Greenhouse, Lever, LinkedIn, Generic adapters (selectors + Playwright) |
| **Form filling** | Yes — adapter-specific + generic LLM classification |
| **Submission** | Yes for Greenhouse/Lever/Generic **when** apply pipeline reaches `adapter.submit()`; **Never** for LinkedIn (`SubmitError`); gated by approvals/config |
| **Screenshots** | Yes — on explicit `screenshot()` calls; files under screenshots dir; API `GET /automation/runtime/screenshots/{filename}` |
| **DOM snapshots** | Yes — `dom_snapshot()` HTML files |

### Real-time visibility

| Mechanism | Status |
|-----------|--------|
| **WebSocket** | Yes — backend broadcasts; **Live Browser** consumes |
| **Runtime snapshot REST** | Yes — `GET /automation/runtime` (polled every 5s on Live Browser + WS updates) |
| **Automation monitor API** | Yes — `/automation/overview` reads **DB application events** + filesystem screenshot list (historical, not live stream) |
| **Embedded Firefox in UI** | **Not implemented** (by design) |

**NOT IMPLEMENTED:** Automatic screenshot every N seconds during automation (planned in architecture docs only).

---

## 7. Approval / safety system status

### Approval queue

- **Yes — DB-backed:** `approval_checkpoints` table, `ApprovalService`, `GET /approvals/pending`.
- **UI:** Review Queue and Control Center `ApprovalQueuePanel` list pending items.

### Is submission blocked until approval?

- **In apply pipeline — mostly yes:**
  - After every fill, a `pre_submit` checkpoint is created.
  - `human_review` mode **returns before submit** (status `awaiting_review`).
  - `auto` mode waits on `wait_for_checkpoint()` when `confirm_before_submit` is true (default **true**).
  - LinkedIn path **never calls** `submit()` even after approval.
- **Gaps (bypasses):**
  - **`PATCH /applications/{id}`** can set `status: submitted` **without** approval service or browser submit (`applications.py`).
  - **CLI `review --approve <id>`** sets `ApplicationStatus.submitted` directly (`review.py`)—**no** checkpoint or Playwright submit.
  - **UI approve with `submit: true`** calls broken `submit_after_approval()`.

### Safety rules: backend vs UI only

| Rule | Backend enforced? |
|------|-------------------|
| Default human review | Yes (config + pipeline) |
| confirm_before_submit | Yes in apply pipeline |
| allow_auto_submit gate | Yes |
| LinkedIn no auto submit | Yes in adapter |
| Approval before submit (auto path) | Yes **while pipeline blocked** |
| UI cannot mark submitted without API hole | **No** — PATCH/CLI review bypass |

### Blacklist

| Mechanism | Type |
|-----------|------|
| `blacklist.yaml` at ingest | **Hard enforcement** — ingest fails |
| Title pattern suggestions | **Advisory** until user approves suggestion |
| `excluded_titles` in preferences | Filter at hunt/search via `matches_filters` (defaults from code if YAML empty) |

---

## 8. Frontend (UI) reality check

### Pages (routes)

| Route | Functional? | Data source |
|-------|-------------|-------------|
| `/` Dashboard | **Yes** — real metrics | `/analytics`, `/jobs`, `/applications`, `/automation`, `/ai/*`, `/status` |
| `/control-center` | **Mostly yes** | Job hunt, ingest, search, settings, activity poll, source health, approvals |
| `/live-browser` | **Partial** | Runtime REST + WebSocket; screenshot when backend captures one |
| `/automation` | Redirect → `/live-browser` | — |
| `/jobs`, `/jobs/[id]` | **Yes** | Jobs/scoring APIs |
| `/resume-studio` | **Yes** | Resume APIs |
| `/review-queue` | **Partial** | Approvals API (not legacy PATCH for approve) |
| `/ai-console` | **Yes** | Log-derived AI activity |
| `/analytics` | **Yes** | Analytics API |
| `/profile` | **Yes** | Profile API |
| `/settings`, `/settings/browser` | **Yes** | Settings + browser APIs |

### Control Center

- **Exists and wired:** Job hunt start/pause/stop, ingest, search, automation preference saves, Firefox profile, activity feed (5s poll), source health panel, approval panel.
- **Gaps:** No discovery scheduler buttons; no blacklist suggestion panel; WebSocket imported but unused; “Start AI Search” does not use full source orchestrator (LinkedIn/Raytheon).

### Live Browser

- **Real (partial):** Shows runtime state, live screenshot **when file exists**, action log from runtime + WS, pause/resume/stop/manual/return AI call real APIs.
- **Not real:** Continuous video-like stream; action queue buttons not wired.

### Static / decorative UI

- Dashboard `PipelineStepper` fixed at step 1.
- Topbar bell icon.

---

## 9. Backend architecture

### Orchestration design

```
CLI / API
    → Pipelines (ingest, score, tailor, apply)
    → JobHuntManager (multi-step hunt loop)
    → DiscoveryScheduler (background poll) ─→ SourceOrchestrator ─→ source adapters
    → AutomationRuntime ─→ BrowserSessionManager ─→ BrowserSession (Playwright)
    → ApprovalService / Blacklist / BlacklistSuggestionService
    → EventBus ─→ WebSocket
```

All run **in-process** in the FastAPI/CLI Python process—**no separate worker process** or job queue (Redis/Celery).

### Worker / scheduler

- **DiscoveryScheduler:** asyncio background task; started only via `POST /control-center/discovery/start` (not auto-started on API boot).
- **JobHuntManager:** separate asyncio task per “start hunt”.

### API completeness

- **Broad REST surface** for CRUD-ish inspection and control (see `app/api/main.py` routers).
- **Inconsistency:** `/control-center/search` vs `SourceOrchestrator` (see §3).

### Database

- **SQLite** via SQLAlchemy async; tables created on `init_db()` (no Alembic migrations in repo).
- **New tables** (`approval_checkpoints`, `blacklist_suggestions`) rely on `create_all`—existing DBs pick them up on next init if fresh; **uncertain** behavior if old DB without migration strategy.

### Event system / WebSocket

- **EventBus:** sync emit to async subscribers.
- **WebSocket:** functional bridge; used on Live Browser page.

---

## 10. CLI capabilities

| Command | Functional? | Notes |
|---------|-------------|--------|
| `init` | **Yes** | Creates data dirs + DB |
| `doctor` | **Yes** | Diagnostics |
| `search` | **Partial** | Uses `SourceOrchestrator.poll_all` (includes browser sources if enabled) |
| `ingest-url` | **Yes** | Single URL |
| `analyze` | **Yes** | Requires LLM |
| `generate-resume` | **Yes** | Requires LLM |
| `apply` | **Yes** | Fill + checkpoint; submit only with `--auto` + config + approval + non-LinkedIn |
| `dry-run` | **Yes** | |
| `review` | **Partial** | List works; `--approve`/`--reject` **bypass** approval service |
| `list-applications` | **Yes** | |
| `export` | **Yes** | |
| `runtime-check` | **Yes** | |
| `browser-profiles` / `browser-clone` / `browser-activate` | **Yes** | |

**NOT IMPLEMENTED:** CLI commands for `discovery/start`, `job-hunt`, or approval checkpoint approve/reject (API only).

---

## 11. Critical gaps (most important)

1. **No turnkey job discovery out of the box** — default sources disabled or empty; UI search does not use browser discovery adapters.
2. **Approval ≠ submit** — Approving in UI does not run Playwright submit; `submit_after_approval` is stubbed; user must finish in Firefox manually (aligned with LinkedIn assist, but unclear for Greenhouse/Lever).
3. **Safety bypasses** — `PATCH /applications` and `jobassist review --approve` can mark applications submitted without going through approval checkpoints or browser.
4. **Split discovery paths** — Job hunt vs CLI search vs control-center search use different code paths; easy to think “search” enables LinkedIn when it does not.
5. **Four of six named job boards are scaffolds only** — Indeed, Glassdoor, L3Harris, TI do nothing.
6. **Raytheon/LinkedIn discovery reliability unproven** — brittle selectors; need live validation.
7. **Supervised loop is fragmented** — Hunt, discovery scheduler, apply, and approvals are separate; no unified “supervised session” UX beyond Live Browser snapshots.
8. **Question memory / agents not integrated** — No learning from past application answers in fill flow.
9. **preferences.yaml missing new fields** — excluded titles/salary/industries only in schema/code defaults.
10. **Testing does not cover E2E automation** — No Playwright integration tests for apply/discovery in CI sense.

---

## 12. Readiness scores

| Dimension | Score | Why |
|-----------|-------|-----|
| **MVP readiness** | **55%** | Core pipelines (ingest, score, tailor, fill) work for Greenhouse/Lever/URL/generic with local LLM. End-to-end “discover → fit → tailor → fill → you approve → submit” is possible **manually** via CLI + URLs. UI and orchestration are substantial but inconsistent; default config discovers nothing. |
| **Automation readiness** | **45%** | Playwright + Firefox + adapters are real; runtime/WS exist. Missing reliable multi-source discovery, post-approval submit, periodic telemetry, and unified scheduler UI. High fragility on LinkedIn/Raytheon scraping. |
| **Real-world usability** | **40%** | Suitable for a **technical operator** willing to configure sources, LLM, Firefox login, and CLI/API. **Not** yet a clear daily driver for supervised mass applying without gaps (approval/submit confusion, bypass paths, empty defaults). |

---

## Appendix: Quick “what works for your goal”

| Your goal | Works today? | Practical path |
|-----------|--------------|----------------|
| Discover jobs | **Partial** | Enable Greenhouse/Lever or add URLs; enable LinkedIn/Raytheon in YAML + use **job hunt** or CLI `search`, **not** Control Center “Start AI Search” alone |
| AI fit analysis | **Yes** | `analyze` or hunt |
| Generate resume/cover letter | **Yes** | `generate-resume` or hunt |
| Prefill applications | **Yes** (ATS-dependent) | `apply` or hunt after tailor |
| Manual approve every critical step | **Partial** | Checkpoints created; you approve in UI; **submit is manual** for LinkedIn; for others may need browser or broken auto path |
| Nothing submitted automatically | **Mostly** | Default settings + LinkedIn block help; **fix bypasses** if you require strict guarantee |

---

*This document reflects the repository state at audit time. Re-run an audit after major changes.*
