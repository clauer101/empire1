> **Status: active** — concrete value proposals for the imbalances measured in
> `data/balancing/20260820_200802/`. Nothing applied yet.

# Balance Fix Proposal — 2026-08-20

Companion to `tasks/season_balance_diff_analysis_20260820.md` §7. Every change below
**preserves the entity's class identity**: a `fast` tower keeps its short reload, a
`strong` tower keeps its big-hit/slow-cadence profile, a `slow` tower stays a support
tower, `burn` towers keep low direct damage, `splash` keeps its radius role. Where a
stat is raised, another stat on the *same* entity is worsened to pay for it.

## Method

Values are checked against the real combat model, not intuition:
`max(1, damage − armour)` flat subtraction, burn refreshes (never stacks) and ignores
armour, `slow_ratio` = retained speed. The working metric is **pass damage / HP** —
what one tower lands on one critter while it walks through that tower's range
(`net_dps × 2·range / speed`), divided by the critter's HP. `1.00` means one tower
kills it in one pass.

Calibration from the eras the sim says are healthy (Iron 63 %, Medieval 61 %,
Industrial 65 %): a tier's **best available counter** for a tank sits at **0.75–0.9**,
for a fast unit at **0.45–0.7**. The broken tiers sit far below that.

| Era | Sim win % | Tank's best counter | Fast unit's best counter |
|---|---:|---:|---:|
| Medieval | 61 | KNIGHT 0.76 | SAMURAI 0.68 |
| Industrial | 65 | SMALL_TANK 0.89 | MOTORBIKE 0.65 |
| **Bronze** | **52** | SWORDMAN 1.11 | **CHARIOT 0.50** |
| **Renaissance** | **28** | **DRAGOONER 0.46** | NINJA 0.44 |
| **Future** | **0** | **MECH_WARRIOR 0.24** | DRONE 0.55 |

---

## A. Bronze — 52 %, wipes 23 % → 48 %

CHARIOT went to 345 castle breaches (from 34). Its HP ×4 landed in a tier whose
towers gained 26–30 % DPS, and ARROW_TOWER — the tower whose job is fast units — lost
range 2 → 1.5 at the same time, so its pass damage collapsed 1.34 → 0.23.

