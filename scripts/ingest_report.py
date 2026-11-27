"""Generate an ingestion report from the database."""

import asyncio
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import func, select

from a11ycoach.config import get_settings
from a11ycoach.db.models import (
    Document,
    IngestItem,
    IngestJob,
    Page,
    ParseFailure,
)
from a11ycoach.db.session import make_engine, make_sessionmaker

REPORT = Path("docs/INGEST_REPORT.md")
START = "<!-- generated:start -->"
END = "<!-- generated:end -->"


async def main() -> None:
    settings = get_settings()
    engine = make_engine(settings)
    sessionmaker = make_sessionmaker(engine)

    try:
        async with sessionmaker() as session:
            documents = await session.scalar(
                select(func.count(Document.id)).where(Document.doc_type != "record")
            )

            page_count, characters = (
                await session.execute(
                    select(
                        func.count(Page.id),
                        func.coalesce(func.sum(func.length(Page.text)), 0),
                    )
                    .join(Document, Page.document_id == Document.id)
                    .where(Document.doc_type != "record")
                )
            ).one()

            parse_failures = await session.scalar(select(func.count(ParseFailure.id)))

            jobs = await session.scalar(select(func.count(IngestJob.id)))

            status_rows = (
                await session.execute(
                    select(
                        IngestItem.status,
                        func.count(IngestItem.id),
                    ).group_by(IngestItem.status)
                )
            ).all()

            statuses = dict(status_rows)

            failed_items = (
                await session.scalars(select(IngestItem).where(IngestItem.status == "failed"))
            ).all()

            failure_reasons: Counter[str] = Counter()

            for item in failed_items:
                error = item.error.lower()

                if error.startswith("parse:"):
                    stage = "Parse"
                elif error.startswith("extract:"):
                    stage = "Extract"
                elif error.startswith("download"):
                    stage = "Download"
                elif error.startswith("gave up"):
                    stage = "Gave up after retries"
                else:
                    stage = "Other"

                failure_reasons[stage] += 1

        tokens = (characters + 3) // 4
        dead_letter = statuses.get("failed", 0)
        average_tokens = tokens / page_count if page_count else 0

        generated = [
            START,
            "",
            f"Updated: {datetime.now(UTC):%Y-%m-%d %H:%M UTC}",
            "",
            "## Corpus statistics",
            "",
            "| Metric | Actual |",
            "|---|---:|",
            f"| Documents | {documents:,} |",
            f"| Pages | {page_count:,} |",
            f"| Text characters | {characters:,} |",
            f"| Tokens of text (estimated) | {tokens:,} |",
            f"| Average tokens per page | {average_tokens:,.1f} |",
            f"| Parse failures | {parse_failures:,} |",
            "",
            "## Ingestion statistics",
            "",
            "| Metric | Count |",
            "|---|---:|",
            f"| Ingestion jobs | {jobs:,} |",
            f"| Done | {statuses.get('done', 0):,} |",
            f"| Skipped | {statuses.get('skipped', 0):,} |",
            f"| Failed | {dead_letter:,} |",
            f"| Queued | {statuses.get('queued', 0):,} |",
            f"| Running | {statuses.get('running', 0):,} |",
            "",
            "## Dead-letter list",
            "",
            "| Failure stage | Items |",
            "|---|---:|",
        ]

        for stage, count in sorted(failure_reasons.items()):
            generated.append(f"| {stage} | {count:,} |")

        if not failure_reasons:
            generated.append("| None | 0 |")

        generated.extend(
            [
                "",
                "**Method:** Approximately four text characters per token.",
                "",
                "Ingestion statistics include historical attempts.",
                "Dead-letter counts include historical failed items,",
                "even when a later retry succeeds.",
                "",
                END,
            ]
        )

        block = "\n".join(generated)

        REPORT.parent.mkdir(parents=True, exist_ok=True)

        if REPORT.exists():
            content = REPORT.read_text(encoding="utf-8")

            if START in content and END in content:
                before = content.split(START, 1)[0]
                after = content.split(END, 1)[1]
                content = before + block + after
            else:
                content = content.rstrip() + "\n\n" + block + "\n"
        else:
            content = (
                "# A11yCoach Ingestion Report\n\n" + block + "\n\n## What I learnt\n\n"
                "- TODO\n"
                "- TODO\n"
                "- TODO\n"
            )

        REPORT.write_text(content, encoding="utf-8")

        print(
            f"documents={documents} pages={page_count} "
            f"dead_letter={dead_letter} -> {REPORT.as_posix()}"
        )

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
