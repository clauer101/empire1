"""The season winner announced to clients is scored on pooled culture.

Both end-rally payloads (`/api/empire/summary` via handlers/auth.py and
`/api/era-map` via routers/empire.py) report the culture leader. They share one
implementation — `rest_api.culture_leader_names` — and these tests pin the
pooling behaviour, the fact that a strong enough solo empire still wins alone,
and that the two payloads cannot drift apart again.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from gameserver.engine.ai_service import AI_UID
from gameserver.network.handlers.auth import _build_end_rally_info
from gameserver.network.rest_api import culture_leader_names
from gameserver.network.routers.empire import _build_end_rally_info_for_era_map

from conftest import make_empire, make_services


def _service_with(*empires):
    svc = make_services()
    for empire in empires:
        svc.empire_service.register(empire)
    return svc


def _game_config():
    gc = MagicMock()
    gc.end_rally_effects = {}
    gc.end_rally_duration = 3600.0
    gc.end_criterion = "THE_WORLD_WONDER"
    return gc


class TestCultureLeaderNames:
    def test_team_total_decides_not_the_best_individual(self):
        svc = _service_with(
            make_empire(uid=1, name="Top Individual", culture=300.0),
            make_empire(uid=2, name="Team A", culture=250.0, allied_uids={3}),
            make_empire(uid=3, name="Team B", culture=100.0, allied_uids={2}),
        )
        assert culture_leader_names(svc.empire_service) == ["Team A", "Team B"]

    def test_a_solo_outscoring_the_team_takes_the_title_alone(self):
        # 500 beats the team's pooled 350 — pooling is a score bonus, not a
        # monopoly on the title.
        svc = _service_with(
            make_empire(uid=1, name="Solo", culture=500.0),
            make_empire(uid=2, name="Team A", culture=250.0, allied_uids={3}),
            make_empire(uid=3, name="Team B", culture=100.0, allied_uids={2}),
        )
        assert culture_leader_names(svc.empire_service) == ["Solo"]

    def test_season_without_alliances_is_led_by_the_top_individual(self):
        svc = _service_with(
            make_empire(uid=1, name="Solo", culture=500.0),
            make_empire(uid=2, name="Also Solo", culture=250.0),
        )
        assert culture_leader_names(svc.empire_service) == ["Solo"]

    def test_ai_empire_is_never_the_leader(self):
        svc = _service_with(
            make_empire(uid=AI_UID, name="AI", culture=10_000_000.0),
            make_empire(uid=1, name="Team A", culture=20.0, allied_uids={2}),
            make_empire(uid=2, name="Team B", culture=10.0, allied_uids={1}),
        )
        assert culture_leader_names(svc.empire_service) == ["Team A", "Team B"]

    def test_no_empire_service_yields_no_names(self):
        assert culture_leader_names(None) == []


class TestEndRallyPayloads:
    def test_both_payloads_report_the_same_pooled_leader(self):
        svc = _service_with(
            make_empire(uid=1, name="Top Individual", culture=300.0),
            make_empire(uid=2, name="Team A", culture=250.0, allied_uids={3}),
            make_empire(uid=3, name="Team B", culture=100.0, allied_uids={2}),
        )
        gc = _game_config()

        summary = _build_end_rally_info(gc, svc.empire_service)
        era_map = _build_end_rally_info_for_era_map(gc, svc.empire_service)

        assert summary["culture_leader_names"] == ["Team A", "Team B"]
        assert era_map["culture_leader_names"] == summary["culture_leader_names"]
        # Legacy string field stays populated for API consumers (bots)
        assert summary["culture_leader_name"] == "Team A & Team B"
        assert era_map["culture_leader_name"] == summary["culture_leader_name"]

    def test_solo_winner_is_reported_without_a_separator(self):
        svc = _service_with(make_empire(uid=1, name="Solo", culture=300.0))
        gc = _game_config()

        summary = _build_end_rally_info(gc, svc.empire_service)
        era_map = _build_end_rally_info_for_era_map(gc, svc.empire_service)

        assert summary["culture_leader_names"] == ["Solo"]
        assert summary["culture_leader_name"] == "Solo"
        assert era_map["culture_leader_names"] == summary["culture_leader_names"]
        assert era_map["culture_leader_name"] == summary["culture_leader_name"]
