#!/usr/bin/env python3
"""Standalone AI player bot for empire1 (dev environment only).

Bot flow is documented in ai_players/docs/bot-flow.md.
Keep that file in sync when changing the tick structure or cycle steps.

Usage:
    python run_bot.py --name alice [--cycles N] [--fast] [--control-port 9301]

On first start the bot signs up a fresh account; credentials and all internal
state are persisted to states/<name>.yaml. SIGINT/SIGTERM saves state and exits.
"""

from __future__ import annotations

import argparse
import logging
import os
import signal
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bot.analyzer import process_new_reports, score_targets  # noqa: E402
from bot.api_client import ApiClient, ApiError  # noqa: E402
from bot.control import ControlServer  # noqa: E402
from bot.dispatch import choose_action  # noqa: E402
from bot.planners.base import BotContext  # noqa: E402
from bot.state import BotState, now_iso  # noqa: E402
from bot.strategy import (  # noqa: E402
    breach_defense_strategy, is_expired, make_override, roll_strategy,
)

log = logging.getLogger("bot")

MAX_ACTIONS_PER_TICK = 20
DEFENSE_WIN_STREAK_TARGET = 3


def load_config() -> dict:
    cfg = yaml.safe_load((Path(__file__).parent / "config.yaml").read_text())
    env_url = os.environ.get("SERVER_URL")
    if env_url:
        cfg["server_url"] = env_url
    return cfg


def _empire_list(api: ApiClient) -> list[dict]:
    """api.empires() returns {"empires": [...]}, not a bare list."""
    empires = api.empires()
    return empires if isinstance(empires, list) else (empires or {}).get("empires", [])


def completed_signature(summary: dict) -> frozenset[str]:
    """Set of completed item iids — used to detect when items catalog changes."""
    done = {iid for iid, rem in (summary.get("buildings") or {}).items()
            if (rem or 0) <= 0}
    done |= {iid for iid, rem in (summary.get("knowledge") or {}).items()
             if (rem or 0) <= 0}
    done |= set(summary.get("artifacts") or [])
    return frozenset(done)


def _sleep_until(deadline: float, stop: dict) -> None:
    while time.time() < deadline and not stop["flag"]:
        time.sleep(0.2)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True, help="bot name (state file key)")
    ap.add_argument("--cycles", type=int, default=0, help="stop after N cycles (0 = forever)")
    ap.add_argument("--fast", action="store_true", help="5s cycle interval (testing)")
    ap.add_argument("--control-port", type=int, default=0)
    ap.add_argument("--allow-remote", action="store_true",
                    help="allow non-localhost server URLs (DANGEROUS)")
    args = ap.parse_args()

    fmt = logging.Formatter(f"%(asctime)s [{args.name}] %(name)s: %(message)s")
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(fmt)
    handlers: list[logging.Handler] = [stream_handler]

    log_dir = Path(__file__).parent / "logs"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_dir / f"{args.name}.log")
        file_handler.setFormatter(fmt)
        handlers.insert(0, file_handler)
    except OSError as e:
        print(f"[{args.name}] file logging disabled ({log_dir}): {e}", flush=True)

    logging.basicConfig(level=logging.INFO, handlers=handlers)

    config = load_config()
    host = urlparse(config["server_url"]).hostname
    env_url_set = bool(os.environ.get("SERVER_URL"))
    if host not in ("localhost", "127.0.0.1") and not args.allow_remote and not env_url_set:
        log.error("refusing non-localhost server %s (use --allow-remote)", host)
        return 1

    state = BotState.load_or_create(args.name)
    api = ApiClient(config["server_url"], state.account["username"], state.account["password"])

    # Signup on first run (state has no uid yet)
    if state.account.get("uid") is None:
        uid = api.signup(state.account["username"], state.account["password"],
                         state.account["empire_name"])
        state.account["uid"] = uid
        state.dirty = True
        state.save()
        log.info("signed up as %s (uid=%d)", state.account["username"], uid)
    else:
        log.info("resuming account %s (uid=%s, %d cycles so far)",
                 state.account["username"], state.account["uid"],
                 state.runtime.get("cycles", 0))

    control = ControlServer(args.control_port or config["control_port_base"] + 1)
    control.start()

    stop = {"flag": False}

    def _on_signal(signum, frame):
        log.info("signal %d, saving state and exiting", signum)
        stop["flag"] = True

    signal.signal(signal.SIGINT, _on_signal)
    signal.signal(signal.SIGTERM, _on_signal)

    interval = 5.0 if args.fast else float(config["cycle_interval_s"])
    run_cycles = 0

    try:
        while not stop["flag"]:
            tick_start = time.time()

            # 1. Login — recreates empire automatically if wiped (auth.py:35-61)
            try:
                api.login()
            except Exception:
                log.exception("login failed — retrying next tick")
                _sleep_until(tick_start + interval, stop)
                continue

            # 2. Run all affordable actions for this tick
            try:
                cycle(api, config, state, control)
            except ApiError as e:
                log.warning("cycle failed: %s", e)
            except Exception:
                log.exception("cycle crashed")

            # 3. Persist state
            run_cycles += 1
            state.runtime["cycles"] = state.runtime.get("cycles", 0) + 1
            state.runtime["last_cycle"] = now_iso()
            if state.dirty:
                state.save()

            # 4. Discard token ("logout") — next tick starts fresh
            api.token = None

            if args.cycles and run_cycles >= args.cycles:
                break

            # 5. Wait until next tick (skipped if cycle took longer than interval)
            _sleep_until(tick_start + interval, stop)
    finally:
        control.stop()
        state.save()
        log.info("state saved to %s", state.path)
    return 0


