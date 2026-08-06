from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional
from app.repositories.candidate_repository import CandidateRepository
from app.schemas.response import APIResponse, success_response, PaginationMeta
from app.auth.jwt_handler import TokenPayload
from app.rbac.permissions import require_role
from app.rbac.models import UserRole
from app.db.mongo import serialize_mongo_doc
from app.utils.relations import RelationResolver

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

    serialized_candidates = serialize_mongo_doc(candidates)
    
    resolver = RelationResolver()
    populated_candidates = await resolver.populate(serialized_candidates)

    return success_response(
        data=populated_candidates,
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

    serialized_candidate = serialize_mongo_doc(candidate)
    
    resolver = RelationResolver()
    populated_candidates = await resolver.populate([serialized_candidate])
    populated_candidate = populated_candidates[0] if populated_candidates else serialized_candidate

    return success_response(data=populated_candidate)
