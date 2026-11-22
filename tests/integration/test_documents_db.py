import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from a11ycoach.api.main import create_app
from a11ycoach.config import Settings
from a11ycoach.db.models import Document
from a11ycoach.db.session import make_sessionmaker

pytestmark = pytest.mark.integration


@pytest.fixture
def integration_client(database_url):
    settings = Settings(app_env="ci", database_url=database_url)
    app = create_app(settings)

    with TestClient(app) as client:
        yield client


@pytest.fixture
def seeded_database(database_url):
    import asyncio

    async def seed():
        settings = Settings(app_env="ci", database_url=database_url)
        from a11ycoach.db.session import make_engine

        engine = make_engine(settings)
        sessionmaker = make_sessionmaker(engine)

        async with sessionmaker() as session:
            await session.execute(delete(Document))
            session.add_all(
                [
                    Document(
                        external_id="INT-001",
                        title="Accessibility Guide",
                        sha256="a" * 64,
                        doc_type="guide",
                        metadata_={"year": 2024, "topic": "accessibility"},
                    ),
                    Document(
                        external_id="INT-002",
                        title="Keyboard Navigation",
                        sha256="b" * 64,
                        doc_type="guide",
                        metadata_={"year": 2025, "topic": "keyboard"},
                    ),
                ]
            )
            await session.commit()

        await engine.dispose()

    asyncio.run(seed())
    yield


def test_list_documents_from_postgres(integration_client, seeded_database):
    response = integration_client.get("/v1/documents")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert {item["id"] for item in body["items"]} == {"INT-001", "INT-002"}


def test_search_documents_in_postgres(integration_client, seeded_database):
    response = integration_client.get("/v1/documents", params={"q": "Keyboard"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == "INT-002"


def test_filter_documents_by_json_metadata(integration_client, seeded_database):
    response = integration_client.get(
        "/v1/documents",
        params={"topic": "accessibility"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == "INT-001"


def test_get_document_from_postgres(integration_client, seeded_database):
    response = integration_client.get("/v1/documents/INT-001")

    assert response.status_code == 200
    assert response.json()["title"] == "Accessibility Guide"


def test_missing_document_from_postgres(integration_client, seeded_database):
    response = integration_client.get("/v1/documents/DOES-NOT-EXIST")

    assert response.status_code == 404
