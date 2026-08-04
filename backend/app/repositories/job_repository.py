from typing import List, Optional, Dict, Any
from bson import ObjectId

from app.db.mongo import get_database
from app.db.models import JobOpening

class JobRepository:

    @property
    def collection(self):
        return get_database()["job_openings"]

    async def create(self, job_data: dict) -> str:
        job = JobOpening(**job_data)
        result = await self.collection.insert_one(
            job.model_dump(by_alias=True, exclude_none=True)
        )
        return str(result.inserted_id)

    async def get_by_id(self, job_id: str) -> Optional[dict]:
        if not ObjectId.is_valid(job_id):
            return None
        return await self.collection.find_one(
            {"_id": ObjectId(job_id)}
        )

    async def get_many(
        self,
        company_id: Optional[str] = None,
        query: Optional[str] = None,
        department: Optional[str] = None,
        employment_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10,
        skip: int = 0,
        sort_key: str = "created_at",
        sort_order: int = -1
    ) -> tuple[List[dict], int]:
        filter_query: Dict[str, Any] = {}
        if company_id:
            filter_query["company_id"] = ObjectId(company_id)

        if query:
            filter_query["$or"] = [
                {"title": {"$regex": query, "$options": "i"}},
                {"location": {"$regex": query, "$options": "i"}},
            ]
            
        if department:
            filter_query["department"] = department
            
        if employment_type:
            filter_query["employment_type"] = employment_type
            
        if status:
            filter_query["status"] = {"$regex": f"^{status}$", "$options": "i"}
            
        cursor = self.collection.find(filter_query).sort(sort_key, sort_order).skip(skip).limit(limit)
        
        jobs = await cursor.to_list(length=limit)
        total = await self.collection.count_documents(filter_query)
        
        return jobs, total

    async def count(self, filter_query: Optional[dict] = None) -> int:
        if filter_query is None:
            filter_query = {}
        return await self.collection.count_documents(filter_query)

    async def update(self, job_id: str, update_data: dict) -> bool:
        if not ObjectId.is_valid(job_id):
            return False
            
        result = await self.collection.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0

    async def delete(self, job_id: str) -> bool:
        if not ObjectId.is_valid(job_id):
            return False
            
        result = await self.collection.delete_one(
            {"_id": ObjectId(job_id)}
        )
        return result.deleted_count > 0
