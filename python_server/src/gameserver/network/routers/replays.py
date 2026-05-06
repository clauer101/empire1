"""Replays router — /api/replays/*."""
from __future__ import annotations

from typing import Any, TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException

from gameserver.network.jwt_auth import get_current_uid

if TYPE_CHECKING:
    from gameserver.main import Services


def make_router(services: "Services") -> APIRouter:  # noqa: ARG001
    router = APIRouter()

    @router.get("/api/replays")
    async def get_replays(uid: int = Depends(get_current_uid)) -> dict[str, Any]:
        """List available battle replays."""
        from gameserver.persistence.replay import list_replays
        replays = list_replays()
        return {"replays": replays}

    @router.get("/api/replays/{key}")
    async def get_replay(key: str, uid: int = Depends(get_current_uid)) -> Any:
        """Get a full battle replay by replay key.

        Returns raw gzip bytes for .json.gz files (client decompresses via
        DecompressionStream) or plain JSON for legacy .json files.
        """
        from gameserver.persistence.replay import get_replay_path
        from starlette.responses import Response, JSONResponse
        path = get_replay_path(key)
        if path is None:
            raise HTTPException(status_code=404, detail="Replay not found")
        if path.suffix == ".gz":
            data = path.read_bytes()
            return Response(
                content=data,
                media_type="application/gzip",
                headers={"Content-Length": str(len(data))},
            )
        import json as _json
        return JSONResponse(content=_json.loads(path.read_text(encoding="utf-8")))

    return router
