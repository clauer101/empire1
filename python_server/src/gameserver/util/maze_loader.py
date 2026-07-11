"""maze_loader.py — Single source of truth for loading attackable hex maps.

Combines two sources of maps, in this priority order:

- **Curated maps** — `python_server/config/saved_maps.yaml`, editable via the
  balance tuner and `/api/tools/map-life`.
- **Past-season snapshots** — every non-AI empire's hex_map from
  `data/prod/results/season*/state.yaml`, prefixed `"season1:Name"` etc. so
  they're distinguishable from curated maps and from same-named empires
  across seasons.

Used by:
- `/api/saved-maps` (`network/web_server.py`, `web/fastapi_server.py`) and the
  `web/tools/sim-map.html` map picker it feeds — via `load_raw_maps()`.
- `scripts/sim_map.py` (single-map lookup by name, incl. season-prefixed
  names) — via `find_raw_map()`.
- `scripts/balance_sim.py` (era-classified simulation pool, curated maps
  only) — via `build_era_maze_pool()`.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from gameserver.engine.hex_pathfinding import find_path_from_spawn_to_castle
from gameserver.util.eras import ERA_ORDER

# Parent of `src/` — `python_server/` locally, `/app` in the Docker image
# (Dockerfile copies `python_server/{src,config}` to `/app/{src,config}`,
# flattening one directory level). Mirrors `_CONFIG_DIR` in `network/web_server.py`.
_BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
SAVED_MAPS_PATH = _BASE_DIR / "config" / "saved_maps.yaml"
# `data/` sits next to `python_server/` locally but is volume-mounted straight
# into `/app/data` in Docker (no extra nesting there) — try both layouts.
SEASON_RESULTS_DIR = (
    _BASE_DIR / "data" / "prod" / "results"
    if (_BASE_DIR / "data").exists()
    else _BASE_DIR.parent / "data" / "prod" / "results"
)


def tile_type(v: Any) -> str:
    """Return the type string from a tile value (str or {"type": ..., "select": ...} dict)."""
    return v if isinstance(v, str) else (v.get("type", "empty") if isinstance(v, dict) else "empty")


def tile_select(v: Any, default: str = "first") -> str:
    """Return the select mode from a tile value (str or dict)."""
    return v.get("select", default) if isinstance(v, dict) else default


# ── Raw map loading (name, hex_map-as-list, life) — feeds /api/saved-maps ────

def load_raw_saved_maps(path: Path = SAVED_MAPS_PATH) -> list[dict[str, Any]]:
    """Load curated maps from saved_maps.yaml as {name, hex_map, life, source} dicts.

    `hex_map` stays in the raw list-of-tiles form (`[{q, r, type}, ...]`) —
    callers normalize it as needed (`normalize_hex_map` below, or the
    `{"type": ...}`-wrapping some power/age_pct helpers expect).
    """
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text()) or {}
    return [
        {"name": m.get("name", m.get("id", "?")), "hex_map": m.get("hex_map") or [], "life": m.get("life"), "source": "saved"}
        for m in (data.get("maps") or [])
    ]


def load_raw_season_maps(season_results_dir: Path = SEASON_RESULTS_DIR) -> list[dict[str, Any]]:
    """Load every non-AI empire's hex_map from past-season state.yaml snapshots."""
    maps: list[dict[str, Any]] = []
    for state_path in sorted(season_results_dir.glob("season*/state.yaml")):
        season_label = state_path.parent.name  # "season1", "season2", ...
        try:
            data = yaml.safe_load(state_path.read_text()) or {}
        except OSError:
            continue
        for empire in data.get("empires") or []:
            name = empire.get("name", "")
            hex_map = empire.get("hex_map") or []
            if name == "AI" or not hex_map:
                continue
            maps.append({
                "name": f"{season_label}:{name}",
                "hex_map": hex_map,
                "life": empire.get("max_life"),
                "source": season_label,
            })
    return maps


def load_raw_maps(
    saved_maps_path: Path = SAVED_MAPS_PATH,
    season_results_dir: Path = SEASON_RESULTS_DIR,
) -> list[dict[str, Any]]:
    """All maps (curated + every past season), each `{name, hex_map, life, source}`."""
    return load_raw_saved_maps(saved_maps_path) + load_raw_season_maps(season_results_dir)


def find_raw_map(name: str, saved_maps_path: Path = SAVED_MAPS_PATH, season_results_dir: Path = SEASON_RESULTS_DIR) -> dict[str, Any] | None:
    """Look up a single map by name across both sources (curated first)."""
    for m in load_raw_maps(saved_maps_path, season_results_dir):
        if m["name"] == name:
            return m
    return None


