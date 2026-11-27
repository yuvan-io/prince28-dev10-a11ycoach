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

## D07 · Parser comparison

<!-- parsers:start -->
| File | Parsers (A / B) | Pages | A found | B found | Time (A / B) | Better, why |
|---|---|---|---|---|---|---|
| contrast-minimum-d64a389c.html | trafilatura / strip tags | 8 | 27,158 chars, 19 headings, 0 tables | 32,720 chars, 0 headings, 0 tables | 0.05 s / 0.01 s | A preferred: preserves 19 headings and extracts 5,562 fewer characters. |
| non-text-content-62581aaa.html | trafilatura / strip tags | 9 | 24,946 chars, 22 headings, 0 tables | 33,187 chars, 0 headings, 0 tables | 0.05 s / 0.01 s | A preferred: preserves 22 headings and extracts 8,241 fewer characters. |
| conformance.html | trafilatura / strip tags | 15 | 38,302 chars, 0 headings, 0 tables | 47,293 chars, 0 headings, 0 tables | 0.06 s / 0.01 s | A extracts 8,991 fewer characters, but neither preserves headings. Manual verification needed. |
| name-role-value-e80095ed.html | trafilatura / strip tags | 5 | 16,903 chars, 16 headings, 0 tables | 24,297 chars, 0 headings, 0 tables | 0.05 s / 0.01 s | A preferred: preserves 16 headings and extracts 7,394 fewer characters. |
| index.html | trafilatura / strip tags | 10 | 26,247 chars, 0 headings, 0 tables | 29,812 chars, 0 headings, 0 tables | 0.05 s / 0.01 s | A extracts 3,565 fewer characters, but neither preserves headings. Manual verification needed. |
| status-messages-0165f144.html | trafilatura / strip tags | 7 | 18,987 chars, 22 headings, 0 tables | 24,741 chars, 0 headings, 0 tables | 0.04 s / 0.01 s | A preferred: preserves 22 headings and extracts 5,754 fewer characters. |
| info-and-relationships-786aa31b.html | trafilatura / strip tags | 5 | 12,288 chars, 15 headings, 0 tables | 20,244 chars, 0 headings, 0 tables | 0.03 s / 0.01 s | A preferred: preserves 15 headings and extracts 7,956 fewer characters. |
| error-identification-dc4f1afa.html | trafilatura / strip tags | 5 | 15,702 chars, 14 headings, 0 tables | 21,203 chars, 0 headings, 0 tables | 0.04 s / 0.00 s | A preferred: preserves 14 headings despite slower extraction. |
| labels-or-instructions-2d139424.html | trafilatura / strip tags | 6 | 15,575 chars, 11 headings, 0 tables | 21,481 chars, 0 headings, 0 tables | 0.03 s / 0.00 s | A preferred: preserves 11 headings and extracts 5,906 fewer characters. |
| non-text-contrast.html | trafilatura / strip tags | 8 | 21,301 chars, 0 headings, 0 tables | 36,800 chars, 0 headings, 0 tables | 0.04 s / 0.01 s | A extracts 15,499 fewer characters, but neither preserves headings. Manual verification needed. |
<!-- parsers:end -->

### Parser comparison findings

- All 10 selected documents were HTML files.
- Trafilatura extracted 217,409 characters compared with 291,778 using strip tags.
- Trafilatura extracted approximately 25.49% fewer characters.
- Trafilatura detected 119 headings, while strip tags detected none.
- Strip tags was faster, but Trafilatura provided better structural information.
- Neither parser detected tables in the selected documents.
- Three documents had no detected headings with either parser.
- No PDF files were included in this comparison, so no corpus-based PDF parser performance conclusion can be made.
- Trafilatura is the preferred HTML parser for A11yCoach based on structural preservation, subject to manual content verification.

### Parsed page quality observations

- Understanding SC 1.1.1 Non-text Content, page 2, correctly retained the heading path: Understanding SC 1.1.1 Non-text Content (Level A) → Intent → Note on CAPTCHA.
- Understanding SC 1.4.3 Contrast (Minimum), page 2, correctly retained the document title and Intent heading.
- Technical information such as contrast ratios, font sizes, CAPTCHA requirements and text alternatives was preserved.
- Three of the five sampled pages had empty heading paths.
- Some extracted content contained awkward line breaks and escaped citation markers.
- No obvious navigation or footer junk was visible in the sampled text.
- No tables were detected in the ten compared HTML documents. Table extraction was verified through unit testing, but not through these corpus samples.
- Trafilatura is preferred for HTML because it preserves more structural information than plain tag stripping.

### D07 · Parsing my corpus

- Files in the manifest: 321 · parsed: 321 · failed: 0 · pages generated: 497.
- Parsing coverage: 100%.
- Initial sample: 20 files, 78 pages, 9.1 seconds.
- Full parsing run: 299 additional files, 417 pages, 104.7 seconds.
- Idempotency check: 0 new pages, 1.0 second.
- Failure recovery: 2 files, 2 pages, 1.6 seconds.

### Failures by reason

| Reason | Initial failures | Remaining failures | What I did |
|---|---:|---:|---|
| empty | 2 | 0 | Removed the minimum 40-character restriction for HTML content while retaining empty-content validation. |
| Total | 2 | 0 | Successfully retried both files. |

- The files I fixed: `blocks-of-text.html` and `prerecorded.html`.
- Reason: Valid WCAG glossary definitions were incorrectly classified as empty because they contained fewer than 40 characters.
- Fix: Updated the HTML parser to accept short, non-empty content.
- Result: Both files were successfully recovered without modifying the original source documents.

### What I saw when I read my parsed pages

- A page where the heading path is right: Understanding SC 1.1.1 Non-text Content (Level A), page 2.
- Heading path: Document title → Intent → Note on CAPTCHA.
- Something that came out wrong: Conformance, page 2, had an empty heading path. Some documents also contained awkward line breaks and escaped citation markers.
- Seven sampled WCAG source fragments retained file paths instead of human-readable document titles.
- No obvious menu or footer junk was visible in the sampled pages.
- A table: Markdown table extraction passed unit testing. No tables were detected in the ten compared HTML documents.

### My parser choice

- For HTML, I use Trafilatura because it detected 119 headings across ten documents, compared with zero using plain tag stripping.
- Trafilatura provides better structural information despite being slower.
- For PDFs, PyMuPDF remains the implementation choice because it supports page structure and table extraction. PDF parser functionality was verified through unit tests, but no PDFs were included in the ten-file corpus comparison.
- A kind of document that neither HTML parser handles well: repository HTML fragments where heading structure is not preserved.

### One thing that went wrong today, and how I fixed it

- Two valid WCAG glossary definitions were incorrectly rejected because their extracted text was shorter than 40 characters. I corrected the validation condition and successfully retried both files.
- The Windows pytest launcher encountered a script path issue. I used `uv run python -m pytest` instead.
- Integration tests initially lacked the integration marker. Adding the marker allowed them to run in the isolated integration test environment.

