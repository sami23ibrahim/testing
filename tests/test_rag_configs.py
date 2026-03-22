"""Tests for the /api/admin/rag-configs CRUD endpoints.

Verifies that all retrieval backend parameters can be stored,
read, updated, and deleted through the admin API.
"""

import httpx
import pytest
from tests.conftest import auth_header


@pytest.fixture(scope="module")
def superuser_token():
    resp = httpx.post(
        "http://localhost:8000/api/auth/login",
        json={"email": "test@test.com", "password": "testtest123"},
    )
    assert resp.status_code == 200
    return resp.json()["token"]


NONE_CONFIG = {
    "name": "Test Direct Gemini",
    "description": "Direct Gemini with no retrieval",
    "retrieval_backend": "none",
    "is_active": False,
    "llm_model": "gemini-2.0-flash",
    "temperature": 0.5,
    "top_k": 10,
    "max_output_tokens": 4096,
    "system_prompt": "You are a helpful test bot.",
    "top_p": 0.9,
}

RAG_STORE_CONFIG = {
    "name": "Test RAG Store",
    "description": "RAG Store backend test",
    "retrieval_backend": "rag_store",
    "is_active": False,
    "llm_model": "gemini-2.0-flash",
    "temperature": 0.2,
    "top_k": 5,
    "max_output_tokens": 2048,
    "system_prompt": "Answer using provided context.",
    "rag_corpus_name": "projects/test-project/locations/us-central1/ragCorpora/123",
    "rag_similarity_top_k": 8,
    "rag_vector_distance_threshold": 0.7,
}

VERTEX_SEARCH_CONFIG = {
    "name": "Test Vertex Search",
    "description": "Vertex AI Search test",
    "retrieval_backend": "vertex_search",
    "is_active": False,
    "llm_model": "gemini-2.0-flash",
    "temperature": 0.3,
    "top_k": 10,
    "max_output_tokens": 2048,
    "vs_serving_config": "projects/test/locations/global/servingConfigs/default",
    "vs_datastore": "projects/test/locations/global/dataStores/ds1",
    "vs_filter": "category: ANY(\"docs\")",
    "vs_order_by": "relevance_score desc",
    "vs_boost_spec": {"condition_boost_specs": [{"condition": "tag: 'important'", "boost": 0.5}]},
    "vs_query_expansion": True,
    "vs_spell_correction": True,
    "vs_summary_result_count": 3,
    "vs_snippet_result_count": 2,
}

VECTOR_SEARCH_CONFIG = {
    "name": "Test Vector Search",
    "description": "Matching Engine test",
    "retrieval_backend": "vector_search",
    "is_active": False,
    "llm_model": "gemini-2.0-flash",
    "temperature": 0.1,
    "top_k": 20,
    "max_output_tokens": 1024,
    "system_prompt": "Be concise.",
    "vec_index_endpoint": "projects/test/locations/us-central1/indexEndpoints/ep1",
    "vec_deployed_index_id": "deployed_idx_1",
    "vec_embedding_model": "text-embedding-005",
    "vec_approx_neighbor_count": 50,
    "vec_fraction_leaf_nodes": 0.05,
    "vec_filter_restricts": [{"namespace": "color", "allow": ["red", "blue"], "deny": []}],
    "vec_return_full_datapoint": True,
}


ALL_CONFIGS = [
    ("none", NONE_CONFIG),
    ("rag_store", RAG_STORE_CONFIG),
    ("vertex_search", VERTEX_SEARCH_CONFIG),
    ("vector_search", VECTOR_SEARCH_CONFIG),
]


