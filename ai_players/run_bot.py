#!/usr/bin/env python3
"""Standalone AI player bot for empire1 (dev environment only).

Usage:
    python run_bot.py --name alice [--cycles N] [--fast] [--control-port 9301]

On first start the bot signs up a fresh account; credentials and all internal
state are persisted to states/<name>.yaml. SIGINT/SIGTERM saves state and exits.
"""

from __future__ import annotations

import argparse
import logging
import os
import random
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
    attack_defeat_strategy, breach_defense_strategy, is_expired, make_override,
    roll_secondary, roll_strategy, should_respond_to_attack_defeat,
    should_respond_to_breach,
)

log = logging.getLogger("bot")


def load_config() -> dict:
    cfg = yaml.safe_load((Path(__file__).parent / "config.yaml").read_text())
    env_url = os.environ.get("SERVER_URL")
    if env_url:
        cfg["server_url"] = env_url
    return cfg


def completed_signature(summary: dict) -> frozenset[str]:
    """Set of completed item iids (mirrors BotContext.completed)."""
    done = {iid for iid, rem in (summary.get("buildings") or {}).items()
            if (rem or 0) <= 0}
    done |= {iid for iid, rem in (summary.get("knowledge") or {}).items()
             if (rem or 0) <= 0}
    done |= set(summary.get("artifacts") or [])
    return frozenset(done)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True, help="bot name (state file key)")
    ap.add_argument("--cycles", type=int, default=0, help="stop after N cycles (0 = forever)")
    ap.add_argument("--fast", action="store_true", help="1s poll interval (testing)")
    ap.add_argument("--control-port", type=int, default=0)
    ap.add_argument("--allow-remote", action="store_true",
                    help="allow non-localhost server URLs (DANGEROUS)")
    args = ap.parse_args()

    fmt = logging.Formatter(f"%(asctime)s [{args.name}] %(name)s: %(message)s")
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(fmt)
    handlers: list[logging.Handler] = [stream_handler]

    # File logging is best-effort: if the logs dir is missing or not writable
    # (e.g. a freshly re-created bind-mount owned by root), keep running and
    # log to stdout only instead of crashing on startup.
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

    # Signup on first run
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
    api.login()

    control = ControlServer(args.control_port or config["control_port_base"] + 1)
    control.start()

    stop = {"flag": False}

    def _on_signal(signum, frame):
        log.info("signal %d, saving state and exiting", signum)
        stop["flag"] = True

    signal.signal(signal.SIGINT, _on_signal)
    signal.signal(signal.SIGTERM, _on_signal)

    items_cache: dict = {"items": {}, "at": 0.0, "sig": None}
    poll = 1.0 if args.fast else float(config["poll_interval_s"])
    jitter = 0.0 if args.fast else float(config["jitter_s"])

    run_cycles = 0
    try:
        while not stop["flag"]:
            try:
                cycle(api, config, state, control, items_cache)
            except ApiError as e:
                log.warning("cycle failed: %s", e)
            except Exception:
                log.exception("cycle crashed")

            run_cycles += 1
            state.runtime["cycles"] = state.runtime.get("cycles", 0) + 1
            state.runtime["last_cycle"] = now_iso()
            if state.dirty:
                state.save()
            if args.cycles and run_cycles >= args.cycles:
                break
            deadline = time.time() + poll + random.uniform(0, jitter)
            while time.time() < deadline and not stop["flag"]:
                time.sleep(0.2)
    finally:
        control.stop()
        state.save()
        log.info("state saved to %s", state.path)
    return 0


def cycle(api: ApiClient, config: dict, state: BotState,
          control: ControlServer, cache: dict) -> None:
    summary = api.summary()

    # The items catalog is server-filtered by progress: completing an item can
    # unlock new catalog entries, so refetch whenever the completed set changes.
    completed_sig = completed_signature(summary)
    if (time.time() - cache["at"] > config["items_cache_s"]
            or not cache["items"]
            or cache.get("sig") != completed_sig):
        cache["items"] = api.items()
        cache["at"] = time.time()
        cache["sig"] = completed_sig
    items = cache["items"]

    # 1. Control commands
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

    # 2. Battle reports → memory
    reports = process_new_reports(api.messages(), state.memory)
    if reports:
        state.dirty = True
        for r in reports:
            log.info("battle report: role=%s won=%s reached=%d culture=%+.1f artifacts=%s",
                     r.role, r.won, r.reached, r.culture, r.artifacts)

    # 2b. Breach → defense: an AI break-through always switches the bot to the
    #     defense strategy so the following hours strengthen the perimeter
    #     (the baseline breach response additionally acts on the very next cycle).
    breach = any(r.role == "defender" and r.reached > 0 for r in reports)
    if breach and (state.strategy or {}).get("type") != "defense":
        if should_respond_to_breach(config, state.personality):
            state.strategy = breach_defense_strategy(config)
            state.dirty = True
            log.info("breach detected → forced defense strategy until %s",
                     state.strategy["valid_until"])
        else:
            log.info("breach detected → %s personality keeps current strategy '%s'",
                     state.personality, (state.strategy or {}).get("type"))

    # 2b. Offensive analog to the breach response: a LOST attack switches the
    #     bot back to the attack strategy against the same opponent (revenge).
    #     Mark the defeat in memory too, so the next regular roll still boosts
    #     attack even when the forced switch is skipped or breach wins above.
    lost_attack = next((r for r in reports if r.role == "attacker" and not r.won), None)
    if lost_attack:
        state.memory["recent_attack_defeat"] = True
        state.dirty = True
    if (lost_attack and not breach
            and (state.strategy or {}).get("type") != "attack"
            and should_respond_to_attack_defeat(config, state.personality)):
        target = next((e for e in (api.empires() or [])
                       if e.get("name") == lost_attack.opponent), None)
        if target:
            state.strategy = attack_defeat_strategy(
                config, int(target["uid"]), lost_attack.opponent)
            state.dirty = True
            log.info("attack defeat → forced revenge attack on %s until %s",
                     lost_attack.opponent, state.strategy["valid_until"])

    # 3. Strategy expiry / completion / roll
    if is_expired(state.strategy) or (state.strategy or {}).get("completed"):
        military = api.military()
        empires = api.empires()
        empire_list = empires if isinstance(empires, list) else empires.get("empires", [])
        targets = score_targets(
            empire_list, summary.get("uid", 0),
            float(summary.get("resources", {}).get("culture", 0.0)),
            summary.get("era", "stone"), state.memory)
        context = {
            "has_army": bool(military.get("armies")),
            "army_price": float(summary.get("army_price", 0.0) or 0.0),
            "recent_defeat": any(r.role == "defender" and not r.won for r in reports),
            "recent_attack_defeat": bool(state.memory.get("recent_attack_defeat")),
            "gold": float(summary.get("resources", {}).get("gold", 0.0)),
            "targets": targets,
        }
        state.strategy = roll_strategy(config, state, context)
        # The defeat boost applies to exactly one roll, then the flag is spent.
        state.memory.pop("recent_attack_defeat", None)
        state.dirty = True
        log.info("new strategy: %s until %s params=%s",
                 state.strategy["type"], state.strategy["valid_until"],
                 state.strategy["params"])

    # 4. Plan + execute one action. The dispatcher gathers scored options from
    #    baseline + active strategy + one weighted secondary strategy and picks
    #    the best (utility-per-gold × personality/active-strategy weight).
    active_type = state.strategy["type"]
    has_target = bool((state.strategy.get("params") or {}).get("target_uid"))
    secondary_type = roll_secondary(config, state, active_type, has_target)
    ctx = BotContext(summary, items, state.memory, state.strategy, api,
                     selection=config.get("selection", {"top_n": 3}),
                     personality=state.personality)
    action = choose_action(ctx, config, active_type, secondary_type)
    if action:
        result = action.run(api)
        if isinstance(result, dict) and result.get("success") is False:
            log.warning("action FAILED: %s → %s", action.description,
                        result.get("error") or result.get("reason", "?"))
        else:
            log.info("action: %s", action.description)
        state.dirty = True
    else:
        log.info("no affordable action for strategy '%s' — waiting", state.strategy["type"])

    # 5. Status snapshot for control API
    control.status = {
        "name": state.name,
        "uid": state.account.get("uid"),
        "strategy": state.strategy,
        "resources": summary.get("resources", {}),
        "cycles": state.runtime.get("cycles", 0),
        "last_action": action.description if action else None,
    }


if __name__ == "__main__":
    sys.exit(main())
