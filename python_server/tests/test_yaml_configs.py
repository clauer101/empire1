"""Structural validation tests for all YAML config files.

Catches formatting errors (like ``0- 600.0`` instead of ``- 600.0``),
missing required fields, null wave lists, and constraint violations before
they cause a 502 at startup.
"""

from __future__ import annotations

import yaml
import pytest
from pathlib import Path

_CONFIG = Path(__file__).resolve().parent.parent / "config"

ERA_ORDER = [
    "stone", "neolithic", "bronze", "iron",
    "middle_ages", "renaissance", "industrial", "modern", "future",
]
_ERA_SET = set(ERA_ORDER)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load(filename: str) -> dict:
    path = _CONFIG / filename
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


# ---------------------------------------------------------------------------
# Syntax: every YAML file must parse without error
# ---------------------------------------------------------------------------

_YAML_FILES = [
    "game.yaml",
    "buildings.yaml",
    "critters.yaml",
    "structures.yaml",
    "knowledge.yaml",
    "artifacts.yaml",
    "rulers.yaml",
    "ai_waves.yaml",
    "saved_maps.yaml",
    "maps/default.yaml",
]


@pytest.mark.parametrize("filename", _YAML_FILES)
def test_yaml_parses_without_error(filename: str):
    """Every config YAML must be valid YAML (catches e.g. '0- 600.0' typos)."""
    path = _CONFIG / filename
    yaml.safe_load(path.read_text(encoding="utf-8"))  # raises on bad YAML


# ---------------------------------------------------------------------------
# game.yaml
# ---------------------------------------------------------------------------

class TestGameYaml:
    @pytest.fixture(scope="class")
    def raw(self):
        return _load("game.yaml")

    def test_required_sections_present(self, raw):
        for section in ("spy_costs", "prices", "era_effects",
                         "structure_upgrades", "critter_upgrades",
                         "end_ralley_effects", "starting_resources"):
            assert section in raw, f"Missing required section '{section}'"

    def test_item_upgrade_base_costs_is_list_of_nine(self, raw):
        costs = raw.get("item_upgrade_base_costs")
        assert isinstance(costs, list), "item_upgrade_base_costs must be a list"
        assert len(costs) == 9, (
            f"item_upgrade_base_costs must have exactly 9 entries, got {len(costs)}"
        )

    def test_item_upgrade_base_costs_all_numeric(self, raw):
        costs = raw.get("item_upgrade_base_costs", [])
        for i, v in enumerate(costs):
            assert isinstance(v, (int, float)), (
                f"item_upgrade_base_costs[{i}] = {v!r} is not a number"
            )

    def test_prices_wave_era_costs_nine_entries(self, raw):
        wec = raw.get("prices", {}).get("wave_era_costs", [])
        assert len(wec) == 9, (
            f"prices.wave_era_costs must have 9 entries, got {len(wec)}"
        )

    def test_era_effects_covers_all_eras(self, raw):
        era_keys = set(raw.get("era_effects", {}).keys())
        missing = _ERA_SET - era_keys
        assert not missing, f"era_effects missing eras: {missing}"

    def test_barbarians_aggressiveness_covers_all_eras(self, raw):
        ba = raw.get("barbarians_aggressiveness", {})
        if ba:
            missing = _ERA_SET - set(ba.keys())
            assert not missing, f"barbarians_aggressiveness missing eras: {missing}"

    def test_starting_resources_has_required_keys(self, raw):
        sr = raw.get("starting_resources", {})
        for key in ("gold", "life"):
            assert key in sr, f"starting_resources missing '{key}'"

    def test_loads_via_loader(self):
        """Full loader must succeed without exceptions."""
        from gameserver.loaders.game_config_loader import load_game_config
        cfg = load_game_config(str(_CONFIG / "game.yaml"))
        assert cfg.item_upgrade_base_costs is not None
        assert len(cfg.item_upgrade_base_costs) == 9


# ---------------------------------------------------------------------------
# critters.yaml
# ---------------------------------------------------------------------------

