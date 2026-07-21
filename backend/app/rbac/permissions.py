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

        if token.role not in [role.value for role in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
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