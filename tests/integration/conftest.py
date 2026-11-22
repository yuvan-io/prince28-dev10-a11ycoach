import os

import pytest


@pytest.fixture(scope="session")
def database_url():
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.fail("DATABASE_URL is missing. Run tests with scripts/test-integration.py.")
    return url