### Verification

- Initial unit test suite: 52 passed.
- Integration tests: 8 passed.
- Parser tests after failure recovery: 16 passed.
- Lint: passed.
- Parsing coverage: 100%.
- Idempotency: passed before failure recovery.
- Parser comparison: 10 HTML files.
- Manual source inspection: completed.

## D08 · LLM gateway

### Provider configuration

- Primary provider: Gemini.
- Primary model: `gemini-3.8-flash`.
- Fallback provider: Groq.
- Fallback model: `openai/gpt-oss-20b`.
- Both providers use OpenAI-compatible API endpoints.
- Provider names, models, API URLs and timeout values are configurable.
- API keys are stored in environment variables, not in source code.
- Automated tests use FakeLLM without requiring real API keys.

### LLM gateway implementation

- Implemented a common gateway for both LLM providers.
- Added streaming and non-streaming response support.
- Implemented automatic retry for retryable provider errors.
- Implemented automatic fallback when the primary provider fails.
- Maximum generation attempts per provider: 2.
- Circuit breaker failure threshold: 3.
- Circuit breaker cooldown: 30 seconds.
- Streaming fallback is allowed only before the first response chunk.
- Added token usage, latency and estimated cost tracking.
- Added request ID tracking for provider calls.
- Added a versioned system prompt: `prompts/chat_system_v1.md`.

### Database migration

- Migration: `3a3eb8fbe41b_add_llm_calls.py`.
- Created the `llm_calls` table.
- Added indexes for request_id and created_at.
- Recorded provider, model, purpose, prompt version, status,
  errors, input tokens, output tokens, latency, estimated cost
  and fallback usage.
- Stored estimated cost using Numeric(12, 6).
- Migration applied successfully.

### API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | /v1/chat | Generate streaming or non-streaming AI responses |
| GET | /v1/usage | Retrieve aggregated LLM usage and estimated cost |

- Streaming responses use Server-Sent Events (SSE).
- Non-streaming responses return JSON.
- Usage data is retrieved from PostgreSQL.

### First real LLM response on my laptop

Question:

"What does success criterion 1.4.3 Contrast (Minimum) require?"

- Provider: Groq.
- Model: `openai/gpt-oss-20b`.
- Automatic fallback: YES.

| Metric | Streaming | Non-streaming |
|---|---:|---:|
| Time to first words | 7.37 s | Not applicable |
| Total response time | 7.83 s | 34.65 s |
| Input tokens | 262 | 262 |
| Output tokens | 286 | 733 |
| Estimated cost (INR) | 0.010018 | 0.022757 |
| Attempts reported | 1 | 1 |
| Fallback used | Yes | Yes |

Observations:

- Both streaming and non-streaming requests returned real AI responses.
- Streaming allowed the answer to appear before generation completed.
- Automatic fallback to Groq worked successfully.
- The streaming response arrived faster than the non-streaming response in this experiment.
- The two responses generated different numbers of output tokens, so their timings are not a controlled performance comparison.
- Gemini also successfully answered a later "Hi" request.
- Gemini's successful request required two attempts and took 22.56 seconds.
- Gemini input tokens: 187.
- Gemini output tokens: 67.
- Gemini estimated cost: INR 0.037192.
- Gemini fallback used: No.

### Performance against Day 1 targets

| Target | Observed result | Status |
|---|---|---|
| First words under 1.5 seconds | 7.37 seconds locally | Not met |
| Average estimated cost under INR 0.50 | Approximately INR 0.00842 | Met in local tests |
| Live streaming response | Pending deployment | Pending |
| Live warm-request latency | Pending measurement | Pending |

The first-word latency target was not achieved locally.
Primary-provider failures and fallback may have contributed
to the end-to-end delay.

### Tokens: English against Tamil

The same provider and model were used for all three measurements.

- Provider: Groq.
- Model: `openai/gpt-oss-20b`.

| Message | Input tokens |
|---|---:|
| Hi (baseline) | 247 |
| Explain in one sentence what a refund is. | 255 |
| பணத்தைத் திரும்பப் பெறுதல் என்றால் என்ன என்பதை ஒரே வாக்கியத்தில் விளக்கவும். | 269 |

Calculation:

- Baseline-adjusted English tokens: 255 - 247 = 8.
- Baseline-adjusted Tamil tokens: 269 - 247 = 22.
- Tamil-to-English ratio: 22 / 8 = 2.75.

Observation:

Tamil required approximately 2.75 times as many
baseline-adjusted input tokens as English for the tested
sentences.

The result is specific to these sentences and this model.
The baseline includes the short "Hi" message, so the ratio
is an approximation.

Both questions were rejected as outside A11yCoach's subject.
The Tamil question received a response in English.

### What the model does without my documents

The current model answers from general knowledge.
The collected WCAG documents are not yet connected to
the LLM through retrieval.

#### Question 6 — Legal compliance

Question:

"Is our website legally compliant in India?"

Observations:

- The model expressed uncertainty about whether the website
  was legally compliant.
- It indicated that an accessibility assessment or audit
  would be necessary.
- It also made legal references that were not independently
  verified.
- The response cannot establish whether a particular website
  is legally compliant.
- Legal compliance requires evidence about the actual website
  and applicable legal requirements.

Measurements:

- Provider: Groq.
- Fallback used: Yes.
- Total response time: 11.82 seconds.
- Input tokens: 254.
- Output tokens: 325.
- Estimated cost: INR 0.011072.

The exact response wording was not retained in these notes.
The observations above are a summary, not a verbatim quote.

#### Off-topic question

Question:

"Who won the 2011 cricket world cup?"

Observations:

- The model declined to answer the off-topic question.
- It recognized that cricket was outside A11yCoach's
  accessibility-related subject.
- The subject restriction in the system prompt worked
  for this request.

Measurements:

- Provider: Groq.
- Fallback used: Yes.
- Total response time: 3.03 seconds.
- Input tokens: 256.
- Output tokens: 97.
- Estimated cost: INR 0.004588.

### Known-answer accuracy tests

#### Test 1 — WCAG 2.2 SC 1.4.3 Contrast (Minimum)

Result: Partially correct.

What the model got right:

- Normal text requires a minimum contrast ratio of 4.5:1.
- Large-scale text requires a minimum contrast ratio of 3:1.

What the model got wrong:

- The streaming response incorrectly used pixels instead
  of points for the large-scale text thresholds.
- Both responses incorrectly included non-text UI components
  under SC 1.4.3.

Correct information:

- Large-scale text is generally at least 18 points,
  or 14 points when bold, or an equivalent size.
- SC 1.4.3 applies to text and images of text,
  subject to its stated exceptions.
- Non-text UI component contrast is addressed separately
  by SC 1.4.11 Non-text Contrast.

Reference:
https://www.w3.org/TR/WCAG22/#contrast-minimum

#### Test 2 — WCAG 2.2 SC 2.1.1 Keyboard

Question:

"What does WCAG 2.2 success criterion 2.1.1 Keyboard require?"

Result: Partially correct.

- The model correctly explained keyboard operability.
- It omitted the requirement concerning specific timings
  for individual keystrokes.
- It omitted the exception for functions that depend on
  the path of movement rather than only the endpoints.
- It mixed focus order requirements from SC 2.4.3.

Measurements:

- Provider: Groq.
- Fallback used: Yes.
- Total response time: 10.77 seconds.
- Input tokens: 265.
- Output tokens: 213.
- Estimated cost: INR 0.007959.

Reference:
https://www.w3.org/TR/WCAG22/#keyboard

#### Test 3 — WCAG 2.2 SC 2.5.8 Target Size (Minimum)

Question:

"What is the minimum target size required by WCAG 2.2
success criterion 2.5.8?"

Result: Incorrect.

- Model answer: 44 x 44 CSS pixels.
- Correct answer: 24 x 24 CSS pixels, subject to exceptions.
- The model confused SC 2.5.8 Target Size (Minimum),
  Level AA, with SC 2.5.5 Target Size (Enhanced),
  Level AAA.

Measurements:

- Provider: Groq.
- Fallback used: Yes.
- Total response time: 3.19 seconds.
- Input tokens: 269.
- Output tokens: 334.
- Estimated cost: INR 0.011436.

Reference:
https://www.w3.org/TR/WCAG22/#target-size-minimum

### Accuracy findings

- The model can provide useful general accessibility guidance.
- It can also produce confident but incorrect technical details.
- A correct criterion number does not guarantee a correct explanation.
- Related WCAG success criteria can be confused with one another.
- The system prompt alone does not guarantee factual accuracy.
- Retrieval-Augmented Generation (RAG) using authoritative
  W3C documents is needed to improve grounding and accuracy.
- Retrieved answers will still require evaluation.

### Fallback and circuit breaker

Experiment:

- Temporarily changed LLM_PRIMARY_MODEL to
  `gemini-no-such-model`.
- Restarted the application.
- Sent multiple requests to deliberately trigger
  primary-provider failure.

Observed database records:

| Time (UTC) | Gemini | Groq |
|---|---|---|
| 09:56:22 | HTTP 404 | Success |
| 09:56:26 | HTTP 404 | Success |
| 09:56:30 | HTTP 404 | Success |
| 09:56:49 | No recorded call | Success |
| 09:56:53 | No recorded call | Success |
| 09:56:56 | No recorded call | Success |
| 09:56:59 | No recorded call | Success |
| 10:00:05 | HTTP 404 | Success |

Observations:

- Gemini returned HTTP 404 for three consecutive recorded failures.
- The next four requests were handled successfully by Groq
  without additional recorded Gemini calls.
- The fourth request after the initial three-failure sequence
  began was the first observed request without a Gemini call.
- This behaviour is consistent with the circuit breaker
  opening after three failures.
- A subsequent Gemini attempt after the cooldown returned
  HTTP 404, followed by successful Groq fallback.
- This is consistent with a half-open probe.
- Circuit breaker state transitions were inferred from
  database records rather than explicit state-transition logs.

#### Four consecutive fallback requests

| Request | Provider | Fallback | Total time (s) | Cost (INR) |
|---|---|---|---:|---:|
| 1 | Groq | Yes | 2.72 | 0.003983 |
| 2 | Groq | Yes | 2.92 | 0.005037 |
| 3 | Groq | Yes | 2.66 | 0.004895 |
| 4 | Groq | Yes | 2.93 | 0.003954 |

- Successful requests: 4/4.
- Success rate: 100% for these four requests.
- Average end-to-end latency: 2.81 seconds.
- Total estimated cost: INR 0.017869.
- Time to first words: Not measured because these requests
  used non-streaming JSON responses.

#### Restoration

- Restored LLM_PRIMARY_MODEL to `gemini-3.8-flash`.
- Restarted the application successfully.
- A successful Gemini response was observed earlier in
  the day's experiments.
- Successful Gemini generation after the final restoration
  remains to be verified.

Conclusion:

A11yCoach continued answering requests despite deliberate
primary-provider failure.

### The bill — Usage endpoint verification

Endpoint:

GET /v1/usage?days=7

Date: 2026-11-25.

| Metric | Result |
|---|---:|
| Recorded provider calls | 29 |
| Provider errors | 11 |
| Successful provider calls | 18 |
| Fallbacks | 17 |
| Input tokens | 4502 |
| Output tokens | 3000 |
| Total tokens | 7502 |
| Total estimated cost (INR) | 0.1515 |

Average estimated cost per successful recorded call:

- INR 0.1515 / 18 = approximately INR 0.00842.
- Day 1 target: under INR 0.50.
- Result: Target met in the observed local experiments.

Observations:

- The usage endpoint successfully aggregated LLM call
  records from PostgreSQL.
- Provider errors included deliberately introduced failures.
- A provider error does not necessarily mean a user request failed.
- Automatic fallback allowed requests to complete despite
  primary-provider errors.
- The recorded cost is an estimate based on configured
  model prices, not an actual provider invoice.
- The average uses successful recorded provider calls
  as a proxy for answered questions.

### Database verification

Verified the llm_calls table using the Neon SQL Editor.

```sql
SELECT
    created_at,
    provider,
    model,
    status,
    LEFT(error, 40) AS error,
    tokens_in,
    tokens_out,
    latency_ms,
    cost_inr,
    fallback_used
FROM llm_calls
ORDER BY id DESC
LIMIT 15;
```

Results:

- Successful Groq calls were recorded.
- Gemini HTTP 404 errors were recorded.
- Gemini HTTP 429 rate-limit errors were recorded.
- Input and output token counts were recorded.
- Successful provider latency was recorded.
- Estimated costs were recorded.
- Fallback flags were recorded.
- Failed provider calls recorded zero tokens and zero latency.

Limitations:

- Failed-call latency is not accurately represented because
  the recorded latency is zero.
- Zero estimated cost for a failed call does not independently
  establish that the provider charged nothing.
- The gateway records provider outcomes, which may not
  represent every individual internal retry.

### Docker and deployment preparation

- Updated the existing multi-stage Dockerfile.
- Added the prompts folder to the builder stage.
- Added the prompts folder to the production runtime stage.
- Verified that prompts/chat_system_v1.md exists.
- Verified that .dockerignore does not exclude the prompts folder.
- Verified that .env is excluded from the Docker build context.
- Verified that .env does not appear in Git status.
- Confirmed that the new migration and prompt files
  appear in Git status.

Dockerfile additions:

Builder stage:

```dockerfile
COPY prompts/ ./prompts/
```

