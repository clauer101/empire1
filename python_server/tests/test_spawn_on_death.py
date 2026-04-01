"""Tests for the spawn_on_death mechanic.

When a critter dies and has spawn_on_death: {IID: count}, the battle service
must spawn `count` new critters of type IID at slightly behind the dead critter's
path position.
"""

import types
import pytest

from gameserver.engine.battle_service import BattleService
from gameserver.models.battle import BattleState
from gameserver.models.critter import Critter
from gameserver.models.hex import HexCoord
from gameserver.models.shot import Shot


# ── Helpers ──────────────────────────────────────────────────────────────────


def _long_path(n: int = 20) -> list[HexCoord]:
    return [HexCoord(i, 0) for i in range(n)]


def _mock_item(iid: str, health=5.0, speed=0.2, armour=0.0, scale=1.0,
               value=3.0, critter_damage=1.0, spawn_on_death=None):
    return types.SimpleNamespace(
        iid=iid,
        health=health,
        speed=speed,
        armour=armour,
        scale=scale,
        value=value,
        critter_damage=critter_damage,
        spawn_on_death=spawn_on_death or {},
    )


def _critter(path_progress=0.5, health=10.0, spawn_on_death=None, cid=1) -> Critter:
    return Critter(
        cid=cid,
        iid="CART",
        health=health,
        max_health=health,
        speed=0.2,
        path=_long_path(),
        path_progress=path_progress,
        spawn_on_death=spawn_on_death or {},
    )


def _battle(*critters: Critter, **kwargs) -> BattleState:
    return BattleState(
        bid=1, defender=None, attacker=None,
        critters={c.cid: c for c in critters},
        **kwargs,
    )


def _svc_with_items(**items_by_iid) -> BattleService:
    """Return a BattleService with a mock item registry."""
    svc = BattleService()
    svc._items_by_iid = items_by_iid
    return svc


# ── Basic spawn count ─────────────────────────────────────────────────────────


class TestSpawnOnDeathCount:
    def test_no_spawn_when_empty(self):
        """Critter with no spawn_on_death leaves critters dict unchanged (minus itself)."""
        svc = _svc_with_items()
        c = _critter(spawn_on_death={})
        b = _battle(c)
        svc._critter_died(b, c)
        assert len(b.critters) == 0

    def test_single_type_spawns_correct_count(self):
        """spawn_on_death: {SLAVE: 3} spawns exactly 3 critters."""
        svc = _svc_with_items(SLAVE=_mock_item("SLAVE"))
        c = _critter(spawn_on_death={"SLAVE": 3})
        b = _battle(c)
        svc._critter_died(b, c)
        assert len(b.critters) == 3
        assert all(ch.iid == "SLAVE" for ch in b.critters.values())

    def test_multiple_types_spawn_all(self):
        """spawn_on_death: {SLAVE: 2, SCOUT: 1} spawns 3 critters total."""
        svc = _svc_with_items(
            SLAVE=_mock_item("SLAVE"),
            SCOUT=_mock_item("SCOUT", health=3.0, speed=0.4),
        )
        c = _critter(spawn_on_death={"SLAVE": 2, "SCOUT": 1})
        b = _battle(c)
        svc._critter_died(b, c)
        assert len(b.critters) == 3
        iids = {ch.iid for ch in b.critters.values()}
        assert "SLAVE" in iids
        assert "SCOUT" in iids

    def test_one_spawn(self):
        svc = _svc_with_items(SLAVE=_mock_item("SLAVE"))
        c = _critter(spawn_on_death={"SLAVE": 1})
        b = _battle(c)
        svc._critter_died(b, c)
        assert len(b.critters) == 1


# ── Path progress placement ───────────────────────────────────────────────────