def _wipe_log_files() -> None:
    """Truncate every FileHandler's backing log file in place.

    The process keeps the file open for the handler's lifetime, so the file
    must be truncated via the open fd (not deleted/reopened) for logging to
    keep working after the wipe.
    """
    for handler in logging.getLogger().handlers:
        if isinstance(handler, logging.FileHandler) and handler.stream:
            handler.stream.truncate(0)
            handler.stream.seek(0)


def _check_season_reset(summary: dict, state: BotState) -> bool:
    """Return True (and reset state + wipe the log file) on a new season."""
    season = summary.get("season_number")
    if season is None:
        return False
    last = state.memory.get("last_season")
    if last is not None and last != season:
        state.reset()
        state.memory["last_season"] = season
        _wipe_log_files()
        log.info("new season %s (was %s) → state and log reset", season, last)
        return True
    state.memory["last_season"] = season
    return False


def cycle(api: ApiClient, config: dict, state: BotState, control: ControlServer) -> None:
    # --- One-time setup for this tick ---
    summary = api.summary()

    # Detect season change and wipe transient state (strategy, memory, savings goals)
    if _check_season_reset(summary, state):
        state.save()

    # Items catalog changes when new items are unlocked; fetch fresh each tick
    # since we have a new token and no stale cache to worry about.
    items = api.items()

    # Control commands (strategy overrides from control port)
    for cmd in control.drain():
        if cmd["cmd"] == "strategy":
            try:
                state.strategy = make_override(cmd["payload"], config)
                state.dirty = True
                log.info("strategy override: %s", state.strategy["type"])
            except ValueError as e:
                log.warning("bad override: %s", e)
        elif cmd["cmd"] == "reroll":
            state.strategy = None
            state.dirty = True

    # Battle reports → memory
    reports = process_new_reports(api.messages(), state.memory, summary.get("era", "stone"))
    if reports:
        state.dirty = True
        for r in reports:
            log.info("battle report: role=%s won=%s reached=%d culture=%+.1f artifacts=%s",
                     r.role, r.won, r.reached, r.culture, r.artifacts)

    # Two rules govern strategy, nothing else:
    # 1. A fully lost defense immediately (and unconditionally) switches to
    #    defense — this always wins, overriding whatever was active before
    #    (attack, growth, or an in-progress defense streak). A battle where
    #    some critters reached the castle but the defender still WON is not
    #    a loss here — only a complete defeat forces this; partial breaches
    #    get the lighter one-off "breach response" action instead
    #    (memory.pending_breach, handled in baseline.py).
    # 2. Winning DEFENSE_WIN_STREAK_TARGET defenses in a row is the ONLY way
    #    out of defense: it rolls a new strategy (attack or growth, weighted
    #    — see bot/strategy.py::roll_strategy). That choice then holds
    #    (NO_EXPIRY) until the next lost defense resets the streak.
    defense_lost = any(r.role == "defender" and not r.won for r in reports)
    if defense_lost:
        state.strategy = breach_defense_strategy(config)
        state.memory["defense_win_streak"] = 0
        state.dirty = True
        log.info("defense lost → forced defense strategy until %s",
                 state.strategy["valid_until"])

    successful_defense = any(r.role == "defender" and r.won for r in reports)
    if successful_defense and not defense_lost:
        streak = int(state.memory.get("defense_win_streak", 0)) + 1
        state.memory["defense_win_streak"] = streak
        state.dirty = True
        if streak < DEFENSE_WIN_STREAK_TARGET:
            log.info("defense succeeded (streak %d/%d) → staying on defense",
                     streak, DEFENSE_WIN_STREAK_TARGET)
        else:
            targets = score_targets(
                _empire_list(api), summary.get("uid", 0),
                float(summary.get("resources", {}).get("culture", 0.0)),
                summary.get("era", "stone"), state.memory)
            state.strategy = roll_strategy(config, state, {"targets": targets})
            log.info("defense streak %d/%d reached → rolled new strategy: %s",
                     streak, DEFENSE_WIN_STREAK_TARGET, state.strategy["type"])

    # Strategy expiry / completion → roll a new strategy. In practice this
    # only ever fires for the "no_targets" placeholder (5 min TTL): defense
    # is only ever entered via rule 1 above (breach_defense_strategy's
    # wall-clock window is set but rule 1 replaces it long before it could
    # expire in normal play), and attack/growth hold with NO_EXPIRY.
    if is_expired(state.strategy) or (state.strategy or {}).get("completed"):
        targets = score_targets(
            _empire_list(api), summary.get("uid", 0),
            float(summary.get("resources", {}).get("culture", 0.0)),
            summary.get("era", "stone"), state.memory)
        state.strategy = roll_strategy(config, state, {"targets": targets})
        state.dirty = True
        log.info("new strategy: %s until %s params=%s",
                 state.strategy["type"], state.strategy["valid_until"],
                 state.strategy["params"])

    # --- Action loop: execute all affordable actions this tick, highest
    # priority first. A server-rejected option (e.g. unmet requirements) is
    # excluded for the rest of THIS tick only (memory isn't touched) so it
    # can't loop forever, but every other priority — including lower ones —
    # still gets tried, per the strict-priority dispatch model (see
    # bot/dispatch.py). ---
    active_type = state.strategy["type"]
    last_action = None
    failed_this_tick: set[str] = set()

    # Fetch map once per tick — shared across all actions to avoid rate-limiting.
    # Invalidated after map-modifying actions (tower placement, tile purchase).
    map_data: dict | None = api.get_map()

    for _ in range(MAX_ACTIONS_PER_TICK):
        summary = api.summary()  # refresh gold/resources after each action
        ctx = BotContext(summary, items, state.memory, state.strategy, api,
                         selection=config.get("selection", {"top_n": 3}),
                         personality=state.personality,
                         map_data=map_data)
        action = choose_action(ctx, config, active_type, exclude=failed_this_tick)
        if action is None:
            break
        result = action.run(api)
        if isinstance(result, dict) and result.get("success") is False:
            log.warning("action FAILED: %s → %s", action.description,
                        result.get("error") or result.get("reason", "?"))
            failed_this_tick.add(action.description)
            continue  # try the next-highest-priority option instead
        log.info("action: %s", action.description)
        last_action = action.description
        state.dirty = True
        # Refresh map after actions that modify it (tile buy, tower placement,
        # tower sale, or era-swap). Any planner action that calls save_map/buy_tile
        # must be listed here, otherwise the stale in-memory map makes the planner
        # re-propose the same action every action-slot until the tick is exhausted.
        if any(w in action.description for w in
               ("buy tile", "build ", "relocate", "move spawn", "move castle",
                "sell ", "tower ", "grow ", "era-swap")):
            map_data = api.get_map()

    if last_action is None:
        log.info("no affordable action for strategy '%s' — waiting", state.strategy["type"])

    # Control status snapshot
    control.status = {
        "name": state.name,
        "uid": state.account.get("uid"),
        "strategy": state.strategy,
        "resources": summary.get("resources", {}),
        "cycles": state.runtime.get("cycles", 0),
        "last_action": last_action,
    }


if __name__ == "__main__":
    sys.exit(main())
