"""Extraction against a real Postgres: merged, resumable and versioned."""

from typing import Literal

import pytest
from pydantic import BaseModel
from sqlalchemy import select

from a11ycoach.config import Settings
from a11ycoach.db.models import Document, Page
from a11ycoach.db.session import make_engine, make_sessionmaker
from a11ycoach.llm.extract import run
from a11ycoach.llm.gateway import FakeLLM, LLMError, LLMGateway

pytestmark = pytest.mark.integration


class Notice(BaseModel):
    kind: Literal["circular", "guideline"]
    topics: list[str]


GOOD = '{"kind": "circular", "topics": ["fees"]}'


async def no_sleep(seconds: float) -> None:
    pass


def document(number: int, doc_type: str = "pdf") -> Document:
    return Document(
        external_id=f"f-{number}",
        title=f"Document {number}",
        doc_type=doc_type,
        sha256=str(number) * 64,
        metadata_={"parser": "pymupdf", "pages": 1},
        pages=[
            Page(
                page_no=1,
                text=f"Text of document {number}.",
                headings=[],
            )
        ],
    )


async def test_extraction_is_stored_resumable_and_versioned(database_url):
    engine = make_engine(
        Settings(
            app_env="ci",
            database_url=database_url,
            _env_file=None,
        )
    )

    sessionmaker = make_sessionmaker(engine)

    async with sessionmaker() as session:
        await session.execute(Document.__table__.delete())

        session.add_all(
            [
                document(1),
                document(2),
                document(3),
                document(4, "record"),
            ]
        )

        await session.commit()

    async def extract_all(
        llm: FakeLLM,
        version: str = "extract_v1",
        **options,
    ):
        said: list[str] = []
        gateway = LLMGateway([llm], sleep=no_sleep)

        options |= {
            "sleep": no_sleep,
            "echo": said.append,
        }

        return (
            await run(
                sessionmaker,
                gateway,
                Notice,
                "Fill.",
                version,
                **options,
            ),
            said,
        )

    async def stored() -> dict[str, dict]:
        async with sessionmaker() as session:
            rows = await session.scalars(select(Document).order_by(Document.external_id))

            return {row.external_id: row.metadata_ for row in rows}

    # Document 1 succeeds, 2 fails, 3 is repaired.
    # Document 4 is a data record and must be skipped.
    llm = FakeLLM(
        script=[
            GOOD,
            "no",
            "no",
            "no",
            '{"kind": "poem", "topics": []}',
            GOOD,
        ]
    )

    counts, said = await extract_all(llm)

    assert (
        counts["ok"],
        counts["repaired"],
        counts["failed"],
    ) == (2, 1, 1)

    assert llm.calls == 6

    meta = await stored()

    assert meta["f-1"]["kind"] == "circular"
    assert meta["f-1"]["parser"] == "pymupdf"

    assert meta["f-1"]["extract"] == {
        "prompt": "extract_v1",
        "model": "fake-1",
        "attempts": 1,
    }

    assert "kind" not in meta["f-2"]
    assert "no JSON object" in meta["f-2"]["extract"]["error"]

    assert meta["f-3"]["extract"]["attempts"] == 2
    assert "extract" not in meta["f-4"]

    assert any(line.startswith("FAILED") for line in said)

    # Running again must not repeat completed documents.
    again = FakeLLM()
    counts, _ = await extract_all(again)

    assert counts["pending"] == 0
    assert again.calls == 0

    # Retry only the failed document.
    retry = FakeLLM(script=[GOOD])

    counts, _ = await extract_all(
        retry,
        retry_failed=True,
    )

    assert counts["ok"] == 1
    assert retry.calls == 1
    assert "error" not in (await stored())["f-2"]["extract"]

    # A new prompt version reprocesses all eligible documents.
    counts, _ = await extract_all(
        FakeLLM(script=[GOOD] * 3),
        version="extract_v2",
    )

    assert counts["pending"] == 3

    # Stop safely when the provider is unavailable.
    down = FakeLLM(script=[LLMError("HTTP 429", retryable=False)] * 2)

    counts, said = await extract_all(
        down,
        version="extract_v3",
    )

    assert counts["stopped"] == 1
    assert counts["ok"] == 0
    assert "stopped" in said[-1]

    await engine.dispose()
