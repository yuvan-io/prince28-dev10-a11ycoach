# Engineering notes: A11yCoach


## D03 · PostgreSQL

### Migrations

Downgrade the GIN index migration:

```text
PS> uv run alembic downgrade -1
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running downgrade beb797f16c9b -> 281e2b8d6ab6, add metadata gin index
```

Upgrade to the latest migration:

```text
PS> uv run alembic upgrade head
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade 281e2b8d6ab6 -> beb797f16c9b, add metadata gin index
```

Current migration:

```text
beb797f16c9b (head)
```

Migration history:

```text
281e2b8d6ab6 -> beb797f16c9b (head), add metadata gin index
<base> -> 281e2b8d6ab6, create documents and pages
```

### Idempotent data loader

- Initial load: 20 inserted, 0 updated, 0 unchanged.
- Second load: 0 inserted, 0 updated, 20 unchanged.
- After modifying one record: 0 inserted, 1 updated, 19 unchanged.
- SHA-256 fingerprints are used to detect changes and avoid unnecessary updates.

### JSONB GIN index — EXPLAIN ANALYZE

Command:

```text
uv run python scripts/explain.py criterion_id 1.1.1
```

The script runs the same JSONB containment query twice.

**1. Normal PostgreSQL planner**

```text
Seq Scan on documents  (cost=0.00..1.25 rows=1 width=36) (actual time=0.016..0.021 rows=1.00 loops=1)
  Filter: (metadata @> '{"criterion_id": "1.1.1"}'::jsonb)
  Rows Removed by Filter: 19
  Buffers: shared hit=1
Planning:
  Buffers: shared hit=125 read=1
Planning Time: 1.213 ms
Execution Time: 0.044 ms
```

**2. With sequential scans disabled**

```text
Bitmap Heap Scan on documents  (cost=8.53..12.55 rows=1 width=36) (actual time=0.050..0.051 rows=1.00 loops=1)
  Recheck Cond: (metadata @> '{"criterion_id": "1.1.1"}'::jsonb)
  Heap Blocks: exact=1
  Buffers: shared hit=3
  ->  Bitmap Index Scan on ix_documents_metadata_gin  (cost=0.00..8.53 rows=1 width=0) (actual time=0.008..0.008 rows=1.00 loops=1)
        Index Cond: (metadata @> '{"criterion_id": "1.1.1"}'::jsonb)
        Index Searches: 1
        Buffers: shared hit=2
Planning:
  Buffers: shared hit=1
Planning Time: 0.103 ms
Execution Time: 0.087 ms
```

### EXPLAIN analysis

- The normal planner chose a sequential scan because the documents table contains only 20 rows. Scanning such a small table is estimated to be cheaper than using an index.
- With sequential scans disabled, PostgreSQL used the `ix_documents_metadata_gin` index through a Bitmap Index Scan.
- The filtered query returned one matching document.
- The GIN index is therefore available and usable for JSONB containment queries.
- The forced index plan took 0.087 ms compared with 0.044 ms for the sequential scan in this run. This is expected for a small table; the index can become more beneficial as the dataset grows.

## D04 · Docker and automated tests

### Docker image

- Added a multi-stage production Dockerfile.
- Runtime uses a non-root `app` user.
- Built image: `a11ycoach:dev`.
- Image disk usage: approximately 301 MB.

### Docker Compose

Services:
- PostgreSQL 17 with pgvector
- Redis 7
- Alembic migration service
- FastAPI application

Verification:
- PostgreSQL and Redis health checks passed.
- Migrations completed successfully.
- API health endpoint returned `status: ok`.
- API readiness endpoint returned `status: ready`, with database check passing.

### Automated tests

- Unit tests: 16 passed.
- Integration tests: 5 passed.
- Total: 21 passed.
- Integration coverage: 75%.
- Integration runner created a fresh temporary PostgreSQL database, applied migrations, ran tests, and removed the database.

### Quality checks

- `uv run poe lint`: passed.
- `uv run poe format`: completed.
- `uv run poe test`: passed.


## D05 · CI/CD and going live

- Live URL: https://a11ycoach.onrender.com
- CI workflow: https://github.com/yuvan-io/prince28-dev10-a11ycoach/actions
- Rollback CD run: https://github.com/yuvan-io/prince28-dev10-a11ycoach/actions/runs/45334610574
- Roll-forward CD run: https://github.com/yuvan-io/prince28-dev10-a11ycoach/actions/runs/45335950273

### Final deployment smoke test

```text
ok /health -> 200, version 73772f701384c232583338d819f0947a905b3aa6
ok /ready -> 200 {'status': 'ready', 'checks': {'database': True}}
ok /v1/documents?limit=1 -> 200
Smoke test passed
```

