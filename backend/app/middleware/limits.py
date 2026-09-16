from fastapi import HTTPException, status, Depends
from typing import Callable

from app.auth.jwt_handler import TokenPayload
from app.rbac.models import UserRole
from app.rbac.permissions import require_company_or_recruiter
from app.repositories.company_repository import CompanyRepository

def check_limit(limit_field: str, usage_field: str) -> Callable:
    """
    Dependency generator to enforce subscription limits.
    limit_field: The key in the limits subdocument (e.g. 'max_recruiters').
    usage_field: The key in the usage subdocument (e.g. 'recruiters_used').
    """
    async def limit_dependency(
        current_user: TokenPayload = Depends(require_company_or_recruiter)
    ):
        company_repo = CompanyRepository()
        company_id = current_user.company_id if current_user.role.upper() == UserRole.RECRUITER.value.upper() else current_user.sub
        company = await company_repo.get_by_id(company_id)
        
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found."
            )
            
        sub_status = company.get("subscription", {}).get("status")
        if sub_status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your subscription is not active. Please renew or verify your subscription."
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
