# Development guide

## Layout

```
app/
  agents/       (reserved for future high-level agents)
  ats/          ATS adapters + registry
  automation/   Playwright + retry + screenshot helpers
  api/          FastAPI inspection app
  cli/          Typer commands
  config/       Pydantic schemas + loader + path resolver
  database/     SQLAlchemy ORM + DAOs + session_scope
  llm/          LLMProvider Protocol + LM Studio/Ollama clients
  models/       Pydantic domain models
  pipelines/    Ingest / Score / Tailor / Apply
  prompts/      Jinja2 templates
  resume/       Tailor + cover letter + DOCX/PDF renderers
  services/     question_memory (Chroma), blacklist
  utils/        logging, errors, hashing, async_utils
```

## Common tasks

| Task | Command |
| --- | --- |
| Run the CLI | `python -m app.cli.main --help` |
| Run the API | `python -m uvicorn app.api.main:app --reload` |
| Format code | `python -m black app tests` |
| Lint | `python -m ruff check app tests` |
| Type-check | `python -m mypy app` |
| Tests | `python -m pytest` |
| Coverage | `python -m pytest --cov=app --cov-report=term-missing` |

A `Makefile` also exposes `setup`, `install`, `fmt`, `lint`, `type`,
`test`, `test-cov`, `run-api`, `run-cli`, `db-init`, and `clean`.

## Adding a new pipeline command

1. Implement the async function in `app/pipelines/`.
2. Add a Typer command under `app/cli/commands/`.
3. Register it in `app/cli/main.py`.
4. (Optional) Expose it over HTTP under `app/api/routers/`.

## Writing tests

- Pure logic tests: drop into `tests/unit/`. They run with no network.
- HTTP-touching tests: use `respx` to mock httpx calls. See
  `tests/integration/test_ingest_greenhouse.py`.
- DB tests: depend on the `fresh_db` fixture in `tests/conftest.py`.
  It rebinds the global engine to in-memory SQLite for the test.

## Architectural rules

- **AI for reasoning, code for actions.** The LLM never sends Playwright
  commands. Adapters take structured suggestions from the LLM and execute
  them deterministically.
- **No god classes.** Each module has one clear responsibility (e.g.,
  `app/services/blacklist.py` is ~30 lines).
- **Async by default.** Sync entry points (Typer commands) wrap async via
  `app/utils/async_utils.run_sync` or a local `asyncio.run`.
- **Pydantic at the edges, dataclasses inside.** The DB layer uses
  SQLAlchemy mapped classes; everywhere else uses Pydantic. DAOs translate.
- **No silent failures.** Adapters log + screenshot when something breaks
  rather than swallowing errors.
