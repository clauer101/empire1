"""Tests for empire power metrics (power_service.py)."""

from unittest.mock import MagicMock

import pytest

from gameserver.engine.power_service import (
    economy_power, attack_power, defense_power, total_power, compute_power,
    PowerReport,
)
from gameserver.models.empire import Empire
from gameserver.models.items import ItemDetails, ItemType


# ── Helpers ───────────────────────────────────────────────────────────────────

def _empire(**kwargs) -> Empire:
    e = Empire(uid=1, name="Test")
    for k, v in kwargs.items():
        object.__setattr__(e, k, v) if e.__class__.__dataclass_fields__.get(k) else setattr(e, k, v)
    return e


def _upgrades(*items: ItemDetails) -> MagicMock:
    up = MagicMock()
    by_iid = {i.iid: i for i in items}
    up.get.side_effect = lambda iid: by_iid.get(iid)
    up.items = by_iid
    return up


def _building(iid: str, effort: float = 100.0) -> ItemDetails:
    return ItemDetails(iid=iid, item_type=ItemType.BUILDING, effort=effort)


def _knowledge(iid: str, effort: float = 200.0) -> ItemDetails:
    return ItemDetails(iid=iid, item_type=ItemType.KNOWLEDGE, effort=effort)


def _critter(iid: str, health: float = 10.0, speed: float = 0.2,
             armour: float = 0.0, slots: int = 1) -> ItemDetails:
    return ItemDetails(iid=iid, item_type=ItemType.CRITTER,
                       health=health, speed=speed, armour=armour, slots=slots)


def _tower(iid: str, damage: float = 5.0, range_: float = 1.5,
           reload_ms: float = 1000.0, effects: dict | None = None) -> ItemDetails:
    return ItemDetails(iid=iid, item_type=ItemType.STRUCTURE,
                       damage=damage, range=range_, reload_time_ms=reload_ms,
                       effects=effects or {})


# ── economy_power ─────────────────────────────────────────────────────────────


class TestEconomyPower:
    def test_empty_empire_nonzero(self):
        """Even an empty empire has a valid (≥0) score."""
        e = _empire()
        assert economy_power(e, _upgrades()) >= 0.0

    def test_completed_building_adds_score(self):
        """Finishing a building with higher effort raises the score."""
        b = _building("HUT", effort=500.0)
        e = _empire(buildings={"HUT": 0.0})
        score = economy_power(e, _upgrades(b))
        assert score > 0.0

    def test_completed_knowledge_adds_score(self):
        k = _knowledge("FIRE", effort=300.0)
        e = _empire(knowledge={"FIRE": 0.0})
        assert economy_power(e, _upgrades(k)) > 0.0

    def test_in_progress_items_do_not_count(self):
        """Items still in progress (remaining > 0) must not contribute."""
        b = _building("HUT", effort=500.0)
        e_done = _empire(buildings={"HUT": 0.0})
        e_wip  = _empire(buildings={"HUT": 100.0})
        assert economy_power(e_done, _upgrades(b)) > economy_power(e_wip, _upgrades(b))

    def test_gold_rate_effect_raises_score(self):
        e_base = _empire()
        e_rich = _empire(effects={"gold_offset": 10.0})
        assert economy_power(e_rich, _upgrades()) > economy_power(e_base, _upgrades())

    def test_culture_rate_effect_raises_score(self):
        e_base = _empire()
        e_cult = _empire(effects={"culture_offset": 5.0})
        assert economy_power(e_cult, _upgrades()) > economy_power(e_base, _upgrades())

    def test_build_speed_modifier_raises_score(self):
        e_base = _empire()
        e_fast = _empire(effects={"build_speed_modifier": 0.5})
        assert economy_power(e_fast, _upgrades()) > economy_power(e_base, _upgrades())

    def test_merchants_raise_score(self):
        e_base = _empire()
        e_merc = _empire(citizens={"merchant": 5, "scientist": 0, "artist": 0})
        assert economy_power(e_merc, _upgrades()) > economy_power(e_base, _upgrades())

    def test_higher_effort_building_scores_more(self):
        """More expensive buildings should contribute more economy power."""
        b_cheap = _building("CHEAP", effort=100.0)
        b_exp   = _building("EXPENSIVE", effort=10_000.0)
        e_cheap = _empire(buildings={"CHEAP": 0.0})
        e_exp   = _empire(buildings={"EXPENSIVE": 0.0})
        up_cheap = _upgrades(b_cheap)
        up_exp   = _upgrades(b_exp)
        assert economy_power(e_exp, up_exp) > economy_power(e_cheap, up_cheap)


