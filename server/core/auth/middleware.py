import os
import time

from dotenv import load_dotenv
from fastapi import Request, status
from fastapi.responses import JSONResponse
from jose import JWTError, jwt

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
if not SECRET_KEY or len(SECRET_KEY.encode("utf-8")) < 32:
    raise RuntimeError("JWT_SECRET_KEY must be configured with at least 32 bytes.")
if ALGORITHM not in {"HS256", "HS384", "HS512"}:
    raise RuntimeError("JWT_ALGORITHM must be one of HS256, HS384, or HS512.")

# Exact public endpoints only. Avoid prefix checks such as /auth/login-anything.
PUBLIC_PATHS = {
    "/",
    "/auth/login",
    "/auth/signup",
    "/auth/verify-email",
    "/auth/social-login",
    "/auth/refresh-token",
    "/auth/request-reset",
    "/auth/reset-password",
    "/auth/resend-verification",
    "/docs",
    "/redoc",
    "/openapi.json",
}


async def verify_jwt_token(request: Request, call_next):
    """Require a valid access token on every non-public API route."""
    if request.url.path in PUBLIC_PATHS:
        return await call_next(request)

    authorization = request.headers.get("Authorization", "")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "A valid Bearer token is required"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token=parts[1], key=SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access" or not payload.get("sub"):
            raise JWTError("Invalid access token")
        if payload.get("exp") is None or payload["exp"] <= time.time():
            raise JWTError("Expired access token")
        request.state.user_id = payload["sub"]
    except JWTError:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid or expired authentication token"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    return await call_next(request)
