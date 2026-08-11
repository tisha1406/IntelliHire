from typing import Optional, Dict
from datetime import datetime, UTC
from bson import ObjectId

from app.repositories.base_repository import BaseRepository
from app.db.models import AuditLog

class AuditLogRepository(BaseRepository):
    def __init__(self):
        super().__init__("audit_logs")

    async def log_action(
        self,
        company_id: str,
        actor_id: str,
        actor_name: str,
        actor_role: str,
        action: str,
        target_entity: str,
        target_id: Optional[str] = None,
        target_name: Optional[str] = None,
        metadata: Dict = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> str:
        """
        Creates a new audit log entry.
        """
        if metadata is None:
            metadata = {}
            
        entry = AuditLog(
            company_id=str(company_id),
            actor_id=str(actor_id),
            actor_name=actor_name,
            actor_role=actor_role,
            action=action,
            target_entity=target_entity,
            target_id=str(target_id) if target_id else None,
            target_name=target_name,
            metadata=metadata,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.now(UTC)
        )
        
        return await self.create(entry.model_dump())

    async def get_by_actor(self, company_id: str, actor_id: str, limit: int = 50, skip: int = 0) -> list[dict]:
        """
        Retrieves audit logs for a specific actor (like a recruiter).
        """
        query = {
            "company_id": ObjectId(company_id),
            "actor_id": ObjectId(actor_id)
        }
        cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
