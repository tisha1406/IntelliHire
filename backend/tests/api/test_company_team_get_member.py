"""
B-08 regression tests.

Contract being verified:
- Backend: `GET /company/team/{member_id}` (backend/app/api/company/team.py)
- Frontend: `recruiterManagementService.getRecruiter(id)`
  (frontend/src/services/company/recruiterManagementService.js), which calls
  `GET /company/team/{id}` — this call previously had no matching backend
  route (only `GET ""` list, `PATCH/DELETE /{member_id}`, and sub-resource
  GETs existed), so it would have 404'd if ever invoked.

These tests call the route function directly (the same approach other tests
in tests/api/ use for thin FastAPI handlers) with a mocked RecruiterRepository,
since team.py instantiates its repository inline rather than via Depends.
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
from bson import ObjectId

from app.auth.jwt_handler import TokenPayload
from app.api.company.team import get_team_member


def _token(company_id: str) -> TokenPayload:
    return TokenPayload(sub=company_id, role="company", exp=9999999999, iat=0)


@pytest.mark.asyncio
async def test_get_team_member_returns_the_member_belonging_to_this_company():
    member_doc = {
        "_id": ObjectId(),
        "company_id": "company_1",
        "name": "Jane Recruiter",
        "email": "jane@example.com",
        "role": "recruiter",
        "status": "active",
    }
    with patch("app.api.company.team.RecruiterRepository") as MockRepo:
        instance = MockRepo.return_value
        instance.get_by_id = AsyncMock(return_value=member_doc)

        result = await get_team_member(member_id=str(member_doc["_id"]), current_user=_token("company_1"))

    assert result.id == str(member_doc["_id"])
    assert result.name == "Jane Recruiter"
    assert result.email == "jane@example.com"


@pytest.mark.asyncio
async def test_get_team_member_404s_when_member_does_not_exist():
    with patch("app.api.company.team.RecruiterRepository") as MockRepo:
        instance = MockRepo.return_value
        instance.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await get_team_member(member_id=str(ObjectId()), current_user=_token("company_1"))

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_team_member_404s_when_member_belongs_to_a_different_company():
    """Tenant isolation: a company must not be able to fetch another
    company's recruiter by id, mirroring the existing PATCH/DELETE behavior."""
    member_doc = {
        "_id": ObjectId(),
        "company_id": "company_OTHER",
        "name": "Not Yours",
        "email": "x@example.com",
        "role": "recruiter",
        "status": "active",
    }
    with patch("app.api.company.team.RecruiterRepository") as MockRepo:
        instance = MockRepo.return_value
        instance.get_by_id = AsyncMock(return_value=member_doc)

        with pytest.raises(HTTPException) as exc_info:
            await get_team_member(member_id=str(member_doc["_id"]), current_user=_token("company_1"))

    assert exc_info.value.status_code == 404
