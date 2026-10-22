# Deployment runbook

## Prerequisites

Create Space-Track and, if available, ESA DISCOS accounts and accept their terms. Provision Neon PostgreSQL, a private Cloudflare R2 bucket, Clerk, Sentry, Render, Cloudflare Pages, and an external HTTPS uptime check. Recheck current provider pricing before deployment.

## Database and API

1. Create Neon and copy its pooled PostgreSQL URL using the `postgresql+asyncpg://` driver form.
2. Create a Render web service from `render.yaml` on the paid 512 MB plan.
3. Add `DATABASE_URL`, exact comma-separated `WEB_ORIGINS`, Clerk issuer/audience, administrator user IDs, and Sentry DSN as Render secrets.
4. Deploy. The container runs `alembic upgrade head` before Uvicorn.
5. Verify `/api/v1/health`, `/api/v1/ready`, and `/docs`; then run the workspace save/share/revoke smoke test.

## Web

Create a Cloudflare Pages project with root directory `/`, build command `pnpm install --frozen-lockfile && pnpm build`, and output `apps/web/dist`. Add `VITE_API_BASE_URL`, Clerk publishable key, and optional Sentry DSN. Configure the custom domain, HTTPS, Brotli, and immutable caching for hashed `/assets` files. `_redirects` provides SPA routing.

## R2 and scheduled ingestion

Create an R2 API token limited to the project bucket. Store R2 and provider credentials only in the protected GitHub `production-data` environment. Enable `Current data synchronization` after a manual run succeeds. The workflow writes content-addressed raw inputs; publication code writes immutable release artifacts and moves `current.json` only after quality gates pass.

Configure bucket lifecycle rules for failed staging/diagnostic objects while retaining curated releases. Never make provider-restricted raw prefixes public.

## Operational checks

- Uptime monitor: `/api/v1/health` every five minutes; alert after two failures.
- Readiness monitor: `/api/v1/ready` from a trusted location.
- Sentry: frontend and backend alerts with secret redaction.
- Freshness: alert at 6 hours; UI stale banner after 12 hours.
- Neon: daily logical backup or provider branch/snapshot, tested quarterly.
- Spend alerts: Render, Neon, R2, Cloudflare, Clerk, and Sentry.

## Release checklist

Run the commands in the README, inspect the Methodology screen, generate OpenAPI contracts, verify that no `.env` or raw archive is tracked, check mobile/keyboard workflows, and download a presentation-safe `apps/web/dist` artifact from CI.
