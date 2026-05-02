"""Military handlers — Strangler Fig domain module.

Contains armies, attacks, waves, siege, and spy handlers.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from gameserver.models.messages import GameMessage

log = logging.getLogger(__name__)


def _svc():
    from gameserver.network.handlers._core import _svc as _core_svc
    return _core_svc()


async def handle_military_request(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``military_request`` — return armies and attack status.

    Can query own armies or another empire's armies (for debug/testing).
    Use ``uid`` parameter to specify a different empire, or defaults to sender_uid.
    """
    svc = _svc()
    # Allow override via message.uid for debug/test access
    target_uid = sender_uid if sender_uid > 0 else getattr(message, "uid", 0) or 0
    empire = svc.empire_service.get(target_uid)
    if empire is None:
        return {
            "type": "military_response",
            "error": f"No empire found for uid {target_uid}",
        }

    armies = []
    for army in empire.armies:
        # Build waves list with details
        waves = []
        for wave in army.waves:
            waves.append({
                "wave_id": wave.wave_id,
                "iid": wave.iid,
                "slots": wave.slots,
                "max_era": wave.max_era,
                "next_slot_price": round(svc.empire_service._critter_slot_price(wave.slots + 1), 2),
                "next_era_price": round(svc.empire_service._wave_era_price(wave.max_era + 1), 2),
            })

        army_wave_count = len(army.waves)
        armies.append({
            "aid": army.aid,
            "name": army.name,
            "waves": waves,
            "next_wave_price": round(svc.empire_service._wave_price(army_wave_count + 1), 2),
        })

    # Get available critters based on completed research AND buildings
    completed: set[str] = set()
    for iid, remaining in empire.buildings.items():
        if remaining <= 0:
            completed.add(iid)
    for iid, remaining in empire.knowledge.items():
        if remaining <= 0:
            completed.add(iid)

    _item_era_index = svc.empire_service._item_era_index

    available_critters = []
    for critter in svc.upgrade_provider.available_critters(completed):
        available_critters.append({
            "iid": critter.iid,
            "name": critter.name,
            "description": critter.description,
            "era_index": _item_era_index.get(critter.iid, 0),
            "slots": critter.slots,
            "health": critter.health,
            "armour": critter.armour,
            "speed": critter.speed,
            "time_between_ms": critter.time_between_ms,
            "is_boss": critter.is_boss,
            "animation": critter.animation,
            "sprite": critter.sprite,
        })

    # Sprite lookup for all critters (including locked) so the frontend
    # can render sprites for critters already placed in waves.
    from gameserver.models.items import ItemType as _ItemType2
    critter_sprites = {
        c.iid: {"sprite": c.sprite, "animation": c.animation}
        for c in svc.upgrade_provider.get_by_type(_ItemType2.CRITTER)
    } if svc.upgrade_provider else {}

    # Ongoing attacks
    _uid_to_username: dict[int, str] = {}
    if svc.database is not None:
        for _urow in await svc.database.list_users():
            _uid_to_username[_urow["uid"]] = _urow["username"]

    def _attack_dto(a):
        if a.army_name_override:
            _army_name = a.army_name_override
        else:
            _att_emp = svc.empire_service.get(a.attacker_uid)
            _army_name = ""
            if _att_emp:
                for _arm in _att_emp.armies:
                    if _arm.aid == a.army_aid:
                        _army_name = _arm.name
                        break
        return {
            "attack_id": a.attack_id,
            "attacker_uid": a.attacker_uid,
            "defender_uid": a.defender_uid,
            "army_aid": a.army_aid,
            "army_name": _army_name,
            "attacker_username": _uid_to_username.get(a.attacker_uid, ""),
            "phase": a.phase.value,
            "eta_seconds": round(a.eta_seconds, 1),
            "total_eta_seconds": round(a.total_eta_seconds, 1),
            "siege_remaining_seconds": round(a.siege_remaining_seconds, 1),
            "total_siege_seconds": round(a.total_siege_seconds, 1),
            "is_spy": a.is_spy,
        }

    incoming = [_attack_dto(a) for a in svc.attack_service.get_incoming(target_uid)]
    outgoing = [_attack_dto(a) for a in svc.attack_service.get_outgoing(target_uid)]

    return {
        "type": "military_response",
        "armies": armies,
        "attacks_incoming": incoming,
        "attacks_outgoing": outgoing,
        "available_critters": available_critters,
        "critter_sprites": critter_sprites,
    }


