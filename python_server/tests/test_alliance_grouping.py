"""Unit tests for the alliance-clustering helper used to pool season/leaderboard
rankings by mutual alliance (see tasks/diplomacy_and_pooled_score_analysis.md)."""

from __future__ import annotations

from gameserver.util.alliance_grouping import group_by_pooled_culture, pooled_culture_leader

from conftest import make_empire


def test_unallied_uids_form_singleton_groups_sorted_by_own_culture():
    culture = {1: 100.0, 2: 300.0, 3: 200.0}
    groups = group_by_pooled_culture(culture, mutual_alliances={})
    assert groups == [[2], [3], [1]]


def test_mutual_pair_is_pooled_and_ranked_on_combined_culture():
    # Pair (2, 3) pools to 250, beating solo uid 1's 200.
    culture = {1: 200.0, 2: 100.0, 3: 150.0}
    mutual = {2: {3}, 3: {2}}
    groups = group_by_pooled_culture(culture, mutual)
    assert groups[0] == [3, 2]  # pooled group first, members sorted by own culture desc
    assert groups[1] == [1]


def test_transitive_chain_pools_into_one_group():
    # get_all_mutual_alliances() only ever returns fully-symmetric edges, but
    # if max_alliances ever rises above 1, chains like 2-3 and 3-4 form one
    # connected group even though 2 and 4 never allied directly.
    culture = {1: 200.0, 2: 50.0, 3: 60.0, 4: 100.0}
    mutual = {2: {3}, 3: {2, 4}, 4: {3}}
    groups = group_by_pooled_culture(culture, mutual)
    assert groups[0] == [4, 3, 2]  # pooled 210, beats uid 1's solo 200
    assert groups[1] == [1]


def test_alliance_partner_absent_from_culture_map_is_ignored():
    # uid 3 is mutually allied with 2 but not present in culture_by_uid
    # (e.g. filtered out elsewhere) -> must not crash or be included.
    culture = {1: 200.0, 2: 100.0}
    mutual = {2: {3}, 3: {2}}
    groups = group_by_pooled_culture(culture, mutual)
    assert groups == [[1], [2]]


# ---------------------------------------------------------------------------
# pooled_culture_leader — who would win the season right now
# ---------------------------------------------------------------------------

def _empire(uid: int, name: str, culture: float, allied: set[int] | None = None):
    return make_empire(uid=uid, name=name, culture=culture, allied_uids=allied or set())


def test_team_total_beats_a_stronger_individual():
    # A two-player team wins on combined culture even though the solo empire
    # holds the highest individual score.
    leaders = pooled_culture_leader([
        _empire(1, "Top Individual", 300.0),
        _empire(2, "Team A", 250.0, allied={3}),
        _empire(3, "Team B", 100.0, allied={2}),
    ])
    assert [e.name for e in leaders] == ["Team A", "Team B"]  # strongest member first


def test_a_solo_empire_outscoring_every_team_leads_alone():
    # The flip side: pooling does not make a team unbeatable — an unallied
    # empire with more culture than any team's total leads on its own.
    leaders = pooled_culture_leader([
        _empire(1, "Runaway Solo", 10_000.0),
        _empire(2, "Team A", 200.0, allied={3}),
        _empire(3, "Team B", 100.0, allied={2}),
    ])
    assert [e.name for e in leaders] == ["Runaway Solo"]


def test_season_without_any_alliance_is_led_by_the_top_individual():
    leaders = pooled_culture_leader([
        _empire(1, "Solo", 300.0),
        _empire(2, "Also Solo", 200.0),
    ])
    assert [e.name for e in leaders] == ["Solo"]


def test_team_members_are_ordered_by_own_culture():
    leaders = pooled_culture_leader([
        _empire(2, "Weaker", 100.0, allied={3}),
        _empire(3, "Stronger", 250.0, allied={2}),
    ])
    assert [e.name for e in leaders] == ["Stronger", "Weaker"]


def test_no_empires_yields_no_leader():
    assert pooled_culture_leader([]) == []
