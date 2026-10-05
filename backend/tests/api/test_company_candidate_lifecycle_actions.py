"""
C-01 regression tests.

Context: `frontend/src/services/company/candidateService.js` was missing
`suspendCandidate`, `activateCandidate`, `resetCredentials`, `inviteCandidate`,
and `bulkAssignCandidates` — their backend routes already existed and were
fully implemented (backend/app/api/company/candidates.py: PATCH
.../suspend, PATCH .../activate, POST .../reset-credentials, POST /invite,
POST /bulk-assign), but had zero test coverage. No backend code was changed
for C-01; these tests exercise the pre-existing, now-reachable backend
behavior directly (route functions called as plain coroutines, same approach
used for the B-08 team.py tests), covering success, not-found/cross-tenant,
and recruiter-not-assigned paths.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from bson import ObjectId

from app.auth.jwt_handler import TokenPayload
from app.api.company.candidates import (
    suspend_candidate,
    activate_candidate,
    reset_credentials,
    bulk_assign_candidates,
    invite_candidate,
    BulkAssignCandidatesRequest,
)
from app.schemas.candidate_portal import InviteCandidateRequest


def _company_token(company_id: str) -> TokenPayload:
    return TokenPayload(sub=company_id, role="company", exp=9999999999, iat=0)


def _recruiter_token(company_id: str, recruiter_id: str) -> TokenPayload:
    return TokenPayload(
        sub=company_id, role="recruiter", company_id=company_id,
        recruiter_id=recruiter_id, exp=9999999999, iat=0,
    )


# ─── suspend / activate ────────────────────────────────────────────────────

class TestSuspendActivateCandidate:
    @pytest.mark.asyncio
    async def test_company_can_suspend_its_own_candidate(self):
        candidate = {"_id": ObjectId(), "company_id": "company_1", "status": "active"}
        with patch("app.api.company.candidates.CandidateRepository") as MockRepo, \
             patch("app.repositories.user_repository.UserRepository") as MockUserRepo:
            MockRepo.return_value.get = AsyncMock(return_value=candidate)
            MockRepo.return_value.update = AsyncMock()
            MockUserRepo.return_value.update = AsyncMock()

            result = await suspend_candidate(
                candidate_id=str(candidate["_id"]), current_user=_company_token("company_1")
            )

        assert result.success is True
        MockRepo.return_value.update.assert_awaited_once()
        update_args = MockRepo.return_value.update.call_args[0]
        assert update_args[1]["status"] == "suspended"

    @pytest.mark.asyncio
    async def test_suspend_404s_for_a_candidate_belonging_to_a_different_company(self):
        candidate = {"_id": ObjectId(), "company_id": "company_OTHER", "status": "active"}
        with patch("app.api.company.candidates.CandidateRepository") as MockRepo:
            MockRepo.return_value.get = AsyncMock(return_value=candidate)

            with pytest.raises(HTTPException) as exc_info:
                await suspend_candidate(
                    candidate_id=str(candidate["_id"]), current_user=_company_token("company_1")
                )
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_suspend_404s_when_candidate_does_not_exist(self):
        with patch("app.api.company.candidates.CandidateRepository") as MockRepo:
            MockRepo.return_value.get = AsyncMock(return_value=None)
            with pytest.raises(HTTPException) as exc_info:
                await suspend_candidate(candidate_id=str(ObjectId()), current_user=_company_token("company_1"))
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_recruiter_cannot_suspend_a_candidate_not_assigned_to_them(self):
        candidate = {
            "_id": ObjectId(), "company_id": "company_1",
            "assigned_recruiter_id": "recruiter_OTHER", "status": "active",
        }
        with patch("app.api.company.candidates.CandidateRepository") as MockRepo:
            MockRepo.return_value.get = AsyncMock(return_value=candidate)
            with pytest.raises(HTTPException) as exc_info:
                await suspend_candidate(
                    candidate_id=str(candidate["_id"]),
                    current_user=_recruiter_token("company_1", "recruiter_1"),
                )
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_company_can_activate_its_own_candidate(self):
        candidate = {"_id": ObjectId(), "company_id": "company_1", "status": "suspended"}
        with patch("app.api.company.candidates.CandidateRepository") as MockRepo, \
             patch("app.repositories.user_repository.UserRepository") as MockUserRepo:
            MockRepo.return_value.get = AsyncMock(return_value=candidate)
            MockRepo.return_value.update = AsyncMock()
            MockUserRepo.return_value.update = AsyncMock()

            result = await activate_candidate(
                candidate_id=str(candidate["_id"]), current_user=_company_token("company_1")
            )

        assert result.success is True
        update_args = MockRepo.return_value.update.call_args[0]
        assert update_args[1]["status"] == "active"


# ─── reset credentials ──────────────────────────────────────────────────────

class TestResetCredentials:
    @pytest.mark.asyncio
    async def test_resets_password_for_own_candidate(self):
        candidate = {
            "_id": ObjectId(), "company_id": "company_1", "campaign_id": ObjectId(),
            "name": "Jane Candidate", "email": "jane@example.com", "status": "active",
            "user_id": ObjectId(),
        }
        with patch("app.api.company.candidates.CandidateRepository") as MockRepo, \
             patch("app.repositories.user_repository.UserRepository") as MockUserRepo:
            MockRepo.return_value.get = AsyncMock(return_value=candidate)
            MockUserRepo.return_value.update = AsyncMock()

            result = await reset_credentials(
                candidate_id=str(candidate["_id"]), current_user=_company_token("company_1")
            )

        assert result.success is True
        assert result.data["candidate"]["email"] == "jane@example.com"
        MockUserRepo.return_value.update.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_404s_for_a_candidate_belonging_to_a_different_company(self):
        candidate = {"_id": ObjectId(), "company_id": "company_OTHER"}
        with patch("app.api.company.candidates.CandidateRepository") as MockRepo:
            MockRepo.return_value.get = AsyncMock(return_value=candidate)
            with pytest.raises(HTTPException) as exc_info:
                await reset_credentials(
                    candidate_id=str(candidate["_id"]), current_user=_company_token("company_1")
                )
        assert exc_info.value.status_code == 404


# ─── bulk-assign ────────────────────────────────────────────────────────────

class TestBulkAssignCandidates:
    @pytest.mark.asyncio
    async def test_assigns_only_candidates_belonging_to_the_caller_company(self):
        company_id = str(ObjectId())  # bulk_assign_candidates builds ObjectId(current_user.sub)
        recruiter_id = str(ObjectId())
        owned_candidate = {"_id": ObjectId(), "company_id": company_id, "name": "Owned"}
        foreign_candidate = {"_id": ObjectId(), "company_id": str(ObjectId()), "name": "Not Mine"}

        with patch("app.api.company.candidates.CandidateRepository") as MockCandRepo, \
             patch("app.repositories.recruiter_repository.RecruiterRepository") as MockRecruiterRepo, \
             patch("app.repositories.audit_log_repository.AuditLogRepository") as MockAuditRepo:
            MockRecruiterRepo.return_value.get_by_id = AsyncMock(
                return_value={"_id": recruiter_id, "company_id": company_id, "name": "Rex Recruiter"}
            )

            async def fake_get_by_id(cid):
                if cid == str(owned_candidate["_id"]):
                    return owned_candidate
                return foreign_candidate
            MockCandRepo.return_value.get_by_id = AsyncMock(side_effect=fake_get_by_id)
            MockCandRepo.return_value.update = AsyncMock()
            MockAuditRepo.return_value.log_action = AsyncMock()

            req = BulkAssignCandidatesRequest(
                candidate_ids=[str(owned_candidate["_id"]), str(foreign_candidate["_id"])],
                recruiter_id=recruiter_id,
            )
            result = await bulk_assign_candidates(req=req, current_user=_company_token(company_id))

        assert result.data["updated"] == 1  # only the owned candidate counted
        MockCandRepo.return_value.update.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_rejects_a_recruiter_id_from_a_different_company(self):
        with patch("app.repositories.recruiter_repository.RecruiterRepository") as MockRecruiterRepo:
            MockRecruiterRepo.return_value.get_by_id = AsyncMock(
                return_value={"_id": "r1", "company_id": "company_OTHER"}
            )
            req = BulkAssignCandidatesRequest(candidate_ids=[str(ObjectId())], recruiter_id="r1")
            with pytest.raises(HTTPException) as exc_info:
                await bulk_assign_candidates(req=req, current_user=_company_token("company_1"))
        assert exc_info.value.status_code == 400


# ─── invite ─────────────────────────────────────────────────────────────────

class TestInviteCandidate:
    @pytest.mark.asyncio
    async def test_company_can_invite_a_candidate_to_their_own_campaign(self):
        fake_result = {
            "candidate": {
                "id": str(ObjectId()), "name": "New Candidate", "email": "n@example.com",
                "username": "n@example.com", "company_id": "company_1",
                "campaign_id": str(ObjectId()), "status": "active",
            },
            "credentials": {"username": "n@example.com", "temporary_password": "temp123"},
        }
        with patch("app.api.company.candidates.InvitationService") as MockService, \
             patch("app.api.company.candidates.CompanyRepository") as MockCompanyRepo, \
             patch("app.repositories.audit_log_repository.AuditLogRepository") as MockAuditRepo:
            MockService.return_value.invite_candidate = AsyncMock(return_value=fake_result)
            MockCompanyRepo.return_value.update_usage = AsyncMock()
            MockCompanyRepo.return_value.get_by_id = AsyncMock(return_value={"name": "Acme Inc"})
            MockAuditRepo.return_value.log_action = AsyncMock()

            req = InviteCandidateRequest(
                name="New Candidate", email="n@example.com", campaign_id=str(ObjectId())
            )
            result = await invite_candidate(
                req=req,
                current_user=_company_token("company_1"),
                _=_company_token("company_1"),
            )

        assert result.data.candidate.name == "New Candidate"
        MockService.return_value.invite_candidate.assert_awaited_once()
        call_kwargs = MockService.return_value.invite_candidate.call_args.kwargs
        assert call_kwargs["company_id"] == "company_1"
        assert call_kwargs["campaign_id"] == req.campaign_id