# ── attack_power ──────────────────────────────────────────────────────────────


class TestAttackPower:
    def test_empty_empire_nonzero(self):
        assert attack_power(_empire(), _upgrades()) >= 0.0

    def test_unlocked_critter_raises_score(self):
        c = _critter("SLAVE", health=10.0)
        e = _empire()   # no requirements for SLAVE
        assert attack_power(e, _upgrades(c)) > 0.0

    def test_boss_critter_excluded(self):
        """Boss critters must not contribute to attack power (not spawnable)."""
        boss = ItemDetails(iid="KING", item_type=ItemType.CRITTER,
                           health=500.0, speed=0.4, armour=5.0, slots=999, is_boss=True)
        normal = _critter("SLAVE", health=10.0)
        e = _empire()
        with_boss   = attack_power(e, _upgrades(boss, normal))
        without_boss = attack_power(e, _upgrades(normal))
        assert with_boss == pytest.approx(without_boss)

    def test_health_modifier_raises_score(self):
        from gameserver.loaders.game_config_loader import GameConfig, CritterUpgradeDef
        c = _critter("SLAVE", health=10.0)
        gc = MagicMock(spec=GameConfig)
        gc.critter_upgrades = CritterUpgradeDef(health=5.0)
        e_base = _empire()
        e_buff = _empire(item_upgrades={"SLAVE": {"health": 4}})
        assert attack_power(e_buff, _upgrades(c), gc=gc) > attack_power(e_base, _upgrades(c), gc=gc)

    def test_armour_raises_score(self):
        """Critters with armour score higher than identical critters without."""
        c_soft  = _critter("SOFT",  health=10.0, armour=0.0)
        c_hard  = _critter("HARD",  health=10.0, armour=5.0)
        e = _empire()
        assert attack_power(e, _upgrades(c_hard)) > attack_power(e, _upgrades(c_soft))

    def test_locked_critter_does_not_count(self):
        """Critter that requires an unmet prerequisite must not contribute."""
        c = ItemDetails(iid="KNIGHT", item_type=ItemType.CRITTER,
                        health=50.0, speed=0.4, armour=6.0, slots=2,
                        requirements=["FEUDALISM"])
        e = _empire()   # FEUDALISM not completed
        assert attack_power(e, _upgrades(c)) == pytest.approx(0.0)

    def test_culture_steal_modifier_raises_score(self):
        c = _critter("SLAVE")
        e_base = _empire()
        e_loot = _empire(effects={"culture_steal_modifier": 0.3})
        assert attack_power(e_loot, _upgrades(c)) > attack_power(e_base, _upgrades(c))


# ── defense_power ─────────────────────────────────────────────────────────────


