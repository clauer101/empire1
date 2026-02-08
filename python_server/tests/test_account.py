"""Tests for account creation, login, deletion, and re-creation.

Uses an in-memory SQLite database via :class:`Database` and
:class:`AuthService` directly — no network layer needed.
"""

import pytest
import pytest_asyncio

from gameserver.persistence.database import Database
from gameserver.network.auth import AuthService


# ── Fixtures ────────────────────────────────────────────────

@pytest_asyncio.fixture
async def db(tmp_path):
    """Create a fresh in-memory database for each test."""
    database = Database(str(tmp_path / "test.db"))
    await database.connect()
    yield database
    await database.close()


@pytest_asyncio.fixture
async def auth(db):
    """AuthService backed by the test database."""
    return AuthService(db)


# ── Database layer tests ────────────────────────────────────

@pytest.mark.asyncio
async def test_create_user(db):
    uid = await db.create_user("alice", "hash123", "alice@test.de", "Aliceland")
    assert uid > 0


@pytest.mark.asyncio
async def test_get_user_after_create(db):
    await db.create_user("bob", "hash456", "bob@test.de", "Bobburg")
    user = await db.get_user("bob")
    assert user is not None
    assert user["username"] == "bob"
    assert user["email"] == "bob@test.de"
    assert user["empire_name"] == "Bobburg"


@pytest.mark.asyncio
async def test_get_user_not_found(db):
    user = await db.get_user("nobody")
    assert user is None


@pytest.mark.asyncio
async def test_delete_user(db):
    await db.create_user("charlie", "hash789", "", "Charland")
    deleted = await db.delete_user("charlie")
    assert deleted is True
    assert await db.get_user("charlie") is None


@pytest.mark.asyncio
async def test_delete_nonexistent_user(db):
    deleted = await db.delete_user("ghost")
    assert deleted is False


@pytest.mark.asyncio
async def test_recreate_user_after_delete(db):
    uid1 = await db.create_user("dave", "h1", "d@test.de", "Daveland")
    await db.delete_user("dave")
    uid2 = await db.create_user("dave", "h2", "d2@test.de", "Daveland2")
    assert uid2 > 0
    assert uid2 != uid1  # AUTOINCREMENT gives a new UID
    user = await db.get_user("dave")
    assert user["empire_name"] == "Daveland2"
    assert user["uid"] == uid2


@pytest.mark.asyncio
async def test_unique_username_constraint(db):
    await db.create_user("eve", "hash", "", "Eveland")
    with pytest.raises(Exception):  # IntegrityError from sqlite
        await db.create_user("eve", "hash2", "", "Eveland2")


# ── AuthService signup tests ───────────────────────────────

@pytest.mark.asyncio
async def test_signup_success(auth):
    result = await auth.signup("player1", "pass1234", "p1@test.de", "Empire1")
    assert isinstance(result, int)
    assert result > 0


@pytest.mark.asyncio
async def test_signup_short_username(auth):
    result = await auth.signup("x", "pass1234")
    assert result == "Username must be at least 2 characters"


@pytest.mark.asyncio
async def test_signup_long_username(auth):
    result = await auth.signup("a" * 21, "pass1234")
    assert result == "Username must be at most 20 characters"


@pytest.mark.asyncio
async def test_signup_short_password(auth):
    result = await auth.signup("player2", "ab")
    assert result == "Password must be at least 4 characters"


@pytest.mark.asyncio
async def test_signup_invalid_email(auth):
    result = await auth.signup("player3", "pass1234", "not-an-email")
    assert result == "Invalid email format"


@pytest.mark.asyncio
async def test_signup_duplicate_username(auth):
    await auth.signup("player4", "pass1234", "p4@test.de")
    result = await auth.signup("player4", "other1234", "p4b@test.de")
    assert result == "Username already taken"


@pytest.mark.asyncio
async def test_signup_default_empire_name(auth, db):
    uid = await auth.signup("player5", "pass1234", "p5@test.de")
    user = await db.get_user("player5")
    assert user["empire_name"] == "player5's Empire"


# ── AuthService login tests ────────────────────────────────

@pytest.mark.asyncio
async def test_login_success(auth):
    await auth.signup("loginuser", "secret99", "lu@test.de", "LoginEmpire")
    uid = await auth.login("loginuser", "secret99")
    assert uid is not None
    assert uid > 0


@pytest.mark.asyncio
async def test_login_wrong_password(auth):
    await auth.signup("loginuser2", "correct1", "lu2@test.de")
    uid = await auth.login("loginuser2", "wrongpass")
    assert uid is None


@pytest.mark.asyncio
async def test_login_unknown_user(auth):
    uid = await auth.login("noexist", "whatever")
    assert uid is None


# ── Delete + re-create full flow ────────────────────────────

@pytest.mark.asyncio
async def test_delete_and_recreate_account(auth, db):
    """Full lifecycle: signup → login → delete → login fails → signup again."""
    # 1. Create account
    uid1 = await auth.signup("phoenix", "rise1234", "ph@test.de", "PhoenixEmpire")
    assert isinstance(uid1, int)

    # 2. Login works
    assert await auth.login("phoenix", "rise1234") == uid1

    # 3. Delete the account
    deleted = await db.delete_user("phoenix")
    assert deleted is True

    # 4. Login must fail after deletion
    assert await auth.login("phoenix", "rise1234") is None

    # 5. Re-create the account (same username, new data)
    uid2 = await auth.signup("phoenix", "newpass99", "ph2@test.de", "PhoenixReborn")
    assert isinstance(uid2, int)
    assert uid2 != uid1

    # 6. Login works with new password
    assert await auth.login("phoenix", "newpass99") == uid2

    # 7. Old password no longer works
    assert await auth.login("phoenix", "rise1234") is None

    # 8. Verify stored data is the new data
    user = await db.get_user("phoenix")
    assert user["empire_name"] == "PhoenixReborn"
    assert user["email"] == "ph2@test.de"
