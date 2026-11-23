import os

import pytest
from fastapi.testclient import TestClient

from a11ycoach.api.deps import check_db, get_repo
from a11ycoach.api.main import create_app
from a11ycoach.config import Settings

SAMPLE = [
    {
        "id": "DOC-001",
        "title": "Alpha guideline",
        "year": 2023,
        "doc_type": "record",
        "source_url": "https://example.com/alpha",
    },
    {
        "id": "DOC-002",
        "title": "Beta circular",
        "year": 2024,
        "doc_type": "record",
        "source_url": "https://example.com/beta",
    },
    {
        "id": "DOC-003",
        "title": "Gamma notice",
        "year": 2025,
        "doc_type": "record",
        "source_url": "https://example.com/gamma",
    },
]


class FakeRepository:
    def __init__(self):
        self.records = SAMPLE

    async def list(self, *, q, filters, limit, offset):
        records = self.records

        if q:
            q_lower = q.lower()
            records = [record for record in records if q_lower in record["title"].lower()]

        for key, value in filters.items():
            records = [record for record in records if str(record.get(key, "")) == value]

        total = len(records)
        return total, records[offset : offset + limit]

    async def get(self, external_id):
        return next(
            (record for record in self.records if record["id"] == external_id),
            None,
        )


@pytest.fixture
def fake_repo():
    return FakeRepository()


@pytest.fixture
def client(fake_repo):
    settings = Settings(
        app_env="ci",
        database_url=os.environ.get(
            "TEST_DATABASE_URL",
            "postgresql://app:app@localhost:5433/app",
        ),
    )

    app = create_app(settings)

    app.dependency_overrides[get_repo] = lambda: fake_repo
    app.dependency_overrides[check_db] = lambda: True

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
