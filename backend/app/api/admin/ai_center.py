from fastapi import APIRouter, Query, Depends
from typing import Optional
from app.schemas.response import APIResponse, success_response, PaginationMeta
from app.auth.jwt_handler import TokenPayload
from app.rbac.permissions import require_role
from app.rbac.models import UserRole
from app.services.ai_center_service import AICenterService

router = APIRouter(
    prefix="/admin/ai-center",
    tags=["Admin - AI Center"]
)

# AI Insights
@router.get("/insights/usage", response_model=APIResponse[dict])
async def get_model_usage(
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    service = AICenterService()
    data = await service.get_model_usage()
    return success_response(
        data=data,
        message="Model usage insights retrieved."
    )

# Resume Screening
@router.get("/resume-screening", response_model=APIResponse[list[dict]])
async def get_resume_screening_records(
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    status_filter: Optional[str] = Query(None, alias="status"),
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    service = AICenterService()
    records, total = await service.get_resume_screening_records(limit, offset, status_filter)
        
    return success_response(
        data=records,
        pagination=PaginationMeta(total=total, limit=limit, skip=offset, has_more=(offset + limit) < total),
        message="Resume screening records retrieved."
    )

# Interview Analysis
@router.get("/interview-analysis", response_model=APIResponse[dict])
async def get_interview_analysis_summary(
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    service = AICenterService()
    data = await service.get_interview_analysis_summary()
    return success_response(
        data=data,
        message="Interview analysis retrieved."
    )

@router.get("/interview-analysis/records", response_model=APIResponse[list[dict]])
async def get_interview_analysis_records(
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    service = AICenterService()
    records, total = await service.get_interview_analysis_records(limit, offset)
    
    return success_response(
        data=records,
        pagination=PaginationMeta(total=total, limit=limit, skip=offset, has_more=(offset + limit) < total),
        message="Interview analysis records retrieved."
    )

# AI Reports
@router.get("/reports", response_model=APIResponse[list[dict]])
async def get_ai_reports(
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    service = AICenterService()
    reports, total = await service.get_ai_reports(limit, offset)
    return success_response(
        data=reports,
        pagination=PaginationMeta(total=total, limit=limit, skip=offset, has_more=(offset + limit) < total),
        message="AI Reports retrieved."
    )