class TestSpawnPosition:
    def test_spawn_progress_behind_dead(self):
        """All spawned critters have path_progress <= dead critter's progress."""
        svc = _svc_with_items(SLAVE=_mock_item("SLAVE"))
        original_progress = 0.6
        c = _critter(path_progress=original_progress, spawn_on_death={"SLAVE": 10})
        b = _battle(c)
        svc._critter_died(b, c)
        for child in b.critters.values():
            assert child.path_progress <= original_progress

    def test_spawn_progress_not_negative(self):
        """Spawned critters never have negative path_progress."""
        svc = _svc_with_items(SLAVE=_mock_item("SLAVE"))
        c = _critter(path_progress=0.0, spawn_on_death={"SLAVE": 10})
        b = _battle(c)
        svc._critter_died(b, c)
        for child in b.critters.values():
            assert child.path_progress >= 0.0

    def test_spawn_progress_evenly_spaced(self):
        """With multiple spawns, critters are evenly spaced within ~1 hex tile."""
        svc = _svc_with_items(SLAVE=_mock_item("SLAVE"))
        c = _critter(path_progress=0.5, spawn_on_death={"SLAVE": 5})
        b = _battle(c)
        svc._critter_died(b, c)
        progresses = sorted([ch.path_progress for ch in b.critters.values()], reverse=True)
        # path has 20 nodes → 19 segments, one_tile = 1/19, spread = 1.2/19
        path_len = 19
        spacing = (1.2 / path_len) / 5
        expected = [0.5 - spacing * (i + 1) for i in range(5)]
        expected.sort(reverse=True)
        for actual, exp in zip(progresses, expected):
            assert actual == pytest.approx(exp, abs=1e-9)

    def test_spawn_clamped_at_zero_on_early_path(self):
        """If dead critter is very early on path, children clamp to 0."""
        svc = _svc_with_items(SLAVE=_mock_item("SLAVE"))
        # progress=0.001, so all spawns go negative → clamp to 0
        c = _critter(path_progress=0.001, spawn_on_death={"SLAVE": 5})
        b = _battle(c)
        svc._critter_died(b, c)
        progresses = [ch.path_progress for ch in b.critters.values()]
        assert any(p == pytest.approx(0.0) for p in progresses)

    def test_fixed_spawn_spacing(self):
        """Spawned critters are evenly spaced within ~1 hex tile behind parent."""
        svc = _svc_with_items(SLAVE=_mock_item("SLAVE"))
        progress = 0.5
        c = _critter(path_progress=progress, spawn_on_death={"SLAVE": 3})
        b = _battle(c)
        svc._critter_died(b, c)
        progresses = sorted([ch.path_progress for ch in b.critters.values()], reverse=True)
        path_len = 19  # _long_path(20)
        spacing = (1.2 / path_len) / 3
        assert progresses[0] == pytest.approx(progress - spacing * 1, abs=1e-9)
        assert progresses[1] == pytest.approx(progress - spacing * 2, abs=1e-9)
        assert progresses[2] == pytest.approx(progress - spacing * 3, abs=1e-9)

    def test_spacing_scales_to_one_hex_tile(self):
        """Total spread covers ~0.8 of a hex tile regardless of path length."""
        svc = _svc_with_items(SLAVE=_mock_item("SLAVE"))
        # Short path: 5 nodes → 4 segments → one_tile = 0.25
        short_path = _long_path(5)
        c1 = Critter(cid=1, iid="CART", health=5.0, max_health=5.0, speed=0.2,
                     path=short_path, path_progress=0.9, spawn_on_death={"SLAVE": 2})
        b1 = _battle(c1)
        svc._critter_died(b1, c1)
        progresses1 = sorted([ch.path_progress for ch in b1.critters.values()], reverse=True)

        # Long path: 50 nodes → 49 segments → one_tile ≈ 0.0204
        long_path = _long_path(50)
        c2 = Critter(cid=10, iid="CART", health=5.0, max_health=5.0, speed=0.2,
                     path=long_path, path_progress=0.5, spawn_on_death={"SLAVE": 2})
        b2 = _battle(c2)
        svc._critter_died(b2, c2)
        progresses2 = sorted([ch.path_progress for ch in b2.critters.values()], reverse=True)

        # Total spread should be ~1.2 of one hex tile for each path
        spread1 = c1.path_progress - progresses1[-1]
        spread2 = c2.path_progress - progresses2[-1]
        expected_spread1 = 1.2 * (1.0 / 4)   # 0.3
        expected_spread2 = 1.2 * (1.0 / 49)
        assert spread1 == pytest.approx(expected_spread1, abs=1e-9)
        assert spread2 == pytest.approx(expected_spread2, abs=1e-9)


# ── Stat inheritance ──────────────────────────────────────────────────────────


