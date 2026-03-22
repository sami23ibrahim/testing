"""Unit tests for RetrievalParams construction from PocketBase configs.

These tests verify the parameter merging logic (PB config over .env defaults)
without requiring GCP credentials or live services.
"""

import pytest
from app.retrieval.base import RetrievalParams


class FakeSettings:
    """Mimics the relevant fields from app.config.Settings."""

    rag_corpus_name = "projects/env-project/locations/us-central1/ragCorpora/env-corpus"
    vertex_search_serving_config = "projects/env-project/locations/global/servingConfigs/default"
    vertex_search_datastore = "projects/env-project/locations/global/dataStores/env-ds"
    vector_search_index_endpoint = "projects/env-project/locations/us-central1/indexEndpoints/env-ep"
    vector_search_deployed_index_id = "env-deployed-idx"
    embedding_model = "text-embedding-005"


class TestRetrievalParamsFromEnv:
    def test_defaults_from_env(self):
        params = RetrievalParams.from_env(FakeSettings())
        assert params.rag_corpus_name == FakeSettings.rag_corpus_name
        assert params.vs_serving_config == FakeSettings.vertex_search_serving_config
        assert params.vec_index_endpoint == FakeSettings.vector_search_index_endpoint
        assert params.vec_embedding_model == "text-embedding-005"
        assert params.top_k == 5

    def test_env_defaults_for_optional_fields(self):
        params = RetrievalParams.from_env(FakeSettings())
        assert params.rag_vector_distance_threshold is None
        assert params.vs_filter == ""
        assert params.vec_approx_neighbor_count is None
        assert params.vec_filter_restricts is None
        assert params.vec_return_full_datapoint is False


class TestRetrievalParamsFromPBConfig:
    def test_pb_overrides_env(self):
        cfg = {
            "rag_corpus_name": "projects/pb/locations/us/ragCorpora/pb-corpus",
            "vs_serving_config": "projects/pb/servingConfigs/custom",
            "vec_index_endpoint": "projects/pb/indexEndpoints/pb-ep",
            "vec_deployed_index_id": "pb-deployed",
            "vec_embedding_model": "text-embedding-004",
            "top_k": 15,
        }
        params = RetrievalParams.from_pb_config(cfg, FakeSettings())
        assert params.rag_corpus_name == cfg["rag_corpus_name"]
        assert params.vs_serving_config == cfg["vs_serving_config"]
        assert params.vec_index_endpoint == cfg["vec_index_endpoint"]
        assert params.vec_deployed_index_id == cfg["vec_deployed_index_id"]
        assert params.vec_embedding_model == "text-embedding-004"
        assert params.top_k == 15

    def test_pb_empty_falls_back_to_env(self):
        cfg = {
            "rag_corpus_name": "",
            "vs_serving_config": "",
            "vec_index_endpoint": "",
        }
        params = RetrievalParams.from_pb_config(cfg, FakeSettings())
        assert params.rag_corpus_name == FakeSettings.rag_corpus_name
        assert params.vs_serving_config == FakeSettings.vertex_search_serving_config
        assert params.vec_index_endpoint == FakeSettings.vector_search_index_endpoint

    def test_rag_store_params(self):
        cfg = {
            "rag_corpus_name": "projects/x/ragCorpora/c1",
            "rag_similarity_top_k": 20,
            "rag_vector_distance_threshold": 0.65,
        }
        params = RetrievalParams.from_pb_config(cfg, FakeSettings())
        assert params.rag_similarity_top_k == 20
        assert params.rag_vector_distance_threshold == 0.65

    def test_vertex_search_params(self):
        cfg = {
            "vs_serving_config": "projects/x/servingConfigs/sc",
            "vs_datastore": "projects/x/dataStores/ds",
            "vs_filter": "category: ANY(\"news\")",
            "vs_order_by": "date desc",
            "vs_boost_spec": {"condition_boost_specs": [{"condition": "a", "boost": 1.0}]},
            "vs_query_expansion": True,
            "vs_spell_correction": True,
            "vs_summary_result_count": 5,
            "vs_snippet_result_count": 3,
        }
        params = RetrievalParams.from_pb_config(cfg, FakeSettings())
        assert params.vs_filter == 'category: ANY("news")'
        assert params.vs_order_by == "date desc"
        assert params.vs_boost_spec["condition_boost_specs"][0]["boost"] == 1.0
        assert params.vs_query_expansion is True
        assert params.vs_spell_correction is True
        assert params.vs_summary_result_count == 5
        assert params.vs_snippet_result_count == 3

    def test_vector_search_params(self):
        cfg = {
            "vec_index_endpoint": "projects/x/indexEndpoints/ep",
            "vec_deployed_index_id": "dep1",
            "vec_embedding_model": "text-embedding-005",
            "vec_approx_neighbor_count": 100,
            "vec_fraction_leaf_nodes": 0.1,
            "vec_filter_restricts": [
                {"namespace": "color", "allow": ["red"], "deny": ["blue"]},
            ],
            "vec_return_full_datapoint": True,
        }
        params = RetrievalParams.from_pb_config(cfg, FakeSettings())
        assert params.vec_approx_neighbor_count == 100
        assert params.vec_fraction_leaf_nodes == 0.1
        assert len(params.vec_filter_restricts) == 1
        assert params.vec_filter_restricts[0]["namespace"] == "color"
        assert params.vec_return_full_datapoint is True

    def test_missing_keys_get_defaults(self):
        cfg = {}
        params = RetrievalParams.from_pb_config(cfg, FakeSettings())
        # Falls back to env
        assert params.rag_corpus_name == FakeSettings.rag_corpus_name
        # Optional fields stay None/default
        assert params.rag_similarity_top_k is None
        assert params.vs_query_expansion is False
        assert params.vec_return_full_datapoint is False


class TestRetrievalParamsEdgeCases:
    def test_zero_threshold_is_preserved(self):
        cfg = {"rag_vector_distance_threshold": 0.0}
        params = RetrievalParams.from_pb_config(cfg, FakeSettings())
        assert params.rag_vector_distance_threshold == 0.0

    def test_empty_restricts_list(self):
        cfg = {"vec_filter_restricts": []}
        params = RetrievalParams.from_pb_config(cfg, FakeSettings())
        assert params.vec_filter_restricts == []

    def test_none_boost_spec(self):
        cfg = {"vs_boost_spec": None}
        params = RetrievalParams.from_pb_config(cfg, FakeSettings())
        assert params.vs_boost_spec is None
