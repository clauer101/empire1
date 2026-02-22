"""Pydantic request/response models for the REST API.

These models define the HTTP request bodies and response shapes.
They are intentionally separate from the WebSocket GameMessage models
to keep the REST API clean and self-documenting.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ===================================================================
# Auth
# ===================================================================


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    uid: int = 0
    token: str = ""
    reason: str = ""
    session_state: Optional[Dict[str, Any]] = None
    summary: Optional[Dict[str, Any]] = None


class SignupRequest(BaseModel):
    username: str
    password: str
    email: str = ""
    empire_name: str = ""


class SignupResponse(BaseModel):
    success: bool
    uid: int = 0
    reason: str = ""


# ===================================================================
# Empire queries
# ===================================================================


class BuildRequest(BaseModel):
    iid: str


class BuildResponse(BaseModel):
    success: bool
    iid: str = ""
    error: str = ""
    build_queue: str = ""
    research_queue: str = ""


class CitizenDistribution(BaseModel):
    merchant: int = 0
    scientist: int = 0
    artist: int = 0


class CitizenResponse(BaseModel):
    success: bool
    error: str = ""
    citizens: Optional[Dict[str, int]] = None


class MapSaveBody(BaseModel):
    tiles: Dict[str, Any]


class MapSaveResponse(BaseModel):
    success: bool
    error: str = ""


class BuyTileRequest(BaseModel):
    q: int
    r: int


class BuyWaveRequest(BaseModel):
    aid: int


class BuyCritterSlotRequest(BaseModel):
    aid: int
    wave_number: int


class ArmyCreateRequest(BaseModel):
    name: str


class ArmyRenameRequest(BaseModel):
    name: str


class WaveCreateRequest(BaseModel):
    pass  # Server decides critter type (SLAVE) and slots (5)


class WaveChangeRequest(BaseModel):
    critter_iid: str = ""
    slots: Optional[int] = None


class AttackRequest(BaseModel):
    target_uid: int = 0
    opponent_name: str = ""
    army_aid: int = 0


class SendMessageRequest(BaseModel):
    to_uid: int
    body: str
