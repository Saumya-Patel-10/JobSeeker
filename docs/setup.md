# Setup

## Prerequisites

- **Python 3.12+** — verify with `python --version`.
- **Local LLM**:
  - **LM Studio** (recommended) running at `http://localhost:1234`. Start the
    OpenAI-compatible server in Developer mode and load a chat model
    (7B+ instruct works well).
  - **Or Ollama** at `http://localhost:11434`. Pull a model with
    `ollama pull llama3.1:8b-instruct` (then set `preferences.yaml: llm.provider: ollama`).
- **~3 GB free disk** for Playwright Firefox + ChromaDB's bundled embedder.
- **OS**: Windows 10+, macOS 13+, or Linux. Scripts in `scripts/` ship as
  both `.ps1` and `.sh`.

## One-shot bootstrap (Windows)

```powershell
.\scripts\bootstrap.ps1
```

## One-shot bootstrap (macOS / Linux)

```bash
bash scripts/bootstrap.sh
```

The script creates a virtual environment in `.venv/`, installs the project
with dev extras, installs Playwright Firefox, and runs `jobassist init`.

## Manual install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1            # macOS/Linux: source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m playwright install firefox
python -m app.cli.main init
```

## Verify

```powershell
python -m app.cli.main doctor
```

Expected output: every row marked `OK` except possibly the LLM if you
haven't started LM Studio yet. The `Configs` row will fail loudly if
`config/profile.yaml` or `config/resume_master.json` is malformed.

## What `init` creates

- `data/{jobs,applications,resumes/{generated,master},logs,cache,browser_profiles,screenshots}/`
- `data/jobassist.db` — empty SQLite database with all tables.
- (Configs already shipped in `config/` — `init` does not overwrite them.)

## Next steps

1. Edit `config/profile.yaml` with your real personal info.
2. Edit `config/resume_master.json` with your real experience.
3. Open LM Studio, load a chat model, and start the local server.
4. `python -m app.cli.main doctor` until everything is green.
5. Try `python -m app.cli.main ingest-url <some_greenhouse_url>`.
