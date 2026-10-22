# Orbital Environment Intelligence

Orbital Environment Intelligence (OEI) analyzes Earth's tracked artificial orbital population as an evolving environment. It combines population, composition, concentration, event, persistence, and 3D exploration workflows instead of presenting only an object catalog.

## Current implementation

This repository contains a runnable production-shaped vertical slice and deployment scaffold:

- React/TypeScript analytical dashboard with an instanced Three.js orbital view.
- FastAPI service implementing the planned `/api/v1` surface.
- SQLAlchemy persistence with local SQLite and production PostgreSQL support.
- Saved workspaces with revocable read-only share links.
- Deterministic development data that exercises every analytical module and the 40,000-point renderer.
- Pipeline primitives for Space-Track/CelesTrak retrieval, SGP4 propagation, snapshot selection, quality quarantine, Arrow/Parquet materialization, R2 publication, and atomic release promotion.
- OpenAPI-generated TypeScript contracts, Alembic migrations for the complete data/provenance schema, Docker images, CI, scheduled ingestion, scheduled quality audits, and deployment configuration.

The bundled dataset is intentionally synthetic and clearly labeled. Real Space-Track and ESA ingestion requires account credentials and acceptance of provider terms.

## Local development

Requirements: Node.js 22+, pnpm 10+, Python 3.12+, and `uv`.

```powershell
Copy-Item .env.example .env
pnpm install
uv sync --project apps/api --extra dev
uv run --project apps/api alembic upgrade head
uv run --project apps/api uvicorn oei_api.main:app --reload --port 8000
pnpm dev
```

Open `http://localhost:5173`. API documentation is available at `http://localhost:8000/docs`.

To build a validated local Arrow/Parquet release:

```powershell
uv run --project apps/api oei-pipeline fixture-release --output data/public --release-id local-check --date 2026-09-01
```

`oei-pipeline sync-current` downloads and checksums CelesTrak fallback inputs. When Space-Track credentials are present it also propagates the current GP catalog with SGP4, quarantines failures, publishes derived artifacts, and updates the release pointer only after validation.

## Verification

```powershell
uv run --project apps/api pytest
uv run --project apps/api ruff check .
pnpm typecheck
pnpm test
pnpm build
```

Regenerate the OpenAPI client after changing API routes or schemas:

```powershell
pnpm contracts:generate
```

Playwright coverage requires a one-time browser install:

```powershell
pnpm --filter @oei/web exec playwright install chromium
pnpm --filter @oei/web test:e2e
```

## Data policy

OEI distinguishes catalogued objects from statistically modeled debris. It is an educational analytics system, not a collision-avoidance or operational space-traffic-management product. Raw restricted/provider archives are never republished; every analytical response includes release, freshness, quality, and source metadata.

## Project documents

- [Architecture](docs/ARCHITECTURE.md)
- [Methodology](docs/METHODOLOGY.md)
- [Data dictionary](docs/DATA_DICTIONARY.md)
- [Deployment runbook](docs/DEPLOYMENT_RUNBOOK.md)
- [Recovery procedure](docs/RECOVERY.md)
- [Presentation guide](docs/PRESENTATION.md)
- [Security policy](SECURITY.md)