async def handle_new_army(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``new_army`` — create a new army.

    Creates a new Army with no waves and adds it to the empire.
    """
    from gameserver.models.army import Army

    svc = _svc()
    name = getattr(message, "name", "").strip()
    target_uid = sender_uid if sender_uid > 0 else message.sender
    empire = svc.empire_service.get(target_uid)

    if empire is None:
        log.warning("new_army failed: no empire found for uid=%d", target_uid)
        return {
            "type": "new_army_response",
            "success": False,
            "error": "No empire found",
        }

    if not name:
        log.info("new_army failed uid=%d: name is empty", target_uid)
        return {
            "type": "new_army_response",
            "success": False,
            "error": "Army name cannot be empty",
        }

    # Calculate cost based on number of existing armies
    army_count = len(empire.armies)
    army_price = svc.empire_service._army_price(army_count + 1)

    # Check if player has enough gold
    current_gold = empire.resources.get('gold', 0.0)
    if current_gold < army_price:
        return {
            "type": "new_army_response",
            "success": False,
            "error": f"Not enough gold (need {army_price:.1f}, have {current_gold:.1f})",
        }

    # Deduct gold
    empire.resources['gold'] -= army_price

    # Get globally unique army ID
    new_aid = svc.empire_service.next_army_id()

    # Create new army with no waves
    new_army = Army(
        aid=new_aid,
        uid=target_uid,
        name=name,
        waves=[],
    )

    # Add to empire
    empire.armies.append(new_army)

    log.info("new_army success uid=%d aid=%d name=%s for %.1f gold", target_uid, new_aid, name, army_price)
    return {
        "type": "new_army_response",
        "success": True,
        "aid": new_aid,
        "name": name,
        "cost": round(army_price, 2),
    }


async def handle_new_attack(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``new_attack_request`` — launch an attack.

    Resolves the defender by ``target_uid`` (direct UID) or
    ``opponent_name`` (empire name lookup, legacy).  Validates army,
    deducts no gold yet, and creates the Attack via AttackService.
    """
    svc = _svc()
    target_uid = sender_uid if sender_uid > 0 else message.sender

    # Resolve defender: prefer target_uid, fall back to opponent_name for legacy
    defender_uid_raw = getattr(message, "target_uid", 0) or 0
    opponent_name = getattr(message, "opponent_name", "") or ""
    army_aid = getattr(message, "army_aid", 0) or 0

    log.debug("[new_attack] uid=%d target_uid=%r opponent_name=%r army_aid=%r",
              target_uid, defender_uid_raw, opponent_name, army_aid)

    if defender_uid_raw:
        defender_uid = defender_uid_raw
    elif opponent_name.strip():
        defender = svc.empire_service.find_by_name(opponent_name.strip())
        if defender is None:
            available_empires = [e.name for e in svc.empire_service.all_empires.values()]
            log.warning("[new_attack] FAIL uid=%d: empire %r not found (available: %s)",
                     target_uid, opponent_name, available_empires)
            return {
                "type": "attack_response",
                "success": False,
                "error": f"Empire '{opponent_name.strip()}' not found",
                "_debug": f"Available empires: {available_empires}",
            }
        defender_uid = defender.uid
    else:
        log.warning("[new_attack] FAIL uid=%d: No target (target_uid=%d, opponent_name=%r, army_aid=%d)",
                    target_uid, defender_uid_raw, opponent_name, army_aid)
        return {
            "type": "attack_response",
            "success": False,
            "error": "No target specified (provide target_uid or opponent_name)",
            "_debug": f"Input: target_uid={defender_uid_raw}, opponent_name={opponent_name!r}, army_aid={army_aid}",
        }

    # Era check: attacker cannot attack a defender in a lower era
    from gameserver.util.eras import ERA_ORDER, ERA_LABELS_DE
    attacker_empire = svc.empire_service.get(target_uid)
    defender_empire = svc.empire_service.get(defender_uid)
    if attacker_empire is not None and defender_empire is not None:
        attacker_era = svc.empire_service.get_current_era(attacker_empire)
        defender_era = svc.empire_service.get_current_era(defender_empire)
        attacker_era_idx = ERA_ORDER.index(attacker_era) if attacker_era in ERA_ORDER else 0
        defender_era_idx = ERA_ORDER.index(defender_era) if defender_era in ERA_ORDER else 0
        if defender_era_idx < attacker_era_idx - 1:
            attacker_label = ERA_LABELS_DE.get(attacker_era, attacker_era)
            defender_label = ERA_LABELS_DE.get(defender_era, defender_era)
            return {
                "type": "attack_response",
                "success": False,
                "error": (
                    f"{defender_empire.name} is in the {defender_label} era — "
                    f"you ({attacker_label}) can only attack empires in the same or a higher era."
                ),
            }

    result = svc.attack_service.start_attack(
        attacker_uid=target_uid,
        defender_uid=defender_uid,
        army_aid=army_aid,
        empire_service=svc.empire_service,
    )

    if isinstance(result, str):
        log.warning("[new_attack] FAIL uid=%d: %s", target_uid, result)
        return {
            "type": "attack_response",
            "success": False,
            "error": result,
            "_debug": f"start_attack validation failed (attacker={target_uid}, defender={defender_uid}, army={army_aid})",
        }

    # result is an Attack object
    log.info("[new_attack] SUCCESS uid=%d → defender=%d army=%d attack_id=%d ETA=%.1fs total=%.1fs",
             target_uid, defender_uid, army_aid, result.attack_id, result.eta_seconds, result.total_eta_seconds)
    return {
        "type": "attack_response",
        "success": True,
        "attack_id": result.attack_id,
        "defender_uid": defender_uid,
        "attacker_uid": target_uid,
        "army_aid": army_aid,
        "eta_seconds": round(result.eta_seconds, 1),
        "total_eta_seconds": round(result.total_eta_seconds, 1),
        "total_siege_seconds": round(result.total_siege_seconds, 1),
        "_debug": f"Attack {result.attack_id} created: {target_uid}→{defender_uid} (army {army_aid}, phase={result.phase.value})",
    }


def _build_spy_report(defender, svc) -> tuple[str, dict]:
    """Build a workshop intelligence report for the attacker.

    Returns (text_report, structured_data) covering only structures and critters
    of the defender's current era.
    """
    from gameserver.util.eras import ERA_ORDER, ERA_LABELS_EN
    from gameserver.models.items import ItemType

    era_key = svc.empire_service.get_current_era(defender)
    era_idx = ERA_ORDER.index(era_key) if era_key in ERA_ORDER else 0
    era_label = ERA_LABELS_EN.get(era_key, era_key)

    items = svc.upgrade_provider.items if svc.upgrade_provider else {}
    item_era_index = svc.empire_service._item_era_index
    upgrades = defender.item_upgrades

    structures = []
    critters = []
    for iid, item in items.items():
        if item_era_index.get(iid, -1) != era_idx:
            continue
        if item.item_type == ItemType.STRUCTURE:
            lvls = upgrades.get(iid, {})
            structures.append((item.name, lvls))
        elif item.item_type == ItemType.CRITTER:
            lvls = upgrades.get(iid, {})
            critters.append((item.name, lvls))

    def _fmt_upgrades(lvls: dict) -> str:
        if not lvls:
            return "(no upgrades)"
        abbrev = {"damage": "dmg", "range": "rng", "reload": "rld",
                  "effect_duration": "eff_dur", "effect_value": "eff_val",
                  "health": "hp", "speed": "spd", "armour": "arm"}
        parts = [f"{abbrev.get(k, k)}+{v}" for k, v in lvls.items() if v > 0]
        return " ".join(parts) if parts else "(no upgrades)"

    lines = [
        f"🔬 Workshop Intelligence — {era_label}",
        "─" * 32,
        "─── Towers ───",
    ]
    for name, lvls in sorted(structures):
        lines.append(f"  🗼 {name:<20} {_fmt_upgrades(lvls)}")
    if not structures:
        lines.append("  (none)")
    lines.append("─── Units ───")
    for name, lvls in sorted(critters):
        lines.append(f"  ⚔ {name:<20} {_fmt_upgrades(lvls)}")
    if not critters:
        lines.append("  (none)")
    lines.append("─" * 32)

    text = "\n".join(lines)
    data = {
        "era": era_label,
        "era_idx": era_idx,
        "structures": [{"name": n, "upgrades": lvl} for n, lvl in sorted(structures)],
        "critters": [{"name": n, "upgrades": lvl} for n, lvl in sorted(critters)],
    }
    return text, data


async def handle_spy_attack(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle a spy attack request.

    Sends the attacker's first army as a fake attack. The defender sees it
    arrive but it resolves immediately (no battle). The attacker gets a
    workshop intelligence report.
    """
    svc = _svc()
    attacker_uid = sender_uid if sender_uid > 0 else message.sender

    defender_uid_raw = getattr(message, "target_uid", 0) or 0
    opponent_name = getattr(message, "opponent_name", "") or ""

    if defender_uid_raw:
        defender_uid = defender_uid_raw
    elif opponent_name.strip():
        defender = svc.empire_service.find_by_name(opponent_name.strip())
        if defender is None:
            return {"type": "spy_attack_response", "success": False,
                    "error": f"Empire '{opponent_name.strip()}' not found"}
        defender_uid = defender.uid
    else:
        return {"type": "spy_attack_response", "success": False,
                "error": "No target specified"}

    if attacker_uid == defender_uid:
        return {"type": "spy_attack_response", "success": False,
                "error": "Cannot spy on yourself"}

    att_empire = svc.empire_service.get(attacker_uid)
    if att_empire is None:
        return {"type": "spy_attack_response", "success": False, "error": "No empire found"}

    if not att_empire.armies:
        return {"type": "spy_attack_response", "success": False,
                "error": "You need at least one army to send a spy"}

    max_spy = svc.game_config.max_spy_armies if svc.game_config else 1
    active_spy_count = sum(
        1 for a in svc.attack_service.get_outgoing(attacker_uid) if a.is_spy
    )
    if active_spy_count >= max_spy:
        return {"type": "spy_attack_response", "success": False,
                "error": f"Spy already dispatched (max {max_spy} active)"}

    # Use first army (lowest aid)
    first_army = min(att_empire.armies, key=lambda a: a.aid)
    if not first_army.waves:
        return {"type": "spy_attack_response", "success": False,
                "error": "First army has no waves"}

    result = svc.attack_service.start_attack(
        attacker_uid=attacker_uid,
        defender_uid=defender_uid,
        army_aid=first_army.aid,
        empire_service=svc.empire_service,
        is_spy=True,
        spy_army_name=first_army.name,
    )

    if isinstance(result, str):
        return {"type": "spy_attack_response", "success": False, "error": result}

    log.info("[spy_attack] uid=%d → defender=%d army=%d attack_id=%d ETA=%.1fs",
             attacker_uid, defender_uid, first_army.aid, result.attack_id, result.eta_seconds)
    return {
        "type": "spy_attack_response",
        "success": True,
        "attack_id": result.attack_id,
        "defender_uid": defender_uid,
        "army_aid": first_army.aid,
        "eta_seconds": round(result.eta_seconds, 1),
    }


async def handle_change_army(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``change_army`` — rename an army.

    Updates the name of an existing army owned by the sender.
    """
    svc = _svc()
    aid = getattr(message, "aid", 0)
    name = getattr(message, "name", "").strip()
    target_uid = sender_uid if sender_uid > 0 else message.sender
    empire = svc.empire_service.get(target_uid)

    if empire is None:
        log.warning("change_army failed: no empire found for uid=%d", target_uid)
        return {
            "type": "change_army_response",
            "success": False,
            "error": "No empire found",
        }

    # Find the army by aid
    army = None
    for a in empire.armies:
        if a.aid == aid:
            army = a
            break

    if army is None:
        log.warning("change_army failed uid=%d: army aid=%d not found", target_uid, aid)
        return {
            "type": "change_army_response",
            "success": False,
            "error": f"Army {aid} not found",
        }

    if not name:
        log.info("change_army failed uid=%d aid=%d: name is empty", target_uid, aid)
        return {
            "type": "change_army_response",
            "success": False,
            "error": "Army name cannot be empty",
        }

    # Update the name
    old_name = army.name
    army.name = name

    log.info("change_army success uid=%d aid=%d: '%s' → '%s'", target_uid, aid, old_name, name)
    return {
        "type": "change_army_response",
        "success": True,
        "aid": aid,
        "name": name,
    }


async def handle_new_wave(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``new_wave`` — add a critter wave to an army.

    Creates a new wave with SLAVE critters (5 slots).
    The server always decides the critter type.
    """
    from gameserver.models.army import CritterWave

    svc = _svc()
    aid = getattr(message, "aid", 0)
    target_uid = sender_uid if sender_uid > 0 else message.sender
    empire = svc.empire_service.get(target_uid)

    if empire is None:
        log.warning("new_wave failed: no empire found for uid=%d", target_uid)
        return {
            "type": "new_wave_response",
            "success": False,
            "error": "No empire found",
        }

    # Find the army by aid
    army = None
    for a in empire.armies:
        if a.aid == aid:
            army = a
            break

    if army is None:
        log.warning("new_wave failed uid=%d: army aid=%d not found", target_uid, aid)
        return {
            "type": "new_wave_response",
            "success": False,
            "error": f"Army {aid} not found",
        }

    # Create new wave with iid and slots (no concrete critters)
    import gameserver.network.handlers._core as _core_mod
    new_wave = CritterWave(
        wave_id=_core_mod._next_wid,
        iid="SLAVE",
        slots=1,
    )
    _core_mod._next_wid += 1

    # Add to army
    army.waves.append(new_wave)

    log.info("new_wave success uid=%d aid=%d wave_id=%d with 1 SLAVE slot", target_uid, aid, new_wave.wave_id)
    return {
        "type": "new_wave_response",
        "success": True,
        "aid": aid,
        "wave_id": new_wave.wave_id,
        "critter_iid": new_wave.iid,
        "slots": new_wave.slots,
        "wave_count": len(army.waves),
    }


async def handle_change_wave(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``change_wave`` — modify critter type or count in an existing wave.

    Supports changing:
    - critter_iid: replace critter type in the wave
    - slots: number of critter slots in the wave

    The wave contains only metadata (iid, slots), not concrete critters.
    """
    svc = _svc()
    aid = getattr(message, "aid", 0)
    wave_number = getattr(message, "wave_number", 0)
    critter_iid = getattr(message, "critter_iid", "").strip()
    slots = getattr(message, "slots", None)
    target_uid = sender_uid if sender_uid > 0 else message.sender
    empire = svc.empire_service.get(target_uid)

    if empire is None:
        log.warning("change_wave failed: no empire found for uid=%d", target_uid)
        return {
            "type": "change_wave_response",
            "success": False,
            "error": "No empire found",
        }

    # Find the army by aid
    army = None
    for a in empire.armies:
        if a.aid == aid:
            army = a
            break

    if army is None:
        log.warning("change_wave failed uid=%d: army aid=%d not found", target_uid, aid)
        return {
            "type": "change_wave_response",
            "success": False,
            "error": f"Army {aid} not found",
        }

    # Find the wave by wave_number (0-indexed)
    if wave_number < 0 or wave_number >= len(army.waves):
        log.warning("change_wave failed uid=%d aid=%d: wave_number=%d out of range",
                    target_uid, aid, wave_number)
        return {
            "type": "change_wave_response",
            "success": False,
            "error": f"Wave {wave_number} not found",
        }

    wave = army.waves[wave_number]

    # Change critter type if provided
    if critter_iid:
        # Validate critter era against wave's max_era using requirement-based lookup
        if svc.upgrade_provider and svc.empire_service:
            from gameserver.util.eras import ERA_ORDER as _ERA_ORDER2
            _req_era: dict[str, int] = {}
            if svc.empire_service._knowledge_era_groups:
                for era_key, iids in svc.empire_service._knowledge_era_groups.items():
                    idx = _ERA_ORDER2.index(era_key) if era_key in _ERA_ORDER2 else 0
                    for iid in iids:
                        _req_era[iid] = idx
            critter_item = svc.upgrade_provider.items.get(critter_iid)
            if critter_item and critter_item.requirements:
                critter_era_idx = max((_req_era.get(r, 0) for r in critter_item.requirements), default=0)
                if critter_era_idx > wave.max_era:
                    return {
                        "type": "change_wave_response",
                        "success": False,
                        "error": f"Critter era (index {critter_era_idx}) exceeds wave max era (index {wave.max_era})",
                    }
        wave.iid = critter_iid
        log.info("change_wave: updated wave %d critter type to %s", wave_number, critter_iid)

    # Update slots if provided
    if slots is not None and slots > 0:
        old_slots = wave.slots
        wave.slots = slots
        log.info("change_wave: updated wave %d slots from %d to %d", wave_number, old_slots, slots)

    log.info("change_wave success uid=%d aid=%d wave=%d critter_iid=%s slots=%d",
             target_uid, aid, wave_number, wave.iid, wave.slots)
    return {
        "type": "change_wave_response",
        "success": True,
        "aid": aid,
        "wave_number": wave_number,
        "critter_iid": wave.iid,
        "slots": wave.slots,
    }


async def handle_end_siege(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Handle ``end_siege`` — end the ongoing siege on sender's empire.

    TODO: Call empire.end_siege().
    """
    log.info("end_siege from uid=%d (not yet implemented)", sender_uid)
    return None


async def handle_buy_wave_request(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Buy a new wave for an army with gold.

    Cost based on total number of waves across all armies.
    """
    from gameserver.models.army import CritterWave

    svc = _svc()
    target_uid = sender_uid if sender_uid > 0 else message.sender
    empire = svc.empire_service.get(target_uid)

    if empire is None:
        return {
            "type": "buy_wave_response",
            "success": False,
            "error": f"No empire found for uid {target_uid}",
        }

    aid = getattr(message, 'aid', None)
    if aid is None:
        return {
            "type": "buy_wave_response",
            "success": False,
            "error": "Missing army ID (aid)",
        }

    # Find the army
    army = None
    for a in empire.armies:
        if a.aid == aid:
            army = a
            break

    if army is None:
        return {
            "type": "buy_wave_response",
            "success": False,
            "error": f"Army {aid} not found",
        }

    # Calculate cost based on waves in this specific army
    wave_price = svc.empire_service._wave_price(len(army.waves) + 1)

    # Check if player has enough gold
    current_gold = empire.resources.get('gold', 0.0)
    if current_gold < wave_price:
        return {
            "type": "buy_wave_response",
            "success": False,
            "error": f"Not enough gold (need {wave_price:.1f}, have {current_gold:.1f})",
        }

    # Deduct gold
    empire.resources['gold'] -= wave_price

    # Create new wave with default critter (SLAVE) and 1 slot
    import gameserver.network.handlers._core as _core_mod
    new_wave = CritterWave(
        wave_id=_core_mod._next_wid,
        iid="SLAVE",
        slots=1,
    )
    _core_mod._next_wid += 1

    # Add to army
    army.waves.append(new_wave)

    log.info(f"Wave purchased for army {aid} by empire {empire.name} (uid={target_uid}) for {wave_price:.1f} gold")

    return {
        "type": "buy_wave_response",
        "success": True,
        "aid": aid,
        "wave_id": new_wave.wave_id,
        "cost": round(wave_price, 2),
        "wave_count": len(army.waves),
    }


async def handle_buy_critter_slot_request(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Buy an additional critter slot for a wave with gold.

    Cost based on total number of critter slots across all waves.
    """
    svc = _svc()
    target_uid = sender_uid if sender_uid > 0 else message.sender
    empire = svc.empire_service.get(target_uid)

    if empire is None:
        return {
            "type": "buy_critter_slot_response",
            "success": False,
            "error": f"No empire found for uid {target_uid}",
        }

    aid = getattr(message, 'aid', None)
    wave_number = getattr(message, 'wave_number', None)

    if aid is None or wave_number is None:
        return {
            "type": "buy_critter_slot_response",
            "success": False,
            "error": "Missing army ID (aid) or wave number",
        }

    # Find the army
    army = None
    for a in empire.armies:
        if a.aid == aid:
            army = a
            break

    if army is None:
        return {
            "type": "buy_critter_slot_response",
            "success": False,
            "error": f"Army {aid} not found",
        }

    # Find the wave
    if wave_number < 0 or wave_number >= len(army.waves):
        return {
            "type": "buy_critter_slot_response",
            "success": False,
            "error": f"Wave {wave_number} not found",
        }

    wave = army.waves[wave_number]

    # Calculate cost based on slots in this specific wave only
    slot_price = svc.empire_service._critter_slot_price(wave.slots + 1)

    # Check if player has enough gold
    current_gold = empire.resources.get('gold', 0.0)
    if current_gold < slot_price:
        return {
            "type": "buy_critter_slot_response",
            "success": False,
            "error": f"Not enough gold (need {slot_price:.1f}, have {current_gold:.1f})",
        }

    # Deduct gold
    empire.resources['gold'] -= slot_price

    # Increase slot count
    old_slots = wave.slots
    wave.slots += 1

    log.info(f"Critter slot purchased for army {aid} wave {wave_number} by empire {empire.name} (uid={target_uid}) for {slot_price:.1f} gold (slots: {old_slots} → {wave.slots})")

    return {
        "type": "buy_critter_slot_response",
        "success": True,
        "aid": aid,
        "wave_number": wave_number,
        "new_slots": wave.slots,
        "cost": round(slot_price, 2),
    }


async def handle_buy_wave_era_request(
    message: GameMessage, sender_uid: int,
) -> Optional[dict[str, Any]]:
    """Buy an era upgrade for a wave with gold. Max era index is 8 (ZUKUNFT)."""
    MAX_ERA_INDEX = 8
    svc = _svc()
    target_uid = sender_uid if sender_uid > 0 else message.sender
    empire = svc.empire_service.get(target_uid)

    if empire is None:
        return {"type": "buy_wave_era_response", "success": False, "error": f"No empire found for uid {target_uid}"}

    aid = getattr(message, 'aid', None)
    wave_number = getattr(message, 'wave_number', None)

    if aid is None or wave_number is None:
        return {"type": "buy_wave_era_response", "success": False, "error": "Missing aid or wave_number"}

    army = next((a for a in empire.armies if a.aid == aid), None)
    if army is None:
        return {"type": "buy_wave_era_response", "success": False, "error": f"Army {aid} not found"}

    if wave_number < 0 or wave_number >= len(army.waves):
        return {"type": "buy_wave_era_response", "success": False, "error": f"Wave {wave_number} not found"}

    wave = army.waves[wave_number]

    if wave.max_era >= MAX_ERA_INDEX:
        return {"type": "buy_wave_era_response", "success": False, "error": "Wave already at maximum era"}

    era_price = svc.empire_service._wave_era_price(wave.max_era + 1)
    current_gold = empire.resources.get('gold', 0.0)
    if current_gold < era_price:
        return {"type": "buy_wave_era_response", "success": False, "error": f"Not enough gold (need {era_price:.1f}, have {current_gold:.1f})"}

    empire.resources['gold'] -= era_price
    old_era = wave.max_era
    wave.max_era += 1

    next_price = svc.empire_service._wave_era_price(wave.max_era + 1) if wave.max_era < MAX_ERA_INDEX else None
    log.info(f"Wave era upgraded for army {aid} wave {wave_number} by uid={target_uid}: era {old_era} → {wave.max_era} for {era_price:.1f} gold")

    return {
        "type": "buy_wave_era_response",
        "success": True,
        "aid": aid,
        "wave_number": wave_number,
        "new_max_era": wave.max_era,
        "cost": round(era_price, 2),
        "next_era_price": round(next_price, 2) if next_price is not None else None,
    }
