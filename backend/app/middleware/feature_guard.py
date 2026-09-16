from fastapi import HTTPException, status, Depends
from typing import Callable

from app.auth.jwt_handler import TokenPayload
from app.rbac.models import UserRole
from app.rbac.permissions import require_role
from app.repositories.company_repository import CompanyRepository

def require_feature(feature_name: str) -> Callable:
    """
    Dependency generator to enforce feature flags.
    feature_name: The key in the features subdocument (e.g. 'analytics').
    """
    async def feature_dependency(
        current_user: TokenPayload = Depends(require_role(UserRole.COMPANY))
    ):
        company_repo = CompanyRepository()
        company = await company_repo.get_by_id(current_user.sub)
        
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
            
        features = company.get("features", {})
        
        if not features.get(feature_name, False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Feature '{feature_name}' is not enabled. Upgrade your subscription."
            )
            
        return current_user
        
    return feature_dependency
