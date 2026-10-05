"""
G-01 regression: pure-unit layer for the refresh-token helpers added to
jwt_handler.py. These back AuthService.refresh()'s hash lookup and expiry
check; tested in isolation so a hashing-scheme or expiry-window regression
is caught here, not only at the (slower) integration layer.
"""
from datetime import UTC, datetime, timedelta

from app.auth.jwt_handler import create_refresh_token, hash_refresh_token, refresh_token_expiry
from app.config.settings import settings


def test_hash_refresh_token_is_deterministic():
    token = create_refresh_token()

    assert hash_refresh_token(token) == hash_refresh_token(token)


def test_hash_refresh_token_differs_for_different_tokens():
    assert hash_refresh_token(create_refresh_token()) != hash_refresh_token(create_refresh_token())


def test_hash_refresh_token_never_returns_the_raw_token():
    token = create_refresh_token()

    assert hash_refresh_token(token) != token


def test_create_refresh_token_is_not_a_jwt():
    """The refresh token must stay an opaque random string (existing
    design) -- it is never a JWT, so decode_jwt() can never mistake it for
    an access token (a 3-dot-separated, header.payload.signature string)."""
    token = create_refresh_token()

    assert token.count(".") == 0


def test_refresh_token_expiry_uses_the_configured_window():
    before = datetime.now(UTC)

    expiry = refresh_token_expiry()

    expected = before + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    assert abs((expiry - expected).total_seconds()) < 5
