from datetime import UTC, datetime
from fastapi import HTTPException, status

from app.auth.jwt_handler import (
    verify_password,
    create_access_token,
    create_refresh_token,
)

from app.repositories.user_repository import UserRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.company_repository import CompanyRepository


class AuthService:

    def __init__(self):
        self.user_repo = UserRepository()
        self.candidate_repo = CandidateRepository()
        self.campaign_repo = CampaignRepository()
        self.company_repo = CompanyRepository()

    async def login(
        self,
        email: str,
        password: str,
    ):
        user = await self.user_repo.get_by_email(email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not verify_password(
            password,
            user["password_hash"],
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Check if account is active
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled. Contact support.",
            )

        role = user["role"]
        candidate_id = str(user["candidate_id"]) if user.get("candidate_id") else None
        company_id = str(user.get("company_id")) if user.get("company_id") else None
        campaign_id = None

        # For candidate logins: fetch campaign context
        candidate_context = None
        if role == "candidate" and candidate_id:
            candidate = await self.candidate_repo.get_by_id(candidate_id)
            if candidate:
                campaign_id = str(candidate.get("campaign_id", ""))
                candidate_context = {
                    "candidate_id": candidate_id,
                    "candidate_name": candidate.get("name", ""),
                    "campaign_id": campaign_id,
                    "company_id": str(candidate.get("company_id", "")),
                }

        access_token = create_access_token(
            user_id=str(user["_id"]),
            role=role,
            company_id=company_id,
            campaign_id=campaign_id,
            candidate_id=candidate_id,
        )

        refresh_token = create_refresh_token()

        # Store refresh token hash (hashed)
        import hashlib
        refresh_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        await self.user_repo.store_refresh_token(
            str(user["_id"]),
            refresh_hash,
        )

        await self.user_repo.update_last_login(
            str(user["_id"])
        )

        base_response = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "role": role,
            "company_id": company_id,
        }

        if candidate_context:
            base_response["candidate_context"] = candidate_context

        return base_response