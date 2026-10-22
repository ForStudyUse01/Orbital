# Failure and recovery procedure

## Upstream source failure

Do not alter `current.json`. Record the failed ingestion run and retain diagnostic metadata without publishing incomplete rows. Public APIs continue serving the last validated release; after 12 hours the client identifies it as stale. Retry only within provider rate limits.

## Bad release discovered after publication

1. Identify the last known-good immutable release manifest.
2. Validate its Arrow/Parquet checksums.
3. Replace only the `current.json` pointer with that manifest.
4. Mark the defective database release withdrawn; do not delete immutable evidence.
5. Purge Cloudflare cache for the pointer and affected API aggregates.
6. Document cause, scope, and corrective quality gate.

## Database failure

Place the API in maintenance mode if writes are unsafe. Restore the latest daily backup to a new Neon branch/database, run migrations, compare workspace/share counts, update `DATABASE_URL`, and validate readiness. Derived analytical artifacts can be reconstructed from immutable source and curated releases; user workspace data cannot, so database backups are mandatory.

## Credential exposure

Revoke the credential at its provider first, rotate deployment/GitHub secrets, audit logs, redeploy, and invalidate affected sessions or share links. Never copy an exposed secret into an issue or incident document.
