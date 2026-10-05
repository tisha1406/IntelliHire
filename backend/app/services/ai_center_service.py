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
        """Aggregate real average scores and topics from all interviews"""
        
        # 1. Overall average score
        pipeline_score = [
            {"$match": {"state": "completed"}},
            {"$project": {"eval_avg": {"$avg": "$evaluation_history.overall_score"}}},
            {"$group": {"_id": None, "global_avg_score": {"$avg": "$eval_avg"}}}
        ]
        
        # 2. Difficulty Distribution
        pipeline_diff = [
            {"$match": {"state": "completed"}},
            {"$unwind": "$question_history"},
            {"$group": {"_id": "$question_history.difficulty", "count": {"$sum": 1}}}
        ]
        
        # 3. Topic Coverage and Scores
        pipeline_topics = [
            {"$match": {"state": "completed"}},
            {"$unwind": "$topic_progress"},
            {"$group": {
                "_id": "$topic_progress.topic_id",
                "avg_score": {"$avg": "$topic_progress.evaluation_aggregate.average_score"},
                "questions_asked": {"$sum": "$topic_progress.questions_asked"}
            }}
        ]
        
        # 4. Blueprint mappings for topic names
        pipeline_names = [
            {"$match": {"state": "completed"}},
            {"$unwind": "$blueprint.topics"},
            {"$group": {"_id": "$blueprint.topics.topic_id", "topic_name": {"$first": "$blueprint.topics.topic_name"}}}
        ]
        
        db_col = self.interview_repo.collection
        
        # Run all pipelines concurrently
        import asyncio
        score_res, diff_res, topics_res, names_res = await asyncio.gather(
            db_col.aggregate(pipeline_score).to_list(length=1),
            db_col.aggregate(pipeline_diff).to_list(length=None),
            db_col.aggregate(pipeline_topics).to_list(length=None),
            db_col.aggregate(pipeline_names).to_list(length=None)
        )
        
        # Parse score
        avg_score = 0
        if score_res and score_res[0].get("global_avg_score"):
            avg_score = int(round(max(0.0, min(1.0, score_res[0]["global_avg_score"])) * 100))
            
        # Parse difficulty
        diff_dict = {"easy": 0, "medium": 0, "hard": 0}
        for d in diff_res:
            lvl = str(d["_id"]).lower()
            if lvl in diff_dict:
                diff_dict[lvl] = d["count"]
                
        # Parse names
        topic_names = {n["_id"]: n["topic_name"] for n in names_res}
        
        # Parse topics
        top_topics = []
        for t in topics_res:
            tid = t["_id"]
            if not tid: continue
            raw_score = t.get("avg_score") or 0.0
            t_score = int(round(max(0.0, min(1.0, raw_score)) * 100))
            top_topics.append({
                "topic_id": tid,
                "topic_name": topic_names.get(tid, tid),
                "average_score": t_score,
                "questions_asked": t.get("questions_asked", 0)
            })
            
        # Sort topics by questions asked or score (we'll sort by score descending)
        top_topics.sort(key=lambda x: x["average_score"], reverse=True)
        
        return {
            "average_score": avg_score,
            "difficulty_distribution": diff_dict,
            "top_topics": top_topics[:5] # limit to top 5
        }

    async def get_interview_analysis_records(self, limit: int, offset: int):
        """Fetch actual interview analysis records"""
        cursor = self.interview_repo.collection.find({"state": "completed"}).sort("created_at", -1).skip(offset).limit(limit)
        interviews = await cursor.to_list(length=limit)
        total = await self.interview_repo.count({"state": "completed"})
        
        records = []
        for i in interviews:
            # Calculate actual score perfectly consistent with InterviewResultService
            score = 0
            evals = i.get("evaluation_history", [])
            if evals:
                avg_01 = sum(e.get("overall_score", 0) for e in evals) / len(evals)
                score = int(round(max(0.0, min(1.0, avg_01)) * 100))
                
            records.append({
                "id": str(i["_id"]),
                "candidate_name": i.get("candidate_name", "Unknown"),
                "campaign": i.get("campaign_name", "Unknown"),
                "score": score,
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
