"""
MAIN WORKFLOW CHECKPOINT (company-side completed interview report)
regression tests.

Root cause fixed: app/api/company/candidates.py's interview-listing/report/
PDF endpoints never actually worked against real AI-interview-engine session
documents, due to THREE independent field/type mismatches between the
generic app.repositories.interview_session_repository and the real engine's
InterviewSessionSchema:

1. get_company_interviews() queried `{"company_id": ObjectId(company_id)}`
   (and candidate_id similarly), but InterviewSessionSchema declares
   candidate_id/company_id/campaign_id as plain `str` fields -- the query
   never matched any real session, so the company's interview list was
   always empty.
2. It read `sess.get("status")` to detect completion, but the real engine
   field is `state` (InterviewState: completed|in_progress|...) -- so even
   with the query fixed, a completed interview would still show "Scheduled"
   and never trigger report generation.
3. It returned `"id": str(sess["_id"])` (Mongo's auto-generated ObjectId) and
   get_interview_results()/get_interview_results_pdf() looked sessions up
   via BaseRepository.get_by_id() (`{"_id": ObjectId(session_id)}`), but
   InterviewResultService.generate_result_report() -- and the real engine's
   own candidate-facing report endpoint -- key everything off the engine's
   own `session_id` field (a UUID-like string, unrelated to Mongo's _id).
   Passing the Mongo _id to generate_result_report() always raised
   SessionNotFoundError; passing the real session_id to the ownership-check
   endpoint always raised InvalidId (not 24 hex chars). Neither identifier
   worked for both halves of the round trip.
4. created_at is persisted as an ISO string (InterviewSessionSchema is
   dumped with model_dump(mode="json") before insert), not a BSON Date --
   `.strftime()` on it raised AttributeError, crashing the endpoint outright
   for any session with created_at set (i.e. virtually all real sessions).

A fourth, closely related gap: nothing filtered mode_id="practice" sessions
out of the company's interview list, so a candidate's 3-question practice
round could appear mixed in with real completed interviews.

Fix: use the real field names (`state`, `session_id`, string ids) throughout
get_company_interviews()/get_interview_results()/get_interview_results_pdf(),
exclude mode_id="practice", and tolerate created_at being a string. A new
InterviewSessionRepository.get_by_session_id() method was added (mirrors the
existing get_by_candidate() convention). No change to InterviewResultService,
report generation, PDF rendering, or the AI interview engine itself.

These tests insert real InterviewSessionSchema-shaped documents (via
model_dump(mode="json"), exactly as SessionCreationService really persists
them) into the isolated test MongoDB and call the route functions directly.
"""
from datetime import datetime, timezone
import uuid

from bson import ObjectId
import pytest
import pytest_asyncio

from app.db.mongo import connect_db, close_db, get_database
from app.repositories.company_repository import CompanyRepository
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.candidate_repository import CandidateRepository

from app.ai_interview.schemas.session import InterviewSessionSchema, TopicProgress
from app.ai_interview.schemas.blueprint import InterviewBlueprint, TopicBlueprint
from app.ai_interview.question_engine.schemas import QuestionRecord
from app.ai_interview.answer_engine.schemas import EvaluationRecord
from app.ai_interview.answer_engine.enums import CoverageSignal, FollowUpSignal
from app.ai_interview.core.enums import DifficultyLevel, QuestionType, InterviewState, TopicState

from app.auth.jwt_handler import TokenPayload
from app.api.company.candidates import (
    get_company_interviews,
    get_interview_results,
    get_interview_results_pdf,
)

from fastapi import HTTPException
from pypdf import PdfReader
from io import BytesIO


def _blueprint():
    return InterviewBlueprint(
        blueprint_version="1", total_question_budget=1, min_questions=1, max_questions=1,
        emergency_max_questions=1,
        topics=[TopicBlueprint(
            topic_id="docker", topic_name="Docker", source="resume", priority=1,
            initial_difficulty=DifficultyLevel.MEDIUM, allowed_question_types=[QuestionType.INITIAL],
            question_budget=1,
        )],
    )


