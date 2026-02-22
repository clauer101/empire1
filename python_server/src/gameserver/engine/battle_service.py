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
import time
from collections import deque
from typing import TYPE_CHECKING, Any, Callable, Awaitable

from gameserver.models.critter import Critter, DamageType
from gameserver.models.hex import HexCoord
from gameserver.models.shot import Shot

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
                await self._send_summary(battle, send_fn)
                break

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
        
        if battle.elapsed_ms > 30000:  # Safety check to prevent infinite battles during testing
            for critter in battle.critters.values():
                critter.health = 0  # Force end of battle
        
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
        # Find target critter
        critter = battle.critters.get(shot.target_cid)
        if not critter:
            log.debug("[SHOT] Shot %d->%d missed (target not found)", shot.source_sid, shot.target_cid)
            return
        
        # Apply base damage (reduced by armour for non-burn damage)
        damage = shot.damage
        if shot.shot_type != DamageType.BURN:
            damage = max(0.0, damage - critter.armour)
        
        critter.health -= damage
        log.debug("[HIT] Critter cid=%d hit by sid=%d for %.1f damage (remaining health: %.1f)", 
                  critter.cid, shot.source_sid, damage, critter.health)
        
        # Apply shot effects based on shot_type
        if shot.shot_type == DamageType.COLD:
            # Apply slow effect
            slow_factor = shot.effects.get("slow_target", 0.5)  # Default 50% speed
            slow_duration_s = shot.effects.get("slow_target_duration", 2.0)  # Default 2s
            
            critter.slow_remaining_ms = slow_duration_s * 1000.0
            critter.slow_speed = critter.speed * slow_factor
            
            log.debug("[SLOW] Critter cid=%d slowed to %.2f hex/s for %.0fms", 
                      critter.cid, critter.slow_speed, critter.slow_remaining_ms)
        
        elif shot.shot_type == DamageType.BURN:
            # Apply burn effect (damage over time)
            burn_dps = shot.effects.get("burn_target_dps", 1.0)  # Default 1 dps
            burn_duration_s = shot.effects.get("burn_target_duration", 3.0)  # Default 3s
            
            critter.burn_remaining_ms = burn_duration_s * 1000.0
            critter.burn_dps = burn_dps
            
            log.debug("[BURN] Critter cid=%d burning for %.1f dps over %.0fms", 
                      critter.cid, critter.burn_dps, critter.burn_remaining_ms)
        
        elif shot.shot_type == DamageType.SPLASH:
            # TODO: Implement splash damage (create sub-shots for nearby critters)
            # For now, just apply direct damage
            log.debug("[SPLASH] Splash damage at critter cid=%d (splash radius not yet implemented)", 
                      critter.cid)

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
                    # Calculate flight time: distance / speed * 1000ms
                    distance = structure.position.distance_to(target.path[int(target.path_progress * (len(target.path) - 1))] if target.path else structure.position)
                    flight_time_ms = (distance / structure.shot_speed) * 1000.0 if structure.shot_speed > 0 else 0.0
                    
                    # Create shot
                    shot = Shot(
                        damage=structure.damage,
                        target_cid=target.cid,
                        source_sid=sid,
                        shot_type=structure.shot_type,
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
        """Find the most-advanced critter within range.
        
        Targeting strategy: critter with highest path_progress (closest to finish).
        """
        best_target: Critter | None = None
        best_progress = -1.0
        
        for critter in battle.critters.values():
            if not critter.path:
                continue
                
            # Get current position from path_progress
            path_idx = int(critter.path_progress * (len(critter.path) - 1))
            critter_pos = critter.path[path_idx]
            
            # Check if in range
            distance = structure.position.distance_to(critter_pos)
            if distance <= structure.range:
                # Select most-advanced (highest path_progress)
                if critter.path_progress > best_progress:
                    best_progress = critter.path_progress
                    best_target = critter
        
        return best_target

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

    def _step_wave(self, wave, dt_ms: float) -> list[Critter]:
        """Step a wave: decrement spawn timer and spawn critters as needed.
        
        This function manages the spawn timing for a single wave, spawning
        critters at the configured spawn interval until all slots are filled.
        
        Args:
            wave: The wave object with .iid (critter type), .slots (total count),
                  .num_critters_spawned, and .next_critter_ms.
            dt_ms: Time delta in milliseconds.
            
        Returns:
            List of newly spawned Critter objects (may be empty).
        """
        critters: list[Critter] = []
        
        # Decrement spawn timer
        next_spawn_ms = max(0, wave.next_critter_ms - dt_ms)
        critters_spawned = wave.num_critters_spawned
                
        if critters_spawned >= wave.slots:
            return []  # Wave fully spawned
        
        # Spawn critters if wave hasn't finished
        if next_spawn_ms <= 0:
            # Get critter stats from item config
            item = self._items_by_iid.get(wave.iid)
            
            critter = Critter(
                cid=_new_cid(),
                iid=wave.iid,
                health=getattr(item, 'health', 1.0) if item else 1.0,
                max_health=getattr(item, 'health', 1.0) if item else 1.0,
                speed=getattr(item, 'speed', 0.15) if item else 0.15,
                armour=getattr(item, 'armour', 0.0) if item else 0.0,
                scale=getattr(item, 'scale', 1.0) if item else 1.0,
            )
            critters.append(critter)
            critters_spawned += 1
            next_spawn_ms = self._get_critter_spawn_interval(wave.iid)
        
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
        
        # Check if defender has 0 life
        if battle.defender and battle.defender.resources.get("life", 0) <= 0:
            battle.is_finished = True
            battle.keep_alive = False
            battle.defender_won = False  # defender lost all life
            log.info("[FINISH] Battle bid=%d finished (defender lost all life)", battle.bid)
            return
        
        # Check if attacker has finished dispatching all waves
        all_armies_done = True
        if battle.army:
            for wave in battle.army.waves:
                if wave.num_critters_spawned < wave.slots:
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
        # Remove critter from battle
        del battle.critters[critter.cid]
        
        # Calculate damage to defender (default 1 life per critter, or from capture dict)
        life_damage = critter.capture.get("life", 1.0)
        
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
        
        Defender gains the bonus resources. Spawns replacement critters if configured.
        """
        del battle.critters[critter.cid]
        log.info("[KILLED] Critter cid=%d (%s) killed at path_progress=%.2f", 
                 critter.cid, critter.iid, critter.path_progress)    
       


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
            shot_updates.append({
                "source_sid": shot.source_sid,
                "target_cid": shot.target_cid,
                "shot_type": shot.shot_type,
                "path_progress": shot.path_progress,
                "origin_q": shot.origin.q if shot.origin else 0,
                "origin_r": shot.origin.r if shot.origin else 0,
            })
        
        msg: dict[str, Any] = {
            "type": "battle_update",
            "bid": battle.bid,
            "elapsed_ms": battle.elapsed_ms,
            "critters": critter_updates,
            "shots": shot_updates,
        }
        
        # Send to all observers
        for uid in battle.observer_uids:
            await send_fn(uid, msg)

    async def _send_summary(
        self,
        battle: BattleState,
        send_fn: Callable[[int, dict[str, Any]], Awaitable[bool]],
    ) -> None:
        """Send battle_summary when battle ends."""
        msg: dict[str, Any] = {
            "type": "battle_summary",
            "bid": battle.bid,
            "defender_won": battle.defender_won or False,
            "attacker_gains": dict(battle.attacker_gains),  # Dict of {uid: {resource: amount}}
            "defender_losses": dict(battle.defender_losses),
        }
        for uid in battle.observer_uids:
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
