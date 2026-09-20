# Configuration reference

All configuration lives under `config/`. Edits take effect on the next CLI
or API invocation (the loader caches via `lru_cache`; call
`app.config.loader.reload_config()` to bust it in long-running processes).

## `config/profile.yaml`

Validated against `app/models/profile.py:Profile`. Required fields:

- `personal.first_name`, `personal.last_name`, `personal.email`, `personal.phone`

All other sections (`address`, `links`, `salary`, `work_authorization`,
`demographic`, `education`, `certifications`, `employment`, `skills`,
`standard_answers`) are optional but recommended.

`standard_answers` is a list of `{question, answer, category?}` entries that
the apply pipeline matches against before invoking the LLM.

## `config/preferences.yaml`

Validated against `app/config/schema.py:Preferences`.

### `llm`

| Key | Default | Notes |
| --- | --- | --- |
| `provider` | `lmstudio` | Or `ollama`. |
| `base_url` | `http://localhost:1234/v1` | LM Studio default; `http://localhost:11434` for Ollama. |
| `api_key` | `lm-studio` | LM Studio ignores; placeholder keeps OpenAI clients happy. |
| `chat_model` | `local-model` | Set to the loaded LM Studio model id (e.g. `meta-llama/Llama-3.1-8B-Instruct-GGUF`). |
| `embedding_model` | `null` | Required only if you want LM Studio embeddings; otherwise ChromaDB's bundled MiniLM is used. |
| `request_timeout` | `120.0` | Seconds. Increase for big prompts on slow CPUs. |
| `max_retries` | `3` | Tenacity exponential backoff. |
| `temperature` | `0.2` | Default; per-prompt overrides live in `prompts.yaml`. |

### `browser`

| Key | Default | Notes |
| --- | --- | --- |
| `headless` | `false` | Start headed so you can log into LinkedIn etc. once; subsequent runs reuse cookies. |
| `slowmo_ms` | `50` | Per-action throttle. |
| `profile` | `default` | Subdirectory of `data/browser_profiles/`. |
| `timeout_ms` | `30000` | Playwright default timeout. |
| `viewport_width` / `viewport_height` | `1366` / `900` | |

### `apply`

| Key | Default | Notes |
| --- | --- | --- |
| `default_mode` | `human_review` | `dry_run` / `human_review` / `auto`. |
| `allow_auto_submit` | `false` | Master switch for auto-submit. CLI also requires `--auto`. |
| `daily_limit` | `20` | Soft cap. Not enforced yet in v1 — reserved for the scheduler. |
| `require_min_score` | `0.6` | Pipelines skip jobs below this composite score. |
| `confirm_before_submit` | `true` | (Reserved for the future interactive review UI.) |

### `scoring.weights`

Mixes the five sub-scores into a single composite. Must sum to non-zero.
Defaults: `skill_overlap 0.35`, `seniority_alignment 0.20`,
`salary_fit 0.15`, `location_compatibility 0.15`, `fit_score 0.15`.

## `config/job_sources.yaml`

A list of named sources. Each has a `type` and `config`:

- `greenhouse_board` — `config.board_token: "stripe"`, optional `keywords` list.
- `lever_board` — `config.site_id: "ramp"`, optional `department`.
- `url_list` — `config.urls: [...]`.

`enabled: false` skips a source without removing it.

## `config/prompts.yaml`

Maps logical names → Jinja2 template files in `app/prompts/`. Per-prompt
overrides for `model`, `temperature`, `max_tokens`, and `response_format`
take precedence over `preferences.yaml` LLM defaults.

The five prompts shipped by default: `job_match`, `resume_tailor`,
`cover_letter`, `field_classify`, `answer_question`. Pipelines look them up
by these exact names; renaming requires updating the pipeline code.

## `config/resume_master.json`

Validated against `app/models/resume.py:ResumeMaster`. Free-form JSON —
you supply your real career data here. The shipped template uses
placeholder content.

## `config/blacklist.yaml`

Three lists (`companies`, `keywords`, `domains`). Substring matching, case
insensitive. The ingest pipeline filters on these immediately after a
successful scrape.

## `.env` (optional)

`.env.example` shows the supported keys: `JOBASSIST_LOG_LEVEL`, optional
URL overrides for LM Studio/Ollama, `JOBASSIST_ROOT` for non-standard
installs.
