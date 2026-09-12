"""
Phase 9 — Session Creation Service (REST)
=========================================
Handles the logic for POST /api/interview/campaigns/{campaign_id}/sessions.
Validates campaign, mode, and resume context.
Runs the Blueprint Planner.
Initializes and persists the CREATED session.
"""
from typing import Dict, Any
from fastapi import HTTPException

from app.auth.jwt_handler import TokenPayload
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.interview_mode_repository import InterviewModeRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.candidate_repository import CandidateRepository
from app.ai_interview.persistence.repository import InterviewSessionRepository
from app.ai_interview.schemas.interview_mode import InterviewModeDefinition
from app.ai_interview.blueprint_planning.schemas import BlueprintPlanningRequest, JobRequirementContext, PlanningConstraints
from app.ai_interview.blueprint_planning.planner import InterviewBlueprintPlanner
from app.ai_interview.runtime.session_initializer import SessionInitializer
from app.ai_interview.transport.services.resume_context_bridge import ResumeContextBridge
from app.ai_interview.transport.services.mode_resolver import resolve_interview_mode

class SessionCreationService:
    def __init__(
        self,
        campaign_repo: CampaignRepository,
        mode_repo: InterviewModeRepository,
        resume_repo: ResumeRepository,
        candidate_repo: CandidateRepository,
        session_repo: InterviewSessionRepository
    ):
        self.campaign_repo = campaign_repo
        self.mode_repo = mode_repo
        self.resume_repo = resume_repo
        self.candidate_repo = candidate_repo
        self.session_repo = session_repo
        self.planner = InterviewBlueprintPlanner()

    async def create_session(self, token: TokenPayload, campaign_id: str) -> Dict[str, Any]:
        """
        Creates a new InterviewSession in CREATED state.
        Returns the initial session metadata.
        """
        # 1. Validate Campaign
        campaign = await self.campaign_repo.get_by_id(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        if campaign.get("status") != "active":
            raise HTTPException(status_code=400, detail="Campaign is not active")
        if str(campaign.get("company_id")) != token.company_id:
            raise HTTPException(status_code=403, detail="Campaign belongs to a different company")

        # 2. Validate Candidate
        candidate = await self.candidate_repo.get(token.candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        if str(candidate.get("campaign_id")) != campaign_id:
            raise HTTPException(status_code=403, detail="Candidate not assigned to this campaign")

        # 2.5 Duplicate Active Session Protection (Idempotency)
        existing_session = await self.session_repo.find_active_session(token.candidate_id, campaign_id)
        if existing_session:
            return {
                "session_id": existing_session.session_id,
                "state": existing_session.state.value,
                "mode_id": existing_session.mode_id,
                "topics_count": len(existing_session.blueprint.topics),
                "total_question_budget": existing_session.blueprint.total_question_budget,
                "min_questions": existing_session.blueprint.min_questions
            }

        # 3. Load Interview Mode
        try:
            mode_id = resolve_interview_mode(campaign)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        mode_doc = await self.mode_repo.get_by_mode_id(mode_id)
        if not mode_doc:
            raise HTTPException(status_code=404, detail=f"Interview mode '{mode_id}' not found or not published")
        mode_definition = InterviewModeDefinition.model_validate(mode_doc)

        # 3.5 Override Mode Difficulty with Campaign Strictness (if provided)
        strictness = campaign.get("interview_settings", {}).get("strictness")
        if strictness:
            mode_definition.settings.difficulty_policy = str(strictness).lower()

        # 4. Load & Bridge Resume Context
        # ResumeRepository.get_by_candidate uses `candidate_id` directly
        resume_doc = await self.resume_repo.get_by_candidate(token.candidate_id)
        if not resume_doc:
            raise HTTPException(status_code=422, detail="No resume analysis found for this candidate")
        candidate_context = ResumeContextBridge.build(resume_doc, token.candidate_id)

        # 5. Build Blueprint (Synchronous)
        # We need a JobRequirementContext. For now we use the campaign data and candidate's target_role.
        job_context = JobRequirementContext(
            role_title=candidate.get("target_role", campaign.get("role_target", campaign.get("name", "Unknown Role"))),
            department=campaign.get("department"),
            required_skills=campaign.get("requirements", []),
            preferred_skills=[],
            job_description=campaign.get("description"),
            experience_expectations=candidate.get("experience_level"),
            interview_duration_minutes=30
        )
        planning_request = BlueprintPlanningRequest(
            candidate_context=candidate_context,
            mode_definition=mode_definition,
            job_context=job_context,
            constraints=None
        )
        blueprint = self.planner.plan(planning_request)

        # 6. Initialize Session
        session = SessionInitializer.initialize(
            blueprint=blueprint,
            candidate_id=token.candidate_id,
            company_id=token.company_id,
            campaign_id=campaign_id,
            mode_id=mode_definition.mode_id,
            mode_version=mode_definition.version
        )

        # 7. Persist (version=0 forces an insert for new documents in our OCC scheme if implemented, 
        # or we just save normally as expected_version=0 is standard for new)
        await self.session_repo.save(session, expected_version=0)

        # 8. Return candidate-safe metadata
        return {
            "session_id": session.session_id,
            "state": session.state.value,
            "mode_id": session.mode_id,
            "topics_count": len(blueprint.topics),
            "total_question_budget": blueprint.total_question_budget,
            "min_questions": blueprint.min_questions
        }