| Entity | Class | Change | Paying for it |
|---|---|---|---|
| CHARIOT | fast critter | `health: 20 → 12` | — (still 2.4× its pre-pass HP of 5; speed 1.3 and tb 1100 untouched, so it stays the tier's fast unit) |
| BALLISTA_TOWER | strong tower | `damage: 12 → 18` | `reload_time: 5000 → 5600`, `gold: 7800 → 8600` |

BALLISTA gets *more* "strong": a bigger hit on a slower cadence for more money. It is
the tier's designated anti-tank and currently does 0.26 against SWORDMAN.

**Effect:** CHARIOT's best counter 0.50 → **0.83**, BALLISTA vs CHARIOT 0.25 → 0.58,
vs SWORDMAN 0.26 → 0.50.

---

## B. Renaissance — 28 %, wipes 41 % → 72 % (worst regression)

MUSKETEER 67 → 305 breaches, DRAGOONER 13 → 137. The tier ships only two towers of
its own — RIFLE (`fast`) and ICE (`slow`) — and both are outperformed by the previous
era's BOILING_OIL against every single renaissance unit.

| Entity | Class | Change | Paying for it |
|---|---|---|---|
| RIFLE_TOWER | fast tower | `damage: 13 → 18` | `reload_time: 700 → 800`, `gold: 85000 → 95000` |
| ICE_TOWER | slow tower | `slow_ratio: 0.3 → 0.2`, `slow_duration: 3000 → 3500` | `damage: 11 → 9`, `reload_time: 2200 → 2500` |
| MUSKETEER | bulk critter | `health: 126 → 105` | — (`time_between: 400` and 1 slot untouched — the dense-spawn identity is the point of `bulk`) |
| DRAGOONER | tank critter | `armour: 10 → 8.5` | — (health 148 and 2.2 slots untouched) |

RIFLE stays overwhelmingly the fastest-firing tower in the tier — the next own-era
option fires every 2500 ms. The damage bump matters because of the flat-armour floor:
against DRAGOONER it goes from 3 net per shot to 9.5.

ICE stops pretending to be a damage dealer and commits to support. Trading 25 % of its
damage for a stronger, longer slow is a clear win in context: against MUSKETEER the
slow now grants a neighbouring RIFLE_TOWER **+36 damage** instead of +27 (**1.33×**,
21 % → 29 % of the target's HP). That is the honest way to fix a class the report
flags as UP purely because damage-share cannot see support value.

**Effect:** MUSKETEER's best counter 0.55 → **0.67** and it is now a renaissance tower
doing the work, NINJA 0.44 via RIFLE, DRAGOONER 0.46 (see caveat below).

> **Structural caveat — this tier needs content, not just values.** Renaissance has no
> `strong` and no `burn` tower of its own, so its anti-armour answer is a medieval
> tower. DRAGOONER stays at 0.46 no matter how RIFLE is tuned, because a `fast` tower
> is the wrong class for that job. Values alone get Renaissance to roughly Medieval's
> level; closing it properly means giving the tier its own heavy or burn tower.

---

## C. Future — 0 %, 100 % wipes

MECH_WARRIOR's best counter is 0.24; nothing else clears 0.21. SNIPER_TOWER is
classed `fast` but fires every 2600 ms — slower than every other `fast` tower in the
game (MG 350, GATLING 550, RIFLE 700, CROSSBOW 850, ARROW 1000).

| Entity | Class | Change | Paying for it |
|---|---|---|---|
| SNIPER_TOWER | fast tower | `reload_time: 2600 → 1600` | `range: 4 → 3.5`, `gold: 800000 → 950000` |
| LASER_TOWER | strong tower | `damage: 180 → 200`, `reload_time: 5000 → 4000` | `gold: 400000 → 700000` |
| ROCKET_TOWER | splash tower | `damage: 60 → 110`, `reload_time: 5000 → 4200` | `splash_radius: 0.5 → 0.3`, `gold: 1000000 → 800000` |
| MECH_WARRIOR | tank critter | `health: 937 → 800`, `armour: 35 → 26` | — (speed 0.65 and 3 slots untouched; still the toughest non-boss in the game by a wide margin — SIEGE_TANK is 350/18) |

Two of these fix problems the analysis already flagged. LASER's price rise closes
§6.1 — at 400 000 gold it had the best gold-per-DPS of anything past Industrial while
being the only tower that never hits the armour floor. ROCKET's radius cut defuses
§6.5: raising its damage while keeping the game's largest no-falloff splash radius
would be exactly the time bomb the notes warn about, so the damage comes with a
smaller area, and the price drops because at 1 M gold for 7.3 % damage share it is
currently the worst value in the game.

**Effect:** MECH_WARRIOR's best counter 0.24 → **0.42** (LASER), with SNIPER 0.33 and
NAPALM 0.32 as real second answers instead of nothing. DRONE 0.55 → **0.78** via
SNIPER — the `fast` tower now counters the `fast` critter, which is what the classes
are for.

---

## D. The slow-tower class — flagged UP in every era, in both runs

§6.3 predicted this and the run confirmed it: TAR_TOWER's damage per placement fell
2409 → 783 (−68 %) and COLD_TOWER's 173 → 68 (−61 %), making COLD the weakest tower in
the game. Both were nerfed on *damage and slow simultaneously*, in a class the
baseline already called underpowered.

| Entity | Class | Change | Paying for it |
|---|---|---|---|
| COLD_TOWER | slow tower | `damage: 5 → 6`, `reload_time: 2700 → 2200`, `slow_ratio: 0.5 → 0.4` | `gold: 17600 → 19500` |
| TAR_TOWER | slow tower | `damage: 8 → 13`, `slow_ratio: 0.4 → 0.3` | `reload_time: 2400 → 2600`, `gold: 40000 → 44000` |

Neither becomes a damage dealer — TAR at 13 damage is still below its pre-pass 15, and
both keep their low-damage/high-utility profile. The slow restoration is the real
content: TAR's assist to a neighbouring HEAVY_TOWER goes up 1.17×, COLD's to a
CROSSBOW_TOWER 1.20×.

Also worth doing while in this file: **the `slow_ratio` comments in `structures.yaml`
are inverted** (`slow_ratio: 0.6 # slows to 30% speed for 1s` on a 2500 ms effect).
Fixing them costs nothing and prevents the next pass from repeating this mistake.

---

## E. Modern and Industrial — smaller corrections

| Entity | Class | Change | Paying for it |
|---|---|---|---|
| NAPALM_THROWER | burn tower | `range: 1.5 → 1.8`, `burn_dps: 42 → 46` | `gold: 540000 → 600000` |
| SOLDIER | health critter | `health: 321 → 250` | — (`time_between: 400` untouched) |

NAPALM's direct damage stays at **1** — the DoT identity is untouched, and the buff
runs entirely through the armour-ignoring channel, which is the correct lever against
the armour inflation this pass introduced. It is also the Future tier's only
armour-ignoring answer, so this change does double duty (§C).

SOLDIER produced 695 castle breaches in Industrial, up from 196 — HP +70 % *plus* the
`bulk` → `health` reclassification stacked. 250 is still +32 % on its pre-pass value.

**Effect:** SIEGE_TANK's best counter 0.91 → **1.19**, SPECOPS 0.39 → 0.51,
HELI 0.43 → 0.57, SOLDIER 0.42 → 0.54.

---

## Result across all tiers

| Era | Unit | Best counter now | After proposal |
|---|---|---:|---:|
| Bronze | CHARIOT (fast) | 0.50 | **0.83** |
| Renaissance | MUSKETEER (bulk) | 0.55 | **0.67** |
| Renaissance | DRAGOONER (tank) | 0.46 | 0.46 ⚠ content gap |
| Industrial | SOLDIER (health) | 0.42 | **0.54** |
| Modern | SIEGE_TANK (tank) | 0.91 | **1.19** |
| Modern | SPECOPS (bulk) | 0.39 | **0.51** |
| Future | MECH_WARRIOR (tank) | 0.24 | **0.42** |
| Future | DRONE (fast) | 0.55 | **0.78** |

Iron, Medieval and Stone are deliberately untouched — the sim says they are fine.

## Verification

These are model-checked, not simulated. Before committing:

```bash
.venv/bin/python scripts/balance_sim.py --era all --n 20 --seed 0
```

and compare against `data/balancing/20260820_200802/`. Watch for over-correction in
Modern (SIEGE_TANK at 1.19 is above the healthy band) and check whether Renaissance
clears 50 % — if it stalls in the 40s, that confirms the structural gap in §B and the
tier needs its own heavy or burn tower rather than more tuning.
