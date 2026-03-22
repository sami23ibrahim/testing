from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.pocketbase import pb

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Validate the PocketBase JWT from the Authorization header."""
    user = await pb.verify_user_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


async def require_superuser(user: dict = Depends(get_current_user)) -> dict:
    """Only allow users whose PocketBase record has role == 'superuser'."""
    if user.get("role") != "superuser":
        raise HTTPException(status_code=403, detail="Superuser access required")
    return user
