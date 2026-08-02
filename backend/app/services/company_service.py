from datetime import datetime, timezone
import secrets
import string
from passlib.context import CryptContext

from app.repositories.company_repository import CompanyRepository
from app.services.audit_service import AuditLogService, AuditLogCreate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class CompanyService:
    def __init__(self):
        self.company_repo = CompanyRepository()

    def generate_random_password(self, length=12):
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        while True:
            password = ''.join(secrets.choice(alphabet) for i in range(length))
            if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and any(c.isdigit() for c in password)):
                break
        return password

    def generate_username(self, company_name: str) -> str:
        base = "".join(c for c in company_name if c.isalnum()).lower()
        if not base:
            base = "company"
        suffix = secrets.token_hex(2)
        return f"{base}_{suffix}"

    async def create_company(self, data: dict, created_by: str) -> tuple[str, str, str]:
        username = self.generate_username(data["general"]["name"])
        temp_password = self.generate_random_password()
        hashed_password = pwd_context.hash(temp_password)
        
        now = datetime.now(timezone.utc).isoformat()
        
        company_doc = data.copy()
        company_doc.update({
            "status": "active",
            "created_at": now,
            "updated_at": now,
            "created_by": created_by,
            "deleted_at": None,
            "deleted_by": None,
            "credentials": {
                "username": username,
                "password_hash": hashed_password,
                "password_must_change": True
            }
        })

        company_id = await self.company_repo.create(company_doc)
        
        await AuditLogService().log_action(AuditLogCreate(
            user_id=created_by,
            action="create_company",
            entity_type="company",
            entity_id=company_id,
            details={"company_name": data["general"]["name"]}
        ))
        
        return company_id, username, temp_password

    async def update_company(self, company_id: str, data: dict, updated_by: str) -> bool:
        update_doc = data.copy()
        update_doc["updated_at"] = datetime.now(timezone.utc).isoformat()
        update_doc["updated_by"] = updated_by
        result = await self.company_repo.update(company_id, update_doc)
        
        await AuditLogService().log_action(AuditLogCreate(
            user_id=updated_by,
            action="update_company",
            entity_type="company",
            entity_id=company_id,
            details={"fields_updated": list(data.keys())}
        ))
        
        return result

    async def soft_delete(self, company_id: str, deleted_by: str) -> bool:
        update_doc = {
            "deleted_at": datetime.now(timezone.utc).isoformat(),
            "deleted_by": deleted_by,
            "subscription.status": "deleted"
        }
        result = await self.company_repo.update(company_id, update_doc)
        
        await AuditLogService().log_action(AuditLogCreate(
            user_id=deleted_by,
            action="soft_delete_company",
            entity_type="company",
            entity_id=company_id
        ))
        
        return result

    async def restore_company(self, company_id: str, updated_by: str) -> bool:
        update_doc = {
            "deleted_at": None,
            "deleted_by": None,
            "subscription.status": "active",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": updated_by
        }
        result = await self.company_repo.update(company_id, update_doc)
        
        await AuditLogService().log_action(AuditLogCreate(
            user_id=updated_by,
            action="restore_company",
            entity_type="company",
            entity_id=company_id
        ))
        
        return result

    async def reset_password(self, company_id: str, updated_by: str) -> str:
        temp_password = self.generate_random_password()
        hashed_password = pwd_context.hash(temp_password)
        update_doc = {
            "credentials.password_hash": hashed_password,
            "credentials.password_must_change": True,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": updated_by
        }
        await self.company_repo.update(company_id, update_doc)
        
        await AuditLogService().log_action(AuditLogCreate(
            user_id=updated_by,
            action="reset_company_password",
            entity_type="company",
            entity_id=company_id
        ))
        
        return temp_password

    async def suspend_company(self, company_id: str, updated_by: str) -> bool:
        return await self.update_company(company_id, {"subscription.status": "suspended"}, updated_by)
        
    async def activate_company(self, company_id: str, updated_by: str) -> bool:
        return await self.update_company(company_id, {"subscription.status": "active"}, updated_by)
