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
2. Applies control-API overrides
3. Parses new battle reports into memory (defense breaches, opponent strength)
   and applies the two strategy rules (see Strategies below)
4. Runs the action loop (up to `MAX_ACTIONS_PER_TICK` iterations): each
   iteration picks the highest-priority affordable action across baseline +
   the active strategy + attack's free background actions, and executes it —
   so a single cycle can run several actions, not just one. Stops when
   nothing affordable remains.

## Strategies

Only three strategies exist:

| Strategy | Duration | Behavior |
|---|---|---|
| `attack` | until next lost defense | build army, spy on a weak target, attack it |
| `defense` | 3–8 h | place towers next to path tiles (near castle), buy tiles, item upgrades |
| `growth` | until next lost defense | invest in neither attack nor defense, not even attack's free actions — gold piles up for baseline research/buildings only |

Two rules govern strategy, nothing else:

1. **A fully lost defense immediately switches to `defense`** — unconditional,
   overrides whatever was active before, resets the win streak to 0.
2. **Winning 3 defenses in a row is the only way out of `defense`** — rolls a
   new strategy, weighted-random between `attack` and `growth`
   (`config.yaml` `strategy.weights`, scaled by personality). Attack is
   excluded from that roll when no attackable target exists. The result
   holds (`NO_EXPIRY`) until the next lost defense.

Attack's free actions (spy/attack calls, filling empty waves with an
already-unlocked critter) cost no gold, so they run every cycle regardless of
which strategy is active — the sole exception is `growth`, which means
"invest in nothing, not even free."

**Baseline obligations** apply to every strategy except growth
([docs/strategies/baseline.md](docs/strategies/baseline.md)): defense is
never neglected (a breach triggers a defensive action before strategy
actions), and building/research idle time is minimized (empty queues are
filled each cycle). Implemented in `bot/planners/baseline.py`, called before
the planner. Growth deliberately suspends the defense obligations — see
[docs/strategies/growth.md](docs/strategies/growth.md).

Detailed goals per strategy: [defense.md](docs/strategies/defense.md),
[attack.md](docs/strategies/attack.md), [growth.md](docs/strategies/growth.md),
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
