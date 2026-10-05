from fastapi import APIRouter, Depends, status

from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
)
from app.schemas.response import success_response, APIResponse
from app.services.auth_service import AuthService
from app.auth.jwt_handler import TokenPayload, decode_jwt
from app.rbac.permissions import require_role
from app.rbac.models import UserRole
from app.repositories.user_repository import UserRepository
from app.repositories.company_repository import CompanyRepository

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)

@router.post(
    "/login",
    response_model=APIResponse[LoginResponse],
)
async def login(request: LoginRequest):
    auth_service = AuthService()

    result = await auth_service.login(
        request.email,
        request.password,
    )
    
    return success_response(data=result, message="Login successful")


@router.post(
    "/refresh",
    response_model=APIResponse[RefreshResponse],
)
async def refresh_token(request: RefreshRequest):
    auth_service = AuthService()

    result = await auth_service.refresh(request.refresh_token)

    return success_response(data=result, message="Token refreshed successfully.")


@router.post(
    "/logout",
    response_model=APIResponse[dict],
)
async def logout(token: TokenPayload = Depends(decode_jwt)):
    # G-02: revoke the authenticated account's currently stored refresh
    # token, reusing exactly the storage/lookup mechanism G-01 introduced
    # (clear_refresh_token sets refresh_token_hash/refresh_token_expires_at
    # to None, so a subsequent /api/auth/refresh can no longer match it --
    # the same "no match" path an invalid/reused token already takes).
    # token.sub is this request's own authenticated account id (from a
    # verified JWT), so only that one account's refresh token is ever
    # touched -- never another user's or company's.
    if token.role == "company":
        await CompanyRepository().clear_refresh_token(token.sub)
    else:
        await UserRepository().clear_refresh_token(token.sub)

    return success_response(message="Logged out successfully")


@router.get(
    "/profile",
    response_model=APIResponse[dict],
)
async def get_profile(token: TokenPayload = Depends(require_role(UserRole.ADMIN))):
    # Fetch admin profile from DB using auth_service.get_profile(token.sub)
    # For now returning base data from token
    return success_response(
        data={
            "id": token.sub,
            "role": token.role,
            "name": "Admin User", 
            "email": "admin@intellihire.com"
        },
        message="Profile retrieved"
    )

