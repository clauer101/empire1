"""Shared pytest fixtures for gameserver tests.

Provides reusable factories and fixtures to reduce boilerplate across test
modules.  Individual tests can still define their own helpers when they need
non-standard data.
"""

from __future__ import annotations

import os
from typing import Any
from unittest.mock import MagicMock

# Provide a test secret so jwt_auth can be imported without a real .env
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-pytest-only!")

import pytest

from gameserver.engine.empire_service import EmpireService
from gameserver.engine.attack_service import AttackService
from gameserver.engine.upgrade_provider import UpgradeProvider
from gameserver.models.empire import Empire
from gameserver.util.events import EventBus


# ---------------------------------------------------------------------------
# Factory functions (can be called directly, or via fixtures)
# ---------------------------------------------------------------------------

def make_empire(
    uid: int = 1,
    name: str = "TestEmpire",
    *,
    gold: float = 1000.0,
    culture: float = 500.0,
    life: float = 10.0,
    max_life: float = 10.0,
    buildings: dict | None = None,
    knowledge: dict | None = None,
    citizens: dict | None = None,
    effects: dict | None = None,
    artefacts: list | None = None,
    structures: dict | None = None,
    armies: list | None = None,
) -> Empire:
    """Create a test empire with sensible defaults."""
    return Empire(
        uid=uid,
        name=name,
        resources={"gold": gold, "culture": culture, "life": life},
        buildings=buildings or {},
        knowledge=knowledge or {},
        citizens=citizens or {},
        effects=effects or {},
        artefacts=artefacts or [],
        max_life=max_life,
        structures=structures or {},
        armies=armies or [],
    )


def make_services(
    empire: Empire | None = None,
    game_config=None,
) -> Any:
    """Create a lightweight Services-like mock for handler/REST tests."""
    event_bus = EventBus()
    upgrade_provider = UpgradeProvider()
    empire_service = EmpireService(upgrade_provider, event_bus, game_config=game_config)
    attack_service = AttackService(event_bus, game_config=game_config,
                                   empire_service=empire_service)
    if empire is not None:
        empire_service.register(empire)

    svc = MagicMock()
    svc.event_bus = event_bus
    svc.upgrade_provider = upgrade_provider
    svc.empire_service = empire_service
    svc.attack_service = attack_service
    svc.database = None
    return svc


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def event_bus() -> EventBus:
    return EventBus()


@pytest.fixture
def upgrade_provider() -> UpgradeProvider:
    return UpgradeProvider()


@pytest.fixture
def empire_service(upgrade_provider, event_bus) -> EmpireService:
    return EmpireService(upgrade_provider=upgrade_provider, event_bus=event_bus)
