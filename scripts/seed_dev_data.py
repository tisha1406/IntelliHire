"""
Seed development data for IntelliHire.

Creates:
- 1 Admin User
- 2 Dummy Companies

Run:

python -m scripts.seed_dev_data
"""

import asyncio

from app.auth.jwt_handler import hash_password
from app.db.mongo import connect_db, close_db
from app.repositories.company_repository import CompanyRepository
from app.repositories.user_repository import UserRepository


ADMIN_EMAIL = "admin@intellihire.dev"
ADMIN_PASSWORD = "ChangeMe123!"


DUMMY_COMPANIES = [
    {
        "name": "Acme Technologies",
        "contact_email": "hr@acme.dev",
        "allowed_languages": ["English", "Hindi"],
        "allowed_voices": ["Aditi"],
        "allowed_strategies": ["Balanced"],
        "allowed_interview_modes": [
            "Balanced",
            "Structured",
        ],
        "allowed_llm_tiers": [
            "Groq",
        ],
        "max_campaigns": 10,
        "status": "active",
    },
    {
        "name": "Northwind Labs",
        "contact_email": "hr@northwind.dev",
        "allowed_languages": ["English"],
        "allowed_voices": ["Aditi"],
        "allowed_strategies": [
            "Balanced",
            "Technical",
        ],
        "allowed_interview_modes": [
            "Deep Technical",
        ],
        "allowed_llm_tiers": [
            "Groq",
        ],
        "max_campaigns": 20,
        "status": "active",
    },
]


async def seed_admin():

    user_repo = UserRepository()

    existing = await user_repo.get_by_email(
        ADMIN_EMAIL
    )

    if existing:
        print("✓ Admin already exists")
        return

    await user_repo.create(
        {
            "name": "System Administrator",
            "email": ADMIN_EMAIL,
            "password_hash": hash_password(
                ADMIN_PASSWORD
            ),
            "role": "admin",
            "company_id": None,
            "status": "active",
        }
    )

    print("✓ Admin created")


async def seed_companies():

    company_repo = CompanyRepository()

    for company in DUMMY_COMPANIES:

        existing = await company_repo.get_by_email(
            company["contact_email"]
        )

        if existing:
            print(
                f"✓ {company['name']} already exists"
            )
            continue

        await company_repo.create(company)

        print(
            f"✓ Created {company['name']}"
        )


async def main():

    print("\nSeeding IntelliHire...\n")

    await connect_db()

    try:

        await seed_admin()

        await seed_companies()

    finally:

        await close_db()

    print("\n✓ Seed completed successfully")


if __name__ == "__main__":
    asyncio.run(main())