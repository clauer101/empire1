#!/usr/bin/env python3
"""
FastAPI server for serving the E3 web client.

Serves static files with proper cache control headers for development.
Much faster and more robust than SimpleHTTPServer.

Usage:
    python3 fastapi_server.py [--port 8000] [--host 0.0.0.0] [--no-cache]
"""

import argparse
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response, JSONResponse
from starlette.datastructures import MutableHeaders
import uvicorn

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
    """List all PNG map files under assets/sprites/maps/."""
    maps_dir = WEB_DIR / "assets" / "sprites" / "maps"
    if not maps_dir.is_dir():
        return JSONResponse({"maps": []})
    files = sorted(
        [{"name": f.name, "url": f"/assets/sprites/maps/{f.name}"}
         for f in maps_dir.iterdir()
         if f.is_file() and f.suffix.lower() == ".png"],
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
