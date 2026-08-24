"""Clustering of empires into mutually-allied groups, ranked by pooled culture."""

from __future__ import annotations


def group_by_pooled_culture(
    culture_by_uid: dict[int, float],
    mutual_alliances: dict[int, set[int]],
) -> list[list[int]]:
    """Cluster uids into connected components of the mutual-alliance graph.

    Groups are sorted by pooled (summed) culture descending; members within
    a group are sorted by their own culture descending. An unallied uid forms
    a group of size 1. `mutual_alliances` maps uid -> set of allied uids, as
    returned by `Database.get_all_mutual_alliances()`.
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
