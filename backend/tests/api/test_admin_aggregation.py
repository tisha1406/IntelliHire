import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from app.db.mongo import get_database
from app.services.interview_result_service import InterviewResultService
from app.services.ai_center_service import AICenterService
from app.services.reports_service import ReportsService
from app.ai_interview.core.enums import InterviewState, DifficultyLevel, QuestionType
from app.ai_interview.answer_engine.enums import CoverageSignal, FollowUpSignal

@pytest.mark.asyncio
async def test_aggregation_matches_result_service():
    from app.db.mongo import connect_db, close_db
    await connect_db()
    db = get_database()
    await db.interview_sessions.delete_many({"session_id": "test_session_agg_1"})
    
    # Insert a dummy session
    session_id = "test_session_agg_1"
    now = datetime.now(timezone.utc)
    
    # Mock data to match schema
    session_doc = {
        "session_id": session_id,
        "candidate_id": "c1",
        "company_id": "comp1",
        "campaign_id": "camp1",
        "mode_id": "mode1",
        "mode_version": 1,
        "state": "completed",
        "blueprint": {
            "blueprint_version": "1.0",
            "total_question_budget": 5,
            "min_questions": 1,
            "max_questions": 5,
            "emergency_max_questions": 5,
            "topics": [
                {
                    "topic_id": "topic1",
                    "topic_name": "Python Basics",
                    "source": "manual",
                    "priority": 1,
                    "mandatory": True,
                    "initial_difficulty": "medium",
                    "allowed_question_types": ["initial"],
                    "question_budget": 2
                },
                {
                    "topic_id": "topic2",
                    "topic_name": "System Design",
                    "source": "manual",
                    "priority": 2,
                    "mandatory": True,
                    "initial_difficulty": "medium",
                    "allowed_question_types": ["initial"],
                    "question_budget": 1
                }
            ]
        },
        "questions_asked_total": 3,
        "question_history": [
            {
                "session_id": session_id,
                "turn_number": 1,
                "record_id": "q1",
                "topic_id": "topic1",
                "question_text": "What is a decorator?",
                "difficulty": "medium",
                "question_type": "initial",
                "dispatched_at": now.isoformat()
            },
            {
                "session_id": session_id,
                "turn_number": 2,
                "record_id": "q2",
                "topic_id": "topic1",
                "question_text": "How do generators work?",
                "difficulty": "hard",
                "question_type": "follow_up",
                "dispatched_at": now.isoformat()
            },
            {
                "session_id": session_id,
                "turn_number": 3,
                "record_id": "q3",
                "topic_id": "topic2",
                "question_text": "Design a tiny URL service.",
                "difficulty": "hard",
                "question_type": "initial",
                "dispatched_at": now.isoformat()
            }
        ],
        "evaluation_history": [
            {
                "evaluation_id": "e1",
                "question_record_id": "q1",
                "topic_id": "topic1",
                "overall_score": 0.8,
                "qualitative_coverage_signal": "qualitatively_covered",
                "follow_up_signal": "none",
                "timestamp": now.isoformat()
            },
            {
                "evaluation_id": "e2",
                "question_record_id": "q2",
                "topic_id": "topic1",
                "overall_score": 0.9,
                "qualitative_coverage_signal": "qualitatively_covered",
                "follow_up_signal": "none",
                "timestamp": now.isoformat()
            },
            {
                "evaluation_id": "e3",
                "question_record_id": "q3",
                "topic_id": "topic2",
                "overall_score": 0.4,
                "qualitative_coverage_signal": "partially_covered",
                "follow_up_signal": "none",
                "timestamp": now.isoformat()
            }
        ],
        "topic_progress": [
            {
                "topic_id": "topic1",
                "state": "covered",
                "structurally_attempted": True,
                "qualitatively_covered": True,
                "coverage_score": 1.0,
                "readiness_score": 0.85,
                "follow_up_count": 0,
                "questions_asked": 2,
                "evaluation_aggregate": {
                    "answers_evaluated": 2,
                    "cumulative_score": 1.7,
                    "average_score": 0.85,
                    "strong_answers": 2,
                    "partial_answers": 0,
                    "weak_answers": 0,
                    "insufficient_answers": 0
                }
            },
            {
                "topic_id": "topic2",
                "state": "not_started",
                "structurally_attempted": True,
                "qualitatively_covered": False,
                "coverage_score": 0.5,
                "readiness_score": 0.4,
                "follow_up_count": 0,
                "questions_asked": 1,
                "evaluation_aggregate": {
                    "answers_evaluated": 1,
                    "cumulative_score": 0.4,
                    "average_score": 0.4,
                    "strong_answers": 0,
                    "partial_answers": 1,
                    "weak_answers": 0,
                    "insufficient_answers": 0
                }
            }
        ],
        "created_at": (now - timedelta(minutes=30)).isoformat(),
        "started_at": (now - timedelta(minutes=25)).isoformat(),
        "completed_at": now.isoformat()
    }
    
    await db.interview_sessions.delete_many({})
    await db.interview_sessions.insert_one(session_doc)
    
    # 1. Use InterviewResultService
    result_svc = InterviewResultService()
    report = await result_svc.generate_result_report(session_id)
    
    # report["overall_score"] = int(round( (0.8 + 0.9 + 0.4)/3 * 100 )) = int(round(0.7 * 100)) = 70
    assert report["overall_score"] == 70
    
    # 2. Use AICenterService
    ai_svc = AICenterService()
    summary = await ai_svc.get_interview_analysis_summary()
    
    # Check that aggregation matches the calculation (70)
    assert summary["average_score"] == 70
    
    # Check difficulty distribution: 1 medium, 2 hard
    assert summary["difficulty_distribution"]["easy"] == 0
    assert summary["difficulty_distribution"]["medium"] == 1
    assert summary["difficulty_distribution"]["hard"] == 2
    
    # Check top topics
    top_topics = summary.get("top_topics", [])
    assert len(top_topics) > 0
    topic_dict = {t["topic_name"]: t["average_score"] for t in top_topics}
    assert topic_dict["Python Basics"] == 85  # 0.85 * 100
    assert topic_dict["System Design"] == 40  # 0.4 * 100
    
    # Check ReportsService
    reports_svc = ReportsService()
    interview_report = await reports_svc.get_interview_report("monthly")
    assert interview_report["average_score"] == 70
    assert interview_report["average_duration"] == 25  # 25 minutes
