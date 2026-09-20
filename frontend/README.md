# Frontend Operations Console

Desktop-first operations console for the local AI job application agent.

## Stack

- Next.js App Router + TypeScript
- shadcn/ui + Tailwind v4 + tweakcn-compatible tokens
- TanStack Query + Zustand
- TanStack Table
- React Hook Form + Zod
- Recharts + Framer Motion
- Sonner notifications

## Run locally

1. Start the backend API on port `8000`.
2. Create env file:

```bash
cp .env.local.example .env.local
```

3. Install and run:

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Available pages

- `/` dashboard
- `/jobs` jobs explorer
- `/jobs/[jobId]` job detail workspace
- `/resume-studio`
- `/review-queue`
- `/automation`
- `/ai-console`
- `/settings`
- `/profile`
- `/analytics`
