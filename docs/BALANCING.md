# Balancing Goals

This is the design intent for combat balance — what a "correctly balanced" maze
and army should feel like, era to era. It's the spec that
`scripts/sim_random_maze.py` (wrapped by the `balancing` skill,
`.claude/skills/balancing/SKILL.md`) exists to check empirically: every goal
below links to the flag combination that tests it.

## 1. Era progression

- Each era's critters should be a noticeable step up from the previous era's.
- A maze built for era N should struggle against critters from era N+1 —
  this already happens for free: `generate_army()` mixes a small,
  configurable slice of next-era critters into an otherwise same-era random
  army (`game.yaml`'s `ai_generator.<era>.min_next_era`/`max_next_era`), so
  ordinary `--era X --n 20` runs already exercise this. No dedicated test
  needed for the *natural* version.
- For a harder, explicit version — "how does an era-N maze do against a
  **full** era-(N+1) army" — use `--army-era`:
  ```bash
  scripts/sim_random_maze.py --era bronze --army-era iron --n 15
  ```

## 2. Tower/critter counters

Towers have a `tower_type` (`strong`/`fast`/`slow`/`burn`/`splash`), critters
have a `critter_type` (`tank`/`fast`/`carrier`/`bulk`/`spread`/`boss`/`health`).
The intended matchups — a maze over-invested in one tower type should be
**strong** against its listed critter type and (where known) **weak** against
its counter:

| Tower type | Strong against (intended) | Weak against (counter) |
|---|---|---|
| `fast`   | `fast` critters   | `tank` critters |
| `burn`   | `tank` critters   | *unknown — find via `--matrix`* |
| `slow`   | `boss` critters   | *unknown — find via `--matrix`* |
| `splash` | `carrier`, `bulk` critters | *unknown — find via `--matrix`* |
| `strong` | none (generalist) | none (generalist) |

`strong` towers are the deliberate baseline: no critter type is their
dedicated counter, and they're not the ideal answer to any critter type
either — every other tower type should beat *something* better than `strong`
does, and lose to *something* worse.

**Why `slow` is intended to beat `boss`/`ruler` specifically:** `boss` and
ruler-carrying critters are rare, single, high-value targets — a `slow`
tower can lock onto one and keep it slowed for its whole time in range.
Every *other* tower near that slowed target benefits too: a slowed critter
spends longer inside each tower's range, so they land more hits on it than
they would against a normal critter. `slow`'s own damage output isn't the
point — it's a force multiplier for the towers around it, which matters most
against a single tough target worth focusing everyone's fire on.

This means testing `slow` in isolation (`--tower-type slow`, an all-`slow`
maze) measures the wrong thing: it strips out every damage tower that would
otherwise benefit from the slow effect, leaving only `slow`'s own (low)
direct damage — the counter-matrix numbers for the `slow` row should not be
read the same way as for `fast`/`burn`/`strong`/`splash`. A fair test mixes
`slow` with damage towers and compares that mix's win rate against the same
mix *without* `slow`, not `slow` alone against a single critter type.

Verify a specific pair:
```bash
scripts/sim_random_maze.py --era bronze --tower-type fast --critter-type tank --n 20   # expect LOW defender win%
scripts/sim_random_maze.py --era bronze --tower-type fast --critter-type fast --n 20   # expect HIGH defender win%
```
Find the missing "weak against" column for `burn`/`slow`/`splash`, and check
the whole table at once, with the matrix mode:
```bash
scripts/sim_random_maze.py --matrix --era bronze --n 15
```

## 3. Tech investment ("getecht")

"Teched" means **workshop `item_upgrades`** applied (tower `damage`/`range`/
`reload`/effect stats, or critter `health`/`speed`/`armour` — see root
`CLAUDE.md`'s Upgrade System section), not tech-tree/era unlocks (those are
already covered by goal 1).

- An upgraded army should beat a stock (un-upgraded) maze of the same era.
- An upgraded maze should beat a stock army of the same era.

**Gap:** `scripts/sim_random_maze.py` currently battles everything at base
stats — the sandbox `Empire` in `scripts/maze_pool.py` never populates
`item_upgrades`, and `scripts/battle_sim.py::make_battle`'s attacker `Army`
has no upgrade-level concept either. This goal **cannot be tested yet**.
Needed before it can be: a way to pass a fixed upgrade level into
`generate_random_maze()`/`generate_random_army()` and confirm how
`battle_service` reads `Empire.item_upgrades` to scale a bare `Structure`'s
stats at battle time (not yet investigated). Flag this to whoever picks up
this gap — it blocks two of the goals in this document.

## 4. Maze length vs. army strength

- Short mazes (near an era's `min_length`) should lose to an era-appropriate
  random army.
- Long mazes (near an era's `max_length`) should beat one.
- Length ranges live in `python_server/config/game.yaml`'s `maze_length`
  section, per era — that's the tuning knob if a whole era is systematically
  too easy or too hard.

```bash
scripts/sim_random_maze.py --era bronze --length 10 --n 15   # near min — expect LOW win%
scripts/sim_random_maze.py --era bronze --length 20 --n 15   # near max — expect HIGH win%
```

## 5. Randomness and variance

- Random armies also draw a small slice of previous/next-era critters (goal
  1), so outcomes should have real spread, not a fixed result — it should be
  possible (if less likely) for a short maze to catch a weak random army and
  win, or a long maze to catch a strong one and lose.
- This is exactly what running `--n 15-20` (not `--n 1`) and reading the
  **win rate**, not a single battle, is for.

## Target win-rate bands

Proposed starting point for reading `--n`-run results (defender win rate) —
adjust once real data pushes back on these:

| Matchup | Target defender win rate |
|---|---|
| Countered (goal 2's "weak against", or maze one era behind) | ~15–40% |
| Balanced / no strong edge either way | ~45–65% |
| Dominant (goal 2's "strong against", or long maze vs. same-era army) | ~75–100% |

A cell that's ~50% when it's supposed to be a hard counter (or the reverse)
is the signal to go tune `game.yaml`/`structures.yaml`/`critters.yaml`.

## Proposed additional goals

Not in the original list — worth deciding whether to adopt:

- **No universally dominant type.** Across a `--matrix` run, no tower type
  should win against *every* critter type of its era, and no critter type
  should beat *every* tower type. If one does, that's an OP flag (mirrors
  `scripts/balance_sim.py`'s existing OP/UP detection, applied to
  auto-generated mazes instead of curated ones).
- **Tech advantage should stay probabilistic, not deterministic.** A
  fully-upgraded maze beating a stock army "dominant"-band (~75-100%) rather
  than always 100% keeps goal 5's variance intact even at the top of the
  upgrade curve — worth stating explicitly once goal 3's gap is closed.
- **A maze that just fell behind an era should be able to catch up.** Goal 1
  says an era-N maze should struggle against era-(N+1) critters; it shouldn't
  say the maze is *permanently* doomed the moment that happens. Given a
  reasonable amount of additional gold/time to react (upgrade or extend), it
  should be able to recover to something like the "balanced" band. Not
  directly testable with this script yet (it builds one maze per trial, not
  a maze that reacts over time) — noted as a direction, not a current check.

## Open gaps

- Upgrade-level simulation (goal 3) — see the callout above.
- The `burn`/`slow`/`splash` "weak against" column (goal 2) is unknown —
  run `--matrix` per era and fill in the table above with what's actually
  found, then decide whether the result matches intent or needs a
  `structures.yaml`/`critters.yaml` tuning pass.
- "Catch-up after falling behind" (proposed goal) has no tooling yet — would
  need a multi-cycle simulation (grow the maze further mid-test), not a
  single-battle one.
