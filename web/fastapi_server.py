#!/usr/bin/env python3
"""
FastAPI server for serving the E3 web client.

Serves static files with proper cache control headers for development.
Much faster and more robust than SimpleHTTPServer.

Usage:
    python3 fastapi_server.py [--port 8000] [--host 0.0.0.0] [--no-cache]
"""

import argparse
import json
import logging
import logging.handlers
import os
import re
import sys
from pathlib import Path

import yaml
from fastapi import FastAPI, Request, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response, JSONResponse
from starlette.datastructures import MutableHeaders
import uvicorn

AI_WAVES_PATH = Path(__file__).parent.parent / "python_server" / "config" / "ai_waves.yaml"
GAME_CONFIG_PATH = Path(__file__).parent.parent / "python_server" / "config" / "game.yaml"
BUILDINGS_PATH = Path(__file__).parent.parent / "python_server" / "config" / "buildings.yaml"
KNOWLEDGE_PATH = Path(__file__).parent.parent / "python_server" / "config" / "knowledge.yaml"
CRITTERS_PATH = Path(__file__).parent.parent / "python_server" / "config" / "critters.yaml"
STRUCTURES_PATH = Path(__file__).parent.parent / "python_server" / "config" / "structures.yaml"

_ITEM_IID_RE = re.compile(r'^([A-Z][A-Z0-9_]+):')

# ERA_PATTERNS kept only for ai_waves.yaml which has no per-entry era fields
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


def _parse_ai_waves():
    """Read ai_waves.yaml, annotate each wave with its era."""
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
    """Build {era_name: [iid, ...]} from explicit era: fields in a YAML file."""
    result: dict[str, list[str]] = {era: [] for era in _ERA_ORDER}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    for iid, item in data.items():
        if not isinstance(item, dict):
            continue
        era = item.get("era", _ERA_ORDER[0])
        if era in result:
            result[era].append(iid)
    return result


def _parse_era_items() -> dict:
    """Return {era_name: [iid, ...]} from buildings.yaml + knowledge.yaml."""
    result: dict[str, list[str]] = {era: [] for era in _ERA_ORDER}
    for path in (BUILDINGS_PATH, KNOWLEDGE_PATH):
        for era, iids in _parse_yaml_era_groups(path).items():
            result[era].extend(iids)
    return result


def _build_era_map() -> dict:
    """Return comprehensive era map for all YAML categories."""
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


def _write_ai_waves(waves_with_era: list[dict]) -> str:
    """Serialize waves back to YAML preserving era comment headers."""
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

    # Group by era, preserving insertion order
    groups: dict[str, list] = {}
    for w in waves_with_era:
        era = w.get("era", "stone")
        groups.setdefault(era, []).append(w)

    # Map lowercase English era keys → YAML comment markers used in ai_waves.yaml
    _ERA_COMMENT_KEY = {
        "stone": "STEINZEIT", "neolithic": "NEOLITHIKUM", "bronze": "BRONZEZEIT",
        "iron": "EISENZEIT", "middle_ages": "MITTELALTER", "renaissance": "RENAISSANCE",
        "industrial": "INDUSTRIALISIERUNG", "modern": "MODERNE", "future": "ZUKUNFT",
    }

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

# Setup logging — rotating file + stdout
_web_fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')
_web_root = logging.getLogger()
_web_root.setLevel(logging.INFO)
_web_file = logging.handlers.TimedRotatingFileHandler(
    "webserver.log", when="midnight", backupCount=14, utc=True, encoding="utf-8"
)
_web_file.setFormatter(_web_fmt)
_web_root.addHandler(_web_file)
_web_stream = logging.StreamHandler()
_web_stream.setFormatter(_web_fmt)
_web_root.addHandler(_web_stream)
log = logging.getLogger(__name__)

# Determine the web directory (where this script is located)
WEB_DIR = Path(__file__).parent.resolve()

# Global flag for cache control (set by main() before app starts)
NO_CACHE = False


