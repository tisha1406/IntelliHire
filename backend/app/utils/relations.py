from bson import ObjectId
from app.repositories.company_repository import CompanyRepository
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.recruiter_repository import RecruiterRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.interview_session_repository import InterviewSessionRepository

class RelationResolver:
    def __init__(self):
        self.company_repo = CompanyRepository()
        self.campaign_repo = CampaignRepository()
        self.recruiter_repo = RecruiterRepository()
        self.candidate_repo = CandidateRepository()
        self.interview_repo = InterviewSessionRepository()

    async def _resolve_entities(self, ids: set, repo, display_field: str = "name") -> dict:
        if not ids:
            return {}
        
        valid_ids = []
        for id_val in ids:
            if isinstance(id_val, str) and ObjectId.is_valid(id_val):
                valid_ids.append(ObjectId(id_val))
            elif isinstance(id_val, ObjectId):
                valid_ids.append(id_val)
                
        if not valid_ids:
            return {}
            
        docs = await repo.collection.find({"_id": {"$in": valid_ids}}).to_list(None)
        
        resolved = {}
        for doc in docs:
            str_id = str(doc["_id"])
            if display_field == "company_name":
                resolved[str_id] = doc.get("general", {}).get("name") or doc.get("company_name")
            else:
                resolved[str_id] = doc.get(display_field)
        return resolved

    async def populate(self, documents: list[dict]) -> list[dict]:
        if not documents:
            return documents
            
        company_ids = set()
        campaign_ids = set()
        recruiter_ids = set()
        candidate_ids = set()
        interview_ids = set()
        
        for doc in documents:
            if doc.get("company_id"): company_ids.add(doc["company_id"])
            if doc.get("campaign_id"): campaign_ids.add(doc["campaign_id"])
            if doc.get("recruiter_id"): recruiter_ids.add(doc["recruiter_id"])
            if doc.get("candidate_id"): candidate_ids.add(doc["candidate_id"])
            if doc.get("interview_id"): interview_ids.add(doc["interview_id"])
            
        # Fetch lookups
        companies_map = await self._resolve_entities(company_ids, self.company_repo, "company_name")
        campaigns_map = await self._resolve_entities(campaign_ids, self.campaign_repo, "title")
        recruiters_map = await self._resolve_entities(recruiter_ids, self.recruiter_repo, "name")
        candidates_map = await self._resolve_entities(candidate_ids, self.candidate_repo, "name")
        interviews_map = await self._resolve_entities(interview_ids, self.interview_repo, "title")
        
        for doc in documents:
            if doc.get("company_id"):
                doc["company_name"] = companies_map.get(str(doc["company_id"]))
            if doc.get("campaign_id"):
                doc["campaign_name"] = campaigns_map.get(str(doc["campaign_id"]))
            if doc.get("recruiter_id"):
                doc["recruiter_name"] = recruiters_map.get(str(doc["recruiter_id"]))
            if doc.get("candidate_id"):
                doc["candidate_name"] = candidates_map.get(str(doc["candidate_id"]))
            if doc.get("interview_id"):
                doc["interview_name"] = interviews_map.get(str(doc["interview_id"]))
                
        return documents