class TestCrittersYaml:
    @pytest.fixture(scope="class")
    def critters(self):
        return _load("critters.yaml")

    def test_all_have_required_fields(self, critters):
        required = ("name", "era", "speed", "health", "armour", "slots")
        missing = {
            iid: [f for f in required if f not in attrs]
            for iid, attrs in critters.items()
            if isinstance(attrs, dict)
            for _ in [None]  # hack to bind attrs
            if any(f not in attrs for f in required)
        }
        # Rebuild properly
        missing = {}
        for iid, attrs in critters.items():
            if not isinstance(attrs, dict):
                continue
            absent = [f for f in required if f not in attrs]
            if absent:
                missing[iid] = absent
        assert not missing, f"Critters missing fields: {missing}"

    def test_speeds_positive(self, critters):
        bad = [iid for iid, a in critters.items()
               if isinstance(a, dict) and float(a.get("speed", 1)) <= 0]
        assert not bad, f"Critters with non-positive speed: {bad}"

    def test_health_positive(self, critters):
        bad = [iid for iid, a in critters.items()
               if isinstance(a, dict) and float(a.get("health", 1)) <= 0]
        assert not bad, f"Critters with non-positive health: {bad}"

    def test_slots_positive(self, critters):
        bad = [iid for iid, a in critters.items()
               if isinstance(a, dict) and float(a.get("slots", 1)) <= 0]
        assert not bad, f"Critters with non-positive slots: {bad}"

    def test_era_values_valid(self, critters):
        bad = {iid: a["era"] for iid, a in critters.items()
               if isinstance(a, dict) and a.get("era") not in _ERA_SET}
        assert not bad, f"Critters with invalid era: {bad}"

    def test_spawn_on_death_references_known_iid(self, critters):
        """spawn_on_death may be null, a string IID, or a {IID: count} dict."""
        known = set(critters.keys())
        bad = {}
        for iid, attrs in critters.items():
            if not isinstance(attrs, dict):
                continue
            sod = attrs.get("spawn_on_death")
            if not sod:
                continue
            if isinstance(sod, str) and sod not in known:
                bad[iid] = sod
            elif isinstance(sod, dict):
                unknown_keys = [k for k in sod if k not in known]
                if unknown_keys:
                    bad[iid] = unknown_keys
        assert not bad, f"spawn_on_death references unknown IIDs: {bad}"


# ---------------------------------------------------------------------------
# buildings.yaml / knowledge.yaml (same schema)
# ---------------------------------------------------------------------------

def _check_item_tree_yaml(filename: str):
    data = _load(filename)
    required = ("name", "era", "effort", "costs", "requirements")
    errors = []
    for iid, attrs in data.items():
        if not isinstance(attrs, dict):
            continue
        for f in required:
            if f not in attrs:
                errors.append(f"{iid}: missing '{f}'")
        era = attrs.get("era")
        if era is not None and era not in _ERA_SET:
            errors.append(f"{iid}: invalid era '{era}'")
        effort = attrs.get("effort")
        if effort is not None and float(effort) <= 0:
            errors.append(f"{iid}: effort must be > 0, got {effort}")
        reqs = attrs.get("requirements")
        if reqs is not None and not isinstance(reqs, list):
            errors.append(f"{iid}: 'requirements' must be a list, got {type(reqs).__name__}")
        costs = attrs.get("costs")
        if costs is not None and not isinstance(costs, dict):
            errors.append(f"{iid}: 'costs' must be a dict, got {type(costs).__name__}")
    return errors


class TestBuildingsYaml:
    def test_structure(self):
        errors = _check_item_tree_yaml("buildings.yaml")
        assert not errors, "buildings.yaml validation errors:\n" + "\n".join(errors)


class TestKnowledgeYaml:
    def test_structure(self):
        errors = _check_item_tree_yaml("knowledge.yaml")
        assert not errors, "knowledge.yaml validation errors:\n" + "\n".join(errors)


# ---------------------------------------------------------------------------
# structures.yaml (towers)
# ---------------------------------------------------------------------------

