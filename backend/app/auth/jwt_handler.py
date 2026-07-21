from datetime import UTC, datetime, timedelta
import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.config.settings import settings


# ==========================================================
# Password Hashing Configuration
# ==========================================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


# ==========================================================
# JWT Authentication Scheme
# ==========================================================

security = HTTPBearer()


# ==========================================================
# JWT Payload Model
# ==========================================================

class TokenPayload(BaseModel):
    """
    JWT Payload as defined in Chapter 12.1 of the SDD.
    """

    sub: str
    role: str
    company_id: str | None = None
    campaign_id: str | None = None
    exp: int
    iat: int


# ==========================================================
# Password Utilities
# ==========================================================

def hash_password(password: str) -> str:
    """
    Hash a plain-text password using bcrypt.
    """
    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    Verify a password against its bcrypt hash.
    """
    return pwd_context.verify(
        plain_password,
        hashed_password,
    )


# ==========================================================
# Access Token
# ==========================================================

def create_access_token(
    user_id: str,
    role: str,
    company_id: str | None = None,
    campaign_id: str | None = None,
) -> str:
    """
    Create a short-lived JWT access token.
    """

    now = datetime.now(UTC)

    expire = now + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": user_id,
        "role": role,
        "company_id": company_id,
        "campaign_id": campaign_id,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


# ==========================================================
# Refresh Token
# ==========================================================

def create_refresh_token() -> str:
    """
    Generate a secure random refresh token.

    NOTE:
    The SDD specifies that this token will later be
    hashed and stored in MongoDB.
    """

    return secrets.token_urlsafe(64)


# ==========================================================
# Decode JWT
# ==========================================================

def decode_jwt(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
) -> TokenPayload:
    """
    Decode and validate an access token.
    """

    token = credentials.credentials

    try:

        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )

        return TokenPayload(**payload)

    except JWTError:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )