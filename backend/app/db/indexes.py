from app.db.mongo import get_database


async def _safe_create_index(collection, keys, **kwargs):
    """
    Create an index while tolerating duplicate-key and already-existing
    index errors that can occur during startup on a populated database.
    """
    try:
        await collection.create_index(keys, **kwargs)
    except Exception as exc:
        message = str(exc).lower()
        if (
            "already exists" in message
            or "duplicate key" in message
            or "e11000" in message
            or "index with name" in message
        ):
            print(
                f"[WARN] Skipping index {kwargs.get('name', 'unnamed')}: {exc}"
            )
        else:
            raise


async def create_indexes():
    """
    Create all MongoDB indexes required by IntelliHire.
    Safe to run multiple times.
    """

    db = get_database()

    # ==========================================================
    # Users
    # ==========================================================
    await _safe_create_index(
        db.users,
        "email",
        unique=True,
        name="idx_users_email_unique",
    )

    # ==========================================================
    # Companies
    # ==========================================================
    try:
        await db.companies.drop_index(
            "idx_company_email_unique"
        )
    except Exception:
        pass

    await _safe_create_index(
        db.companies,
        [("general.contact_email", 1)],
        unique=True,
        name="idx_company_email_unique",
    )

    # ==========================================================
    # Interview Campaigns
    # ==========================================================
    await _safe_create_index(
        db.interview_campaigns,
        "company_id",
        name="idx_campaign_company",
    )

    await _safe_create_index(
        db.interview_campaigns,
        "status",
        name="idx_campaign_status",
    )

    # ==========================================================
    # Candidates
    # ==========================================================
    await _safe_create_index(
        db.candidates,
        "campaign_id",
        name="idx_candidate_campaign",
    )

    await _safe_create_index(
        db.candidates,
        "company_id",
        name="idx_candidate_company",
    )

    await _safe_create_index(
        db.candidates,
        "email",
        name="idx_candidate_email",
    )

    # ==========================================================
    # Interview Sessions
    # ==========================================================
    await _safe_create_index(
        db.interview_sessions,
        "candidate_id",
        name="idx_session_candidate",
    )

    await _safe_create_index(
        db.interview_sessions,
        "campaign_id",
        name="idx_session_campaign",
    )

    await _safe_create_index(
        db.interview_sessions,
        "company_id",
        name="idx_session_company",
    )

    await _safe_create_index(
        db.interview_sessions,
        "status",
        name="idx_session_status",
    )

    # ==========================================================
    # Interview Reports
    # ==========================================================
    await _safe_create_index(
        db.interview_reports,
        "session_id",
        unique=True,
        name="idx_report_session_unique",
    )

    await _safe_create_index(
        db.interview_reports,
        "company_id",
        name="idx_report_company",
    )

    # ==========================================================
    # Validator Logs
    # ==========================================================
    await _safe_create_index(
        db.validator_logs,
        "session_id",
        name="idx_validator_session",
    )

    await _safe_create_index(
        db.validator_logs,
        "turn_number",
        name="idx_validator_turn",
    )

    print("MongoDB indexes created.")