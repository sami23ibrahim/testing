import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from app.config import settings
from app.routers import auth_routes, chat, admin

logger = logging.getLogger(__name__)

app = FastAPI(title="RAG Chatbot", version="1.0.0", docs_url="/api/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(chat.router)
app.include_router(admin.router)

STATIC_DIR = Path(__file__).parent / "static"


# ── Error notification middleware ──
@app.middleware("http")
async def error_notify_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as exc:
        logger.exception(f"Unhandled error on {request.method} {request.url.path}")
        # Send email in background — don't block the response
        try:
            from app.services.notifier import send_error_email
            user_email = ""
            if hasattr(request.state, "user"):
                user_email = request.state.user.get("email", "")
            send_error_email(
                error=exc,
                context=f"{request.method} {request.url.path}",
                user_email=user_email,
            )
        except Exception:
            pass
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# ── Branding endpoint (public, no auth) ──
@app.get("/api/branding")
async def branding():
    return {
        "bot_name": settings.bot_name,
        "bot_icon_url": settings.bot_icon_url,
        "welcome_title": settings.welcome_title,
        "welcome_subtitle": settings.welcome_subtitle,
        "powered_by_text": settings.powered_by_text,
    }


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# ── UI routes ──
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def user_ui():
    """Regular user chat UI — clean, no admin controls."""
    return FileResponse(STATIC_DIR / "user.html")


@app.get("/admin")
async def admin_ui():
    """Admin chat UI — backend/config selectors, stats access."""
    return FileResponse(STATIC_DIR / "index.html")
