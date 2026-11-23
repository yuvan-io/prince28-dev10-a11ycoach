# A11yCoach
[![CI](https://github.com/yuvan-io/prince28-dev10-a11ycoach/actions/workflows/ci.yml/badge.svg)](https://github.com/yuvan-io/prince28-dev10-a11ycoach/actions/workflows/ci.yml)
[![Live](https://img.shields.io/website?url=https%3A%2F%2Fa11ycoach.onrender.com%2Fhealth&label=live)](https://a11ycoach.onrender.com/docs)
[![Uptime (30 days)](https://img.shields.io/uptimerobot/ratio/[![CI](https://github.com/yuvan-io/prince28-dev10-a11ycoach/actions/workflows/ci.yml/badge.svg)](https://github.com/yuvan-io/prince28-dev10-a11ycoach/actions/workflows/ci.yml)
[![Live](https://img.shields.io/website?url=https%3A%2F%2Fa11ycoach.onrender.com%2Fhealth&label=live)](https://a11ycoach.onrender.com/docs)
[![Uptime (30 days)](https://img.shields.io/uptimerobot/ratio/YOUR-MONITOR-KEY)](https://a11ycoach.onrender.com/health)

**Live:** https://a11ycoach.onrender.com · [API docs](https://a11ycoach.onrender.com/docs) · [health](https://a11ycoach.onrender.com/health)
)](https://a11ycoach.onrender.com/health)

**Live:** https://a11ycoach.onrender.com · [API docs](https://a11ycoach.onrender.com/docs) · [health](https://a11ycoach.onrender.com/health)

An accessibility mentor that maps UI problems to WCAG 2.2 success criteria and provides actionable fixes based on W3C techniques and ARIA patterns.

**Status:** Day 4 — Dockerized FastAPI service, PostgreSQL migrations, Redis, and automated unit/integration tests.

## Who it's for

Frontend developers working on learning platforms, especially teams that need to make their applications accessible for government clients.

## The Problem

Developers often find accessibility issues in their web applications but struggle to identify the correct WCAG success criterion to follow. WCAG documentation is extensive, and finding the right technique or failure example takes time. This is especially challenging for developers working on educational platforms that must meet accessibility requirements for government clients. A11yCoach aims to simplify this process by mapping UI accessibility issues to relevant WCAG criteria and providing practical fixes based on trusted W3C documentation.

## Data sources

- WCAG 2.2 Recommendation
- Understanding WCAG
- W3C WCAG techniques and failures
- WAI-ARIA Authoring Practices

Links:

- https://www.w3.org/TR/WCAG22/
- https://github.com/w3c/wcag
- https://github.com/w3c/aria-practices

Content is referenced and linked according to the applicable W3C document license.

## Hardest problem

Mapping an accessibility issue to the correct success criterion, conformance level, and WCAG version. A criterion may have sufficient techniques, advisory techniques, and documented failures. The answer must distinguish these accurately rather than inventing a fix.

## Signature feature

**Issue Mapper:** A developer describes an accessibility issue or provides an HTML snippet, and A11yCoach suggests the relevant WCAG criterion, level, documented failure (if applicable), and a recommended fix.

## Target metric

Correctly map at least 85% of a test set of 50 accessibility issues to the correct criterion and conformance level.

## Run locally

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Docker Desktop with Docker Compose

### Run with Docker Compose

Create your local environment file:

```powershell
Copy-Item .env.example .env
```

Start the stack:

```bash
docker compose up --build -d
```

The stack includes:

- **PostgreSQL 17 with pgvector** — persistent database storage
- **Redis 7** — cache service
- **Migration service** — applies Alembic migrations before the API starts
- **FastAPI** — application API

Check service status:

```bash
docker compose ps
```

Check the API:

- Health: http://localhost:8000/health
- Readiness: http://localhost:8000/ready
- API documentation: http://localhost:8000/docs

Stop the stack:

```bash
docker compose down
```

To remove the persistent PostgreSQL volume as well:

```bash
docker compose down -v
```

### Run locally without Docker

Install dependencies:

```bash
uv sync
```

Create `.env` from `.env.example` and configure `DATABASE_URL` to point to a running PostgreSQL database.

Run the API:

```bash
uv run uvicorn a11ycoach.api.main:create_app --factory --reload
```

## Tests and quality checks

Run unit tests:

```bash
uv run poe test-unit
```

Run integration tests against a fresh temporary PostgreSQL database:

```bash
uv run poe test-integration
```

Run both suites:

```bash
uv run poe test
```

Run linting and formatting:

```bash
uv run poe lint
uv run poe format
```

Integration tests require Docker Compose's PostgreSQL service to be running and accessible at `localhost:5432`.

The integration test runner creates a uniquely named temporary database, applies migrations, runs the integration suite, and drops the temporary database afterward.