class TestStructuresYaml:
    @pytest.fixture(scope="class")
    def structures(self):
        return _load("structures.yaml")

    def test_required_fields(self, structures):
        required = ("name", "era", "damage", "range", "reload_time", "costs")
        errors = []
        for iid, attrs in structures.items():
            if not isinstance(attrs, dict):
                continue
            for f in required:
                if f not in attrs:
                    errors.append(f"{iid}: missing '{f}'")
        assert not errors, "structures.yaml validation errors:\n" + "\n".join(errors)

    def test_era_values_valid(self, structures):
        bad = {iid: a["era"] for iid, a in structures.items()
               if isinstance(a, dict) and a.get("era") not in _ERA_SET}
        assert not bad, f"Structures with invalid era: {bad}"

    def test_range_positive(self, structures):
        bad = [iid for iid, a in structures.items()
               if isinstance(a, dict) and float(a.get("range", 1)) <= 0]
        assert not bad, f"Structures with non-positive range: {bad}"

    def test_reload_time_positive(self, structures):
        bad = [iid for iid, a in structures.items()
               if isinstance(a, dict) and float(a.get("reload_time", 1)) <= 0]
        assert not bad, f"Structures with non-positive reload_time: {bad}"


# ---------------------------------------------------------------------------
# artifacts.yaml
# ---------------------------------------------------------------------------

class TestArtifactsYaml:
    @pytest.fixture(scope="class")
    def artifacts(self):
        return _load("artifacts.yaml")

    def test_required_fields(self, artifacts):
        errors = []
        for iid, attrs in artifacts.items():
            if not isinstance(attrs, dict):
                continue
            if "name" not in attrs:
                errors.append(f"{iid}: missing 'name'")
            if "effects" not in attrs:
                errors.append(f"{iid}: missing 'effects'")
            elif not isinstance(attrs["effects"], dict):
                errors.append(f"{iid}: 'effects' must be a dict")
        assert not errors, "artifacts.yaml validation errors:\n" + "\n".join(errors)


# ---------------------------------------------------------------------------
# rulers.yaml
# ---------------------------------------------------------------------------

class TestRulersYaml:
    @pytest.fixture(scope="class")
    def rulers(self):
        return _load("rulers.yaml")

    def test_required_fields(self, rulers):
        errors = []
        for iid, attrs in rulers.items():
            if not isinstance(attrs, dict):
                continue
            for f in ("name", "q", "w", "e", "r"):
                if f not in attrs:
                    errors.append(f"{iid}: missing '{f}'")
        assert not errors, "rulers.yaml validation errors:\n" + "\n".join(errors)

    def test_qwe_have_five_levels(self, rulers):
        errors = []
        for iid, attrs in rulers.items():
            if not isinstance(attrs, dict):
                continue
            for ability in ("q", "w", "e"):
                levels = (attrs.get(ability) or {}).get("levels", [])
                if len(levels) != 5:
                    errors.append(f"{iid}.{ability}: expected 5 levels, got {len(levels)}")
        assert not errors, "rulers.yaml level count errors:\n" + "\n".join(errors)

    def test_r_has_three_levels(self, rulers):
        errors = []
        for iid, attrs in rulers.items():
            if not isinstance(attrs, dict):
                continue
            levels = (attrs.get("r") or {}).get("levels", [])
            if len(levels) != 3:
                errors.append(f"{iid}.r: expected 3 levels, got {len(levels)}")
        assert not errors, "rulers.yaml R-ability level count errors:\n" + "\n".join(errors)

    def test_all_levels_non_empty(self, rulers):
        errors = []
        for iid, attrs in rulers.items():
            if not isinstance(attrs, dict):
                continue
            for ability in ("q", "w", "e", "r"):
                levels = (attrs.get(ability) or {}).get("levels", [])
                for i, lvl in enumerate(levels):
                    if not isinstance(lvl, dict) or not lvl:
                        errors.append(f"{iid}.{ability}[{i}]: level must be a non-empty dict")
        assert not errors, "rulers.yaml empty level errors:\n" + "\n".join(errors)


# ---------------------------------------------------------------------------
# ai_waves.yaml
# ---------------------------------------------------------------------------