class NoCacheASGIMiddleware:
    """ASGI middleware that removes cache headers at the response level."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start" and NO_CACHE:
                # Intercept the response headers before they're sent
                headers = MutableHeaders(scope=message)
                # Remove conditional caching headers
                if "etag" in headers:
                    del headers["etag"]
                if "last-modified" in headers:
                    del headers["last-modified"]
                # Set no-cache headers
                headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0, private"
                headers["Pragma"] = "no-cache"
                headers["Expires"] = "0"
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)


class NoCacheStaticFiles(StaticFiles):
    """StaticFiles class (now middleware handles caching)."""
    pass


# Create FastAPI app
app = FastAPI(title="E3 Web Client", version="1.0.0")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "E3 Web Client"}



@app.get("/api/ai-waves")
async def get_ai_waves():
    """Return all AI wave definitions annotated with era."""
    try:
        waves = _parse_ai_waves()
        return JSONResponse({"waves": waves})
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.get("/api/era-items")
async def get_era_items():
    """Return all building/knowledge IIDs grouped by era."""
    try:
        return JSONResponse({"eras": _parse_era_items()})
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.get("/api/era-map")
async def get_era_map():
    """Return era order + item IIDs per era for all YAML categories."""
    try:
        return JSONResponse(_build_era_map())
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.post("/api/ai-waves")
async def save_ai_waves(request: Request):
    """Save updated AI wave definitions back to the YAML file."""
    try:
        body = await request.json()
        waves = body.get("waves", [])
        yaml_text = _write_ai_waves(waves)
        AI_WAVES_PATH.write_text(yaml_text, encoding="utf-8")
        return JSONResponse({"success": True})
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.get("/api/prices")
async def get_prices():
    """Return the prices section from game.yaml."""
    try:
        raw = yaml.safe_load(GAME_CONFIG_PATH.read_text(encoding="utf-8")) or {}
        return JSONResponse(raw.get("prices", {}))
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.post("/api/prices")
async def save_prices(request: Request):
    """Update the prices section in game.yaml (patch only the prices block)."""
    try:
        prices = await request.json()
        raw = yaml.safe_load(GAME_CONFIG_PATH.read_text(encoding="utf-8")) or {}
        raw["prices"] = prices
        # Dump back preserving order — use yaml.dump with default_flow_style=False
        GAME_CONFIG_PATH.write_text(
            yaml.dump(raw, default_flow_style=False, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        return JSONResponse({"success": True})
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.get("/api/ai-generator")
async def get_ai_generator():
    """Return the ai_generator section from game.yaml, keyed by lowercase English era keys."""
    try:
        raw = yaml.safe_load(GAME_CONFIG_PATH.read_text(encoding="utf-8")) or {}
        return JSONResponse(raw.get("ai_generator", {}))
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.post("/api/ai-generator")
async def save_ai_generator(request: Request):
    """Update the ai_generator section in game.yaml."""
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


# ── Army generation ───────────────────────────────────────────────────────────

import sys as _sys
_sys.path.insert(0, str(Path(__file__).parent.parent / "python_server" / "src"))
from gameserver.util.army_generator import (
    generate_army as _gen_army,
    parse_critter_era_groups as _parse_critter_era_groups,
    parse_slot_by_iid as _parse_slot_by_iid,
)


def _generate_army(era: str, seed: int) -> dict:
    """Generate an AI army for *era* (lowercase English era key) using the shared generator."""
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


@app.get("/api/ai-generator/generate")
async def generate_ai_army(era: str, seed: int):
    """Generate an AI army for the given era and seed."""
    try:
        return JSONResponse(_generate_army(era, seed))
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


def _parse_items_full(path: Path) -> list[dict]:
    """Parse buildings/knowledge YAML → list of items annotated with era."""
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


def _save_efforts(path: Path, updates: dict) -> None:
    """Patch effort values in a YAML file, preserving all comments."""
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


@app.get("/api/buildings")
async def get_buildings():
    return JSONResponse(_parse_items_full(BUILDINGS_PATH))


@app.get("/api/knowledge")
async def get_knowledge():
    return JSONResponse(_parse_items_full(KNOWLEDGE_PATH))


@app.post("/api/buildings")
async def save_buildings(request: Request):
    try:
        updates = await request.json()  # {iid: effort, ...}
        _save_efforts(BUILDINGS_PATH, updates)
        return JSONResponse({"success": True})
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.post("/api/knowledge")
async def save_knowledge(request: Request):
    try:
        updates = await request.json()
        _save_efforts(KNOWLEDGE_PATH, updates)
        return JSONResponse({"success": True})
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


def _save_gold_costs(path: Path, updates: dict) -> None:
    """Patch gold cost values in a YAML file, preserving all comments.
    updates: {iid: gold_value, ...}
    Handles both inline `costs: {gold: N}` and block-style costs sections.
    """
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
            # Inline: costs: {gold: 123}
            im = re.match(r'^(\s+costs:\s*\{(?:[^}]*,\s*)?gold:\s*)\d+(\s*(?:,\s*[^}]*)?\}.*)', line)
            if im:
                line = f"{im.group(1)}{int(updates[current_iid])}{im.group(2)}"
                result.append(line)
                continue
            # Inline costs with only gold: costs: {gold: 123}
            im2 = re.match(r'^(\s+costs:\s*\{gold:\s*)\d+(\}.*)', line)
            if im2:
                line = f"{im2.group(1)}{int(updates[current_iid])}{im2.group(2)}"
                result.append(line)
                continue
            # Block-style: detect `costs:` line
            if re.match(r'^\s+costs:\s*$', line):
                in_costs = True
                result.append(line)
                continue
            # Block-style gold line inside costs block
            if in_costs:
                gm = re.match(r'^(\s+gold:\s*)\d+(.*)', line)
                if gm:
                    line = f"{gm.group(1)}{int(updates[current_iid])}{gm.group(2)}"
                    in_costs = False
                    result.append(line)
                    continue
                # leaving costs block if indent drops
                if re.match(r'^\s{0,4}\S', line):
                    in_costs = False
        result.append(line)
    path.write_text("\n".join(result), encoding="utf-8")


@app.post("/api/buildings-gold")
async def save_buildings_gold(request: Request):
    try:
        updates = await request.json()  # {iid: gold, ...}
        _save_gold_costs(BUILDINGS_PATH, updates)
        return JSONResponse({"success": True})
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.post("/api/knowledge-gold")
async def save_knowledge_gold(request: Request):
    try:
        updates = await request.json()  # {iid: gold, ...}
        _save_gold_costs(KNOWLEDGE_PATH, updates)
        return JSONResponse({"success": True})
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


_SPRITE_EXTS = [".png", ".webp", ".jpg"]


def _resolve_sprite(animation: str) -> str:
    """Given an animation folder path, find the actual sprite file with extension."""
    if not animation:
        return ""
    folder = animation.lstrip("/")
    name = folder.split("/")[-1]
    for ext in _SPRITE_EXTS:
        candidate = WEB_DIR / folder / (name + ext)
        if candidate.exists():
            return f"{folder}/{name}{ext}"
    return f"{folder}/{name}.png"  # fallback


def _parse_critters(path: Path) -> list[dict]:
    """Parse critters.yaml → list of critter stats annotated with era."""
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
            "sprite": _resolve_sprite(animation),
            "spawn_on_death": item.get("spawn_on_death") or {},
        })
    return result


def _parse_structures(path: Path) -> list[dict]:
    """Parse structures.yaml → list of tower stats annotated with era."""
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


@app.get("/api/critter-stats")
async def get_critter_stats():
    return JSONResponse(_parse_critters(CRITTERS_PATH))


def _patch_yaml_inplace(path: Path, changes: dict) -> None:
    """Update YAML scalar values in-place, preserving comments and formatting.

    changes = { TOP_LEVEL_KEY: { field: new_value, ... } }
    Dot-notation supported for nested fields (e.g. 'costs.gold').
    Only the value portion of matching lines is replaced; all other content
    (comments, blank lines, era blocks) is left untouched.
    """
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)

    # Locate top-level key start lines (e.g. "SLAVE:", "BASIC_TOWER:")
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

    def fmt(v) -> str:
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
        end   = block_end(start)

        for field, value in fields.items():
            if '.' in field:
                # Dot-notation: update a key inside an inline dict on one line
                # e.g. "effects.burn_dps" → matches "  effects: {...burn_dps: OLD...}"
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
            field_re = re.compile(
                r'^(\s+' + re.escape(field) + r':\s*).*$'
            )
            for j in range(start + 1, end):
                m = field_re.match(lines[j].rstrip("\r\n"))
                if m:
                    eol = "\n" if lines[j].endswith("\n") else ""
                    lines[j] = m.group(1) + fmt(value) + eol
                    break

    path.write_text("".join(lines), encoding="utf-8")


@app.patch("/api/critter-stats")
async def patch_critter_stats(changes: dict = Body(...)):
    """Update critters.yaml in-place. Body: { IID: { field: value } }"""
    _patch_yaml_inplace(CRITTERS_PATH, changes)
    return {"ok": True}


def _set_era_field_in_yaml(path: Path, iid: str, era: str) -> None:
    """Add or update the `era:` field for a critter entry in YAML.

    If the field already exists in the block, replaces it.
    Otherwise inserts it as the first indented field after the IID: line.
    """
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    key_re = re.compile(r'^([A-Z][A-Z0-9_]*):\s*(?:#.*)?$')

    # Find start of IID block and end of block
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

    # Field not found — insert after IID: line
    indent = "  "
    eol = "\n" if lines[start].endswith("\n") else ""
    lines.insert(start + 1, f"{indent}era: {era}\n")
    path.write_text("".join(lines), encoding="utf-8")


@app.patch("/api/critter-era")
async def patch_critter_era(changes: dict = Body(...)):
    """Set era for critters. Body: { IID: 'Eisenzeit', ... }"""
    for iid, era in changes.items():
        _set_era_field_in_yaml(CRITTERS_PATH, str(iid), str(era))
    return {"ok": True}


@app.get("/api/structure-stats")
async def get_structure_stats():
    return JSONResponse(_parse_structures(STRUCTURES_PATH))


@app.patch("/api/structure-stats")
async def patch_structure_stats(changes: dict = Body(...)):
    """Update structures.yaml in-place. Body: { IID: { field: value } }"""
    _patch_yaml_inplace(STRUCTURES_PATH, changes)
    return {"ok": True}


def _fmt_yaml(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float) and v == int(v):
        return str(int(v))
    if isinstance(v, (int, float)):
        return f"{v:.10g}"
    return str(v)


def _add_effect_to_yaml(path: Path, iid: str, eff_key: str, value) -> bool:
    """Add a new effect key/value to an item's effects block in a YAML file."""
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
    """Remove an effect key from an item's effects block in a YAML file."""
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
            # Recalculate end after deletion
            end2 = next((p for p in sorted_pos if p > start), len(lines))
            # Check if the effects block is now empty (no more indented effect lines)
            has_remaining = any(
                re.match(r'^\s{4}\S', lines[k]) for k in range(start + 1, end2)
            )
            if not has_remaining:
                # Find the effects: header line and make it effects: {}
                for k in range(start + 1, end2):
                    m = effects_header_re.match(lines[k].rstrip("\r\n"))
                    if m:
                        eol = "\n" if lines[k].endswith("\n") else ""
                        lines[k] = m.group(1) + " {}" + eol
                        break
            path.write_text("".join(lines), encoding="utf-8")
            return True
    return False


