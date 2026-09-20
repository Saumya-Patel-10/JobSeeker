# Unified monorepo task runner.

PY ?= python
NODE ?= node

.PHONY: help bootstrap dev backend frontend doctor install lint test fmt type clean run-api run-cli

help:
	@echo "Job Finding Assistant - unified workflow targets"
	@echo ""
	@echo "  bootstrap  - Install backend + frontend deps, install Playwright Firefox, init DB"
	@echo "  dev        - Start backend + frontend with health checks"
	@echo "  backend    - Start only backend API server"
	@echo "  frontend   - Start only frontend app server"
	@echo "  doctor     - Run runtime diagnostics"
	@echo "  install    - Install backend/frontend dependencies"
	@echo "  lint       - Run backend and frontend lint checks"
	@echo "  test       - Run backend tests + frontend type checks"
	@echo "  fmt        - Format backend Python files"
	@echo "  type       - Run backend mypy checks"
	@echo "  run-api    - Legacy alias for backend"
	@echo "  run-cli    - Show backend CLI help"
	@echo "  clean      - Remove Python and frontend caches/build artifacts"

bootstrap:
	$(NODE) scripts/dev/bootstrap.mjs

dev:
	$(NODE) scripts/dev/dev.mjs

backend:
	$(NODE) scripts/dev/backend.mjs

frontend:
	$(NODE) scripts/dev/frontend.mjs

doctor:
	$(NODE) scripts/dev/doctor.mjs

install:
	$(NODE) scripts/dev/install.mjs

lint:
	$(NODE) scripts/dev/lint.mjs

test:
	$(NODE) scripts/dev/test.mjs

fmt:
	$(PY) -m black app tests

type:
	$(PY) -m mypy app

run-api: backend

run-cli:
	$(PY) -m app.cli.main --help

clean:
	@$(PY) -c "import pathlib, shutil; [shutil.rmtree(p, ignore_errors=True) for p in ['build', 'dist', '.pytest_cache', '.mypy_cache', '.ruff_cache', 'htmlcov', 'frontend/.next', 'frontend/node_modules/.cache']]; [p.unlink() for p in pathlib.Path('.').rglob('*.pyc')]; print('cleaned')"
