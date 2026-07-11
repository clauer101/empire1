"""Tests for argon2 password hashing and legacy SHA-256 upgrade path."""
from __future__ import annotations

import hashlib
import time
from unittest.mock import AsyncMock, MagicMock, patch


from gameserver.network.auth import AuthService, _hash_password, _verify_password


def test_new_hash_is_argon2() -> None:
    h = _hash_password("hunter2")
    assert h.startswith("$argon2"), f"Expected argon2 hash, got: {h[:20]}"


def test_argon2_verify_correct() -> None:
    h = _hash_password("correct")
    assert _verify_password("correct", h) is True


def test_argon2_verify_wrong() -> None:
    h = _hash_password("correct")
    assert _verify_password("wrong", h) is False


def test_legacy_sha256_still_verifies() -> None:
    legacy = hashlib.sha256("oldpassword".encode()).hexdigest()
    assert _verify_password("oldpassword", legacy) is True


def test_legacy_sha256_wrong_password() -> None:
    legacy = hashlib.sha256("oldpassword".encode()).hexdigest()
    assert _verify_password("notmypassword", legacy) is False


async def test_login_upgrades_legacy_hash() -> None:
    """Successful login with a SHA-256 hash triggers an argon2 re-hash."""
    legacy_hash = hashlib.sha256("secret".encode()).hexdigest()
    db = MagicMock()
    db.get_user = AsyncMock(return_value={"uid": 1, "password_hash": legacy_hash})
    db.update_password_hash = AsyncMock()

    svc = AuthService(db)
    uid = await svc.login("alice", "secret")

    assert uid == 1
    db.update_password_hash.assert_awaited_once()
    new_hash = db.update_password_hash.call_args[0][1]
    assert new_hash.startswith("$argon2"), "Upgraded hash should be argon2"


async def test_login_no_upgrade_for_existing_argon2() -> None:
    """Logins with an existing argon2 hash do not trigger an extra DB write."""
    from gameserver.network.auth import _hasher
    argon_hash = _hasher.hash("secret")
    db = MagicMock()
    db.get_user = AsyncMock(return_value={"uid": 2, "password_hash": argon_hash})
    db.update_password_hash = AsyncMock()

    svc = AuthService(db)
    uid = await svc.login("bob", "secret")

    assert uid == 2
    db.update_password_hash.assert_not_awaited()


def _db_with_password(uid: int, password: str) -> MagicMock:
    db = MagicMock()
    db.get_user_by_uid = AsyncMock(
        return_value={"uid": uid, "password_hash": _hash_password(password)})
    db.update_password_hash = AsyncMock()
    return db


async def test_change_password_wrong_current_password() -> None:
    db = _db_with_password(1, "correct")
    svc = AuthService(db)
    error = await svc.change_password(1, "wrong", "newpass123")
    assert error == "Current password is incorrect"
    db.update_password_hash.assert_not_awaited()


async def test_change_password_new_password_too_short() -> None:
    db = _db_with_password(1, "correct")
    svc = AuthService(db)
    error = await svc.change_password(1, "correct", "ab")
    assert error is not None and "at least" in error
    db.update_password_hash.assert_not_awaited()


async def test_change_password_success() -> None:
    db = _db_with_password(1, "correct")
    svc = AuthService(db)
    error = await svc.change_password(1, "correct", "newpass123")
    assert error is None
    db.update_password_hash.assert_awaited_once()
    new_hash = db.update_password_hash.call_args[0][1]
    assert new_hash.startswith("$argon2")
    assert _verify_password("newpass123", new_hash)


async def test_change_password_unknown_user() -> None:
    db = MagicMock()
    db.get_user_by_uid = AsyncMock(return_value=None)
    svc = AuthService(db)
    error = await svc.change_password(999, "whatever", "newpass123")
    assert error == "User not found"


async def test_change_email_wrong_password() -> None:
    db = _db_with_password(1, "correct")
    svc = AuthService(db)
    error = await svc.change_email(1, "wrong", "new@example.com")
    assert error == "Current password is incorrect"


async def test_change_email_invalid_format() -> None:
    db = _db_with_password(1, "correct")
    svc = AuthService(db)
    error = await svc.change_email(1, "correct", "not-an-email")
    assert error == "Invalid email format"


async def test_change_email_success() -> None:
    db = _db_with_password(1, "correct")
    db.update_email = AsyncMock()
    svc = AuthService(db)
    error = await svc.change_email(1, "correct", "new@example.com")
    assert error is None
    db.update_email.assert_awaited_once_with(1, "new@example.com")


async def test_change_email_can_clear() -> None:
    db = _db_with_password(1, "correct")
    db.update_email = AsyncMock()
    svc = AuthService(db)
    error = await svc.change_email(1, "correct", "")
    assert error is None
    db.update_email.assert_awaited_once_with(1, "")


