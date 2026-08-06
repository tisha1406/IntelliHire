from fastapi import HTTPException, status, Depends
from typing import Callable

from app.auth.jwt_handler import TokenPayload
from app.rbac.models import UserRole
from app.rbac.permissions import require_role
from app.repositories.company_repository import CompanyRepository

def check_limit(limit_field: str, usage_field: str) -> Callable:
    """
    Dependency generator to enforce subscription limits.
    limit_field: The key in the limits subdocument (e.g. 'max_recruiters').
    usage_field: The key in the usage subdocument (e.g. 'recruiters_used').
    """
    async def limit_dependency(
        current_user: TokenPayload = Depends(require_role(UserRole.COMPANY))
    ):
        company_repo = CompanyRepository()
        company = await company_repo.get_by_id(current_user.sub)
        
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found."
            )
            
        limits = company.get("limits", {})
        usage = company.get("usage", {})
        
        limit_val = limits.get(limit_field, 0)
        usage_val = usage.get(usage_field, 0)
        
        if usage_val >= limit_val:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Limit exceeded for {limit_field}. Upgrade your subscription."
            )
            
        return current_user
        
    return limit_dependency
