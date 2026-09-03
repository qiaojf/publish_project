from datetime import timedelta

import pytest

from app.core.exceptions import AuthenticationError
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hash_and_verify() -> None:
    hashed = hash_password("correct-password")
    assert hashed != "correct-password"
    assert verify_password("correct-password", hashed)
    assert not verify_password("wrong-password", hashed)


def test_jwt_round_trip_and_expiration() -> None:
    token = create_access_token(42)
    assert decode_access_token(token) == 42
    expired = create_access_token(42, timedelta(seconds=-1))
    with pytest.raises(AuthenticationError):
        decode_access_token(expired)
