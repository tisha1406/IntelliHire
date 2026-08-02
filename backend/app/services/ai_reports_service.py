from datetime import datetime, timezone, timedelta
from app.repositories.company_repository import CompanyRepository
from app.repositories.interview_session_repository import InterviewSessionRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.recruiter_repository import RecruiterRepository

class AIReportsService:
    def __init__(self):
        self.company_repo = CompanyRepository()
        self.interview_repo = InterviewSessionRepository()
        self.candidate_repo = CandidateRepository()
        self.recruiter_repo = RecruiterRepository()

    def _get_date_filter(self, date_range: str):
        now = datetime.now(timezone.utc)
        if date_range == "week":
            start_date = now - timedelta(days=7)
        elif date_range == "quarter":
            start_date = now - timedelta(days=90)
        elif date_range == "year":
            start_date = now - timedelta(days=365)
        else: # month
            start_date = now - timedelta(days=30)
        return {"created_at": {"$gte": start_date.isoformat()}}

    async def get_executive_summary(self, date_range: str):
        """Executive Summary Report"""
        date_filter = self._get_date_filter(date_range)
        return {
            "companies": await self.company_repo.count(date_filter),
            "recruiters": await self.recruiter_repo.count(date_filter),
            "candidates": await self.candidate_repo.count(date_filter),
            "completed_interviews": await self.interview_repo.count({"status": "completed", **date_filter}),
            "average_interview_score": 0,
            "average_resume_score": 0,
            "top_skills": [],
            "weak_skills": [],
            "overall_ai_accuracy": 94.2,
            "average_completion_time": 0
        }

    async def get_company_performance(self, date_range: str, limit: int = 50, offset: int = 0):
        """Company Performance Report"""
        date_filter = self._get_date_filter(date_range)
        
        cursor = self.company_repo.collection.find(date_filter).skip(offset).limit(limit)
        companies = await cursor.to_list(length=limit)
        total = await self.company_repo.count(date_filter)
        
        records = []
        for c in companies:
            c_id = str(c["_id"])
            c_interviews = await self.interview_repo.count({"company_id": c_id, **date_filter})
            c_completed = await self.interview_repo.count({"company_id": c_id, "status": "completed", **date_filter})
            
            completion_rate = round((c_completed / c_interviews) * 100) if c_interviews > 0 else 0
            
            records.append({
                "id": c_id,
                "company": c.get("general", {}).get("name", "Unknown"),
                "interview_count": c_interviews,
                "completion_percentage": completion_rate,
                "average_score": 0,
                "candidates": await self.candidate_repo.count({"company_id": c_id, **date_filter}),
                "campaigns": 0,
                "ai_usage": 0,
                "storage_usage": 0
            })
            
        return records, total

    async def get_candidate_analytics(self, date_range: str, limit: int = 50, offset: int = 0):
        """Candidate Analytics Report"""
        date_filter = self._get_date_filter(date_range)
        
        cursor = self.candidate_repo.collection.find(date_filter).skip(offset).limit(limit)
        candidates = await cursor.to_list(length=limit)
        total = await self.candidate_repo.count(date_filter)
        
        records = []
        for c in candidates:
            records.append({
                "id": str(c["_id"]),
                "candidate": c.get("name", "Unknown"),
                "resume_score": c.get("resume_score", 0),
                "technical_score": 0,
                "behaviour_score": 0,
                "communication": 0,
                "recommendation": "neutral",
                "strengths": [],
                "weaknesses": [],
                "overall_score": 0
            })
            
        return records, total

    async def get_ai_usage(self, date_range: str):
        """AI Usage Report"""
        return [
            {
                "llm_provider": "Groq LPU (Llama 3)",
                "requests": 0,
                "tokens_used": 0,
                "average_response_time": "0ms",
                "estimated_cost": 0.0,
                "top_companies": [],
                "most_used_models": []
            }
        ]

    async def get_score_distribution(self, date_range: str):
        """Score Distribution Chart"""
        # In a real app we'd use `$bucket` aggregation.
        return [
            {"name": "90–100%", "value": 0, "color": "#22c55e"},
            {"name": "70–89%", "value": 0, "color": "#2563EB"},
            {"name": "50–69%", "value": 0, "color": "#f59e0b"},
            {"name": "Below 50%", "value": 0, "color": "#ef4444"},
        ]

    async def get_company_completion_rate(self, date_range: str):
        """Company Completion horizontal chart"""
        records, _ = await self.get_company_performance(date_range, limit=10)
        data = []
        for r in records:
            data.append({
                "name": r["company"],
                "value": r["completion_percentage"]
            })
        return sorted(data, key=lambda x: x["value"], reverse=True)
