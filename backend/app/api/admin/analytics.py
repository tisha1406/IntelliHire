from fastapi import APIRouter, Depends

from app.schemas.response import APIResponse, success_response
from app.services.analytics_service import AnalyticsService
from app.auth.jwt_handler import TokenPayload, decode_jwt
from app.rbac.permissions import require_role
from app.rbac.models import UserRole

router = APIRouter(
    prefix="/admin/analytics",
    tags=["Admin - Analytics"]
)

@router.get("/dashboard", response_model=APIResponse[dict])
async def get_dashboard_stats(
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    service = AnalyticsService()
    stats = await service.get_dashboard_stats()
    
    return success_response(
        data=stats,
        message="Dashboard statistics retrieved successfully."
    )

@router.get("/hiring", response_model=APIResponse[dict])
async def get_hiring_analytics(
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    service = AnalyticsService()
    data = await service.get_hiring_analytics()
    return success_response(
        data=data,
        message="Hiring analytics retrieved."
    )

@router.get("/performance", response_model=APIResponse[dict])
async def get_performance_metrics(
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    service = AnalyticsService()
    data = await service.get_performance_metrics()
    return success_response(
        data=data,
        message="Performance metrics retrieved."
    )

@router.get("/reports", response_model=APIResponse[list[dict]])
async def get_analytics_reports(
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    service = AnalyticsService()
    data = await service.get_analytics_reports()
    return success_response(
        data=data,
        message="Custom reports retrieved."
    )

@router.get("/companies", response_model=APIResponse[list[dict]])
async def get_company_analytics(
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    from app.repositories.company_repository import CompanyRepository
    from app.repositories.interview_session_repository import InterviewSessionRepository
    from app.repositories.recruiter_repository import RecruiterRepository
    from app.repositories.campaign_repository import CampaignRepository
    
    company_repo = CompanyRepository()
    session_repo = InterviewSessionRepository()
    recruiter_repo = RecruiterRepository()
    campaign_repo = CampaignRepository()
    
    companies = await company_repo.get_many()
    
    data = []
    for c in companies:
        company_id_str = str(c["_id"])
        interviews = await session_repo.count({"company_id": c["_id"]})
        recruiters = await recruiter_repo.count({"company_id": company_id_str})
        campaigns = await campaign_repo.count({"company_id": c["_id"]})
        
        data.append({
            "company_id": company_id_str,
            "company_name": c.get("general", {}).get("name", "Unknown"),
            "status": c.get("subscription", {}).get("status", "unknown"),
            "plan": c.get("subscription", {}).get("plan", "Unknown"),
            "total_interviews": interviews,
            "total_recruiters": recruiters,
            "total_campaigns": campaigns,
            "created_at": c.get("created_at")
        })
        
    return success_response(
        data=data,
        message="Company analytics retrieved."
    )

