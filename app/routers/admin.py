from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.auth import require_superuser
from app.services.pocketbase import pb
from app.services.stats import get_stats

router = APIRouter(prefix="/api/admin", tags=["admin"])


class RAGConfigPayload(BaseModel):
    # ── General ──
    name: str
    description: str = ""
    retrieval_backend: str = "none"
    is_active: bool = False

    # ── LLM ──
    llm_model: str = "gemini-2.0-flash"
    temperature: float = 0.3
    top_k: int = 5
    max_output_tokens: int = 2048
    system_prompt: str = ""
    top_p: float | None = None

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


@router.get("/rag-configs")
async def list_configs(_user: dict = Depends(require_superuser)):
    return await pb.list_rag_configs()


@router.get("/rag-configs/{config_id}")
async def get_config(config_id: str, _user: dict = Depends(require_superuser)):
    try:
        return await pb.get_rag_config(config_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Config not found")


@router.post("/rag-configs")
async def create_config(
    body: RAGConfigPayload, _user: dict = Depends(require_superuser)
):
    return await pb.upsert_rag_config(body.model_dump(exclude_none=True))


@router.patch("/rag-configs/{config_id}")
async def update_config(
    config_id: str, body: RAGConfigPayload, _user: dict = Depends(require_superuser)
):
    return await pb.upsert_rag_config(body.model_dump(exclude_none=True), config_id)


@router.delete("/rag-configs/{config_id}")
async def delete_config(config_id: str, _user: dict = Depends(require_superuser)):
    await pb.delete_rag_config(config_id)
    return {"deleted": True}


@router.get("/stats")
async def stats(_user: dict = Depends(require_superuser)):
    return await get_stats()


@router.get("/moderation-logs")
async def moderation_logs(
    page: int = 1,
    per_page: int = 50,
    _user: dict = Depends(require_superuser),
):
    """List moderation violation logs (most recent first)."""
    import httpx
    for attempt in range(2):
        token = await pb._admin_auth(force_refresh=attempt > 0)
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{pb.base_url}/api/collections/moderation_logs/records",
                params={"page": page, "perPage": per_page},
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code == 401 and attempt == 0:
                continue
            resp.raise_for_status()
            return resp.json()
