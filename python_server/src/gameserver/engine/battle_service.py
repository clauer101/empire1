"""Battle service — real-time tower-defense battle simulation.

Runs each battle as an independent asyncio task with ~15ms tick rate.

Tick order (must be preserved):
1. step_shots     — decrement flight time, apply damage on arrival
2. step_critters  — movement along hex path + burn tick
3. step_towers    — acquire targets + fire
4. step_armies    — wave timers + critter spawning
5. broadcast      — send delta to observers (throttled to 250ms)

Architecture (Java-equivalent):
  Server computes movement & combat; sends delta events every 250ms.
  Client receives critter paths + speed and autonomously animates them.
  Only events (spawn / die / finish / shot) are sent — no position spam.

Provides deterministic tick function for testing (explicit dt_ms).
"""

from __future__ import annotations

import asyncio
import logging
import math
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

def _shot_visual_type(effects: dict) -> int:
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

    def __init__(self, items: list | dict | None = None) -> None:
        """Initialize battle service.
        
        Args:
            items: List or dict of ItemDetails for looking up critter stats (e.g., time_between_ms).
                   Can be a list of ItemDetails or a dict[str, ItemDetails].
        """
        if items is None:
            self._items_by_iid = {}
        elif isinstance(items, dict):
            self._items_by_iid = items
        else:
            self._items_by_iid = {item.iid: item for item in items}

    def _get_wave_critter_slot_cost(self, wave) -> int:
        """Return the slot cost for the next critter of this wave."""
        item = self._items_by_iid.get(wave.iid)
        return max(1, int(getattr(item, "slots", 1) or 1))

    def _mark_wave_complete_if_blocked(self, wave) -> bool:
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
                "[SPAWN] Wave %d completed early: remaining_slots=%d cannot fit critter %s (cost=%d)",
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
                 battle.bid, battle.defender.uid if battle.defender else None, battle.attacker.uid if battle.attacker else None)
        
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
        """Execute one deterministic battle tick."""
        self._step_shots(battle, dt_ms)
        self._step_critters(battle, dt_ms)
        self._step_towers(battle, dt_ms)
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
        """Move all critters, handle finish/death."""
        for cid, critter in list(battle.critters.items()):
            # Move critter first (if alive and not finished yet)
            if critter.health > 0 and critter.path_progress < 1.0:
                self._move_critter(battle, critter, dt_ms)
            
            # Then check final state once (after movement)
            if critter.health <= 0:
                self._critter_died(battle, critter)
            elif critter.path_progress >= 1.0:
                self._critter_finished(battle, critter)
                    


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
        for sid, structure in battle.structures.items():
            # Decrement reload timer
            if structure.reload_remaining_ms > 0:
                structure.reload_remaining_ms -= dt_ms
            
            # Check if tower is ready to fire
            if structure.reload_remaining_ms <= 0:
                # Find target: most-advanced critter in range
                target = self._find_target(battle, structure)
                
                if target:
                    # Flight distance using interpolated critter position
                    cq, cr = critter_hex_pos(target.path, target.path_progress)
                    distance = hex_world_distance(
                        float(structure.position.q), float(structure.position.r), cq, cr
                    )
                    flight_time_ms = (distance / structure.shot_speed) * 1000.0 if structure.shot_speed > 0 else 0.0
                    
                    # Create shot
                    shot = Shot(
                        damage=structure.damage,
                        target_cid=target.cid,
                        source_sid=sid,
                        effects=dict(structure.effects),
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
    
    def _find_target(self, battle: BattleState, structure: Structure) -> Critter | None:
        """Find a critter within range using the structure's targeting strategy.

        Strategies:
          first  — most-advanced critter (highest path_progress, closest to finish)
          last   — least-advanced critter (lowest path_progress, furthest from spawn)
          random — random critter among those in range
        """
        in_range: list[Critter] = []

        tq, tr = float(structure.position.q), float(structure.position.r)

        for critter in battle.critters.values():
            if not critter.path:
                continue

            # Interpolated critter position (between two hex centers)
            cq, cr = critter_hex_pos(critter.path, critter.path_progress)

            # Check if in range (continuous hex-world distance)
            distance = hex_world_distance(tq, tr, cq, cr)
            if distance <= structure.range:
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

    # -- Army wave dispatch ---------

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

    def _make_critter_from_item(self, iid: str, path: list, path_progress: float = 0.0) -> Critter:
        """Create a Critter from item config, placing it at path_progress."""
        item = self._items_by_iid.get(iid)
        return Critter(
            cid=_new_cid(),
            iid=iid,
            path=path,
            path_progress=path_progress,
            health=getattr(item, 'health', 1.0) if item else 1.0,
            max_health=getattr(item, 'health', 1.0) if item else 1.0,
            speed=getattr(item, 'speed', 0.15) if item else 0.15,
            armour=getattr(item, 'armour', 0.0) if item else 0.0,
            scale=getattr(item, 'scale', 1.0) if item else 1.0,
            value=getattr(item, 'value', getattr(item, 'health', 1.0) if item else 1.0) if item else 1.0,
            damage=getattr(item, 'critter_damage', 1.0) if item else 1.0,
            spawn_on_death=dict(getattr(item, 'spawn_on_death', None) or {}),
        )

    def _step_wave(self, wave, dt_ms: float) -> list[Critter]:
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
        """Advance wave timers, spawn critters from active waves.
        
        Steps all waves and assigns the precomputed critter path to spawned critters.
        """
        if not battle.army:
            return
        
        # Get the precomputed critter path (calculated when battle was created)
        if not battle.critter_path:
            log.warning("[_step_armies] Battle %d has no critter path", battle.bid)
            return
        
        # Step all waves up to and including the next wave
        for wave in battle.army.waves:
            new_critters = self._step_wave(wave, dt_ms)            
            
            for critter in new_critters:
                # Set the critter's path from the precomputed battle path
                critter.path = battle.critter_path
                
                battle.critters[critter.cid] = critter
                log.info("[SPAWN] Critter cid=%d (%s) spawned from wave %d (progress=%d/%d, path_length=%d)",
                         critter.cid, critter.iid, wave.wave_id, wave.num_critters_spawned, wave.slots, len(critter.path))


    # -- Finish conditions -----------------------------------------------
    def _check_finished(self, battle: BattleState) -> None:
        """Check if battle is done: all armies dispatched and no critters left."""
        if battle.is_finished:
            return
        if battle.elapsed_ms < battle.MIN_KEEP_ALIVE_MS:
            return

        # Check if defender has lost all life (< 1.0 accounts for fractional offsets like life_offset)
        if battle.defender and battle.defender.resources.get("life", 0) < 1.0:
            battle.is_finished = True
            battle.keep_alive = False
            battle.defender_won = False  # defender lost all life
            log.info("[FINISH] Battle bid=%d finished (defender lost all life)", battle.bid)
            return
        
        # Check if attacker has finished dispatching all waves
        all_armies_done = True
        if battle.army:
            for wave in battle.army.waves:
                if not self._mark_wave_complete_if_blocked(wave):
                    all_armies_done = False
                    break
        
        no_critters = len(battle.critters) == 0

        if all_armies_done and no_critters:
            battle.is_finished = True
            battle.keep_alive = False
            battle.defender_won = True  # critters didn't break through
            log.info("[FINISH] Battle bid=%d finished (defender won)", battle.bid)
        
        


    def _critter_finished(self, battle: BattleState, critter: Critter) -> None:
        """Handle critter reaching the castle.
        
        Attacker gains the capture resources, defender loses life.
        """
        battle.removed_critters.append({"cid": critter.cid, "reason": "reached", "path_progress": critter.path_progress, "damage": critter.damage})
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
        
        # Give capture resources to attacker (if any beyond life damage)
        if battle.attacker and critter.capture:
            attacker_uid = battle.attacker.uid
            if attacker_uid not in battle.attacker_gains:
                battle.attacker_gains[attacker_uid] = {}
            
            for resource, amount in critter.capture.items():
                if resource != "life":  # life is defender loss, not attacker gain
                    battle.attacker_gains[attacker_uid][resource] = (
                        battle.attacker_gains[attacker_uid].get(resource, 0.0) + amount
                    )

    def _critter_died(self, battle: BattleState, critter: Critter) -> None:
        """Handle critter killed by tower.

        Defender gains gold equal to the critter's value.
        Spawns child critters if spawn_on_death is configured.
        """
        battle.removed_critters.append({"cid": critter.cid, "reason": "died", "path_progress": critter.path_progress, "value": critter.value})
        del battle.critters[critter.cid]

        # Award gold to defender
        if battle.defender and critter.value > 0:
            gold = battle.defender.resources.get("gold", 0.0)
            battle.defender.resources["gold"] = gold + critter.value
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
                "path_progress": shot.path_progress,
                "origin_q": shot.origin.q if shot.origin else 0,
                "origin_r": shot.origin.r if shot.origin else 0,
            })
        
        defender_life = battle.defender.resources.get("life", 0) if battle.defender else 0
        defender_max_life = battle.defender.max_life if battle.defender else 10

        # Wave info — first wave that hasn't started spawning yet
        wave_info = None
        if battle.army and battle.army.waves:
            total_waves = len(battle.army.waves)
            for i, w in enumerate(battle.army.waves):
                if w.num_critters_spawned == 0:
                    item = self._items_by_iid.get(w.iid)
                    critter_name = item.name if item else w.iid
                    wave_info = {
                        "wave_index": i + 1,
                        "total_waves": total_waves,
                        "iid": w.iid,
                        "critter_name": critter_name,
                        "slots": w.slots,
                        "spawned": 0,
                        "next_critter_ms": max(0.0, w.next_critter_ms),
                    }
                    break

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
        loot: dict | None = None,
    ) -> None:
        """Send battle_summary when battle ends.
        
        Args:
            loot: Optional loot dict computed after battle ends (only on defender loss).
                  Shape: {knowledge, culture, artefact}
        """
        msg: dict[str, Any] = {
            "type": "battle_summary",
            "bid": battle.bid,
            "defender_won": battle.defender_won or False,
            "attacker_uid": battle.attacker.uid if battle.attacker else None,
            "army_name": battle.army.name if battle.army else "",
            "attacker_gains": dict(battle.attacker_gains),  # Dict of {uid: {resource: amount}}
            "defender_losses": dict(battle.defender_losses),
            "loot": loot or {},
        }

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
        from gameserver.models.empire import Empire
        
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
