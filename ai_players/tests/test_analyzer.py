import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot.analyzer import parse_report, process_new_reports, score_targets  # noqa: E402

DEFENDER_LOSS = (
    "🛡 You Lost!\n"
    "────────────────────\n"
    "⚔ Attacker(s): Evil Empire\n"
    "📋 Waves:      3\n"
    "────────────────────\n"
    "🐛 Spawned:   24\n"
    "💀 Killed:    18\n"
    "🏰 Reached:   6\n"
    "🗼 Towers:    5\n"
    "💰 Earned:    +120 gold\n"
    "🎭 Culture: -245.5\n"
    "⚜ Lost Almanac stolen by Evil Empire\n"
    "⏱ Duration:  2m 15s\n"
    "────────────────────\n"
    "▶ Replay: #replay/20260610_120000_42"
)

ATTACKER_WIN = (
    "⚔ You Won!\n"
    "────────────────────\n"
    "🛡 Defender:  Weak Empire\n"
    "📋 Army:      Raiders (2 waves)\n"
    "────────────────────\n"
    "🐛 Spawned:   20\n"
    "💀 Killed:    5\n"
    "🏰 Reached:   15\n"
    "🎭 Culture: +122.5\n"
    "⚜ Holy Grail acquired\n"
    "⏱ Duration:  1m 5s\n"
    "────────────────────\n"
    "▶ Replay: #replay/key123"
)


def test_parse_defender_loss():
    r = parse_report(DEFENDER_LOSS)
    assert r is not None
    assert r.role == "defender" and not r.won
    assert r.reached == 6 and r.killed == 18 and r.spawned == 24
    assert r.culture == -245.5
    assert r.artifacts == ["Lost Almanac"]
    assert r.opponent == "Evil Empire"
    assert r.replay_key == "20260610_120000_42"


def test_parse_attacker_win():
    r = parse_report(ATTACKER_WIN)
    assert r.role == "attacker" and r.won
    assert r.culture == 122.5
    assert r.artifacts == ["Holy Grail"]
    assert r.opponent == "Weak Empire"


def test_parse_non_battle_message():
    assert parse_report("hello world") is None


def test_process_new_reports_updates_memory():
    memory = {"last_seen_message_id": 0}
    messages = {"battle_reports": [
        {"id": 1, "body": DEFENDER_LOSS},
        {"id": 2, "body": ATTACKER_WIN},
    ]}
    reports = process_new_reports(messages, memory, era="iron")
    assert len(reports) == 2
    assert memory["last_seen_message_id"] == 2
    assert memory["defense_weak_waves"]["breaches"] == 6
    assert memory["opponents"]["Weak Empire"]["last_outcome"] == "victory"
    assert memory["last_beaten_name"] == "Weak Empire"
    assert memory["attack_history"][-1]["artifacts"] == ["Holy Grail"]
    # battle_log covers both roles, tagged with the era passed in
    assert [e["role"] for e in memory["battle_log"]] == ["defender", "attacker"]
    assert all(e["era"] == "iron" for e in memory["battle_log"])
    assert memory["battle_log"][0]["won"] is False
    assert memory["battle_log"][1]["won"] is True
    assert [e["mid"] for e in memory["battle_log"]] == [1, 2]
    # second run: nothing new
    assert process_new_reports(messages, memory) == []
    assert len(memory["battle_log"]) == 2


def test_score_targets():
    empires = [
        {"uid": 1, "name": "Me", "is_self": True, "culture": 500, "era": "bronze"},
        {"uid": 2, "name": "Weak", "culture": 100, "era": "stone", "online": False,
         "artifact_count": 0},
        {"uid": 3, "name": "Strong", "culture": 900, "era": "future", "online": True,
         "artifact_count": 5},
        {"uid": 4, "name": "Rich", "culture": 300, "era": "bronze", "online": True,
         "artifact_count": 2},
    ]
    targets = score_targets(empires, own_uid=1, own_culture=500, own_era="bronze",
                            memory={})
    uids = [t["uid"] for t in targets]
    assert 1 not in uids          # never self
    assert 3 not in uids          # never higher era
    assert uids[0] == 2           # weakest first

    art_targets = score_targets(empires, 1, 500, "bronze", {}, prefer_artifacts=True)
    assert art_targets[0]["uid"] == 4  # artifact holder preferred


def test_score_targets_prefers_last_beaten():
    empires = [
        {"uid": 1, "name": "Me", "is_self": True, "culture": 500, "era": "bronze"},
        {"uid": 2, "name": "Weakest", "culture": 50, "era": "stone"},
        {"uid": 4, "name": "Rich", "culture": 300, "era": "bronze"},
    ]
    # Without history, the globally weakest empire wins.
    targets = score_targets(empires, 1, 500, "bronze", {})
    assert targets[0]["uid"] == 2

    # Having last beaten "Rich" nudges it above the (still weaker) "Weakest" —
    # this is what lets different bots stick to different opponents instead
    # of every bot converging on the single weakest empire.
    targets = score_targets(empires, 1, 500, "bronze",
                            {"last_beaten_name": "Rich"})
    assert targets[0]["uid"] == 4
