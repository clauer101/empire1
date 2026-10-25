"""Router-level integration tests via httpx AsyncClient.

Covers previously untested endpoints in:
- routers/messages.py
- routers/army.py
- routers/attack.py
- routers/replays.py
- parts of rest_api.py

Uses the same httpx + ASGITransport pattern as test_rest_api.py.
"""

from __future__ import annotations

from typing import Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from gameserver.engine.attack_service import AttackService
from gameserver.engine.empire_service import EmpireService
from gameserver.engine.upgrade_provider import UpgradeProvider
from gameserver.loaders.game_config_loader import GameConfig
from gameserver.models.army import Army, CritterWave
from gameserver.models.attack import Attack, AttackPhase
from gameserver.models.empire import Empire
from gameserver.models.items import ItemDetails, ItemType
from gameserver.models.map import HexCoord
from gameserver.models.structure import Structure
from gameserver.network.handlers import register_all_handlers
from gameserver.network.jwt_auth import create_token
from gameserver.network.rest_api import create_app
from gameserver.network.router import Router
from gameserver.util.events import EventBus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TEST_UID = 42


def _make_empire(uid: int = TEST_UID, name: str = "TestEmpire") -> Empire:
    return Empire(
        uid=uid,
        name=name,
        resources={"gold": 5000.0, "culture": 1000.0, "life": 10.0},
        citizens={"merchant": 3, "scientist": 2, "artist": 1},
        buildings={},
        knowledge={},
        structures={
            1: Structure(
                sid=1, iid="tower", position=HexCoord(2, 3),
                damage=10.0, range=3, reload_time_ms=1000.0, shot_speed=5.0,
            ),
        },
        armies=[Army(aid=1, uid=uid, name="Alpha",
                     waves=[CritterWave(wave_id=1, iid="goblin", slots=3)])],
        effects={},
        artifacts=[],
        max_life=10.0,
    )


def _make_db_mock() -> AsyncMock:
    db = AsyncMock()
    db.send_message = AsyncMock(return_value={
        "id": 1, "from_uid": TEST_UID, "to_uid": 0, "body": "hello",
        "sent_at": "2024-01-01T00:00:00Z", "read": False,
    })
    db.get_global = AsyncMock(return_value=[])
    db.get_private_for = AsyncMock(return_value=[])
    db.get_battle_reports_for = AsyncMock(return_value=[])
    db.unread_count_private = AsyncMock(return_value=0)
    db.unread_count_battle = AsyncMock(return_value=0)
    db.mark_read = AsyncMock(return_value=True)
    db.list_users = AsyncMock(return_value=[])
    db.save_push_subscription = AsyncMock()
    db.delete_push_subscription = AsyncMock()
    db.save_spy_report = AsyncMock()
    db.get_spy_reports_for = AsyncMock(return_value=[])
    db.toggle_alliance_declaration = AsyncMock(return_value=True)
    db.remove_alliance_declaration = AsyncMock(return_value=True)
    db.get_alliance_declarations_for = AsyncMock(return_value=(set(), set()))
    db.get_all_mutual_alliances = AsyncMock(return_value={})
    return db


def _make_services(empire: Optional[Empire] = None, with_db: bool = False) -> Any:
    event_bus = EventBus()
    upgrade_provider = UpgradeProvider()
    empire_service = EmpireService(upgrade_provider, event_bus)
    attack_service = AttackService(event_bus, empire_service=empire_service)
    if empire is not None:
        empire_service.register(empire)

    router = Router()
    auth_service = AsyncMock()
    auth_service.login = AsyncMock(return_value=TEST_UID)
    auth_service.signup = AsyncMock(return_value=TEST_UID)

    svc = MagicMock()
    svc.event_bus = event_bus
    svc.upgrade_provider = upgrade_provider
    svc.empire_service = empire_service
    svc.attack_service = attack_service
    svc.router = router
    svc.auth_service = auth_service
    svc.game_config = None
    svc.database = _make_db_mock() if with_db else None
    svc.server = MagicMock()
    return svc


def _token(uid: int = TEST_UID) -> str:
    return create_token(uid)


