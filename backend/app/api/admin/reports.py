from fastapi import APIRouter, Query, Depends
from fastapi.responses import Response
from typing import Optional
from app.schemas.response import APIResponse, success_response, PaginationMeta
from app.auth.jwt_handler import TokenPayload
from app.rbac.permissions import require_role
from app.rbac.models import UserRole
from app.services.reports_service import ReportsService

router = APIRouter(
    prefix="/admin/reports",
    tags=["Admin - Reports"]
)

@router.get("/platform", response_model=APIResponse[dict])
async def get_platform_report(
    range: str = Query("monthly"),
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    service = ReportsService()
    data = await service.get_platform_report(range)
    return success_response(data=data, message="Platform report retrieved.")

@router.get("/company", response_model=APIResponse[list[dict]])
async def get_company_report(
    range: str = Query("monthly"),
    limit: int = Query(50),
    offset: int = Query(0),
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    service = ReportsService()
    records, total = await service.get_company_report(range, limit, offset)
    return success_response(
        data=records,
        pagination=PaginationMeta(total=total, limit=limit, skip=offset, has_more=(offset + limit) < total),
        message="Company report retrieved."
    )

@router.get("/interview", response_model=APIResponse[dict])
async def get_interview_report(
    range: str = Query("monthly"),
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    service = ReportsService()
    data = await service.get_interview_report(range)
    return success_response(data=data, message="Interview report retrieved.")

@router.get("/candidate", response_model=APIResponse[list[dict]])
async def get_candidate_report(
    range: str = Query("monthly"),
    limit: int = Query(50),
    offset: int = Query(0),
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    service = ReportsService()
    records, total = await service.get_candidate_report(range, limit, offset)
    return success_response(
        data=records,
        pagination=PaginationMeta(total=total, limit=limit, skip=offset, has_more=(offset + limit) < total),
        message="Candidate report retrieved."
    )

@router.get("/chart/interviews", response_model=APIResponse[list[dict]])
async def get_interviews_chart(
    range: str = Query("monthly"),
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    service = ReportsService()
    data = await service.get_interviews_chart(range)
    return success_response(data=data, message="Chart data retrieved.")

@router.post("/export/csv")
async def export_csv(
    report_type: str = Query("platform"),
    range: str = Query("monthly"),
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    service = ReportsService()
    csv_data = await service.export_csv(report_type, range)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={report_type}_report.csv"}
    )

@router.post("/export/pdf")
async def export_pdf(
    report_type: str = Query("platform"),
    range: str = Query("monthly"),
    token: TokenPayload = Depends(require_role(UserRole.ADMIN))
):
    service = ReportsService()
    pdf_bytes = await service.export_pdf(report_type, range)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={report_type}_report.pdf"}
    )
