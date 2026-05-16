"""Web client routes — static files + game config admin API.

Extracted from web/fastapi_server.py and integrated into the main
gameserver REST app via register_web_routes().
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, Request, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, StreamingResponse

log = logging.getLogger(__name__)

# ── Config paths (relative to this file → python_server/config/) ─────────────
_CONFIG_DIR = Path(__file__).resolve().parent.parent.parent.parent / "config"
AI_WAVES_PATH   = _CONFIG_DIR / "ai_waves.yaml"
GAME_CONFIG_PATH = _CONFIG_DIR / "game.yaml"
BUILDINGS_PATH  = _CONFIG_DIR / "buildings.yaml"
KNOWLEDGE_PATH  = _CONFIG_DIR / "knowledge.yaml"
CRITTERS_PATH   = _CONFIG_DIR / "critters.yaml"
STRUCTURES_PATH = _CONFIG_DIR / "structures.yaml"
ARTIFACTS_PATH  = _CONFIG_DIR / "artifacts.yaml"
_SAVED_MAPS_PATH = _CONFIG_DIR / "saved_maps.yaml"

_ITEM_IID_RE = re.compile(r'^([A-Z][A-Z0-9_]+):')

_ERA_PATTERNS = [
    ("stone",        re.compile(r'#\s+STEINZEIT')),
    ("neolithic",    re.compile(r'#\s+NEOLITHIKUM')),
    ("bronze",       re.compile(r'#\s+BRONZEZEIT')),
    ("iron",         re.compile(r'#\s+EISENZEIT')),
    ("middle_ages",  re.compile(r'#\s+MITTELALTER')),
    ("renaissance",  re.compile(r'#\s+RENAISSANCE')),
    ("industrial",   re.compile(r'#\s+INDUSTRIALIS')),
    ("modern",       re.compile(r'#\s+MODERNE')),
    ("future",       re.compile(r'#\s+ZUKUNFT')),
]

_ERA_INFO = {
    "stone":        "Effort 20 – 1.500",
    "neolithic":    "Effort 800 – 7.500",
    "bronze":       "Effort 2.500 – 8.000",
    "iron":         "Effort 8.000 – 30.000",
    "middle_ages":  "Effort 28.000 – 130.000",
    "renaissance":  "Effort 100.000 – 500.000",
    "industrial":   "Effort 500.000 – 2.000.000",
    "modern":       "Effort 2.000.000 – 5.300.000",
    "future":       "Effort 40.000.000 – 100.000.000",
}

_ERA_ORDER = list(_ERA_INFO.keys())

_ERA_COMMENT_KEY = {
    "stone": "STEINZEIT", "neolithic": "NEOLITHIKUM", "bronze": "BRONZEZEIT",
    "iron": "EISENZEIT", "middle_ages": "MITTELALTER", "renaissance": "RENAISSANCE",
    "industrial": "INDUSTRIALISIERUNG", "modern": "MODERNE", "future": "ZUKUNFT",
}

_SPRITE_EXTS = [".png", ".webp", ".jpg"]

_map_power_upgrades = None
_structure_era_map: dict[str, str] | None = None
NON_TOWER = {"castle", "spawnpoint", "path", "empty", "blocked", "void", ""}


# ── Helper functions ──────────────────────────────────────────────────────────

def _parse_ai_waves() -> list[dict[str, Any]]:
    raw = AI_WAVES_PATH.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    waves = data.get("armies", [])
    current_era = "stone"
    wave_eras: list[str] = []
    for line in raw.split("\n"):
        for era_name, pattern in _ERA_PATTERNS:
            if pattern.search(line):
                current_era = era_name
                break
        if line.strip().startswith("- name:"):
            wave_eras.append(current_era)
    result = []
    for i, wave in enumerate(waves):
        era = wave_eras[i] if i < len(wave_eras) else "stone"
        result.append({**wave, "era": era})
    return result


def _parse_yaml_era_groups(path: Path) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {era: [] for era in _ERA_ORDER}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    for iid, item in data.items():
        if not isinstance(item, dict):
            continue
        era = item.get("era", _ERA_ORDER[0])
        if era in result:
            result[era].append(iid)
    return result


def _parse_era_items() -> dict[str, list[str]]:
    result: dict[str, list[str]] = {era: [] for era in _ERA_ORDER}
    for path in (BUILDINGS_PATH, KNOWLEDGE_PATH):
        for era, iids in _parse_yaml_era_groups(path).items():
            result[era].extend(iids)
    return result


def _build_era_map() -> dict[str, Any]:
    critters_by_era = _parse_yaml_era_groups(CRITTERS_PATH)
    structures_by_era = _parse_yaml_era_groups(STRUCTURES_PATH)
    bk: dict[str, list[str]] = {era: [] for era in _ERA_ORDER}
    for path in (BUILDINGS_PATH, KNOWLEDGE_PATH):
        for era, iids in _parse_yaml_era_groups(path).items():
            bk[era].extend(iids)
    return {
        "eras": _ERA_ORDER,
        "info": _ERA_INFO,
        "critters": critters_by_era,
        "structures": structures_by_era,
        "buildings_knowledge": bk,
    }


def _write_ai_waves(waves_with_era: list[dict[str, Any]]) -> str:
    header = (
        "# ============================================================\n"
        "# AI Hardcoded Wave Definitions\n"
        "# ============================================================\n"
        "# Each entry defines an army the AI will send when the\n"
        "# defender matches ALL trigger conditions.\n"
        "#\n"
        "# Entries are evaluated IN ORDER.  The LAST matching entry\n"
        "# wins  (most-specific entries should go last).\n"
        "# If no entry matches, the adaptive heuristic is used.\n"
        "#\n"
        "# ── Trigger fields (all optional, default = always true) ────\n"
        "#   items:    list of building/knowledge IIDs that must ALL be\n"
        "#             completed by the defender (remaining_effort == 0)\n"
        "#   citizen:  defender must have at least this many citizens\n"
        "#\n"
        "# ── Wave fields ─────────────────────────────────────────────\n"
        "#   critter:  critter IID (matched case-insensitively)\n"
        "#   slots:    number of critters in this wave\n"
        "#\n"
        "# ── Optional top-level fields ───────────────────────────────\n"
        "#   travel_time: travel duration in seconds before the attack\n"
        "#                arrives (overrides ai_travel_seconds from\n"
        "#                game.yaml).  Omit to use the default.\n"
        "#\n"
        "# ── Progression overview ────────────────────────────────────\n"
        "#   Steinzeit      →  SLAVE / WARRIOR / SCOUT\n"
        "#   Neolithikum    →  CLUBMAN / SCOUT / WARRIOR\n"
        "#   Bronzezeit     →  BOWMAN / SWORDMAN / CHARIOT\n"
        "#   Eisenzeit      →  PIKENEER / HORSEMAN_FAST / LEGIONARY\n"
        "#   Mittelalter    →  CRUSADER / KNIGHT / SAMURAI / SIEGE_RAM\n"
        "#   Renaissance    →  NINJA / MUSKETEER / DRAGOONER\n"
        "#   Industrialis.  →  SOLDIER / MOTORBIKE / SMALL_TANK / SIEGE_TANK\n"
        "#   Moderne        →  SPECOPS / HELI\n"
        "#   Zukunft        →  MECH_WARRIOR\n"
        "# ============================================================\n"
        "\n"
        "armies:\n"
    )
    groups: dict[str, list[dict[str, Any]]] = {}
    for w in waves_with_era:
        era = w.get("era", "stone")
        groups.setdefault(era, []).append(w)
    lines = [header]
    for era in _ERA_ORDER:
        if era not in groups:
            continue
        info = _ERA_INFO.get(era, "")
        comment_key = _ERA_COMMENT_KEY.get(era, era.upper())
        lines.append(f"  # {'─' * 58}")
        lines.append(f"  #   {comment_key}  ({info})")
        lines.append(f"  # {'─' * 58}")
        lines.append("")
        for w in groups[era]:
            lines.append(f"  - name: {json.dumps(w['name'], ensure_ascii=False)}")
            if "travel_time" in w:
                lines.append(f"    travel_time: {int(w['travel_time'])}")
            if "siege_time" in w:
                lines.append(f"    siege_time: {int(w['siege_time'])}")
            if w.get("time_between") is not None:
                lines.append(f"    time_between: {int(w['time_between'])}")
            if "trigger" in w:
                trig = w["trigger"]
                lines.append("    trigger:")
                if "items" in trig:
                    items_str = ", ".join(trig["items"])
                    lines.append(f"      items: [{items_str}]")
                if "citizen" in trig:
                    lines.append(f"      citizen: {trig['citizen']}")
            lines.append("    waves:")
            for unit in w.get("waves", []):
                lines.append(f"      - critter: {unit['critter']}")
                lines.append(f"        slots: {unit['slots']}")
            lines.append("")
    return "\n".join(lines)


def _parse_items_full(path: Path) -> list[dict[str, Any]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    result = []
    for iid, item in data.items():
        if not isinstance(item, dict):
            continue
        result.append({
            "iid": iid,
            "era": item.get("era", "stone"),
            "name": item.get("name", iid),
            "effort": item.get("effort", 0),
            "costs": item.get("costs", {}),
            "requirements": item.get("requirements", []),
            "effects": item.get("effects", {}),
        })
    return result


def _save_efforts(path: Path, updates: dict[str, Any]) -> None:
    lines = path.read_text(encoding="utf-8").split("\n")
    result = []
    current_iid = None
    effort_done = False
    for line in lines:
        m = _ITEM_IID_RE.match(line)
        if m:
            current_iid = m.group(1)
            effort_done = False
            result.append(line)
            continue
        if current_iid in updates and not effort_done:
            em = re.match(r'^(\s+effort:\s*)\d+(.*)', line)
            if em:
                line = f"{em.group(1)}{int(updates[current_iid])}{em.group(2)}"
                effort_done = True
        result.append(line)
    path.write_text("\n".join(result), encoding="utf-8")


def _save_gold_costs(path: Path, updates: dict[str, Any]) -> None:
    lines = path.read_text(encoding="utf-8").split("\n")
    result = []
    current_iid = None
    in_costs = False
    for line in lines:
        m = _ITEM_IID_RE.match(line)
        if m:
            current_iid = m.group(1)
            in_costs = False
            result.append(line)
            continue
        if current_iid in updates:
            im = re.match(r'^(\s+costs:\s*\{(?:[^}]*,\s*)?gold:\s*)\d+(\s*(?:,\s*[^}]*)?\}.*)', line)
            if im:
                line = f"{im.group(1)}{int(updates[current_iid])}{im.group(2)}"
                result.append(line)
                continue
            im2 = re.match(r'^(\s+costs:\s*\{gold:\s*)\d+(\}.*)', line)
            if im2:
                line = f"{im2.group(1)}{int(updates[current_iid])}{im2.group(2)}"
                result.append(line)
                continue
            if re.match(r'^\s+costs:\s*$', line):
                in_costs = True
                result.append(line)
                continue
            if in_costs:
                gm = re.match(r'^(\s+gold:\s*)\d+(.*)', line)
                if gm:
                    line = f"{gm.group(1)}{int(updates[current_iid])}{gm.group(2)}"
                    in_costs = False
                    result.append(line)
                    continue
                if re.match(r'^\s{0,4}\S', line):
                    in_costs = False
        result.append(line)
    path.write_text("\n".join(result), encoding="utf-8")


def _resolve_sprite(web_dir: Path, animation: str) -> str:
    if not animation:
        return ""
    folder = animation.lstrip("/")
    name = folder.split("/")[-1]
    for ext in _SPRITE_EXTS:
        candidate = web_dir / folder / (name + ext)
        if candidate.exists():
            return f"{folder}/{name}{ext}"
    return f"{folder}/{name}.png"


def _parse_critters(web_dir: Path, path: Path) -> list[dict[str, Any]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    result = []
    for iid, item in data.items():
        if not isinstance(item, dict):
            continue
        animation = item.get("animation", "")
        result.append({
            "iid": iid, "era": item.get("era", "stone"),
            "name": item.get("name", iid),
            "speed": item.get("speed", 0), "health": item.get("health", 1),
            "value": item.get("value", 0), "damage": item.get("damage", 1),
            "armour": item.get("armour", 0), "slots": item.get("slots", 1),
            "time_between": item.get("time_between", 2000),
            "is_boss": item.get("is_boss", False),
            "scale": item.get("scale", 1),
            "requirements": item.get("requirements", []),
            "animation": animation,
            "sprite": _resolve_sprite(web_dir, animation),
            "spawn_on_death": item.get("spawn_on_death") or {},
        })
    return result


def _parse_structures(path: Path) -> list[dict[str, Any]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    result = []
    for iid, item in data.items():
        if not isinstance(item, dict):
            continue
        result.append({
            "iid": iid, "era": item.get("era", "stone"),
            "name": item.get("name", iid),
            "damage": item.get("damage", 0), "range": item.get("range", 1),
            "reload_time": item.get("reload_time", 2000),
            "shot_speed": item.get("shot_speed", 1),
            "shot_type": item.get("shot_type", "normal"),
            "effects": item.get("effects") or {},
            "sprite": item.get("sprite", ""),
            "costs": item.get("costs", {}),
            "requirements": item.get("requirements", []),
        })
    return result


def _fmt_yaml(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float) and v == int(v):
        return str(int(v))
    if isinstance(v, (int, float)):
        return f"{v:.10g}"
    return str(v)


def _patch_yaml_inplace(path: Path, changes: dict[str, Any]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    key_re = re.compile(r'^([A-Z][A-Z0-9_]*):\s*(?:#.*)?$')
    key_positions: dict[str, int] = {}
    for i, line in enumerate(lines):
        m = key_re.match(line.rstrip("\r\n"))
        if m:
            key_positions[m.group(1)] = i
    sorted_positions = sorted(key_positions.values())

    def block_end(start: int) -> int:
        for pos in sorted_positions:
            if pos > start:
                return pos
        return len(lines)

    def fmt(v: Any) -> str:
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, int):
            return str(v)
        if isinstance(v, float):
            return str(int(v)) if v == int(v) else f"{v:.10g}"
        return str(v)

    for iid, fields in changes.items():
        if iid not in key_positions:
            continue
        start = key_positions[iid]
        end = block_end(start)
        for field, value in fields.items():
            if '.' in field:
                parent, child = field.split('.', 1)
                dot_re = re.compile(
                    r'^(\s+' + re.escape(parent) + r':\s*\{[^}]*\b'
                    + re.escape(child) + r':\s*)([^,}]+)(.*)$'
                )
                for j in range(start + 1, end):
                    m = dot_re.match(lines[j].rstrip("\r\n"))
                    if m:
                        eol = "\n" if lines[j].endswith("\n") else ""
                        lines[j] = m.group(1) + fmt(value) + m.group(3) + eol
                        break
                continue
            field_re = re.compile(r'^(\s+' + re.escape(field) + r':\s*).*$')
            for j in range(start + 1, end):
                m = field_re.match(lines[j].rstrip("\r\n"))
                if m:
                    eol = "\n" if lines[j].endswith("\n") else ""
                    lines[j] = m.group(1) + fmt(value) + eol
                    break
    path.write_text("".join(lines), encoding="utf-8")


def _add_effect_to_yaml(path: Path, iid: str, eff_key: str, value: Any) -> bool:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    key_re = re.compile(r'^([A-Z][A-Z0-9_]*):\s*(?:#.*)?$')
    key_positions: dict[str, int] = {}
    for i, line in enumerate(lines):
        m = key_re.match(line.rstrip("\r\n"))
        if m:
            key_positions[m.group(1)] = i
    if iid not in key_positions:
        return False
    start = key_positions[iid]
    sorted_pos = sorted(key_positions.values())
    end = next((p for p in sorted_pos if p > start), len(lines))
    new_line = f"    {eff_key}: {_fmt_yaml(value)}\n"
    effects_idx: int | None = None
    for j in range(start + 1, end):
        if re.match(r'^\s{2}effects:', lines[j]):
            effects_idx = j
            break
    if effects_idx is None:
        lines.insert(end, new_line)
        lines.insert(end, "  effects:\n")
    else:
        if re.match(r'^\s{2}effects:\s*(\{[^}]*\})?\s*$', lines[effects_idx].rstrip('\r\n')):
            lines[effects_idx] = "  effects:\n"
        insert_at = effects_idx
        for j in range(effects_idx + 1, end):
            ln = lines[j]
            if ln.startswith("    ") and not ln.lstrip().startswith("#"):
                insert_at = j
            elif not ln.strip():
                continue
            else:
                break
        lines.insert(insert_at + 1, new_line)
    path.write_text("".join(lines), encoding="utf-8")
    return True


def _remove_effect_from_yaml(path: Path, iid: str, eff_key: str) -> bool:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    key_re = re.compile(r'^([A-Z][A-Z0-9_]*):\s*(?:#.*)?$')
    key_positions: dict[str, int] = {}
    for i, line in enumerate(lines):
        m = key_re.match(line.rstrip("\r\n"))
        if m:
            key_positions[m.group(1)] = i
    if iid not in key_positions:
        return False
    start = key_positions[iid]
    sorted_pos = sorted(key_positions.values())
    end = next((p for p in sorted_pos if p > start), len(lines))
    eff_re = re.compile(r'^\s{4}' + re.escape(eff_key) + r':\s')
    effects_header_re = re.compile(r'^(\s{2}effects:)\s*$')
    for j in range(start + 1, end):
        if eff_re.match(lines[j]):
            del lines[j]
            end2 = next((p for p in sorted_pos if p > start), len(lines))
            has_remaining = any(
                re.match(r'^\s{4}\S', lines[k]) for k in range(start + 1, end2)
            )
            if not has_remaining:
                for k in range(start + 1, end2):
                    m = effects_header_re.match(lines[k].rstrip("\r\n"))
                    if m:
                        eol = "\n" if lines[k].endswith("\n") else ""
                        lines[k] = m.group(1) + " {}" + eol
                        break
            path.write_text("".join(lines), encoding="utf-8")
            return True
    return False


def _patch_requirements_in_yaml(path: Path, iid: str, new_reqs: list[str]) -> bool:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    key_re = re.compile(r'^([A-Z][A-Z0-9_]*):\s*(?:#.*)?$')
    key_positions: dict[str, int] = {}
    for i, line in enumerate(lines):
        m = key_re.match(line.rstrip("\r\n"))
        if m:
            key_positions[m.group(1)] = i
    if iid not in key_positions:
        return False
    start = key_positions[iid]
    sorted_pos = sorted(key_positions.values())
    end = next((p for p in sorted_pos if p > start), len(lines))
    req_re = re.compile(r'^(\s+requirements:\s*).*$')
    new_val = "[" + ", ".join(new_reqs) + "]" if new_reqs else "[]"
    for j in range(start + 1, end):
        m = req_re.match(lines[j].rstrip("\r\n"))
        if m:
            lines[j] = m.group(1) + new_val + "\n"
            path.write_text("".join(lines), encoding="utf-8")
            return True
    indent = "  "
    lines.insert(start + 1, f"{indent}requirements: {new_val}\n")
    path.write_text("".join(lines), encoding="utf-8")
    return True


def _set_era_field_in_yaml(path: Path, iid: str, era: str) -> None:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    key_re = re.compile(r'^([A-Z][A-Z0-9_]*):\s*(?:#.*)?$')
    start = None
    next_start = None
    for i, line in enumerate(lines):
        m = key_re.match(line.rstrip("\r\n"))
        if m:
            if m.group(1) == iid:
                start = i
            elif start is not None:
                next_start = i
                break
    if start is None:
        return
    end = next_start if next_start is not None else len(lines)
    era_re = re.compile(r'^(\s+era:\s*).*$')
    for j in range(start + 1, end):
        m = era_re.match(lines[j].rstrip("\r\n"))
        if m:
            eol = "\n" if lines[j].endswith("\n") else ""
            lines[j] = m.group(1) + era + eol
            path.write_text("".join(lines), encoding="utf-8")
            return
    indent = "  "
    lines.insert(start + 1, f"{indent}era: {era}\n")
    path.write_text("".join(lines), encoding="utf-8")


def _get_map_power_upgrades() -> Any:
    global _map_power_upgrades
    if _map_power_upgrades is None:
        from gameserver.main import load_configuration
        from gameserver.engine.upgrade_provider import UpgradeProvider
        cfg = load_configuration(config_dir=str(_CONFIG_DIR))
        up = UpgradeProvider()
        up.load(cfg.items)
        _map_power_upgrades = (up, getattr(cfg.game, "starting_max_life", 10.0))
    return _map_power_upgrades


def _get_structure_era_map() -> dict[str, str]:
    global _structure_era_map
    if _structure_era_map is None:
        from gameserver.util.eras import ERA_LABELS_EN
        data = yaml.safe_load(STRUCTURES_PATH.read_text(encoding="utf-8")) or {}
        _structure_era_map = {}
        for iid, item in data.items():
            if isinstance(item, dict):
                era = item.get("era") or "stone"
                _structure_era_map[iid] = ERA_LABELS_EN.get(era, era)
    return _structure_era_map


def _compute_map_age_pct(m: dict[str, Any]) -> dict[str, float]:
    tower_era = _get_structure_era_map()
    counts: dict[str, int] = {}
    for t in (m.get("hex_map") or []):
        tt = t.get("type", "")
        if isinstance(tt, dict):
            tt = tt.get("type", "")
        if tt in NON_TOWER or not tt:
            continue
        era_label = tower_era.get(tt)
        if era_label:
            counts[era_label] = counts.get(era_label, 0) + 1
    total = sum(counts.values())
    if not total:
        return {}
    return {era: round(cnt / total * 100, 1) for era, cnt in counts.items()}


def _compute_map_defense_power(m: dict[str, Any]) -> float:
    from gameserver.engine.power_service import defense_power
    from gameserver.engine.hex_pathfinding import find_path_from_spawn_to_castle
    from gameserver.models.empire import Empire
    upgrades, default_life = _get_map_power_upgrades()
    hex_map = {f"{t['q']},{t['r']}": {"type": t.get("type", "empty")} for t in (m.get("hex_map") or [])}
    empire = Empire(uid=0, name="")
    empire.hex_map = hex_map
    empire.max_life = float(m.get("life") or default_life)
    try:
        from gameserver.engine.hex_pathfinding import find_path_from_spawn_to_castle
        str_map = {k: (v.get("type") or "empty") for k, v in hex_map.items()}
        path = find_path_from_spawn_to_castle(str_map)
        path_length = len(path) - 1 if path else None
    except Exception:
        # Pathfinding may fail on incomplete/malformed maps — treat as unknown length
        path_length = None
    return defense_power(empire, upgrades, path_length=path_length)


# ── NoCacheStaticFiles ────────────────────────────────────────────────────────

class NoCacheStaticFiles(StaticFiles):
    """StaticFiles that sets no-cache headers on every response."""

    async def get_response(self, path: str, scope: Any) -> Any:
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0, private"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


# ── Route registration ────────────────────────────────────────────────────────

def register_web_routes(app: FastAPI, web_dir: Path) -> None:
    """Register all web-client routes on *app*, then mount static files.

    Must be called AFTER all game API routes are registered so the
    catch-all static mount doesn't shadow them.
    """

    # Ensure gameserver package is importable (needed for army_generator import)
    _src = str(Path(__file__).resolve().parent.parent.parent)
    if _src not in sys.path:
        sys.path.insert(0, _src)

    from gameserver.util.army_generator import (
        generate_army as _gen_army,
        parse_critter_era_groups as _parse_critter_era_groups,
        parse_slot_by_iid as _parse_slot_by_iid,
    )

    def _generate_army(era: str, seed: int) -> dict[str, Any]:
        raw_cfg = yaml.safe_load(GAME_CONFIG_PATH.read_text(encoding="utf-8")) or {}
        ai_generator_cfg = raw_cfg.get("ai_generator", {})
        critter_era_groups = _parse_critter_era_groups(CRITTERS_PATH)
        slot_by_iid = _parse_slot_by_iid(CRITTERS_PATH)
        result = _gen_army(
            era_internal=era,
            ai_generator_cfg=ai_generator_cfg,
            critter_era_groups=critter_era_groups,
            slot_by_iid=slot_by_iid,
            seed=seed,
        )
        return {"era": era, "seed": seed, "name": result["name"], "waves": result["waves"]}

    @app.get("/health")
    async def health_check() -> Any:
        return {"status": "ok", "service": "Relics & Rockets"}

    @app.get("/api/ai-waves")
    async def get_ai_waves() -> Any:
        try:
            return JSONResponse({"waves": _parse_ai_waves()})
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)

    @app.post("/api/ai-waves")
    async def save_ai_waves(request: Request) -> Any:
        try:
            body = await request.json()
            AI_WAVES_PATH.write_text(_write_ai_waves(body.get("waves", [])), encoding="utf-8")
            return JSONResponse({"success": True})
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)

    @app.get("/api/era-items")
    async def get_era_items() -> Any:
        try:
            return JSONResponse({"eras": _parse_era_items()})
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)

    @app.get("/api/era-map")
    async def get_era_map() -> Any:
        try:
            return JSONResponse(_build_era_map())
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)

    @app.get("/api/prices")
    async def get_prices() -> Any:
        try:
            raw = yaml.safe_load(GAME_CONFIG_PATH.read_text(encoding="utf-8")) or {}
            return JSONResponse(raw.get("prices", {}))
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)

    @app.post("/api/prices")
    async def save_prices(request: Request) -> Any:
        try:
            prices = await request.json()
            raw = yaml.safe_load(GAME_CONFIG_PATH.read_text(encoding="utf-8")) or {}
            raw["prices"] = prices
            GAME_CONFIG_PATH.write_text(
                yaml.dump(raw, default_flow_style=False, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            return JSONResponse({"success": True})
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)

    @app.get("/api/ai-generator")
    async def get_ai_generator() -> Any:
        try:
            raw = yaml.safe_load(GAME_CONFIG_PATH.read_text(encoding="utf-8")) or {}
            return JSONResponse(raw.get("ai_generator", {}))
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)

    @app.post("/api/ai-generator")
    async def save_ai_generator(request: Request) -> Any:
        try:
            data = await request.json()
            raw = yaml.safe_load(GAME_CONFIG_PATH.read_text(encoding="utf-8")) or {}
            raw["ai_generator"] = data
            GAME_CONFIG_PATH.write_text(
                yaml.dump(raw, default_flow_style=False, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            return JSONResponse({"success": True})
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)

    @app.get("/api/barbarians-aggressiveness")
    async def get_barbarians_aggressiveness() -> Any:
        try:
            raw = yaml.safe_load(GAME_CONFIG_PATH.read_text(encoding="utf-8")) or {}
            return JSONResponse(raw.get("barbarians_aggressiveness", {}))
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)

    @app.post("/api/barbarians-aggressiveness")
    async def save_barbarians_aggressiveness(request: Request) -> Any:
        try:
            data = await request.json()
            raw = yaml.safe_load(GAME_CONFIG_PATH.read_text(encoding="utf-8")) or {}
            raw["barbarians_aggressiveness"] = data
            GAME_CONFIG_PATH.write_text(
                yaml.dump(raw, default_flow_style=False, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            return JSONResponse({"success": True})
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)

    @app.get("/api/ai-generator/generate")
    async def generate_ai_army(era: str, seed: int) -> Any:
        try:
            return JSONResponse(_generate_army(era, seed))
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)

    @app.get("/api/buildings")
    async def get_buildings() -> Any:
        return JSONResponse(_parse_items_full(BUILDINGS_PATH))

    @app.get("/api/knowledge")
    async def get_knowledge() -> Any:
        return JSONResponse(_parse_items_full(KNOWLEDGE_PATH))

    @app.post("/api/buildings")
    async def save_buildings(request: Request) -> Any:
        try:
            _save_efforts(BUILDINGS_PATH, await request.json())
            return JSONResponse({"success": True})
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)

    @app.post("/api/knowledge")
    async def save_knowledge(request: Request) -> Any:
        try:
            _save_efforts(KNOWLEDGE_PATH, await request.json())
            return JSONResponse({"success": True})
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)

    @app.post("/api/buildings-gold")
    async def save_buildings_gold(request: Request) -> Any:
        try:
            _save_gold_costs(BUILDINGS_PATH, await request.json())
            return JSONResponse({"success": True})
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)

    @app.post("/api/knowledge-gold")
    async def save_knowledge_gold(request: Request) -> Any:
        try:
            _save_gold_costs(KNOWLEDGE_PATH, await request.json())
            return JSONResponse({"success": True})
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)

    @app.post("/api/structure-gold")
    async def save_structure_gold(request: Request) -> Any:
        try:
            _save_gold_costs(STRUCTURES_PATH, await request.json())
            return JSONResponse({"success": True})
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)

    @app.get("/api/critter-stats")
    async def get_critter_stats() -> Any:
        return JSONResponse(_parse_critters(web_dir, CRITTERS_PATH))

    @app.patch("/api/critter-stats")
    async def patch_critter_stats(changes: dict[str, Any] = Body(...)) -> Any:
        _patch_yaml_inplace(CRITTERS_PATH, changes)
        return {"ok": True}

    @app.patch("/api/critter-era")
    async def patch_critter_era(changes: dict[str, Any] = Body(...)) -> Any:
        for iid, era in changes.items():
            _set_era_field_in_yaml(CRITTERS_PATH, str(iid), str(era))
        return {"ok": True}

    @app.get("/api/structure-stats")
    async def get_structure_stats() -> Any:
        return JSONResponse(_parse_structures(STRUCTURES_PATH))

    @app.patch("/api/structure-stats")
    async def patch_structure_stats(changes: dict[str, Any] = Body(...)) -> Any:
        _patch_yaml_inplace(STRUCTURES_PATH, changes)
        return {"ok": True}

    @app.patch("/api/building-effects")
    async def patch_building_effects(changes: dict[str, Any] = Body(...)) -> Any:
        _patch_yaml_inplace(BUILDINGS_PATH, changes)
        return {"ok": True}

    @app.patch("/api/knowledge-effects")
    async def patch_knowledge_effects(changes: dict[str, Any] = Body(...)) -> Any:
        _patch_yaml_inplace(KNOWLEDGE_PATH, changes)
        return {"ok": True}

    @app.post("/api/building-effects")
    async def add_building_effect(body: dict[str, Any] = Body(...)) -> Any:
        ok = _add_effect_to_yaml(BUILDINGS_PATH, body["iid"], body["effect"], body["value"])
        return JSONResponse({"ok": ok}, status_code=200 if ok else 404)

    @app.post("/api/knowledge-effects")
    async def add_knowledge_effect(body: dict[str, Any] = Body(...)) -> Any:
        ok = _add_effect_to_yaml(KNOWLEDGE_PATH, body["iid"], body["effect"], body["value"])
        return JSONResponse({"ok": ok}, status_code=200 if ok else 404)

    @app.post("/api/building-effects/remove")
    async def remove_building_effect(body: dict[str, Any] = Body(...)) -> Any:
        ok = _remove_effect_from_yaml(BUILDINGS_PATH, body["iid"], body["effect"])
        return JSONResponse({"ok": ok}, status_code=200 if ok else 404)

    @app.post("/api/knowledge-effects/remove")
    async def remove_knowledge_effect(body: dict[str, Any] = Body(...)) -> Any:
        ok = _remove_effect_from_yaml(KNOWLEDGE_PATH, body["iid"], body["effect"])
        return JSONResponse({"ok": ok}, status_code=200 if ok else 404)

    @app.patch("/api/item-requirements")
    async def patch_item_requirements(body: dict[str, Any] = Body(...)) -> Any:
        results = {}
        yaml_files = [BUILDINGS_PATH, KNOWLEDGE_PATH, CRITTERS_PATH, STRUCTURES_PATH]
        raw_by_path = {p: yaml.safe_load(p.read_text(encoding="utf-8")) or {} for p in yaml_files}
        for iid, reqs in body.items():
            if not isinstance(reqs, list):
                results[iid] = "error: reqs must be a list"
                continue
            reqs = [str(r).strip().upper() for r in reqs if str(r).strip()]
            target = next((p for p, raw in raw_by_path.items() if iid in raw), None)
            if target is None:
                results[iid] = "not found"
                continue
            ok = _patch_requirements_in_yaml(target, iid, reqs)
            results[iid] = "ok" if ok else "error"
        return {"results": results}

    @app.patch("/api/tower-effects/{iid}")
    async def patch_tower_effects(iid: str, body: dict[str, Any] = Body(...)) -> Any:
        new_effects: dict[str, Any] = body.get("effects", {})
        lines = STRUCTURES_PATH.read_text(encoding="utf-8").splitlines()
        iid_idx = next((i for i, ln in enumerate(lines) if ln.startswith(f"{iid}:")), None)
        if iid_idx is None:
            return JSONResponse({"error": f"'{iid}' not found"}, status_code=404)
        if new_effects:
            pairs = ", ".join(f"{k}: {v}" for k, v in new_effects.items())
            new_val = f"  effects: {{{pairs}}}"
        else:
            new_val = "  effects: {}"
        for i in range(iid_idx + 1, len(lines)):
            line = lines[i]
            if line and not line.startswith(" ") and not line.startswith("#"):
                break
            if line.lstrip().startswith("effects:"):
                rest = line[line.index("effects:"):]
                hi = rest.find("#")
                comment = ("   " + rest[hi:]) if hi != -1 else ""
                lines[i] = new_val + comment
                STRUCTURES_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
                return JSONResponse({"ok": True})
        return JSONResponse({"error": "effects line not found"}, status_code=500)

    @app.get("/api/artifacts")
    async def get_artifacts() -> Any:
        try:
            raw = yaml.safe_load(ARTIFACTS_PATH.read_text(encoding="utf-8")) or {}
            result = [
                {"iid": iid, "name": data.get("name", ""), "description": data.get("description", ""),
                 "type": data.get("type", ""), "effects": data.get("effects") or {}}
                for iid, data in raw.items() if isinstance(data, dict)
            ]
            return JSONResponse(result)
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)

    @app.post("/api/artifacts")
    async def save_artifacts(request: Request) -> Any:
        try:
            items = await request.json()
            raw = {}
            for item in items:
                iid = item["iid"].strip().upper().replace(" ", "_")
                raw[iid] = {
                    "name": item.get("name", ""), "description": item.get("description", ""),
                    "type": item.get("type", ""), "effects": item.get("effects") or {},
                }
            header = "# Artifact definitions (collectible passive effect items)\n# effects: passive bonuses while the artifact is owned\n# description: flavour text\n\n"
            ARTIFACTS_PATH.write_text(
                header + yaml.dump(raw, default_flow_style=False, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            return JSONResponse({"success": True})
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)

    @app.get("/api/admin/catalog")
    async def get_catalog() -> Any:
        def _load(path: Path) -> dict[str, Any]:
            with open(path) as f:
                raw = yaml.safe_load(f) or {}
            return {
                iid: {"name": item.get("name", iid), "effects": item.get("effects") or {}}
                for iid, item in raw.items()
            }
        return JSONResponse({"buildings": _load(BUILDINGS_PATH), "knowledge": _load(KNOWLEDGE_PATH)})

    @app.get("/api/sprite-files")
    async def list_sprite_files() -> Any:
        tools_dir = web_dir / "tools"
        files = sorted(
            f.name for f in tools_dir.iterdir()
            if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png")
            and ".__orig" not in f.stem
        )
        return JSONResponse({"files": files})

    @app.get("/api/maps")
    async def list_maps() -> Any:
        maps_dir = web_dir / "assets" / "sprites" / "maps"
        if not maps_dir.is_dir():
            return JSONResponse({"maps": []})
        files = sorted(
            [{"name": f.name, "url": f"/assets/sprites/maps/{f.name}"}
             for f in maps_dir.iterdir()
             if f.is_file() and f.suffix.lower() in (".png", ".webp")],
            key=lambda x: x["name"]
        )
        return JSONResponse({"maps": files})

    @app.get("/api/critters")
    async def list_critters() -> Any:
        GIF_NAMES = {"forward": "front.gif", "left": "left.gif", "right": "right.gif", "backward": "back.gif"}
        result = []

        def _scan_dir(sprite_dir: "Path", name_prefix: str = "") -> None:
            if not sprite_dir.is_dir():
                return
            for d in sorted(sprite_dir.iterdir()):
                if not d.is_dir():
                    continue
                name = name_prefix + d.name
                base = f"/{d.relative_to(web_dir)}"
                gif_paths = {dir_: d / fname for dir_, fname in GIF_NAMES.items()}
                if all(p.exists() for p in gif_paths.values()):
                    result.append({"name": name, "type": "gifs",
                                    "files": {dir_: f"{base}/{fname}" for dir_, fname in GIF_NAMES.items()}})
                    continue
                sheets = sorted(f.name for f in d.iterdir() if f.suffix.lower() in (".png", ".webp") and "_splash" not in f.name)
                if sheets:
                    result.append({"name": name, "type": "spritesheet", "file": f"{base}/{sheets[0]}"})

        _scan_dir(web_dir / "assets" / "sprites" / "critters")
        _scan_dir(web_dir / "assets" / "sprites" / "ruler", name_prefix="ruler_")
        return JSONResponse({"critters": result})

    @app.get("/api/saved-maps")
    async def list_saved_maps() -> Any:
        if not _SAVED_MAPS_PATH.exists():
            return JSONResponse({"maps": [], "life": {}})
        data = yaml.safe_load(_SAVED_MAPS_PATH.read_text()) or {}
        names, life, power, age_pct = [], {}, {}, {}
        for m in (data.get("maps") or []):
            name = m.get("name", m.get("id", "?"))
            names.append(name)
            if m.get("life") is not None:
                life[name] = m["life"]
            try:
                power[name] = round(_compute_map_defense_power(m), 1)
            except Exception:
                # Defense power is derived/optional — skip if map data is incomplete
                pass
            try:
                age_pct[name] = _compute_map_age_pct(m)
            except Exception:
                # Age distribution is derived/optional — skip if map data is incomplete
                pass
        return JSONResponse({"maps": names, "life": life, "power": power, "age_pct": age_pct})

    @app.put("/api/tools/map-life")
    async def set_map_life(payload: dict[str, Any]) -> Any:
        map_name = payload.get("map_name", "")
        life = payload.get("life")
        if not map_name or life is None:
            return JSONResponse({"ok": False, "error": "map_name and life required"}, status_code=400)
        try:
            life = float(life)
        except (TypeError, ValueError):
            return JSONResponse({"ok": False, "error": "life must be a number"}, status_code=400)
        if not _SAVED_MAPS_PATH.exists():
            return JSONResponse({"ok": False, "error": "saved_maps.yaml not found"}, status_code=404)
        data = yaml.safe_load(_SAVED_MAPS_PATH.read_text()) or {}
        found = False
        for m in (data.get("maps") or []):
            if m.get("name", m.get("id", "")) == map_name:
                m["life"] = life
                found = True
                break
        if not found:
            return JSONResponse({"ok": False, "error": f"Map '{map_name}' not found"}, status_code=404)
        _SAVED_MAPS_PATH.write_text(yaml.dump(data, allow_unicode=True, sort_keys=False))
        return JSONResponse({"ok": True})

    @app.get("/api/tools/sim-map")
    async def sim_map(map_name: str, era: str, n: int) -> Any:
        import asyncio
        import tempfile
        script = Path(__file__).resolve().parent.parent.parent.parent.parent / "sim_map.py"
        python = Path(sys.executable)
        out_fd, out_path = tempfile.mkstemp(suffix=".jsonl", prefix="sim_map_")
        os.close(out_fd)

        async def generate() -> Any:
            proc = await asyncio.create_subprocess_exec(
                str(python), str(script), map_name, era, str(n), out_path,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
                cwd=str(script.parent),
            )
            try:
                with open(out_path, "r") as f:
                    while True:
                        line = f.readline()
                        if line:
                            yield f"data: {line.rstrip()}\n\n"
                        else:
                            try:
                                await asyncio.wait_for(asyncio.shield(proc.wait()), timeout=0.1)
                                for line in f:
                                    yield f"data: {line.rstrip()}\n\n"
                                break
                            except asyncio.TimeoutError:
                                await asyncio.sleep(0.05)
            finally:
                try:
                    os.unlink(out_path)
                except OSError:
                    pass

        return StreamingResponse(generate(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    # ── Static files (must be LAST — catch-all) ───────────────────────────────
    app.mount("/", NoCacheStaticFiles(directory=str(web_dir), html=True), name="static")
    log.info("Web routes registered, static files served from %s", web_dir)
