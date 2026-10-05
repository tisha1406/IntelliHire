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
from app.ai_interview.schemas.interview_mode import InterviewModeDefinition, InterviewModeSettings
from datetime import datetime, timezone
from app.ai_interview.blueprint_planning.schemas import BlueprintPlanningRequest, JobRequirementContext, PlanningConstraints
from app.ai_interview.blueprint_planning.planner import InterviewBlueprintPlanner
from app.ai_interview.runtime.session_initializer import SessionInitializer
from app.ai_interview.transport.services.resume_context_bridge import ResumeContextBridge
from app.ai_interview.transport.services.mode_resolver import resolve_interview_mode
from app.ai_interview.core.enums import InterviewState, InterviewModeStatus
from app.ai_interview.question_engine.enums import QuestionStatus
from app.ai_interview.runtime.enums import RuntimeAction
from app.ai_interview.runtime.runtime_controller import RuntimeController

def _extract_required_skill_names(requirements) -> list:
    """Adapts a campaign's stored `requirements` to the List[str] of skill
    names JobRequirementContext.required_skills expects.

    POST /company/campaigns stores each requirement as
    {"skill": ..., "criticality": ...} (CampaignRequirement.model_dump());
    the campaign schema also allows a plain string. Criticality is not lost:
    the raw `requirements` list is still passed separately to
    SessionInitializer(campaign_requirements=...), which reads it per topic.
    """
    names = []
    for req in requirements or []:
        if isinstance(req, dict):
            name = str(req.get("skill", "")).strip()
        else:
            name = str(req).strip()
        if name:
            names.append(name)
    return names


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

    async def create_session(self, token: TokenPayload, campaign_id: str, is_practice: bool = False) -> Dict[str, Any]:
        """
        Creates a new InterviewSession in CREATED state.
        Returns the initial session metadata.
        """
        # 1. Validate Campaign (Optional for Practice)
        campaign = {}
        if campaign_id and campaign_id != "None":
            campaign = await self.campaign_repo.get_by_id(campaign_id) or {}
            if not campaign and not is_practice:
                raise HTTPException(status_code=404, detail="Campaign not found")
            if campaign and campaign.get("status") != "active" and not is_practice:
                raise HTTPException(status_code=400, detail="Campaign is not active")
            if campaign and str(campaign.get("company_id")) != token.company_id and not is_practice:
                raise HTTPException(status_code=403, detail="Campaign belongs to a different company")
        elif not is_practice:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # 2. Validate Candidate
        candidate = await self.candidate_repo.get(token.candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        if not is_practice and str(candidate.get("campaign_id")) != campaign_id:
            raise HTTPException(status_code=403, detail="Candidate not assigned to this campaign")

        # 2.5 Resolve Target Mode
        if is_practice:
            target_mode_id = "practice"
        else:
            try:
                target_mode_id = resolve_interview_mode(campaign)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

        # 2.6 Duplicate Active Session Protection (Idempotency)
        existing_session = await self.session_repo.find_active_session(
            candidate_id=token.candidate_id, 
            campaign_id=campaign_id,
            mode_id=target_mode_id
        )
        if existing_session:
            is_stuck = False
            if existing_session.state == InterviewState.IN_PROGRESS:
                last_q = existing_session.question_history[-1] if existing_session.question_history else None
                if not last_q or last_q.status != QuestionStatus.DISPATCHED:
                    is_stuck = True

            if is_stuck:
                RuntimeController.execute_transition(existing_session, RuntimeAction.FAIL)
                existing_session.generation_claim = None
                for q in existing_session.question_history:
                    q.evaluation_claim = None
                await self.session_repo.save(existing_session, expected_version=existing_session.version)
            else:
                return {
                    "session_id": existing_session.session_id,
                    "state": existing_session.state.value,
                    "mode_id": existing_session.mode_id,
                    "topics_count": len(existing_session.blueprint.topics),
                    "total_question_budget": existing_session.blueprint.total_question_budget,
                    "min_questions": existing_session.blueprint.min_questions
                }

        # 3. Load Interview Mode
        if is_practice:
            mode_definition = InterviewModeDefinition(
                mode_id="practice",
                name="Practice Mode",
                description="Conversational practice mode to help candidates warm up.",
                version=1,
                status=InterviewModeStatus.PUBLISHED,
                settings=InterviewModeSettings(
                    allowed_question_types=["initial", "follow_up"],
                    question_style="conversational",
                ),
                created_at=datetime.now(timezone.utc)
            )
        else:
            mode_doc = await self.mode_repo.get_by_mode_id(target_mode_id)
            if not mode_doc:
                raise HTTPException(status_code=404, detail=f"Interview mode '{target_mode_id}' not found or not published")
            mode_definition = InterviewModeDefinition.model_validate(mode_doc)

            # 3.5 Override Mode Difficulty with Campaign Strictness (if provided)
            strictness = campaign.get("interview_settings", {}).get("strictness")
            if strictness:
                mode_definition.settings.difficulty_policy = str(strictness).lower()

        # 4. Load & Bridge Resume Context
        # ResumeRepository.get_by_candidate uses `candidate_id` directly
        resume_doc = await self.resume_repo.get_by_candidate(token.candidate_id)
        if not resume_doc:
            if is_practice:
                resume_doc = {
                    "candidate_id": token.candidate_id,
                    "structured_resume": {
                        "personal_info": {"name": "Candidate"},
                        "professional_summary": "Practice",
                        "work_experience": [],
                        "education": [],
                        "skills": {"hard_skills": ["Practice"], "soft_skills": []}
                    },
                    "extraction_metadata": {
                        "source_type": "practice",
                        "extractor_name": "none",
                        "extractor_version": "none",
                        "character_count": 0,
                        "detected_sections": [],
                        "warning_count": 0,
                        "processing_duration_ms": 0.0
                    },
                    "quality_status": "acceptable",
                    "warnings": []
                }
                candidate_context = ResumeContextBridge.build(resume_doc, token.candidate_id)
            else:
                raise HTTPException(status_code=422, detail="No resume analysis found for this candidate")
        else:
            candidate_context = ResumeContextBridge.build(resume_doc, token.candidate_id)

        # 5. Build Blueprint
        interview_type = None
        mixed_composition = None
        if is_practice:
            from app.ai_interview.schemas.blueprint import InterviewBlueprint, TopicBlueprint
            from app.ai_interview.core.enums import DifficultyLevel, QuestionType
            blueprint = InterviewBlueprint(
                blueprint_version="practice_1.0",
                total_question_budget=3,
                min_questions=3,
                max_questions=3,
                emergency_max_questions=3,
                topics=[
                    TopicBlueprint(
                        topic_id="practice_1",
                        topic_name="Welcome to IntelliHire Practice. Could you tell me a little bit about yourself?",
                        source="practice",
                        priority=1,
                        mandatory=True,
                        initial_difficulty=DifficultyLevel.EASY,
                        allowed_question_types=[QuestionType.INITIAL],
                        question_budget=1
                    ),
                    TopicBlueprint(
                        topic_id="practice_2",
                        topic_name="What made you interested in practicing your interview skills today?",
                        source="practice",
                        priority=2,
                        mandatory=True,
                        initial_difficulty=DifficultyLevel.EASY,
                        allowed_question_types=[QuestionType.INITIAL],
                        question_budget=1
                    ),
                    TopicBlueprint(
                        topic_id="practice_3",
                        topic_name="What is one professional skill you are hoping to improve this year?",
                        source="practice",
                        priority=3,
                        mandatory=True,
                        initial_difficulty=DifficultyLevel.EASY,
                        allowed_question_types=[QuestionType.INITIAL],
                        question_budget=1
                    )
                ]
            )
        else:
            job_context = JobRequirementContext(
                role_title=candidate.get("target_role", campaign.get("role_target", campaign.get("name", "Unknown Role"))),
                department=campaign.get("department"),
                required_skills=_extract_required_skill_names(campaign.get("requirements", [])),
                preferred_skills=[],
                job_description=campaign.get("description"),
                experience_expectations=candidate.get("experience_level"),
                interview_duration_minutes=30
            )
            constraints = None

            # Derive interview_type/mixed_composition here (not just later,
            # at step 6) -- D-03: TopicSelector needs them to decide whether
            # a situational topic must be produced, which happens inside
            # self.planner.plan() below. Previously this derivation only
            # existed after blueprint planning, too late for TopicSelector to
            # ever see either field.
            i_type = campaign.get("interview_type")
            if i_type:
                from app.ai_interview.core.enums import InterviewType
                try:
                    interview_type = InterviewType(i_type)
                except ValueError:
                    pass

            m_comp = campaign.get("mixed_composition")
            if m_comp:
                from app.ai_interview.schemas.strategy import MixedComposition
                try:
                    mixed_composition = MixedComposition.model_validate(m_comp)
                except Exception:
                    pass

            # D-03: deterministically select a situational scenario (if any
            # is active for this role/domain) only when the campaign actually
            # requests situational coverage. No LLM call, no fabrication --
            # if nothing matches, selected_scenario stays None and
            # TopicSelector simply won't add a situational topic (the
            # campaign-save-time warning in campaigns.py is what surfaces
            # this absence to the company).
            selected_scenario = None
            from app.ai_interview.core.enums import InterviewType
            needs_situational = (
                interview_type == InterviewType.SITUATIONAL_CASE
                or (
                    interview_type == InterviewType.MIXED
                    and mixed_composition is not None
                    and mixed_composition.situational_case > 0
                )
            )
            if needs_situational:
                from app.repositories.scenario_repository import ScenarioRepository
                from app.ai_interview.blueprint_planning.scenario_schemas import Scenario
                scenario_doc = await ScenarioRepository().select_scenario_for_role(job_context.role_title)
                if scenario_doc:
                    selected_scenario = Scenario.model_validate(scenario_doc)

            planning_request = BlueprintPlanningRequest(
                candidate_context=candidate_context,
                mode_definition=mode_definition,
                job_context=job_context,
                constraints=constraints,
                interview_type=interview_type,
                mixed_composition=mixed_composition,
                selected_scenario=selected_scenario,
            )
            blueprint = self.planner.plan(planning_request)

        # 6. Initialize Session
        strategy_def = None
        campaign_requirements = None

        if not is_practice:
            snapshot_dict = campaign.get("strategy_snapshot")
            if snapshot_dict and "definition" in snapshot_dict:
                from app.ai_interview.schemas.strategy import StrategyDefinition
                try:
                    strategy_def = StrategyDefinition.model_validate(snapshot_dict["definition"])
                except Exception:
                    pass

            # Breadth Screening (budget_mode="distinct_topics") stores
            # min/target/max_questions as 0 in the strategies collection --
            # those are a dynamic placeholder, not a literal budget.
            # CompletionEngine treats them literally, so resolve the real
            # per-session budget here (the one place both the final,
            # deduplicated/truncated blueprint.topics and the strategy
            # definition are available) from the actual topic count, on a
            # copy of the snapshot -- the loaded strategy_def object itself
            # (and the campaign/strategies documents it came from) are never
            # mutated.
            if strategy_def is not None and strategy_def.budget_mode == "distinct_topics":
                topic_count = len(blueprint.topics)
                strategy_def = strategy_def.model_copy(update={
                    "min_questions": topic_count,
                    "target_questions": topic_count,
                    "max_questions": topic_count,
                })

            campaign_requirements = campaign.get("requirements", [])

        session = SessionInitializer.initialize(
            blueprint=blueprint,
            candidate_id=token.candidate_id,
            company_id=token.company_id,
            campaign_id=campaign_id,
            mode_id=mode_definition.mode_id,
            mode_version=mode_definition.version,
            strategy_snapshot=strategy_def,
            interview_type=interview_type,
            mixed_composition=mixed_composition,
            campaign_requirements=campaign_requirements,
            candidate_context=candidate_context if not is_practice else None,
            voice_id=campaign.get("voice_id")
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
