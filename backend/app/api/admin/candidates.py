from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional
from app.repositories.candidate_repository import CandidateRepository
from app.schemas.response import APIResponse, success_response, PaginationMeta
from app.auth.jwt_handler import TokenPayload
from app.rbac.permissions import require_role
from app.rbac.models import UserRole

router = APIRouter(
    prefix="/admin/candidates",
    tags=["Admin - Candidates"]
)

@router.get("/", response_model=APIResponse[list[dict]])
async def get_all_candidates(
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None, description="Search by name or email"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    repo = CandidateRepository()
    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    if status_filter:
        query["status"] = status_filter

    candidates = await repo.get_many(query=query, limit=limit, skip=offset)
    total = await repo.count(query)

    for c in candidates:
        c["id"] = str(c["_id"])
        del c["_id"]

    return success_response(
        data=candidates,
        pagination=PaginationMeta(total=total, limit=limit, skip=offset, has_more=(offset + limit) < total),
        message="Candidates retrieved successfully."
    )

@router.get("/{candidate_id}", response_model=APIResponse[dict])
async def get_candidate(
    candidate_id: str,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    repo = CandidateRepository()
    candidate = await repo.get_by_id(candidate_id)

    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    candidate["id"] = str(candidate["_id"])
    del candidate["_id"]

    return success_response(data=candidate)
