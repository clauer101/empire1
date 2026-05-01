"""Tests for argon2 password hashing and legacy SHA-256 upgrade path."""
from __future__ import annotations

import hashlib
from unittest.mock import AsyncMock, MagicMock

import pytest

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