class TestAiWavesYaml:
    @pytest.fixture(scope="class")
    def armies(self):
        data = _load("ai_waves.yaml")
        return data.get("armies", [])

    def test_has_armies(self, armies):
        assert len(armies) > 0, "ai_waves.yaml has no armies"

    def test_all_armies_have_name(self, armies):
        bad = [a for a in armies if not a.get("name")]
        assert not bad, f"{len(bad)} armies missing 'name'"

    def test_waves_is_list_not_null(self, armies):
        """waves: null (bare 'waves:') causes TypeError at runtime — must be []."""
        null_waves = [a["name"] for a in armies if a.get("waves") is None]
        assert not null_waves, (
            "Armies with null waves (should be '[]'):\n" + "\n".join(null_waves)
        )

    def test_waves_is_list_type(self, armies):
        bad = [a["name"] for a in armies
               if a.get("waves") is not None and not isinstance(a.get("waves"), list)]
        assert not bad, f"Armies where 'waves' is not a list: {bad}"

    def test_wave_entries_have_required_fields(self, armies):
        errors = []
        for army in armies:
            name = army.get("name", "?")
            for i, wave in enumerate(army.get("waves") or []):
                if not isinstance(wave, dict):
                    errors.append(f"{name}[{i}]: wave must be a dict")
                    continue
                iid = wave.get("iid") or wave.get("critter")
                if not iid:
                    errors.append(f"{name}[{i}]: missing 'iid' or 'critter'")
                if "slots" not in wave:
                    errors.append(f"{name}[{i}]: missing 'slots'")
                elif float(wave["slots"]) <= 0:
                    errors.append(f"{name}[{i}]: slots must be > 0, got {wave['slots']}")
        assert not errors, "ai_waves.yaml wave field errors:\n" + "\n".join(errors)

    def test_modern_wave_slots_max_40(self, armies):
        """Modern era waves must not exceed 40 slots (balance constraint)."""
        import re
        raw = (_CONFIG / "ai_waves.yaml").read_text(encoding="utf-8")
        _ERA_SECTION_RE = re.compile(r"#\s+(STONE_AGE|NEOLITHIC|BRONZE_AGE|IRON_AGE"
                                      r"|MIDDLE_AGES|RENAISSANCE|INDUSTRIAL|MODERN|FUTURE)\b")
        _ERA_KEY_MAP = {
            "STONE_AGE": "stone", "NEOLITHIC": "neolithic", "BRONZE_AGE": "bronze",
            "IRON_AGE": "iron", "MIDDLE_AGES": "middle_ages", "RENAISSANCE": "renaissance",
            "INDUSTRIAL": "industrial", "MODERN": "modern", "FUTURE": "future",
        }
        name_to_era: dict[str, str] = {}
        current_era = ERA_ORDER[0]
        for line in raw.splitlines():
            m = _ERA_SECTION_RE.search(line)
            if m:
                current_era = _ERA_KEY_MAP[m.group(1)]
                continue
            if line.strip().startswith("- name:"):
                army_name = line.strip()[len("- name:"):].strip().strip('"').strip("'")
                name_to_era[army_name] = current_era

        violations = []
        for army in armies:
            aname = army.get("name", "")
            if name_to_era.get(aname) != "modern":
                continue
            for wave in army.get("waves") or []:
                slots = float(wave.get("slots", 0))
                if slots > 40:
                    violations.append(f"{aname}: slots={slots} > 40")
        assert not violations, "Modern waves exceed 40 slots:\n" + "\n".join(violations)


# ---------------------------------------------------------------------------
# maps/default.yaml
# ---------------------------------------------------------------------------

class TestDefaultMapYaml:
    @pytest.fixture(scope="class")
    def mapdata(self):
        return _load("maps/default.yaml")

    def test_has_tiles_or_build_tiles(self, mapdata):
        assert "tiles" in mapdata or "build_tiles" in mapdata, (
            "maps/default.yaml must have 'tiles' or 'build_tiles' key"
        )

    def test_tiles_is_nonempty_dict(self, mapdata):
        tiles = mapdata.get("tiles")
        if tiles is not None:
            assert isinstance(tiles, dict) and len(tiles) > 0, (
                "maps/default.yaml 'tiles' must be a non-empty dict"
            )

    def test_loads_via_loader(self):
        from gameserver.loaders.map_loader import load_map
        hm = load_map(_CONFIG / "maps" / "default.yaml")
        assert len(hm.build_tiles) > 0 or len(hm.critter_path) > 0