async def test_request_password_reset_unknown_identifier() -> None:
    db = MagicMock()
    db.get_user_by_email = AsyncMock(return_value=None)
    db.get_user = AsyncMock(return_value=None)
    db.create_password_reset = AsyncMock()
    svc = AuthService(db)
    with patch("gameserver.network.auth.send_password_reset_email",
               new=AsyncMock(return_value=True)) as mock_send:
        await svc.request_password_reset("nobody@example.com")
    db.create_password_reset.assert_not_awaited()
    mock_send.assert_not_awaited()


async def test_request_password_reset_by_username_without_email() -> None:
    """Username matches a real account, but it has no email on file — no reset possible."""
    db = MagicMock()
    db.get_user_by_email = AsyncMock(return_value=None)
    db.get_user = AsyncMock(return_value={"uid": 1, "username": "bob", "email": ""})
    db.create_password_reset = AsyncMock()
    svc = AuthService(db)
    with patch("gameserver.network.auth.send_password_reset_email",
               new=AsyncMock(return_value=True)) as mock_send:
        await svc.request_password_reset("bob")
    db.create_password_reset.assert_not_awaited()
    mock_send.assert_not_awaited()


async def test_request_password_reset_by_username_with_email() -> None:
    db = MagicMock()
    db.get_user_by_email = AsyncMock(return_value=None)
    db.get_user = AsyncMock(
        return_value={"uid": 1, "username": "bob", "email": "bob@example.com"})
    db.create_password_reset = AsyncMock()
    svc = AuthService(db)
    with patch("gameserver.network.auth.send_password_reset_email",
               new=AsyncMock(return_value=True)) as mock_send:
        await svc.request_password_reset("bob")
    db.create_password_reset.assert_awaited_once()
    mock_send.assert_awaited_once()
    assert mock_send.call_args[0][0] == "bob@example.com"


async def test_request_password_reset_known_email() -> None:
    db = MagicMock()
    db.get_user_by_email = AsyncMock(
        return_value={"uid": 1, "email": "alice@example.com"})
    db.create_password_reset = AsyncMock()
    svc = AuthService(db)
    with patch("gameserver.network.auth.send_password_reset_email",
               new=AsyncMock(return_value=True)) as mock_send:
        await svc.request_password_reset("alice@example.com")
    db.create_password_reset.assert_awaited_once()
    token = db.create_password_reset.call_args[0][0]
    mock_send.assert_awaited_once()
    assert mock_send.call_args[0][0] == "alice@example.com"
    assert token in mock_send.call_args[0][1]


async def test_reset_password_invalid_token() -> None:
    db = MagicMock()
    db.get_password_reset = AsyncMock(return_value=None)
    svc = AuthService(db)
    error = await svc.reset_password("bogus", "newpass123")
    assert error == "Reset link is invalid or has expired"


async def test_reset_password_expired_token() -> None:
    db = MagicMock()
    db.get_password_reset = AsyncMock(
        return_value={"token": "t", "uid": 1, "expires_at": int(time.time()) - 10, "used": 0})
    svc = AuthService(db)
    error = await svc.reset_password("t", "newpass123")
    assert error == "Reset link is invalid or has expired"


async def test_reset_password_already_used_token() -> None:
    db = MagicMock()
    db.get_password_reset = AsyncMock(
        return_value={"token": "t", "uid": 1, "expires_at": int(time.time()) + 3600, "used": 1})
    svc = AuthService(db)
    error = await svc.reset_password("t", "newpass123")
    assert error == "Reset link is invalid or has expired"


async def test_reset_password_too_short() -> None:
    db = MagicMock()
    db.get_password_reset = AsyncMock(
        return_value={"token": "t", "uid": 1, "expires_at": int(time.time()) + 3600, "used": 0})
    db.update_password_hash = AsyncMock()
    svc = AuthService(db)
    error = await svc.reset_password("t", "ab")
    assert error is not None and "at least" in error
    db.update_password_hash.assert_not_awaited()


async def test_reset_password_success() -> None:
    db = MagicMock()
    db.get_password_reset = AsyncMock(
        return_value={"token": "t", "uid": 1, "expires_at": int(time.time()) + 3600, "used": 0})
    db.update_password_hash = AsyncMock()
    db.mark_password_reset_used = AsyncMock()
    svc = AuthService(db)
    error = await svc.reset_password("t", "newpass123")
    assert error is None
    db.update_password_hash.assert_awaited_once()
    new_hash = db.update_password_hash.call_args[0][1]
    assert _verify_password("newpass123", new_hash)
    db.mark_password_reset_used.assert_awaited_once_with("t")
