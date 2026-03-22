import httpx
from app.config import settings


class PocketBaseClient:
    """Thin client for PocketBase REST API."""

    def __init__(self):
        self.base_url = settings.pocketbase_url
        self._admin_token: str | None = None

    async def _admin_auth(self, force_refresh: bool = False) -> str:
        if self._admin_token and not force_refresh:
            return self._admin_token
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/api/collections/_superusers/auth-with-password",
                json={
                    "identity": settings.pocketbase_admin_email,
                    "password": settings.pocketbase_admin_password,
                },
            )
            resp.raise_for_status()
            self._admin_token = resp.json()["token"]
            return self._admin_token

    async def verify_user_token(self, token: str) -> dict | None:
        """Validate a user auth token and return the user record."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/api/collections/users/auth-refresh",
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code != 200:
                return None
            return resp.json().get("record")

    async def authenticate_user(self, email: str, password: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/api/collections/users/auth-with-password",
                json={"identity": email, "password": password},
            )
            resp.raise_for_status()
            return resp.json()

    async def create_user(self, email: str, password: str, name: str = "") -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/api/collections/users/records",
                json={
                    "email": email,
                    "password": password,
                    "passwordConfirm": password,
                    "name": name,
                },
            )
            resp.raise_for_status()
            return resp.json()

    # ── RAG configuration CRUD (stored in rag_configs collection) ────

    async def get_rag_config(self, config_id: str) -> dict:
        token = await self._admin_auth()
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/api/collections/rag_configs/records/{config_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()
            return resp.json()

    async def list_rag_configs(self) -> list[dict]:
        token = await self._admin_auth()
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/api/collections/rag_configs/records",
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()
            return resp.json().get("items", [])

    async def upsert_rag_config(self, data: dict, config_id: str | None = None) -> dict:
        token = await self._admin_auth()
        async with httpx.AsyncClient() as client:
            if config_id:
                resp = await client.patch(
                    f"{self.base_url}/api/collections/rag_configs/records/{config_id}",
                    json=data,
                    headers={"Authorization": f"Bearer {token}"},
                )
            else:
                resp = await client.post(
                    f"{self.base_url}/api/collections/rag_configs/records",
                    json=data,
                    headers={"Authorization": f"Bearer {token}"},
                )
            resp.raise_for_status()
            return resp.json()

    async def delete_rag_config(self, config_id: str) -> None:
        token = await self._admin_auth()
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{self.base_url}/api/collections/rag_configs/records/{config_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()

    async def get_active_rag_config(self) -> dict | None:
        """Return the first rag_config marked as active, or the first one if none is active."""
        token = await self._admin_auth()
        async with httpx.AsyncClient() as client:
            # Try active first
            resp = await client.get(
                f"{self.base_url}/api/collections/rag_configs/records",
                params={"filter": "is_active=true", "perPage": 1},
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                if items:
                    return items[0]
            # Fallback: return the most recent config
            resp = await client.get(
                f"{self.base_url}/api/collections/rag_configs/records",
                params={"sort": "-created", "perPage": 1},
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                if items:
                    return items[0]
        return None


pb = PocketBaseClient()
