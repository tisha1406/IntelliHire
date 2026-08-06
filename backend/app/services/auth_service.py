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
        is_company_login = False
        user = await self.user_repo.get_by_email(email)

        # Ignore legacy seeded company users in the users collection
        if user and user.get("role") == "company":
            user = None

        if not user:
            company = await self.company_repo.get_by_email(email)
            if company and "credentials" in company:
                user = company
                is_company_login = True
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Company account not found.",
                )

        if is_company_login:
            if not verify_password(password, user["credentials"]["password_hash"]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password.",
                )
            
            # Check if active
            company_status = user.get("subscription", {}).get("status") or user.get("status")
            if company_status != "active":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Company account is inactive.\nPlease contact IntelliHire administrator.",
                )
            if user.get("deleted_at"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot login. Company account deleted.",
                )

            role = "company"
            company_id = str(user["_id"])
            candidate_id = None
        else:
            if not verify_password(password, user["password_hash"]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                )

            if not user.get("is_active", True):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is disabled. Contact support.",
                )

            role = user["role"]
            candidate_id = str(user["candidate_id"]) if user.get("candidate_id") else None
            company_id = str(user.get("company_id")) if user.get("company_id") else None
            recruiter_id = str(user.get("recruiter_id")) if role == "recruiter" else None
        
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
            recruiter_id=recruiter_id if 'recruiter_id' in locals() else None,
        )

        refresh_token = create_refresh_token()

        # Store refresh token hash (hashed)
        import hashlib
        refresh_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        
        if is_company_login:
            await self.company_repo.store_refresh_token(
                str(user["_id"]),
                refresh_hash,
            )
            await self.company_repo.update_last_login(
                str(user["_id"])
            )
        else:
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
            "company_name": "",
        }

        if role == "recruiter":
            base_response["must_change_password"] = user.get("must_change_password", False)

        if role == "company" and company_id:
            company = await self.company_repo.get_by_id(company_id)
            if company:
                base_response["company_name"] = (
                    company.get("company_name")
                    or company.get("general", {}).get("name", "")
                    or company.get("name", "")
                )

        if candidate_context:
            base_response["candidate_context"] = candidate_context

        return base_response