def _completed_session_doc(session_id, candidate_id, company_id, campaign_id, mode_id="technical", with_evidence=True):
    kwargs = dict(
        session_id=session_id, candidate_id=str(candidate_id), company_id=str(company_id),
        campaign_id=str(campaign_id), mode_id=mode_id, mode_version=1,
        state=InterviewState.COMPLETED, blueprint=_blueprint(),
        created_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc), version=1,
    )
    if with_evidence:
        qr = QuestionRecord(
            record_id="q1", session_id=session_id, turn_number=1, topic_id="docker",
            question_text="Explain multi-stage Docker builds.", question_type=QuestionType.INITIAL,
            difficulty=DifficultyLevel.MEDIUM,
        )
        ev = EvaluationRecord(
            evaluation_id=str(uuid.uuid4()), question_record_id="q1", topic_id="docker", overall_score=0.9,
            qualitative_coverage_signal=CoverageSignal.QUALITATIVELY_COVERED,
            follow_up_signal=FollowUpSignal.NONE, timestamp=datetime.now(timezone.utc),
        )
        tp = TopicProgress(
            topic_id="docker", state=TopicState.COVERED, structurally_attempted=True,
            qualitatively_covered=True, coverage_score=0.9, readiness_score=0.9, questions_asked=1,
        )
        kwargs.update(question_history=[qr], evaluation_history=[ev], topic_progress=[tp])
    return InterviewSessionSchema(**kwargs).model_dump(mode="json")


@pytest_asyncio.fixture
async def company_candidate_fixtures():
    await connect_db()
    db = get_database()
    company_repo = CompanyRepository()
    campaign_repo = CampaignRepository()
    candidate_repo = CandidateRepository()

    company_id = await company_repo.create({
        "general": {"name": "Checkpoint6 Co", "contact_email": "checkpoint6-co@example.com"},
        "status": "active",
    })
    other_company_id = await company_repo.create({
        "general": {"name": "Other Co", "contact_email": "checkpoint6-other-co@example.com"},
        "status": "active",
    })
    campaign_id = await campaign_repo.create({
        "company_id": ObjectId(company_id), "name": "Checkpoint6 Role", "role_target": "Backend Engineer",
    })
    candidate_id = await candidate_repo.create({
        "name": "Checkpoint6 Candidate", "company_id": ObjectId(company_id),
        "campaign_id": ObjectId(campaign_id), "status": "active",
    })

    yield {
        "company_id": company_id, "other_company_id": other_company_id,
        "campaign_id": campaign_id, "candidate_id": candidate_id,
    }

    await db.interview_sessions.delete_many({"candidate_id": str(candidate_id)})
    await candidate_repo.collection.delete_many({"_id": ObjectId(candidate_id)})
    await campaign_repo.collection.delete_many({"_id": ObjectId(campaign_id)})
    await company_repo.collection.delete_many({"_id": {"$in": [ObjectId(company_id), ObjectId(other_company_id)]}})
    await close_db()


def _company_token(company_id):
    return TokenPayload(sub=str(company_id), role="company", exp=9999999999, iat=0)