@app.patch("/api/building-effects")
async def patch_building_effects(changes: dict = Body(...)):
    """Update effect values in buildings.yaml. Body: { IID: { effect_key: value } }"""
    _patch_yaml_inplace(BUILDINGS_PATH, changes)
    return {"ok": True}


@app.patch("/api/knowledge-effects")
async def patch_knowledge_effects(changes: dict = Body(...)):
    """Update effect values in knowledge.yaml. Body: { IID: { effect_key: value } }"""
    _patch_yaml_inplace(KNOWLEDGE_PATH, changes)
    return {"ok": True}


@app.post("/api/building-effects")
async def add_building_effect(body: dict = Body(...)):
    """Add an effect key to a building. Body: {iid, effect, value}"""
    ok = _add_effect_to_yaml(BUILDINGS_PATH, body["iid"], body["effect"], body["value"])
    return JSONResponse({"ok": ok}, status_code=200 if ok else 404)


@app.post("/api/knowledge-effects")
async def add_knowledge_effect(body: dict = Body(...)):
    """Add an effect key to a knowledge item. Body: {iid, effect, value}"""
    ok = _add_effect_to_yaml(KNOWLEDGE_PATH, body["iid"], body["effect"], body["value"])
    return JSONResponse({"ok": ok}, status_code=200 if ok else 404)


