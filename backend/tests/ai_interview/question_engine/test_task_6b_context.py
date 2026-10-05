import pytest
from app.ai_interview.core.enums import (
    InterviewType, TopicDimension, QuestionCategory, 
    RequirementCriticality, ResumeEvidence, QuestionType, DifficultyLevel, TopicSource, InterviewState
)
from app.ai_interview.question_engine.question_turn_planner import QuestionTurnPlanner
from app.ai_interview.question_engine.question_request_builder import QuestionRequestBuilder
from app.ai_interview.question_engine.schemas import QuestionTurnPlan, QuestionGenerationRequest
from app.ai_interview.question_engine.llm_question_generator import LLMQuestionGenerator
from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress
from app.ai_interview.schemas.blueprint import InterviewBlueprint, TopicBlueprint
from app.ai_interview.runtime.schemas import RuntimeDecision, RuntimeAction
from app.ai_interview.schemas.strategy import StrategyDefinition

def _mock_provider():
    class MockProvider:
        def generate_structured(self, system_prompt, user_prompt, response_model, temperature):
            return {"system_prompt": system_prompt, "user_prompt": user_prompt}
    return MockProvider()

def test_planner_sets_context_fields():
    session = InterviewSessionSchema.model_construct(
        session_id="s1", candidate_id="c1", company_id="c1", campaign_id="c1",
        mode_id="m1", mode_version=1,
        state=InterviewState.IN_PROGRESS, questions_asked_total=0,
        interview_type=InterviewType.MIXED,
        blueprint=InterviewBlueprint.model_construct(
            topics=[TopicBlueprint.model_construct(topic_id="t1", topic_name="Docker", question_budget=3, allowed_question_types=[QuestionType.INITIAL], initial_difficulty=DifficultyLevel.MEDIUM)],
            total_question_budget=10, min_questions=1, emergency_max_questions=10
        ),
        topic_progress=[
            TopicProgress(
                topic_id="t1",
                dimension=TopicDimension.TECHNICAL,
                source=TopicSource.REQUIREMENT,
                criticality=RequirementCriticality.CRITICAL,
                resume_evidence=ResumeEvidence.STRONG,
                campaign_requirement="Docker",
                questions_asked=0
            )
        ]
    )
    decision = RuntimeDecision(
        current_state=session.state, allowed_action=RuntimeAction.ADVANCE_TOPIC, active_topic_id="t1"
    )
    
    plan = QuestionTurnPlanner.plan(session, decision)
    
    assert plan.allowed is True
    assert plan.interview_type == InterviewType.MIXED
    assert plan.dimension == TopicDimension.TECHNICAL
    assert plan.category == QuestionCategory.NEW
    assert plan.resume_evidence == ResumeEvidence.STRONG
    assert plan.campaign_requirement == "Docker"
    assert plan.requirement_criticality == RequirementCriticality.CRITICAL

def test_builder_propagates_context_fields(candidate_context, interview_mode):
    plan = QuestionTurnPlan(
        session_id="s1", topic_id="t1", topic_name="Docker", difficulty=DifficultyLevel.MEDIUM,
        allowed_question_types=[QuestionType.INITIAL], topic_question_budget=3, topic_questions_asked=0,
        total_question_budget=10, total_questions_asked=0, turn_number=1, allowed=True,
        interview_type=InterviewType.MIXED, dimension=TopicDimension.TECHNICAL,
        category=QuestionCategory.NEW, resume_evidence=ResumeEvidence.STRONG,
        campaign_requirement="Docker", requirement_criticality=RequirementCriticality.CRITICAL
    )
    
    req = QuestionRequestBuilder.build(plan, candidate_context, interview_mode, [])
    
    assert req.interview_type == InterviewType.MIXED
    assert req.dimension == TopicDimension.TECHNICAL
    assert req.category == QuestionCategory.NEW
    assert req.resume_evidence == ResumeEvidence.STRONG
    assert req.requirement_criticality == RequirementCriticality.CRITICAL
    assert req.campaign_requirement == "Docker"


