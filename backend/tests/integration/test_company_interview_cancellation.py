"""
Follow-up to Checkpoint 6: fix for PATCH /company/candidates/interviews/{session_id}/cancel.

Root cause (same category of bug as Checkpoint 6's get_company_interviews()/
get_interview_results()): this endpoint looked the session up via
BaseRepository.get_by_id() (Mongo `_id`), but the real engine's own
session_id string (the identifier the company UI actually has, via
get_company_interviews()) never matches an ObjectId query. It also wrote
`{"status": "cancelled"}`, a field the real InterviewSessionSchema does not
have (the real field is `state`, an InterviewState value) -- so even when
the lookup accidentally succeeded, the write was never recognized by the
engine (find_active_session(), InterviewResultService, etc. all read
`state`).

Fix: resolve by session_id (via the Checkpoint-6-added
InterviewSessionRepository.get_by_session_id()), write the real `state`
field using InterviewState's existing "failed" terminal value (there is no
dedicated CANCELLED value -- "failed" is already used for the same
"will-not-continue" purpose by RuntimeController.execute_transition(...,
RuntimeAction.FAIL) when SessionCreationService detects a stuck session),
and add the missing safety checks: a practice session or an already
completed/failed session must never be cancellable through this endpoint.

Exercises the real route function against the isolated test MongoDB
(tests/conftest.py forces DATABASE_NAME=intellihire_test).
"""
from datetime import datetime, timezone

from bson import ObjectId
import pytest
import pytest_asyncio
from fastapi import HTTPException

from app.db.mongo import connect_db, close_db, get_database
from app.repositories.company_repository import CompanyRepository
from app.repositories.candidate_repository import CandidateRepository

from app.ai_interview.schemas.session import InterviewSessionSchema
from app.ai_interview.schemas.blueprint import InterviewBlueprint, TopicBlueprint
from app.ai_interview.core.enums import DifficultyLevel, QuestionType, InterviewState

from app.auth.jwt_handler import TokenPayload
from app.api.company.candidates import cancel_company_interview


def _blueprint():
    return InterviewBlueprint(
        blueprint_version="1", total_question_budget=1, min_questions=1, max_questions=1,
        emergency_max_questions=1,
        topics=[TopicBlueprint(
            topic_id="t1", topic_name="Python", source="resume", priority=1,
            initial_difficulty=DifficultyLevel.MEDIUM, allowed_question_types=[QuestionType.INITIAL],
            question_budget=1,
        )],
    )


def _session_doc(session_id, candidate_id, company_id, campaign_id, state, mode_id="technical"):
    kwargs = dict(
        session_id=session_id, candidate_id=str(candidate_id), company_id=str(company_id),
        campaign_id=str(campaign_id), mode_id=mode_id, mode_version=1, state=state,
        blueprint=_blueprint(), created_at=datetime.now(timezone.utc), version=1,
    )
    if state == InterviewState.COMPLETED:
        kwargs["completed_at"] = datetime.now(timezone.utc)
    return InterviewSessionSchema(**kwargs).model_dump(mode="json")


@pytest_asyncio.fixture
async def cancellation_fixtures():
    await connect_db()
    db = get_database()
    company_repo = CompanyRepository()
    candidate_repo = CandidateRepository()

    company_id = await company_repo.create({
        "general": {"name": "CancelTest Co", "contact_email": "canceltest-co@example.com"},
        "status": "active",
    })
    other_company_id = await company_repo.create({
        "general": {"name": "CancelTest Other Co", "contact_email": "canceltest-other-co@example.com"},
        "status": "active",
    })
    campaign_id = str(ObjectId())
    candidate_id = await candidate_repo.create({
        "name": "CancelTest Candidate", "company_id": ObjectId(company_id),
        "campaign_id": ObjectId(campaign_id), "status": "active",
    })

    yield {
        "company_id": company_id, "other_company_id": other_company_id,
        "campaign_id": campaign_id, "candidate_id": candidate_id,
    }

    await db.interview_sessions.delete_many({"candidate_id": str(candidate_id)})
    await candidate_repo.collection.delete_many({"_id": ObjectId(candidate_id)})
    await company_repo.collection.delete_many({"_id": {"$in": [ObjectId(company_id), ObjectId(other_company_id)]}})
    await close_db()


def _company_token(company_id):
    return TokenPayload(sub=str(company_id), role="company", company_id=str(company_id), exp=9999999999, iat=0)


