from fastapi import APIRouter, Depends, status

from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
)
from app.schemas.response import success_response, APIResponse
from app.services.auth_service import AuthService
from app.auth.jwt_handler import TokenPayload, decode_jwt
from app.rbac.permissions import require_role
from app.rbac.models import UserRole

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
    response_model=APIResponse[dict],
)
async def refresh_token():
    # Scaffold for refresh
    return success_response(
        data={"access_token": "new_token_here"},
        message="Token refreshed successfully."
    )


@router.post(
    "/logout",
    response_model=APIResponse[dict],
)
async def logout(token: TokenPayload = Depends(decode_jwt)):
    # Clear refresh token from DB logic can go here using auth_service.logout(token.sub)
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