class TestSpawnStats:
    def test_spawned_critter_has_correct_health(self):
        svc = _svc_with_items(SLAVE=_mock_item("SLAVE", health=7.0))
        c = _critter(spawn_on_death={"SLAVE": 1})
        b = _battle(c)
        svc._critter_died(b, c)
        child = next(iter(b.critters.values()))
        assert child.health == pytest.approx(7.0)
        assert child.max_health == pytest.approx(7.0)

    def test_spawned_critter_has_correct_speed(self):
        svc = _svc_with_items(SLAVE=_mock_item("SLAVE", speed=0.35))
        c = _critter(spawn_on_death={"SLAVE": 1})
        b = _battle(c)
        svc._critter_died(b, c)
        child = next(iter(b.critters.values()))
        assert child.speed == pytest.approx(0.35)

    def test_spawned_critter_inherits_path(self):
        """Spawned critter shares the same path as the dead critter."""
        svc = _svc_with_items(SLAVE=_mock_item("SLAVE"))
        path = _long_path(15)
        c = Critter(cid=1, iid="CART", health=5.0, max_health=5.0, speed=0.2,
                    path=path, path_progress=0.5, spawn_on_death={"SLAVE": 1})
        b = _battle(c)
        svc._critter_died(b, c)
        child = next(iter(b.critters.values()))
        assert child.path is path

    def test_spawned_critter_has_unique_cid(self):
        """Each spawned critter gets a unique CID, different from others."""
        svc = _svc_with_items(SLAVE=_mock_item("SLAVE"))
        c = _critter(spawn_on_death={"SLAVE": 5})
        b = _battle(c)
        svc._critter_died(b, c)
        cids = [ch.cid for ch in b.critters.values()]
        assert len(cids) == len(set(cids))  # all unique

    def test_spawned_critter_unknown_item_uses_defaults(self):
        """If spawn iid not in item registry, critter still spawns with fallback stats."""
        svc = _svc_with_items()  # empty registry
        c = _critter(spawn_on_death={"UNKNOWN": 2})
        b = _battle(c)
        svc._critter_died(b, c)
        assert len(b.critters) == 2
        for child in b.critters.values():
            assert child.health > 0


# ── Via shot → damage pipeline ────────────────────────────────────────────────


class TestSpawnOnDeathViaShot:
    def test_killing_shot_triggers_spawn(self):
        """A shot that kills a carrier critter causes children to appear."""
        svc = _svc_with_items(SLAVE=_mock_item("SLAVE"))
        path = _long_path()
        carrier = Critter(
            cid=10, iid="CART", health=5.0, max_health=5.0, speed=0.2,
            path=path, path_progress=0.4,
            spawn_on_death={"SLAVE": 3},
        )
        shot = Shot(
            damage=10.0,   # More than carrier health — lethal
            target_cid=carrier.cid,
            source_sid=1,
            flight_remaining_ms=1.0,
            origin=HexCoord(0, 0),
        )
        b = _battle(carrier, pending_shots=[shot])
        svc._step_shots(b, 50.0)    # Shot arrives, health goes to -5
        svc._step_critters(b, 1.0)  # Death & spawn handling

        # Carrier removed, 3 SLAVE critters present
        assert carrier.cid not in b.critters
        assert len(b.critters) == 3
        assert all(ch.iid == "SLAVE" for ch in b.critters.values())

    def test_non_lethal_shot_does_not_spawn(self):
        """A shot that doesn't kill the carrier must not trigger spawn."""
        svc = _svc_with_items(SLAVE=_mock_item("SLAVE"))
        carrier = Critter(
            cid=10, iid="CART", health=10.0, max_health=10.0, speed=0.2,
            path=_long_path(), path_progress=0.4,
            spawn_on_death={"SLAVE": 3},
        )
        shot = Shot(
            damage=3.0,  # Non-lethal
            target_cid=carrier.cid,
            source_sid=1,
            flight_remaining_ms=1.0,
            origin=HexCoord(0, 0),
        )
        b = _battle(carrier, pending_shots=[shot])
        svc._step_shots(b, 50.0)
        svc._step_critters(b, 1.0)

        assert carrier.cid in b.critters
        assert len(b.critters) == 1


# ── Wave spawner propagates spawn_on_death ────────────────────────────────────


class TestWaveSpawnPropagation:
    def test_wave_spawned_critter_inherits_spawn_on_death(self):
        """Critters spawned via _make_critter_from_item carry spawn_on_death from item."""
        svc = _svc_with_items(
            CART=_mock_item("CART", spawn_on_death={"SLAVE": 5}),
        )
        critter = svc._make_critter_from_item("CART", path=_long_path())
        assert critter.spawn_on_death == {"SLAVE": 5}

    def test_wave_spawned_critter_no_spawn_on_death(self):
        """Critters without spawn_on_death in item config get empty dict."""
        svc = _svc_with_items(
            SLAVE=_mock_item("SLAVE", spawn_on_death={}),
        )
        critter = svc._make_critter_from_item("SLAVE", path=_long_path())
        assert critter.spawn_on_death == {}
