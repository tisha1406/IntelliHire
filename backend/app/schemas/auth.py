from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str
    company_id: str | None = None
    company_name: str | None = None
    subscription_status: str | None = None
    required_redirect: str | None = None
    must_change_password: bool | None = None
    candidate_context: dict | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    """
    G-01: deliberately smaller than LoginResponse. A refresh is not a new
    login decision -- it carries forward the same session's role/claims, so
    it does not recompute or return company_name/subscription_status/
    required_redirect/candidate_context (those are UI-flow fields resolved
    at login time; the frontend already holds them and can re-derive
    identity claims from the new access token, exactly as it does today).
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str