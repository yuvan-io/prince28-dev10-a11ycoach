"""Generate A11yCoach dataset and capacity statistics."""

import argparse
import json
import math
from collections import Counter
from pathlib import Path

START = "<!-- generated:start -->"
END = "<!-- generated:end -->"


def replace_generated(path: Path, content: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Create {path} with generated markers first.")

    original = path.read_text(encoding="utf-8")
    if original.count(START) != 1 or original.count(END) != 1:
        raise ValueError(f"{path}: expected exactly one marker pair")

    before, remainder = original.split(START, 1)
    _, after = remainder.split(END, 1)
    path.write_text(
        before + START + "\n" + content.strip() + "\n" + END + after,
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full-pages", type=int, default=1500)
    args = parser.parse_args()

    if args.full_pages <= 0:
        parser.error("--full-pages must be positive")

    root = Path(__file__).resolve().parents[1]
    manifest = root / "data" / "manifest.jsonl"

    rows = [
        json.loads(line)
        for line in manifest.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    # Keep the latest record for each document path.
    unique = {
        row["path"]: row for row in rows if row.get("path") and row.get("status") == "downloaded"
    }

    documents = []
    for relative_path, row in unique.items():
        path = root / relative_path
        if path.is_file():
            documents.append((path, row))

    sources = Counter(row.get("source", "unknown") for _, row in documents)
    total_bytes = sum(path.stat().st_size for path, _ in documents)
    total_mb = total_bytes / (1024 * 1024)
    count = len(documents)

    # Rough planning assumptions, NOT actual tokenization.
    chars = sum(len(path.read_text(encoding="utf-8", errors="replace")) for path, _ in documents)
    estimated_tokens = math.ceil(chars / 4)
    tokens_per_page = estimated_tokens / count if count else 0

    # Assume 500-token chunks and 1,536-dimensional float32 vectors.
    chunk_tokens = 500
    dimensions = 1536
    projected_tokens = math.ceil(tokens_per_page * args.full_pages)
    projected_chunks = math.ceil(projected_tokens / chunk_tokens)
    vector_bytes = projected_chunks * dimensions * 4
    vector_mb = vector_bytes / (1024 * 1024)

    dataset_summary = f"""\
- Unique available documents: **{count}**
- Historical manifest records: **{len(rows)}**
- Selected document bytes: **{total_bytes:,} ({total_mb:.2f} MiB)**
- Source breakdown: **{dict(sources)}**
- Estimated tokens in collected files: **{estimated_tokens:,}**
- Estimated tokens per document: **{tokens_per_page:,.0f}**

These are raw-file estimates. HTML markup and repository templates
have not yet been cleaned or deduplicated.
"""

    capacity_summary = f"""\
| Metric | Estimate |
|---|---:|
| Planned pages | {args.full_pages:,} |
| Estimated raw tokens per page | {tokens_per_page:,.0f} |
| Projected raw tokens | {projected_tokens:,} |
| Assumed tokens per chunk | {chunk_tokens} |
| Projected chunks | {projected_chunks:,} |
| Assumed embedding dimensions | {dimensions:,} |
| Raw vector payload | {vector_mb:.2f} MiB |
| 10x raw vector payload | {vector_mb * 10:.2f} MiB |

**Method:** Approximately four characters per token.
One 1,536-dimensional float32 embedding occupies 6,144 bytes.
Actual vector storage will be higher due to row/index overhead.
Chunk overlap, text cleaning, metadata and indexes are excluded.

**Embedding cost:** Not priced because a provider, model,
price per million tokens and INR exchange rate have not
yet been selected or verified.
"""

    replace_generated(root / "DATASET.md", dataset_summary)
    replace_generated(root / "docs" / "CAPACITY.md", capacity_summary)

    print(f"manifest_records={len(rows)}")
    print(f"unique_available_documents={count}")
    print(f"selected_mib={total_mb:.2f}")
    print(f"estimated_tokens={estimated_tokens}")
    print(f"projected_chunks={projected_chunks}")
    print(f"raw_vector_mib={vector_mb:.2f}")
    print("Updated DATASET.md and docs/CAPACITY.md")


if __name__ == "__main__":
    main()
