from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.auth.jwt_handler import TokenPayload
from app.rbac.permissions import require_recruiter_scope
from app.schemas.response import APIResponse, success_response
from app.repositories.interview_session_repository import InterviewSessionRepository
from app.repositories.candidate_repository import CandidateRepository

router = APIRouter(
    prefix="/interviews",
    tags=["Recruiter - Interviews"]
)

@router.get("/", response_model=APIResponse[list])
async def get_recruiter_interviews(
    token: TokenPayload = Depends(require_recruiter_scope)
):
    # First get all candidates assigned to this recruiter
    candidate_repo = CandidateRepository()
    candidates = await candidate_repo.get_many({"assigned_recruiter_id": token.recruiter_id})
    candidate_ids = [str(c["_id"]) for c in candidates]
    
    if not candidate_ids:
        return success_response(data=[])
        
    repo = InterviewSessionRepository()
    interviews = await repo.get_many({"candidate_id": {"$in": candidate_ids}})
    
    for i in interviews:
        i["id"] = str(i["_id"])
        i.pop("_id", None)
        
    return success_response(data=interviews)
