from fastapi import APIRouter, Query, Depends
from app.schemas.response import APIResponse, success_response, PaginationMeta
from app.auth.jwt_handler import TokenPayload
from app.rbac.permissions import require_role
from app.rbac.models import UserRole
from app.services.ai_reports_service import AIReportsService

router = APIRouter(
    prefix="/admin/ai-reports",
    tags=["Admin - AI Reports"]
)

@router.get("/score-distribution", response_model=APIResponse[list[dict]])
async def get_score_distribution(
    range: str = Query("month"),
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    service = AIReportsService()
    data = await service.get_score_distribution(range)
    return success_response(data=data, message="Score distribution retrieved.")

@router.get("/company-completion", response_model=APIResponse[list[dict]])
async def get_company_completion(
    range: str = Query("month"),
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    service = AIReportsService()
    data = await service.get_company_completion_rate(range)
    return success_response(data=data, message="Company completion rate retrieved.")

@router.get("/{report_type}", response_model=APIResponse)
async def get_ai_report(
    report_type: str,
    range: str = Query("month"),
    limit: int = Query(50),
    offset: int = Query(0),
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    service = AIReportsService()
    if report_type == "executive":
        data = await service.get_executive_summary(range)
        return success_response(data=data, message="Executive summary retrieved.")
    elif report_type == "company":
        records, total = await service.get_company_performance(range, limit, offset)
        return success_response(
            data=records,
            pagination=PaginationMeta(total=total, limit=limit, skip=offset, has_more=(offset + limit) < total),
            message="Company report retrieved."
        )
    elif report_type == "candidate":
        records, total = await service.get_candidate_analytics(range, limit, offset)
        return success_response(
            data=records,
            pagination=PaginationMeta(total=total, limit=limit, skip=offset, has_more=(offset + limit) < total),
            message="Candidate report retrieved."
        )
    elif report_type == "usage":
        data = await service.get_ai_usage(range)
        return success_response(data=data, message="Usage report retrieved.")
    
    return success_response(data={}, message="Unknown report type.")
