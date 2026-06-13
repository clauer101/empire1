# AI Players

Autonomous bot players for empire1. Bots play via the public REST API and run
completely independent of the gameserver process. **Dev environment only** —
`run_bot.py` refuses non-localhost server URLs.

## Quick start

```bash
# Start the dev stack first (API on localhost:8180), then:
cd ai_players
python run_bot.py --name alice              # signs up a new account on first run
python fleet.py --count 3                   # run 3 bots at once
```

State (credentials, current strategy, memory) is persisted per bot in
`states/<name>.yaml`. On SIGINT/SIGTERM the bot saves state and exits.

## How it works

Every cycle (default 15 s + jitter) the bot:

1. Polls `GET /api/empire/summary` (and the item catalog, cached 5 min)
2. Applies control-API overrides; re-rolls the strategy if expired or completed
3. Parses new battle reports into memory (defense breaches, opponent strength)
4. Lets the active strategy's planner propose **one** action and executes it;
   if nothing is affordable it simply waits

## Strategies

Randomly chosen (weighted) and valid for hours, so bots stick to a plan:

| Strategy | Duration | Behavior |
|---|---|---|
| `economy` | 4–10 h | queue research/buildings with economy effects, buy citizens, ruler skills |
| `defense` | 3–8 h | place towers next to path tiles (near castle), buy tiles, item upgrades |
| `attack` | 1–3 h | build army, spy on a weak target, attack it |
| `artifact` | 1–3 h | like attack, but targets players holding artifacts |

**Baseline obligations** apply to every strategy ([docs/strategies/baseline.md](docs/strategies/baseline.md)):
defense is never neglected (a breach triggers a defensive action before strategy
actions), and building/research idle time is minimized (empty queues are filled
each cycle). Implemented in `bot/planners/baseline.py`, called before the planner.

Detailed goals per strategy: [docs/strategies/economy.md](docs/strategies/economy.md),
[defense.md](docs/strategies/defense.md), [attack.md](docs/strategies/attack.md),
[artifact.md](docs/strategies/artifact.md)

These docs are the **spec** for the planners in `bot/planners/`: each doc names its
implementing class and maps objectives 1:1 to the planner's code. When changing a
planner, compare it against its strategy doc and keep both in sync.

## Control API (strategy overrides)

Each bot runs a localhost HTTP server (port `control_port_base + n`, default 9301+):

```bash
curl localhost:9301/status
curl -X POST localhost:9301/strategy \
  -d '{"type": "attack", "params": {"target_uid": 42, "target_name": "Enemy"}, "duration_hours": 2}'
curl -X POST localhost:9301/reroll
```

Overrides have `source: override` and the given time validity.

## Tests

```bash
cd ai_players && python -m pytest tests/
```
