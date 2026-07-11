#!/usr/bin/env python3
"""Spawn AI player bots as subprocesses.

Usage: python fleet.py --count 3 [--fast]
Resumes every bot that already has a persisted state file in states/, then
tops up with freshly-named bots (random fantasy names) until --count bots run.
Each bot gets a unique control port (base+1, base+2, ...).
Ctrl-C stops all bots gracefully (they save state on SIGTERM).
"""

from __future__ import annotations

import argparse
import signal
import subprocess
import sys
import time
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bot.state import BotState, random_fantasy_name  # noqa: E402


def reset_all_states(here: Path) -> None:
    """Clear transient state (strategy, memory, savings goals) from all bot state files.

    Keeps account credentials and personality so bots can log back in after a season reset.
    """
    states_dir = here / "states"
    for path in sorted(states_dir.glob("*.yaml")):
        state = BotState.load_or_create(path.stem)
        state.reset()
        state.save()
        print(f"reset {path.stem}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=3)
    ap.add_argument("--fast", action="store_true")
    ap.add_argument("--reset-states", action="store_true",
                    help="Clear strategy/memory/savings from all bot state files, then exit")
    args = ap.parse_args()

    here = Path(__file__).resolve().parent

    if args.reset_states:
        reset_all_states(here)
        return 0

    config = yaml.safe_load((here / "config.yaml").read_text())
    base_port = config["control_port_base"]

    # Resume every persisted bot, then top up with fresh fantasy-named bots
    # until we reach --count. New names are rolled until unique among states/.
    names = sorted(p.stem for p in (here / "states").glob("*.yaml"))
    while len(names) < args.count:
        name = random_fantasy_name()
        if name not in names:
            names.append(name)

    procs: list[subprocess.Popen] = []
    for port_offset, name in enumerate(names, start=1):
        port = base_port + port_offset
        cmd = [sys.executable, str(here / "run_bot.py"),
               "--name", name, "--control-port", str(port)]
        if args.fast:
            cmd.append("--fast")
        procs.append(subprocess.Popen(cmd))
        print(f"started {name} (pid={procs[-1].pid}, control port {port})")
        time.sleep(1)

    # Docker sends SIGTERM (and fleet runs as PID 1, where unhandled signals
    # are ignored) — translate it into the same shutdown path as Ctrl-C.
    def _sigterm(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, _sigterm)

    try:
        while any(p.poll() is None for p in procs):
            time.sleep(2)
    except KeyboardInterrupt:
        print("stopping fleet...")
        for p in procs:
            if p.poll() is None:
                p.send_signal(signal.SIGTERM)
        for p in procs:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
    return 0


if __name__ == "__main__":
    sys.exit(main())