def normalize_hex_map(tiles_list: list[dict[str, Any]]) -> dict[str, str]:
    """Convert the list-of-tiles format into {"q,r": type} with plain-string types.

    Mirrors `persistence.state_load._deserialize_editor_hex_map`'s keying; also
    flattens nested `{type, select}` tile values to a plain type string (the
    select strategy is re-derived separately where needed, e.g.
    `scripts.battle_sim.build_structures`).
    """
    return {f"{t['q']},{t['r']}": tile_type(t.get("type", "")) for t in tiles_list}


# ── Era-classified maze pool — feeds scripts/balance_sim.py ──────────────────

@dataclass
class Maze:
    """A single attackable hex map with its dominant era classification."""

    name: str
    source: str  # "saved" | "season1" | "season2" | ...
    hex_map: dict[str, str]  # "q,r" -> tile type (normalized to plain strings)
    path: list[Any]  # list[HexCoord] from spawn to castle
    era: str  # lowercase ERA_ORDER key
    tower_count: int
    life: float
    era_counts: dict[str, int] = field(default_factory=dict)


def _classify_era(hex_map: dict[str, str], item_era_index: dict[str, int]) -> tuple[str | None, dict[str, int], int]:
    """Return (era, era_counts, tower_count) for a hex_map.

    The maze's era is the *highest* era among its placed towers — a single
    Iron Age tower makes the whole maze an Iron Age maze, regardless of how
    many older-era towers surround it. This mirrors how a player's maze
    actually reflects their era progress: once they place a newer-era tower,
    the maze belongs to that era, even before most of it is upgraded. Uses
    the same `item_era_index` the live server builds from
    `structures.yaml`/`critters.yaml` `era:` fields. Unknown iids (unowned
    tiles, ruler markers, removed items) are skipped — they are not in
    `item_era_index`.
    """
    era_counts: Counter[str] = Counter()
    tower_count = 0
    best_idx: int | None = None
    for tt in hex_map.values():
        era_idx = item_era_index.get(tt)
        if era_idx is None:
            continue
        tower_count += 1
        era_counts[ERA_ORDER[era_idx]] += 1
        if best_idx is None or era_idx > best_idx:
            best_idx = era_idx
    if best_idx is None:
        return None, {}, 0
    return ERA_ORDER[best_idx], dict(era_counts), tower_count


def _maze_from_raw(raw: dict[str, Any], item_era_index: dict[str, int]) -> Maze | None:
    hex_map = normalize_hex_map(raw["hex_map"])
    era, era_counts, tower_count = _classify_era(hex_map, item_era_index)
    if era is None:
        return None
    path = find_path_from_spawn_to_castle(hex_map)
    if not path:
        return None
    return Maze(
        name=raw["name"], source=raw["source"], hex_map=hex_map, path=path, era=era,
        tower_count=tower_count, life=float(raw.get("life") or 10.0), era_counts=era_counts,
    )


def build_era_maze_pool(
    item_era_index: dict[str, int],
    saved_maps_path: Path = SAVED_MAPS_PATH,
) -> dict[str, list[Maze]]:
    """Return {era: [Maze, ...]}, from curated maps (`saved_maps.yaml`) only.

    An era absent from `saved_maps.yaml` is simply absent from the returned
    dict — callers should report it as uncovered.
    """
    all_mazes = [
        m for raw in load_raw_saved_maps(saved_maps_path)
        if (m := _maze_from_raw(raw, item_era_index)) is not None
    ]

    pool: dict[str, list[Maze]] = {}
    for maze in all_mazes:
        pool.setdefault(maze.era, []).append(maze)
    return pool


def coverage_report(pool: dict[str, list[Maze]]) -> str:
    """Human-readable per-era maze coverage table."""
    source_col = 24
    lines = [f"{'Era':<14}{'Mazes':>7}  {'Source(s)':<{source_col}}{'Towers (min-max)':<20}"]
    lines.append("-" * len(lines[0]))
    for era in ERA_ORDER:
        mazes = pool.get(era, [])
        if not mazes:
            lines.append(f"{era:<14}{'0':>7}  {'— uncovered —':<{source_col}}")
            continue
        sources = sorted({m.source for m in mazes})
        tower_counts = [m.tower_count for m in mazes]
        towers_str = f"{min(tower_counts)}-{max(tower_counts)}"
        lines.append(
            f"{era:<14}{len(mazes):>7}  {','.join(sources):<{source_col}}{towers_str}"
        )
    return "\n".join(lines)
