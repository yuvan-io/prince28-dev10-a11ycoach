# Engineering notes: A11yCoach

## D03 Â· PostgreSQL

### Migrations (upgrade, downgrade, upgrade)

```text
[paste output of downgrade -1]

[paste output of current]

[paste output of upgrade head]

[paste output of history]
```

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
