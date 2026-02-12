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


# ── Critter step (mirrors Java Critter.step()) ──────────────

def step_critter(critter: Critter, dt_ms: float) -> bool:
    """Advance critter along its hex path.

    Speed is in hex-fields-per-second.
    path_progress is a float index into critter.path.
    Returns True if critter just finished (reached end).
    """
    if critter.is_finished or not critter.is_alive:
        return False

    # Apply burn damage
    if critter.burn_remaining_ms > 0:
        burn_dmg = critter.burn_dps * dt_ms / 1000.0
        critter.health = max(0.0, critter.health - burn_dmg)
        critter.burn_remaining_ms = max(0.0, critter.burn_remaining_ms - dt_ms)
        if not critter.is_alive:
            return False

    # Reduce slow timer
    if critter.slow_remaining_ms > 0:
        critter.slow_remaining_ms = max(0.0, critter.slow_remaining_ms - dt_ms)

    # Movement
    speed = critter.effective_speed  # hex / sec
    distance = speed * dt_ms / 1000.0
    max_progress = len(critter.path) - 1

    critter.path_progress = min(critter.path_progress + distance, max_progress)

    if critter.path_progress >= max_progress:
        return True  # finished — reached castle

    return False


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
        
        # Log active critter count periodically
        #if battle.elapsed_ms % 1000 < dt_ms:  # Every ~1 second
        #    log.info("[battle %d] Active critters: %d", battle.bid, len(battle.critters))

    # -- Shot resolution -------------------------------------------------

    def _step_shots(self, battle: BattleState, dt_ms: float) -> None:
        """Decrement flight time, apply damage/effects when shots arrive."""
        finished: list[Shot] = []
        for shot in battle.pending_shots:
            shot.flight_remaining_ms = max(0.0, shot.flight_remaining_ms - dt_ms)
            if shot.flight_remaining_ms <= 0:
                critter = battle.critters.get(shot.target_cid)
                if critter and critter.is_alive and not critter.is_finished:
                    # Damage (armour reduces non-burn)
                    dmg = shot.damage
                    if shot.shot_type != DamageType.BURN:
                        dmg = max(min(dmg, 1.0), dmg - critter.armour)
                    critter.health = max(0.0, critter.health - dmg)

                    # Slow effect
                    slow_val = shot.effects.get("slow_target")
                    slow_dur = shot.effects.get("slow_target_duration")
                    if slow_val is not None and slow_dur is not None:
                        critter.slow_remaining_ms = slow_dur * 1000.0
                        critter.slow_speed = critter.speed * slow_val

                    # Burn effect
                    burn_val = shot.effects.get("burn_target")
                    burn_dur = shot.effects.get("burn_target_duration")
                    if burn_val is not None and burn_dur is not None:
                        critter.burn_remaining_ms = burn_dur * 1000.0
                        critter.burn_dps = burn_val

                    if not critter.is_alive:
                        self._critter_died(battle, critter)

                finished.append(shot)

        for shot in finished:
            battle.pending_shots.remove(shot)

    # -- Critter movement ------------------------------------------------

    def _step_critters(self, battle: BattleState, dt_ms: float) -> None:
        """Move all critters, handle finish/death."""
        to_remove: list[int] = []
        for cid, critter in battle.critters.items():
            if not critter.is_alive:
                continue
            reached_end = step_critter(critter, dt_ms)
            if reached_end:
                self._critter_finished(battle, critter)
                to_remove.append(cid)
            elif not critter.is_alive:
                self._critter_died(battle, critter)
                to_remove.append(cid)

        for cid in to_remove:
            battle.critters.pop(cid, None)

    # -- Tower targeting & firing ----------------------------------------

    def _step_towers(self, battle: BattleState, dt_ms: float) -> None:
        """Towers acquire targets and fire shots."""
        for sid, structure in battle.structures.items():
            # Reload
            structure.reload_remaining_ms = max(
                0.0, structure.reload_remaining_ms - dt_ms
            )

            # Validate focus
            if structure.focus_cid is not None:
                target = battle.critters.get(structure.focus_cid)
                if target is None or not target.is_alive or target.is_finished:
                    structure.focus_cid = None  # lost target
                elif structure.position.distance_to(target.current_hex) > structure.range:
                    structure.focus_cid = None  # out of range

            # Acquire new target (most advanced critter in range)
            if structure.focus_cid is None and battle.critters:
                best_cid = None
                best_progress = -1.0
                for cid, critter in battle.critters.items():
                    if not critter.is_alive or critter.is_finished:
                        continue
                    dist = structure.position.distance_to(critter.current_hex)
                    if dist <= structure.range and critter.path_progress > best_progress:
                        best_progress = critter.path_progress
                        best_cid = cid
                structure.focus_cid = best_cid

            # Fire
            if (
                structure.focus_cid is not None
                and structure.reload_remaining_ms <= 0
                and structure.damage > 0
            ):
                target = battle.critters.get(structure.focus_cid)
                if target is not None:
                    # Compute flight time from distance
                    dist = structure.position.distance_to(target.current_hex)
                    flight_ms = (
                        (dist / structure.shot_speed * 1000.0)
                        if structure.shot_speed > 0
                        else 0.0
                    )
                    shot = Shot(
                        damage=structure.damage,
                        target_cid=structure.focus_cid,
                        source_sid=sid,
                        shot_type=DamageType.NORMAL,
                        effects=dict(structure.effects),
                        flight_remaining_ms=flight_ms,
                    )
                    battle.pending_shots.append(shot)
                    battle.new_shots.append(shot)
                    structure.reload_remaining_ms = structure.reload_time_ms

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
                battle.new_critters.append(critter)
                log.info("[SPAWN] Critter cid=%d (%s) spawned from wave %d (progress=%d/%d)",
                         critter.cid, critter.iid, wave.wave_id, wave.num_critters_spawned, wave.slots)



    # -- Finish conditions -----------------------------------------------

    def _check_finished(self, battle: BattleState) -> None:
        """Check if battle is done: all armies dispatched and no critters left."""
        if battle.is_finished:
            return
        if battle.elapsed_ms < battle.MIN_KEEP_ALIVE_MS:
            return

        # Check if attacker has finished dispatching all waves
        all_armies_done = True
        if battle.attacker and battle.attacker.current_wave_pointer < len(battle.attacker.waves):
            all_armies_done = False
        
        no_critters = len(battle.critters) == 0

        if all_armies_done and no_critters:
            battle.is_finished = True
            battle.keep_alive = False
            battle.defender_won = True  # critters didn't break through

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
        battle.dead_critter_ids.append(critter.cid)
        log.info("[SPAWN] Critter cid=%d (%s) killed at path_progress=%.2f", 
                 critter.cid, critter.iid, critter.path_progress)
        
        # Record defender's resource gains from kill bonus
        for resource_key, amount in critter.bonus.items():
            if resource_key not in battle.defender_losses:
                battle.defender_losses[resource_key] = 0.0
            # bonus represents resources the defender GAINS, not loses
            # So this is actually negative loss (gain)
            battle.defender_losses[resource_key] -= amount  # Negative = gain
            log.debug("Defender gains %.0f %s from kill", amount, resource_key)
        
        # Check if critter spawns replacements on death
        if not critter.spawn_on_death:
            return
        
        # Spawn replacement critters at death location
        try:
            for iid, count in critter.spawn_on_death.items():
                for _ in range(count):
                    # Create replacement critter at death location
                    new_critter = Critter(
                        cid=_new_cid(),
                        iid=iid,
                        health=10.0,  # TODO: load from item config
                        max_health=10.0,
                        speed=1.5,  # TODO: load from item config
                        armour=0.0,  # TODO: load from item config
                        path=critter.path,
                        path_progress=critter.path_progress,  # Start at death location
                    )
                    battle.critters[new_critter.cid] = new_critter
                    battle.new_critters.append(new_critter)
                    log.info("[SPAWN] Critter cid=%d spawned on death of cid=%d (parent_type=%s, type=%s)", 
                             new_critter.cid, critter.cid, critter.iid, iid)
        except Exception as e:
            log.error("Error spawning critter on death: %s", e)


    # -- Broadcasting (delta-based, like Java) ---------------------------

    async def _broadcast(
        self,
        battle: BattleState,
        send_fn: Callable[[int, dict[str, Any]], Awaitable[bool]],
    ) -> None:
        """Send battle_update delta to all observers (only when changes exist)."""
        has_changes = (
            battle.new_critters
            or battle.new_shots
            or battle.dead_critter_ids
            or battle.finished_critter_ids
        )

        if has_changes:
            msg: dict[str, Any] = {
                "type": "battle_update",
                "bid": battle.bid,
                "time": battle.elapsed_ms,
                "new_critters": [
                    {
                        "cid": c.cid,
                        "iid": c.iid,
                        "health": c.health,
                        "speed": c.speed,
                        "path": [{"q": h.q, "r": h.r} for h in c.path],
                    }
                    for c in battle.new_critters
                ],
                "dead_critter_ids": list(battle.dead_critter_ids),
                "finished_critter_ids": list(battle.finished_critter_ids),
                "new_shots": [
                    {
                        "source_sid": s.source_sid,
                        "target_cid": s.target_cid,
                        "damage": s.damage,
                        "shot_type": s.shot_type,
                        "flight_ms": s.flight_remaining_ms,
                    }
                    for s in battle.new_shots
                ],
            }
            for uid in battle.observer_uids:
                await send_fn(uid, msg)

        battle.reset_broadcast()

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
