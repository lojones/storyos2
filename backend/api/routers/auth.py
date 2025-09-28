"""Authentication API routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from backend.api.dependencies import get_auth_service, get_current_user
from backend.api.schemas import AuthResponse, RegisterRequest, Token
from backend.services.auth_service import AuthService

router = APIRouter()


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )
    return token


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
) -> Token:
    user = auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    role = user.get("role", "user")
    token = auth_service.create_access_token(user["user_id"], role)
    return Token(access_token=token, user_role=role)


@router.post("/register", response_model=AuthResponse)
async def register(
    payload: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
    authorization: str | None = Header(default=None),
) -> AuthResponse:
    user_count = auth_service.db_manager.get_user_count()
    token = _extract_bearer_token(authorization) if authorization else None

    if user_count > 0:
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )
        current_user = auth_service.resolve_user_from_token(token)
        if current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required",
            )
    else:
        # Force the very first user to become an admin unless explicitly overridden
        if payload.role == "user":
            payload.role = "admin"  # type: ignore[assignment]

    auth_service.register_user(payload.username, payload.password, payload.role)
    return AuthResponse(user_id=payload.username, role=payload.role)


@router.get("/me", response_model=AuthResponse)
async def get_me(current_user: dict = Depends(get_current_user)) -> AuthResponse:
    return AuthResponse(user_id=current_user["user_id"], role=current_user.get("role", "user"))


__all__ = ["router"]
