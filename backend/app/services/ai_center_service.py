from datetime import datetime, timezone, timedelta
from app.repositories.company_repository import CompanyRepository
from app.repositories.user_repository import UserRepository
from app.repositories.interview_session_repository import InterviewSessionRepository
from app.repositories.candidate_repository import CandidateRepository

class AICenterService:
    def __init__(self):
        self.company_repo = CompanyRepository()
        self.user_repo = UserRepository()
        self.interview_repo = InterviewSessionRepository()
        self.candidate_repo = CandidateRepository()

    async def get_model_usage(self):
        """Aggregate token usage across models (returns 0s if no data)"""
        # In a real system, we'd query a token_usage or billing collection.
        # Since we don't have this, we return 0 rather than mock data.
        return {
            "total_tokens": 0,
            "cost_estimated": 0.0,
            "models_distribution": {},
            "average_latency_ms": 0
        }

    async def get_resume_screening_records(self, limit: int, offset: int, status_filter: str = None):
        """Fetch real candidates with resume screening scores"""
        query = {}
        if status_filter:
            query["status"] = status_filter
            
        cursor = self.candidate_repo.collection.find(query).skip(offset).limit(limit)
        candidates = await cursor.to_list(length=limit)
        total = await self.candidate_repo.count(query)
        
        records = []
        for c in candidates:
            records.append({
                "id": str(c["_id"]),
                "candidate_name": c.get("name", "Unknown"),
                "company_name": c.get("company_name", "Unknown"), # Could join with companies if needed
                "status": c.get("status", "pending"),
                "score": c.get("resume_score"),
                "processing_time": c.get("processing_time"),
                "created_at": c.get("created_at")
            })
            
        return records, total

    async def get_interview_analysis_summary(self):
        """Aggregate real average scores and confidence from all interviews"""
        pipeline = [
            {"$match": {"status": "completed", "score": {"$exists": True}}},
            {"$group": {
                "_id": None,
                "avg_score": {"$avg": "$score"},
                "avg_confidence": {"$avg": "$ai_confidence"},
                "avg_communication": {"$avg": "$skills.communication"},
                "avg_technical": {"$avg": "$skills.technical"},
                "avg_problem_solving": {"$avg": "$skills.problem_solving"}
            }}
        ]
        
        cursor = self.interview_repo.collection.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        
        if not result:
            return {
                "average_score": 0,
                "skill_distribution": {
                    "communication": 0,
                    "technical": 0,
                    "problem_solving": 0
                },
                "difficulty_distribution": {
                    "easy": 0,
                    "medium": 0,
                    "hard": 0
                }
            }
            
        agg = result[0]
        return {
            "average_score": round(agg.get("avg_score") or 0),
            "skill_distribution": {
                "communication": round(agg.get("avg_communication") or 0),
                "technical": round(agg.get("avg_technical") or 0),
                "problem_solving": round(agg.get("avg_problem_solving") or 0)
            },
            "difficulty_distribution": {
                "easy": 0,
                "medium": 0,
                "hard": 0
            }
        }

    async def get_interview_analysis_records(self, limit: int, offset: int):
        """Fetch actual interview analysis records"""
        cursor = self.interview_repo.collection.find({"status": "completed"}).sort("created_at", -1).skip(offset).limit(limit)
        interviews = await cursor.to_list(length=limit)
        total = await self.interview_repo.count({"status": "completed"})
        
        records = []
        for i in interviews:
            records.append({
                "id": str(i["_id"]),
                "candidate_name": i.get("candidate_name", "Unknown"),
                "campaign": i.get("campaign_name", "Unknown"),
                "score": i.get("score", 0),
                "ai_confidence": i.get("ai_confidence", 0),
                "created_at": i.get("created_at")
            })
            
        return records, total

    async def get_ai_reports(self, limit: int, offset: int):
        """Fetch real AI reports from DB (if collection exists)"""
        # Assuming reports collection does not exist or is empty
        # We will query it safely
        try:
            reports_col = self.company_repo.database.get_collection("ai_reports")
            cursor = reports_col.find().sort("created_at", -1).skip(offset).limit(limit)
            reports = await cursor.to_list(length=limit)
            total = await reports_col.count_documents({})
            
            records = []
            for r in reports:
                records.append({
                    "id": str(r["_id"]),
                    "title": r.get("title", "Untitled Report"),
                    "type": r.get("type", "pdf"),
                    "downloads": r.get("downloads", 0),
                    "created_at": r.get("created_at")
                })
            return records, total
        except Exception:
            return [], 0