class TestCompanyInterviewListing:
    @pytest.mark.asyncio
    async def test_completed_official_session_is_listed_with_real_report_data(self, company_candidate_fixtures):
        f = company_candidate_fixtures
        db = get_database()
        await db.interview_sessions.insert_one(
            _completed_session_doc("sess-official-1", f["candidate_id"], f["company_id"], f["campaign_id"])
        )

        result = await get_company_interviews(current_user=_company_token(f["company_id"]))

        assert len(result["interviews"]) == 1
        entry = result["interviews"][0]
        assert entry["id"] == "sess-official-1"
        assert entry["status"] == "Completed"
        assert entry["aiScore"] == 90
        assert entry["evaluation"]["questions"][0]["q"] == "Explain multi-stage Docker builds."
        assert result["stats"]["completed"] == 1
        assert result["stats"]["averageScore"] == 90

    @pytest.mark.asyncio
    async def test_practice_session_is_excluded_from_the_company_interview_list(self, company_candidate_fixtures):
        f = company_candidate_fixtures
        db = get_database()
        await db.interview_sessions.insert_one(
            _completed_session_doc("sess-practice-1", f["candidate_id"], f["company_id"], f["campaign_id"], mode_id="practice")
        )

        result = await get_company_interviews(current_user=_company_token(f["company_id"]))

        assert len(result["interviews"]) == 0

    @pytest.mark.asyncio
    async def test_practice_and_official_both_present_only_official_is_listed(self, company_candidate_fixtures):
        f = company_candidate_fixtures
        db = get_database()
        await db.interview_sessions.insert_one(
            _completed_session_doc("sess-official-2", f["candidate_id"], f["company_id"], f["campaign_id"])
        )
        await db.interview_sessions.insert_one(
            _completed_session_doc("sess-practice-2", f["candidate_id"], f["company_id"], f["campaign_id"], mode_id="practice")
        )

        result = await get_company_interviews(current_user=_company_token(f["company_id"]))

        ids = [i["id"] for i in result["interviews"]]
        assert ids == ["sess-official-2"]

    @pytest.mark.asyncio
    async def test_completed_session_with_no_evaluations_is_handled_safely(self, company_candidate_fixtures):
        """The existing supported COMPLETED_NO_DATA state must not crash the listing."""
        f = company_candidate_fixtures
        db = get_database()
        await db.interview_sessions.insert_one(
            _completed_session_doc("sess-official-3", f["candidate_id"], f["company_id"], f["campaign_id"], with_evidence=False)
        )

        result = await get_company_interviews(current_user=_company_token(f["company_id"]))

        assert result["interviews"][0]["status"] == "Completed"
        assert result["interviews"][0]["aiScore"] is None

    @pytest.mark.asyncio
    async def test_other_companys_sessions_are_never_listed(self, company_candidate_fixtures):
        f = company_candidate_fixtures
        db = get_database()
        await db.interview_sessions.insert_one(
            _completed_session_doc("sess-official-4", f["candidate_id"], f["company_id"], f["campaign_id"])
        )

        result = await get_company_interviews(current_user=_company_token(f["other_company_id"]))

        assert result["interviews"] == []


class TestCompanyReportAndPdfRetrieval:
    @pytest.mark.asyncio
    async def test_get_interview_results_resolves_by_the_listed_session_id(self, company_candidate_fixtures):
        f = company_candidate_fixtures
        db = get_database()
        await db.interview_sessions.insert_one(
            _completed_session_doc("sess-official-5", f["candidate_id"], f["company_id"], f["campaign_id"])
        )
        listing = await get_company_interviews(current_user=_company_token(f["company_id"]))
        session_id = listing["interviews"][0]["id"]

        report = await get_interview_results(session_id=session_id, current_user=_company_token(f["company_id"]))

        assert report["has_report"] is True
        assert report["overall_score"] == 90
        assert report["topic_scores"][0]["topic_name"] == "Docker"

    @pytest.mark.asyncio
    async def test_get_interview_results_pdf_resolves_by_the_listed_session_id(self, company_candidate_fixtures):
        f = company_candidate_fixtures
        db = get_database()
        await db.interview_sessions.insert_one(
            _completed_session_doc("sess-official-6", f["candidate_id"], f["company_id"], f["campaign_id"])
        )
        listing = await get_company_interviews(current_user=_company_token(f["company_id"]))
        session_id = listing["interviews"][0]["id"]

        resp = await get_interview_results_pdf(session_id=session_id, current_user=_company_token(f["company_id"]))

        assert resp.media_type == "application/pdf"
        reader = PdfReader(BytesIO(resp.body))
        text = "\n".join(p.extract_text() or "" for p in reader.pages)
        assert "90" in text

    @pytest.mark.asyncio
    async def test_cross_company_access_to_results_is_forbidden(self, company_candidate_fixtures):
        f = company_candidate_fixtures
        db = get_database()
        await db.interview_sessions.insert_one(
            _completed_session_doc("sess-official-7", f["candidate_id"], f["company_id"], f["campaign_id"])
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_interview_results(session_id="sess-official-7", current_user=_company_token(f["other_company_id"]))

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_nonexistent_session_id_returns_404_not_500(self, company_candidate_fixtures):
        f = company_candidate_fixtures

        with pytest.raises(HTTPException) as exc_info:
            await get_interview_results(session_id="does-not-exist", current_user=_company_token(f["company_id"]))

        assert exc_info.value.status_code == 404