Runtime stage:

```dockerfile
COPY --from=builder --chown=app:app /app/prompts ./prompts
```

The actual updated Docker image build and production
deployment remain to be verified.

### Where my LLM secrets belong

- GEMINI_API_KEY: Local .env and Render environment.
- GROQ_API_KEY: Local .env and Render environment.
- .env.example: Empty API key placeholders only.
- Real LLM API keys must not be committed to Git.
- GitHub Actions does not require real LLM API keys
  because automated tests use FakeLLM.
- Exposed credentials must be rotated before deployment.

### Problems encountered and how I fixed them

#### 1. Gemini provider availability

Problem:

Gemini returned a timeout, HTTP 503 and HTTP 429
during the experiments.

Resolution:

- Used the gateway's retry and fallback mechanisms.
- Groq successfully handled requests when Gemini failed.
- Gemini successfully answered a later request.

#### 2. Windows pytest launcher

Problem:

The Windows pytest launcher encountered a script
execution issue.

Resolution:

Used:

```powershell
uv run python -m pytest
```

#### 3. Incorrect middleware import

Problem:

The application imported request_context instead of
the existing request_context_middleware function.

Resolution:

Corrected the middleware import and registration
in api/main.py.

#### 4. Test fixture document IDs

Problem:

Existing tests expected document IDs such as DOC-001,
but the modified fixtures used IDs such as 001.

Resolution:

Restored the expected DOC-prefixed document IDs.

#### 5. Missing integration test marker

Problem:

The LLM call integration test was not correctly
classified as an integration test.

Resolution:

Added the pytest integration marker and used the
existing isolated integration test runner.

#### 6. Ruff import formatting

Problem:

Ruff reported import ordering violations.

Resolution:

Corrected the import ordering and reran the lint checks.
All checks passed.

#### 7. Missing development task

Problem:

The trainer's command uv run poe dev did not work
because the project does not define a dev task.

Resolution:

Started the application directly using:

```powershell
uv run python -m uvicorn a11ycoach.api.main:create_app --factory --reload --host 127.0.0.1 --port 8000
```

### Final local verification

| Check | Result |
|---|---|
| Unit tests | 79 passed |
| Integration tests | 9 passed |
| Total tests | 88 passed |
| Database migrations | All 4 applied successfully |
| Integration-only coverage | 47% |
| Ruff lint | Passed |
| Streaming chat | Passed |
| Non-streaming chat | Passed |
| Groq fallback | Passed |
| Gemini generation | Observed successfully |
| Circuit breaker | Behaviour consistent with expected design |
| Cooldown retry | Observed |
| LLM call recording | Passed |
| Usage endpoint | Passed |
| Prompt file verification | Passed |
| Dockerfile changes | Verified |
| Production Docker build | Pending |

The trainer's reference suite expects 89 tests.
My current implementation contains 88 passing tests.
The one-test difference has not yet been investigated.

### Live deployment verification

- Live URL: https://a11ycoach.onrender.com
- Feature branch: feat/day-08-llm-gateway
- Credential rotation: Awaiting confirmation.
- Render environment configuration: Awaiting confirmation.
- Commit: Pending.
- Pull request: Pending.
- CI: Pending.
- Merge: Pending.
- CD deployment: Pending.
- Live health endpoint: Pending Day 8 verification.
- Live readiness endpoint: Pending Day 8 verification.
- Live streaming chat: Pending.
- Live usage endpoint: Pending.
- Live warm-request first-word latency: Pending.
- Day 1 first-word latency target: Under 1.5 seconds.

Live test command:

```powershell
uv run python scripts/ask.py "What does success criterion 1.4.3 Contrast (Minimum) require?" --url https://a11ycoach.onrender.com
```

Run the command twice after deployment and record
the second, warm-request measurements.

- Live provider: Pending.
- Live model: Pending.
- Fallback used: Pending.
- First words after: Pending.
- Total response time: Pending.
- Input tokens: Pending.
- Output tokens: Pending.
- Estimated cost: Pending.

Live usage endpoint:

https://a11ycoach.onrender.com/v1/usage

### What I learned today

- An LLM integration is fundamentally an HTTP API integration.
- A gateway separates application logic from provider-specific logic.
- Retry handles temporary failures.
- Fallback provides an alternative when the primary provider fails.
- A circuit breaker avoids repeatedly calling an unhealthy provider.
- Streaming can improve perceived responsiveness.
- Token consumption varies across languages and models.
- LLM usage and estimated costs should be measured.
- Passing software tests does not guarantee factual accuracy
  in AI-generated answers.
- Authoritative document retrieval is important for reliable
  accessibility guidance.

### Day 8 status

- Milestone 1 — Two LLM providers: Completed.
- Milestone 2 — LLM calls database table: Completed.
- Milestone 3 — LLM gateway: Completed.
- Milestone 4 — Chat and usage endpoints: Completed.
- Milestone 5 — Break it on purpose: Completed, with
  post-restoration Gemini verification still pending.
- Milestone 6 — Ship and deploy: In progress.

## D09 · Prompts and structured output

### Objectives

- Implement versioned prompts.
- Build a question classifier for A11yCoach.
- Evaluate classifier accuracy using a labelled test set.
- Compare prompt versions and improve classification accuracy.
- Define a structured metadata contract using Pydantic.
- Extract and validate document metadata using an LLM.
- Store extracted metadata in PostgreSQL.
- Support automatic repair, resumability and prompt versioning.
- Verify metadata filtering through the API.

### Prompt versions compared

<!-- prompts:start -->

| Prompt version | Correct | Accuracy | Invalid replies | Avg tokens in |
|---|---|---|---|---|
| classify_v1 | 12/20 | 60% | 1 | 111 |
| classify_v2 | 19/20 | 95% | 0 | 284 |
| classify_v3 | 19/20 | 95% | 0 | 410 |
| classify_v4 | 20/20 | 100% | 0 | 310 |

<!-- prompts:end -->

### Question router

The question router classifies user questions into three categories:

- docs: Questions that can be answered using A11yCoach's
  accessibility documents.
- personal: Questions requiring private information,
  live information or evidence about a specific situation.
- off_topic: Questions unrelated to accessibility.

The classifier uses temperature 0 to reduce unnecessary
variation in its responses.

User questions are enclosed in question tags and treated
as data rather than instructions.

### Evaluation dataset

- Dataset: eval/prompt_testset.jsonl.
- Total labelled questions: 20.
- Documentation questions: 9.
- Personal questions: 6.
- Off-topic questions: 5.
- Includes a prompt injection attempt.
- Includes an intentionally unanswerable private policy question.
- No TODO placeholders remain.
- Labels changed after seeing the evaluation results: None.
- Independent classmate review: Not yet confirmed.

The generated evaluation cache is excluded from Git
through the eval/cache/ entry in .gitignore.

### Prompt evaluation findings

- classify_v1 achieved 12/20 (60%).
- classify_v2 achieved 19/20 (95%).
- classify_v3 achieved 19/20 (95%).
- classify_v4 achieved 20/20 (100%).

Both v2 and v3 incorrectly classified the question:

"Is our website legally compliant in India?"

Expected label: personal.

Predicted label: off_topic.

I selected v2 as the base for v4 because v2 and v3
achieved the same accuracy, while v2 required fewer
input tokens.

In v4, I improved the personal label definition to
explicitly include website-specific legal compliance,
audit outcomes, accessibility status and certification
questions that require evidence about a particular website.

This change resolved the remaining classification error.

Additional observations:

- v4 correctly classified the prompt injection attempt.
- v4 correctly classified the private EduApp policy question.
- No LEAK warnings were reported.
- The initial comparison made 56 new model calls
  and reused 4 cached answers.
- The second comparison made 20 new model calls
  and reused 60 cached answers.
- Total new model calls across both comparisons: 76.
- All 26 classifier and gateway unit tests passed.

### My best router prompt

- Selected prompt: classify_v4.
- Correct classifications: 20/20.
- Accuracy: 100%.
- Invalid replies: 0.
- Average input tokens: 310.
- Questions my best version still gets wrong:
  None on the current development test set.

### Is the extra accuracy worth the tokens?

| Metric | v1 | v4 |
|---|---:|---:|
| Accuracy | 60% | 100% |
| Correct classifications | 12 | 20 |
| Invalid replies | 1 | 0 |
| Average input tokens | 111 | 310 |

- Accuracy improved by 40 percentage points.
- Average input tokens increased by 199 compared with v1.
- v4 uses approximately 24.39% fewer input tokens than v3.
- v4 provides better classification accuracy than v3
  while requiring fewer input tokens.

The additional input tokens are justified by the improvement
in classification accuracy on the current evaluation dataset.

Limitation:

The 100% accuracy was measured on a small development
dataset used to refine the prompt. It does not establish
100% accuracy on unseen questions.

A separate evaluation dataset is required to measure
generalisation performance.

### My contract (DocMeta)

Implemented a Pydantic model in:

src/a11ycoach/llm/doc_meta.py

The metadata contract contains ten fields.

| Field | Purpose |
|---|---|
| doc_kind | Document category |
| year | Publication or effective year |
| language | Main document language |
| summary | Short document description |
| topics | Main accessibility topics |
| criterion_id | WCAG success criterion identifiers |
| level | WCAG conformance levels |
| wcag_version | Relevant WCAG versions |
| technique_id | W3C technique or failure identifiers |
| technique_type | Technique or failure categories |

Common fields retained:

- doc_kind
- year
- language
- summary
- topics

Domain-specific fields retained:

- criterion_id
- level
- wcag_version
- technique_id
- technique_type

Fields deleted: None.

All five domain-specific fields are relevant to A11yCoach.

Field tightened:

The level field accepts only the following values:

- A
- AA
- AAA

Validation rules:

- Unexpected fields are rejected.
- Publication year must be between 1950 and 2027,
  or null when unavailable.
- Language must be en, ta, hi or other.
- Summary length must be between 20 and 300 characters.
- Topics must contain between 1 and 6 values.
- Domain-specific lists contain at most 8 values.
- Short string values contain at most 80 characters.
- Topics are converted to lowercase and deduplicated.
- Missing domain-specific information is represented
  using empty lists.

### Structured extraction engine

Implemented in:

src/a11ycoach/llm/extract.py

Features:

- Uses a versioned extraction prompt.
- Includes the Pydantic JSON schema in the model instructions.
- Supports optional native JSON schema output.
- Parses JSON from the model response.
- Validates extracted metadata using Pydantic.
- Automatically requests corrections for invalid responses.
- Allows up to three extraction attempts.
- Records extraction prompt version, model and attempt count.
- Records validation errors when extraction fails.
- Preserves existing parser metadata.
- Stores extraction results in PostgreSQL JSONB metadata.
- Commits results after each processed document.
- Skips documents already processed by the selected prompt.
- Supports retrying failed extractions.
- Supports re-extraction when the prompt version changes.
- Stops gracefully when all LLM providers are unavailable.

The extraction engine reads up to the first three parsed
pages of each document, limited to 6,000 characters by default.

This reduces input token consumption but may omit relevant
information located later in a document.

### Extraction CLI

Implemented in:

scripts/extract_metadata.py

Supported options:

| Option | Purpose |
|---|---|
| --limit | Limit the number of documents processed |
| --rpm | Control the document processing rate |
| --chars | Set the maximum input character count |
| --retry-failed | Retry previously failed extractions |
| --schema | Request native JSON schema output |

The CLI reports:

- Prompt version.
- Pending documents.
- Successful extractions.
- Repaired responses.
- Failed extractions.
- Input tokens.
- Output tokens.
- Estimated cost.
- Total duration.

### Metadata extraction trial — v1

Command:

```powershell
uv run python scripts/extract_metadata.py --limit 5
```

Results:

| Metric | Result |
|---|---:|
| Prompt version | extract_v1 |
| Documents processed | 5 |
| Successful extractions | 5 |
| Repaired responses | 0 |
| Failed extractions | 0 |
| Input tokens | 10,312 |
| Output tokens | 3,661 |
| Estimated cost (INR) | 0.1778 |
| Duration | 56 seconds |

Observed problem:

W3C Understanding documents were inconsistently classified
as guideline, rule and tutorial despite belonging to
the same document family.

WCAG version formatting was also inconsistent.

Improvement:

Created extract_v2 to improve document category consistency,
WCAG version formatting and identifier formatting.

The original extract_v1 prompt was retained for reproducibility.

### Metadata extraction trial — v2

Command:

```powershell
uv run python scripts/extract_metadata.py --limit 5
```

Results:

| Metric | Result |
|---|---:|
| Prompt version | extract_v2 |
| Documents processed | 5 |
| Successful extractions | 5 |
| Repaired responses | 0 |
| Failed extractions | 0 |
| Input tokens | 11,062 |
| Output tokens | 3,634 |
| Estimated cost (INR) | 0.1824 |
| Duration | 44 seconds |

Improvements:

- All five sampled W3C Understanding documents were
  consistently classified as reference.
- Populated WCAG version values used numeric strings.
- Criterion identifiers used the expected numeric format.
- Conformance levels used valid A or AA values.
- All five records passed Pydantic validation.
- All five records were stored successfully in PostgreSQL.

### Manual source verification

The following two original W3C documents were inspected
against their extracted metadata:

1. Understanding SC 2.1.1 Keyboard.
2. Understanding SC 2.4.7 Focus Visible.

| Document | Expected criterion | Extracted criterion | Expected level | Extracted level |
|---|---|---|---|---|
| Keyboard | 2.1.1 | 2.1.1 | A | A |
| Focus Visible | 2.4.7 | 2.4.7 | AA | AA |

