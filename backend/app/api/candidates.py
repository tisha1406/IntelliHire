from fastapi import APIRouter, status

from app.schemas.candidate import (
    CandidateCreateRequest,
    CandidateCreateResponse,
)

router = APIRouter(
    prefix="/api/candidates",
    tags=["Candidates"],
)


@router.post(
    "/",
    response_model=CandidateCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Candidate",
    description="Register a candidate using a campaign invite token.",
)
async def register_candidate(
    request: CandidateCreateRequest,
):
    """
    Candidate Registration Endpoint

    Week 1:
    Route signature only.

    Logic will be implemented later.
    """

    return CandidateCreateResponse(
        candidate_id="dummy_candidate_id",
        jwt="dummy_jwt_token",
    )