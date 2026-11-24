# A11yCoach Capacity Planning

## Objective

Estimate the processing cost and database storage required for the A11yCoach accessibility knowledge base.

## Full target

The planned corpus contains at least 1,500 pages of WCAG guidelines, Understanding documents, techniques, failures and WAI-ARIA patterns.

The application will use PostgreSQL with pgvector to store and retrieve document embeddings.

## Capacity estimates

<!-- generated:start -->
| Metric | Estimate |
|---|---:|
| Planned pages | 1,500 |
| Estimated raw tokens per page | 1,407 |
| Projected raw tokens | 2,110,295 |
| Assumed tokens per chunk | 500 |
| Projected chunks | 4,221 |
| Assumed embedding dimensions | 1,536 |
| Raw vector payload | 24.73 MiB |
| 10x raw vector payload | 247.32 MiB |

**Method:** Approximately four characters per token.
One 1,536-dimensional float32 embedding occupies 6,144 bytes.
Actual vector storage will be higher due to row/index overhead.
Chunk overlap, text cleaning, metadata and indexes are excluded.

**Embedding cost:** Not priced because a provider, model,
price per million tokens and INR exchange rate have not
yet been selected or verified.
<!-- generated:end -->

## Conclusions

### Embedding cost

The full target of 1,500 pages is estimated to contain 2,110,295 raw tokens and produce approximately 4,221 chunks.

Assuming an embedding price of USD 0.02 per million tokens and an exchange rate of INR 90 per USD, the estimated one-time embedding cost is approximately INR 3.80.

These are illustrative pricing assumptions and must be verified before purchasing API usage.

### Database storage

The estimated raw vector payload for the full corpus is 24.73 MiB. The estimated raw text equivalent is approximately 8.05 MiB.

The combined planning estimate is approximately 32.78 MiB, excluding indexes, metadata, PostgreSQL overhead and chunk overlap.

The actual PostgreSQL storage limit must be checked in the hosting provider's dashboard before confirming that the full corpus fits.

### Least certain estimate

The token and chunk counts are the least certain estimates because they are calculated from raw HTML characters rather than cleaned document text.

After implementing HTML cleaning, measure the actual token counts using the selected embedding model's tokenizer and record the actual number of chunks produced.

### Tenfold growth

Increasing the corpus to 15,000 pages would produce approximately 21.1 million raw tokens and 42,210 chunks.

The estimated raw vector payload would increase to 247.32 MiB, with an illustrative embedding cost of approximately INR 38.

Database capacity, vector indexes and retrieval performance should be reassessed before expanding to this scale.

### Key finding

The initial corpus is relatively small. Under the current assumptions, embedding costs are low, while database storage, indexing and retrieval performance require more careful capacity planning.