The criterion identifiers, conformance levels and main
topics were accurate for these two sampled documents.

Remaining observations:

- The model assigned WCAG version 2.1 to the Keyboard
  document without explicit supporting evidence in
  the inspected text.
- Some technique identifiers were omitted.
- Missing publication years were represented as null.
- The extraction input limit may omit information
  appearing later in a document.

Additional factual discrepancies were identified during
the API metadata review.

| Document | Extracted value | Correct value |
|---|---|---|
| Page Titled | Level AA | Level A |
| Audio Control | Criterion 2.2.1 | Criterion 1.4.2 |
| Contrast (Enhanced) | Criterion 1.4.3 | Criterion 1.4.6 |

Original W3C references:

- https://www.w3.org/WAI/WCAG22/Understanding/keyboard.html
- https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html
- https://www.w3.org/WAI/WCAG22/Understanding/page-titled.html
- https://www.w3.org/WAI/WCAG22/Understanding/audio-control.html
- https://www.w3.org/WAI/WCAG22/Understanding/contrast-enhanced.html

The final manual verification of the last three original
documents remains to be confirmed.

Decision:

Use extract_v2 for the corpus extraction while retaining
extract_v1 for reproducibility.

### Whole corpus extraction

Command:

```powershell
uv run python scripts/extract_metadata.py
```

Estimated eligible corpus: 321 documents.

Five documents had already been processed successfully
using extract_v2 during the trial.

#### Corpus extraction — Run 1

| Metric | Result |
|---|---:|
| Prompt version | extract_v2 |
| Pending at start | 316 |
| Successful extractions | 78 |
| Repaired responses | 15 |
| Failed extractions | 0 |
| Input tokens | 119,131 |
| Output tokens | 93,693 |
| Estimated cost (INR) | 3.5191 |
| Duration | 1,559 seconds |

Observed validation issues:

- Some summaries exceeded the 300-character limit.
- Some initial responses contained no JSON object.
- The automatic repair mechanism recovered 15 responses.

The extraction stopped gracefully when the LLM providers
became unavailable.

Gemini reported HTTP 429 quota exhaustion.

Successfully processed documents remained stored
in PostgreSQL.

#### Corpus extraction — Run 2

The same command was executed again to verify resumability.

```powershell
uv run python scripts/extract_metadata.py
```

| Metric | Result |
|---|---:|
| Prompt version | extract_v2 |
| Pending at start | 238 |
| Successful extractions | 1 |
| Repaired responses | 0 |
| Failed extractions | 0 |
| Input tokens | 1,181 |
| Output tokens | 548 |
| Estimated cost (INR) | 0.0240 |
| Duration | 123 seconds |

The extraction resumed without reprocessing the documents
already completed using extract_v2.

The run stopped again because Gemini was unavailable
and Groq returned HTTP 429 rate-limit errors.

This verified that extraction is resumable and that
previously completed results are preserved.

### Final extraction status

| Metric | Result |
|---|---:|
| Estimated eligible corpus | 321 |
| Successful trial documents using v2 | 5 |
| Successful corpus Run 1 documents | 78 |
| Successful corpus Run 2 documents | 1 |
| Total unique successfully extracted documents | 84 |
| Automatically repaired responses | 15 |
| Recorded extraction failures | 0 |
| Remaining documents | 237 |
| Estimated extraction coverage | 26.17% |
| Minimum Day 9 requirement | 50 documents |

The minimum Day 9 extraction requirement was exceeded
by 34 documents.

All 84 completed documents passed structural validation.

Zero recorded extraction failures does not mean that
all documents were processed or that every extracted
metadata value is factually correct.

The remaining 237 documents are deferred until provider
quotas become available.

To resume:

```powershell
uv run python scripts/extract_metadata.py
```

The extractor skips documents already processed using
the selected prompt version.

### Extraction cost

| Run | Estimated cost (INR) |
|---|---:|
| extract_v1 trial | 0.1778 |
| extract_v2 trial | 0.1824 |
| Corpus extraction Run 1 | 3.5191 |
| Corpus extraction Run 2 | 0.0240 |
| Total | 3.9033 |

Total reported extraction input tokens: 141,686.

Total reported extraction output tokens: 101,536.

Total reported extraction tokens: 243,222.

Effective estimated extraction cost per unique
successfully processed document:

INR 3.9033 / 84 = approximately INR 0.0465.

This includes the cost of both prompt trials and
the two corpus extraction runs.

The cost excludes classifier prompt comparison calls
and other unrelated LLM requests.

These are estimated costs based on configured model
prices, not actual provider invoices.

### Neon database verification

Verified extraction results using the Neon SQL Editor.

#### Successful and failed extractions by prompt

```sql
SELECT
    metadata->'extract'->>'prompt' AS prompt,
    COUNT(*) FILTER (
        WHERE NOT (metadata->'extract' ? 'error')
    ) AS ok,
    COUNT(*) FILTER (
        WHERE metadata->'extract' ? 'error'
    ) AS failed
FROM documents
WHERE doc_type <> 'record'
  AND metadata ? 'extract'
GROUP BY 1;
```

Observed result:

| Prompt | Successful | Failed |
|---|---:|---:|
| extract_v2 | 84 | 0 |

#### Extraction errors grouped by reason

```sql
SELECT
    metadata->'extract'->>'error' AS error,
    COUNT(*) AS documents
FROM documents
WHERE metadata->'extract' ? 'error'
GROUP BY 1
ORDER BY 2 DESC;
```

Observed result:

No rows returned.

There were no recorded terminal extraction errors
at the time of verification.

Provider quota exhaustion prevented further processing
but did not create failed metadata records.

#### Document category distribution

```sql
SELECT
    metadata->>'doc_kind' AS kind,
    COUNT(*) AS documents
FROM documents
WHERE metadata ? 'doc_kind'
GROUP BY 1
ORDER BY 2 DESC;
```

Observed result:

| Document category | Documents |
|---|---:|
| guideline | 64 |
| reference | 18 |
| notice | 1 |
| list | 1 |
| Total | 84 |

The metadata was successfully stored in PostgreSQL
and could be queried using JSONB fields.

### API metadata filtering

Started the local application using:

```powershell
uv run python -m uvicorn a11ycoach.api.main:create_app --factory --reload --host 127.0.0.1 --port 8000
```

Verified the following endpoints:

| Endpoint | HTTP status |
|---|---|
| /docs | 200 |
| /openapi.json | 200 |
| /v1/documents?doc_kind=guideline&limit=3 | 200 |
| /v1/documents?doc_kind=reference&limit=3 | 200 |
| /v1/documents?language=en&limit=3 | 200 |
| /v1/documents?criterion_id=1.4.3&limit=3 | 200 |

Observed filtering results:

