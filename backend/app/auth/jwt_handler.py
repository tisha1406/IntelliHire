from datetime import UTC, datetime, timedelta
import hashlib
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
    name: str | None = None
    email: str | None = None
    company_id: str | None = None
    campaign_id: str | None = None
    candidate_id: str | None = None
    recruiter_id: str | None = None
    must_change_password: bool = False
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
    candidate_id: str | None = None,
    recruiter_id: str | None = None,
    must_change_password: bool = False,
    name: str | None = None,
    email: str | None = None,
) -> str:
    """
    Create a short-lived JWT access token.

    `name`/`email` are display identity claims only (G-03): they mirror the
    DB-resolved identity at login time and must never be treated as an
    authorization source. They are appended last (not inserted earlier in
    the signature) and default to None, so every existing positional caller
    keeps the same argument meaning it always had.
    """

    now = datetime.now(UTC)

    expire = now + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": user_id,
        "role": role,
        "name": name,
        "email": email,
        "company_id": company_id,
        "campaign_id": campaign_id,
        "candidate_id": candidate_id,
        "recruiter_id": recruiter_id,
        "must_change_password": must_change_password,
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


def hash_refresh_token(refresh_token: str) -> str:
    """
    Hash a raw refresh token for storage/lookup.

    Single source of truth for the hashing scheme (sha256), used by both
    login (store) and refresh (look up + rotate) so the two paths can never
    drift apart. The refresh token itself is opaque (not a JWT, no claims)
    and is never accepted in place of an access token -- decode_jwt() only
    ever validates a real signed JWT, so a raw refresh token simply fails to
    decode if it is ever sent as a Bearer access token.
    """

    return hashlib.sha256(refresh_token.encode()).hexdigest()


def refresh_token_expiry() -> datetime:
    """
    The absolute expiry timestamp for a refresh token minted right now,
    using the existing (previously unused) REFRESH_TOKEN_EXPIRE_DAYS setting.
    """

    return datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)


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