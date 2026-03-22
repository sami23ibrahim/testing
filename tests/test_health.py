import httpx


def test_fastapi_health(api_url):
    resp = httpx.get(f"{api_url}/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_pocketbase_health(pb_url):
    resp = httpx.get(f"{pb_url}/api/health")
    assert resp.status_code == 200


def test_user_ui_served(api_url):
    resp = httpx.get(f"{api_url}/")
    assert resp.status_code == 200
    assert "chat-screen" in resp.text


def test_admin_ui_served(api_url):
    resp = httpx.get(f"{api_url}/admin")
    assert resp.status_code == 200
    assert "RAG Chatbot" in resp.text


def test_branding_endpoint(api_url):
    resp = httpx.get(f"{api_url}/api/branding")
    assert resp.status_code == 200
    data = resp.json()
    assert "bot_name" in data
    assert "bot_icon_url" in data
