from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.auth import get_current_user
from app.config import RetrievalBackend
from app.services.chat import ask

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    query: str
    backend: RetrievalBackend | None = None  # None = use PB config or env default
    config_id: str | None = None  # PocketBase rag_config ID (optional)
    top_k: int = 5


@router.post("")
async def chat(body: ChatRequest, user: dict = Depends(get_current_user)):
    result = await ask(
        query=body.query,
        backend=body.backend,
        config_id=body.config_id,
        top_k=body.top_k,
    )
    result["user"] = user.get("email")
    return result
