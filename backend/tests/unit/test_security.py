"""
Unit tests for security utilities.

These tests require NO database and NO running server.
They test pure functions: password hashing and JWT operations.
"""

from datetime import timedelta

import pytest

from app.utils.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.exceptions import AuthenticationError


class TestPasswordHashing:
    """Tests for bcrypt password hashing."""

    def test_hash_returns_string(self):
        """Hashing a password returns a non-empty string."""
        hashed = get_password_hash("testpassword")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_is_not_plaintext(self):
        """The hash should never equal the original password."""
        password = "my_secret_password"
        hashed = get_password_hash(password)
        assert hashed != password

    def test_verify_correct_password(self):
        """A correct password should verify successfully."""
        password = "correct_password_123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_verify_wrong_password(self):
        """A wrong password should fail verification."""
        hashed = get_password_hash("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_different_hashes_for_same_password(self):
        """bcrypt generates a unique salt each time, so hashes differ."""
        password = "same_password"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        assert hash1 != hash2
        # But both should verify
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestAccessToken:
    """Tests for access token creation and decoding."""

    def test_create_and_decode_access_token(self):
        """An access token should decode correctly with the right claims."""
        user_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        token = create_access_token(subject=user_id)
        payload = decode_token(token, expected_type="access")

        assert payload["sub"] == user_id
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_access_token_rejected_as_refresh(self):
        """An access token should not be accepted when refresh is expected."""
        token = create_access_token(subject="some-user-id")
        with pytest.raises(AuthenticationError, match="Expected refresh token"):
            decode_token(token, expected_type="refresh")


class TestRefreshToken:
    """Tests for refresh token creation and decoding."""

    def test_create_and_decode_refresh_token(self):
        """A refresh token should decode correctly with the right claims."""
        user_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        token = create_refresh_token(subject=user_id)
        payload = decode_token(token, expected_type="refresh")

        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"
        assert "exp" in payload
        assert "iat" in payload

    def test_refresh_token_rejected_as_access(self):
        """A refresh token should not be accepted when access is expected."""
        token = create_refresh_token(subject="some-user-id")
        with pytest.raises(AuthenticationError, match="Expected access token"):
            decode_token(token, expected_type="access")


class TestTokenExpiry:
    """Tests for token expiration handling."""

    def test_expired_token_raises(self):
        """An expired token should raise AuthenticationError."""
        token = create_access_token(
            subject="some-user-id",
            expires_delta=timedelta(seconds=-1),  # Already expired
        )
        with pytest.raises(AuthenticationError, match="expired"):
            decode_token(token, expected_type="access")


class TestTokenTampering:
    """Tests for token integrity validation."""

    def test_tampered_token_raises(self):
        """A modified token should raise AuthenticationError."""
        token = create_access_token(subject="some-user-id")
        # Tamper with the token by changing the first character of the signature
        parts = token.split(".")
        parts[2] = ("A" if parts[2][0] != "A" else "B") + parts[2][1:]
        tampered = ".".join(parts)
        with pytest.raises(AuthenticationError):
            decode_token(tampered, expected_type="access")

    def test_garbage_token_raises(self):
        """A completely invalid string should raise AuthenticationError."""
        with pytest.raises(AuthenticationError):
            decode_token("not.a.jwt", expected_type="access")

    def test_empty_token_raises(self):
        """An empty string should raise AuthenticationError."""
        with pytest.raises(AuthenticationError):
            decode_token("", expected_type="access")