### Rollback drill

- Rolled back to SHA: `c00dd44245430730cf5020ba1f92b2356067120f`
- Rollback workflow: CD #8 — manually triggered, successful, 49 seconds.
- Rolled forward to SHA: `73772f701384c232583338d819f0947a905b3aa6`
- Roll-forward workflow: CD #9 — manually triggered, successful, 49 seconds.
- Both deployments passed the smoke test.

The database stayed on the newer schema because the manual rollback workflow skips migrations. No database downgrade was performed. The rollback candidate had the same database models and migration files as the current version, so the existing schema remained compatible with it.

### Where my secrets live

- Neon connection string: GitHub Secret `DATABASE_URL` and Render environment. Not committed to Git or included in the image.
- Render deploy hook: GitHub Secret `RENDER_DEPLOY_HOOK` only.

### Monitoring

- UptimeRobot monitor configured for `/health` at a 5-minute interval, with email alerts.
- The health endpoint supports both GET and HEAD requests.
- A periodic health check can help keep a sleeping Render instance warm and reduce cold-start delays.


### Kill and resume

- Run 1: I pressed Ctrl+C after 6 files.
- Run 2: downloaded=4 skipped=6.
- Run 3: downloaded=0 skipped=10.
- Remaining incomplete .part files: 0.
- The downloader resumed successfully without downloading
  previously completed documents again.

## D06 · Collecting the corpus

### Collection targets

- Start target: WCAG 2.2 and Understanding documents.
- Full target: 1,500+ pages, including techniques, failures and WAI-ARIA patterns.
- Start target achieved: 321 unique document paths.
- URL-downloaded documents: 10.
- Selected repository documents: 311.
- Selected corpus size: 1.74 MiB.
- Total raw directory size, including supporting assets: 6.41 MiB.
- Historical manifest records: 322.
- WCAG repository commit: 2766fae25f.

### Collection doors used

- Door 1 — URL list.
- Door 2 — Git repository.
- Door 3 — Sitemap: not required.
- Door 4 — Manual collection: not required.

### Licence and responsible collection

| Source | Licence | Collection method |
|---|---|---|
| W3C Understanding WCAG | W3C Document License | URL downloads |
| w3c/wcag | W3C Document License | Git repository |
| w3c/aria-practices | Pending verification | Planned |

- Respect robots.txt and source terms.
- Maximum concurrent URL requests: 4.
- Default request delay: 0.5 seconds.
- Do not bypass blocked requests.
- Retain copyright and attribution information.
- Cite and link to original documentation.
- No personal data is intentionally collected.

### Kill-and-resume experiment

| Run | Downloaded | Skipped |
|---|---:|---:|
| Run 1 — Interrupted | 6 | — |
| Run 2 — Resumed | 4 | 6 |
| Run 3 — Repeated | 0 | 10 |

- Remaining incomplete .part files: 0.
- Single-file recovery produced an additional manifest record for contrast-minimum-d64a389c.html.
- Repository repeat run: added=0 unchanged=311.
- The downloader successfully avoided unnecessary repeated downloads.

### Capacity estimates

- Current estimated tokens: 451,603.
- Average estimated tokens per document: 1,407.
- Full target: 1,500 pages.
- Projected tokens: 2,110,295.
- Projected chunks: 4,221.
- Raw vector payload: 24.73 MiB.
- Estimated one-time embedding cost: INR 3.80, using illustrative pricing assumptions.
- Tenfold growth vector payload: 247.32 MiB.
- Hosted PostgreSQL storage limit: pending confirmation.

### What surprised me

The selected corpus is only 1.74 MiB, even though the raw directory occupies 6.41 MiB. Supporting assets should not be counted as selected accessibility documents.

The estimated embedding cost is also relatively small compared with the importance of database capacity and retrieval performance.

### Problems encountered and fixes

- Asynchronous tests initially failed because pytest-asyncio was missing. Installed the dependency and configured asyncio_mode.
- Integration tests initially failed because PostgreSQL was not running. Started the database using Docker Compose.
- Downloaded documents appeared in Git status. Added data/raw/ to .gitignore.
- Markdown was accidentally pasted into dataset_report.py, causing a SyntaxError. Replaced it with a working Python report generator.
- Repository file counts differed because the checkout included supporting images, configuration files and other assets. Used unique manifest paths to measure the selected corpus.

### Verification

- Unit tests: 36 passed.
- Integration tests: 5 passed.
- Lint: passed.
- Dataset report generation: passed.
- Report regeneration: passed.
- Raw documents excluded from Git.
