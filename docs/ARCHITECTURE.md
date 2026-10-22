# Architecture

OEI is split into a static analytical client, a small transactional API, a reproducible data pipeline, and object storage. The split keeps PostgreSQL small while allowing browser-friendly historical releases to grow independently.

```text
Space-Track / CelesTrak / GCAT / ESA / NASA
                    |
             scheduled ingestion
                    v
      immutable raw inputs in Cloudflare R2
                    |
        normalize -> validate -> propagate
                    |
       +------------+----------------+
       |                             |
curated Parquet + Arrow          Neon PostgreSQL
snapshots and histories          aggregates, provenance,
in R2                            events, workspaces
       |                             |
       +-------------+---------------+
                     v
              FastAPI / Render
                     |
       cached JSON, exports, manifests
                     v
      React / Cloudflare Pages / browser GPU
```

## Runtime boundaries

- `apps/web` owns routing, accessible charts and tables, GPU point rendering, saved-view controls, and client-side visual exports.
- `apps/api` owns validation, authorization, low-latency aggregate queries, public metadata, workspace persistence, and export authorization.
- `apps/api/src/oei_pipeline` owns source retrieval, checksums, orbital derivations, release quality gates, Arrow/Parquet materialization, and atomic publication.
- `packages/contracts` contains the generated OpenAPI surface and ergonomic shared domain types.

The API never serves provider bulk archives. A release becomes visible only when immutable artifacts have been validated and the mutable `current.json` pointer is written last. A failed run leaves the previous pointer unchanged.

## Performance strategy

The 3D view uses a single typed-buffer point cloud rather than one React component per object. Current development snapshots exercise 40,000 points. Production historical snapshots are discrete observations; the UI crossfades between them and does not invent monthly trajectories. Charts and tables remain the accessible alternative to WebGL.

## Trust boundaries

Clerk signs identity tokens; FastAPI validates issuer, audience, signature, and subject. The database owns private workspace state. R2 public artifacts contain only derived, publishable data. Administrative routes require both a valid token and membership in `ADMIN_USER_IDS`.