@app.post("/api/building-effects/remove")
async def remove_building_effect(body: dict = Body(...)):
    """Remove an effect key from a building. Body: {iid, effect}"""
    ok = _remove_effect_from_yaml(BUILDINGS_PATH, body["iid"], body["effect"])
    return JSONResponse({"ok": ok}, status_code=200 if ok else 404)


@app.post("/api/knowledge-effects/remove")
async def remove_knowledge_effect(body: dict = Body(...)):
    """Remove an effect key from a knowledge item. Body: {iid, effect}"""
    ok = _remove_effect_from_yaml(KNOWLEDGE_PATH, body["iid"], body["effect"])
    return JSONResponse({"ok": ok}, status_code=200 if ok else 404)


def _patch_requirements_in_yaml(path: Path, iid: str, new_reqs: list[str]) -> bool:
    """Replace the requirements list for *iid* in a YAML file."""
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
    # requirements line not found — insert after the item key line
    indent = "  "
    lines.insert(start + 1, f"{indent}requirements: {new_val}\n")
    path.write_text("".join(lines), encoding="utf-8")
    return True


@app.patch("/api/item-requirements")
async def patch_item_requirements(body: dict = Body(...)):
    """Set requirements list for items in buildings.yaml or knowledge.yaml.
    Body: { IID: [req1, req2, ...] }  — type auto-detected from which YAML contains the IID.
    """
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
async def patch_tower_effects(iid: str, body: dict = Body(...)):
    """Replace the entire effects dict for a tower in structures.yaml, preserving inline comments."""
    new_effects: dict = body.get("effects", {})
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


