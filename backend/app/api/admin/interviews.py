from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional
from app.repositories.interview_session_repository import InterviewSessionRepository
from app.schemas.response import APIResponse, success_response, PaginationMeta
from app.auth.jwt_handler import TokenPayload
from app.rbac.permissions import require_role
from app.rbac.models import UserRole

router = APIRouter(
    prefix="/admin/interviews",
    tags=["Admin - Interviews"]
)

@router.get("/", response_model=APIResponse[list[dict]])
async def get_all_interviews(
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    company_id: Optional[str] = Query(None, description="Filter by company"),
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    repo = InterviewSessionRepository()
    query = {}
    if status_filter:
        query["status"] = status_filter
    if company_id:
        query["company_id"] = company_id

    interviews = await repo.get_many(query=query, limit=limit, skip=offset)
    total = await repo.count(query)

    for i in interviews:
        i["id"] = str(i["_id"])
        del i["_id"]

    return success_response(
        data=interviews,
        pagination=PaginationMeta(total=total, limit=limit, skip=offset, has_more=(offset + limit) < total),
        message="Interviews retrieved successfully."
    )

@router.get("/{interview_id}", response_model=APIResponse[dict])
async def get_interview(
    interview_id: str,
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    repo = InterviewSessionRepository()
    interview = await repo.get_by_id(interview_id)

    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found.")

    interview["id"] = str(interview["_id"])
    del interview["_id"]

    return success_response(data=interview)

@router.get("/calendar/events", response_model=APIResponse[list[dict]])
async def get_calendar_events(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    repo = InterviewSessionRepository()
    query = {}
    # If we had proper dates we could filter, for now return all
    
    interviews = await repo.get_many(query=query, limit=100)
    
    events = []
    for i in interviews:
        events.append({
            "id": str(i["_id"]),
            "title": i.get("title", f"Interview {str(i['_id'])[:6]}"),
            "start": i.get("scheduled_at", i.get("created_at")),
            "end": i.get("scheduled_at", i.get("created_at")), # mock end
            "status": i.get("status", "scheduled"),
            "company_id": i.get("company_id")
        })

    return success_response(data=events, message="Calendar events retrieved.")
