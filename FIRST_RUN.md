# First Run Guide

This guide is for a fresh machine with no dependencies installed.

## Prerequisites

- Python 3.12+
- Node.js 20+
- Firefox installed locally

## Step-by-step

1. Run bootstrap:

   ```bash
   pnpm bootstrap
   ```

2. Start the stack:

   ```bash
   pnpm dev
   ```

3. Verify services:
   - Frontend: `http://127.0.0.1:3000`
   - Backend API docs: `http://127.0.0.1:8000/docs`

4. In the UI open `Browser Settings` and choose:
   - a **system** Firefox profile to reuse existing logins, or
   - a **managed** profile cloned from system.

5. Check `Dashboard -> Runtime Health` for:
   - backend reachable
   - database ready
   - browser session cookie state
   - LLM connectivity
