from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class RetrievedChunk:
    text: str
    score: float
    source: str  # identifier / URI of the source document
    metadata: dict


@dataclass
class RetrievalParams:
    """All backend-specific parameters extracted from a PocketBase rag_config."""

    top_k: int = 5

    # ── RAG Store ──
    rag_corpus_name: str = ""
    rag_similarity_top_k: int | None = None
    rag_vector_distance_threshold: float | None = None

    # ── Vertex AI Search ──
    vs_serving_config: str = ""
    vs_datastore: str = ""
    vs_filter: str = ""
    vs_order_by: str = ""
    vs_boost_spec: dict | None = None
    vs_query_expansion: bool = False
    vs_spell_correction: bool = False
    vs_summary_result_count: int = 0
    vs_snippet_result_count: int = 0

    # ── Vector Search (Matching Engine) ──
    vec_index_endpoint: str = ""
    vec_deployed_index_id: str = ""
    vec_embedding_model: str = ""
    vec_approx_neighbor_count: int | None = None
    vec_fraction_leaf_nodes: float | None = None
    vec_filter_restricts: list[dict] | None = None
    vec_return_full_datapoint: bool = False

    @classmethod
    def from_pb_config(cls, cfg: dict, env_settings) -> "RetrievalParams":
        """Build params by merging PocketBase config over .env defaults."""
        return cls(
            top_k=cfg.get("top_k") or 5,
            # RAG Store
            rag_corpus_name=cfg.get("rag_corpus_name") or env_settings.rag_corpus_name,
            rag_similarity_top_k=cfg.get("rag_similarity_top_k"),
            rag_vector_distance_threshold=cfg.get("rag_vector_distance_threshold"),
            # Vertex Search
            vs_serving_config=cfg.get("vs_serving_config") or env_settings.vertex_search_serving_config,
            vs_datastore=cfg.get("vs_datastore") or env_settings.vertex_search_datastore,
            vs_filter=cfg.get("vs_filter") or "",
            vs_order_by=cfg.get("vs_order_by") or "",
            vs_boost_spec=cfg.get("vs_boost_spec"),
            vs_query_expansion=bool(cfg.get("vs_query_expansion")),
            vs_spell_correction=bool(cfg.get("vs_spell_correction")),
            vs_summary_result_count=cfg.get("vs_summary_result_count") or 0,
            vs_snippet_result_count=cfg.get("vs_snippet_result_count") or 0,
            # Vector Search
            vec_index_endpoint=cfg.get("vec_index_endpoint") or env_settings.vector_search_index_endpoint,
            vec_deployed_index_id=cfg.get("vec_deployed_index_id") or env_settings.vector_search_deployed_index_id,
            vec_embedding_model=cfg.get("vec_embedding_model") or env_settings.embedding_model,
            vec_approx_neighbor_count=cfg.get("vec_approx_neighbor_count"),
            vec_fraction_leaf_nodes=cfg.get("vec_fraction_leaf_nodes"),
            vec_filter_restricts=cfg.get("vec_filter_restricts"),
            vec_return_full_datapoint=bool(cfg.get("vec_return_full_datapoint")),
        )

    @classmethod
    def from_env(cls, env_settings) -> "RetrievalParams":
        """Build params purely from .env defaults."""
        return cls(
            rag_corpus_name=env_settings.rag_corpus_name,
            vs_serving_config=env_settings.vertex_search_serving_config,
            vs_datastore=env_settings.vertex_search_datastore,
            vec_index_endpoint=env_settings.vector_search_index_endpoint,
            vec_deployed_index_id=env_settings.vector_search_deployed_index_id,
            vec_embedding_model=env_settings.embedding_model,
        )


class BaseRetriever(ABC):
    @abstractmethod
    async def retrieve(self, query: str, params: RetrievalParams) -> list[RetrievedChunk]:
        ...