ARTEFACTS_PATH = Path(__file__).parent.parent / "python_server" / "config" / "artefacts.yaml"


@app.get("/api/artefacts")
async def get_artefacts():
    """Return all artefacts from artefacts.yaml."""
    try:
        raw = yaml.safe_load(ARTEFACTS_PATH.read_text(encoding="utf-8")) or {}
        result = []
        for iid, data in raw.items():
            if isinstance(data, dict):
                result.append({
                    "iid": iid,
                    "name": data.get("name", ""),
                    "description": data.get("description", ""),
                    "type": data.get("type", ""),
                    "effects": data.get("effects") or {},
                })
        return JSONResponse(result)
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.post("/api/artefacts")
async def save_artefacts(request: Request):
    """Save full artefacts list to artefacts.yaml."""
    try:
        items = await request.json()
        raw = {}
        for item in items:
            iid = item["iid"].strip().upper().replace(" ", "_")
            raw[iid] = {
                "name": item.get("name", ""),
                "description": item.get("description", ""),
                "type": item.get("type", ""),
                "effects": item.get("effects") or {},
            }
        header = "# Artefact definitions (collectible passive effect items)\n# effects: passive bonuses while the artefact is owned\n# description: flavour text\n\n"
        body = yaml.dump(raw, default_flow_style=False, allow_unicode=True, sort_keys=False)
        ARTEFACTS_PATH.write_text(header + body, encoding="utf-8")
        return JSONResponse({"success": True})
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.get("/api/admin/catalog")
async def get_catalog():
    """Return full item catalog (buildings + knowledge) with effects — no auth needed on web port."""
    def _load(path):
        import yaml
        with open(path) as f:
            raw = yaml.safe_load(f) or {}
        return {
            iid: {"name": item.get("name", iid), "effects": item.get("effects") or {}}
            for iid, item in raw.items()
        }
    return JSONResponse({
        "buildings": _load(BUILDINGS_PATH),
        "knowledge": _load(KNOWLEDGE_PATH),
    })


@app.get("/api/sprite-files")
async def list_sprite_files():
    """List all JPG and PNG files in the tools directory."""
    tools_dir = WEB_DIR / "tools"
    files = sorted(
        f.name
        for f in tools_dir.iterdir()
        if f.is_file()
        and f.suffix.lower() in (".jpg", ".jpeg", ".png")
        and ".__orig" not in f.stem
    )
    return JSONResponse({"files": files})


