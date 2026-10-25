---
name: balancing
description: Run empirical tower/critter balance experiments via scripts/sim_random_maze.py — random maze vs random army per era, single-class counter tests, full counter matrices, cross-era stress tests. Use when asked to check game balance, find OP/UP towers or critters, or test a specific counter matchup.
---

# Balancing

`scripts/sim_random_maze.py` battles a freshly auto-generated maze
(`gameserver/engine/maze_generator.py`, the same engine behind the admin
`/api/admin/maze/step` tool) against a freshly generated random army
(`gameserver/util/army_generator.py`, the same generator behind
`web/tools/send-ai-army.html`'s "🎲 Random Army" button), using the real
headless battle engine (`scripts/battle_sim.py` — no running server needed).
Win rate here is an actual simulated combat outcome, not a formula-based
estimate.

Always run from the repo root with the project venv:
```bash
.venv/bin/python3 scripts/sim_random_maze.py [flags]
```

## Discover what's available first

Tower/critter "class" filters below only work with real values from the
config. Check before guessing:
```bash
.venv/bin/python3 scripts/sim_random_maze.py --list-classes --era bronze
.venv/bin/python3 scripts/sim_random_maze.py --list-classes            # every era
```
`tower_type` is **cumulative** (a maze for era X may place any tower unlocked
up to X). `critter_type` is **native-only** (an army's main pool is exactly
its own era — only a small configured slice mixes in from adjacent eras).
Requesting a type an era doesn't have raises a clear error listing what IS
available for that era; in `--era all` mode such an era is skipped with a
one-line warning instead of aborting the whole run.

## Scenarios

**1. Baseline — random maze vs random army, per era:**
```bash
.venv/bin/python3 scripts/sim_random_maze.py --era bronze --n 20
.venv/bin/python3 scripts/sim_random_maze.py --era all --n 10 --seed 42   # reproducible
```

**2. Single-class counter test** (e.g. "do `fast` towers hold up against an
all-`tank` army?"):
```bash
.venv/bin/python3 scripts/sim_random_maze.py --era bronze --tower-type fast --critter-type tank --n 20
```

**3. Repeated matchup, one side fixed** (e.g. "20x random maze vs an all-tank
army" — leave the tower side unfiltered):
```bash
.venv/bin/python3 scripts/sim_random_maze.py --era bronze --critter-type tank --n 20
```

**4. Full counter matrix for an era** — the fastest way to *find* counters
rather than test a guess. Runs every `tower_type × critter_type` pairing that
exists for one era, `--n` trials each, prints a grid of
`win% (avg life% left)`. A uniformly weak row/column flags an under/over-
powered type; one low cell against an otherwise-strong row flags a specific
counter:
```bash
.venv/bin/python3 scripts/sim_random_maze.py --matrix --era bronze --n 10
```
(`--matrix` requires a single `--era`, not `all` — bounds runtime; a full
9-era matrix sweep is a lot of battles.)

**5. Cross-era stress test** — attacker from a different era than the maze,
e.g. "does a Bronze Age maze already fall to an Iron Age army?":
```bash
.venv/bin/python3 scripts/sim_random_maze.py --era bronze --army-era iron --n 10
```

**6. Fixed maze length** — bypass the random draw from game.yaml's per-era
`maze_length` range to test one exact length (e.g. "is a short len=8 maze
already viable?"):
```bash
.venv/bin/python3 scripts/sim_random_maze.py --era bronze --length 8 --n 10
```

Flags combine freely — e.g. `--era bronze --army-era iron --tower-type slow --n 15`
tests one specific tower class against a next-era army.

## Reading results

Each row is one battle: army name, maze shape (`{towers}t/{path length}len`),
🛡 (defender won) or ⚔ (attacker won) with life left and kills/reached. The
footer gives win rate and average life left across the run — prefer this over
a single battle's outcome; `--n` of at least 10-20 is needed for a stable
signal given both sides are randomized per trial.

## Where the balancing parameter lives

Maze length per era (`min_length`/`max_length`) is a tunable in
`python_server/config/game.yaml`'s `maze_length` section — adjust it there if
a whole era's mazes are systematically too short/long, then re-run to verify.

## Noted, not implemented

Investigated but out of scope for this pass — flag to the user if a
balancing question needs one of these before building it:
- **Upgrade-level sweep**: testing towers at a fixed `item_upgrades` level
  before battle (does maxing out an UP-flagged tower fix it?). Needs
  confirming how `battle_service` applies upgrade scaling to a bare sandbox
  `Structure` first.
- **CSV/report export**: `scripts/balance_sim.py` already does this for the
  curated map pool (`data/balancing/<timestamp>/{battles,critters,towers}.csv`
  + `report.md`) — the same export could be added here for tracking
  auto-generated-maze results over time.
