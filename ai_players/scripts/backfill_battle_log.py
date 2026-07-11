#!/usr/bin/env python3
"""One-off backfill: populate memory["battle_log"] from each bot's full,
already-seen message history.

Why this is needed: process_new_reports() (bot/analyzer.py) only appends to
battle_log for messages with id > last_seen_message_id. Bots that were already
running before battle_log existed have last_seen_message_id far past their
entire battle history, so battle_log stays empty until the *next* battle — the
winrate/last-10 widgets on the bot status page show nothing until then.

This script logs in as each bot, fetches its full message history (the
/api/messages battle_reports list is NOT filtered by read/unread — the bot's
own last_seen_message_id cursor is a client-side concept), and appends any
report not yet represented in battle_log (matched by message id, stored as
"mid" on each entry). It does NOT touch last_seen_message_id, attack_history,
opponents, or breach counters — those already reflect history correctly and
re-running that logic would double-count.

Caveat: old reports have no stored era, so backfilled entries are tagged with
the bot's CURRENT era (one live api.summary() call) — inaccurate for battles
fought in an earlier era, but far better than no data. Only battles from here
forward get the exact era.

Run from the repo root (bots do NOT need to be stopped — this only appends to
battle_log and saves the state file, same file bots already read/write).

The compose-managed dev/prod environments do NOT use ai_players/states/ — the
webserver container bind-mounts data/dev/bot_states (or data/prod/bot_states)
over /app/ai_players/states, so THAT's where the live state files actually
live on the host. Point --states-dir there; otherwise this operates on
whatever states/ dir sits next to this script (only useful for bots run
directly via run_bot.py outside Docker).

    python ai_players/scripts/backfill_battle_log.py \\
        --states-dir data/dev/bot_states                     # dev, all bots
    python ai_players/scripts/backfill_battle_log.py \\
        --states-dir data/dev/bot_states --name alice
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bot.state as _bot_state  # noqa: E402
from bot.analyzer import BATTLE_LOG_CAP, parse_report  # noqa: E402
from bot.api_client import ApiClient, ApiError  # noqa: E402
from bot.state import BotState, now_iso  # noqa: E402

import yaml  # noqa: E402


def load_config() -> dict:
    return yaml.safe_load((Path(__file__).parent.parent / "config.yaml").read_text())


def backfill_bot(name: str, server_url: str) -> int:
    state = BotState.load_or_create(name)
    if state.account.get("uid") is None:
        print(f"[{name}] no account yet, skipping")
        return 0

    api = ApiClient(server_url, state.account["username"], state.account["password"])
    try:
        api.login()
        summary = api.summary()
        messages = api.messages()
    except ApiError as e:
        print(f"[{name}] API error, skipping: {e}")
        return 0

    era = summary.get("era", "stone")
    battle_log = state.memory.setdefault("battle_log", [])
    seen_mids = {e.get("mid") for e in battle_log if e.get("mid") is not None}

    added = 0
    # Oldest first, so battle_log ends up in the same chronological order it
    # would have if these had been processed live.
    reports = sorted(messages.get("battle_reports", []), key=lambda m: m.get("id", 0))
    for msg in reports:
        mid = msg.get("id", 0)
        if mid in seen_mids:
            continue
        report = parse_report(msg.get("body", ""))
        if report is None:
            continue
        battle_log.append({
            "mid": mid,
            "ts": now_iso(),  # backfill time, not the original battle time (not stored server-side)
            "role": report.role,
            "won": report.won,
            "era": era,  # best-effort: bot's current era, not era-at-battle-time
            "opponent": report.opponent,
        })
        seen_mids.add(mid)
        added += 1

    if added:
        state.memory["battle_log"] = battle_log[-BATTLE_LOG_CAP:]
        state.dirty = True
        state.save()
    print(f"[{name}] backfilled {added} battle_log entries "
          f"(total now {len(state.memory['battle_log'])})")
    return added


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", help="only backfill this bot (default: all bots found)")
    ap.add_argument("--states-dir", type=Path, default=None,
                    help="override the states/ directory (e.g. data/dev/bot_states "
                         "for the docker-compose dev environment)")
    ap.add_argument("--server-url", default=None,
                    help="override config.yaml's server_url (e.g. if the dev/prod "
                         "gameserver is reachable at a different host:port from here)")
    args = ap.parse_args()

    if args.states_dir:
        # BotState.path (bot/state.py) builds paths from this module-level
        # constant, so overriding it here redirects load_or_create()/save().
        _bot_state.STATES_DIR = args.states_dir.resolve()

    config = load_config()
    server_url = args.server_url or config["server_url"]

    if args.name:
        names = [args.name]
    else:
        names = sorted(p.stem for p in _bot_state.STATES_DIR.glob("*.yaml"))

    total = 0
    for name in names:
        total += backfill_bot(name, server_url)
    print(f"done: {total} entries backfilled across {len(names)} bot(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
