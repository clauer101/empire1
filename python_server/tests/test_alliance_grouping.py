"""Unit tests for the alliance-clustering helper used to pool season/leaderboard
rankings by mutual alliance (see tasks/diplomacy_and_pooled_score_analysis.md)."""

from __future__ import annotations

from gameserver.util.alliance_grouping import group_by_pooled_culture


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
