"""
Seed development data for IntelliHire.

Creates:
- 1 Admin User
- 2 Dummy Companies
- Company Campaigns
- Candidates
- Interview Sessions
- Interview Reports

Run:
python -m scripts.seed_dev_data
"""

import asyncio
from datetime import datetime, UTC, timezone
from bson import ObjectId

from app.auth.jwt_handler import hash_password
from app.db.mongo import connect_db, close_db
from app.repositories.company_repository import CompanyRepository
from app.repositories.user_repository import UserRepository
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.interview_session_repository import InterviewSessionRepository
from app.repositories.interview_report_repository import InterviewReportRepository
from app.schemas.admin import CompanyCreateRequest


ADMIN_EMAIL = "admin@intellihire.dev"
ADMIN_PASSWORD = "ChangeMe123!"

COMPANY_PASSWORD = "Company@123"


DUMMY_COMPANIES = [
    {
        "general": {
            "name": "Acme Technologies",
            "contact_email": "hr@acme.dev",
            "industry": "Technology",
            "website": "https://acme.dev"
        },
        "subscription": {
            "plan": "Enterprise",
            "status": "active",
            "billing_cycle": "annual",
            "seat_count": 5
        },
        "limits": {
            "max_recruiters": 5,
            "max_candidates": 500,
            "max_campaigns": 10,
            "monthly_interviews": 100,
            "concurrent_interviews": 5,
            "storage_limit_gb": 10.0,
            "api_requests_per_month": 10000,
            "ai_credits": 1000,
            "resume_uploads": 5000
        },
        "security": {
            "login_enabled": True,
            "mfa_required": False,
            "password_policy": "standard",
            "session_timeout_minutes": 60,
            "jwt_lifetime_hours": 24,
            "refresh_token_lifetime_days": 7,
            "sso_enabled": False,
            "allowed_domains": [],
            "ip_whitelist": [],
            "concurrent_sessions_allowed": 3,
            "remember_me_allowed": True,
            "login_attempts_before_lockout": 5
        },
        "features": {
            "reports": True,
            "analytics": True,
            "exports": True,
            "resume_screening": True,
            "interview_analysis": True,
            "voice_interview": True,
            "explainability": True,
            "branding": True,
            "api_access": True,
            "custom_questions": True
        },
        "allowed_languages": ["English", "Hindi"],
        "allowed_voices": ["Aditi"],
        "allowed_strategies": ["Balanced"],
        "allowed_interview_modes": [
            "Balanced",
            "Structured",
        ],
        "allowed_llm_tiers": [
            "Groq",
        ],
        "status": "active",
    },
    {
        "general": {
            "name": "Northwind Labs",
            "contact_email": "hr@northwind.dev",
            "industry": "Research",
            "website": "https://northwind.dev"
        },
        "subscription": {
            "plan": "Professional",
            "status": "active",
            "billing_cycle": "annual",
            "seat_count": 5
        },
        "limits": {
            "max_recruiters": 5,
            "max_candidates": 500,
            "max_campaigns": 20,
            "monthly_interviews": 100,
            "concurrent_interviews": 5,
            "storage_limit_gb": 10.0,
            "api_requests_per_month": 10000,
            "ai_credits": 1000,
            "resume_uploads": 5000
        },
        "security": {
            "login_enabled": True,
            "mfa_required": False,
            "password_policy": "standard",
            "session_timeout_minutes": 60,
            "jwt_lifetime_hours": 24,
            "refresh_token_lifetime_days": 7,
            "sso_enabled": False,
            "allowed_domains": [],
            "ip_whitelist": [],
            "concurrent_sessions_allowed": 3,
            "remember_me_allowed": True,
            "login_attempts_before_lockout": 5
        },
        "features": {
            "reports": True,
            "analytics": True,
            "exports": True,
            "resume_screening": True,
            "interview_analysis": True,
            "voice_interview": True,
            "explainability": False,
            "branding": False,
            "api_access": False,
            "custom_questions": True
        },
        "allowed_languages": ["English"],
        "allowed_voices": ["Aditi"],
        "allowed_strategies": [
            "Balanced",
            "Technical",
        ],
        "allowed_interview_modes": [
            "Deep Technical",
        ],
        "allowed_llm_tiers": [
            "Groq",
        ],
        "status": "active",
    },
]


