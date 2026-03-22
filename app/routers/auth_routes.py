from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.services.pocketbase import pb

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str = ""


@router.post("/login")
async def login(body: LoginRequest):
    try:
        return await pb.authenticate_user(body.email, body.password)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/register")
async def register(body: RegisterRequest):
    try:
        user = await pb.create_user(body.email, body.password, body.name)
        return {"id": user["id"], "email": user.get("email", body.email)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