@app.get("/api/maps")
async def list_maps():
    """List all PNG/WebP map files under assets/sprites/maps/."""
    maps_dir = WEB_DIR / "assets" / "sprites" / "maps"
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
async def list_critters():
    """
    Scan assets/sprites/critters/ and return a manifest for every critter.

    Each entry has:
      name   – folder name
      type   – "gifs" or "spritesheet"

    For "gifs":
      files  – {"forward": ..., "left": ..., "right": ..., "backward": ...}

    For "spritesheet":
      file   – relative URL to the PNG (relative to web root)
    """
    critters_dir = WEB_DIR / "assets" / "sprites" / "critters"
    if not critters_dir.is_dir():
        return JSONResponse({"critters": []})

    # Canonical GIF file names for each direction
    GIF_NAMES = {
        "forward":  "front.gif",
        "left":     "left.gif",
        "right":    "right.gif",
        "backward": "back.gif",
    }

    result = []
    for d in sorted(critters_dir.iterdir()):
        if not d.is_dir():
            continue

        name = d.name
        base = f"/assets/sprites/critters/{name}"

        # Prefer GIFs when all four are present
        gif_paths = {dir_: d / fname for dir_, fname in GIF_NAMES.items()}
        if all(p.exists() for p in gif_paths.values()):
            result.append({
                "name": name,
                "type": "gifs",
                "files": {dir_: f"{base}/{fname}" for dir_, fname in GIF_NAMES.items()},
            })
            continue

        # Fall back to first PNG/WebP sprite sheet found
        sheets = sorted(f.name for f in d.iterdir() if f.suffix.lower() in (".png", ".webp"))
        if sheets:
            result.append({
                "name": name,
                "type": "spritesheet",
                "file": f"{base}/{sheets[0]}",
            })

    return JSONResponse({"critters": result})


_SAVED_MAPS_PATH = Path(__file__).resolve().parent.parent / "python_server" / "config" / "saved_maps.yaml"

# Lazy-load game config + power service for map power computation
_map_power_upgrades = None

def _get_map_power_upgrades():
    global _map_power_upgrades
    if _map_power_upgrades is None:
        from gameserver.main import load_configuration
        from gameserver.engine.upgrade_provider import UpgradeProvider
        cfg = load_configuration(config_dir=str(Path(__file__).resolve().parent.parent / "python_server" / "config"))
        up = UpgradeProvider()
        up.load(cfg.items)
        _map_power_upgrades = (up, getattr(cfg.game, "starting_max_life", 10.0))
    return _map_power_upgrades

def _get_structure_era_map() -> dict[str, str]:
    """Return {iid: era_label_en} for all structures, parsed from structures.yaml."""
    from gameserver.util.eras import ERA_LABELS_EN
    CONFIG_DIR = Path(__file__).resolve().parent.parent / "python_server" / "config"
    data = yaml.safe_load((CONFIG_DIR / "structures.yaml").read_text(encoding="utf-8")) or {}
    result: dict[str, str] = {}
    for iid, item in data.items():
        if isinstance(item, dict):
            era = item.get("era", "stone")
            result[iid] = ERA_LABELS_EN.get(era, era)
    return result

_structure_era_map: dict[str, str] | None = None

def _get_cached_structure_era_map() -> dict[str, str]:
    global _structure_era_map
    if _structure_era_map is None:
        _structure_era_map = _get_structure_era_map()
    return _structure_era_map

NON_TOWER = {"castle", "spawnpoint", "path", "empty", "blocked", "void", ""}

def _compute_map_age_pct(m: dict) -> dict[str, float]:
    """Return {era_label: pct} tower era distribution for a map entry."""
    tower_era = _get_cached_structure_era_map()
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


def _compute_map_defense_power(m: dict) -> float:
    from gameserver.engine.power_service import defense_power
    from gameserver.engine.hex_pathfinding import find_path_from_spawn_to_castle
    from gameserver.models.empire import Empire
    upgrades, default_life = _get_map_power_upgrades()
    hex_map = {f"{t['q']},{t['r']}": {"type": t.get("type", "empty")} for t in (m.get("hex_map") or [])}
    empire = Empire(uid=0, name="")
    empire.hex_map = hex_map
    empire.max_life = float(m.get("life") or default_life)
    try:
        path = find_path_from_spawn_to_castle(hex_map)
        path_length = len(path) - 1 if path else None
    except Exception:
        path_length = None
    return defense_power(empire, upgrades, path_length=path_length)


