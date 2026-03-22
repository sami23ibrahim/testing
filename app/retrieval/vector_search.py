from app.retrieval.base import BaseRetriever, RetrievedChunk, RetrievalParams


class VectorSearchRetriever(BaseRetriever):
    """Retrieve from Vertex AI Vector Search (Matching Engine)."""

    def __init__(self):
        from google.cloud import aiplatform
        self._aiplatform = aiplatform

    def _get_endpoint(self, params: RetrievalParams):
        return self._aiplatform.MatchingEngineIndexEndpoint(params.vec_index_endpoint)

    def _get_embedding_model(self, params: RetrievalParams):
        from vertexai.language_models import TextEmbeddingModel
        return TextEmbeddingModel.from_pretrained(params.vec_embedding_model)

    async def retrieve(self, query: str, params: RetrievalParams) -> list[RetrievedChunk]:
        embedding_model = self._get_embedding_model(params)
        embeddings = embedding_model.get_embeddings([query])
        query_embedding = embeddings[0].values

        index_endpoint = self._get_endpoint(params)

        find_kwargs: dict = {
            "deployed_index_id": params.vec_deployed_index_id,
            "queries": [query_embedding],
            "num_neighbors": params.top_k,
        }

        if params.vec_approx_neighbor_count is not None:
            find_kwargs["num_neighbors"] = params.vec_approx_neighbor_count

        if params.vec_fraction_leaf_nodes is not None:
            find_kwargs["fraction_leaf_nodes_to_search_override"] = params.vec_fraction_leaf_nodes

        if params.vec_return_full_datapoint:
            find_kwargs["return_full_datapoint"] = True

        if params.vec_filter_restricts:
            from google.cloud.aiplatform.matching_engine.matching_engine_index_endpoint import Namespace
            restricts = []
            for r in params.vec_filter_restricts:
                restricts.append(Namespace(
                    name=r.get("namespace", ""),
                    allow_tokens=r.get("allow", []),
                    deny_tokens=r.get("deny", []),
                ))
            find_kwargs["filter"] = restricts

        neighbors = index_endpoint.find_neighbors(**find_kwargs)

        chunks: list[RetrievedChunk] = []
        for match in neighbors[0]:
            chunks.append(
                RetrievedChunk(
                    text="",  # Vector Search returns IDs; text lookup is app-specific
                    score=match.distance,
                    source=match.id,
                    metadata={"restricts": getattr(match, "restricts", {})},
                )
            )
        return chunks
