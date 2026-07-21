from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    status,
)

from app.schemas.interview import (
    InterviewStartRequest,
    InterviewStartResponse,
    InterviewQuestionResponse,
    InterviewAnswerResponse,
    InterviewReportResponse,
)

router = APIRouter(
    prefix="/api/interview",
    tags=["Interview"],
)

@router.post(
    "/start",
    response_model=InterviewStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start Interview",
    description="Creates a new interview session.",
)
async def start_interview(
    request: InterviewStartRequest,
):
    """
    Week 1

    Route signature only.
    """

    return InterviewStartResponse(
        session_id="dummy_session_id",
    )

@router.get(
    "/{session_id}/next-question",
    response_model=InterviewQuestionResponse,
    summary="Get Next Question",
)
async def get_next_question(
    session_id: str,
):
    """
    Week 1

    Route signature only.
    """

    return InterviewQuestionResponse(
        question="Tell me about yourself.",
        audio_reference="dummy_audio_url",
    )

@router.post(
    "/{session_id}/answer",
    response_model=InterviewAnswerResponse,
    summary="Submit Answer",
)
async def submit_answer(
    session_id: str,
    audio: UploadFile = File(...),
    response_time_seconds: float = Form(...),
):
    """
    Week 1

    Route signature only.
    """

    return InterviewAnswerResponse(
        evaluation_summary="Placeholder evaluation.",
        next_question="Explain your final year project.",
        completed=False,
    )

@router.get(
    "/{session_id}/report",
    response_model=InterviewReportResponse,
    summary="Get Interview Report",
)
async def get_report(
    session_id: str,
):
    """
    Week 1

    Route signature only.
    """

    return InterviewReportResponse(
        report={
            "overall_score": 82,
            "technical": 85,
            "communication": 80,
        }
    )