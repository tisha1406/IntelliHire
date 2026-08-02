from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from typing import List

from app.auth.jwt_handler import TokenPayload, decode_jwt
from app.rbac.permissions import require_role
from app.rbac.models import UserRole

from app.services.candidate_portal_service import CandidatePortalService
from app.services.resume_processing_service import ResumeProcessingService

from app.schemas.response import APIResponse, success_response, error_response
from app.schemas.candidate_portal import (
    DashboardResponse, ResumeStatusResponse, ResumeAnalysisResponse,
    ProfileResponse, ProfileUpdateRequest, SettingsResponse, SettingsUpdateRequest,
    NotificationsResponse, MarkReadRequest, SupportResponse, CreateTicketRequest,
    CreateTicketResponse, PracticeStatusResponse, StartPracticeResponse,
    CompletePracticeResponse, InterviewStatusResponse, StartInterviewResponse,
    ActivityResponse, DocumentsResponse
)

router = APIRouter(
    prefix="/api/candidate",
    tags=["Candidate Portal"],
)


def get_candidate_context(token: TokenPayload = Depends(require_role(UserRole.CANDIDATE))):
    if not token.candidate_id:
        raise HTTPException(status_code=403, detail="Candidate ID missing in token")
    return token


@router.get("/dashboard", response_model=APIResponse[DashboardResponse])
async def get_dashboard(token: TokenPayload = Depends(get_candidate_context)):
    service = CandidatePortalService()
    data = await service.get_dashboard(token.candidate_id)
    return success_response(data=data)


@router.get("/resume", response_model=APIResponse[ResumeStatusResponse])
async def get_resume_status(token: TokenPayload = Depends(get_candidate_context)):
    service = CandidatePortalService()
    data = await service.get_resume_status(token.candidate_id)
    return success_response(data=data)


@router.post("/resume", response_model=APIResponse[bool])
async def upload_resume(
    file: UploadFile = File(...),
    token: TokenPayload = Depends(get_candidate_context)
):
    # Log activity
    service = CandidatePortalService()
    await service.log_activity(token.candidate_id, "RESUME_UPLOADED", f"Uploaded resume: {file.filename}")
    
    file_bytes = await file.read()
    processor = ResumeProcessingService()
    
    # Process asynchronously if this takes long, but for now we wait (Groq is fast)
    await processor.process_resume(
        candidate_id=token.candidate_id,
        company_id=token.company_id,
        campaign_id=token.campaign_id,
        file_bytes=file_bytes,
        filename=file.filename
    )
    
    return success_response(data=True, message="Resume processed successfully")


@router.get("/resume-analysis", response_model=APIResponse[ResumeAnalysisResponse])
async def get_resume_analysis(token: TokenPayload = Depends(get_candidate_context)):
    service = CandidatePortalService()
    try:
        data = await service.get_resume_analysis(token.candidate_id)
        return success_response(data=data)
    except ValueError as e:
        return error_response(str(e))


@router.get("/profile", response_model=APIResponse[ProfileResponse])
async def get_profile(token: TokenPayload = Depends(get_candidate_context)):
    service = CandidatePortalService()
    data = await service.get_profile(token.candidate_id)
    return success_response(data=data)


@router.put("/profile", response_model=APIResponse[bool])
async def update_profile(
    req: ProfileUpdateRequest,
    token: TokenPayload = Depends(get_candidate_context)
):
    service = CandidatePortalService()
    await service.update_profile(
        candidate_id=token.candidate_id,
        phone=req.phone,
        avatar_url=req.avatar_url
    )
    await service.log_activity(token.candidate_id, "PROFILE_UPDATED", "Updated profile settings")
    return success_response(data=True)


@router.get("/settings", response_model=APIResponse[SettingsResponse])
async def get_settings(token: TokenPayload = Depends(get_candidate_context)):
    service = CandidatePortalService()
    data = await service.get_settings(token.candidate_id)
    return success_response(data=data)


@router.put("/settings", response_model=APIResponse[bool])
async def update_settings(
    req: SettingsUpdateRequest,
    token: TokenPayload = Depends(get_candidate_context)
):
    service = CandidatePortalService()
    await service.update_settings(token.candidate_id, req.model_dump())
    return success_response(data=True)


@router.get("/notifications", response_model=APIResponse[NotificationsResponse])
async def get_notifications(token: TokenPayload = Depends(get_candidate_context)):
    service = CandidatePortalService()
    data = await service.get_notifications(token.candidate_id)
    return success_response(data=data)


@router.put("/notifications/read", response_model=APIResponse[bool])
async def mark_notifications_read(
    req: MarkReadRequest,
    token: TokenPayload = Depends(get_candidate_context)
):
    service = CandidatePortalService()
    await service.mark_notifications_read(token.candidate_id, req.notification_ids)
    return success_response(data=True)


@router.get("/support", response_model=APIResponse[SupportResponse])
async def get_support(token: TokenPayload = Depends(get_candidate_context)):
    service = CandidatePortalService()
    data = await service.get_support(token.candidate_id)
    return success_response(data=data)


@router.post("/support", response_model=APIResponse[CreateTicketResponse])
async def create_support_ticket(
    req: CreateTicketRequest,
    token: TokenPayload = Depends(get_candidate_context)
):
    service = CandidatePortalService()
    ticket_id = await service.create_ticket(
        candidate_id=token.candidate_id,
        company_id=token.company_id,
        subject=req.subject,
        message=req.message
    )
    await service.log_activity(token.candidate_id, "TICKET_CREATED", f"Created support ticket: {req.subject}")
    return success_response(data=CreateTicketResponse(ticket_id=ticket_id, status="open"))


@router.get("/activity", response_model=APIResponse[ActivityResponse])
async def get_activity(token: TokenPayload = Depends(get_candidate_context)):
    service = CandidatePortalService()
    data = await service.get_activity(token.candidate_id)
    return success_response(data=data)


@router.post("/practice/start", response_model=APIResponse[bool])
async def start_practice(token: TokenPayload = Depends(get_candidate_context)):
    service = CandidatePortalService()
    await service.start_practice(token.candidate_id)
    return success_response(data=True)


@router.post("/practice/complete", response_model=APIResponse[bool])
async def complete_practice(token: TokenPayload = Depends(get_candidate_context)):
    service = CandidatePortalService()
    await service.complete_practice(token.candidate_id)
    return success_response(data=True)


@router.post("/interview/start", response_model=APIResponse[bool])
async def start_interview(token: TokenPayload = Depends(get_candidate_context)):
    service = CandidatePortalService()
    await service.start_interview(token.candidate_id)
    return success_response(data=True)


@router.get("/documents", response_model=APIResponse[DocumentsResponse])
async def get_documents(token: TokenPayload = Depends(get_candidate_context)):
    # Mock documents for now until we have real file management
    return success_response(data=DocumentsResponse(documents=[
        {"id": "1", "name": "Interview Guidelines.pdf", "type": "Company Document", "status": "Available", "date": "1 day ago"}
    ]))
