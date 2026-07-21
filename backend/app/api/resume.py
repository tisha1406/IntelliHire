from fastapi import APIRouter, UploadFile, File, status

from app.schemas.resume import ResumeProfileResponse

router = APIRouter(
    prefix="/api/resume",
    tags=["Resume"],
)


@router.post(
    "/upload",
    response_model=ResumeProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload Resume",
    description="Upload candidate resume for processing.",
)
async def upload_resume(
    file: UploadFile = File(...)
):
    """
    Week 1

    Route signature only.
    Resume parsing will be implemented later.
    """

    return ResumeProfileResponse(
        candidate_name="Demo Candidate",
        email="candidate@example.com",
        skills=[
            "Python",
            "FastAPI",
            "MongoDB",
        ],
        education=[
            "B.Tech Computer Engineering",
        ],
        experience=[
            "Intern at ABC Company",
        ],
    )