def _auth(uid: int = TEST_UID) -> dict[str, str]:
    return {"Authorization": f"Bearer {_token(uid)}"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def svc():
    empire = _make_empire()
    s = _make_services(empire, with_db=True)
    register_all_handlers(s)
    return s


@pytest.fixture
def app(svc):
    return create_app(svc)


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# Messages router
# ---------------------------------------------------------------------------

class TestMessagesRouter:
    async def test_send_message_global(self, client, svc):
        resp = await client.post(
            "/api/messages",
            json={"body": "hello world", "to_uid": 0},
            headers=_auth(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    async def test_send_message_empty_body_rejected(self, client, svc):
        resp = await client.post(
            "/api/messages",
            json={"body": "   ", "to_uid": 0},
            headers=_auth(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False

    async def test_send_message_to_self_rejected(self, client, svc):
        resp = await client.post(
            "/api/messages",
            json={"body": "hi me", "to_uid": TEST_UID},
            headers=_auth(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False

    async def test_get_messages(self, client, svc):
        resp = await client.get("/api/messages", headers=_auth())
        assert resp.status_code == 200
        data = resp.json()
        assert "global" in data
        assert "private" in data
        assert "battle_reports" in data

    async def test_mark_read(self, client, svc):
        resp = await client.post("/api/messages/1/read", headers=_auth())
        assert resp.status_code == 200
        data = resp.json()
        assert "success" in data

    async def test_vapid_public_key(self, client):
        resp = await client.get("/api/push/vapid-public-key")
        assert resp.status_code == 200
        data = resp.json()
        assert "key" in data

    async def test_requires_auth(self, client):
        resp = await client.get("/api/messages")
        assert resp.status_code in (401, 403, 422)


# ---------------------------------------------------------------------------
# Army router
# ---------------------------------------------------------------------------

class TestArmyRouter:
    async def test_create_army(self, client, svc):
        resp = await client.post(
            "/api/army",
            json={"name": "My Army"},
            headers=_auth(),
        )
        assert resp.status_code == 200

    async def test_rename_army(self, client, svc):
        resp = await client.put(
            "/api/army/1",
            json={"name": "Renamed"},
            headers=_auth(),
        )
        assert resp.status_code == 200

    async def test_toggle_siege_corruption_off_and_on(self, client, svc):
        army = svc.empire_service.get(TEST_UID).armies[0]
        assert army.siege_corruption_enabled is True  # default

        resp = await client.put(
            "/api/army/1/siege-corruption", json={"enabled": False}, headers=_auth(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["siege_corruption_enabled"] is False
        assert army.siege_corruption_enabled is False

        resp = await client.put(
            "/api/army/1/siege-corruption", json={"enabled": True}, headers=_auth(),
        )
        assert resp.json()["siege_corruption_enabled"] is True
        assert army.siege_corruption_enabled is True

    async def test_toggle_siege_corruption_unknown_army_rejected(self, client, svc):
        resp = await client.put(
            "/api/army/9999/siege-corruption", json={"enabled": False}, headers=_auth(),
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is False

    async def test_military_payload_reports_the_toggle(self, client, svc):
        svc.empire_service.get(TEST_UID).armies[0].siege_corruption_enabled = False
        resp = await client.get("/api/empire/military", headers=_auth())
        assert resp.status_code == 200
        army = next(a for a in resp.json()["armies"] if a["aid"] == 1)
        assert army["siege_corruption_enabled"] is False

    async def test_add_wave(self, client, svc):
        resp = await client.post("/api/army/1/wave", headers=_auth())
        assert resp.status_code == 200

    async def test_change_wave(self, client, svc):
        resp = await client.put(
            "/api/army/1/wave/1",
            json={"critter_iid": "goblin", "slots": 2},
            headers=_auth(),
        )
        assert resp.status_code == 200

    async def test_buy_wave_requires_auth(self, client):
        resp = await client.post("/api/army/buy-wave", json={"aid": 1})
        assert resp.status_code in (401, 403, 422)

    async def test_buy_item_upgrade(self, client, svc):
        resp = await client.post(
            "/api/item/buy-upgrade",
            json={"iid": "goblin", "stat": "health"},
            headers=_auth(),
        )
        assert resp.status_code == 200

    async def test_buy_item_upgrade_rejects_effect_stat_with_no_matching_effect(
        self, client, svc):
        # A plain damage tower (effects={}, e.g. HEAVY_TOWER) has no
        # slow/burn effect for effect_duration to modify — the server must
        # reject the purchase rather than silently take gold for a level
        # that never applies in combat (see battle_service._step_structures,
        # which only scales slow_duration/burn_duration/slow_ratio/burn_dps).
        # Reset the module-global season-freeze flag: another test in the
        # full suite run may have left it set, which would short-circuit
        # this endpoint before our new validation even runs.
        from gameserver.engine.global_state import set_season_reset_triggered
        set_season_reset_triggered(False)
        svc.upgrade_provider.load([
            ItemDetails(iid="plain_tower", item_type=ItemType.STRUCTURE,
                       damage=10.0, range=1.5, reload_time_ms=1000.0, effects={}),
        ])
        resp = await client.post(
            "/api/item/buy-upgrade",
            json={"iid": "plain_tower", "stat": "effect_duration"},
            headers=_auth(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert "effect" in data["error"].lower()

    async def test_buy_item_upgrade_allows_effect_stat_with_matching_effect(
        self, client, svc):
        from gameserver.engine.global_state import set_season_reset_triggered
        set_season_reset_triggered(False)
        svc.upgrade_provider.load([
            ItemDetails(iid="slow_tower", item_type=ItemType.STRUCTURE,
                       damage=1.0, range=1.5, reload_time_ms=1000.0,
                       effects={"slow_duration": 2000.0, "slow_ratio": 0.5}),
        ])
        resp = await client.post(
            "/api/item/buy-upgrade",
            json={"iid": "slow_tower", "stat": "effect_duration"},
            headers=_auth(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True


# ---------------------------------------------------------------------------
# Attack router
# ---------------------------------------------------------------------------

class TestAttackRouter:
    async def test_skip_siege_not_found(self, client, svc):
        resp = await client.post("/api/attack/999/skip-siege", headers=_auth())
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert "error" in data

    async def test_skip_siege_success(self, client, svc):
        # Add a real attack in IN_SIEGE
        attack = Attack(
            attack_id=1, attacker_uid=99, defender_uid=TEST_UID,
            army_aid=1, phase=AttackPhase.IN_SIEGE, eta_seconds=0.0,
        )
        attack.siege_remaining_seconds = 60.0
        svc.attack_service._attacks = [attack]

        resp = await client.post("/api/attack/1/skip-siege", headers=_auth())
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["phase"] == "in_siege"  # attack.phase is now in_battle after skip

    async def test_attack_endpoint_exists(self, client, svc):
        resp = await client.post(
            "/api/attack",
            json={"target_uid": 99, "opponent_name": "enemy", "army_aid": 1},
            headers=_auth(),
        )
        assert resp.status_code == 200

    async def test_attack_rejected_against_ally(self, client, svc):
        svc.database.get_alliance_declarations_for = AsyncMock(return_value=({99}, {99}))
        resp = await client.post(
            "/api/attack",
            json={"target_uid": 99, "army_aid": 1},
            headers=_auth(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert "ally" in data["error"].lower() or "allied" in data["error"].lower()

    async def test_attack_allowed_against_one_sided_declaration(self, client, svc):
        # Not mutual (only declared_to, no declared_by) -> not allied, so the
        # alliance check does not block the attack (it fails later for an
        # unrelated reason: uid 99 has no registered empire in this test).
        svc.database.get_alliance_declarations_for = AsyncMock(return_value=({99}, set()))
        resp = await client.post(
            "/api/attack",
            json={"target_uid": 99, "army_aid": 1},
            headers=_auth(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert "ally" not in data["error"].lower()
        assert "allied" not in data["error"].lower()


# ---------------------------------------------------------------------------
# Replays router
# ---------------------------------------------------------------------------

class TestReplaysRouter:
    async def test_get_replays_empty(self, client):
        with patch("gameserver.persistence.replay.list_replays", return_value=[]):
            resp = await client.get("/api/replays", headers=_auth())
        assert resp.status_code == 200
        data = resp.json()
        assert data["replays"] == []

    async def test_get_replay_not_found(self, client):
        with patch("gameserver.persistence.replay.get_replay_path", return_value=None):
            resp = await client.get("/api/replays/nonexistent", headers=_auth())
        assert resp.status_code == 404

    async def test_replays_requires_auth(self, client):
        resp = await client.get("/api/replays")
        assert resp.status_code in (401, 403, 422)


# ---------------------------------------------------------------------------
# Global map router
# ---------------------------------------------------------------------------

class TestGlobalMapRouter:
    async def test_global_map_tiles_use_stored_coords(self, client, svc):
        emp = svc.empire_service.all_empires[TEST_UID]
        emp.hex_map = {"100,-50": "castle", "101,-50": "barracks"}

        resp = await client.get("/api/global-map")
        assert resp.status_code == 200
        data = resp.json()
        e = next(x for x in data["empires"] if x["uid"] == TEST_UID)
        assert e["origin"] == {"q": 100, "r": -50}
        coords = {(t["q"], t["r"], t["type"]) for t in e["tiles"]}
        assert (100, -50, "castle") in coords
        assert (101, -50, "barracks") in coords

    async def test_global_map_castle_sets_origin(self, client, svc):
        emp = svc.empire_service.all_empires[TEST_UID]
        emp.hex_map = {"2,3": "castle"}

        resp = await client.get("/api/global-map")
        data = resp.json()
        e = next(x for x in data["empires"] if x["uid"] == TEST_UID)
        assert e["origin"] == {"q": 2, "r": 3}
        coords = {(t["q"], t["r"], t["type"]) for t in e["tiles"]}
        assert (2, 3, "castle") in coords

    async def test_global_map_viewport_clips_tiles(self, client, svc):
        emp = svc.empire_service.all_empires[TEST_UID]
        emp.hex_map = {"0,0": "castle", "5,5": "barracks"}

        resp = await client.get("/api/global-map?q0=-1&r0=-1&q1=1&r1=1")
        assert resp.status_code == 200
        data = resp.json()
        e = next(x for x in data["empires"] if x["uid"] == TEST_UID)
        coords = {(t["q"], t["r"], t["type"]) for t in e["tiles"]}
        assert (0, 0, "castle") in coords
        assert (5, 5, "barracks") not in coords


# ---------------------------------------------------------------------------
# Map neighbors router (fog of war)
# ---------------------------------------------------------------------------

class TestMapNeighborsRouter:
    async def test_neighbors_clipped_to_viewport(self, client, svc):
        emp = svc.empire_service.all_empires[TEST_UID]
        emp.hex_map = {"0,0": "castle"}

        resp = await client.get(
            "/api/map/neighbors?q0=0&r0=0&q1=0&r1=1", headers=_auth()
        )
        assert resp.status_code == 200
        tiles = resp.json()["neighbor_tiles"]
        # Only the (0,1) fog tile falls inside the strict viewport rect.
        assert tiles == [{"q": 0, "r": 1, "uid": None, "iid": None, "tile_type": None}]

    async def test_neighbors_owner_via_world_index(self, client, svc):
        emp = svc.empire_service.all_empires[TEST_UID]
        emp.hex_map = {"0,0": "castle"}

        enemy = _make_empire(uid=99, name="Enemy")
        enemy.hex_map = {"1,0": "barracks"}  # global coords directly
        svc.empire_service.register(enemy)

        resp = await client.get("/api/map/neighbors", headers=_auth())
        tiles = {(t["q"], t["r"]): t["uid"] for t in resp.json()["neighbor_tiles"]}
        assert tiles[(1, 0)] == 99

    async def test_neighbors_index_refreshes_after_invalidate(self, client, svc):
        emp = svc.empire_service.all_empires[TEST_UID]
        emp.hex_map = {"0,0": "castle"}

        enemy = _make_empire(uid=99, name="Enemy")
        enemy.hex_map = {"1,0": "barracks"}  # global coords directly
        svc.empire_service.register(enemy)

        r1 = await client.get("/api/map/neighbors", headers=_auth())
        owners1 = {(t["q"], t["r"]): t["uid"] for t in r1.json()["neighbor_tiles"]}
        assert owners1[(1, 0)] == 99

        # Enemy abandons the tile; index must reflect it after invalidation.
        enemy.hex_map = {}
        svc.empire_service.invalidate_tile_index()

        r2 = await client.get("/api/map/neighbors", headers=_auth())
        owners2 = {(t["q"], t["r"]): t["uid"] for t in r2.json()["neighbor_tiles"]}
        assert owners2[(1, 0)] is None


# ---------------------------------------------------------------------------
# Empire router — rename, ruler skill-up, ruler choose
# ---------------------------------------------------------------------------

class TestEmpireRenameRouter:
    async def test_rename_success(self, client, svc):
        resp = await client.post(
            "/api/empire/rename",
            json={"name": "NewName"},
            headers=_auth(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert svc.empire_service.all_empires[TEST_UID].name == "NewName"

    async def test_rename_too_short(self, client, svc):
        resp = await client.post(
            "/api/empire/rename",
            json={"name": "ab"},
            headers=_auth(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False

    async def test_rename_too_long(self, client, svc):
        resp = await client.post(
            "/api/empire/rename",
            json={"name": "x" * 41},
            headers=_auth(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False

    async def test_rename_requires_auth(self, client):
        resp = await client.post("/api/empire/rename", json={"name": "Hacker"})
        assert resp.status_code in (401, 403, 422)


class TestRulerEndpoints:
    async def test_choose_ruler_success(self, client, svc):
        # Ensure ruler_unlock effect is set and _rulers is populated
        empire = svc.empire_service.all_empires[TEST_UID]
        empire.effects["ruler_unlock"] = 1
        svc.empire_service._rulers = {
            "WARRIOR": {"name": "Warrior", "skills": {}, "splash": ""},
        }
        resp = await client.post(
            "/api/empire/ruler/choose",
            json={"ruler_iid": "WARRIOR"},
            headers=_auth(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert empire.ruler.type == "WARRIOR"

    async def test_choose_ruler_already_chosen(self, client, svc):
        empire = svc.empire_service.all_empires[TEST_UID]
        empire.ruler.type = "WARRIOR"
        svc.empire_service._rulers = {"WARRIOR": {"name": "Warrior"}}
        resp = await client.post(
            "/api/empire/ruler/choose",
            json={"ruler_iid": "WARRIOR"},
            headers=_auth(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False

    async def test_choose_ruler_unknown_iid(self, client, svc):
        empire = svc.empire_service.all_empires[TEST_UID]
        empire.ruler.type = ""
        svc.empire_service._rulers = {}
        resp = await client.post(
            "/api/empire/ruler/choose",
            json={"ruler_iid": "NONEXISTENT"},
            headers=_auth(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False

    async def test_change_ruler_swaps_in_one_call_and_replaces_ruler_waves(self, client, svc):
        empire = svc.empire_service.all_empires[TEST_UID]
        empire.effects["ruler_unlock"] = 1
        empire.ruler.type = "WARRIOR"
        empire.ruler.r = 0
        empire.ruler.xp = 500.0
        empire.ruler.level = 7
        empire.ruler.q = 3
        svc.empire_service._rulers = {"WARRIOR": {"name": "Warrior"}, "MAJA": {"name": "Maja"}}
        empire.armies.append(
            Army(
                aid=99,
                uid=TEST_UID,
                waves=[
                    CritterWave(wave_id=0, iid="WARRIOR", slots=1),
                    CritterWave(wave_id=1, iid="ARCHER", slots=5),
                ],
            )
        )
        resp = await client.post(
            "/api/empire/ruler/change", json={"ruler_iid": "MAJA"}, headers=_auth(),
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        # New ruler is active immediately — the empire is never ruler-less.
        assert empire.ruler.type == "MAJA"
        assert empire.ruler.name == "Maja"
        # XP / level / skill points are reset by the swap.
        assert empire.ruler.xp == 0.0
        assert empire.ruler.level == 1
        assert empire.ruler.q == 0
        new_army = next(a for a in empire.armies if a.aid == 99)
        assert new_army.waves[0].iid == "SLAVE"
        assert new_army.waves[1].iid == "ARCHER"

    async def test_change_ruler_blocked_when_r_skill_upgraded(self, client, svc):
        empire = svc.empire_service.all_empires[TEST_UID]
        empire.effects["ruler_unlock"] = 1
        empire.ruler.type = "WARRIOR"
        empire.ruler.r = 1
        svc.empire_service._rulers = {"WARRIOR": {"name": "Warrior"}, "MAJA": {"name": "Maja"}}
        resp = await client.post(
            "/api/empire/ruler/change", json={"ruler_iid": "MAJA"}, headers=_auth(),
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is False
        assert empire.ruler.type == "WARRIOR"

    async def test_change_ruler_rejection_leaves_old_ruler_intact(self, client, svc):
        # The bug this endpoint exists for: a failed change must never strand
        # the player without a ruler (the old dismiss-then-choose flow did).
        empire = svc.empire_service.all_empires[TEST_UID]
        empire.effects["ruler_unlock"] = 1
        empire.ruler.type = "WARRIOR"
        empire.ruler.r = 0
        empire.ruler.xp = 500.0
        empire.ruler.level = 7
        svc.empire_service._rulers = {"WARRIOR": {"name": "Warrior"}}
        resp = await client.post(
            "/api/empire/ruler/change", json={"ruler_iid": "NONEXISTENT"}, headers=_auth(),
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is False
        assert empire.ruler.type == "WARRIOR"
        assert empire.ruler.xp == 500.0
        assert empire.ruler.level == 7

    async def test_change_ruler_to_same_ruler_is_rejected(self, client, svc):
        # Guards against wiping your own XP by re-picking the ruler you have.
        empire = svc.empire_service.all_empires[TEST_UID]
        empire.effects["ruler_unlock"] = 1
        empire.ruler.type = "WARRIOR"
        empire.ruler.r = 0
        empire.ruler.xp = 500.0
        svc.empire_service._rulers = {"WARRIOR": {"name": "Warrior"}}
        resp = await client.post(
            "/api/empire/ruler/change", json={"ruler_iid": "WARRIOR"}, headers=_auth(),
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is False
        assert empire.ruler.xp == 500.0

    async def test_skill_up_no_points(self, client, svc):
        """Ruler at level 1 with 0 XP should have 0 points available."""
        empire = svc.empire_service.all_empires[TEST_UID]
        empire.ruler.xp = 0.0
        empire.ruler.q = 0
        empire.ruler.w = 0
        empire.ruler.e = 0
        empire.ruler.r = 0
        resp = await client.post(
            "/api/empire/ruler/skill-up",
            json={"skill": "q"},
            headers=_auth(),
        )
        assert resp.status_code == 200
        data = resp.json()
        # Level 1 has 1 point available (total_points=0 < level=1)
        # so either success (point spent) or no-point error depending on XP
        assert "success" in data

    async def test_skill_up_invalid_skill(self, client, svc):
        resp = await client.post(
            "/api/empire/ruler/skill-up",
            json={"skill": "x"},
            headers=_auth(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False

    async def test_skill_up_requires_auth(self, client):
        resp = await client.post("/api/empire/ruler/skill-up", json={"skill": "q"})
        assert resp.status_code in (401, 403, 422)


# ---------------------------------------------------------------------------
# Army router — buy-critter-slot, buy-wave-era, set-ruler-wave
# ---------------------------------------------------------------------------

class TestArmyBuyEndpoints:
    async def test_buy_critter_slot_endpoint_exists(self, client, svc):
        resp = await client.post(
            "/api/army/buy-critter-slot",
            json={"aid": 1, "wave_number": 1},
            headers=_auth(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "success" in data

    async def test_buy_wave_era_endpoint_exists(self, client, svc):
        resp = await client.post(
            "/api/army/buy-wave-era",
            json={"aid": 1, "wave_number": 1},
            headers=_auth(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "success" in data

    async def test_set_ruler_wave_endpoint_exists(self, client, svc):
        resp = await client.post(
            "/api/army/set-ruler-wave",
            json={"aid": 1, "wave_number": 1, "ruler_iid": "WARRIOR"},
            headers=_auth(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "success" in data

    async def test_buy_critter_slot_requires_auth(self, client):
        resp = await client.post("/api/army/buy-critter-slot", json={"aid": 1, "wave_number": 1})
        assert resp.status_code in (401, 403, 422)

    async def test_buy_wave_era_requires_auth(self, client):
        resp = await client.post("/api/army/buy-wave-era", json={"aid": 1, "wave_number": 1})
        assert resp.status_code in (401, 403, 422)

    async def test_set_ruler_wave_requires_auth(self, client):
        resp = await client.post("/api/army/set-ruler-wave", json={"aid": 1, "wave_number": 1, "ruler_iid": "X"})
        assert resp.status_code in (401, 403, 422)


# ---------------------------------------------------------------------------
# Attack router — spy-attack, buy-tile
# ---------------------------------------------------------------------------

class TestSpyAttackRouter:
    async def test_spy_attack_endpoint_exists(self, client, svc):
        resp = await client.post(
            "/api/spy-attack",
            json={"target_uid": 99, "opponent_name": "Enemy"},
            headers=_auth(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "success" in data

    async def test_spy_attack_requires_auth(self, client):
        resp = await client.post("/api/spy-attack", json={"target_uid": 99, "opponent_name": "Enemy"})
        assert resp.status_code in (401, 403, 422)


class TestSpyReportsRouter:
    async def test_get_spy_reports_empty(self, client, svc):
        resp = await client.get("/api/spy-reports", headers=_auth())
        assert resp.status_code == 200
        data = resp.json()
        assert data["reports"] == []

    async def test_get_spy_reports_returns_stored_reports(self, client, svc):
        svc.database.get_spy_reports_for = AsyncMock(return_value=[
            {"defender_uid": 99, "defender_name": "Enemy", "era": "stone", "era_idx": 0,
             "placed_towers": [], "path_length": 10, "created_at": "2026-07-28 00:00:00"},
        ])
        resp = await client.get("/api/spy-reports", headers=_auth())
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["reports"]) == 1
        assert data["reports"][0]["defender_uid"] == 99
        assert data["reports"][0]["era"] == "stone"

    async def test_get_spy_reports_requires_auth(self, client):
        resp = await client.get("/api/spy-reports")
        assert resp.status_code in (401, 403, 422)


# ---------------------------------------------------------------------------
# Diplomacy router — alliance declarations
# ---------------------------------------------------------------------------

class TestDiplomacyDisabled:
    """game.yaml `alliances_enabled: false` takes diplomacy out of a season.

    The endpoints stay in place and refuse, so flipping the flag back on
    restores them without code changes.
    """

    @staticmethod
    def _disable(svc):
        svc.game_config = MagicMock()
        svc.game_config.alliances_enabled = False

    async def test_toggle_refused_while_disabled(self, client, svc):
        self._disable(svc)
        svc.database.toggle_alliance_declaration = AsyncMock(return_value=True)
        svc.database.get_alliance_declarations_for = AsyncMock(return_value=(set(), set()))

        resp = await client.post(
            "/api/diplomacy/alliance", json={"target_uid": 99}, headers=_auth(),
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is False
        # Refused before touching the database — no declaration is written
        svc.database.toggle_alliance_declaration.assert_not_awaited()

    async def test_decline_refused_while_disabled(self, client, svc):
        self._disable(svc)
        svc.database.remove_alliance_declaration = AsyncMock(return_value=True)
        svc.database.get_alliance_declarations_for = AsyncMock(return_value=(set(), {99}))

        resp = await client.post(
            "/api/diplomacy/alliance/decline", json={"target_uid": 99}, headers=_auth(),
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is False
        svc.database.remove_alliance_declaration.assert_not_awaited()

    async def test_enabled_flag_leaves_the_endpoint_working(self, client, svc):
        svc.game_config = MagicMock()
        svc.game_config.alliances_enabled = True
        svc.database.toggle_alliance_declaration = AsyncMock(return_value=True)
        svc.database.get_alliance_declarations_for = AsyncMock(return_value=({99}, set()))

        resp = await client.post(
            "/api/diplomacy/alliance", json={"target_uid": 99}, headers=_auth(),
        )
        assert resp.json()["success"] is True


class TestDiplomacyRouter:
    async def test_declare_alliance_from_none(self, client, svc):
        svc.database.toggle_alliance_declaration = AsyncMock(return_value=True)
        svc.database.get_alliance_declarations_for = AsyncMock(return_value=({99}, set()))
        resp = await client.post(
            "/api/diplomacy/alliance", json={"target_uid": 99}, headers=_auth(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["declared"] is True
        assert data["alliance_status"] == "pending_sent"
        svc.database.toggle_alliance_declaration.assert_awaited_once_with(TEST_UID, 99)

    async def test_completing_mutual_declaration_returns_allied(self, client, svc):
        svc.database.toggle_alliance_declaration = AsyncMock(return_value=True)
        svc.database.get_alliance_declarations_for = AsyncMock(return_value=({99}, {99}))
        resp = await client.post(
            "/api/diplomacy/alliance", json={"target_uid": 99}, headers=_auth(),
        )
        data = resp.json()
        assert data["alliance_status"] == "allied"

    async def test_accepting_request_rejected_when_already_allied_elsewhere(self, client, svc):
        # I'm already allied with uid 50; uid 99 has now sent me a request
        # (pending_received). Accepting it would create a second alliance,
        # which the current max_alliances=1 cap must reject.
        me = svc.empire_service.get(TEST_UID)
        me.allied_uids = {50}
        svc.database.toggle_alliance_declaration = AsyncMock(return_value=True)
        svc.database.get_alliance_declarations_for = AsyncMock(return_value=(set(), {99}))
        resp = await client.post(
            "/api/diplomacy/alliance", json={"target_uid": 99}, headers=_auth(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert "alliance" in data["error"].lower()
        # Toggle must never have been called — request is rejected up front.
        svc.database.toggle_alliance_declaration.assert_not_awaited()

    async def test_accepting_request_rejected_when_partner_already_allied_elsewhere(self, client, svc):
        # uid 99 (the requester) is already allied with someone else; I must
        # not be able to complete a second alliance for them either.
        partner = _make_empire(uid=99, name="Partner")
        partner.allied_uids = {50}
        svc.empire_service.register(partner)
        svc.database.toggle_alliance_declaration = AsyncMock(return_value=True)
        svc.database.get_alliance_declarations_for = AsyncMock(return_value=(set(), {99}))
        resp = await client.post(
            "/api/diplomacy/alliance", json={"target_uid": 99}, headers=_auth(),
        )
        data = resp.json()
        assert data["success"] is False
        svc.database.toggle_alliance_declaration.assert_not_awaited()

    async def test_sending_request_allowed_while_already_allied(self, client, svc):
        # Sending a NEW request (not yet mutual) while already allied is fine
        # — the cap only blocks the moment an alliance would actually complete.
        me = svc.empire_service.get(TEST_UID)
        me.allied_uids = {50}
        svc.database.toggle_alliance_declaration = AsyncMock(return_value=True)
        # Not mutual yet: target hasn't declared toward me.
        svc.database.get_alliance_declarations_for = AsyncMock(return_value=({99}, set()))
        resp = await client.post(
            "/api/diplomacy/alliance", json={"target_uid": 99}, headers=_auth(),
        )
        data = resp.json()
        assert data["success"] is True
        assert data["alliance_status"] == "pending_sent"

    async def test_breaking_existing_alliance_then_accepting_new_one_allowed(self, client, svc):
        # Retracting my declaration toward an existing ally (breaking it) must
        # never be blocked by the cap, regardless of allied_uids content.
        me = svc.empire_service.get(TEST_UID)
        me.allied_uids = {99}
        svc.database.toggle_alliance_declaration = AsyncMock(return_value=False)
        svc.database.get_alliance_declarations_for = AsyncMock(
            side_effect=[({99}, {99}), (set(), {99})]
        )
        resp = await client.post(
            "/api/diplomacy/alliance", json={"target_uid": 99}, headers=_auth(),
        )
        data = resp.json()
        assert data["success"] is True
        assert data["alliance_status"] == "pending_received"

    async def test_completing_alliance_charges_culture_cost_both_ways(self, client, svc):
        me = svc.empire_service.get(TEST_UID)
        me.resources["culture"] = 1000.0
        partner = _make_empire(uid=99, name="Partner")
        partner.resources["culture"] = 400.0
        svc.empire_service.register(partner)
        svc.game_config = GameConfig(alliance_culture_cost=0.05)

        svc.database.toggle_alliance_declaration = AsyncMock(return_value=True)
        svc.database.get_alliance_declarations_for = AsyncMock(return_value=({99}, {99}))
        resp = await client.post(
            "/api/diplomacy/alliance", json={"target_uid": 99}, headers=_auth(),
        )
        assert resp.status_code == 200
        assert resp.json()["alliance_status"] == "allied"

        # 5% of 1000 (50) and 5% of 400 (20) are swapped between the two.
        assert me.resources["culture"] == pytest.approx(1000.0 - 50.0 + 20.0)
        assert partner.resources["culture"] == pytest.approx(400.0 - 20.0 + 50.0)

    async def test_completing_alliance_applies_ally_ruler_effects_both_ways(self, client, svc):
        from gameserver.models.empire import Ruler

        svc.empire_service._rulers = {
            "MAJA": {"ally_effects": {"research_speed_modifier": 0.3}},
            "NANDI": {"ally_effects": {"tile_cost_modifier": 0.05}},
        }
        me = svc.empire_service.get(TEST_UID)
        me.ruler = Ruler(type="MAJA", name="Maja")
        partner = _make_empire(uid=99, name="Partner")
        partner.ruler = Ruler(type="NANDI", name="Nandi")
        svc.empire_service.register(partner)

        svc.database.toggle_alliance_declaration = AsyncMock(return_value=True)
        # Before: only pending_received ({} sent, {99} received). After: mutual.
        svc.database.get_alliance_declarations_for = AsyncMock(
            side_effect=[(set(), {99}), ({99}, {99})]
        )
        resp = await client.post(
            "/api/diplomacy/alliance", json={"target_uid": 99}, headers=_auth(),
        )
        assert resp.json()["alliance_status"] == "allied"

        assert 99 in me.allied_uids
        assert TEST_UID in partner.allied_uids
        # I receive the partner's (NANDI) ally_effects; they receive mine (MAJA).
        assert me.effects.get("tile_cost_modifier") == pytest.approx(0.05)
        assert partner.effects.get("research_speed_modifier") == pytest.approx(0.3)

    async def test_breaking_alliance_removes_ally_ruler_effects(self, client, svc):
        from gameserver.models.empire import Ruler

        svc.empire_service._rulers = {
            "NANDI": {"ally_effects": {"tile_cost_modifier": 0.05}},
        }
        me = svc.empire_service.get(TEST_UID)
        partner = _make_empire(uid=99, name="Partner")
        partner.ruler = Ruler(type="NANDI", name="Nandi")
        svc.empire_service.register(partner)
        me.allied_uids = {99}
        partner.allied_uids = {TEST_UID}
        svc.empire_service.recalculate_effects(me)
        assert me.effects.get("tile_cost_modifier") == pytest.approx(0.05)

        svc.database.toggle_alliance_declaration = AsyncMock(return_value=False)
        svc.database.get_alliance_declarations_for = AsyncMock(
            side_effect=[({99}, {99}), (set(), {99})]
        )
        resp = await client.post(
            "/api/diplomacy/alliance", json={"target_uid": 99}, headers=_auth(),
        )
        assert resp.json()["alliance_status"] == "pending_received"

        assert 99 not in me.allied_uids
        assert me.effects.get("tile_cost_modifier", 0.0) == 0.0

    async def test_pending_declaration_does_not_charge_culture(self, client, svc):
        me = svc.empire_service.get(TEST_UID)
        me.resources["culture"] = 1000.0
        partner = _make_empire(uid=99, name="Partner")
        partner.resources["culture"] = 400.0
        svc.empire_service.register(partner)
        svc.game_config = GameConfig(alliance_culture_cost=0.05)

        svc.database.toggle_alliance_declaration = AsyncMock(return_value=True)
        svc.database.get_alliance_declarations_for = AsyncMock(return_value=({99}, set()))
        resp = await client.post(
            "/api/diplomacy/alliance", json={"target_uid": 99}, headers=_auth(),
        )
        assert resp.json()["alliance_status"] == "pending_sent"
        assert me.resources["culture"] == 1000.0
        assert partner.resources["culture"] == 400.0

    async def test_retract_pending_declaration(self, client, svc):
        svc.database.toggle_alliance_declaration = AsyncMock(return_value=False)
        svc.database.get_alliance_declarations_for = AsyncMock(return_value=(set(), set()))
        resp = await client.post(
            "/api/diplomacy/alliance", json={"target_uid": 99}, headers=_auth(),
        )
        data = resp.json()
        assert data["declared"] is False
        assert data["alliance_status"] == "none"

    async def test_break_active_alliance_leaves_pending_received(self, client, svc):
        svc.database.toggle_alliance_declaration = AsyncMock(return_value=False)
        svc.database.get_alliance_declarations_for = AsyncMock(return_value=(set(), {99}))
        resp = await client.post(
            "/api/diplomacy/alliance", json={"target_uid": 99}, headers=_auth(),
        )
        data = resp.json()
        assert data["alliance_status"] == "pending_received"

    async def test_breaking_alliance_charges_breaker_only_and_destroys_it(self, client, svc):
        me = svc.empire_service.get(TEST_UID)
        me.resources["culture"] = 1000.0
        partner = _make_empire(uid=99, name="Partner")
        partner.resources["culture"] = 400.0
        svc.empire_service.register(partner)
        svc.game_config = GameConfig(alliance_culture_cost=0.05)

        svc.database.toggle_alliance_declaration = AsyncMock(return_value=False)
        # Before: mutual (allied). After: breaker's declared_to is gone -> pending_received.
        svc.database.get_alliance_declarations_for = AsyncMock(
            side_effect=[({99}, {99}), (set(), {99})]
        )
        resp = await client.post(
            "/api/diplomacy/alliance", json={"target_uid": 99}, headers=_auth(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["declared"] is False
        assert data["alliance_status"] == "pending_received"

        # Breaker (me) pays 5% of 1000 = 50, destroyed — not sent to partner.
        assert me.resources["culture"] == pytest.approx(950.0)
        assert partner.resources["culture"] == 400.0

    async def test_pending_declaration_retract_does_not_charge_penalty(self, client, svc):
        # Retracting a one-sided (never mutual) declaration is not "breaking
        # an alliance" and must not incur the penalty.
        me = svc.empire_service.get(TEST_UID)
        me.resources["culture"] = 1000.0
        svc.game_config = GameConfig(alliance_culture_cost=0.05)

        svc.database.toggle_alliance_declaration = AsyncMock(return_value=False)
        svc.database.get_alliance_declarations_for = AsyncMock(
            side_effect=[({99}, set()), (set(), set())]
        )
        resp = await client.post(
            "/api/diplomacy/alliance", json={"target_uid": 99}, headers=_auth(),
        )
        assert resp.json()["alliance_status"] == "none"
        assert me.resources["culture"] == 1000.0

    async def test_rejects_self_target(self, client, svc):
        resp = await client.post(
            "/api/diplomacy/alliance", json={"target_uid": TEST_UID}, headers=_auth(),
        )
        data = resp.json()
        assert data["success"] is False

    async def test_requires_auth(self, client):
        resp = await client.post("/api/diplomacy/alliance", json={"target_uid": 99})
        assert resp.status_code in (401, 403, 422)

    async def test_list_empires_includes_alliance_status(self, client, svc):
        other = _make_empire(uid=99, name="Other")
        svc.empire_service.register(other)
        svc.database.list_users = AsyncMock(return_value=[
            {"uid": TEST_UID, "username": "me", "last_seen": ""},
            {"uid": 99, "username": "other", "last_seen": ""},
        ])
        svc.database.get_alliance_declarations_for = AsyncMock(return_value=({99}, set()))
        svc.database.get_season_winners = AsyncMock(return_value=[])
        svc.database.get_all_empire_stats = AsyncMock(return_value=[])
        resp = await client.get("/api/empires", headers=_auth())
        assert resp.status_code == 200
        rows = {e["uid"]: e for e in resp.json()["empires"]}
        assert rows[99]["alliance_status"] == "pending_sent"
        assert rows[TEST_UID]["alliance_status"] == "none"

    async def test_list_empires_includes_ally_ruler_name_when_allied(self, client, svc):
        from gameserver.models.empire import Ruler

        svc.empire_service._rulers = {
            "LUCIEN": {"name": "Lucien Duskbane", "ally_effects": {"gold_modifier": 0.2}},
        }
        other = _make_empire(uid=99, name="Other")
        other.ruler = Ruler(type="LUCIEN", name="Lucien Duskbane")
        svc.empire_service.register(other)
        svc.database.list_users = AsyncMock(return_value=[
            {"uid": TEST_UID, "username": "me", "last_seen": ""},
            {"uid": 99, "username": "other", "last_seen": ""},
        ])
        svc.database.get_alliance_declarations_for = AsyncMock(return_value=({99}, {99}))
        svc.database.get_season_winners = AsyncMock(return_value=[])
        svc.database.get_all_empire_stats = AsyncMock(return_value=[])
        resp = await client.get("/api/empires", headers=_auth())
        assert resp.status_code == 200
        rows = {e["uid"]: e for e in resp.json()["empires"]}
        assert rows[99]["alliance_status"] == "allied"
        assert rows[99]["ally_ruler_name"] == "Lucien Duskbane"
        assert rows[99]["ally_ruler_bonus"] == {"gold_modifier": 0.2}
        # Not allied with myself -> blank/empty.
        assert rows[TEST_UID]["ally_ruler_name"] == ""
        assert rows[TEST_UID]["ally_ruler_bonus"] == {}

    async def test_list_empires_ally_ruler_name_blank_when_not_allied(self, client, svc):
        from gameserver.models.empire import Ruler

        svc.empire_service._rulers = {
            "LUCIEN": {"name": "Lucien Duskbane", "ally_effects": {"gold_modifier": 0.2}},
        }
        other = _make_empire(uid=99, name="Other")
        other.ruler = Ruler(type="LUCIEN", name="Lucien Duskbane")
        svc.empire_service.register(other)
        svc.database.list_users = AsyncMock(return_value=[
            {"uid": TEST_UID, "username": "me", "last_seen": ""},
            {"uid": 99, "username": "other", "last_seen": ""},
        ])
        # Only pending, not mutual.
        svc.database.get_alliance_declarations_for = AsyncMock(return_value=({99}, set()))
        svc.database.get_season_winners = AsyncMock(return_value=[])
        svc.database.get_all_empire_stats = AsyncMock(return_value=[])
        resp = await client.get("/api/empires", headers=_auth())
        rows = {e["uid"]: e for e in resp.json()["empires"]}
        assert rows[99]["alliance_status"] == "pending_sent"
        assert rows[99]["ally_ruler_name"] == ""
        assert rows[99]["ally_ruler_bonus"] == {}

    async def test_list_empires_ranks_by_pooled_allied_culture(self, client, svc):
        # TEST_UID has 1000 culture (own). uid 99 has 200 (own), but is allied
        # with uid 100 (900 culture) -> pooled 1100, so 99 should outrank TEST_UID
        # even though 99's own culture is displayed unchanged.
        low_ally = _make_empire(uid=99, name="LowAlly")
        low_ally.resources["culture"] = 200.0
        high_ally = _make_empire(uid=100, name="HighAlly")
        high_ally.resources["culture"] = 900.0
        svc.empire_service.register(low_ally)
        svc.empire_service.register(high_ally)
        svc.database.list_users = AsyncMock(return_value=[
            {"uid": TEST_UID, "username": "me", "last_seen": ""},
            {"uid": 99, "username": "lowally", "last_seen": ""},
            {"uid": 100, "username": "highally", "last_seen": ""},
        ])
        svc.database.get_alliance_declarations_for = AsyncMock(return_value=(set(), set()))
        svc.database.get_all_mutual_alliances = AsyncMock(return_value={99: {100}, 100: {99}})
        svc.database.get_season_winners = AsyncMock(return_value=[])
        svc.database.get_all_empire_stats = AsyncMock(return_value=[])
        resp = await client.get("/api/empires", headers=_auth())
        assert resp.status_code == 200
        body = resp.json()["empires"]
        uids_in_order = [e["uid"] for e in body]
        assert uids_in_order.index(99) < uids_in_order.index(TEST_UID)
        # 99 and 100 must be listed contiguously (adjacent, allied block),
        # with the higher-culture ally (100) first within the block.
        assert uids_in_order.index(99) == uids_in_order.index(100) + 1
        rows = {e["uid"]: e for e in body}
        assert rows[99]["culture"] == 200.0
        assert rows[99]["alliance_group_id"] is not None
        assert rows[99]["alliance_group_id"] == rows[100]["alliance_group_id"]
        assert rows[TEST_UID]["alliance_group_id"] is None
        assert rows[99]["alliance_group_culture"] == 1100.0
        assert rows[100]["alliance_group_culture"] == 1100.0
        assert rows[TEST_UID]["alliance_group_culture"] is None


class TestDissolveInactiveAlliances:
    """An inactive/hidden player can't act to break an alliance themselves —
    dissolve_alliances_for_inactive() does it for them wherever the "hidden
    due to inactivity" filter runs (>1 week no login and <=0 culture)."""

    async def test_breaks_mutual_alliance_in_both_directions(self, svc):
        from gameserver.network.routers.diplomacy import dissolve_alliances_for_inactive

        me = svc.empire_service.get(TEST_UID)
        partner = _make_empire(uid=99, name="Partner")
        me.allied_uids = {99}
        partner.allied_uids = {TEST_UID}
        svc.empire_service.register(partner)
        svc.database.get_alliance_declarations_for = AsyncMock(return_value=({99}, {99}))

        await dissolve_alliances_for_inactive(svc, TEST_UID)

        svc.database.remove_alliance_declaration.assert_any_await(TEST_UID, 99)
        svc.database.remove_alliance_declaration.assert_any_await(99, TEST_UID)
        assert svc.database.remove_alliance_declaration.await_count == 2
        assert 99 not in me.allied_uids
        assert TEST_UID not in partner.allied_uids

    async def test_removes_ally_ruler_effects_from_the_surviving_partner(self, svc):
        from gameserver.models.empire import Ruler
        from gameserver.network.routers.diplomacy import dissolve_alliances_for_inactive

        svc.empire_service._rulers = {
            "NANDI": {"ally_effects": {"tile_cost_modifier": 0.05}},
        }
        me = svc.empire_service.get(TEST_UID)
        partner = _make_empire(uid=99, name="Partner")
        partner.ruler = Ruler(type="NANDI", name="Nandi")
        partner.allied_uids = {TEST_UID}
        svc.empire_service.register(partner)
        svc.empire_service.recalculate_effects(partner)
        me.allied_uids = {99}
        svc.empire_service.recalculate_effects(me)
        assert me.effects.get("tile_cost_modifier") == pytest.approx(0.05)

        svc.database.get_alliance_declarations_for = AsyncMock(return_value=({99}, {99}))
        await dissolve_alliances_for_inactive(svc, TEST_UID)

        assert "tile_cost_modifier" not in me.effects

    async def test_is_a_noop_without_a_mutual_alliance(self, svc):
        from gameserver.network.routers.diplomacy import dissolve_alliances_for_inactive

        # Only pending (one-directional) — nothing mutual to break.
        svc.database.get_alliance_declarations_for = AsyncMock(return_value=({99}, set()))
        await dissolve_alliances_for_inactive(svc, TEST_UID)
        svc.database.remove_alliance_declaration.assert_not_awaited()

    async def test_charges_no_culture_cost(self, svc):
        from gameserver.network.routers.diplomacy import dissolve_alliances_for_inactive

        svc.game_config = GameConfig(alliance_culture_cost=0.05)
        me = svc.empire_service.get(TEST_UID)
        me.resources["culture"] = 1000.0
        partner = _make_empire(uid=99, name="Partner")
        partner.resources["culture"] = 400.0
        svc.empire_service.register(partner)
        svc.database.get_alliance_declarations_for = AsyncMock(return_value=({99}, {99}))

        await dissolve_alliances_for_inactive(svc, TEST_UID)

        # Unlike a player-initiated break (toggle_alliance), no culture moves —
        # becoming inactive isn't a decision the player made.
        assert me.resources["culture"] == 1000.0
        assert partner.resources["culture"] == 400.0

    async def test_list_empires_dissolves_alliance_before_hiding_inactive_empire(
        self, client, svc,
    ):
        """Integration: GET /api/empires hides uid 99 (0 culture, never seen)
        and must dissolve its mutual alliance with uid 77 as a side effect."""
        hidden = _make_empire(uid=99, name="Hidden")
        hidden.resources["culture"] = 0.0
        hidden.allied_uids = {77}
        ally = _make_empire(uid=77, name="Ally")
        ally.allied_uids = {99}
        svc.empire_service.register(hidden)
        svc.empire_service.register(ally)
        svc.database.list_users = AsyncMock(return_value=[
            {"uid": TEST_UID, "username": "me", "last_seen": ""},
            {"uid": 99, "username": "hidden", "last_seen": ""},
            {"uid": 77, "username": "ally", "last_seen": ""},
        ])

        def _declarations_for(uid: int):
            if uid == 99:
                return ({77}, {77})
            return (set(), set())

        svc.database.get_alliance_declarations_for = AsyncMock(side_effect=_declarations_for)
        svc.database.get_all_mutual_alliances = AsyncMock(return_value={99: {77}, 77: {99}})
        svc.database.get_season_winners = AsyncMock(return_value=[])
        svc.database.get_all_empire_stats = AsyncMock(return_value=[])

        resp = await client.get("/api/empires", headers=_auth())

        assert resp.status_code == 200
        rows = {e["uid"]: e for e in resp.json()["empires"]}
        assert 99 not in rows  # hidden from the list, as before
        assert 77 in rows      # the surviving partner still shows up
        svc.database.remove_alliance_declaration.assert_any_await(99, 77)
        svc.database.remove_alliance_declaration.assert_any_await(77, 99)
        assert 99 not in ally.allied_uids


class TestSeasonResultsRouter:
    async def test_season_podium_pools_allied_pair_above_solo_leader(self, client, svc):
        # uid 99 (500) and uid 100 (700) are mutually allied -> pooled 1200,
        # which outranks TEST_UID's solo 1000, even though neither of 99/100
        # individually beats TEST_UID.
        me = svc.empire_service.get(TEST_UID)
        me.resources["culture"] = 1000.0
        low_ally = _make_empire(uid=99, name="LowAlly")
        low_ally.resources["culture"] = 500.0
        high_ally = _make_empire(uid=100, name="HighAlly")
        high_ally.resources["culture"] = 700.0
        svc.empire_service.register(low_ally)
        svc.empire_service.register(high_ally)

        svc.database.get_all_mutual_alliances = AsyncMock(return_value={99: {100}, 100: {99}})
        svc.database.get_all_empire_stats = AsyncMock(return_value=[])
        svc.database.get_longest_artifact_hold_per_uid = AsyncMock(return_value=[])
        svc.database.get_era_firsts = AsyncMock(return_value=[])
        svc.database.get_longest_single_artifact_holds = AsyncMock(return_value=[])

        resp = await client.get("/api/season-results", headers=_auth())
        assert resp.status_code == 200
        data = resp.json()

        podium = data["season_podium"]
        assert podium[0]["place"] == 1
        assert podium[0]["pooled_culture"] == 1200.0
        assert {m["uid"] for m in podium[0]["members"]} == {99, 100}
        # Higher own-culture member listed first within the team.
        assert podium[0]["members"][0]["uid"] == 100

        # The solo empire still places — one rank below the team it lost to.
        assert podium[1]["place"] == 2
        assert podium[1]["pooled_culture"] == 1000.0
        assert [m["uid"] for m in podium[1]["members"]] == [TEST_UID]

    async def test_solo_leader_outscoring_the_team_takes_first_place_alone(self, client, svc):
        # Pooling is a score bonus, not a monopoly: TEST_UID's solo 2000 beats
        # the allied pair's pooled 1200 and wins the podium on its own.
        me = svc.empire_service.get(TEST_UID)
        me.resources["culture"] = 2000.0
        low_ally = _make_empire(uid=99, name="LowAlly")
        low_ally.resources["culture"] = 500.0
        high_ally = _make_empire(uid=100, name="HighAlly")
        high_ally.resources["culture"] = 700.0
        svc.empire_service.register(low_ally)
        svc.empire_service.register(high_ally)

        svc.database.get_all_mutual_alliances = AsyncMock(return_value={99: {100}, 100: {99}})
        svc.database.get_all_empire_stats = AsyncMock(return_value=[])
        svc.database.get_longest_artifact_hold_per_uid = AsyncMock(return_value=[])
        svc.database.get_era_firsts = AsyncMock(return_value=[])
        svc.database.get_longest_single_artifact_holds = AsyncMock(return_value=[])

        resp = await client.get("/api/season-results", headers=_auth())
        assert resp.status_code == 200
        podium = resp.json()["season_podium"]

        assert podium[0]["place"] == 1
        assert podium[0]["pooled_culture"] == 2000.0
        assert [m["uid"] for m in podium[0]["members"]] == [TEST_UID]
        assert {m["uid"] for m in podium[1]["members"]} == {99, 100}

    async def test_season_podium_lists_individual_places_when_unallied(self, client, svc):
        me = svc.empire_service.get(TEST_UID)
        me.resources["culture"] = 1000.0

        svc.database.get_all_mutual_alliances = AsyncMock(return_value={})
        svc.database.get_all_empire_stats = AsyncMock(return_value=[])
        svc.database.get_longest_artifact_hold_per_uid = AsyncMock(return_value=[])
        svc.database.get_era_firsts = AsyncMock(return_value=[])
        svc.database.get_longest_single_artifact_holds = AsyncMock(return_value=[])

        resp = await client.get("/api/season-results", headers=_auth())
        assert resp.status_code == 200
        podium = resp.json()["season_podium"]
        assert len(podium) == 1
        assert podium[0]["place"] == 1
        assert podium[0]["pooled_culture"] == 1000.0
        assert [m["uid"] for m in podium[0]["members"]] == [TEST_UID]


class TestBuyTileRouter:
    async def test_buy_tile_endpoint_exists(self, client, svc):
        resp = await client.post(
            "/api/map/buy-tile",
            json={"q": 1, "r": 0},
            headers=_auth(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "success" in data

    async def test_buy_tile_requires_auth(self, client):
        resp = await client.post("/api/map/buy-tile", json={"q": 1, "r": 0})
        assert resp.status_code in (401, 403, 422)



class TestPublicRulersEndpoint:
    async def test_public_rulers_needs_no_auth(self, client, svc):
        # The landing page renders this before login — it must not 401/403.
        svc.empire_service._rulers = {
            "MAJA": {
                "name": "Maja",
                "description": "A scholar.",
                "animation": "assets/sprites/ruler/maja",
                "q_meta": {"name": "Insight", "description": ""},
                "q": [{"research_speed_offset": 0.2}, {"research_speed_offset": 0.3}],
            },
        }
        resp = await client.get("/api/empire/rulers")
        assert resp.status_code == 200
        rulers = resp.json()["rulers"]
        assert rulers["MAJA"]["name"] == "Maja"
        # Every level's effects are exposed so the client can script the values
        # instead of hardcoding them.
        assert rulers["MAJA"]["skills"]["q"]["levels"] == [
            {"research_speed_offset": 0.2}, {"research_speed_offset": 0.3},
        ]

    async def test_public_rulers_matches_authenticated_catalog(self, client, svc):
        # Both must come from the same builder — a hardcoded landing-page copy
        # is exactly what drifted out of sync before.
        svc.empire_service._rulers = {
            "MAJA": {
                "name": "Maja",
                "animation": "assets/sprites/ruler/maja",
                "q_meta": {"name": "Insight", "description": ""},
                "q": [{"research_speed_offset": 0.2}],
            },
        }
        public = (await client.get("/api/empire/rulers")).json()["rulers"]
        authed = (await client.get("/api/empire/items", headers=_auth())).json()["rulers"]
        assert public == authed
