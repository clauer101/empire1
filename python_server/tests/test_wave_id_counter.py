"""Tests for the wave ID counter (sync_wid_counter).

Regression test for the bug where _next_wid was not synced after server restart,
causing new waves to reuse wave_ids already present in the loaded state.
"""

from gameserver.models.army import Army, CritterWave
from gameserver.models.empire import Empire
from gameserver.network.handlers._core import sync_wid_counter
import gameserver.network.handlers._core as _core_mod


class TestSyncWidCounter:
    def _empire_with_waves(self, uid: int, wave_ids: list[int]) -> Empire:
        empire = Empire(uid=uid, name=f"empire_{uid}")
        waves = [CritterWave(wave_id=wid, iid="SLAVE", slots=1) for wid in wave_ids]
        empire.armies.append(Army(aid=uid * 100, uid=uid, name="Army", waves=waves))
        return empire

    def test_counter_set_above_max_wave_id(self):
        empires = {
            1: self._empire_with_waves(1, [1, 2, 3]),
            2: self._empire_with_waves(2, [4, 5, 10]),
        }
        sync_wid_counter(empires)
        assert _core_mod._next_wid == 11

    def test_counter_set_above_max_across_all_armies(self):
        empire = Empire(uid=3, name="multi")
        empire.armies.append(Army(aid=300, uid=3, name="A", waves=[
            CritterWave(wave_id=7, iid="SLAVE", slots=1),
        ]))
        empire.armies.append(Army(aid=301, uid=3, name="B", waves=[
            CritterWave(wave_id=20, iid="SLAVE", slots=1),
            CritterWave(wave_id=15, iid="SLAVE", slots=1),
        ]))
        sync_wid_counter({3: empire})
        assert _core_mod._next_wid == 21

    def test_counter_is_one_when_no_waves(self):
        empire = Empire(uid=4, name="empty")
        empire.armies.append(Army(aid=400, uid=4, name="A", waves=[]))
        sync_wid_counter({4: empire})
        assert _core_mod._next_wid == 1

    def test_new_wave_ids_do_not_collide_after_sync(self):
        """After sync, new waves must not reuse existing wave_ids."""
        existing_ids = [1, 2, 3, 5, 8]
        empires = {1: self._empire_with_waves(1, existing_ids)}
        sync_wid_counter(empires)

        assigned = []
        for _ in range(5):
            assigned.append(_core_mod._next_wid)
            _core_mod._next_wid += 1

        for new_id in assigned:
            assert new_id not in existing_ids, f"wave_id {new_id} collides with existing"
