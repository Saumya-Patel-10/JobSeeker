# Troubleshooting

## `doctor` says LLM is `FAIL`

- Confirm LM Studio is running and the local server is started (status bar in
  LM Studio shows "Running on http://localhost:1234").
- Open `http://localhost:1234/v1/models` in your browser — you should see a
  JSON listing.
- For Ollama, run `ollama list` to verify a model is installed.
- Update `preferences.yaml: llm.chat_model` to the exact model id printed
  by `/v1/models` or `ollama list`.

## `doctor` says Playwright Firefox is `FAIL`

```powershell
python -m playwright install firefox
```

On Windows, you may also need `python -m playwright install-deps` (Linux only).

## `chromadb` import error on Windows

ChromaDB depends on `onnxruntime`. If pip can't find a wheel, install the
Visual C++ Redistributable (commonly already on Windows 10/11) and retry.
You can also pin `chromadb==0.5.x` if a newer release ships a broken wheel
for your Python version.

## `LMStudioProvider` returns valid JSON wrapped in code fences

The provider already strips ```json fences. If you see `LLMValidationError`,
the model probably emitted prose around the JSON; pick a stronger model or
lower `temperature` to 0.0 for the affected prompt in `config/prompts.yaml`.

## Playwright says "Executable doesn't exist"

That means the `playwright install` step was skipped. Run:

```powershell
python -m playwright install firefox
```

If you bootstrapped with `scripts/bootstrap.ps1` and it failed at that step,
you'll see this error.

## LinkedIn adapter refuses to submit

That is intentional. The LinkedIn adapter is assist-only — it fills the
form and stops at the Submit button so the user can review. Submitting
automatically violates LinkedIn's Terms of Service.

## Resume rendering produces ugly DOCX

- DOCX styling is intentionally minimal for ATS-friendliness (no tables,
  no images, plain bold runs).
- For a flashier visual, open the generated `.docx` in Word and apply a
  template post-hoc.

## "Job not found" after `ingest-url`

Run `jobassist list-applications` and `jobassist doctor` — if the DB row
is missing, check `data/logs/app.log` for the actual error from the adapter.

## Adapter fails silently on a Greenhouse page

Two common causes:

1. The board is private. Greenhouse exposes the public API only for boards
   the company has enabled. If the API returns 404, the adapter raises
   `ScrapeError`.
2. The URL is from `boards.greenhouse.io/embed/...`. Use the canonical
   `boards.greenhouse.io/<token>/jobs/<id>` URL instead.

## Logs

Everything important is in `data/logs/app.log` as JSON lines. Tail with:

```powershell
Get-Content -Path data\logs\app.log -Wait -Tail 50
```

```bash
tail -f data/logs/app.log | jq .
```
