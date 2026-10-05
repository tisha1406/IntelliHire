"""
B-01 regression fix tests: GET /api/candidate/settings was 500ing for any
candidate whose settings document was created by a single-field PUT (e.g.
Settings.jsx's handleToggle sends only `{ [key]: !current }`), because
CandidateSettingsRepository.upsert() does a sparse Mongo $set and
CandidatePortalService.get_settings() used to do `SettingsResponse(**settings)`
directly against that possibly-partial document.

These tests exercise CandidatePortalService.get_settings()/update_settings()
directly (same approach as other service-level tests in this suite), with
CandidateSettingsRepository mocked -- no real MongoDB needed, since the bug
and its fix are entirely about in-memory default-merging logic.
"""
import pytest
from unittest.mock import AsyncMock

from app.services.candidate_portal_service import CandidatePortalService, SETTINGS_DEFAULTS
from app.schemas.candidate_portal import SettingsResponse

REQUIRED_FIELDS = [
    "high_contrast", "reduced_motion", "sidebar_auto_collapse",
    "company_updates", "result_notifications", "portal_language", "live_subtitles",
]

# B-01 canonical names that must never regress back to the old, incorrect ones.
CANONICAL_B01_FIELDS = {
    "sidebar_auto_collapse", "interview_reminders", "company_updates",
    "portal_language", "live_subtitles",
}
OLD_INCORRECT_FIELDS = {
    "sidebar_collapsed", "email_notifications", "sms_notifications",
    "language", "subtitles",
}


def _service_with_settings_doc(doc):
    svc = CandidatePortalService.__new__(CandidatePortalService)
    svc.settings_repo = AsyncMock()
    svc.settings_repo.get_by_candidate = AsyncMock(return_value=doc)
    svc.settings_repo.upsert = AsyncMock(return_value=True)
    return svc


class TestGetSettingsCompleteDocument:
    @pytest.mark.asyncio
    async def test_complete_document_returns_its_own_values_unchanged(self):
        doc = {
            "candidate_id": "c1",
            "high_contrast": True, "reduced_motion": True, "sidebar_auto_collapse": False,
            "interview_reminders": False, "company_updates": False,
            "result_notifications": False, "portal_language": "French",
            "live_subtitles": False,
        }
        svc = _service_with_settings_doc(doc)
        result = await svc.get_settings("c1")

        assert isinstance(result, SettingsResponse)
        assert result.high_contrast is True
        assert result.portal_language == "French"
        assert result.interview_reminders is False


class TestGetSettingsLegacyIncompleteDocument:
    @pytest.mark.asyncio
    async def test_document_missing_all_seven_fields_does_not_500(self):
        """Reproduces the exact production bug: a document created by a
        single handleToggle('interview_reminders') PUT call."""
        doc = {"candidate_id": "c1", "interview_reminders": False, "updated_at": "2026-01-01"}
        svc = _service_with_settings_doc(doc)

        result = await svc.get_settings("c1")  # must not raise

        assert isinstance(result, SettingsResponse)
        for field in REQUIRED_FIELDS:
            assert getattr(result, field) == SETTINGS_DEFAULTS[field]

    @pytest.mark.asyncio
    async def test_existing_value_is_not_overwritten_by_defaults(self):
        """The one field the legacy document DOES have must survive the
        merge -- defaults fill gaps, they never clobber real data."""
        doc = {"candidate_id": "c1", "interview_reminders": False}
        svc = _service_with_settings_doc(doc)

        result = await svc.get_settings("c1")

        assert result.interview_reminders is False  # not the default (True)

    @pytest.mark.asyncio
    async def test_partially_complete_document_only_backfills_missing_fields(self):
        doc = {
            "candidate_id": "c1",
            "high_contrast": True,  # non-default, must survive
            "portal_language": "German",  # non-default, must survive
            # everything else missing
        }
        svc = _service_with_settings_doc(doc)

        result = await svc.get_settings("c1")

        assert result.high_contrast is True
        assert result.portal_language == "German"
        assert result.reduced_motion == SETTINGS_DEFAULTS["reduced_motion"]
        assert result.live_subtitles == SETTINGS_DEFAULTS["live_subtitles"]

    @pytest.mark.asyncio
    async def test_no_document_at_all_returns_full_defaults(self):
        svc = _service_with_settings_doc(None)

        result = await svc.get_settings("c1")

        for field, expected in SETTINGS_DEFAULTS.items():
            assert getattr(result, field) == expected


class TestSettingsResponseValidation:
    def test_settings_defaults_validate_successfully(self):
        SettingsResponse(**SETTINGS_DEFAULTS)  # must not raise

    def test_canonical_b01_field_names_are_exactly_what_settings_defaults_declares(self):
        assert CANONICAL_B01_FIELDS <= set(SETTINGS_DEFAULTS.keys())

    def test_no_old_incorrect_field_names_are_required(self):
        declared_fields = set(SettingsResponse.model_fields.keys())
        assert not (OLD_INCORRECT_FIELDS & declared_fields)


class TestPutThenGetRoundTrip:
    @pytest.mark.asyncio
    async def test_put_updates_canonical_field_then_get_reflects_it(self):
        """Simulates: GET (nothing yet) -> toggle interview_reminders ->
        PUT (sparse) -> GET again -> change survives and nothing else 500s."""
        svc = CandidatePortalService.__new__(CandidatePortalService)
        svc.settings_repo = AsyncMock()

        # Nothing persisted yet.
        svc.settings_repo.get_by_candidate = AsyncMock(return_value=None)
        initial = await svc.get_settings("c1")
        assert initial.interview_reminders is True  # default

        # PUT only sends the one changed field (handleToggle's real payload shape).
        stored = {}

        async def fake_upsert(candidate_id, update_data):
            stored.update(update_data)
            return True

        svc.settings_repo.upsert = fake_upsert
        await svc.update_settings("c1", {"interview_reminders": False})
        assert stored == {"interview_reminders": False}

        # Subsequent GET must reflect the change and still not 500, even
        # though `stored` is missing every other field.
        svc.settings_repo.get_by_candidate = AsyncMock(return_value={"candidate_id": "c1", **stored})
        after = await svc.get_settings("c1")

        assert after.interview_reminders is False
        for field in REQUIRED_FIELDS:
            assert getattr(after, field) == SETTINGS_DEFAULTS[field]

    @pytest.mark.asyncio
    async def test_update_settings_filters_none_values(self):
        """Existing behavior (unchanged by this fix): update_settings must
        not persist fields the caller didn't actually set."""
        svc = CandidatePortalService.__new__(CandidatePortalService)
        svc.settings_repo = AsyncMock()
        captured = {}

        async def fake_upsert(candidate_id, update_data):
            captured.update(update_data)
            return True

        svc.settings_repo.upsert = fake_upsert
        await svc.update_settings("c1", {"portal_language": "Spanish", "high_contrast": None})

        assert captured == {"portal_language": "Spanish"}
