import httpx
import uuid


def test_login_success(api_url):
    resp = httpx.post(
        f"{api_url}/api/auth/login",
        json={"email": "test@test.com", "password": "testtest123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert data["record"]["email"] == "test@test.com"


def test_login_wrong_password(api_url):
    resp = httpx.post(
        f"{api_url}/api/auth/login",
        json={"email": "test@test.com", "password": "wrongpassword"},
    )
    assert resp.status_code == 401


def test_register_and_login(api_url):
    email = f"user-{uuid.uuid4().hex[:8]}@test.com"
    # Register
    resp = httpx.post(
        f"{api_url}/api/auth/register",
        json={"email": email, "password": "testtest123", "name": "New User"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == email

    # Login with new account
    resp = httpx.post(
        f"{api_url}/api/auth/login",
        json={"email": email, "password": "testtest123"},
    )
    assert resp.status_code == 200
    assert "token" in resp.json()


def test_chat_requires_auth(api_url):
    resp = httpx.post(
        f"{api_url}/api/chat",
        json={"query": "hello"},
    )
    # HTTPBearer returns 401 when no Authorization header
    assert resp.status_code in (401, 403)


def test_chat_rejects_bad_token(api_url):
    resp = httpx.post(
        f"{api_url}/api/chat",
        json={"query": "hello"},
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert resp.status_code == 401
