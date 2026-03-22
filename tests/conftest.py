import asyncio
import pytest
import httpx

PB_URL = "http://localhost:8090"
API_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "adminadmin123"
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "testtest123"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def api_url():
    return API_URL


@pytest.fixture(scope="session")
def pb_url():
    return PB_URL


@pytest.fixture(scope="session")
def user_token():
    """Get a user JWT from the running PocketBase."""
    resp = httpx.post(
        f"{API_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["token"]


@pytest.fixture(scope="session")
def admin_pb_token():
    """Get a PocketBase superuser token for direct PB API calls."""
    resp = httpx.post(
        f"{PB_URL}/api/collections/_superusers/auth-with-password",
        json={"identity": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert resp.status_code == 200, f"PB admin auth failed: {resp.text}"
    return resp.json()["token"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
