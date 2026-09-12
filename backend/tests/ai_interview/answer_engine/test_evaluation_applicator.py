import pytest
from app.ai_interview.answer_engine.evaluation_applicator import EvaluationApplicator
from app.ai_interview.answer_engine.coverage_assessor import CoverageAssessment
from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress, TopicEvaluationAggregate
from app.ai_interview.answer_engine.schemas import EvaluationResult
from app.ai_interview.schemas.blueprint import InterviewBlueprint
from app.ai_interview.core.enums import InterviewState, TopicState
from app.ai_interview.answer_engine.enums import FollowUpSignal, CoverageSignal
from datetime import datetime

@pytest.fixture
def mock_session():
    bp = InterviewBlueprint(blueprint_version="1", total_question_budget=5, min_questions=1, max_questions=5, emergency_max_questions=7, topics=[])
    session = InterviewSessionSchema(
        session_id="s1", candidate_id="c1", company_id="comp1", campaign_id="camp1", mode_id="m1", mode_version=1,
        state=InterviewState.IN_PROGRESS, blueprint=bp, created_at=datetime.utcnow()
    )
    prog = TopicProgress(topic_id="t1", state=TopicState.IN_PROGRESS, evaluation_aggregate=TopicEvaluationAggregate())
    session.topic_progress.append(prog)
    return session

def test_applicator_success(mock_session):
    prog = mock_session.topic_progress[0]
    eval_res = EvaluationResult(session_id="s1", question_record_id="q1", topic_id="t1", overall_score=0.9, follow_up_signal=FollowUpSignal.NONE, qualitative_coverage_signal=CoverageSignal.QUALITATIVELY_COVERED, evidence_summary="")
    assessment = CoverageAssessment(is_covered=True)
    
    EvaluationApplicator.apply(mock_session, prog, eval_res, assessment)
    
    assert len(mock_session.evaluation_history) == 1
    assert mock_session.evaluation_history[0].evaluation_id == eval_res.evaluation_id
    assert prog.qualitatively_covered is True
    assert prog.evaluation_aggregate.answers_evaluated == 1
    assert prog.evaluation_aggregate.strong_answers == 1

def test_applicator_rollback(mock_session):
    prog = mock_session.topic_progress[0]
    # Missing fields to trigger exception if anything is wrong, or we can just mock a failure
    eval_res = None # Will throw AttributeError when applying
    assessment = CoverageAssessment(is_covered=True)
    
    with pytest.raises(Exception):
        EvaluationApplicator.apply(mock_session, prog, eval_res, assessment)
        
    assert len(mock_session.evaluation_history) == 0
    assert prog.qualitatively_covered is False
    assert prog.evaluation_aggregate.answers_evaluated == 0