| Filter | Matching documents |
|---|---:|
| doc_kind=guideline | 64 |
| doc_kind=reference | 18 |
| language=en | 80 |
| criterion_id=1.4.3 | 5 |

All four metadata filter requests returned HTTP 200
and respected the requested pagination limit.

The criterion_id filter retrieved both existing
structured records and newly extracted documents.

This verified that the existing API can query
LLM-generated metadata.

However, correct filtering does not guarantee that
the stored metadata itself is factually correct.

### Valid but incorrect metadata

The following factual discrepancies were observed
during metadata review:

1. Page Titled was assigned Level AA instead of Level A.

2. Audio Control was assigned criterion 2.2.1 instead
   of criterion 1.4.2.

3. Contrast (Enhanced) was assigned criterion 1.4.3
   instead of criterion 1.4.6.

These values passed structural validation because
they satisfied the metadata schema.

The schema did not verify whether a criterion identifier
or conformance level matched the actual document.

Lesson learned:

Pydantic guarantees that data conforms to the defined
structure and validation rules. It does not independently
guarantee factual correctness.

Incorrect metadata can cause irrelevant documents
to appear in retrieval results.

Future improvements:

- Validate criterion identifiers against an authoritative
  WCAG success criterion mapping.
- Validate criterion titles and conformance levels together.
- Extract identifiers deterministically from source headings
  and trusted document metadata where possible.
- Avoid inferring WCAG versions without supporting evidence.
- Inspect additional document content when technique
  identifiers are missing.
- Evaluate metadata factual accuracy separately from
  schema validation success.

### Automated tests

Added tests for:

- Prompt version discovery and numeric version ordering.
- Question classification.
- Question tag construction.
- Classification accuracy calculation.
- Prompt leakage detection.
- Classifier temperature and usage recording.
- Optional response_format forwarding.
- JSON parsing.
- Invalid JSON handling.
- Pydantic schema validation.
- Automatic extraction repair.
- Maximum extraction attempts.
- Native JSON schema mode.
- DocMeta field validation.
- Extraction prompt field coverage.
- Metadata persistence.
- Preservation of existing parser metadata.
- Extraction resumability.
- Prompt version changes.
- Retrying failed extractions.
- Graceful stopping when providers are unavailable.

Targeted test results:

| Test group | Passed |
|---|---:|
| Classifier and gateway | 26 |
| Extraction unit tests | 8 |
| Combined targeted unit tests | 34 |

Final complete test suite:

| Test group | Passed |
|---|---:|
| Unit tests | 94 |
| Integration tests | 10 |
| Total automated tests | 104 |

Integration-only coverage: 49%.

Extraction module integration coverage: 96%.

The integration runner:

- Created a fresh temporary PostgreSQL database.
- Applied all four database migrations.
- Executed the integration tests.
- Removed the temporary database after completion.

The production Neon corpus was not used as the
destructive integration test database.

### Problems encountered and how I fixed them

#### 1. Windows pytest launcher

Problem:

The pytest launcher reported a script path
canonicalisation error.

Resolution:

Executed pytest through the Python module interface.

```powershell
uv run python -m pytest
```

#### 2. Missing FakeLLM request tracking

Problem:

The classifier test failed because FakeLLM did not
provide the seen attribute.

Resolution:

Added request tracking to FakeLLM so tests could
inspect messages and generation options.

The classifier and gateway tests passed afterward.

#### 3. Missing integration test marker

Problem:

The new extraction integration test was executed
as part of the unit test suite.

It failed because DATABASE_URL was unavailable.

Resolution:

Added the integration marker:

```python
pytestmark = pytest.mark.integration
```

The integration test was then correctly excluded
from the unit test suite and executed using the
isolated integration test runner.

#### 4. Duplicate import and Ruff violations

Problem:

The extraction integration test contained a
duplicate Literal import.

Resolution:

```powershell
uv run ruff check tests/integration/test_extract_store.py --fix
```

Ruff corrected the import issue.

Subsequent lint checks passed.

#### 5. Inconsistent metadata categories

Problem:

Similar W3C Understanding documents were assigned
different document categories.

Resolution:

Created extract_v2 with clearer category and
formatting instructions.

All five trial documents were consistently
classified as reference after re-extraction.

#### 6. Invalid structured output

Problem:

Some LLM responses contained no JSON object or
summaries exceeding the permitted length.

Resolution:

Used Pydantic validation and automatic correction
requests.

The extraction engine recovered 15 responses
without recording terminal extraction failures.

#### 7. LLM provider quota exhaustion

Problem:

Gemini and Groq became unavailable due to quota
and rate limits during corpus extraction.

Resolution:

The extractor waited 60 seconds and retried.

When the providers remained unavailable, the
extractor stopped gracefully.

Previously completed records remained stored
in PostgreSQL.

A subsequent run resumed successfully.

The remaining documents will be processed when
provider quotas become available.

#### 8. Missing Poe development task

Problem:

The command uv run poe dev failed because the
project does not define a dev task.

Resolution:

Started Uvicorn directly:

```powershell
uv run python -m uvicorn a11ycoach.api.main:create_app --factory --reload --host 127.0.0.1 --port 8000
```

The local application started successfully.

#### 9. Non-blocking warnings

Observed warnings:

- Starlette TestClient httpx deprecation warning.
- urllib3 optional PySocks dependency warning.
- Duplicate OpenAPI operation ID for the health endpoint.
- Missing favicon returning HTTP 404.

These warnings did not prevent automated tests,
metadata extraction or API filtering from succeeding.

They remain separate maintenance items.

### Final local verification

| Check | Result |
|---|---|
| Versioned prompt loader | Passed |
| Question classifier | Passed |
| Evaluation dataset | 20 labelled questions |
| Best classifier prompt | classify_v4 |
| Development dataset accuracy | 100% |
| Prompt leakage check | No warnings |
| Structured metadata contract | Passed |
| Best extraction prompt | extract_v2 |
| Five-document extraction trial | Passed |
| Automatic repair | 15 recovered responses |
| Metadata persistence | Passed |
| Extraction resumability | Passed |
| Successfully extracted documents | 84 |
| Minimum 50-document requirement | Met |
| Recorded extraction failures | 0 |
| Neon database verification | Passed |
| Document category filtering | Passed |
| Language filtering | Passed |
| Criterion identifier filtering | Passed |
| Unit tests | 94 passed |
| Integration tests | 10 passed |
| Total automated tests | 104 passed |
| Ruff lint | Passed |
| Full corpus extraction | Deferred due to quotas |
| Metadata factual accuracy | Further improvement required |

### Files added

Prompts:

- prompts/classify_v1.md
- prompts/classify_v2.md
- prompts/classify_v3.md
- prompts/classify_v4.md
- prompts/extract_v1.md
- prompts/extract_v2.md

Evaluation:

