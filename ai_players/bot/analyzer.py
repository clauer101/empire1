"""Battle report parsing and opponent target scoring."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# Battle report body format produced by battle_task.py:
#   "🛡 You Won!" / "🛡 You Lost!"  (defender report)
#   "⚔ You Won!" / "⚔ You Lost!"  (attacker report)
#   "⚔ Attacker(s): NAME, NAME"   / "🛡 Defender:  NAME"
#   "🐛 Spawned:   N" / "💀 Killed:    N" / "🏰 Reached:   N"
#   "🎭 Culture: +N" or "-N", "📖 ... research", "⚜ NAME stolen by X" / "⚜ NAME acquired"
#   "▶ Replay: #replay/KEY"

RE_REACHED = re.compile(r"🏰 Reached:\s*(\d+)")
RE_KILLED = re.compile(r"💀 Killed:\s*(\d+)")
RE_SPAWNED = re.compile(r"🐛 Spawned:\s*(\d+)")
RE_CULTURE = re.compile(r"🎭 Culture:\s*([+-][\d.]+)")
RE_REPLAY = re.compile(r"▶ Replay:\s*#replay/(\S+)")
RE_ATTACKERS = re.compile(r"⚔ Attacker\(s\):\s*(.+)")
RE_DEFENDER = re.compile(r"🛡 Defender:\s*(.+)")
RE_ARTIFACT_STOLEN = re.compile(r"⚜ (.+) stolen by (.+)")
RE_ARTIFACT_ACQUIRED = re.compile(r"⚜ (.+) acquired")


@dataclass
class BattleReport:
    role: str  # "defender" | "attacker"
    won: bool
    spawned: int = 0
    killed: int = 0
    reached: int = 0
    culture: float = 0.0
    artifacts: list[str] = field(default_factory=list)
    opponent: str = ""
    replay_key: str = ""


def parse_report(body: str) -> BattleReport | None:
    """Parse one battle-report message body. Returns None for non-battle messages."""
    if body.startswith("🛡 You Won!"):
        role, won = "defender", True
    elif body.startswith("🛡 You Lost!"):
        role, won = "defender", False
    elif body.startswith("⚔ You Won!"):
        role, won = "attacker", True
    elif body.startswith("⚔ You Lost!"):
        role, won = "attacker", False
    else:
        return None

    def _int(rx: re.Pattern) -> int:
        m = rx.search(body)
        return int(m.group(1)) if m else 0

    report = BattleReport(role=role, won=won,
                          spawned=_int(RE_SPAWNED), killed=_int(RE_KILLED),
                          reached=_int(RE_REACHED))
    m = RE_CULTURE.search(body)
    if m:
        report.culture = float(m.group(1))
    m = RE_REPLAY.search(body)
    if m:
        report.replay_key = m.group(1)
    m = RE_ATTACKERS.search(body) if role == "defender" else RE_DEFENDER.search(body)
    if m:
        report.opponent = m.group(1).strip()
    report.artifacts = (
        [m.group(1) for m in RE_ARTIFACT_ACQUIRED.finditer(body)]
        if role == "attacker"
        else [m.group(1) for m in RE_ARTIFACT_STOLEN.finditer(body)]
    )
    return report


def process_new_reports(messages: dict, memory: dict) -> list[BattleReport]:
    """Parse all unseen battle reports, update bot memory, return new reports."""
    last_id = memory.get("last_seen_message_id", 0)
    new_reports: list[BattleReport] = []
    for msg in messages.get("battle_reports", []):
        mid = msg.get("id", 0)
        if mid <= last_id:
            continue
        last_id = max(last_id, mid)
        report = parse_report(msg.get("body", ""))
        if report is None:
            continue
        new_reports.append(report)
        if report.role == "defender" and report.replay_key:
            # Queue replay for defense weakness analysis (DefensePlanner)
            replays = memory.setdefault("defense_replays", [])
            replays.append(report.replay_key)
            memory["defense_replays"] = replays[-5:]
        if report.role == "defender" and report.reached > 0:
            # Own defense breached: remember the breach severity
            weak = memory.setdefault("defense_weak_waves", {})
            weak["breaches"] = weak.get("breaches", 0) + report.reached
            memory["pending_breach"] = True  # triggers baseline defense response
        if report.role == "attacker" and report.opponent:
            opp = memory.setdefault("opponents", {}).setdefault(report.opponent, {})
            opp["last_outcome"] = "victory" if report.won else "defeat"
            # Strength estimate: ratio of killed critters (higher = stronger defense)
            if report.spawned > 0:
                opp["est_strength"] = round(report.killed / report.spawned, 2)
        memory.setdefault("attack_history", [])
        if report.role == "attacker":
            memory["attack_history"].append({
                "outcome": "victory" if report.won else "defeat",
                "opponent": report.opponent,
                "culture": report.culture,
                "artifacts": report.artifacts,
            })
            memory["attack_history"] = memory["attack_history"][-50:]
    memory["last_seen_message_id"] = last_id
    return new_reports


ERA_RANK = {e: i for i, e in enumerate([
    "stone", "neolithic", "bronze", "iron", "middle_ages",
    "renaissance", "industrial", "modern", "future",
])}


def score_targets(empires: list[dict], own_uid: int, own_culture: float,
                  own_era: str, memory: dict,
                  prefer_artifacts: bool = False) -> list[dict[str, Any]]:
    """Score potential targets; lower-strength opponents first."""
    own_rank = ERA_RANK.get(own_era, 0)
    scored = []
    for e in empires:
        if e.get("uid") == own_uid or e.get("is_self"):
            continue
        rank = ERA_RANK.get(e.get("era", "stone"), 0)
        if rank > own_rank:
            continue  # never attack up
        score = 0.0
        # Weaker (less culture) is better
        culture = float(e.get("culture", 0.0))
        score += max(0.0, 1.0 - culture / max(own_culture, 1.0))
        if not e.get("online"):
            score += 0.5
        if prefer_artifacts:
            score += 2.0 * min(e.get("artifact_count", 0), 3)
        opp = memory.get("opponents", {}).get(e.get("name", ""), {})
        if opp.get("last_outcome") == "victory":
            score += 0.3
        elif opp.get("last_outcome") == "defeat":
            score -= 1.0
        scored.append({**e, "score": score})
    scored.sort(key=lambda x: -x["score"])
    return scored
