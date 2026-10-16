"""
R-11 regression tests: recruiters are managed inside the Company portal, not
a separate recruiter-facing workflow (final product decision).

Before this fix, four standalone recruiter self-service routers
(dashboard/candidates/campaigns/interviews, under /api/recruiter/) were
mounted in app/main.py despite having zero frontend callers and zero test
coverage -- confirmed by grep before removal. They represented the exact
"separate recruiter portal" architecture the product decision rejects, and
left live, unaudited, authenticated endpoints reachable at runtime.

/api/recruiter/profile is kept: recruiters still use it for their own
profile/password-change within the shared Company-portal architecture
(frontend/src/services/recruiter/recruiterService.js).
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_removed_recruiter_self_service_routes_are_gone():
    """The 4 obsolete standalone routers must no longer be registered --
    hitting their old prefixes should 404 (no route), not reach a handler."""
    for path in (
        "/api/recruiter/dashboard/stats",
        "/api/recruiter/candidates/",
        "/api/recruiter/campaigns/",
        "/api/recruiter/interviews/",
    ):
        response = client.get(path)
        assert response.status_code == 404, f"{path} should no longer be routed"


def test_recruiter_profile_router_still_registered():
    """profile.py must remain mounted -- recruiters still need it for their
    own profile within the shared Company portal. Expect a 401/403 (route
    exists, auth required) rather than a 404 (route missing)."""
    response = client.get("/api/recruiter/profile/")
    assert response.status_code in (401, 403), (
        f"expected an auth failure (route exists) not a 404, got {response.status_code}"
    )


def test_no_internal_code_imports_the_removed_recruiter_routers():
    """Static guard against silently reintroducing the rejected standalone
    recruiter-portal architecture."""
    import app.main as main_module
    import inspect

    source = inspect.getsource(main_module)
    for removed in (
        "recruiter.dashboard", "recruiter.candidates",
        "recruiter.campaigns", "recruiter.interviews",
    ):
        assert removed not in source, f"app.main should no longer reference {removed}"
