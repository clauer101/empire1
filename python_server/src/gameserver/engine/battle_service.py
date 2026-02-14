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
                 battle.bid, battle.defender_uid, battle.attacker_uids)
        
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
        # TODO: Implement more efficient iteration if needed (e.g., separate lists for alive/finished).
        for cid, critter in list(battle.critters.items()):
            # Move critter along path based on speed and dt_ms
            # Check for finish (reached end) or death (health <= 0) and handle accordingly
            if critter.health <= 0:
                self._critter_died(battle, critter)
                del battle.critters[cid]
            else:
                # TODO: Move critter along path  
                pass
            
        

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
                health=1.0,
                max_health=1.0,
                speed=0.0,
                armour=0.0,
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
        
        Steps all waves from 0 to current_wave_pointer + 1 if they exist.
        """
        if not battle.attacker:
            return
        
        army = battle.attacker        

        # Step all waves up to and including the next wave
        for wave in army.waves:
            new_critters = self._step_wave(wave, dt_ms)
            
            for critter in new_critters:
                battle.critters[critter.cid] = critter
                log.info("[SPAWN] Critter cid=%d (%s) spawned from wave %d (progress=%d/%d)",
                         critter.cid, critter.iid, wave.wave_id, wave.num_critters_spawned, wave.slots)



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
        if battle.attacker:
            for wave in battle.attacker.waves:
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
        battle.finished_critter_ids.append(critter.cid)
        log.debug("Critter %d (%s) finished", critter.cid, critter.iid)
        
        # Record attacker's resource gains for each attacker (split evenly for now)
        # TODO: should this be distributed or split among all attackers?
        for attacker_uid in battle.attacker_uids:
            if attacker_uid not in battle.attacker_gains:
                battle.attacker_gains[attacker_uid] = {}
            
            for resource_key, amount in critter.capture.items():
                if resource_key not in battle.attacker_gains[attacker_uid]:
                    battle.attacker_gains[attacker_uid][resource_key] = 0.0
                battle.attacker_gains[attacker_uid][resource_key] += amount
                log.debug("Attacker %d gains %.0f %s from critter", 
                          attacker_uid, amount, resource_key)

    def _critter_died(self, battle: BattleState, critter: Critter) -> None:
        """Handle critter killed by tower.
        
        Defender gains the bonus resources. Spawns replacement critters if configured.
        """
        log.info("[KILLED] Critter cid=%d (%s) killed at path_progress=%.2f", 
                 critter.cid, critter.iid, critter.path_progress)    
       


    # -- Broadcasting (delta-based, like Java) ---------------------------

    async def _broadcast(
        self,
        battle: BattleState,
        send_fn: Callable[[int, dict[str, Any]], Awaitable[bool]],
    ) -> None:
        """Send battle_update delta to all observers (only when changes exist)."""
        # TODO: send battle update

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