async def seed_admin():
    user_repo = UserRepository()

    existing = await user_repo.get_by_email(
        ADMIN_EMAIL
    )

    if existing:
        print("✓ Admin already exists")
        return

    await user_repo.create(
        {
            "name": "System Administrator",
            "email": ADMIN_EMAIL,
            "password_hash": hash_password(
                ADMIN_PASSWORD
            ),
            "role": "admin",
            "company_id": None,
            "status": "active",
        }
    )

    print("✓ Admin created")


async def seed_companies():
    company_repo = CompanyRepository()

    for company in DUMMY_COMPANIES:
        existing = await company_repo.get_by_email(
            company["general"]["contact_email"],
            include_deleted=True
        )

        if existing:
            if not existing.get("company_name"):
                await company_repo.update(
                    str(existing["_id"]),
                    {
                        "company_name": existing.get("company_name")
                        or existing.get("general", {}).get("name", "")
                        or existing.get("name", ""),
                    },
                )
            print(
                f"✓ {company['general']['name']} already exists"
            )
            continue

        validated_data = CompanyCreateRequest(
            **company
        ).model_dump()

        now = datetime.now(
            timezone.utc
        ).isoformat()

        validated_data.update(
            {
                "company_name": validated_data["general"]["name"],
                "status": "active",
                "created_at": now,
                "updated_at": now,
                "created_by": "seed_script",
                "deleted_at": None,
                "deleted_by": None,
                "credentials": {
                    "username":
                        validated_data["general"]["name"]
                        .lower()
                        .replace(" ", "")
                        + "_admin",
                    "password_hash":
                        hash_password(
                            COMPANY_PASSWORD
                        ),
                    "password_must_change": True
                }
            }
        )

        await company_repo.create(
            validated_data
        )

        print(
            f"✓ Created {company['general']['name']}"
        )


async def seed_company_users():
    user_repo = UserRepository()
    company_repo = CompanyRepository()

    for company in DUMMY_COMPANIES:
        company_doc = await company_repo.get_by_email(
            company["general"]["contact_email"]
        )

        if not company_doc:
            continue

        existing = await user_repo.get_by_email(
            company["general"]["contact_email"]
        )

        if existing:
            print(
                f"✓ User already exists for {company['general']['name']}"
            )
            continue

        await user_repo.create(
            {
                "name": f"{company['general']['name']} HR",
                "email": company["general"]["contact_email"],
                "password_hash": hash_password(
                    COMPANY_PASSWORD
                ),
                "role": "company",
                "company_id": str(company_doc["_id"]),
                "status": "active",
            }
        )

        print(
             f"✓ Company user created for {company['general']['name']}"
        )


