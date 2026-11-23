def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "app": "a11ycoach",
        "env": "ci",
        "version": "dev",
    }


def test_health_version(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert "version" in response.json()
    assert response.json()["version"] == "dev"


def test_ready(client):
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {"database": True},
    }


def test_list_documents(client):
    response = client.get("/v1/documents")

    assert response.status_code == 200
    assert response.json()["total"] == 3
    assert len(response.json()["items"]) == 3


def test_document_limit(client):
    response = client.get("/v1/documents?limit=2")

    assert response.status_code == 200
    assert len(response.json()["items"]) == 2
    assert response.json()["total"] == 3


def test_document_offset(client):
    response = client.get("/v1/documents?limit=2&offset=1")

    assert response.status_code == 200
    assert response.json()["items"][0]["id"] == "DOC-002"


def test_search_documents(client):
    response = client.get("/v1/documents?q=Alpha")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["id"] == "DOC-001"


def test_search_is_case_insensitive(client):
    response = client.get("/v1/documents?q=alpha")

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_filter_documents(client):
    response = client.get("/v1/documents?year=2024")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["id"] == "DOC-002"
    assert response.json()["filters"] == {"year": "2024"}


def test_filter_no_matches(client):
    response = client.get("/v1/documents?year=2030")

    assert response.status_code == 200
    assert response.json()["total"] == 0
    assert response.json()["items"] == []


def test_invalid_filter_name(client):
    response = client.get("/v1/documents?bad-filter=value")

    assert response.status_code == 400
    assert response.headers["content-type"].startswith("application/problem+json")


def test_get_document(client):
    response = client.get("/v1/documents/DOC-002")

    assert response.status_code == 200
    assert response.json()["title"] == "Beta circular"


def test_missing_document(client):
    response = client.get("/v1/documents/DOC-999")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["status"] == 404


def test_invalid_limit(client):
    response = client.get("/v1/documents?limit=0")

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")


def test_invalid_offset(client):
    response = client.get("/v1/documents?offset=-1")

    assert response.status_code == 422


def test_request_id(client):
    response = client.get(
        "/health",
        headers={"X-Request-ID": "a11ycoach-test-123"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "a11ycoach-test-123"


def test_error_request_id(client):
    response = client.get(
        "/v1/documents/DOC-999",
        headers={"X-Request-ID": "a11ycoach-error-123"},
    )

    assert response.status_code == 404
    assert response.json()["request_id"] == "a11ycoach-error-123"
