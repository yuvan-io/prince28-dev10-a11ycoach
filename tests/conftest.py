import json

import pytest
from fastapi.testclient import TestClient

from a11ycoach.api.main import create_app
from a11ycoach.config import Settings

SAMPLE = [
    {"id": "001", "title": "Alpha guideline", "year": 2023},
    {"id": "002", "title": "Beta circular", "year": 2024},
    {"id": "003", "title": "Gamma notice", "year": 2025},
]


@pytest.fixture
def data_file(tmp_path):
    path = tmp_path / "records.json"
    path.write_text(json.dumps(SAMPLE), encoding="utf-8")
    return path


@pytest.fixture
def client(data_file):
    settings = Settings(app_env="ci", data_file=data_file)
    with TestClient(create_app(settings)) as test_client:
        yield test_client
