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