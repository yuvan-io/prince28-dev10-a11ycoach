# A11yCoach Ingestion Report

<!-- generated:start -->

Updated: 2026-11-27 10:05 UTC

## Corpus statistics

| Metric | Actual |
|---|---:|
| Documents | 321 |
| Pages | 497 |
| Text characters | 751,098 |
| Tokens of text (estimated) | 187,775 |
| Average tokens per page | 377.8 |
| Parse failures | 0 |

## Ingestion statistics

| Metric | Count |
|---|---:|
| Ingestion jobs | 5 |
| Done | 57 |
| Skipped | 2 |
| Failed | 5 |
| Queued | 0 |
| Running | 0 |

## Dead-letter list

| Failure stage | Items |
|---|---:|
| Gave up after retries | 5 |

**Method:** Approximately four text characters per token.

Ingestion statistics include historical attempts.
Dead-letter counts include historical failed items,
even when a later retry succeeds.

<!-- generated:end -->

## What I learnt

- I learnt how Redis and ARQ allow the API to accept ingestion requests immediately while a background worker processes documents separately.
- I learnt that storing job status and attempts in PostgreSQL allows interrupted jobs to recover after a worker crash without duplicating documents.
- I learnt how LLM rate limits affect ingestion speed and how retries, pacing and dead-letter lists help handle failures safely.
