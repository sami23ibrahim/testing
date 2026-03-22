from app.retrieval.base import BaseRetriever, RetrievedChunk, RetrievalParams


class RAGStoreRetriever(BaseRetriever):
    """Retrieve from Vertex AI RAG Store (managed RAG corpus)."""

    async def retrieve(self, query: str, params: RetrievalParams) -> list[RetrievedChunk]:
        from vertexai.preview import rag as rag_api

        kwargs = {
            "rag_resources": [
                rag_api.RagResource(rag_corpus=params.rag_corpus_name)
            ],
            "text": query,
            "similarity_top_k": params.rag_similarity_top_k or params.top_k,
        }

        if params.rag_vector_distance_threshold is not None:
            kwargs["vector_distance_threshold"] = params.rag_vector_distance_threshold

        response = rag_api.retrieval_query(**kwargs)

        chunks: list[RetrievedChunk] = []
        for ctx in response.contexts.contexts:
            chunks.append(
                RetrievedChunk(
                    text=ctx.text,
                    score=ctx.score,
                    source=ctx.source_uri,
                    metadata={"display_name": ctx.source_display_name},
                )
            )
        return chunks