class TestCancellationHappyPath:
    @pytest.mark.asyncio
    async def test_upcoming_official_interview_can_be_cancelled(self, cancellation_fixtures):
        f = cancellation_fixtures
        db = get_database()
        await db.interview_sessions.insert_one(
            _session_doc("sess-upcoming-1", f["candidate_id"], f["company_id"], f["campaign_id"], InterviewState.CREATED)
        )

        result = await cancel_company_interview(session_id="sess-upcoming-1", current_user=_company_token(f["company_id"]))

        assert result["message"] == "AI Interview session cancelled successfully."

    @pytest.mark.asyncio
    async def test_persisted_state_uses_the_real_lifecycle_field_and_value(self, cancellation_fixtures):
        """Must write `state` (InterviewState), never the nonexistent
        `status` field -- and must use an existing InterviewState value."""
        f = cancellation_fixtures
        db = get_database()
        await db.interview_sessions.insert_one(
            _session_doc("sess-upcoming-2", f["candidate_id"], f["company_id"], f["campaign_id"], InterviewState.CREATED)
        )

        await cancel_company_interview(session_id="sess-upcoming-2", current_user=_company_token(f["company_id"]))

        doc = await db.interview_sessions.find_one({"session_id": "sess-upcoming-2"})
        assert doc["state"] == InterviewState.FAILED.value
        assert "status" not in doc or doc.get("status") is None

    @pytest.mark.asyncio
    async def test_correct_session_is_resolved_by_engine_session_id_not_mongo_id(self, cancellation_fixtures):
        """The Mongo _id must never be usable as the session_id parameter --
        proves the lookup is genuinely keyed off the session_id field."""
        f = cancellation_fixtures
        db = get_database()
        insert_result = await db.interview_sessions.insert_one(
            _session_doc("sess-upcoming-3", f["candidate_id"], f["company_id"], f["campaign_id"], InterviewState.CREATED)
        )
        mongo_id = str(insert_result.inserted_id)

        with pytest.raises(HTTPException) as exc_info:
            await cancel_company_interview(session_id=mongo_id, current_user=_company_token(f["company_id"]))
        assert exc_info.value.status_code == 404

        # The real session_id still works and is untouched by the failed attempt.
        result = await cancel_company_interview(session_id="sess-upcoming-3", current_user=_company_token(f["company_id"]))
        assert result["message"] == "AI Interview session cancelled successfully."


class TestCancellationScopingAndSafety:
    @pytest.mark.asyncio
    async def test_cross_company_cancellation_is_rejected(self, cancellation_fixtures):
        f = cancellation_fixtures
        db = get_database()
        await db.interview_sessions.insert_one(
            _session_doc("sess-upcoming-4", f["candidate_id"], f["company_id"], f["campaign_id"], InterviewState.CREATED)
        )

        with pytest.raises(HTTPException) as exc_info:
            await cancel_company_interview(session_id="sess-upcoming-4", current_user=_company_token(f["other_company_id"]))

        assert exc_info.value.status_code == 404
        doc = await db.interview_sessions.find_one({"session_id": "sess-upcoming-4"})
        assert doc["state"] == InterviewState.CREATED.value  # untouched

    @pytest.mark.asyncio
    async def test_nonexistent_session_returns_404(self, cancellation_fixtures):
        f = cancellation_fixtures

        with pytest.raises(HTTPException) as exc_info:
            await cancel_company_interview(session_id="does-not-exist", current_user=_company_token(f["company_id"]))

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_completed_interview_cannot_be_cancelled(self, cancellation_fixtures):
        f = cancellation_fixtures
        db = get_database()
        await db.interview_sessions.insert_one(
            _session_doc("sess-completed-1", f["candidate_id"], f["company_id"], f["campaign_id"], InterviewState.COMPLETED)
        )

        with pytest.raises(HTTPException) as exc_info:
            await cancel_company_interview(session_id="sess-completed-1", current_user=_company_token(f["company_id"]))

        assert exc_info.value.status_code == 400
        doc = await db.interview_sessions.find_one({"session_id": "sess-completed-1"})
        assert doc["state"] == InterviewState.COMPLETED.value  # report data not corrupted

    @pytest.mark.asyncio
    async def test_practice_session_cannot_be_cancelled_via_this_endpoint(self, cancellation_fixtures):
        f = cancellation_fixtures
        db = get_database()
        await db.interview_sessions.insert_one(
            _session_doc("sess-practice-1", f["candidate_id"], f["company_id"], f["campaign_id"], InterviewState.CREATED, mode_id="practice")
        )

        with pytest.raises(HTTPException) as exc_info:
            await cancel_company_interview(session_id="sess-practice-1", current_user=_company_token(f["company_id"]))

        assert exc_info.value.status_code == 404
        doc = await db.interview_sessions.find_one({"session_id": "sess-practice-1"})
        assert doc["state"] == InterviewState.CREATED.value  # untouched

    @pytest.mark.asyncio
    async def test_already_failed_session_cannot_be_cancelled_again(self, cancellation_fixtures):
        f = cancellation_fixtures
        db = get_database()
        await db.interview_sessions.insert_one(
            _session_doc("sess-failed-1", f["candidate_id"], f["company_id"], f["campaign_id"], InterviewState.FAILED)
        )

        with pytest.raises(HTTPException) as exc_info:
            await cancel_company_interview(session_id="sess-failed-1", current_user=_company_token(f["company_id"]))

        assert exc_info.value.status_code == 400
