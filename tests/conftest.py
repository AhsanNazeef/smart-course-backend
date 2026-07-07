import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    """
    A test client for the FastAPI app.

    Using `with TestClient(app)` (a context manager) triggers the app's
    lifespan events - so this also proves the app STARTS UP cleanly.
    """
    with TestClient(app) as test_client:
        yield test_client