class TestDefensePower:
    def _hex_map_with_tower(self, iid: str) -> dict:
        return {"0,0": {"type": iid}}

    def test_empty_empire_nonzero(self):
        """max_life alone gives a floor score."""
        assert defense_power(_empire(), _upgrades()) >= 0.0

    def test_placed_tower_raises_score(self):
        t = _tower("BASIC_TOWER", damage=5.0, range_=1.5, reload_ms=2000.0)
        e_no_tower = _empire()
        e_tower    = _empire(hex_map=self._hex_map_with_tower("BASIC_TOWER"))
        assert defense_power(e_tower, _upgrades(t)) > defense_power(e_no_tower, _upgrades(t))

    def test_higher_dps_tower_scores_more(self):
        t_weak   = _tower("WEAK",   damage=2.0,  reload_ms=2000.0)
        t_strong = _tower("STRONG", damage=20.0, reload_ms=2000.0)
        e_weak   = _empire(hex_map=self._hex_map_with_tower("WEAK"))
        e_strong = _empire(hex_map=self._hex_map_with_tower("STRONG"))
        assert defense_power(e_strong, _upgrades(t_strong)) > defense_power(e_weak, _upgrades(t_weak))

    def test_damage_modifier_raises_score(self):
        from gameserver.loaders.game_config_loader import GameConfig, StructureUpgradeDef
        t = _tower("T", damage=10.0, reload_ms=1000.0)
        gc = MagicMock(spec=GameConfig)
        gc.structure_upgrades = StructureUpgradeDef(damage=5.0)
        e_base = _empire(hex_map=self._hex_map_with_tower("T"))
        e_buff = _empire(hex_map=self._hex_map_with_tower("T"),
                         item_upgrades={"T": {"damage": 4}})
        assert defense_power(e_buff, _upgrades(t), gc=gc) > defense_power(e_base, _upgrades(t), gc=gc)

    def test_slow_tower_gets_bonus(self):
        t_plain = _tower("PLAIN", damage=5.0, reload_ms=1000.0)
        t_slow  = _tower("SLOW",  damage=5.0, reload_ms=1000.0,
                         effects={"slow_duration": 2000, "slow_ratio": 0.3})
        e_plain = _empire(hex_map=self._hex_map_with_tower("PLAIN"))
        e_slow  = _empire(hex_map=self._hex_map_with_tower("SLOW"))
        assert defense_power(e_slow, _upgrades(t_slow)) > defense_power(e_plain, _upgrades(t_plain))

    def test_splash_tower_gets_bonus(self):
        t_plain  = _tower("PLAIN",  damage=5.0, reload_ms=1000.0)
        t_splash = _tower("SPLASH", damage=5.0, reload_ms=1000.0,
                          effects={"splash_radius": 0.6})
        e_plain  = _empire(hex_map=self._hex_map_with_tower("PLAIN"))
        e_splash = _empire(hex_map=self._hex_map_with_tower("SPLASH"))
        assert defense_power(e_splash, _upgrades(t_splash)) > defense_power(e_plain, _upgrades(t_plain))

    def test_non_tower_tiles_ignored(self):
        """Tiles like 'path', 'castle', 'empty' must not contribute."""
        e = _empire(hex_map={
            "0,0": {"type": "castle"},
            "1,0": {"type": "path"},
            "2,0": {"type": "empty"},
        })
        assert defense_power(e, _upgrades()) == defense_power(_empire(), _upgrades())

    def test_max_life_contributes(self):
        e_low  = _empire(max_life=5.0)
        e_high = _empire(max_life=50.0)
        assert defense_power(e_high, _upgrades()) > defense_power(e_low, _upgrades())

    def test_artefacts_contribute(self):
        e_none = _empire()
        e_art  = _empire(artefacts=["SWORD", "SHIELD"])
        assert defense_power(e_art, _upgrades()) > defense_power(e_none, _upgrades())


# ── total_power ───────────────────────────────────────────────────────────────


class TestTotalPower:
    def test_is_weighted_combination(self):
        tot = total_power(economy=1000.0, attack=2000.0, defense=3000.0)
        assert tot == pytest.approx(1000 * 0.3 + 2000 * 0.35 + 3000 * 0.35)

    def test_all_zero_gives_zero(self):
        assert total_power(0.0, 0.0, 0.0) == pytest.approx(0.0)


# ── compute_power ─────────────────────────────────────────────────────────────


class TestComputePower:
    def test_returns_power_report(self):
        e = _empire()
        report = compute_power(e, _upgrades())
        assert isinstance(report, PowerReport)

    def test_to_dict_keys(self):
        e = _empire()
        d = compute_power(e, _upgrades()).to_dict()
        assert set(d.keys()) == {"economy", "attack", "defense", "total"}

    def test_total_matches_components(self):
        t = _tower("T", damage=10.0, reload_ms=1000.0)
        c = _critter("C", health=20.0)
        b = _building("B", effort=500.0)
        e = _empire(
            buildings={"B": 0.0},
            hex_map={"0,0": {"type": "T"}},
        )
        up = _upgrades(t, c, b)
        r = compute_power(e, up)
        expected_total = total_power(r.economy, r.attack, r.defense)
        assert r.total == pytest.approx(expected_total)

    def test_stronger_empire_scores_higher_total(self):
        """An empire with completed research + towers should outscores an empty one."""
        k = _knowledge("FIRE", effort=5000.0)
        t = _tower("CANNON", damage=32.0, reload_ms=2000.0)
        c = _critter("KNIGHT", health=44.0, armour=6.0, slots=2)

        e_empty = _empire()
        e_rich  = _empire(
            knowledge={"FIRE": 0.0},
            hex_map={"0,0": {"type": "CANNON"}},
            effects={"gold_offset": 5.0, "damage_modifier": 0.3},
        )
        up = _upgrades(k, t, c)
        assert compute_power(e_rich, up).total > compute_power(e_empty, up).total
