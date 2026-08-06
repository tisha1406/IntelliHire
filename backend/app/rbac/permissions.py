from fastapi import Depends, HTTPException, Path, status

from app.auth.jwt_handler import TokenPayload, decode_jwt
from app.rbac.models import UserRole


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


def require_recruiter_scope(
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
    return token