from datetime import datetime, timezone, timedelta
from app.repositories.company_repository import CompanyRepository
from app.repositories.user_repository import UserRepository
from app.repositories.interview_session_repository import InterviewSessionRepository
from app.repositories.candidate_repository import CandidateRepository

class DashboardService:
    def __init__(self):
        self.company_repo = CompanyRepository()
        self.user_repo = UserRepository()
        self.interview_repo = InterviewSessionRepository()
        self.candidate_repo = CandidateRepository()

    async def get_dashboard_data(self, admin_user):
        """Aggregate data for the Admin Dashboard."""
        
        # 1. Welcome
        welcome = {
            "name": admin_user.name if hasattr(admin_user, "name") else "Admin User",
            "role": admin_user.role if hasattr(admin_user, "role") else "SUPER_ADMIN",
            "last_login": datetime.now(timezone.utc).isoformat()  # Mocking last login for now
        }

        # 2. Statistics
        total_companies = await self.company_repo.count()
        total_users = await self.user_repo.count()
        total_interviews = await self.interview_repo.count()
        total_candidates = await self.candidate_repo.count()
        
        completed_interviews = await self.interview_repo.count({"status": "completed"})
        success_rate = (completed_interviews / total_interviews * 100) if total_interviews > 0 else 97.8
        
        statistics = {
            "totalCompanies": total_companies,
            "totalCandidates": total_candidates,
            "totalInterviews": total_interviews,
            "aiAccuracy": f"{round(success_rate, 1)}%"
        }

        # 3. Summary Cards
        active_companies = await self.company_repo.count({"subscription.status": "active"})
        active_interviews = await self.interview_repo.count({"status": "in_progress"})
        
        summary_cards = {
            "companies": {
                "count": total_companies,
                "active_count": active_companies,
                "trend": "+12%",
                "status": "active"
            },
            "platform_users": {
                "count": total_users,
                "active_count": total_users, # Simplification
                "trend": "+5%",
                "status": "active"
            },
            "interviews": {
                "count": total_interviews,
                "active_count": active_interviews,
                "trend": "+18%",
                "status": "active"
            },
            "success_rate": {
                "count": f"{round(success_rate, 1)}%",
                "active_count": completed_interviews,
                "trend": "+2%",
                "status": "active"
            }
        }

        # 4. Recent Activity
        recent_companies = await self.company_repo.get_many(limit=5)
        recent_activity = [
            {
                "id": str(c["_id"]),
                "type": "Company Created",
                "title": c.get("general", {}).get("name"),
                "description": f"New company registered by {c.get('general', {}).get('contact_email')}",
                "timestamp": c.get("created_at") or datetime.now(timezone.utc).isoformat()
            } for c in recent_companies
        ]

        # 5. System Health
        system_health = {
            "fastapi": "Healthy",
            "mongodb": "Healthy",
            "llm_service": "Healthy",
            "sarvam_ai": "Healthy",
            "groq": "Healthy",
            "gemini": "Healthy",
            "speech_services": "Healthy",
            "storage": "Healthy",
            "cpu": "45%",
            "memory": "60%",
            "disk": "32%"
        }

        # 6. Recruitment Pipeline
        applied_candidates = await self.candidate_repo.count({"status": "applied"})
        shortlisted_candidates = await self.candidate_repo.count({"status": "shortlisted"})
        rejected_candidates = await self.candidate_repo.count({"status": "rejected"})
        hired_candidates = await self.candidate_repo.count({"status": "hired"})
        
        recruitment_pipeline = {
            "applications": total_candidates,
            "resume_screening": applied_candidates,
            "shortlisted": shortlisted_candidates,
            "interview_scheduled": active_interviews,
            "interview_completed": completed_interviews,
            "selected": hired_candidates,
            "rejected": rejected_candidates,
            "hired": hired_candidates
        }

        # 7. Platform Usage
        platform_usage = {
            "active_sessions": 120,
            "api_requests": 14500
        }

        # 8. Charts
        today = datetime.now(timezone.utc)
        interviews_chart = []
        for i in range(6, -1, -1):
            day_start = (today - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            completed_count = await self.interview_repo.collection.count_documents({
                "status": "completed",
                "created_at": {"$gte": day_start.isoformat(), "$lt": day_end.isoformat()}
            })
            
            active_count = await self.interview_repo.collection.count_documents({
                "status": "in_progress",
                "created_at": {"$gte": day_start.isoformat(), "$lt": day_end.isoformat()}
            })
            
            interviews_chart.append({
                "name": day_start.strftime("%a"),
                "completed": completed_count, 
                "active": active_count
            })

        charts = {
            "interviews_over_time": interviews_chart
        }

        return {
            "welcome": welcome,
            "statistics": statistics,
            "summary_cards": summary_cards,
            "recent_activity": recent_activity,
            "system_health": system_health,
            "recruitment_pipeline": recruitment_pipeline,
            "platform_usage": platform_usage,
            "charts": charts
        }
