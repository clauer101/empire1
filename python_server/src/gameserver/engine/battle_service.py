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
        # TODO: Implement shot stepping: decrement flight time, apply damage/effects on arrival, remove from pending_shots.
        pass

    # -- Critter movement ------------------------------------------------

    def _step_critters(self, battle: BattleState, dt_ms: float) -> None:
        """Move all critters, handle finish/death."""
        for cid, critter in list(battle.critters.items()):
            if critter.health <= 0:
                self._critter_died(battle, critter)
            elif critter.path_progress >= 1.0:
                self._critter_finished(battle, critter)
            else:
                self._move_critter(battle, critter, dt_ms)
                    


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
        
        # Decrement status effect timers
        if critter.slow_remaining_ms > 0:
            critter.slow_remaining_ms -= dt_ms
        if critter.burn_remaining_ms > 0:
            critter.burn_remaining_ms -= dt_ms
            # Apply burn damage
            burn_damage = critter.burn_dps * dt_s
            critter.health = max(0, critter.health - burn_damage)
            if burn_damage > 0:
                log.debug("[BURN] Critter %d takes %.1f burn damage (remaining: %.0fms)", 
                          critter.cid, burn_damage, critter.burn_remaining_ms)
            
        

    # -- Tower targeting & firing ----------------------------------------

    def _step_towers(self, battle: BattleState, dt_ms: float) -> None:
        """Towers acquire targets and fire shots."""
        # TODO: Implement tower targeting logic (e.g., nearest, first, last) and shot creation.
        pass

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
            critter = Critter(
                cid=_new_cid(),
                iid=wave.iid,
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
        
        Attacker gains the capture resources.
        """
        log.debug("Critter %d (%s) finished", critter.cid, critter.iid)
        
        

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
            })
        
        msg: dict[str, Any] = {
            "type": "battle_update",
            "bid": battle.bid,
            "elapsed_ms": battle.elapsed_ms,
            "critters": critter_updates,
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
