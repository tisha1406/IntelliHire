"""
G-03 regression: specs.md (Section 20) confirmed the JWT payload never
included `name`/`email`, even though the frontend's AuthContext.jsx reads
`decoded.name`/`decoded.email` -- making them permanently empty strings.

This file is the pure-unit layer: create_access_token/TokenPayload/decode_jwt
now carry name/email end-to-end, and every pre-existing caller that omits
them still works (no other claim is affected, no existing token format is
broken).
"""
from datetime import UTC, datetime, timedelta

from jose import jwt

from app.auth.jwt_handler import TokenPayload, create_access_token
from app.config.settings import settings


def _decode_raw(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


def test_create_access_token_embeds_name_and_email():
    token = create_access_token(user_id="u1", role="recruiter", name="Alex Kim", email="alex@acme.com")

    claims = _decode_raw(token)

    assert claims["name"] == "Alex Kim"
    assert claims["email"] == "alex@acme.com"


def test_decoded_token_payload_exposes_name_and_email():
    token = create_access_token(user_id="u1", role="admin", name="System Administrator", email="admin@intellihire.com")

    payload = TokenPayload(**_decode_raw(token))

    assert payload.name == "System Administrator"
    assert payload.email == "admin@intellihire.com"


def test_create_access_token_without_name_or_email_still_works():
    """Every existing call site that omits name/email (and every token minted
    before G-03) must keep working: the claims are optional, defaulting to
    None, never a required field that would break old callers/tokens."""
    token = create_access_token(user_id="u1", role="company", company_id="co1")

    payload = TokenPayload(**_decode_raw(token))

    assert payload.name is None
    assert payload.email is None
    assert payload.company_id == "co1"


def test_token_payload_accepts_legacy_claims_with_no_name_or_email_keys():
    """A token minted before this fix (no name/email keys in the JWT at all,
    not even null) must still decode without validation errors."""
    now = datetime.now(UTC)
    legacy_claims = {
        "sub": "u1", "role": "candidate",
        "iat": int(now.timestamp()), "exp": int((now + timedelta(minutes=5)).timestamp()),
    }

    payload = TokenPayload(**legacy_claims)

    assert payload.name is None
    assert payload.email is None
