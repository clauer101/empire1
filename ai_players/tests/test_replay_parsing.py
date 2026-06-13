import gzip
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot.api_client import decode_replay_response  # noqa: E402

REPLAY = {"bid": 1, "events": [{"type": "battle_summary", "defender_won": True}]}


def test_decode_gzip_body():
    body = gzip.compress(json.dumps(REPLAY).encode())
    assert decode_replay_response("application/gzip", body) == REPLAY


def test_decode_plain_json_body():
    body = json.dumps(REPLAY).encode()
    assert decode_replay_response("application/json", body) == REPLAY
