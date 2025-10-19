"""Authentication API routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from backend.api.dependencies import get_auth_service, get_current_user
from backend.api.schemas import AuthResponse, RegisterRequest, Token
from backend.logging_config import get_logger
from backend.services.auth_service import AuthService

logger = get_logger(__name__)
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
    logger.info(f"POST /api/auth/login - Login attempt for username={form_data.username}")
    user = auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.warning(f"POST /api/auth/login - Failed login attempt for username={form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    role = user.get("role", "user")

    # Reject login for pending users
    if role == "pending":
        logger.warning(f"POST /api/auth/login - Login rejected for pending user username={form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is pending approval. Please contact an administrator.",
        )

    token = auth_service.create_access_token(user["user_id"], role)
    logger.info(f"POST /api/auth/login - Successful login for username={form_data.username}, role={role}")
    return Token(access_token=token, user_role=role)


@router.post("/register", response_model=AuthResponse)
async def register(
    payload: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
    authorization: str | None = Header(default=None),
) -> AuthResponse:
    logger.info(f"POST /api/auth/register - Registration attempt for username={payload.username}")
    user_count = auth_service.db_manager.get_user_count()
    token = _extract_bearer_token(authorization) if authorization else None

    # Check if this is an admin creating a user
    is_admin_creating = False
    if token:
        try:
            current_user = auth_service.resolve_user_from_token(token)
            if current_user.get("role") == "admin":
                is_admin_creating = True
                logger.info(f"POST /api/auth/register - Admin user_id={current_user['user_id']} creating new user")
        except:
            pass

    if user_count == 0:
        # Force the very first user to become an admin
        if payload.role == "user" or payload.role == "pending":
            payload.role = "admin"  # type: ignore[assignment]
        logger.info(f"POST /api/auth/register - First user registration, setting role=admin for username={payload.username}")
    elif not is_admin_creating:
        # Public registration - force role to pending
        payload.role = "pending"  # type: ignore[assignment]
        logger.info(f"POST /api/auth/register - Public registration, setting role=pending for username={payload.username}")

    auth_service.register_user(payload.username, payload.password, payload.role)
    logger.info(f"POST /api/auth/register - Successfully registered username={payload.username}, role={payload.role}")
    return AuthResponse(user_id=payload.username, role=payload.role)


@router.get("/me", response_model=AuthResponse)
async def get_me(current_user: dict = Depends(get_current_user)) -> AuthResponse:
    logger.info(f"GET /api/auth/me - User info request for user_id={current_user['user_id']}")
    return AuthResponse(user_id=current_user["user_id"], role=current_user.get("role", "user"))


__all__ = ["router"]
