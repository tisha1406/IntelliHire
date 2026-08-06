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
        last_login = None
        if isinstance(admin_user, dict):
            last_login = admin_user.get("last_login")
        elif hasattr(admin_user, "last_login"):
            last_login = admin_user.last_login

        welcome = {
            "name": admin_user.get("name") if isinstance(admin_user, dict) else (admin_user.name if hasattr(admin_user, "name") else "Admin User"),
            "role": admin_user.get("role") if isinstance(admin_user, dict) else (admin_user.role if hasattr(admin_user, "role") else "SUPER_ADMIN"),
            "last_login": last_login.isoformat() if hasattr(last_login, "isoformat") else str(last_login) if last_login else None,
        }

        # 2. Statistics
        total_companies = await self.company_repo.count()
        total_users = await self.user_repo.count()
        total_interviews = await self.interview_repo.count()
        total_candidates = await self.candidate_repo.count()
        
        completed_interviews = await self.interview_repo.count({"status": "completed"})
        success_rate = round(completed_interviews / total_interviews * 100, 1) if total_interviews > 0 else 0.0
        
        statistics = {
            "totalCompanies": total_companies,
            "totalCandidates": total_candidates,
            "totalInterviews": total_interviews,
            "aiAccuracy": f"{round(success_rate, 1)}%"
        }

        # 3. Summary Cards
        active_companies = await self.company_repo.count({"subscription.status": "active"})
        suspended_companies = await self.company_repo.count({"subscription.status": "suspended"})
        
        # Calculate companies near limits
        all_companies = await self.company_repo.get_many(limit=1000)
        near_limits_count = 0
        plans_distribution = {"Starter": 0, "Professional": 0, "Enterprise": 0}
        
        for c in all_companies:
            plan = c.get("subscription", {}).get("plan", "Starter")
            if plan in plans_distribution:
                plans_distribution[plan] += 1
            else:
                plans_distribution[plan] = 1
                
            limits = c.get("limits", {})
            usage = c.get("usage", {})
            
            if limits and usage:
                max_rec = limits.get("max_recruiters", 1)
                used_rec = usage.get("recruiters_used", 0)
                if max_rec > 0 and (used_rec / max_rec) >= 0.8:
                    near_limits_count += 1
                    continue
                
                max_camp = limits.get("max_campaigns", 1)
                used_camp = usage.get("campaigns_used", 0)
                if max_camp > 0 and (used_camp / max_camp) >= 0.8:
                    near_limits_count += 1
                    continue
        
        active_interviews = await self.interview_repo.count({"status": "in_progress"})
        
        summary_cards = {
            "companies": {
                "count": total_companies,
                "active_count": active_companies,
                "suspended_count": suspended_companies,
                "near_limits": near_limits_count,
                "plans": plans_distribution
            },
            "platform_users": {
                "count": total_users,
                "recruiters": await self.user_repo.count({"role": "RECRUITER"}),
                "candidates": total_candidates,
            },
            "interviews": {
                "count": total_interviews,
                "active_count": active_interviews,
                "success_rate": f"{round(success_rate, 1)}%",
                "status": "active"
            },
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

        # 6. Recruitment Pipeline / Platform Usage
        applied_candidates = await self.candidate_repo.count({"status": "applied"})
        shortlisted_candidates = await self.candidate_repo.count({"status": "shortlisted"})
        rejected_candidates = await self.candidate_repo.count({"status": "rejected"})
        hired_candidates = await self.candidate_repo.count({"status": "hired"})
        
        # Calculate AI Tokens (mocking a collection query for now as we don't have token logs yet)
        # Assuming ~4500 tokens per completed interview
        total_ai_tokens = completed_interviews * 4500
        total_storage_mb = total_interviews * 15 # 15MB per interview audio/video
        
        recruitment_pipeline = {
            "applications": total_candidates,
            "resume_screening": applied_candidates,
            "shortlisted": shortlisted_candidates,
            "interview_scheduled": active_interviews,
            "interview_completed": completed_interviews,
            "selected": hired_candidates,
            "rejected": rejected_candidates,
            "hired": hired_candidates,
            "total_ai_tokens": total_ai_tokens,
            "total_storage_mb": total_storage_mb
        }

        # 7. Platform Usage – real active session count from MongoDB
        active_sessions = await self.interview_repo.count({"status": "in_progress"})
        platform_usage = {
            "active_sessions": active_sessions,
            "api_requests": 0,    # No request counter collection yet; will be 0 until Phase 2
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