class TestRAGConfigCRUD:
    """Test create / read / update / delete for every backend type."""

    @pytest.mark.parametrize("backend,payload", ALL_CONFIGS)
    def test_create_and_read(self, superuser_token, backend, payload):
        # Create
        resp = httpx.post(
            "http://localhost:8000/api/admin/rag-configs",
            json=payload,
            headers=auth_header(superuser_token),
        )
        assert resp.status_code == 200, f"Create {backend} failed: {resp.text}"
        config_id = resp.json()["id"]

        # Read back and verify all fields
        resp = httpx.get(
            f"http://localhost:8000/api/admin/rag-configs/{config_id}",
            headers=auth_header(superuser_token),
        )
        assert resp.status_code == 200
        data = resp.json()

        for key, expected in payload.items():
            actual = data.get(key)
            if isinstance(expected, float):
                assert abs((actual or 0) - expected) < 0.001, f"{backend}.{key}: {actual} != {expected}"
            elif expected is None:
                continue
            else:
                assert actual == expected, f"{backend}.{key}: {actual} != {expected}"

        # Cleanup
        httpx.delete(
            f"http://localhost:8000/api/admin/rag-configs/{config_id}",
            headers=auth_header(superuser_token),
        )

    @pytest.mark.parametrize("backend,payload", ALL_CONFIGS)
    def test_update(self, superuser_token, backend, payload):
        # Create
        resp = httpx.post(
            "http://localhost:8000/api/admin/rag-configs",
            json=payload,
            headers=auth_header(superuser_token),
        )
        config_id = resp.json()["id"]

        # Update
        resp = httpx.patch(
            f"http://localhost:8000/api/admin/rag-configs/{config_id}",
            json={**payload, "name": f"Updated {backend}", "temperature": 0.99},
            headers=auth_header(superuser_token),
        )
        assert resp.status_code == 200

        # Verify
        resp = httpx.get(
            f"http://localhost:8000/api/admin/rag-configs/{config_id}",
            headers=auth_header(superuser_token),
        )
        data = resp.json()
        assert data["name"] == f"Updated {backend}"
        assert abs(data["temperature"] - 0.99) < 0.001

        # Cleanup
        httpx.delete(
            f"http://localhost:8000/api/admin/rag-configs/{config_id}",
            headers=auth_header(superuser_token),
        )

    def test_list_configs(self, superuser_token):
        # Create two
        id1 = httpx.post(
            "http://localhost:8000/api/admin/rag-configs",
            json={"name": "list-test-1", "retrieval_backend": "none"},
            headers=auth_header(superuser_token),
        ).json()["id"]
        id2 = httpx.post(
            "http://localhost:8000/api/admin/rag-configs",
            json={"name": "list-test-2", "retrieval_backend": "rag_store"},
            headers=auth_header(superuser_token),
        ).json()["id"]

        resp = httpx.get(
            "http://localhost:8000/api/admin/rag-configs",
            headers=auth_header(superuser_token),
        )
        assert resp.status_code == 200
        items = resp.json()
        assert isinstance(items, list)
        assert len(items) >= 2

        # Cleanup
        httpx.delete(f"http://localhost:8000/api/admin/rag-configs/{id1}", headers=auth_header(superuser_token))
        httpx.delete(f"http://localhost:8000/api/admin/rag-configs/{id2}", headers=auth_header(superuser_token))

    def test_delete(self, superuser_token):
        cid = httpx.post(
            "http://localhost:8000/api/admin/rag-configs",
            json={"name": "delete-test", "retrieval_backend": "none"},
            headers=auth_header(superuser_token),
        ).json()["id"]

        resp = httpx.delete(
            f"http://localhost:8000/api/admin/rag-configs/{cid}",
            headers=auth_header(superuser_token),
        )
        assert resp.status_code == 200
        assert resp.json()["deleted"] is True

        resp = httpx.get(
            f"http://localhost:8000/api/admin/rag-configs/{cid}",
            headers=auth_header(superuser_token),
        )
        assert resp.status_code == 404

    def test_get_nonexistent_returns_404(self, superuser_token):
        resp = httpx.get(
            "http://localhost:8000/api/admin/rag-configs/nonexistent_id",
            headers=auth_header(superuser_token),
        )
        assert resp.status_code == 404


class TestNonSuperuserBlocked:
    def test_regular_user_cannot_list(self, api_url):
        import uuid
        email = f"regular-{uuid.uuid4().hex[:6]}@test.com"
        httpx.post(
            f"{api_url}/api/auth/register",
            json={"email": email, "password": "testtest123"},
        )
        resp = httpx.post(
            f"{api_url}/api/auth/login",
            json={"email": email, "password": "testtest123"},
        )
        token = resp.json()["token"]

        resp = httpx.get(
            f"{api_url}/api/admin/rag-configs",
            headers=auth_header(token),
        )
        assert resp.status_code == 403
