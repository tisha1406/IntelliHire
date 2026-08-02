from app.repositories.base_repository import BaseRepository
from datetime import datetime, timezone

class SecurityLogRepository(BaseRepository):
    def __init__(self):
        super().__init__("security_logs")

    async def log_event(self, event: str, user: str, ip: str = "Unknown", severity: str = "Info", status: str = "Success"):
        doc = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "user": user,
            "ip": ip,
            "severity": severity,
            "status": status
        }
        return await self.create(doc)
