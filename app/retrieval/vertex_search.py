from app.retrieval.base import BaseRetriever, RetrievedChunk, RetrievalParams


class VertexSearchRetriever(BaseRetriever):
    """Retrieve from Vertex AI Search (Discovery Engine)."""

    def __init__(self):
        from google.cloud import discoveryengine_v1 as discoveryengine
        self._discoveryengine = discoveryengine
        self.client = discoveryengine.SearchServiceClient()

    async def retrieve(self, query: str, params: RetrievalParams) -> list[RetrievedChunk]:
        de = self._discoveryengine

        request_kwargs: dict = {
            "serving_config": params.vs_serving_config,
            "query": query,
            "page_size": params.top_k,
        }

        if params.vs_filter:
            request_kwargs["filter"] = params.vs_filter

        if params.vs_order_by:
            request_kwargs["order_by"] = params.vs_order_by

        if params.vs_boost_spec:
            request_kwargs["boost_spec"] = de.SearchRequest.BoostSpec(params.vs_boost_spec)

        if params.vs_query_expansion:
            request_kwargs["query_expansion_spec"] = de.SearchRequest.QueryExpansionSpec(
                condition=de.SearchRequest.QueryExpansionSpec.Condition.AUTO
            )

        if params.vs_spell_correction:
            request_kwargs["spell_correction_spec"] = de.SearchRequest.SpellCorrectionSpec(
                mode=de.SearchRequest.SpellCorrectionSpec.Mode.AUTO
            )

        content_search_spec_kwargs = {}
        if params.vs_summary_result_count > 0:
            content_search_spec_kwargs["summary_spec"] = de.SearchRequest.ContentSearchSpec.SummarySpec(
                summary_result_count=params.vs_summary_result_count,
                include_citations=True,
            )
        if params.vs_snippet_result_count > 0:
            content_search_spec_kwargs["snippet_spec"] = de.SearchRequest.ContentSearchSpec.SnippetSpec(
                max_snippet_count=params.vs_snippet_result_count,
                return_snippet=True,
            )
        if content_search_spec_kwargs:
            request_kwargs["content_search_spec"] = de.SearchRequest.ContentSearchSpec(
                **content_search_spec_kwargs
            )

        request = de.SearchRequest(**request_kwargs)
        response = self.client.search(request=request)

        chunks: list[RetrievedChunk] = []
        for result in response.results:
            doc = result.document
            struct_data = dict(doc.struct_data) if doc.struct_data else {}

            text = ""
            if doc.derived_struct_data:
                snippets = doc.derived_struct_data.get("snippets", [])
                if snippets:
                    text = snippets[0].get("snippet", "")
            if not text:
                text = struct_data.get("content", str(struct_data))

            chunks.append(
                RetrievedChunk(
                    text=text,
                    score=result.relevance_score if hasattr(result, "relevance_score") else 0.0,
                    source=doc.name,
                    metadata=struct_data,
                )
            )
        return chunks
