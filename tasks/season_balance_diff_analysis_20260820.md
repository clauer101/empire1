> **Status: active** — analysis of the config changes between 2026-08-10 and
> 2026-08-20. Describes what changed and what it implies; no code changes made.

# Config Diff Analysis: 2026-08-10 → 2026-08-20

Baseline commit: `63b732d` (prod snapshot, 2026-08-10 17:56). Compared against the
current working tree (HEAD `4882385` + uncommitted edits).

## 0. Change timeline — everything landed in one day

The five config files were **untouched for ten days**. All changes come from two
edits on 2026-08-20:

| Wave | Where | Files | Character |
|---|---|---|---|
| A | commit `7736db7` "pre bala changes" (17:36) | rulers, artifacts, game, critters (requirements only), structures (partial) | **Structural**: ruler skill trees reshuffled, artifact effects rewritten, economy/prices, unlock-requirement simplification |
| B | uncommitted working tree | critters, structures | **Numeric**: the actual season balance pass (HP/armor/speed/damage/reload) |

`data/balancing/20260820_185405/` and `.../20260820_185426/` are the **pre-change**
baseline (identical win rates in both). **Wave B has not been re-simulated.**

Diff volume: rulers 75±, critters 89±, structures 76±, artifacts 19/22, game 21/25.

---

## 1. `game.yaml` — economy and new systems

### Removed
- **`spy_costs` block deleted entirely** (defense 500 / build_queue 1000 /
  research_queue 2000 / attacks 5000 / artifacts 10000). The loader's
  `SpyCosts` dataclass and its "required section" validation are gone too, and no
  reference remains anywhere in `python_server/src` or `web/js`.
  Spying is no longer a gold purchase — it is now a **spy army attack**
  (`POST /api/spy-attack`, `handle_spy_attack` in `network/handlers/military.py`),
  gated by `max_spy_armies: 1` instead of by gold. New frontend:
  `web/js/lib/spy_report_overlay.js`, `GET /api/spy-reports`.

### Added
- `alliance_culture_cost: 0.05` and `max_alliances: 1` — config for the new
  alliance/diplomacy system (`network/routers/diplomacy.py`). Forming *and*
  breaking an alliance costs 5 % of own culture; hard cap of one ally.

### Changed
| Key | Old → New | Effect |
|---|---|---|
| `accounts_per_artifact` | 11 → 8 | ~38 % more artifacts in circulation per player count |
| `spy_effects.*` (all four) | 0.25 → 0.5 | Spy sabotage effects doubled: slow_tower, reduce_tower_damage, increase_armour, increase_critter_speed |
| `prices.citizen` | u 34→6, y 1→7.8, z 1.5→1, v 3.3→3.6 | Curve reshaped: much lower entry cost, far steeper growth |
| `prices.tile.v` | 2.1 → 2.4 | Steeper tile-cost growth |
| `prices.army` (z/v) | z 2→1.5, v 6.8→8 | Cheaper early armies, much steeper late |
| `era_upgrade_costs` (last 4) | 128k/280k/430k/730k → 228k/480k/1.43M/2.73M | **Late-era progression cost up 1.8×–3.7×** |
| `item_upgrade_base_costs` | 540/900/1800/3600/5400 → 440/1800/3800/4600/5400 | Level 2 cheaper, levels 3–4 roughly doubled |

**Reading:** a deliberate flattening of the early game and steepening of the late
game. The `accounts_per_artifact` cut plus doubled spy effects plus the alliance
cap all push toward more PvP interaction density.

---

## 2. `rulers.yaml` — skill trees restructured, not just retuned

All five rulers had **skills swapped between slots**, which is a bigger change than
the raw diff size suggests: an existing player's invested skill points now sit on a
different effect.

| Ruler | Slot move |
|---|---|
| MAJA | `w` gold_lump_sum_after_research → **workshop_cost_modifier**; `r` workshop_cost_modifier → **gold_lump_sum_after_research** (swapped w↔r) |
| BORIN | `w` wave_delay_offset **unit fix: 0.6–3 → 1200–4000** (seconds → milliseconds); `e` restore_life_after_loss → **artifact_retention_time**; `r` artifact_retention_time → **critter_gold_modifier** |
| ALRIC | `e` artifact_steal_* → **enemy_siege_time_modifier**; `r` enemy_siege_time_modifier → **artifact steal package** (now incl. new `artifact_steal_defeat_modifier`) |
| NANDI / LUCIEN | Slots kept, values rescaled |

