from datetime import UTC, datetime
from fastapi import HTTPException, status

from app.auth.jwt_handler import (
    verify_password,
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
    refresh_token_expiry,
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
            allowed_statuses = ["active", "pending_verification", "pending_payment", "expired", "trial"]
            if company_status not in allowed_statuses:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Company account is {company_status or 'inactive'}.\nPlease contact IntelliHire administrator.",
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

            if company_id:
                company = await self.company_repo.get_by_id(company_id)
                if not company:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Company account not found.",
                    )
                company_status = company.get("subscription", {}).get("status") or company.get("status")
                if company_status != "active" or company.get("deleted_at"):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Company account is inactive or deleted.",
                    )
        
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

        # G-03: resolve the same display name/email every role already has
        # available at this point in login(), so the JWT's identity claims
        # are never blank. This mirrors the lookup each role's doc already
        # uses elsewhere (company_name resolution below; candidate_context
        # above) -- it does not introduce a new source of truth, just carries
        # the existing one into the token.
        if is_company_login:
            display_name = (
                user.get("company_name")
                or user.get("general", {}).get("name", "")
                or user.get("name", "")
            )
            display_email = user.get("general", {}).get("contact_email") or user.get("email", "")
        elif role == "candidate":
            display_name = candidate_context["candidate_name"] if candidate_context else ""
            display_email = user.get("email", "")
        else:
            display_name = user.get("name", "")
            display_email = user.get("email", "")

        access_token = create_access_token(
            user_id=str(user["_id"]),
            role=role,
            name=display_name,
            email=display_email,
            company_id=company_id,
            campaign_id=campaign_id,
            candidate_id=candidate_id,
            recruiter_id=recruiter_id if 'recruiter_id' in locals() else None,
            must_change_password=user.get("must_change_password", False),
        )

        refresh_token = create_refresh_token()

        # Store refresh token hash, plus its expiry (G-01: the expiry field
        # is what makes an "expired refresh token" actually rejectable by
        # refresh() below; hash_refresh_token() is the same sha256 scheme
        # that was already inlined here, just named so refresh() can share
        # it instead of re-deriving its own hashing rule).
        refresh_hash = hash_refresh_token(refresh_token)
        refresh_expires_at = refresh_token_expiry()

        if is_company_login:
            await self.company_repo.store_refresh_token(
                str(user["_id"]),
                refresh_hash,
                refresh_expires_at,
            )
            await self.company_repo.update_last_login(
                str(user["_id"])
            )
        else:
            await self.user_repo.store_refresh_token(
                str(user["_id"]),
                refresh_hash,
                refresh_expires_at,
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
                
                # Subscription logic
                sub_status = company.get("subscription", {}).get("status", "active")
                base_response["subscription_status"] = sub_status
                if sub_status == "pending_verification":
                    base_response["required_redirect"] = "/company/subscription/verify"
                elif sub_status == "pending_payment":
                    base_response["required_redirect"] = "/company/subscription/payment"
                elif sub_status == "expired":
                    base_response["required_redirect"] = "/company/subscription/renew"

        if candidate_context:
            base_response["candidate_context"] = candidate_context

        return base_response

    async def refresh(self, refresh_token: str) -> dict:
        """
        G-01: exchange a valid, unexpired refresh token for a new access
        token. The refresh token itself is the credential here (no password
        check) -- the stored hash lookup IS the authentication.

        Rotation: a brand-new refresh token is minted and its hash replaces
        the old one in the same document update, so the old refresh token's
        hash no longer matches anything afterwards. Reusing it is therefore
        indistinguishable from presenting a refresh token that was never
        issued -- INVALID_REFRESH_TOKEN, not a special "already used" case.
        This is the existing store/lookup mechanism (store_refresh_token /
        get_by_refresh_token), not a new revocation system; G-02's logout
        revocation is a separate, still-untouched concern (clear_refresh_token
        is not called from here).

        Claim resolution (role/company_id/campaign_id/candidate_id/
        recruiter_id/name/email) intentionally mirrors login()'s logic
        exactly, so a refreshed session carries the same authorization
        claims a fresh login would produce. It is kept as separate code
        (not extracted into a shared helper) specifically because this task
        must not touch login()'s own control flow.
        """
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token.",
            )

        token_hash = hash_refresh_token(refresh_token)

        is_company_login = False
        user = await self.user_repo.get_by_refresh_token(token_hash)
        if not user:
            user = await self.company_repo.get_by_refresh_token(token_hash)
            if user:
                is_company_login = True

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token.",
            )

        expires_at = user.get("refresh_token_expires_at")
        if expires_at is not None and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if not expires_at or expires_at < datetime.now(UTC):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired.",
            )

        if is_company_login:
            if user.get("deleted_at"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot refresh. Company account deleted.",
                )
            company_status = user.get("subscription", {}).get("status") or user.get("status")
            allowed_statuses = ["active", "pending_verification", "pending_payment", "expired", "trial"]
            if company_status not in allowed_statuses:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Company account is {company_status or 'inactive'}.",
                )

            role = "company"
            company_id = str(user["_id"])
            candidate_id = None
            recruiter_id = None
        else:
            if not user.get("is_active", True):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is disabled. Contact support.",
                )

            role = user["role"]
            candidate_id = str(user["candidate_id"]) if user.get("candidate_id") else None
            company_id = str(user.get("company_id")) if user.get("company_id") else None
            recruiter_id = str(user.get("recruiter_id")) if role == "recruiter" else None

            if company_id:
                company = await self.company_repo.get_by_id(company_id)
                if not company:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Company account not found.",
                    )
                company_status = company.get("subscription", {}).get("status") or company.get("status")
                if company_status != "active" or company.get("deleted_at"):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Company account is inactive or deleted.",
                    )

        campaign_id = None
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

        if is_company_login:
            display_name = (
                user.get("company_name")
                or user.get("general", {}).get("name", "")
                or user.get("name", "")
            )
            display_email = user.get("general", {}).get("contact_email") or user.get("email", "")
        elif role == "candidate":
            display_name = candidate_context["candidate_name"] if candidate_context else ""
            display_email = user.get("email", "")
        else:
            display_name = user.get("name", "")
            display_email = user.get("email", "")

        access_token = create_access_token(
            user_id=str(user["_id"]),
            role=role,
            name=display_name,
            email=display_email,
            company_id=company_id,
            campaign_id=campaign_id,
            candidate_id=candidate_id,
            recruiter_id=recruiter_id,
            must_change_password=user.get("must_change_password", False),
        )

        new_refresh_token = create_refresh_token()
        new_hash = hash_refresh_token(new_refresh_token)
        new_expiry = refresh_token_expiry()

        if is_company_login:
            await self.company_repo.store_refresh_token(str(user["_id"]), new_hash, new_expiry)
        else:
            await self.user_repo.store_refresh_token(str(user["_id"]), new_hash, new_expiry)

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "role": role,
        }
