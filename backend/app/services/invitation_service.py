from datetime import UTC, datetime, timedelta
import secrets
import string
from bson import ObjectId

from fastapi import HTTPException

from app.auth.jwt_handler import hash_password
from app.repositories.user_repository import UserRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.invitation_repository import InvitationRepository
from app.repositories.candidate_workflow_repository import CandidateWorkflowRepository
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.company_repository import CompanyRepository

class InvitationService:

    def __init__(self):
        self.user_repo = UserRepository()
        self.candidate_repo = CandidateRepository()
        self.invitation_repo = InvitationRepository()
        self.workflow_repo = CandidateWorkflowRepository()
        self.campaign_repo = CampaignRepository()
        self.company_repo = CompanyRepository()

    def _generate_token(self, length=32):
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for i in range(length))

    async def invite_candidate(
        self,
        company_id: str,
        campaign_id: str,
        name: str,
        email: str,
    ) -> str:
        """
        Creates a candidate invitation.
        Does NOT create the user account yet - they must accept the invite to set a password.
        (Or depending on flow, we can create the user and candidate now).
        Per the user's request:
        "The backend should automatically:
        Create the User record. Assign the Candidate role. Create the Candidate profile.
        Associate the candidate with the selected company. Associate the candidate with the selected campaign.
        Generate a secure invitation token. Send an invitation email..."
        """

        # Verify campaign
        campaign = await self.campaign_repo.get_by_id(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Verify company ownership
        if str(campaign["company_id"]) != company_id:
            raise HTTPException(status_code=403, detail="Not authorized for this campaign")

        # 1. Create User
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            raise HTTPException(status_code=400, detail="User with this email already exists")

        user_data = {
            "email": email,
            "password_hash": "", # Will be set on acceptance
            "role": "candidate",
            "company_id": ObjectId(company_id),
            "is_active": True,
            "must_change_password": True, # Force them to set one via the token
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
        user_id = await self.user_repo.create(user_data)

        # 2. Create Candidate Profile
        candidate_data = {
            "user_id": ObjectId(user_id),
            "company_id": ObjectId(company_id),
            "campaign_id": ObjectId(campaign_id),
            "name": name,
            "email": email,
            "target_role": campaign.get("job_position", ""),
            "status": "invited",
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
        candidate_id = await self.candidate_repo.create(candidate_data)

        # Update User with Candidate ID
        await self.user_repo.update(user_id, {"candidate_id": ObjectId(candidate_id)})

        # 3. Create Workflow
        workflow_data = {
            "candidate_id": ObjectId(candidate_id),
            "user_id": ObjectId(user_id),
            "company_id": ObjectId(company_id),
            "campaign_id": ObjectId(campaign_id),
            "stage": "INVITATION_PENDING",
            "next_action": "UPLOAD_RESUME", # default after login
            "resume_uploaded": False,
            "practice_completed": False,
            "official_completed": False,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
        await self.workflow_repo.create(workflow_data)

        # 4. Generate Invitation
        token = self._generate_token()
        invitation_data = {
            "token": token,
            "candidate_id": ObjectId(candidate_id),
            "user_id": ObjectId(user_id),
            "company_id": ObjectId(company_id),
            "campaign_id": ObjectId(campaign_id),
            "email": email,
            "name": name,
            "expires_at": datetime.now(UTC) + timedelta(days=7),
            "used": False,
            "created_at": datetime.now(UTC),
        }
        await self.invitation_repo.create(invitation_data)

        # 5. TODO: Send Email

        return token

    async def accept_invitation(self, token: str, password: str):
        """
        Candidate accepts invitation by providing the token and their new password.
        Returns data needed for login.
        """
        invitation = await self.invitation_repo.get_by_token(token)
        if not invitation:
            raise HTTPException(status_code=400, detail="Invalid or expired invitation")
        
        if invitation["expires_at"].replace(tzinfo=UTC) < datetime.now(UTC):
            raise HTTPException(status_code=400, detail="Invitation has expired")

        user_id = str(invitation["user_id"])
        
        # Hash password and update user
        hashed_password = hash_password(password)
        await self.user_repo.update(user_id, {
            "password_hash": hashed_password,
            "must_change_password": False,
            "updated_at": datetime.now(UTC)
        })

        # Update candidate status
        await self.candidate_repo.update(str(invitation["candidate_id"]), {
            "status": "active",
            "updated_at": datetime.now(UTC)
        })

        # Mark token as used
        await self.invitation_repo.mark_used(token)

        # Update workflow
        await self.workflow_repo.set_step_status(
            str(invitation["candidate_id"]),
            "stage",
            "ACCOUNT_ACTIVATED"
        )

        return True
