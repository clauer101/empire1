"""Thin REST client for the empire1 game API.

Handles JWT auth, automatic re-login on 401, and backoff on 429/5xx.
"""

from __future__ import annotations

import gzip
import json
import logging
import time
from typing import Any

import requests

log = logging.getLogger("bot.api")


class ApiError(Exception):
    def __init__(self, status: int, body: str):
        self.status = status
        self.body = body
        super().__init__(f"HTTP {status}: {body[:200]}")


def decode_replay_response(content_type: str, content: bytes) -> dict:
    """Decode a /api/replays/{key} response body.

    The server returns raw gzip bytes (media_type application/gzip, no
    Content-Encoding header — requests does NOT auto-decompress); legacy
    replays come back as plain JSON.
    """
    if "gzip" in (content_type or ""):
        content = gzip.decompress(content)
    return json.loads(content)


class ApiClient:
    def __init__(self, server_url: str, username: str, password: str):
        self.base = server_url.rstrip("/")
        self.username = username
        self.password = password
        self.token: str | None = None
        self.session = requests.Session()

    # ── auth ──────────────────────────────────────────────────────────────

    def signup(self, username: str, password: str, empire_name: str, email: str = "") -> int:
        r = self.session.post(f"{self.base}/api/auth/signup", json={
            "username": username, "password": password,
            "email": email, "empire_name": empire_name,
            "is_bot": True,  # AI players declare themselves as bots
        }, timeout=15)
        data = r.json()
        if not data.get("success"):
            raise ApiError(r.status_code, data.get("reason", r.text))
        return int(data["uid"])

    def login(self) -> dict:
        r = self.session.post(f"{self.base}/api/auth/login", json={
            "username": self.username, "password": self.password,
        }, timeout=15)
        data = r.json()
        if not data.get("success"):
            raise ApiError(r.status_code, data.get("reason", r.text))
        self.token = data["token"]
        return data

    # ── request core ──────────────────────────────────────────────────────

    def _request_raw(self, method: str, path: str, *, retries: int = 4,
                     **kwargs) -> requests.Response:
        """Auth/backoff request loop returning the raw Response."""
        if self.token is None:
            self.login()
        url = f"{self.base}{path}"
        backoff = 2.0
        for attempt in range(retries):
            headers = {"Authorization": f"Bearer {self.token}"}
            r = self.session.request(method, url, headers=headers, timeout=20, **kwargs)
            if r.status_code == 401:
                log.info("token expired, re-login")
                self.login()
                continue
            if r.status_code == 429 or r.status_code >= 500:
                log.warning("HTTP %d on %s, backoff %.0fs", r.status_code, path, backoff)
                time.sleep(backoff)
                backoff *= 2
                continue
            if r.status_code >= 400:
                raise ApiError(r.status_code, r.text)
            return r
        raise ApiError(0, f"retries exhausted for {path}")

    def _request(self, method: str, path: str, *, retries: int = 4, **kwargs) -> Any:
        r = self._request_raw(method, path, retries=retries, **kwargs)
        return r.json() if r.content else {}

    def get(self, path: str, **kw) -> Any:
        return self._request("GET", path, **kw)

    def post(self, path: str, json: dict | None = None, **kw) -> Any:
        return self._request("POST", path, json=json, **kw)

    def put(self, path: str, json: dict | None = None, **kw) -> Any:
        return self._request("PUT", path, json=json, **kw)

    # ── convenience wrappers ──────────────────────────────────────────────

    def summary(self) -> dict:
        return self.get("/api/empire/summary")

    def items(self) -> dict:
        return self.get("/api/empire/items")

    def military(self) -> dict:
        return self.get("/api/empire/military")

    def empires(self) -> Any:
        return self.get("/api/empires")

    def messages(self) -> dict:
        return self.get("/api/messages")

    def build(self, iid: str) -> dict:
        return self.post("/api/empire/build", {"iid": iid})

    def citizen_upgrade(self) -> dict:
        return self.post("/api/empire/citizen/upgrade")

    def set_citizens(self, dist: dict[str, int]) -> dict:
        return self.put("/api/empire/citizen", dist)

    def get_map(self) -> dict:
        return self.get("/api/map")

    def map_neighbors(self) -> dict:
        """Non-owned tiles within the fog radius — what the map screen shows."""
        return self.get("/api/map/neighbors")

    def save_map(self, tiles: dict[str, str]) -> dict:
        return self.put("/api/map", {"tiles": tiles})

    def buy_tile(self, q: int, r: int) -> dict:
        return self.post("/api/map/buy-tile", {"q": q, "r": r})

    def create_army(self, name: str) -> dict:
        return self.post("/api/army", {"name": name})

    def add_wave(self, aid: int) -> dict:
        return self.post(f"/api/army/{aid}/wave")

    def set_wave(self, aid: int, wave_number: int, critter_iid: str, slots: int) -> dict:
        return self.put(f"/api/army/{aid}/wave/{wave_number}",
                        {"critter_iid": critter_iid, "slots": slots})

    def buy_critter_slot(self, aid: int, wave_number: int) -> dict:
        return self.post("/api/army/buy-critter-slot", {"aid": aid, "wave_number": wave_number})

    def buy_wave_era(self, aid: int, wave_number: int) -> dict:
        return self.post("/api/army/buy-wave-era", {"aid": aid, "wave_number": wave_number})

    def set_ruler_wave(self, aid: int, wave_number: int, ruler_iid: str) -> dict:
        return self.post("/api/army/set-ruler-wave", {
            "aid": aid, "wave_number": wave_number, "ruler_iid": ruler_iid})

    def attack(self, target_uid: int, opponent_name: str, army_aid: int) -> dict:
        return self.post("/api/attack", {
            "target_uid": target_uid, "opponent_name": opponent_name, "army_aid": army_aid})

    def spy_attack(self, target_uid: int, opponent_name: str) -> dict:
        return self.post("/api/spy-attack", {
            "target_uid": target_uid, "opponent_name": opponent_name})

    def get_replay(self, key: str) -> dict:
        r = self._request_raw("GET", f"/api/replays/{key}")
        return decode_replay_response(r.headers.get("Content-Type", ""), r.content)

    def buy_item_upgrade(self, iid: str, stat: str) -> dict:
        return self.post("/api/item/buy-upgrade", {"iid": iid, "stat": stat})

    def choose_ruler(self, ruler_iid: str) -> dict:
        return self.post("/api/empire/ruler/choose", {"ruler_iid": ruler_iid})

    def ruler_skill_up(self, skill: str) -> dict:
        return self.post("/api/empire/ruler/skill-up", {"skill": skill})