Two things worth flagging:

1. **`wave_delay_offset` 0.6 → 1200 is almost certainly a unit bugfix**, not a
   buff — the old values were in seconds against a millisecond field, i.e. the
   skill was effectively inert. Verify which unit the engine consumes.
2. **`LUCIEN.e` level 3 is `other_citizen_gold_modifier: 0`** — a dead level in the
   middle of a monotone ramp (0.004 / 0.005 / **0** / 0.007 / 0.01). Levelling from
   2 to 3 makes the player strictly worse. Looks like a typo for 0.006.

Value trend elsewhere: **level-1 entries were removed and the ramps compressed
upward** — most skills now start where level 2 used to be and end lower than the old
level 5 (e.g. MAJA research_speed 0.1–1.6 → 0.2–1.5, ALRIC wave_slot 0.05–0.25 →
0.1–0.3). Net: less spread between an unskilled and a maxed ruler, higher floor.
The `r` (ultimate) tiers moved the other way — NANDI's culture lump sum 5M → 10M,
MAJA's gold lump sum 200k → 1M.

---

## 3. `artifacts.yaml` — offsets purged, culture added everywhere

Systematic rewrite along two axes:

- **Almost every `*_offset` effect was deleted** (`gold_offset`, `culture_offset`,
  `research_speed_offset`, `build_speed_offset`), leaving `*_modifier` effects only.
  Sole survivor: `BOOK_OF_HEROES.research_speed_offset` (0.3 → 0.2).
- **Surviving modifiers were cut hard** — typically to 20–40 % of their old value:
  `ANCIENT_RELIQUE.research_speed_modifier` 0.8 → 0.1, `SCROLLS_OF_WISDOM` 0.8 → 0.2,
  `LOST_ALMANAC` 0.4 → 0.1, `AWE_INSPIRING_GRAIL.culture_modifier` 0.33 → 0.2.
- **`culture_modifier` was added to six artifacts** that had none
  (ASSASSINS_DAGGER 0.3, BATTLE_DRUMS 0.2, FINE_TROWEL 0.2, GOLDEN_ARC 0.1,
  MERCIFUL_ARMOUR 0.2, AWE_INSPIRING_GRAIL 0.2).

**Reading:** artifacts were roughly halved in raw economic power and re-pointed at
culture — consistent with `accounts_per_artifact` 11 → 8 (more artifacts held, each
worth less), and with culture becoming the currency alliances are paid for.

---

## 4. `critters.yaml` — the attacker side of the balance pass

### 4a. Wave A (committed): unlock requirements simplified
19 critters lost their **building** prerequisites, keeping only knowledge:
`WARRIOR [CRAFTSMANSHIP, GRANARY] → [CRAFTSMANSHIP]`, `SWORDMAN` lost SWORD_MAKER,
`HORSEMAN_*` lost STABLES, `LEGIONARY [FORGE, LORE_COLLECTION, MECHANICS] →
[MECHANICS]`, `SPECOPS` lost ELITE_ACADEMY, `THE_GENERAL` lost RECRUITING_OFFICE, etc.
Every unit is now gated by 1–2 knowledge items. This **materially accelerates
army access** and devalues the dropped military buildings — worth checking whether
those buildings still have any purpose.

### 4b. Wave B (uncommitted): stats

