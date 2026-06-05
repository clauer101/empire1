"""Tests that ai_waves.yaml armies don't use critters from later eras.

Rule: at most 5 % of an army's total slots may use critters whose era comes
after the army's own era (determined by YAML section headers).
"""
from __future__ import annotations

import re
import yaml
from pathlib import Path

import pytest

# ── Paths ────────────────────────────────────────────────────────────────────

_CONFIG = Path(__file__).resolve().parent.parent / "config"
_AI_WAVES  = _CONFIG / "ai_waves.yaml"
_CRITTERS  = _CONFIG / "critters.yaml"

# ── Constants ─────────────────────────────────────────────────────────────────

ERA_ORDER = [
    "stone", "neolithic", "bronze", "iron",
    "middle_ages", "renaissance", "industrial", "modern", "future",
]

_ERA_SECTION_RE = re.compile(
    r"#\s+(STONE_AGE|NEOLITHIC|BRONZE_AGE|IRON_AGE|MIDDLE_AGES"
    r"|RENAISSANCE|INDUSTRIAL|MODERN|FUTURE)\b"
)
_ERA_KEY_MAP = {
    "STONE_AGE": "stone", "NEOLITHIC": "neolithic", "BRONZE_AGE": "bronze",
    "IRON_AGE": "iron", "MIDDLE_AGES": "middle_ages", "RENAISSANCE": "renaissance",
    "INDUSTRIAL": "industrial", "MODERN": "modern", "FUTURE": "future",
}

MAX_LATER_ERA_FRACTION = 0.05


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_critter_eras() -> dict[str, str]:
    """Return {IID: era} for every critter in critters.yaml."""
    data = yaml.safe_load(_CRITTERS.read_text(encoding="utf-8"))
    return {iid.upper(): v["era"] for iid, v in data.items() if "era" in v}


def _load_armies_with_era() -> list[tuple[str, str, list[dict]]]:
    """Parse ai_waves.yaml and return [(name, era, waves), …].

    Army era is derived from the section header (STONE_AGE, NEOLITHIC, …)
    that precedes the army definition in the file.
    """
    raw = _AI_WAVES.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    armies_raw: list[dict] = data.get("armies", [])

    # Map army name → era by scanning raw lines for section headers
    name_to_era: dict[str, str] = {}
    current_era = ERA_ORDER[0]
    for line in raw.splitlines():
        m = _ERA_SECTION_RE.search(line)
        if m:
            current_era = _ERA_KEY_MAP[m.group(1)]
            continue
        if line.strip().startswith("- name:"):
            name = line.strip()[len("- name:"):].strip().strip('"').strip("'")
            name_to_era[name] = current_era

    result = []
    for army in armies_raw:
        name = army.get("name", "")
        era = name_to_era.get(name, ERA_ORDER[0])
        waves = army.get("waves", [])
        result.append((name, era, waves))
    return result


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def critter_eras() -> dict[str, str]:
    return _load_critter_eras()


@pytest.fixture(scope="module")
def armies() -> list[tuple[str, str, list[dict]]]:
    return _load_armies_with_era()


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestAiWavesEraConsistency:

    def test_all_armies_have_era_assigned(self, armies):
        """Every army must be covered by a section header."""
        for name, era, _ in armies:
            assert era in ERA_ORDER, (
                f"Army '{name}' has unrecognised era '{era}'"
            )

    def test_later_era_critters_at_most_5_percent(self, armies, critter_eras):
        """No army may have more than 5 % of its slots filled by critters
        from an era that comes after the army's own era."""
        violations: list[str] = []

        for name, era, waves in armies:
            era_idx = ERA_ORDER.index(era)
            total_slots = sum(w.get("slots", 1) for w in waves)
            if total_slots == 0:
                continue

            later_slots = 0
            for w in waves:
                critter = w.get("critter", "").upper()
                critter_era = critter_eras.get(critter)
                if critter_era is None:
                    continue
                if ERA_ORDER.index(critter_era) > era_idx:
                    later_slots += w.get("slots", 1)

            fraction = later_slots / total_slots
            if fraction > MAX_LATER_ERA_FRACTION:
                violations.append(
                    f"  '{name}' (era={era}): {fraction:.1%} later-era slots "
                    f"({later_slots}/{total_slots})"
                )

        assert not violations, (
            f"Armies exceed {MAX_LATER_ERA_FRACTION:.0%} later-era critter limit:\n"
            + "\n".join(violations)
        )

    def test_no_unknown_critters(self, armies, critter_eras):
        """Every critter IID used in a wave must exist in critters.yaml."""
        unknown: list[str] = []
        for name, era, waves in armies:
            for w in waves:
                iid = w.get("critter", "").upper()
                if iid and iid not in critter_eras:
                    unknown.append(f"  '{name}' uses unknown critter '{iid}'")
        assert not unknown, "Unknown critter IIDs found:\n" + "\n".join(unknown)

    def test_9_era_sections_present(self):
        """The YAML file must contain all 9 English era section headers."""
        raw = _AI_WAVES.read_text(encoding="utf-8")
        found = set(_ERA_KEY_MAP[m.group(1)] for m in _ERA_SECTION_RE.finditer(raw))
        missing = set(ERA_ORDER) - found
        assert not missing, f"Missing era section headers: {missing}"
