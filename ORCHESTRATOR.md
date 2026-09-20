# Supervised Job Application Orchestrator

Unified supervised workflow for discovery, scoring, tailoring, browser fill, approval, and submission.

## Architecture

```mermaid
flowchart TB
  subgraph entry [Entry points]
    CC[Control Center UI]
    CLI[CLI jobassist]
    API[/orchestrator/*]
  end

  subgraph orchestrator [JobApplicationOrchestrator]
    D[1 Discover]
    F[2 Filter]
    S[3 Score]
    T[4 Tailor]
    P[5 Prepare - Playwright fill]
    A[6 STOP - approval checkpoint]
    SUB[7 Submit if approved]
    D --> F --> S --> T --> P --> A --> SUB
  end

  subgraph discovery [SourceOrchestrator.discover]
    REG[SourceRegistry]
    GH[Greenhouse / Lever API]
    LI[LinkedIn browser]
    RT[Raytheon browser]
    STUB[Indeed / Glassdoor / L3Harris / TI stubs]
    URL[url_list fallback]
    REG --> GH & LI & RT & STUB & URL
  end

  subgraph submit_gate [Single submit gateway]
    SAF[submit_application_if_approved]
  end

  CC --> orchestrator
  CLI --> orchestrator
  API --> orchestrator
  D --> discovery
  SUB --> SAF
```

## Pipeline stages

| Stage | Description |
|-------|-------------|
| `discovering` | `SourceOrchestrator.discover_urls` / `poll_all` |
| `ingesting` | `ingest_url` per URL |
| `filtering` | `matches_filters` + score threshold |
| `scoring` | `score_existing_job` |
| `tailoring` | `tailor_existing_job` |
| `preparing` | `prepare_application` (fill only) |
| `awaiting_approval` | `pre_submit` checkpoint created |
| `submitting` | `submit_application_if_approved` (autonomous mode only) |

## Removed / consolidated flows

| Removed or deprecated | Replaced by |
|----------------------|-------------|
| `JobHuntManager` independent loop | `JobApplicationOrchestrator` (facade re-exports for compat) |
| `collect_source_urls` in Control Center search | `orchestrator.discover()` → `SourceOrchestrator.poll_all` |
| CLI `search` calling legacy collectors | `orchestrator.discover(ingest=True)` |
| `apply_pipeline` inline `adapter.submit()` | `prepare_application` + `submit_application_if_approved` |
| `PATCH /applications` → `submitted` | **403** — must approve checkpoint |
| `jobassist review --approve` on application id | Checkpoint id + optional `--submit` via gateway |
| `submit_after_approval` stub | `submit_application_if_approved` |

**Still present (optional, not the main hunt loop):** `DiscoveryScheduler` for background poll-only runs via `/control-center/discovery/*`. Prefer **Start Job Hunt** for the full pipeline.

## API endpoints

### Orchestrator (canonical)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/orchestrator/status` | Full `OrchestratorStatus` (stage, queue, stats) |
| POST | `/orchestrator/start` | Start supervised loop |
| POST | `/orchestrator/pause` | Pause |
| POST | `/orchestrator/resume` | Resume |
| POST | `/orchestrator/stop` | Stop |

### Control Center (UI aliases — same backend)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/control-center/job-hunt/status` | Same as orchestrator status |
| POST | `/control-center/job-hunt/start` | Start hunt |
| POST | `/control-center/job-hunt/pause` | Pause |
| POST | `/control-center/job-hunt/resume` | Resume |
| POST | `/control-center/job-hunt/stop` | Stop |
| POST | `/control-center/search` | Discovery + ingest only (`discover(ingest=True)`) |
| POST | `/control-center/ingest` | Manual URL ingest (filter only) |

### Approvals & submission

| Method | Path | Description |
|--------|------|-------------|
| GET | `/approvals/pending` | Pending checkpoints |
| POST | `/approvals/{id}/approve?submit=true` | Approve + `submit_application_if_approved` |

### Blacklist (safe mode)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/blacklist/suggestions` | AI suggestions only |
| POST | `/blacklist/suggestions/{id}/approve` | User approves → YAML updated |
| POST | `/blacklist/suggestions/{id}/reject` | Dismiss |

### Live browser

| Event | Description |
|-------|-------------|
| `browser.navigate` | URL / title changes |
| `browser.action` | Clicks, fills |
| `browser.screenshot` | On demand + every ~8s when session active |
| `automation.state` | Runtime snapshot |
| `orchestrator.*` / `job_hunt.*` | Pipeline progress (dual-emitted for UI compat) |

WebSocket: `GET /ws/events`

## Control Center UI map

| Area | Purpose |
|------|---------|
| **Start Job Hunt** | Full orchestrator loop |
| **Stage badge + current job** | Live pipeline position |
| **Job queue** | Next URLs being processed |
| **Discover & ingest** | Search-only (no score/apply) |
| **Source health** | Per-adapter status |
| **Approval queue** | Pre-submit checkpoints |
| **Blacklist suggestions** | User-approved YAML updates only |
| **Live activity** | DB + log feed (WS-invalidated) |

`/live-browser` — runtime snapshot, screenshots, queued actions via WebSocket.

## Migration plan (non-breaking)

1. **Backend** — Deploy orchestrator + submission gateway (done). Existing `/control-center/job-hunt/*` unchanged.
2. **Clients** — Point new integrations at `/orchestrator/*`; UI already uses job-hunt aliases.
3. **Operators** — Use Control Center **Start Job Hunt** instead of CLI for normal runs.
4. **CLI** — `jobassist search` / `apply` / `review` call unified paths; update scripts that PATCH `submitted`.
5. **Config** — Enable sources in `job_sources.yaml`; set `apply.allow_auto_submit` only if autonomous submit is intended.
6. **Deprecate** — After one release, remove `DiscoveryScheduler` UI endpoints if unused; remove `collect_source_urls` exports.

## Success criteria checklist

- [ ] Control Center **Start Job Hunt** runs discover → score → tailor → prepare without CLI
- [ ] Each application stops at `awaiting_approval` in manual modes
- [ ] Submit only after UI/CLI approve + `submit_application_if_approved`
- [ ] Search uses same sources as hunt (LinkedIn/Raytheon when enabled)
- [ ] Live Browser shows URL, actions, periodic screenshots over WS