@app.get("/api/saved-maps")
async def list_saved_maps():
    """Return map names and their life values from saved_maps.yaml."""
    if not _SAVED_MAPS_PATH.exists():
        return JSONResponse({"maps": [], "life": {}})
    data = yaml.safe_load(_SAVED_MAPS_PATH.read_text()) or {}
    names   = []
    life    = {}
    power   = {}
    age_pct = {}
    for m in (data.get("maps") or []):
        name = m.get("name", m.get("id", "?"))
        names.append(name)
        if m.get("life") is not None:
            life[name] = m["life"]
        try:
            power[name] = round(_compute_map_defense_power(m), 1)
        except Exception:
            pass
        try:
            age_pct[name] = _compute_map_age_pct(m)
        except Exception:
            pass
    return JSONResponse({"maps": names, "life": life, "power": power, "age_pct": age_pct})


@app.put("/api/tools/map-life")
async def set_map_life(payload: dict):
    """Update the life value of a map in saved_maps.yaml."""
    map_name = payload.get("map_name", "")
    life     = payload.get("life")
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
        name = m.get("name", m.get("id", ""))
        if name == map_name:
            m["life"] = life
            found = True
            break
    if not found:
        return JSONResponse({"ok": False, "error": f"Map '{map_name}' not found"}, status_code=404)

    _SAVED_MAPS_PATH.write_text(yaml.dump(data, allow_unicode=True, sort_keys=False))
    return JSONResponse({"ok": True})


@app.get("/api/tools/sim-map")
async def sim_map(map_name: str, era: str, n: int):
    """Run sim_map.py and stream its output file line-by-line as SSE."""
    import asyncio
    import tempfile
    from fastapi.responses import StreamingResponse

    script = Path(__file__).resolve().parent.parent / "sim_map.py"
    python = Path(__file__).resolve().parent.parent / "python_server" / ".venv" / "bin" / "python3"
    if not python.exists():
        python = Path(sys.executable)

    # Temp file that sim_map.py writes JSON lines into
    out_fd, out_path = tempfile.mkstemp(suffix=".jsonl", prefix="sim_map_")
    os.close(out_fd)

    async def generate():
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
                        data = line.rstrip("\n")
                        yield f"data: {data}\n\n"
                    else:
                        # No new data — check if process finished
                        try:
                            await asyncio.wait_for(asyncio.shield(proc.wait()), timeout=0.1)
                            # Process done — flush remaining lines
                            for line in f:
                                data = line.rstrip("\n")
                                yield f"data: {data}\n\n"
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


@app.post("/api/admin/restart-web")
async def restart_web():
    """Restart the web server process via os.execv (self-restart)."""
    import asyncio
    import os
    import sys

    async def _do_restart() -> None:
        await asyncio.sleep(0.3)
        os.execv(sys.executable, [sys.executable] + sys.argv)

    asyncio.create_task(_do_restart())
    return JSONResponse({"ok": True, "message": "Web server restarting …"})


app.mount(
    "/",
    NoCacheStaticFiles(directory=str(WEB_DIR), html=True),
    name="static"
)


def main():
    parser = argparse.ArgumentParser(description="E3 FastAPI Web Server")
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to listen on (default: 8000)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable caching (development mode)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload on file changes"
    )
    
    args = parser.parse_args()
    
    global NO_CACHE
    NO_CACHE = args.no_cache
    
    log.info("=" * 60)
    log.info("🚀 E3 Web Server Starting")
    log.info("=" * 60)
    log.info(f"📂 Serving from: {WEB_DIR}")
    log.info(f"🌐 URL:          http://{args.host}:{args.port}")
    log.info(f"🔧 Mode:         {'Development (No-Cache)' if args.no_cache else 'Production'}")
    log.info(f"🔄 Reload:       {'Enabled' if args.reload else 'Disabled'}")
    log.info("=" * 60)
    log.info("ℹ️  Press Ctrl+C to stop")
    log.info("=" * 60)
    
    # Wrap app with no-cache middleware if needed
    asgi_app = app
    if NO_CACHE:
        asgi_app = NoCacheASGIMiddleware(app)
    
    uvicorn.run(
        asgi_app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    main()
