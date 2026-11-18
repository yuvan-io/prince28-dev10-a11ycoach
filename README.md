# A11yCoach

An accessibility mentor that maps UI problems to WCAG 2.2 success criteria and provides actionable fixes based on W3C techniques and ARIA patterns.

**Status:** Day 1 foundation — Python package, FastAPI skeleton, quality gates, and tests.

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

```bash
uv sync
cp .env.example .env
uv run uvicorn a11ycoach.api.main:create_app --factory --reload
```

On Windows PowerShell, use:

```powershell
Copy-Item .env.example .env
```

Then open http://localhost:8000/docs

## Checks

```bash
uv run pytest
uv run ruff check .
```
