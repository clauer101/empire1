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
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response, JSONResponse
from starlette.datastructures import MutableHeaders
import uvicorn

AI_WAVES_PATH = Path(__file__).parent.parent / "python_server" / "config" / "ai_waves.yaml"
GAME_CONFIG_PATH = Path(__file__).parent.parent / "python_server" / "config" / "game.yaml"
BUILDINGS_PATH = Path(__file__).parent.parent / "python_server" / "config" / "buildings.yaml"
KNOWLEDGE_PATH = Path(__file__).parent.parent / "python_server" / "config" / "knowledge.yaml"

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

        # Fall back to first PNG sprite sheet found
        pngs = sorted(f.name for f in d.iterdir() if f.suffix.lower() == ".png")
        if pngs:
            result.append({
                "name": name,
                "type": "spritesheet",
                "file": f"{base}/{pngs[0]}",
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
