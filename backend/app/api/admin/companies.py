from fastapi import APIRouter

router = APIRouter(
    prefix="/admin/companies",
    tags=["Admin - Companies"]
)


@router.get("/")
async def get_companies():
    """
    Get all companies.
    """
    return {
        "message": "Companies endpoint is ready."
    }