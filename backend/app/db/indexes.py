from app.db.mongo import get_database


async def create_indexes():
    """
    Create all MongoDB indexes required by IntelliHire.
    Safe to run multiple times.
    """

    db = get_database()

    # ==========================================================
    # Users
    # ==========================================================
    await db.users.create_index(
        "email",
        unique=True,
        name="idx_users_email_unique",
    )

    # ==========================================================
    # Companies
    # ==========================================================
    await db.companies.create_index(
        "contact_email",
        unique=True,
        name="idx_company_email_unique",
    )

    # ==========================================================
    # Interview Campaigns
    # ==========================================================
    await db.interview_campaigns.create_index(
        "company_id",
        name="idx_campaign_company",
    )

    await db.interview_campaigns.create_index(
        "status",
        name="idx_campaign_status",
    )

    # ==========================================================
    # Candidates
    # ==========================================================
    await db.candidates.create_index(
        "campaign_id",
        name="idx_candidate_campaign",
    )

    await db.candidates.create_index(
        "company_id",
        name="idx_candidate_company",
    )

    await db.candidates.create_index(
        "email",
        name="idx_candidate_email",
    )

    # ==========================================================
    # Interview Sessions
    # ==========================================================
    await db.interview_sessions.create_index(
        "candidate_id",
        name="idx_session_candidate",
    )

    await db.interview_sessions.create_index(
        "campaign_id",
        name="idx_session_campaign",
    )

    await db.interview_sessions.create_index(
        "company_id",
        name="idx_session_company",
    )

    await db.interview_sessions.create_index(
        "status",
        name="idx_session_status",
    )

    # ==========================================================
    # Interview Reports
    # ==========================================================
    await db.interview_reports.create_index(
        "session_id",
        unique=True,
        name="idx_report_session_unique",
    )

    await db.interview_reports.create_index(
        "company_id",
        name="idx_report_company",
    )

    # ==========================================================
    # Validator Logs
    # ==========================================================
    await db.validator_logs.create_index(
        "session_id",
        name="idx_validator_session",
    )

    await db.validator_logs.create_index(
        "turn_number",
        name="idx_validator_turn",
    )

    print("✅ MongoDB indexes created.")