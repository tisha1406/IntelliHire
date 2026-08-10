from fastapi import Depends, HTTPException, Path, status

from app.auth.jwt_handler import TokenPayload, decode_jwt
from app.rbac.models import UserRole
from app.rbac.permissions_matrix import Permission, get_permissions_for_role


def require_permission(required_permission: Permission):
    """
    Allows access only to users who have the required granular permission.
    For backward compatibility, if permissions are not explicitly in the token,
    derives them from the user's role/sub_role.
    """
    def dependency(token: TokenPayload = Depends(decode_jwt)) -> TokenPayload:
        if token.role.upper() == "SUPER_ADMIN":
            return token
            
        # Determine effective role: if token has 'designation' or 'sub_role', use it; otherwise use base role
        # For simplicity, we'll map the role. If token has a specific sub-role, we would use it here.
        # Assuming token.role might contain "company" or "recruiter"
        effective_role = token.role
        
        user_permissions = get_permissions_for_role(effective_role)
        
        if required_permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {required_permission.value}",
            )
            
        return token
        
    return dependency

def require_role(*allowed_roles: UserRole):
    """
    Allows access only to users with one of the allowed roles.
    """

    def dependency(
        token: TokenPayload = Depends(decode_jwt),
    ) -> TokenPayload:

        user_role_upper = token.role.upper()
        allowed_values = [r.value.upper() for r in allowed_roles]

        if user_role_upper != "SUPER_ADMIN" and user_role_upper not in allowed_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Your role: {token.role}, Required: {allowed_values}",
            )

        return token

    return dependency


def require_own_company(
    company_id: str = Path(...),
    token: TokenPayload = Depends(
        require_role(UserRole.COMPANY)
    ),
) -> TokenPayload:
    """
    Prevents one company from accessing another company's data.
    """

    if token.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cross-tenant access denied",
        )

    return token


async def require_recruiter_scope(
    token: TokenPayload = Depends(require_role(UserRole.RECRUITER)),
) -> TokenPayload:
    """
    Ensures that the token belongs to a recruiter.
    """
    if not token.recruiter_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Recruiter scope missing",
        )
        
    from app.repositories.user_repository import UserRepository
    user_repo = UserRepository()
    user = await user_repo.get_by_id(token.sub)
    if not user or not user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Recruiter account suspended.",
        )
        
    return token


async def require_company_or_recruiter(
    token: TokenPayload = Depends(decode_jwt),
) -> TokenPayload:
    """
    Shared endpoint guard for Company Admins and Recruiters.
    Both roles use the same endpoints; the backend scopes data by JWT claims.
    - Company: scopes by company_id (all company data)
    - Recruiter: scopes by recruiter_id (assigned records only)
    """
    allowed = {UserRole.COMPANY.value.upper(), UserRole.RECRUITER.value.upper(), "SUPER_ADMIN"}
    if token.role.upper() not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required: company or recruiter role.",
        )
    # Recruiters must have recruiter_id in their JWT
    if token.role.upper() == UserRole.RECRUITER.value.upper():
        if not token.recruiter_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Recruiter scope missing from token",
            )
        
        # Enforce suspension / soft deletion for recruiters
        from app.repositories.user_repository import UserRepository
        user_repo = UserRepository()
        user = await user_repo.get_by_id(token.sub)
        if not user or not user.get("is_active"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Recruiter account suspended.",
            )
            
    return token