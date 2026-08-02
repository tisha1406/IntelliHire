from fastapi import APIRouter, status, HTTPException

from app.schemas.candidate import (
    CandidateCreateRequest,
    CandidateCreateResponse,
)
from app.services.invitation_service import InvitationService
from app.repositories.invitation_repository import InvitationRepository
from app.auth.jwt_handler import create_access_token

router = APIRouter(
    prefix="/api/candidates",
    tags=["Candidates"],
)


@router.post(
    "/",
    response_model=CandidateCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Candidate",
    description="Register a candidate using a campaign invite token and set their password.",
)
async def register_candidate(
    request: CandidateCreateRequest,
):
    """
    Candidate Registration / Invitation Acceptance Endpoint.
    Validates the invitation token, sets the password, marks the invite as used,
    updates candidate workflow status, and returns candidate ID with a JWT.
    """
    invitation_repo = InvitationRepository()
    invitation = await invitation_repo.get_by_token(request.campaign_invite_token)
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired invitation token."
        )

    # Optional: Verify if request email matches invitation email
    if invitation["email"].lower() != request.email.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address does not match invitation."
        )

    invitation_service = InvitationService()
    try:
        await invitation_service.accept_invitation(
            token=request.campaign_invite_token,
            password=request.password
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register candidate: {str(e)}"
        )

    # Generate access token
    jwt_token = create_access_token(
        user_id=str(invitation["user_id"]),
        role="candidate",
        company_id=str(invitation["company_id"]),
        campaign_id=str(invitation["campaign_id"]),
        candidate_id=str(invitation["candidate_id"]),
    )

    return CandidateCreateResponse(
        candidate_id=str(invitation["candidate_id"]),
        jwt=jwt_token,
    )