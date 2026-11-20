def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready(client):
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["checks"]["records_loaded"] is True


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


def test_search_documents(client):
    response = client.get("/v1/documents?q=Alpha")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["id"] == "001"


def test_get_document(client):
    response = client.get("/v1/documents/002")

    assert response.status_code == 200
    assert response.json()["title"] == "Beta circular"


def test_missing_document(client):
    response = client.get("/v1/documents/999")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["status"] == 404


def test_invalid_limit(client):
    response = client.get("/v1/documents?limit=0")

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")


def test_request_id(client):
    response = client.get(
        "/health",
        headers={"X-Request-ID": "a11ycoach-test-123"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "a11ycoach-test-123"


def test_error_request_id(client):
    response = client.get(
        "/v1/documents/999",
        headers={"X-Request-ID": "a11ycoach-error-123"},
    )

    assert response.status_code == 404
    assert response.json()["request_id"] == "a11ycoach-error-123"