- eval/prompt_testset.jsonl

Scripts:

- scripts/compare_prompts.py
- scripts/extract_metadata.py

Application modules:

- src/a11ycoach/llm/prompts.py
- src/a11ycoach/llm/classify.py
- src/a11ycoach/llm/doc_meta.py
- src/a11ycoach/llm/extract.py

Tests:

- tests/unit/test_classify.py
- tests/unit/test_extract.py
- tests/integration/test_extract_store.py

### Files modified

- .gitignore
- NOTES.md
- src/a11ycoach/llm/gateway.py
- tests/unit/test_gateway.py

### What I learned today

- Prompt wording affects classification accuracy.
- Few-shot examples do not always improve results.
- Versioned prompts make experiments reproducible.
- Evaluation datasets help measure prompt quality.
- Cached evaluation results avoid unnecessary LLM calls.
- Structured output makes LLM responses easier to process.
- Pydantic validation detects malformed responses.
- Automatic correction can recover invalid model outputs.
- Metadata extraction supports document filtering.
- Saving progress after each document enables resumability.
- Provider quotas affect large-scale extraction workloads.
- Structural correctness does not guarantee factual accuracy.
- Authoritative source verification remains essential.

### Remaining limitations

- The classifier was evaluated on a small development dataset.
- Independent evaluation on unseen questions is required.
- Classmate review of the evaluation dataset is unconfirmed.
- Final manual source verification of three additional
  documents is unconfirmed.
- Some extracted metadata contains factual inaccuracies.
- The extraction input limit may omit relevant information.
- The remaining 237 documents have not been processed.
- The question router has been implemented and tested
  independently; integration into the live chat request
  flow has not been verified.
- Retrieval-Augmented Generation is not yet implemented
  as part of today's work.

### Live deployment verification

- Live URL: https://a11ycoach.onrender.com
- Feature branch: day09-prompts
- Commit: Pending.
- Pull request: Pending.
- CI: Pending.
- Merge: Pending.
- CD deployment: Pending.
- Live health endpoint: Pending Day 9 verification.
- Live readiness endpoint: Pending Day 9 verification.
- Live document metadata filtering: Pending.
- Uptime monitor: Pending final verification.

Live endpoints to verify after deployment:

```text
https://a11ycoach.onrender.com/health
https://a11ycoach.onrender.com/ready
https://a11ycoach.onrender.com/docs
https://a11ycoach.onrender.com/v1/documents?doc_kind=guideline&limit=3
https://a11ycoach.onrender.com/v1/documents?doc_kind=reference&limit=3
https://a11ycoach.onrender.com/v1/documents?language=en&limit=3
https://a11ycoach.onrender.com/v1/documents?criterion_id=1.4.3&limit=3
```

### Day 9 status

- Milestone 1 — Versioned prompts and question router:
  Completed.
- Milestone 2 — Labelled evaluation dataset:
  Technical implementation completed; classmate review
  remains unconfirmed.
- Milestone 3 — Prompt comparison and improvement:
  Completed.
- Milestone 4 — Structured metadata extraction:
  Completed.
- Milestone 5 — Corpus extraction and metadata filtering:
  Minimum extraction requirement achieved, with full
  corpus processing and final manual review outstanding.
- Milestone 6 — Notes, pull request and live check:
  In progress.

Day 9 implementation is ready for final Git verification
and submission, with the remaining limitations documented.

### D10 · Queue and worker

- First run: 10 documents queued, finished in 197 s. Done 9, skipped 0, failed 1.
- Second run: 10 documents queued, finished in 196 s. Done 9, skipped 0, failed 1.
- Pace: 19.7 s per requested document in the first batch, including retries and provider delays.
- Configured INGEST_RPM = 12, INGEST_CONCURRENCY = 2 (default settings; verify against local configuration).
- The API returned HTTP 202 immediately while the background worker processed documents asynchronously.

### Kill test

- Job ID: `fc4ab8a40f5945eb8619e2434b6f8ed9`
- Queued: 20.
- At the kill: queued 13, running 2, done 5, failed 0.
- Last progress before interruption: 56 s.
- First reported progress after recovery: 177 s.
- Observed interruption and recovery gap: 121 s.
- After the new worker: done 20 + skipped 0 + failed 0 = 20.
- Final completion time: 372 s.
- Pages processed: 59.
- Documents in the database: 321, different external IDs: 321.
- Lost items: 0.
- Duplicate external IDs: 0.
- Interrupted items 48 and 49 both completed with two attempts.
- The interrupted jobs had to wait for their Redis locks to expire before they could be processed again.
- Nothing was doubled because the worker checks document identity and existing processing results before repeating work.
- Health endpoint returned status ok. Localhost verification during the interruption is pending confirmation.

### Dead-letter list

| Stage | Items | What I did |
|---|---:|---|
| Parse | 0 | No action required |
| Extract validation | 0 | No action required |
| Download | 0 | No action required |
| Gave up after retries | 5 historical failures | Retried four failed items; one completed, two were skipped and one failed again due to the daily token limit |

- Retry job ID: `9e44eb7a86f44e398adf434874a57e23`
- Retry duration: 195 s.
- Remaining retry failure: `label-in-name.html`.
- Groq daily token limit: 200,000.
- Tokens used at the time of failure: 197,604.
- Further retries should wait until sufficient provider quota is available.

### Live ingestion

- A11yCoach on Render: PENDING — Milestone 7.
- Live documents completed: PENDING.
- Live documents failed: PENDING.
- A live request without the admin token gets status: PENDING.
- Local unauthenticated POST request returned HTTP 401.

### Week 2 against Monday's estimate

- docs/CAPACITY.md estimated 1,500 pages and 2,110,295 raw tokens.
- docs/INGEST_REPORT.md reports 321 documents, 497 pages and approximately 187,775 cleaned text tokens.
- Actual page coverage: 33.1% of the full target.
- Estimated tokens per page decreased from 1,407 to 377.8, approximately 73.1% lower.
- The difference is likely due to HTML cleaning and differences in document composition, as well as the corpus not yet reaching its full target.
- At the current average text density, 1,500 pages would contain approximately 566,726 tokens.
- Token counts use the approximate four-characters-per-token method.

### One thing that went wrong today, and how I fixed it

The worker initially failed to connect to Neon because of a hostname resolution error. I checked the database hostname using nslookup, verified the API readiness endpoint and restarted the worker successfully.

I also encountered LLM provider rate limits. The worker handled these using automatic retries and recorded exhausted attempts in the dead-letter list. The daily quota limitation remains unresolved.

### Testing and validation

- Unit tests: 108 passed.
- Integration tests: 14 passed.
- Total tests passed across both runs: 122.
- Worker recovery test: 20 of 20 completed.
- Docker Compose defines five services: db, redis, migrate, api and worker.
- Ingestion report generated successfully.
- No queued or running ingestion items remain.
