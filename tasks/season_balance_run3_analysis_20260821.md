> **Status: active** — comparison of `data/balancing/20260821_112541` (after your
> edits) against `data/balancing/20260820_200802`. Nothing applied.

# Balance Run 3 — 2026-08-21

Run: `scripts/balance_sim.py --era all --n 20 --seed 0`, 854 battles, ~30 min.

## 1. Confound: three change classes landed at once

Besides tower/critter stats you also shrank the armies, so win-rate gains are
**partly unrelated to tower balance**:

- `game.yaml` → `ai_generator`: wave counts cut in every era (Iron 8–11 → 7–9,
  Modern 15–18 → 14–17, Renaissance 14–17 → 12–15, …).
- `ai_waves.yaml`: −128 lines — every hardcoded army lost its last and largest wave.

Measured effect: **critters per battle fell 13–15 %** in every era
(Bronze 63 → 54, Renaissance 251 → 214, Modern 338 → 295, Future 326 → 284).

OP/UP verdicts below therefore use the **relative** metrics (damage-share ÷
placement-share, reach-rate ÷ era-mean), which are normalised inside a single run
and stay valid. Absolute win rates are directional only.

## 2. Win rates

| Era | Win % | Life left % | Critters/battle |
|---|---:|---:|---:|
| Stone | 95 → 95 | 66 → 66 | 14 → 14 |
| Neolithic | 56 → **54** | 43 → 44 | 21 → 19 |
| Bronze | 52 → **66** | 40 → 51 | 63 → 54 |
| Iron | 63 → 64 | 52 → 54 | 109 → 88 |
| Medieval | 61 → 61 | 54 → 55 | 150 → 135 |
| Renaissance | 28 → **65** | 20 → 49 | 251 → 214 |
| Industrial | 65 → **79** | 56 → 73 | 278 → 245 |
| Modern | 15 → **50** | 6 → 23 | 338 → 295 |
| Future | 0 → **14** | 0 → 6 | 326 → 284 |

Every previously broken tier moved up. Renaissance and Modern are the big wins.
Neolithic is the only era that slipped, and Future is still far from playable.

## 3. The dominant remaining problem is wave composition, not stats

`ai_generator` deliberately imports next-era critters via `min_next_era` /
`max_next_era`. The data says those imports now **dominate** their host era:

| Era | Next-era share of castle damage | Top importer (reach rate) | Config |
|---|---:|---|---|
| Stone | **57 %** | WARRIOR (82 %) | max_next_era 1 |
| Neolithic | **52 %** | BOWMAN (49 %) | max_next_era 1 |
| Bronze | 26 % | PIKENEER (34 %) | max_next_era 1 |
| Iron | **61 %** | CONDOTTERI (34 %) | max_next_era 2 |
| Medieval | 15 % | THE_KING (29 %) | max_next_era 2 |
| Renaissance | **77 %** | SOLDIER (34 %) | max_next_era 3 |
| Industrial | 35 % | SPECOPS (22 %) | max_next_era 2 |
| Modern | 23 % | MECH_WARRIOR (**64 %**) | **min** 1 / max 2 |
| Future | 0 % | — | 0 / 0 |

**In every single era the top OP critter is an import from the next era**, and the
era's own roster is inert. This is the cleanest signal in the whole run:

| Era | Its own units' reach rate | The import doing the work |
|---|---|---|
| Renaissance | DRAGOONER 0.3 %, MUSKETEER 0.8 %, NINJA 0.3 %, CARGO 0.0 % | SMALL_TANK 56 %, SOLDIER 34 % |
| Industrial | SMALL_TANK 0.0 %, MOTORBIKE 0.1 % | SPECOPS 22 % |
| Modern | SIEGE_TANK 0.2 %, HELI 0.0 %, DRONE 0.9 % | MECH_WARRIOR **64 %** |

MECH_WARRIOR reaches the castle in **64 %** of Modern battles but only **11 %** of
Future battles — it is six times more effective against the era below it than
against the era it belongs to. `modern.min_next_era: 1` guarantees at least one such
wave in every Modern army.

## 4. OP / UP marking

Thresholds: towers OP ≥ 2.0 / UP ≤ 0.5 (damage-share ÷ placement-share); critters
OP ≥ 2.0 / UP ≤ 0.25 (reach-rate ÷ era-mean).

### Towers — OP

