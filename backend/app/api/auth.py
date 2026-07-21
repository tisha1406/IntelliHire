from fastapi import APIRouter

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


@router.post("/refresh")
async def refresh_token():
    """
    Refresh JWT access token.

    NOTE:
    This endpoint will be fully implemented once the
    login flow and refresh-token persistence are added.
    """
    return {
        "message": (
            "Refresh endpoint scaffold created. "
            "Implementation will be completed after "
            "login and refresh-token storage are integrated."
        )
    }