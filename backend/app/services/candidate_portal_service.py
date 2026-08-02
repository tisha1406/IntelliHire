from typing import Dict, Any
from bson import ObjectId
from datetime import UTC, datetime

from app.repositories.candidate_repository import CandidateRepository
from app.repositories.candidate_workflow_repository import CandidateWorkflowRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.support_repository import SupportRepository
from app.repositories.activity_log_repository import ActivityLogRepository
from app.repositories.candidate_settings_repository import CandidateSettingsRepository
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.company_repository import CompanyRepository

from app.schemas.candidate_portal import (
    DashboardResponse,
    WorkflowStepOut,
    ResumeStatusResponse,
    ResumeAnalysisResponse,
    ProfileResponse,
    SettingsResponse,
    NotificationsResponse,
    NotificationOut,
    SupportResponse,
    FAQOut,
    TicketOut,
    PracticeStatusResponse,
    InterviewStatusResponse,
    ActivityResponse,
    ActivityEntryOut
)


class CandidatePortalService:
    def __init__(self):
        self.candidate_repo = CandidateRepository()
        self.workflow_repo = CandidateWorkflowRepository()
        self.resume_repo = ResumeRepository()
        self.notification_repo = NotificationRepository()
        self.support_repo = SupportRepository()
        self.activity_repo = ActivityLogRepository()
        self.settings_repo = CandidateSettingsRepository()
        self.campaign_repo = CampaignRepository()
        self.company_repo = CompanyRepository()

    async def get_dashboard(self, candidate_id: str) -> DashboardResponse:
        candidate = await self.candidate_repo.get_by_id(candidate_id)
        if not candidate:
            raise ValueError("Candidate not found")
        
        campaign_id = str(candidate.get("campaign_id"))
        campaign = await self.campaign_repo.get_by_id(campaign_id)
        company_id = str(campaign.get("company_id"))
        company = await self.company_repo.get_by_id(company_id)

        workflow = await self.workflow_repo.get_by_candidate(candidate_id)
        if not workflow:
            # Create default if missing (should be created during invite, but just in case)
            await self.workflow_repo.upsert(candidate_id, {
                "user_id": ObjectId(candidate.get("user_id")),
                "company_id": ObjectId(company_id),
                "campaign_id": ObjectId(campaign_id),
                "stage": "RESUME_UPLOAD_REQUIRED",
                "next_action": "UPLOAD_RESUME",
                "created_at": datetime.now(UTC)
            })
            workflow = await self.workflow_repo.get_by_candidate(candidate_id)

        # Compute readiness score
        score = 0
        if workflow.get("resume_uploaded"): score += 25
        if workflow.get("resume_analysed"): score += 25
        if workflow.get("practice_completed"): score += 25
        if workflow.get("system_check_completed"): score += 15
        if score == 90: score = 100 # all checks done bonus

        # Compute steps
        steps = [
            WorkflowStepOut(
                key="resume",
                label="Resume Analysed",
                status="completed" if workflow.get("resume_analysed") else ("in_progress" if workflow.get("resume_uploaded") else "available"),
                completed_at=str(workflow.get("resume_analysed_at")) if workflow.get("resume_analysed_at") else None
            ),
            WorkflowStepOut(
                key="practice",
                label="Practice Interview",
                status="completed" if workflow.get("practice_completed") else ("available" if workflow.get("resume_analysed") else "locked"),
                completed_at=str(workflow.get("practice_completed_at")) if workflow.get("practice_completed_at") else None
            ),
            WorkflowStepOut(
                key="official",
                label="Official Interview",
                status="completed" if workflow.get("official_completed") else ("available" if workflow.get("practice_completed") else "locked"),
                completed_at=str(workflow.get("official_completed_at")) if workflow.get("official_completed_at") else None
            )
        ]

        return DashboardResponse(
            candidate_name=candidate.get("name", ""),
            candidate_email=candidate.get("email", ""),
            company_name=company.get("general", {}).get("name", ""),
            campaign_name=campaign.get("general", {}).get("name", ""),
            job_position=campaign.get("general", {}).get("job_position", ""),
            deadline=campaign.get("settings", {}).get("deadline", ""),
            interview_duration=f'{campaign.get("settings", {}).get("duration_minutes", 45)} min',
            interview_type=campaign.get("settings", {}).get("interview_mode", "Technical"),
            interview_language=campaign.get("settings", {}).get("language", "English"),
            interview_strategy=campaign.get("settings", {}).get("strategy", "Balanced"),
            stage=workflow.get("stage", ""),
            next_action=workflow.get("next_action", ""),
            readiness_score=score,
            steps=steps
        )

    async def get_resume_status(self, candidate_id: str) -> ResumeStatusResponse:
        workflow = await self.workflow_repo.get_by_candidate(candidate_id)
        if not workflow:
            return ResumeStatusResponse(has_resume=False)
        
        has_resume = workflow.get("resume_uploaded", False)
        status = None
        if has_resume:
            status = "analysed" if workflow.get("resume_analysed") else "processing"
            
        return ResumeStatusResponse(
            has_resume=has_resume,
            status=status,
            uploaded_at=str(workflow.get("resume_uploaded_at")) if workflow.get("resume_uploaded_at") else None
        )

    async def get_resume_analysis(self, candidate_id: str) -> ResumeAnalysisResponse:
        analysis = await self.resume_repo.get_by_candidate(candidate_id)
        if not analysis:
            raise ValueError("No resume analysis found")
            
        return ResumeAnalysisResponse(**analysis)

    async def get_profile(self, candidate_id: str) -> ProfileResponse:
        candidate = await self.candidate_repo.get_by_id(candidate_id)
        if not candidate:
            raise ValueError("Candidate not found")
            
        campaign_id = str(candidate.get("campaign_id"))
        campaign = await self.campaign_repo.get_by_id(campaign_id)
        company_id = str(campaign.get("company_id"))
        company = await self.company_repo.get_by_id(company_id)
        
        return ProfileResponse(
            candidate_id=candidate_id,
            name=candidate.get("name", ""),
            email=candidate.get("email", ""),
            phone=candidate.get("phone", ""),
            company_name=company.get("general", {}).get("name", ""),
            campaign_name=campaign.get("general", {}).get("name", ""),
            job_position=campaign.get("general", {}).get("job_position", ""),
            member_since=str(candidate.get("created_at")),
            avatar_url=candidate.get("avatar_url")
        )
        
    async def update_profile(self, candidate_id: str, phone: str = None, avatar_url: str = None):
        update_data = {}
        if phone is not None: update_data["phone"] = phone
        if avatar_url is not None: update_data["avatar_url"] = avatar_url
        if update_data:
            update_data["updated_at"] = datetime.now(UTC)
            await self.candidate_repo.update(candidate_id, update_data)
        
    async def get_settings(self, candidate_id: str) -> SettingsResponse:
        settings = await self.settings_repo.get_by_candidate(candidate_id)
        if not settings:
            # Default
            return SettingsResponse(
                high_contrast=False,
                reduced_motion=False,
                sidebar_auto_collapse=True,
                interview_reminders=True,
                company_updates=True,
                result_notifications=True,
                portal_language="English",
                live_subtitles=True
            )
        return SettingsResponse(**settings)
        
    async def update_settings(self, candidate_id: str, data: dict):
        # Filter out None values
        update_data = {k: v for k, v in data.items() if v is not None}
        if update_data:
            await self.settings_repo.upsert(candidate_id, update_data)
            
    async def get_notifications(self, candidate_id: str) -> NotificationsResponse:
        notifications = await self.notification_repo.get_by_candidate(candidate_id)
        unread_count = await self.notification_repo.get_unread_count(candidate_id)
        
        out = []
        for n in notifications:
            out.append(NotificationOut(
                id=str(n["_id"]),
                type=n.get("type", "system"),
                title=n.get("title", ""),
                message=n.get("message", ""),
                read=n.get("read", False),
                created_at=str(n.get("created_at"))
            ))
            
        return NotificationsResponse(notifications=out, unread_count=unread_count)
        
    async def mark_notifications_read(self, candidate_id: str, ids: list = None):
        await self.notification_repo.mark_read(candidate_id, ids)
        
    async def get_support(self, candidate_id: str) -> SupportResponse:
        tickets = await self.support_repo.get_by_candidate(candidate_id)
        out = []
        for t in tickets:
            out.append(TicketOut(
                id=str(t["_id"]),
                subject=t.get("subject", ""),
                message=t.get("message", ""),
                status=t.get("status", "open"),
                created_at=str(t.get("created_at"))
            ))
            
        # Hardcoded FAQs for Phase 1
        faqs = [
            FAQOut(id="faq_1", question="How does the AI Voice Interview work?", answer="You will be connected to our AI system which acts as the interviewer. It will ask you questions based on the job role and dynamically adapt based on your answers. You will reply using your microphone."),
            FAQOut(id="faq_2", question="Can I pause the interview?", answer="No, once the official interview starts, it cannot be paused. Ensure you are in a quiet environment with a stable internet connection."),
            FAQOut(id="faq_3", question="Who will see my report?", answer="Your final interview report is shared directly with the hiring team at the company that invited you.")
        ]
        
        return SupportResponse(faqs=faqs, tickets=out)
        
    async def create_ticket(self, candidate_id: str, company_id: str, subject: str, message: str) -> str:
        ticket_id = await self.support_repo.create({
            "candidate_id": ObjectId(candidate_id),
            "company_id": ObjectId(company_id),
            "subject": subject,
            "message": message,
            "status": "open",
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC)
        })
        return str(ticket_id)
        
    async def get_activity(self, candidate_id: str) -> ActivityResponse:
        activities = await self.activity_repo.get_by_candidate(candidate_id)
        out = []
        for a in activities:
            out.append(ActivityEntryOut(
                id=str(a["_id"]),
                event=a.get("event", ""),
                description=a.get("description", ""),
                created_at=str(a.get("created_at"))
            ))
        return ActivityResponse(activities=out)

    async def log_activity(self, candidate_id: str, event: str, description: str, metadata: dict = None):
        await self.activity_repo.create({
            "candidate_id": ObjectId(candidate_id),
            "event": event,
            "description": description,
            "metadata": metadata or {},
            "created_at": datetime.now(UTC)
        })

    # Dummy methods for Practice & Interview for Phase 1 (to be fleshed out with real engine later)
    async def start_practice(self, candidate_id: str):
        await self.workflow_repo.set_step_status(
            candidate_id, "stage", "PRACTICE_AVAILABLE",
            {
                "practice_started": True,
                "practice_started_at": datetime.now(UTC),
                "next_action": "PRACTICE"
            }
        )
        await self.log_activity(candidate_id, "PRACTICE_STARTED", "Started practice session")

    async def complete_practice(self, candidate_id: str):
        await self.workflow_repo.set_step_status(
            candidate_id, "stage", "OFFICIAL_INTERVIEW_READY",
            {
                "practice_completed": True,
                "practice_completed_at": datetime.now(UTC),
                "next_action": "OFFICIAL_INTERVIEW"
            }
        )
        await self.log_activity(candidate_id, "PRACTICE_COMPLETED", "Completed practice session")

    async def start_interview(self, candidate_id: str):
        await self.workflow_repo.set_step_status(
            candidate_id, "stage", "INTERVIEW_IN_PROGRESS",
            {
                "official_started": True,
                "official_started_at": datetime.now(UTC),
                "next_action": "INTERVIEW_IN_PROGRESS"
            }
        )
        await self.log_activity(candidate_id, "INTERVIEW_STARTED", "Started official interview")
