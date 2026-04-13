import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


TEST_DB_PATH = Path("/workspaces/AGX-travel/test_agx.db")
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
sys.path.insert(0, "/workspaces/AGX-travel")

from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_db():
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    yield
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture()
def client() -> TestClient:
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth_token(client: TestClient) -> str:
    email = "pytest-user@example.com"
    password = "Test@1234"

    client.post(
        "/v1/auth/register",
        json={"name": "Pytest User", "email": email, "password": password},
    )
    login = client.post("/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    return login.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
