"""Clustering of empires into mutually-allied groups, ranked by pooled culture."""

from __future__ import annotations

from typing import Any, Iterable


def group_by_pooled_culture(
    culture_by_uid: dict[int, float],
    mutual_alliances: dict[int, set[int]],
) -> list[list[int]]:
    """Cluster uids into connected components of the mutual-alliance graph.

    Groups are sorted by pooled (summed) culture descending; members within
    a group are sorted by their own culture descending. An unallied uid forms
    a group of size 1 and is ranked on its own culture, so a strong solo
    empire can outrank — and outplace — a team. `mutual_alliances` maps
    uid -> set of allied uids, as returned by
    `Database.get_all_mutual_alliances()`.
    """
    listed_uids = set(culture_by_uid)
    seen: set[int] = set()
    groups: list[list[int]] = []
    for root in culture_by_uid:
        if root in seen:
            continue
        stack = [root]
        cluster: set[int] = set()
        while stack:
            u = stack.pop()
            if u in cluster or u not in listed_uids:
                continue
            cluster.add(u)
            stack.extend(mutual_alliances.get(u, set()))
        seen |= cluster
        groups.append(sorted(cluster))

    def _pooled(group: list[int]) -> float:
        return sum(culture_by_uid[u] for u in group)

    groups.sort(key=_pooled, reverse=True)
    for group in groups:
        group.sort(key=lambda u: culture_by_uid[u], reverse=True)
    return groups


def pooled_culture_leader(empires: Iterable[Any]) -> list[Any]:
    """Return the empires that would win the season if it ended now.

    The season is a pure score race on pooled culture: allied empires are
    ranked on their combined total and win together, an unallied empire is
    ranked on its own and can take the title alone if it outscores every team.
    So this is the leading group, members strongest-first — two names for a
    team, one for a solo winner, `[]` only when no empires were passed.

    Reads `Empire.allied_uids` — the in-memory mirror of the mutual-alliance
    table, kept in sync by the diplomacy router — so no database access is
    needed and this stays callable from synchronous payload builders. Callers
    pass an already-filtered iterable (the AI empire does not belong in a
    culture ranking).
    """
    by_uid = {e.uid: e for e in empires}
    if not by_uid:
        return []
    culture_by_uid = {uid: e.resources.get("culture", 0.0) for uid, e in by_uid.items()}
    mutual_alliances = {uid: set(getattr(e, "allied_uids", ())) for uid, e in by_uid.items()}
    groups = group_by_pooled_culture(culture_by_uid, mutual_alliances)
    return [by_uid[u] for u in groups[0]] if groups else []
