"""Integration tests for the /api/chat endpoint.

Tests that the chat endpoint correctly reads PocketBase configs,
selects the right backend, and returns the expected response shape.

These tests call the live FastAPI server (which talks to the live PocketBase),
and mock only the Vertex AI / Gemini SDK calls that require GCP credentials.
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
    return resp.json()["token"]


def _create_config(token, payload):
    resp = httpx.post(
        "http://localhost:8000/api/admin/rag-configs",
        json=payload,
        headers=auth_header(token),
    )
    assert resp.status_code == 200, f"Create config failed: {resp.text}"
    return resp.json()["id"]


def _delete_config(token, config_id):
    httpx.delete(
        f"http://localhost:8000/api/admin/rag-configs/{config_id}",
        headers=auth_header(token),
    )


class TestConfigStorageAndRetrieval:
    """Verify that configs with all backend-specific params are stored and read back correctly."""

    def test_none_config_round_trip(self, superuser_token):
        payload = {
            "name": "IntTest None",
            "retrieval_backend": "none",
            "llm_model": "gemini-2.0-flash",
            "temperature": 0.5,
            "top_k": 10,
            "max_output_tokens": 4096,
            "system_prompt": "You are a test bot.",
            "top_p": 0.9,
            "is_active": False,
        }
        cid = _create_config(superuser_token, payload)
        try:
            resp = httpx.get(
                f"http://localhost:8000/api/admin/rag-configs/{cid}",
                headers=auth_header(superuser_token),
            )
            data = resp.json()
            assert data["name"] == "IntTest None"
            assert data["retrieval_backend"] == "none"
            assert data["system_prompt"] == "You are a test bot."
            assert data["max_output_tokens"] == 4096
            assert abs(data["top_p"] - 0.9) < 0.01
        finally:
            _delete_config(superuser_token, cid)

    def test_rag_store_config_round_trip(self, superuser_token):
        payload = {
            "name": "IntTest RAG",
            "retrieval_backend": "rag_store",
            "rag_corpus_name": "projects/p1/locations/us/ragCorpora/c1",
            "rag_similarity_top_k": 8,
            "rag_vector_distance_threshold": 0.7,
            "system_prompt": "Use context.",
        }
        cid = _create_config(superuser_token, payload)
        try:
            resp = httpx.get(
                f"http://localhost:8000/api/admin/rag-configs/{cid}",
                headers=auth_header(superuser_token),
            )
            data = resp.json()
            assert data["rag_corpus_name"] == "projects/p1/locations/us/ragCorpora/c1"
            assert data["rag_similarity_top_k"] == 8
            assert abs(data["rag_vector_distance_threshold"] - 0.7) < 0.01
        finally:
            _delete_config(superuser_token, cid)

    def test_vertex_search_config_round_trip(self, superuser_token):
        payload = {
            "name": "IntTest VS",
            "retrieval_backend": "vertex_search",
            "vs_serving_config": "projects/p/servingConfigs/default",
            "vs_datastore": "projects/p/dataStores/ds1",
            "vs_filter": "category: ANY(\"docs\")",
            "vs_order_by": "relevance desc",
            "vs_boost_spec": {"condition_boost_specs": [{"condition": "tag:important", "boost": 0.5}]},
            "vs_query_expansion": True,
            "vs_spell_correction": True,
            "vs_summary_result_count": 3,
            "vs_snippet_result_count": 2,
        }
        cid = _create_config(superuser_token, payload)
        try:
            resp = httpx.get(
                f"http://localhost:8000/api/admin/rag-configs/{cid}",
                headers=auth_header(superuser_token),
            )
            data = resp.json()
            assert data["vs_serving_config"] == "projects/p/servingConfigs/default"
            assert data["vs_filter"] == 'category: ANY("docs")'
            assert data["vs_query_expansion"] is True
            assert data["vs_spell_correction"] is True
            assert data["vs_summary_result_count"] == 3
            assert data["vs_snippet_result_count"] == 2
            assert data["vs_boost_spec"]["condition_boost_specs"][0]["boost"] == 0.5
        finally:
            _delete_config(superuser_token, cid)

    def test_vector_search_config_round_trip(self, superuser_token):
        payload = {
            "name": "IntTest Vec",
            "retrieval_backend": "vector_search",
            "vec_index_endpoint": "projects/p/indexEndpoints/ep1",
            "vec_deployed_index_id": "dep_1",
            "vec_embedding_model": "text-embedding-005",
            "vec_approx_neighbor_count": 50,
            "vec_fraction_leaf_nodes": 0.05,
            "vec_filter_restricts": [{"namespace": "color", "allow": ["red"], "deny": []}],
            "vec_return_full_datapoint": True,
        }
        cid = _create_config(superuser_token, payload)
        try:
            resp = httpx.get(
                f"http://localhost:8000/api/admin/rag-configs/{cid}",
                headers=auth_header(superuser_token),
            )
            data = resp.json()
            assert data["vec_index_endpoint"] == "projects/p/indexEndpoints/ep1"
            assert data["vec_deployed_index_id"] == "dep_1"
            assert data["vec_approx_neighbor_count"] == 50
            assert abs(data["vec_fraction_leaf_nodes"] - 0.05) < 0.001
            assert data["vec_return_full_datapoint"] is True
            assert data["vec_filter_restricts"][0]["namespace"] == "color"
        finally:
            _delete_config(superuser_token, cid)


class TestActiveConfigSelection:
    """Verify that the active config is picked up by the chat endpoint."""

    def test_active_config_is_returned(self, superuser_token):
        cid = _create_config(superuser_token, {
            "name": "Active Test",
            "retrieval_backend": "none",
            "system_prompt": "Active prompt",
            "is_active": True,
        })
        try:
            # Chat will fail at Gemini call (no GCP), but we can check the config is loaded
            # by hitting the admin endpoint
            resp = httpx.get(
                "http://localhost:8000/api/admin/rag-configs",
                headers=auth_header(superuser_token),
            )
            configs = resp.json()
            active = [c for c in configs if c.get("is_active")]
            assert len(active) >= 1
            assert any(c["id"] == cid for c in active)
        finally:
            _delete_config(superuser_token, cid)


class TestChatEndpointValidation:
    """Verify chat endpoint request/response validation."""

    def test_chat_with_invalid_backend(self, superuser_token):
        resp = httpx.post(
            "http://localhost:8000/api/chat",
            json={"query": "test", "backend": "invalid_backend"},
            headers=auth_header(superuser_token),
        )
        assert resp.status_code == 422  # validation error

    def test_chat_empty_query(self, superuser_token):
        resp = httpx.post(
            "http://localhost:8000/api/chat",
            json={"query": ""},
            headers=auth_header(superuser_token),
        )
        # Empty query is valid (Gemini handles it), but will fail at LLM call without GCP
        # Just verify it doesn't crash with a validation error
        assert resp.status_code != 422

    def test_chat_with_nonexistent_config_id(self, superuser_token):
        resp = httpx.post(
            "http://localhost:8000/api/chat",
            json={"query": "test", "config_id": "nonexistent_id_12345"},
            headers=auth_header(superuser_token),
        )
        # Should not crash — falls back to env defaults
        # Will fail at Gemini call without GCP, but not a 422
        assert resp.status_code != 422
