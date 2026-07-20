from fastapi import APIRouter

router = APIRouter(
    prefix="/admin/interview-modes",
    tags=["Admin - Interview Modes"]
)


@router.get("/")
async def get_interview_modes():
    """
    Get all interview modes.
    """
    return {
        "message": "Interview modes endpoint is ready."
    }