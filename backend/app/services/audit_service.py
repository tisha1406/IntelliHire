from datetime import datetime, timezone
from pydantic import BaseModel
from app.repositories.base_repository import BaseRepository

class AuditLogCreate(BaseModel):
    user_id: str
    action: str
    entity_type: str
    entity_id: str | None = None
    details: dict | None = None
    ip_address: str | None = None
    user_agent: str | None = None

class AuditLogRepository(BaseRepository):
    def __init__(self):
        super().__init__("audit_logs")

class AuditLogService:
    def __init__(self):
        self.repo = AuditLogRepository()

    async def log_action(self, log_data: AuditLogCreate):
        document = log_data.model_dump(exclude_none=True)
        document["timestamp"] = datetime.now(timezone.utc)
        await self.repo.create(document)

    async def get_logs(self, limit: int = 50, skip: int = 0):
        logs = await self.repo.get_many(
            query={},
            limit=limit,
            skip=skip,
        )
        # We might want to sort by timestamp DESC. Let's add sorting to get_many in BaseRepository later if needed,
        # or do it here. For now, since BaseRepository.get_many doesn't support sort directly, let's fix it later.
        # Actually, let's just return what we have and we will update BaseRepository to support sorting.
        return logs

    async def count_logs(self) -> int:
        return await self.repo.count()

    async def get_company_logs(self, company_id: str, limit: int = 50, skip: int = 0):
        # We assume entity_id is the company_id for company level logs or 
        # that logs could just be filtered by user_id from that company.
        # But looking at how we log: entity_type="company", entity_id=company_id
        logs = await self.repo.get_many(
            query={"entity_id": company_id},
            limit=limit,
            skip=skip,
        )
        return logs
