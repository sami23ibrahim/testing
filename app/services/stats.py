"""Retrieve usage statistics from PocketBase."""

from __future__ import annotations
import httpx
from app.config import settings
from app.services.pocketbase import pb


async def get_stats() -> dict:
    """Gather stats from PocketBase collections."""
    token = await pb._admin_auth()
    base = settings.pocketbase_url

    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}

        # Total users
        r = await client.get(f"{base}/api/collections/users/records", params={"perPage": 1}, headers=headers)
        total_users = r.json().get("totalItems", 0) if r.status_code == 200 else 0

        # Users by role
        r_su = await client.get(f"{base}/api/collections/users/records", params={"filter": "role='superuser'", "perPage": 1}, headers=headers)
        superusers = r_su.json().get("totalItems", 0) if r_su.status_code == 200 else 0

        # Total chats
        r_ch = await client.get(f"{base}/api/collections/chat_history/records", params={"perPage": 1}, headers=headers)
        total_chats = r_ch.json().get("totalItems", 0) if r_ch.status_code == 200 else 0

        # Chats per backend
        backends = {}
        for be in ["none", "rag_store", "vertex_search", "vector_search"]:
            r_be = await client.get(
                f"{base}/api/collections/chat_history/records",
                params={"filter": f"backend='{be}'", "perPage": 1},
                headers=headers,
            )
            backends[be] = r_be.json().get("totalItems", 0) if r_be.status_code == 200 else 0

        # Recent chats (last 10)
        r_recent = await client.get(
            f"{base}/api/collections/chat_history/records",
            params={"sort": "-created", "perPage": 10, "fields": "id,created,backend,query"},
            headers=headers,
        )
        recent = r_recent.json().get("items", []) if r_recent.status_code == 200 else []

        # RAG configs count
        r_cfg = await client.get(f"{base}/api/collections/rag_configs/records", params={"perPage": 1}, headers=headers)
        total_configs = r_cfg.json().get("totalItems", 0) if r_cfg.status_code == 200 else 0

        # Active config
        r_active = await client.get(
            f"{base}/api/collections/rag_configs/records",
            params={"filter": "is_active=true", "perPage": 1, "fields": "id,name,retrieval_backend"},
            headers=headers,
        )
        active_items = r_active.json().get("items", []) if r_active.status_code == 200 else []
        active_config = active_items[0] if active_items else None

    return {
        "users": {
            "total": total_users,
            "superusers": superusers,
            "regular": total_users - superusers,
        },
        "chats": {
            "total": total_chats,
            "by_backend": backends,
        },
        "recent_chats": recent,
        "configs": {
            "total": total_configs,
            "active": active_config,
        },
    }
