# Quickstart

This repository now runs as a local monorepo platform.

## 1) Clone + enter directory

```bash
git clone <repo-url>
cd "Job Finding Assistant"
```

## 2) Bootstrap once

```bash
pnpm bootstrap
```

If `pnpm` is unavailable, use:

```bash
npm run bootstrap
```

## 3) Start everything

```bash
pnpm dev
```

This starts:

- FastAPI backend on `http://127.0.0.1:8000`
- Next.js frontend on `http://127.0.0.1:3000`
- Health checks and runtime diagnostics

## 4) Open the console

Go to `http://127.0.0.1:3000`, then open:

- `Settings -> Browser Settings`
- Select a Firefox profile (system or managed)
- Start pipeline operations
