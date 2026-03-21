#!/usr/bin/env python3
"""Analysiert alle Hex-Maps aus state.yaml:
- Weglänge von Spawnpoint zu Castle
- Kosten aller Türme
- Zeitalter-Verteilung der Türme
"""

import sys
from collections import deque
from pathlib import Path

import yaml

STATE_FILE = Path(__file__).parent / "python_server/state.yaml"
STRUCTURES_FILE = Path(__file__).parent / "python_server/config/structures.yaml"

# Zeitalter-Einteilung nach Effort-Schwellen (aus structures.yaml-Kommentaren)
AGES = [
    ("Stone Age",   0,          200),
    ("Neolithic",   200,      1_500),
    ("Bronze Age",  1_500,    8_000),
    ("Iron Age",    8_000,   30_000),
    ("Middle Ages", 30_000, 130_000),
    ("Renaissance", 130_000, 500_000),
    ("Industrial",  500_000, 2_000_000),
    ("Modern",    2_000_000, 999_999_999),
]

HEX_DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]


def cost_to_age(gold: float) -> str:
    for name, lo, hi in AGES:
        if lo <= gold < hi:
            return name
    return "Unbekannt"


def bfs_path_length(hex_map: list[dict]) -> int | None:
    """BFS von spawnpoint zu castle über path/spawnpoint/castle-Felder."""
    walkable = set()
    start = None
    goal = None

    for cell in hex_map:
        t = cell["type"]
        if isinstance(t, dict):
            t = t.get("type", "")
        q, r = cell["q"], cell["r"]
        if t in ("path", "spawnpoint", "castle"):
            walkable.add((q, r))
        if t == "spawnpoint":
            start = (q, r)
        if t == "castle":
            goal = (q, r)

    if start is None or goal is None:
        return None

    queue = deque([(start, 0)])
    visited = {start}
    while queue:
        (q, r), dist = queue.popleft()
        if (q, r) == goal:
            return dist
        for dq, dr in HEX_DIRECTIONS:
            nb = (q + dq, r + dr)
            if nb not in visited and nb in walkable:
                visited.add(nb)
                queue.append((nb, dist + 1))
    return None


def analyze_towers(hex_map: list[dict], structures: dict) -> tuple[int, list[str], dict]:
    """Gibt zurück: (gesamt_kosten, tower_liste, zeitalter_counts)"""
    total_cost = 0
    tower_names = []
    age_counts: dict[str, int] = {}

    for cell in hex_map:
        t = cell["type"]
        if isinstance(t, dict):
            t = t.get("type", "")
        if t not in ("path", "castle", "spawnpoint", "") and t is not None:
            if t in structures:
                cfg = structures[t]
                cost = cfg.get("costs", {}).get("gold", 0)
                total_cost += cost
                tower_names.append(t)
                age = cost_to_age(cost)
                age_counts[age] = age_counts.get(age, 0) + 1

    return total_cost, tower_names, age_counts


def main():
    state = yaml.safe_load(STATE_FILE.read_text())
    structures = yaml.safe_load(STRUCTURES_FILE.read_text())

    empires = state.get("empires", [])
    player_empires = [e for e in empires if e.get("hex_map")]

    for empire in player_empires:
        name = empire.get("name", f"uid={empire['uid']}")
        uid = empire["uid"]
        hex_map = empire["hex_map"]

        print(f"\n{'='*55}")
        print(f"  Empire: {name}  (uid={uid})")
        print(f"{'='*55}")

        # 1. Weglänge
        path_len = bfs_path_length(hex_map)
        if path_len is not None:
            print(f"  Weglänge Spawn → Castle : {path_len} Felder")
        else:
            print("  Weglänge: Kein vollständiger Pfad gefunden")

        # 2. Turmkosten
        total_cost, tower_names, age_counts = analyze_towers(hex_map, structures)
        num_towers = len(tower_names)
        print(f"  Türme gesamt            : {num_towers}")
        if num_towers:
            print(f"  Gesamtkosten Türme      : {total_cost:,.0f} Gold")
            print(f"  Ø Kosten pro Turm       : {total_cost / num_towers:,.0f} Gold")

            # Turmtypen-Übersicht
            from collections import Counter
            counts = Counter(tower_names)
            print(f"  Turmtypen:")
            for ttype, cnt in sorted(counts.items(), key=lambda x: -x[1]):
                gold = structures.get(ttype, {}).get("costs", {}).get("gold", 0)
                print(f"    {ttype:<25} x{cnt}  ({gold:,.0f} Gold)")

            # 3. Zeitalter-Verteilung
            print(f"  Zeitalter-Verteilung:")
            for age_name, _, _ in AGES:
                cnt = age_counts.get(age_name, 0)
                if cnt > 0:
                    pct = cnt / num_towers * 100
                    bar = "█" * int(pct / 5)
                    print(f"    {age_name:<15} {cnt:>2}x  {pct:5.1f}%  {bar}")
        else:
            print("  Keine Türme auf der Map.")


if __name__ == "__main__":
    main()
