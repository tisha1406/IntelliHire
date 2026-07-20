from fastapi import APIRouter

router = APIRouter(
    prefix="/admin/strategies",
    tags=["Admin - Strategies"]
)


@router.get("/")
async def get_strategies():
    """
    Get all interview strategies.
    """
    return {
        "message": "Strategies endpoint is ready."
    }