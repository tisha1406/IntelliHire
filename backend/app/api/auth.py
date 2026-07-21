from fastapi import APIRouter

from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
)

from app.services.auth_service import AuthService

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)

@router.post(
    "/login",
    response_model=LoginResponse,
)
async def login(request: LoginRequest):
    auth_service = AuthService()

    return await auth_service.login(
        request.email,
        request.password,
    )


@router.post("/refresh")
async def refresh_token():
    return {
        "message": (
            "Refresh endpoint scaffold created. "
            "Implementation will be completed after "
            "refresh-token persistence is integrated."
        )
    }