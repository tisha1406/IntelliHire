"""
Seed candidate for IntelliHire development.

Creates:
- 1 Candidate User (associated with Acme Technologies and a campaign)
- Initializes their workflow and profile

Run:
python -m scripts.seed_candidate
"""

import asyncio
from bson import ObjectId

from app.auth.jwt_handler import hash_password
from app.db.mongo import connect_db, close_db
from app.repositories.company_repository import CompanyRepository
from app.repositories.campaign_repository import CampaignRepository
from app.services.invitation_service import InvitationService

CANDIDATE_EMAIL = "candidate@intellihire.dev"
CANDIDATE_PASSWORD = "TestCandidate123!"

async def seed_candidate():
    print(f"Creating candidate {CANDIDATE_EMAIL}...")
    company_repo = CompanyRepository()
    campaign_repo = CampaignRepository()
    invitation_service = InvitationService()

    # Find Acme Technologies
    company = await company_repo.get_by_email("hr@acme.dev")
    if not company:
        print("Acme Technologies not found. Please run seed_dev_data first.")
        return

    # Find a campaign for Acme
    campaigns = await campaign_repo.get_by_company(ObjectId(company["_id"]))
    if not campaigns:
        # Create a dummy campaign if none exist
        campaign_id = await campaign_repo.create({
            "company_id": company["_id"],
            "general": {
                "name": "Q3 Engineering Drive",
                "job_position": "Senior Software Engineer"
            },
            "settings": {
                "interview_mode": "Technical",
                "duration_minutes": 45,
                "strategy": "Balanced",
                "language": "English",
                "difficulty": "Hard"
            },
            "status": "active"
        })
        campaign = await campaign_repo.get_by_id(campaign_id)
    else:
        campaign = campaigns[0]

    company_id_str = str(company["_id"])
    campaign_id_str = str(campaign["_id"])

    # Invite the candidate
    try:
        token = await invitation_service.invite_candidate(
            company_id=company_id_str,
            campaign_id=campaign_id_str,
            name="Priya Sharma (Test)",
            email=CANDIDATE_EMAIL
        )
        print(f"Candidate invited. Token: {token}")

        # Accept the invitation directly
        print(f"Accepting invitation and setting password to {CANDIDATE_PASSWORD}...")
        await invitation_service.accept_invitation(token, CANDIDATE_PASSWORD)

        print("Candidate successfully seeded and activated!")
        print(f"Login Email: {CANDIDATE_EMAIL}")
        print(f"Login Password: {CANDIDATE_PASSWORD}")

    except Exception as e:
        print(f"Failed to seed candidate: {e}")


async def main():
    print("\nSeeding Candidate Data...\n")
    await connect_db()
    try:
        await seed_candidate()
    finally:
        await close_db()
    print("\n✓ Seed completed")


if __name__ == "__main__":
    asyncio.run(main())
