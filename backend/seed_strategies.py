import asyncio
from datetime import datetime, timezone

async def seed_strategies():
    from app.db.mongo import get_database, connect_db
    await connect_db()
    db = get_database()
    
    strategies = [
        {
            "strategy_id": "adaptive_depth",
            "name": "Adaptive Depth",
            "description": "Adapts follow-up depth based on candidate performance and focuses additional questions where evidence is weak.",
            "version": 1,
            "is_active": True,
            "applicable_interview_types": ["technical", "mixed"],
            "min_questions": 8,
            "target_questions": 10,
            "max_questions": 12,
            "max_questions_per_topic": 3,
            "max_followups_per_topic": 2,
            "strong_threshold": 0.8,
            "acceptable_threshold": 0.6,
            "weak_threshold": 0.4,
            "topic_selection_policy": {
                "policy_type": "priority_score"
            },
            "difficulty_policy": {
                "adapts": True,
                "scope": "per_topic",
                "reset_on_switch": True,
                "step_size": 1,
                "band_constrainable": True
            },
            "followup_policy": {
                "allowed_categories": ["followup_clarification", "followup_depth", "followup_evidence"],
                "max_per_topic": 2
            },
            "gap_policy": {
                "enabled": True,
                "max_share_of_budget": 0.4
            },
            "completion_policy": {
                "allow_early_exit": True,
                "require_all_critical_covered": True
            },
            "company_override_bounds": {
                "target_questions_min_delta": -2,
                "target_questions_max_delta": 2,
                "allowed_difficulty_bands": ["easy", "medium", "hard"]
            },
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "strategy_id": "fixed_coverage",
            "name": "Fixed Coverage",
            "description": "Consistent interview structure where candidates receive the same overall interview shape and topic coverage.",
            "version": 1,
            "is_active": True,
            "applicable_interview_types": ["technical", "resume_experience", "hr_behavioral", "situational_case", "mixed"],
            "min_questions": 10,
            "target_questions": 10,
            "max_questions": 10,
            "max_questions_per_topic": 2,
            "max_followups_per_topic": 1,
            "strong_threshold": 0.8,
            "acceptable_threshold": 0.6,
            "weak_threshold": 0.4,
            "topic_selection_policy": {
                "policy_type": "round_robin"
            },
            "difficulty_policy": {
                "adapts": False,
                "scope": "global",
                "reset_on_switch": False,
                "step_size": 0,
                "band_constrainable": True
            },
            "followup_policy": {
                "allowed_categories": ["followup_clarification", "followup_depth"],
                "max_per_topic": 1
            },
            "gap_policy": {
                "enabled": False,
                "max_share_of_budget": 0.0
            },
            "completion_policy": {
                "allow_early_exit": False,
                "require_all_critical_covered": True
            },
            "company_override_bounds": {
                "target_questions_min_delta": -5,
                "target_questions_max_delta": 5,
                "allowed_difficulty_bands": ["easy", "medium", "hard"]
            },
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "strategy_id": "critical_skills_deep_dive",
            "name": "Critical Skills Deep Dive",
            "description": "Prioritizes critical required skills and allows deeper verification before moving to secondary skills.",
            "version": 1,
            "is_active": True,
            "applicable_interview_types": ["technical"],
            "min_questions": 8,
            "target_questions": 12,
            "max_questions": 15,
            "max_questions_per_topic": 4,
            "max_followups_per_topic": 1,
            "critical_topic_max_followups": 3,
            "strong_threshold": 0.8,
            "acceptable_threshold": 0.6,
            "weak_threshold": 0.4,
            "topic_selection_policy": {
                "policy_type": "criticality_first"
            },
            "difficulty_policy": {
                "adapts": True,
                "scope": "per_topic",
                "reset_on_switch": True,
                "step_size": 1,
                "band_constrainable": True
            },
            "followup_policy": {
                "allowed_categories": ["followup_clarification", "followup_depth", "followup_evidence"],
                "max_per_topic": 1
            },
            "gap_policy": {
                "enabled": True,
                "max_share_of_budget": 0.5
            },
            "completion_policy": {
                "allow_early_exit": True,
                "require_all_critical_covered": True
            },
            "company_override_bounds": {
                "target_questions_min_delta": -4,
                "target_questions_max_delta": 3,
                "allowed_difficulty_bands": ["easy", "medium", "hard"]
            },
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "strategy_id": "breadth_screening",
            "name": "Breadth Screening",
            "description": "Fast first-pass screening that checks breadth across distinct topics with minimal follow-up.",
            "version": 1,
            "is_active": True,
            "applicable_interview_types": ["technical", "resume_experience", "hr_behavioral", "situational_case", "mixed"],
            "budget_mode": "distinct_topics",
            "min_questions": 0,
            "target_questions": 0,
            "max_questions": 0,
            "max_questions_per_topic": 1,
            "max_followups_per_topic": 1,
            "strong_threshold": 0.8,
            "acceptable_threshold": 0.6,
            "weak_threshold": 0.4,
            "topic_selection_policy": {
                "policy_type": "round_robin"
            },
            "difficulty_policy": {
                "adapts": False,
                "scope": "global",
                "reset_on_switch": False,
                "step_size": 0,
                "band_constrainable": False
            },
            "followup_policy": {
                "allowed_categories": ["followup_clarification"],
                "max_per_topic": 1
            },
            "gap_policy": {
                "enabled": False,
                "max_share_of_budget": 0.0
            },
            "completion_policy": {
                "allow_early_exit": True,
                "require_all_critical_covered": False
            },
            "company_override_bounds": {
                "target_questions_min_delta": -5,
                "target_questions_max_delta": 5,
                "allowed_difficulty_bands": ["medium"]
            },
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "strategy_id": "requirement_gap_verification",
            "name": "Requirement Gap Verification",
            "description": "Ensures required skills are explicitly checked even when they are missing from the candidate's resume.",
            "version": 1,
            "is_active": True,
            "applicable_interview_types": ["technical", "mixed"],
            "min_questions": 8,
            "target_questions": 10,
            "max_questions": 12,
            "max_questions_per_topic": 2,
            "max_followups_per_topic": 1,
            "strong_threshold": 0.8,
            "acceptable_threshold": 0.6,
            "weak_threshold": 0.4,
            "topic_selection_policy": {
                "policy_type": "priority_score"
            },
            "difficulty_policy": {
                "adapts": True,
                "scope": "per_topic",
                "reset_on_switch": True,
                "step_size": 1,
                "band_constrainable": True
            },
            "followup_policy": {
                "allowed_categories": ["followup_clarification", "followup_depth"],
                "max_per_topic": 1
            },
            "gap_policy": {
                "enabled": True,
                "max_share_of_budget": 0.4
            },
            "completion_policy": {
                "allow_early_exit": True,
                "require_all_critical_covered": True
            },
            "company_override_bounds": {
                "target_questions_min_delta": -2,
                "target_questions_max_delta": 2,
                "allowed_difficulty_bands": ["easy", "medium", "hard"]
            },
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "strategy_id": "behavioral_adaptive",
            "name": "Behavioral Adaptive",
            "description": "Uses structured behavioral questioning and adaptive follow-ups to gather stronger evidence about communication, teamwork, leadership, conflict handling, and similar competencies.",
            "version": 1,
            "is_active": True,
            "applicable_interview_types": ["hr_behavioral"],
            "min_questions": 5,
            "target_questions": 8,
            "max_questions": 10,
            "max_questions_per_topic": 2,
            "max_followups_per_topic": 2,
            "strong_threshold": 0.8,
            "acceptable_threshold": 0.6,
            "weak_threshold": 0.4,
            "topic_selection_policy": {
                "policy_type": "priority_score"
            },
            "difficulty_policy": {
                "adapts": False,
                "scope": "global",
                "reset_on_switch": False,
                "step_size": 0,
                "band_constrainable": False
            },
            "followup_policy": {
                "allowed_categories": ["followup_clarification", "followup_depth", "followup_evidence"],
                "max_per_topic": 2
            },
            "gap_policy": {
                "enabled": False,
                "max_share_of_budget": 0.0
            },
            "completion_policy": {
                "allow_early_exit": True,
                "require_all_critical_covered": False
            },
            "company_override_bounds": {
                "target_questions_min_delta": -3,
                "target_questions_max_delta": 2,
                "allowed_difficulty_bands": ["medium"]
            },
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
    ]

    for strat in strategies:
        # Upsert safely (Strategy ID + Version)
        await db.strategies.update_one(
            {"strategy_id": strat["strategy_id"], "version": strat["version"]},
            {
                "$set": strat,
                "$unset": {"question_budget_bounds": ""}
            },
            upsert=True
        )
        print(f"Upserted strategy: {strat['strategy_id']} v{strat['version']}")
        
    print("Strategy seeding complete.")
    
    # Let's also validate them through Pydantic
    from app.ai_interview.schemas.strategy import StrategyDefinition
    db_strats = await db.strategies.find({}).to_list(length=None)
    for s in db_strats:
        s.pop("_id", None)
        s.pop("created_at", None)
        s.pop("updated_at", None)
        try:
            StrategyDefinition(**s)
        except Exception as e:
            print(f"Validation failed for {s.get('strategy_id')}: {e}")

if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    asyncio.run(seed_strategies())