| Era | Tower | Class | Ratio (prev → now) |
|---|---|---|---:|
| Medieval | CANNON_TOWER | splash | 3.44 → **3.38** |
| Renaissance | HEAVY_TOWER | strong | 3.20 → **2.91** |
| Modern | MG_TOWER | fast | 2.98 → **2.81** |
| Future | MG_TOWER | fast | 2.65 → **2.81** |
| Industrial | GATLING_TOWER | fast | 2.49 → **2.42** |
| Renaissance | RIFLE_TOWER | fast | 2.10 → **2.22** |
| Medieval | HEAVY_TOWER | strong | 2.13 → **2.15** |

### Towers — UP **in their own era** (the real problem; earlier-era towers showing UP in later tiers is normal obsolescence)

| Era | Tower | Class | Ratio |
|---|---|---|---:|
| Neolithic | SPIKE_TRAP | slow | 0.26 |
| Medieval | TAR_TOWER | slow | 0.27 |
| Renaissance | ICE_TOWER | slow | 0.23 |
| Industrial | SHOCK_TOWER | slow | 0.24 |
| Modern | PARALYZNG_TOWER | slow | 0.12 |

**Every slow tower in the game is UP in its own era — third run in a row.**
COLD_TOWER is at 0.01 wherever it appears, i.e. it contributes essentially nothing.

### Critters — OP (⚑ = imported from the next era)

| Era | Critter | Ratio | Reach % |
|---|---|---:|---:|
| Industrial | ⚑ SPECOPS | **9.37** | 21.6 |
| Renaissance | ⚑ SMALL_TANK | **7.53** | 56.2 |
| Modern | ⚑ MECH_WARRIOR | **7.33** | 63.5 |
| Medieval | ⚑ THE_KING | **7.16** | 29.4 |
| Renaissance | ⚑ SOLDIER | 4.57 | 34.2 |
| Bronze | ⚑ THE_SWORDMASTER | 4.32 | **100.0** |
| Neolithic | ⚑ CHARIOT | 2.92 | 71.2 |
| Iron | ⚑ KNIGHT | 2.88 | 41.4 |
| Iron | ⚑ CONDOTTERI | 2.37 | 34.1 |
| Modern | THE_GENERAL | 2.31 | 20.0 |
| Future | MECH_WARRIOR | 2.23 | 10.9 |
| Stone | ⚑ WARRIOR | 2.10 | 82.2 |

Ten of twelve are imports. THE_SWORDMASTER (Iron boss) reaching the castle in
**100 %** of Bronze battles is the most extreme case.

### Critters — UP, own era (over-nerfed or outclassed by imports)

| Era | Critter | Class | Ratio (prev → now) | Reach % |
|---|---|---|---:|---:|
| Renaissance | DRAGOONER | tank | 0.49 → **0.04** | 0.3 |
| Renaissance | MUSKETEER | bulk | 0.27 → **0.10** | 0.8 |
| Renaissance | NINJA | fast | 0.03 → 0.04 | 0.3 |
| Renaissance | CARGO | carrier | 0.00 → 0.00 | 0.0 |
| Modern | DRONE | fast | 0.24 → **0.10** | 0.9 |
| Modern | SIEGE_TANK | tank | 0.06 → 0.03 | 0.2 |
| Modern | HELI | fast | 0.05 → **0.00** | 0.0 |
| Industrial | SMALL_TANK | tank | 0.02 → 0.01 | 0.0 |
| Industrial | MOTORBIKE | fast | 0.04 → 0.07 | 0.1 |

DRAGOONER and MUSKETEER were cut just as their era's difficulty was already being
solved by the army-size reduction — they are now irrelevant.

## 5. Per-maze — mazes still stuck at zero

| Era | Maze | Win % |
|---|---|---:|
| Bronze | Weak Bronze | 0 → 0 |
| Medieval | Mixed Early | 0 → 0 |
| Medieval | Early | 12 → **4** ↓ |
| Future | Weak Modern | 0 → 0 |
| Future | S2 Gempire | 0 → 4 |
| Iron | Schafshügel (Bronze) | 4 → 4 |
| Neolithic | Neolith | 21 → 21 |

Big movers: Renaissance `Mixed late` 0 → 71, Modern `Short Mixed Modern` 27 → 77,
Bronze `Arrow Bronze` 25 → 67, Future `S1 Limperium` 0 → 39.
