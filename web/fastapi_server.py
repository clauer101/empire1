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
import re
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

_ERA_PATTERNS = [
    ("Steinzeit",          re.compile(r'#\s+STEINZEIT')),
    ("Neolithikum",        re.compile(r'#\s+NEOLITHIKUM')),
    ("Bronzezeit",         re.compile(r'#\s+BRONZEZEIT')),
    ("Eisenzeit",          re.compile(r'#\s+EISENZEIT')),
    ("Mittelalter",        re.compile(r'#\s+MITTELALTER')),
    ("Renaissance",        re.compile(r'#\s+RENAISSANCE')),
    ("Industrialisierung", re.compile(r'#\s+INDUSTRIALIS')),
    ("Moderne",            re.compile(r'#\s+MODERNE')),
    ("Zukunft",            re.compile(r'#\s+ZUKUNFT')),
]

_ERA_INFO = {
    "Steinzeit":          "Effort 20 – 1.500",
    "Neolithikum":        "Effort 800 – 7.500",
    "Bronzezeit":         "Effort 2.500 – 8.000",
    "Eisenzeit":          "Effort 8.000 – 30.000",
    "Mittelalter":        "Effort 28.000 – 130.000",
    "Renaissance":        "Effort 100.000 – 500.000",
    "Industrialisierung": "Effort 500.000 – 2.000.000",
    "Moderne":            "Effort 2.000.000 – 5.300.000",
    "Zukunft":            "Effort 40.000.000 – 100.000.000",
}

_ERA_ORDER = list(_ERA_INFO.keys())


def _parse_ai_waves():
    """Read ai_waves.yaml, annotate each wave with its era."""
    raw = AI_WAVES_PATH.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    waves = data.get("armies", [])

    current_era = "Steinzeit"
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
        era = wave_eras[i] if i < len(wave_eras) else "Unbekannt"
        result.append({**wave, "era": era})
    return result


def _parse_era_items() -> dict:
    """Return {era_name: [iid, ...]} from buildings.yaml + knowledge.yaml."""
    result: dict[str, list[str]] = {era: [] for era in _ERA_ORDER}
    for path in (BUILDINGS_PATH, KNOWLEDGE_PATH):
        raw = path.read_text(encoding="utf-8")
        current_era = "Steinzeit"
        for line in raw.split("\n"):
            for era_name, pattern in _ERA_PATTERNS:
                if pattern.search(line):
                    current_era = era_name
                    break
            m = _ITEM_IID_RE.match(line)
            if m:
                result.setdefault(current_era, []).append(m.group(1))
    return result


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
        era = w.get("era", "Unbekannt")
        groups.setdefault(era, []).append(w)

    lines = [header]
    for era in _ERA_ORDER:
        if era not in groups:
            continue
        info = _ERA_INFO.get(era, "")
        lines.append(f"  # {'─' * 58}")
        lines.append(f"  #   {era.upper()}  ({info})")
        lines.append(f"  # {'─' * 58}")
        lines.append("")
        for w in groups[era]:
            lines.append(f"  - name: {json.dumps(w['name'], ensure_ascii=False)}")
            if "travel_time" in w:
                lines.append(f"    travel_time: {int(w['travel_time'])}")
            if "siege_time" in w:
                lines.append(f"    siege_time: {int(w['siege_time'])}")
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

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
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


def _parse_items_full(path: Path) -> list[dict]:
    """Parse buildings/knowledge YAML → list of items annotated with era."""
    raw = path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw) or {}
    iid_to_era: dict[str, str] = {}
    current_era = "Steinzeit"
    for line in raw.split("\n"):
        for era_name, pattern in _ERA_PATTERNS:
            if pattern.search(line):
                current_era = era_name
                break
        m = _ITEM_IID_RE.match(line)
        if m:
            iid_to_era[m.group(1)] = current_era
    result = []
    for iid, item in data.items():
        if not isinstance(item, dict):
            continue
        result.append({
            "iid": iid,
            "era": iid_to_era.get(iid, "Steinzeit"),
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


def _parse_critters(path: Path) -> list[dict]:
    """Parse critters.yaml → list of critter stats annotated with era."""
    raw = path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw) or {}
    iid_to_era: dict[str, str] = {}
    current_era = "Steinzeit"
    for line in raw.split("\n"):
        for era_name, pattern in _ERA_PATTERNS:
            if pattern.search(line):
                current_era = era_name
                break
        m = _ITEM_IID_RE.match(line)
        if m:
            iid_to_era[m.group(1)] = current_era
    result = []
    for iid, item in data.items():
        if not isinstance(item, dict):
            continue
        result.append({
            "iid": iid, "era": iid_to_era.get(iid, "Steinzeit"),
            "name": item.get("name", iid),
            "speed": item.get("speed", 0), "health": item.get("health", 1),
            "value": item.get("value", 0), "damage": item.get("damage", 1),
            "armour": item.get("armour", 0), "slots": item.get("slots", 1),
            "time_between": item.get("time_between", 2000),
            "is_boss": item.get("is_boss", False),
            "scale": item.get("scale", 1),
            "requirements": item.get("requirements", []),
            "animation": item.get("animation", ""),
        })
    return result


def _parse_structures(path: Path) -> list[dict]:
    """Parse structures.yaml → list of tower stats annotated with era."""
    raw = path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw) or {}
    iid_to_era: dict[str, str] = {}
    current_era = "Steinzeit"
    for line in raw.split("\n"):
        for era_name, pattern in _ERA_PATTERNS:
            if pattern.search(line):
                current_era = era_name
                break
        m = _ITEM_IID_RE.match(line)
        if m:
            iid_to_era[m.group(1)] = current_era
    result = []
    for iid, item in data.items():
        if not isinstance(item, dict):
            continue
        result.append({
            "iid": iid, "era": iid_to_era.get(iid, "Steinzeit"),
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
