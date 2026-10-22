# Data dictionary

| Entity | Purpose | Key fields |
|---|---|---|
| `objects` | Stable normalized object identity | `norad_id` (`BIGINT`), designator, source and normalized class, lifecycle |
| `object_aliases` | Reviewed cross-source names | source, alias, object, reviewed flag |
| `object_source_records` | Source-level provenance pointers | source, object, epoch, checksum, immutable raw key |
| `sources` | Attribution and access policy | homepage, license, attribution, restricted flag |
| `dataset_releases` | Atomic reproducible release | transform/classifier versions, checksums, quality statistics, manifest |
| `snapshots` | Validated temporal slice | date, resolution, counts, Parquet and Arrow keys |
| `environment_metrics` | Low-latency aggregate facts | snapshot, metric, dimension, value |
| `concentration_bins` | Altitude–inclination cells | bin boundaries, count, share, shell density |
| `events` | Authoritative fragmentation/collision event | date, source, type, cause, details |
| `event_objects` | Parent and fragment membership | event, object, role |
| `modeled_population_estimates` | Separate statistical debris context | source, date, size band, estimate, method note |
| `ingestion_runs` | Operational run ledger | job type, status, times, release, statistics, error |
| `data_quality_issues` | Quarantine and validation evidence | run, code, severity, object, message, raw pointer |
| `workspaces` | Private saved analytical state | Clerk owner, name, notes, JSON state |
| `workspace_shares` | Revocable unlisted read-only access | workspace, cryptographic token, revoked timestamp |

Every public analytical response contains `release_id`, generation time, data timestamp, freshness, citations, and known warnings. Production responses also record active filters and bin definitions where applicable.
