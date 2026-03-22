from __future__ import annotations
from app.config import settings, RetrievalBackend
from app.retrieval.base import RetrievedChunk, RetrievalParams
from app.services.pocketbase import pb

_vertexai_initialized = False
_retrievers: dict = {}


def _ensure_vertexai():
    global _vertexai_initialized
    if not _vertexai_initialized:
        import vertexai
        vertexai.init(project=settings.gcp_project_id, location=settings.gcp_location)
        _vertexai_initialized = True


def _get_model(model_name: str, system_instruction: str | None = None):
    from vertexai.generative_models import GenerativeModel
    _ensure_vertexai()
    return GenerativeModel(model_name, system_instruction=system_instruction)


def get_retriever(backend: RetrievalBackend):
    _ensure_vertexai()
    if backend not in _retrievers:
        if backend == RetrievalBackend.RAG_STORE:
            from app.retrieval.rag_store import RAGStoreRetriever
            _retrievers[backend] = RAGStoreRetriever()
        elif backend == RetrievalBackend.VERTEX_SEARCH:
            from app.retrieval.vertex_search import VertexSearchRetriever
            _retrievers[backend] = VertexSearchRetriever()
        elif backend == RetrievalBackend.VECTOR_SEARCH:
            from app.retrieval.vector_search import VectorSearchRetriever
            _retrievers[backend] = VectorSearchRetriever()
    return _retrievers[backend]


def _build_rag_prompt(query: str, chunks: list[RetrievedChunk], system_prompt: str = "") -> str:
    context = "\n\n---\n\n".join(
        f"[Source: {c.source} | Score: {c.score:.3f}]\n{c.text}" for c in chunks if c.text
    )
    prefix = system_prompt + "\n\n" if system_prompt else ""
    return (
        f"{prefix}"
        "Answer the user's question using ONLY the context below. "
        "If the context does not contain enough information, say so.\n\n"
        f"## Context\n{context}\n\n"
        f"## Question\n{query}"
    )


async def _resolve_config(config_id: str | None) -> dict | None:
    """Fetch a specific config by ID, or the active one from PocketBase."""
    if config_id:
        try:
            return await pb.get_rag_config(config_id)
        except Exception:
            return None
    return await pb.get_active_rag_config()


async def ask(
    query: str,
    backend: RetrievalBackend | None = None,
    top_k: int = 5,
    config_id: str | None = None,
    model_override: str | None = None,
    temperature_override: float | None = None,
) -> dict:
    # Load PocketBase config (system prompt, model overrides, retrieval params)
    pb_config = await _resolve_config(config_id)
    system_prompt = ""
    max_output_tokens = settings.llm_max_output_tokens
    top_p = None

    if pb_config:
        system_prompt = pb_config.get("system_prompt", "")
        if not backend:
            cfg_backend = pb_config.get("retrieval_backend", "")
            backend = RetrievalBackend(cfg_backend) if cfg_backend else settings.default_retrieval_backend
        if not model_override:
            model_override = pb_config.get("llm_model") or None
        if temperature_override is None:
            temperature_override = pb_config.get("temperature")
        if top_k == 5 and pb_config.get("top_k"):
            top_k = pb_config["top_k"]
        if pb_config.get("max_output_tokens"):
            max_output_tokens = pb_config["max_output_tokens"]
        if pb_config.get("top_p") is not None:
            top_p = pb_config["top_p"]

    backend = backend or settings.default_retrieval_backend
    model_name = model_override or settings.llm_model
    temperature = temperature_override if temperature_override is not None else settings.llm_temperature

    # Build retrieval params from PB config merged with .env defaults
    if pb_config:
        retrieval_params = RetrievalParams.from_pb_config(pb_config, settings)
        retrieval_params.top_k = top_k
    else:
        retrieval_params = RetrievalParams.from_env(settings)
        retrieval_params.top_k = top_k

    gen_config: dict = {
        "temperature": temperature,
        "max_output_tokens": max_output_tokens,
    }
    if top_p is not None:
        gen_config["top_p"] = top_p

    # ── Direct Gemini mode (no retrieval) ──
    if backend == RetrievalBackend.NONE:
        model = _get_model(model_name, system_instruction=system_prompt or None)
        response = model.generate_content(query, generation_config=gen_config)
        return {
            "answer": response.text,
            "backend": "none",
            "config_id": pb_config["id"] if pb_config else None,
            "sources": [],
        }

    # ── RAG mode (with retrieval) ──
    retriever = get_retriever(backend)
    chunks = await retriever.retrieve(query, retrieval_params)

    model = _get_model(model_name)
    prompt = _build_rag_prompt(query, chunks, system_prompt)
    response = model.generate_content(prompt, generation_config=gen_config)

    return {
        "answer": response.text,
        "backend": backend.value,
        "config_id": pb_config["id"] if pb_config else None,
        "sources": [
            {"source": c.source, "score": c.score, "text": c.text[:200]}
            for c in chunks
        ],
    }
