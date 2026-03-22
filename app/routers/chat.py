from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.auth import get_current_user
from app.config import RetrievalBackend
from app.services.chat import ask
from app.services import moderation

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    query: str
    backend: RetrievalBackend | None = None  # None = use PB config or env default
    config_id: str | None = None  # PocketBase rag_config ID (optional)
    top_k: int = 5


@router.post("")
async def chat(body: ChatRequest, user: dict = Depends(get_current_user)):
    # ── Check user input ──
    input_check = moderation.check(body.query)
    if input_check.blocked:
        await moderation.log_violation(
            user_id=user.get("id", ""),
            user_email=user.get("email", ""),
            text=body.query,
            category=input_check.category,
            matched=input_check.matched,
            direction="input",
        )
        raise HTTPException(status_code=422, detail={
            "message": moderation.BLOCKED_MESSAGE,
            "category": input_check.category,
        })

    result = await ask(
        query=body.query,
        backend=body.backend,
        config_id=body.config_id,
        top_k=body.top_k,
    )

    # ── Check bot output ──
    output_check = moderation.check(result.get("answer", ""))
    if output_check.blocked:
        await moderation.log_violation(
            user_id=user.get("id", ""),
            user_email=user.get("email", ""),
            text=result.get("answer", ""),
            category=output_check.category,
            matched=output_check.matched,
            direction="output",
        )
        result["answer"] = moderation.BLOCKED_OUTPUT_MESSAGE
        result["moderated"] = True

    result["user"] = user.get("email")
    return result
