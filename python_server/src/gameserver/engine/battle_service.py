"""Battle service — real-time tower-defense battle simulation.

Runs each battle as an independent asyncio task with ~15ms tick rate.

Tick order (must be preserved):
1. step_critters  — movement along hex path + burn tick; marks reached_goal
2. step_towers    — acquire targets + fire (skips reached_goal critters)
3. step_shots     — decrement flight time, apply damage on arrival;
                    can still kill reached_goal critters at the gate
4. flush_reached  — apply castle damage or critter_died for reached critters
5. step_armies    — wave timers + critter spawning
6. broadcast      — send delta to observers (throttled to 250ms)

Architecture (Java-equivalent):
  Server computes movement & combat; sends delta events every 250ms.
  Client receives critter paths + speed and autonomously animates them.
  Only events (spawn / die / finish / shot) are sent — no position spam.

Provides deterministic tick function for testing (explicit dt_ms).
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from collections import deque
from typing import TYPE_CHECKING, Any, Callable, Awaitable

from gameserver.models.critter import Critter
from gameserver.models.hex import HexCoord
from gameserver.models.shot import Shot
from gameserver.engine.hex_pathfinding import critter_hex_pos, hex_world_distance

# Visual shot type constants (sent to client for rendering only)
_VISUAL_NORMAL = 0
_VISUAL_SLOW   = 1
_VISUAL_BURN   = 2
_VISUAL_SPLASH = 3

def _shot_visual_type(effects: dict[str, Any]) -> int:
    """Derive a visual shot-type integer from the effects dict (for client rendering only)."""
    if "splash_radius" in effects:
        return _VISUAL_SPLASH
    if "burn_dps" in effects or "burn_duration" in effects:
        return _VISUAL_BURN
    if "slow_duration" in effects or "slow_ratio" in effects:
        return _VISUAL_SLOW
    return _VISUAL_NORMAL

if TYPE_CHECKING:
    from gameserver.models.battle import BattleState
    from gameserver.models.empire import Empire
    from gameserver.models.army import Army
    from gameserver.models.structure import Structure

log = logging.getLogger(__name__)

# Next unique critter instance id (global counter)
_next_cid: int = 1


def _new_cid() -> int:
    global _next_cid
    cid = _next_cid
    _next_cid += 1
    return cid


# ── Hex-path BFS ────────────────────────────────────────────

def find_hex_path(
    start: tuple[int, int],
    end: tuple[int, int],
    passable: set[tuple[int, int]],
) -> list[HexCoord]:
    """BFS shortest path on hex grid. Returns list of HexCoord including start+end."""
    queue: deque[tuple[tuple[int, int], list[tuple[int, int]]]] = deque()
    queue.append((start, [start]))
    visited = {start}

    _dirs = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]

    while queue:
        (q, r), path = queue.popleft()
        if (q, r) == end:
            return [HexCoord(pq, pr) for pq, pr in path]
        for dq, dr in _dirs:
            nq, nr = q + dq, r + dr
            if (nq, nr) not in visited and (nq, nr) in passable:
                visited.add((nq, nr))
                queue.append(((nq, nr), path + [(nq, nr)]))
    return []


class BattleService:
    """Service that runs and manages tower-defense battles.

    Uses a send_fn callback for network I/O so the service stays
    decoupled from the WebSocket server.
    """

    def __init__(self, items: list[Any] | dict[str, Any] | None = None, gc: Any = None) -> None:
        """Initialize battle service.

        Args:
            items: List or dict of ItemDetails for looking up critter stats.
            gc: GameConfig instance for upgrade definitions.
        """
        if items is None:
            self._items_by_iid = {}
        elif isinstance(items, dict):
            self._items_by_iid = items
        else:
            self._items_by_iid = {item.iid: item for item in items}
        self._gc = gc

    def _get_wave_critter_slot_cost(self, wave: Any) -> float:
        """Return the slot cost for the next critter of this wave."""
        item = self._items_by_iid.get(wave.iid)
        return max(0.1, float(getattr(item, "slots", 1.0) or 1.0))

    def _mark_wave_complete_if_blocked(self, wave: Any) -> bool:
        """Mark a wave complete when its remaining slots cannot fit another critter.
        
        Always lets the first critter through regardless of slot cost.
        """
        if wave.num_critters_spawned >= wave.slots:
            return True

        remaining_slots = wave.slots - wave.num_critters_spawned
        if remaining_slots <= 0:
            wave.num_critters_spawned = wave.slots
            wave.next_critter_ms = 0
            return True

        # If nothing has been spawned yet, never block — guarantee at least one critter.
        if wave.num_critters_spawned == 0:
            return False

        critter_slot_cost = self._get_wave_critter_slot_cost(wave)
        if critter_slot_cost > remaining_slots:
            log.info(
                "[SPAWN] Wave %d completed early: remaining_slots=%.2f cannot fit critter %s (cost=%.2f)",
                wave.wave_id,
                remaining_slots,
                wave.iid,
                critter_slot_cost,
            )
            wave.num_critters_spawned = wave.slots
            wave.next_critter_ms = 0
            return True

        return False

    # ── Main loop ──────────────────────────────────────────────

    async def run_battle(
        self,
        battle: BattleState,
        send_fn: Callable[[int, dict[str, Any]], Awaitable[bool]],
        broadcast_interval_ms: float = 250.0,
    ) -> None:
        """Run a battle to completion as an asyncio task.

        Args:
            battle: Mutable battle state.
            send_fn: Async callable (uid, data_dict) -> bool used to
                     push messages to connected clients.
            broadcast_interval_ms: Network broadcast interval in milliseconds
                                   (from game.yaml configuration).
        """
        battle.broadcast_interval_ms = broadcast_interval_ms
        battle.broadcast_timer_ms = broadcast_interval_ms
        
        log.info("[battle_loop] Starting battle (bid=%d, defender=%d, attackers=%s)",
                 battle.bid, battle.defender.uid if battle.defender else None, battle.attacker_uids)
        
        last = time.monotonic()
        while battle.keep_alive:
            now = time.monotonic()
            dt_ms = (now - last) * 1000.0
            last = now

            self.tick(battle, dt_ms)

            if battle.should_broadcast():
                await self._broadcast(battle, send_fn)

            if battle.is_finished:
                break  # Caller (_run_battle_task) sends summary after computing loot

            await asyncio.sleep(0.015)

    # ── Deterministic tick (also used by tests) ────────────────

    def tick(self, battle: BattleState, dt_ms: float) -> None:
        """Execute one deterministic battle tick.

        Tick order (critters move first so in-flight shots can intercept
        critters that reach the goal in the same tick):
        1. step_critters  — move + mark reached_goal (don't remove yet)
        2. step_towers    — fire at live critters (skips reached_goal)
        3. step_shots     — arriving shots can still kill reached_goal critters
        4. flush_reached  — apply castle damage or critter_died for reached
        5. step_armies    — spawn new critters
        """
        self._step_critters(battle, dt_ms)
        self._step_towers(battle, dt_ms)
        self._step_shots(battle, dt_ms)
        self._flush_reached(battle)
        self._step_armies(battle, dt_ms)
        battle.elapsed_ms += dt_ms
        battle.broadcast_timer_ms -= dt_ms
        self._check_finished(battle)
        
        # Log active critter count periodically
        #if battle.elapsed_ms % 1000 < dt_ms:  # Every ~1 second
        #    log.info("[battle %d] Active critters: %d", battle.bid, len(battle.critters))

    # -- Shot resolution -------------------------------------------------

    def _step_shots(self, battle: BattleState, dt_ms: float) -> None:
        """Decrement flight time, apply damage/effects when shots arrive."""
        shots_to_remove = []
        
        for shot in battle.pending_shots:
            # Store original flight time for path_progress calculation
            if shot.path_progress == 0.0:
                # First tick, store total flight time in a way we can access it
                # We'll use the ratio of flight_remaining_ms to calculate progress
                shot._total_flight_ms = shot.flight_remaining_ms
            
            # Decrement flight time
            shot.flight_remaining_ms -= dt_ms
            
            # Update path_progress (0.0 at start, 1.0 at arrival)
            if hasattr(shot, '_total_flight_ms') and shot._total_flight_ms > 0:
                shot.path_progress = 1.0 - (shot.flight_remaining_ms / shot._total_flight_ms)
                shot.path_progress = max(0.0, min(1.0, shot.path_progress))
            
            # Check if shot has arrived
            if shot.flight_remaining_ms <= 0:
                self._apply_shot_damage(battle, shot)
                shots_to_remove.append(shot)
        
        # Remove resolved shots
        for shot in shots_to_remove:
            battle.pending_shots.remove(shot)
    
    def _apply_shot_damage(self, battle: BattleState, shot: Shot) -> None:
        """Apply damage and effects from a shot to its target critter."""
        critter = battle.critters.get(shot.target_cid)
        if not critter:
            log.debug("[SHOT] Shot %d->%d missed (target not found)", shot.source_sid, shot.target_cid)
            return

        # Apply base damage (reduced by armour, minimum 0.5; zero if tower has 0 base damage)
        has_burn = "burn_dps" in shot.effects or "burn_duration" in shot.effects
        damage = max(0.5, shot.damage - critter.armour) if shot.damage > 0 else 0.0
        if damage > 0:
            critter.health -= damage
        log.debug("[HIT] Critter cid=%d hit by sid=%d for %.1f damage (remaining health: %.1f)",
                  critter.cid, shot.source_sid, damage, critter.health)

        # Apply slow effect if effects dict contains slow keys
        if "slow_duration" in shot.effects or "slow_ratio" in shot.effects:
            slow_ratio       = float(shot.effects.get("slow_ratio", 0.5))
            slow_duration_ms = float(shot.effects.get("slow_duration", 2000.0))
            critter.slow_remaining_ms = slow_duration_ms
            critter.slow_speed = critter.speed * slow_ratio
            log.debug("[SLOW] Critter cid=%d slowed to %.2f hex/s for %.0fms",
                      critter.cid, critter.slow_speed, critter.slow_remaining_ms)

        # Apply burn effect if effects dict contains burn keys
        if has_burn:
            critter.burn_remaining_ms = float(shot.effects.get("burn_duration", 3000.0))
            critter.burn_dps          = float(shot.effects.get("burn_dps", 1.0))
            log.debug("[BURN] Critter cid=%d burning for %.1f dps over %.0fms",
                      critter.cid, critter.burn_dps, critter.burn_remaining_ms)

        # Apply splash damage (and effects) to nearby critters
        if "splash_radius" in shot.effects and critter.path:
            splash_radius = float(shot.effects["splash_radius"])
            impact_q, impact_r = critter_hex_pos(critter.path, critter.path_progress)
            has_splash_slow = "slow_duration" in shot.effects or "slow_ratio" in shot.effects
            has_splash_burn = "burn_dps" in shot.effects or "burn_duration" in shot.effects
            for other_cid, other in list(battle.critters.items()):
                if other_cid == critter.cid or not other.path:
                    continue
                oq, or_ = critter_hex_pos(other.path, other.path_progress)
                dist = hex_world_distance(impact_q, impact_r, oq, or_)
                if dist <= splash_radius:
                    splash_dmg = max(0.5, shot.damage - other.armour) if shot.damage > 0 else 0.0
                    other.health -= splash_dmg
                    if has_splash_slow:
                        other.slow_remaining_ms = float(shot.effects.get("slow_duration", 2000.0))
                        other.slow_speed = other.speed * float(shot.effects.get("slow_ratio", 0.5))
                    if has_splash_burn:
                        other.burn_remaining_ms = float(shot.effects.get("burn_duration", 3000.0))
                        other.burn_dps = float(shot.effects.get("burn_dps", 1.0))
                    log.debug("[SPLASH] Critter cid=%d hit for %.1f dmg (dist=%.2f, slow=%s, burn=%s)",
                              other_cid, splash_dmg, dist, has_splash_slow, has_splash_burn)

    # -- Critter movement ------------------------------------------------

    def _step_critters(self, battle: BattleState, dt_ms: float) -> None:
        """Move all critters, handle death, mark those that reach the goal.

        Critters that reach path_progress >= 1.0 are marked reached_goal=True
        but NOT removed here.  _flush_reached (called after _step_shots) handles
        removal so that in-flight shots from previous ticks can still intercept
        them at the castle gate.
        """
        for cid, critter in list(battle.critters.items()):
            if critter.reached_goal:
                # Already at the gate — will be flushed after shots resolve.
                # Check if a shot killed it between steps.
                if critter.health <= 0:
                    self._critter_died(battle, critter)
                continue

            # Move critter (if alive and still on path)
            if critter.health > 0 and critter.path_progress < 1.0:
                self._move_critter(battle, critter, dt_ms)

            # Check final state after movement
            if critter.health <= 0:
                self._critter_died(battle, critter)
            elif critter.path_progress >= 1.0:
                critter.reached_goal = True  # defer removal until after shots
                    


    def _move_critter(self, battle: BattleState, critter: Critter, dt_ms: float) -> None:
        """Move a critter along its path based on speed and effects.
        
        Updates critter.path_progress (normalized 0.0 to 1.0) based on:
        - Base speed (hex tiles per second)
        - Slow effects (reduces speed)
        - Time delta (dt_ms)
        - Path length normalization
        """
        if not critter.path or len(critter.path) < 2:
            return
        
        # Calculate effective speed (reduced by slow effects)
        effective_speed = critter.speed
        if critter.slow_remaining_ms > 0:
            effective_speed = critter.slow_speed
        
        # Distance traveled in this tick (in hex tiles)
        dt_s = dt_ms / 1000.0
        distance = effective_speed * dt_s
        
        # Normalize by path length to get progress in [0, 1]
        path_length = len(critter.path) - 1
        if path_length > 0:
            normalized_distance = distance / path_length
            critter.path_progress += normalized_distance
        
        # Clamp to valid range [0.0, 1.0]
        critter.path_progress = max(0.0, min(1.0, critter.path_progress))
        
        # Apply burn damage if burning
        if critter.burn_remaining_ms > 0:
            # Calculate actual burn time (might be less than dt_ms if effect expires)
            burn_time_ms = min(dt_ms, critter.burn_remaining_ms)
            burn_damage = critter.burn_dps * (burn_time_ms / 1000.0)
            
            critter.health = max(0, critter.health - burn_damage)
            critter.burn_remaining_ms -= dt_ms
            critter.burn_remaining_ms = max(0.0, critter.burn_remaining_ms)
            
            if burn_damage > 0:
                log.debug("[BURN] Critter %d takes %.1f burn damage (remaining: %.0fms)", 
                          critter.cid, burn_damage, critter.burn_remaining_ms)
        
        # Decrement slow effect timer
        if critter.slow_remaining_ms > 0:
            critter.slow_remaining_ms -= dt_ms
            critter.slow_remaining_ms = max(0.0, critter.slow_remaining_ms)
            
        

    # -- Tower targeting & firing ----------------------------------------

    def _step_towers(self, battle: BattleState, dt_ms: float) -> None:
        """Towers acquire targets and fire shots."""
        defender = battle.defender
        su = self._gc.structure_upgrades if self._gc else None
        item_upgrades = defender.item_upgrades if defender else {}

        for sid, structure in battle.structures.items():
            # Per-IID upgrade levels for this tower
            iid_upgrades = item_upgrades.get(structure.iid, {})
            dmg_lvl    = iid_upgrades.get("damage", 0)
            rng_lvl    = iid_upgrades.get("range", 0)
            rld_lvl    = iid_upgrades.get("reload", 0)
            efdur_lvl  = iid_upgrades.get("effect_duration", 0)
            efval_lvl  = iid_upgrades.get("effect_value", 0)

            damage_mult = 1.0 + (su.damage / 100.0) * dmg_lvl if su else 1.0
            range_mult  = 1.0 + (su.range  / 100.0) * rng_lvl if su else 1.0
            reload_mult = 1.0 + (su.reload / 100.0) * rld_lvl if su else 1.0

            # Decrement reload timer (reload upgrade speeds up reload)
            if structure.reload_remaining_ms > 0:
                structure.reload_remaining_ms -= dt_ms * reload_mult

            # Check if tower is ready to fire
            if structure.reload_remaining_ms <= 0:
                effective_range = structure.range * range_mult
                target = self._find_target(battle, structure, range_override=effective_range)

                if target:
                    cq, cr = critter_hex_pos(target.path, target.path_progress)
                    distance = hex_world_distance(
                        float(structure.position.q), float(structure.position.r), cq, cr
                    )
                    flight_time_ms = (distance / structure.shot_speed) * 1000.0 if structure.shot_speed > 0 else 0.0

                    # Apply effect_duration and effect_value upgrades to shot effects
                    shot_effects = dict(structure.effects)
                    if su and (efdur_lvl > 0 or efval_lvl > 0):
                        efdur_mult   = 1.0 + (su.effect_duration / 100.0) * efdur_lvl
                        efval_mult   = 1.0 + (su.effect_value / 100.0) * efval_lvl
                        for k in ("slow_duration", "burn_duration"):
                            if k in shot_effects:
                                shot_effects[k] = shot_effects[k] * efdur_mult
                        for k in ("slow_ratio", "burn_dps"):
                            if k in shot_effects:
                                shot_effects[k] = shot_effects[k] * efval_mult

                    shot = Shot(
                        damage=structure.damage * damage_mult,
                        target_cid=target.cid,
                        source_sid=sid,
                        effects=shot_effects,
                        flight_remaining_ms=flight_time_ms,
                        origin=structure.position,
                        path_progress=0.0,
                    )
                    
                    # Add to pending shots
                    battle.pending_shots.append(shot)
                    
                    # Update tower state
                    structure.focus_cid = target.cid
                    structure.reload_remaining_ms = structure.reload_time_ms
                    
                    log.debug("[SHOT] Tower sid=%d fired at critter cid=%d (distance=%.1f, flight_time=%.0fms)",
                             sid, target.cid, distance, flight_time_ms)
    
    def _find_target(self, battle: BattleState, structure: Structure,
                     range_override: float | None = None) -> Critter | None:
        """Find a critter within range using the structure's targeting strategy.

        Strategies:
          first  — most-advanced critter (highest path_progress, closest to finish)
          last   — least-advanced critter (lowest path_progress, furthest from spawn)
          random — random critter among those in range

        Args:
            range_override: If set, use this range instead of structure.range
                            (used when range_modifier effect is active).
        """
        in_range: list[Critter] = []

        tq, tr = float(structure.position.q), float(structure.position.r)
        effective_range = range_override if range_override is not None else structure.range

        for critter in battle.critters.values():
            if not critter.path or critter.reached_goal:
                continue

            # Interpolated critter position (between two hex centers)
            cq, cr = critter_hex_pos(critter.path, critter.path_progress)

            # Check if in range (continuous hex-world distance)
            distance = hex_world_distance(tq, tr, cq, cr)
            if distance <= effective_range:
                in_range.append(critter)

        if not in_range:
            return None

        strategy = structure.select
        if strategy == "last":
            return min(in_range, key=lambda c: c.path_progress)
        if strategy == "random":
            return random.choice(in_range)
        # default: "first" — highest path_progress
        return max(in_range, key=lambda c: c.path_progress)

    def _flush_reached(self, battle: BattleState) -> None:
        """Process critters marked reached_goal after shots have been applied.

        Called after _step_shots so that in-flight shots had a chance to kill
        critters at the gate before they deal castle damage.
        """
        for critter in list(battle.critters.values()):
            if not critter.reached_goal:
                continue
            if critter.health <= 0:
                self._critter_died(battle, critter)
            else:
                self._critter_finished(battle, critter)

    # -- Army wave dispatch ---------

    def build_upcoming_waves(self, armies: "dict[Any, Any]") -> list[dict[str, Any]]:
        """Return sorted list of next unstarted waves across all armies with eta_ms."""
        upcoming: list[dict[str, Any]] = []
        for army in armies.values():
            total_waves = len(army.waves)
            for i, w in enumerate(army.waves):
                if w.num_critters_spawned >= w.slots:
                    continue  # fully spent
                if w.num_critters_spawned > 0:
                    continue  # active wave, currently spawning
                item = self._items_by_iid.get(w.iid)
                critter_name = item.name if item else w.iid
                critter_slot_cost = self._get_wave_critter_slot_cost(w)
                critter_count = max(1, round(w.slots / critter_slot_cost))
                upcoming.append({
                    "army_uid": army.uid,
                    "wave_index": i + 1,
                    "total_waves": total_waves,
                    "iid": w.iid,
                    "critter_name": critter_name,
                    "critter_count": critter_count,
                    "eta_ms": round(max(0.0, w.next_critter_ms)),
                })
        upcoming.sort(key=lambda e: e["eta_ms"])
        return upcoming

    def _get_critter_spawn_interval(self, critter_iid: str) -> float:
        """Get spawn interval (time_between_ms) for a critter type.
        
        Args:
            critter_iid: Critter item ID.
            
        Returns:
            Spawn interval in milliseconds (default 500ms if not found).
        """
        item = self._items_by_iid.get(critter_iid)
        if item and hasattr(item, 'time_between_ms'):
            return float(item.time_between_ms)
        return 500.0  # Fallback default
    
    def _get_wave_interval(self, army: Army) -> float:
        """Get interval between waves (wave_start_ms) for a wave."""
        return 10000.0  # Fallback default

    def _make_critter_from_item(self, iid: str, path: list[Any], path_progress: float = 0.0,
                                attacker_item_upgrades: "dict[str, Any] | None" = None) -> Critter:
        """Create a Critter from item config, placing it at path_progress."""
        item = self._items_by_iid.get(iid)
        health = getattr(item, 'health', 1.0) if item else 1.0
        speed  = getattr(item, 'speed', 0.15) if item else 0.15
        armour = getattr(item, 'armour', 0.0) if item else 0.0

        cu = self._gc.critter_upgrades if self._gc else None
        if cu and attacker_item_upgrades:
            iid_upgrades = attacker_item_upgrades.get(iid, {})
            health *= 1.0 + (cu.health / 100.0) * iid_upgrades.get("health", 0)
            speed  *= 1.0 + (cu.speed  / 100.0) * iid_upgrades.get("speed",  0)
            armour *= 1.0 + (cu.armour / 100.0) * iid_upgrades.get("armour", 0)

        return Critter(
            cid=_new_cid(),
            iid=iid,
            path=path,
            path_progress=path_progress,
            health=health,
            max_health=health,
            speed=speed,
            armour=armour,
            scale=getattr(item, 'scale', 1.0) if item else 1.0,
            value=getattr(item, 'value', getattr(item, 'health', 1.0) if item else 1.0) if item else 1.0,
            damage=getattr(item, 'critter_damage', 1.0) if item else 1.0,
            spawn_on_death=dict(getattr(item, 'spawn_on_death', None) or {}),
        )

    def _step_wave(self, wave: Any, dt_ms: float) -> list[Critter]:
        """Step a wave: decrement spawn timer and spawn critters as needed.

        This function manages the spawn timing for a single wave, spawning
        critters at the configured spawn interval until all slots are filled.

        Each critter consumes a number of slots (e.g. CART costs 2 slots, SLAVE costs 1).
        The wave spawner fills the wave until num_critters_spawned >= wave.slots.

        Args:
            wave: The wave object with .iid (critter type), .slots (total slot capacity),
                  .num_critters_spawned (slots filled so far), and .next_critter_ms.
            dt_ms: Time delta in milliseconds.

        Returns:
            List of newly spawned Critter objects (may be empty).
        """
        critters: list[Critter] = []

        if self._mark_wave_complete_if_blocked(wave):
            return critters

        # Decrement spawn timer
        next_spawn_ms = max(0, wave.next_critter_ms - dt_ms)
        critters_spawned = wave.num_critters_spawned

        # Spawn critters if wave hasn't finished
        if next_spawn_ms <= 0:
            critter_slot_cost = self._get_wave_critter_slot_cost(wave)

            # Spawn if it fits, or if this is the very first critter of the wave
            if critters_spawned == 0 or critters_spawned + critter_slot_cost <= wave.slots:
                critter = self._make_critter_from_item(wave.iid, path=[])
                critters.append(critter)
                critters_spawned += critter_slot_cost
                next_spawn_ms = self._get_critter_spawn_interval(wave.iid)
            else:
                wave.num_critters_spawned = critters_spawned
                wave.next_critter_ms = int(next_spawn_ms)
                self._mark_wave_complete_if_blocked(wave)
                return critters

        # Update wave state with new pointers and timer
        wave.num_critters_spawned = critters_spawned
        wave.next_critter_ms = int(next_spawn_ms)

        return critters

    def _step_armies(self, battle: BattleState, dt_ms: float) -> None:
        """Advance wave timers, spawn critters from all active armies."""
        if not battle.critter_path:
            log.warning("[_step_armies] Battle %d has no critter path", battle.bid)
            return

        cu = self._gc.critter_upgrades if self._gc else None

        for army in battle.armies.values():
            uid = army.uid  # owner uid from the Army object (not the dict key)
            attacker_item_upgrades: dict[str, Any] | None = None
            from gameserver.network.handlers._core import _svc as _core_svc
            try:
                svc = _core_svc()
                emp = svc.empire_service.get(uid) if svc.empire_service else None
                attacker_item_upgrades = emp.item_upgrades if emp else None
            except Exception:
                pass

            for wave in army.waves:
                new_critters = self._step_wave(wave, dt_ms)
                for critter in new_critters:
                    critter.path = battle.critter_path
                    critter.owner_uid = uid
                    if cu and attacker_item_upgrades:
                        iid_upgrades = attacker_item_upgrades.get(critter.iid, {})
                        critter.health *= 1.0 + (cu.health / 100.0) * iid_upgrades.get("health", 0)
                        critter.max_health = critter.health
                        critter.speed  *= 1.0 + (cu.speed  / 100.0) * iid_upgrades.get("speed",  0)
                        critter.armour *= 1.0 + (cu.armour / 100.0) * iid_upgrades.get("armour", 0)
                    battle.critters[critter.cid] = critter
                    battle.critters_spawned += 1
                    log.info("[SPAWN] Critter cid=%d (%s) owner=%d wave=%d (%.2f/%.2f, path=%d)",
                             critter.cid, critter.iid, uid, wave.wave_id,
                             wave.num_critters_spawned, wave.slots, len(critter.path))


    # -- Finish conditions -----------------------------------------------
    def _check_finished(self, battle: BattleState) -> None:
        """Check if battle is done: all armies dispatched and no critters left."""
        if battle.is_finished:
            return
        if battle.elapsed_ms < battle.MIN_KEEP_ALIVE_MS:
            return

        if battle.defender and battle.defender.resources.get("life", 0) < 1.0:
            battle.is_finished = True
            battle.keep_alive = False
            battle.defender_won = False
            log.info("[FINISH] Battle bid=%d finished (defender lost all life)", battle.bid)
            return

        # All armies from all attackers must be exhausted
        all_armies_done = True
        for army in battle.armies.values():
            for wave in army.waves:
                if not self._mark_wave_complete_if_blocked(wave):
                    all_armies_done = False
                    break
            if not all_armies_done:
                break

        if all_armies_done and len(battle.critters) == 0:
            battle.is_finished = True
            battle.keep_alive = False
            battle.defender_won = True
            log.info("[FINISH] Battle bid=%d finished (defender won)", battle.bid)
        
        


    def _critter_finished(self, battle: BattleState, critter: Critter) -> None:
        """Handle critter reaching the castle.
        
        Attacker gains the capture resources, defender loses life.
        """
        battle.removed_critters.append({"cid": critter.cid, "reason": "reached", "path_progress": critter.path_progress, "damage": critter.damage})
        battle.critters_reached += 1
        # Remove critter from battle
        del battle.critters[critter.cid]
        
        # Calculate damage to defender from critter.damage field
        life_damage = critter.damage
        
        # Apply damage to defender
        if battle.defender:
            current_life = battle.defender.resources.get("life", 0.0)
            new_life = max(0.0, current_life - life_damage)
            battle.defender.resources["life"] = new_life
            
            log.info("[FINISHED] Critter cid=%d (%s) reached goal, defender life: %.1f -> %.1f (damage: %.1f)",
                     critter.cid, critter.iid, current_life, new_life, life_damage)
        
        # Track defender losses for summary
        battle.defender_losses["life"] = battle.defender_losses.get("life", 0.0) + life_damage
        
        # Give capture resources to the owning attacker
        owner_uid = critter.owner_uid or (battle.attacker_uids[0] if battle.attacker_uids else 0)
        if owner_uid and critter.capture:
            if owner_uid not in battle.attacker_gains:
                battle.attacker_gains[owner_uid] = {}
            for resource, amount in critter.capture.items():
                if resource != "life":
                    battle.attacker_gains[owner_uid][resource] = (
                        battle.attacker_gains[owner_uid].get(resource, 0.0) + amount
                    )

    def _critter_died(self, battle: BattleState, critter: Critter) -> None:
        """Handle critter killed by tower.

        Defender gains gold equal to the critter's value.
        Spawns child critters if spawn_on_death is configured.
        """
        battle.removed_critters.append({"cid": critter.cid, "reason": "died", "path_progress": critter.path_progress, "value": critter.value})
        battle.critters_killed += 1
        del battle.critters[critter.cid]

        # Award gold to defender
        if battle.defender and critter.value > 0:
            gold = battle.defender.resources.get("gold", 0.0)
            battle.defender.resources["gold"] = gold + critter.value
            battle.defender_gold_earned += critter.value
            log.info("[KILLED] Critter cid=%d (%s) killed — defender awarded %.1f gold (total: %.1f)",
                     critter.cid, critter.iid, critter.value, battle.defender.resources["gold"])
        else:
            log.info("[KILLED] Critter cid=%d (%s) killed at path_progress=%.2f",
                     critter.cid, critter.iid, critter.path_progress)

        if critter.spawn_on_death:
            self._spawn_death_critters(battle, critter)

    def _spawn_death_critters(self, battle: BattleState, dead: Critter) -> None:
        """Spawn child critters at the dead critter's position, spread within ~1 hex tile.

        All spawned critters are placed slightly behind the dead carrier,
        offset backwards along the path but staying within roughly one hex tile.
        """
        path_len = max(len(dead.path) - 1, 1)
        # 1 hex tile in path_progress units
        one_tile = 1.0 / path_len
        # Total spawn count across all types
        total = sum(dead.spawn_on_death.values())
        # Spread all spawns within 1.2 of a hex tile
        spread = one_tile * 1.2
        spacing = spread / max(total, 1)

        spawn_idx = 0
        for iid, count in dead.spawn_on_death.items():
            for i in range(count):
                offset = spacing * (spawn_idx + 1)
                spawn_progress = max(0.0, dead.path_progress - offset)
                child = self._make_critter_from_item(iid, path=dead.path, path_progress=spawn_progress)
                battle.critters[child.cid] = child
                log.info("[SPAWN_ON_DEATH] Critter cid=%d (%s) spawned from dead cid=%d at progress=%.3f",
                         child.cid, child.iid, dead.cid, spawn_progress)
                spawn_idx += 1


    # -- Broadcasting (delta-based, like Java) ---------------------------

    async def _broadcast(
        self,
        battle: BattleState,
        send_fn: Callable[[int, dict[str, Any]], Awaitable[bool]],
    ) -> None:
        """Send battle_update delta to all observers with current critter positions."""
        # Build critter snapshot for all active critters
        critter_updates = []
        for cid, critter in battle.critters.items():
            critter_updates.append({
                "cid": cid,
                "iid": critter.iid,
                "health": critter.health,
                "max_health": critter.max_health,
                "path_progress": critter.path_progress,
                "slow_remaining_ms": max(0, critter.slow_remaining_ms),
                "burn_remaining_ms": max(0, critter.burn_remaining_ms),
                "scale": critter.scale,
            })
        
        # Build shot snapshot for all pending shots
        shot_updates = []
        for shot in battle.pending_shots:
            src_struct = battle.structures.get(shot.source_sid)
            shot_updates.append({
                "source_sid": shot.source_sid,
                "target_cid": shot.target_cid,
                "shot_type": _shot_visual_type(shot.effects),
                "shot_sprite": src_struct.shot_sprite if src_struct else "",
                "shot_sprite_scale": src_struct.shot_sprite_scale if src_struct else 1.0,
                "projectile_y_offset": src_struct.projectile_y_offset if src_struct else 0.0,
                "path_progress": shot.path_progress,
                "origin_q": shot.origin.q if shot.origin else 0,
                "origin_r": shot.origin.r if shot.origin else 0,
            })
        
        defender_life = battle.defender.resources.get("life", 0) if battle.defender else 0
        defender_max_life = battle.defender.max_life if battle.defender else 10

        upcoming_waves = self.build_upcoming_waves(battle.armies)
        wave_info = upcoming_waves[0] if upcoming_waves else None
        wave_infos = upcoming_waves

        msg: dict[str, Any] = {
            "type": "battle_update",
            "bid": battle.bid,
            "elapsed_ms": battle.elapsed_ms,
            "critters": critter_updates,
            "shots": shot_updates,
            "removed_critters": battle.removed_critters,
            "defender_life": defender_life,
            "defender_max_life": defender_max_life,
            "wave_info": wave_info,
            "wave_infos": wave_infos,
        }
        
        # Record for replay before clearing deltas
        if battle.recorder is not None:
            battle.recorder.record(battle.elapsed_ms, msg)

        # Send to all observers (snapshot to avoid mutation during async iteration)
        for uid in list(battle.observer_uids):
            await send_fn(uid, msg)
        
        # Clear removed_critters after broadcast
        battle.removed_critters = []

    async def send_summary(
        self,
        battle: BattleState,
        send_fn: Callable[[int, dict[str, Any]], Awaitable[bool]],
        loot: dict[str, Any] | None = None,
    ) -> None:
        """Send battle_summary when battle ends.
        
        Args:
            loot: Optional loot dict computed after battle ends (only on defender loss).
                  Shape: {knowledge, culture, artifact}
        """
        total_waves = sum(len(a.waves) for a in battle.armies.values())
        # army_names: uid → list of army names (one uid can have multiple armies)
        army_names_by_uid: dict[int, list[str]] = {}
        for a in battle.armies.values():
            army_names_by_uid.setdefault(a.uid, []).append(a.name)
        # attacker_empire_names: uid → empire name (resolved from defender/svc if available)
        attacker_empire_names: dict[int, str] = {}
        try:
            from gameserver.network.handlers._core import _svc as _core_svc
            _s = _core_svc()
            for uid in battle.attacker_uids:
                emp = _s.empire_service.get(uid) if _s.empire_service else None
                attacker_empire_names[uid] = emp.name if emp else str(uid)
        except Exception:
            pass
        msg: dict[str, Any] = {
            "type": "battle_summary",
            "bid": battle.bid,
            "defender_won": battle.defender_won or False,
            "attacker_uid": battle.attacker_uids[0] if battle.attacker_uids else None,
            "attacker_uids": list(battle.attacker_uids),
            "army_name": battle.army.name if battle.army else "",
            "army_names": army_names_by_uid,
            "attacker_empire_names": attacker_empire_names,
            "attacker_gains": dict(battle.attacker_gains),
            "defender_losses": dict(battle.defender_losses),
            "defender_gold_earned": battle.defender_gold_earned,
            "critters_spawned": battle.critters_spawned,
            "critters_killed": battle.critters_killed,
            "critters_reached": battle.critters_reached,
            "duration_s": round(battle.elapsed_ms / 1000, 1),
            "num_waves": total_waves,
            "num_towers": len(battle.structures),
            "loot": loot or {},
        }

        # Recompute the path from the defender's current tiles now that the battle is
        # over, so the client immediately shows the up-to-date (possibly changed) path.
        if battle.defender and getattr(battle.defender, 'hex_map', None):
            from gameserver.engine.hex_pathfinding import find_path_from_spawn_to_castle

            def _tile_type_local(v: object) -> str:
                if isinstance(v, dict):
                    return str(v.get('type', 'empty'))
                return str(v) if v else 'empty'

            normalized = {k: _tile_type_local(v) for k, v in battle.defender.hex_map.items()}
            computed_path = find_path_from_spawn_to_castle(normalized)
            msg["path"] = [[c.q, c.r] for c in computed_path] if computed_path else None
        else:
            msg["path"] = None

        # Record summary for replay
        if battle.recorder is not None:
            battle.recorder.record(battle.elapsed_ms, msg)

        for uid in list(battle.observer_uids):
            await send_fn(uid, msg)

    # -- Loot (stub) -----------------------------------------------------

    def apply_battle_resources(
        self, 
        battle: BattleState, 
        attacker_empires: dict[int, "Empire"],
        defender_empire: "Empire",
    ) -> None:
        """Apply resource transfers after battle ends.
        
        Args:
            battle: Completed battle state with captured resources.
            attacker_empires: Dict of attacker UID -> Empire object.
            defender_empire: The defending Empire object.
        """
        
        # Transfer losses from defender
        for resource_key, amount in battle.defender_losses.items():
            if resource_key in defender_empire.resources:
                defender_empire.resources[resource_key] = max(0, 
                    defender_empire.resources[resource_key] - amount)
                log.debug("Defender lost %.0f %s", amount, resource_key)
        
        # Transfer gains to attackers
        for attacker_uid, gains in battle.attacker_gains.items():
            attacker = attacker_empires.get(attacker_uid)
            if attacker:
                for resource_key, amount in gains.items():
                    if resource_key not in attacker.resources:
                        attacker.resources[resource_key] = 0.0
                    attacker.resources[resource_key] += amount
                    log.debug("Attacker %d gained %.0f %s", attacker_uid, amount, resource_key)

    def loot_defender(
        self, battle: BattleState, defender: Empire, attackers: dict[int, Empire]
    ) -> None:
        """Apply end-of-battle loot on defender loss."""
        # TODO: implement full loot like Java
        pass
