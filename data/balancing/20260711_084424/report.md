# Balancing Report

Generated: 2026-07-11T08:44:24.155944+00:00

## Maze Coverage

```
Era             Mazes  Source(s)               Towers (min-max)    
-------------------------------------------------------------------
stone               6  saved                   1-3
neolithic           2  saved                   4-10
bronze              4  saved                   6-29
iron                5  saved                   13-33
medieval            5  saved                   18-41
renaissance         3  saved                   32-45
industrial          4  saved                   28-61
modern              4  saved                   33-66
future              1  saved                   58-58
```

## Win Rates

| Era | Battles | Defender Win % | Hardcoded Win % | Random Win % |
|---|---:|---:|---:|---:|
| Stone Age | 138 | 95% | 83% | 97% |
| Neolithic | 48 | 60% | 88% | 55% |
| Bronze Age | 96 | 77% | 75% | 78% |
| Iron Age | 125 | 58% | 48% | 61% |
| Medieval | 130 | 52% | 23% | 61% |
| Renaissance | 72 | 71% | 42% | 77% |
| Industrial | 100 | 97% | 100% | 96% |
| Modern | 104 | 39% | 50% | 36% |
| Future | 23 | 43% | 67% | 40% |

## Battle-by-Battle Overview

🟩 defender won · 🟥 defender lost. Life % uses a 5-step gradient
(🟢 ≥80% · 🟡 ≥50% · 🟠 ≥20% · 🔴 >0% · ⬛ 0%). "Reached" lists the
critter types that made it to the castle (× count), blank if none.
One table per map, with that map's own tower-era distribution.

### Stone Age

#### 1 Basic Tower

| Tower Era Distribution (1 towers) | Towers |
|---|---|
| Stone Age 100% (1) | BASIC_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Stone Age Raid | hardcoded | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×6 |
| 🟩 | Primitive Assault | hardcoded | Stone Age 100% | 🟠 4/10 (40%) | SCOUT×4, CLUBMAN×2 | CLUBMAN×6, SCOUT×10 |
| 🟥 | Clan Attack | hardcoded | Stone Age 100% | ⬛ 0/10 (0%) | CLUBMAN×5, SCOUT×5 | CLUBMAN×6, CLUBMAN×8, SCOUT×8, SCOUT×6, CLUBMAN×14 |
| 🟩 | Disorganized Mob | random | Stone Age 70%, Neolithic 30% | 🟠 2/10 (20%) | SCOUT×4, CART×2 | SLAVE×6, SCOUT×8, CART×6 |
| 🟩 | Disorganized Mob | random | Stone Age 70%, Neolithic 30% | 🟠 2/10 (20%) | SCOUT×4, CART×2 | SLAVE×6, SCOUT×8, CART×6 |
| 🟩 | Savage Rabble | random | Stone Age 100% | 🔴 1/10 (10%) | CLUBMAN×9 | SLAVE×7, CLUBMAN×8, CLUBMAN×6, CLUBMAN×8 |
| 🟩 | Blundering Invaders | random | Stone Age 100% | 🟡 7/10 (70%) | CLUBMAN×3 | CLUBMAN×6, CLUBMAN×4, SLAVE×5, SLAVE×7 |
| 🟩 | Frenzied Pillagers | random | Stone Age 100% | 🟠 2/10 (20%) | SCOUT×7, CLUBMAN×1 | SLAVE×5, SCOUT×7, SCOUT×6, CLUBMAN×4 |
| 🟩 | Petty Bandits | random | Stone Age 100% | 🟠 3/10 (30%) | CLUBMAN×7 | SLAVE×7, CLUBMAN×4, CLUBMAN×6, CLUBMAN×8 |
| 🟩 | Drunken Raiders | random | Stone Age 53%, Neolithic 47% | 🟠 4/10 (40%) | CART×3 | CART×9, SLAVE×4, SLAVE×6 |
| 🟩 | Crude Invaders | random | Neolithic 50%, Stone Age 50% | 🔴 1/10 (10%) | WARRIOR×6, SCOUT×3 | WARRIOR×6, SCOUT×6 |
| 🟩 | Frenzied Pillagers | random | Stone Age 100% | 🟠 4/10 (40%) | CLUBMAN×3, SCOUT×3 | CLUBMAN×8, SCOUT×6 |
| 🟩 | Wandering Pillagers | random | Stone Age 100% | 🟠 4/10 (40%) | SCOUT×6 | SCOUT×7, SCOUT×5 |
| 🟩 | Wandering Pillagers | random | Stone Age 71%, Neolithic 29% | 🟠 2/10 (20%) | WARRIOR×4, SCOUT×3, CLUBMAN×1 | SCOUT×6, CLUBMAN×4, WARRIOR×4 |
| 🟩 | Rampaging Rabble | random | Stone Age 67%, Neolithic 33% | 🟠 2/10 (20%) | CLUBMAN×4, CART×2 | CART×6, CLUBMAN×8, CLUBMAN×4 |
| 🟩 | Crude Invaders | random | Neolithic 58%, Stone Age 42% | 🔴 1/10 (10%) | WARRIOR×7, SCOUT×2 | SCOUT×5, WARRIOR×7 |
| 🟩 | Forgotten Warband | random | Stone Age 100% | 🟢 8/10 (80%) | CLUBMAN×2 | SLAVE×4, SLAVE×4, CLUBMAN×6 |
| 🟥 | Lazy Raiders | random | Stone Age 56%, Neolithic 44% | ⬛ 0/10 (0%) | WARRIOR×7, CLUBMAN×3 | CLUBMAN×6, CLUBMAN×4, WARRIOR×8 |
| 🟩 | Lazy Raiders | random | Stone Age 100% | 🟡 6/10 (60%) | CLUBMAN×4 | CLUBMAN×8, CLUBMAN×4 |
| 🟩 | Rude Barbarians | random | Stone Age 70%, Neolithic 30% | 🟠 3/10 (30%) | CLUBMAN×3, CART×2 | SLAVE×8, CLUBMAN×6, CART×6 |
| 🟩 | Muddy Marauders | random | Stone Age 71%, Neolithic 29% | 🟠 2/10 (20%) | CART×2, CLUBMAN×2, SCOUT×2 | CART×6, CLUBMAN×6, SLAVE×4, SCOUT×5 |
| 🟩 | Frenzied Pillagers | random | Stone Age 72%, Neolithic 28% | 🟠 2/10 (20%) | WARRIOR×5, CLUBMAN×3 | WARRIOR×5, SLAVE×7, CLUBMAN×6 |
| 🟩 | Frenzied Pillagers | random | Stone Age 100% | 🟡 5/10 (50%) | SCOUT×4, SLAVE×1 | SCOUT×8, SLAVE×7 |

#### 1 Basic Tower (len: 3)

| Tower Era Distribution (1 towers) | Towers |
|---|---|
| Stone Age 100% (1) | BASIC_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Stone Age Raid | hardcoded | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×6 |
| 🟩 | Primitive Assault | hardcoded | Stone Age 100% | 🟢 9/10 (90%) | SCOUT×1 | CLUBMAN×6, SCOUT×10 |
| 🟥 | Clan Attack | hardcoded | Stone Age 100% | ⬛ 0/10 (0%) | SCOUT×6, CLUBMAN×4 | CLUBMAN×6, CLUBMAN×8, SCOUT×8, SCOUT×6, CLUBMAN×14 |
| 🟩 | Disorganized Mob | random | Stone Age 70%, Neolithic 30% | 🟡 6/10 (60%) | CART×2 | SLAVE×6, SCOUT×8, CART×6 |
| 🟩 | Disorganized Mob | random | Stone Age 70%, Neolithic 30% | 🟡 6/10 (60%) | CART×2 | SLAVE×6, SCOUT×8, CART×6 |
| 🟩 | Savage Rabble | random | Stone Age 100% | 🟡 6/10 (60%) | CLUBMAN×4 | SLAVE×7, CLUBMAN×8, CLUBMAN×6, CLUBMAN×8 |
| 🟩 | Blundering Invaders | random | Stone Age 100% | 🟢 10/10 (100%) |  | CLUBMAN×6, CLUBMAN×4, SLAVE×5, SLAVE×7 |
| 🟩 | Frenzied Pillagers | random | Stone Age 100% | 🟡 7/10 (70%) | SCOUT×3 | SLAVE×5, SCOUT×7, SCOUT×6, CLUBMAN×4 |
| 🟩 | Petty Bandits | random | Stone Age 100% | 🟢 9/10 (90%) | CLUBMAN×1 | SLAVE×7, CLUBMAN×4, CLUBMAN×6, CLUBMAN×8 |
| 🟩 | Drunken Raiders | random | Stone Age 53%, Neolithic 47% | 🟠 4/10 (40%) | CART×3 | CART×9, SLAVE×4, SLAVE×6 |
| 🟥 | Crude Invaders | random | Neolithic 50%, Stone Age 50% | ⬛ 0/10 (0%) | WARRIOR×6, SCOUT×4 | WARRIOR×6, SCOUT×6 |
| 🟩 | Frenzied Pillagers | random | Stone Age 100% | 🟡 6/10 (60%) | SCOUT×3, CLUBMAN×1 | CLUBMAN×8, SCOUT×6 |
| 🟩 | Wandering Pillagers | random | Stone Age 100% | 🟢 8/10 (80%) | SCOUT×2 | SCOUT×7, SCOUT×5 |
| 🟩 | Wandering Pillagers | random | Stone Age 71%, Neolithic 29% | 🟡 6/10 (60%) | WARRIOR×4 | SCOUT×6, CLUBMAN×4, WARRIOR×4 |
| 🟩 | Rampaging Rabble | random | Stone Age 67%, Neolithic 33% | 🟡 5/10 (50%) | CART×2, CLUBMAN×1 | CART×6, CLUBMAN×8, CLUBMAN×4 |
| 🟩 | Crude Invaders | random | Neolithic 58%, Stone Age 42% | 🟠 3/10 (30%) | WARRIOR×7 | SCOUT×5, WARRIOR×7 |
| 🟩 | Forgotten Warband | random | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×4, SLAVE×4, CLUBMAN×6 |
| 🟩 | Lazy Raiders | random | Stone Age 56%, Neolithic 44% | 🟠 2/10 (20%) | WARRIOR×8 | CLUBMAN×6, CLUBMAN×4, WARRIOR×8 |
| 🟩 | Lazy Raiders | random | Stone Age 100% | 🟢 9/10 (90%) | CLUBMAN×1 | CLUBMAN×8, CLUBMAN×4 |
| 🟩 | Rude Barbarians | random | Stone Age 70%, Neolithic 30% | 🟠 4/10 (40%) | CLUBMAN×2, CART×2 | SLAVE×8, CLUBMAN×6, CART×6 |
| 🟩 | Muddy Marauders | random | Stone Age 71%, Neolithic 29% | 🟡 6/10 (60%) | CART×2 | CART×6, CLUBMAN×6, SLAVE×4, SCOUT×5 |
| 🟩 | Frenzied Pillagers | random | Stone Age 72%, Neolithic 28% | 🟠 3/10 (30%) | WARRIOR×5, CLUBMAN×2 | WARRIOR×5, SLAVE×7, CLUBMAN×6 |
| 🟩 | Frenzied Pillagers | random | Stone Age 100% | 🟢 10/10 (100%) |  | SCOUT×8, SLAVE×7 |

#### 1 Basic Tower (len: 4)

| Tower Era Distribution (1 towers) | Towers |
|---|---|
| Stone Age 100% (1) | BASIC_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Stone Age Raid | hardcoded | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×6 |
| 🟩 | Primitive Assault | hardcoded | Stone Age 100% | 🟢 10/10 (100%) |  | CLUBMAN×6, SCOUT×10 |
| 🟥 | Clan Attack | hardcoded | Stone Age 100% | ⬛ 0/10 (0%) | SCOUT×9, CLUBMAN×1 | CLUBMAN×6, CLUBMAN×8, SCOUT×8, SCOUT×6, CLUBMAN×14 |
| 🟩 | Disorganized Mob | random | Stone Age 70%, Neolithic 30% | 🟠 3/10 (30%) | CLUBMAN×5, CART×1 | SLAVE×6, SCOUT×8, CART×6 |
| 🟩 | Disorganized Mob | random | Stone Age 70%, Neolithic 30% | 🟠 3/10 (30%) | CLUBMAN×5, CART×1 | SLAVE×6, SCOUT×8, CART×6 |
| 🟩 | Savage Rabble | random | Stone Age 100% | 🟢 8/10 (80%) | CLUBMAN×2 | SLAVE×7, CLUBMAN×8, CLUBMAN×6, CLUBMAN×8 |
| 🟩 | Blundering Invaders | random | Stone Age 100% | 🟢 10/10 (100%) |  | CLUBMAN×6, CLUBMAN×4, SLAVE×5, SLAVE×7 |
| 🟩 | Frenzied Pillagers | random | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×5, SCOUT×7, SCOUT×6, CLUBMAN×4 |
| 🟩 | Petty Bandits | random | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×7, CLUBMAN×4, CLUBMAN×6, CLUBMAN×8 |
| 🟩 | Drunken Raiders | random | Stone Age 53%, Neolithic 47% | 🟠 2/10 (20%) | CLUBMAN×4, CART×2 | CART×9, SLAVE×4, SLAVE×6 |
| 🟥 | Crude Invaders | random | Neolithic 50%, Stone Age 50% | ⬛ 0/10 (0%) | WARRIOR×6, SCOUT×4 | WARRIOR×6, SCOUT×6 |
| 🟩 | Frenzied Pillagers | random | Stone Age 100% | 🟡 6/10 (60%) | SCOUT×4 | CLUBMAN×8, SCOUT×6 |
| 🟩 | Wandering Pillagers | random | Stone Age 100% | 🟢 10/10 (100%) |  | SCOUT×7, SCOUT×5 |
| 🟩 | Wandering Pillagers | random | Stone Age 71%, Neolithic 29% | 🟡 6/10 (60%) | WARRIOR×4 | SCOUT×6, CLUBMAN×4, WARRIOR×4 |
| 🟩 | Rampaging Rabble | random | Stone Age 67%, Neolithic 33% | 🟠 2/10 (20%) | CLUBMAN×6, CART×1 | CART×6, CLUBMAN×8, CLUBMAN×4 |
| 🟩 | Crude Invaders | random | Neolithic 58%, Stone Age 42% | 🟠 3/10 (30%) | WARRIOR×7 | SCOUT×5, WARRIOR×7 |
| 🟩 | Forgotten Warband | random | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×4, SLAVE×4, CLUBMAN×6 |
| 🟩 | Lazy Raiders | random | Stone Age 56%, Neolithic 44% | 🟠 2/10 (20%) | WARRIOR×8 | CLUBMAN×6, CLUBMAN×4, WARRIOR×8 |
| 🟩 | Lazy Raiders | random | Stone Age 100% | 🟢 10/10 (100%) |  | CLUBMAN×8, CLUBMAN×4 |
| 🟩 | Rude Barbarians | random | Stone Age 70%, Neolithic 30% | 🟠 3/10 (30%) | CLUBMAN×5, CART×1 | SLAVE×8, CLUBMAN×6, CART×6 |
| 🟩 | Muddy Marauders | random | Stone Age 71%, Neolithic 29% | 🟠 3/10 (30%) | CLUBMAN×5, CART×1 | CART×6, CLUBMAN×6, SLAVE×4, SCOUT×5 |
| 🟩 | Frenzied Pillagers | random | Stone Age 72%, Neolithic 28% | 🟠 3/10 (30%) | WARRIOR×5, CLUBMAN×2 | WARRIOR×5, SLAVE×7, CLUBMAN×6 |
| 🟩 | Frenzied Pillagers | random | Stone Age 100% | 🟢 10/10 (100%) |  | SCOUT×8, SLAVE×7 |

#### 2 Basic Tower (len: 4)

| Tower Era Distribution (2 towers) | Towers |
|---|---|
| Stone Age 100% (2) | BASIC_TOWER×2 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Stone Age Raid | hardcoded | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×6 |
| 🟩 | Primitive Assault | hardcoded | Stone Age 100% | 🟢 10/10 (100%) |  | CLUBMAN×6, SCOUT×10 |
| 🟩 | Clan Attack | hardcoded | Stone Age 100% | 🟢 9/10 (90%) | SCOUT×1 | CLUBMAN×6, CLUBMAN×8, SCOUT×8, SCOUT×6, CLUBMAN×14 |
| 🟩 | Disorganized Mob | random | Stone Age 70%, Neolithic 30% | 🟡 5/10 (50%) | CLUBMAN×3, CART×1 | SLAVE×6, SCOUT×8, CART×6 |
| 🟩 | Disorganized Mob | random | Stone Age 70%, Neolithic 30% | 🟡 5/10 (50%) | CLUBMAN×3, CART×1 | SLAVE×6, SCOUT×8, CART×6 |
| 🟩 | Savage Rabble | random | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×7, CLUBMAN×8, CLUBMAN×6, CLUBMAN×8 |
| 🟩 | Blundering Invaders | random | Stone Age 100% | 🟢 10/10 (100%) |  | CLUBMAN×6, CLUBMAN×4, SLAVE×5, SLAVE×7 |
| 🟩 | Frenzied Pillagers | random | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×5, SCOUT×7, SCOUT×6, CLUBMAN×4 |
| 🟩 | Petty Bandits | random | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×7, CLUBMAN×4, CLUBMAN×6, CLUBMAN×8 |
| 🟩 | Drunken Raiders | random | Stone Age 53%, Neolithic 47% | 🟠 4/10 (40%) | CART×2, CLUBMAN×2 | CART×9, SLAVE×4, SLAVE×6 |
| 🟩 | Crude Invaders | random | Neolithic 50%, Stone Age 50% | 🟠 3/10 (30%) | WARRIOR×5, SCOUT×2 | WARRIOR×6, SCOUT×6 |
| 🟩 | Frenzied Pillagers | random | Stone Age 100% | 🟢 10/10 (100%) |  | CLUBMAN×8, SCOUT×6 |
| 🟩 | Wandering Pillagers | random | Stone Age 100% | 🟢 10/10 (100%) |  | SCOUT×7, SCOUT×5 |
| 🟩 | Wandering Pillagers | random | Stone Age 71%, Neolithic 29% | 🟡 7/10 (70%) | WARRIOR×3 | SCOUT×6, CLUBMAN×4, WARRIOR×4 |
| 🟩 | Rampaging Rabble | random | Stone Age 67%, Neolithic 33% | 🟡 6/10 (60%) | CLUBMAN×2, CART×1 | CART×6, CLUBMAN×8, CLUBMAN×4 |
| 🟩 | Crude Invaders | random | Neolithic 58%, Stone Age 42% | 🟠 4/10 (40%) | WARRIOR×6 | SCOUT×5, WARRIOR×7 |
| 🟩 | Forgotten Warband | random | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×4, SLAVE×4, CLUBMAN×6 |
| 🟩 | Lazy Raiders | random | Stone Age 56%, Neolithic 44% | 🟠 3/10 (30%) | WARRIOR×7 | CLUBMAN×6, CLUBMAN×4, WARRIOR×8 |
| 🟩 | Lazy Raiders | random | Stone Age 100% | 🟢 10/10 (100%) |  | CLUBMAN×8, CLUBMAN×4 |
| 🟩 | Rude Barbarians | random | Stone Age 70%, Neolithic 30% | 🟡 6/10 (60%) | CLUBMAN×2, CART×1 | SLAVE×8, CLUBMAN×6, CART×6 |
| 🟩 | Muddy Marauders | random | Stone Age 71%, Neolithic 29% | 🟡 6/10 (60%) | CLUBMAN×2, CART×1 | CART×6, CLUBMAN×6, SLAVE×4, SCOUT×5 |
| 🟩 | Frenzied Pillagers | random | Stone Age 72%, Neolithic 28% | 🟡 6/10 (60%) | WARRIOR×4 | WARRIOR×5, SLAVE×7, CLUBMAN×6 |
| 🟩 | Frenzied Pillagers | random | Stone Age 100% | 🟢 10/10 (100%) |  | SCOUT×8, SLAVE×7 |

#### two towers (len: 1)

| Tower Era Distribution (2 towers) | Towers |
|---|---|
| Stone Age 100% (2) | SLING_TOWER×1, BASIC_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Stone Age Raid | hardcoded | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×6 |
| 🟩 | Primitive Assault | hardcoded | Stone Age 100% | 🟢 10/10 (100%) |  | CLUBMAN×6, SCOUT×10 |
| 🟩 | Clan Attack | hardcoded | Stone Age 100% | 🟢 10/10 (100%) |  | CLUBMAN×6, CLUBMAN×8, SCOUT×8, SCOUT×6, CLUBMAN×14 |
| 🟩 | Disorganized Mob | random | Stone Age 70%, Neolithic 30% | 🟠 3/10 (30%) | CLUBMAN×5, CART×1 | SLAVE×6, SCOUT×8, CART×6 |
| 🟩 | Disorganized Mob | random | Stone Age 70%, Neolithic 30% | 🟠 3/10 (30%) | CLUBMAN×5, CART×1 | SLAVE×6, SCOUT×8, CART×6 |
| 🟩 | Savage Rabble | random | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×7, CLUBMAN×8, CLUBMAN×6, CLUBMAN×8 |
| 🟩 | Blundering Invaders | random | Stone Age 100% | 🟢 10/10 (100%) |  | CLUBMAN×6, CLUBMAN×4, SLAVE×5, SLAVE×7 |
| 🟩 | Frenzied Pillagers | random | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×5, SCOUT×7, SCOUT×6, CLUBMAN×4 |
| 🟩 | Petty Bandits | random | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×7, CLUBMAN×4, CLUBMAN×6, CLUBMAN×8 |
| 🟥 | Drunken Raiders | random | Stone Age 53%, Neolithic 47% | ⬛ 0/10 (0%) | CLUBMAN×8, CART×1 | CART×9, SLAVE×4, SLAVE×6 |
| 🟩 | Crude Invaders | random | Neolithic 50%, Stone Age 50% | 🟠 4/10 (40%) | WARRIOR×6 | WARRIOR×6, SCOUT×6 |
| 🟩 | Frenzied Pillagers | random | Stone Age 100% | 🟢 10/10 (100%) |  | CLUBMAN×8, SCOUT×6 |
| 🟩 | Wandering Pillagers | random | Stone Age 100% | 🟢 10/10 (100%) |  | SCOUT×7, SCOUT×5 |
| 🟩 | Wandering Pillagers | random | Stone Age 71%, Neolithic 29% | 🟡 6/10 (60%) | WARRIOR×4 | SCOUT×6, CLUBMAN×4, WARRIOR×4 |
| 🟩 | Rampaging Rabble | random | Stone Age 67%, Neolithic 33% | 🟠 4/10 (40%) | CLUBMAN×4, CART×1 | CART×6, CLUBMAN×8, CLUBMAN×4 |
| 🟩 | Crude Invaders | random | Neolithic 58%, Stone Age 42% | 🟠 3/10 (30%) | WARRIOR×7 | SCOUT×5, WARRIOR×7 |
| 🟩 | Forgotten Warband | random | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×4, SLAVE×4, CLUBMAN×6 |
| 🟩 | Lazy Raiders | random | Stone Age 56%, Neolithic 44% | 🟠 2/10 (20%) | WARRIOR×8 | CLUBMAN×6, CLUBMAN×4, WARRIOR×8 |
| 🟩 | Lazy Raiders | random | Stone Age 100% | 🟢 10/10 (100%) |  | CLUBMAN×8, CLUBMAN×4 |
| 🟩 | Rude Barbarians | random | Stone Age 70%, Neolithic 30% | 🔴 1/10 (10%) | CLUBMAN×7, CART×1 | SLAVE×8, CLUBMAN×6, CART×6 |
| 🟩 | Muddy Marauders | random | Stone Age 71%, Neolithic 29% | 🟠 4/10 (40%) | CLUBMAN×4, CART×1 | CART×6, CLUBMAN×6, SLAVE×4, SCOUT×5 |
| 🟩 | Frenzied Pillagers | random | Stone Age 72%, Neolithic 28% | 🟡 5/10 (50%) | WARRIOR×5 | WARRIOR×5, SLAVE×7, CLUBMAN×6 |
| 🟩 | Frenzied Pillagers | random | Stone Age 100% | 🟢 10/10 (100%) |  | SCOUT×8, SLAVE×7 |

#### 3 Towers (len: 6)

| Tower Era Distribution (3 towers) | Towers |
|---|---|
| Stone Age 100% (3) | SLING_TOWER×3 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Stone Age Raid | hardcoded | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×6 |
| 🟩 | Primitive Assault | hardcoded | Stone Age 100% | 🟢 10/10 (100%) |  | CLUBMAN×6, SCOUT×10 |
| 🟩 | Clan Attack | hardcoded | Stone Age 100% | 🟢 10/10 (100%) |  | CLUBMAN×6, CLUBMAN×8, SCOUT×8, SCOUT×6, CLUBMAN×14 |
| 🟩 | Disorganized Mob | random | Stone Age 70%, Neolithic 30% | 🟢 10/10 (100%) |  | SLAVE×6, SCOUT×8, CART×6 |
| 🟩 | Disorganized Mob | random | Stone Age 70%, Neolithic 30% | 🟢 10/10 (100%) |  | SLAVE×6, SCOUT×8, CART×6 |
| 🟩 | Savage Rabble | random | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×7, CLUBMAN×8, CLUBMAN×6, CLUBMAN×8 |
| 🟩 | Blundering Invaders | random | Stone Age 100% | 🟢 10/10 (100%) |  | CLUBMAN×6, CLUBMAN×4, SLAVE×5, SLAVE×7 |
| 🟩 | Frenzied Pillagers | random | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×5, SCOUT×7, SCOUT×6, CLUBMAN×4 |
| 🟩 | Petty Bandits | random | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×7, CLUBMAN×4, CLUBMAN×6, CLUBMAN×8 |
| 🟩 | Drunken Raiders | random | Stone Age 53%, Neolithic 47% | 🟠 4/10 (40%) | CLUBMAN×6 | CART×9, SLAVE×4, SLAVE×6 |
| 🟩 | Crude Invaders | random | Neolithic 50%, Stone Age 50% | 🟡 7/10 (70%) | WARRIOR×3 | WARRIOR×6, SCOUT×6 |
| 🟩 | Frenzied Pillagers | random | Stone Age 100% | 🟢 10/10 (100%) |  | CLUBMAN×8, SCOUT×6 |
| 🟩 | Wandering Pillagers | random | Stone Age 100% | 🟢 10/10 (100%) |  | SCOUT×7, SCOUT×5 |
| 🟩 | Wandering Pillagers | random | Stone Age 71%, Neolithic 29% | 🟢 10/10 (100%) |  | SCOUT×6, CLUBMAN×4, WARRIOR×4 |
| 🟩 | Rampaging Rabble | random | Stone Age 67%, Neolithic 33% | 🟢 10/10 (100%) |  | CART×6, CLUBMAN×8, CLUBMAN×4 |
| 🟩 | Crude Invaders | random | Neolithic 58%, Stone Age 42% | 🟡 7/10 (70%) | WARRIOR×3 | SCOUT×5, WARRIOR×7 |
| 🟩 | Forgotten Warband | random | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×4, SLAVE×4, CLUBMAN×6 |
| 🟩 | Lazy Raiders | random | Stone Age 56%, Neolithic 44% | 🟡 6/10 (60%) | WARRIOR×4 | CLUBMAN×6, CLUBMAN×4, WARRIOR×8 |
| 🟩 | Lazy Raiders | random | Stone Age 100% | 🟢 10/10 (100%) |  | CLUBMAN×8, CLUBMAN×4 |
| 🟩 | Rude Barbarians | random | Stone Age 70%, Neolithic 30% | 🟢 10/10 (100%) |  | SLAVE×8, CLUBMAN×6, CART×6 |
| 🟩 | Muddy Marauders | random | Stone Age 71%, Neolithic 29% | 🟢 10/10 (100%) |  | CART×6, CLUBMAN×6, SLAVE×4, SCOUT×5 |
| 🟩 | Frenzied Pillagers | random | Stone Age 72%, Neolithic 28% | 🟢 9/10 (90%) | WARRIOR×1 | WARRIOR×5, SLAVE×7, CLUBMAN×6 |
| 🟩 | Frenzied Pillagers | random | Stone Age 100% | 🟢 10/10 (100%) |  | SCOUT×8, SLAVE×7 |

### Neolithic

#### Neolith

| Tower Era Distribution (4 towers) | Towers |
|---|---|
| Stone Age 75% (3), Neolithic 25% (1) | BASIC_TOWER×3, DOUBLE_SLING_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Neolithic Horde | hardcoded | Neolithic 100% | 🟠 2/10 (20%) | WARRIOR×4, CLUBMAN×2, CART×1 | CART×6, WARRIOR×4, WARRIOR×6, CART×6 |
| 🟩 | Tribal Warband | hardcoded | Neolithic 100% | 🟡 6/10 (60%) | WARRIOR×4 | CART×3, WARRIOR×2, CART×5, WARRIOR×6, WARRIOR×5 |
| 🟩 | Harvest Raiders | hardcoded | Neolithic 95%, Bronze Age 5% | 🟢 10/10 (100%) |  | CART×5, WARRIOR×4, CART×5, BOWMAN×1, WARRIOR×6 |
| 🟥 | Pottery Thieves | hardcoded | Neolithic 100% | ⬛ 0/10 (0%) | WARRIOR×10 | WARRIOR×8, WARRIOR×8, CART×9, WARRIOR×12, WARRIOR×8 |
| 🟥 | Rowdy Plunderers | random | Neolithic 77%, Bronze Age 23% | ⬛ 0/10 (0%) | CHARIOT×5, CLUBMAN×3, CART×1 | CHARIOT×7, CART×6, CART×9, WARRIOR×8 |
| 🟥 | Rowdy Plunderers | random | Neolithic 77%, Bronze Age 23% | ⬛ 0/10 (0%) | CHARIOT×5, CLUBMAN×3, CART×1 | CHARIOT×7, CART×6, CART×9, WARRIOR×8 |
| 🟥 | Drunken Raiders | random | Neolithic 100% | ⬛ 0/10 (0%) | WARRIOR×3, CLUBMAN×3, CART×2 | WARRIOR×9, CART×6, CART×9, WARRIOR×9, WARRIOR×7 |
| 🟥 | Shrieking Horde | random | Neolithic 100% | ⬛ 0/10 (0%) | WARRIOR×10 | WARRIOR×7, WARRIOR×9, WARRIOR×9, CART×6, WARRIOR×6 |
| 🟥 | Disorganized Mob | random | Neolithic 100% | ⬛ 0/10 (0%) | CLUBMAN×5, WARRIOR×3, CART×1 | CART×6, WARRIOR×6, CART×9, CART×9, WARRIOR×9 |
| 🟥 | Clumsy Attackers | random | Neolithic 81%, Stone Age 19% | ⬛ 0/10 (0%) | WARRIOR×6, SCOUT×4 | WARRIOR×10, WARRIOR×9, SCOUT×8, CART×9, CART×6 |
| 🟥 | Petty Bandits | random | Neolithic 69%, Bronze Age 31% | ⬛ 0/10 (0%) | BOWMAN×5 | BOWMAN×10, CART×9, WARRIOR×8, WARRIOR×5 |
| 🟥 | Grumpy Marauders | random | Neolithic 67%, Bronze Age 33% | ⬛ 0/10 (0%) | BOWMAN×5, WARRIOR×1 | WARRIOR×7, CART×9, BOWMAN×8 |
| 🟩 | Angry Mob | random | Neolithic 69%, Stone Age 31% | 🔴 1/10 (10%) | WARRIOR×3, CART×2, CLUBMAN×2 | SLAVE×8, WARRIOR×9, CART×9 |
| 🟩 | Savage Rabble | random | Neolithic 71%, Stone Age 29% | 🟢 9/10 (90%) | CLUBMAN×1 | CART×9, SCOUT×6, CART×6 |
| 🟥 | Petty Bandits | random | Neolithic 44%, Bronze Age 37%, Stone Age 19% | ⬛ 0/10 (0%) | CHARIOT×8, CLUBMAN×2 | SLAVE×5, CHARIOT×10, WARRIOR×6, CART×6 |
| 🟥 | Shrieking Horde | random | Neolithic 48%, Stone Age 26%, Bronze Age 26% | ⬛ 0/10 (0%) | CLUBMAN×4, SWORDMAN×3 | CART×9, CLUBMAN×8, CART×6, SWORDMAN×8 |
| 🟥 | Unlucky Raiders | random | Neolithic 64%, Bronze Age 36% | ⬛ 0/10 (0%) | CLUBMAN×3, WARRIOR×2, SWORDMAN×2, CART×1 | WARRIOR×8, CART×6, SWORDMAN×8 |
| 🟥 | Crude Invaders | random | Neolithic 100% | ⬛ 0/10 (0%) | WARRIOR×10 | WARRIOR×5, WARRIOR×8, WARRIOR×5, CART×9 |
| 🟥 | Grumpy Marauders | random | Neolithic 77%, Bronze Age 23% | ⬛ 0/10 (0%) | CHARIOT×6, WARRIOR×4 | WARRIOR×8, CHARIOT×7, WARRIOR×10, WARRIOR×6 |
| 🟥 | Ragged Warband | random | Neolithic 100% | ⬛ 0/10 (0%) | CLUBMAN×5, WARRIOR×3, CART×1 | WARRIOR×5, WARRIOR×6, CART×9 |
| 🟥 | Savage Rabble | random | Neolithic 77%, Bronze Age 23% | ⬛ 0/10 (0%) | CHARIOT×7, WARRIOR×3 | WARRIOR×10, CART×6, CHARIOT×7, WARRIOR×7 |
| 🟥 | Disorganized Mob | random | Neolithic 81%, Bronze Age 19% | ⬛ 0/10 (0%) | BOWMAN×5 | CART×6, BOWMAN×6, CART×9, CART×6, WARRIOR×5 |
| 🟥 | Muddy Marauders | random | Neolithic 60%, Bronze Age 20%, Stone Age 20% | ⬛ 0/10 (0%) | CLUBMAN×2, SWORDMAN×2, WARRIOR×2, CART×1 | CART×9, SWORDMAN×6, WARRIOR×9, SLAVE×6 |
| 🟥 | Disorganized Mob | random | Neolithic 100% | ⬛ 0/10 (0%) | CLUBMAN×6, WARRIOR×2, CART×1 | WARRIOR×8, CART×9, CART×9 |

#### Imperium Aperol 🍹 (pure neo)

| Tower Era Distribution (10 towers) | Towers |
|---|---|
| Neolithic 100% (10) | DOUBLE_SLING_TOWER×9, SPIKE_TRAP×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Neolithic Horde | hardcoded | Neolithic 100% | 🟢 10/10 (100%) |  | CART×6, WARRIOR×4, WARRIOR×6, CART×6 |
| 🟩 | Tribal Warband | hardcoded | Neolithic 100% | 🟢 10/10 (100%) |  | CART×3, WARRIOR×2, CART×5, WARRIOR×6, WARRIOR×5 |
| 🟩 | Harvest Raiders | hardcoded | Neolithic 95%, Bronze Age 5% | 🟢 10/10 (100%) |  | CART×5, WARRIOR×4, CART×5, BOWMAN×1, WARRIOR×6 |
| 🟩 | Pottery Thieves | hardcoded | Neolithic 100% | 🟢 10/10 (100%) |  | WARRIOR×8, WARRIOR×8, CART×9, WARRIOR×12, WARRIOR×8 |
| 🟩 | Rowdy Plunderers | random | Neolithic 77%, Bronze Age 23% | 🟢 10/10 (100%) |  | CHARIOT×7, CART×6, CART×9, WARRIOR×8 |
| 🟩 | Rowdy Plunderers | random | Neolithic 77%, Bronze Age 23% | 🟢 10/10 (100%) |  | CHARIOT×7, CART×6, CART×9, WARRIOR×8 |
| 🟩 | Drunken Raiders | random | Neolithic 100% | 🟢 10/10 (100%) |  | WARRIOR×9, CART×6, CART×9, WARRIOR×9, WARRIOR×7 |
| 🟩 | Shrieking Horde | random | Neolithic 100% | 🟢 10/10 (100%) |  | WARRIOR×7, WARRIOR×9, WARRIOR×9, CART×6, WARRIOR×6 |
| 🟩 | Disorganized Mob | random | Neolithic 100% | 🟢 10/10 (100%) |  | CART×6, WARRIOR×6, CART×9, CART×9, WARRIOR×9 |
| 🟩 | Clumsy Attackers | random | Neolithic 81%, Stone Age 19% | 🟢 10/10 (100%) |  | WARRIOR×10, WARRIOR×9, SCOUT×8, CART×9, CART×6 |
| 🟩 | Petty Bandits | random | Neolithic 69%, Bronze Age 31% | 🟡 6/10 (60%) | BOWMAN×2 | BOWMAN×10, CART×9, WARRIOR×8, WARRIOR×5 |
| 🟩 | Grumpy Marauders | random | Neolithic 67%, Bronze Age 33% | 🟠 2/10 (20%) | BOWMAN×4 | WARRIOR×7, CART×9, BOWMAN×8 |
| 🟩 | Angry Mob | random | Neolithic 69%, Stone Age 31% | 🟢 10/10 (100%) |  | SLAVE×8, WARRIOR×9, CART×9 |
| 🟩 | Savage Rabble | random | Neolithic 71%, Stone Age 29% | 🟢 10/10 (100%) |  | CART×9, SCOUT×6, CART×6 |
| 🟩 | Petty Bandits | random | Neolithic 44%, Bronze Age 37%, Stone Age 19% | 🟢 10/10 (100%) |  | SLAVE×5, CHARIOT×10, WARRIOR×6, CART×6 |
| 🟩 | Shrieking Horde | random | Neolithic 48%, Stone Age 26%, Bronze Age 26% | 🟢 10/10 (100%) |  | CART×9, CLUBMAN×8, CART×6, SWORDMAN×8 |
| 🟩 | Unlucky Raiders | random | Neolithic 64%, Bronze Age 36% | 🟢 10/10 (100%) |  | WARRIOR×8, CART×6, SWORDMAN×8 |
| 🟩 | Crude Invaders | random | Neolithic 100% | 🟢 10/10 (100%) |  | WARRIOR×5, WARRIOR×8, WARRIOR×5, CART×9 |
| 🟩 | Grumpy Marauders | random | Neolithic 77%, Bronze Age 23% | 🟢 10/10 (100%) |  | WARRIOR×8, CHARIOT×7, WARRIOR×10, WARRIOR×6 |
| 🟩 | Ragged Warband | random | Neolithic 100% | 🟢 10/10 (100%) |  | WARRIOR×5, WARRIOR×6, CART×9 |
| 🟩 | Savage Rabble | random | Neolithic 77%, Bronze Age 23% | 🟢 10/10 (100%) |  | WARRIOR×10, CART×6, CHARIOT×7, WARRIOR×7 |
| 🟩 | Disorganized Mob | random | Neolithic 81%, Bronze Age 19% | 🟢 10/10 (100%) |  | CART×6, BOWMAN×6, CART×9, CART×6, WARRIOR×5 |
| 🟩 | Muddy Marauders | random | Neolithic 60%, Bronze Age 20%, Stone Age 20% | 🟢 10/10 (100%) |  | CART×9, SWORDMAN×6, WARRIOR×9, SLAVE×6 |
| 🟩 | Disorganized Mob | random | Neolithic 100% | 🟢 10/10 (100%) |  | WARRIOR×8, CART×9, CART×9 |

### Bronze Age

#### Arrow Bronze (len: 8)

| Tower Era Distribution (10 towers) | Towers |
|---|---|
| Bronze Age 100% (10) | ARROW_TOWER×7, FIRE_TOWER×3 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Bronze Warriors | hardcoded | Bronze Age 97%, Iron Age 3% | 🟢 13/13 (100%) |  | BOWMAN×6, BOWMAN×8, SWORDMAN×10, PIKENEER×2, SWORDMAN×10, CHARIOT×12, SWORDMAN×14 |
| 🟩 | Chariot Rush | hardcoded | Bronze Age 100% | 🟢 13/13 (100%) |  | BOWMAN×12, SWORDMAN×12, SWORDMAN×12, BOWMAN×13, SWORDMAN×9, BOWMAN×12, SWORDMAN×14, SWORDMAN×16 |
| 🟩 | Copper Blades | hardcoded | Bronze Age 100% | 🟢 13/13 (100%) |  | SWORDMAN×11, CHARIOT×12, CHARIOT×13, CHARIOT×14, SWORDMAN×14, CHARIOT×12, BOWMAN×14, CHARIOT×16 |
| 🟥 | Harbor Raiders | hardcoded | Bronze Age 100% | ⬛ 0/13 (0%) | BOWMAN×6, CHARIOT×1 | BOWMAN×13, BOWMAN×14, BOWMAN×14, CHARIOT×15, SWORDMAN×15, BOWMAN×16, BOWMAN×14, BOWMAN×16, SWORDMAN×18 |
| 🟩 | Clumsy Attackers | random | Bronze Age 76%, Neolithic 13%, Iron Age 11% | 🟡 8/13 (62%) | PIKENEER×5 | SWORDMAN×8, PIKENEER×9, CHARIOT×10, SWORDMAN×8, CHARIOT×13, BOWMAN×11, CHARIOT×10, WARRIOR×10 |
| 🟩 | Clumsy Attackers | random | Bronze Age 76%, Neolithic 13%, Iron Age 11% | 🟡 8/13 (62%) | PIKENEER×5 | SWORDMAN×8, PIKENEER×9, CHARIOT×10, SWORDMAN×8, CHARIOT×13, BOWMAN×11, CHARIOT×10, WARRIOR×10 |
| 🟩 | Petty Bandits | random | Bronze Age 86%, Neolithic 14% | 🟠 6/13 (46%) | CHARIOT×5, BOWMAN×1 | SWORDMAN×12, SWORDMAN×10, BOWMAN×12, BOWMAN×10, CHARIOT×10, WARRIOR×13, BOWMAN×11, SWORDMAN×12 |
| 🟩 | Noisy Barbarians | random | Bronze Age 89%, Neolithic 11% | 🟢 13/13 (100%) |  | SWORDMAN×10, CHARIOT×9, CART×9, BOWMAN×12, BOWMAN×9, BOWMAN×11, SWORDMAN×8, SWORDMAN×12 |
| 🟩 | Rude Barbarians | random | Bronze Age 87%, Neolithic 13% | 🟢 13/13 (100%) |  | CART×12, BOWMAN×8, CHARIOT×10, SWORDMAN×12, CHARIOT×12, SWORDMAN×8, CHARIOT×10, CHARIOT×11, SWORDMAN×12 |
| 🟩 | Disorganized Mob | random | Bronze Age 73%, Neolithic 27% | 🟢 13/13 (100%) |  | WARRIOR×12, SWORDMAN×12, CHARIOT×11, WARRIOR×12, BOWMAN×12, SWORDMAN×8, SWORDMAN×12, BOWMAN×10 |
| 🟩 | Shrieking Horde | random | Bronze Age 74%, Neolithic 15%, Iron Age 11% | 🟠 3/13 (23%) | HORSEMAN_FAST×8, BOWMAN×1 | BOWMAN×10, SWORDMAN×8, CHARIOT×13, BOWMAN×13, HORSEMAN_FAST×9, BOWMAN×10, CART×12, BOWMAN×7 |
| 🟩 | Rowdy Plunderers | random | Bronze Age 66%, Neolithic 20%, Iron Age 14% | 🟡 9/13 (69%) | LEGIONARY×4 | CHARIOT×9, WARRIOR×12, CHARIOT×10, LEGIONARY×8, SWORDMAN×10, BOWMAN×10 |
| 🟩 | Crude Invaders | random | Bronze Age 70%, Neolithic 30% | 🟢 13/13 (100%) |  | SWORDMAN×12, BOWMAN×10, WARRIOR×10, CHARIOT×11, BOWMAN×10, WARRIOR×8 |
| 🟩 | Rampaging Rabble | random | Bronze Age 69%, Neolithic 31% | 🟢 13/13 (100%) |  | CHARIOT×11, CHARIOT×8, CART×9, CHARIOT×9, SWORDMAN×12, CART×9 |
| 🟩 | Drunken Raiders | random | Bronze Age 60%, Neolithic 24%, Iron Age 15% | 🟡 9/13 (69%) | PIKENEER×4 | CHARIOT×13, WARRIOR×10, CHARIOT×10, LARGE_CART×12, CART×9, BOWMAN×9, BOWMAN×7, SWORDMAN×8 |
| 🟩 | Howling Savages | random | Bronze Age 63%, Neolithic 25%, Iron Age 11% | 🟠 5/13 (38%) | HORSEMAN_SLOW×4 | CART×12, HORSEMAN_SLOW×9, SWORDMAN×8, WARRIOR×8, SWORDMAN×10, SWORDMAN×12, CHARIOT×10, SWORDMAN×10 |
| 🟩 | Bored Mercenaries | random | Bronze Age 67%, Neolithic 18%, Iron Age 15% | 🟠 5/13 (38%) | LEGIONARY×8 | CHARIOT×7, CHARIOT×8, SWORDMAN×10, CHARIOT×9, BOWMAN×11, LEGIONARY×10, CART×12 |
| 🟩 | Angry Mob | random | Bronze Age 88%, Neolithic 12% | 🟢 13/13 (100%) |  | CHARIOT×9, CART×9, SWORDMAN×10, BOWMAN×7, BOWMAN×8, SWORDMAN×10, CHARIOT×11, BOWMAN×10 |
| 🟩 | Noisy Barbarians | random | Bronze Age 75%, Iron Age 14%, Neolithic 11% | 🟡 8/13 (62%) | HORSEMAN_FAST×5 | BOWMAN×12, WARRIOR×8, BOWMAN×13, SWORDMAN×12, CHARIOT×9, SWORDMAN×8, HORSEMAN_FAST×10 |
| 🟩 | Restless Horde | random | Bronze Age 83%, Neolithic 17% | 🟢 13/13 (100%) |  | BOWMAN×7, CART×9, BOWMAN×7, SWORDMAN×10, SWORDMAN×8, SWORDMAN×12 |
| 🟩 | Howling Savages | random | Bronze Age 74%, Iron Age 15%, Neolithic 11% | 🟠 6/13 (46%) | HORSEMAN_FAST×7 | SWORDMAN×10, SWORDMAN×8, SWORDMAN×10, CART×9, CHARIOT×10, HORSEMAN_FAST×12, BOWMAN×9, BOWMAN×13 |
| 🟩 | Weary Plunderers | random | Bronze Age 74%, Iron Age 14%, Neolithic 12% | 🟡 7/13 (54%) | HORSEMAN_FAST×6 | HORSEMAN_FAST×11, BOWMAN×8, BOWMAN×8, CHARIOT×9, SWORDMAN×8, CART×9, CHARIOT×12, BOWMAN×11 |
| 🟩 | Weary Plunderers | random | Bronze Age 56%, Neolithic 27%, Iron Age 17% | 🟠 4/13 (31%) | PIKENEER×9 | SWORDMAN×12, SWORDMAN×10, PIKENEER×13, BOWMAN×12, BOWMAN×8, WARRIOR×11, CART×9 |
| 🟩 | Disorganized Mob | random | Bronze Age 84%, Neolithic 16% | 🟢 13/13 (100%) |  | SWORDMAN×10, BOWMAN×11, CHARIOT×8, SWORDMAN×10, WARRIOR×10, CHARIOT×13 |

#### Late Bronze

| Tower Era Distribution (14 towers) | Towers |
|---|---|
| Bronze Age 86% (12), Neolithic 14% (2) | ARROW_TOWER×5, BALLISTA_TOWER×4, FIRE_TOWER×3, SPIKE_TRAP×2 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Bronze Warriors | hardcoded | Bronze Age 97%, Iron Age 3% | 🟢 13/13 (100%) |  | BOWMAN×6, BOWMAN×8, SWORDMAN×10, PIKENEER×2, SWORDMAN×10, CHARIOT×12, SWORDMAN×14 |
| 🟩 | Chariot Rush | hardcoded | Bronze Age 100% | 🟢 13/13 (100%) |  | BOWMAN×12, SWORDMAN×12, SWORDMAN×12, BOWMAN×13, SWORDMAN×9, BOWMAN×12, SWORDMAN×14, SWORDMAN×16 |
| 🟩 | Copper Blades | hardcoded | Bronze Age 100% | 🟢 13/13 (100%) |  | SWORDMAN×11, CHARIOT×12, CHARIOT×13, CHARIOT×14, SWORDMAN×14, CHARIOT×12, BOWMAN×14, CHARIOT×16 |
| 🟩 | Harbor Raiders | hardcoded | Bronze Age 100% | 🟡 7/13 (54%) | BOWMAN×2, CHARIOT×2 | BOWMAN×13, BOWMAN×14, BOWMAN×14, CHARIOT×15, SWORDMAN×15, BOWMAN×16, BOWMAN×14, BOWMAN×16, SWORDMAN×18 |
| 🟩 | Clumsy Attackers | random | Bronze Age 76%, Neolithic 13%, Iron Age 11% | 🟢 13/13 (100%) |  | SWORDMAN×8, PIKENEER×9, CHARIOT×10, SWORDMAN×8, CHARIOT×13, BOWMAN×11, CHARIOT×10, WARRIOR×10 |
| 🟩 | Clumsy Attackers | random | Bronze Age 76%, Neolithic 13%, Iron Age 11% | 🟢 13/13 (100%) |  | SWORDMAN×8, PIKENEER×9, CHARIOT×10, SWORDMAN×8, CHARIOT×13, BOWMAN×11, CHARIOT×10, WARRIOR×10 |
| 🟩 | Petty Bandits | random | Bronze Age 86%, Neolithic 14% | 🟢 13/13 (100%) |  | SWORDMAN×12, SWORDMAN×10, BOWMAN×12, BOWMAN×10, CHARIOT×10, WARRIOR×13, BOWMAN×11, SWORDMAN×12 |
| 🟩 | Noisy Barbarians | random | Bronze Age 89%, Neolithic 11% | 🟢 13/13 (100%) |  | SWORDMAN×10, CHARIOT×9, CART×9, BOWMAN×12, BOWMAN×9, BOWMAN×11, SWORDMAN×8, SWORDMAN×12 |
| 🟩 | Rude Barbarians | random | Bronze Age 87%, Neolithic 13% | 🟢 13/13 (100%) |  | CART×12, BOWMAN×8, CHARIOT×10, SWORDMAN×12, CHARIOT×12, SWORDMAN×8, CHARIOT×10, CHARIOT×11, SWORDMAN×12 |
| 🟩 | Disorganized Mob | random | Bronze Age 73%, Neolithic 27% | 🟢 13/13 (100%) |  | WARRIOR×12, SWORDMAN×12, CHARIOT×11, WARRIOR×12, BOWMAN×12, SWORDMAN×8, SWORDMAN×12, BOWMAN×10 |
| 🟩 | Shrieking Horde | random | Bronze Age 74%, Neolithic 15%, Iron Age 11% | 🟡 10/13 (77%) | HORSEMAN_FAST×3 | BOWMAN×10, SWORDMAN×8, CHARIOT×13, BOWMAN×13, HORSEMAN_FAST×9, BOWMAN×10, CART×12, BOWMAN×7 |
| 🟩 | Rowdy Plunderers | random | Bronze Age 66%, Neolithic 20%, Iron Age 14% | 🟢 13/13 (100%) |  | CHARIOT×9, WARRIOR×12, CHARIOT×10, LEGIONARY×8, SWORDMAN×10, BOWMAN×10 |
| 🟩 | Crude Invaders | random | Bronze Age 70%, Neolithic 30% | 🟢 13/13 (100%) |  | SWORDMAN×12, BOWMAN×10, WARRIOR×10, CHARIOT×11, BOWMAN×10, WARRIOR×8 |
| 🟩 | Rampaging Rabble | random | Bronze Age 69%, Neolithic 31% | 🟢 13/13 (100%) |  | CHARIOT×11, CHARIOT×8, CART×9, CHARIOT×9, SWORDMAN×12, CART×9 |
| 🟩 | Drunken Raiders | random | Bronze Age 60%, Neolithic 24%, Iron Age 15% | 🟢 13/13 (100%) |  | CHARIOT×13, WARRIOR×10, CHARIOT×10, LARGE_CART×12, CART×9, BOWMAN×9, BOWMAN×7, SWORDMAN×8 |
| 🟩 | Howling Savages | random | Bronze Age 63%, Neolithic 25%, Iron Age 11% | 🟢 11/13 (85%) | HORSEMAN_SLOW×1 | CART×12, HORSEMAN_SLOW×9, SWORDMAN×8, WARRIOR×8, SWORDMAN×10, SWORDMAN×12, CHARIOT×10, SWORDMAN×10 |
| 🟩 | Bored Mercenaries | random | Bronze Age 67%, Neolithic 18%, Iron Age 15% | 🟢 13/13 (100%) |  | CHARIOT×7, CHARIOT×8, SWORDMAN×10, CHARIOT×9, BOWMAN×11, LEGIONARY×10, CART×12 |
| 🟩 | Angry Mob | random | Bronze Age 88%, Neolithic 12% | 🟢 13/13 (100%) |  | CHARIOT×9, CART×9, SWORDMAN×10, BOWMAN×7, BOWMAN×8, SWORDMAN×10, CHARIOT×11, BOWMAN×10 |
| 🟩 | Noisy Barbarians | random | Bronze Age 75%, Iron Age 14%, Neolithic 11% | 🟢 13/13 (100%) |  | BOWMAN×12, WARRIOR×8, BOWMAN×13, SWORDMAN×12, CHARIOT×9, SWORDMAN×8, HORSEMAN_FAST×10 |
| 🟩 | Restless Horde | random | Bronze Age 83%, Neolithic 17% | 🟢 13/13 (100%) |  | BOWMAN×7, CART×9, BOWMAN×7, SWORDMAN×10, SWORDMAN×8, SWORDMAN×12 |
| 🟩 | Howling Savages | random | Bronze Age 74%, Iron Age 15%, Neolithic 11% | 🟢 13/13 (100%) |  | SWORDMAN×10, SWORDMAN×8, SWORDMAN×10, CART×9, CHARIOT×10, HORSEMAN_FAST×12, BOWMAN×9, BOWMAN×13 |
| 🟩 | Weary Plunderers | random | Bronze Age 74%, Iron Age 14%, Neolithic 12% | 🟢 13/13 (100%) |  | HORSEMAN_FAST×11, BOWMAN×8, BOWMAN×8, CHARIOT×9, SWORDMAN×8, CART×9, CHARIOT×12, BOWMAN×11 |
| 🟩 | Weary Plunderers | random | Bronze Age 56%, Neolithic 27%, Iron Age 17% | 🟢 11/13 (85%) | PIKENEER×2 | SWORDMAN×12, SWORDMAN×10, PIKENEER×13, BOWMAN×12, BOWMAN×8, WARRIOR×11, CART×9 |
| 🟩 | Disorganized Mob | random | Bronze Age 84%, Neolithic 16% | 🟢 13/13 (100%) |  | SWORDMAN×10, BOWMAN×11, CHARIOT×8, SWORDMAN×10, WARRIOR×10, CHARIOT×13 |

#### Big Bronze

| Tower Era Distribution (29 towers) | Towers |
|---|---|
| Bronze Age 76% (22), Neolithic 24% (7) | ARROW_TOWER×20, SPIKE_TRAP×7, FIRE_TOWER×2 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Bronze Warriors | hardcoded | Bronze Age 97%, Iron Age 3% | 🟢 13/13 (100%) |  | BOWMAN×6, BOWMAN×8, SWORDMAN×10, PIKENEER×2, SWORDMAN×10, CHARIOT×12, SWORDMAN×14 |
| 🟩 | Chariot Rush | hardcoded | Bronze Age 100% | 🟢 13/13 (100%) |  | BOWMAN×12, SWORDMAN×12, SWORDMAN×12, BOWMAN×13, SWORDMAN×9, BOWMAN×12, SWORDMAN×14, SWORDMAN×16 |
| 🟩 | Copper Blades | hardcoded | Bronze Age 100% | 🟢 13/13 (100%) |  | SWORDMAN×11, CHARIOT×12, CHARIOT×13, CHARIOT×14, SWORDMAN×14, CHARIOT×12, BOWMAN×14, CHARIOT×16 |
| 🟩 | Harbor Raiders | hardcoded | Bronze Age 100% | 🟢 13/13 (100%) |  | BOWMAN×13, BOWMAN×14, BOWMAN×14, CHARIOT×15, SWORDMAN×15, BOWMAN×16, BOWMAN×14, BOWMAN×16, SWORDMAN×18 |
| 🟩 | Clumsy Attackers | random | Bronze Age 76%, Neolithic 13%, Iron Age 11% | 🟢 13/13 (100%) |  | SWORDMAN×8, PIKENEER×9, CHARIOT×10, SWORDMAN×8, CHARIOT×13, BOWMAN×11, CHARIOT×10, WARRIOR×10 |
| 🟩 | Clumsy Attackers | random | Bronze Age 76%, Neolithic 13%, Iron Age 11% | 🟢 13/13 (100%) |  | SWORDMAN×8, PIKENEER×9, CHARIOT×10, SWORDMAN×8, CHARIOT×13, BOWMAN×11, CHARIOT×10, WARRIOR×10 |
| 🟩 | Petty Bandits | random | Bronze Age 86%, Neolithic 14% | 🟢 13/13 (100%) |  | SWORDMAN×12, SWORDMAN×10, BOWMAN×12, BOWMAN×10, CHARIOT×10, WARRIOR×13, BOWMAN×11, SWORDMAN×12 |
| 🟩 | Noisy Barbarians | random | Bronze Age 89%, Neolithic 11% | 🟢 13/13 (100%) |  | SWORDMAN×10, CHARIOT×9, CART×9, BOWMAN×12, BOWMAN×9, BOWMAN×11, SWORDMAN×8, SWORDMAN×12 |
| 🟩 | Rude Barbarians | random | Bronze Age 87%, Neolithic 13% | 🟢 13/13 (100%) |  | CART×12, BOWMAN×8, CHARIOT×10, SWORDMAN×12, CHARIOT×12, SWORDMAN×8, CHARIOT×10, CHARIOT×11, SWORDMAN×12 |
| 🟩 | Disorganized Mob | random | Bronze Age 73%, Neolithic 27% | 🟢 13/13 (100%) |  | WARRIOR×12, SWORDMAN×12, CHARIOT×11, WARRIOR×12, BOWMAN×12, SWORDMAN×8, SWORDMAN×12, BOWMAN×10 |
| 🟩 | Shrieking Horde | random | Bronze Age 74%, Neolithic 15%, Iron Age 11% | 🟢 13/13 (100%) |  | BOWMAN×10, SWORDMAN×8, CHARIOT×13, BOWMAN×13, HORSEMAN_FAST×9, BOWMAN×10, CART×12, BOWMAN×7 |
| 🟩 | Rowdy Plunderers | random | Bronze Age 66%, Neolithic 20%, Iron Age 14% | 🟢 13/13 (100%) |  | CHARIOT×9, WARRIOR×12, CHARIOT×10, LEGIONARY×8, SWORDMAN×10, BOWMAN×10 |
| 🟩 | Crude Invaders | random | Bronze Age 70%, Neolithic 30% | 🟢 13/13 (100%) |  | SWORDMAN×12, BOWMAN×10, WARRIOR×10, CHARIOT×11, BOWMAN×10, WARRIOR×8 |
| 🟩 | Rampaging Rabble | random | Bronze Age 69%, Neolithic 31% | 🟢 13/13 (100%) |  | CHARIOT×11, CHARIOT×8, CART×9, CHARIOT×9, SWORDMAN×12, CART×9 |
| 🟩 | Drunken Raiders | random | Bronze Age 60%, Neolithic 24%, Iron Age 15% | 🟢 13/13 (100%) |  | CHARIOT×13, WARRIOR×10, CHARIOT×10, LARGE_CART×12, CART×9, BOWMAN×9, BOWMAN×7, SWORDMAN×8 |
| 🟩 | Howling Savages | random | Bronze Age 63%, Neolithic 25%, Iron Age 11% | 🟢 13/13 (100%) |  | CART×12, HORSEMAN_SLOW×9, SWORDMAN×8, WARRIOR×8, SWORDMAN×10, SWORDMAN×12, CHARIOT×10, SWORDMAN×10 |
| 🟩 | Bored Mercenaries | random | Bronze Age 67%, Neolithic 18%, Iron Age 15% | 🟢 13/13 (100%) |  | CHARIOT×7, CHARIOT×8, SWORDMAN×10, CHARIOT×9, BOWMAN×11, LEGIONARY×10, CART×12 |
| 🟩 | Angry Mob | random | Bronze Age 88%, Neolithic 12% | 🟢 13/13 (100%) |  | CHARIOT×9, CART×9, SWORDMAN×10, BOWMAN×7, BOWMAN×8, SWORDMAN×10, CHARIOT×11, BOWMAN×10 |
| 🟩 | Noisy Barbarians | random | Bronze Age 75%, Iron Age 14%, Neolithic 11% | 🟢 13/13 (100%) |  | BOWMAN×12, WARRIOR×8, BOWMAN×13, SWORDMAN×12, CHARIOT×9, SWORDMAN×8, HORSEMAN_FAST×10 |
| 🟩 | Restless Horde | random | Bronze Age 83%, Neolithic 17% | 🟢 13/13 (100%) |  | BOWMAN×7, CART×9, BOWMAN×7, SWORDMAN×10, SWORDMAN×8, SWORDMAN×12 |
| 🟩 | Howling Savages | random | Bronze Age 74%, Iron Age 15%, Neolithic 11% | 🟢 13/13 (100%) |  | SWORDMAN×10, SWORDMAN×8, SWORDMAN×10, CART×9, CHARIOT×10, HORSEMAN_FAST×12, BOWMAN×9, BOWMAN×13 |
| 🟩 | Weary Plunderers | random | Bronze Age 74%, Iron Age 14%, Neolithic 12% | 🟢 13/13 (100%) |  | HORSEMAN_FAST×11, BOWMAN×8, BOWMAN×8, CHARIOT×9, SWORDMAN×8, CART×9, CHARIOT×12, BOWMAN×11 |
| 🟩 | Weary Plunderers | random | Bronze Age 56%, Neolithic 27%, Iron Age 17% | 🟢 13/13 (100%) |  | SWORDMAN×12, SWORDMAN×10, PIKENEER×13, BOWMAN×12, BOWMAN×8, WARRIOR×11, CART×9 |
| 🟩 | Disorganized Mob | random | Bronze Age 84%, Neolithic 16% | 🟢 13/13 (100%) |  | SWORDMAN×10, BOWMAN×11, CHARIOT×8, SWORDMAN×10, WARRIOR×10, CHARIOT×13 |

#### Weak Bronze

| Tower Era Distribution (6 towers) | Towers |
|---|---|
| Bronze Age 50% (3), Neolithic 50% (3) | DOUBLE_SLING_TOWER×3, ARROW_TOWER×2, FIRE_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Bronze Warriors | hardcoded | Bronze Age 97%, Iron Age 3% | 🟡 8/13 (62%) | BOWMAN×2, PIKENEER×1 | BOWMAN×6, BOWMAN×8, SWORDMAN×10, PIKENEER×2, SWORDMAN×10, CHARIOT×12, SWORDMAN×14 |
| 🟥 | Chariot Rush | hardcoded | Bronze Age 100% | ⬛ 0/13 (0%) | BOWMAN×6, SWORDMAN×1 | BOWMAN×12, SWORDMAN×12, SWORDMAN×12, BOWMAN×13, SWORDMAN×9, BOWMAN×12, SWORDMAN×14, SWORDMAN×16 |
| 🟥 | Copper Blades | hardcoded | Bronze Age 100% | ⬛ 0/13 (0%) | CHARIOT×7, SWORDMAN×2, BOWMAN×1 | SWORDMAN×11, CHARIOT×12, CHARIOT×13, CHARIOT×14, SWORDMAN×14, CHARIOT×12, BOWMAN×14, CHARIOT×16 |
| 🟥 | Harbor Raiders | hardcoded | Bronze Age 100% | ⬛ 0/13 (0%) | BOWMAN×7 | BOWMAN×13, BOWMAN×14, BOWMAN×14, CHARIOT×15, SWORDMAN×15, BOWMAN×16, BOWMAN×14, BOWMAN×16, SWORDMAN×18 |
| 🟥 | Clumsy Attackers | random | Bronze Age 76%, Neolithic 13%, Iron Age 11% | ⬛ 0/13 (0%) | PIKENEER×7, CHARIOT×3, BOWMAN×2 | SWORDMAN×8, PIKENEER×9, CHARIOT×10, SWORDMAN×8, CHARIOT×13, BOWMAN×11, CHARIOT×10, WARRIOR×10 |
| 🟥 | Clumsy Attackers | random | Bronze Age 76%, Neolithic 13%, Iron Age 11% | ⬛ 0/13 (0%) | PIKENEER×7, CHARIOT×3, BOWMAN×2 | SWORDMAN×8, PIKENEER×9, CHARIOT×10, SWORDMAN×8, CHARIOT×13, BOWMAN×11, CHARIOT×10, WARRIOR×10 |
| 🟥 | Petty Bandits | random | Bronze Age 86%, Neolithic 14% | ⬛ 0/13 (0%) | BOWMAN×7 | SWORDMAN×12, SWORDMAN×10, BOWMAN×12, BOWMAN×10, CHARIOT×10, WARRIOR×13, BOWMAN×11, SWORDMAN×12 |
| 🟥 | Noisy Barbarians | random | Bronze Age 89%, Neolithic 11% | ⬛ 0/13 (0%) | BOWMAN×7 | SWORDMAN×10, CHARIOT×9, CART×9, BOWMAN×12, BOWMAN×9, BOWMAN×11, SWORDMAN×8, SWORDMAN×12 |
| 🟥 | Rude Barbarians | random | Bronze Age 87%, Neolithic 13% | ⬛ 0/13 (0%) | CHARIOT×5, BOWMAN×4 | CART×12, BOWMAN×8, CHARIOT×10, SWORDMAN×12, CHARIOT×12, SWORDMAN×8, CHARIOT×10, CHARIOT×11, SWORDMAN×12 |
| 🟥 | Disorganized Mob | random | Bronze Age 73%, Neolithic 27% | ⬛ 0/13 (0%) | WARRIOR×4, SWORDMAN×3, CHARIOT×1, BOWMAN×1 | WARRIOR×12, SWORDMAN×12, CHARIOT×11, WARRIOR×12, BOWMAN×12, SWORDMAN×8, SWORDMAN×12, BOWMAN×10 |
| 🟥 | Shrieking Horde | random | Bronze Age 74%, Neolithic 15%, Iron Age 11% | ⬛ 0/13 (0%) | HORSEMAN_FAST×5, BOWMAN×4 | BOWMAN×10, SWORDMAN×8, CHARIOT×13, BOWMAN×13, HORSEMAN_FAST×9, BOWMAN×10, CART×12, BOWMAN×7 |
| 🟥 | Rowdy Plunderers | random | Bronze Age 66%, Neolithic 20%, Iron Age 14% | ⬛ 0/13 (0%) | LEGIONARY×8, BOWMAN×3 | CHARIOT×9, WARRIOR×12, CHARIOT×10, LEGIONARY×8, SWORDMAN×10, BOWMAN×10 |
| 🟥 | Crude Invaders | random | Bronze Age 70%, Neolithic 30% | ⬛ 0/13 (0%) | BOWMAN×7 | SWORDMAN×12, BOWMAN×10, WARRIOR×10, CHARIOT×11, BOWMAN×10, WARRIOR×8 |
| 🟩 | Rampaging Rabble | random | Bronze Age 69%, Neolithic 31% | 🟢 13/13 (100%) |  | CHARIOT×11, CHARIOT×8, CART×9, CHARIOT×9, SWORDMAN×12, CART×9 |
| 🟥 | Drunken Raiders | random | Bronze Age 60%, Neolithic 24%, Iron Age 15% | ⬛ 0/13 (0%) | PIKENEER×7, CHARIOT×4, BOWMAN×1 | CHARIOT×13, WARRIOR×10, CHARIOT×10, LARGE_CART×12, CART×9, BOWMAN×9, BOWMAN×7, SWORDMAN×8 |
| 🟥 | Howling Savages | random | Bronze Age 63%, Neolithic 25%, Iron Age 11% | ⬛ 0/13 (0%) | HORSEMAN_SLOW×7 | CART×12, HORSEMAN_SLOW×9, SWORDMAN×8, WARRIOR×8, SWORDMAN×10, SWORDMAN×12, CHARIOT×10, SWORDMAN×10 |
| 🟥 | Bored Mercenaries | random | Bronze Age 67%, Neolithic 18%, Iron Age 15% | ⬛ 0/13 (0%) | BOWMAN×5, LEGIONARY×3 | CHARIOT×7, CHARIOT×8, SWORDMAN×10, CHARIOT×9, BOWMAN×11, LEGIONARY×10, CART×12 |
| 🟥 | Angry Mob | random | Bronze Age 88%, Neolithic 12% | ⬛ 0/13 (0%) | BOWMAN×7 | CHARIOT×9, CART×9, SWORDMAN×10, BOWMAN×7, BOWMAN×8, SWORDMAN×10, CHARIOT×11, BOWMAN×10 |
| 🟥 | Noisy Barbarians | random | Bronze Age 75%, Iron Age 14%, Neolithic 11% | ⬛ 0/13 (0%) | BOWMAN×7 | BOWMAN×12, WARRIOR×8, BOWMAN×13, SWORDMAN×12, CHARIOT×9, SWORDMAN×8, HORSEMAN_FAST×10 |
| 🟩 | Restless Horde | random | Bronze Age 83%, Neolithic 17% | 🟠 3/13 (23%) | BOWMAN×5 | BOWMAN×7, CART×9, BOWMAN×7, SWORDMAN×10, SWORDMAN×8, SWORDMAN×12 |
| 🟥 | Howling Savages | random | Bronze Age 74%, Iron Age 15%, Neolithic 11% | ⬛ 0/13 (0%) | HORSEMAN_FAST×11, BOWMAN×1 | SWORDMAN×10, SWORDMAN×8, SWORDMAN×10, CART×9, CHARIOT×10, HORSEMAN_FAST×12, BOWMAN×9, BOWMAN×13 |
| 🟥 | Weary Plunderers | random | Bronze Age 74%, Iron Age 14%, Neolithic 12% | ⬛ 0/13 (0%) | HORSEMAN_FAST×9, BOWMAN×2 | HORSEMAN_FAST×11, BOWMAN×8, BOWMAN×8, CHARIOT×9, SWORDMAN×8, CART×9, CHARIOT×12, BOWMAN×11 |
| 🟥 | Weary Plunderers | random | Bronze Age 56%, Neolithic 27%, Iron Age 17% | ⬛ 0/13 (0%) | PIKENEER×11, SWORDMAN×1 | SWORDMAN×12, SWORDMAN×10, PIKENEER×13, BOWMAN×12, BOWMAN×8, WARRIOR×11, CART×9 |
| 🟥 | Disorganized Mob | random | Bronze Age 84%, Neolithic 16% | ⬛ 0/13 (0%) | BOWMAN×5, CHARIOT×4 | SWORDMAN×10, BOWMAN×11, CHARIOT×8, SWORDMAN×10, WARRIOR×10, CHARIOT×13 |

### Iron Age

#### Schafshügel (Bronze)

| Tower Era Distribution (13 towers) | Towers |
|---|---|
| Bronze Age 77% (10), Iron Age 23% (3) | BALLISTA_TOWER×5, FIRE_TOWER×4, CATAPULTS×3, ARROW_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟥 | Iron Legion | hardcoded | Iron Age 100% | ⬛ 0/12 (0%) | PIKENEER×9, LEGIONARY×3 | HORSEMAN_SLOW×10, HORSEMAN_SLOW×10, LEGIONARY×11, PIKENEER×12, HORSEMAN_SLOW×12, PIKENEER×13, LEGIONARY×15, HORSEMAN_FAST×16, THE_SWORDMASTER×18, LEGIONARY×20, LEGIONARY×22, PIKENEER×24 |
| 🟥 | Cavalry Strike | hardcoded | Iron Age 96%, Medieval 4% | ⬛ 0/12 (0%) | PIKENEER×5, HORSEMAN_FAST×4, LEGIONARY×3 | LEGIONARY×14, PIKENEER×15, HORSEMAN_FAST×16, LARGE_CART×17, LEGIONARY×17, LEGIONARY×18, KNIGHT×9, PIKENEER×22, LARGE_CART×18, HORSEMAN_SLOW×20, HORSEMAN_SLOW×22, PIKENEER×24, LEGIONARY×26 |
| 🟥 | Legionary March | hardcoded | Iron Age 96%, Medieval 4% | ⬛ 0/12 (0%) | PIKENEER×6, LEGIONARY×3, HORSEMAN_FAST×1, HORSEMAN_SLOW×1 | LEGIONARY×14, HORSEMAN_SLOW×15, PIKENEER×16, HORSEMAN_FAST×17, HORSEMAN_FAST×17, HORSEMAN_SLOW×18, CRUSADER×9, LARGE_CART×20, LEGIONARY×18, HORSEMAN_FAST×20, LEGIONARY×22, HORSEMAN_FAST×24, THE_SWORDMASTER×26 |
| 🟥 | Iron Tide | hardcoded | Iron Age 95%, Medieval 5% | ⬛ 0/12 (0%) | HORSEMAN_FAST×8, LEGIONARY×4 | LEGIONARY×14, HORSEMAN_FAST×15, LARGE_CART×16, HORSEMAN_SLOW×16, LARGE_CART×17, HORSEMAN_FAST×18, LEGIONARY×18, THE_SWORDMASTER×19, PIKENEER×20, THE_SWORDMASTER×20, LARGE_CART×22, CRUSADER×12, THE_SWORDMASTER×26, LEGIONARY×28 |
| 🟥 | Quartermaster Force | hardcoded | Iron Age 92%, Bronze Age 8% | ⬛ 0/12 (0%) | LEGIONARY×3, THE_SWORDMASTER×1, HORSEMAN_SLOW×1 | THE_SWORDMASTER×16, LEGIONARY×17, HORSEMAN_SLOW×18, LARGE_CART×19, PIKENEER×20, LARGE_CART×21, LARGE_CART×22, LEGIONARY×16, PIKENEER×18, LARGE_CART×20, HORSEMAN_SLOW×22, HORSEMAN_SLOW×24, HORSEMAN_FAST×26, SWORDMAN×28, PIKENEER×28, LEGIONARY×28 |
| 🟥 | Desperate Looters | random | Iron Age 99%, Medieval 1% | ⬛ 0/12 (0%) | KNIGHT×3, LEGIONARY×3, HORSEMAN_SLOW×2, HORSEMAN_FAST×2 | KNIGHT×9, HORSEMAN_SLOW×13, HORSEMAN_FAST×8, LEGIONARY×13, HORSEMAN_SLOW×9, LARGE_CART×8, PIKENEER×11, HORSEMAN_FAST×11, HORSEMAN_FAST×15, THE_SWORDMASTER×999 |
| 🟥 | Desperate Looters | random | Iron Age 99%, Medieval 1% | ⬛ 0/12 (0%) | KNIGHT×3, LEGIONARY×3, HORSEMAN_SLOW×2, HORSEMAN_FAST×2 | KNIGHT×9, HORSEMAN_SLOW×13, HORSEMAN_FAST×8, LEGIONARY×13, HORSEMAN_SLOW×9, LARGE_CART×8, PIKENEER×11, HORSEMAN_FAST×11, HORSEMAN_FAST×15, THE_SWORDMASTER×999 |
| 🟥 | Restless Horde | random | Iron Age 99%, Bronze Age 1% | ⬛ 0/12 (0%) | PIKENEER×3, THE_SWORDMASTER×1, HORSEMAN_SLOW×1 | LARGE_CART×8, THE_SWORDMASTER×999, LEGIONARY×11, HORSEMAN_SLOW×11, PIKENEER×14, HORSEMAN_FAST×13, HORSEMAN_FAST×9, LEGIONARY×14, CHARIOT×8, LEGIONARY×11 |
| 🟥 | Drunken Raiders | random | Iron Age 99%, Medieval 1% | ⬛ 0/12 (0%) | PIKENEER×3, HORSEMAN_FAST×2, THE_SWORDMASTER×1 | PIKENEER×13, HORSEMAN_SLOW×13, THE_SWORDMASTER×999, HORSEMAN_FAST×11, LEGIONARY×9, SIEGE_RAM×15, PIKENEER×10, HORSEMAN_SLOW×13, PIKENEER×13, HORSEMAN_FAST×14 |
| 🟥 | Howling Savages | random | Iron Age 99%, Bronze Age 1% | ⬛ 0/12 (0%) | HORSEMAN_FAST×10, LEGIONARY×2 | LEGIONARY×9, LEGIONARY×14, HORSEMAN_FAST×13, LEGIONARY×15, LARGE_CART×12, PIKENEER×10, LEGIONARY×13, SWORDMAN×14, LEGIONARY×11, HORSEMAN_FAST×11, THE_SWORDMASTER×999 |
| 🟥 | Bored Mercenaries | random | Iron Age 70%, Bronze Age 30% | ⬛ 0/12 (0%) | PIKENEER×5, LEGIONARY×5, HORSEMAN_SLOW×1 | LARGE_CART×12, HORSEMAN_SLOW×14, CHARIOT×10, BOWMAN×13, LEGIONARY×13, PIKENEER×11, HORSEMAN_SLOW×13, LEGIONARY×9, BOWMAN×14, HORSEMAN_FAST×14 |
| 🟥 | Crude Invaders | random | Iron Age 99%, Medieval 1% | ⬛ 0/12 (0%) | HANDGUNNER×12 | PIKENEER×8, HORSEMAN_SLOW×12, HANDGUNNER×15, LARGE_CART×8, PIKENEER×8, LARGE_CART×12, LEGIONARY×11, HORSEMAN_FAST×13, HORSEMAN_FAST×9, THE_SWORDMASTER×999 |
| 🟥 | Crude Invaders | random | Iron Age 77%, Medieval 23% | ⬛ 0/12 (0%) | SAMURAI×9, PIKENEER×3 | SAMURAI×10, HORSEMAN_SLOW×12, LARGE_CART×8, PIKENEER×13, LARGE_CART×12, LEGIONARY×9, HORSEMAN_FAST×11, SIEGE_RAM×9 |
| 🟩 | Restless Horde | random | Iron Age 76%, Bronze Age 24% | 🔴 1/12 (8%) | PIKENEER×5, HORSEMAN_SLOW×3 | HORSEMAN_FAST×14, HORSEMAN_SLOW×9, BOWMAN×9, PIKENEER×12, CHARIOT×13, HORSEMAN_SLOW×12, PIKENEER×12, LARGE_CART×12 |
| 🟥 | Restless Horde | random | Iron Age 96%, Bronze Age 4% | ⬛ 0/12 (0%) | LEGIONARY×2, PIKENEER×1, BOWMAN×1, THE_SWORDMASTER×1 | SWORDMAN×10, LARGE_CART×8, LARGE_CART×12, PIKENEER×12, THE_SWORDMASTER×999, BOWMAN×15, BOWMAN×13, LEGIONARY×12 |
| 🟥 | Angry Mob | random | Iron Age 95%, Bronze Age 3%, Medieval 2% | ⬛ 0/12 (0%) | HANDGUNNER×8, HORSEMAN_FAST×1, THE_SWORDMASTER×1 | HANDGUNNER×9, THE_SWORDMASTER×999, HORSEMAN_FAST×9, LARGE_CART×12, SAMURAI×13, SWORDMAN×14, BOWMAN×14, PIKENEER×8, LARGE_CART×8, SWORDMAN×10 |
| 🟥 | Lazy Raiders | random | Iron Age 97%, Bronze Age 2%, Medieval 1% | ⬛ 0/12 (0%) | LEGIONARY×12 | LEGIONARY×12, LEGIONARY×14, LEGIONARY×9, LEGIONARY×9, BOWMAN×10, THE_SWORDMASTER×999, SWORDMAN×10, HORSEMAN_FAST×11, SIEGE_RAM×9, HORSEMAN_FAST×13 |
| 🟥 | Clumsy Attackers | random | Iron Age 99%, Medieval 1% | ⬛ 0/12 (0%) | HORSEMAN_FAST×4, PIKENEER×4, HORSEMAN_SLOW×1, THE_SWORDMASTER×1 | HORSEMAN_SLOW×12, HORSEMAN_FAST×13, PIKENEER×14, THE_SWORDMASTER×999, PIKENEER×8, LEGIONARY×13, HANDGUNNER×10, HORSEMAN_FAST×14, LEGIONARY×12 |
| 🟥 | Unlucky Raiders | random | Iron Age 99%, Bronze Age 1% | ⬛ 0/12 (0%) | HORSEMAN_FAST×10, LEGIONARY×2 | LEGIONARY×13, HORSEMAN_FAST×11, SWORDMAN×12, HORSEMAN_FAST×12, PIKENEER×9, PIKENEER×13, HORSEMAN_FAST×12, HORSEMAN_SLOW×9, PIKENEER×8, THE_SWORDMASTER×999 |
| 🟥 | Lazy Raiders | random | Iron Age 98%, Bronze Age 1%, Medieval 1% | ⬛ 0/12 (0%) | CRUSADER×2, HORSEMAN_FAST×1, THE_SWORDMASTER×1 | HORSEMAN_FAST×13, SWORDMAN×14, HORSEMAN_FAST×9, HORSEMAN_SLOW×8, THE_SWORDMASTER×999, LEGIONARY×8, CRUSADER×13, PIKENEER×10, PIKENEER×15 |
| 🟥 | Forgotten Warband | random | Iron Age 71%, Medieval 18%, Bronze Age 11% | ⬛ 0/12 (0%) | HANDGUNNER×7, PIKENEER×3, LEGIONARY×2 | HORSEMAN_SLOW×8, HORSEMAN_FAST×11, LEGIONARY×15, LARGE_CART×8, HANDGUNNER×15, HORSEMAN_FAST×10, HORSEMAN_SLOW×8, BOWMAN×9 |
| 🟥 | Grumpy Marauders | random | Iron Age 98%, Medieval 2% | ⬛ 0/12 (0%) | PIKENEER×5, HORSEMAN_FAST×4, LEGIONARY×3 | LEGIONARY×9, PIKENEER×15, HORSEMAN_SLOW×11, HORSEMAN_FAST×10, HANDGUNNER×9, HORSEMAN_FAST×8, HORSEMAN_SLOW×11, THE_SWORDMASTER×999, CONDOTTERI×10, HORSEMAN_FAST×14 |
| 🟥 | Hungry Invaders | random | Iron Age 89%, Medieval 11% | ⬛ 0/12 (0%) | HORSEMAN_FAST×3, CRUSADER×3, SIEGE_RAM×1 | LARGE_CART×12, HORSEMAN_FAST×13, HORSEMAN_SLOW×12, SIEGE_RAM×12, LEGIONARY×10, LARGE_CART×8, LARGE_CART×12, LARGE_CART×12, PIKENEER×9, HORSEMAN_SLOW×10 |
| 🟥 | Clumsy Attackers | random | Iron Age 64%, Bronze Age 27%, Medieval 8% | ⬛ 0/12 (0%) | CHARIOT×5, HORSEMAN_SLOW×2, LEGIONARY×2, HORSEMAN_FAST×1 | HORSEMAN_SLOW×9, HORSEMAN_FAST×12, LEGIONARY×9, HORSEMAN_SLOW×14, LEGIONARY×11, CHARIOT×14, SAMURAI×9, LEGIONARY×13, BOWMAN×15 |
| 🟥 | Grumpy Marauders | random | Iron Age 78%, Medieval 13%, Bronze Age 10% | ⬛ 0/12 (0%) | HORSEMAN_FAST×5, SIEGE_RAM×2, LEGIONARY×1 | LEGIONARY×12, SIEGE_RAM×12, HORSEMAN_FAST×12, HORSEMAN_FAST×12, LARGE_CART×16, HORSEMAN_SLOW×13, LARGE_CART×8, BOWMAN×9 |

#### Mixed Iron/Bronze

| Tower Era Distribution (31 towers) | Towers |
|---|---|
| Bronze Age 68% (21), Iron Age 32% (10) | FIRE_TOWER×9, CATAPULTS×8, ARROW_TOWER×6, BALLISTA_TOWER×6, ARBELESTE_TOWER×2 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Iron Legion | hardcoded | Iron Age 100% | 🟡 9/16 (56%) | THE_SWORDMASTER×1 | HORSEMAN_SLOW×10, HORSEMAN_SLOW×10, LEGIONARY×11, PIKENEER×12, HORSEMAN_SLOW×12, PIKENEER×13, LEGIONARY×15, HORSEMAN_FAST×16, THE_SWORDMASTER×18, LEGIONARY×20, LEGIONARY×22, PIKENEER×24 |
| 🟩 | Cavalry Strike | hardcoded | Iron Age 96%, Medieval 4% | 🟢 13/16 (81%) | KNIGHT×3 | LEGIONARY×14, PIKENEER×15, HORSEMAN_FAST×16, LARGE_CART×17, LEGIONARY×17, LEGIONARY×18, KNIGHT×9, PIKENEER×22, LARGE_CART×18, HORSEMAN_SLOW×20, HORSEMAN_SLOW×22, PIKENEER×24, LEGIONARY×26 |
| 🟥 | Legionary March | hardcoded | Iron Age 96%, Medieval 4% | ⬛ 0/16 (0%) | CRUSADER×7, THE_SWORDMASTER×1 | LEGIONARY×14, HORSEMAN_SLOW×15, PIKENEER×16, HORSEMAN_FAST×17, HORSEMAN_FAST×17, HORSEMAN_SLOW×18, CRUSADER×9, LARGE_CART×20, LEGIONARY×18, HORSEMAN_FAST×20, LEGIONARY×22, HORSEMAN_FAST×24, THE_SWORDMASTER×26 |
| 🟥 | Iron Tide | hardcoded | Iron Age 95%, Medieval 5% | ⬛ 0/16 (0%) | CRUSADER×5, THE_SWORDMASTER×1 | LEGIONARY×14, HORSEMAN_FAST×15, LARGE_CART×16, HORSEMAN_SLOW×16, LARGE_CART×17, HORSEMAN_FAST×18, LEGIONARY×18, THE_SWORDMASTER×19, PIKENEER×20, THE_SWORDMASTER×20, LARGE_CART×22, CRUSADER×12, THE_SWORDMASTER×26, LEGIONARY×28 |
| 🟩 | Quartermaster Force | hardcoded | Iron Age 92%, Bronze Age 8% | 🟢 16/16 (100%) |  | THE_SWORDMASTER×16, LEGIONARY×17, HORSEMAN_SLOW×18, LARGE_CART×19, PIKENEER×20, LARGE_CART×21, LARGE_CART×22, LEGIONARY×16, PIKENEER×18, LARGE_CART×20, HORSEMAN_SLOW×22, HORSEMAN_SLOW×24, HORSEMAN_FAST×26, SWORDMAN×28, PIKENEER×28, LEGIONARY×28 |
| 🟩 | Desperate Looters | random | Iron Age 99%, Medieval 1% | 🟢 15/16 (94%) | KNIGHT×1 | KNIGHT×9, HORSEMAN_SLOW×13, HORSEMAN_FAST×8, LEGIONARY×13, HORSEMAN_SLOW×9, LARGE_CART×8, PIKENEER×11, HORSEMAN_FAST×11, HORSEMAN_FAST×15, THE_SWORDMASTER×999 |
| 🟩 | Desperate Looters | random | Iron Age 99%, Medieval 1% | 🟢 15/16 (94%) | KNIGHT×1 | KNIGHT×9, HORSEMAN_SLOW×13, HORSEMAN_FAST×8, LEGIONARY×13, HORSEMAN_SLOW×9, LARGE_CART×8, PIKENEER×11, HORSEMAN_FAST×11, HORSEMAN_FAST×15, THE_SWORDMASTER×999 |
| 🟩 | Restless Horde | random | Iron Age 99%, Bronze Age 1% | 🟢 16/16 (100%) |  | LARGE_CART×8, THE_SWORDMASTER×999, LEGIONARY×11, HORSEMAN_SLOW×11, PIKENEER×14, HORSEMAN_FAST×13, HORSEMAN_FAST×9, LEGIONARY×14, CHARIOT×8, LEGIONARY×11 |
| 🟥 | Drunken Raiders | random | Iron Age 99%, Medieval 1% | ⬛ 0/16 (0%) | CRUSADER×4, THE_SWORDMASTER×1, SIEGE_RAM×1 | PIKENEER×13, HORSEMAN_SLOW×13, THE_SWORDMASTER×999, HORSEMAN_FAST×11, LEGIONARY×9, SIEGE_RAM×15, PIKENEER×10, HORSEMAN_SLOW×13, PIKENEER×13, HORSEMAN_FAST×14 |
| 🟩 | Howling Savages | random | Iron Age 99%, Bronze Age 1% | 🟢 16/16 (100%) |  | LEGIONARY×9, LEGIONARY×14, HORSEMAN_FAST×13, LEGIONARY×15, LARGE_CART×12, PIKENEER×10, LEGIONARY×13, SWORDMAN×14, LEGIONARY×11, HORSEMAN_FAST×11, THE_SWORDMASTER×999 |
| 🟩 | Bored Mercenaries | random | Iron Age 70%, Bronze Age 30% | 🟢 16/16 (100%) |  | LARGE_CART×12, HORSEMAN_SLOW×14, CHARIOT×10, BOWMAN×13, LEGIONARY×13, PIKENEER×11, HORSEMAN_SLOW×13, LEGIONARY×9, BOWMAN×14, HORSEMAN_FAST×14 |
| 🟩 | Crude Invaders | random | Iron Age 99%, Medieval 1% | 🔴 3/16 (19%) | HANDGUNNER×13 | PIKENEER×8, HORSEMAN_SLOW×12, HANDGUNNER×15, LARGE_CART×8, PIKENEER×8, LARGE_CART×12, LEGIONARY×11, HORSEMAN_FAST×13, HORSEMAN_FAST×9, THE_SWORDMASTER×999 |
| 🟩 | Crude Invaders | random | Iron Age 77%, Medieval 23% | 🔴 3/16 (19%) | CRUSADER×6, SAMURAI×1 | SAMURAI×10, HORSEMAN_SLOW×12, LARGE_CART×8, PIKENEER×13, LARGE_CART×12, LEGIONARY×9, HORSEMAN_FAST×11, SIEGE_RAM×9 |
| 🟩 | Restless Horde | random | Iron Age 76%, Bronze Age 24% | 🟢 16/16 (100%) |  | HORSEMAN_FAST×14, HORSEMAN_SLOW×9, BOWMAN×9, PIKENEER×12, CHARIOT×13, HORSEMAN_SLOW×12, PIKENEER×12, LARGE_CART×12 |
| 🟩 | Restless Horde | random | Iron Age 96%, Bronze Age 4% | 🟢 16/16 (100%) |  | SWORDMAN×10, LARGE_CART×8, LARGE_CART×12, PIKENEER×12, THE_SWORDMASTER×999, BOWMAN×15, BOWMAN×13, LEGIONARY×12 |
| 🟩 | Angry Mob | random | Iron Age 95%, Bronze Age 3%, Medieval 2% | 🟡 8/16 (50%) | HANDGUNNER×6, SAMURAI×2 | HANDGUNNER×9, THE_SWORDMASTER×999, HORSEMAN_FAST×9, LARGE_CART×12, SAMURAI×13, SWORDMAN×14, BOWMAN×14, PIKENEER×8, LARGE_CART×8, SWORDMAN×10 |
| 🟥 | Lazy Raiders | random | Iron Age 97%, Bronze Age 2%, Medieval 1% | ⬛ 0/16 (0%) | CRUSADER×5, THE_SWORDMASTER×1 | LEGIONARY×12, LEGIONARY×14, LEGIONARY×9, LEGIONARY×9, BOWMAN×10, THE_SWORDMASTER×999, SWORDMAN×10, HORSEMAN_FAST×11, SIEGE_RAM×9, HORSEMAN_FAST×13 |
| 🟩 | Clumsy Attackers | random | Iron Age 99%, Medieval 1% | 🟡 8/16 (50%) | HANDGUNNER×8 | HORSEMAN_SLOW×12, HORSEMAN_FAST×13, PIKENEER×14, THE_SWORDMASTER×999, PIKENEER×8, LEGIONARY×13, HANDGUNNER×10, HORSEMAN_FAST×14, LEGIONARY×12 |
| 🟩 | Unlucky Raiders | random | Iron Age 99%, Bronze Age 1% | 🟢 16/16 (100%) |  | LEGIONARY×13, HORSEMAN_FAST×11, SWORDMAN×12, HORSEMAN_FAST×12, PIKENEER×9, PIKENEER×13, HORSEMAN_FAST×12, HORSEMAN_SLOW×9, PIKENEER×8, THE_SWORDMASTER×999 |
| 🟥 | Lazy Raiders | random | Iron Age 98%, Bronze Age 1%, Medieval 1% | ⬛ 0/16 (0%) | CRUSADER×5, THE_SWORDMASTER×1 | HORSEMAN_FAST×13, SWORDMAN×14, HORSEMAN_FAST×9, HORSEMAN_SLOW×8, THE_SWORDMASTER×999, LEGIONARY×8, CRUSADER×13, PIKENEER×10, PIKENEER×15 |
| 🟩 | Forgotten Warband | random | Iron Age 71%, Medieval 18%, Bronze Age 11% | 🔴 2/16 (12%) | HANDGUNNER×14 | HORSEMAN_SLOW×8, HORSEMAN_FAST×11, LEGIONARY×15, LARGE_CART×8, HANDGUNNER×15, HORSEMAN_FAST×10, HORSEMAN_SLOW×8, BOWMAN×9 |
| 🟥 | Grumpy Marauders | random | Iron Age 98%, Medieval 2% | ⬛ 0/16 (0%) | HANDGUNNER×6, CONDOTTERI×2, THE_SWORDMASTER×1 | LEGIONARY×9, PIKENEER×15, HORSEMAN_SLOW×11, HORSEMAN_FAST×10, HANDGUNNER×9, HORSEMAN_FAST×8, HORSEMAN_SLOW×11, THE_SWORDMASTER×999, CONDOTTERI×10, HORSEMAN_FAST×14 |
| 🟥 | Hungry Invaders | random | Iron Age 89%, Medieval 11% | ⬛ 0/16 (0%) | CRUSADER×7, SIEGE_RAM×1 | LARGE_CART×12, HORSEMAN_FAST×13, HORSEMAN_SLOW×12, SIEGE_RAM×12, LEGIONARY×10, LARGE_CART×8, LARGE_CART×12, LARGE_CART×12, PIKENEER×9, HORSEMAN_SLOW×10 |
| 🟩 | Clumsy Attackers | random | Iron Age 64%, Bronze Age 27%, Medieval 8% | 🟢 15/16 (94%) | SAMURAI×1 | HORSEMAN_SLOW×9, HORSEMAN_FAST×12, LEGIONARY×9, HORSEMAN_SLOW×14, LEGIONARY×11, CHARIOT×14, SAMURAI×9, LEGIONARY×13, BOWMAN×15 |
| 🟥 | Grumpy Marauders | random | Iron Age 78%, Medieval 13%, Bronze Age 10% | ⬛ 0/16 (0%) | CRUSADER×7, SIEGE_RAM×1 | LEGIONARY×12, SIEGE_RAM×12, HORSEMAN_FAST×12, HORSEMAN_FAST×12, LARGE_CART×16, HORSEMAN_SLOW×13, LARGE_CART×8, BOWMAN×9 |

#### Almost Bronze

| Tower Era Distribution (25 towers) | Towers |
|---|---|
| Bronze Age 92% (23), Iron Age 8% (2) | ARROW_TOWER×14, BALLISTA_TOWER×7, FIRE_TOWER×2, ARBELESTE_TOWER×2 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟥 | Iron Legion | hardcoded | Iron Age 100% | ⬛ 0/13 (0%) | LEGIONARY×3, PIKENEER×3, THE_SWORDMASTER×1 | HORSEMAN_SLOW×10, HORSEMAN_SLOW×10, LEGIONARY×11, PIKENEER×12, HORSEMAN_SLOW×12, PIKENEER×13, LEGIONARY×15, HORSEMAN_FAST×16, THE_SWORDMASTER×18, LEGIONARY×20, LEGIONARY×22, PIKENEER×24 |
| 🟥 | Cavalry Strike | hardcoded | Iron Age 96%, Medieval 4% | ⬛ 0/13 (0%) | PIKENEER×8, KNIGHT×3, LEGIONARY×2 | LEGIONARY×14, PIKENEER×15, HORSEMAN_FAST×16, LARGE_CART×17, LEGIONARY×17, LEGIONARY×18, KNIGHT×9, PIKENEER×22, LARGE_CART×18, HORSEMAN_SLOW×20, HORSEMAN_SLOW×22, PIKENEER×24, LEGIONARY×26 |
| 🟥 | Legionary March | hardcoded | Iron Age 96%, Medieval 4% | ⬛ 0/13 (0%) | CRUSADER×6, PIKENEER×1, HORSEMAN_FAST×1 | LEGIONARY×14, HORSEMAN_SLOW×15, PIKENEER×16, HORSEMAN_FAST×17, HORSEMAN_FAST×17, HORSEMAN_SLOW×18, CRUSADER×9, LARGE_CART×20, LEGIONARY×18, HORSEMAN_FAST×20, LEGIONARY×22, HORSEMAN_FAST×24, THE_SWORDMASTER×26 |
| 🟥 | Iron Tide | hardcoded | Iron Age 95%, Medieval 5% | ⬛ 0/13 (0%) | THE_SWORDMASTER×2 | LEGIONARY×14, HORSEMAN_FAST×15, LARGE_CART×16, HORSEMAN_SLOW×16, LARGE_CART×17, HORSEMAN_FAST×18, LEGIONARY×18, THE_SWORDMASTER×19, PIKENEER×20, THE_SWORDMASTER×20, LARGE_CART×22, CRUSADER×12, THE_SWORDMASTER×26, LEGIONARY×28 |
| 🟥 | Quartermaster Force | hardcoded | Iron Age 92%, Bronze Age 8% | ⬛ 0/13 (0%) | PIKENEER×8, HORSEMAN_FAST×5 | THE_SWORDMASTER×16, LEGIONARY×17, HORSEMAN_SLOW×18, LARGE_CART×19, PIKENEER×20, LARGE_CART×21, LARGE_CART×22, LEGIONARY×16, PIKENEER×18, LARGE_CART×20, HORSEMAN_SLOW×22, HORSEMAN_SLOW×24, HORSEMAN_FAST×26, SWORDMAN×28, PIKENEER×28, LEGIONARY×28 |
| 🟩 | Desperate Looters | random | Iron Age 99%, Medieval 1% | 🟢 13/13 (100%) |  | KNIGHT×9, HORSEMAN_SLOW×13, HORSEMAN_FAST×8, LEGIONARY×13, HORSEMAN_SLOW×9, LARGE_CART×8, PIKENEER×11, HORSEMAN_FAST×11, HORSEMAN_FAST×15, THE_SWORDMASTER×999 |
| 🟩 | Desperate Looters | random | Iron Age 99%, Medieval 1% | 🟢 13/13 (100%) |  | KNIGHT×9, HORSEMAN_SLOW×13, HORSEMAN_FAST×8, LEGIONARY×13, HORSEMAN_SLOW×9, LARGE_CART×8, PIKENEER×11, HORSEMAN_FAST×11, HORSEMAN_FAST×15, THE_SWORDMASTER×999 |
| 🟩 | Restless Horde | random | Iron Age 99%, Bronze Age 1% | 🟢 13/13 (100%) |  | LARGE_CART×8, THE_SWORDMASTER×999, LEGIONARY×11, HORSEMAN_SLOW×11, PIKENEER×14, HORSEMAN_FAST×13, HORSEMAN_FAST×9, LEGIONARY×14, CHARIOT×8, LEGIONARY×11 |
| 🟥 | Drunken Raiders | random | Iron Age 99%, Medieval 1% | ⬛ 0/13 (0%) | CRUSADER×3, THE_SWORDMASTER×1 | PIKENEER×13, HORSEMAN_SLOW×13, THE_SWORDMASTER×999, HORSEMAN_FAST×11, LEGIONARY×9, SIEGE_RAM×15, PIKENEER×10, HORSEMAN_SLOW×13, PIKENEER×13, HORSEMAN_FAST×14 |
| 🟩 | Howling Savages | random | Iron Age 99%, Bronze Age 1% | 🟢 13/13 (100%) |  | LEGIONARY×9, LEGIONARY×14, HORSEMAN_FAST×13, LEGIONARY×15, LARGE_CART×12, PIKENEER×10, LEGIONARY×13, SWORDMAN×14, LEGIONARY×11, HORSEMAN_FAST×11, THE_SWORDMASTER×999 |
| 🟩 | Bored Mercenaries | random | Iron Age 70%, Bronze Age 30% | 🟢 13/13 (100%) |  | LARGE_CART×12, HORSEMAN_SLOW×14, CHARIOT×10, BOWMAN×13, LEGIONARY×13, PIKENEER×11, HORSEMAN_SLOW×13, LEGIONARY×9, BOWMAN×14, HORSEMAN_FAST×14 |
| 🟥 | Crude Invaders | random | Iron Age 99%, Medieval 1% | ⬛ 0/13 (0%) | HANDGUNNER×13 | PIKENEER×8, HORSEMAN_SLOW×12, HANDGUNNER×15, LARGE_CART×8, PIKENEER×8, LARGE_CART×12, LEGIONARY×11, HORSEMAN_FAST×13, HORSEMAN_FAST×9, THE_SWORDMASTER×999 |
| 🟥 | Crude Invaders | random | Iron Age 77%, Medieval 23% | ⬛ 0/13 (0%) | CRUSADER×5, SAMURAI×3 | SAMURAI×10, HORSEMAN_SLOW×12, LARGE_CART×8, PIKENEER×13, LARGE_CART×12, LEGIONARY×9, HORSEMAN_FAST×11, SIEGE_RAM×9 |
| 🟩 | Restless Horde | random | Iron Age 76%, Bronze Age 24% | 🟢 13/13 (100%) |  | HORSEMAN_FAST×14, HORSEMAN_SLOW×9, BOWMAN×9, PIKENEER×12, CHARIOT×13, HORSEMAN_SLOW×12, PIKENEER×12, LARGE_CART×12 |
| 🟩 | Restless Horde | random | Iron Age 96%, Bronze Age 4% | 🟢 13/13 (100%) |  | SWORDMAN×10, LARGE_CART×8, LARGE_CART×12, PIKENEER×12, THE_SWORDMASTER×999, BOWMAN×15, BOWMAN×13, LEGIONARY×12 |
| 🟩 | Angry Mob | random | Iron Age 95%, Bronze Age 3%, Medieval 2% | 🔴 1/13 (8%) | HANDGUNNER×7, SAMURAI×5 | HANDGUNNER×9, THE_SWORDMASTER×999, HORSEMAN_FAST×9, LARGE_CART×12, SAMURAI×13, SWORDMAN×14, BOWMAN×14, PIKENEER×8, LARGE_CART×8, SWORDMAN×10 |
| 🟥 | Lazy Raiders | random | Iron Age 97%, Bronze Age 2%, Medieval 1% | ⬛ 0/13 (0%) | CRUSADER×3, THE_SWORDMASTER×1 | LEGIONARY×12, LEGIONARY×14, LEGIONARY×9, LEGIONARY×9, BOWMAN×10, THE_SWORDMASTER×999, SWORDMAN×10, HORSEMAN_FAST×11, SIEGE_RAM×9, HORSEMAN_FAST×13 |
| 🟩 | Clumsy Attackers | random | Iron Age 99%, Medieval 1% | 🟠 5/13 (38%) | HANDGUNNER×8 | HORSEMAN_SLOW×12, HORSEMAN_FAST×13, PIKENEER×14, THE_SWORDMASTER×999, PIKENEER×8, LEGIONARY×13, HANDGUNNER×10, HORSEMAN_FAST×14, LEGIONARY×12 |
| 🟩 | Unlucky Raiders | random | Iron Age 99%, Bronze Age 1% | 🟢 13/13 (100%) |  | LEGIONARY×13, HORSEMAN_FAST×11, SWORDMAN×12, HORSEMAN_FAST×12, PIKENEER×9, PIKENEER×13, HORSEMAN_FAST×12, HORSEMAN_SLOW×9, PIKENEER×8, THE_SWORDMASTER×999 |
| 🟥 | Lazy Raiders | random | Iron Age 98%, Bronze Age 1%, Medieval 1% | ⬛ 0/13 (0%) | CRUSADER×3, THE_SWORDMASTER×1 | HORSEMAN_FAST×13, SWORDMAN×14, HORSEMAN_FAST×9, HORSEMAN_SLOW×8, THE_SWORDMASTER×999, LEGIONARY×8, CRUSADER×13, PIKENEER×10, PIKENEER×15 |
| 🟥 | Forgotten Warband | random | Iron Age 71%, Medieval 18%, Bronze Age 11% | ⬛ 0/13 (0%) | HANDGUNNER×13 | HORSEMAN_SLOW×8, HORSEMAN_FAST×11, LEGIONARY×15, LARGE_CART×8, HANDGUNNER×15, HORSEMAN_FAST×10, HORSEMAN_SLOW×8, BOWMAN×9 |
| 🟥 | Grumpy Marauders | random | Iron Age 98%, Medieval 2% | ⬛ 0/13 (0%) | HANDGUNNER×7, THE_SWORDMASTER×1 | LEGIONARY×9, PIKENEER×15, HORSEMAN_SLOW×11, HORSEMAN_FAST×10, HANDGUNNER×9, HORSEMAN_FAST×8, HORSEMAN_SLOW×11, THE_SWORDMASTER×999, CONDOTTERI×10, HORSEMAN_FAST×14 |
| 🟥 | Hungry Invaders | random | Iron Age 89%, Medieval 11% | ⬛ 0/13 (0%) | CRUSADER×5, SIEGE_RAM×1 | LARGE_CART×12, HORSEMAN_FAST×13, HORSEMAN_SLOW×12, SIEGE_RAM×12, LEGIONARY×10, LARGE_CART×8, LARGE_CART×12, LARGE_CART×12, PIKENEER×9, HORSEMAN_SLOW×10 |
| 🟩 | Clumsy Attackers | random | Iron Age 64%, Bronze Age 27%, Medieval 8% | 🟡 8/13 (62%) | SAMURAI×5 | HORSEMAN_SLOW×9, HORSEMAN_FAST×12, LEGIONARY×9, HORSEMAN_SLOW×14, LEGIONARY×11, CHARIOT×14, SAMURAI×9, LEGIONARY×13, BOWMAN×15 |
| 🟥 | Grumpy Marauders | random | Iron Age 78%, Medieval 13%, Bronze Age 10% | ⬛ 0/13 (0%) | CRUSADER×5, SIEGE_RAM×1 | LEGIONARY×12, SIEGE_RAM×12, HORSEMAN_FAST×12, HORSEMAN_FAST×12, LARGE_CART×16, HORSEMAN_SLOW×13, LARGE_CART×8, BOWMAN×9 |

#### S2 Baumhaus

| Tower Era Distribution (22 towers) | Towers |
|---|---|
| Bronze Age 64% (14), Iron Age 36% (8) | ARROW_TOWER×8, CATAPULTS×4, FIRE_TOWER×4, ARBELESTE_TOWER×4, BALLISTA_TOWER×2 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Iron Legion | hardcoded | Iron Age 100% | 🟢 16/16 (100%) |  | HORSEMAN_SLOW×10, HORSEMAN_SLOW×10, LEGIONARY×11, PIKENEER×12, HORSEMAN_SLOW×12, PIKENEER×13, LEGIONARY×15, HORSEMAN_FAST×16, THE_SWORDMASTER×18, LEGIONARY×20, LEGIONARY×22, PIKENEER×24 |
| 🟩 | Cavalry Strike | hardcoded | Iron Age 96%, Medieval 4% | 🟢 14/16 (88%) | KNIGHT×2 | LEGIONARY×14, PIKENEER×15, HORSEMAN_FAST×16, LARGE_CART×17, LEGIONARY×17, LEGIONARY×18, KNIGHT×9, PIKENEER×22, LARGE_CART×18, HORSEMAN_SLOW×20, HORSEMAN_SLOW×22, PIKENEER×24, LEGIONARY×26 |
| 🟩 | Legionary March | hardcoded | Iron Age 96%, Medieval 4% | 🔴 1/16 (6%) | CRUSADER×4, THE_SWORDMASTER×1 | LEGIONARY×14, HORSEMAN_SLOW×15, PIKENEER×16, HORSEMAN_FAST×17, HORSEMAN_FAST×17, HORSEMAN_SLOW×18, CRUSADER×9, LARGE_CART×20, LEGIONARY×18, HORSEMAN_FAST×20, LEGIONARY×22, HORSEMAN_FAST×24, THE_SWORDMASTER×26 |
| 🟥 | Iron Tide | hardcoded | Iron Age 95%, Medieval 5% | ⬛ 0/16 (0%) | CRUSADER×8 | LEGIONARY×14, HORSEMAN_FAST×15, LARGE_CART×16, HORSEMAN_SLOW×16, LARGE_CART×17, HORSEMAN_FAST×18, LEGIONARY×18, THE_SWORDMASTER×19, PIKENEER×20, THE_SWORDMASTER×20, LARGE_CART×22, CRUSADER×12, THE_SWORDMASTER×26, LEGIONARY×28 |
| 🟩 | Quartermaster Force | hardcoded | Iron Age 92%, Bronze Age 8% | 🟢 16/16 (100%) |  | THE_SWORDMASTER×16, LEGIONARY×17, HORSEMAN_SLOW×18, LARGE_CART×19, PIKENEER×20, LARGE_CART×21, LARGE_CART×22, LEGIONARY×16, PIKENEER×18, LARGE_CART×20, HORSEMAN_SLOW×22, HORSEMAN_SLOW×24, HORSEMAN_FAST×26, SWORDMAN×28, PIKENEER×28, LEGIONARY×28 |
| 🟩 | Desperate Looters | random | Iron Age 99%, Medieval 1% | 🟢 16/16 (100%) |  | KNIGHT×9, HORSEMAN_SLOW×13, HORSEMAN_FAST×8, LEGIONARY×13, HORSEMAN_SLOW×9, LARGE_CART×8, PIKENEER×11, HORSEMAN_FAST×11, HORSEMAN_FAST×15, THE_SWORDMASTER×999 |
| 🟩 | Desperate Looters | random | Iron Age 99%, Medieval 1% | 🟢 16/16 (100%) |  | KNIGHT×9, HORSEMAN_SLOW×13, HORSEMAN_FAST×8, LEGIONARY×13, HORSEMAN_SLOW×9, LARGE_CART×8, PIKENEER×11, HORSEMAN_FAST×11, HORSEMAN_FAST×15, THE_SWORDMASTER×999 |
| 🟩 | Restless Horde | random | Iron Age 99%, Bronze Age 1% | 🟢 16/16 (100%) |  | LARGE_CART×8, THE_SWORDMASTER×999, LEGIONARY×11, HORSEMAN_SLOW×11, PIKENEER×14, HORSEMAN_FAST×13, HORSEMAN_FAST×9, LEGIONARY×14, CHARIOT×8, LEGIONARY×11 |
| 🟥 | Drunken Raiders | random | Iron Age 99%, Medieval 1% | ⬛ 0/16 (0%) | CRUSADER×8 | PIKENEER×13, HORSEMAN_SLOW×13, THE_SWORDMASTER×999, HORSEMAN_FAST×11, LEGIONARY×9, SIEGE_RAM×15, PIKENEER×10, HORSEMAN_SLOW×13, PIKENEER×13, HORSEMAN_FAST×14 |
| 🟩 | Howling Savages | random | Iron Age 99%, Bronze Age 1% | 🟢 16/16 (100%) |  | LEGIONARY×9, LEGIONARY×14, HORSEMAN_FAST×13, LEGIONARY×15, LARGE_CART×12, PIKENEER×10, LEGIONARY×13, SWORDMAN×14, LEGIONARY×11, HORSEMAN_FAST×11, THE_SWORDMASTER×999 |
| 🟩 | Bored Mercenaries | random | Iron Age 70%, Bronze Age 30% | 🟢 16/16 (100%) |  | LARGE_CART×12, HORSEMAN_SLOW×14, CHARIOT×10, BOWMAN×13, LEGIONARY×13, PIKENEER×11, HORSEMAN_SLOW×13, LEGIONARY×9, BOWMAN×14, HORSEMAN_FAST×14 |
| 🟩 | Crude Invaders | random | Iron Age 99%, Medieval 1% | 🟠 4/16 (25%) | HANDGUNNER×12 | PIKENEER×8, HORSEMAN_SLOW×12, HANDGUNNER×15, LARGE_CART×8, PIKENEER×8, LARGE_CART×12, LEGIONARY×11, HORSEMAN_FAST×13, HORSEMAN_FAST×9, THE_SWORDMASTER×999 |
| 🟩 | Crude Invaders | random | Iron Age 77%, Medieval 23% | 🟠 4/16 (25%) | CRUSADER×5, SAMURAI×2 | SAMURAI×10, HORSEMAN_SLOW×12, LARGE_CART×8, PIKENEER×13, LARGE_CART×12, LEGIONARY×9, HORSEMAN_FAST×11, SIEGE_RAM×9 |
| 🟩 | Restless Horde | random | Iron Age 76%, Bronze Age 24% | 🟢 16/16 (100%) |  | HORSEMAN_FAST×14, HORSEMAN_SLOW×9, BOWMAN×9, PIKENEER×12, CHARIOT×13, HORSEMAN_SLOW×12, PIKENEER×12, LARGE_CART×12 |
| 🟩 | Restless Horde | random | Iron Age 96%, Bronze Age 4% | 🟢 16/16 (100%) |  | SWORDMAN×10, LARGE_CART×8, LARGE_CART×12, PIKENEER×12, THE_SWORDMASTER×999, BOWMAN×15, BOWMAN×13, LEGIONARY×12 |
| 🟩 | Angry Mob | random | Iron Age 95%, Bronze Age 3%, Medieval 2% | 🟠 5/16 (31%) | HANDGUNNER×6, SAMURAI×5 | HANDGUNNER×9, THE_SWORDMASTER×999, HORSEMAN_FAST×9, LARGE_CART×12, SAMURAI×13, SWORDMAN×14, BOWMAN×14, PIKENEER×8, LARGE_CART×8, SWORDMAN×10 |
| 🟩 | Lazy Raiders | random | Iron Age 97%, Bronze Age 2%, Medieval 1% | 🟠 6/16 (38%) | CRUSADER×5 | LEGIONARY×12, LEGIONARY×14, LEGIONARY×9, LEGIONARY×9, BOWMAN×10, THE_SWORDMASTER×999, SWORDMAN×10, HORSEMAN_FAST×11, SIEGE_RAM×9, HORSEMAN_FAST×13 |
| 🟩 | Clumsy Attackers | random | Iron Age 99%, Medieval 1% | 🟡 9/16 (56%) | HANDGUNNER×7 | HORSEMAN_SLOW×12, HORSEMAN_FAST×13, PIKENEER×14, THE_SWORDMASTER×999, PIKENEER×8, LEGIONARY×13, HANDGUNNER×10, HORSEMAN_FAST×14, LEGIONARY×12 |
| 🟩 | Unlucky Raiders | random | Iron Age 99%, Bronze Age 1% | 🟢 16/16 (100%) |  | LEGIONARY×13, HORSEMAN_FAST×11, SWORDMAN×12, HORSEMAN_FAST×12, PIKENEER×9, PIKENEER×13, HORSEMAN_FAST×12, HORSEMAN_SLOW×9, PIKENEER×8, THE_SWORDMASTER×999 |
| 🟥 | Lazy Raiders | random | Iron Age 98%, Bronze Age 1%, Medieval 1% | ⬛ 0/16 (0%) | CRUSADER×7, PIKENEER×3 | HORSEMAN_FAST×13, SWORDMAN×14, HORSEMAN_FAST×9, HORSEMAN_SLOW×8, THE_SWORDMASTER×999, LEGIONARY×8, CRUSADER×13, PIKENEER×10, PIKENEER×15 |
| 🟩 | Forgotten Warband | random | Iron Age 71%, Medieval 18%, Bronze Age 11% | 🔴 3/16 (19%) | HANDGUNNER×13 | HORSEMAN_SLOW×8, HORSEMAN_FAST×11, LEGIONARY×15, LARGE_CART×8, HANDGUNNER×15, HORSEMAN_FAST×10, HORSEMAN_SLOW×8, BOWMAN×9 |
| 🟥 | Grumpy Marauders | random | Iron Age 98%, Medieval 2% | ⬛ 0/16 (0%) | HANDGUNNER×6, CONDOTTERI×5 | LEGIONARY×9, PIKENEER×15, HORSEMAN_SLOW×11, HORSEMAN_FAST×10, HANDGUNNER×9, HORSEMAN_FAST×8, HORSEMAN_SLOW×11, THE_SWORDMASTER×999, CONDOTTERI×10, HORSEMAN_FAST×14 |
| 🟥 | Hungry Invaders | random | Iron Age 89%, Medieval 11% | ⬛ 0/16 (0%) | CRUSADER×8 | LARGE_CART×12, HORSEMAN_FAST×13, HORSEMAN_SLOW×12, SIEGE_RAM×12, LEGIONARY×10, LARGE_CART×8, LARGE_CART×12, LARGE_CART×12, PIKENEER×9, HORSEMAN_SLOW×10 |
| 🟩 | Clumsy Attackers | random | Iron Age 64%, Bronze Age 27%, Medieval 8% | 🟡 11/16 (69%) | SAMURAI×5 | HORSEMAN_SLOW×9, HORSEMAN_FAST×12, LEGIONARY×9, HORSEMAN_SLOW×14, LEGIONARY×11, CHARIOT×14, SAMURAI×9, LEGIONARY×13, BOWMAN×15 |
| 🟥 | Grumpy Marauders | random | Iron Age 78%, Medieval 13%, Bronze Age 10% | ⬛ 0/16 (0%) | CRUSADER×7, SIEGE_RAM×1 | LEGIONARY×12, SIEGE_RAM×12, HORSEMAN_FAST×12, HORSEMAN_FAST×12, LARGE_CART×16, HORSEMAN_SLOW×13, LARGE_CART×8, BOWMAN×9 |

#### Only Arbaleste

| Tower Era Distribution (33 towers) | Towers |
|---|---|
| Iron Age 100% (33) | ARBELESTE_TOWER×33 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Iron Legion | hardcoded | Iron Age 100% | 🟢 16/16 (100%) |  | HORSEMAN_SLOW×10, HORSEMAN_SLOW×10, LEGIONARY×11, PIKENEER×12, HORSEMAN_SLOW×12, PIKENEER×13, LEGIONARY×15, HORSEMAN_FAST×16, THE_SWORDMASTER×18, LEGIONARY×20, LEGIONARY×22, PIKENEER×24 |
| 🟩 | Cavalry Strike | hardcoded | Iron Age 96%, Medieval 4% | 🟢 16/16 (100%) |  | LEGIONARY×14, PIKENEER×15, HORSEMAN_FAST×16, LARGE_CART×17, LEGIONARY×17, LEGIONARY×18, KNIGHT×9, PIKENEER×22, LARGE_CART×18, HORSEMAN_SLOW×20, HORSEMAN_SLOW×22, PIKENEER×24, LEGIONARY×26 |
| 🟩 | Legionary March | hardcoded | Iron Age 96%, Medieval 4% | 🟢 16/16 (100%) |  | LEGIONARY×14, HORSEMAN_SLOW×15, PIKENEER×16, HORSEMAN_FAST×17, HORSEMAN_FAST×17, HORSEMAN_SLOW×18, CRUSADER×9, LARGE_CART×20, LEGIONARY×18, HORSEMAN_FAST×20, LEGIONARY×22, HORSEMAN_FAST×24, THE_SWORDMASTER×26 |
| 🟩 | Iron Tide | hardcoded | Iron Age 95%, Medieval 5% | 🟢 16/16 (100%) |  | LEGIONARY×14, HORSEMAN_FAST×15, LARGE_CART×16, HORSEMAN_SLOW×16, LARGE_CART×17, HORSEMAN_FAST×18, LEGIONARY×18, THE_SWORDMASTER×19, PIKENEER×20, THE_SWORDMASTER×20, LARGE_CART×22, CRUSADER×12, THE_SWORDMASTER×26, LEGIONARY×28 |
| 🟩 | Quartermaster Force | hardcoded | Iron Age 92%, Bronze Age 8% | 🟢 16/16 (100%) |  | THE_SWORDMASTER×16, LEGIONARY×17, HORSEMAN_SLOW×18, LARGE_CART×19, PIKENEER×20, LARGE_CART×21, LARGE_CART×22, LEGIONARY×16, PIKENEER×18, LARGE_CART×20, HORSEMAN_SLOW×22, HORSEMAN_SLOW×24, HORSEMAN_FAST×26, SWORDMAN×28, PIKENEER×28, LEGIONARY×28 |
| 🟩 | Desperate Looters | random | Iron Age 99%, Medieval 1% | 🟢 16/16 (100%) |  | KNIGHT×9, HORSEMAN_SLOW×13, HORSEMAN_FAST×8, LEGIONARY×13, HORSEMAN_SLOW×9, LARGE_CART×8, PIKENEER×11, HORSEMAN_FAST×11, HORSEMAN_FAST×15, THE_SWORDMASTER×999 |
| 🟩 | Desperate Looters | random | Iron Age 99%, Medieval 1% | 🟢 16/16 (100%) |  | KNIGHT×9, HORSEMAN_SLOW×13, HORSEMAN_FAST×8, LEGIONARY×13, HORSEMAN_SLOW×9, LARGE_CART×8, PIKENEER×11, HORSEMAN_FAST×11, HORSEMAN_FAST×15, THE_SWORDMASTER×999 |
| 🟩 | Restless Horde | random | Iron Age 99%, Bronze Age 1% | 🟢 16/16 (100%) |  | LARGE_CART×8, THE_SWORDMASTER×999, LEGIONARY×11, HORSEMAN_SLOW×11, PIKENEER×14, HORSEMAN_FAST×13, HORSEMAN_FAST×9, LEGIONARY×14, CHARIOT×8, LEGIONARY×11 |
| 🟩 | Drunken Raiders | random | Iron Age 99%, Medieval 1% | 🟡 12/16 (75%) | CRUSADER×2 | PIKENEER×13, HORSEMAN_SLOW×13, THE_SWORDMASTER×999, HORSEMAN_FAST×11, LEGIONARY×9, SIEGE_RAM×15, PIKENEER×10, HORSEMAN_SLOW×13, PIKENEER×13, HORSEMAN_FAST×14 |
| 🟩 | Howling Savages | random | Iron Age 99%, Bronze Age 1% | 🟢 16/16 (100%) |  | LEGIONARY×9, LEGIONARY×14, HORSEMAN_FAST×13, LEGIONARY×15, LARGE_CART×12, PIKENEER×10, LEGIONARY×13, SWORDMAN×14, LEGIONARY×11, HORSEMAN_FAST×11, THE_SWORDMASTER×999 |
| 🟩 | Bored Mercenaries | random | Iron Age 70%, Bronze Age 30% | 🟢 16/16 (100%) |  | LARGE_CART×12, HORSEMAN_SLOW×14, CHARIOT×10, BOWMAN×13, LEGIONARY×13, PIKENEER×11, HORSEMAN_SLOW×13, LEGIONARY×9, BOWMAN×14, HORSEMAN_FAST×14 |
| 🟩 | Crude Invaders | random | Iron Age 99%, Medieval 1% | 🟢 16/16 (100%) |  | PIKENEER×8, HORSEMAN_SLOW×12, HANDGUNNER×15, LARGE_CART×8, PIKENEER×8, LARGE_CART×12, LEGIONARY×11, HORSEMAN_FAST×13, HORSEMAN_FAST×9, THE_SWORDMASTER×999 |
| 🟩 | Crude Invaders | random | Iron Age 77%, Medieval 23% | 🟢 16/16 (100%) |  | SAMURAI×10, HORSEMAN_SLOW×12, LARGE_CART×8, PIKENEER×13, LARGE_CART×12, LEGIONARY×9, HORSEMAN_FAST×11, SIEGE_RAM×9 |
| 🟩 | Restless Horde | random | Iron Age 76%, Bronze Age 24% | 🟢 16/16 (100%) |  | HORSEMAN_FAST×14, HORSEMAN_SLOW×9, BOWMAN×9, PIKENEER×12, CHARIOT×13, HORSEMAN_SLOW×12, PIKENEER×12, LARGE_CART×12 |
| 🟩 | Restless Horde | random | Iron Age 96%, Bronze Age 4% | 🟢 16/16 (100%) |  | SWORDMAN×10, LARGE_CART×8, LARGE_CART×12, PIKENEER×12, THE_SWORDMASTER×999, BOWMAN×15, BOWMAN×13, LEGIONARY×12 |
| 🟩 | Angry Mob | random | Iron Age 95%, Bronze Age 3%, Medieval 2% | 🟢 16/16 (100%) |  | HANDGUNNER×9, THE_SWORDMASTER×999, HORSEMAN_FAST×9, LARGE_CART×12, SAMURAI×13, SWORDMAN×14, BOWMAN×14, PIKENEER×8, LARGE_CART×8, SWORDMAN×10 |
| 🟩 | Lazy Raiders | random | Iron Age 97%, Bronze Age 2%, Medieval 1% | 🟢 16/16 (100%) |  | LEGIONARY×12, LEGIONARY×14, LEGIONARY×9, LEGIONARY×9, BOWMAN×10, THE_SWORDMASTER×999, SWORDMAN×10, HORSEMAN_FAST×11, SIEGE_RAM×9, HORSEMAN_FAST×13 |
| 🟩 | Clumsy Attackers | random | Iron Age 99%, Medieval 1% | 🟢 16/16 (100%) |  | HORSEMAN_SLOW×12, HORSEMAN_FAST×13, PIKENEER×14, THE_SWORDMASTER×999, PIKENEER×8, LEGIONARY×13, HANDGUNNER×10, HORSEMAN_FAST×14, LEGIONARY×12 |
| 🟩 | Unlucky Raiders | random | Iron Age 99%, Bronze Age 1% | 🟢 16/16 (100%) |  | LEGIONARY×13, HORSEMAN_FAST×11, SWORDMAN×12, HORSEMAN_FAST×12, PIKENEER×9, PIKENEER×13, HORSEMAN_FAST×12, HORSEMAN_SLOW×9, PIKENEER×8, THE_SWORDMASTER×999 |
| 🟩 | Lazy Raiders | random | Iron Age 98%, Bronze Age 1%, Medieval 1% | 🟢 16/16 (100%) |  | HORSEMAN_FAST×13, SWORDMAN×14, HORSEMAN_FAST×9, HORSEMAN_SLOW×8, THE_SWORDMASTER×999, LEGIONARY×8, CRUSADER×13, PIKENEER×10, PIKENEER×15 |
| 🟩 | Forgotten Warband | random | Iron Age 71%, Medieval 18%, Bronze Age 11% | 🟢 16/16 (100%) |  | HORSEMAN_SLOW×8, HORSEMAN_FAST×11, LEGIONARY×15, LARGE_CART×8, HANDGUNNER×15, HORSEMAN_FAST×10, HORSEMAN_SLOW×8, BOWMAN×9 |
| 🟩 | Grumpy Marauders | random | Iron Age 98%, Medieval 2% | 🟢 16/16 (100%) |  | LEGIONARY×9, PIKENEER×15, HORSEMAN_SLOW×11, HORSEMAN_FAST×10, HANDGUNNER×9, HORSEMAN_FAST×8, HORSEMAN_SLOW×11, THE_SWORDMASTER×999, CONDOTTERI×10, HORSEMAN_FAST×14 |
| 🟩 | Hungry Invaders | random | Iron Age 89%, Medieval 11% | 🟢 14/16 (88%) | CRUSADER×1 | LARGE_CART×12, HORSEMAN_FAST×13, HORSEMAN_SLOW×12, SIEGE_RAM×12, LEGIONARY×10, LARGE_CART×8, LARGE_CART×12, LARGE_CART×12, PIKENEER×9, HORSEMAN_SLOW×10 |
| 🟩 | Clumsy Attackers | random | Iron Age 64%, Bronze Age 27%, Medieval 8% | 🟢 16/16 (100%) |  | HORSEMAN_SLOW×9, HORSEMAN_FAST×12, LEGIONARY×9, HORSEMAN_SLOW×14, LEGIONARY×11, CHARIOT×14, SAMURAI×9, LEGIONARY×13, BOWMAN×15 |
| 🟩 | Grumpy Marauders | random | Iron Age 78%, Medieval 13%, Bronze Age 10% | 🟡 8/16 (50%) | CRUSADER×4 | LEGIONARY×12, SIEGE_RAM×12, HORSEMAN_FAST×12, HORSEMAN_FAST×12, LARGE_CART×16, HORSEMAN_SLOW×13, LARGE_CART×8, BOWMAN×9 |

### Medieval

#### Early

| Tower Era Distribution (18 towers) | Towers |
|---|---|
| Medieval 61% (11), Bronze Age 22% (4), Iron Age 17% (3) | HEAVY_TOWER×5, TAR_TOWER×3, BOILING_OIL×3, FIRE_TOWER×2, BALLISTA_TOWER×2, ARBELESTE_TOWER×2, CATAPULTS×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟥 | Medieval Siege | hardcoded | Medieval 97%, Renaissance 3% | ⬛ 0/16 (0%) | NINJA×6, CRUSADER×4, CONDOTTERI×1, SAMURAI×1 | CRUSADER×12, CONDOTTERI×13, KNIGHT×14, SAMURAI×15, SIEGE_RAM×15, KNIGHT×16, CONDOTTERI×17, CRUSADER×18, NINJA×11, SIEGE_RAM×20, HANDGUNNER×22, HANDGUNNER×24, HANDGUNNER×26, SAMURAI×28, SIEGE_RAM×30, CONDOTTERI×34 |
| 🟥 | Knights' Charge | hardcoded | Medieval 100% | ⬛ 0/16 (0%) | SAMURAI×6, CRUSADER×5 | CRUSADER×16, SIEGE_RAM×17, CRUSADER×18, SIEGE_RAM×19, SAMURAI×20, KNIGHT×21, SAMURAI×22, CRUSADER×16, SAMURAI×18, KNIGHT×20, KNIGHT×22, CRUSADER×24, KNIGHT×26, KNIGHT×28, SIEGE_RAM×30, CONDOTTERI×32, HANDGUNNER×34, HANDGUNNER×32 |
| 🟥 | Crusader Host | hardcoded | Medieval 100% | ⬛ 0/16 (0%) | CRUSADER×5, SAMURAI×5, SIEGE_RAM×1 | CRUSADER×16, SIEGE_RAM×17, SAMURAI×18, SIEGE_RAM×19, SIEGE_RAM×20, SAMURAI×21, CRUSADER×22, KNIGHT×16, KNIGHT×18, CRUSADER×20, CRUSADER×22, HANDGUNNER×24, CONDOTTERI×26, SAMURAI×28, KNIGHT×30, CRUSADER×32, CRUSADER×34, KNIGHT×31 |
| 🟥 | Castle Assault | hardcoded | Medieval 100% | ⬛ 0/16 (0%) | SAMURAI×9, CRUSADER×4 | SAMURAI×16, KNIGHT×17, KNIGHT×18, KNIGHT×19, CRUSADER×20, CRUSADER×21, SIEGE_RAM×22, SAMURAI×16, CRUSADER×18, CRUSADER×20, CRUSADER×22, SAMURAI×24, SIEGE_RAM×26, CRUSADER×28, CRUSADER×30, SAMURAI×32, CONDOTTERI×34, SIEGE_RAM×32, KNIGHT×33 |
| 🟥 | Feudal Army | hardcoded | Medieval 100% | ⬛ 0/16 (0%) | CRUSADER×7, SIEGE_RAM×1 | KNIGHT×16, SIEGE_RAM×17, KNIGHT×18, SIEGE_RAM×19, CRUSADER×20, CRUSADER×21, CONDOTTERI×22, HANDGUNNER×16, CRUSADER×18, SIEGE_RAM×20, SIEGE_RAM×22, CRUSADER×24, KNIGHT×26, CONDOTTERI×28, KNIGHT×30, CONDOTTERI×32, CONDOTTERI×34, CRUSADER×31, CRUSADER×33 |
| 🟥 | Holy Crusade | hardcoded | Medieval 82%, Iron Age 15%, Renaissance 3% | ⬛ 0/16 (0%) | CONDOTTERI×6, HANDGUNNER×4 | SAMURAI×16, CONDOTTERI×17, HANDGUNNER×17, KNIGHT×18, THE_SWORDMASTER×19, CONDOTTERI×19, CONDOTTERI×20, HANDGUNNER×21, KNIGHT×21, LARGE_CART×22, LEGIONARY×23, MUSKETEER×12, HANDGUNNER×24, SIEGE_RAM×28, SIEGE_RAM×30, KNIGHT×32, HANDGUNNER×31, CRUSADER×28, CRUSADER×34 |
| 🟥 | Grumpy Marauders | random | Medieval 92%, Renaissance 8% | ⬛ 0/16 (0%) | HANDGUNNER×14, SAMURAI×2 | CONDOTTERI×13, SAMURAI×15, HANDGUNNER×18, SAMURAI×12, HANDGUNNER×14, DRAGOONER×13, KNIGHT×12, KNIGHT×15, CRUSADER×14, SAMURAI×13, CRUSADER×14, CONDOTTERI×14 |
| 🟥 | Grumpy Marauders | random | Medieval 92%, Renaissance 8% | ⬛ 0/16 (0%) | HANDGUNNER×14, SAMURAI×2 | CONDOTTERI×13, SAMURAI×15, HANDGUNNER×18, SAMURAI×12, HANDGUNNER×14, DRAGOONER×13, KNIGHT×12, KNIGHT×15, CRUSADER×14, SAMURAI×13, CRUSADER×14, CONDOTTERI×14 |
| 🟥 | Howling Savages | random | Iron Age 85%, Medieval 15% | ⬛ 0/16 (0%) | CRUSADER×7, SAMURAI×2 | KNIGHT×15, SIEGE_RAM×15, SAMURAI×18, THE_SWORDMASTER×999, KNIGHT×12, SIEGE_RAM×18, CRUSADER×17, CRUSADER×17, SAMURAI×16, CRUSADER×12, CRUSADER×16, HANDGUNNER×15 |
| 🟥 | Shrieking Horde | random | Medieval 90%, Renaissance 10% | ⬛ 0/16 (0%) | CRUSADER×6, NINJA×2, CONDOTTERI×1 | CRUSADER×17, SIEGE_RAM×12, NINJA×18, CONDOTTERI×15, HANDGUNNER×13, CRUSADER×16, SAMURAI×17, CRUSADER×13, SAMURAI×14, CONDOTTERI×13, CRUSADER×16, CONDOTTERI×15 |
| 🟥 | Crude Invaders | random | Medieval 93%, Iron Age 7% | ⬛ 0/16 (0%) | HANDGUNNER×8, SAMURAI×6, CONDOTTERI×1 | SAMURAI×16, CONDOTTERI×16, CONDOTTERI×13, HANDGUNNER×18, SAMURAI×13, SIEGE_RAM×12, HANDGUNNER×15, CONDOTTERI×14, HORSEMAN_FAST×14, SAMURAI×16, CONDOTTERI×15, HANDGUNNER×15, CRUSADER×13 |
| 🟥 | Reckless Looters | random | Medieval 75%, Iron Age 25% | ⬛ 0/16 (0%) | CRUSADER×7, CONDOTTERI×1 | KNIGHT×18, KNIGHT×15, PIKENEER×17, CONDOTTERI×16, SIEGE_RAM×15, CRUSADER×14, CONDOTTERI×13, HORSEMAN_SLOW×13, KNIGHT×15, SIEGE_RAM×12, SAMURAI×17, PIKENEER×14 |
| 🟥 | Howling Savages | random | Medieval 90%, Renaissance 10% | ⬛ 0/16 (0%) | HANDGUNNER×12, SAMURAI×2, CRUSADER×1 | CRUSADER×14, SAMURAI×11, KNIGHT×18, KNIGHT×15, HANDGUNNER×18, CRUSADER×11, HANDGUNNER×13, SAMURAI×14, KNIGHT×18, CONDOTTERI×15, CARGO×16 |
| 🟥 | Unlucky Raiders | random | Medieval 80%, Renaissance 20% | ⬛ 0/16 (0%) | CRUSADER×4, CONDOTTERI×3, SAMURAI×2 | CRUSADER×16, SIEGE_RAM×12, CONDOTTERI×13, KNIGHT×15, SAMURAI×13, CONDOTTERI×15, CARGO×12, SAMURAI×14, MUSKETEER×13 |
| 🟩 | Frenzied Pillagers | random | Medieval 80%, Iron Age 20% | 🟡 9/16 (56%) | HANDGUNNER×7 | CRUSADER×15, PIKENEER×12, PIKENEER×15, SAMURAI×17, KNIGHT×15, CONDOTTERI×15, KNIGHT×12, HANDGUNNER×16, CRUSADER×15 |
| 🟥 | Hungry Invaders | random | Iron Age 93%, Medieval 7% | ⬛ 0/16 (0%) | HANDGUNNER×6, CRUSADER×4, CONDOTTERI×1 | HANDGUNNER×12, SIEGE_RAM×12, CONDOTTERI×16, HANDGUNNER×13, THE_SWORDMASTER×999, CONDOTTERI×13, LARGE_CART×16, SIEGE_RAM×15, HORSEMAN_FAST×15 |
| 🟥 | Angry Mob | random | Iron Age 90%, Medieval 7%, Renaissance 3% | ⬛ 0/16 (0%) | MUSKETEER×10, DRAGOONER×2, CRUSADER×1 | SAMURAI×12, CRUSADER×11, SAMURAI×14, HORSEMAN_SLOW×17, THE_SWORDMASTER×999, LARGE_CART×12, CONDOTTERI×14, CRUSADER×14, MUSKETEER×16, DRAGOONER×15, HANDGUNNER×17 |
| 🟥 | Grumpy Marauders | random | Medieval 72%, Iron Age 19%, Renaissance 9% | ⬛ 0/16 (0%) | MUSKETEER×9, SAMURAI×3, CONDOTTERI×2 | CONDOTTERI×16, MUSKETEER×14, SAMURAI×14, KNIGHT×15, SIEGE_RAM×18, SIEGE_RAM×12, HANDGUNNER×14, SIEGE_RAM×15, CRUSADER×12, HORSEMAN_FAST×15, PIKENEER×15 |
| 🟥 | Muddy Marauders | random | Medieval 91%, Renaissance 9% | ⬛ 0/16 (0%) | CRUSADER×4, MUSKETEER×4, CARGO×1 | CONDOTTERI×11, SIEGE_RAM×15, SIEGE_RAM×15, CARGO×12, CONDOTTERI×18, HANDGUNNER×12, KNIGHT×12, CRUSADER×16, SIEGE_RAM×15, HANDGUNNER×13 |
| 🟥 | Restless Horde | random | Medieval 89%, Iron Age 11% | ⬛ 0/16 (0%) | CRUSADER×4, HANDGUNNER×3, SAMURAI×2, SIEGE_RAM×1 | HANDGUNNER×16, SAMURAI×15, SIEGE_RAM×15, CRUSADER×15, PIKENEER×16, CRUSADER×12, SIEGE_RAM×12, SIEGE_RAM×12, SAMURAI×15, CRUSADER×11, CONDOTTERI×13 |
| 🟥 | Noisy Barbarians | random | Medieval 82%, Renaissance 10%, Iron Age 8% | ⬛ 0/16 (0%) | HANDGUNNER×6, SAMURAI×4, CRUSADER×3 | CRUSADER×12, HANDGUNNER×14, SAMURAI×14, LARGE_CART×12, HANDGUNNER×11, SIEGE_RAM×12, CRUSADER×16, SAMURAI×12, SAMURAI×16, CRUSADER×18, CARGO×16 |
| 🟥 | Savage Rabble | random | Iron Age 89%, Medieval 10%, Renaissance 1% | ⬛ 0/16 (0%) | HANDGUNNER×6, MUSKETEER×2, CRUSADER×2, SAMURAI×2, CONDOTTERI×1 | CONDOTTERI×13, HANDGUNNER×18, KNIGHT×12, KNIGHT×12, THE_SWORDMASTER×999, MUSKETEER×11, SIEGE_RAM×18, SAMURAI×14, SAMURAI×13, KNIGHT×12 |
| 🟥 | Blundering Invaders | random | Medieval 82%, Renaissance 18% | ⬛ 0/16 (0%) | MUSKETEER×6, CRUSADER×4, SAMURAI×2 | MUSKETEER×17, SIEGE_RAM×12, CRUSADER×13, CRUSADER×16, SAMURAI×15, HANDGUNNER×14, HANDGUNNER×13, DRAGOONER×15, SAMURAI×17, SAMURAI×13, CRUSADER×18, KNIGHT×15 |
| 🟥 | Wandering Pillagers | random | Renaissance 87%, Medieval 13% | ⬛ 0/16 (0%) | SAMURAI×3, CONDOTTERI×2, CRUSADER×1, THE_KING×1 | CONDOTTERI×15, THE_KING×999, SIEGE_RAM×12, CONDOTTERI×13, SAMURAI×16, CONDOTTERI×13, CRUSADER×12, SIEGE_RAM×15, KNIGHT×15, KNIGHT×12, CONDOTTERI×17, SAMURAI×11 |
| 🟥 | Noisy Barbarians | random | Medieval 72%, Iron Age 19%, Renaissance 9% | ⬛ 0/16 (0%) | CRUSADER×4, DRAGOONER×4, SAMURAI×1 | SIEGE_RAM×15, KNIGHT×12, KNIGHT×18, SAMURAI×15, LARGE_CART×16, CRUSADER×18, DRAGOONER×13, SIEGE_RAM×12, SIEGE_RAM×15, HORSEMAN_FAST×12 |
| 🟥 | Noisy Barbarians | random | Medieval 76%, Renaissance 12%, Iron Age 12% | ⬛ 0/16 (0%) | MUSKETEER×8, CRUSADER×4 | SAMURAI×15, SAMURAI×15, SIEGE_RAM×15, CRUSADER×12, CARGO×16, CONDOTTERI×12, LEGIONARY×16, CONDOTTERI×18, KNIGHT×15 |

#### Mixed Early

| Tower Era Distribution (27 towers) | Towers |
|---|---|
| Medieval 48% (13), Iron Age 22% (6), Bronze Age 22% (6), Neolithic 7% (2) | TAR_TOWER×7, HEAVY_TOWER×6, CATAPULTS×4, BALLISTA_TOWER×3, DOUBLE_SLING_TOWER×2, ARBELESTE_TOWER×2, ARROW_TOWER×2, FIRE_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟥 | Medieval Siege | hardcoded | Medieval 97%, Renaissance 3% | ⬛ 0/13 (0%) | CRUSADER×4, CONDOTTERI×2, SAMURAI×2 | CRUSADER×12, CONDOTTERI×13, KNIGHT×14, SAMURAI×15, SIEGE_RAM×15, KNIGHT×16, CONDOTTERI×17, CRUSADER×18, NINJA×11, SIEGE_RAM×20, HANDGUNNER×22, HANDGUNNER×24, HANDGUNNER×26, SAMURAI×28, SIEGE_RAM×30, CONDOTTERI×34 |
| 🟥 | Knights' Charge | hardcoded | Medieval 100% | ⬛ 0/13 (0%) | CRUSADER×7 | CRUSADER×16, SIEGE_RAM×17, CRUSADER×18, SIEGE_RAM×19, SAMURAI×20, KNIGHT×21, SAMURAI×22, CRUSADER×16, SAMURAI×18, KNIGHT×20, KNIGHT×22, CRUSADER×24, KNIGHT×26, KNIGHT×28, SIEGE_RAM×30, CONDOTTERI×32, HANDGUNNER×34, HANDGUNNER×32 |
| 🟥 | Crusader Host | hardcoded | Medieval 100% | ⬛ 0/13 (0%) | SAMURAI×5, CRUSADER×4 | CRUSADER×16, SIEGE_RAM×17, SAMURAI×18, SIEGE_RAM×19, SIEGE_RAM×20, SAMURAI×21, CRUSADER×22, KNIGHT×16, KNIGHT×18, CRUSADER×20, CRUSADER×22, HANDGUNNER×24, CONDOTTERI×26, SAMURAI×28, KNIGHT×30, CRUSADER×32, CRUSADER×34, KNIGHT×31 |
| 🟥 | Castle Assault | hardcoded | Medieval 100% | ⬛ 0/13 (0%) | CRUSADER×5, KNIGHT×3 | SAMURAI×16, KNIGHT×17, KNIGHT×18, KNIGHT×19, CRUSADER×20, CRUSADER×21, SIEGE_RAM×22, SAMURAI×16, CRUSADER×18, CRUSADER×20, CRUSADER×22, SAMURAI×24, SIEGE_RAM×26, CRUSADER×28, CRUSADER×30, SAMURAI×32, CONDOTTERI×34, SIEGE_RAM×32, KNIGHT×33 |
| 🟥 | Feudal Army | hardcoded | Medieval 100% | ⬛ 0/13 (0%) | CRUSADER×6, KNIGHT×1 | KNIGHT×16, SIEGE_RAM×17, KNIGHT×18, SIEGE_RAM×19, CRUSADER×20, CRUSADER×21, CONDOTTERI×22, HANDGUNNER×16, CRUSADER×18, SIEGE_RAM×20, SIEGE_RAM×22, CRUSADER×24, KNIGHT×26, CONDOTTERI×28, KNIGHT×30, CONDOTTERI×32, CONDOTTERI×34, CRUSADER×31, CRUSADER×33 |
| 🟥 | Holy Crusade | hardcoded | Medieval 82%, Iron Age 15%, Renaissance 3% | ⬛ 0/13 (0%) | HANDGUNNER×5, CONDOTTERI×4 | SAMURAI×16, CONDOTTERI×17, HANDGUNNER×17, KNIGHT×18, THE_SWORDMASTER×19, CONDOTTERI×19, CONDOTTERI×20, HANDGUNNER×21, KNIGHT×21, LARGE_CART×22, LEGIONARY×23, MUSKETEER×12, HANDGUNNER×24, SIEGE_RAM×28, SIEGE_RAM×30, KNIGHT×32, HANDGUNNER×31, CRUSADER×28, CRUSADER×34 |
| 🟥 | Grumpy Marauders | random | Medieval 92%, Renaissance 8% | ⬛ 0/13 (0%) | HANDGUNNER×8, SAMURAI×5 | CONDOTTERI×13, SAMURAI×15, HANDGUNNER×18, SAMURAI×12, HANDGUNNER×14, DRAGOONER×13, KNIGHT×12, KNIGHT×15, CRUSADER×14, SAMURAI×13, CRUSADER×14, CONDOTTERI×14 |
| 🟥 | Grumpy Marauders | random | Medieval 92%, Renaissance 8% | ⬛ 0/13 (0%) | HANDGUNNER×8, SAMURAI×5 | CONDOTTERI×13, SAMURAI×15, HANDGUNNER×18, SAMURAI×12, HANDGUNNER×14, DRAGOONER×13, KNIGHT×12, KNIGHT×15, CRUSADER×14, SAMURAI×13, CRUSADER×14, CONDOTTERI×14 |
| 🟥 | Howling Savages | random | Iron Age 85%, Medieval 15% | ⬛ 0/13 (0%) | CRUSADER×5, SAMURAI×2, KNIGHT×1 | KNIGHT×15, SIEGE_RAM×15, SAMURAI×18, THE_SWORDMASTER×999, KNIGHT×12, SIEGE_RAM×18, CRUSADER×17, CRUSADER×17, SAMURAI×16, CRUSADER×12, CRUSADER×16, HANDGUNNER×15 |
| 🟥 | Shrieking Horde | random | Medieval 90%, Renaissance 10% | ⬛ 0/13 (0%) | NINJA×5, CRUSADER×4 | CRUSADER×17, SIEGE_RAM×12, NINJA×18, CONDOTTERI×15, HANDGUNNER×13, CRUSADER×16, SAMURAI×17, CRUSADER×13, SAMURAI×14, CONDOTTERI×13, CRUSADER×16, CONDOTTERI×15 |
| 🟥 | Crude Invaders | random | Medieval 93%, Iron Age 7% | ⬛ 0/13 (0%) | CONDOTTERI×6, HANDGUNNER×1 | SAMURAI×16, CONDOTTERI×16, CONDOTTERI×13, HANDGUNNER×18, SAMURAI×13, SIEGE_RAM×12, HANDGUNNER×15, CONDOTTERI×14, HORSEMAN_FAST×14, SAMURAI×16, CONDOTTERI×15, HANDGUNNER×15, CRUSADER×13 |
| 🟥 | Reckless Looters | random | Medieval 75%, Iron Age 25% | ⬛ 0/13 (0%) | CRUSADER×5, SIEGE_RAM×1 | KNIGHT×18, KNIGHT×15, PIKENEER×17, CONDOTTERI×16, SIEGE_RAM×15, CRUSADER×14, CONDOTTERI×13, HORSEMAN_SLOW×13, KNIGHT×15, SIEGE_RAM×12, SAMURAI×17, PIKENEER×14 |
| 🟥 | Howling Savages | random | Medieval 90%, Renaissance 10% | ⬛ 0/13 (0%) | HANDGUNNER×9, KNIGHT×3, SAMURAI×1 | CRUSADER×14, SAMURAI×11, KNIGHT×18, KNIGHT×15, HANDGUNNER×18, CRUSADER×11, HANDGUNNER×13, SAMURAI×14, KNIGHT×18, CONDOTTERI×15, CARGO×16 |
| 🟥 | Unlucky Raiders | random | Medieval 80%, Renaissance 20% | ⬛ 0/13 (0%) | CRUSADER×5, CONDOTTERI×2 | CRUSADER×16, SIEGE_RAM×12, CONDOTTERI×13, KNIGHT×15, SAMURAI×13, CONDOTTERI×15, CARGO×12, SAMURAI×14, MUSKETEER×13 |
| 🟥 | Frenzied Pillagers | random | Medieval 80%, Iron Age 20% | ⬛ 0/13 (0%) | HANDGUNNER×5, CONDOTTERI×4 | CRUSADER×15, PIKENEER×12, PIKENEER×15, SAMURAI×17, KNIGHT×15, CONDOTTERI×15, KNIGHT×12, HANDGUNNER×16, CRUSADER×15 |
| 🟥 | Hungry Invaders | random | Iron Age 93%, Medieval 7% | ⬛ 0/13 (0%) | CRUSADER×6, CONDOTTERI×1 | HANDGUNNER×12, SIEGE_RAM×12, CONDOTTERI×16, HANDGUNNER×13, THE_SWORDMASTER×999, CONDOTTERI×13, LARGE_CART×16, SIEGE_RAM×15, HORSEMAN_FAST×15 |
| 🟥 | Angry Mob | random | Iron Age 90%, Medieval 7%, Renaissance 3% | ⬛ 0/13 (0%) | MUSKETEER×6, CRUSADER×3, SAMURAI×1 | SAMURAI×12, CRUSADER×11, SAMURAI×14, HORSEMAN_SLOW×17, THE_SWORDMASTER×999, LARGE_CART×12, CONDOTTERI×14, CRUSADER×14, MUSKETEER×16, DRAGOONER×15, HANDGUNNER×17 |
| 🟥 | Grumpy Marauders | random | Medieval 72%, Iron Age 19%, Renaissance 9% | ⬛ 0/13 (0%) | MUSKETEER×6, SAMURAI×4, CONDOTTERI×2 | CONDOTTERI×16, MUSKETEER×14, SAMURAI×14, KNIGHT×15, SIEGE_RAM×18, SIEGE_RAM×12, HANDGUNNER×14, SIEGE_RAM×15, CRUSADER×12, HORSEMAN_FAST×15, PIKENEER×15 |
| 🟥 | Muddy Marauders | random | Medieval 91%, Renaissance 9% | ⬛ 0/13 (0%) | CRUSADER×5, MUSKETEER×3 | CONDOTTERI×11, SIEGE_RAM×15, SIEGE_RAM×15, CARGO×12, CONDOTTERI×18, HANDGUNNER×12, KNIGHT×12, CRUSADER×16, SIEGE_RAM×15, HANDGUNNER×13 |
| 🟥 | Restless Horde | random | Medieval 89%, Iron Age 11% | ⬛ 0/13 (0%) | HANDGUNNER×4, CRUSADER×4, SAMURAI×1 | HANDGUNNER×16, SAMURAI×15, SIEGE_RAM×15, CRUSADER×15, PIKENEER×16, CRUSADER×12, SIEGE_RAM×12, SIEGE_RAM×12, SAMURAI×15, CRUSADER×11, CONDOTTERI×13 |
| 🟥 | Noisy Barbarians | random | Medieval 82%, Renaissance 10%, Iron Age 8% | ⬛ 0/13 (0%) | HANDGUNNER×9, CRUSADER×2 | CRUSADER×12, HANDGUNNER×14, SAMURAI×14, LARGE_CART×12, HANDGUNNER×11, SIEGE_RAM×12, CRUSADER×16, SAMURAI×12, SAMURAI×16, CRUSADER×18, CARGO×16 |
| 🟥 | Savage Rabble | random | Iron Age 89%, Medieval 10%, Renaissance 1% | ⬛ 0/13 (0%) | HANDGUNNER×9, CONDOTTERI×2 | CONDOTTERI×13, HANDGUNNER×18, KNIGHT×12, KNIGHT×12, THE_SWORDMASTER×999, MUSKETEER×11, SIEGE_RAM×18, SAMURAI×14, SAMURAI×13, KNIGHT×12 |
| 🟥 | Blundering Invaders | random | Medieval 82%, Renaissance 18% | ⬛ 0/13 (0%) | MUSKETEER×8, CRUSADER×3 | MUSKETEER×17, SIEGE_RAM×12, CRUSADER×13, CRUSADER×16, SAMURAI×15, HANDGUNNER×14, HANDGUNNER×13, DRAGOONER×15, SAMURAI×17, SAMURAI×13, CRUSADER×18, KNIGHT×15 |
| 🟥 | Wandering Pillagers | random | Renaissance 87%, Medieval 13% | ⬛ 0/13 (0%) | SAMURAI×5, CONDOTTERI×2, CRUSADER×2 | CONDOTTERI×15, THE_KING×999, SIEGE_RAM×12, CONDOTTERI×13, SAMURAI×16, CONDOTTERI×13, CRUSADER×12, SIEGE_RAM×15, KNIGHT×15, KNIGHT×12, CONDOTTERI×17, SAMURAI×11 |
| 🟥 | Noisy Barbarians | random | Medieval 72%, Iron Age 19%, Renaissance 9% | ⬛ 0/13 (0%) | SAMURAI×4, CRUSADER×3, KNIGHT×3 | SIEGE_RAM×15, KNIGHT×12, KNIGHT×18, SAMURAI×15, LARGE_CART×16, CRUSADER×18, DRAGOONER×13, SIEGE_RAM×12, SIEGE_RAM×15, HORSEMAN_FAST×12 |
| 🟥 | Noisy Barbarians | random | Medieval 76%, Renaissance 12%, Iron Age 12% | ⬛ 0/13 (0%) | CRUSADER×5, MUSKETEER×3 | SAMURAI×15, SAMURAI×15, SIEGE_RAM×15, CRUSADER×12, CARGO×16, CONDOTTERI×12, LEGIONARY×16, CONDOTTERI×18, KNIGHT×15 |

#### Full Heavy

| Tower Era Distribution (32 towers) | Towers |
|---|---|
| Medieval 100% (32) | HEAVY_TOWER×29, BOILING_OIL×2, TAR_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟥 | Medieval Siege | hardcoded | Medieval 97%, Renaissance 3% | ⬛ 0/23 (0%) | HANDGUNNER×13, CRUSADER×4, SAMURAI×2 | CRUSADER×12, CONDOTTERI×13, KNIGHT×14, SAMURAI×15, SIEGE_RAM×15, KNIGHT×16, CONDOTTERI×17, CRUSADER×18, NINJA×11, SIEGE_RAM×20, HANDGUNNER×22, HANDGUNNER×24, HANDGUNNER×26, SAMURAI×28, SIEGE_RAM×30, CONDOTTERI×34 |
| 🟥 | Knights' Charge | hardcoded | Medieval 100% | ⬛ 0/23 (0%) | CRUSADER×8, CONDOTTERI×3, HANDGUNNER×2 | CRUSADER×16, SIEGE_RAM×17, CRUSADER×18, SIEGE_RAM×19, SAMURAI×20, KNIGHT×21, SAMURAI×22, CRUSADER×16, SAMURAI×18, KNIGHT×20, KNIGHT×22, CRUSADER×24, KNIGHT×26, KNIGHT×28, SIEGE_RAM×30, CONDOTTERI×32, HANDGUNNER×34, HANDGUNNER×32 |
| 🟩 | Crusader Host | hardcoded | Medieval 100% | 🔴 1/23 (4%) | HANDGUNNER×9, CRUSADER×6, SAMURAI×1 | CRUSADER×16, SIEGE_RAM×17, SAMURAI×18, SIEGE_RAM×19, SIEGE_RAM×20, SAMURAI×21, CRUSADER×22, KNIGHT×16, KNIGHT×18, CRUSADER×20, CRUSADER×22, HANDGUNNER×24, CONDOTTERI×26, SAMURAI×28, KNIGHT×30, CRUSADER×32, CRUSADER×34, KNIGHT×31 |
| 🟥 | Castle Assault | hardcoded | Medieval 100% | ⬛ 0/23 (0%) | CRUSADER×12 | SAMURAI×16, KNIGHT×17, KNIGHT×18, KNIGHT×19, CRUSADER×20, CRUSADER×21, SIEGE_RAM×22, SAMURAI×16, CRUSADER×18, CRUSADER×20, CRUSADER×22, SAMURAI×24, SIEGE_RAM×26, CRUSADER×28, CRUSADER×30, SAMURAI×32, CONDOTTERI×34, SIEGE_RAM×32, KNIGHT×33 |
| 🟥 | Feudal Army | hardcoded | Medieval 100% | ⬛ 0/23 (0%) | HANDGUNNER×9, CONDOTTERI×7 | KNIGHT×16, SIEGE_RAM×17, KNIGHT×18, SIEGE_RAM×19, CRUSADER×20, CRUSADER×21, CONDOTTERI×22, HANDGUNNER×16, CRUSADER×18, SIEGE_RAM×20, SIEGE_RAM×22, CRUSADER×24, KNIGHT×26, CONDOTTERI×28, KNIGHT×30, CONDOTTERI×32, CONDOTTERI×34, CRUSADER×31, CRUSADER×33 |
| 🟥 | Holy Crusade | hardcoded | Medieval 82%, Iron Age 15%, Renaissance 3% | ⬛ 0/23 (0%) | CRUSADER×9, HANDGUNNER×5, CONDOTTERI×1 | SAMURAI×16, CONDOTTERI×17, HANDGUNNER×17, KNIGHT×18, THE_SWORDMASTER×19, CONDOTTERI×19, CONDOTTERI×20, HANDGUNNER×21, KNIGHT×21, LARGE_CART×22, LEGIONARY×23, MUSKETEER×12, HANDGUNNER×24, SIEGE_RAM×28, SIEGE_RAM×30, KNIGHT×32, HANDGUNNER×31, CRUSADER×28, CRUSADER×34 |
| 🟩 | Grumpy Marauders | random | Medieval 92%, Renaissance 8% | 🟢 23/23 (100%) |  | CONDOTTERI×13, SAMURAI×15, HANDGUNNER×18, SAMURAI×12, HANDGUNNER×14, DRAGOONER×13, KNIGHT×12, KNIGHT×15, CRUSADER×14, SAMURAI×13, CRUSADER×14, CONDOTTERI×14 |
| 🟩 | Grumpy Marauders | random | Medieval 92%, Renaissance 8% | 🟢 23/23 (100%) |  | CONDOTTERI×13, SAMURAI×15, HANDGUNNER×18, SAMURAI×12, HANDGUNNER×14, DRAGOONER×13, KNIGHT×12, KNIGHT×15, CRUSADER×14, SAMURAI×13, CRUSADER×14, CONDOTTERI×14 |
| 🟩 | Howling Savages | random | Iron Age 85%, Medieval 15% | 🟢 23/23 (100%) |  | KNIGHT×15, SIEGE_RAM×15, SAMURAI×18, THE_SWORDMASTER×999, KNIGHT×12, SIEGE_RAM×18, CRUSADER×17, CRUSADER×17, SAMURAI×16, CRUSADER×12, CRUSADER×16, HANDGUNNER×15 |
| 🟩 | Shrieking Horde | random | Medieval 90%, Renaissance 10% | 🟢 23/23 (100%) |  | CRUSADER×17, SIEGE_RAM×12, NINJA×18, CONDOTTERI×15, HANDGUNNER×13, CRUSADER×16, SAMURAI×17, CRUSADER×13, SAMURAI×14, CONDOTTERI×13, CRUSADER×16, CONDOTTERI×15 |
| 🟩 | Crude Invaders | random | Medieval 93%, Iron Age 7% | 🟢 23/23 (100%) |  | SAMURAI×16, CONDOTTERI×16, CONDOTTERI×13, HANDGUNNER×18, SAMURAI×13, SIEGE_RAM×12, HANDGUNNER×15, CONDOTTERI×14, HORSEMAN_FAST×14, SAMURAI×16, CONDOTTERI×15, HANDGUNNER×15, CRUSADER×13 |
| 🟩 | Reckless Looters | random | Medieval 75%, Iron Age 25% | 🟢 23/23 (100%) |  | KNIGHT×18, KNIGHT×15, PIKENEER×17, CONDOTTERI×16, SIEGE_RAM×15, CRUSADER×14, CONDOTTERI×13, HORSEMAN_SLOW×13, KNIGHT×15, SIEGE_RAM×12, SAMURAI×17, PIKENEER×14 |
| 🟩 | Howling Savages | random | Medieval 90%, Renaissance 10% | 🟢 21/23 (91%) | MUSKETEER×2 | CRUSADER×14, SAMURAI×11, KNIGHT×18, KNIGHT×15, HANDGUNNER×18, CRUSADER×11, HANDGUNNER×13, SAMURAI×14, KNIGHT×18, CONDOTTERI×15, CARGO×16 |
| 🟩 | Unlucky Raiders | random | Medieval 80%, Renaissance 20% | 🟢 23/23 (100%) |  | CRUSADER×16, SIEGE_RAM×12, CONDOTTERI×13, KNIGHT×15, SAMURAI×13, CONDOTTERI×15, CARGO×12, SAMURAI×14, MUSKETEER×13 |
| 🟩 | Frenzied Pillagers | random | Medieval 80%, Iron Age 20% | 🟢 23/23 (100%) |  | CRUSADER×15, PIKENEER×12, PIKENEER×15, SAMURAI×17, KNIGHT×15, CONDOTTERI×15, KNIGHT×12, HANDGUNNER×16, CRUSADER×15 |
| 🟩 | Hungry Invaders | random | Iron Age 93%, Medieval 7% | 🟢 23/23 (100%) |  | HANDGUNNER×12, SIEGE_RAM×12, CONDOTTERI×16, HANDGUNNER×13, THE_SWORDMASTER×999, CONDOTTERI×13, LARGE_CART×16, SIEGE_RAM×15, HORSEMAN_FAST×15 |
| 🟩 | Angry Mob | random | Iron Age 90%, Medieval 7%, Renaissance 3% | 🟢 23/23 (100%) |  | SAMURAI×12, CRUSADER×11, SAMURAI×14, HORSEMAN_SLOW×17, THE_SWORDMASTER×999, LARGE_CART×12, CONDOTTERI×14, CRUSADER×14, MUSKETEER×16, DRAGOONER×15, HANDGUNNER×17 |
| 🟩 | Grumpy Marauders | random | Medieval 72%, Iron Age 19%, Renaissance 9% | 🟢 22/23 (96%) | MUSKETEER×1 | CONDOTTERI×16, MUSKETEER×14, SAMURAI×14, KNIGHT×15, SIEGE_RAM×18, SIEGE_RAM×12, HANDGUNNER×14, SIEGE_RAM×15, CRUSADER×12, HORSEMAN_FAST×15, PIKENEER×15 |
| 🟩 | Muddy Marauders | random | Medieval 91%, Renaissance 9% | 🔴 3/23 (13%) | CRUSADER×6, MUSKETEER×4, HANDGUNNER×4 | CONDOTTERI×11, SIEGE_RAM×15, SIEGE_RAM×15, CARGO×12, CONDOTTERI×18, HANDGUNNER×12, KNIGHT×12, CRUSADER×16, SIEGE_RAM×15, HANDGUNNER×13 |
| 🟩 | Restless Horde | random | Medieval 89%, Iron Age 11% | 🟢 23/23 (100%) |  | HANDGUNNER×16, SAMURAI×15, SIEGE_RAM×15, CRUSADER×15, PIKENEER×16, CRUSADER×12, SIEGE_RAM×12, SIEGE_RAM×12, SAMURAI×15, CRUSADER×11, CONDOTTERI×13 |
| 🟩 | Noisy Barbarians | random | Medieval 82%, Renaissance 10%, Iron Age 8% | 🟡 14/23 (61%) | MUSKETEER×7, CRUSADER×1 | CRUSADER×12, HANDGUNNER×14, SAMURAI×14, LARGE_CART×12, HANDGUNNER×11, SIEGE_RAM×12, CRUSADER×16, SAMURAI×12, SAMURAI×16, CRUSADER×18, CARGO×16 |
| 🟩 | Savage Rabble | random | Iron Age 89%, Medieval 10%, Renaissance 1% | 🟢 23/23 (100%) |  | CONDOTTERI×13, HANDGUNNER×18, KNIGHT×12, KNIGHT×12, THE_SWORDMASTER×999, MUSKETEER×11, SIEGE_RAM×18, SAMURAI×14, SAMURAI×13, KNIGHT×12 |
| 🟩 | Blundering Invaders | random | Medieval 82%, Renaissance 18% | 🟢 23/23 (100%) |  | MUSKETEER×17, SIEGE_RAM×12, CRUSADER×13, CRUSADER×16, SAMURAI×15, HANDGUNNER×14, HANDGUNNER×13, DRAGOONER×15, SAMURAI×17, SAMURAI×13, CRUSADER×18, KNIGHT×15 |
| 🟩 | Wandering Pillagers | random | Renaissance 87%, Medieval 13% | 🟡 13/23 (57%) | THE_KING×1 | CONDOTTERI×15, THE_KING×999, SIEGE_RAM×12, CONDOTTERI×13, SAMURAI×16, CONDOTTERI×13, CRUSADER×12, SIEGE_RAM×15, KNIGHT×15, KNIGHT×12, CONDOTTERI×17, SAMURAI×11 |
| 🟩 | Noisy Barbarians | random | Medieval 72%, Iron Age 19%, Renaissance 9% | 🟢 21/23 (91%) | DRAGOONER×1 | SIEGE_RAM×15, KNIGHT×12, KNIGHT×18, SAMURAI×15, LARGE_CART×16, CRUSADER×18, DRAGOONER×13, SIEGE_RAM×12, SIEGE_RAM×15, HORSEMAN_FAST×12 |
| 🟩 | Noisy Barbarians | random | Medieval 76%, Renaissance 12%, Iron Age 12% | 🟢 21/23 (91%) | MUSKETEER×2 | SAMURAI×15, SAMURAI×15, SIEGE_RAM×15, CRUSADER×12, CARGO×16, CONDOTTERI×12, LEGIONARY×16, CONDOTTERI×18, KNIGHT×15 |

#### Mixed

| Tower Era Distribution (61 towers) | Towers |
|---|---|
| Industrial 92% (56), Renaissance 7% (4), Iron Age 2% (1) | FLAME_THROWER×26, SHOCK_TOWER×19, GATLING_TOWER×11, ICE_TOWER×4, COLD_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Medieval Siege | hardcoded | Medieval 97%, Renaissance 3% | 🟢 23/23 (100%) |  | CRUSADER×12, CONDOTTERI×13, KNIGHT×14, SAMURAI×15, SIEGE_RAM×15, KNIGHT×16, CONDOTTERI×17, CRUSADER×18, NINJA×11, SIEGE_RAM×20, HANDGUNNER×22, HANDGUNNER×24, HANDGUNNER×26, SAMURAI×28, SIEGE_RAM×30, CONDOTTERI×34 |
| 🟩 | Knights' Charge | hardcoded | Medieval 100% | 🟢 23/23 (100%) |  | CRUSADER×16, SIEGE_RAM×17, CRUSADER×18, SIEGE_RAM×19, SAMURAI×20, KNIGHT×21, SAMURAI×22, CRUSADER×16, SAMURAI×18, KNIGHT×20, KNIGHT×22, CRUSADER×24, KNIGHT×26, KNIGHT×28, SIEGE_RAM×30, CONDOTTERI×32, HANDGUNNER×34, HANDGUNNER×32 |
| 🟩 | Crusader Host | hardcoded | Medieval 100% | 🟢 23/23 (100%) |  | CRUSADER×16, SIEGE_RAM×17, SAMURAI×18, SIEGE_RAM×19, SIEGE_RAM×20, SAMURAI×21, CRUSADER×22, KNIGHT×16, KNIGHT×18, CRUSADER×20, CRUSADER×22, HANDGUNNER×24, CONDOTTERI×26, SAMURAI×28, KNIGHT×30, CRUSADER×32, CRUSADER×34, KNIGHT×31 |
| 🟩 | Castle Assault | hardcoded | Medieval 100% | 🟢 23/23 (100%) |  | SAMURAI×16, KNIGHT×17, KNIGHT×18, KNIGHT×19, CRUSADER×20, CRUSADER×21, SIEGE_RAM×22, SAMURAI×16, CRUSADER×18, CRUSADER×20, CRUSADER×22, SAMURAI×24, SIEGE_RAM×26, CRUSADER×28, CRUSADER×30, SAMURAI×32, CONDOTTERI×34, SIEGE_RAM×32, KNIGHT×33 |
| 🟩 | Feudal Army | hardcoded | Medieval 100% | 🟢 23/23 (100%) |  | KNIGHT×16, SIEGE_RAM×17, KNIGHT×18, SIEGE_RAM×19, CRUSADER×20, CRUSADER×21, CONDOTTERI×22, HANDGUNNER×16, CRUSADER×18, SIEGE_RAM×20, SIEGE_RAM×22, CRUSADER×24, KNIGHT×26, CONDOTTERI×28, KNIGHT×30, CONDOTTERI×32, CONDOTTERI×34, CRUSADER×31, CRUSADER×33 |
| 🟩 | Holy Crusade | hardcoded | Medieval 82%, Iron Age 15%, Renaissance 3% | 🟢 23/23 (100%) |  | SAMURAI×16, CONDOTTERI×17, HANDGUNNER×17, KNIGHT×18, THE_SWORDMASTER×19, CONDOTTERI×19, CONDOTTERI×20, HANDGUNNER×21, KNIGHT×21, LARGE_CART×22, LEGIONARY×23, MUSKETEER×12, HANDGUNNER×24, SIEGE_RAM×28, SIEGE_RAM×30, KNIGHT×32, HANDGUNNER×31, CRUSADER×28, CRUSADER×34 |
| 🟩 | Grumpy Marauders | random | Medieval 92%, Renaissance 8% | 🟢 23/23 (100%) |  | CONDOTTERI×13, SAMURAI×15, HANDGUNNER×18, SAMURAI×12, HANDGUNNER×14, DRAGOONER×13, KNIGHT×12, KNIGHT×15, CRUSADER×14, SAMURAI×13, CRUSADER×14, CONDOTTERI×14 |
| 🟩 | Grumpy Marauders | random | Medieval 92%, Renaissance 8% | 🟢 23/23 (100%) |  | CONDOTTERI×13, SAMURAI×15, HANDGUNNER×18, SAMURAI×12, HANDGUNNER×14, DRAGOONER×13, KNIGHT×12, KNIGHT×15, CRUSADER×14, SAMURAI×13, CRUSADER×14, CONDOTTERI×14 |
| 🟩 | Howling Savages | random | Iron Age 85%, Medieval 15% | 🟢 23/23 (100%) |  | KNIGHT×15, SIEGE_RAM×15, SAMURAI×18, THE_SWORDMASTER×999, KNIGHT×12, SIEGE_RAM×18, CRUSADER×17, CRUSADER×17, SAMURAI×16, CRUSADER×12, CRUSADER×16, HANDGUNNER×15 |
| 🟩 | Shrieking Horde | random | Medieval 90%, Renaissance 10% | 🟢 23/23 (100%) |  | CRUSADER×17, SIEGE_RAM×12, NINJA×18, CONDOTTERI×15, HANDGUNNER×13, CRUSADER×16, SAMURAI×17, CRUSADER×13, SAMURAI×14, CONDOTTERI×13, CRUSADER×16, CONDOTTERI×15 |
| 🟩 | Crude Invaders | random | Medieval 93%, Iron Age 7% | 🟢 23/23 (100%) |  | SAMURAI×16, CONDOTTERI×16, CONDOTTERI×13, HANDGUNNER×18, SAMURAI×13, SIEGE_RAM×12, HANDGUNNER×15, CONDOTTERI×14, HORSEMAN_FAST×14, SAMURAI×16, CONDOTTERI×15, HANDGUNNER×15, CRUSADER×13 |
| 🟩 | Reckless Looters | random | Medieval 75%, Iron Age 25% | 🟢 23/23 (100%) |  | KNIGHT×18, KNIGHT×15, PIKENEER×17, CONDOTTERI×16, SIEGE_RAM×15, CRUSADER×14, CONDOTTERI×13, HORSEMAN_SLOW×13, KNIGHT×15, SIEGE_RAM×12, SAMURAI×17, PIKENEER×14 |
| 🟩 | Howling Savages | random | Medieval 90%, Renaissance 10% | 🟢 23/23 (100%) |  | CRUSADER×14, SAMURAI×11, KNIGHT×18, KNIGHT×15, HANDGUNNER×18, CRUSADER×11, HANDGUNNER×13, SAMURAI×14, KNIGHT×18, CONDOTTERI×15, CARGO×16 |
| 🟩 | Unlucky Raiders | random | Medieval 80%, Renaissance 20% | 🟢 23/23 (100%) |  | CRUSADER×16, SIEGE_RAM×12, CONDOTTERI×13, KNIGHT×15, SAMURAI×13, CONDOTTERI×15, CARGO×12, SAMURAI×14, MUSKETEER×13 |
| 🟩 | Frenzied Pillagers | random | Medieval 80%, Iron Age 20% | 🟢 23/23 (100%) |  | CRUSADER×15, PIKENEER×12, PIKENEER×15, SAMURAI×17, KNIGHT×15, CONDOTTERI×15, KNIGHT×12, HANDGUNNER×16, CRUSADER×15 |
| 🟩 | Hungry Invaders | random | Iron Age 93%, Medieval 7% | 🟢 23/23 (100%) |  | HANDGUNNER×12, SIEGE_RAM×12, CONDOTTERI×16, HANDGUNNER×13, THE_SWORDMASTER×999, CONDOTTERI×13, LARGE_CART×16, SIEGE_RAM×15, HORSEMAN_FAST×15 |
| 🟩 | Angry Mob | random | Iron Age 90%, Medieval 7%, Renaissance 3% | 🟢 23/23 (100%) |  | SAMURAI×12, CRUSADER×11, SAMURAI×14, HORSEMAN_SLOW×17, THE_SWORDMASTER×999, LARGE_CART×12, CONDOTTERI×14, CRUSADER×14, MUSKETEER×16, DRAGOONER×15, HANDGUNNER×17 |
| 🟩 | Grumpy Marauders | random | Medieval 72%, Iron Age 19%, Renaissance 9% | 🟢 23/23 (100%) |  | CONDOTTERI×16, MUSKETEER×14, SAMURAI×14, KNIGHT×15, SIEGE_RAM×18, SIEGE_RAM×12, HANDGUNNER×14, SIEGE_RAM×15, CRUSADER×12, HORSEMAN_FAST×15, PIKENEER×15 |
| 🟩 | Muddy Marauders | random | Medieval 91%, Renaissance 9% | 🟢 23/23 (100%) |  | CONDOTTERI×11, SIEGE_RAM×15, SIEGE_RAM×15, CARGO×12, CONDOTTERI×18, HANDGUNNER×12, KNIGHT×12, CRUSADER×16, SIEGE_RAM×15, HANDGUNNER×13 |
| 🟩 | Restless Horde | random | Medieval 89%, Iron Age 11% | 🟢 23/23 (100%) |  | HANDGUNNER×16, SAMURAI×15, SIEGE_RAM×15, CRUSADER×15, PIKENEER×16, CRUSADER×12, SIEGE_RAM×12, SIEGE_RAM×12, SAMURAI×15, CRUSADER×11, CONDOTTERI×13 |
| 🟩 | Noisy Barbarians | random | Medieval 82%, Renaissance 10%, Iron Age 8% | 🟢 23/23 (100%) |  | CRUSADER×12, HANDGUNNER×14, SAMURAI×14, LARGE_CART×12, HANDGUNNER×11, SIEGE_RAM×12, CRUSADER×16, SAMURAI×12, SAMURAI×16, CRUSADER×18, CARGO×16 |
| 🟩 | Savage Rabble | random | Iron Age 89%, Medieval 10%, Renaissance 1% | 🟢 23/23 (100%) |  | CONDOTTERI×13, HANDGUNNER×18, KNIGHT×12, KNIGHT×12, THE_SWORDMASTER×999, MUSKETEER×11, SIEGE_RAM×18, SAMURAI×14, SAMURAI×13, KNIGHT×12 |
| 🟩 | Blundering Invaders | random | Medieval 82%, Renaissance 18% | 🟢 23/23 (100%) |  | MUSKETEER×17, SIEGE_RAM×12, CRUSADER×13, CRUSADER×16, SAMURAI×15, HANDGUNNER×14, HANDGUNNER×13, DRAGOONER×15, SAMURAI×17, SAMURAI×13, CRUSADER×18, KNIGHT×15 |
| 🟩 | Wandering Pillagers | random | Renaissance 87%, Medieval 13% | 🟢 23/23 (100%) |  | CONDOTTERI×15, THE_KING×999, SIEGE_RAM×12, CONDOTTERI×13, SAMURAI×16, CONDOTTERI×13, CRUSADER×12, SIEGE_RAM×15, KNIGHT×15, KNIGHT×12, CONDOTTERI×17, SAMURAI×11 |
| 🟩 | Noisy Barbarians | random | Medieval 72%, Iron Age 19%, Renaissance 9% | 🟢 23/23 (100%) |  | SIEGE_RAM×15, KNIGHT×12, KNIGHT×18, SAMURAI×15, LARGE_CART×16, CRUSADER×18, DRAGOONER×13, SIEGE_RAM×12, SIEGE_RAM×15, HORSEMAN_FAST×12 |
| 🟩 | Noisy Barbarians | random | Medieval 76%, Renaissance 12%, Iron Age 12% | 🟢 23/23 (100%) |  | SAMURAI×15, SAMURAI×15, SIEGE_RAM×15, CRUSADER×12, CARGO×16, CONDOTTERI×12, LEGIONARY×16, CONDOTTERI×18, KNIGHT×15 |

#### Long Early

| Tower Era Distribution (28 towers) | Towers |
|---|---|
| Iron Age 50% (14), Medieval 50% (14) | ARBELESTE_TOWER×14, BOILING_OIL×5, HEAVY_TOWER×5, TAR_TOWER×4 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟥 | Medieval Siege | hardcoded | Medieval 97%, Renaissance 3% | ⬛ 0/23 (0%) | HANDGUNNER×9, SAMURAI×8, CRUSADER×3 | CRUSADER×12, CONDOTTERI×13, KNIGHT×14, SAMURAI×15, SIEGE_RAM×15, KNIGHT×16, CONDOTTERI×17, CRUSADER×18, NINJA×11, SIEGE_RAM×20, HANDGUNNER×22, HANDGUNNER×24, HANDGUNNER×26, SAMURAI×28, SIEGE_RAM×30, CONDOTTERI×34 |
| 🟥 | Knights' Charge | hardcoded | Medieval 100% | ⬛ 0/23 (0%) | HANDGUNNER×11, CONDOTTERI×5, CRUSADER×1, KNIGHT×1 | CRUSADER×16, SIEGE_RAM×17, CRUSADER×18, SIEGE_RAM×19, SAMURAI×20, KNIGHT×21, SAMURAI×22, CRUSADER×16, SAMURAI×18, KNIGHT×20, KNIGHT×22, CRUSADER×24, KNIGHT×26, KNIGHT×28, SIEGE_RAM×30, CONDOTTERI×32, HANDGUNNER×34, HANDGUNNER×32 |
| 🟥 | Crusader Host | hardcoded | Medieval 100% | ⬛ 0/23 (0%) | HANDGUNNER×10, SAMURAI×9, CRUSADER×2 | CRUSADER×16, SIEGE_RAM×17, SAMURAI×18, SIEGE_RAM×19, SIEGE_RAM×20, SAMURAI×21, CRUSADER×22, KNIGHT×16, KNIGHT×18, CRUSADER×20, CRUSADER×22, HANDGUNNER×24, CONDOTTERI×26, SAMURAI×28, KNIGHT×30, CRUSADER×32, CRUSADER×34, KNIGHT×31 |
| 🟥 | Castle Assault | hardcoded | Medieval 100% | ⬛ 0/23 (0%) | SAMURAI×11, CRUSADER×6 | SAMURAI×16, KNIGHT×17, KNIGHT×18, KNIGHT×19, CRUSADER×20, CRUSADER×21, SIEGE_RAM×22, SAMURAI×16, CRUSADER×18, CRUSADER×20, CRUSADER×22, SAMURAI×24, SIEGE_RAM×26, CRUSADER×28, CRUSADER×30, SAMURAI×32, CONDOTTERI×34, SIEGE_RAM×32, KNIGHT×33 |
| 🟥 | Feudal Army | hardcoded | Medieval 100% | ⬛ 0/23 (0%) | HANDGUNNER×7, CRUSADER×4, CONDOTTERI×4 | KNIGHT×16, SIEGE_RAM×17, KNIGHT×18, SIEGE_RAM×19, CRUSADER×20, CRUSADER×21, CONDOTTERI×22, HANDGUNNER×16, CRUSADER×18, SIEGE_RAM×20, SIEGE_RAM×22, CRUSADER×24, KNIGHT×26, CONDOTTERI×28, KNIGHT×30, CONDOTTERI×32, CONDOTTERI×34, CRUSADER×31, CRUSADER×33 |
| 🟥 | Holy Crusade | hardcoded | Medieval 82%, Iron Age 15%, Renaissance 3% | ⬛ 0/23 (0%) | HANDGUNNER×7, CONDOTTERI×5, CRUSADER×3 | SAMURAI×16, CONDOTTERI×17, HANDGUNNER×17, KNIGHT×18, THE_SWORDMASTER×19, CONDOTTERI×19, CONDOTTERI×20, HANDGUNNER×21, KNIGHT×21, LARGE_CART×22, LEGIONARY×23, MUSKETEER×12, HANDGUNNER×24, SIEGE_RAM×28, SIEGE_RAM×30, KNIGHT×32, HANDGUNNER×31, CRUSADER×28, CRUSADER×34 |
| 🟩 | Grumpy Marauders | random | Medieval 92%, Renaissance 8% | 🟢 23/23 (100%) |  | CONDOTTERI×13, SAMURAI×15, HANDGUNNER×18, SAMURAI×12, HANDGUNNER×14, DRAGOONER×13, KNIGHT×12, KNIGHT×15, CRUSADER×14, SAMURAI×13, CRUSADER×14, CONDOTTERI×14 |
| 🟩 | Grumpy Marauders | random | Medieval 92%, Renaissance 8% | 🟢 23/23 (100%) |  | CONDOTTERI×13, SAMURAI×15, HANDGUNNER×18, SAMURAI×12, HANDGUNNER×14, DRAGOONER×13, KNIGHT×12, KNIGHT×15, CRUSADER×14, SAMURAI×13, CRUSADER×14, CONDOTTERI×14 |
| 🟩 | Howling Savages | random | Iron Age 85%, Medieval 15% | 🟢 23/23 (100%) |  | KNIGHT×15, SIEGE_RAM×15, SAMURAI×18, THE_SWORDMASTER×999, KNIGHT×12, SIEGE_RAM×18, CRUSADER×17, CRUSADER×17, SAMURAI×16, CRUSADER×12, CRUSADER×16, HANDGUNNER×15 |
| 🟩 | Shrieking Horde | random | Medieval 90%, Renaissance 10% | 🟢 23/23 (100%) |  | CRUSADER×17, SIEGE_RAM×12, NINJA×18, CONDOTTERI×15, HANDGUNNER×13, CRUSADER×16, SAMURAI×17, CRUSADER×13, SAMURAI×14, CONDOTTERI×13, CRUSADER×16, CONDOTTERI×15 |
| 🟩 | Crude Invaders | random | Medieval 93%, Iron Age 7% | 🟢 23/23 (100%) |  | SAMURAI×16, CONDOTTERI×16, CONDOTTERI×13, HANDGUNNER×18, SAMURAI×13, SIEGE_RAM×12, HANDGUNNER×15, CONDOTTERI×14, HORSEMAN_FAST×14, SAMURAI×16, CONDOTTERI×15, HANDGUNNER×15, CRUSADER×13 |
| 🟩 | Reckless Looters | random | Medieval 75%, Iron Age 25% | 🟢 23/23 (100%) |  | KNIGHT×18, KNIGHT×15, PIKENEER×17, CONDOTTERI×16, SIEGE_RAM×15, CRUSADER×14, CONDOTTERI×13, HORSEMAN_SLOW×13, KNIGHT×15, SIEGE_RAM×12, SAMURAI×17, PIKENEER×14 |
| 🟩 | Howling Savages | random | Medieval 90%, Renaissance 10% | 🟢 23/23 (100%) |  | CRUSADER×14, SAMURAI×11, KNIGHT×18, KNIGHT×15, HANDGUNNER×18, CRUSADER×11, HANDGUNNER×13, SAMURAI×14, KNIGHT×18, CONDOTTERI×15, CARGO×16 |
| 🟩 | Unlucky Raiders | random | Medieval 80%, Renaissance 20% | 🟢 21/23 (91%) | CRUSADER×1 | CRUSADER×16, SIEGE_RAM×12, CONDOTTERI×13, KNIGHT×15, SAMURAI×13, CONDOTTERI×15, CARGO×12, SAMURAI×14, MUSKETEER×13 |
| 🟩 | Frenzied Pillagers | random | Medieval 80%, Iron Age 20% | 🟢 23/23 (100%) |  | CRUSADER×15, PIKENEER×12, PIKENEER×15, SAMURAI×17, KNIGHT×15, CONDOTTERI×15, KNIGHT×12, HANDGUNNER×16, CRUSADER×15 |
| 🟩 | Hungry Invaders | random | Iron Age 93%, Medieval 7% | 🟡 16/23 (70%) | CONDOTTERI×2, HANDGUNNER×1, CRUSADER×1 | HANDGUNNER×12, SIEGE_RAM×12, CONDOTTERI×16, HANDGUNNER×13, THE_SWORDMASTER×999, CONDOTTERI×13, LARGE_CART×16, SIEGE_RAM×15, HORSEMAN_FAST×15 |
| 🟩 | Angry Mob | random | Iron Age 90%, Medieval 7%, Renaissance 3% | 🟠 9/23 (39%) | DRAGOONER×4, CRUSADER×2, MUSKETEER×1, HANDGUNNER×1 | SAMURAI×12, CRUSADER×11, SAMURAI×14, HORSEMAN_SLOW×17, THE_SWORDMASTER×999, LARGE_CART×12, CONDOTTERI×14, CRUSADER×14, MUSKETEER×16, DRAGOONER×15, HANDGUNNER×17 |
| 🟩 | Grumpy Marauders | random | Medieval 72%, Iron Age 19%, Renaissance 9% | 🟡 17/23 (74%) | CRUSADER×3 | CONDOTTERI×16, MUSKETEER×14, SAMURAI×14, KNIGHT×15, SIEGE_RAM×18, SIEGE_RAM×12, HANDGUNNER×14, SIEGE_RAM×15, CRUSADER×12, HORSEMAN_FAST×15, PIKENEER×15 |
| 🟩 | Muddy Marauders | random | Medieval 91%, Renaissance 9% | 🟠 9/23 (39%) | HANDGUNNER×6, CONDOTTERI×4 | CONDOTTERI×11, SIEGE_RAM×15, SIEGE_RAM×15, CARGO×12, CONDOTTERI×18, HANDGUNNER×12, KNIGHT×12, CRUSADER×16, SIEGE_RAM×15, HANDGUNNER×13 |
| 🟩 | Restless Horde | random | Medieval 89%, Iron Age 11% | 🟢 23/23 (100%) |  | HANDGUNNER×16, SAMURAI×15, SIEGE_RAM×15, CRUSADER×15, PIKENEER×16, CRUSADER×12, SIEGE_RAM×12, SIEGE_RAM×12, SAMURAI×15, CRUSADER×11, CONDOTTERI×13 |
| 🟩 | Noisy Barbarians | random | Medieval 82%, Renaissance 10%, Iron Age 8% | 🟢 22/23 (96%) | MUSKETEER×1 | CRUSADER×12, HANDGUNNER×14, SAMURAI×14, LARGE_CART×12, HANDGUNNER×11, SIEGE_RAM×12, CRUSADER×16, SAMURAI×12, SAMURAI×16, CRUSADER×18, CARGO×16 |
| 🟩 | Savage Rabble | random | Iron Age 89%, Medieval 10%, Renaissance 1% | 🟢 23/23 (100%) |  | CONDOTTERI×13, HANDGUNNER×18, KNIGHT×12, KNIGHT×12, THE_SWORDMASTER×999, MUSKETEER×11, SIEGE_RAM×18, SAMURAI×14, SAMURAI×13, KNIGHT×12 |
| 🟩 | Blundering Invaders | random | Medieval 82%, Renaissance 18% | 🟢 22/23 (96%) | HANDGUNNER×1 | MUSKETEER×17, SIEGE_RAM×12, CRUSADER×13, CRUSADER×16, SAMURAI×15, HANDGUNNER×14, HANDGUNNER×13, DRAGOONER×15, SAMURAI×17, SAMURAI×13, CRUSADER×18, KNIGHT×15 |
| 🟩 | Wandering Pillagers | random | Renaissance 87%, Medieval 13% | 🟡 13/23 (57%) | THE_KING×1 | CONDOTTERI×15, THE_KING×999, SIEGE_RAM×12, CONDOTTERI×13, SAMURAI×16, CONDOTTERI×13, CRUSADER×12, SIEGE_RAM×15, KNIGHT×15, KNIGHT×12, CONDOTTERI×17, SAMURAI×11 |
| 🟩 | Noisy Barbarians | random | Medieval 72%, Iron Age 19%, Renaissance 9% | 🟢 23/23 (100%) |  | SIEGE_RAM×15, KNIGHT×12, KNIGHT×18, SAMURAI×15, LARGE_CART×16, CRUSADER×18, DRAGOONER×13, SIEGE_RAM×12, SIEGE_RAM×15, HORSEMAN_FAST×12 |
| 🟩 | Noisy Barbarians | random | Medieval 76%, Renaissance 12%, Iron Age 12% | 🟠 10/23 (43%) | MUSKETEER×7, CRUSADER×3 | SAMURAI×15, SAMURAI×15, SIEGE_RAM×15, CRUSADER×12, CARGO×16, CONDOTTERI×12, LEGIONARY×16, CONDOTTERI×18, KNIGHT×15 |

### Renaissance

#### Mixed late

| Tower Era Distribution (32 towers) | Towers |
|---|---|
| Renaissance 78% (25), Medieval 19% (6), Iron Age 3% (1) | RIFLE_TOWER×18, ICE_TOWER×7, CANNON_TOWER×6, COLD_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟥 | Renaissance Force | hardcoded | Renaissance 96%, Industrial 4% | ⬛ 0/24 (0%) | SMALL_TANK×9, DRAGOONER×3 | MUSKETEER×16, DRAGOONER×17, NINJA×17, NINJA×18, MUSKETEER×19, MUSKETEER×19, MUSKETEER×20, SMALL_TANK×22, MUSKETEER×21, DRAGOONER×22, NINJA×23, DRAGOONER×20, DRAGOONER×24, NINJA×28, DRAGOONER×30, DRAGOONER×32, CARGO×32, CARGO×34, THE_KING×36, MUSKETEER×35, DRAGOONER×36, DRAGOONER×35 |
| 🟩 | Musketeer Brigade | hardcoded | Renaissance 98%, Industrial 2% | 🟠 7/24 (29%) | MUSKETEER×5, NINJA×2, THE_KING×1 | MUSKETEER×16, DRAGOONER×17, DRAGOONER×17, CARGO×18, DRAGOONER×19, NINJA×19, MUSKETEER×20, CARGO×21, MUSKETEER×21, DRAGOONER×22, MOTORBIKE×12, NINJA×23, MUSKETEER×24, CARGO×28, THE_KING×30, CARGO×32, NINJA×34, MUSKETEER×36, MUSKETEER×36, NINJA×35, NINJA×38, DRAGOONER×34 |
| 🟥 | Ninja Infiltration | hardcoded | Renaissance 96%, Industrial 4% | ⬛ 0/24 (0%) | DRAGOONER×8, MUSKETEER×2, SOLDIER×1, THE_KING×1 | NINJA×16, DRAGOONER×17, DRAGOONER×17, NINJA×18, MUSKETEER×19, CARGO×19, DRAGOONER×20, DRAGOONER×21, DRAGOONER×21, MUSKETEER×22, CARGO×23, CARGO×23, NINJA×33, NINJA×28, CARGO×30, CARGO×32, MUSKETEER×34, DRAGOONER×36, THE_KING×38, NINJA×36, NINJA×35, SOLDIER×22 |
| 🟥 | Cannon Barrage | hardcoded | Renaissance 96%, Industrial 4% | ⬛ 0/24 (0%) | DRAGOONER×5, SOLDIER×5, THE_KING×1 | MUSKETEER×16, DRAGOONER×17, CARGO×17, MUSKETEER×18, NINJA×19, NINJA×19, MUSKETEER×20, DRAGOONER×21, NINJA×21, NINJA×22, DRAGOONER×23, NINJA×23, MUSKETEER×24, MUSKETEER×28, THE_KING×30, NINJA×32, SOLDIER×20, DRAGOONER×36, DRAGOONER×36, DRAGOONER×36, MUSKETEER×36, MUSKETEER×35 |
| 🟥 | Rampaging Rabble | random | Renaissance 97%, Industrial 3% | ⬛ 0/24 (0%) | SMALL_TANK×7, THE_KING×1 | MUSKETEER×24, THE_KING×999, SMALL_TANK×20, MUSKETEER×17, CARGO×24, NINJA×20, MUSKETEER×18, DRAGOONER×24, DRAGOONER×20, MUSKETEER×17, DRAGOONER×22, NINJA×22, MUSKETEER×18, CARGO×20, TRANSPORTER×20, MUSKETEER×18 |
| 🟥 | Rampaging Rabble | random | Renaissance 97%, Industrial 3% | ⬛ 0/24 (0%) | SMALL_TANK×7, THE_KING×1 | MUSKETEER×24, THE_KING×999, SMALL_TANK×20, MUSKETEER×17, CARGO×24, NINJA×20, MUSKETEER×18, DRAGOONER×24, DRAGOONER×20, MUSKETEER×17, DRAGOONER×22, NINJA×22, MUSKETEER×18, CARGO×20, TRANSPORTER×20, MUSKETEER×18 |
| 🟩 | Petty Bandits | random | Renaissance 97%, Industrial 2%, Medieval 1% | 🟠 7/24 (29%) | SOLDIER×5, MUSKETEER×2, THE_KING×1 | MUSKETEER×24, DRAGOONER×18, NINJA×24, THE_KING×999, CARGO×16, DRAGOONER×20, SOLDIER×21, CARGO×20, CARGO×16, NINJA×25, MUSKETEER×22, SAMURAI×19, NINJA×18, CARGO×20, MUSKETEER×25, DRAGOONER×22 |
| 🟩 | Savage Rabble | random | Renaissance 99%, Industrial 1% | 🟠 10/24 (42%) | SMALL_TANK×7 | CARGO×24, MUSKETEER×23, DRAGOONER×15, CARGO×20, NINJA×17, MUSKETEER×22, MUSKETEER×18, SMALL_TANK×16, DRAGOONER×24, DRAGOONER×20, CARGO×20, MUSKETEER×23, NINJA×20, CARGO×24, MUSKETEER×23, THE_KING×999 |
| 🟩 | Noisy Barbarians | random | Renaissance 99%, Medieval 1% | 🟡 14/24 (58%) | THE_KING×1 | MUSKETEER×24, CARGO×20, MUSKETEER×21, CONDOTTERI×20, DRAGOONER×20, MUSKETEER×24, NINJA×26, MUSKETEER×16, MUSKETEER×21, CARGO×20, NINJA×21, DRAGOONER×24, DRAGOONER×22, CARGO×16, THE_KING×999, DRAGOONER×26, DRAGOONER×24 |
| 🟩 | Rude Barbarians | random | Renaissance 95%, Medieval 5% | 🟢 24/24 (100%) |  | MUSKETEER×19, MUSKETEER×26, SAMURAI×26, MUSKETEER×23, MUSKETEER×25, KNIGHT×18, DRAGOONER×18, CARGO×20, CARGO×20, HANDGUNNER×19, MUSKETEER×16, CARGO×24, MUSKETEER×17, NINJA×24, THE_KING×999, DRAGOONER×22 |
| 🟩 | Restless Horde | random | Renaissance 97%, Industrial 3% | 🔴 4/24 (17%) | SOLDIER×6, MUSKETEER×4, THE_KING×1 | MUSKETEER×18, NINJA×25, NINJA×21, SOLDIER×19, CARGO×24, THE_KING×999, CARGO×20, MUSKETEER×25, SOLDIER×22, CARGO×24, CARGO×24, MUSKETEER×24, DRAGOONER×20, NINJA×17, DRAGOONER×26, CARGO×20 |
| 🟥 | Blundering Invaders | random | Renaissance 95%, Industrial 5% | ⬛ 0/24 (0%) | SMALL_TANK×7, THE_KING×1 | DRAGOONER×18, NINJA×22, SOLDIER×25, THE_KING×999, CARGO×20, MUSKETEER×21, DRAGOONER×22, NINJA×25, SOLDIER×19, NINJA×20, NINJA×17, SMALL_TANK×24, MUSKETEER×26, MUSKETEER×21 |
| 🟩 | Relentless Mob | random | Renaissance 95%, Medieval 3%, Industrial 2% | 🟢 24/24 (100%) |  | NINJA×26, NINJA×21, DRAGOONER×22, DRAGOONER×20, MOTORBIKE×21, SAMURAI×21, DRAGOONER×18, DRAGOONER×18, DRAGOONER×18, CARGO×24, NINJA×16, THE_KING×999, CRUSADER×21, MUSKETEER×24 |
| 🟩 | Grumpy Marauders | random | Renaissance 95%, Medieval 5% | 🟢 24/24 (100%) |  | CARGO×24, MUSKETEER×19, CARGO×20, KNIGHT×21, MUSKETEER×25, CONDOTTERI×19, CARGO×16, DRAGOONER×22, CRUSADER×25, DRAGOONER×18, NINJA×21, THE_KING×999, CARGO×24, DRAGOONER×22 |
| 🟩 | Weary Plunderers | random | Renaissance 93%, Medieval 5%, Industrial 3% | 🟢 24/24 (100%) |  | CARGO×16, KNIGHT×18, CARGO×20, SOLDIER×17, MUSKETEER×23, CARGO×16, CRUSADER×21, NINJA×26, SOLDIER×17, MUSKETEER×24, SAMURAI×21, MUSKETEER×20, MUSKETEER×25, DRAGOONER×20, THE_KING×999, MUSKETEER×18 |
| 🟥 | Frenzied Pillagers | random | Renaissance 93%, Medieval 3%, Industrial 3% | ⬛ 0/24 (0%) | SMALL_TANK×10, MUSKETEER×3, THE_KING×1 | DRAGOONER×18, MUSKETEER×21, NINJA×19, CONDOTTERI×24, MUSKETEER×25, MOTORBIKE×17, DRAGOONER×22, KNIGHT×21, MUSKETEER×17, MUSKETEER×20, MUSKETEER×24, THE_KING×999, SMALL_TANK×26, DRAGOONER×22, MUSKETEER×22, CARGO×20 |
| 🟩 | Reckless Looters | random | Renaissance 97%, Industrial 3% | 🟢 24/24 (100%) |  | DRAGOONER×24, MOTORBIKE×19, MUSKETEER×21, NINJA×25, MOTORBIKE×18, CARGO×16, THE_KING×999, NINJA×17, MUSKETEER×20, DRAGOONER×22, MUSKETEER×17, DRAGOONER×22, DRAGOONER×24, CARGO×20, MUSKETEER×25 |
| 🟩 | Forgotten Warband | random | Renaissance 98%, Medieval 2% | 🟢 24/24 (100%) |  | NINJA×17, NINJA×20, DRAGOONER×20, DRAGOONER×22, MUSKETEER×17, NINJA×22, NINJA×19, SAMURAI×23, NINJA×16, DRAGOONER×20, MUSKETEER×25, THE_KING×999, MUSKETEER×23, DRAGOONER×24, MUSKETEER×18, DRAGOONER×24 |
| 🟩 | Blundering Invaders | random | Renaissance 96%, Industrial 3%, Medieval 1% | 🟢 24/24 (100%) |  | CARGO×24, SOLDIER×22, MUSKETEER×23, KNIGHT×18, MUSKETEER×24, SOLDIER×18, THE_KING×999, CARGO×16, MUSKETEER×26, MUSKETEER×25, NINJA×19, DRAGOONER×24, NINJA×18, MUSKETEER×17, NINJA×22 |
| 🟩 | Rude Barbarians | random | Renaissance 97%, Industrial 2%, Medieval 1% | 🟠 6/24 (25%) | SMALL_TANK×9 | THE_KING×999, NINJA×16, MUSKETEER×16, NINJA×17, NINJA×20, DRAGOONER×18, MUSKETEER×18, SMALL_TANK×20, DRAGOONER×26, NINJA×17, CONDOTTERI×17, MUSKETEER×18, CARGO×24, CARGO×20 |
| 🟩 | Clumsy Attackers | random | Renaissance 96%, Industrial 4% | 🟠 8/24 (33%) | SOLDIER×6, THE_KING×1 | DRAGOONER×24, NINJA×19, CARGO×20, DRAGOONER×24, CARGO×24, THE_KING×999, NINJA×25, MUSKETEER×20, SOLDIER×16, TRANSPORTER×20, MUSKETEER×16, DRAGOONER×20, CARGO×16, TRANSPORTER×20, MUSKETEER×20, MUSKETEER×21 |
| 🟩 | Hungry Invaders | random | Renaissance 97%, Industrial 3% | 🟡 15/24 (62%) | SOLDIER×5, MUSKETEER×4 | DRAGOONER×20, MUSKETEER×21, NINJA×17, DRAGOONER×22, MUSKETEER×22, CARGO×20, NINJA×18, THE_KING×999, DRAGOONER×24, MUSKETEER×23, MUSKETEER×21, DRAGOONER×22, SOLDIER×24, CARGO×20, SMALL_TANK×16, NINJA×24 |
| 🟩 | Clumsy Attackers | random | Renaissance 94%, Industrial 3%, Medieval 3% | 🟡 17/24 (71%) | SOLDIER×7 | MUSKETEER×21, NINJA×21, CARGO×20, CARGO×24, DRAGOONER×18, THE_KING×999, NINJA×24, KNIGHT×21, TRANSPORTER×20, CARGO×20, DRAGOONER×18, KNIGHT×18, NINJA×25, NINJA×21, MOTORBIKE×20 |
| 🟩 | Clumsy Attackers | random | Renaissance 96%, Industrial 2%, Medieval 2% | 🟢 24/24 (100%) |  | CRUSADER×25, DRAGOONER×24, CARGO×16, DRAGOONER×20, MUSKETEER×22, NINJA×22, NINJA×17, DRAGOONER×26, NINJA×21, MUSKETEER×18, MUSKETEER×21, NINJA×23, THE_KING×999, MOTORBIKE×26 |

#### Full Heavy Medieval

| Tower Era Distribution (45 towers) | Towers |
|---|---|
| Medieval 84% (38), Renaissance 16% (7) | HEAVY_TOWER×38, ICE_TOWER×7 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟥 | Renaissance Force | hardcoded | Renaissance 96%, Industrial 4% | ⬛ 0/28 (0%) | SMALL_TANK×10, MUSKETEER×4, DRAGOONER×2 | MUSKETEER×16, DRAGOONER×17, NINJA×17, NINJA×18, MUSKETEER×19, MUSKETEER×19, MUSKETEER×20, SMALL_TANK×22, MUSKETEER×21, DRAGOONER×22, NINJA×23, DRAGOONER×20, DRAGOONER×24, NINJA×28, DRAGOONER×30, DRAGOONER×32, CARGO×32, CARGO×34, THE_KING×36, MUSKETEER×35, DRAGOONER×36, DRAGOONER×35 |
| 🟥 | Musketeer Brigade | hardcoded | Renaissance 98%, Industrial 2% | ⬛ 0/28 (0%) | MUSKETEER×12, NINJA×6, THE_KING×1 | MUSKETEER×16, DRAGOONER×17, DRAGOONER×17, CARGO×18, DRAGOONER×19, NINJA×19, MUSKETEER×20, CARGO×21, MUSKETEER×21, DRAGOONER×22, MOTORBIKE×12, NINJA×23, MUSKETEER×24, CARGO×28, THE_KING×30, CARGO×32, NINJA×34, MUSKETEER×36, MUSKETEER×36, NINJA×35, NINJA×38, DRAGOONER×34 |
| 🟥 | Ninja Infiltration | hardcoded | Renaissance 96%, Industrial 4% | ⬛ 0/28 (0%) | DRAGOONER×10, MUSKETEER×8 | NINJA×16, DRAGOONER×17, DRAGOONER×17, NINJA×18, MUSKETEER×19, CARGO×19, DRAGOONER×20, DRAGOONER×21, DRAGOONER×21, MUSKETEER×22, CARGO×23, CARGO×23, NINJA×33, NINJA×28, CARGO×30, CARGO×32, MUSKETEER×34, DRAGOONER×36, THE_KING×38, NINJA×36, NINJA×35, SOLDIER×22 |
| 🟥 | Cannon Barrage | hardcoded | Renaissance 96%, Industrial 4% | ⬛ 0/28 (0%) | SOLDIER×10, DRAGOONER×4, THE_KING×1 | MUSKETEER×16, DRAGOONER×17, CARGO×17, MUSKETEER×18, NINJA×19, NINJA×19, MUSKETEER×20, DRAGOONER×21, NINJA×21, NINJA×22, DRAGOONER×23, NINJA×23, MUSKETEER×24, MUSKETEER×28, THE_KING×30, NINJA×32, SOLDIER×20, DRAGOONER×36, DRAGOONER×36, DRAGOONER×36, MUSKETEER×36, MUSKETEER×35 |
| 🟥 | Rampaging Rabble | random | Renaissance 97%, Industrial 3% | ⬛ 0/28 (0%) | SMALL_TANK×8, MUSKETEER×3, THE_KING×1 | MUSKETEER×24, THE_KING×999, SMALL_TANK×20, MUSKETEER×17, CARGO×24, NINJA×20, MUSKETEER×18, DRAGOONER×24, DRAGOONER×20, MUSKETEER×17, DRAGOONER×22, NINJA×22, MUSKETEER×18, CARGO×20, TRANSPORTER×20, MUSKETEER×18 |
| 🟥 | Rampaging Rabble | random | Renaissance 97%, Industrial 3% | ⬛ 0/28 (0%) | SMALL_TANK×8, MUSKETEER×3, THE_KING×1 | MUSKETEER×24, THE_KING×999, SMALL_TANK×20, MUSKETEER×17, CARGO×24, NINJA×20, MUSKETEER×18, DRAGOONER×24, DRAGOONER×20, MUSKETEER×17, DRAGOONER×22, NINJA×22, MUSKETEER×18, CARGO×20, TRANSPORTER×20, MUSKETEER×18 |
| 🟥 | Petty Bandits | random | Renaissance 97%, Industrial 2%, Medieval 1% | ⬛ 0/28 (0%) | SOLDIER×7, MUSKETEER×3, CARGO×2, THE_KING×1 | MUSKETEER×24, DRAGOONER×18, NINJA×24, THE_KING×999, CARGO×16, DRAGOONER×20, SOLDIER×21, CARGO×20, CARGO×16, NINJA×25, MUSKETEER×22, SAMURAI×19, NINJA×18, CARGO×20, MUSKETEER×25, DRAGOONER×22 |
| 🟩 | Savage Rabble | random | Renaissance 99%, Industrial 1% | 🟠 12/28 (43%) | SMALL_TANK×6, DRAGOONER×2 | CARGO×24, MUSKETEER×23, DRAGOONER×15, CARGO×20, NINJA×17, MUSKETEER×22, MUSKETEER×18, SMALL_TANK×16, DRAGOONER×24, DRAGOONER×20, CARGO×20, MUSKETEER×23, NINJA×20, CARGO×24, MUSKETEER×23, THE_KING×999 |
| 🟩 | Noisy Barbarians | random | Renaissance 99%, Medieval 1% | 🟢 28/28 (100%) |  | MUSKETEER×24, CARGO×20, MUSKETEER×21, CONDOTTERI×20, DRAGOONER×20, MUSKETEER×24, NINJA×26, MUSKETEER×16, MUSKETEER×21, CARGO×20, NINJA×21, DRAGOONER×24, DRAGOONER×22, CARGO×16, THE_KING×999, DRAGOONER×26, DRAGOONER×24 |
| 🟩 | Rude Barbarians | random | Renaissance 95%, Medieval 5% | 🟢 28/28 (100%) |  | MUSKETEER×19, MUSKETEER×26, SAMURAI×26, MUSKETEER×23, MUSKETEER×25, KNIGHT×18, DRAGOONER×18, CARGO×20, CARGO×20, HANDGUNNER×19, MUSKETEER×16, CARGO×24, MUSKETEER×17, NINJA×24, THE_KING×999, DRAGOONER×22 |
| 🟥 | Restless Horde | random | Renaissance 97%, Industrial 3% | ⬛ 0/28 (0%) | SOLDIER×15, MUSKETEER×6, THE_KING×1 | MUSKETEER×18, NINJA×25, NINJA×21, SOLDIER×19, CARGO×24, THE_KING×999, CARGO×20, MUSKETEER×25, SOLDIER×22, CARGO×24, CARGO×24, MUSKETEER×24, DRAGOONER×20, NINJA×17, DRAGOONER×26, CARGO×20 |
| 🟥 | Blundering Invaders | random | Renaissance 95%, Industrial 5% | ⬛ 0/28 (0%) | SOLDIER×11, DRAGOONER×2, NINJA×1, MUSKETEER×1, THE_KING×1, SMALL_TANK×1 | DRAGOONER×18, NINJA×22, SOLDIER×25, THE_KING×999, CARGO×20, MUSKETEER×21, DRAGOONER×22, NINJA×25, SOLDIER×19, NINJA×20, NINJA×17, SMALL_TANK×24, MUSKETEER×26, MUSKETEER×21 |
| 🟩 | Relentless Mob | random | Renaissance 95%, Medieval 3%, Industrial 2% | 🟢 28/28 (100%) |  | NINJA×26, NINJA×21, DRAGOONER×22, DRAGOONER×20, MOTORBIKE×21, SAMURAI×21, DRAGOONER×18, DRAGOONER×18, DRAGOONER×18, CARGO×24, NINJA×16, THE_KING×999, CRUSADER×21, MUSKETEER×24 |
| 🟩 | Grumpy Marauders | random | Renaissance 95%, Medieval 5% | 🟢 28/28 (100%) |  | CARGO×24, MUSKETEER×19, CARGO×20, KNIGHT×21, MUSKETEER×25, CONDOTTERI×19, CARGO×16, DRAGOONER×22, CRUSADER×25, DRAGOONER×18, NINJA×21, THE_KING×999, CARGO×24, DRAGOONER×22 |
| 🟩 | Weary Plunderers | random | Renaissance 93%, Medieval 5%, Industrial 3% | 🔴 4/28 (14%) | MUSKETEER×11, SOLDIER×5, DRAGOONER×4 | CARGO×16, KNIGHT×18, CARGO×20, SOLDIER×17, MUSKETEER×23, CARGO×16, CRUSADER×21, NINJA×26, SOLDIER×17, MUSKETEER×24, SAMURAI×21, MUSKETEER×20, MUSKETEER×25, DRAGOONER×20, THE_KING×999, MUSKETEER×18 |
| 🟥 | Frenzied Pillagers | random | Renaissance 93%, Medieval 3%, Industrial 3% | ⬛ 0/28 (0%) | SMALL_TANK×5, MOTORBIKE×4, CONDOTTERI×1, THE_KING×1 | DRAGOONER×18, MUSKETEER×21, NINJA×19, CONDOTTERI×24, MUSKETEER×25, MOTORBIKE×17, DRAGOONER×22, KNIGHT×21, MUSKETEER×17, MUSKETEER×20, MUSKETEER×24, THE_KING×999, SMALL_TANK×26, DRAGOONER×22, MUSKETEER×22, CARGO×20 |
| 🟩 | Reckless Looters | random | Renaissance 97%, Industrial 3% | 🟢 28/28 (100%) |  | DRAGOONER×24, MOTORBIKE×19, MUSKETEER×21, NINJA×25, MOTORBIKE×18, CARGO×16, THE_KING×999, NINJA×17, MUSKETEER×20, DRAGOONER×22, MUSKETEER×17, DRAGOONER×22, DRAGOONER×24, CARGO×20, MUSKETEER×25 |
| 🟩 | Forgotten Warband | random | Renaissance 98%, Medieval 2% | 🟡 18/28 (64%) | THE_KING×1 | NINJA×17, NINJA×20, DRAGOONER×20, DRAGOONER×22, MUSKETEER×17, NINJA×22, NINJA×19, SAMURAI×23, NINJA×16, DRAGOONER×20, MUSKETEER×25, THE_KING×999, MUSKETEER×23, DRAGOONER×24, MUSKETEER×18, DRAGOONER×24 |
| 🟥 | Blundering Invaders | random | Renaissance 96%, Industrial 3%, Medieval 1% | ⬛ 0/28 (0%) | SOLDIER×15, MUSKETEER×4, THE_KING×1 | CARGO×24, SOLDIER×22, MUSKETEER×23, KNIGHT×18, MUSKETEER×24, SOLDIER×18, THE_KING×999, CARGO×16, MUSKETEER×26, MUSKETEER×25, NINJA×19, DRAGOONER×24, NINJA×18, MUSKETEER×17, NINJA×22 |
| 🟩 | Rude Barbarians | random | Renaissance 97%, Industrial 2%, Medieval 1% | 🟠 12/28 (43%) | SMALL_TANK×8 | THE_KING×999, NINJA×16, MUSKETEER×16, NINJA×17, NINJA×20, DRAGOONER×18, MUSKETEER×18, SMALL_TANK×20, DRAGOONER×26, NINJA×17, CONDOTTERI×17, MUSKETEER×18, CARGO×24, CARGO×20 |
| 🟥 | Clumsy Attackers | random | Renaissance 96%, Industrial 4% | ⬛ 0/28 (0%) | SOLDIER×18, THE_KING×1 | DRAGOONER×24, NINJA×19, CARGO×20, DRAGOONER×24, CARGO×24, THE_KING×999, NINJA×25, MUSKETEER×20, SOLDIER×16, TRANSPORTER×20, MUSKETEER×16, DRAGOONER×20, CARGO×16, TRANSPORTER×20, MUSKETEER×20, MUSKETEER×21 |
| 🟥 | Hungry Invaders | random | Renaissance 97%, Industrial 3% | ⬛ 0/28 (0%) | SOLDIER×12, MUSKETEER×2, CARGO×1, THE_KING×1 | DRAGOONER×20, MUSKETEER×21, NINJA×17, DRAGOONER×22, MUSKETEER×22, CARGO×20, NINJA×18, THE_KING×999, DRAGOONER×24, MUSKETEER×23, MUSKETEER×21, DRAGOONER×22, SOLDIER×24, CARGO×20, SMALL_TANK×16, NINJA×24 |
| 🟩 | Clumsy Attackers | random | Renaissance 94%, Industrial 3%, Medieval 3% | 🟡 17/28 (61%) | SOLDIER×11 | MUSKETEER×21, NINJA×21, CARGO×20, CARGO×24, DRAGOONER×18, THE_KING×999, NINJA×24, KNIGHT×21, TRANSPORTER×20, CARGO×20, DRAGOONER×18, KNIGHT×18, NINJA×25, NINJA×21, MOTORBIKE×20 |
| 🟩 | Clumsy Attackers | random | Renaissance 96%, Industrial 2%, Medieval 2% | 🟢 28/28 (100%) |  | CRUSADER×25, DRAGOONER×24, CARGO×16, DRAGOONER×20, MUSKETEER×22, NINJA×22, NINJA×17, DRAGOONER×26, NINJA×21, MUSKETEER×18, MUSKETEER×21, NINJA×23, THE_KING×999, MOTORBIKE×26 |

#### Full Rifle

| Tower Era Distribution (35 towers) | Towers |
|---|---|
| Renaissance 80% (28), Medieval 20% (7) | RIFLE_TOWER×28, TAR_TOWER×7 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Renaissance Force | hardcoded | Renaissance 96%, Industrial 4% | 🟡 12/16 (75%) | SMALL_TANK×2 | MUSKETEER×16, DRAGOONER×17, NINJA×17, NINJA×18, MUSKETEER×19, MUSKETEER×19, MUSKETEER×20, SMALL_TANK×22, MUSKETEER×21, DRAGOONER×22, NINJA×23, DRAGOONER×20, DRAGOONER×24, NINJA×28, DRAGOONER×30, DRAGOONER×32, CARGO×32, CARGO×34, THE_KING×36, MUSKETEER×35, DRAGOONER×36, DRAGOONER×35 |
| 🟩 | Musketeer Brigade | hardcoded | Renaissance 98%, Industrial 2% | 🟢 16/16 (100%) |  | MUSKETEER×16, DRAGOONER×17, DRAGOONER×17, CARGO×18, DRAGOONER×19, NINJA×19, MUSKETEER×20, CARGO×21, MUSKETEER×21, DRAGOONER×22, MOTORBIKE×12, NINJA×23, MUSKETEER×24, CARGO×28, THE_KING×30, CARGO×32, NINJA×34, MUSKETEER×36, MUSKETEER×36, NINJA×35, NINJA×38, DRAGOONER×34 |
| 🟩 | Ninja Infiltration | hardcoded | Renaissance 96%, Industrial 4% | 🟢 16/16 (100%) |  | NINJA×16, DRAGOONER×17, DRAGOONER×17, NINJA×18, MUSKETEER×19, CARGO×19, DRAGOONER×20, DRAGOONER×21, DRAGOONER×21, MUSKETEER×22, CARGO×23, CARGO×23, NINJA×33, NINJA×28, CARGO×30, CARGO×32, MUSKETEER×34, DRAGOONER×36, THE_KING×38, NINJA×36, NINJA×35, SOLDIER×22 |
| 🟩 | Cannon Barrage | hardcoded | Renaissance 96%, Industrial 4% | 🟢 16/16 (100%) |  | MUSKETEER×16, DRAGOONER×17, CARGO×17, MUSKETEER×18, NINJA×19, NINJA×19, MUSKETEER×20, DRAGOONER×21, NINJA×21, NINJA×22, DRAGOONER×23, NINJA×23, MUSKETEER×24, MUSKETEER×28, THE_KING×30, NINJA×32, SOLDIER×20, DRAGOONER×36, DRAGOONER×36, DRAGOONER×36, MUSKETEER×36, MUSKETEER×35 |
| 🟩 | Rampaging Rabble | random | Renaissance 97%, Industrial 3% | 🟠 4/16 (25%) | SMALL_TANK×6 | MUSKETEER×24, THE_KING×999, SMALL_TANK×20, MUSKETEER×17, CARGO×24, NINJA×20, MUSKETEER×18, DRAGOONER×24, DRAGOONER×20, MUSKETEER×17, DRAGOONER×22, NINJA×22, MUSKETEER×18, CARGO×20, TRANSPORTER×20, MUSKETEER×18 |
| 🟩 | Rampaging Rabble | random | Renaissance 97%, Industrial 3% | 🟠 4/16 (25%) | SMALL_TANK×6 | MUSKETEER×24, THE_KING×999, SMALL_TANK×20, MUSKETEER×17, CARGO×24, NINJA×20, MUSKETEER×18, DRAGOONER×24, DRAGOONER×20, MUSKETEER×17, DRAGOONER×22, NINJA×22, MUSKETEER×18, CARGO×20, TRANSPORTER×20, MUSKETEER×18 |
| 🟩 | Petty Bandits | random | Renaissance 97%, Industrial 2%, Medieval 1% | 🟢 16/16 (100%) |  | MUSKETEER×24, DRAGOONER×18, NINJA×24, THE_KING×999, CARGO×16, DRAGOONER×20, SOLDIER×21, CARGO×20, CARGO×16, NINJA×25, MUSKETEER×22, SAMURAI×19, NINJA×18, CARGO×20, MUSKETEER×25, DRAGOONER×22 |
| 🟩 | Savage Rabble | random | Renaissance 99%, Industrial 1% | 🟢 16/16 (100%) |  | CARGO×24, MUSKETEER×23, DRAGOONER×15, CARGO×20, NINJA×17, MUSKETEER×22, MUSKETEER×18, SMALL_TANK×16, DRAGOONER×24, DRAGOONER×20, CARGO×20, MUSKETEER×23, NINJA×20, CARGO×24, MUSKETEER×23, THE_KING×999 |
| 🟩 | Noisy Barbarians | random | Renaissance 99%, Medieval 1% | 🟢 16/16 (100%) |  | MUSKETEER×24, CARGO×20, MUSKETEER×21, CONDOTTERI×20, DRAGOONER×20, MUSKETEER×24, NINJA×26, MUSKETEER×16, MUSKETEER×21, CARGO×20, NINJA×21, DRAGOONER×24, DRAGOONER×22, CARGO×16, THE_KING×999, DRAGOONER×26, DRAGOONER×24 |
| 🟩 | Rude Barbarians | random | Renaissance 95%, Medieval 5% | 🟢 16/16 (100%) |  | MUSKETEER×19, MUSKETEER×26, SAMURAI×26, MUSKETEER×23, MUSKETEER×25, KNIGHT×18, DRAGOONER×18, CARGO×20, CARGO×20, HANDGUNNER×19, MUSKETEER×16, CARGO×24, MUSKETEER×17, NINJA×24, THE_KING×999, DRAGOONER×22 |
| 🟩 | Restless Horde | random | Renaissance 97%, Industrial 3% | 🟢 16/16 (100%) |  | MUSKETEER×18, NINJA×25, NINJA×21, SOLDIER×19, CARGO×24, THE_KING×999, CARGO×20, MUSKETEER×25, SOLDIER×22, CARGO×24, CARGO×24, MUSKETEER×24, DRAGOONER×20, NINJA×17, DRAGOONER×26, CARGO×20 |
| 🟩 | Blundering Invaders | random | Renaissance 95%, Industrial 5% | 🟡 10/16 (62%) | SMALL_TANK×3 | DRAGOONER×18, NINJA×22, SOLDIER×25, THE_KING×999, CARGO×20, MUSKETEER×21, DRAGOONER×22, NINJA×25, SOLDIER×19, NINJA×20, NINJA×17, SMALL_TANK×24, MUSKETEER×26, MUSKETEER×21 |
| 🟩 | Relentless Mob | random | Renaissance 95%, Medieval 3%, Industrial 2% | 🟢 16/16 (100%) |  | NINJA×26, NINJA×21, DRAGOONER×22, DRAGOONER×20, MOTORBIKE×21, SAMURAI×21, DRAGOONER×18, DRAGOONER×18, DRAGOONER×18, CARGO×24, NINJA×16, THE_KING×999, CRUSADER×21, MUSKETEER×24 |
| 🟩 | Grumpy Marauders | random | Renaissance 95%, Medieval 5% | 🟢 16/16 (100%) |  | CARGO×24, MUSKETEER×19, CARGO×20, KNIGHT×21, MUSKETEER×25, CONDOTTERI×19, CARGO×16, DRAGOONER×22, CRUSADER×25, DRAGOONER×18, NINJA×21, THE_KING×999, CARGO×24, DRAGOONER×22 |
| 🟩 | Weary Plunderers | random | Renaissance 93%, Medieval 5%, Industrial 3% | 🟢 16/16 (100%) |  | CARGO×16, KNIGHT×18, CARGO×20, SOLDIER×17, MUSKETEER×23, CARGO×16, CRUSADER×21, NINJA×26, SOLDIER×17, MUSKETEER×24, SAMURAI×21, MUSKETEER×20, MUSKETEER×25, DRAGOONER×20, THE_KING×999, MUSKETEER×18 |
| 🟥 | Frenzied Pillagers | random | Renaissance 93%, Medieval 3%, Industrial 3% | ⬛ 0/16 (0%) | SMALL_TANK×8 | DRAGOONER×18, MUSKETEER×21, NINJA×19, CONDOTTERI×24, MUSKETEER×25, MOTORBIKE×17, DRAGOONER×22, KNIGHT×21, MUSKETEER×17, MUSKETEER×20, MUSKETEER×24, THE_KING×999, SMALL_TANK×26, DRAGOONER×22, MUSKETEER×22, CARGO×20 |
| 🟩 | Reckless Looters | random | Renaissance 97%, Industrial 3% | 🟢 16/16 (100%) |  | DRAGOONER×24, MOTORBIKE×19, MUSKETEER×21, NINJA×25, MOTORBIKE×18, CARGO×16, THE_KING×999, NINJA×17, MUSKETEER×20, DRAGOONER×22, MUSKETEER×17, DRAGOONER×22, DRAGOONER×24, CARGO×20, MUSKETEER×25 |
| 🟩 | Forgotten Warband | random | Renaissance 98%, Medieval 2% | 🟢 16/16 (100%) |  | NINJA×17, NINJA×20, DRAGOONER×20, DRAGOONER×22, MUSKETEER×17, NINJA×22, NINJA×19, SAMURAI×23, NINJA×16, DRAGOONER×20, MUSKETEER×25, THE_KING×999, MUSKETEER×23, DRAGOONER×24, MUSKETEER×18, DRAGOONER×24 |
| 🟩 | Blundering Invaders | random | Renaissance 96%, Industrial 3%, Medieval 1% | 🟢 16/16 (100%) |  | CARGO×24, SOLDIER×22, MUSKETEER×23, KNIGHT×18, MUSKETEER×24, SOLDIER×18, THE_KING×999, CARGO×16, MUSKETEER×26, MUSKETEER×25, NINJA×19, DRAGOONER×24, NINJA×18, MUSKETEER×17, NINJA×22 |
| 🟩 | Rude Barbarians | random | Renaissance 97%, Industrial 2%, Medieval 1% | 🟡 10/16 (62%) | SMALL_TANK×3 | THE_KING×999, NINJA×16, MUSKETEER×16, NINJA×17, NINJA×20, DRAGOONER×18, MUSKETEER×18, SMALL_TANK×20, DRAGOONER×26, NINJA×17, CONDOTTERI×17, MUSKETEER×18, CARGO×24, CARGO×20 |
| 🟩 | Clumsy Attackers | random | Renaissance 96%, Industrial 4% | 🟢 16/16 (100%) |  | DRAGOONER×24, NINJA×19, CARGO×20, DRAGOONER×24, CARGO×24, THE_KING×999, NINJA×25, MUSKETEER×20, SOLDIER×16, TRANSPORTER×20, MUSKETEER×16, DRAGOONER×20, CARGO×16, TRANSPORTER×20, MUSKETEER×20, MUSKETEER×21 |
| 🟩 | Hungry Invaders | random | Renaissance 97%, Industrial 3% | 🟢 16/16 (100%) |  | DRAGOONER×20, MUSKETEER×21, NINJA×17, DRAGOONER×22, MUSKETEER×22, CARGO×20, NINJA×18, THE_KING×999, DRAGOONER×24, MUSKETEER×23, MUSKETEER×21, DRAGOONER×22, SOLDIER×24, CARGO×20, SMALL_TANK×16, NINJA×24 |
| 🟩 | Clumsy Attackers | random | Renaissance 94%, Industrial 3%, Medieval 3% | 🟢 16/16 (100%) |  | MUSKETEER×21, NINJA×21, CARGO×20, CARGO×24, DRAGOONER×18, THE_KING×999, NINJA×24, KNIGHT×21, TRANSPORTER×20, CARGO×20, DRAGOONER×18, KNIGHT×18, NINJA×25, NINJA×21, MOTORBIKE×20 |
| 🟩 | Clumsy Attackers | random | Renaissance 96%, Industrial 2%, Medieval 2% | 🟢 16/16 (100%) |  | CRUSADER×25, DRAGOONER×24, CARGO×16, DRAGOONER×20, MUSKETEER×22, NINJA×22, NINJA×17, DRAGOONER×26, NINJA×21, MUSKETEER×18, MUSKETEER×21, NINJA×23, THE_KING×999, MOTORBIKE×26 |

### Industrial

#### Flame/Gatling

| Tower Era Distribution (35 towers) | Towers |
|---|---|
| Industrial 91% (32), Iron Age 9% (3) | FLAME_THROWER×16, GATLING_TOWER×16, COLD_TOWER×3 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Industrial March | hardcoded | Industrial 98%, Modern 2% | 🟡 18/28 (64%) | SOLDIER×10 | SOLDIER×16, SOLDIER×17, MOTORBIKE×17, TRANSPORTER×18, TRANSPORTER×19, SMALL_TANK×19, TRANSPORTER×20, TRANSPORTER×21, SMALL_TANK×21, SMALL_TANK×22, MOTORBIKE×23, MOTORBIKE×23, SPECOPS×10, MOTORBIKE×28, SMALL_TANK×30, SOLDIER×32, SOLDIER×34, TRANSPORTER×36, TRANSPORTER×38, TRANSPORTER×40, MOTORBIKE×36 |
| 🟩 | Mechanized Strike | hardcoded | Industrial 100% | 🟢 27/28 (96%) | SOLDIER×1 | SOLDIER×18, SMALL_TANK×19, TRANSPORTER×19, SMALL_TANK×20, TRANSPORTER×21, SMALL_TANK×21, SOLDIER×22, SOLDIER×22, TRANSPORTER×23, MOTORBIKE×24, SMALL_TANK×24, MOTORBIKE×25, TRANSPORTER×26, TRANSPORTER×26, SOLDIER×27, SOLDIER×27, SMALL_TANK×28, SMALL_TANK×29, SMALL_TANK×29, TRANSPORTER×30, MOTORBIKE×34, SMALL_TANK×35, SOLDIER×35 |
| 🟩 | Steam Assault | hardcoded | Industrial 100% | 🟢 26/28 (93%) | SOLDIER×2 | TRANSPORTER×18, SOLDIER×19, SOLDIER×19, SMALL_TANK×20, TRANSPORTER×21, SOLDIER×21, SOLDIER×22, SMALL_TANK×22, TRANSPORTER×23, SMALL_TANK×24, TRANSPORTER×24, SMALL_TANK×25, SOLDIER×26, TRANSPORTER×26, SMALL_TANK×27, MOTORBIKE×27, SOLDIER×28, TRANSPORTER×29, SOLDIER×29, MOTORBIKE×30, SMALL_TANK×33, TRANSPORTER×35, TRANSPORTER×37 |
| 🟩 | Tank Column | hardcoded | Industrial 100% | 🟢 26/28 (93%) | SOLDIER×2 | SMALL_TANK×18, MOTORBIKE×19, MOTORBIKE×19, TRANSPORTER×20, TRANSPORTER×21, TRANSPORTER×21, SOLDIER×22, MOTORBIKE×22, TRANSPORTER×23, TRANSPORTER×24, SMALL_TANK×24, MOTORBIKE×25, TRANSPORTER×26, SMALL_TANK×26, TRANSPORTER×27, SMALL_TANK×27, TRANSPORTER×28, MOTORBIKE×29, MOTORBIKE×29, SOLDIER×30, SOLDIER×34, SOLDIER×36, TRANSPORTER×38, SOLDIER×34 |
| 🟩 | Factory Raid | hardcoded | Industrial 88%, Renaissance 10%, Modern 2% | 🟢 28/28 (100%) |  | MOTORBIKE×18, MOTORBIKE×20, MOTORBIKE×20, MOTORBIKE×22, SOLDIER×20, TRANSPORTER×21, MOTORBIKE×22, SMALL_TANK×22, SMALL_TANK×25, SOLDIER×24, MOTORBIKE×24, TRANSPORTER×25, SMALL_TANK×26, SMALL_TANK×28, MOTORBIKE×30, CARGO×30, TRANSPORTER×32, DRAGOONER×34, HELI×13, TRANSPORTER×38, SMALL_TANK×38, SOLDIER×36, SMALL_TANK×33, SMALL_TANK×36 |
| 🟩 | Reckless Looters | random | Modern 72%, Industrial 26%, Renaissance 2% | 🟢 28/28 (100%) |  | TRANSPORTER×20, SOLDIER×25, TRANSPORTER×20, SMALL_TANK×28, TRANSPORTER×20, TRANSPORTER×30, SOLDIER×19, MOTORBIKE×26, MUSKETEER×29, SOLDIER×24, MOTORBIKE×27, SOLDIER×28, MOTORBIKE×21, THE_GENERAL×999, SMALL_TANK×24, SOLDIER×27, MOTORBIKE×20 |
| 🟩 | Reckless Looters | random | Modern 72%, Industrial 26%, Renaissance 2% | 🟢 28/28 (100%) |  | TRANSPORTER×20, SOLDIER×25, TRANSPORTER×20, SMALL_TANK×28, TRANSPORTER×20, TRANSPORTER×30, SOLDIER×19, MOTORBIKE×26, MUSKETEER×29, SOLDIER×24, MOTORBIKE×27, SOLDIER×28, MOTORBIKE×21, THE_GENERAL×999, SMALL_TANK×24, SOLDIER×27, MOTORBIKE×20 |
| 🟩 | Reckless Looters | random | Renaissance 72%, Industrial 28% | 🟢 28/28 (100%) |  | SOLDIER×29, MOTORBIKE×32, MOTORBIKE×29, SOLDIER×20, SOLDIER×24, SOLDIER×31, SOLDIER×18, MUSKETEER×19, SOLDIER×27, SMALL_TANK×24, TRANSPORTER×30, TRANSPORTER×20, MOTORBIKE×19, SOLDIER×25, SMALL_TANK×30, SMALL_TANK×32, THE_KING×999 |
| 🟩 | Stubborn Raiders | random | Renaissance 71%, Industrial 27%, Modern 2% | 🟢 28/28 (100%) |  | SIEGE_TANK×24, MOTORBIKE×25, THE_KING×999, SMALL_TANK×26, MOTORBIKE×29, TRANSPORTER×20, SOLDIER×22, SMALL_TANK×20, SOLDIER×28, SMALL_TANK×20, SOLDIER×29, TRANSPORTER×20, SMALL_TANK×22, MOTORBIKE×31, SOLDIER×30, TRANSPORTER×30, MOTORBIKE×28 |
| 🟩 | Shrieking Horde | random | Industrial 91%, Renaissance 9% | 🟢 28/28 (100%) |  | MOTORBIKE×28, SMALL_TANK×28, MOTORBIKE×23, SMALL_TANK×24, SOLDIER×29, MUSKETEER×23, SOLDIER×21, TRANSPORTER×20, TRANSPORTER×30, SMALL_TANK×20, SMALL_TANK×28, MOTORBIKE×24, MUSKETEER×19, SOLDIER×25, TRANSPORTER×30, TRANSPORTER×30, MOTORBIKE×28, TRANSPORTER×30 |
| 🟩 | Restless Horde | random | Renaissance 76%, Industrial 24% | 🟢 28/28 (100%) |  | SOLDIER×25, SMALL_TANK×22, MUSKETEER×32, SMALL_TANK×20, MUSKETEER×23, CARGO×24, MOTORBIKE×31, SMALL_TANK×28, SOLDIER×25, SMALL_TANK×28, MOTORBIKE×29, SOLDIER×29, MOTORBIKE×31, TRANSPORTER×20, SOLDIER×22, THE_KING×999, SOLDIER×29 |
| 🟩 | Ragged Warband | random | Modern 71%, Industrial 27%, Renaissance 1% | 🟢 28/28 (100%) |  | MOTORBIKE×18, SOLDIER×26, SOLDIER×31, TRANSPORTER×30, SMALL_TANK×20, SOLDIER×18, NINJA×21, THE_GENERAL×999, TRANSPORTER×30, SOLDIER×24, TRANSPORTER×20, TRANSPORTER×30, MOTORBIKE×24, TRANSPORTER×30, SOLDIER×32, TRANSPORTER×20, TRANSPORTER×30 |
| 🟩 | Disorganized Mob | random | Modern 78%, Industrial 21%, Renaissance 1% | 🟢 28/28 (100%) |  | MOTORBIKE×22, SOLDIER×29, DRAGOONER×20, SMALL_TANK×22, SMALL_TANK×20, SPECOPS×27, SMALL_TANK×22, SOLDIER×26, MOTORBIKE×25, SMALL_TANK×26, TRANSPORTER×20, MOTORBIKE×26, TRANSPORTER×20, THE_GENERAL×999, SOLDIER×20 |
| 🟩 | Petty Bandits | random | Industrial 82%, Renaissance 18% | 🟢 28/28 (100%) |  | SOLDIER×25, MOTORBIKE×29, SOLDIER×20, SOLDIER×20, SOLDIER×26, MOTORBIKE×29, SMALL_TANK×26, CARGO×24, SOLDIER×25, MUSKETEER×20, MOTORBIKE×23, SOLDIER×26, TRANSPORTER×30, MUSKETEER×22, TRANSPORTER×20 |
| 🟩 | Crude Invaders | random | Renaissance 79%, Industrial 21% | 🟢 28/28 (100%) |  | SMALL_TANK×22, SMALL_TANK×26, SMALL_TANK×22, NINJA×19, MOTORBIKE×25, TRANSPORTER×30, MUSKETEER×25, THE_KING×999, SOLDIER×27, SMALL_TANK×28, TRANSPORTER×20, TRANSPORTER×30, TRANSPORTER×20, MOTORBIKE×30, CARGO×20 |
| 🟩 | Forgotten Warband | random | Renaissance 78%, Industrial 19%, Modern 3% | 🟢 28/28 (100%) |  | SIEGE_TANK×20, MOTORBIKE×24, NINJA×23, TRANSPORTER×30, SIEGE_TANK×20, TRANSPORTER×20, MUSKETEER×19, THE_KING×999, SOLDIER×18, SMALL_TANK×26, SOLDIER×23, MOTORBIKE×21, MOTORBIKE×22, SOLDIER×23, TRANSPORTER×20, TRANSPORTER×30, MUSKETEER×19 |
| 🟩 | Forgotten Warband | random | Renaissance 76%, Industrial 23%, Modern 1% | 🟢 28/28 (100%) |  | SIEGE_TANK×20, TRANSPORTER×30, SOLDIER×20, TRANSPORTER×20, SMALL_TANK×26, DRAGOONER×31, MOTORBIKE×24, SMALL_TANK×30, MOTORBIKE×25, DRAGOONER×22, SOLDIER×26, SMALL_TANK×20, SMALL_TANK×24, THE_KING×999, MOTORBIKE×26, SMALL_TANK×28, TRANSPORTER×20 |
| 🟩 | Drunken Raiders | random | Renaissance 74%, Industrial 24%, Modern 2% | 🟢 28/28 (100%) |  | SMALL_TANK×26, THE_KING×999, TRANSPORTER×20, SMALL_TANK×26, SMALL_TANK×28, MOTORBIKE×21, SOLDIER×22, SOLDIER×24, TRANSPORTER×20, SOLDIER×28, SOLDIER×22, MOTORBIKE×23, SMALL_TANK×18, SPECOPS×27, TRANSPORTER×30, TRANSPORTER×20 |
| 🟩 | Unlucky Raiders | random | Industrial 89%, Renaissance 11% | 🟢 28/28 (100%) |  | SOLDIER×26, SMALL_TANK×24, NINJA×22, MOTORBIKE×26, TRANSPORTER×30, SMALL_TANK×22, DRAGOONER×22, TRANSPORTER×20, MOTORBIKE×19, SOLDIER×28, SOLDIER×22, TRANSPORTER×20, MOTORBIKE×26, SOLDIER×19, SMALL_TANK×20, SOLDIER×19, MOTORBIKE×19 |
| 🟩 | Angry Mob | random | Renaissance 76%, Industrial 23%, Modern 2% | 🟢 26/28 (93%) | SPECOPS×1 | MOTORBIKE×27, SOLDIER×20, MOTORBIKE×24, SOLDIER×19, TRANSPORTER×20, TRANSPORTER×20, SPECOPS×22, SMALL_TANK×22, SOLDIER×29, SOLDIER×31, DRAGOONER×22, TRANSPORTER×20, TRANSPORTER×30, TRANSPORTER×20, THE_KING×999, MOTORBIKE×21 |
| 🟩 | Angry Mob | random | Renaissance 77%, Industrial 21%, Modern 2% | 🔴 4/28 (14%) | SPECOPS×9, SOLDIER×6 | SOLDIER×24, TRANSPORTER×30, MOTORBIKE×19, DRAGOONER×22, MOTORBIKE×19, MOTORBIKE×23, MOTORBIKE×18, SMALL_TANK×22, THE_KING×999, MOTORBIKE×21, SOLDIER×29, SPECOPS×26, TRANSPORTER×20, SOLDIER×25, SMALL_TANK×32 |
| 🟩 | Shrieking Horde | random | Renaissance 72%, Industrial 25%, Modern 4% | 🟡 22/28 (79%) | SOLDIER×6 | TRANSPORTER×20, SMALL_TANK×20, SOLDIER×22, HELI×26, MOTORBIKE×23, TRANSPORTER×20, TRANSPORTER×20, SOLDIER×28, SOLDIER×31, SOLDIER×30, MOTORBIKE×30, HELI×24, THE_KING×999, MOTORBIKE×26, SMALL_TANK×30, TRANSPORTER×20, MOTORBIKE×27 |
| 🟩 | Reckless Looters | random | Modern 72%, Industrial 26%, Renaissance 1% | 🟢 28/28 (100%) |  | SMALL_TANK×30, CARGO×20, MOTORBIKE×24, MOTORBIKE×21, SOLDIER×21, SOLDIER×30, SMALL_TANK×26, SMALL_TANK×22, SMALL_TANK×26, MOTORBIKE×28, SOLDIER×19, SMALL_TANK×26, THE_GENERAL×999, SMALL_TANK×22, MOTORBIKE×19, TRANSPORTER×20, SOLDIER×27 |
| 🟩 | Noisy Barbarians | random | Industrial 72%, Renaissance 20%, Modern 7% | 🟢 28/28 (100%) |  | MOTORBIKE×20, SOLDIER×29, SMALL_TANK×20, SMALL_TANK×30, NINJA×31, SOLDIER×20, SMALL_TANK×24, SOLDIER×31, SIEGE_TANK×30, SMALL_TANK×28, MOTORBIKE×27, TRANSPORTER×20, SMALL_TANK×20, NINJA×29, TRANSPORTER×20, NINJA×22 |
| 🟩 | Frenzied Pillagers | random | Industrial 80%, Renaissance 14%, Modern 6% | 🟢 24/28 (86%) | SPECOPS×2 | MOTORBIKE×26, SOLDIER×19, CARGO×32, SMALL_TANK×28, MOTORBIKE×26, MOTORBIKE×27, SMALL_TANK×26, SOLDIER×27, TRANSPORTER×20, SOLDIER×19, SPECOPS×20, TRANSPORTER×30, MOTORBIKE×20, CARGO×20, TRANSPORTER×20 |

#### Indy / Renaissance

| Tower Era Distribution (28 towers) | Towers |
|---|---|
| Renaissance 46% (13), Industrial 46% (13), Iron Age 7% (2) | RIFLE_TOWER×10, FLAME_THROWER×8, GATLING_TOWER×5, ICE_TOWER×3, COLD_TOWER×2 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Industrial March | hardcoded | Industrial 98%, Modern 2% | 🔴 2/16 (12%) | SOLDIER×14 | SOLDIER×16, SOLDIER×17, MOTORBIKE×17, TRANSPORTER×18, TRANSPORTER×19, SMALL_TANK×19, TRANSPORTER×20, TRANSPORTER×21, SMALL_TANK×21, SMALL_TANK×22, MOTORBIKE×23, MOTORBIKE×23, SPECOPS×10, MOTORBIKE×28, SMALL_TANK×30, SOLDIER×32, SOLDIER×34, TRANSPORTER×36, TRANSPORTER×38, TRANSPORTER×40, MOTORBIKE×36 |
| 🟩 | Mechanized Strike | hardcoded | Industrial 100% | 🟢 16/16 (100%) |  | SOLDIER×18, SMALL_TANK×19, TRANSPORTER×19, SMALL_TANK×20, TRANSPORTER×21, SMALL_TANK×21, SOLDIER×22, SOLDIER×22, TRANSPORTER×23, MOTORBIKE×24, SMALL_TANK×24, MOTORBIKE×25, TRANSPORTER×26, TRANSPORTER×26, SOLDIER×27, SOLDIER×27, SMALL_TANK×28, SMALL_TANK×29, SMALL_TANK×29, TRANSPORTER×30, MOTORBIKE×34, SMALL_TANK×35, SOLDIER×35 |
| 🟩 | Steam Assault | hardcoded | Industrial 100% | 🟡 8/16 (50%) | SOLDIER×8 | TRANSPORTER×18, SOLDIER×19, SOLDIER×19, SMALL_TANK×20, TRANSPORTER×21, SOLDIER×21, SOLDIER×22, SMALL_TANK×22, TRANSPORTER×23, SMALL_TANK×24, TRANSPORTER×24, SMALL_TANK×25, SOLDIER×26, TRANSPORTER×26, SMALL_TANK×27, MOTORBIKE×27, SOLDIER×28, TRANSPORTER×29, SOLDIER×29, MOTORBIKE×30, SMALL_TANK×33, TRANSPORTER×35, TRANSPORTER×37 |
| 🟩 | Tank Column | hardcoded | Industrial 100% | 🟢 13/16 (81%) | SOLDIER×3 | SMALL_TANK×18, MOTORBIKE×19, MOTORBIKE×19, TRANSPORTER×20, TRANSPORTER×21, TRANSPORTER×21, SOLDIER×22, MOTORBIKE×22, TRANSPORTER×23, TRANSPORTER×24, SMALL_TANK×24, MOTORBIKE×25, TRANSPORTER×26, SMALL_TANK×26, TRANSPORTER×27, SMALL_TANK×27, TRANSPORTER×28, MOTORBIKE×29, MOTORBIKE×29, SOLDIER×30, SOLDIER×34, SOLDIER×36, TRANSPORTER×38, SOLDIER×34 |
| 🟩 | Factory Raid | hardcoded | Industrial 88%, Renaissance 10%, Modern 2% | 🟢 13/16 (81%) | SOLDIER×3 | MOTORBIKE×18, MOTORBIKE×20, MOTORBIKE×20, MOTORBIKE×22, SOLDIER×20, TRANSPORTER×21, MOTORBIKE×22, SMALL_TANK×22, SMALL_TANK×25, SOLDIER×24, MOTORBIKE×24, TRANSPORTER×25, SMALL_TANK×26, SMALL_TANK×28, MOTORBIKE×30, CARGO×30, TRANSPORTER×32, DRAGOONER×34, HELI×13, TRANSPORTER×38, SMALL_TANK×38, SOLDIER×36, SMALL_TANK×33, SMALL_TANK×36 |
| 🟩 | Reckless Looters | random | Modern 72%, Industrial 26%, Renaissance 2% | 🟢 16/16 (100%) |  | TRANSPORTER×20, SOLDIER×25, TRANSPORTER×20, SMALL_TANK×28, TRANSPORTER×20, TRANSPORTER×30, SOLDIER×19, MOTORBIKE×26, MUSKETEER×29, SOLDIER×24, MOTORBIKE×27, SOLDIER×28, MOTORBIKE×21, THE_GENERAL×999, SMALL_TANK×24, SOLDIER×27, MOTORBIKE×20 |
| 🟩 | Reckless Looters | random | Modern 72%, Industrial 26%, Renaissance 2% | 🟢 16/16 (100%) |  | TRANSPORTER×20, SOLDIER×25, TRANSPORTER×20, SMALL_TANK×28, TRANSPORTER×20, TRANSPORTER×30, SOLDIER×19, MOTORBIKE×26, MUSKETEER×29, SOLDIER×24, MOTORBIKE×27, SOLDIER×28, MOTORBIKE×21, THE_GENERAL×999, SMALL_TANK×24, SOLDIER×27, MOTORBIKE×20 |
| 🟩 | Reckless Looters | random | Renaissance 72%, Industrial 28% | 🟢 16/16 (100%) |  | SOLDIER×29, MOTORBIKE×32, MOTORBIKE×29, SOLDIER×20, SOLDIER×24, SOLDIER×31, SOLDIER×18, MUSKETEER×19, SOLDIER×27, SMALL_TANK×24, TRANSPORTER×30, TRANSPORTER×20, MOTORBIKE×19, SOLDIER×25, SMALL_TANK×30, SMALL_TANK×32, THE_KING×999 |
| 🟩 | Stubborn Raiders | random | Renaissance 71%, Industrial 27%, Modern 2% | 🟢 16/16 (100%) |  | SIEGE_TANK×24, MOTORBIKE×25, THE_KING×999, SMALL_TANK×26, MOTORBIKE×29, TRANSPORTER×20, SOLDIER×22, SMALL_TANK×20, SOLDIER×28, SMALL_TANK×20, SOLDIER×29, TRANSPORTER×20, SMALL_TANK×22, MOTORBIKE×31, SOLDIER×30, TRANSPORTER×30, MOTORBIKE×28 |
| 🟩 | Shrieking Horde | random | Industrial 91%, Renaissance 9% | 🟢 16/16 (100%) |  | MOTORBIKE×28, SMALL_TANK×28, MOTORBIKE×23, SMALL_TANK×24, SOLDIER×29, MUSKETEER×23, SOLDIER×21, TRANSPORTER×20, TRANSPORTER×30, SMALL_TANK×20, SMALL_TANK×28, MOTORBIKE×24, MUSKETEER×19, SOLDIER×25, TRANSPORTER×30, TRANSPORTER×30, MOTORBIKE×28, TRANSPORTER×30 |
| 🟩 | Restless Horde | random | Renaissance 76%, Industrial 24% | 🟢 16/16 (100%) |  | SOLDIER×25, SMALL_TANK×22, MUSKETEER×32, SMALL_TANK×20, MUSKETEER×23, CARGO×24, MOTORBIKE×31, SMALL_TANK×28, SOLDIER×25, SMALL_TANK×28, MOTORBIKE×29, SOLDIER×29, MOTORBIKE×31, TRANSPORTER×20, SOLDIER×22, THE_KING×999, SOLDIER×29 |
| 🟩 | Ragged Warband | random | Modern 71%, Industrial 27%, Renaissance 1% | 🔴 2/16 (12%) | SOLDIER×14 | MOTORBIKE×18, SOLDIER×26, SOLDIER×31, TRANSPORTER×30, SMALL_TANK×20, SOLDIER×18, NINJA×21, THE_GENERAL×999, TRANSPORTER×30, SOLDIER×24, TRANSPORTER×20, TRANSPORTER×30, MOTORBIKE×24, TRANSPORTER×30, SOLDIER×32, TRANSPORTER×20, TRANSPORTER×30 |
| 🟩 | Disorganized Mob | random | Modern 78%, Industrial 21%, Renaissance 1% | 🟡 10/16 (62%) | SPECOPS×3 | MOTORBIKE×22, SOLDIER×29, DRAGOONER×20, SMALL_TANK×22, SMALL_TANK×20, SPECOPS×27, SMALL_TANK×22, SOLDIER×26, MOTORBIKE×25, SMALL_TANK×26, TRANSPORTER×20, MOTORBIKE×26, TRANSPORTER×20, THE_GENERAL×999, SOLDIER×20 |
| 🟩 | Petty Bandits | random | Industrial 82%, Renaissance 18% | 🟢 16/16 (100%) |  | SOLDIER×25, MOTORBIKE×29, SOLDIER×20, SOLDIER×20, SOLDIER×26, MOTORBIKE×29, SMALL_TANK×26, CARGO×24, SOLDIER×25, MUSKETEER×20, MOTORBIKE×23, SOLDIER×26, TRANSPORTER×30, MUSKETEER×22, TRANSPORTER×20 |
| 🟩 | Crude Invaders | random | Renaissance 79%, Industrial 21% | 🟢 16/16 (100%) |  | SMALL_TANK×22, SMALL_TANK×26, SMALL_TANK×22, NINJA×19, MOTORBIKE×25, TRANSPORTER×30, MUSKETEER×25, THE_KING×999, SOLDIER×27, SMALL_TANK×28, TRANSPORTER×20, TRANSPORTER×30, TRANSPORTER×20, MOTORBIKE×30, CARGO×20 |
| 🟩 | Forgotten Warband | random | Renaissance 78%, Industrial 19%, Modern 3% | 🟢 16/16 (100%) |  | SIEGE_TANK×20, MOTORBIKE×24, NINJA×23, TRANSPORTER×30, SIEGE_TANK×20, TRANSPORTER×20, MUSKETEER×19, THE_KING×999, SOLDIER×18, SMALL_TANK×26, SOLDIER×23, MOTORBIKE×21, MOTORBIKE×22, SOLDIER×23, TRANSPORTER×20, TRANSPORTER×30, MUSKETEER×19 |
| 🟩 | Forgotten Warband | random | Renaissance 76%, Industrial 23%, Modern 1% | 🟢 16/16 (100%) |  | SIEGE_TANK×20, TRANSPORTER×30, SOLDIER×20, TRANSPORTER×20, SMALL_TANK×26, DRAGOONER×31, MOTORBIKE×24, SMALL_TANK×30, MOTORBIKE×25, DRAGOONER×22, SOLDIER×26, SMALL_TANK×20, SMALL_TANK×24, THE_KING×999, MOTORBIKE×26, SMALL_TANK×28, TRANSPORTER×20 |
| 🟥 | Drunken Raiders | random | Renaissance 74%, Industrial 24%, Modern 2% | ⬛ 0/16 (0%) | SPECOPS×8 | SMALL_TANK×26, THE_KING×999, TRANSPORTER×20, SMALL_TANK×26, SMALL_TANK×28, MOTORBIKE×21, SOLDIER×22, SOLDIER×24, TRANSPORTER×20, SOLDIER×28, SOLDIER×22, MOTORBIKE×23, SMALL_TANK×18, SPECOPS×27, TRANSPORTER×30, TRANSPORTER×20 |
| 🟩 | Unlucky Raiders | random | Industrial 89%, Renaissance 11% | 🟢 16/16 (100%) |  | SOLDIER×26, SMALL_TANK×24, NINJA×22, MOTORBIKE×26, TRANSPORTER×30, SMALL_TANK×22, DRAGOONER×22, TRANSPORTER×20, MOTORBIKE×19, SOLDIER×28, SOLDIER×22, TRANSPORTER×20, MOTORBIKE×26, SOLDIER×19, SMALL_TANK×20, SOLDIER×19, MOTORBIKE×19 |
| 🟩 | Angry Mob | random | Renaissance 76%, Industrial 23%, Modern 2% | 🟠 5/16 (31%) | SOLDIER×9, SPECOPS×1 | MOTORBIKE×27, SOLDIER×20, MOTORBIKE×24, SOLDIER×19, TRANSPORTER×20, TRANSPORTER×20, SPECOPS×22, SMALL_TANK×22, SOLDIER×29, SOLDIER×31, DRAGOONER×22, TRANSPORTER×20, TRANSPORTER×30, TRANSPORTER×20, THE_KING×999, MOTORBIKE×21 |
| 🟥 | Angry Mob | random | Renaissance 77%, Industrial 21%, Modern 2% | ⬛ 0/16 (0%) | SPECOPS×7, SOLDIER×3 | SOLDIER×24, TRANSPORTER×30, MOTORBIKE×19, DRAGOONER×22, MOTORBIKE×19, MOTORBIKE×23, MOTORBIKE×18, SMALL_TANK×22, THE_KING×999, MOTORBIKE×21, SOLDIER×29, SPECOPS×26, TRANSPORTER×20, SOLDIER×25, SMALL_TANK×32 |
| 🟥 | Shrieking Horde | random | Renaissance 72%, Industrial 25%, Modern 4% | ⬛ 0/16 (0%) | SOLDIER×8, HELI×2, MOTORBIKE×1 | TRANSPORTER×20, SMALL_TANK×20, SOLDIER×22, HELI×26, MOTORBIKE×23, TRANSPORTER×20, TRANSPORTER×20, SOLDIER×28, SOLDIER×31, SOLDIER×30, MOTORBIKE×30, HELI×24, THE_KING×999, MOTORBIKE×26, SMALL_TANK×30, TRANSPORTER×20, MOTORBIKE×27 |
| 🟩 | Reckless Looters | random | Modern 72%, Industrial 26%, Renaissance 1% | 🟢 16/16 (100%) |  | SMALL_TANK×30, CARGO×20, MOTORBIKE×24, MOTORBIKE×21, SOLDIER×21, SOLDIER×30, SMALL_TANK×26, SMALL_TANK×22, SMALL_TANK×26, MOTORBIKE×28, SOLDIER×19, SMALL_TANK×26, THE_GENERAL×999, SMALL_TANK×22, MOTORBIKE×19, TRANSPORTER×20, SOLDIER×27 |
| 🟩 | Noisy Barbarians | random | Industrial 72%, Renaissance 20%, Modern 7% | 🟠 4/16 (25%) | SIEGE_TANK×6 | MOTORBIKE×20, SOLDIER×29, SMALL_TANK×20, SMALL_TANK×30, NINJA×31, SOLDIER×20, SMALL_TANK×24, SOLDIER×31, SIEGE_TANK×30, SMALL_TANK×28, MOTORBIKE×27, TRANSPORTER×20, SMALL_TANK×20, NINJA×29, TRANSPORTER×20, NINJA×22 |
| 🟩 | Frenzied Pillagers | random | Industrial 80%, Renaissance 14%, Modern 6% | 🔴 2/16 (12%) | SPECOPS×7 | MOTORBIKE×26, SOLDIER×19, CARGO×32, SMALL_TANK×28, MOTORBIKE×26, MOTORBIKE×27, SMALL_TANK×26, SOLDIER×27, TRANSPORTER×20, SOLDIER×19, SPECOPS×20, TRANSPORTER×30, MOTORBIKE×20, CARGO×20, TRANSPORTER×20 |

#### Full Gatling

| Tower Era Distribution (60 towers) | Towers |
|---|---|
| Industrial 82% (49), Renaissance 17% (10), Iron Age 2% (1) | GATLING_TOWER×42, ICE_TOWER×10, FLAME_THROWER×4, SHOCK_TOWER×3, COLD_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Industrial March | hardcoded | Industrial 98%, Modern 2% | 🟢 50/58 (86%) | SMALL_TANK×3, SOLDIER×2 | SOLDIER×16, SOLDIER×17, MOTORBIKE×17, TRANSPORTER×18, TRANSPORTER×19, SMALL_TANK×19, TRANSPORTER×20, TRANSPORTER×21, SMALL_TANK×21, SMALL_TANK×22, MOTORBIKE×23, MOTORBIKE×23, SPECOPS×10, MOTORBIKE×28, SMALL_TANK×30, SOLDIER×32, SOLDIER×34, TRANSPORTER×36, TRANSPORTER×38, TRANSPORTER×40, MOTORBIKE×36 |
| 🟩 | Mechanized Strike | hardcoded | Industrial 100% | 🟢 50/58 (86%) | SMALL_TANK×4 | SOLDIER×18, SMALL_TANK×19, TRANSPORTER×19, SMALL_TANK×20, TRANSPORTER×21, SMALL_TANK×21, SOLDIER×22, SOLDIER×22, TRANSPORTER×23, MOTORBIKE×24, SMALL_TANK×24, MOTORBIKE×25, TRANSPORTER×26, TRANSPORTER×26, SOLDIER×27, SOLDIER×27, SMALL_TANK×28, SMALL_TANK×29, SMALL_TANK×29, TRANSPORTER×30, MOTORBIKE×34, SMALL_TANK×35, SOLDIER×35 |
| 🟩 | Steam Assault | hardcoded | Industrial 100% | 🟢 58/58 (100%) |  | TRANSPORTER×18, SOLDIER×19, SOLDIER×19, SMALL_TANK×20, TRANSPORTER×21, SOLDIER×21, SOLDIER×22, SMALL_TANK×22, TRANSPORTER×23, SMALL_TANK×24, TRANSPORTER×24, SMALL_TANK×25, SOLDIER×26, TRANSPORTER×26, SMALL_TANK×27, MOTORBIKE×27, SOLDIER×28, TRANSPORTER×29, SOLDIER×29, MOTORBIKE×30, SMALL_TANK×33, TRANSPORTER×35, TRANSPORTER×37 |
| 🟩 | Tank Column | hardcoded | Industrial 100% | 🟢 58/58 (100%) |  | SMALL_TANK×18, MOTORBIKE×19, MOTORBIKE×19, TRANSPORTER×20, TRANSPORTER×21, TRANSPORTER×21, SOLDIER×22, MOTORBIKE×22, TRANSPORTER×23, TRANSPORTER×24, SMALL_TANK×24, MOTORBIKE×25, TRANSPORTER×26, SMALL_TANK×26, TRANSPORTER×27, SMALL_TANK×27, TRANSPORTER×28, MOTORBIKE×29, MOTORBIKE×29, SOLDIER×30, SOLDIER×34, SOLDIER×36, TRANSPORTER×38, SOLDIER×34 |
| 🟩 | Factory Raid | hardcoded | Industrial 88%, Renaissance 10%, Modern 2% | 🟢 48/58 (83%) | SMALL_TANK×5 | MOTORBIKE×18, MOTORBIKE×20, MOTORBIKE×20, MOTORBIKE×22, SOLDIER×20, TRANSPORTER×21, MOTORBIKE×22, SMALL_TANK×22, SMALL_TANK×25, SOLDIER×24, MOTORBIKE×24, TRANSPORTER×25, SMALL_TANK×26, SMALL_TANK×28, MOTORBIKE×30, CARGO×30, TRANSPORTER×32, DRAGOONER×34, HELI×13, TRANSPORTER×38, SMALL_TANK×38, SOLDIER×36, SMALL_TANK×33, SMALL_TANK×36 |
| 🟩 | Reckless Looters | random | Modern 72%, Industrial 26%, Renaissance 2% | 🟡 40/58 (69%) | THE_GENERAL×1 | TRANSPORTER×20, SOLDIER×25, TRANSPORTER×20, SMALL_TANK×28, TRANSPORTER×20, TRANSPORTER×30, SOLDIER×19, MOTORBIKE×26, MUSKETEER×29, SOLDIER×24, MOTORBIKE×27, SOLDIER×28, MOTORBIKE×21, THE_GENERAL×999, SMALL_TANK×24, SOLDIER×27, MOTORBIKE×20 |
| 🟩 | Reckless Looters | random | Modern 72%, Industrial 26%, Renaissance 2% | 🟡 40/58 (69%) | THE_GENERAL×1 | TRANSPORTER×20, SOLDIER×25, TRANSPORTER×20, SMALL_TANK×28, TRANSPORTER×20, TRANSPORTER×30, SOLDIER×19, MOTORBIKE×26, MUSKETEER×29, SOLDIER×24, MOTORBIKE×27, SOLDIER×28, MOTORBIKE×21, THE_GENERAL×999, SMALL_TANK×24, SOLDIER×27, MOTORBIKE×20 |
| 🟩 | Reckless Looters | random | Renaissance 72%, Industrial 28% | 🟢 48/58 (83%) | THE_KING×1 | SOLDIER×29, MOTORBIKE×32, MOTORBIKE×29, SOLDIER×20, SOLDIER×24, SOLDIER×31, SOLDIER×18, MUSKETEER×19, SOLDIER×27, SMALL_TANK×24, TRANSPORTER×30, TRANSPORTER×20, MOTORBIKE×19, SOLDIER×25, SMALL_TANK×30, SMALL_TANK×32, THE_KING×999 |
| 🟩 | Stubborn Raiders | random | Renaissance 71%, Industrial 27%, Modern 2% | 🟢 58/58 (100%) |  | SIEGE_TANK×24, MOTORBIKE×25, THE_KING×999, SMALL_TANK×26, MOTORBIKE×29, TRANSPORTER×20, SOLDIER×22, SMALL_TANK×20, SOLDIER×28, SMALL_TANK×20, SOLDIER×29, TRANSPORTER×20, SMALL_TANK×22, MOTORBIKE×31, SOLDIER×30, TRANSPORTER×30, MOTORBIKE×28 |
| 🟩 | Shrieking Horde | random | Industrial 91%, Renaissance 9% | 🟢 58/58 (100%) |  | MOTORBIKE×28, SMALL_TANK×28, MOTORBIKE×23, SMALL_TANK×24, SOLDIER×29, MUSKETEER×23, SOLDIER×21, TRANSPORTER×20, TRANSPORTER×30, SMALL_TANK×20, SMALL_TANK×28, MOTORBIKE×24, MUSKETEER×19, SOLDIER×25, TRANSPORTER×30, TRANSPORTER×30, MOTORBIKE×28, TRANSPORTER×30 |
| 🟩 | Restless Horde | random | Renaissance 76%, Industrial 24% | 🟢 58/58 (100%) |  | SOLDIER×25, SMALL_TANK×22, MUSKETEER×32, SMALL_TANK×20, MUSKETEER×23, CARGO×24, MOTORBIKE×31, SMALL_TANK×28, SOLDIER×25, SMALL_TANK×28, MOTORBIKE×29, SOLDIER×29, MOTORBIKE×31, TRANSPORTER×20, SOLDIER×22, THE_KING×999, SOLDIER×29 |
| 🟩 | Ragged Warband | random | Modern 71%, Industrial 27%, Renaissance 1% | 🟢 58/58 (100%) |  | MOTORBIKE×18, SOLDIER×26, SOLDIER×31, TRANSPORTER×30, SMALL_TANK×20, SOLDIER×18, NINJA×21, THE_GENERAL×999, TRANSPORTER×30, SOLDIER×24, TRANSPORTER×20, TRANSPORTER×30, MOTORBIKE×24, TRANSPORTER×30, SOLDIER×32, TRANSPORTER×20, TRANSPORTER×30 |
| 🟩 | Disorganized Mob | random | Modern 78%, Industrial 21%, Renaissance 1% | 🟡 32/58 (55%) | SPECOPS×11, SMALL_TANK×2 | MOTORBIKE×22, SOLDIER×29, DRAGOONER×20, SMALL_TANK×22, SMALL_TANK×20, SPECOPS×27, SMALL_TANK×22, SOLDIER×26, MOTORBIKE×25, SMALL_TANK×26, TRANSPORTER×20, MOTORBIKE×26, TRANSPORTER×20, THE_GENERAL×999, SOLDIER×20 |
| 🟩 | Petty Bandits | random | Industrial 82%, Renaissance 18% | 🟢 58/58 (100%) |  | SOLDIER×25, MOTORBIKE×29, SOLDIER×20, SOLDIER×20, SOLDIER×26, MOTORBIKE×29, SMALL_TANK×26, CARGO×24, SOLDIER×25, MUSKETEER×20, MOTORBIKE×23, SOLDIER×26, TRANSPORTER×30, MUSKETEER×22, TRANSPORTER×20 |
| 🟩 | Crude Invaders | random | Renaissance 79%, Industrial 21% | 🟢 58/58 (100%) |  | SMALL_TANK×22, SMALL_TANK×26, SMALL_TANK×22, NINJA×19, MOTORBIKE×25, TRANSPORTER×30, MUSKETEER×25, THE_KING×999, SOLDIER×27, SMALL_TANK×28, TRANSPORTER×20, TRANSPORTER×30, TRANSPORTER×20, MOTORBIKE×30, CARGO×20 |
| 🟩 | Forgotten Warband | random | Renaissance 78%, Industrial 19%, Modern 3% | 🟢 58/58 (100%) |  | SIEGE_TANK×20, MOTORBIKE×24, NINJA×23, TRANSPORTER×30, SIEGE_TANK×20, TRANSPORTER×20, MUSKETEER×19, THE_KING×999, SOLDIER×18, SMALL_TANK×26, SOLDIER×23, MOTORBIKE×21, MOTORBIKE×22, SOLDIER×23, TRANSPORTER×20, TRANSPORTER×30, MUSKETEER×19 |
| 🟩 | Forgotten Warband | random | Renaissance 76%, Industrial 23%, Modern 1% | 🟢 58/58 (100%) |  | SIEGE_TANK×20, TRANSPORTER×30, SOLDIER×20, TRANSPORTER×20, SMALL_TANK×26, DRAGOONER×31, MOTORBIKE×24, SMALL_TANK×30, MOTORBIKE×25, DRAGOONER×22, SOLDIER×26, SMALL_TANK×20, SMALL_TANK×24, THE_KING×999, MOTORBIKE×26, SMALL_TANK×28, TRANSPORTER×20 |
| 🟩 | Drunken Raiders | random | Renaissance 74%, Industrial 24%, Modern 2% | 🟡 46/58 (79%) | SPECOPS×6 | SMALL_TANK×26, THE_KING×999, TRANSPORTER×20, SMALL_TANK×26, SMALL_TANK×28, MOTORBIKE×21, SOLDIER×22, SOLDIER×24, TRANSPORTER×20, SOLDIER×28, SOLDIER×22, MOTORBIKE×23, SMALL_TANK×18, SPECOPS×27, TRANSPORTER×30, TRANSPORTER×20 |
| 🟩 | Unlucky Raiders | random | Industrial 89%, Renaissance 11% | 🟢 58/58 (100%) |  | SOLDIER×26, SMALL_TANK×24, NINJA×22, MOTORBIKE×26, TRANSPORTER×30, SMALL_TANK×22, DRAGOONER×22, TRANSPORTER×20, MOTORBIKE×19, SOLDIER×28, SOLDIER×22, TRANSPORTER×20, MOTORBIKE×26, SOLDIER×19, SMALL_TANK×20, SOLDIER×19, MOTORBIKE×19 |
| 🟩 | Angry Mob | random | Renaissance 76%, Industrial 23%, Modern 2% | 🟢 50/58 (86%) | SPECOPS×4 | MOTORBIKE×27, SOLDIER×20, MOTORBIKE×24, SOLDIER×19, TRANSPORTER×20, TRANSPORTER×20, SPECOPS×22, SMALL_TANK×22, SOLDIER×29, SOLDIER×31, DRAGOONER×22, TRANSPORTER×20, TRANSPORTER×30, TRANSPORTER×20, THE_KING×999, MOTORBIKE×21 |
| 🟩 | Angry Mob | random | Renaissance 77%, Industrial 21%, Modern 2% | 🟡 33/58 (57%) | SPECOPS×12, SOLDIER×1 | SOLDIER×24, TRANSPORTER×30, MOTORBIKE×19, DRAGOONER×22, MOTORBIKE×19, MOTORBIKE×23, MOTORBIKE×18, SMALL_TANK×22, THE_KING×999, MOTORBIKE×21, SOLDIER×29, SPECOPS×26, TRANSPORTER×20, SOLDIER×25, SMALL_TANK×32 |
| 🟩 | Shrieking Horde | random | Renaissance 72%, Industrial 25%, Modern 4% | 🟢 55/58 (95%) | SOLDIER×3 | TRANSPORTER×20, SMALL_TANK×20, SOLDIER×22, HELI×26, MOTORBIKE×23, TRANSPORTER×20, TRANSPORTER×20, SOLDIER×28, SOLDIER×31, SOLDIER×30, MOTORBIKE×30, HELI×24, THE_KING×999, MOTORBIKE×26, SMALL_TANK×30, TRANSPORTER×20, MOTORBIKE×27 |
| 🟩 | Reckless Looters | random | Modern 72%, Industrial 26%, Renaissance 1% | 🟡 40/58 (69%) | THE_GENERAL×1 | SMALL_TANK×30, CARGO×20, MOTORBIKE×24, MOTORBIKE×21, SOLDIER×21, SOLDIER×30, SMALL_TANK×26, SMALL_TANK×22, SMALL_TANK×26, MOTORBIKE×28, SOLDIER×19, SMALL_TANK×26, THE_GENERAL×999, SMALL_TANK×22, MOTORBIKE×19, TRANSPORTER×20, SOLDIER×27 |
| 🟩 | Noisy Barbarians | random | Industrial 72%, Renaissance 20%, Modern 7% | 🟡 38/58 (66%) | SIEGE_TANK×7, SMALL_TANK×3 | MOTORBIKE×20, SOLDIER×29, SMALL_TANK×20, SMALL_TANK×30, NINJA×31, SOLDIER×20, SMALL_TANK×24, SOLDIER×31, SIEGE_TANK×30, SMALL_TANK×28, MOTORBIKE×27, TRANSPORTER×20, SMALL_TANK×20, NINJA×29, TRANSPORTER×20, NINJA×22 |
| 🟩 | Frenzied Pillagers | random | Industrial 80%, Renaissance 14%, Modern 6% | 🟡 42/58 (72%) | SPECOPS×8 | MOTORBIKE×26, SOLDIER×19, CARGO×32, SMALL_TANK×28, MOTORBIKE×26, MOTORBIKE×27, SMALL_TANK×26, SOLDIER×27, TRANSPORTER×20, SOLDIER×19, SPECOPS×20, TRANSPORTER×30, MOTORBIKE×20, CARGO×20, TRANSPORTER×20 |

#### Mixed

| Tower Era Distribution (61 towers) | Towers |
|---|---|
| Industrial 92% (56), Renaissance 7% (4), Iron Age 2% (1) | FLAME_THROWER×26, SHOCK_TOWER×19, GATLING_TOWER×11, ICE_TOWER×4, COLD_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Industrial March | hardcoded | Industrial 98%, Modern 2% | 🟢 28/28 (100%) |  | SOLDIER×16, SOLDIER×17, MOTORBIKE×17, TRANSPORTER×18, TRANSPORTER×19, SMALL_TANK×19, TRANSPORTER×20, TRANSPORTER×21, SMALL_TANK×21, SMALL_TANK×22, MOTORBIKE×23, MOTORBIKE×23, SPECOPS×10, MOTORBIKE×28, SMALL_TANK×30, SOLDIER×32, SOLDIER×34, TRANSPORTER×36, TRANSPORTER×38, TRANSPORTER×40, MOTORBIKE×36 |
| 🟩 | Mechanized Strike | hardcoded | Industrial 100% | 🟢 28/28 (100%) |  | SOLDIER×18, SMALL_TANK×19, TRANSPORTER×19, SMALL_TANK×20, TRANSPORTER×21, SMALL_TANK×21, SOLDIER×22, SOLDIER×22, TRANSPORTER×23, MOTORBIKE×24, SMALL_TANK×24, MOTORBIKE×25, TRANSPORTER×26, TRANSPORTER×26, SOLDIER×27, SOLDIER×27, SMALL_TANK×28, SMALL_TANK×29, SMALL_TANK×29, TRANSPORTER×30, MOTORBIKE×34, SMALL_TANK×35, SOLDIER×35 |
| 🟩 | Steam Assault | hardcoded | Industrial 100% | 🟢 28/28 (100%) |  | TRANSPORTER×18, SOLDIER×19, SOLDIER×19, SMALL_TANK×20, TRANSPORTER×21, SOLDIER×21, SOLDIER×22, SMALL_TANK×22, TRANSPORTER×23, SMALL_TANK×24, TRANSPORTER×24, SMALL_TANK×25, SOLDIER×26, TRANSPORTER×26, SMALL_TANK×27, MOTORBIKE×27, SOLDIER×28, TRANSPORTER×29, SOLDIER×29, MOTORBIKE×30, SMALL_TANK×33, TRANSPORTER×35, TRANSPORTER×37 |
| 🟩 | Tank Column | hardcoded | Industrial 100% | 🟢 28/28 (100%) |  | SMALL_TANK×18, MOTORBIKE×19, MOTORBIKE×19, TRANSPORTER×20, TRANSPORTER×21, TRANSPORTER×21, SOLDIER×22, MOTORBIKE×22, TRANSPORTER×23, TRANSPORTER×24, SMALL_TANK×24, MOTORBIKE×25, TRANSPORTER×26, SMALL_TANK×26, TRANSPORTER×27, SMALL_TANK×27, TRANSPORTER×28, MOTORBIKE×29, MOTORBIKE×29, SOLDIER×30, SOLDIER×34, SOLDIER×36, TRANSPORTER×38, SOLDIER×34 |
| 🟩 | Factory Raid | hardcoded | Industrial 88%, Renaissance 10%, Modern 2% | 🟢 28/28 (100%) |  | MOTORBIKE×18, MOTORBIKE×20, MOTORBIKE×20, MOTORBIKE×22, SOLDIER×20, TRANSPORTER×21, MOTORBIKE×22, SMALL_TANK×22, SMALL_TANK×25, SOLDIER×24, MOTORBIKE×24, TRANSPORTER×25, SMALL_TANK×26, SMALL_TANK×28, MOTORBIKE×30, CARGO×30, TRANSPORTER×32, DRAGOONER×34, HELI×13, TRANSPORTER×38, SMALL_TANK×38, SOLDIER×36, SMALL_TANK×33, SMALL_TANK×36 |
| 🟩 | Reckless Looters | random | Modern 72%, Industrial 26%, Renaissance 2% | 🟢 28/28 (100%) |  | TRANSPORTER×20, SOLDIER×25, TRANSPORTER×20, SMALL_TANK×28, TRANSPORTER×20, TRANSPORTER×30, SOLDIER×19, MOTORBIKE×26, MUSKETEER×29, SOLDIER×24, MOTORBIKE×27, SOLDIER×28, MOTORBIKE×21, THE_GENERAL×999, SMALL_TANK×24, SOLDIER×27, MOTORBIKE×20 |
| 🟩 | Reckless Looters | random | Modern 72%, Industrial 26%, Renaissance 2% | 🟢 28/28 (100%) |  | TRANSPORTER×20, SOLDIER×25, TRANSPORTER×20, SMALL_TANK×28, TRANSPORTER×20, TRANSPORTER×30, SOLDIER×19, MOTORBIKE×26, MUSKETEER×29, SOLDIER×24, MOTORBIKE×27, SOLDIER×28, MOTORBIKE×21, THE_GENERAL×999, SMALL_TANK×24, SOLDIER×27, MOTORBIKE×20 |
| 🟩 | Reckless Looters | random | Renaissance 72%, Industrial 28% | 🟢 28/28 (100%) |  | SOLDIER×29, MOTORBIKE×32, MOTORBIKE×29, SOLDIER×20, SOLDIER×24, SOLDIER×31, SOLDIER×18, MUSKETEER×19, SOLDIER×27, SMALL_TANK×24, TRANSPORTER×30, TRANSPORTER×20, MOTORBIKE×19, SOLDIER×25, SMALL_TANK×30, SMALL_TANK×32, THE_KING×999 |
| 🟩 | Stubborn Raiders | random | Renaissance 71%, Industrial 27%, Modern 2% | 🟢 28/28 (100%) |  | SIEGE_TANK×24, MOTORBIKE×25, THE_KING×999, SMALL_TANK×26, MOTORBIKE×29, TRANSPORTER×20, SOLDIER×22, SMALL_TANK×20, SOLDIER×28, SMALL_TANK×20, SOLDIER×29, TRANSPORTER×20, SMALL_TANK×22, MOTORBIKE×31, SOLDIER×30, TRANSPORTER×30, MOTORBIKE×28 |
| 🟩 | Shrieking Horde | random | Industrial 91%, Renaissance 9% | 🟢 28/28 (100%) |  | MOTORBIKE×28, SMALL_TANK×28, MOTORBIKE×23, SMALL_TANK×24, SOLDIER×29, MUSKETEER×23, SOLDIER×21, TRANSPORTER×20, TRANSPORTER×30, SMALL_TANK×20, SMALL_TANK×28, MOTORBIKE×24, MUSKETEER×19, SOLDIER×25, TRANSPORTER×30, TRANSPORTER×30, MOTORBIKE×28, TRANSPORTER×30 |
| 🟩 | Restless Horde | random | Renaissance 76%, Industrial 24% | 🟢 28/28 (100%) |  | SOLDIER×25, SMALL_TANK×22, MUSKETEER×32, SMALL_TANK×20, MUSKETEER×23, CARGO×24, MOTORBIKE×31, SMALL_TANK×28, SOLDIER×25, SMALL_TANK×28, MOTORBIKE×29, SOLDIER×29, MOTORBIKE×31, TRANSPORTER×20, SOLDIER×22, THE_KING×999, SOLDIER×29 |
| 🟩 | Ragged Warband | random | Modern 71%, Industrial 27%, Renaissance 1% | 🟢 28/28 (100%) |  | MOTORBIKE×18, SOLDIER×26, SOLDIER×31, TRANSPORTER×30, SMALL_TANK×20, SOLDIER×18, NINJA×21, THE_GENERAL×999, TRANSPORTER×30, SOLDIER×24, TRANSPORTER×20, TRANSPORTER×30, MOTORBIKE×24, TRANSPORTER×30, SOLDIER×32, TRANSPORTER×20, TRANSPORTER×30 |
| 🟩 | Disorganized Mob | random | Modern 78%, Industrial 21%, Renaissance 1% | 🟢 28/28 (100%) |  | MOTORBIKE×22, SOLDIER×29, DRAGOONER×20, SMALL_TANK×22, SMALL_TANK×20, SPECOPS×27, SMALL_TANK×22, SOLDIER×26, MOTORBIKE×25, SMALL_TANK×26, TRANSPORTER×20, MOTORBIKE×26, TRANSPORTER×20, THE_GENERAL×999, SOLDIER×20 |
| 🟩 | Petty Bandits | random | Industrial 82%, Renaissance 18% | 🟢 28/28 (100%) |  | SOLDIER×25, MOTORBIKE×29, SOLDIER×20, SOLDIER×20, SOLDIER×26, MOTORBIKE×29, SMALL_TANK×26, CARGO×24, SOLDIER×25, MUSKETEER×20, MOTORBIKE×23, SOLDIER×26, TRANSPORTER×30, MUSKETEER×22, TRANSPORTER×20 |
| 🟩 | Crude Invaders | random | Renaissance 79%, Industrial 21% | 🟢 28/28 (100%) |  | SMALL_TANK×22, SMALL_TANK×26, SMALL_TANK×22, NINJA×19, MOTORBIKE×25, TRANSPORTER×30, MUSKETEER×25, THE_KING×999, SOLDIER×27, SMALL_TANK×28, TRANSPORTER×20, TRANSPORTER×30, TRANSPORTER×20, MOTORBIKE×30, CARGO×20 |
| 🟩 | Forgotten Warband | random | Renaissance 78%, Industrial 19%, Modern 3% | 🟢 28/28 (100%) |  | SIEGE_TANK×20, MOTORBIKE×24, NINJA×23, TRANSPORTER×30, SIEGE_TANK×20, TRANSPORTER×20, MUSKETEER×19, THE_KING×999, SOLDIER×18, SMALL_TANK×26, SOLDIER×23, MOTORBIKE×21, MOTORBIKE×22, SOLDIER×23, TRANSPORTER×20, TRANSPORTER×30, MUSKETEER×19 |
| 🟩 | Forgotten Warband | random | Renaissance 76%, Industrial 23%, Modern 1% | 🟢 28/28 (100%) |  | SIEGE_TANK×20, TRANSPORTER×30, SOLDIER×20, TRANSPORTER×20, SMALL_TANK×26, DRAGOONER×31, MOTORBIKE×24, SMALL_TANK×30, MOTORBIKE×25, DRAGOONER×22, SOLDIER×26, SMALL_TANK×20, SMALL_TANK×24, THE_KING×999, MOTORBIKE×26, SMALL_TANK×28, TRANSPORTER×20 |
| 🟩 | Drunken Raiders | random | Renaissance 74%, Industrial 24%, Modern 2% | 🟢 28/28 (100%) |  | SMALL_TANK×26, THE_KING×999, TRANSPORTER×20, SMALL_TANK×26, SMALL_TANK×28, MOTORBIKE×21, SOLDIER×22, SOLDIER×24, TRANSPORTER×20, SOLDIER×28, SOLDIER×22, MOTORBIKE×23, SMALL_TANK×18, SPECOPS×27, TRANSPORTER×30, TRANSPORTER×20 |
| 🟩 | Unlucky Raiders | random | Industrial 89%, Renaissance 11% | 🟢 28/28 (100%) |  | SOLDIER×26, SMALL_TANK×24, NINJA×22, MOTORBIKE×26, TRANSPORTER×30, SMALL_TANK×22, DRAGOONER×22, TRANSPORTER×20, MOTORBIKE×19, SOLDIER×28, SOLDIER×22, TRANSPORTER×20, MOTORBIKE×26, SOLDIER×19, SMALL_TANK×20, SOLDIER×19, MOTORBIKE×19 |
| 🟩 | Angry Mob | random | Renaissance 76%, Industrial 23%, Modern 2% | 🟢 28/28 (100%) |  | MOTORBIKE×27, SOLDIER×20, MOTORBIKE×24, SOLDIER×19, TRANSPORTER×20, TRANSPORTER×20, SPECOPS×22, SMALL_TANK×22, SOLDIER×29, SOLDIER×31, DRAGOONER×22, TRANSPORTER×20, TRANSPORTER×30, TRANSPORTER×20, THE_KING×999, MOTORBIKE×21 |
| 🟩 | Angry Mob | random | Renaissance 77%, Industrial 21%, Modern 2% | 🟢 28/28 (100%) |  | SOLDIER×24, TRANSPORTER×30, MOTORBIKE×19, DRAGOONER×22, MOTORBIKE×19, MOTORBIKE×23, MOTORBIKE×18, SMALL_TANK×22, THE_KING×999, MOTORBIKE×21, SOLDIER×29, SPECOPS×26, TRANSPORTER×20, SOLDIER×25, SMALL_TANK×32 |
| 🟩 | Shrieking Horde | random | Renaissance 72%, Industrial 25%, Modern 4% | 🟢 28/28 (100%) |  | TRANSPORTER×20, SMALL_TANK×20, SOLDIER×22, HELI×26, MOTORBIKE×23, TRANSPORTER×20, TRANSPORTER×20, SOLDIER×28, SOLDIER×31, SOLDIER×30, MOTORBIKE×30, HELI×24, THE_KING×999, MOTORBIKE×26, SMALL_TANK×30, TRANSPORTER×20, MOTORBIKE×27 |
| 🟩 | Reckless Looters | random | Modern 72%, Industrial 26%, Renaissance 1% | 🟢 28/28 (100%) |  | SMALL_TANK×30, CARGO×20, MOTORBIKE×24, MOTORBIKE×21, SOLDIER×21, SOLDIER×30, SMALL_TANK×26, SMALL_TANK×22, SMALL_TANK×26, MOTORBIKE×28, SOLDIER×19, SMALL_TANK×26, THE_GENERAL×999, SMALL_TANK×22, MOTORBIKE×19, TRANSPORTER×20, SOLDIER×27 |
| 🟩 | Noisy Barbarians | random | Industrial 72%, Renaissance 20%, Modern 7% | 🟢 28/28 (100%) |  | MOTORBIKE×20, SOLDIER×29, SMALL_TANK×20, SMALL_TANK×30, NINJA×31, SOLDIER×20, SMALL_TANK×24, SOLDIER×31, SIEGE_TANK×30, SMALL_TANK×28, MOTORBIKE×27, TRANSPORTER×20, SMALL_TANK×20, NINJA×29, TRANSPORTER×20, NINJA×22 |
| 🟩 | Frenzied Pillagers | random | Industrial 80%, Renaissance 14%, Modern 6% | 🟢 28/28 (100%) |  | MOTORBIKE×26, SOLDIER×19, CARGO×32, SMALL_TANK×28, MOTORBIKE×26, MOTORBIKE×27, SMALL_TANK×26, SOLDIER×27, TRANSPORTER×20, SOLDIER×19, SPECOPS×20, TRANSPORTER×30, MOTORBIKE×20, CARGO×20, TRANSPORTER×20 |

### Modern

#### Weak Modern

| Tower Era Distribution (33 towers) | Towers |
|---|---|
| Modern 61% (20), Industrial 30% (10), Iron Age 6% (2), Renaissance 3% (1) | FLAME_THROWER×10, MG_TOWER×7, RADAR_TOWER×5, ANTI_AIR_TOWER×4, LASER_TOWER×4, COLD_TOWER×2, ICE_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Modern Warfare | hardcoded | Modern 85%, Industrial 12%, Future 4% | 🟢 27/28 (96%) | DRONE×1 | SPECOPS×18, SIEGE_TANK×18, SIEGE_TANK×19, HELI×20, HELI×20, SIEGE_TANK×20, SPECOPS×21, SIEGE_TANK×22, SPECOPS×22, SPECOPS×22, SPECOPS×23, SIEGE_TANK×24, HELI×24, SIEGE_TANK×24, DRONE×25, SIEGE_TANK×26, SPECOPS×26, TRANSPORTER×26, HELI×27, SIEGE_TANK×28, TRANSPORTER×28, SPECOPS×28, HELI×29, SMALL_TANK×30, HELI×30, SIEGE_TANK×33, THE_GENERAL×40, HELI×34 |
| 🟥 | Special Ops | hardcoded | Modern 88%, Industrial 9%, Future 4% | ⬛ 0/28 (0%) | SOLDIER×10, SPECOPS×9 | HELI×18, HELI×18, SPECOPS×19, SIEGE_TANK×20, SIEGE_TANK×20, SIEGE_TANK×20, SPECOPS×21, SPECOPS×22, SPECOPS×22, HELI×22, SIEGE_TANK×23, SPECOPS×24, SIEGE_TANK×24, HELI×24, HELI×25, MECH_WARRIOR×26, SPECOPS×26, SIEGE_TANK×26, SPECOPS×27, HELI×28, SPECOPS×28, TRANSPORTER×28, HELI×29, SIEGE_TANK×30, HELI×30, SMALL_TANK×32, SIEGE_TANK×33, THE_GENERAL×36 |
| 🟩 | Heli Strike | hardcoded | Modern 82%, Industrial 13%, Future 5% | 🟠 6/28 (21%) | DRONE×12, SOLDIER×5, HELI×1, SPECOPS×1 | HELI×18, SPECOPS×18, HELI×19, SPECOPS×20, HELI×20, SPECOPS×20, SPECOPS×21, SPECOPS×22, TRANSPORTER×22, SPECOPS×22, SPECOPS×23, SIEGE_TANK×24, HELI×24, TRANSPORTER×24, SIEGE_TANK×25, HELI×26, SPECOPS×26, MOTORBIKE×26, SPECOPS×27, HELI×28, TRANSPORTER×28, HELI×28, HELI×29, SIEGE_TANK×30, SPECOPS×30, THE_GENERAL×35, DRONE×36, SIEGE_TANK×36, HELI×40 |
| 🟥 | Siege Assault | hardcoded | Modern 82%, Industrial 11%, Future 4%, Renaissance 3% | ⬛ 0/28 (0%) | SPECOPS×11, SOLDIER×7 | SIEGE_TANK×18, SIEGE_TANK×18, SIEGE_TANK×19, SPECOPS×20, HELI×20, SPECOPS×20, TRANSPORTER×21, SIEGE_TANK×22, NINJA×22, HELI×22, SIEGE_TANK×23, SIEGE_TANK×24, SOLDIER×24, SPECOPS×24, SIEGE_TANK×25, SPECOPS×26, SPECOPS×26, HELI×26, SIEGE_TANK×27, TRANSPORTER×28, HELI×28, HELI×28, SIEGE_TANK×29, MECH_WARRIOR×30, SPECOPS×30, THE_GENERAL×40, SIEGE_TANK×40 |
| 🟥 | Urban Combat | hardcoded | Modern 83%, Industrial 12%, Future 5% | ⬛ 0/28 (0%) | SOLDIER×12, SPECOPS×8 | SPECOPS×18, SIEGE_TANK×18, SPECOPS×19, THE_GENERAL×20, SPECOPS×20, SPECOPS×20, HELI×21, SPECOPS×22, SPECOPS×22, SIEGE_TANK×22, SIEGE_TANK×23, SIEGE_TANK×24, SPECOPS×24, SOLDIER×24, SPECOPS×25, SPECOPS×26, SIEGE_TANK×26, HELI×26, SPECOPS×27, HELI×28, SPECOPS×28, HELI×28, TRANSPORTER×29, HELI×30, SMALL_TANK×30, DRONE×34, SIEGE_TANK×36, SPECOPS×37 |
| 🟥 | Cyber Strike | hardcoded | Modern 91%, Future 4%, Industrial 4% | ⬛ 0/28 (0%) | SPECOPS×14, SOLDIER×1 | SIEGE_TANK×18, HELI×18, HELI×19, SPECOPS×19, SPECOPS×20, SPECOPS×20, SIEGE_TANK×21, SPECOPS×21, SPECOPS×21, SIEGE_TANK×22, SPECOPS×22, SPECOPS×23, SPECOPS×23, SIEGE_TANK×24, SIEGE_TANK×24, SIEGE_TANK×24, HELI×25, SPECOPS×25, HELI×26, SIEGE_TANK×26, SPECOPS×27, SPECOPS×27, HELI×27, SIEGE_TANK×28, SIEGE_TANK×28, SOLDIER×29, DRONE×30, THE_GENERAL×35 |
| 🟥 | Shrieking Horde | random | Modern 96%, Future 4% | ⬛ 0/28 (0%) | SPECOPS×14 | HELI×22, SPECOPS×31, MECH_WARRIOR×33, SIEGE_TANK×22, SPECOPS×21, SIEGE_TANK×26, SPECOPS×31, SPECOPS×27, THE_GENERAL×999, SPECOPS×28, HELI×24, HELI×26, SIEGE_TANK×22, DRONE×31, SPECOPS×34, SIEGE_TANK×22, SIEGE_TANK×26, SPECOPS×30 |
| 🟥 | Shrieking Horde | random | Modern 96%, Future 4% | ⬛ 0/28 (0%) | SPECOPS×14 | HELI×22, SPECOPS×31, MECH_WARRIOR×33, SIEGE_TANK×22, SPECOPS×21, SIEGE_TANK×26, SPECOPS×31, SPECOPS×27, THE_GENERAL×999, SPECOPS×28, HELI×24, HELI×26, SIEGE_TANK×22, DRONE×31, SPECOPS×34, SIEGE_TANK×22, SIEGE_TANK×26, SPECOPS×30 |
| 🟥 | Stubborn Raiders | random | Modern 96%, Future 2%, Industrial 1% | ⬛ 0/28 (0%) | SOLDIER×9, SPECOPS×7, HELI×2 | SIEGE_TANK×26, SIEGE_TANK×28, HELI×20, SPECOPS×29, SIEGE_TANK×22, THE_GENERAL×999, SIEGE_TANK×32, SPECOPS×22, SIEGE_TANK×34, HELI×24, MECH_WARRIOR×30, HELI×20, SPECOPS×31, HELI×26, SPECOPS×25, HELI×26, SOLDIER×21, HELI×32 |
| 🟥 | Shrieking Horde | random | Modern 98%, Future 2% | ⬛ 0/28 (0%) | SPECOPS×9, SOLDIER×7, HELI×1 | SIEGE_TANK×26, HELI×24, SPECOPS×27, SIEGE_TANK×24, SPECOPS×31, SIEGE_TANK×26, SIEGE_TANK×30, HELI×22, SPECOPS×20, MECH_WARRIOR×27, HELI×20, THE_GENERAL×999, SIEGE_TANK×30, SIEGE_TANK×30, SIEGE_TANK×30, SPECOPS×32, SPECOPS×30, HELI×30 |
| 🟥 | Relentless Mob | random | Modern 96%, Future 2%, Industrial 2% | ⬛ 0/28 (0%) | SPECOPS×12, SOLDIER×5 | DRONE×29, HELI×22, HELI×26, SPECOPS×30, SIEGE_TANK×30, HELI×34, MOTORBIKE×28, SPECOPS×30, SIEGE_TANK×24, SPECOPS×20, SPECOPS×27, HELI×26, HELI×26, SPECOPS×28, SPECOPS×25, HELI×22, THE_GENERAL×999, SPECOPS×31, HELI×32 |
| 🟥 | Desperate Looters | random | Modern 92%, Industrial 5%, Future 2% | ⬛ 0/28 (0%) | SOLDIER×16, SPECOPS×3, HELI×2 | DRONE×32, SIEGE_TANK×24, SPECOPS×33, MOTORBIKE×34, MOTORBIKE×25, SIEGE_TANK×26, HELI×22, HELI×30, SIEGE_TANK×26, SIEGE_TANK×30, SPECOPS×33, SPECOPS×31, HELI×30, SIEGE_TANK×32, THE_GENERAL×999, HELI×24, TRANSPORTER×20, SIEGE_TANK×22 |
| 🟥 | Ragged Warband | random | Modern 96%, Future 4% | ⬛ 0/28 (0%) | DRONE×16, SPECOPS×4, SOLDIER×4 | SIEGE_TANK×20, SPECOPS×31, HELI×26, DRONE×28, SIEGE_TANK×28, HELI×34, THE_GENERAL×999, HELI×34, SIEGE_TANK×20, SPECOPS×23, SIEGE_TANK×28, HELI×22, SPECOPS×27, DRONE×32, HELI×34, HELI×34, SIEGE_TANK×24, SIEGE_TANK×34 |
| 🟥 | Shrieking Horde | random | Modern 96%, Future 4% | ⬛ 0/28 (0%) | SPECOPS×9, SOLDIER×6, MECH_WARRIOR×1 | HELI×24, SIEGE_TANK×22, MECH_WARRIOR×33, SPECOPS×27, SPECOPS×24, MECH_WARRIOR×30, HELI×22, THE_GENERAL×999, SPECOPS×31, SIEGE_TANK×30, HELI×24, SIEGE_TANK×28, HELI×28, SIEGE_TANK×24, SIEGE_TANK×32, SIEGE_TANK×32 |
| 🟩 | Relentless Mob | random | Modern 92%, Industrial 6%, Future 2% | 🟠 11/28 (39%) | SOLDIER×7, SPECOPS×4, DRONE×2 | SIEGE_TANK×22, SIEGE_TANK×28, SPECOPS×31, SIEGE_TANK×20, SIEGE_TANK×26, HELI×30, THE_GENERAL×999, MOTORBIKE×27, HELI×28, SIEGE_TANK×28, SIEGE_TANK×28, DRONE×30, MOTORBIKE×27, SPECOPS×26, HELI×22, SOLDIER×32 |
| 🟥 | Muddy Marauders | random | Modern 91%, Industrial 7%, Future 2% | ⬛ 0/28 (0%) | SPECOPS×12, SOLDIER×4 | THE_GENERAL×999, SMALL_TANK×24, HELI×26, SIEGE_TANK×32, SOLDIER×27, HELI×22, MOTORBIKE×21, SOLDIER×32, SPECOPS×33, SIEGE_TANK×34, MECH_WARRIOR×30, SPECOPS×25, HELI×28, SIEGE_TANK×30, HELI×30, SIEGE_TANK×28 |
| 🟩 | Howling Savages | random | Modern 90%, Industrial 7%, Future 3% | 🟠 6/28 (21%) | SPECOPS×6, SOLDIER×5, SIEGE_TANK×1, HELI×1 | MECH_WARRIOR×27, DRONE×22, SPECOPS×25, SOLDIER×22, THE_GENERAL×999, SIEGE_TANK×34, SPECOPS×30, HELI×22, SPECOPS×26, SOLDIER×27, HELI×22, SOLDIER×21, SIEGE_TANK×24, SPECOPS×33, SIEGE_TANK×22, MOTORBIKE×27, SPECOPS×27, SIEGE_TANK×32 |
| 🟥 | Lazy Raiders | random | Modern 93%, Industrial 4%, Future 3% | ⬛ 0/28 (0%) | SOLDIER×9, SPECOPS×8, HELI×1 | HELI×22, SPECOPS×29, DRONE×22, SMALL_TANK×34, MOTORBIKE×21, HELI×22, SPECOPS×25, SPECOPS×27, SIEGE_TANK×24, HELI×30, HELI×32, THE_GENERAL×999, SPECOPS×28, SPECOPS×32, HELI×28, SIEGE_TANK×28, MECH_WARRIOR×24, SPECOPS×22 |
| 🟥 | Angry Mob | random | Modern 96%, Future 4% | ⬛ 0/28 (0%) | SPECOPS×14 | SIEGE_TANK×24, SIEGE_TANK×32, MECH_WARRIOR×30, HELI×24, SPECOPS×31, SPECOPS×21, SIEGE_TANK×32, SIEGE_TANK×22, SIEGE_TANK×20, SIEGE_TANK×22, HELI×30, THE_GENERAL×999, HELI×28, SPECOPS×26, DRONE×28, SPECOPS×30, SIEGE_TANK×28 |
| 🟥 | Forgotten Warband | random | Modern 96%, Future 2%, Industrial 2% | ⬛ 0/28 (0%) | DRONE×20, SPECOPS×4 | SPECOPS×31, THE_GENERAL×999, SPECOPS×21, SPECOPS×29, SPECOPS×25, DRONE×30, SIEGE_TANK×20, SIEGE_TANK×30, SIEGE_TANK×24, SOLDIER×25, HELI×26, SIEGE_TANK×32, SPECOPS×30, SIEGE_TANK×22, SPECOPS×28, SIEGE_TANK×22, SPECOPS×29, SIEGE_TANK×20 |
| 🟥 | Drunken Raiders | random | Modern 93%, Future 4%, Industrial 4% | ⬛ 0/28 (0%) | SPECOPS×14 | SPECOPS×21, SIEGE_TANK×30, SPECOPS×33, SOLDIER×29, SIEGE_TANK×34, SPECOPS×29, SPECOPS×33, SOLDIER×22, MECH_WARRIOR×24, SPECOPS×23, SIEGE_TANK×24, HELI×20, THE_GENERAL×999, DRONE×33, SPECOPS×33, SIEGE_TANK×24, SIEGE_TANK×30 |
| 🟩 | Hungry Invaders | random | Modern 94%, Industrial 4%, Future 2% | 🟡 20/28 (71%) | SPECOPS×3, SOLDIER×2 | SPECOPS×25, HELI×32, SMALL_TANK×26, SPECOPS×22, HELI×22, SPECOPS×20, SPECOPS×23, SPECOPS×21, HELI×24, SPECOPS×21, THE_GENERAL×999, DRONE×29, HELI×34, SMALL_TANK×28, SPECOPS×21, SPECOPS×20 |
| 🟥 | Lazy Raiders | random | Modern 96%, Future 4% | ⬛ 0/28 (0%) | SPECOPS×7, SOLDIER×5, HELI×3 | THE_GENERAL×999, SPECOPS×20, SIEGE_TANK×20, SPECOPS×31, SIEGE_TANK×26, HELI×28, SIEGE_TANK×34, SPECOPS×25, SPECOPS×26, HELI×22, SPECOPS×27, HELI×22, MECH_WARRIOR×27, HELI×24, HELI×32, MECH_WARRIOR×30, SPECOPS×32, HELI×22 |
| 🟥 | Unlucky Raiders | random | Modern 96%, Future 4% | ⬛ 0/28 (0%) | DRONE×24, SPECOPS×2 | SIEGE_TANK×32, SPECOPS×21, SIEGE_TANK×22, SIEGE_TANK×22, SIEGE_TANK×20, HELI×24, SIEGE_TANK×26, SPECOPS×29, DRONE×34, DRONE×22, HELI×30, SIEGE_TANK×28, SPECOPS×29, THE_GENERAL×999, SPECOPS×26, SPECOPS×30, SIEGE_TANK×30, HELI×24 |
| 🟥 | Bored Mercenaries | random | Modern 91%, Industrial 5%, Future 4% | ⬛ 0/28 (0%) | SOLDIER×7, SPECOPS×7, HELI×3 | THE_GENERAL×999, SIEGE_TANK×28, TRANSPORTER×20, SIEGE_TANK×32, SPECOPS×22, MECH_WARRIOR×33, SIEGE_TANK×22, HELI×26, HELI×22, HELI×32, MECH_WARRIOR×24, HELI×30, SIEGE_TANK×34, SOLDIER×23, SPECOPS×29, MOTORBIKE×26, SIEGE_TANK×32 |
| 🟥 | Unlucky Raiders | random | Modern 96%, Industrial 2%, Future 2% | ⬛ 0/28 (0%) | SPECOPS×8, SOLDIER×6, HELI×2 | SPECOPS×23, SPECOPS×21, HELI×32, SIEGE_TANK×28, SIEGE_TANK×34, SPECOPS×26, SPECOPS×27, HELI×24, SPECOPS×32, DRONE×23, SIEGE_TANK×22, SPECOPS×24, SIEGE_TANK×26, THE_GENERAL×999, SIEGE_TANK×32, TRANSPORTER×30 |

#### Mixed Modern

| Tower Era Distribution (51 towers) | Towers |
|---|---|
| Modern 88% (45), Industrial 12% (6) | MG_TOWER×21, RADAR_TOWER×12, NAPALM_THROWER×6, SHOCK_TOWER×6, PARALYZNG_TOWER×6 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟥 | Modern Warfare | hardcoded | Modern 85%, Industrial 12%, Future 4% | ⬛ 0/48 (0%) | SPECOPS×16, SIEGE_TANK×8 | SPECOPS×18, SIEGE_TANK×18, SIEGE_TANK×19, HELI×20, HELI×20, SIEGE_TANK×20, SPECOPS×21, SIEGE_TANK×22, SPECOPS×22, SPECOPS×22, SPECOPS×23, SIEGE_TANK×24, HELI×24, SIEGE_TANK×24, DRONE×25, SIEGE_TANK×26, SPECOPS×26, TRANSPORTER×26, HELI×27, SIEGE_TANK×28, TRANSPORTER×28, SPECOPS×28, HELI×29, SMALL_TANK×30, HELI×30, SIEGE_TANK×33, THE_GENERAL×40, HELI×34 |
| 🟥 | Special Ops | hardcoded | Modern 88%, Industrial 9%, Future 4% | ⬛ 0/48 (0%) | SPECOPS×21, SIEGE_TANK×3 | HELI×18, HELI×18, SPECOPS×19, SIEGE_TANK×20, SIEGE_TANK×20, SIEGE_TANK×20, SPECOPS×21, SPECOPS×22, SPECOPS×22, HELI×22, SIEGE_TANK×23, SPECOPS×24, SIEGE_TANK×24, HELI×24, HELI×25, MECH_WARRIOR×26, SPECOPS×26, SIEGE_TANK×26, SPECOPS×27, HELI×28, SPECOPS×28, TRANSPORTER×28, HELI×29, SIEGE_TANK×30, HELI×30, SMALL_TANK×32, SIEGE_TANK×33, THE_GENERAL×36 |
| 🟥 | Heli Strike | hardcoded | Modern 82%, Industrial 13%, Future 5% | ⬛ 0/48 (0%) | SIEGE_TANK×12, SPECOPS×9, SOLDIER×5, DRONE×1 | HELI×18, SPECOPS×18, HELI×19, SPECOPS×20, HELI×20, SPECOPS×20, SPECOPS×21, SPECOPS×22, TRANSPORTER×22, SPECOPS×22, SPECOPS×23, SIEGE_TANK×24, HELI×24, TRANSPORTER×24, SIEGE_TANK×25, HELI×26, SPECOPS×26, MOTORBIKE×26, SPECOPS×27, HELI×28, TRANSPORTER×28, HELI×28, HELI×29, SIEGE_TANK×30, SPECOPS×30, THE_GENERAL×35, DRONE×36, SIEGE_TANK×36, HELI×40 |
| 🟥 | Siege Assault | hardcoded | Modern 82%, Industrial 11%, Future 4%, Renaissance 3% | ⬛ 0/48 (0%) | SPECOPS×15, SIEGE_TANK×8, HELI×1 | SIEGE_TANK×18, SIEGE_TANK×18, SIEGE_TANK×19, SPECOPS×20, HELI×20, SPECOPS×20, TRANSPORTER×21, SIEGE_TANK×22, NINJA×22, HELI×22, SIEGE_TANK×23, SIEGE_TANK×24, SOLDIER×24, SPECOPS×24, SIEGE_TANK×25, SPECOPS×26, SPECOPS×26, HELI×26, SIEGE_TANK×27, TRANSPORTER×28, HELI×28, HELI×28, SIEGE_TANK×29, MECH_WARRIOR×30, SPECOPS×30, THE_GENERAL×40, SIEGE_TANK×40 |
| 🟥 | Urban Combat | hardcoded | Modern 83%, Industrial 12%, Future 5% | ⬛ 0/48 (0%) | SPECOPS×13, SIEGE_TANK×2, THE_GENERAL×1 | SPECOPS×18, SIEGE_TANK×18, SPECOPS×19, THE_GENERAL×20, SPECOPS×20, SPECOPS×20, HELI×21, SPECOPS×22, SPECOPS×22, SIEGE_TANK×22, SIEGE_TANK×23, SIEGE_TANK×24, SPECOPS×24, SOLDIER×24, SPECOPS×25, SPECOPS×26, SIEGE_TANK×26, HELI×26, SPECOPS×27, HELI×28, SPECOPS×28, HELI×28, TRANSPORTER×29, HELI×30, SMALL_TANK×30, DRONE×34, SIEGE_TANK×36, SPECOPS×37 |
| 🟥 | Cyber Strike | hardcoded | Modern 91%, Future 4%, Industrial 4% | ⬛ 0/48 (0%) | SPECOPS×20, SIEGE_TANK×4 | SIEGE_TANK×18, HELI×18, HELI×19, SPECOPS×19, SPECOPS×20, SPECOPS×20, SIEGE_TANK×21, SPECOPS×21, SPECOPS×21, SIEGE_TANK×22, SPECOPS×22, SPECOPS×23, SPECOPS×23, SIEGE_TANK×24, SIEGE_TANK×24, SIEGE_TANK×24, HELI×25, SPECOPS×25, HELI×26, SIEGE_TANK×26, SPECOPS×27, SPECOPS×27, HELI×27, SIEGE_TANK×28, SIEGE_TANK×28, SOLDIER×29, DRONE×30, THE_GENERAL×35 |
| 🟥 | Shrieking Horde | random | Modern 96%, Future 4% | ⬛ 0/48 (0%) | SPECOPS×14, MECH_WARRIOR×5 | HELI×22, SPECOPS×31, MECH_WARRIOR×33, SIEGE_TANK×22, SPECOPS×21, SIEGE_TANK×26, SPECOPS×31, SPECOPS×27, THE_GENERAL×999, SPECOPS×28, HELI×24, HELI×26, SIEGE_TANK×22, DRONE×31, SPECOPS×34, SIEGE_TANK×22, SIEGE_TANK×26, SPECOPS×30 |
| 🟥 | Shrieking Horde | random | Modern 96%, Future 4% | ⬛ 0/48 (0%) | SPECOPS×14, MECH_WARRIOR×5 | HELI×22, SPECOPS×31, MECH_WARRIOR×33, SIEGE_TANK×22, SPECOPS×21, SIEGE_TANK×26, SPECOPS×31, SPECOPS×27, THE_GENERAL×999, SPECOPS×28, HELI×24, HELI×26, SIEGE_TANK×22, DRONE×31, SPECOPS×34, SIEGE_TANK×22, SIEGE_TANK×26, SPECOPS×30 |
| 🟥 | Stubborn Raiders | random | Modern 96%, Future 2%, Industrial 1% | ⬛ 0/48 (0%) | SPECOPS×17, SIEGE_TANK×7 | SIEGE_TANK×26, SIEGE_TANK×28, HELI×20, SPECOPS×29, SIEGE_TANK×22, THE_GENERAL×999, SIEGE_TANK×32, SPECOPS×22, SIEGE_TANK×34, HELI×24, MECH_WARRIOR×30, HELI×20, SPECOPS×31, HELI×26, SPECOPS×25, HELI×26, SOLDIER×21, HELI×32 |
| 🟥 | Shrieking Horde | random | Modern 98%, Future 2% | ⬛ 0/48 (0%) | SPECOPS×14, SIEGE_TANK×10 | SIEGE_TANK×26, HELI×24, SPECOPS×27, SIEGE_TANK×24, SPECOPS×31, SIEGE_TANK×26, SIEGE_TANK×30, HELI×22, SPECOPS×20, MECH_WARRIOR×27, HELI×20, THE_GENERAL×999, SIEGE_TANK×30, SIEGE_TANK×30, SIEGE_TANK×30, SPECOPS×32, SPECOPS×30, HELI×30 |
| 🟥 | Relentless Mob | random | Modern 96%, Future 2%, Industrial 2% | ⬛ 0/48 (0%) | SPECOPS×15, SIEGE_TANK×9 | DRONE×29, HELI×22, HELI×26, SPECOPS×30, SIEGE_TANK×30, HELI×34, MOTORBIKE×28, SPECOPS×30, SIEGE_TANK×24, SPECOPS×20, SPECOPS×27, HELI×26, HELI×26, SPECOPS×28, SPECOPS×25, HELI×22, THE_GENERAL×999, SPECOPS×31, HELI×32 |
| 🟥 | Desperate Looters | random | Modern 92%, Industrial 5%, Future 2% | ⬛ 0/48 (0%) | SPECOPS×16, SIEGE_TANK×8 | DRONE×32, SIEGE_TANK×24, SPECOPS×33, MOTORBIKE×34, MOTORBIKE×25, SIEGE_TANK×26, HELI×22, HELI×30, SIEGE_TANK×26, SIEGE_TANK×30, SPECOPS×33, SPECOPS×31, HELI×30, SIEGE_TANK×32, THE_GENERAL×999, HELI×24, TRANSPORTER×20, SIEGE_TANK×22 |
| 🟥 | Ragged Warband | random | Modern 96%, Future 4% | ⬛ 0/48 (0%) | SOLDIER×11, SIEGE_TANK×9, SPECOPS×8, DRONE×3 | SIEGE_TANK×20, SPECOPS×31, HELI×26, DRONE×28, SIEGE_TANK×28, HELI×34, THE_GENERAL×999, HELI×34, SIEGE_TANK×20, SPECOPS×23, SIEGE_TANK×28, HELI×22, SPECOPS×27, DRONE×32, HELI×34, HELI×34, SIEGE_TANK×24, SIEGE_TANK×34 |
| 🟥 | Shrieking Horde | random | Modern 96%, Future 4% | ⬛ 0/48 (0%) | SPECOPS×22, MECH_WARRIOR×1 | HELI×24, SIEGE_TANK×22, MECH_WARRIOR×33, SPECOPS×27, SPECOPS×24, MECH_WARRIOR×30, HELI×22, THE_GENERAL×999, SPECOPS×31, SIEGE_TANK×30, HELI×24, SIEGE_TANK×28, HELI×28, SIEGE_TANK×24, SIEGE_TANK×32, SIEGE_TANK×32 |
| 🟥 | Relentless Mob | random | Modern 92%, Industrial 6%, Future 2% | ⬛ 0/48 (0%) | SIEGE_TANK×12, SPECOPS×12 | SIEGE_TANK×22, SIEGE_TANK×28, SPECOPS×31, SIEGE_TANK×20, SIEGE_TANK×26, HELI×30, THE_GENERAL×999, MOTORBIKE×27, HELI×28, SIEGE_TANK×28, SIEGE_TANK×28, DRONE×30, MOTORBIKE×27, SPECOPS×26, HELI×22, SOLDIER×32 |
| 🟥 | Muddy Marauders | random | Modern 91%, Industrial 7%, Future 2% | ⬛ 0/48 (0%) | SOLDIER×12, SPECOPS×10, SIEGE_TANK×7, HELI×1 | THE_GENERAL×999, SMALL_TANK×24, HELI×26, SIEGE_TANK×32, SOLDIER×27, HELI×22, MOTORBIKE×21, SOLDIER×32, SPECOPS×33, SIEGE_TANK×34, MECH_WARRIOR×30, SPECOPS×25, HELI×28, SIEGE_TANK×30, HELI×30, SIEGE_TANK×28 |
| 🟥 | Howling Savages | random | Modern 90%, Industrial 7%, Future 3% | ⬛ 0/48 (0%) | SPECOPS×21, SOLDIER×2, MECH_WARRIOR×1 | MECH_WARRIOR×27, DRONE×22, SPECOPS×25, SOLDIER×22, THE_GENERAL×999, SIEGE_TANK×34, SPECOPS×30, HELI×22, SPECOPS×26, SOLDIER×27, HELI×22, SOLDIER×21, SIEGE_TANK×24, SPECOPS×33, SIEGE_TANK×22, MOTORBIKE×27, SPECOPS×27, SIEGE_TANK×32 |
| 🟥 | Lazy Raiders | random | Modern 93%, Industrial 4%, Future 3% | ⬛ 0/48 (0%) | SPECOPS×12, SIEGE_TANK×8, SOLDIER×4, HELI×1, DRONE×1 | HELI×22, SPECOPS×29, DRONE×22, SMALL_TANK×34, MOTORBIKE×21, HELI×22, SPECOPS×25, SPECOPS×27, SIEGE_TANK×24, HELI×30, HELI×32, THE_GENERAL×999, SPECOPS×28, SPECOPS×32, HELI×28, SIEGE_TANK×28, MECH_WARRIOR×24, SPECOPS×22 |
| 🟥 | Angry Mob | random | Modern 96%, Future 4% | ⬛ 0/48 (0%) | SOLDIER×16, SIEGE_TANK×6, SPECOPS×6, MECH_WARRIOR×2 | SIEGE_TANK×24, SIEGE_TANK×32, MECH_WARRIOR×30, HELI×24, SPECOPS×31, SPECOPS×21, SIEGE_TANK×32, SIEGE_TANK×22, SIEGE_TANK×20, SIEGE_TANK×22, HELI×30, THE_GENERAL×999, HELI×28, SPECOPS×26, DRONE×28, SPECOPS×30, SIEGE_TANK×28 |
| 🟥 | Forgotten Warband | random | Modern 96%, Future 2%, Industrial 2% | ⬛ 0/48 (0%) | SPECOPS×14, DRONE×6, THE_GENERAL×1 | SPECOPS×31, THE_GENERAL×999, SPECOPS×21, SPECOPS×29, SPECOPS×25, DRONE×30, SIEGE_TANK×20, SIEGE_TANK×30, SIEGE_TANK×24, SOLDIER×25, HELI×26, SIEGE_TANK×32, SPECOPS×30, SIEGE_TANK×22, SPECOPS×28, SIEGE_TANK×22, SPECOPS×29, SIEGE_TANK×20 |
| 🟥 | Drunken Raiders | random | Modern 93%, Future 4%, Industrial 4% | ⬛ 0/48 (0%) | SPECOPS×17, SIEGE_TANK×7 | SPECOPS×21, SIEGE_TANK×30, SPECOPS×33, SOLDIER×29, SIEGE_TANK×34, SPECOPS×29, SPECOPS×33, SOLDIER×22, MECH_WARRIOR×24, SPECOPS×23, SIEGE_TANK×24, HELI×20, THE_GENERAL×999, DRONE×33, SPECOPS×33, SIEGE_TANK×24, SIEGE_TANK×30 |
| 🟩 | Hungry Invaders | random | Modern 94%, Industrial 4%, Future 2% | 🟡 34/48 (71%) | SOLDIER×6, SPECOPS×4 | SPECOPS×25, HELI×32, SMALL_TANK×26, SPECOPS×22, HELI×22, SPECOPS×20, SPECOPS×23, SPECOPS×21, HELI×24, SPECOPS×21, THE_GENERAL×999, DRONE×29, HELI×34, SMALL_TANK×28, SPECOPS×21, SPECOPS×20 |
| 🟥 | Lazy Raiders | random | Modern 96%, Future 4% | ⬛ 0/48 (0%) | SOLDIER×10, SPECOPS×6, SIEGE_TANK×4, THE_GENERAL×1 | THE_GENERAL×999, SPECOPS×20, SIEGE_TANK×20, SPECOPS×31, SIEGE_TANK×26, HELI×28, SIEGE_TANK×34, SPECOPS×25, SPECOPS×26, HELI×22, SPECOPS×27, HELI×22, MECH_WARRIOR×27, HELI×24, HELI×32, MECH_WARRIOR×30, SPECOPS×32, HELI×22 |
| 🟥 | Unlucky Raiders | random | Modern 96%, Future 4% | ⬛ 0/48 (0%) | DRONE×15, SIEGE_TANK×14, SOLDIER×5 | SIEGE_TANK×32, SPECOPS×21, SIEGE_TANK×22, SIEGE_TANK×22, SIEGE_TANK×20, HELI×24, SIEGE_TANK×26, SPECOPS×29, DRONE×34, DRONE×22, HELI×30, SIEGE_TANK×28, SPECOPS×29, THE_GENERAL×999, SPECOPS×26, SPECOPS×30, SIEGE_TANK×30, HELI×24 |
| 🟥 | Bored Mercenaries | random | Modern 91%, Industrial 5%, Future 4% | ⬛ 0/48 (0%) | SPECOPS×9, SIEGE_TANK×6, THE_GENERAL×1 | THE_GENERAL×999, SIEGE_TANK×28, TRANSPORTER×20, SIEGE_TANK×32, SPECOPS×22, MECH_WARRIOR×33, SIEGE_TANK×22, HELI×26, HELI×22, HELI×32, MECH_WARRIOR×24, HELI×30, SIEGE_TANK×34, SOLDIER×23, SPECOPS×29, MOTORBIKE×26, SIEGE_TANK×32 |
| 🟥 | Unlucky Raiders | random | Modern 96%, Industrial 2%, Future 2% | ⬛ 0/48 (0%) | SPECOPS×23, SOLDIER×2 | SPECOPS×23, SPECOPS×21, HELI×32, SIEGE_TANK×28, SIEGE_TANK×34, SPECOPS×26, SPECOPS×27, HELI×24, SPECOPS×32, DRONE×23, SIEGE_TANK×22, SPECOPS×24, SIEGE_TANK×26, THE_GENERAL×999, SIEGE_TANK×32, TRANSPORTER×30 |

#### S2 Gempire

| Tower Era Distribution (66 towers) | Towers |
|---|---|
| Modern 65% (43), Industrial 21% (14), Iron Age 12% (8), Renaissance 2% (1) | RADAR_TOWER×29, FLAME_THROWER×13, ANTI_AIR_TOWER×11, COLD_TOWER×8, LASER_TOWER×3, ICE_TOWER×1, SHOCK_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Modern Warfare | hardcoded | Modern 85%, Industrial 12%, Future 4% | 🟢 38/38 (100%) |  | SPECOPS×18, SIEGE_TANK×18, SIEGE_TANK×19, HELI×20, HELI×20, SIEGE_TANK×20, SPECOPS×21, SIEGE_TANK×22, SPECOPS×22, SPECOPS×22, SPECOPS×23, SIEGE_TANK×24, HELI×24, SIEGE_TANK×24, DRONE×25, SIEGE_TANK×26, SPECOPS×26, TRANSPORTER×26, HELI×27, SIEGE_TANK×28, TRANSPORTER×28, SPECOPS×28, HELI×29, SMALL_TANK×30, HELI×30, SIEGE_TANK×33, THE_GENERAL×40, HELI×34 |
| 🟩 | Special Ops | hardcoded | Modern 88%, Industrial 9%, Future 4% | 🟢 38/38 (100%) |  | HELI×18, HELI×18, SPECOPS×19, SIEGE_TANK×20, SIEGE_TANK×20, SIEGE_TANK×20, SPECOPS×21, SPECOPS×22, SPECOPS×22, HELI×22, SIEGE_TANK×23, SPECOPS×24, SIEGE_TANK×24, HELI×24, HELI×25, MECH_WARRIOR×26, SPECOPS×26, SIEGE_TANK×26, SPECOPS×27, HELI×28, SPECOPS×28, TRANSPORTER×28, HELI×29, SIEGE_TANK×30, HELI×30, SMALL_TANK×32, SIEGE_TANK×33, THE_GENERAL×36 |
| 🟩 | Heli Strike | hardcoded | Modern 82%, Industrial 13%, Future 5% | 🟢 38/38 (100%) |  | HELI×18, SPECOPS×18, HELI×19, SPECOPS×20, HELI×20, SPECOPS×20, SPECOPS×21, SPECOPS×22, TRANSPORTER×22, SPECOPS×22, SPECOPS×23, SIEGE_TANK×24, HELI×24, TRANSPORTER×24, SIEGE_TANK×25, HELI×26, SPECOPS×26, MOTORBIKE×26, SPECOPS×27, HELI×28, TRANSPORTER×28, HELI×28, HELI×29, SIEGE_TANK×30, SPECOPS×30, THE_GENERAL×35, DRONE×36, SIEGE_TANK×36, HELI×40 |
| 🟩 | Siege Assault | hardcoded | Modern 82%, Industrial 11%, Future 4%, Renaissance 3% | 🟡 30/38 (79%) | SPECOPS×4 | SIEGE_TANK×18, SIEGE_TANK×18, SIEGE_TANK×19, SPECOPS×20, HELI×20, SPECOPS×20, TRANSPORTER×21, SIEGE_TANK×22, NINJA×22, HELI×22, SIEGE_TANK×23, SIEGE_TANK×24, SOLDIER×24, SPECOPS×24, SIEGE_TANK×25, SPECOPS×26, SPECOPS×26, HELI×26, SIEGE_TANK×27, TRANSPORTER×28, HELI×28, HELI×28, SIEGE_TANK×29, MECH_WARRIOR×30, SPECOPS×30, THE_GENERAL×40, SIEGE_TANK×40 |
| 🟩 | Urban Combat | hardcoded | Modern 83%, Industrial 12%, Future 5% | 🟢 38/38 (100%) |  | SPECOPS×18, SIEGE_TANK×18, SPECOPS×19, THE_GENERAL×20, SPECOPS×20, SPECOPS×20, HELI×21, SPECOPS×22, SPECOPS×22, SIEGE_TANK×22, SIEGE_TANK×23, SIEGE_TANK×24, SPECOPS×24, SOLDIER×24, SPECOPS×25, SPECOPS×26, SIEGE_TANK×26, HELI×26, SPECOPS×27, HELI×28, SPECOPS×28, HELI×28, TRANSPORTER×29, HELI×30, SMALL_TANK×30, DRONE×34, SIEGE_TANK×36, SPECOPS×37 |
| 🟩 | Cyber Strike | hardcoded | Modern 91%, Future 4%, Industrial 4% | 🟢 38/38 (100%) |  | SIEGE_TANK×18, HELI×18, HELI×19, SPECOPS×19, SPECOPS×20, SPECOPS×20, SIEGE_TANK×21, SPECOPS×21, SPECOPS×21, SIEGE_TANK×22, SPECOPS×22, SPECOPS×23, SPECOPS×23, SIEGE_TANK×24, SIEGE_TANK×24, SIEGE_TANK×24, HELI×25, SPECOPS×25, HELI×26, SIEGE_TANK×26, SPECOPS×27, SPECOPS×27, HELI×27, SIEGE_TANK×28, SIEGE_TANK×28, SOLDIER×29, DRONE×30, THE_GENERAL×35 |
| 🟩 | Shrieking Horde | random | Modern 96%, Future 4% | 🟢 38/38 (100%) |  | HELI×22, SPECOPS×31, MECH_WARRIOR×33, SIEGE_TANK×22, SPECOPS×21, SIEGE_TANK×26, SPECOPS×31, SPECOPS×27, THE_GENERAL×999, SPECOPS×28, HELI×24, HELI×26, SIEGE_TANK×22, DRONE×31, SPECOPS×34, SIEGE_TANK×22, SIEGE_TANK×26, SPECOPS×30 |
| 🟩 | Shrieking Horde | random | Modern 96%, Future 4% | 🟢 38/38 (100%) |  | HELI×22, SPECOPS×31, MECH_WARRIOR×33, SIEGE_TANK×22, SPECOPS×21, SIEGE_TANK×26, SPECOPS×31, SPECOPS×27, THE_GENERAL×999, SPECOPS×28, HELI×24, HELI×26, SIEGE_TANK×22, DRONE×31, SPECOPS×34, SIEGE_TANK×22, SIEGE_TANK×26, SPECOPS×30 |
| 🟩 | Stubborn Raiders | random | Modern 96%, Future 2%, Industrial 1% | 🟢 37/38 (97%) | SOLDIER×1 | SIEGE_TANK×26, SIEGE_TANK×28, HELI×20, SPECOPS×29, SIEGE_TANK×22, THE_GENERAL×999, SIEGE_TANK×32, SPECOPS×22, SIEGE_TANK×34, HELI×24, MECH_WARRIOR×30, HELI×20, SPECOPS×31, HELI×26, SPECOPS×25, HELI×26, SOLDIER×21, HELI×32 |
| 🟩 | Shrieking Horde | random | Modern 98%, Future 2% | 🟢 38/38 (100%) |  | SIEGE_TANK×26, HELI×24, SPECOPS×27, SIEGE_TANK×24, SPECOPS×31, SIEGE_TANK×26, SIEGE_TANK×30, HELI×22, SPECOPS×20, MECH_WARRIOR×27, HELI×20, THE_GENERAL×999, SIEGE_TANK×30, SIEGE_TANK×30, SIEGE_TANK×30, SPECOPS×32, SPECOPS×30, HELI×30 |
| 🟩 | Relentless Mob | random | Modern 96%, Future 2%, Industrial 2% | 🟢 38/38 (100%) |  | DRONE×29, HELI×22, HELI×26, SPECOPS×30, SIEGE_TANK×30, HELI×34, MOTORBIKE×28, SPECOPS×30, SIEGE_TANK×24, SPECOPS×20, SPECOPS×27, HELI×26, HELI×26, SPECOPS×28, SPECOPS×25, HELI×22, THE_GENERAL×999, SPECOPS×31, HELI×32 |
| 🟩 | Desperate Looters | random | Modern 92%, Industrial 5%, Future 2% | 🟢 32/38 (84%) | SPECOPS×2, SOLDIER×2 | DRONE×32, SIEGE_TANK×24, SPECOPS×33, MOTORBIKE×34, MOTORBIKE×25, SIEGE_TANK×26, HELI×22, HELI×30, SIEGE_TANK×26, SIEGE_TANK×30, SPECOPS×33, SPECOPS×31, HELI×30, SIEGE_TANK×32, THE_GENERAL×999, HELI×24, TRANSPORTER×20, SIEGE_TANK×22 |
| 🟩 | Ragged Warband | random | Modern 96%, Future 4% | 🟢 35/38 (92%) | DRONE×3 | SIEGE_TANK×20, SPECOPS×31, HELI×26, DRONE×28, SIEGE_TANK×28, HELI×34, THE_GENERAL×999, HELI×34, SIEGE_TANK×20, SPECOPS×23, SIEGE_TANK×28, HELI×22, SPECOPS×27, DRONE×32, HELI×34, HELI×34, SIEGE_TANK×24, SIEGE_TANK×34 |
| 🟩 | Shrieking Horde | random | Modern 96%, Future 4% | 🟡 28/38 (74%) | SPECOPS×5 | HELI×24, SIEGE_TANK×22, MECH_WARRIOR×33, SPECOPS×27, SPECOPS×24, MECH_WARRIOR×30, HELI×22, THE_GENERAL×999, SPECOPS×31, SIEGE_TANK×30, HELI×24, SIEGE_TANK×28, HELI×28, SIEGE_TANK×24, SIEGE_TANK×32, SIEGE_TANK×32 |
| 🟩 | Relentless Mob | random | Modern 92%, Industrial 6%, Future 2% | 🟢 38/38 (100%) |  | SIEGE_TANK×22, SIEGE_TANK×28, SPECOPS×31, SIEGE_TANK×20, SIEGE_TANK×26, HELI×30, THE_GENERAL×999, MOTORBIKE×27, HELI×28, SIEGE_TANK×28, SIEGE_TANK×28, DRONE×30, MOTORBIKE×27, SPECOPS×26, HELI×22, SOLDIER×32 |
| 🟩 | Muddy Marauders | random | Modern 91%, Industrial 7%, Future 2% | 🟡 24/38 (63%) | SPECOPS×6, SOLDIER×2 | THE_GENERAL×999, SMALL_TANK×24, HELI×26, SIEGE_TANK×32, SOLDIER×27, HELI×22, MOTORBIKE×21, SOLDIER×32, SPECOPS×33, SIEGE_TANK×34, MECH_WARRIOR×30, SPECOPS×25, HELI×28, SIEGE_TANK×30, HELI×30, SIEGE_TANK×28 |
| 🟩 | Howling Savages | random | Modern 90%, Industrial 7%, Future 3% | 🟢 32/38 (84%) | SPECOPS×2, SOLDIER×2 | MECH_WARRIOR×27, DRONE×22, SPECOPS×25, SOLDIER×22, THE_GENERAL×999, SIEGE_TANK×34, SPECOPS×30, HELI×22, SPECOPS×26, SOLDIER×27, HELI×22, SOLDIER×21, SIEGE_TANK×24, SPECOPS×33, SIEGE_TANK×22, MOTORBIKE×27, SPECOPS×27, SIEGE_TANK×32 |
| 🟩 | Lazy Raiders | random | Modern 93%, Industrial 4%, Future 3% | 🟢 38/38 (100%) |  | HELI×22, SPECOPS×29, DRONE×22, SMALL_TANK×34, MOTORBIKE×21, HELI×22, SPECOPS×25, SPECOPS×27, SIEGE_TANK×24, HELI×30, HELI×32, THE_GENERAL×999, SPECOPS×28, SPECOPS×32, HELI×28, SIEGE_TANK×28, MECH_WARRIOR×24, SPECOPS×22 |
| 🟩 | Angry Mob | random | Modern 96%, Future 4% | 🟢 34/38 (89%) | SPECOPS×2 | SIEGE_TANK×24, SIEGE_TANK×32, MECH_WARRIOR×30, HELI×24, SPECOPS×31, SPECOPS×21, SIEGE_TANK×32, SIEGE_TANK×22, SIEGE_TANK×20, SIEGE_TANK×22, HELI×30, THE_GENERAL×999, HELI×28, SPECOPS×26, DRONE×28, SPECOPS×30, SIEGE_TANK×28 |
| 🟩 | Forgotten Warband | random | Modern 96%, Future 2%, Industrial 2% | 🟢 38/38 (100%) |  | SPECOPS×31, THE_GENERAL×999, SPECOPS×21, SPECOPS×29, SPECOPS×25, DRONE×30, SIEGE_TANK×20, SIEGE_TANK×30, SIEGE_TANK×24, SOLDIER×25, HELI×26, SIEGE_TANK×32, SPECOPS×30, SIEGE_TANK×22, SPECOPS×28, SIEGE_TANK×22, SPECOPS×29, SIEGE_TANK×20 |
| 🟩 | Drunken Raiders | random | Modern 93%, Future 4%, Industrial 4% | 🟢 38/38 (100%) |  | SPECOPS×21, SIEGE_TANK×30, SPECOPS×33, SOLDIER×29, SIEGE_TANK×34, SPECOPS×29, SPECOPS×33, SOLDIER×22, MECH_WARRIOR×24, SPECOPS×23, SIEGE_TANK×24, HELI×20, THE_GENERAL×999, DRONE×33, SPECOPS×33, SIEGE_TANK×24, SIEGE_TANK×30 |
| 🟩 | Hungry Invaders | random | Modern 94%, Industrial 4%, Future 2% | 🟢 38/38 (100%) |  | SPECOPS×25, HELI×32, SMALL_TANK×26, SPECOPS×22, HELI×22, SPECOPS×20, SPECOPS×23, SPECOPS×21, HELI×24, SPECOPS×21, THE_GENERAL×999, DRONE×29, HELI×34, SMALL_TANK×28, SPECOPS×21, SPECOPS×20 |
| 🟩 | Lazy Raiders | random | Modern 96%, Future 4% | 🟢 34/38 (89%) | SPECOPS×2 | THE_GENERAL×999, SPECOPS×20, SIEGE_TANK×20, SPECOPS×31, SIEGE_TANK×26, HELI×28, SIEGE_TANK×34, SPECOPS×25, SPECOPS×26, HELI×22, SPECOPS×27, HELI×22, MECH_WARRIOR×27, HELI×24, HELI×32, MECH_WARRIOR×30, SPECOPS×32, HELI×22 |
| 🟩 | Unlucky Raiders | random | Modern 96%, Future 4% | 🟡 27/38 (71%) | DRONE×9, SPECOPS×1 | SIEGE_TANK×32, SPECOPS×21, SIEGE_TANK×22, SIEGE_TANK×22, SIEGE_TANK×20, HELI×24, SIEGE_TANK×26, SPECOPS×29, DRONE×34, DRONE×22, HELI×30, SIEGE_TANK×28, SPECOPS×29, THE_GENERAL×999, SPECOPS×26, SPECOPS×30, SIEGE_TANK×30, HELI×24 |
| 🟩 | Bored Mercenaries | random | Modern 91%, Industrial 5%, Future 4% | 🟢 38/38 (100%) |  | THE_GENERAL×999, SIEGE_TANK×28, TRANSPORTER×20, SIEGE_TANK×32, SPECOPS×22, MECH_WARRIOR×33, SIEGE_TANK×22, HELI×26, HELI×22, HELI×32, MECH_WARRIOR×24, HELI×30, SIEGE_TANK×34, SOLDIER×23, SPECOPS×29, MOTORBIKE×26, SIEGE_TANK×32 |
| 🟩 | Unlucky Raiders | random | Modern 96%, Industrial 2%, Future 2% | 🟢 32/38 (84%) | DRONE×6 | SPECOPS×23, SPECOPS×21, HELI×32, SIEGE_TANK×28, SIEGE_TANK×34, SPECOPS×26, SPECOPS×27, HELI×24, SPECOPS×32, DRONE×23, SIEGE_TANK×22, SPECOPS×24, SIEGE_TANK×26, THE_GENERAL×999, SIEGE_TANK×32, TRANSPORTER×30 |

#### S2 Wicked$Kingdom

| Tower Era Distribution (62 towers) | Towers |
|---|---|
| Industrial 48% (30), Modern 34% (21), Iron Age 16% (10), Renaissance 2% (1) | RADAR_TOWER×21, GATLING_TOWER×19, FLAME_THROWER×11, COLD_TOWER×10, ICE_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Modern Warfare | hardcoded | Modern 85%, Industrial 12%, Future 4% | 🟡 28/38 (74%) | SOLDIER×8, SPECOPS×1 | SPECOPS×18, SIEGE_TANK×18, SIEGE_TANK×19, HELI×20, HELI×20, SIEGE_TANK×20, SPECOPS×21, SIEGE_TANK×22, SPECOPS×22, SPECOPS×22, SPECOPS×23, SIEGE_TANK×24, HELI×24, SIEGE_TANK×24, DRONE×25, SIEGE_TANK×26, SPECOPS×26, TRANSPORTER×26, HELI×27, SIEGE_TANK×28, TRANSPORTER×28, SPECOPS×28, HELI×29, SMALL_TANK×30, HELI×30, SIEGE_TANK×33, THE_GENERAL×40, HELI×34 |
| 🟥 | Special Ops | hardcoded | Modern 88%, Industrial 9%, Future 4% | ⬛ 0/38 (0%) | SPECOPS×16, SOLDIER×6 | HELI×18, HELI×18, SPECOPS×19, SIEGE_TANK×20, SIEGE_TANK×20, SIEGE_TANK×20, SPECOPS×21, SPECOPS×22, SPECOPS×22, HELI×22, SIEGE_TANK×23, SPECOPS×24, SIEGE_TANK×24, HELI×24, HELI×25, MECH_WARRIOR×26, SPECOPS×26, SIEGE_TANK×26, SPECOPS×27, HELI×28, SPECOPS×28, TRANSPORTER×28, HELI×29, SIEGE_TANK×30, HELI×30, SMALL_TANK×32, SIEGE_TANK×33, THE_GENERAL×36 |
| 🟩 | Heli Strike | hardcoded | Modern 82%, Industrial 13%, Future 5% | 🟠 12/38 (32%) | DRONE×9, SOLDIER×7, SPECOPS×5 | HELI×18, SPECOPS×18, HELI×19, SPECOPS×20, HELI×20, SPECOPS×20, SPECOPS×21, SPECOPS×22, TRANSPORTER×22, SPECOPS×22, SPECOPS×23, SIEGE_TANK×24, HELI×24, TRANSPORTER×24, SIEGE_TANK×25, HELI×26, SPECOPS×26, MOTORBIKE×26, SPECOPS×27, HELI×28, TRANSPORTER×28, HELI×28, HELI×29, SIEGE_TANK×30, SPECOPS×30, THE_GENERAL×35, DRONE×36, SIEGE_TANK×36, HELI×40 |
| 🟩 | Siege Assault | hardcoded | Modern 82%, Industrial 11%, Future 4%, Renaissance 3% | 🔴 5/38 (13%) | SPECOPS×10, SOLDIER×7, SIEGE_TANK×1, MECH_WARRIOR×1 | SIEGE_TANK×18, SIEGE_TANK×18, SIEGE_TANK×19, SPECOPS×20, HELI×20, SPECOPS×20, TRANSPORTER×21, SIEGE_TANK×22, NINJA×22, HELI×22, SIEGE_TANK×23, SIEGE_TANK×24, SOLDIER×24, SPECOPS×24, SIEGE_TANK×25, SPECOPS×26, SPECOPS×26, HELI×26, SIEGE_TANK×27, TRANSPORTER×28, HELI×28, HELI×28, SIEGE_TANK×29, MECH_WARRIOR×30, SPECOPS×30, THE_GENERAL×40, SIEGE_TANK×40 |
| 🟥 | Urban Combat | hardcoded | Modern 83%, Industrial 12%, Future 5% | ⬛ 0/38 (0%) | SPECOPS×17, SOLDIER×4 | SPECOPS×18, SIEGE_TANK×18, SPECOPS×19, THE_GENERAL×20, SPECOPS×20, SPECOPS×20, HELI×21, SPECOPS×22, SPECOPS×22, SIEGE_TANK×22, SIEGE_TANK×23, SIEGE_TANK×24, SPECOPS×24, SOLDIER×24, SPECOPS×25, SPECOPS×26, SIEGE_TANK×26, HELI×26, SPECOPS×27, HELI×28, SPECOPS×28, HELI×28, TRANSPORTER×29, HELI×30, SMALL_TANK×30, DRONE×34, SIEGE_TANK×36, SPECOPS×37 |
| 🟩 | Cyber Strike | hardcoded | Modern 91%, Future 4%, Industrial 4% | 🔴 5/38 (13%) | SPECOPS×12, SOLDIER×7, DRONE×2 | SIEGE_TANK×18, HELI×18, HELI×19, SPECOPS×19, SPECOPS×20, SPECOPS×20, SIEGE_TANK×21, SPECOPS×21, SPECOPS×21, SIEGE_TANK×22, SPECOPS×22, SPECOPS×23, SPECOPS×23, SIEGE_TANK×24, SIEGE_TANK×24, SIEGE_TANK×24, HELI×25, SPECOPS×25, HELI×26, SIEGE_TANK×26, SPECOPS×27, SPECOPS×27, HELI×27, SIEGE_TANK×28, SIEGE_TANK×28, SOLDIER×29, DRONE×30, THE_GENERAL×35 |
| 🟥 | Shrieking Horde | random | Modern 96%, Future 4% | ⬛ 0/38 (0%) | SPECOPS×17, MECH_WARRIOR×1 | HELI×22, SPECOPS×31, MECH_WARRIOR×33, SIEGE_TANK×22, SPECOPS×21, SIEGE_TANK×26, SPECOPS×31, SPECOPS×27, THE_GENERAL×999, SPECOPS×28, HELI×24, HELI×26, SIEGE_TANK×22, DRONE×31, SPECOPS×34, SIEGE_TANK×22, SIEGE_TANK×26, SPECOPS×30 |
| 🟥 | Shrieking Horde | random | Modern 96%, Future 4% | ⬛ 0/38 (0%) | SPECOPS×17, MECH_WARRIOR×1 | HELI×22, SPECOPS×31, MECH_WARRIOR×33, SIEGE_TANK×22, SPECOPS×21, SIEGE_TANK×26, SPECOPS×31, SPECOPS×27, THE_GENERAL×999, SPECOPS×28, HELI×24, HELI×26, SIEGE_TANK×22, DRONE×31, SPECOPS×34, SIEGE_TANK×22, SIEGE_TANK×26, SPECOPS×30 |
| 🟥 | Stubborn Raiders | random | Modern 96%, Future 2%, Industrial 1% | ⬛ 0/38 (0%) | SOLDIER×9, SPECOPS×6, THE_GENERAL×1 | SIEGE_TANK×26, SIEGE_TANK×28, HELI×20, SPECOPS×29, SIEGE_TANK×22, THE_GENERAL×999, SIEGE_TANK×32, SPECOPS×22, SIEGE_TANK×34, HELI×24, MECH_WARRIOR×30, HELI×20, SPECOPS×31, HELI×26, SPECOPS×25, HELI×26, SOLDIER×21, HELI×32 |
| 🟥 | Shrieking Horde | random | Modern 98%, Future 2% | ⬛ 0/38 (0%) | SPECOPS×14, SOLDIER×4, HELI×2 | SIEGE_TANK×26, HELI×24, SPECOPS×27, SIEGE_TANK×24, SPECOPS×31, SIEGE_TANK×26, SIEGE_TANK×30, HELI×22, SPECOPS×20, MECH_WARRIOR×27, HELI×20, THE_GENERAL×999, SIEGE_TANK×30, SIEGE_TANK×30, SIEGE_TANK×30, SPECOPS×32, SPECOPS×30, HELI×30 |
| 🟩 | Relentless Mob | random | Modern 96%, Future 2%, Industrial 2% | 🟠 8/38 (21%) | SPECOPS×10, SOLDIER×7, HELI×1 | DRONE×29, HELI×22, HELI×26, SPECOPS×30, SIEGE_TANK×30, HELI×34, MOTORBIKE×28, SPECOPS×30, SIEGE_TANK×24, SPECOPS×20, SPECOPS×27, HELI×26, HELI×26, SPECOPS×28, SPECOPS×25, HELI×22, THE_GENERAL×999, SPECOPS×31, HELI×32 |
| 🟥 | Desperate Looters | random | Modern 92%, Industrial 5%, Future 2% | ⬛ 0/38 (0%) | SPECOPS×11, SOLDIER×5, HELI×4 | DRONE×32, SIEGE_TANK×24, SPECOPS×33, MOTORBIKE×34, MOTORBIKE×25, SIEGE_TANK×26, HELI×22, HELI×30, SIEGE_TANK×26, SIEGE_TANK×30, SPECOPS×33, SPECOPS×31, HELI×30, SIEGE_TANK×32, THE_GENERAL×999, HELI×24, TRANSPORTER×20, SIEGE_TANK×22 |
| 🟥 | Ragged Warband | random | Modern 96%, Future 4% | ⬛ 0/38 (0%) | DRONE×19, SOLDIER×9, SPECOPS×5 | SIEGE_TANK×20, SPECOPS×31, HELI×26, DRONE×28, SIEGE_TANK×28, HELI×34, THE_GENERAL×999, HELI×34, SIEGE_TANK×20, SPECOPS×23, SIEGE_TANK×28, HELI×22, SPECOPS×27, DRONE×32, HELI×34, HELI×34, SIEGE_TANK×24, SIEGE_TANK×34 |
| 🟥 | Shrieking Horde | random | Modern 96%, Future 4% | ⬛ 0/38 (0%) | SPECOPS×13, SOLDIER×3, MECH_WARRIOR×3 | HELI×24, SIEGE_TANK×22, MECH_WARRIOR×33, SPECOPS×27, SPECOPS×24, MECH_WARRIOR×30, HELI×22, THE_GENERAL×999, SPECOPS×31, SIEGE_TANK×30, HELI×24, SIEGE_TANK×28, HELI×28, SIEGE_TANK×24, SIEGE_TANK×32, SIEGE_TANK×32 |
| 🟩 | Relentless Mob | random | Modern 92%, Industrial 6%, Future 2% | 🟠 17/38 (45%) | SPECOPS×10, SOLDIER×1 | SIEGE_TANK×22, SIEGE_TANK×28, SPECOPS×31, SIEGE_TANK×20, SIEGE_TANK×26, HELI×30, THE_GENERAL×999, MOTORBIKE×27, HELI×28, SIEGE_TANK×28, SIEGE_TANK×28, DRONE×30, MOTORBIKE×27, SPECOPS×26, HELI×22, SOLDIER×32 |
| 🟥 | Muddy Marauders | random | Modern 91%, Industrial 7%, Future 2% | ⬛ 0/38 (0%) | SPECOPS×14, SOLDIER×5, HELI×2 | THE_GENERAL×999, SMALL_TANK×24, HELI×26, SIEGE_TANK×32, SOLDIER×27, HELI×22, MOTORBIKE×21, SOLDIER×32, SPECOPS×33, SIEGE_TANK×34, MECH_WARRIOR×30, SPECOPS×25, HELI×28, SIEGE_TANK×30, HELI×30, SIEGE_TANK×28 |
| 🟩 | Howling Savages | random | Modern 90%, Industrial 7%, Future 3% | 🔴 1/38 (3%) | SOLDIER×9, SPECOPS×4, SIEGE_TANK×1, THE_GENERAL×1 | MECH_WARRIOR×27, DRONE×22, SPECOPS×25, SOLDIER×22, THE_GENERAL×999, SIEGE_TANK×34, SPECOPS×30, HELI×22, SPECOPS×26, SOLDIER×27, HELI×22, SOLDIER×21, SIEGE_TANK×24, SPECOPS×33, SIEGE_TANK×22, MOTORBIKE×27, SPECOPS×27, SIEGE_TANK×32 |
| 🟥 | Lazy Raiders | random | Modern 93%, Industrial 4%, Future 3% | ⬛ 0/38 (0%) | SOLDIER×6, SPECOPS×6, MECH_WARRIOR×1, THE_GENERAL×1 | HELI×22, SPECOPS×29, DRONE×22, SMALL_TANK×34, MOTORBIKE×21, HELI×22, SPECOPS×25, SPECOPS×27, SIEGE_TANK×24, HELI×30, HELI×32, THE_GENERAL×999, SPECOPS×28, SPECOPS×32, HELI×28, SIEGE_TANK×28, MECH_WARRIOR×24, SPECOPS×22 |
| 🟥 | Angry Mob | random | Modern 96%, Future 4% | ⬛ 0/38 (0%) | SPECOPS×16, MECH_WARRIOR×2 | SIEGE_TANK×24, SIEGE_TANK×32, MECH_WARRIOR×30, HELI×24, SPECOPS×31, SPECOPS×21, SIEGE_TANK×32, SIEGE_TANK×22, SIEGE_TANK×20, SIEGE_TANK×22, HELI×30, THE_GENERAL×999, HELI×28, SPECOPS×26, DRONE×28, SPECOPS×30, SIEGE_TANK×28 |
| 🟥 | Forgotten Warband | random | Modern 96%, Future 2%, Industrial 2% | ⬛ 0/38 (0%) | SPECOPS×11, DRONE×6, THE_GENERAL×1 | SPECOPS×31, THE_GENERAL×999, SPECOPS×21, SPECOPS×29, SPECOPS×25, DRONE×30, SIEGE_TANK×20, SIEGE_TANK×30, SIEGE_TANK×24, SOLDIER×25, HELI×26, SIEGE_TANK×32, SPECOPS×30, SIEGE_TANK×22, SPECOPS×28, SIEGE_TANK×22, SPECOPS×29, SIEGE_TANK×20 |
| 🟩 | Drunken Raiders | random | Modern 93%, Future 4%, Industrial 4% | 🔴 5/38 (13%) | SPECOPS×16, DRONE×1 | SPECOPS×21, SIEGE_TANK×30, SPECOPS×33, SOLDIER×29, SIEGE_TANK×34, SPECOPS×29, SPECOPS×33, SOLDIER×22, MECH_WARRIOR×24, SPECOPS×23, SIEGE_TANK×24, HELI×20, THE_GENERAL×999, DRONE×33, SPECOPS×33, SIEGE_TANK×24, SIEGE_TANK×30 |
| 🟩 | Hungry Invaders | random | Modern 94%, Industrial 4%, Future 2% | 🟢 35/38 (92%) | SOLDIER×3 | SPECOPS×25, HELI×32, SMALL_TANK×26, SPECOPS×22, HELI×22, SPECOPS×20, SPECOPS×23, SPECOPS×21, HELI×24, SPECOPS×21, THE_GENERAL×999, DRONE×29, HELI×34, SMALL_TANK×28, SPECOPS×21, SPECOPS×20 |
| 🟥 | Lazy Raiders | random | Modern 96%, Future 4% | ⬛ 0/38 (0%) | SOLDIER×13, SPECOPS×11, HELI×1 | THE_GENERAL×999, SPECOPS×20, SIEGE_TANK×20, SPECOPS×31, SIEGE_TANK×26, HELI×28, SIEGE_TANK×34, SPECOPS×25, SPECOPS×26, HELI×22, SPECOPS×27, HELI×22, MECH_WARRIOR×27, HELI×24, HELI×32, MECH_WARRIOR×30, SPECOPS×32, HELI×22 |
| 🟥 | Unlucky Raiders | random | Modern 96%, Future 4% | ⬛ 0/38 (0%) | DRONE×32, SPECOPS×3 | SIEGE_TANK×32, SPECOPS×21, SIEGE_TANK×22, SIEGE_TANK×22, SIEGE_TANK×20, HELI×24, SIEGE_TANK×26, SPECOPS×29, DRONE×34, DRONE×22, HELI×30, SIEGE_TANK×28, SPECOPS×29, THE_GENERAL×999, SPECOPS×26, SPECOPS×30, SIEGE_TANK×30, HELI×24 |
| 🟥 | Bored Mercenaries | random | Modern 91%, Industrial 5%, Future 4% | ⬛ 0/38 (0%) | SPECOPS×9, SOLDIER×7, HELI×2, MECH_WARRIOR×2 | THE_GENERAL×999, SIEGE_TANK×28, TRANSPORTER×20, SIEGE_TANK×32, SPECOPS×22, MECH_WARRIOR×33, SIEGE_TANK×22, HELI×26, HELI×22, HELI×32, MECH_WARRIOR×24, HELI×30, SIEGE_TANK×34, SOLDIER×23, SPECOPS×29, MOTORBIKE×26, SIEGE_TANK×32 |
| 🟥 | Unlucky Raiders | random | Modern 96%, Industrial 2%, Future 2% | ⬛ 0/38 (0%) | SPECOPS×12, SOLDIER×10, HELI×1, DRONE×1 | SPECOPS×23, SPECOPS×21, HELI×32, SIEGE_TANK×28, SIEGE_TANK×34, SPECOPS×26, SPECOPS×27, HELI×24, SPECOPS×32, DRONE×23, SIEGE_TANK×22, SPECOPS×24, SIEGE_TANK×26, THE_GENERAL×999, SIEGE_TANK×32, TRANSPORTER×30 |

### Future

#### S1 Limperium

| Tower Era Distribution (58 towers) | Towers |
|---|---|
| Modern 69% (40), Future 17% (10), Iron Age 14% (8) | MG_TOWER×35, ROCKET_TOWER×10, COLD_TOWER×8, NAPALM_THROWER×5 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Mech Uprising | hardcoded | Future 100% | 🔴 4/48 (8%) | SPECOPS×18, MECH_WARRIOR×2 | MECH_WARRIOR×18, DRONE×18, MECH_WARRIOR×19, MECH_WARRIOR×19, MECH_WARRIOR×20, DRONE×20, MECH_WARRIOR×21, DRONE×21, MECH_WARRIOR×21, DRONE×22, MECH_WARRIOR×22, DRONE×23, MECH_WARRIOR×23, MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×24, DRONE×25, MECH_WARRIOR×25, DRONE×26, DRONE×26, MECH_WARRIOR×27, DRONE×27, DRONE×27, MECH_WARRIOR×28, DRONE×28, MECH_WARRIOR×29, DRONE×29, MECH_WARRIOR×30, DRONE×30 |
| 🟥 | Drone Swarm | hardcoded | Future 100% | ⬛ 0/48 (0%) | SPECOPS×22, MECH_WARRIOR×1 | DRONE×18, MECH_WARRIOR×18, MECH_WARRIOR×19, DRONE×19, DRONE×20, DRONE×20, MECH_WARRIOR×21, MECH_WARRIOR×21, MECH_WARRIOR×22, MECH_WARRIOR×22, DRONE×22, MECH_WARRIOR×23, MECH_WARRIOR×23, DRONE×24, MECH_WARRIOR×24, DRONE×25, MECH_WARRIOR×25, MECH_WARRIOR×26, MECH_WARRIOR×26, DRONE×26, MECH_WARRIOR×27, MECH_WARRIOR×27, MECH_WARRIOR×28, DRONE×28, DRONE×29, DRONE×29, DRONE×30, DRONE×30 |
| 🟩 | Future Shock | hardcoded | Future 100% | 🟡 30/48 (62%) | SPECOPS×9 | MECH_WARRIOR×18, MECH_WARRIOR×18, DRONE×19, DRONE×19, MECH_WARRIOR×20, DRONE×20, MECH_WARRIOR×21, MECH_WARRIOR×21, MECH_WARRIOR×21, DRONE×22, MECH_WARRIOR×22, MECH_WARRIOR×23, DRONE×23, MECH_WARRIOR×24, DRONE×24, DRONE×24, MECH_WARRIOR×25, DRONE×25, MECH_WARRIOR×26, DRONE×26, DRONE×27, MECH_WARRIOR×27, DRONE×27, DRONE×28, DRONE×28, MECH_WARRIOR×29, DRONE×29, MECH_WARRIOR×30 |
| 🟥 | Shrieking Horde | random | Modern 69%, Future 31% | ⬛ 0/48 (0%) | SPECOPS×16, MECH_WARRIOR×4 | DRONE×30, MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×29, DRONE×26, DRONE×28, MECH_WARRIOR×24, DRONE×22, MECH_WARRIOR×33, MECH_WARRIOR×30, DRONE×29, DRONE×31, DRONE×20, THE_GENERAL×999, MECH_WARRIOR×27, DRONE×27, DRONE×23, MECH_WARRIOR×27 |
| 🟥 | Shrieking Horde | random | Modern 69%, Future 31% | ⬛ 0/48 (0%) | SPECOPS×16, MECH_WARRIOR×4 | DRONE×30, MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×29, DRONE×26, DRONE×28, MECH_WARRIOR×24, DRONE×22, MECH_WARRIOR×33, MECH_WARRIOR×30, DRONE×29, DRONE×31, DRONE×20, THE_GENERAL×999, MECH_WARRIOR×27, DRONE×27, DRONE×23, MECH_WARRIOR×27 |
| 🟩 | Rampaging Rabble | random | Modern 67%, Future 33% | 🔴 2/48 (4%) | SPECOPS×15, MECH_WARRIOR×4 | MECH_WARRIOR×21, DRONE×34, THE_GENERAL×999, DRONE×31, DRONE×29, MECH_WARRIOR×27, MECH_WARRIOR×27, DRONE×26, DRONE×34, DRONE×26, DRONE×22, MECH_WARRIOR×33, DRONE×21, MECH_WARRIOR×33, DRONE×20, DRONE×31, DRONE×33, MECH_WARRIOR×21, MECH_WARRIOR×27 |
| 🟥 | Weary Plunderers | random | Modern 67%, Future 33% | ⬛ 0/48 (0%) | SPECOPS×16, MECH_WARRIOR×4 | DRONE×31, DRONE×30, DRONE×32, MECH_WARRIOR×27, MECH_WARRIOR×24, DRONE×23, DRONE×30, MECH_WARRIOR×27, MECH_WARRIOR×24, MECH_WARRIOR×30, MECH_WARRIOR×21, MECH_WARRIOR×27, DRONE×20, THE_GENERAL×999, MECH_WARRIOR×24, DRONE×31, DRONE×27, DRONE×32, DRONE×33 |
| 🟥 | Petty Bandits | random | Future 96%, Modern 4% | ⬛ 0/48 (0%) | SPECOPS×18, MECH_WARRIOR×3 | MECH_WARRIOR×21, MECH_WARRIOR×27, DRONE×31, MECH_WARRIOR×21, DRONE×27, MECH_WARRIOR×30, MECH_WARRIOR×33, DRONE×31, DRONE×30, DRONE×26, MECH_WARRIOR×24, MECH_WARRIOR×30, DRONE×23, MECH_WARRIOR×27, DRONE×25, MECH_WARRIOR×30, MECH_WARRIOR×27, MECH_WARRIOR×24, DRONE×25, HELI×22 |
| 🟩 | Relentless Mob | random | Modern 70%, Future 30% | 🔴 6/48 (12%) | SPECOPS×13, MECH_WARRIOR×4 | MECH_WARRIOR×24, DRONE×31, DRONE×24, SPECOPS×23, MECH_WARRIOR×30, DRONE×26, DRONE×31, MECH_WARRIOR×24, DRONE×32, MECH_WARRIOR×21, DRONE×32, THE_GENERAL×999, MECH_WARRIOR×30, MECH_WARRIOR×24, HELI×32, DRONE×32, DRONE×26, DRONE×26, DRONE×31 |
| 🟥 | Rowdy Plunderers | random | Future 94%, Modern 6% | ⬛ 0/48 (0%) | SPECOPS×14, SOLDIER×8, DRONE×5, MECH_WARRIOR×2 | MECH_WARRIOR×30, DRONE×26, DRONE×26, MECH_WARRIOR×30, DRONE×20, DRONE×28, DRONE×20, MECH_WARRIOR×27, MECH_WARRIOR×33, MECH_WARRIOR×33, MECH_WARRIOR×24, HELI×28, DRONE×33, DRONE×34, MECH_WARRIOR×33, MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×23 |
| 🟥 | Noisy Barbarians | random | Future 92%, Modern 8% | ⬛ 0/48 (0%) | SPECOPS×24 | DRONE×28, MECH_WARRIOR×24, DRONE×31, MECH_WARRIOR×21, MECH_WARRIOR×24, DRONE×24, DRONE×22, MECH_WARRIOR×27, MECH_WARRIOR×24, DRONE×26, MECH_WARRIOR×27, MECH_WARRIOR×24, DRONE×28, MECH_WARRIOR×24, HELI×30 |
| 🟩 | Lazy Raiders | random | Modern 75%, Future 25% | 🟡 24/48 (50%) | SPECOPS×6, MECH_WARRIOR×3 | DRONE×31, DRONE×28, THE_GENERAL×999, DRONE×27, MECH_WARRIOR×24, MECH_WARRIOR×27, DRONE×31, DRONE×27, DRONE×22, HELI×22, DRONE×22, MECH_WARRIOR×30, DRONE×25, MECH_WARRIOR×21, DRONE×28 |
| 🟥 | Crude Invaders | random | Future 81%, Modern 19% | ⬛ 0/48 (0%) | SPECOPS×16, MECH_WARRIOR×4 | MECH_WARRIOR×30, HELI×26, MECH_WARRIOR×24, DRONE×29, MECH_WARRIOR×21, SIEGE_TANK×32, DRONE×20, HELI×22, MECH_WARRIOR×24, DRONE×32, MECH_WARRIOR×30, MECH_WARRIOR×30, MECH_WARRIOR×33, MECH_WARRIOR×24, DRONE×28, MECH_WARRIOR×24 |
| 🟥 | Crude Invaders | random | Future 83%, Modern 17% | ⬛ 0/48 (0%) | SPECOPS×9, MECH_WARRIOR×5, SIEGE_TANK×4, DRONE×3 | DRONE×25, DRONE×23, SPECOPS×26, SIEGE_TANK×22, SIEGE_TANK×30, MECH_WARRIOR×27, DRONE×25, DRONE×24, DRONE×26, DRONE×23, MECH_WARRIOR×33, MECH_WARRIOR×27, MECH_WARRIOR×33, MECH_WARRIOR×21, MECH_WARRIOR×24, DRONE×20, MECH_WARRIOR×21, DRONE×25 |
| 🟥 | Petty Bandits | random | Future 88%, Modern 12% | ⬛ 0/48 (0%) | SPECOPS×11, MECH_WARRIOR×7 | MECH_WARRIOR×24, DRONE×26, DRONE×22, SPECOPS×28, SIEGE_TANK×30, DRONE×27, MECH_WARRIOR×21, DRONE×28, MECH_WARRIOR×27, DRONE×28, MECH_WARRIOR×24, MECH_WARRIOR×33, MECH_WARRIOR×30, MECH_WARRIOR×30, MECH_WARRIOR×24, MECH_WARRIOR×30, DRONE×31, MECH_WARRIOR×27 |
| 🟥 | Bored Mercenaries | random | Future 94%, Modern 6% | ⬛ 0/48 (0%) | SPECOPS×16, MECH_WARRIOR×4 | MECH_WARRIOR×33, MECH_WARRIOR×27, HELI×24, MECH_WARRIOR×27, DRONE×25, DRONE×26, DRONE×23, MECH_WARRIOR×24, DRONE×24, MECH_WARRIOR×21, DRONE×30, MECH_WARRIOR×24, DRONE×28, MECH_WARRIOR×21, MECH_WARRIOR×30, DRONE×24 |
| 🟩 | Wandering Pillagers | random | Future 90%, Modern 10% | 🟡 28/48 (58%) | SPECOPS×10 | DRONE×28, MECH_WARRIOR×24, DRONE×20, DRONE×21, MECH_WARRIOR×21, DRONE×20, MECH_WARRIOR×27, MECH_WARRIOR×24, HELI×20, DRONE×24, DRONE×31, MECH_WARRIOR×24, DRONE×28, SPECOPS×24, DRONE×28, MECH_WARRIOR×30, DRONE×21, MECH_WARRIOR×24 |
| 🟩 | Drunken Raiders | random | Modern 73%, Future 27% | 🔴 4/48 (8%) | SPECOPS×16, MECH_WARRIOR×3 | DRONE×31, MECH_WARRIOR×24, MECH_WARRIOR×30, MECH_WARRIOR×24, DRONE×33, DRONE×29, MECH_WARRIOR×21, DRONE×28, SPECOPS×21, DRONE×23, DRONE×26, DRONE×22, MECH_WARRIOR×24, THE_GENERAL×999, MECH_WARRIOR×24, DRONE×21, MECH_WARRIOR×24 |
| 🟩 | Howling Savages | random | Future 88%, Modern 12% | 🟡 32/48 (67%) | SPECOPS×8 | DRONE×27, DRONE×20, DRONE×25, HELI×20, DRONE×28, DRONE×29, MECH_WARRIOR×24, DRONE×23, MECH_WARRIOR×33, DRONE×26, DRONE×22, MECH_WARRIOR×24, DRONE×31, MECH_WARRIOR×33, HELI×30, DRONE×21 |
| 🟩 | Clumsy Attackers | random | Future 94%, Modern 6% | 🔴 7/48 (15%) | SPECOPS×14, MECH_WARRIOR×3, DRONE×1 | DRONE×28, DRONE×24, DRONE×28, DRONE×29, MECH_WARRIOR×27, MECH_WARRIOR×24, DRONE×33, MECH_WARRIOR×30, DRONE×25, DRONE×33, DRONE×30, MECH_WARRIOR×21, MECH_WARRIOR×24, HELI×32, MECH_WARRIOR×27, DRONE×32, MECH_WARRIOR×30, DRONE×32 |
| 🟩 | Blundering Invaders | random | Future 95%, Modern 5% | 🟡 24/48 (50%) | SPECOPS×10, MECH_WARRIOR×1 | DRONE×30, MECH_WARRIOR×24, MECH_WARRIOR×21, DRONE×29, SIEGE_TANK×26, DRONE×21, DRONE×21, MECH_WARRIOR×27, DRONE×29, MECH_WARRIOR×27, DRONE×32, MECH_WARRIOR×24, DRONE×23, DRONE×23, MECH_WARRIOR×24, MECH_WARRIOR×30, DRONE×26, MECH_WARRIOR×24, MECH_WARRIOR×27 |
| 🟥 | Bored Mercenaries | random | Modern 72%, Future 28% | ⬛ 0/48 (0%) | SPECOPS×18, DRONE×8, MECH_WARRIOR×1 | MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×24, DRONE×31, DRONE×22, THE_GENERAL×999, DRONE×22, MECH_WARRIOR×24, MECH_WARRIOR×24, MECH_WARRIOR×33, SIEGE_TANK×32, MECH_WARRIOR×30, DRONE×33, DRONE×31, DRONE×29, DRONE×34, MECH_WARRIOR×24 |
| 🟥 | Frenzied Pillagers | random | Future 94%, Modern 6% | ⬛ 0/48 (0%) | SPECOPS×16, MECH_WARRIOR×4 | DRONE×28, DRONE×22, MECH_WARRIOR×33, MECH_WARRIOR×30, DRONE×28, DRONE×29, MECH_WARRIOR×27, DRONE×29, MECH_WARRIOR×27, DRONE×21, SPECOPS×22, MECH_WARRIOR×33, DRONE×22, MECH_WARRIOR×24, MECH_WARRIOR×21 |

## Flagged Critters/Towers

### Stone Age
- **Critters UP (rarely reach the castle):** SLAVE (reach_rate=0.2%, era_mean=13.1%)

### Neolithic
- **Towers UP (damage share far below placement share):** SPIKE_TRAP (damage_share=6.4% vs placement_share=25.0%, ratio=0.25)

### Bronze Age
- **Towers OP (damage share far above placement share):** ARROW_TOWER (damage_share=72.0% vs placement_share=33.3%, ratio=2.16)
- **Towers UP (damage share far below placement share):** FIRE_TOWER (damage_share=14.5% vs placement_share=33.3%, ratio=0.44); SPIKE_TRAP (damage_share=1.6% vs placement_share=16.7%, ratio=0.10)

### Iron Age
- **Critters OP (reach rate far above era mean):** THE_SWORDMASTER (reach_rate=27.2%, era_mean=5.8%)
- **Critters UP (rarely reach the castle):** LARGE_CART (reach_rate=0.0%, era_mean=5.8%)

### Medieval
- **Critters OP (reach rate far above era mean):** HANDGUNNER (reach_rate=9.7%, era_mean=3.5%)
- **Critters UP (rarely reach the castle):** SIEGE_RAM (reach_rate=0.4%, era_mean=3.5%)
- **Towers OP (damage share far above placement share):** HEAVY_TOWER (damage_share=38.5% vs placement_share=19.2%, ratio=2.00); CANNON_TOWER (damage_share=18.6% vs placement_share=3.8%, ratio=4.83)
- **Towers UP (damage share far below placement share):** TAR_TOWER (damage_share=9.2% vs placement_share=19.2%, ratio=0.48); FIRE_TOWER (damage_share=0.4% vs placement_share=7.7%, ratio=0.06); BALLISTA_TOWER (damage_share=0.6% vs placement_share=7.7%, ratio=0.08); CATAPULTS (damage_share=1.0% vs placement_share=7.7%, ratio=0.13); DOUBLE_SLING_TOWER (damage_share=0.3% vs placement_share=3.8%, ratio=0.08); ARROW_TOWER (damage_share=0.3% vs placement_share=3.8%, ratio=0.08)

### Renaissance
- **Critters UP (rarely reach the castle):** NINJA (reach_rate=0.2%, era_mean=7.0%); CARGO (reach_rate=0.3%, era_mean=7.0%)
- **Towers OP (damage share far above placement share):** RIFLE_TOWER (damage_share=61.4% vs placement_share=25.0%, ratio=2.46); HEAVY_TOWER (damage_share=26.7% vs placement_share=12.5%, ratio=2.14)
- **Towers UP (damage share far below placement share):** CANNON_TOWER (damage_share=5.4% vs placement_share=12.5%, ratio=0.43); ICE_TOWER (damage_share=5.2% vs placement_share=25.0%, ratio=0.21); COLD_TOWER (damage_share=0.3% vs placement_share=12.5%, ratio=0.02); TAR_TOWER (damage_share=0.9% vs placement_share=12.5%, ratio=0.07)

### Industrial
- **Towers OP (damage share far above placement share):** FLAME_THROWER (damage_share=50.4% vs placement_share=22.2%, ratio=2.27)
- **Towers UP (damage share far below placement share):** COLD_TOWER (damage_share=0.4% vs placement_share=22.2%, ratio=0.02); ICE_TOWER (damage_share=1.5% vs placement_share=16.7%, ratio=0.09); SHOCK_TOWER (damage_share=2.4% vs placement_share=11.1%, ratio=0.22)

### Modern
- **Towers OP (damage share far above placement share):** FLAME_THROWER (damage_share=47.4% vs placement_share=12.5%, ratio=3.79)
- **Towers UP (damage share far below placement share):** COLD_TOWER (damage_share=0.8% vs placement_share=12.5%, ratio=0.06); ICE_TOWER (damage_share=0.2% vs placement_share=12.5%, ratio=0.01); SHOCK_TOWER (damage_share=0.7% vs placement_share=8.3%, ratio=0.09); PARALYZNG_TOWER (damage_share=0.4% vs placement_share=4.2%, ratio=0.09)

### Future
- **Critters UP (rarely reach the castle):** DRONE (reach_rate=0.2%, era_mean=2.2%)
- **Towers OP (damage share far above placement share):** MG_TOWER (damage_share=70.8% vs placement_share=25.0%, ratio=2.83)
- **Towers UP (damage share far below placement share):** ROCKET_TOWER (damage_share=6.3% vs placement_share=25.0%, ratio=0.25); COLD_TOWER (damage_share=0.7% vs placement_share=25.0%, ratio=0.03)