async def seed_company_interviews():
    company_repo = CompanyRepository()
    campaign_repo = CampaignRepository()
    candidate_repo = CandidateRepository()
    session_repo = InterviewSessionRepository()
    report_repo = InterviewReportRepository()

    # Get Acme Technologies
    company_doc = await company_repo.get_by_email("hr@acme.dev")
    if not company_doc:
        print("✗ Company hr@acme.dev not found for interview seeding")
        return

    company_id = company_doc["_id"]

    # Clear existing data for this company to prevent duplication
    await campaign_repo.collection.delete_many({"company_id": company_id})
    await candidate_repo.collection.delete_many({"company_id": company_id})
    await session_repo.collection.delete_many({"company_id": company_id})
    await report_repo.collection.delete_many({"company_id": company_id})

    # 1. Create a Campaign
    campaign_data = {
        "company_id": company_id,
        "name": "Lead Frontend Engineer Campaign",
        "role_target": "Lead Frontend Engineer (React)",
        "interview_type": "technical",
        "voice_config": {
            "voice_id": "Aditi",
            "language": "English",
            "accent": "Indian"
        },
        "interview_mode": "Balanced",
        "delegate_language_choice_to_candidate": False,
        "delegate_domain_choice_to_candidate": False,
        "allowed_candidate_languages": ["English"],
        "status": "active",
        "created_at": datetime.now(UTC)
    }
    campaign_id_str = await campaign_repo.create(campaign_data)
    campaign_id = ObjectId(campaign_id_str)
    print(f"✓ Created Campaign: {campaign_data['name']}")

    # 2. Seed Candidates & Sessions & Reports
    candidates_to_seed = [
        {
            "name": "Alexander Wright",
            "email": "alexander.wright@gmail.com",
            "phone": "+1 (555) 019-2834",
            "experience_level": "Senior",
            "target_role": "Lead Frontend Engineer (React)",
            "experience": "6 years",
            "education": "B.S. in Computer Science, Stanford University",
            "skills": ["React", "TypeScript", "Next.js", "CSS Modules", "System Design"],
            "aiMatch": 96,
            "resumeScore": 92,
            "interviewScore": 96,
            "currentStage": "Interviewing",
            "status": "Completed",
            "timeline": [
                {"stage": "Applied", "date": "2026-07-10", "status": "completed", "notes": "Applied online"},
                {"stage": "Resume Screen", "date": "2026-07-12", "status": "completed", "notes": "AI Match 92%"},
                {"stage": "AI Interview", "date": "2026-07-22", "status": "completed", "notes": "Completed. Score: 96/100"}
            ],
            "aiRecommendations": "Alexander demonstrated absolute mastery of advanced frontend concepts, web performance optimization, and clean state designs.",
            "notes": "Highly experienced developer. Great communication skills.",
            "session_status": "completed",
            "report": {
                "overall_score": 96,
                "interview_readiness_score": 96.0,
                "resume_match_analysis": {
                    "matched_skills": ["React", "TypeScript", "Next.js"],
                    "gap_skills": [],
                    "consistency_notes": "Strong Hire"
                },
                "topic_wise_scores": {"React Performance": 98, "React Server Components": 94},
                "technical_skills_assessment": "Exceptional React architectural logic.",
                "communication_assessment": "Clear explainability of systems design.",
                "interview_risk_assessment": {"risks": [], "severity": "low"},
                "strengths": "Exceptional React architectural logic\nHighly detailed performance rendering knowledge\nClear explainability of systems design",
                "weaknesses": "Prefers CSS Modules; less warm towards utility-first frameworks\nMight be slightly over-qualified for junior code mentoring",
                "improvement_plan": "Onboard directly into complex React and NextJS services.",
                "recruiter_summary": "Alexander demonstrated absolute mastery of advanced frontend concepts, web performance optimization, and clean state designs.",
                "questions": [
                    {
                        "q": "How would you optimize a large list of 10,000 React items updates dynamically?",
                        "a": "I would use a virtualization library like react-window, memoize list rows with React.memo, leverage CSS content-visibility: auto, and throttle scroll listener updates.",
                        "sentiment": "Excellent",
                        "score": 98
                    },
                    {
                        "q": "Explain how React 19 handles Server Components compared to standard client rendering.",
                        "a": "Server Components execute directly on the server to reduce client bundle sizes and compile state. They stream standard HTML tags and interactive nodes to the client.",
                        "sentiment": "Very Good",
                        "score": 94
                    }
                ]
            }
        },
        {
            "name": "Priya Sharma",
            "email": "priya.sharma@talentgrid.com",
            "phone": "+91 98765 43210",
            "experience_level": "Senior",
            "target_role": "Lead Frontend Engineer (React)",
            "experience": "5 years",
            "education": "B.Tech in Information Technology, IIT Bombay",
            "skills": ["React", "Redux", "Webpack", "JavaScript (ES6+)", "Sass"],
            "aiMatch": 88,
            "resumeScore": 85,
            "interviewScore": None,
            "currentStage": "Interview Scheduled",
            "status": "Scheduled",
            "timeline": [
                {"stage": "Applied", "date": "2026-07-15", "status": "completed", "notes": "Applied online"},
                {"stage": "Resume Screen", "date": "2026-07-16", "status": "completed", "notes": "AI Match 85%"},
                {"stage": "AI Interview", "date": "2026-07-23", "status": "scheduled", "notes": "Scheduled for 10:00 AM"}
            ],
            "aiRecommendations": "Priya has strong React foundational skills and experience in large-scale state management. Good fit for the frontend team.",
            "notes": "Solid background. Scheduled for technical screening.",
            "session_status": "scheduled",
            "report": None
        },
        {
            "name": "Emily Watson",
            "email": "emily.watson@talentgrid.com",
            "phone": "+1 (555) 382-9102",
            "experience_level": "Mid",
            "target_role": "Lead Frontend Engineer (React)",
            "experience": "4 years",
            "education": "M.S. in Software Engineering, Carnegie Mellon University",
            "skills": ["React", "GraphQL", "Agile", "Jira", "TypeScript"],
            "aiMatch": 85,
            "resumeScore": 82,
            "interviewScore": 86,
            "currentStage": "Selected",
            "status": "Completed",
            "timeline": [
                {"stage": "Applied", "date": "2026-07-11", "status": "completed", "notes": "Applied online"},
                {"stage": "Resume Screen", "date": "2026-07-12", "status": "completed", "notes": "AI Match 82%"},
                {"stage": "AI Interview", "date": "2026-07-19", "status": "completed", "notes": "Completed. Score: 86/100"}
            ],
            "aiRecommendations": "Emily demonstrated a good balance of technical knowledge and agile management frameworks. Clear communicator.",
            "notes": "Communicates extremely well. Strong candidate for product-focused dev role.",
            "session_status": "completed",
            "report": {
                "overall_score": 86,
                "interview_readiness_score": 86.0,
                "resume_match_analysis": {
                    "matched_skills": ["React", "TypeScript", "Agile"],
                    "gap_skills": ["CSS Modules"],
                    "consistency_notes": "Hire"
                },
                "topic_wise_scores": {"Agile Methodologies": 86, "API Design": 86},
                "technical_skills_assessment": "Good technical overview, strong API documentation.",
                "communication_assessment": "Excellent developer-to-business communications.",
                "interview_risk_assessment": {"risks": [], "severity": "low"},
                "strengths": "Excellent requirements gathering\nClear developer communication\nStrong API documentation skills",
                "weaknesses": "Familiar with basic SQL query designs but not database optimization",
                "improvement_plan": "Support her integration with technical database query tuning exercises.",
                "recruiter_summary": "Emily Watson demonstrated a good balance of technical knowledge and agile management frameworks. Clear communicator.",
                "questions": [
                    {
                        "q": "How do you resolve conflicts between engineering and marketing team requests?",
                        "a": "I prioritize based on company OKRs, customer value impact, implementation cost, and run quick scoping studies to find balanced solutions.",
                        "sentiment": "Good",
                        "score": 86
                    }
                ]
            }
        },
        {
            "name": "Carlos Mendez",
            "email": "carlos.mendez@globetech.org",
            "phone": "+1 (555) 739-1029",
            "experience_level": "Mid",
            "target_role": "Lead Frontend Engineer (React)",
            "experience": "3 years",
            "education": "B.S. in Web Development, UT Austin",
            "skills": ["HTML5", "CSS3", "JavaScript", "React", "Sass"],
            "aiMatch": 72,
            "resumeScore": 70,
            "interviewScore": None,
            "currentStage": "Rejected",
            "status": "Cancelled",
            "timeline": [
                {"stage": "Applied", "date": "2026-07-14", "status": "completed", "notes": "Applied online"},
                {"stage": "Resume Screen", "date": "2026-07-15", "status": "completed", "notes": "AI Match 70%"},
                {"stage": "AI Interview", "date": "2026-07-24", "status": "cancelled", "notes": "Cancelled by company"}
            ],
            "aiRecommendations": "Carlos has base web development skills but lacks modern React and state rendering scale practices required.",
            "notes": "Rejected due to mismatch in experience level.",
            "session_status": "cancelled",
            "report": None
        }
    ]

    for cand in candidates_to_seed:
        # Create Candidate
        cand_doc = {
            "campaign_id": campaign_id,
            "company_id": company_id,
            "name": cand["name"],
            "email": cand["email"],
            "phone": cand["phone"],
            "experience_level": cand["experience_level"],
            "target_role": cand["target_role"],
            "experience": cand["experience"],
            "education": cand["education"],
            "skills": cand["skills"],
            "aiMatch": cand["aiMatch"],
            "ai_match": cand["aiMatch"],
            "resumeScore": cand["resumeScore"],
            "resume_score": cand["resumeScore"],
            "interviewScore": cand["interviewScore"],
            "interview_score": cand["interviewScore"],
            "currentStage": cand["currentStage"],
            "current_stage": cand["currentStage"],
            "status": cand["status"],
            "timeline": cand["timeline"],
            "aiRecommendations": cand["aiRecommendations"],
            "notes": cand["notes"],
            "created_at": datetime.now(UTC)
        }
        cand_id_str = await candidate_repo.create(cand_doc)
        cand_id = ObjectId(cand_id_str)
        print(f"  ✓ Created Candidate: {cand['name']}")

        # Create Session if session_status is set
        if cand["session_status"]:
            session_doc = {
                "company_id": company_id,
                "campaign_id": campaign_id,
                "candidate_id": cand_id,
                "language": "English",
                "interview_mode": "Balanced",
                "status": "completed" if cand["session_status"] == "completed" else "cancelled" if cand["session_status"] == "cancelled" else "in_progress",
                "question_budget": {
                    "min_questions": 5,
                    "max_questions": 10,
                    "complexity_scores": {"experience": 7.0, "skills": 7.0, "projects": 7.0}
                },
                "interview_state": {
                    "current_question": "Dummy Question?",
                    "current_topic": "General",
                    "difficulty": "medium",
                    "interview_phase": "completed" if cand["session_status"] == "completed" else "active"
                },
                "turns": [],
                "created_at": datetime.now(UTC)
            }

            # Map report questions to turns if completed
            if cand["report"] and cand["report"]["questions"]:
                for idx, q_item in enumerate(cand["report"]["questions"]):
                    session_doc["turns"].append({
                        "turn_number": idx + 1,
                        "question": q_item["q"],
                        "answer_transcript": q_item["a"],
                        "response_time_seconds": 15.0,
                        "was_follow_up": False,
                        "was_blocked_by_guardrail": False,
                        "calibrate_hold_triggered": False,
                        "cheating_risk_detected": False,
                        "evaluation": {
                            "technical_score": q_item["score"] / 10.0,
                            "communication_score": q_item["score"] / 10.0,
                            "completeness_score": q_item["score"] / 10.0,
                            "logical_flow_score": q_item["score"] / 10.0,
                            "resume_consistency_score": q_item["score"] / 10.0,
                            "project_explanation_score": q_item["score"] / 10.0,
                            "professionalism_score": q_item["score"] / 10.0,
                            "response_quality_score": q_item["score"] / 10.0,
                            "topic": "Assessment",
                            "readiness_score": q_item["score"] / 10.0,
                            "suggests_follow_up": False
                        }
                    })

            session_id_str = await session_repo.create(session_doc)
            session_id = ObjectId(session_id_str)

            # Create Report if report is set
            if cand["report"]:
                rep = cand["report"]
                report_doc = {
                    "session_id": session_id,
                    "company_id": company_id,
                    "campaign_id": campaign_id,
                    "overall_score": rep["overall_score"],
                    "interview_readiness_score": rep["interview_readiness_score"],
                    "resume_match_analysis": rep["resume_match_analysis"],
                    "topic_wise_scores": rep["topic_wise_scores"],
                    "technical_skills_assessment": rep["technical_skills_assessment"],
                    "communication_assessment": rep["communication_assessment"],
                    "interview_risk_assessment": rep["interview_risk_assessment"],
                    "strengths": rep["strengths"],
                    "weaknesses": rep["weaknesses"],
                    "improvement_plan": rep["improvement_plan"],
                    "learning_resources": [],
                    "recruiter_summary": rep["recruiter_summary"],
                    "explainability": {
                        "topic_selection_explanations": [],
                        "difficulty_change_explanations": [],
                        "follow_up_explanations": [],
                        "completion_explanation": {"reason": "Completed standard flow"},
                        "readiness_score_explanation": {"formula_summary": "Standard", "score": rep["overall_score"]}
                    },
                    "generated_at": datetime.now(UTC)
                }
                await report_repo.create(report_doc)


async def main():
    print("\nSeeding IntelliHire...\n")

    await connect_db()

    try:
        await seed_admin()

        await seed_companies()

        await seed_company_users()

        await seed_company_interviews()

    finally:
        await close_db()

    print("\n✓ Seed completed successfully")


if __name__ == "__main__":
    asyncio.run(main())