Aggregate per era (mean change across that era's units):

| Era | Tower DPS Δ | Critter HP Δ | Armor Δ | Speed Δ | Spawn rate Δ |
|---|---:|---:|---:|---:|---:|
| neolithic | **+50 %** | +6 % | +25 % | +50 % | −10 % |
| bronze | +77 % | **+193 %** | +58 % | +4 % | −4 % |
| iron | +39 % | +44 % | +19 % | +5 % | 0 % |
| medieval | **−2 %** | +26 % | +2 % | +11 % | +9 % |
| renaissance | **+1 %** | +6 % | **+38 %** | **+32 %** | +6 % |
| industrial | +21 % | +21 % | +7 % | +17 % | +4 % |
| modern | +31 % | +27 % | +20 % | +3 % | **+20 %** |
| future | +8 % | **+67 %** | **+47 %** | +18 % | 0 % |

Biggest individual moves:

- **MECH_WARRIOR** (future tank): HP 400 → 937 (+134 %), armor 18 → **35** (+94 %),
  speed 0.5 → 0.65. The single largest buff in the file.
- **SOLDIER** (industrial): HP 189 → 321 (+70 %) **and reclassified `bulk` → `health`**.
- **SPECOPS** (modern): HP 240 → 410 (+71 %), still `bulk`, still 1 slot / 300 ms —
  the identity problem flagged in `season_balance_magnitude_notes.md` §7.2 was **not**
  addressed, it was amplified.
- **SWORDMAN** (bronze tank): HP 14 → 39 (+179 %), armor 4 → 7 (+75 %).
- **BOWMAN** HP ×2, **CHARIOT** HP ×4, **HORSEMAN_FAST** HP ×2, **CONDOTTERI** +41 %,
  **MUSKETEER** +37 %, **KNIGHT** HP +36 % / armor 8.5 → 12, **THE_GENERAL** armor 13 → 25.
- **THE_KING** (renaissance boss): HP 1080 → 880 (−19 %) but speed **0.45 → 1.0**
  (+122 %) — the only boss that got faster instead of tankier.
- Fast units got uniformly faster *and* denser: NINJA 1.45→1.6 & 900→700 ms,
  HELI 1.6→1.8 & **900→500 ms**, MOTORBIKE 1.5→1.7 & 700→600 ms, SAMURAI 1.4→1.5 &
  1000→800 ms, DRONE 1.9→2.0.
- Carriers got faster: CART 0.2→0.4, SIEGE_RAM 0.4→0.6, TRANSPORTER 0.4→0.6,
  CARGO 0.7→0.9 **and slots 4 → 3** (cheaper wave capacity for the same payload).

The class specialization intent from the notes is clearly executed: **tanks tankier,
fast units faster and denser, carriers cheaper to field.**

---

## 5. `structures.yaml` — the defender side

### Single-target DPS (burn-aware; burn *refreshes*, it does not stack)

| Tower | Era | DPS old → new | Δ |
|---|---|---:|---:|
| DOUBLE_SLING_TOWER | neolithic | 0.91 → 1.82 | **+100 %** |
| ARROW_TOWER | bronze | 2.31 → 3.00 | +30 % |
| BALLISTA_TOWER | bronze | 1.90 → 2.40 | +26 % |
| FIRE_TOWER | bronze | 1.58 → 4.33 | **+174 %** |
| COLD_TOWER | iron | 2.31 → 1.85 | −20 % |
| ARBELESTE_TOWER | iron | 2.73 → 4.58 | +68 % |
| CROSSBOW_TOWER | iron | 3.64 → 7.06 | +94 % |
| TAR_TOWER | medieval | 7.14 → 3.33 | **−53 %** |
| HEAVY_TOWER | medieval | 6.00 → 7.02 | +17 % |
| BOILING_OIL | medieval | 13.24 → 18.53 | +40 % |
| CANNON_TOWER | medieval | 4.38 → 3.80 | −13 % |
| RIFLE_TOWER | renaissance | 16.67 → 18.57 | +11 % |
| ICE_TOWER | renaissance | 5.50 → 5.00 | −9 % |
| FLAME_THROWER | industrial | 26.97 → 28.33 | +5 % |
| GATLING_TOWER | industrial | 21.82 → 30.91 | +42 % |
| SHOCK_TOWER | industrial | 8.24 → 9.47 | +15 % |
| MG_TOWER | modern | 45.71 → 54.29 | +19 % |
| RADAR_TOWER | modern | 3.73 → 6.40 | +72 % |
| ANTI_AIR_TOWER | modern | 15.26 → 20.00 | +31 % |
| PARALYZNG_TOWER | modern | 6.67 → 8.57 | +29 % |
| SNIPER_TOWER | future | 36.11 → 25.00 | **−31 %** |
| LASER_TOWER | → future | 16.00 → 36.00 | **+125 %** |
| ROCKET_TOWER | future | 40.00 → 12.00 | **−70 %** |

### Identity / structural changes
- **LASER_TOWER moved `era: modern` → `era: future`**, damage 80 → 180, new sprite
  (`assets/sprites/structures/laser_tower/laser_tower.webp`, added this pass).
- **ROCKET_TOWER `strong` → `splash`**: damage 200 → 60, `splash_radius: 0.5`,
  range 6 → 2.5, shot_speed 0.5 → 3.
- **SNIPER_TOWER range 10 → 4** (a range-10 tower covered most of a map).
- Range: ARROW 2→1.5, ICE 3→2.5, FLAME 1.5→2, RADAR 1.5→2.5.
- Splash radii: CANNON 0.3→0.35, RADAR 0.3→0.4, ROCKET new 0.5.
- Slow effects retuned. **`slow_ratio` is the *retained* speed fraction**
  (`critter.slow_speed = critter.speed * slow_ratio`, `battle_service.py:313`), so a
  *lower* value is a *stronger* slow — the inline comments in `structures.yaml` state
  the inverse and are wrong throughout (e.g. `slow_ratio: 0.6 # slows to 30% speed
  for 1s` on a 2500 ms effect). Reading the values correctly:

  | Tower | duration | retained speed | verdict |
  |---|---|---|---|
  | SPIKE_TRAP | 2000 → 2500 | 70 % → 60 % | buff (longer + stronger) |
  | COLD_TOWER | 3000 | 40 % → **50 %** | **nerf** |
  | TAR_TOWER | 3000 → 3300 | 30 % → **40 %** | **nerf** (longer, but weaker) |
  | SHOCK_TOWER | 1500 → 2500 | 35 % → **20 %** | strong buff (longer + stronger) |
- Burn effects up across the board: FIRE 1.25→4 dps, BOILING_OIL 16→22,
  FLAME 26→32, NAPALM 36→42 dps.
- CANNON_TOWER lost the CANNON_MANUFACTORY requirement (GUNPOWDER only).

### Gold efficiency (gold per point of DPS, lower = better)

| Tower | Era | old → new |
|---|---|---:|
| FIRE_TOWER | bronze | 3158 → **1154** |
| BOILING_OIL | medieval | 3551 → **2536** |
| GATLING_TOWER | industrial | 5729 → 4044 |
| **LASER_TOWER** | future | 25 000 → **11 111** |
| MG_TOWER | modern | 8750 → 7368 |
| TAR_TOWER | medieval | 5600 → **12 000** |
| SNIPER_TOWER | future | 22 154 → 32 000 |
| **ROCKET_TOWER** | future | 25 000 → **83 333** |
| RADAR_TOWER | modern | 134 211 → 78 125 |

---

## 6. Findings and risks

### 6.1 LASER_TOWER is now the strongest tower in the game — and it is not a future tower in practice
`era` is display metadata only (`network/handlers/economy.py` uses it for grouping;
unlock is decided by `requirements`). LASER_TOWER's requirements are unchanged —
`RESEARCH_LAB` (era modern) and `ELECTRONICS` (era modern). So it is labelled
"future" but buildable in the **modern** era, at an unchanged **400 000 gold**, with
damage 180. It has the best gold/DPS of any tower past industrial (11 111 vs
ANTI_AIR 22 500, SNIPER 32 000, ROCKET 83 333) *and* 180 flat damage means it is the
only tower that never approaches the `max(1, damage − armor)` floor: net 145 against
MECH_WARRIOR's new armor 35, where HEAVY_TOWER nets 1. Expect it to become the
mandatory pick from modern onward. Either raise its cost, restore modern-tier
damage, or move its requirements to actual future-era knowledge.

### 6.2 The `max(1, damage − armor)` floor got worse, not better
The notes' §7.1 proposal was to lift floored towers above Modern-tier armor. Net
damage per shot against the new armor values:

| vs. | MECH_WARRIOR (35) | THE_GENERAL (25) | KNIGHT (12) |
|---|---:|---:|---:|
| HEAVY_TOWER (33) | 9 → **1** | 14 → 8 | 18 → 21 |
| MG_TOWER (19) | 1 → 1 | 3 → **1** | 8 → 7 |
| GATLING_TOWER (17) | 1 → 1 | 1 → 1 | 4 → 5 |
| RADAR_TOWER (32) | 1 → 1 | 6 → 7 | 10 → 20 |
| TAR_TOWER (8) | 1 → 1 | 2 → **1** | 6 → **1** |
| ANTI_AIR_TOWER (72) | 40 → 37 | 45 → 47 | 50 → 60 |
| LASER_TOWER (180) | 62 → 145 | 67 → 155 | 72 → 168 |

MECH_WARRIOR's armor 35 now floors **every tower except ANTI_AIR, SNIPER, LASER and
ROCKET**. THE_GENERAL's armor 25 floors MG and GATLING. The gap between "works" and
"does literally 1 damage" widened.

**Mitigation that is present:** burn ignores armor entirely, and burn was buffed
everywhere (FIRE ×3.2, BOILING_OIL +38 %, FLAME +23 %, NAPALM +17 %). That matches
the notes' §7.1 "surgical fix" — DoT as the anti-armor answer. But burn only exists
in 4 towers, and none of them are in iron, renaissance or future.

### 6.3 TAR_TOWER contradicts the baseline finding
Notes §7.4: slow towers are underpowered **in every era**. TAR_TOWER was then cut
from 15 → 8 damage (DPS −53 %, gold/DPS 5600 → 12 000), is now floored at 1 net
damage against every armored unit from SWORDMAN (armor 7) upward, **and its slow got
weaker too** (retained speed 30 % → 40 %, only partly offset by 3000 → 3300 ms).
That is a nerf on both axes of an already-underpowered class. COLD_TOWER moves the
same way: −20 % DPS *and* a weaker slow (40 % → 50 % retained). Only SPIKE_TRAP and
SHOCK_TOWER (35 % → 20 % retained, 1500 → 2500 ms — a large buff) go in the direction
the baseline data asked for. Fixing the inverted comments in `structures.yaml` first
would make this class easier to reason about.

### 6.4 Modern era lost one of its two functioning towers
The 18:54 baseline has Modern defender win rate at **12 %**, with the notes
identifying ANTI_AIR and LASER as the only two Modern towers doing meaningful damage.
LASER was then relabelled to `future`. Because the *requirements* did not move it is
still buildable, so this is a UI/pricing problem rather than a removal — but if the
intent was to make it future-only, Modern drops to one working tower and the 12 %
gets worse. Compensating Modern buffs are present (ANTI_AIR +31 %, RADAR +72 % and
range 1.5→2.5, MG +19 %, PARALYZNG +29 %) but the era's critters also got +27 % HP,
+20 % armor and **+20 % spawn rate**.

### 6.5 ROCKET_TOWER walks straight into the documented splash trap
Notes §5: splash has **no falloff and no target cap**, so splash strength scales with
maze clustering and cannot be balanced by a damage number. ROCKET_TOWER was just
converted from single-target to `splash_radius: 0.5` — the largest radius in the
game. Single-target it is now 70 % weaker (fine, 1 M gold buys 12 DPS), but against a
clustered maze it hits every unit in radius for full unreduced damage. This is
exactly the mechanism the notes call "a ticking time bomb". The same applies more
mildly to CANNON 0.3→0.35 and RADAR 0.3→0.4.

### 6.6 Era-level attacker/defender swings look uneven
Comparing tower DPS growth against critter HP+armor growth per era:
- **Attacker-favoured:** bronze (+77 % towers vs +193 % HP / +58 % armor),
  medieval (−2 % vs +26 %), renaissance (+1 % vs +38 % armor / +32 % speed),
  future (+8 % vs +67 % HP / +47 % armor).
- **Defender-favoured:** neolithic (+50 % towers vs +6 % HP).
- **Roughly neutral:** iron, industrial, modern.

Bronze and renaissance stand out. Bronze baseline defender win rate was 77 % so it
has room; renaissance was already at 59 % (25 % hardcoded) and got a pure attacker
buff. Future was at 13 % and got the biggest attacker buff in the file
(MECH_WARRIOR) alongside a net-neutral tower tier.

### 6.7 Smaller items
- **Two dead levels where a ramp drops to 0** — both almost certainly typos:
  - `LUCIEN.e` (Tribute of the Masses) level 3: 0.004 / 0.005 / **0** / 0.007 / 0.01
  - `BORIN.e` (Undying Defiance) level **5**: 24686 / 37029 / 49371 / 61714 / **0**
    — worse than Lucien's, because it is the *max* level: fully levelling the
    skill turns it off. Now visible on the public landing page too, which
    renders each skill's max-level value.
- `BORIN.w` `wave_delay_offset` seconds → milliseconds: confirm the engine's unit.
- 19 critters dropped their building requirements; check whether GRANARY,
  SWORD_MAKER, BOW_MAKER, STABLES, BOOT_CAMP, FENCING_SCHOOL, VEHICLE_WORKSHOP,
  HANGAR, ELITE_ACADEMY, RECRUITING_OFFICE, THE_KINGS_LAIR, SECRET_ORDER, GUNSMITH,
  BARRACKS, FACTORY, PARLIAMENT still have a reason to be built.
- CARGO slots 4 → 3 while gaining HP and armor — strictly better per wave slot.

## 7. Post-change simulation (2026-08-20 20:08)

Run: `python3 scripts/balance_sim.py --era all --n 20 --seed 0`, 854 battles, 29 min →
`data/balancing/20260820_200802/`. Seed 0 was recovered from the baseline's
`battles.csv` (`army_seed` values 0–19), so armies are identical between the runs —
critters-per-battle per era is unchanged, confirming the comparison is clean on that
axis.

### 7.1 Win rates

| Era | Defender win % | Mean life left % | Total-wipe % | Battles |
|---|---:|---:|---:|---:|
| Stone | 95 → 95 | 65 → 66 | 5 → 5 | 138 |
| Neolithic | 60 → **56** | 55 → **43** | 40 → 44 | 48 |
| Bronze | 77 → **52** | 70 → **40** | 23 → **48** | 96 |
| Iron | 57 → **63** | 45 → **52** | 43 → 37 | 125 |
| Medieval | 70 → **61** | 62 → 54 | 30 → 39 | 130 |
| Renaissance | 59 → **28** | 45 → **20** | 41 → **72** | 96 |
| Industrial | 74 → **65** | 61 → 56 | 26 → 35 | 100 |
| Modern | 12 → 15 | 7 → 6 | 88 → 85 | 104 → **52** ⚠ |
| Future | 13 → **0** | 2 → **0** | 87 → **100** | 23 → **69** ⚠ |

⚠ Modern and Future are not directly comparable — see §7.2.

Net: the pass moved the game toward the attacker in six of nine eras. Iron is the
only era that improved.

### 7.2 Measurement artifact: LASER_TOWER's era change reshuffled the maze pool

`maze_loader._classify_era` assigns a maze the **highest era among its placed
towers** — one high-era tower defines the whole maze. Moving LASER_TOWER from
`modern` to `future` therefore reclassified every maze containing one:

- Modern: 4 mazes → 2 (`S2 Gempire` and `Weak Modern` left)
- Future: 1 maze → 3 (the same two arrived)

So Future's 0 % is partly measured on **modern-built mazes now facing future
armies**, which they were never designed for. This is **simulation-only** —
`build_era_maze_pool` is called exclusively by `scripts/balance_sim.py`, nothing in
the live server uses it — so it is not a gameplay bug, but the Modern/Future rows
must be read per-maze.

On the one Future maze present in **both** runs, `S1 Limperium`: **13 % → 0 %**,
mean life 2 % → 0 %. The Future regression is real, not just the reshuffle.

### 7.3 Per-maze, on identical mazes

| Era | Maze | Win % |
|---|---|---:|
| Bronze | Arrow Bronze | 96 → **25** |
| Bronze | Late Bronze | 100 → 83 |
| Medieval | Mixed Early | 35 → **0** |
| Medieval | Early | 31 → 12 |
| Renaissance | Mixed late | 58 → **0** |
| Renaissance | Full Rifle | 75 → 46 |
| Renaissance | Full Heavy Medieval | 71 → 50 |
| Industrial | Flame/Gatling | 96 → **60** |
| Modern | Short Mixed Modern | 0 → **27** ✅ |
| Modern | S2 Wicked$Kingdom | 8 → 4 |
| Iron | S2 Baumhaus | 72 → **88** ✅ |
| Future | S1 Limperium | 13 → **0** |

### 7.4 What is actually breaking through

Critters reaching the castle, total count baseline → new:

| Era | Dominant breaker | Change |
|---|---|---|
| Bronze | **CHARIOT** | 34 → **345** (10×) |
| Medieval | KNIGHT 5 → 27, CRUSADER 153 → 186 | |
| Renaissance | **MUSKETEER** 67 → **305**, **DRAGOONER** 13 → **137** | |
| Industrial | **SOLDIER** | 196 → **695** (3.5×) |
| Future | **DRONE** | 11 → **618**; MECH_WARRIOR 222 → 373 |

Each maps onto a specific edit: CHARIOT HP 5 → 20 (+300 %), MUSKETEER HP +37 %,
DRAGOONER armor 7.5 → 10, SOLDIER HP +70 % **and** the `bulk` → `health`
reclassification, KNIGHT armor 8.5 → 12. The DRONE figure is inflated by the maze
reshuffle (3× the battles) but is still ~18× per battle on speed 1.9 → 2.0 alone —
DRONE costs 0.6 slots, so a speed bump multiplies across a very large spawn count.

Battles also got **shorter** everywhere (Bronze 109 → 95 s, Renaissance 245 → 207 s,
Future 232 → 142 s) with **fewer** critters killed (Future 413 → 210). Defenders are
not grinding down bigger armies — they are being overrun sooner.

### 7.5 What worked

- **Burn-as-anti-armor did what it was supposed to.** FIRE_TOWER's damage per
  placement went 100 → **353** (+253 %), share 14.7 % → 29.0 %, and it **dropped off
  the UP list** in Bronze for the first time. This validates §6.2's mitigation path.
- **ARROW_TOWER is no longer OP.** Share 71.4 % → 56.2 %, off the OP list — the
  range 2 → 1.5 cut did its job.
- **The Modern buffs landed on the era's weakest maze.** `Short Mixed Modern`
  0 % → 27 %, driven by MG_TOWER (share 12.9 % → 29.8 %) and RADAR_TOWER
  (20.6 % → 24.0 %, helped by range 1.5 → 2.5).
- **Iron is the one era that came out better balanced** (57 % → 63 %) — tower gains
  matched critter gains there.

### 7.6 What went wrong, and where problems are expected

1. **Renaissance is the worst regression (59 % → 28 %, 72 % total wipes).** Predicted
   in §6.6: +38 % armor and +32 % speed on critters against +1 % tower DPS. Two of
   four mazes now win 0–17 %. Needs tower compensation, not more critter tuning.
2. **Future is unplayable as configured — 0 % across 69 battles, 100 % wipes.** Even
   discounting the reshuffle, the shared maze went 13 % → 0 %.
3. **Bronze fell off a cliff (77 % → 52 %, wipes 23 % → 48 %)** — and it is a new
   player's first real era. `Arrow Bronze` at 25 % is the clearest signal: CHARIOT
   HP ×4 was too much for a tier whose towers gained 26–30 % DPS.
4. **§6.3 confirmed exactly.** TAR_TOWER damage per placement 2409 → **783** (−68 %),
   share 4.8 % → 1.5 %. COLD_TOWER 173 → **68** (−61 %), share 0.2 % → 0.1 % — now
   the weakest tower in the game. The whole slow class (SPIKE_TRAP, COLD, ICE, SHOCK,
   PARALYZNG) is flagged UP again in **every** era it appears, unchanged from the
   baseline. The double nerf made a known problem worse.
5. **ROCKET_TOWER's splash conversion backfired.** Share 33.4 % → 7.3 %, damage per
   placement 37 613 → 13 976 (−63 %). At 1 000 000 gold it is now the worst value in
   the game. The §6.5 splash time bomb did **not** go off — sim mazes do not cluster
   critters densely enough to exploit no-falloff splash — but the tower lost its
   identity without gaining the upside.
6. **LASER_TOWER did not dominate the damage tables** (11.3 % share in Future,
   10 813 damage/placement vs MG_TOWER's 28 121), so §6.1's *damage-share* worry is
   not borne out. That does not clear §6.1's actual claim, which was about **gold per
   DPS and never hitting the armor floor** — the sim's share metric measures neither,
   and MG_TOWER tops the chart by firing 6× as often at low-armor targets (DRONE
   armor 2, SOLDIER 5). LASER's cost efficiency still needs a separate look.

**Caveat on absolute numbers:** damage-per-placement rose across the board simply
because critters have more HP, while battles got shorter. Only **shares** and
**ratios** are comparable between runs; raw damage totals are not.

### 7.7 Suggested next actions

Highest leverage first; each is a config-only change:

1. Compensate Renaissance and Bronze **towers** rather than reverting critter stats —
   the class specialization is working, those tiers just never got their counter-side
   buff. Renaissance has no burn tower at all (§6.2); adding one, or making
   BOILING_OIL available there, targets the armor problem directly.
2. Roll back the TAR_TOWER and COLD_TOWER nerfs — they contradict the data in both
   runs.
3. Decide what Future is meant to look like; at 0 % it cannot be evaluated. Build a
   real future-era maze in `saved_maps.yaml` so the tier gets a fair test, since two
   of its three mazes are modern builds.
4. Re-examine ROCKET_TOWER's damage now that splash is confirmed not to be exploding
   in the sim.
