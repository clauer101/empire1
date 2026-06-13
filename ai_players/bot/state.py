"""Per-bot persistent state, stored as one YAML file per bot."""

from __future__ import annotations

import os
import random
import secrets
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

STATES_DIR = Path(__file__).resolve().parent.parent / "states"

# Per-bot strategic temperament, rolled once at account creation and persisted.
# Biases strategy selection (see config.yaml `personalities`) so multiple bot
# instances develop into distinct, recognizable play styles.
PERSONALITIES = ["economy", "aggressive", "defensive", "balanced"]

# Whimsical fantasy name parts. A new bot gets a random adjective + noun
# (e.g. "GildedRaven"), which becomes its state-file key, username and empire
# name. Lowercased for the state filename.
_NAME_ADJECTIVES = [
    "Gilded", "Crimson", "Shadow", "Frost", "Ember", "Silent", "Storm",
    "Iron", "Velvet", "Obsidian", "Radiant", "Thorn", "Mystic", "Azure",
    "Ravenous", "Gleaming", "Wandering", "Eternal", "Hollow", "Verdant",
    "Brazen", "Cinder", "Dusk", "Gloom", "Hallowed", "Lunar", "Onyx",
    "Scarlet", "Solar", "Whispering", "Wild", "Amber", "Glacial", "Searing",
]
_NAME_NOUNS = [
    "Raven", "Wolf", "Drake", "Sphinx", "Phoenix", "Griffin", "Basilisk",
    "Wyrm", "Falcon", "Serpent", "Hydra", "Golem", "Specter", "Warden",
    "Sentinel", "Reaver", "Oracle", "Marauder", "Harbinger", "Tempest",
    "Talon", "Fang", "Crown", "Bastion", "Citadel", "Vortex", "Ember",
    "Wraith", "Cobra", "Stag", "Lynx", "Kraken", "Manticore", "Nomad",
]


def random_fantasy_name(max_len: int = 15) -> str:
    """Return a random whimsical name like 'GildedRaven', at most max_len chars.

    max_len defaults to 15 so the derived username (name + 5-char hex suffix)
    stays within the server's 20-character limit.
    """
    for _ in range(50):
        name = random.choice(_NAME_ADJECTIVES) + random.choice(_NAME_NOUNS)
        if len(name) <= max_len:
            return name
    # Fallback: shortest possible combination.
    return min(_NAME_ADJECTIVES, key=len) + min(_NAME_NOUNS, key=len)


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


@dataclass
class BotState:
    name: str
    account: dict[str, Any] = field(default_factory=dict)
    personality: str = "balanced"
    strategy: dict[str, Any] | None = None
    memory: dict[str, Any] = field(default_factory=lambda: {
        "last_seen_message_id": 0,
        "defense_weak_waves": {},
        "opponents": {},
        "attack_history": [],
    })
    runtime: dict[str, Any] = field(default_factory=lambda: {"cycles": 0, "last_cycle": ""})
    dirty: bool = False

    @property
    def path(self) -> Path:
        return STATES_DIR / f"{self.name}.yaml"

    @classmethod
    def load_or_create(cls, name: str) -> "BotState":
        path = STATES_DIR / f"{name}.yaml"
        if path.exists():
            data = yaml.safe_load(path.read_text()) or {}
            return cls(
                name=name,
                account=data.get("account", {}),
                personality=data.get("personality", "balanced"),
                strategy=data.get("strategy"),
                memory=data.get("memory", cls(name).memory),
                runtime=data.get("runtime", {"cycles": 0, "last_cycle": ""}),
            )
        state = cls(name=name)
        # Server caps usernames at 20 chars. A 4-hex suffix (_xxxx = 5 chars)
        # keeps them unique, leaving 15 for the fantasy name.
        suffix = f"_{secrets.token_hex(2)}"
        username = name[: 20 - len(suffix)] + suffix
        state.account = {
            "username": username,
            "password": secrets.token_urlsafe(16),
            "email": "",
            "empire_name": f"{name}'s Dominion",
            "uid": None,
        }
        state.personality = random.choice(PERSONALITIES)
        state.dirty = True
        return state

    def save(self) -> None:
        STATES_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "account": self.account,
            "personality": self.personality,
            "strategy": self.strategy,
            "memory": self.memory,
            "runtime": self.runtime,
        }
        fd, tmp = tempfile.mkstemp(dir=STATES_DIR, suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as f:
                yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
            os.replace(tmp, self.path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        self.dirty = False
