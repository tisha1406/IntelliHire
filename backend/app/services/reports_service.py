import io
import csv
from datetime import datetime, timezone, timedelta
from app.repositories.company_repository import CompanyRepository
from app.repositories.recruiter_repository import RecruiterRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.interview_session_repository import InterviewSessionRepository

class ReportsService:
    def __init__(self):
        self.company_repo = CompanyRepository()
        self.recruiter_repo = RecruiterRepository()
        self.candidate_repo = CandidateRepository()
        self.interview_repo = InterviewSessionRepository()

    def _get_date_filter(self, date_range: str):
        now = datetime.now(timezone.utc)
        if date_range == "daily":
            start_date = now - timedelta(days=1)
        elif date_range == "weekly":
            start_date = now - timedelta(days=7)
        else: # monthly by default
            start_date = now - timedelta(days=30)
        return {"created_at": {"$gte": start_date.isoformat()}}

    async def get_platform_report(self, date_range: str):
        """Aggregate platform metrics"""
        date_filter = self._get_date_filter(date_range)
        
        companies = await self.company_repo.count(date_filter)
        recruiters = await self.recruiter_repo.count(date_filter)
        candidates = await self.candidate_repo.count(date_filter)
        
        active_interviews = await self.interview_repo.count({"state": "in_progress", **date_filter})
        completed_interviews = await self.interview_repo.count({"state": "completed", **date_filter})
        
        return {
            "companies": companies,
            "recruiters": recruiters,
            "candidates": candidates,
            "active_interviews": active_interviews,
            "completed_interviews": completed_interviews
        }

    async def get_company_report(self, date_range: str, limit: int = 50, offset: int = 0):
        """List companies with stats"""
        date_filter = self._get_date_filter(date_range)
        
        cursor = self.company_repo.collection.find(date_filter).skip(offset).limit(limit)
        companies = await cursor.to_list(length=limit)
        total = await self.company_repo.count(date_filter)
        
        records = []
        for c in companies:
            company_id = str(c["_id"])
            c_interviews = await self.interview_repo.count({"company_id": company_id, **date_filter})
            c_completed = await self.interview_repo.count({"company_id": company_id, "state": "completed", **date_filter})
            
            completion_rate = f"{round((c_completed / c_interviews) * 100)}%" if c_interviews > 0 else "—"
            
            records.append({
                "id": company_id,
                "company": c.get("general", {}).get("name", "Unknown"),
                "candidates": await self.candidate_repo.count({"company_id": company_id, **date_filter}),
                "recruiters": await self.recruiter_repo.count({"company_id": company_id, **date_filter}),
                "interviews": c_interviews,
                "completions": c_completed,
                "completion": completion_rate,
                "period": "Current"
            })
            
        return records, total

    async def get_interview_report(self, date_range: str):
        """Interview metrics"""
        date_filter = self._get_date_filter(date_range)
        
        total = await self.interview_repo.count(date_filter)
        completed = await self.interview_repo.count({"state": "completed", **date_filter})
        cancelled = await self.interview_repo.count({"state": "failed", **date_filter})
        
        # Calculate average duration and average score using MongoDB aggregation
        pipeline = [
            {"$match": {"state": "completed", **date_filter}},
            {"$project": {
                "duration_ms": {"$subtract": [
                    {"$dateFromString": {"dateString": "$completed_at"}},
                    {"$dateFromString": {"dateString": "$started_at"}}
                ]},
                "eval_avg": {"$avg": "$evaluation_history.overall_score"}
            }},
            {"$group": {
                "_id": None,
                "avg_duration_ms": {"$avg": "$duration_ms"},
                "global_avg_score": {"$avg": "$eval_avg"}
            }}
        ]
        agg_cursor = self.interview_repo.collection.aggregate(pipeline)
        agg_results = await agg_cursor.to_list(length=1)
        
        avg_duration = 0
        avg_score = 0
        if agg_results:
            agg = agg_results[0]
            if agg.get("avg_duration_ms"):
                avg_duration = int(round(agg["avg_duration_ms"] / 60000))
            if agg.get("global_avg_score"):
                avg_score = int(round(max(0.0, min(1.0, agg["global_avg_score"])) * 100))
        
        return {
            "interview_count": total,
            "completed": completed,
            "cancelled": cancelled,
            "average_duration": avg_duration,
            "average_score": avg_score
        }

    async def get_candidate_report(self, date_range: str, limit: int = 50, offset: int = 0):
        """Candidate metrics"""
        date_filter = self._get_date_filter(date_range)
        
        cursor = self.candidate_repo.collection.find(date_filter).skip(offset).limit(limit)
        candidates = await cursor.to_list(length=limit)
        total = await self.candidate_repo.count(date_filter)
        
        records = []
        for c in candidates:
            c_id = str(c["_id"])
            
            # Fetch real interview score from latest completed session
            latest_session = await self.interview_repo.collection.find_one(
                {"candidate_id": c_id, "state": "completed"}, 
                sort=[("completed_at", -1)]
            )
            interview_score = 0
            if latest_session and latest_session.get("evaluation_history"):
                evals = latest_session["evaluation_history"]
                avg_01 = sum(e.get("overall_score", 0) for e in evals) / len(evals)
                interview_score = int(round(max(0.0, min(1.0, avg_01)) * 100))

            records.append({
                "id": c_id,
                "candidate": c.get("name", "Unknown"),
                "resume_score": c.get("resume_score", 0),
                "interview_score": interview_score,
                "status": c.get("status", "pending"),
                "offer_status": c.get("offer_status", "none")
            })
            
        return records, total

    async def get_interviews_chart(self, date_range: str):
        """Data for interview chart"""
        now = datetime.now(timezone.utc)
        days = 7 if date_range == "weekly" else (30 if date_range == "monthly" else 1)
        
        data = []
        for i in range(days - 1, -1, -1):
            day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            f = {"created_at": {"$gte": day_start.isoformat(), "$lt": day_end.isoformat()}}
            completed = await self.interview_repo.count({"state": "completed", **f})
            cancelled = await self.interview_repo.count({"state": "failed", **f})
            scheduled = await self.interview_repo.count({"state": "created", **f})
            
            data.append({
                "name": day_start.strftime("%b %d" if days > 1 else "%H:00"),
                "completed": completed,
                "cancelled": cancelled,
                "scheduled": scheduled,
                "interviews": completed + cancelled + scheduled
            })
            
        return data

    async def export_csv(self, report_type: str, date_range: str):
        """Generate CSV string"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        if report_type == "platform":
            data = await self.get_platform_report(date_range)
            writer.writerow(["Metric", "Value"])
            for k, v in data.items():
                if isinstance(v, (int, float, str)):
                    writer.writerow([k, v])
                    
        elif report_type == "company":
            data, _ = await self.get_company_report(date_range, limit=1000)
            writer.writerow(["Company", "Candidates", "Recruiters", "Interviews", "Completions", "Completion Rate"])
            for r in data:
                writer.writerow([r["company"], r["candidates"], r["recruiters"], r["interviews"], r["completions"], r["completion"]])
                
        return output.getvalue()

    async def export_pdf(self, report_type: str, date_range: str):
        """Generate PDF bytes (using simple dummy bytes)"""
        return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n" 
