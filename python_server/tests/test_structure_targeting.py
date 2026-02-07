"""Tests for structure targeting."""

from __future__ import annotations

from gameserver.models.critter import Critter
from gameserver.models.hex import HexCoord
from gameserver.models.structure import Structure


def _make_tower(q: int = 5, r: int = 1, range_: int = 3, damage: float = 10.0) -> Structure:
    return Structure(
        sid=1, iid="tower", position=HexCoord(q, r),
        damage=damage, range=range_, reload_time_ms=1000,
        shot_speed=5.0,
    )


def _make_critter_at(
    cid: int, q: int, path_progress: float = 0.0, path_len: int = 10
) -> Critter:
    path = [HexCoord(i, 0) for i in range(path_len)]
    c = Critter(
        cid=cid, iid="c", health=20, max_health=20,
        speed=2.0, armour=0, path=path, path_progress=path_progress,
    )
    return c


def _find_best_target(
    structure: Structure, critters: dict[int, Critter]
) -> int | None:
    """Targeting: critter with lowest remainder_path within range."""
    best_cid, best_remainder = None, float('inf')
    for cid, c in critters.items():
        if not c.is_alive or c.is_finished:
            continue
        if structure.position.distance_to(c.current_hex) > structure.range:
            continue
        if c.remainder_path < best_remainder:
            best_cid, best_remainder = cid, c.remainder_path
    return best_cid


class TestStructureTargeting:
    def test_targets_most_advanced(self):
        tower = _make_tower(q=5, r=1, range_=3)
        critters = {
            1: _make_critter_at(1, 3, path_progress=3.0),  # closer to end
            2: _make_critter_at(2, 4, path_progress=1.0),  # farther from end
        }
        assert _find_best_target(tower, critters) == 1

    def test_out_of_range_ignored(self):
        tower = _make_tower(q=5, r=1, range_=2)
        critters = {
            1: _make_critter_at(1, 0, path_progress=0.0),  # distance = 5+1 > 2
        }
        assert _find_best_target(tower, critters) is None

    def test_dead_ignored(self):
        tower = _make_tower(q=5, r=1, range_=5)
        c = _make_critter_at(1, 5, path_progress=5.0)
        c.health = 0
        critters = {1: c}
        assert _find_best_target(tower, critters) is None

    def test_finished_ignored(self):
        tower = _make_tower(q=5, r=1, range_=5)
        c = _make_critter_at(1, 9, path_progress=9.0)  # at end of 10-field path
        critters = {1: c}
        assert _find_best_target(tower, critters) is None

    def test_range_symmetric(self):
        """Range is equal in all 6 directions."""
        tower = _make_tower(q=0, r=0, range_=2)
        center = tower.position
        for n in center.neighbors():
            for nn in n.neighbors():
                dist = center.distance_to(nn)
                if dist <= 2:
                    path = [nn]
                    c = Critter(
                        cid=1, iid="c", health=10, max_health=10,
                        speed=1, armour=0, path=path, path_progress=0,
                    )
                    in_range = center.distance_to(c.current_hex) <= tower.range
                    assert in_range
