# Balancing Report

Generated: 2026-08-21T11:25:41.683846+00:00

## Maze Coverage

```
Era             Mazes  Source(s)               Towers (min-max)    
-------------------------------------------------------------------
stone               6  saved                   1-3
neolithic           2  saved                   4-10
bronze              4  saved                   6-29
iron                5  saved                   13-33
medieval            5  saved                   18-41
renaissance         4  saved                   32-45
industrial          4  saved                   28-61
modern              2  saved                   51-62
future              3  saved                   33-66
```

## Win Rates

| Era | Battles | Defender Win % | Hardcoded Win % | Random Win % |
|---|---:|---:|---:|---:|
| Stone Age | 138 | 95% | 83% | 97% |
| Neolithic | 48 | 54% | 88% | 48% |
| Bronze Age | 96 | 66% | 56% | 68% |
| Iron Age | 125 | 64% | 60% | 65% |
| Medieval | 130 | 61% | 60% | 61% |
| Renaissance | 96 | 65% | 50% | 68% |
| Industrial | 100 | 79% | 75% | 80% |
| Modern | 52 | 50% | 58% | 48% |
| Future | 69 | 14% | 11% | 15% |

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
| 🟩 | Disorganized Mob | random | Stone Age 70%, Neolithic 30% | 🟡 6/10 (60%) | CART×2 | SLAVE×6, SCOUT×8, CART×6 |
| 🟩 | Disorganized Mob | random | Stone Age 70%, Neolithic 30% | 🟡 6/10 (60%) | CART×2 | SLAVE×6, SCOUT×8, CART×6 |
| 🟩 | Savage Rabble | random | Stone Age 100% | 🟢 8/10 (80%) | CLUBMAN×2 | SLAVE×7, CLUBMAN×8, CLUBMAN×6, CLUBMAN×8 |
| 🟩 | Blundering Invaders | random | Stone Age 100% | 🟢 10/10 (100%) |  | CLUBMAN×6, CLUBMAN×4, SLAVE×5, SLAVE×7 |
| 🟩 | Frenzied Pillagers | random | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×5, SCOUT×7, SCOUT×6, CLUBMAN×4 |
| 🟩 | Petty Bandits | random | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×7, CLUBMAN×4, CLUBMAN×6, CLUBMAN×8 |
| 🟩 | Drunken Raiders | random | Stone Age 53%, Neolithic 47% | 🟠 4/10 (40%) | CART×3 | CART×9, SLAVE×4, SLAVE×6 |
| 🟥 | Crude Invaders | random | Neolithic 50%, Stone Age 50% | ⬛ 0/10 (0%) | WARRIOR×6, SCOUT×4 | WARRIOR×6, SCOUT×6 |
| 🟩 | Frenzied Pillagers | random | Stone Age 100% | 🟡 6/10 (60%) | SCOUT×4 | CLUBMAN×8, SCOUT×6 |
| 🟩 | Wandering Pillagers | random | Stone Age 100% | 🟢 10/10 (100%) |  | SCOUT×7, SCOUT×5 |
| 🟩 | Wandering Pillagers | random | Stone Age 71%, Neolithic 29% | 🟡 6/10 (60%) | WARRIOR×4 | SCOUT×6, CLUBMAN×4, WARRIOR×4 |
| 🟩 | Rampaging Rabble | random | Stone Age 67%, Neolithic 33% | 🟡 6/10 (60%) | CART×2 | CART×6, CLUBMAN×8, CLUBMAN×4 |
| 🟩 | Crude Invaders | random | Neolithic 58%, Stone Age 42% | 🟠 3/10 (30%) | WARRIOR×7 | SCOUT×5, WARRIOR×7 |
| 🟩 | Forgotten Warband | random | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×4, SLAVE×4, CLUBMAN×6 |
| 🟩 | Lazy Raiders | random | Stone Age 56%, Neolithic 44% | 🟠 2/10 (20%) | WARRIOR×8 | CLUBMAN×6, CLUBMAN×4, WARRIOR×8 |
| 🟩 | Lazy Raiders | random | Stone Age 100% | 🟢 10/10 (100%) |  | CLUBMAN×8, CLUBMAN×4 |
| 🟩 | Rude Barbarians | random | Stone Age 70%, Neolithic 30% | 🟡 6/10 (60%) | CART×2 | SLAVE×8, CLUBMAN×6, CART×6 |
| 🟩 | Muddy Marauders | random | Stone Age 71%, Neolithic 29% | 🟡 6/10 (60%) | CART×2 | CART×6, CLUBMAN×6, SLAVE×4, SCOUT×5 |
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
| 🟩 | Disorganized Mob | random | Stone Age 70%, Neolithic 30% | 🟡 6/10 (60%) | CART×2 | SLAVE×6, SCOUT×8, CART×6 |
| 🟩 | Disorganized Mob | random | Stone Age 70%, Neolithic 30% | 🟡 6/10 (60%) | CART×2 | SLAVE×6, SCOUT×8, CART×6 |
| 🟩 | Savage Rabble | random | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×7, CLUBMAN×8, CLUBMAN×6, CLUBMAN×8 |
| 🟩 | Blundering Invaders | random | Stone Age 100% | 🟢 10/10 (100%) |  | CLUBMAN×6, CLUBMAN×4, SLAVE×5, SLAVE×7 |
| 🟩 | Frenzied Pillagers | random | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×5, SCOUT×7, SCOUT×6, CLUBMAN×4 |
| 🟩 | Petty Bandits | random | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×7, CLUBMAN×4, CLUBMAN×6, CLUBMAN×8 |
| 🟩 | Drunken Raiders | random | Stone Age 53%, Neolithic 47% | 🟠 3/10 (30%) | CLUBMAN×3, CART×2 | CART×9, SLAVE×4, SLAVE×6 |
| 🟩 | Crude Invaders | random | Neolithic 50%, Stone Age 50% | 🟠 2/10 (20%) | WARRIOR×5, SCOUT×3 | WARRIOR×6, SCOUT×6 |
| 🟩 | Frenzied Pillagers | random | Stone Age 100% | 🟢 10/10 (100%) |  | CLUBMAN×8, SCOUT×6 |
| 🟩 | Wandering Pillagers | random | Stone Age 100% | 🟢 10/10 (100%) |  | SCOUT×7, SCOUT×5 |
| 🟩 | Wandering Pillagers | random | Stone Age 71%, Neolithic 29% | 🟡 7/10 (70%) | WARRIOR×3 | SCOUT×6, CLUBMAN×4, WARRIOR×4 |
| 🟩 | Rampaging Rabble | random | Stone Age 67%, Neolithic 33% | 🟡 5/10 (50%) | CLUBMAN×3, CART×1 | CART×6, CLUBMAN×8, CLUBMAN×4 |
| 🟩 | Crude Invaders | random | Neolithic 58%, Stone Age 42% | 🟠 4/10 (40%) | WARRIOR×6 | SCOUT×5, WARRIOR×7 |
| 🟩 | Forgotten Warband | random | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×4, SLAVE×4, CLUBMAN×6 |
| 🟩 | Lazy Raiders | random | Stone Age 56%, Neolithic 44% | 🟠 3/10 (30%) | WARRIOR×7 | CLUBMAN×6, CLUBMAN×4, WARRIOR×8 |
| 🟩 | Lazy Raiders | random | Stone Age 100% | 🟢 10/10 (100%) |  | CLUBMAN×8, CLUBMAN×4 |
| 🟩 | Rude Barbarians | random | Stone Age 70%, Neolithic 30% | 🟡 5/10 (50%) | CLUBMAN×3, CART×1 | SLAVE×8, CLUBMAN×6, CART×6 |
| 🟩 | Muddy Marauders | random | Stone Age 71%, Neolithic 29% | 🟡 5/10 (50%) | CLUBMAN×3, CART×1 | CART×6, CLUBMAN×6, SLAVE×4, SCOUT×5 |
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
| 🟩 | Disorganized Mob | random | Stone Age 70%, Neolithic 30% | 🟡 6/10 (60%) | CART×2 | SLAVE×6, SCOUT×8, CART×6 |
| 🟩 | Disorganized Mob | random | Stone Age 70%, Neolithic 30% | 🟡 6/10 (60%) | CART×2 | SLAVE×6, SCOUT×8, CART×6 |
| 🟩 | Savage Rabble | random | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×7, CLUBMAN×8, CLUBMAN×6, CLUBMAN×8 |
| 🟩 | Blundering Invaders | random | Stone Age 100% | 🟢 10/10 (100%) |  | CLUBMAN×6, CLUBMAN×4, SLAVE×5, SLAVE×7 |
| 🟩 | Frenzied Pillagers | random | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×5, SCOUT×7, SCOUT×6, CLUBMAN×4 |
| 🟩 | Petty Bandits | random | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×7, CLUBMAN×4, CLUBMAN×6, CLUBMAN×8 |
| 🟩 | Drunken Raiders | random | Stone Age 53%, Neolithic 47% | 🟠 4/10 (40%) | CART×3 | CART×9, SLAVE×4, SLAVE×6 |
| 🟩 | Crude Invaders | random | Neolithic 50%, Stone Age 50% | 🟠 4/10 (40%) | WARRIOR×6 | WARRIOR×6, SCOUT×6 |
| 🟩 | Frenzied Pillagers | random | Stone Age 100% | 🟢 10/10 (100%) |  | CLUBMAN×8, SCOUT×6 |
| 🟩 | Wandering Pillagers | random | Stone Age 100% | 🟢 10/10 (100%) |  | SCOUT×7, SCOUT×5 |
| 🟩 | Wandering Pillagers | random | Stone Age 71%, Neolithic 29% | 🟡 6/10 (60%) | WARRIOR×4 | SCOUT×6, CLUBMAN×4, WARRIOR×4 |
| 🟩 | Rampaging Rabble | random | Stone Age 67%, Neolithic 33% | 🟡 6/10 (60%) | CART×2 | CART×6, CLUBMAN×8, CLUBMAN×4 |
| 🟩 | Crude Invaders | random | Neolithic 58%, Stone Age 42% | 🟠 3/10 (30%) | WARRIOR×7 | SCOUT×5, WARRIOR×7 |
| 🟩 | Forgotten Warband | random | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×4, SLAVE×4, CLUBMAN×6 |
| 🟩 | Lazy Raiders | random | Stone Age 56%, Neolithic 44% | 🟠 2/10 (20%) | WARRIOR×8 | CLUBMAN×6, CLUBMAN×4, WARRIOR×8 |
| 🟩 | Lazy Raiders | random | Stone Age 100% | 🟢 10/10 (100%) |  | CLUBMAN×8, CLUBMAN×4 |
| 🟩 | Rude Barbarians | random | Stone Age 70%, Neolithic 30% | 🟠 3/10 (30%) | CLUBMAN×3, CART×2 | SLAVE×8, CLUBMAN×6, CART×6 |
| 🟩 | Muddy Marauders | random | Stone Age 71%, Neolithic 29% | 🟡 6/10 (60%) | CART×2 | CART×6, CLUBMAN×6, SLAVE×4, SCOUT×5 |
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
| 🟩 | Disorganized Mob | random | Stone Age 70%, Neolithic 30% | 🟡 6/10 (60%) | CLUBMAN×4 | SLAVE×6, SCOUT×8, CART×6 |
| 🟩 | Disorganized Mob | random | Stone Age 70%, Neolithic 30% | 🟡 6/10 (60%) | CLUBMAN×4 | SLAVE×6, SCOUT×8, CART×6 |
| 🟩 | Savage Rabble | random | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×7, CLUBMAN×8, CLUBMAN×6, CLUBMAN×8 |
| 🟩 | Blundering Invaders | random | Stone Age 100% | 🟢 10/10 (100%) |  | CLUBMAN×6, CLUBMAN×4, SLAVE×5, SLAVE×7 |
| 🟩 | Frenzied Pillagers | random | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×5, SCOUT×7, SCOUT×6, CLUBMAN×4 |
| 🟩 | Petty Bandits | random | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×7, CLUBMAN×4, CLUBMAN×6, CLUBMAN×8 |
| 🟥 | Drunken Raiders | random | Stone Age 53%, Neolithic 47% | ⬛ 0/10 (0%) | CLUBMAN×10 | CART×9, SLAVE×4, SLAVE×6 |
| 🟩 | Crude Invaders | random | Neolithic 50%, Stone Age 50% | 🟢 9/10 (90%) | WARRIOR×1 | WARRIOR×6, SCOUT×6 |
| 🟩 | Frenzied Pillagers | random | Stone Age 100% | 🟢 10/10 (100%) |  | CLUBMAN×8, SCOUT×6 |
| 🟩 | Wandering Pillagers | random | Stone Age 100% | 🟢 10/10 (100%) |  | SCOUT×7, SCOUT×5 |
| 🟩 | Wandering Pillagers | random | Stone Age 71%, Neolithic 29% | 🟢 10/10 (100%) |  | SCOUT×6, CLUBMAN×4, WARRIOR×4 |
| 🟩 | Rampaging Rabble | random | Stone Age 67%, Neolithic 33% | 🟡 7/10 (70%) | CLUBMAN×3 | CART×6, CLUBMAN×8, CLUBMAN×4 |
| 🟩 | Crude Invaders | random | Neolithic 58%, Stone Age 42% | 🟢 9/10 (90%) | WARRIOR×1 | SCOUT×5, WARRIOR×7 |
| 🟩 | Forgotten Warband | random | Stone Age 100% | 🟢 10/10 (100%) |  | SLAVE×4, SLAVE×4, CLUBMAN×6 |
| 🟩 | Lazy Raiders | random | Stone Age 56%, Neolithic 44% | 🟢 8/10 (80%) | WARRIOR×2 | CLUBMAN×6, CLUBMAN×4, WARRIOR×8 |
| 🟩 | Lazy Raiders | random | Stone Age 100% | 🟢 10/10 (100%) |  | CLUBMAN×8, CLUBMAN×4 |
| 🟩 | Rude Barbarians | random | Stone Age 70%, Neolithic 30% | 🟡 7/10 (70%) | CLUBMAN×3 | SLAVE×8, CLUBMAN×6, CART×6 |
| 🟩 | Muddy Marauders | random | Stone Age 71%, Neolithic 29% | 🟡 7/10 (70%) | CLUBMAN×3 | CART×6, CLUBMAN×6, SLAVE×4, SCOUT×5 |
| 🟩 | Frenzied Pillagers | random | Stone Age 72%, Neolithic 28% | 🟢 10/10 (100%) |  | WARRIOR×5, SLAVE×7, CLUBMAN×6 |
| 🟩 | Frenzied Pillagers | random | Stone Age 100% | 🟢 10/10 (100%) |  | SCOUT×8, SLAVE×7 |

### Neolithic

#### Neolith

| Tower Era Distribution (4 towers) | Towers |
|---|---|
| Stone Age 75% (3), Neolithic 25% (1) | BASIC_TOWER×3, DOUBLE_SLING_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Neolithic Horde | hardcoded | Neolithic 100% | 🔴 1/10 (10%) | WARRIOR×5, CLUBMAN×2, CART×1 | CART×6, WARRIOR×4, WARRIOR×6, CART×6 |
| 🟩 | Tribal Warband | hardcoded | Neolithic 100% | 🟢 8/10 (80%) | WARRIOR×2 | CART×3, WARRIOR×2, CART×5, WARRIOR×6, WARRIOR×5 |
| 🟩 | Harvest Raiders | hardcoded | Neolithic 95%, Bronze Age 5% | 🟢 8/10 (80%) | BOWMAN×1 | CART×5, WARRIOR×4, CART×5, BOWMAN×1, WARRIOR×6 |
| 🟥 | Pottery Thieves | hardcoded | Neolithic 100% | ⬛ 0/10 (0%) | WARRIOR×4, CART×3 | WARRIOR×8, WARRIOR×8, CART×9, WARRIOR×12, WARRIOR×8 |
| 🟥 | Rowdy Plunderers | random | Neolithic 77%, Bronze Age 23% | ⬛ 0/10 (0%) | CHARIOT×7, CLUBMAN×3 | CHARIOT×7, CART×6, CART×9, WARRIOR×8 |
| 🟥 | Rowdy Plunderers | random | Neolithic 77%, Bronze Age 23% | ⬛ 0/10 (0%) | CHARIOT×7, CLUBMAN×3 | CHARIOT×7, CART×6, CART×9, WARRIOR×8 |
| 🟥 | Savage Rabble | random | Neolithic 100% | ⬛ 0/10 (0%) | WARRIOR×6, CART×2 | WARRIOR×9, WARRIOR×9, CART×6, CART×9 |
| 🟥 | Blundering Invaders | random | Neolithic 100% | ⬛ 0/10 (0%) | WARRIOR×6, CLUBMAN×4 | WARRIOR×7, CART×6, WARRIOR×6, WARRIOR×9 |
| 🟥 | Frenzied Pillagers | random | Neolithic 100% | ⬛ 0/10 (0%) | CLUBMAN×9, WARRIOR×1 | WARRIOR×6, CART×9, CART×9, CART×6 |
| 🟥 | Petty Bandits | random | Neolithic 74%, Stone Age 26% | ⬛ 0/10 (0%) | CLUBMAN×9, WARRIOR×1 | SLAVE×9, CART×6, CART×9, WARRIOR×10 |
| 🟥 | Petty Bandits | random | Neolithic 69%, Bronze Age 31% | ⬛ 0/10 (0%) | BOWMAN×5 | BOWMAN×10, CART×9, WARRIOR×8, WARRIOR×5 |
| 🟥 | Grumpy Marauders | random | Neolithic 67%, Bronze Age 33% | ⬛ 0/10 (0%) | CLUBMAN×7, WARRIOR×1, BOWMAN×1 | WARRIOR×7, CART×9, BOWMAN×8 |
| 🟥 | Angry Mob | random | Neolithic 69%, Stone Age 31% | ⬛ 0/10 (0%) | CLUBMAN×5, WARRIOR×3, CART×1 | SLAVE×8, WARRIOR×9, CART×9 |
| 🟩 | Savage Rabble | random | Neolithic 71%, Stone Age 29% | 🟢 10/10 (100%) |  | CART×9, SCOUT×6, CART×6 |
| 🟥 | Petty Bandits | random | Neolithic 44%, Bronze Age 37%, Stone Age 19% | ⬛ 0/10 (0%) | CHARIOT×10 | SLAVE×5, CHARIOT×10, WARRIOR×6, CART×6 |
| 🟩 | Shrieking Horde | random | Neolithic 48%, Stone Age 26%, Bronze Age 26% | 🟠 2/10 (20%) | SWORDMAN×4 | CART×9, CLUBMAN×8, CART×6, SWORDMAN×8 |
| 🟥 | Unlucky Raiders | random | Neolithic 64%, Bronze Age 36% | ⬛ 0/10 (0%) | WARRIOR×5, CLUBMAN×4, SWORDMAN×1 | WARRIOR×8, CART×6, SWORDMAN×8 |
| 🟥 | Crude Invaders | random | Neolithic 100% | ⬛ 0/10 (0%) | WARRIOR×6, CART×2 | WARRIOR×5, WARRIOR×8, WARRIOR×5, CART×9 |
| 🟥 | Lazy Raiders | random | Neolithic 58%, Bronze Age 42% | ⬛ 0/10 (0%) | BOWMAN×5, WARRIOR×1 | WARRIOR×8, WARRIOR×6, BOWMAN×10 |
| 🟥 | Ragged Warband | random | Neolithic 100% | ⬛ 0/10 (0%) | WARRIOR×5, CART×2, CLUBMAN×1 | WARRIOR×5, WARRIOR×6, CART×9 |
| 🟥 | Savage Rabble | random | Neolithic 77%, Bronze Age 23% | ⬛ 0/10 (0%) | CHARIOT×7, CLUBMAN×3 | WARRIOR×10, CART×6, CHARIOT×7, WARRIOR×7 |
| 🟥 | Muddy Marauders | random | Neolithic 65%, Bronze Age 35% | ⬛ 0/10 (0%) | CHARIOT×9, WARRIOR×1 | CHARIOT×9, CART×6, WARRIOR×5, CART×6 |
| 🟥 | Frenzied Pillagers | random | Neolithic 39%, Stone Age 35%, Bronze Age 26% | ⬛ 0/10 (0%) | BOWMAN×5 | BOWMAN×6, WARRIOR×9, CLUBMAN×8 |
| 🟥 | Disorganized Mob | random | Neolithic 100% | ⬛ 0/10 (0%) | CLUBMAN×9, WARRIOR×1 | WARRIOR×8, CART×9, CART×9 |

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
| 🟩 | Rowdy Plunderers | random | Neolithic 77%, Bronze Age 23% | 🟢 8/10 (80%) | CHARIOT×2 | CHARIOT×7, CART×6, CART×9, WARRIOR×8 |
| 🟩 | Rowdy Plunderers | random | Neolithic 77%, Bronze Age 23% | 🟢 8/10 (80%) | CHARIOT×2 | CHARIOT×7, CART×6, CART×9, WARRIOR×8 |
| 🟩 | Savage Rabble | random | Neolithic 100% | 🟢 10/10 (100%) |  | WARRIOR×9, WARRIOR×9, CART×6, CART×9 |
| 🟩 | Blundering Invaders | random | Neolithic 100% | 🟢 10/10 (100%) |  | WARRIOR×7, CART×6, WARRIOR×6, WARRIOR×9 |
| 🟩 | Frenzied Pillagers | random | Neolithic 100% | 🟢 10/10 (100%) |  | WARRIOR×6, CART×9, CART×9, CART×6 |
| 🟩 | Petty Bandits | random | Neolithic 74%, Stone Age 26% | 🟢 10/10 (100%) |  | SLAVE×9, CART×6, CART×9, WARRIOR×10 |
| 🟥 | Petty Bandits | random | Neolithic 69%, Bronze Age 31% | ⬛ 0/10 (0%) | BOWMAN×5 | BOWMAN×10, CART×9, WARRIOR×8, WARRIOR×5 |
| 🟥 | Grumpy Marauders | random | Neolithic 67%, Bronze Age 33% | ⬛ 0/10 (0%) | BOWMAN×5 | WARRIOR×7, CART×9, BOWMAN×8 |
| 🟩 | Angry Mob | random | Neolithic 69%, Stone Age 31% | 🟢 10/10 (100%) |  | SLAVE×8, WARRIOR×9, CART×9 |
| 🟩 | Savage Rabble | random | Neolithic 71%, Stone Age 29% | 🟢 10/10 (100%) |  | CART×9, SCOUT×6, CART×6 |
| 🟩 | Petty Bandits | random | Neolithic 44%, Bronze Age 37%, Stone Age 19% | 🟡 6/10 (60%) | CHARIOT×4 | SLAVE×5, CHARIOT×10, WARRIOR×6, CART×6 |
| 🟩 | Shrieking Horde | random | Neolithic 48%, Stone Age 26%, Bronze Age 26% | 🟢 8/10 (80%) | SWORDMAN×1 | CART×9, CLUBMAN×8, CART×6, SWORDMAN×8 |
| 🟩 | Unlucky Raiders | random | Neolithic 64%, Bronze Age 36% | 🟡 6/10 (60%) | SWORDMAN×2 | WARRIOR×8, CART×6, SWORDMAN×8 |
| 🟩 | Crude Invaders | random | Neolithic 100% | 🟢 10/10 (100%) |  | WARRIOR×5, WARRIOR×8, WARRIOR×5, CART×9 |
| 🟥 | Lazy Raiders | random | Neolithic 58%, Bronze Age 42% | ⬛ 0/10 (0%) | BOWMAN×5 | WARRIOR×8, WARRIOR×6, BOWMAN×10 |
| 🟩 | Ragged Warband | random | Neolithic 100% | 🟢 10/10 (100%) |  | WARRIOR×5, WARRIOR×6, CART×9 |
| 🟩 | Savage Rabble | random | Neolithic 77%, Bronze Age 23% | 🟠 4/10 (40%) | CHARIOT×6 | WARRIOR×10, CART×6, CHARIOT×7, WARRIOR×7 |
| 🟩 | Muddy Marauders | random | Neolithic 65%, Bronze Age 35% | 🟡 7/10 (70%) | CHARIOT×3 | CHARIOT×9, CART×6, WARRIOR×5, CART×6 |
| 🟩 | Frenzied Pillagers | random | Neolithic 39%, Stone Age 35%, Bronze Age 26% | 🟡 6/10 (60%) | BOWMAN×2 | BOWMAN×6, WARRIOR×9, CLUBMAN×8 |
| 🟩 | Disorganized Mob | random | Neolithic 100% | 🟢 10/10 (100%) |  | WARRIOR×8, CART×9, CART×9 |

### Bronze Age

#### Arrow Bronze (len: 8)

| Tower Era Distribution (10 towers) | Towers |
|---|---|
| Bronze Age 100% (10) | ARROW_TOWER×7, FIRE_TOWER×3 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Bronze Warriors | hardcoded | Bronze Age 97%, Iron Age 3% | 🟢 13/13 (100%) |  | BOWMAN×6, BOWMAN×8, SWORDMAN×10, PIKENEER×2, SWORDMAN×10, CHARIOT×12, SWORDMAN×14 |
| 🟥 | Chariot Rush | hardcoded | Bronze Age 100% | ⬛ 0/13 (0%) | SWORDMAN×6, BOWMAN×1 | BOWMAN×12, SWORDMAN×12, SWORDMAN×12, BOWMAN×13, SWORDMAN×9, BOWMAN×12, SWORDMAN×14 |
| 🟩 | Copper Blades | hardcoded | Bronze Age 100% | 🟠 6/13 (46%) | CHARIOT×5, SWORDMAN×1 | SWORDMAN×11, CHARIOT×12, CHARIOT×13, CHARIOT×14, SWORDMAN×14, CHARIOT×12, BOWMAN×14 |
| 🟥 | Harbor Raiders | hardcoded | Bronze Age 100% | ⬛ 0/13 (0%) | BOWMAN×7 | BOWMAN×13, BOWMAN×14, BOWMAN×14, CHARIOT×15, SWORDMAN×15, BOWMAN×16, BOWMAN×14 |
| 🟩 | Bored Mercenaries | random | Bronze Age 74%, Iron Age 14%, Neolithic 11% | 🔴 1/13 (8%) | PIKENEER×5, CHARIOT×5, BOWMAN×1 | SWORDMAN×8, WARRIOR×8, PIKENEER×10, BOWMAN×11, CHARIOT×10, CHARIOT×10, CHARIOT×13 |
| 🟩 | Bored Mercenaries | random | Bronze Age 74%, Iron Age 14%, Neolithic 11% | 🔴 1/13 (8%) | PIKENEER×5, CHARIOT×5, BOWMAN×1 | SWORDMAN×8, WARRIOR×8, PIKENEER×10, BOWMAN×11, CHARIOT×10, CHARIOT×10, CHARIOT×13 |
| 🟥 | Desperate Looters | random | Bronze Age 86%, Neolithic 14% | ⬛ 0/13 (0%) | BOWMAN×6, CHARIOT×1 | SWORDMAN×10, WARRIOR×11, BOWMAN×10, BOWMAN×12, SWORDMAN×12, CHARIOT×10, SWORDMAN×12 |
| 🟩 | Rude Barbarians | random | Bronze Age 87%, Neolithic 13% | 🟠 5/13 (38%) | SWORDMAN×3, BOWMAN×1 | BOWMAN×12, SWORDMAN×12, CART×9, BOWMAN×9, SWORDMAN×8, SWORDMAN×10, BOWMAN×11 |
| 🟩 | Frenzied Pillagers | random | Bronze Age 87%, Neolithic 13% | 🟡 10/13 (77%) | CHARIOT×3 | CHARIOT×10, SWORDMAN×12, BOWMAN×8, CHARIOT×12, SWORDMAN×8, CHARIOT×11, CHARIOT×10, WARRIOR×11 |
| 🟥 | Hungry Invaders | random | Bronze Age 71%, Neolithic 29% | ⬛ 0/13 (0%) | CHARIOT×7, BOWMAN×2, SWORDMAN×1 | WARRIOR×12, WARRIOR×10, SWORDMAN×8, SWORDMAN×12, BOWMAN×12, CHARIOT×11, SWORDMAN×12 |
| 🟥 | Noisy Barbarians | random | Bronze Age 70%, Iron Age 16%, Neolithic 14% | ⬛ 0/13 (0%) | PIKENEER×4, CHARIOT×4, BOWMAN×1, LARGE_CART×1 | BOWMAN×7, SWORDMAN×8, WARRIOR×10, LARGE_CART×12, BOWMAN×10, CHARIOT×13, BOWMAN×13 |
| 🟩 | Crude Invaders | random | Bronze Age 59%, Iron Age 24%, Neolithic 18% | 🟡 7/13 (54%) | PIKENEER×6 | PIKENEER×12, CART×9, SWORDMAN×10, CHARIOT×10, BOWMAN×10 |
| 🟥 | Angry Mob | random | Bronze Age 62%, Neolithic 38% | ⬛ 0/13 (0%) | CHARIOT×9, BOWMAN×2 | WARRIOR×10, WARRIOR×10, BOWMAN×10, CHARIOT×11, SWORDMAN×12 |
| 🟩 | Drunken Raiders | random | Bronze Age 57%, Neolithic 43% | 🟢 13/13 (100%) |  | CHARIOT×11, CART×12, CHARIOT×8, CHARIOT×9, CART×9 |
| 🟩 | Frenzied Pillagers | random | Bronze Age 59%, Neolithic 30%, Iron Age 11% | 🟠 6/13 (46%) | THE_SWORDMASTER×1 | CHARIOT×13, THE_SWORDMASTER×7, SWORDMAN×8, CHARIOT×10, WARRIOR×10, WARRIOR×9, BOWMAN×7 |
| 🟩 | Savage Rabble | random | Bronze Age 58%, Neolithic 30%, Iron Age 12% | 🟡 7/13 (54%) | PIKENEER×6 | SWORDMAN×10, CART×9, SWORDMAN×12, CART×12, PIKENEER×8, SWORDMAN×10, SWORDMAN×8 |
| 🟥 | Ragged Warband | random | Bronze Age 64%, Iron Age 20%, Neolithic 16% | ⬛ 0/13 (0%) | CHARIOT×7, LEGIONARY×6 | BOWMAN×11, CHARIOT×8, CART×9, LEGIONARY×11, SWORDMAN×10, CHARIOT×7 |
| 🟩 | Wandering Pillagers | random | Bronze Age 85%, Neolithic 15% | 🟠 4/13 (31%) | CHARIOT×5, BOWMAN×2 | SWORDMAN×10, BOWMAN×10, WARRIOR×10, BOWMAN×8, CHARIOT×11, BOWMAN×7, CHARIOT×9 |
| 🟩 | Rowdy Plunderers | random | Bronze Age 68%, Neolithic 19%, Iron Age 13% | 🟠 3/13 (23%) | CHARIOT×3, PIKENEER×3, SWORDMAN×2 | WARRIOR×12, SWORDMAN×12, SWORDMAN×8, CHARIOT×9, PIKENEER×8, BOWMAN×13 |
| 🟩 | Noisy Barbarians | random | Bronze Age 84%, Neolithic 16% | 🟢 13/13 (100%) |  | SWORDMAN×12, BOWMAN×7, WARRIOR×7, SWORDMAN×8, SWORDMAN×10 |
| 🟥 | Stubborn Raiders | random | Bronze Age 75%, Neolithic 15%, Iron Age 10% | ⬛ 0/13 (0%) | CHARIOT×9, BOWMAN×2 | BOWMAN×13, CHARIOT×10, WARRIOR×10, SWORDMAN×10, BOWMAN×9, THE_SWORDMASTER×7, SWORDMAN×8 |
| 🟩 | Bored Mercenaries | random | Bronze Age 70%, Neolithic 17%, Iron Age 12% | 🟡 9/13 (69%) | PIKENEER×4 | BOWMAN×8, WARRIOR×11, CHARIOT×9, SWORDMAN×8, LARGE_CART×8, BOWMAN×8, CHARIOT×12 |
| 🟩 | Wandering Pillagers | random | Bronze Age 52%, Neolithic 30%, Iron Age 18% | 🔴 2/13 (15%) | HORSEMAN_FAST×11 | SWORDMAN×12, HORSEMAN_FAST×11, CART×9, BOWMAN×8, CART×9, BOWMAN×12 |
| 🟩 | Frenzied Pillagers | random | Bronze Age 81%, Neolithic 19% | 🟢 13/13 (100%) |  | WARRIOR×10, CHARIOT×8, CHARIOT×13, SWORDMAN×10, BOWMAN×11 |

#### Late Bronze

| Tower Era Distribution (14 towers) | Towers |
|---|---|
| Bronze Age 86% (12), Neolithic 14% (2) | ARROW_TOWER×5, BALLISTA_TOWER×4, FIRE_TOWER×3, SPIKE_TRAP×2 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Bronze Warriors | hardcoded | Bronze Age 97%, Iron Age 3% | 🟢 12/13 (92%) | CHARIOT×1 | BOWMAN×6, BOWMAN×8, SWORDMAN×10, PIKENEER×2, SWORDMAN×10, CHARIOT×12, SWORDMAN×14 |
| 🟩 | Chariot Rush | hardcoded | Bronze Age 100% | 🟢 11/13 (85%) | SWORDMAN×1 | BOWMAN×12, SWORDMAN×12, SWORDMAN×12, BOWMAN×13, SWORDMAN×9, BOWMAN×12, SWORDMAN×14 |
| 🟩 | Copper Blades | hardcoded | Bronze Age 100% | 🟢 13/13 (100%) |  | SWORDMAN×11, CHARIOT×12, CHARIOT×13, CHARIOT×14, SWORDMAN×14, CHARIOT×12, BOWMAN×14 |
| 🟥 | Harbor Raiders | hardcoded | Bronze Age 100% | ⬛ 0/13 (0%) | BOWMAN×5, CHARIOT×3 | BOWMAN×13, BOWMAN×14, BOWMAN×14, CHARIOT×15, SWORDMAN×15, BOWMAN×16, BOWMAN×14 |
| 🟩 | Bored Mercenaries | random | Bronze Age 74%, Iron Age 14%, Neolithic 11% | 🟡 8/13 (62%) | PIKENEER×3, CHARIOT×2 | SWORDMAN×8, WARRIOR×8, PIKENEER×10, BOWMAN×11, CHARIOT×10, CHARIOT×10, CHARIOT×13 |
| 🟩 | Bored Mercenaries | random | Bronze Age 74%, Iron Age 14%, Neolithic 11% | 🟡 8/13 (62%) | PIKENEER×3, CHARIOT×2 | SWORDMAN×8, WARRIOR×8, PIKENEER×10, BOWMAN×11, CHARIOT×10, CHARIOT×10, CHARIOT×13 |
| 🟩 | Desperate Looters | random | Bronze Age 86%, Neolithic 14% | 🟡 7/13 (54%) | SWORDMAN×2, CHARIOT×2 | SWORDMAN×10, WARRIOR×11, BOWMAN×10, BOWMAN×12, SWORDMAN×12, CHARIOT×10, SWORDMAN×12 |
| 🟩 | Rude Barbarians | random | Bronze Age 87%, Neolithic 13% | 🟢 13/13 (100%) |  | BOWMAN×12, SWORDMAN×12, CART×9, BOWMAN×9, SWORDMAN×8, SWORDMAN×10, BOWMAN×11 |
| 🟩 | Frenzied Pillagers | random | Bronze Age 87%, Neolithic 13% | 🟢 12/13 (92%) | CHARIOT×1 | CHARIOT×10, SWORDMAN×12, BOWMAN×8, CHARIOT×12, SWORDMAN×8, CHARIOT×11, CHARIOT×10, WARRIOR×11 |
| 🟩 | Hungry Invaders | random | Bronze Age 71%, Neolithic 29% | 🔴 2/13 (15%) | CHARIOT×7, SWORDMAN×1, BOWMAN×1 | WARRIOR×12, WARRIOR×10, SWORDMAN×8, SWORDMAN×12, BOWMAN×12, CHARIOT×11, SWORDMAN×12 |
| 🟩 | Noisy Barbarians | random | Bronze Age 70%, Iron Age 16%, Neolithic 14% | 🟡 8/13 (62%) | PIKENEER×5 | BOWMAN×7, SWORDMAN×8, WARRIOR×10, LARGE_CART×12, BOWMAN×10, CHARIOT×13, BOWMAN×13 |
| 🟩 | Crude Invaders | random | Bronze Age 59%, Iron Age 24%, Neolithic 18% | 🟢 11/13 (85%) | PIKENEER×2 | PIKENEER×12, CART×9, SWORDMAN×10, CHARIOT×10, BOWMAN×10 |
| 🟩 | Angry Mob | random | Bronze Age 62%, Neolithic 38% | 🟢 11/13 (85%) | CHARIOT×2 | WARRIOR×10, WARRIOR×10, BOWMAN×10, CHARIOT×11, SWORDMAN×12 |
| 🟩 | Drunken Raiders | random | Bronze Age 57%, Neolithic 43% | 🟢 13/13 (100%) |  | CHARIOT×11, CART×12, CHARIOT×8, CHARIOT×9, CART×9 |
| 🟩 | Frenzied Pillagers | random | Bronze Age 59%, Neolithic 30%, Iron Age 11% | 🟠 6/13 (46%) | THE_SWORDMASTER×1 | CHARIOT×13, THE_SWORDMASTER×7, SWORDMAN×8, CHARIOT×10, WARRIOR×10, WARRIOR×9, BOWMAN×7 |
| 🟩 | Savage Rabble | random | Bronze Age 58%, Neolithic 30%, Iron Age 12% | 🟡 10/13 (77%) | PIKENEER×3 | SWORDMAN×10, CART×9, SWORDMAN×12, CART×12, PIKENEER×8, SWORDMAN×10, SWORDMAN×8 |
| 🟩 | Ragged Warband | random | Bronze Age 64%, Iron Age 20%, Neolithic 16% | 🟠 3/13 (23%) | CHARIOT×5, LEGIONARY×3, SWORDMAN×1 | BOWMAN×11, CHARIOT×8, CART×9, LEGIONARY×11, SWORDMAN×10, CHARIOT×7 |
| 🟩 | Wandering Pillagers | random | Bronze Age 85%, Neolithic 15% | 🟢 12/13 (92%) | CHARIOT×1 | SWORDMAN×10, BOWMAN×10, WARRIOR×10, BOWMAN×8, CHARIOT×11, BOWMAN×7, CHARIOT×9 |
| 🟩 | Rowdy Plunderers | random | Bronze Age 68%, Neolithic 19%, Iron Age 13% | 🟢 11/13 (85%) | CHARIOT×1, PIKENEER×1 | WARRIOR×12, SWORDMAN×12, SWORDMAN×8, CHARIOT×9, PIKENEER×8, BOWMAN×13 |
| 🟩 | Noisy Barbarians | random | Bronze Age 84%, Neolithic 16% | 🟢 13/13 (100%) |  | SWORDMAN×12, BOWMAN×7, WARRIOR×7, SWORDMAN×8, SWORDMAN×10 |
| 🟩 | Stubborn Raiders | random | Bronze Age 75%, Neolithic 15%, Iron Age 10% | 🟠 6/13 (46%) | THE_SWORDMASTER×1 | BOWMAN×13, CHARIOT×10, WARRIOR×10, SWORDMAN×10, BOWMAN×9, THE_SWORDMASTER×7, SWORDMAN×8 |
| 🟩 | Bored Mercenaries | random | Bronze Age 70%, Neolithic 17%, Iron Age 12% | 🟢 13/13 (100%) |  | BOWMAN×8, WARRIOR×11, CHARIOT×9, SWORDMAN×8, LARGE_CART×8, BOWMAN×8, CHARIOT×12 |
| 🟩 | Wandering Pillagers | random | Bronze Age 52%, Neolithic 30%, Iron Age 18% | 🟡 8/13 (62%) | HORSEMAN_FAST×5 | SWORDMAN×12, HORSEMAN_FAST×11, CART×9, BOWMAN×8, CART×9, BOWMAN×12 |
| 🟩 | Frenzied Pillagers | random | Bronze Age 81%, Neolithic 19% | 🟢 13/13 (100%) |  | WARRIOR×10, CHARIOT×8, CHARIOT×13, SWORDMAN×10, BOWMAN×11 |

#### Big Bronze

| Tower Era Distribution (29 towers) | Towers |
|---|---|
| Bronze Age 76% (22), Neolithic 24% (7) | ARROW_TOWER×20, SPIKE_TRAP×7, FIRE_TOWER×2 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Bronze Warriors | hardcoded | Bronze Age 97%, Iron Age 3% | 🟢 13/13 (100%) |  | BOWMAN×6, BOWMAN×8, SWORDMAN×10, PIKENEER×2, SWORDMAN×10, CHARIOT×12, SWORDMAN×14 |
| 🟩 | Chariot Rush | hardcoded | Bronze Age 100% | 🟢 13/13 (100%) |  | BOWMAN×12, SWORDMAN×12, SWORDMAN×12, BOWMAN×13, SWORDMAN×9, BOWMAN×12, SWORDMAN×14 |
| 🟩 | Copper Blades | hardcoded | Bronze Age 100% | 🟢 13/13 (100%) |  | SWORDMAN×11, CHARIOT×12, CHARIOT×13, CHARIOT×14, SWORDMAN×14, CHARIOT×12, BOWMAN×14 |
| 🟩 | Harbor Raiders | hardcoded | Bronze Age 100% | 🟢 13/13 (100%) |  | BOWMAN×13, BOWMAN×14, BOWMAN×14, CHARIOT×15, SWORDMAN×15, BOWMAN×16, BOWMAN×14 |
| 🟩 | Bored Mercenaries | random | Bronze Age 74%, Iron Age 14%, Neolithic 11% | 🟢 13/13 (100%) |  | SWORDMAN×8, WARRIOR×8, PIKENEER×10, BOWMAN×11, CHARIOT×10, CHARIOT×10, CHARIOT×13 |
| 🟩 | Bored Mercenaries | random | Bronze Age 74%, Iron Age 14%, Neolithic 11% | 🟢 13/13 (100%) |  | SWORDMAN×8, WARRIOR×8, PIKENEER×10, BOWMAN×11, CHARIOT×10, CHARIOT×10, CHARIOT×13 |
| 🟩 | Desperate Looters | random | Bronze Age 86%, Neolithic 14% | 🟢 13/13 (100%) |  | SWORDMAN×10, WARRIOR×11, BOWMAN×10, BOWMAN×12, SWORDMAN×12, CHARIOT×10, SWORDMAN×12 |
| 🟩 | Rude Barbarians | random | Bronze Age 87%, Neolithic 13% | 🟢 13/13 (100%) |  | BOWMAN×12, SWORDMAN×12, CART×9, BOWMAN×9, SWORDMAN×8, SWORDMAN×10, BOWMAN×11 |
| 🟩 | Frenzied Pillagers | random | Bronze Age 87%, Neolithic 13% | 🟢 13/13 (100%) |  | CHARIOT×10, SWORDMAN×12, BOWMAN×8, CHARIOT×12, SWORDMAN×8, CHARIOT×11, CHARIOT×10, WARRIOR×11 |
| 🟩 | Hungry Invaders | random | Bronze Age 71%, Neolithic 29% | 🟢 13/13 (100%) |  | WARRIOR×12, WARRIOR×10, SWORDMAN×8, SWORDMAN×12, BOWMAN×12, CHARIOT×11, SWORDMAN×12 |
| 🟩 | Noisy Barbarians | random | Bronze Age 70%, Iron Age 16%, Neolithic 14% | 🟢 13/13 (100%) |  | BOWMAN×7, SWORDMAN×8, WARRIOR×10, LARGE_CART×12, BOWMAN×10, CHARIOT×13, BOWMAN×13 |
| 🟩 | Crude Invaders | random | Bronze Age 59%, Iron Age 24%, Neolithic 18% | 🟢 13/13 (100%) |  | PIKENEER×12, CART×9, SWORDMAN×10, CHARIOT×10, BOWMAN×10 |
| 🟩 | Angry Mob | random | Bronze Age 62%, Neolithic 38% | 🟢 13/13 (100%) |  | WARRIOR×10, WARRIOR×10, BOWMAN×10, CHARIOT×11, SWORDMAN×12 |
| 🟩 | Drunken Raiders | random | Bronze Age 57%, Neolithic 43% | 🟢 13/13 (100%) |  | CHARIOT×11, CART×12, CHARIOT×8, CHARIOT×9, CART×9 |
| 🟩 | Frenzied Pillagers | random | Bronze Age 59%, Neolithic 30%, Iron Age 11% | 🟠 6/13 (46%) | THE_SWORDMASTER×1 | CHARIOT×13, THE_SWORDMASTER×7, SWORDMAN×8, CHARIOT×10, WARRIOR×10, WARRIOR×9, BOWMAN×7 |
| 🟩 | Savage Rabble | random | Bronze Age 58%, Neolithic 30%, Iron Age 12% | 🟢 13/13 (100%) |  | SWORDMAN×10, CART×9, SWORDMAN×12, CART×12, PIKENEER×8, SWORDMAN×10, SWORDMAN×8 |
| 🟩 | Ragged Warband | random | Bronze Age 64%, Iron Age 20%, Neolithic 16% | 🟢 13/13 (100%) |  | BOWMAN×11, CHARIOT×8, CART×9, LEGIONARY×11, SWORDMAN×10, CHARIOT×7 |
| 🟩 | Wandering Pillagers | random | Bronze Age 85%, Neolithic 15% | 🟢 13/13 (100%) |  | SWORDMAN×10, BOWMAN×10, WARRIOR×10, BOWMAN×8, CHARIOT×11, BOWMAN×7, CHARIOT×9 |
| 🟩 | Rowdy Plunderers | random | Bronze Age 68%, Neolithic 19%, Iron Age 13% | 🟢 13/13 (100%) |  | WARRIOR×12, SWORDMAN×12, SWORDMAN×8, CHARIOT×9, PIKENEER×8, BOWMAN×13 |
| 🟩 | Noisy Barbarians | random | Bronze Age 84%, Neolithic 16% | 🟢 13/13 (100%) |  | SWORDMAN×12, BOWMAN×7, WARRIOR×7, SWORDMAN×8, SWORDMAN×10 |
| 🟩 | Stubborn Raiders | random | Bronze Age 75%, Neolithic 15%, Iron Age 10% | 🟠 6/13 (46%) | THE_SWORDMASTER×1 | BOWMAN×13, CHARIOT×10, WARRIOR×10, SWORDMAN×10, BOWMAN×9, THE_SWORDMASTER×7, SWORDMAN×8 |
| 🟩 | Bored Mercenaries | random | Bronze Age 70%, Neolithic 17%, Iron Age 12% | 🟢 13/13 (100%) |  | BOWMAN×8, WARRIOR×11, CHARIOT×9, SWORDMAN×8, LARGE_CART×8, BOWMAN×8, CHARIOT×12 |
| 🟩 | Wandering Pillagers | random | Bronze Age 52%, Neolithic 30%, Iron Age 18% | 🟢 13/13 (100%) |  | SWORDMAN×12, HORSEMAN_FAST×11, CART×9, BOWMAN×8, CART×9, BOWMAN×12 |
| 🟩 | Frenzied Pillagers | random | Bronze Age 81%, Neolithic 19% | 🟢 13/13 (100%) |  | WARRIOR×10, CHARIOT×8, CHARIOT×13, SWORDMAN×10, BOWMAN×11 |

#### Weak Bronze

| Tower Era Distribution (6 towers) | Towers |
|---|---|
| Bronze Age 50% (3), Neolithic 50% (3) | DOUBLE_SLING_TOWER×3, ARROW_TOWER×2, FIRE_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟥 | Bronze Warriors | hardcoded | Bronze Age 97%, Iron Age 3% | ⬛ 0/13 (0%) | BOWMAN×7 | BOWMAN×6, BOWMAN×8, SWORDMAN×10, PIKENEER×2, SWORDMAN×10, CHARIOT×12, SWORDMAN×14 |
| 🟥 | Chariot Rush | hardcoded | Bronze Age 100% | ⬛ 0/13 (0%) | BOWMAN×7 | BOWMAN×12, SWORDMAN×12, SWORDMAN×12, BOWMAN×13, SWORDMAN×9, BOWMAN×12, SWORDMAN×14 |
| 🟥 | Copper Blades | hardcoded | Bronze Age 100% | ⬛ 0/13 (0%) | CHARIOT×8, SWORDMAN×3 | SWORDMAN×11, CHARIOT×12, CHARIOT×13, CHARIOT×14, SWORDMAN×14, CHARIOT×12, BOWMAN×14 |
| 🟥 | Harbor Raiders | hardcoded | Bronze Age 100% | ⬛ 0/13 (0%) | BOWMAN×7 | BOWMAN×13, BOWMAN×14, BOWMAN×14, CHARIOT×15, SWORDMAN×15, BOWMAN×16, BOWMAN×14 |
| 🟥 | Bored Mercenaries | random | Bronze Age 74%, Iron Age 14%, Neolithic 11% | ⬛ 0/13 (0%) | PIKENEER×8, CHARIOT×3, SWORDMAN×1 | SWORDMAN×8, WARRIOR×8, PIKENEER×10, BOWMAN×11, CHARIOT×10, CHARIOT×10, CHARIOT×13 |
| 🟥 | Bored Mercenaries | random | Bronze Age 74%, Iron Age 14%, Neolithic 11% | ⬛ 0/13 (0%) | PIKENEER×8, CHARIOT×3, SWORDMAN×1 | SWORDMAN×8, WARRIOR×8, PIKENEER×10, BOWMAN×11, CHARIOT×10, CHARIOT×10, CHARIOT×13 |
| 🟥 | Desperate Looters | random | Bronze Age 86%, Neolithic 14% | ⬛ 0/13 (0%) | BOWMAN×5, SWORDMAN×2 | SWORDMAN×10, WARRIOR×11, BOWMAN×10, BOWMAN×12, SWORDMAN×12, CHARIOT×10, SWORDMAN×12 |
| 🟥 | Rude Barbarians | random | Bronze Age 87%, Neolithic 13% | ⬛ 0/13 (0%) | BOWMAN×7 | BOWMAN×12, SWORDMAN×12, CART×9, BOWMAN×9, SWORDMAN×8, SWORDMAN×10, BOWMAN×11 |
| 🟥 | Frenzied Pillagers | random | Bronze Age 87%, Neolithic 13% | ⬛ 0/13 (0%) | CHARIOT×5, SWORDMAN×2, BOWMAN×2 | CHARIOT×10, SWORDMAN×12, BOWMAN×8, CHARIOT×12, SWORDMAN×8, CHARIOT×11, CHARIOT×10, WARRIOR×11 |
| 🟥 | Hungry Invaders | random | Bronze Age 71%, Neolithic 29% | ⬛ 0/13 (0%) | SWORDMAN×6, WARRIOR×1 | WARRIOR×12, WARRIOR×10, SWORDMAN×8, SWORDMAN×12, BOWMAN×12, CHARIOT×11, SWORDMAN×12 |
| 🟥 | Noisy Barbarians | random | Bronze Age 70%, Iron Age 16%, Neolithic 14% | ⬛ 0/13 (0%) | PIKENEER×5, BOWMAN×3, SWORDMAN×1 | BOWMAN×7, SWORDMAN×8, WARRIOR×10, LARGE_CART×12, BOWMAN×10, CHARIOT×13, BOWMAN×13 |
| 🟥 | Crude Invaders | random | Bronze Age 59%, Iron Age 24%, Neolithic 18% | ⬛ 0/13 (0%) | PIKENEER×9, CHARIOT×4 | PIKENEER×12, CART×9, SWORDMAN×10, CHARIOT×10, BOWMAN×10 |
| 🟥 | Angry Mob | random | Bronze Age 62%, Neolithic 38% | ⬛ 0/13 (0%) | CHARIOT×5, BOWMAN×4 | WARRIOR×10, WARRIOR×10, BOWMAN×10, CHARIOT×11, SWORDMAN×12 |
| 🟥 | Drunken Raiders | random | Bronze Age 57%, Neolithic 43% | ⬛ 0/13 (0%) | CHARIOT×13 | CHARIOT×11, CART×12, CHARIOT×8, CHARIOT×9, CART×9 |
| 🟥 | Frenzied Pillagers | random | Bronze Age 59%, Neolithic 30%, Iron Age 11% | ⬛ 0/13 (0%) | CHARIOT×6, THE_SWORDMASTER×1 | CHARIOT×13, THE_SWORDMASTER×7, SWORDMAN×8, CHARIOT×10, WARRIOR×10, WARRIOR×9, BOWMAN×7 |
| 🟥 | Savage Rabble | random | Bronze Age 58%, Neolithic 30%, Iron Age 12% | ⬛ 0/13 (0%) | SWORDMAN×6, PIKENEER×1 | SWORDMAN×10, CART×9, SWORDMAN×12, CART×12, PIKENEER×8, SWORDMAN×10, SWORDMAN×8 |
| 🟥 | Ragged Warband | random | Bronze Age 64%, Iron Age 20%, Neolithic 16% | ⬛ 0/13 (0%) | CHARIOT×7, BOWMAN×3 | BOWMAN×11, CHARIOT×8, CART×9, LEGIONARY×11, SWORDMAN×10, CHARIOT×7 |
| 🟥 | Wandering Pillagers | random | Bronze Age 85%, Neolithic 15% | ⬛ 0/13 (0%) | BOWMAN×5, SWORDMAN×2 | SWORDMAN×10, BOWMAN×10, WARRIOR×10, BOWMAN×8, CHARIOT×11, BOWMAN×7, CHARIOT×9 |
| 🟥 | Rowdy Plunderers | random | Bronze Age 68%, Neolithic 19%, Iron Age 13% | ⬛ 0/13 (0%) | CHARIOT×5, SWORDMAN×4 | WARRIOR×12, SWORDMAN×12, SWORDMAN×8, CHARIOT×9, PIKENEER×8, BOWMAN×13 |
| 🟥 | Noisy Barbarians | random | Bronze Age 84%, Neolithic 16% | ⬛ 0/13 (0%) | BOWMAN×4, SWORDMAN×3 | SWORDMAN×12, BOWMAN×7, WARRIOR×7, SWORDMAN×8, SWORDMAN×10 |
| 🟥 | Stubborn Raiders | random | Bronze Age 75%, Neolithic 15%, Iron Age 10% | ⬛ 0/13 (0%) | CHARIOT×7, BOWMAN×3 | BOWMAN×13, CHARIOT×10, WARRIOR×10, SWORDMAN×10, BOWMAN×9, THE_SWORDMASTER×7, SWORDMAN×8 |
| 🟥 | Bored Mercenaries | random | Bronze Age 70%, Neolithic 17%, Iron Age 12% | ⬛ 0/13 (0%) | CHARIOT×5, BOWMAN×4 | BOWMAN×8, WARRIOR×11, CHARIOT×9, SWORDMAN×8, LARGE_CART×8, BOWMAN×8, CHARIOT×12 |
| 🟥 | Wandering Pillagers | random | Bronze Age 52%, Neolithic 30%, Iron Age 18% | ⬛ 0/13 (0%) | HORSEMAN_FAST×11, SWORDMAN×1 | SWORDMAN×12, HORSEMAN_FAST×11, CART×9, BOWMAN×8, CART×9, BOWMAN×12 |
| 🟥 | Frenzied Pillagers | random | Bronze Age 81%, Neolithic 19% | ⬛ 0/13 (0%) | CHARIOT×11, SWORDMAN×1 | WARRIOR×10, CHARIOT×8, CHARIOT×13, SWORDMAN×10, BOWMAN×11 |

### Iron Age

#### Schafshügel (Bronze)

| Tower Era Distribution (13 towers) | Towers |
|---|---|
| Bronze Age 77% (10), Iron Age 23% (3) | BALLISTA_TOWER×5, FIRE_TOWER×4, CATAPULTS×3, ARROW_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟥 | Iron Legion | hardcoded | Iron Age 100% | ⬛ 0/12 (0%) | LEGIONARY×5, PIKENEER×5, HORSEMAN_FAST×2 | HORSEMAN_SLOW×10, HORSEMAN_SLOW×10, LEGIONARY×11, PIKENEER×12, LEGIONARY×15, HORSEMAN_FAST×16, THE_SWORDMASTER×18, LEGIONARY×20, LEGIONARY×22, PIKENEER×24 |
| 🟥 | Cavalry Strike | hardcoded | Iron Age 95%, Medieval 5% | ⬛ 0/12 (0%) | PIKENEER×7, HORSEMAN_FAST×5 | LEGIONARY×14, PIKENEER×15, HORSEMAN_FAST×16, LARGE_CART×17, LEGIONARY×18, KNIGHT×9, PIKENEER×22, LARGE_CART×18, HORSEMAN_SLOW×22, LEGIONARY×26 |
| 🟥 | Legionary March | hardcoded | Iron Age 95%, Medieval 5% | ⬛ 0/12 (0%) | PIKENEER×7, LEGIONARY×2, HORSEMAN_SLOW×1, HORSEMAN_FAST×1 | LEGIONARY×14, HORSEMAN_SLOW×15, PIKENEER×16, HORSEMAN_FAST×17, HORSEMAN_FAST×17, HORSEMAN_SLOW×18, CRUSADER×9, LARGE_CART×20, LEGIONARY×18, THE_SWORDMASTER×26 |
| 🟥 | Iron Tide | hardcoded | Iron Age 94%, Medieval 6% | ⬛ 0/12 (0%) | HORSEMAN_FAST×12 | LEGIONARY×14, HORSEMAN_FAST×15, LARGE_CART×16, HORSEMAN_SLOW×16, LARGE_CART×17, HORSEMAN_FAST×18, LEGIONARY×18, THE_SWORDMASTER×19, CRUSADER×12, THE_SWORDMASTER×26, LEGIONARY×28 |
| 🟥 | Quartermaster Force | hardcoded | Iron Age 100% | ⬛ 0/12 (0%) | PIKENEER×3, LEGIONARY×2, THE_SWORDMASTER×1 | THE_SWORDMASTER×16, LEGIONARY×17, HORSEMAN_SLOW×18, LARGE_CART×19, PIKENEER×20, LARGE_CART×21, LARGE_CART×22, LEGIONARY×16, PIKENEER×18, LARGE_CART×20, HORSEMAN_SLOW×22, HORSEMAN_SLOW×24, LEGIONARY×28 |
| 🟥 | Blundering Invaders | random | Iron Age 90%, Medieval 10% | ⬛ 0/12 (0%) | SAMURAI×7, HORSEMAN_FAST×5 | SAMURAI×8, LEGIONARY×13, HORSEMAN_SLOW×9, HORSEMAN_FAST×11, THE_SWORDMASTER×7, LARGE_CART×8, PIKENEER×11, HORSEMAN_FAST×15 |
| 🟥 | Blundering Invaders | random | Iron Age 90%, Medieval 10% | ⬛ 0/12 (0%) | SAMURAI×7, HORSEMAN_FAST×5 | SAMURAI×8, LEGIONARY×13, HORSEMAN_SLOW×9, HORSEMAN_FAST×11, THE_SWORDMASTER×7, LARGE_CART×8, PIKENEER×11, HORSEMAN_FAST×15 |
| 🟥 | Relentless Mob | random | Iron Age 92%, Bronze Age 8% | ⬛ 0/12 (0%) | HORSEMAN_FAST×8, THE_SWORDMASTER×1 | HORSEMAN_SLOW×11, HORSEMAN_FAST×13, THE_SWORDMASTER×7, PIKENEER×14, HORSEMAN_FAST×9, LEGIONARY×11, LEGIONARY×11, LEGIONARY×14, CHARIOT×8 |
| 🟥 | Bored Mercenaries | random | Iron Age 88%, Medieval 12% | ⬛ 0/12 (0%) | HORSEMAN_FAST×9, PIKENEER×3 | HORSEMAN_FAST×14, HORSEMAN_SLOW×13, PIKENEER×10, HORSEMAN_FAST×11, KNIGHT×12, PIKENEER×13, LEGIONARY×9, THE_SWORDMASTER×7, PIKENEER×13 |
| 🟥 | Petty Bandits | random | Iron Age 85%, Bronze Age 15% | ⬛ 0/12 (0%) | HORSEMAN_FAST×12 | HORSEMAN_FAST×13, PIKENEER×10, LEGIONARY×14, HORSEMAN_FAST×11, LEGIONARY×9, LEGIONARY×11, THE_SWORDMASTER×7, LEGIONARY×13, CHARIOT×15 |
| 🟥 | Angry Mob | random | Iron Age 66%, Bronze Age 34% | ⬛ 0/12 (0%) | HORSEMAN_FAST×7, PIKENEER×5 | HORSEMAN_SLOW×13, LARGE_CART×12, HORSEMAN_FAST×14, PIKENEER×11, CHARIOT×10, BOWMAN×13, LEGIONARY×13, BOWMAN×14, LEGIONARY×9 |
| 🟥 | Relentless Mob | random | Iron Age 85%, Medieval 15% | ⬛ 0/12 (0%) | CRUSADER×4, SIEGE_RAM×1 | HORSEMAN_SLOW×12, SIEGE_RAM×12, THE_SWORDMASTER×7, HORSEMAN_FAST×13, LARGE_CART×12, PIKENEER×8, PIKENEER×8, LARGE_CART×8 |
| 🟥 | Grumpy Marauders | random | Iron Age 75%, Medieval 25% | ⬛ 0/12 (0%) | CRUSADER×3, SAMURAI×2, SIEGE_RAM×1 | SIEGE_RAM×9, SAMURAI×10, HORSEMAN_SLOW×12, LARGE_CART×12, PIKENEER×13, HORSEMAN_FAST×11, LARGE_CART×8 |
| 🟩 | Blundering Invaders | random | Iron Age 74%, Bronze Age 26% | 🔴 1/12 (8%) | HORSEMAN_FAST×8, PIKENEER×3 | PIKENEER×12, PIKENEER×12, HORSEMAN_FAST×14, HORSEMAN_SLOW×12, BOWMAN×9, CHARIOT×13, LARGE_CART×12 |
| 🟥 | Weary Plunderers | random | Bronze Age 51%, Iron Age 49% | ⬛ 0/12 (0%) | PIKENEER×4, BOWMAN×2, THE_SWORDMASTER×1 | LARGE_CART×8, LARGE_CART×12, BOWMAN×13, PIKENEER×12, BOWMAN×15, THE_SWORDMASTER×7, CHARIOT×12 |
| 🟥 | Drunken Raiders | random | Bronze Age 41%, Iron Age 32%, Medieval 27% | ⬛ 0/12 (0%) | CONDOTTERI×5, PIKENEER×3 | CHARIOT×14, SWORDMAN×12, LARGE_CART×12, CONDOTTERI×15, HANDGUNNER×10, BOWMAN×11, PIKENEER×8, HORSEMAN_FAST×9 |
| 🟥 | Rampaging Rabble | random | Iron Age 64%, Bronze Age 25%, Medieval 11% | ⬛ 0/12 (0%) | KNIGHT×3, LEGIONARY×2, THE_SWORDMASTER×1 | SWORDMAN×12, THE_SWORDMASTER×7, LEGIONARY×9, CHARIOT×9, LEGIONARY×14, KNIGHT×9, LEGIONARY×12, HORSEMAN_FAST×11 |
| 🟥 | Drunken Raiders | random | Iron Age 84%, Medieval 16% | ⬛ 0/12 (0%) | CONDOTTERI×4, LEGIONARY×3, PIKENEER×2 | LEGIONARY×12, PIKENEER×8, CONDOTTERI×13, THE_SWORDMASTER×7, HORSEMAN_SLOW×12, PIKENEER×14, HORSEMAN_FAST×13 |
| 🟥 | Bored Mercenaries | random | Iron Age 85%, Bronze Age 15% | ⬛ 0/12 (0%) | HORSEMAN_FAST×10, THE_SWORDMASTER×1 | HORSEMAN_SLOW×9, HORSEMAN_FAST×11, SWORDMAN×12, PIKENEER×9, THE_SWORDMASTER×7, HORSEMAN_FAST×12, LEGIONARY×13, PIKENEER×8 |
| 🟥 | Unlucky Raiders | random | Iron Age 71%, Medieval 18%, Bronze Age 12% | ⬛ 0/12 (0%) | SAMURAI×12 | SAMURAI×15, BOWMAN×10, PIKENEER×15, LEGIONARY×8, THE_SWORDMASTER×7, HORSEMAN_FAST×13, HORSEMAN_SLOW×8, HORSEMAN_FAST×9 |
| 🟥 | Rude Barbarians | random | Iron Age 73%, Bronze Age 14%, Medieval 13% | ⬛ 0/12 (0%) | HORSEMAN_FAST×6, LEGIONARY×4, CHARIOT×2 | HORSEMAN_FAST×11, HORSEMAN_SLOW×8, HORSEMAN_FAST×10, LEGIONARY×15, HORSEMAN_SLOW×8, CHARIOT×10, KNIGHT×9 |
| 🟥 | Frenzied Pillagers | random | Iron Age 70%, Medieval 30% | ⬛ 0/12 (0%) | HORSEMAN_FAST×6, THE_SWORDMASTER×1 | HORSEMAN_SLOW×11, HORSEMAN_FAST×10, THE_SWORDMASTER×7, LEGIONARY×9, SAMURAI×11, HORSEMAN_FAST×8, PIKENEER×15, SIEGE_RAM×15 |
| 🟥 | Stubborn Raiders | random | Iron Age 88%, Medieval 12% | ⬛ 0/12 (0%) | PIKENEER×3, HORSEMAN_FAST×3, CONDOTTERI×3 | LARGE_CART×8, LARGE_CART×12, HORSEMAN_FAST×13, LARGE_CART×12, CONDOTTERI×12, PIKENEER×9, LEGIONARY×10, HORSEMAN_SLOW×10, HORSEMAN_SLOW×12 |
| 🟥 | Desperate Looters | random | Iron Age 58%, Bronze Age 28%, Medieval 14% | ⬛ 0/12 (0%) | CONDOTTERI×6 | HORSEMAN_SLOW×9, SWORDMAN×12, BOWMAN×15, CONDOTTERI×14, LEGIONARY×13, LEGIONARY×9, HORSEMAN_SLOW×14, LEGIONARY×11 |
| 🟥 | Grumpy Marauders | random | Iron Age 74%, Bronze Age 15%, Medieval 11% | ⬛ 0/12 (0%) | CRUSADER×6 | CRUSADER×9, LEGIONARY×12, LARGE_CART×16, HORSEMAN_SLOW×13, SWORDMAN×12, HORSEMAN_FAST×12, LARGE_CART×8 |

#### Mixed Iron/Bronze

| Tower Era Distribution (31 towers) | Towers |
|---|---|
| Bronze Age 68% (21), Iron Age 32% (10) | FIRE_TOWER×9, CATAPULTS×8, ARROW_TOWER×6, BALLISTA_TOWER×6, ARBELESTE_TOWER×2 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Iron Legion | hardcoded | Iron Age 100% | 🟢 16/16 (100%) |  | HORSEMAN_SLOW×10, HORSEMAN_SLOW×10, LEGIONARY×11, PIKENEER×12, LEGIONARY×15, HORSEMAN_FAST×16, THE_SWORDMASTER×18, LEGIONARY×20, LEGIONARY×22, PIKENEER×24 |
| 🟩 | Cavalry Strike | hardcoded | Iron Age 95%, Medieval 5% | 🟢 14/16 (88%) | KNIGHT×2 | LEGIONARY×14, PIKENEER×15, HORSEMAN_FAST×16, LARGE_CART×17, LEGIONARY×18, KNIGHT×9, PIKENEER×22, LARGE_CART×18, HORSEMAN_SLOW×22, LEGIONARY×26 |
| 🟥 | Legionary March | hardcoded | Iron Age 95%, Medieval 5% | ⬛ 0/16 (0%) | CRUSADER×5, THE_SWORDMASTER×1 | LEGIONARY×14, HORSEMAN_SLOW×15, PIKENEER×16, HORSEMAN_FAST×17, HORSEMAN_FAST×17, HORSEMAN_SLOW×18, CRUSADER×9, LARGE_CART×20, LEGIONARY×18, THE_SWORDMASTER×26 |
| 🟥 | Iron Tide | hardcoded | Iron Age 94%, Medieval 6% | ⬛ 0/16 (0%) | CRUSADER×5, THE_SWORDMASTER×1 | LEGIONARY×14, HORSEMAN_FAST×15, LARGE_CART×16, HORSEMAN_SLOW×16, LARGE_CART×17, HORSEMAN_FAST×18, LEGIONARY×18, THE_SWORDMASTER×19, CRUSADER×12, THE_SWORDMASTER×26, LEGIONARY×28 |
| 🟩 | Quartermaster Force | hardcoded | Iron Age 100% | 🟢 16/16 (100%) |  | THE_SWORDMASTER×16, LEGIONARY×17, HORSEMAN_SLOW×18, LARGE_CART×19, PIKENEER×20, LARGE_CART×21, LARGE_CART×22, LEGIONARY×16, PIKENEER×18, LARGE_CART×20, HORSEMAN_SLOW×22, HORSEMAN_SLOW×24, LEGIONARY×28 |
| 🟩 | Blundering Invaders | random | Iron Age 90%, Medieval 10% | 🟢 16/16 (100%) |  | SAMURAI×8, LEGIONARY×13, HORSEMAN_SLOW×9, HORSEMAN_FAST×11, THE_SWORDMASTER×7, LARGE_CART×8, PIKENEER×11, HORSEMAN_FAST×15 |
| 🟩 | Blundering Invaders | random | Iron Age 90%, Medieval 10% | 🟢 16/16 (100%) |  | SAMURAI×8, LEGIONARY×13, HORSEMAN_SLOW×9, HORSEMAN_FAST×11, THE_SWORDMASTER×7, LARGE_CART×8, PIKENEER×11, HORSEMAN_FAST×15 |
| 🟩 | Relentless Mob | random | Iron Age 92%, Bronze Age 8% | 🟢 16/16 (100%) |  | HORSEMAN_SLOW×11, HORSEMAN_FAST×13, THE_SWORDMASTER×7, PIKENEER×14, HORSEMAN_FAST×9, LEGIONARY×11, LEGIONARY×11, LEGIONARY×14, CHARIOT×8 |
| 🟩 | Bored Mercenaries | random | Iron Age 88%, Medieval 12% | 🟠 6/16 (38%) | KNIGHT×3, THE_SWORDMASTER×1 | HORSEMAN_FAST×14, HORSEMAN_SLOW×13, PIKENEER×10, HORSEMAN_FAST×11, KNIGHT×12, PIKENEER×13, LEGIONARY×9, THE_SWORDMASTER×7, PIKENEER×13 |
| 🟩 | Petty Bandits | random | Iron Age 85%, Bronze Age 15% | 🟡 9/16 (56%) | THE_SWORDMASTER×1 | HORSEMAN_FAST×13, PIKENEER×10, LEGIONARY×14, HORSEMAN_FAST×11, LEGIONARY×9, LEGIONARY×11, THE_SWORDMASTER×7, LEGIONARY×13, CHARIOT×15 |
| 🟩 | Angry Mob | random | Iron Age 66%, Bronze Age 34% | 🟢 16/16 (100%) |  | HORSEMAN_SLOW×13, LARGE_CART×12, HORSEMAN_FAST×14, PIKENEER×11, CHARIOT×10, BOWMAN×13, LEGIONARY×13, BOWMAN×14, LEGIONARY×9 |
| 🟥 | Relentless Mob | random | Iron Age 85%, Medieval 15% | ⬛ 0/16 (0%) | CRUSADER×6, SIEGE_RAM×1 | HORSEMAN_SLOW×12, SIEGE_RAM×12, THE_SWORDMASTER×7, HORSEMAN_FAST×13, LARGE_CART×12, PIKENEER×8, PIKENEER×8, LARGE_CART×8 |
| 🟩 | Grumpy Marauders | random | Iron Age 75%, Medieval 25% | 🔴 2/16 (12%) | SAMURAI×4, CRUSADER×3, SIEGE_RAM×1 | SIEGE_RAM×9, SAMURAI×10, HORSEMAN_SLOW×12, LARGE_CART×12, PIKENEER×13, HORSEMAN_FAST×11, LARGE_CART×8 |
| 🟩 | Blundering Invaders | random | Iron Age 74%, Bronze Age 26% | 🟢 16/16 (100%) |  | PIKENEER×12, PIKENEER×12, HORSEMAN_FAST×14, HORSEMAN_SLOW×12, BOWMAN×9, CHARIOT×13, LARGE_CART×12 |
| 🟩 | Weary Plunderers | random | Bronze Age 51%, Iron Age 49% | 🟡 9/16 (56%) | THE_SWORDMASTER×1 | LARGE_CART×8, LARGE_CART×12, BOWMAN×13, PIKENEER×12, BOWMAN×15, THE_SWORDMASTER×7, CHARIOT×12 |
| 🟥 | Drunken Raiders | random | Bronze Age 41%, Iron Age 32%, Medieval 27% | ⬛ 0/16 (0%) | CONDOTTERI×6, HANDGUNNER×4 | CHARIOT×14, SWORDMAN×12, LARGE_CART×12, CONDOTTERI×15, HANDGUNNER×10, BOWMAN×11, PIKENEER×8, HORSEMAN_FAST×9 |
| 🟩 | Rampaging Rabble | random | Iron Age 64%, Bronze Age 25%, Medieval 11% | 🟢 14/16 (88%) | KNIGHT×2 | SWORDMAN×12, THE_SWORDMASTER×7, LEGIONARY×9, CHARIOT×9, LEGIONARY×14, KNIGHT×9, LEGIONARY×12, HORSEMAN_FAST×11 |
| 🟩 | Drunken Raiders | random | Iron Age 84%, Medieval 16% | 🔴 2/16 (12%) | CONDOTTERI×7 | LEGIONARY×12, PIKENEER×8, CONDOTTERI×13, THE_SWORDMASTER×7, HORSEMAN_SLOW×12, PIKENEER×14, HORSEMAN_FAST×13 |
| 🟩 | Bored Mercenaries | random | Iron Age 85%, Bronze Age 15% | 🟢 16/16 (100%) |  | HORSEMAN_SLOW×9, HORSEMAN_FAST×11, SWORDMAN×12, PIKENEER×9, THE_SWORDMASTER×7, HORSEMAN_FAST×12, LEGIONARY×13, PIKENEER×8 |
| 🟩 | Unlucky Raiders | random | Iron Age 71%, Medieval 18%, Bronze Age 12% | 🟠 6/16 (38%) | SAMURAI×3, THE_SWORDMASTER×1 | SAMURAI×15, BOWMAN×10, PIKENEER×15, LEGIONARY×8, THE_SWORDMASTER×7, HORSEMAN_FAST×13, HORSEMAN_SLOW×8, HORSEMAN_FAST×9 |
| 🟩 | Rude Barbarians | random | Iron Age 73%, Bronze Age 14%, Medieval 13% | 🟢 14/16 (88%) | KNIGHT×2 | HORSEMAN_FAST×11, HORSEMAN_SLOW×8, HORSEMAN_FAST×10, LEGIONARY×15, HORSEMAN_SLOW×8, CHARIOT×10, KNIGHT×9 |
| 🟥 | Frenzied Pillagers | random | Iron Age 70%, Medieval 30% | ⬛ 0/16 (0%) | CRUSADER×5, SAMURAI×3, SIEGE_RAM×1 | HORSEMAN_SLOW×11, HORSEMAN_FAST×10, THE_SWORDMASTER×7, LEGIONARY×9, SAMURAI×11, HORSEMAN_FAST×8, PIKENEER×15, SIEGE_RAM×15 |
| 🟩 | Stubborn Raiders | random | Iron Age 88%, Medieval 12% | 🟡 8/16 (50%) | CONDOTTERI×4 | LARGE_CART×8, LARGE_CART×12, HORSEMAN_FAST×13, LARGE_CART×12, CONDOTTERI×12, PIKENEER×9, LEGIONARY×10, HORSEMAN_SLOW×10, HORSEMAN_SLOW×12 |
| 🟥 | Desperate Looters | random | Iron Age 58%, Bronze Age 28%, Medieval 14% | ⬛ 0/16 (0%) | CONDOTTERI×8 | HORSEMAN_SLOW×9, SWORDMAN×12, BOWMAN×15, CONDOTTERI×14, LEGIONARY×13, LEGIONARY×9, HORSEMAN_SLOW×14, LEGIONARY×11 |
| 🟩 | Grumpy Marauders | random | Iron Age 74%, Bronze Age 15%, Medieval 11% | 🟢 14/16 (88%) | CRUSADER×1 | CRUSADER×9, LEGIONARY×12, LARGE_CART×16, HORSEMAN_SLOW×13, SWORDMAN×12, HORSEMAN_FAST×12, LARGE_CART×8 |

#### Almost Bronze

| Tower Era Distribution (25 towers) | Towers |
|---|---|
| Bronze Age 92% (23), Iron Age 8% (2) | ARROW_TOWER×14, BALLISTA_TOWER×7, FIRE_TOWER×2, ARBELESTE_TOWER×2 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟥 | Iron Legion | hardcoded | Iron Age 100% | ⬛ 0/13 (0%) | PIKENEER×4, LEGIONARY×2, THE_SWORDMASTER×1 | HORSEMAN_SLOW×10, HORSEMAN_SLOW×10, LEGIONARY×11, PIKENEER×12, LEGIONARY×15, HORSEMAN_FAST×16, THE_SWORDMASTER×18, LEGIONARY×20, LEGIONARY×22, PIKENEER×24 |
| 🟩 | Cavalry Strike | hardcoded | Iron Age 95%, Medieval 5% | 🟡 7/13 (54%) | PIKENEER×2, HORSEMAN_FAST×2, KNIGHT×2 | LEGIONARY×14, PIKENEER×15, HORSEMAN_FAST×16, LARGE_CART×17, LEGIONARY×18, KNIGHT×9, PIKENEER×22, LARGE_CART×18, HORSEMAN_SLOW×22, LEGIONARY×26 |
| 🟥 | Legionary March | hardcoded | Iron Age 95%, Medieval 5% | ⬛ 0/13 (0%) | CRUSADER×6, HORSEMAN_FAST×1 | LEGIONARY×14, HORSEMAN_SLOW×15, PIKENEER×16, HORSEMAN_FAST×17, HORSEMAN_FAST×17, HORSEMAN_SLOW×18, CRUSADER×9, LARGE_CART×20, LEGIONARY×18, THE_SWORDMASTER×26 |
| 🟥 | Iron Tide | hardcoded | Iron Age 94%, Medieval 6% | ⬛ 0/13 (0%) | CRUSADER×2, HORSEMAN_FAST×1, PIKENEER×1, THE_SWORDMASTER×1 | LEGIONARY×14, HORSEMAN_FAST×15, LARGE_CART×16, HORSEMAN_SLOW×16, LARGE_CART×17, HORSEMAN_FAST×18, LEGIONARY×18, THE_SWORDMASTER×19, CRUSADER×12, THE_SWORDMASTER×26, LEGIONARY×28 |
| 🟩 | Quartermaster Force | hardcoded | Iron Age 100% | 🟠 6/13 (46%) | PIKENEER×7 | THE_SWORDMASTER×16, LEGIONARY×17, HORSEMAN_SLOW×18, LARGE_CART×19, PIKENEER×20, LARGE_CART×21, LARGE_CART×22, LEGIONARY×16, PIKENEER×18, LARGE_CART×20, HORSEMAN_SLOW×22, HORSEMAN_SLOW×24, LEGIONARY×28 |
| 🟩 | Blundering Invaders | random | Iron Age 90%, Medieval 10% | 🟢 11/13 (85%) | SAMURAI×2 | SAMURAI×8, LEGIONARY×13, HORSEMAN_SLOW×9, HORSEMAN_FAST×11, THE_SWORDMASTER×7, LARGE_CART×8, PIKENEER×11, HORSEMAN_FAST×15 |
| 🟩 | Blundering Invaders | random | Iron Age 90%, Medieval 10% | 🟢 11/13 (85%) | SAMURAI×2 | SAMURAI×8, LEGIONARY×13, HORSEMAN_SLOW×9, HORSEMAN_FAST×11, THE_SWORDMASTER×7, LARGE_CART×8, PIKENEER×11, HORSEMAN_FAST×15 |
| 🟩 | Relentless Mob | random | Iron Age 92%, Bronze Age 8% | 🟢 13/13 (100%) |  | HORSEMAN_SLOW×11, HORSEMAN_FAST×13, THE_SWORDMASTER×7, PIKENEER×14, HORSEMAN_FAST×9, LEGIONARY×11, LEGIONARY×11, LEGIONARY×14, CHARIOT×8 |
| 🟩 | Bored Mercenaries | random | Iron Age 88%, Medieval 12% | 🟢 11/13 (85%) | KNIGHT×2 | HORSEMAN_FAST×14, HORSEMAN_SLOW×13, PIKENEER×10, HORSEMAN_FAST×11, KNIGHT×12, PIKENEER×13, LEGIONARY×9, THE_SWORDMASTER×7, PIKENEER×13 |
| 🟩 | Petty Bandits | random | Iron Age 85%, Bronze Age 15% | 🟠 6/13 (46%) | THE_SWORDMASTER×1 | HORSEMAN_FAST×13, PIKENEER×10, LEGIONARY×14, HORSEMAN_FAST×11, LEGIONARY×9, LEGIONARY×11, THE_SWORDMASTER×7, LEGIONARY×13, CHARIOT×15 |
| 🟩 | Angry Mob | random | Iron Age 66%, Bronze Age 34% | 🟢 13/13 (100%) |  | HORSEMAN_SLOW×13, LARGE_CART×12, HORSEMAN_FAST×14, PIKENEER×11, CHARIOT×10, BOWMAN×13, LEGIONARY×13, BOWMAN×14, LEGIONARY×9 |
| 🟥 | Relentless Mob | random | Iron Age 85%, Medieval 15% | ⬛ 0/13 (0%) | CRUSADER×5, SIEGE_RAM×1 | HORSEMAN_SLOW×12, SIEGE_RAM×12, THE_SWORDMASTER×7, HORSEMAN_FAST×13, LARGE_CART×12, PIKENEER×8, PIKENEER×8, LARGE_CART×8 |
| 🟥 | Grumpy Marauders | random | Iron Age 75%, Medieval 25% | ⬛ 0/13 (0%) | SAMURAI×7, SIEGE_RAM×1, CRUSADER×1 | SIEGE_RAM×9, SAMURAI×10, HORSEMAN_SLOW×12, LARGE_CART×12, PIKENEER×13, HORSEMAN_FAST×11, LARGE_CART×8 |
| 🟩 | Blundering Invaders | random | Iron Age 74%, Bronze Age 26% | 🟢 13/13 (100%) |  | PIKENEER×12, PIKENEER×12, HORSEMAN_FAST×14, HORSEMAN_SLOW×12, BOWMAN×9, CHARIOT×13, LARGE_CART×12 |
| 🟩 | Weary Plunderers | random | Bronze Age 51%, Iron Age 49% | 🟠 6/13 (46%) | THE_SWORDMASTER×1 | LARGE_CART×8, LARGE_CART×12, BOWMAN×13, PIKENEER×12, BOWMAN×15, THE_SWORDMASTER×7, CHARIOT×12 |
| 🟥 | Drunken Raiders | random | Bronze Age 41%, Iron Age 32%, Medieval 27% | ⬛ 0/13 (0%) | CONDOTTERI×7 | CHARIOT×14, SWORDMAN×12, LARGE_CART×12, CONDOTTERI×15, HANDGUNNER×10, BOWMAN×11, PIKENEER×8, HORSEMAN_FAST×9 |
| 🟩 | Rampaging Rabble | random | Iron Age 64%, Bronze Age 25%, Medieval 11% | 🟠 4/13 (31%) | KNIGHT×2, THE_SWORDMASTER×1 | SWORDMAN×12, THE_SWORDMASTER×7, LEGIONARY×9, CHARIOT×9, LEGIONARY×14, KNIGHT×9, LEGIONARY×12, HORSEMAN_FAST×11 |
| 🟥 | Drunken Raiders | random | Iron Age 84%, Medieval 16% | ⬛ 0/13 (0%) | CONDOTTERI×7 | LEGIONARY×12, PIKENEER×8, CONDOTTERI×13, THE_SWORDMASTER×7, HORSEMAN_SLOW×12, PIKENEER×14, HORSEMAN_FAST×13 |
| 🟩 | Bored Mercenaries | random | Iron Age 85%, Bronze Age 15% | 🟢 13/13 (100%) |  | HORSEMAN_SLOW×9, HORSEMAN_FAST×11, SWORDMAN×12, PIKENEER×9, THE_SWORDMASTER×7, HORSEMAN_FAST×12, LEGIONARY×13, PIKENEER×8 |
| 🟥 | Unlucky Raiders | random | Iron Age 71%, Medieval 18%, Bronze Age 12% | ⬛ 0/13 (0%) | SAMURAI×8, THE_SWORDMASTER×1 | SAMURAI×15, BOWMAN×10, PIKENEER×15, LEGIONARY×8, THE_SWORDMASTER×7, HORSEMAN_FAST×13, HORSEMAN_SLOW×8, HORSEMAN_FAST×9 |
| 🟩 | Rude Barbarians | random | Iron Age 73%, Bronze Age 14%, Medieval 13% | 🟢 11/13 (85%) | KNIGHT×2 | HORSEMAN_FAST×11, HORSEMAN_SLOW×8, HORSEMAN_FAST×10, LEGIONARY×15, HORSEMAN_SLOW×8, CHARIOT×10, KNIGHT×9 |
| 🟥 | Frenzied Pillagers | random | Iron Age 70%, Medieval 30% | ⬛ 0/13 (0%) | SAMURAI×9, SIEGE_RAM×1 | HORSEMAN_SLOW×11, HORSEMAN_FAST×10, THE_SWORDMASTER×7, LEGIONARY×9, SAMURAI×11, HORSEMAN_FAST×8, PIKENEER×15, SIEGE_RAM×15 |
| 🟥 | Stubborn Raiders | random | Iron Age 88%, Medieval 12% | ⬛ 0/13 (0%) | CONDOTTERI×7 | LARGE_CART×8, LARGE_CART×12, HORSEMAN_FAST×13, LARGE_CART×12, CONDOTTERI×12, PIKENEER×9, LEGIONARY×10, HORSEMAN_SLOW×10, HORSEMAN_SLOW×12 |
| 🟥 | Desperate Looters | random | Iron Age 58%, Bronze Age 28%, Medieval 14% | ⬛ 0/13 (0%) | CONDOTTERI×7 | HORSEMAN_SLOW×9, SWORDMAN×12, BOWMAN×15, CONDOTTERI×14, LEGIONARY×13, LEGIONARY×9, HORSEMAN_SLOW×14, LEGIONARY×11 |
| 🟩 | Grumpy Marauders | random | Iron Age 74%, Bronze Age 15%, Medieval 11% | 🟠 6/13 (46%) | CRUSADER×3, PIKENEER×1 | CRUSADER×9, LEGIONARY×12, LARGE_CART×16, HORSEMAN_SLOW×13, SWORDMAN×12, HORSEMAN_FAST×12, LARGE_CART×8 |

#### S2 Baumhaus

| Tower Era Distribution (22 towers) | Towers |
|---|---|
| Bronze Age 64% (14), Iron Age 36% (8) | ARROW_TOWER×8, CATAPULTS×4, FIRE_TOWER×4, ARBELESTE_TOWER×4, BALLISTA_TOWER×2 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Iron Legion | hardcoded | Iron Age 100% | 🟢 16/16 (100%) |  | HORSEMAN_SLOW×10, HORSEMAN_SLOW×10, LEGIONARY×11, PIKENEER×12, LEGIONARY×15, HORSEMAN_FAST×16, THE_SWORDMASTER×18, LEGIONARY×20, LEGIONARY×22, PIKENEER×24 |
| 🟩 | Cavalry Strike | hardcoded | Iron Age 95%, Medieval 5% | 🟢 14/16 (88%) | KNIGHT×2 | LEGIONARY×14, PIKENEER×15, HORSEMAN_FAST×16, LARGE_CART×17, LEGIONARY×18, KNIGHT×9, PIKENEER×22, LARGE_CART×18, HORSEMAN_SLOW×22, LEGIONARY×26 |
| 🟩 | Legionary March | hardcoded | Iron Age 95%, Medieval 5% | 🟢 16/16 (100%) |  | LEGIONARY×14, HORSEMAN_SLOW×15, PIKENEER×16, HORSEMAN_FAST×17, HORSEMAN_FAST×17, HORSEMAN_SLOW×18, CRUSADER×9, LARGE_CART×20, LEGIONARY×18, THE_SWORDMASTER×26 |
| 🟩 | Iron Tide | hardcoded | Iron Age 94%, Medieval 6% | 🟠 6/16 (38%) | CRUSADER×5 | LEGIONARY×14, HORSEMAN_FAST×15, LARGE_CART×16, HORSEMAN_SLOW×16, LARGE_CART×17, HORSEMAN_FAST×18, LEGIONARY×18, THE_SWORDMASTER×19, CRUSADER×12, THE_SWORDMASTER×26, LEGIONARY×28 |
| 🟩 | Quartermaster Force | hardcoded | Iron Age 100% | 🟢 16/16 (100%) |  | THE_SWORDMASTER×16, LEGIONARY×17, HORSEMAN_SLOW×18, LARGE_CART×19, PIKENEER×20, LARGE_CART×21, LARGE_CART×22, LEGIONARY×16, PIKENEER×18, LARGE_CART×20, HORSEMAN_SLOW×22, HORSEMAN_SLOW×24, LEGIONARY×28 |
| 🟩 | Blundering Invaders | random | Iron Age 90%, Medieval 10% | 🟢 16/16 (100%) |  | SAMURAI×8, LEGIONARY×13, HORSEMAN_SLOW×9, HORSEMAN_FAST×11, THE_SWORDMASTER×7, LARGE_CART×8, PIKENEER×11, HORSEMAN_FAST×15 |
| 🟩 | Blundering Invaders | random | Iron Age 90%, Medieval 10% | 🟢 16/16 (100%) |  | SAMURAI×8, LEGIONARY×13, HORSEMAN_SLOW×9, HORSEMAN_FAST×11, THE_SWORDMASTER×7, LARGE_CART×8, PIKENEER×11, HORSEMAN_FAST×15 |
| 🟩 | Relentless Mob | random | Iron Age 92%, Bronze Age 8% | 🟢 16/16 (100%) |  | HORSEMAN_SLOW×11, HORSEMAN_FAST×13, THE_SWORDMASTER×7, PIKENEER×14, HORSEMAN_FAST×9, LEGIONARY×11, LEGIONARY×11, LEGIONARY×14, CHARIOT×8 |
| 🟩 | Bored Mercenaries | random | Iron Age 88%, Medieval 12% | 🟢 16/16 (100%) |  | HORSEMAN_FAST×14, HORSEMAN_SLOW×13, PIKENEER×10, HORSEMAN_FAST×11, KNIGHT×12, PIKENEER×13, LEGIONARY×9, THE_SWORDMASTER×7, PIKENEER×13 |
| 🟩 | Petty Bandits | random | Iron Age 85%, Bronze Age 15% | 🟢 16/16 (100%) |  | HORSEMAN_FAST×13, PIKENEER×10, LEGIONARY×14, HORSEMAN_FAST×11, LEGIONARY×9, LEGIONARY×11, THE_SWORDMASTER×7, LEGIONARY×13, CHARIOT×15 |
| 🟩 | Angry Mob | random | Iron Age 66%, Bronze Age 34% | 🟢 16/16 (100%) |  | HORSEMAN_SLOW×13, LARGE_CART×12, HORSEMAN_FAST×14, PIKENEER×11, CHARIOT×10, BOWMAN×13, LEGIONARY×13, BOWMAN×14, LEGIONARY×9 |
| 🟥 | Relentless Mob | random | Iron Age 85%, Medieval 15% | ⬛ 0/16 (0%) | CRUSADER×6, SIEGE_RAM×1 | HORSEMAN_SLOW×12, SIEGE_RAM×12, THE_SWORDMASTER×7, HORSEMAN_FAST×13, LARGE_CART×12, PIKENEER×8, PIKENEER×8, LARGE_CART×8 |
| 🟥 | Grumpy Marauders | random | Iron Age 75%, Medieval 25% | ⬛ 0/16 (0%) | CRUSADER×6, SAMURAI×5 | SIEGE_RAM×9, SAMURAI×10, HORSEMAN_SLOW×12, LARGE_CART×12, PIKENEER×13, HORSEMAN_FAST×11, LARGE_CART×8 |
| 🟩 | Blundering Invaders | random | Iron Age 74%, Bronze Age 26% | 🟢 16/16 (100%) |  | PIKENEER×12, PIKENEER×12, HORSEMAN_FAST×14, HORSEMAN_SLOW×12, BOWMAN×9, CHARIOT×13, LARGE_CART×12 |
| 🟩 | Weary Plunderers | random | Bronze Age 51%, Iron Age 49% | 🟢 16/16 (100%) |  | LARGE_CART×8, LARGE_CART×12, BOWMAN×13, PIKENEER×12, BOWMAN×15, THE_SWORDMASTER×7, CHARIOT×12 |
| 🟥 | Drunken Raiders | random | Bronze Age 41%, Iron Age 32%, Medieval 27% | ⬛ 0/16 (0%) | HANDGUNNER×9, CONDOTTERI×4 | CHARIOT×14, SWORDMAN×12, LARGE_CART×12, CONDOTTERI×15, HANDGUNNER×10, BOWMAN×11, PIKENEER×8, HORSEMAN_FAST×9 |
| 🟩 | Rampaging Rabble | random | Iron Age 64%, Bronze Age 25%, Medieval 11% | 🟢 14/16 (88%) | KNIGHT×2 | SWORDMAN×12, THE_SWORDMASTER×7, LEGIONARY×9, CHARIOT×9, LEGIONARY×14, KNIGHT×9, LEGIONARY×12, HORSEMAN_FAST×11 |
| 🟩 | Drunken Raiders | random | Iron Age 84%, Medieval 16% | 🟠 6/16 (38%) | CONDOTTERI×5 | LEGIONARY×12, PIKENEER×8, CONDOTTERI×13, THE_SWORDMASTER×7, HORSEMAN_SLOW×12, PIKENEER×14, HORSEMAN_FAST×13 |
| 🟩 | Bored Mercenaries | random | Iron Age 85%, Bronze Age 15% | 🟢 16/16 (100%) |  | HORSEMAN_SLOW×9, HORSEMAN_FAST×11, SWORDMAN×12, PIKENEER×9, THE_SWORDMASTER×7, HORSEMAN_FAST×12, LEGIONARY×13, PIKENEER×8 |
| 🟩 | Unlucky Raiders | random | Iron Age 71%, Medieval 18%, Bronze Age 12% | 🟡 11/16 (69%) | SAMURAI×5 | SAMURAI×15, BOWMAN×10, PIKENEER×15, LEGIONARY×8, THE_SWORDMASTER×7, HORSEMAN_FAST×13, HORSEMAN_SLOW×8, HORSEMAN_FAST×9 |
| 🟩 | Rude Barbarians | random | Iron Age 73%, Bronze Age 14%, Medieval 13% | 🟢 16/16 (100%) |  | HORSEMAN_FAST×11, HORSEMAN_SLOW×8, HORSEMAN_FAST×10, LEGIONARY×15, HORSEMAN_SLOW×8, CHARIOT×10, KNIGHT×9 |
| 🟥 | Frenzied Pillagers | random | Iron Age 70%, Medieval 30% | ⬛ 0/16 (0%) | CRUSADER×6, SAMURAI×4 | HORSEMAN_SLOW×11, HORSEMAN_FAST×10, THE_SWORDMASTER×7, LEGIONARY×9, SAMURAI×11, HORSEMAN_FAST×8, PIKENEER×15, SIEGE_RAM×15 |
| 🟩 | Stubborn Raiders | random | Iron Age 88%, Medieval 12% | 🟡 8/16 (50%) | CONDOTTERI×4 | LARGE_CART×8, LARGE_CART×12, HORSEMAN_FAST×13, LARGE_CART×12, CONDOTTERI×12, PIKENEER×9, LEGIONARY×10, HORSEMAN_SLOW×10, HORSEMAN_SLOW×12 |
| 🟩 | Desperate Looters | random | Iron Age 58%, Bronze Age 28%, Medieval 14% | 🔴 2/16 (12%) | CONDOTTERI×7 | HORSEMAN_SLOW×9, SWORDMAN×12, BOWMAN×15, CONDOTTERI×14, LEGIONARY×13, LEGIONARY×9, HORSEMAN_SLOW×14, LEGIONARY×11 |
| 🟩 | Grumpy Marauders | random | Iron Age 74%, Bronze Age 15%, Medieval 11% | 🟢 16/16 (100%) |  | CRUSADER×9, LEGIONARY×12, LARGE_CART×16, HORSEMAN_SLOW×13, SWORDMAN×12, HORSEMAN_FAST×12, LARGE_CART×8 |

#### Only Arbaleste

| Tower Era Distribution (33 towers) | Towers |
|---|---|
| Iron Age 100% (33) | ARBELESTE_TOWER×33 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Iron Legion | hardcoded | Iron Age 100% | 🟢 16/16 (100%) |  | HORSEMAN_SLOW×10, HORSEMAN_SLOW×10, LEGIONARY×11, PIKENEER×12, LEGIONARY×15, HORSEMAN_FAST×16, THE_SWORDMASTER×18, LEGIONARY×20, LEGIONARY×22, PIKENEER×24 |
| 🟩 | Cavalry Strike | hardcoded | Iron Age 95%, Medieval 5% | 🟢 16/16 (100%) |  | LEGIONARY×14, PIKENEER×15, HORSEMAN_FAST×16, LARGE_CART×17, LEGIONARY×18, KNIGHT×9, PIKENEER×22, LARGE_CART×18, HORSEMAN_SLOW×22, LEGIONARY×26 |
| 🟩 | Legionary March | hardcoded | Iron Age 95%, Medieval 5% | 🟢 16/16 (100%) |  | LEGIONARY×14, HORSEMAN_SLOW×15, PIKENEER×16, HORSEMAN_FAST×17, HORSEMAN_FAST×17, HORSEMAN_SLOW×18, CRUSADER×9, LARGE_CART×20, LEGIONARY×18, THE_SWORDMASTER×26 |
| 🟩 | Iron Tide | hardcoded | Iron Age 94%, Medieval 6% | 🟢 16/16 (100%) |  | LEGIONARY×14, HORSEMAN_FAST×15, LARGE_CART×16, HORSEMAN_SLOW×16, LARGE_CART×17, HORSEMAN_FAST×18, LEGIONARY×18, THE_SWORDMASTER×19, CRUSADER×12, THE_SWORDMASTER×26, LEGIONARY×28 |
| 🟩 | Quartermaster Force | hardcoded | Iron Age 100% | 🟢 16/16 (100%) |  | THE_SWORDMASTER×16, LEGIONARY×17, HORSEMAN_SLOW×18, LARGE_CART×19, PIKENEER×20, LARGE_CART×21, LARGE_CART×22, LEGIONARY×16, PIKENEER×18, LARGE_CART×20, HORSEMAN_SLOW×22, HORSEMAN_SLOW×24, LEGIONARY×28 |
| 🟩 | Blundering Invaders | random | Iron Age 90%, Medieval 10% | 🟢 16/16 (100%) |  | SAMURAI×8, LEGIONARY×13, HORSEMAN_SLOW×9, HORSEMAN_FAST×11, THE_SWORDMASTER×7, LARGE_CART×8, PIKENEER×11, HORSEMAN_FAST×15 |
| 🟩 | Blundering Invaders | random | Iron Age 90%, Medieval 10% | 🟢 16/16 (100%) |  | SAMURAI×8, LEGIONARY×13, HORSEMAN_SLOW×9, HORSEMAN_FAST×11, THE_SWORDMASTER×7, LARGE_CART×8, PIKENEER×11, HORSEMAN_FAST×15 |
| 🟩 | Relentless Mob | random | Iron Age 92%, Bronze Age 8% | 🟢 16/16 (100%) |  | HORSEMAN_SLOW×11, HORSEMAN_FAST×13, THE_SWORDMASTER×7, PIKENEER×14, HORSEMAN_FAST×9, LEGIONARY×11, LEGIONARY×11, LEGIONARY×14, CHARIOT×8 |
| 🟩 | Bored Mercenaries | random | Iron Age 88%, Medieval 12% | 🟢 16/16 (100%) |  | HORSEMAN_FAST×14, HORSEMAN_SLOW×13, PIKENEER×10, HORSEMAN_FAST×11, KNIGHT×12, PIKENEER×13, LEGIONARY×9, THE_SWORDMASTER×7, PIKENEER×13 |
| 🟩 | Petty Bandits | random | Iron Age 85%, Bronze Age 15% | 🟢 16/16 (100%) |  | HORSEMAN_FAST×13, PIKENEER×10, LEGIONARY×14, HORSEMAN_FAST×11, LEGIONARY×9, LEGIONARY×11, THE_SWORDMASTER×7, LEGIONARY×13, CHARIOT×15 |
| 🟩 | Angry Mob | random | Iron Age 66%, Bronze Age 34% | 🟢 16/16 (100%) |  | HORSEMAN_SLOW×13, LARGE_CART×12, HORSEMAN_FAST×14, PIKENEER×11, CHARIOT×10, BOWMAN×13, LEGIONARY×13, BOWMAN×14, LEGIONARY×9 |
| 🟩 | Relentless Mob | random | Iron Age 85%, Medieval 15% | 🟢 16/16 (100%) |  | HORSEMAN_SLOW×12, SIEGE_RAM×12, THE_SWORDMASTER×7, HORSEMAN_FAST×13, LARGE_CART×12, PIKENEER×8, PIKENEER×8, LARGE_CART×8 |
| 🟩 | Grumpy Marauders | random | Iron Age 75%, Medieval 25% | 🟢 16/16 (100%) |  | SIEGE_RAM×9, SAMURAI×10, HORSEMAN_SLOW×12, LARGE_CART×12, PIKENEER×13, HORSEMAN_FAST×11, LARGE_CART×8 |
| 🟩 | Blundering Invaders | random | Iron Age 74%, Bronze Age 26% | 🟢 16/16 (100%) |  | PIKENEER×12, PIKENEER×12, HORSEMAN_FAST×14, HORSEMAN_SLOW×12, BOWMAN×9, CHARIOT×13, LARGE_CART×12 |
| 🟩 | Weary Plunderers | random | Bronze Age 51%, Iron Age 49% | 🟢 16/16 (100%) |  | LARGE_CART×8, LARGE_CART×12, BOWMAN×13, PIKENEER×12, BOWMAN×15, THE_SWORDMASTER×7, CHARIOT×12 |
| 🟩 | Drunken Raiders | random | Bronze Age 41%, Iron Age 32%, Medieval 27% | 🟢 13/16 (81%) | CONDOTTERI×1, HANDGUNNER×1 | CHARIOT×14, SWORDMAN×12, LARGE_CART×12, CONDOTTERI×15, HANDGUNNER×10, BOWMAN×11, PIKENEER×8, HORSEMAN_FAST×9 |
| 🟩 | Rampaging Rabble | random | Iron Age 64%, Bronze Age 25%, Medieval 11% | 🟢 16/16 (100%) |  | SWORDMAN×12, THE_SWORDMASTER×7, LEGIONARY×9, CHARIOT×9, LEGIONARY×14, KNIGHT×9, LEGIONARY×12, HORSEMAN_FAST×11 |
| 🟩 | Drunken Raiders | random | Iron Age 84%, Medieval 16% | 🟢 16/16 (100%) |  | LEGIONARY×12, PIKENEER×8, CONDOTTERI×13, THE_SWORDMASTER×7, HORSEMAN_SLOW×12, PIKENEER×14, HORSEMAN_FAST×13 |
| 🟩 | Bored Mercenaries | random | Iron Age 85%, Bronze Age 15% | 🟢 16/16 (100%) |  | HORSEMAN_SLOW×9, HORSEMAN_FAST×11, SWORDMAN×12, PIKENEER×9, THE_SWORDMASTER×7, HORSEMAN_FAST×12, LEGIONARY×13, PIKENEER×8 |
| 🟩 | Unlucky Raiders | random | Iron Age 71%, Medieval 18%, Bronze Age 12% | 🟢 16/16 (100%) |  | SAMURAI×15, BOWMAN×10, PIKENEER×15, LEGIONARY×8, THE_SWORDMASTER×7, HORSEMAN_FAST×13, HORSEMAN_SLOW×8, HORSEMAN_FAST×9 |
| 🟩 | Rude Barbarians | random | Iron Age 73%, Bronze Age 14%, Medieval 13% | 🟢 16/16 (100%) |  | HORSEMAN_FAST×11, HORSEMAN_SLOW×8, HORSEMAN_FAST×10, LEGIONARY×15, HORSEMAN_SLOW×8, CHARIOT×10, KNIGHT×9 |
| 🟩 | Frenzied Pillagers | random | Iron Age 70%, Medieval 30% | 🟢 16/16 (100%) |  | HORSEMAN_SLOW×11, HORSEMAN_FAST×10, THE_SWORDMASTER×7, LEGIONARY×9, SAMURAI×11, HORSEMAN_FAST×8, PIKENEER×15, SIEGE_RAM×15 |
| 🟩 | Stubborn Raiders | random | Iron Age 88%, Medieval 12% | 🟢 16/16 (100%) |  | LARGE_CART×8, LARGE_CART×12, HORSEMAN_FAST×13, LARGE_CART×12, CONDOTTERI×12, PIKENEER×9, LEGIONARY×10, HORSEMAN_SLOW×10, HORSEMAN_SLOW×12 |
| 🟩 | Desperate Looters | random | Iron Age 58%, Bronze Age 28%, Medieval 14% | 🟢 16/16 (100%) |  | HORSEMAN_SLOW×9, SWORDMAN×12, BOWMAN×15, CONDOTTERI×14, LEGIONARY×13, LEGIONARY×9, HORSEMAN_SLOW×14, LEGIONARY×11 |
| 🟩 | Grumpy Marauders | random | Iron Age 74%, Bronze Age 15%, Medieval 11% | 🟢 16/16 (100%) |  | CRUSADER×9, LEGIONARY×12, LARGE_CART×16, HORSEMAN_SLOW×13, SWORDMAN×12, HORSEMAN_FAST×12, LARGE_CART×8 |

### Medieval

#### Early

| Tower Era Distribution (18 towers) | Towers |
|---|---|
| Medieval 61% (11), Bronze Age 22% (4), Iron Age 17% (3) | HEAVY_TOWER×5, TAR_TOWER×3, BOILING_OIL×3, FIRE_TOWER×2, BALLISTA_TOWER×2, ARBELESTE_TOWER×2, CATAPULTS×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟥 | Medieval Siege | hardcoded | Medieval 96%, Renaissance 4% | ⬛ 0/13 (0%) | NINJA×4, CRUSADER×3 | CRUSADER×12, CONDOTTERI×13, KNIGHT×14, SAMURAI×15, SIEGE_RAM×15, KNIGHT×16, CONDOTTERI×17, CRUSADER×18, NINJA×11, SIEGE_RAM×20, HANDGUNNER×22, HANDGUNNER×24, HANDGUNNER×26, SAMURAI×28 |
| 🟥 | Knights' Charge | hardcoded | Medieval 91%, Renaissance 9% | ⬛ 0/13 (0%) | CRUSADER×4, SIEGE_RAM×1, SAMURAI×1 | CRUSADER×16, SIEGE_RAM×17, CRUSADER×18, SIEGE_RAM×19, SAMURAI×20, KNIGHT×21, SAMURAI×22, CRUSADER×16, SAMURAI×18, KNIGHT×20, KNIGHT×22, CRUSADER×24, KNIGHT×26, KNIGHT×28, NINJA×30 |
| 🟥 | Crusader Host | hardcoded | Medieval 90%, Iron Age 10% | ⬛ 0/13 (0%) | CRUSADER×4, SIEGE_RAM×1, SAMURAI×1 | CRUSADER×16, SIEGE_RAM×17, SAMURAI×18, SIEGE_RAM×19, SIEGE_RAM×20, SAMURAI×21, CRUSADER×22, KNIGHT×16, KNIGHT×18, CRUSADER×20, CRUSADER×22, HANDGUNNER×24, CONDOTTERI×26, SAMURAI×28, LARGE_CART×31 |
| 🟥 | Castle Assault | hardcoded | Medieval 83%, Iron Age 17% | ⬛ 0/13 (0%) | SAMURAI×9, CRUSADER×2 | SAMURAI×16, KNIGHT×17, KNIGHT×18, KNIGHT×19, CRUSADER×20, CRUSADER×21, SIEGE_RAM×22, SAMURAI×16, CRUSADER×18, CRUSADER×20, CRUSADER×22, SAMURAI×24, SIEGE_RAM×26, LEGIONARY×28, SAMURAI×32, HORSEMAN_FAST×32 |
| 🟥 | Feudal Army | hardcoded | Medieval 91%, Iron Age 9% | ⬛ 0/13 (0%) | CRUSADER×7 | KNIGHT×16, SIEGE_RAM×17, KNIGHT×18, SIEGE_RAM×19, CRUSADER×20, CRUSADER×21, CONDOTTERI×22, HANDGUNNER×16, CRUSADER×18, SIEGE_RAM×20, SIEGE_RAM×22, CRUSADER×24, KNIGHT×26, CONDOTTERI×28, LARGE_CART×32, CRUSADER×31 |
| 🟥 | Holy Crusade | hardcoded | Medieval 71%, Iron Age 26%, Renaissance 4% | ⬛ 0/13 (0%) | HANDGUNNER×8, CONDOTTERI×3 | SAMURAI×16, CONDOTTERI×17, HANDGUNNER×17, KNIGHT×18, THE_SWORDMASTER×19, CONDOTTERI×19, CONDOTTERI×20, HANDGUNNER×21, KNIGHT×21, LARGE_CART×22, LEGIONARY×23, MUSKETEER×12, THE_SWORDMASTER×24, SIEGE_RAM×28, HANDGUNNER×31, CRUSADER×34 |
| 🟥 | Desperate Looters | random | Medieval 93%, Renaissance 7% | ⬛ 0/13 (0%) | CONDOTTERI×2, THE_KING×1 | THE_KING×10, CONDOTTERI×13, CRUSADER×14, CONDOTTERI×14, CRUSADER×14, KNIGHT×15, SAMURAI×13, SAMURAI×12, HANDGUNNER×14, HANDGUNNER×18 |
| 🟥 | Desperate Looters | random | Medieval 93%, Renaissance 7% | ⬛ 0/13 (0%) | CONDOTTERI×2, THE_KING×1 | THE_KING×10, CONDOTTERI×13, CRUSADER×14, CONDOTTERI×14, CRUSADER×14, KNIGHT×15, SAMURAI×13, SAMURAI×12, HANDGUNNER×14, HANDGUNNER×18 |
| 🟥 | Lazy Raiders | random | Medieval 92%, Iron Age 8% | ⬛ 0/13 (0%) | SAMURAI×8, CRUSADER×2, HANDGUNNER×1 | SAMURAI×16, HANDGUNNER×15, PIKENEER×12, CRUSADER×17, KNIGHT×15, CRUSADER×16, CRUSADER×17, SAMURAI×18, SIEGE_RAM×18, SIEGE_RAM×15 |
| 🟥 | Reckless Looters | random | Medieval 90%, Renaissance 10% | ⬛ 0/13 (0%) | MUSKETEER×4, CRUSADER×2, SAMURAI×1, CARGO×1 | SAMURAI×14, SIEGE_RAM×12, CARGO×15, SAMURAI×17, CONDOTTERI×15, CRUSADER×16, HANDGUNNER×13, CRUSADER×13, CONDOTTERI×13, CRUSADER×16 |
| 🟥 | Bored Mercenaries | random | Medieval 92%, Iron Age 8% | ⬛ 0/13 (0%) | SAMURAI×4, CRUSADER×4, CONDOTTERI×1 | SAMURAI×16, SIEGE_RAM×12, CONDOTTERI×14, SAMURAI×16, SAMURAI×13, HANDGUNNER×15, CRUSADER×13, LARGE_CART×12, CONDOTTERI×16, HANDGUNNER×15, HANDGUNNER×18 |
| 🟥 | Bored Mercenaries | random | Medieval 70%, Iron Age 30% | ⬛ 0/13 (0%) | CRUSADER×7 | CONDOTTERI×16, KNIGHT×18, LARGE_CART×12, HORSEMAN_SLOW×16, SIEGE_RAM×15, CRUSADER×14, KNIGHT×15, SIEGE_RAM×12, PIKENEER×17, SAMURAI×17 |
| 🟥 | Hungry Invaders | random | Medieval 92%, Renaissance 8% | ⬛ 0/13 (0%) | SAMURAI×6, HANDGUNNER×2, CONDOTTERI×2, MUSKETEER×1 | HANDGUNNER×18, CRUSADER×11, KNIGHT×15, KNIGHT×18, CONDOTTERI×15, CRUSADER×14, SAMURAI×11, KNIGHT×18, SAMURAI×14, CARGO×12 |
| 🟥 | Crude Invaders | random | Medieval 77%, Renaissance 23% | ⬛ 0/13 (0%) | SAMURAI×6, CONDOTTERI×2, CRUSADER×2 | NINJA×13, KNIGHT×15, CONDOTTERI×13, CRUSADER×16, CONDOTTERI×15, SIEGE_RAM×12, SAMURAI×14, MUSKETEER×13 |
| 🟩 | Petty Bandits | random | Medieval 82%, Iron Age 18% | 🟠 3/13 (23%) | CONDOTTERI×3, SAMURAI×2, CRUSADER×1 | LEGIONARY×12, THE_SWORDMASTER×7, CRUSADER×15, KNIGHT×12, KNIGHT×15, CRUSADER×15, CONDOTTERI×15, SAMURAI×17 |
| 🟥 | Restless Horde | random | Medieval 65%, Iron Age 35% | ⬛ 0/13 (0%) | CRUSADER×3, CONDOTTERI×1, SIEGE_RAM×1, HANDGUNNER×1 | LEGIONARY×14, CONDOTTERI×13, CONDOTTERI×16, SIEGE_RAM×15, HANDGUNNER×12, THE_SWORDMASTER×7, HORSEMAN_SLOW×16, SIEGE_RAM×12 |
| 🟥 | Angry Mob | random | Medieval 51%, Iron Age 28%, Renaissance 21% | ⬛ 0/13 (0%) | MUSKETEER×10, HANDGUNNER×3 | CARGO×12, HANDGUNNER×17, SAMURAI×12, CONDOTTERI×14, MUSKETEER×16, THE_SWORDMASTER×7, HORSEMAN_SLOW×17, CRUSADER×11, CRUSADER×14, HORSEMAN_FAST×14 |
| 🟥 | Lazy Raiders | random | Medieval 72%, Iron Age 21%, Renaissance 7% | ⬛ 0/13 (0%) | CRUSADER×7 | SIEGE_RAM×15, SIEGE_RAM×18, CRUSADER×12, SIEGE_RAM×12, HORSEMAN_SLOW×14, HANDGUNNER×14, HORSEMAN_FAST×15, SAMURAI×14, THE_KING×10, CONDOTTERI×16 |
| 🟥 | Clumsy Attackers | random | Medieval 90%, Renaissance 10% | ⬛ 0/13 (0%) | CRUSADER×5, SIEGE_RAM×1 | SIEGE_RAM×15, SIEGE_RAM×15, HANDGUNNER×13, SIEGE_RAM×15, HANDGUNNER×12, CRUSADER×16, CONDOTTERI×18, CONDOTTERI×11, NINJA×13 |
| 🟥 | Restless Horde | random | Medieval 91%, Iron Age 9% | ⬛ 0/13 (0%) | CRUSADER×7 | SAMURAI×15, CRUSADER×15, SIEGE_RAM×12, CONDOTTERI×13, SIEGE_RAM×15, LEGIONARY×13, CRUSADER×11, HANDGUNNER×16, SAMURAI×15, CRUSADER×12 |
| 🟥 | Lazy Raiders | random | Medieval 82%, Renaissance 13%, Iron Age 6% | ⬛ 0/13 (0%) | CRUSADER×3, HANDGUNNER×3, NINJA×2 | SAMURAI×16, THE_SWORDMASTER×7, SAMURAI×12, CRUSADER×16, HANDGUNNER×14, CRUSADER×12, NINJA×16, SAMURAI×14, CRUSADER×18 |
| 🟥 | Forgotten Warband | random | Medieval 73%, Renaissance 16%, Iron Age 11% | ⬛ 0/13 (0%) | SAMURAI×2, CARGO×2, MUSKETEER×2, SIEGE_RAM×1 | KNIGHT×12, SAMURAI×14, SIEGE_RAM×18, CONDOTTERI×13, CARGO×18, SAMURAI×13, KNIGHT×12, HORSEMAN_SLOW×12 |
| 🟥 | Grumpy Marauders | random | Medieval 83%, Renaissance 17% | ⬛ 0/13 (0%) | SAMURAI×7, CRUSADER×1, THE_KING×1 | SIEGE_RAM×12, CRUSADER×18, SAMURAI×15, SAMURAI×13, THE_KING×10, CRUSADER×13, SAMURAI×17, HANDGUNNER×14, DRAGOONER×13, HANDGUNNER×13 |
| 🟥 | Hungry Invaders | random | Medieval 89%, Renaissance 11% | ⬛ 0/13 (0%) | CRUSADER×3, DRAGOONER×2, KNIGHT×2, CONDOTTERI×1 | CONDOTTERI×17, SAMURAI×16, KNIGHT×15, DRAGOONER×15, SIEGE_RAM×12, CONDOTTERI×13, CONDOTTERI×13, CONDOTTERI×15, CRUSADER×12, KNIGHT×12 |
| 🟥 | Clumsy Attackers | random | Medieval 65%, Iron Age 26%, Renaissance 9% | ⬛ 0/13 (0%) | CRUSADER×7 | KNIGHT×12, SAMURAI×15, SIEGE_RAM×12, KNIGHT×18, SIEGE_RAM×15, LARGE_CART×16, MUSKETEER×12, SIEGE_RAM×15, PIKENEER×18 |
| 🟥 | Grumpy Marauders | random | Medieval 76%, Renaissance 14%, Iron Age 10% | ⬛ 0/13 (0%) | MUSKETEER×5, CRUSADER×4 | SIEGE_RAM×15, MUSKETEER×16, SAMURAI×15, SAMURAI×15, CONDOTTERI×18, KNIGHT×15, CONDOTTERI×12, PIKENEER×12 |

#### Mixed Early

| Tower Era Distribution (27 towers) | Towers |
|---|---|
| Medieval 48% (13), Iron Age 22% (6), Bronze Age 22% (6), Neolithic 7% (2) | TAR_TOWER×7, HEAVY_TOWER×6, CATAPULTS×4, BALLISTA_TOWER×3, DOUBLE_SLING_TOWER×2, ARBELESTE_TOWER×2, ARROW_TOWER×2, FIRE_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟥 | Medieval Siege | hardcoded | Medieval 96%, Renaissance 4% | ⬛ 0/16 (0%) | SAMURAI×6, CRUSADER×3, KNIGHT×3, CONDOTTERI×1 | CRUSADER×12, CONDOTTERI×13, KNIGHT×14, SAMURAI×15, SIEGE_RAM×15, KNIGHT×16, CONDOTTERI×17, CRUSADER×18, NINJA×11, SIEGE_RAM×20, HANDGUNNER×22, HANDGUNNER×24, HANDGUNNER×26, SAMURAI×28 |
| 🟥 | Knights' Charge | hardcoded | Medieval 91%, Renaissance 9% | ⬛ 0/16 (0%) | CRUSADER×6, SIEGE_RAM×1 | CRUSADER×16, SIEGE_RAM×17, CRUSADER×18, SIEGE_RAM×19, SAMURAI×20, KNIGHT×21, SAMURAI×22, CRUSADER×16, SAMURAI×18, KNIGHT×20, KNIGHT×22, CRUSADER×24, KNIGHT×26, KNIGHT×28, NINJA×30 |
| 🟥 | Crusader Host | hardcoded | Medieval 90%, Iron Age 10% | ⬛ 0/16 (0%) | SAMURAI×8, CRUSADER×4 | CRUSADER×16, SIEGE_RAM×17, SAMURAI×18, SIEGE_RAM×19, SIEGE_RAM×20, SAMURAI×21, CRUSADER×22, KNIGHT×16, KNIGHT×18, CRUSADER×20, CRUSADER×22, HANDGUNNER×24, CONDOTTERI×26, SAMURAI×28, LARGE_CART×31 |
| 🟥 | Castle Assault | hardcoded | Medieval 83%, Iron Age 17% | ⬛ 0/16 (0%) | KNIGHT×7, CRUSADER×5 | SAMURAI×16, KNIGHT×17, KNIGHT×18, KNIGHT×19, CRUSADER×20, CRUSADER×21, SIEGE_RAM×22, SAMURAI×16, CRUSADER×18, CRUSADER×20, CRUSADER×22, SAMURAI×24, SIEGE_RAM×26, LEGIONARY×28, SAMURAI×32, HORSEMAN_FAST×32 |
| 🟥 | Feudal Army | hardcoded | Medieval 91%, Iron Age 9% | ⬛ 0/16 (0%) | CRUSADER×5, KNIGHT×3, SIEGE_RAM×1 | KNIGHT×16, SIEGE_RAM×17, KNIGHT×18, SIEGE_RAM×19, CRUSADER×20, CRUSADER×21, CONDOTTERI×22, HANDGUNNER×16, CRUSADER×18, SIEGE_RAM×20, SIEGE_RAM×22, CRUSADER×24, KNIGHT×26, CONDOTTERI×28, LARGE_CART×32, CRUSADER×31 |
| 🟥 | Holy Crusade | hardcoded | Medieval 71%, Iron Age 26%, Renaissance 4% | ⬛ 0/16 (0%) | HANDGUNNER×6, CONDOTTERI×5 | SAMURAI×16, CONDOTTERI×17, HANDGUNNER×17, KNIGHT×18, THE_SWORDMASTER×19, CONDOTTERI×19, CONDOTTERI×20, HANDGUNNER×21, KNIGHT×21, LARGE_CART×22, LEGIONARY×23, MUSKETEER×12, THE_SWORDMASTER×24, SIEGE_RAM×28, HANDGUNNER×31, CRUSADER×34 |
| 🟥 | Desperate Looters | random | Medieval 93%, Renaissance 7% | ⬛ 0/16 (0%) | CRUSADER×2, CONDOTTERI×1, THE_KING×1 | THE_KING×10, CONDOTTERI×13, CRUSADER×14, CONDOTTERI×14, CRUSADER×14, KNIGHT×15, SAMURAI×13, SAMURAI×12, HANDGUNNER×14, HANDGUNNER×18 |
| 🟥 | Desperate Looters | random | Medieval 93%, Renaissance 7% | ⬛ 0/16 (0%) | CRUSADER×2, CONDOTTERI×1, THE_KING×1 | THE_KING×10, CONDOTTERI×13, CRUSADER×14, CONDOTTERI×14, CRUSADER×14, KNIGHT×15, SAMURAI×13, SAMURAI×12, HANDGUNNER×14, HANDGUNNER×18 |
| 🟥 | Lazy Raiders | random | Medieval 92%, Iron Age 8% | ⬛ 0/16 (0%) | SAMURAI×6, CRUSADER×3, KNIGHT×3, HANDGUNNER×1 | SAMURAI×16, HANDGUNNER×15, PIKENEER×12, CRUSADER×17, KNIGHT×15, CRUSADER×16, CRUSADER×17, SAMURAI×18, SIEGE_RAM×18, SIEGE_RAM×15 |
| 🟥 | Reckless Looters | random | Medieval 90%, Renaissance 10% | ⬛ 0/16 (0%) | CRUSADER×4, MUSKETEER×3, SAMURAI×1, CARGO×1 | SAMURAI×14, SIEGE_RAM×12, CARGO×15, SAMURAI×17, CONDOTTERI×15, CRUSADER×16, HANDGUNNER×13, CRUSADER×13, CONDOTTERI×13, CRUSADER×16 |
| 🟥 | Bored Mercenaries | random | Medieval 92%, Iron Age 8% | ⬛ 0/16 (0%) | SAMURAI×10, CRUSADER×2, CONDOTTERI×1 | SAMURAI×16, SIEGE_RAM×12, CONDOTTERI×14, SAMURAI×16, SAMURAI×13, HANDGUNNER×15, CRUSADER×13, LARGE_CART×12, CONDOTTERI×16, HANDGUNNER×15, HANDGUNNER×18 |
| 🟥 | Bored Mercenaries | random | Medieval 70%, Iron Age 30% | ⬛ 0/16 (0%) | CRUSADER×7, KNIGHT×3 | CONDOTTERI×16, KNIGHT×18, LARGE_CART×12, HORSEMAN_SLOW×16, SIEGE_RAM×15, CRUSADER×14, KNIGHT×15, SIEGE_RAM×12, PIKENEER×17, SAMURAI×17 |
| 🟥 | Hungry Invaders | random | Medieval 92%, Renaissance 8% | ⬛ 0/16 (0%) | HANDGUNNER×5, KNIGHT×5, CONDOTTERI×3 | HANDGUNNER×18, CRUSADER×11, KNIGHT×15, KNIGHT×18, CONDOTTERI×15, CRUSADER×14, SAMURAI×11, KNIGHT×18, SAMURAI×14, CARGO×12 |
| 🟥 | Crude Invaders | random | Medieval 77%, Renaissance 23% | ⬛ 0/16 (0%) | NINJA×4, CONDOTTERI×4 | NINJA×13, KNIGHT×15, CONDOTTERI×13, CRUSADER×16, CONDOTTERI×15, SIEGE_RAM×12, SAMURAI×14, MUSKETEER×13 |
| 🟥 | Petty Bandits | random | Medieval 82%, Iron Age 18% | ⬛ 0/16 (0%) | SAMURAI×5, KNIGHT×3, CRUSADER×2, CONDOTTERI×2 | LEGIONARY×12, THE_SWORDMASTER×7, CRUSADER×15, KNIGHT×12, KNIGHT×15, CRUSADER×15, CONDOTTERI×15, SAMURAI×17 |
| 🟥 | Restless Horde | random | Medieval 65%, Iron Age 35% | ⬛ 0/16 (0%) | CONDOTTERI×6, SIEGE_RAM×1, CRUSADER×1 | LEGIONARY×14, CONDOTTERI×13, CONDOTTERI×16, SIEGE_RAM×15, HANDGUNNER×12, THE_SWORDMASTER×7, HORSEMAN_SLOW×16, SIEGE_RAM×12 |
| 🟥 | Angry Mob | random | Medieval 51%, Iron Age 28%, Renaissance 21% | ⬛ 0/16 (0%) | HANDGUNNER×9, MUSKETEER×4, SAMURAI×3 | CARGO×12, HANDGUNNER×17, SAMURAI×12, CONDOTTERI×14, MUSKETEER×16, THE_SWORDMASTER×7, HORSEMAN_SLOW×17, CRUSADER×11, CRUSADER×14, HORSEMAN_FAST×14 |
| 🟥 | Lazy Raiders | random | Medieval 72%, Iron Age 21%, Renaissance 7% | ⬛ 0/16 (0%) | CRUSADER×8 | SIEGE_RAM×15, SIEGE_RAM×18, CRUSADER×12, SIEGE_RAM×12, HORSEMAN_SLOW×14, HANDGUNNER×14, HORSEMAN_FAST×15, SAMURAI×14, THE_KING×10, CONDOTTERI×16 |
| 🟥 | Clumsy Attackers | random | Medieval 90%, Renaissance 10% | ⬛ 0/16 (0%) | CRUSADER×8 | SIEGE_RAM×15, SIEGE_RAM×15, HANDGUNNER×13, SIEGE_RAM×15, HANDGUNNER×12, CRUSADER×16, CONDOTTERI×18, CONDOTTERI×11, NINJA×13 |
| 🟥 | Restless Horde | random | Medieval 91%, Iron Age 9% | ⬛ 0/16 (0%) | CRUSADER×8 | SAMURAI×15, CRUSADER×15, SIEGE_RAM×12, CONDOTTERI×13, SIEGE_RAM×15, LEGIONARY×13, CRUSADER×11, HANDGUNNER×16, SAMURAI×15, CRUSADER×12 |
| 🟥 | Lazy Raiders | random | Medieval 82%, Renaissance 13%, Iron Age 6% | ⬛ 0/16 (0%) | CRUSADER×5, HANDGUNNER×5, SAMURAI×1 | SAMURAI×16, THE_SWORDMASTER×7, SAMURAI×12, CRUSADER×16, HANDGUNNER×14, CRUSADER×12, NINJA×16, SAMURAI×14, CRUSADER×18 |
| 🟥 | Forgotten Warband | random | Medieval 73%, Renaissance 16%, Iron Age 11% | ⬛ 0/16 (0%) | CRUSADER×7, SAMURAI×1, KNIGHT×1 | KNIGHT×12, SAMURAI×14, SIEGE_RAM×18, CONDOTTERI×13, CARGO×18, SAMURAI×13, KNIGHT×12, HORSEMAN_SLOW×12 |
| 🟥 | Grumpy Marauders | random | Medieval 83%, Renaissance 17% | ⬛ 0/16 (0%) | SAMURAI×8, CRUSADER×4 | SIEGE_RAM×12, CRUSADER×18, SAMURAI×15, SAMURAI×13, THE_KING×10, CRUSADER×13, SAMURAI×17, HANDGUNNER×14, DRAGOONER×13, HANDGUNNER×13 |
| 🟥 | Hungry Invaders | random | Medieval 89%, Renaissance 11% | ⬛ 0/16 (0%) | SAMURAI×8, CONDOTTERI×4 | CONDOTTERI×17, SAMURAI×16, KNIGHT×15, DRAGOONER×15, SIEGE_RAM×12, CONDOTTERI×13, CONDOTTERI×13, CONDOTTERI×15, CRUSADER×12, KNIGHT×12 |
| 🟥 | Clumsy Attackers | random | Medieval 65%, Iron Age 26%, Renaissance 9% | ⬛ 0/16 (0%) | CRUSADER×6, SAMURAI×2, KNIGHT×2 | KNIGHT×12, SAMURAI×15, SIEGE_RAM×12, KNIGHT×18, SIEGE_RAM×15, LARGE_CART×16, MUSKETEER×12, SIEGE_RAM×15, PIKENEER×18 |
| 🟥 | Grumpy Marauders | random | Medieval 76%, Renaissance 14%, Iron Age 10% | ⬛ 0/16 (0%) | CRUSADER×5, MUSKETEER×5, SAMURAI×1 | SIEGE_RAM×15, MUSKETEER×16, SAMURAI×15, SAMURAI×15, CONDOTTERI×18, KNIGHT×15, CONDOTTERI×12, PIKENEER×12 |

#### Full Heavy

| Tower Era Distribution (32 towers) | Towers |
|---|---|
| Medieval 100% (32) | HEAVY_TOWER×29, BOILING_OIL×2, TAR_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Medieval Siege | hardcoded | Medieval 96%, Renaissance 4% | 🟢 23/23 (100%) |  | CRUSADER×12, CONDOTTERI×13, KNIGHT×14, SAMURAI×15, SIEGE_RAM×15, KNIGHT×16, CONDOTTERI×17, CRUSADER×18, NINJA×11, SIEGE_RAM×20, HANDGUNNER×22, HANDGUNNER×24, HANDGUNNER×26, SAMURAI×28 |
| 🟩 | Knights' Charge | hardcoded | Medieval 91%, Renaissance 9% | 🟢 19/23 (83%) | CRUSADER×2 | CRUSADER×16, SIEGE_RAM×17, CRUSADER×18, SIEGE_RAM×19, SAMURAI×20, KNIGHT×21, SAMURAI×22, CRUSADER×16, SAMURAI×18, KNIGHT×20, KNIGHT×22, CRUSADER×24, KNIGHT×26, KNIGHT×28, NINJA×30 |
| 🟩 | Crusader Host | hardcoded | Medieval 90%, Iron Age 10% | 🟡 18/23 (78%) | CRUSADER×2, HANDGUNNER×1 | CRUSADER×16, SIEGE_RAM×17, SAMURAI×18, SIEGE_RAM×19, SIEGE_RAM×20, SAMURAI×21, CRUSADER×22, KNIGHT×16, KNIGHT×18, CRUSADER×20, CRUSADER×22, HANDGUNNER×24, CONDOTTERI×26, SAMURAI×28, LARGE_CART×31 |
| 🟩 | Castle Assault | hardcoded | Medieval 83%, Iron Age 17% | 🟠 10/23 (43%) | CRUSADER×6, SAMURAI×1 | SAMURAI×16, KNIGHT×17, KNIGHT×18, KNIGHT×19, CRUSADER×20, CRUSADER×21, SIEGE_RAM×22, SAMURAI×16, CRUSADER×18, CRUSADER×20, CRUSADER×22, SAMURAI×24, SIEGE_RAM×26, LEGIONARY×28, SAMURAI×32, HORSEMAN_FAST×32 |
| 🟩 | Feudal Army | hardcoded | Medieval 91%, Iron Age 9% | 🟡 12/23 (52%) | CONDOTTERI×3, CRUSADER×2, HANDGUNNER×1 | KNIGHT×16, SIEGE_RAM×17, KNIGHT×18, SIEGE_RAM×19, CRUSADER×20, CRUSADER×21, CONDOTTERI×22, HANDGUNNER×16, CRUSADER×18, SIEGE_RAM×20, SIEGE_RAM×22, CRUSADER×24, KNIGHT×26, CONDOTTERI×28, LARGE_CART×32, CRUSADER×31 |
| 🟩 | Holy Crusade | hardcoded | Medieval 71%, Iron Age 26%, Renaissance 4% | 🟠 11/23 (48%) | CONDOTTERI×2, HANDGUNNER×2, SIEGE_RAM×1, CRUSADER×1 | SAMURAI×16, CONDOTTERI×17, HANDGUNNER×17, KNIGHT×18, THE_SWORDMASTER×19, CONDOTTERI×19, CONDOTTERI×20, HANDGUNNER×21, KNIGHT×21, LARGE_CART×22, LEGIONARY×23, MUSKETEER×12, THE_SWORDMASTER×24, SIEGE_RAM×28, HANDGUNNER×31, CRUSADER×34 |
| 🟩 | Desperate Looters | random | Medieval 93%, Renaissance 7% | 🟢 23/23 (100%) |  | THE_KING×10, CONDOTTERI×13, CRUSADER×14, CONDOTTERI×14, CRUSADER×14, KNIGHT×15, SAMURAI×13, SAMURAI×12, HANDGUNNER×14, HANDGUNNER×18 |
| 🟩 | Desperate Looters | random | Medieval 93%, Renaissance 7% | 🟢 23/23 (100%) |  | THE_KING×10, CONDOTTERI×13, CRUSADER×14, CONDOTTERI×14, CRUSADER×14, KNIGHT×15, SAMURAI×13, SAMURAI×12, HANDGUNNER×14, HANDGUNNER×18 |
| 🟩 | Lazy Raiders | random | Medieval 92%, Iron Age 8% | 🟢 23/23 (100%) |  | SAMURAI×16, HANDGUNNER×15, PIKENEER×12, CRUSADER×17, KNIGHT×15, CRUSADER×16, CRUSADER×17, SAMURAI×18, SIEGE_RAM×18, SIEGE_RAM×15 |
| 🟩 | Reckless Looters | random | Medieval 90%, Renaissance 10% | 🟢 23/23 (100%) |  | SAMURAI×14, SIEGE_RAM×12, CARGO×15, SAMURAI×17, CONDOTTERI×15, CRUSADER×16, HANDGUNNER×13, CRUSADER×13, CONDOTTERI×13, CRUSADER×16 |
| 🟩 | Bored Mercenaries | random | Medieval 92%, Iron Age 8% | 🟢 23/23 (100%) |  | SAMURAI×16, SIEGE_RAM×12, CONDOTTERI×14, SAMURAI×16, SAMURAI×13, HANDGUNNER×15, CRUSADER×13, LARGE_CART×12, CONDOTTERI×16, HANDGUNNER×15, HANDGUNNER×18 |
| 🟩 | Bored Mercenaries | random | Medieval 70%, Iron Age 30% | 🟢 23/23 (100%) |  | CONDOTTERI×16, KNIGHT×18, LARGE_CART×12, HORSEMAN_SLOW×16, SIEGE_RAM×15, CRUSADER×14, KNIGHT×15, SIEGE_RAM×12, PIKENEER×17, SAMURAI×17 |
| 🟩 | Hungry Invaders | random | Medieval 92%, Renaissance 8% | 🟢 22/23 (96%) | MUSKETEER×1 | HANDGUNNER×18, CRUSADER×11, KNIGHT×15, KNIGHT×18, CONDOTTERI×15, CRUSADER×14, SAMURAI×11, KNIGHT×18, SAMURAI×14, CARGO×12 |
| 🟩 | Crude Invaders | random | Medieval 77%, Renaissance 23% | 🟢 23/23 (100%) |  | NINJA×13, KNIGHT×15, CONDOTTERI×13, CRUSADER×16, CONDOTTERI×15, SIEGE_RAM×12, SAMURAI×14, MUSKETEER×13 |
| 🟩 | Petty Bandits | random | Medieval 82%, Iron Age 18% | 🟢 23/23 (100%) |  | LEGIONARY×12, THE_SWORDMASTER×7, CRUSADER×15, KNIGHT×12, KNIGHT×15, CRUSADER×15, CONDOTTERI×15, SAMURAI×17 |
| 🟩 | Restless Horde | random | Medieval 65%, Iron Age 35% | 🟢 23/23 (100%) |  | LEGIONARY×14, CONDOTTERI×13, CONDOTTERI×16, SIEGE_RAM×15, HANDGUNNER×12, THE_SWORDMASTER×7, HORSEMAN_SLOW×16, SIEGE_RAM×12 |
| 🟩 | Angry Mob | random | Medieval 51%, Iron Age 28%, Renaissance 21% | 🟢 22/23 (96%) | MUSKETEER×1 | CARGO×12, HANDGUNNER×17, SAMURAI×12, CONDOTTERI×14, MUSKETEER×16, THE_SWORDMASTER×7, HORSEMAN_SLOW×17, CRUSADER×11, CRUSADER×14, HORSEMAN_FAST×14 |
| 🟩 | Lazy Raiders | random | Medieval 72%, Iron Age 21%, Renaissance 7% | 🟢 23/23 (100%) |  | SIEGE_RAM×15, SIEGE_RAM×18, CRUSADER×12, SIEGE_RAM×12, HORSEMAN_SLOW×14, HANDGUNNER×14, HORSEMAN_FAST×15, SAMURAI×14, THE_KING×10, CONDOTTERI×16 |
| 🟩 | Clumsy Attackers | random | Medieval 90%, Renaissance 10% | 🟢 23/23 (100%) |  | SIEGE_RAM×15, SIEGE_RAM×15, HANDGUNNER×13, SIEGE_RAM×15, HANDGUNNER×12, CRUSADER×16, CONDOTTERI×18, CONDOTTERI×11, NINJA×13 |
| 🟩 | Restless Horde | random | Medieval 91%, Iron Age 9% | 🟢 23/23 (100%) |  | SAMURAI×15, CRUSADER×15, SIEGE_RAM×12, CONDOTTERI×13, SIEGE_RAM×15, LEGIONARY×13, CRUSADER×11, HANDGUNNER×16, SAMURAI×15, CRUSADER×12 |
| 🟩 | Lazy Raiders | random | Medieval 82%, Renaissance 13%, Iron Age 6% | 🟢 23/23 (100%) |  | SAMURAI×16, THE_SWORDMASTER×7, SAMURAI×12, CRUSADER×16, HANDGUNNER×14, CRUSADER×12, NINJA×16, SAMURAI×14, CRUSADER×18 |
| 🟩 | Forgotten Warband | random | Medieval 73%, Renaissance 16%, Iron Age 11% | 🟢 21/23 (91%) | MUSKETEER×2 | KNIGHT×12, SAMURAI×14, SIEGE_RAM×18, CONDOTTERI×13, CARGO×18, SAMURAI×13, KNIGHT×12, HORSEMAN_SLOW×12 |
| 🟩 | Grumpy Marauders | random | Medieval 83%, Renaissance 17% | 🟢 23/23 (100%) |  | SIEGE_RAM×12, CRUSADER×18, SAMURAI×15, SAMURAI×13, THE_KING×10, CRUSADER×13, SAMURAI×17, HANDGUNNER×14, DRAGOONER×13, HANDGUNNER×13 |
| 🟩 | Hungry Invaders | random | Medieval 89%, Renaissance 11% | 🟢 23/23 (100%) |  | CONDOTTERI×17, SAMURAI×16, KNIGHT×15, DRAGOONER×15, SIEGE_RAM×12, CONDOTTERI×13, CONDOTTERI×13, CONDOTTERI×15, CRUSADER×12, KNIGHT×12 |
| 🟩 | Clumsy Attackers | random | Medieval 65%, Iron Age 26%, Renaissance 9% | 🟢 23/23 (100%) |  | KNIGHT×12, SAMURAI×15, SIEGE_RAM×12, KNIGHT×18, SIEGE_RAM×15, LARGE_CART×16, MUSKETEER×12, SIEGE_RAM×15, PIKENEER×18 |
| 🟩 | Grumpy Marauders | random | Medieval 76%, Renaissance 14%, Iron Age 10% | 🟢 23/23 (100%) |  | SIEGE_RAM×15, MUSKETEER×16, SAMURAI×15, SAMURAI×15, CONDOTTERI×18, KNIGHT×15, CONDOTTERI×12, PIKENEER×12 |

#### Big Mixed

| Tower Era Distribution (41 towers) | Towers |
|---|---|
| Medieval 100% (41) | CANNON_TOWER×17, TAR_TOWER×10, HEAVY_TOWER×8, BOILING_OIL×6 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Medieval Siege | hardcoded | Medieval 96%, Renaissance 4% | 🟢 23/23 (100%) |  | CRUSADER×12, CONDOTTERI×13, KNIGHT×14, SAMURAI×15, SIEGE_RAM×15, KNIGHT×16, CONDOTTERI×17, CRUSADER×18, NINJA×11, SIEGE_RAM×20, HANDGUNNER×22, HANDGUNNER×24, HANDGUNNER×26, SAMURAI×28 |
| 🟩 | Knights' Charge | hardcoded | Medieval 91%, Renaissance 9% | 🟢 23/23 (100%) |  | CRUSADER×16, SIEGE_RAM×17, CRUSADER×18, SIEGE_RAM×19, SAMURAI×20, KNIGHT×21, SAMURAI×22, CRUSADER×16, SAMURAI×18, KNIGHT×20, KNIGHT×22, CRUSADER×24, KNIGHT×26, KNIGHT×28, NINJA×30 |
| 🟩 | Crusader Host | hardcoded | Medieval 90%, Iron Age 10% | 🟢 23/23 (100%) |  | CRUSADER×16, SIEGE_RAM×17, SAMURAI×18, SIEGE_RAM×19, SIEGE_RAM×20, SAMURAI×21, CRUSADER×22, KNIGHT×16, KNIGHT×18, CRUSADER×20, CRUSADER×22, HANDGUNNER×24, CONDOTTERI×26, SAMURAI×28, LARGE_CART×31 |
| 🟩 | Castle Assault | hardcoded | Medieval 83%, Iron Age 17% | 🟢 23/23 (100%) |  | SAMURAI×16, KNIGHT×17, KNIGHT×18, KNIGHT×19, CRUSADER×20, CRUSADER×21, SIEGE_RAM×22, SAMURAI×16, CRUSADER×18, CRUSADER×20, CRUSADER×22, SAMURAI×24, SIEGE_RAM×26, LEGIONARY×28, SAMURAI×32, HORSEMAN_FAST×32 |
| 🟩 | Feudal Army | hardcoded | Medieval 91%, Iron Age 9% | 🟢 23/23 (100%) |  | KNIGHT×16, SIEGE_RAM×17, KNIGHT×18, SIEGE_RAM×19, CRUSADER×20, CRUSADER×21, CONDOTTERI×22, HANDGUNNER×16, CRUSADER×18, SIEGE_RAM×20, SIEGE_RAM×22, CRUSADER×24, KNIGHT×26, CONDOTTERI×28, LARGE_CART×32, CRUSADER×31 |
| 🟩 | Holy Crusade | hardcoded | Medieval 71%, Iron Age 26%, Renaissance 4% | 🟢 23/23 (100%) |  | SAMURAI×16, CONDOTTERI×17, HANDGUNNER×17, KNIGHT×18, THE_SWORDMASTER×19, CONDOTTERI×19, CONDOTTERI×20, HANDGUNNER×21, KNIGHT×21, LARGE_CART×22, LEGIONARY×23, MUSKETEER×12, THE_SWORDMASTER×24, SIEGE_RAM×28, HANDGUNNER×31, CRUSADER×34 |
| 🟩 | Desperate Looters | random | Medieval 93%, Renaissance 7% | 🟢 23/23 (100%) |  | THE_KING×10, CONDOTTERI×13, CRUSADER×14, CONDOTTERI×14, CRUSADER×14, KNIGHT×15, SAMURAI×13, SAMURAI×12, HANDGUNNER×14, HANDGUNNER×18 |
| 🟩 | Desperate Looters | random | Medieval 93%, Renaissance 7% | 🟢 23/23 (100%) |  | THE_KING×10, CONDOTTERI×13, CRUSADER×14, CONDOTTERI×14, CRUSADER×14, KNIGHT×15, SAMURAI×13, SAMURAI×12, HANDGUNNER×14, HANDGUNNER×18 |
| 🟩 | Lazy Raiders | random | Medieval 92%, Iron Age 8% | 🟢 23/23 (100%) |  | SAMURAI×16, HANDGUNNER×15, PIKENEER×12, CRUSADER×17, KNIGHT×15, CRUSADER×16, CRUSADER×17, SAMURAI×18, SIEGE_RAM×18, SIEGE_RAM×15 |
| 🟩 | Reckless Looters | random | Medieval 90%, Renaissance 10% | 🟢 23/23 (100%) |  | SAMURAI×14, SIEGE_RAM×12, CARGO×15, SAMURAI×17, CONDOTTERI×15, CRUSADER×16, HANDGUNNER×13, CRUSADER×13, CONDOTTERI×13, CRUSADER×16 |
| 🟩 | Bored Mercenaries | random | Medieval 92%, Iron Age 8% | 🟢 23/23 (100%) |  | SAMURAI×16, SIEGE_RAM×12, CONDOTTERI×14, SAMURAI×16, SAMURAI×13, HANDGUNNER×15, CRUSADER×13, LARGE_CART×12, CONDOTTERI×16, HANDGUNNER×15, HANDGUNNER×18 |
| 🟩 | Bored Mercenaries | random | Medieval 70%, Iron Age 30% | 🟢 23/23 (100%) |  | CONDOTTERI×16, KNIGHT×18, LARGE_CART×12, HORSEMAN_SLOW×16, SIEGE_RAM×15, CRUSADER×14, KNIGHT×15, SIEGE_RAM×12, PIKENEER×17, SAMURAI×17 |
| 🟩 | Hungry Invaders | random | Medieval 92%, Renaissance 8% | 🟢 23/23 (100%) |  | HANDGUNNER×18, CRUSADER×11, KNIGHT×15, KNIGHT×18, CONDOTTERI×15, CRUSADER×14, SAMURAI×11, KNIGHT×18, SAMURAI×14, CARGO×12 |
| 🟩 | Crude Invaders | random | Medieval 77%, Renaissance 23% | 🟢 23/23 (100%) |  | NINJA×13, KNIGHT×15, CONDOTTERI×13, CRUSADER×16, CONDOTTERI×15, SIEGE_RAM×12, SAMURAI×14, MUSKETEER×13 |
| 🟩 | Petty Bandits | random | Medieval 82%, Iron Age 18% | 🟢 23/23 (100%) |  | LEGIONARY×12, THE_SWORDMASTER×7, CRUSADER×15, KNIGHT×12, KNIGHT×15, CRUSADER×15, CONDOTTERI×15, SAMURAI×17 |
| 🟩 | Restless Horde | random | Medieval 65%, Iron Age 35% | 🟢 23/23 (100%) |  | LEGIONARY×14, CONDOTTERI×13, CONDOTTERI×16, SIEGE_RAM×15, HANDGUNNER×12, THE_SWORDMASTER×7, HORSEMAN_SLOW×16, SIEGE_RAM×12 |
| 🟩 | Angry Mob | random | Medieval 51%, Iron Age 28%, Renaissance 21% | 🟢 23/23 (100%) |  | CARGO×12, HANDGUNNER×17, SAMURAI×12, CONDOTTERI×14, MUSKETEER×16, THE_SWORDMASTER×7, HORSEMAN_SLOW×17, CRUSADER×11, CRUSADER×14, HORSEMAN_FAST×14 |
| 🟩 | Lazy Raiders | random | Medieval 72%, Iron Age 21%, Renaissance 7% | 🟢 23/23 (100%) |  | SIEGE_RAM×15, SIEGE_RAM×18, CRUSADER×12, SIEGE_RAM×12, HORSEMAN_SLOW×14, HANDGUNNER×14, HORSEMAN_FAST×15, SAMURAI×14, THE_KING×10, CONDOTTERI×16 |
| 🟩 | Clumsy Attackers | random | Medieval 90%, Renaissance 10% | 🟢 23/23 (100%) |  | SIEGE_RAM×15, SIEGE_RAM×15, HANDGUNNER×13, SIEGE_RAM×15, HANDGUNNER×12, CRUSADER×16, CONDOTTERI×18, CONDOTTERI×11, NINJA×13 |
| 🟩 | Restless Horde | random | Medieval 91%, Iron Age 9% | 🟢 23/23 (100%) |  | SAMURAI×15, CRUSADER×15, SIEGE_RAM×12, CONDOTTERI×13, SIEGE_RAM×15, LEGIONARY×13, CRUSADER×11, HANDGUNNER×16, SAMURAI×15, CRUSADER×12 |
| 🟩 | Lazy Raiders | random | Medieval 82%, Renaissance 13%, Iron Age 6% | 🟢 23/23 (100%) |  | SAMURAI×16, THE_SWORDMASTER×7, SAMURAI×12, CRUSADER×16, HANDGUNNER×14, CRUSADER×12, NINJA×16, SAMURAI×14, CRUSADER×18 |
| 🟩 | Forgotten Warband | random | Medieval 73%, Renaissance 16%, Iron Age 11% | 🟢 23/23 (100%) |  | KNIGHT×12, SAMURAI×14, SIEGE_RAM×18, CONDOTTERI×13, CARGO×18, SAMURAI×13, KNIGHT×12, HORSEMAN_SLOW×12 |
| 🟩 | Grumpy Marauders | random | Medieval 83%, Renaissance 17% | 🟢 23/23 (100%) |  | SIEGE_RAM×12, CRUSADER×18, SAMURAI×15, SAMURAI×13, THE_KING×10, CRUSADER×13, SAMURAI×17, HANDGUNNER×14, DRAGOONER×13, HANDGUNNER×13 |
| 🟩 | Hungry Invaders | random | Medieval 89%, Renaissance 11% | 🟢 23/23 (100%) |  | CONDOTTERI×17, SAMURAI×16, KNIGHT×15, DRAGOONER×15, SIEGE_RAM×12, CONDOTTERI×13, CONDOTTERI×13, CONDOTTERI×15, CRUSADER×12, KNIGHT×12 |
| 🟩 | Clumsy Attackers | random | Medieval 65%, Iron Age 26%, Renaissance 9% | 🟢 23/23 (100%) |  | KNIGHT×12, SAMURAI×15, SIEGE_RAM×12, KNIGHT×18, SIEGE_RAM×15, LARGE_CART×16, MUSKETEER×12, SIEGE_RAM×15, PIKENEER×18 |
| 🟩 | Grumpy Marauders | random | Medieval 76%, Renaissance 14%, Iron Age 10% | 🟢 23/23 (100%) |  | SIEGE_RAM×15, MUSKETEER×16, SAMURAI×15, SAMURAI×15, CONDOTTERI×18, KNIGHT×15, CONDOTTERI×12, PIKENEER×12 |

#### Long Early

| Tower Era Distribution (28 towers) | Towers |
|---|---|
| Iron Age 50% (14), Medieval 50% (14) | ARBELESTE_TOWER×14, BOILING_OIL×5, HEAVY_TOWER×5, TAR_TOWER×4 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Medieval Siege | hardcoded | Medieval 96%, Renaissance 4% | 🟠 5/23 (22%) | HANDGUNNER×11, SAMURAI×5, CRUSADER×1 | CRUSADER×12, CONDOTTERI×13, KNIGHT×14, SAMURAI×15, SIEGE_RAM×15, KNIGHT×16, CONDOTTERI×17, CRUSADER×18, NINJA×11, SIEGE_RAM×20, HANDGUNNER×22, HANDGUNNER×24, HANDGUNNER×26, SAMURAI×28 |
| 🟩 | Knights' Charge | hardcoded | Medieval 91%, Renaissance 9% | 🟡 17/23 (74%) | NINJA×3 | CRUSADER×16, SIEGE_RAM×17, CRUSADER×18, SIEGE_RAM×19, SAMURAI×20, KNIGHT×21, SAMURAI×22, CRUSADER×16, SAMURAI×18, KNIGHT×20, KNIGHT×22, CRUSADER×24, KNIGHT×26, KNIGHT×28, NINJA×30 |
| 🟩 | Crusader Host | hardcoded | Medieval 90%, Iron Age 10% | 🔴 2/23 (9%) | CRUSADER×6, SAMURAI×5, HANDGUNNER×4 | CRUSADER×16, SIEGE_RAM×17, SAMURAI×18, SIEGE_RAM×19, SIEGE_RAM×20, SAMURAI×21, CRUSADER×22, KNIGHT×16, KNIGHT×18, CRUSADER×20, CRUSADER×22, HANDGUNNER×24, CONDOTTERI×26, SAMURAI×28, LARGE_CART×31 |
| 🟩 | Castle Assault | hardcoded | Medieval 83%, Iron Age 17% | 🔴 4/23 (17%) | CRUSADER×7, SAMURAI×1, SIEGE_RAM×1 | SAMURAI×16, KNIGHT×17, KNIGHT×18, KNIGHT×19, CRUSADER×20, CRUSADER×21, SIEGE_RAM×22, SAMURAI×16, CRUSADER×18, CRUSADER×20, CRUSADER×22, SAMURAI×24, SIEGE_RAM×26, LEGIONARY×28, SAMURAI×32, HORSEMAN_FAST×32 |
| 🟩 | Feudal Army | hardcoded | Medieval 91%, Iron Age 9% | 🟡 15/23 (65%) | CRUSADER×2, CONDOTTERI×2 | KNIGHT×16, SIEGE_RAM×17, KNIGHT×18, SIEGE_RAM×19, CRUSADER×20, CRUSADER×21, CONDOTTERI×22, HANDGUNNER×16, CRUSADER×18, SIEGE_RAM×20, SIEGE_RAM×22, CRUSADER×24, KNIGHT×26, CONDOTTERI×28, LARGE_CART×32, CRUSADER×31 |
| 🟩 | Holy Crusade | hardcoded | Medieval 71%, Iron Age 26%, Renaissance 4% | 🟠 5/23 (22%) | CRUSADER×6, HANDGUNNER×2, SIEGE_RAM×1 | SAMURAI×16, CONDOTTERI×17, HANDGUNNER×17, KNIGHT×18, THE_SWORDMASTER×19, CONDOTTERI×19, CONDOTTERI×20, HANDGUNNER×21, KNIGHT×21, LARGE_CART×22, LEGIONARY×23, MUSKETEER×12, THE_SWORDMASTER×24, SIEGE_RAM×28, HANDGUNNER×31, CRUSADER×34 |
| 🟩 | Desperate Looters | random | Medieval 93%, Renaissance 7% | 🟢 23/23 (100%) |  | THE_KING×10, CONDOTTERI×13, CRUSADER×14, CONDOTTERI×14, CRUSADER×14, KNIGHT×15, SAMURAI×13, SAMURAI×12, HANDGUNNER×14, HANDGUNNER×18 |
| 🟩 | Desperate Looters | random | Medieval 93%, Renaissance 7% | 🟢 23/23 (100%) |  | THE_KING×10, CONDOTTERI×13, CRUSADER×14, CONDOTTERI×14, CRUSADER×14, KNIGHT×15, SAMURAI×13, SAMURAI×12, HANDGUNNER×14, HANDGUNNER×18 |
| 🟩 | Lazy Raiders | random | Medieval 92%, Iron Age 8% | 🟢 23/23 (100%) |  | SAMURAI×16, HANDGUNNER×15, PIKENEER×12, CRUSADER×17, KNIGHT×15, CRUSADER×16, CRUSADER×17, SAMURAI×18, SIEGE_RAM×18, SIEGE_RAM×15 |
| 🟩 | Reckless Looters | random | Medieval 90%, Renaissance 10% | 🟢 23/23 (100%) |  | SAMURAI×14, SIEGE_RAM×12, CARGO×15, SAMURAI×17, CONDOTTERI×15, CRUSADER×16, HANDGUNNER×13, CRUSADER×13, CONDOTTERI×13, CRUSADER×16 |
| 🟩 | Bored Mercenaries | random | Medieval 92%, Iron Age 8% | 🟢 23/23 (100%) |  | SAMURAI×16, SIEGE_RAM×12, CONDOTTERI×14, SAMURAI×16, SAMURAI×13, HANDGUNNER×15, CRUSADER×13, LARGE_CART×12, CONDOTTERI×16, HANDGUNNER×15, HANDGUNNER×18 |
| 🟩 | Bored Mercenaries | random | Medieval 70%, Iron Age 30% | 🟢 23/23 (100%) |  | CONDOTTERI×16, KNIGHT×18, LARGE_CART×12, HORSEMAN_SLOW×16, SIEGE_RAM×15, CRUSADER×14, KNIGHT×15, SIEGE_RAM×12, PIKENEER×17, SAMURAI×17 |
| 🟩 | Hungry Invaders | random | Medieval 92%, Renaissance 8% | 🟢 22/23 (96%) | MUSKETEER×1 | HANDGUNNER×18, CRUSADER×11, KNIGHT×15, KNIGHT×18, CONDOTTERI×15, CRUSADER×14, SAMURAI×11, KNIGHT×18, SAMURAI×14, CARGO×12 |
| 🟩 | Crude Invaders | random | Medieval 77%, Renaissance 23% | 🟢 23/23 (100%) |  | NINJA×13, KNIGHT×15, CONDOTTERI×13, CRUSADER×16, CONDOTTERI×15, SIEGE_RAM×12, SAMURAI×14, MUSKETEER×13 |
| 🟩 | Petty Bandits | random | Medieval 82%, Iron Age 18% | 🟢 23/23 (100%) |  | LEGIONARY×12, THE_SWORDMASTER×7, CRUSADER×15, KNIGHT×12, KNIGHT×15, CRUSADER×15, CONDOTTERI×15, SAMURAI×17 |
| 🟩 | Restless Horde | random | Medieval 65%, Iron Age 35% | 🟢 23/23 (100%) |  | LEGIONARY×14, CONDOTTERI×13, CONDOTTERI×16, SIEGE_RAM×15, HANDGUNNER×12, THE_SWORDMASTER×7, HORSEMAN_SLOW×16, SIEGE_RAM×12 |
| 🟩 | Angry Mob | random | Medieval 51%, Iron Age 28%, Renaissance 21% | 🟡 17/23 (74%) | MUSKETEER×2, CONDOTTERI×2 | CARGO×12, HANDGUNNER×17, SAMURAI×12, CONDOTTERI×14, MUSKETEER×16, THE_SWORDMASTER×7, HORSEMAN_SLOW×17, CRUSADER×11, CRUSADER×14, HORSEMAN_FAST×14 |
| 🟩 | Lazy Raiders | random | Medieval 72%, Iron Age 21%, Renaissance 7% | 🟢 23/23 (100%) |  | SIEGE_RAM×15, SIEGE_RAM×18, CRUSADER×12, SIEGE_RAM×12, HORSEMAN_SLOW×14, HANDGUNNER×14, HORSEMAN_FAST×15, SAMURAI×14, THE_KING×10, CONDOTTERI×16 |
| 🟩 | Clumsy Attackers | random | Medieval 90%, Renaissance 10% | 🟡 17/23 (74%) | SIEGE_RAM×1, CRUSADER×1 | SIEGE_RAM×15, SIEGE_RAM×15, HANDGUNNER×13, SIEGE_RAM×15, HANDGUNNER×12, CRUSADER×16, CONDOTTERI×18, CONDOTTERI×11, NINJA×13 |
| 🟩 | Restless Horde | random | Medieval 91%, Iron Age 9% | 🟢 23/23 (100%) |  | SAMURAI×15, CRUSADER×15, SIEGE_RAM×12, CONDOTTERI×13, SIEGE_RAM×15, LEGIONARY×13, CRUSADER×11, HANDGUNNER×16, SAMURAI×15, CRUSADER×12 |
| 🟩 | Lazy Raiders | random | Medieval 82%, Renaissance 13%, Iron Age 6% | 🟢 21/23 (91%) | CRUSADER×1 | SAMURAI×16, THE_SWORDMASTER×7, SAMURAI×12, CRUSADER×16, HANDGUNNER×14, CRUSADER×12, NINJA×16, SAMURAI×14, CRUSADER×18 |
| 🟩 | Forgotten Warband | random | Medieval 73%, Renaissance 16%, Iron Age 11% | 🟢 23/23 (100%) |  | KNIGHT×12, SAMURAI×14, SIEGE_RAM×18, CONDOTTERI×13, CARGO×18, SAMURAI×13, KNIGHT×12, HORSEMAN_SLOW×12 |
| 🟩 | Grumpy Marauders | random | Medieval 83%, Renaissance 17% | 🟢 23/23 (100%) |  | SIEGE_RAM×12, CRUSADER×18, SAMURAI×15, SAMURAI×13, THE_KING×10, CRUSADER×13, SAMURAI×17, HANDGUNNER×14, DRAGOONER×13, HANDGUNNER×13 |
| 🟩 | Hungry Invaders | random | Medieval 89%, Renaissance 11% | 🟢 23/23 (100%) |  | CONDOTTERI×17, SAMURAI×16, KNIGHT×15, DRAGOONER×15, SIEGE_RAM×12, CONDOTTERI×13, CONDOTTERI×13, CONDOTTERI×15, CRUSADER×12, KNIGHT×12 |
| 🟩 | Clumsy Attackers | random | Medieval 65%, Iron Age 26%, Renaissance 9% | 🟢 23/23 (100%) |  | KNIGHT×12, SAMURAI×15, SIEGE_RAM×12, KNIGHT×18, SIEGE_RAM×15, LARGE_CART×16, MUSKETEER×12, SIEGE_RAM×15, PIKENEER×18 |
| 🟩 | Grumpy Marauders | random | Medieval 76%, Renaissance 14%, Iron Age 10% | 🟡 15/23 (65%) | MUSKETEER×4, CRUSADER×2 | SIEGE_RAM×15, MUSKETEER×16, SAMURAI×15, SAMURAI×15, CONDOTTERI×18, KNIGHT×15, CONDOTTERI×12, PIKENEER×12 |

### Renaissance

#### Mixed late

| Tower Era Distribution (32 towers) | Towers |
|---|---|
| Renaissance 78% (25), Medieval 19% (6), Iron Age 3% (1) | RIFLE_TOWER×18, ICE_TOWER×7, CANNON_TOWER×6, COLD_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟥 | Renaissance Force | hardcoded | Renaissance 95%, Industrial 5% | ⬛ 0/24 (0%) | SMALL_TANK×9, DRAGOONER×3 | MUSKETEER×16, DRAGOONER×17, NINJA×17, NINJA×18, MUSKETEER×19, MUSKETEER×19, MUSKETEER×20, SMALL_TANK×22, MUSKETEER×21, DRAGOONER×22, NINJA×23, DRAGOONER×20, DRAGOONER×24, NINJA×28, DRAGOONER×30, DRAGOONER×32, CARGO×32, CARGO×34, THE_KING×36, MUSKETEER×35 |
| 🟩 | Musketeer Brigade | hardcoded | Renaissance 98%, Industrial 2% | 🟡 14/24 (58%) | THE_KING×1 | MUSKETEER×16, DRAGOONER×17, DRAGOONER×17, CARGO×18, DRAGOONER×19, NINJA×19, MUSKETEER×20, CARGO×21, MUSKETEER×21, DRAGOONER×22, MOTORBIKE×12, NINJA×23, MUSKETEER×24, CARGO×28, THE_KING×30, CARGO×32, NINJA×34, MUSKETEER×36, MUSKETEER×36, NINJA×35 |
| 🟩 | Ninja Infiltration | hardcoded | Renaissance 96%, Industrial 4% | 🔴 3/24 (12%) | SOLDIER×11, THE_KING×1 | NINJA×16, DRAGOONER×17, DRAGOONER×17, NINJA×18, MUSKETEER×19, CARGO×19, DRAGOONER×20, DRAGOONER×21, DRAGOONER×21, MUSKETEER×22, CARGO×23, CARGO×23, NINJA×33, NINJA×28, CARGO×30, CARGO×32, DRAGOONER×36, THE_KING×38, NINJA×36, SOLDIER×22 |
| 🟩 | Cannon Barrage | hardcoded | Renaissance 96%, Industrial 4% | 🟠 10/24 (42%) | SOLDIER×8, DRAGOONER×3 | MUSKETEER×16, DRAGOONER×17, CARGO×17, MUSKETEER×18, NINJA×19, NINJA×19, MUSKETEER×20, DRAGOONER×21, NINJA×21, NINJA×22, DRAGOONER×23, NINJA×23, MUSKETEER×24, MUSKETEER×28, THE_KING×30, NINJA×32, SOLDIER×20, DRAGOONER×36, DRAGOONER×36, DRAGOONER×36 |
| 🟥 | Reckless Looters | random | Renaissance 86%, Industrial 14% | ⬛ 0/24 (0%) | SMALL_TANK×10, MUSKETEER×4 | CARGO×21, MOTORBIKE×18, THE_KING×10, SMALL_TANK×22, MUSKETEER×18, CARGO×27, MUSKETEER×18, NINJA×22, DRAGOONER×24, MUSKETEER×17, MUSKETEER×17, MUSKETEER×24, DRAGOONER×20, NINJA×20 |
| 🟥 | Reckless Looters | random | Renaissance 86%, Industrial 14% | ⬛ 0/24 (0%) | SMALL_TANK×10, MUSKETEER×4 | CARGO×21, MOTORBIKE×18, THE_KING×10, SMALL_TANK×22, MUSKETEER×18, CARGO×27, MUSKETEER×18, NINJA×22, DRAGOONER×24, MUSKETEER×17, MUSKETEER×17, MUSKETEER×24, DRAGOONER×20, NINJA×20 |
| 🟩 | Desperate Looters | random | Renaissance 85%, Medieval 8%, Industrial 7% | 🟡 19/24 (79%) | SOLDIER×5 | THE_KING×10, DRAGOONER×22, NINJA×24, TRANSPORTER×20, SAMURAI×22, CARGO×15, NINJA×18, DRAGOONER×20, CARGO×18, NINJA×25, MUSKETEER×24, MUSKETEER×25, CARGO×18, DRAGOONER×18 |
| 🟩 | Drunken Raiders | random | Renaissance 92%, Industrial 8% | 🟢 24/24 (100%) |  | DRAGOONER×20, DRAGOONER×24, CARGO×21, MOTORBIKE×23, MUSKETEER×22, MUSKETEER×23, CARGO×18, CARGO×24, CARGO×24, DRAGOONER×15, THE_KING×10, MUSKETEER×23, NINJA×17, MUSKETEER×18 |
| 🟩 | Restless Horde | random | Renaissance 93%, Medieval 7% | 🟢 24/24 (100%) |  | MUSKETEER×21, DRAGOONER×24, NINJA×26, CARGO×21, DRAGOONER×26, DRAGOONER×20, MUSKETEER×16, SAMURAI×21, THE_KING×10, DRAGOONER×24, DRAGOONER×22, CARGO×21, MUSKETEER×24, NINJA×21, MUSKETEER×24 |
| 🟩 | Grumpy Marauders | random | Renaissance 78%, Medieval 22% | 🟢 24/24 (100%) |  | DRAGOONER×18, CARGO×18, CARGO×24, MUSKETEER×16, THE_KING×10, KNIGHT×18, MUSKETEER×19, MUSKETEER×23, NINJA×24, MUSKETEER×25, CARGO×18, SAMURAI×26, DRAGOONER×22, KNIGHT×18 |
| 🟥 | Savage Rabble | random | Renaissance 82%, Industrial 18% | ⬛ 0/24 (0%) | SOLDIER×12, SMALL_TANK×6 | NINJA×21, THE_KING×10, NINJA×17, CARGO×24, MUSKETEER×24, MUSKETEER×18, CARGO×21, MUSKETEER×25, SMALL_TANK×26, CARGO×27, TRANSPORTER×30, NINJA×25, DRAGOONER×20, CARGO×18 |
| 🟥 | Lazy Raiders | random | Renaissance 75%, Industrial 25% | ⬛ 0/24 (0%) | SOLDIER×15, THE_KING×1 | SOLDIER×25, MUSKETEER×21, DRAGOONER×18, NINJA×22, CARGO×21, SOLDIER×19, MUSKETEER×21, THE_KING×10, SOLDIER×17, DRAGOONER×22, MUSKETEER×26, NINJA×20 |
| 🟩 | Forgotten Warband | random | Renaissance 72%, Medieval 19%, Industrial 9% | 🟡 14/24 (58%) | SOLDIER×10 | DRAGOONER×18, NINJA×21, CONDOTTERI×24, NINJA×16, SIEGE_RAM×21, MUSKETEER×24, NINJA×26, DRAGOONER×22, SOLDIER×21, THE_KING×10, DRAGOONER×18, DRAGOONER×18 |
| 🟩 | Stubborn Raiders | random | Renaissance 74%, Medieval 26% | 🟢 24/24 (100%) |  | SAMURAI×16, DRAGOONER×22, DRAGOONER×18, DRAGOONER×22, NINJA×21, CARGO×24, SAMURAI×25, CARGO×24, MUSKETEER×19, CARGO×18, CARGO×18, KNIGHT×24 |
| 🟩 | Unlucky Raiders | random | Renaissance 63%, Medieval 22%, Industrial 15% | 🟡 13/24 (54%) | SOLDIER×11 | CARGO×18, MUSKETEER×20, SAMURAI×23, CARGO×18, MUSKETEER×24, KNIGHT×18, NINJA×26, MUSKETEER×25, SIEGE_RAM×21, MOTORBIKE×21, MUSKETEER×18, THE_KING×10, SOLDIER×21, CARGO×21 |
| 🟩 | Howling Savages | random | Renaissance 69%, Medieval 16%, Industrial 15% | 🟡 17/24 (71%) | SOLDIER×7 | CARGO×21, SAMURAI×24, TRANSPORTER×20, NINJA×19, THE_KING×10, MOTORBIKE×22, DRAGOONER×18, DRAGOONER×22, MUSKETEER×17, MUSKETEER×22, SIEGE_RAM×21, MUSKETEER×20, MUSKETEER×25, MUSKETEER×21 |
| 🟩 | Desperate Looters | random | Renaissance 87%, Industrial 13% | 🟠 6/24 (25%) | SOLDIER×8, THE_KING×1 | CARGO×18, DRAGOONER×22, DRAGOONER×24, CARGO×18, DRAGOONER×22, MUSKETEER×20, MUSKETEER×25, NINJA×25, MUSKETEER×21, THE_KING×10, SOLDIER×17, MOTORBIKE×17, DRAGOONER×24 |
| 🟩 | Wandering Pillagers | random | Renaissance 94%, Medieval 6% | 🟢 24/24 (100%) |  | NINJA×16, DRAGOONER×20, NINJA×22, MUSKETEER×18, MUSKETEER×17, THE_KING×10, NINJA×19, MUSKETEER×23, DRAGOONER×24, NINJA×20, DRAGOONER×22, CRUSADER×17, DRAGOONER×20, DRAGOONER×24 |
| 🟥 | Clumsy Attackers | random | Renaissance 74%, Industrial 16%, Medieval 10% | ⬛ 0/24 (0%) | SMALL_TANK×12 | NINJA×19, MUSKETEER×24, MUSKETEER×17, CARGO×24, SMALL_TANK×26, NINJA×22, MOTORBIKE×18, SAMURAI×26, CARGO×15, MUSKETEER×23, THE_KING×10, MUSKETEER×25, NINJA×18 |
| 🟩 | Angry Mob | random | Renaissance 85%, Industrial 8%, Medieval 7% | 🟢 24/24 (100%) |  | SAMURAI×16, NINJA×17, CARGO×27, NINJA×17, CARGO×21, MUSKETEER×18, NINJA×16, MOTORBIKE×18, NINJA×20, DRAGOONER×18, DRAGOONER×26, THE_KING×10 |
| 🟩 | Frenzied Pillagers | random | Renaissance 79%, Industrial 21% | 🔴 1/24 (4%) | SOLDIER×10, MOTORBIKE×1, THE_KING×1 | NINJA×19, MUSKETEER×20, CARGO×21, NINJA×25, SOLDIER×16, MOTORBIKE×21, DRAGOONER×20, CARGO×18, MUSKETEER×16, MUSKETEER×20, DRAGOONER×24, DRAGOONER×24, THE_KING×10, TRANSPORTER×20 |
| 🟩 | Forgotten Warband | random | Renaissance 85%, Industrial 15% | 🟡 15/24 (62%) | SOLDIER×9 | MUSKETEER×23, NINJA×18, MUSKETEER×21, DRAGOONER×22, DRAGOONER×24, CARGO×18, TRANSPORTER×20, NINJA×17, DRAGOONER×20, NINJA×24, MOTORBIKE×22, MUSKETEER×21, THE_KING×10, DRAGOONER×22 |
| 🟥 | Frenzied Pillagers | random | Renaissance 66%, Medieval 18%, Industrial 15% | ⬛ 0/24 (0%) | SOLDIER×24 | THE_KING×10, DRAGOONER×18, CARGO×24, MUSKETEER×21, CRUSADER×24, DRAGOONER×18, NINJA×21, CARGO×21, CARGO×21, SOLDIER×18, SOLDIER×22, NINJA×21, KNIGHT×24 |
| 🟩 | Ragged Warband | random | Renaissance 85%, Industrial 7%, Medieval 7% | 🔴 2/24 (8%) | SMALL_TANK×9, MUSKETEER×4 | MUSKETEER×22, NINJA×22, CRUSADER×17, THE_KING×10, SMALL_TANK×18, DRAGOONER×26, CARGO×18, NINJA×21, DRAGOONER×24, MUSKETEER×21, MUSKETEER×18, NINJA×23 |

#### Full Heavy Medieval

| Tower Era Distribution (45 towers) | Towers |
|---|---|
| Medieval 84% (38), Renaissance 16% (7) | HEAVY_TOWER×38, ICE_TOWER×7 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Renaissance Force | hardcoded | Renaissance 95%, Industrial 5% | 🔴 1/28 (4%) | SMALL_TANK×6, MUSKETEER×5, THE_KING×1 | MUSKETEER×16, DRAGOONER×17, NINJA×17, NINJA×18, MUSKETEER×19, MUSKETEER×19, MUSKETEER×20, SMALL_TANK×22, MUSKETEER×21, DRAGOONER×22, NINJA×23, DRAGOONER×20, DRAGOONER×24, NINJA×28, DRAGOONER×30, DRAGOONER×32, CARGO×32, CARGO×34, THE_KING×36, MUSKETEER×35 |
| 🟥 | Musketeer Brigade | hardcoded | Renaissance 98%, Industrial 2% | ⬛ 0/28 (0%) | MUSKETEER×10, NINJA×4, THE_KING×1 | MUSKETEER×16, DRAGOONER×17, DRAGOONER×17, CARGO×18, DRAGOONER×19, NINJA×19, MUSKETEER×20, CARGO×21, MUSKETEER×21, DRAGOONER×22, MOTORBIKE×12, NINJA×23, MUSKETEER×24, CARGO×28, THE_KING×30, CARGO×32, NINJA×34, MUSKETEER×36, MUSKETEER×36, NINJA×35 |
| 🟥 | Ninja Infiltration | hardcoded | Renaissance 96%, Industrial 4% | ⬛ 0/28 (0%) | MUSKETEER×8, SOLDIER×4, DRAGOONER×2, NINJA×1, THE_KING×1 | NINJA×16, DRAGOONER×17, DRAGOONER×17, NINJA×18, MUSKETEER×19, CARGO×19, DRAGOONER×20, DRAGOONER×21, DRAGOONER×21, MUSKETEER×22, CARGO×23, CARGO×23, NINJA×33, NINJA×28, CARGO×30, CARGO×32, DRAGOONER×36, THE_KING×38, NINJA×36, SOLDIER×22 |
| 🟩 | Cannon Barrage | hardcoded | Renaissance 96%, Industrial 4% | 🟡 14/28 (50%) | SOLDIER×14 | MUSKETEER×16, DRAGOONER×17, CARGO×17, MUSKETEER×18, NINJA×19, NINJA×19, MUSKETEER×20, DRAGOONER×21, NINJA×21, NINJA×22, DRAGOONER×23, NINJA×23, MUSKETEER×24, MUSKETEER×28, THE_KING×30, NINJA×32, SOLDIER×20, DRAGOONER×36, DRAGOONER×36, DRAGOONER×36 |
| 🟩 | Reckless Looters | random | Renaissance 86%, Industrial 14% | 🟠 9/28 (32%) | MUSKETEER×7, SMALL_TANK×5, NINJA×1 | CARGO×21, MOTORBIKE×18, THE_KING×10, SMALL_TANK×22, MUSKETEER×18, CARGO×27, MUSKETEER×18, NINJA×22, DRAGOONER×24, MUSKETEER×17, MUSKETEER×17, MUSKETEER×24, DRAGOONER×20, NINJA×20 |
| 🟩 | Reckless Looters | random | Renaissance 86%, Industrial 14% | 🟠 9/28 (32%) | MUSKETEER×7, SMALL_TANK×5, NINJA×1 | CARGO×21, MOTORBIKE×18, THE_KING×10, SMALL_TANK×22, MUSKETEER×18, CARGO×27, MUSKETEER×18, NINJA×22, DRAGOONER×24, MUSKETEER×17, MUSKETEER×17, MUSKETEER×24, DRAGOONER×20, NINJA×20 |
| 🟩 | Desperate Looters | random | Renaissance 85%, Medieval 8%, Industrial 7% | 🟡 16/28 (57%) | SOLDIER×12 | THE_KING×10, DRAGOONER×22, NINJA×24, TRANSPORTER×20, SAMURAI×22, CARGO×15, NINJA×18, DRAGOONER×20, CARGO×18, NINJA×25, MUSKETEER×24, MUSKETEER×25, CARGO×18, DRAGOONER×18 |
| 🟩 | Drunken Raiders | random | Renaissance 92%, Industrial 8% | 🟢 23/28 (82%) | MUSKETEER×5 | DRAGOONER×20, DRAGOONER×24, CARGO×21, MOTORBIKE×23, MUSKETEER×22, MUSKETEER×23, CARGO×18, CARGO×24, CARGO×24, DRAGOONER×15, THE_KING×10, MUSKETEER×23, NINJA×17, MUSKETEER×18 |
| 🟩 | Restless Horde | random | Renaissance 93%, Medieval 7% | 🟢 28/28 (100%) |  | MUSKETEER×21, DRAGOONER×24, NINJA×26, CARGO×21, DRAGOONER×26, DRAGOONER×20, MUSKETEER×16, SAMURAI×21, THE_KING×10, DRAGOONER×24, DRAGOONER×22, CARGO×21, MUSKETEER×24, NINJA×21, MUSKETEER×24 |
| 🟩 | Grumpy Marauders | random | Renaissance 78%, Medieval 22% | 🟢 28/28 (100%) |  | DRAGOONER×18, CARGO×18, CARGO×24, MUSKETEER×16, THE_KING×10, KNIGHT×18, MUSKETEER×19, MUSKETEER×23, NINJA×24, MUSKETEER×25, CARGO×18, SAMURAI×26, DRAGOONER×22, KNIGHT×18 |
| 🟥 | Savage Rabble | random | Renaissance 82%, Industrial 18% | ⬛ 0/28 (0%) | SMALL_TANK×8, NINJA×5, MUSKETEER×3 | NINJA×21, THE_KING×10, NINJA×17, CARGO×24, MUSKETEER×24, MUSKETEER×18, CARGO×21, MUSKETEER×25, SMALL_TANK×26, CARGO×27, TRANSPORTER×30, NINJA×25, DRAGOONER×20, CARGO×18 |
| 🟥 | Lazy Raiders | random | Renaissance 75%, Industrial 25% | ⬛ 0/28 (0%) | SOLDIER×27, MUSKETEER×1 | SOLDIER×25, MUSKETEER×21, DRAGOONER×18, NINJA×22, CARGO×21, SOLDIER×19, MUSKETEER×21, THE_KING×10, SOLDIER×17, DRAGOONER×22, MUSKETEER×26, NINJA×20 |
| 🟩 | Forgotten Warband | random | Renaissance 72%, Medieval 19%, Industrial 9% | 🟠 10/28 (36%) | SOLDIER×14, MUSKETEER×4 | DRAGOONER×18, NINJA×21, CONDOTTERI×24, NINJA×16, SIEGE_RAM×21, MUSKETEER×24, NINJA×26, DRAGOONER×22, SOLDIER×21, THE_KING×10, DRAGOONER×18, DRAGOONER×18 |
| 🟩 | Stubborn Raiders | random | Renaissance 74%, Medieval 26% | 🟢 28/28 (100%) |  | SAMURAI×16, DRAGOONER×22, DRAGOONER×18, DRAGOONER×22, NINJA×21, CARGO×24, SAMURAI×25, CARGO×24, MUSKETEER×19, CARGO×18, CARGO×18, KNIGHT×24 |
| 🟩 | Unlucky Raiders | random | Renaissance 63%, Medieval 22%, Industrial 15% | 🟡 15/28 (54%) | SOLDIER×13 | CARGO×18, MUSKETEER×20, SAMURAI×23, CARGO×18, MUSKETEER×24, KNIGHT×18, NINJA×26, MUSKETEER×25, SIEGE_RAM×21, MOTORBIKE×21, MUSKETEER×18, THE_KING×10, SOLDIER×21, CARGO×21 |
| 🟩 | Howling Savages | random | Renaissance 69%, Medieval 16%, Industrial 15% | 🟠 7/28 (25%) | SOLDIER×13, CRUSADER×4 | CARGO×21, SAMURAI×24, TRANSPORTER×20, NINJA×19, THE_KING×10, MOTORBIKE×22, DRAGOONER×18, DRAGOONER×22, MUSKETEER×17, MUSKETEER×22, SIEGE_RAM×21, MUSKETEER×20, MUSKETEER×25, MUSKETEER×21 |
| 🟩 | Desperate Looters | random | Renaissance 87%, Industrial 13% | 🔴 5/28 (18%) | SOLDIER×14, MOTORBIKE×3 | CARGO×18, DRAGOONER×22, DRAGOONER×24, CARGO×18, DRAGOONER×22, MUSKETEER×20, MUSKETEER×25, NINJA×25, MUSKETEER×21, THE_KING×10, SOLDIER×17, MOTORBIKE×17, DRAGOONER×24 |
| 🟩 | Wandering Pillagers | random | Renaissance 94%, Medieval 6% | 🟢 28/28 (100%) |  | NINJA×16, DRAGOONER×20, NINJA×22, MUSKETEER×18, MUSKETEER×17, THE_KING×10, NINJA×19, MUSKETEER×23, DRAGOONER×24, NINJA×20, DRAGOONER×22, CRUSADER×17, DRAGOONER×20, DRAGOONER×24 |
| 🟩 | Clumsy Attackers | random | Renaissance 74%, Industrial 16%, Medieval 10% | 🟠 12/28 (43%) | SMALL_TANK×8 | NINJA×19, MUSKETEER×24, MUSKETEER×17, CARGO×24, SMALL_TANK×26, NINJA×22, MOTORBIKE×18, SAMURAI×26, CARGO×15, MUSKETEER×23, THE_KING×10, MUSKETEER×25, NINJA×18 |
| 🟩 | Angry Mob | random | Renaissance 85%, Industrial 8%, Medieval 7% | 🟢 28/28 (100%) |  | SAMURAI×16, NINJA×17, CARGO×27, NINJA×17, CARGO×21, MUSKETEER×18, NINJA×16, MOTORBIKE×18, NINJA×20, DRAGOONER×18, DRAGOONER×26, THE_KING×10 |
| 🟩 | Frenzied Pillagers | random | Renaissance 79%, Industrial 21% | 🟠 10/28 (36%) | SOLDIER×15, MOTORBIKE×1 | NINJA×19, MUSKETEER×20, CARGO×21, NINJA×25, SOLDIER×16, MOTORBIKE×21, DRAGOONER×20, CARGO×18, MUSKETEER×16, MUSKETEER×20, DRAGOONER×24, DRAGOONER×24, THE_KING×10, TRANSPORTER×20 |
| 🟩 | Forgotten Warband | random | Renaissance 85%, Industrial 15% | 🟡 22/28 (79%) | SOLDIER×6 | MUSKETEER×23, NINJA×18, MUSKETEER×21, DRAGOONER×22, DRAGOONER×24, CARGO×18, TRANSPORTER×20, NINJA×17, DRAGOONER×20, NINJA×24, MOTORBIKE×22, MUSKETEER×21, THE_KING×10, DRAGOONER×22 |
| 🟥 | Frenzied Pillagers | random | Renaissance 66%, Medieval 18%, Industrial 15% | ⬛ 0/28 (0%) | SOLDIER×27, MUSKETEER×1 | THE_KING×10, DRAGOONER×18, CARGO×24, MUSKETEER×21, CRUSADER×24, DRAGOONER×18, NINJA×21, CARGO×21, CARGO×21, SOLDIER×18, SOLDIER×22, NINJA×21, KNIGHT×24 |
| 🟩 | Ragged Warband | random | Renaissance 85%, Industrial 7%, Medieval 7% | 🟢 28/28 (100%) |  | MUSKETEER×22, NINJA×22, CRUSADER×17, THE_KING×10, SMALL_TANK×18, DRAGOONER×26, CARGO×18, NINJA×21, DRAGOONER×24, MUSKETEER×21, MUSKETEER×18, NINJA×23 |

#### Full Rifle

| Tower Era Distribution (35 towers) | Towers |
|---|---|
| Renaissance 80% (28), Medieval 20% (7) | RIFLE_TOWER×28, TAR_TOWER×7 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟥 | Renaissance Force | hardcoded | Renaissance 95%, Industrial 5% | ⬛ 0/16 (0%) | SMALL_TANK×8 | MUSKETEER×16, DRAGOONER×17, NINJA×17, NINJA×18, MUSKETEER×19, MUSKETEER×19, MUSKETEER×20, SMALL_TANK×22, MUSKETEER×21, DRAGOONER×22, NINJA×23, DRAGOONER×20, DRAGOONER×24, NINJA×28, DRAGOONER×30, DRAGOONER×32, CARGO×32, CARGO×34, THE_KING×36, MUSKETEER×35 |
| 🟩 | Musketeer Brigade | hardcoded | Renaissance 98%, Industrial 2% | 🟢 16/16 (100%) |  | MUSKETEER×16, DRAGOONER×17, DRAGOONER×17, CARGO×18, DRAGOONER×19, NINJA×19, MUSKETEER×20, CARGO×21, MUSKETEER×21, DRAGOONER×22, MOTORBIKE×12, NINJA×23, MUSKETEER×24, CARGO×28, THE_KING×30, CARGO×32, NINJA×34, MUSKETEER×36, MUSKETEER×36, NINJA×35 |
| 🟩 | Ninja Infiltration | hardcoded | Renaissance 96%, Industrial 4% | 🟢 16/16 (100%) |  | NINJA×16, DRAGOONER×17, DRAGOONER×17, NINJA×18, MUSKETEER×19, CARGO×19, DRAGOONER×20, DRAGOONER×21, DRAGOONER×21, MUSKETEER×22, CARGO×23, CARGO×23, NINJA×33, NINJA×28, CARGO×30, CARGO×32, DRAGOONER×36, THE_KING×38, NINJA×36, SOLDIER×22 |
| 🟩 | Cannon Barrage | hardcoded | Renaissance 96%, Industrial 4% | 🟢 16/16 (100%) |  | MUSKETEER×16, DRAGOONER×17, CARGO×17, MUSKETEER×18, NINJA×19, NINJA×19, MUSKETEER×20, DRAGOONER×21, NINJA×21, NINJA×22, DRAGOONER×23, NINJA×23, MUSKETEER×24, MUSKETEER×28, THE_KING×30, NINJA×32, SOLDIER×20, DRAGOONER×36, DRAGOONER×36, DRAGOONER×36 |
| 🟥 | Reckless Looters | random | Renaissance 86%, Industrial 14% | ⬛ 0/16 (0%) | SMALL_TANK×8 | CARGO×21, MOTORBIKE×18, THE_KING×10, SMALL_TANK×22, MUSKETEER×18, CARGO×27, MUSKETEER×18, NINJA×22, DRAGOONER×24, MUSKETEER×17, MUSKETEER×17, MUSKETEER×24, DRAGOONER×20, NINJA×20 |
| 🟥 | Reckless Looters | random | Renaissance 86%, Industrial 14% | ⬛ 0/16 (0%) | SMALL_TANK×8 | CARGO×21, MOTORBIKE×18, THE_KING×10, SMALL_TANK×22, MUSKETEER×18, CARGO×27, MUSKETEER×18, NINJA×22, DRAGOONER×24, MUSKETEER×17, MUSKETEER×17, MUSKETEER×24, DRAGOONER×20, NINJA×20 |
| 🟩 | Desperate Looters | random | Renaissance 85%, Medieval 8%, Industrial 7% | 🟢 16/16 (100%) |  | THE_KING×10, DRAGOONER×22, NINJA×24, TRANSPORTER×20, SAMURAI×22, CARGO×15, NINJA×18, DRAGOONER×20, CARGO×18, NINJA×25, MUSKETEER×24, MUSKETEER×25, CARGO×18, DRAGOONER×18 |
| 🟩 | Drunken Raiders | random | Renaissance 92%, Industrial 8% | 🟢 16/16 (100%) |  | DRAGOONER×20, DRAGOONER×24, CARGO×21, MOTORBIKE×23, MUSKETEER×22, MUSKETEER×23, CARGO×18, CARGO×24, CARGO×24, DRAGOONER×15, THE_KING×10, MUSKETEER×23, NINJA×17, MUSKETEER×18 |
| 🟩 | Restless Horde | random | Renaissance 93%, Medieval 7% | 🟢 16/16 (100%) |  | MUSKETEER×21, DRAGOONER×24, NINJA×26, CARGO×21, DRAGOONER×26, DRAGOONER×20, MUSKETEER×16, SAMURAI×21, THE_KING×10, DRAGOONER×24, DRAGOONER×22, CARGO×21, MUSKETEER×24, NINJA×21, MUSKETEER×24 |
| 🟩 | Grumpy Marauders | random | Renaissance 78%, Medieval 22% | 🟢 16/16 (100%) |  | DRAGOONER×18, CARGO×18, CARGO×24, MUSKETEER×16, THE_KING×10, KNIGHT×18, MUSKETEER×19, MUSKETEER×23, NINJA×24, MUSKETEER×25, CARGO×18, SAMURAI×26, DRAGOONER×22, KNIGHT×18 |
| 🟥 | Savage Rabble | random | Renaissance 82%, Industrial 18% | ⬛ 0/16 (0%) | SOLDIER×11, SMALL_TANK×3 | NINJA×21, THE_KING×10, NINJA×17, CARGO×24, MUSKETEER×24, MUSKETEER×18, CARGO×21, MUSKETEER×25, SMALL_TANK×26, CARGO×27, TRANSPORTER×30, NINJA×25, DRAGOONER×20, CARGO×18 |
| 🟩 | Lazy Raiders | random | Renaissance 75%, Industrial 25% | 🟢 16/16 (100%) |  | SOLDIER×25, MUSKETEER×21, DRAGOONER×18, NINJA×22, CARGO×21, SOLDIER×19, MUSKETEER×21, THE_KING×10, SOLDIER×17, DRAGOONER×22, MUSKETEER×26, NINJA×20 |
| 🟩 | Forgotten Warband | random | Renaissance 72%, Medieval 19%, Industrial 9% | 🟢 16/16 (100%) |  | DRAGOONER×18, NINJA×21, CONDOTTERI×24, NINJA×16, SIEGE_RAM×21, MUSKETEER×24, NINJA×26, DRAGOONER×22, SOLDIER×21, THE_KING×10, DRAGOONER×18, DRAGOONER×18 |
| 🟩 | Stubborn Raiders | random | Renaissance 74%, Medieval 26% | 🟢 16/16 (100%) |  | SAMURAI×16, DRAGOONER×22, DRAGOONER×18, DRAGOONER×22, NINJA×21, CARGO×24, SAMURAI×25, CARGO×24, MUSKETEER×19, CARGO×18, CARGO×18, KNIGHT×24 |
| 🟩 | Unlucky Raiders | random | Renaissance 63%, Medieval 22%, Industrial 15% | 🟢 16/16 (100%) |  | CARGO×18, MUSKETEER×20, SAMURAI×23, CARGO×18, MUSKETEER×24, KNIGHT×18, NINJA×26, MUSKETEER×25, SIEGE_RAM×21, MOTORBIKE×21, MUSKETEER×18, THE_KING×10, SOLDIER×21, CARGO×21 |
| 🟩 | Howling Savages | random | Renaissance 69%, Medieval 16%, Industrial 15% | 🟢 16/16 (100%) |  | CARGO×21, SAMURAI×24, TRANSPORTER×20, NINJA×19, THE_KING×10, MOTORBIKE×22, DRAGOONER×18, DRAGOONER×22, MUSKETEER×17, MUSKETEER×22, SIEGE_RAM×21, MUSKETEER×20, MUSKETEER×25, MUSKETEER×21 |
| 🟩 | Desperate Looters | random | Renaissance 87%, Industrial 13% | 🟢 16/16 (100%) |  | CARGO×18, DRAGOONER×22, DRAGOONER×24, CARGO×18, DRAGOONER×22, MUSKETEER×20, MUSKETEER×25, NINJA×25, MUSKETEER×21, THE_KING×10, SOLDIER×17, MOTORBIKE×17, DRAGOONER×24 |
| 🟩 | Wandering Pillagers | random | Renaissance 94%, Medieval 6% | 🟢 16/16 (100%) |  | NINJA×16, DRAGOONER×20, NINJA×22, MUSKETEER×18, MUSKETEER×17, THE_KING×10, NINJA×19, MUSKETEER×23, DRAGOONER×24, NINJA×20, DRAGOONER×22, CRUSADER×17, DRAGOONER×20, DRAGOONER×24 |
| 🟥 | Clumsy Attackers | random | Renaissance 74%, Industrial 16%, Medieval 10% | ⬛ 0/16 (0%) | SMALL_TANK×8 | NINJA×19, MUSKETEER×24, MUSKETEER×17, CARGO×24, SMALL_TANK×26, NINJA×22, MOTORBIKE×18, SAMURAI×26, CARGO×15, MUSKETEER×23, THE_KING×10, MUSKETEER×25, NINJA×18 |
| 🟩 | Angry Mob | random | Renaissance 85%, Industrial 8%, Medieval 7% | 🟢 16/16 (100%) |  | SAMURAI×16, NINJA×17, CARGO×27, NINJA×17, CARGO×21, MUSKETEER×18, NINJA×16, MOTORBIKE×18, NINJA×20, DRAGOONER×18, DRAGOONER×26, THE_KING×10 |
| 🟩 | Frenzied Pillagers | random | Renaissance 79%, Industrial 21% | 🟢 16/16 (100%) |  | NINJA×19, MUSKETEER×20, CARGO×21, NINJA×25, SOLDIER×16, MOTORBIKE×21, DRAGOONER×20, CARGO×18, MUSKETEER×16, MUSKETEER×20, DRAGOONER×24, DRAGOONER×24, THE_KING×10, TRANSPORTER×20 |
| 🟩 | Forgotten Warband | random | Renaissance 85%, Industrial 15% | 🟢 16/16 (100%) |  | MUSKETEER×23, NINJA×18, MUSKETEER×21, DRAGOONER×22, DRAGOONER×24, CARGO×18, TRANSPORTER×20, NINJA×17, DRAGOONER×20, NINJA×24, MOTORBIKE×22, MUSKETEER×21, THE_KING×10, DRAGOONER×22 |
| 🟩 | Frenzied Pillagers | random | Renaissance 66%, Medieval 18%, Industrial 15% | 🟢 16/16 (100%) |  | THE_KING×10, DRAGOONER×18, CARGO×24, MUSKETEER×21, CRUSADER×24, DRAGOONER×18, NINJA×21, CARGO×21, CARGO×21, SOLDIER×18, SOLDIER×22, NINJA×21, KNIGHT×24 |
| 🟥 | Ragged Warband | random | Renaissance 85%, Industrial 7%, Medieval 7% | ⬛ 0/16 (0%) | SMALL_TANK×8 | MUSKETEER×22, NINJA×22, CRUSADER×17, THE_KING×10, SMALL_TANK×18, DRAGOONER×26, CARGO×18, NINJA×21, DRAGOONER×24, MUSKETEER×21, MUSKETEER×18, NINJA×23 |

#### Mixed early ren

| Tower Era Distribution (33 towers) | Towers |
|---|---|
| Medieval 82% (27), Renaissance 18% (6) | BOILING_OIL×9, TAR_TOWER×9, CANNON_TOWER×9, RIFLE_TOWER×6 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟥 | Renaissance Force | hardcoded | Renaissance 95%, Industrial 5% | ⬛ 0/10 (0%) | SMALL_TANK×4, MUSKETEER×2 | MUSKETEER×16, DRAGOONER×17, NINJA×17, NINJA×18, MUSKETEER×19, MUSKETEER×19, MUSKETEER×20, SMALL_TANK×22, MUSKETEER×21, DRAGOONER×22, NINJA×23, DRAGOONER×20, DRAGOONER×24, NINJA×28, DRAGOONER×30, DRAGOONER×32, CARGO×32, CARGO×34, THE_KING×36, MUSKETEER×35 |
| 🟥 | Musketeer Brigade | hardcoded | Renaissance 98%, Industrial 2% | ⬛ 0/10 (0%) | MUSKETEER×1, THE_KING×1 | MUSKETEER×16, DRAGOONER×17, DRAGOONER×17, CARGO×18, DRAGOONER×19, NINJA×19, MUSKETEER×20, CARGO×21, MUSKETEER×21, DRAGOONER×22, MOTORBIKE×12, NINJA×23, MUSKETEER×24, CARGO×28, THE_KING×30, CARGO×32, NINJA×34, MUSKETEER×36, MUSKETEER×36, NINJA×35 |
| 🟥 | Ninja Infiltration | hardcoded | Renaissance 96%, Industrial 4% | ⬛ 0/10 (0%) | MUSKETEER×6, NINJA×2 | NINJA×16, DRAGOONER×17, DRAGOONER×17, NINJA×18, MUSKETEER×19, CARGO×19, DRAGOONER×20, DRAGOONER×21, DRAGOONER×21, MUSKETEER×22, CARGO×23, CARGO×23, NINJA×33, NINJA×28, CARGO×30, CARGO×32, DRAGOONER×36, THE_KING×38, NINJA×36, SOLDIER×22 |
| 🟥 | Cannon Barrage | hardcoded | Renaissance 96%, Industrial 4% | ⬛ 0/10 (0%) | SOLDIER×10 | MUSKETEER×16, DRAGOONER×17, CARGO×17, MUSKETEER×18, NINJA×19, NINJA×19, MUSKETEER×20, DRAGOONER×21, NINJA×21, NINJA×22, DRAGOONER×23, NINJA×23, MUSKETEER×24, MUSKETEER×28, THE_KING×30, NINJA×32, SOLDIER×20, DRAGOONER×36, DRAGOONER×36, DRAGOONER×36 |
| 🟥 | Reckless Looters | random | Renaissance 86%, Industrial 14% | ⬛ 0/10 (0%) | SMALL_TANK×5, MUSKETEER×1 | CARGO×21, MOTORBIKE×18, THE_KING×10, SMALL_TANK×22, MUSKETEER×18, CARGO×27, MUSKETEER×18, NINJA×22, DRAGOONER×24, MUSKETEER×17, MUSKETEER×17, MUSKETEER×24, DRAGOONER×20, NINJA×20 |
| 🟥 | Reckless Looters | random | Renaissance 86%, Industrial 14% | ⬛ 0/10 (0%) | SMALL_TANK×5, MUSKETEER×1 | CARGO×21, MOTORBIKE×18, THE_KING×10, SMALL_TANK×22, MUSKETEER×18, CARGO×27, MUSKETEER×18, NINJA×22, DRAGOONER×24, MUSKETEER×17, MUSKETEER×17, MUSKETEER×24, DRAGOONER×20, NINJA×20 |
| 🟩 | Desperate Looters | random | Renaissance 85%, Medieval 8%, Industrial 7% | 🟠 3/10 (30%) | SOLDIER×7 | THE_KING×10, DRAGOONER×22, NINJA×24, TRANSPORTER×20, SAMURAI×22, CARGO×15, NINJA×18, DRAGOONER×20, CARGO×18, NINJA×25, MUSKETEER×24, MUSKETEER×25, CARGO×18, DRAGOONER×18 |
| 🟩 | Drunken Raiders | random | Renaissance 92%, Industrial 8% | 🟡 5/10 (50%) | MUSKETEER×2, MOTORBIKE×1 | DRAGOONER×20, DRAGOONER×24, CARGO×21, MOTORBIKE×23, MUSKETEER×22, MUSKETEER×23, CARGO×18, CARGO×24, CARGO×24, DRAGOONER×15, THE_KING×10, MUSKETEER×23, NINJA×17, MUSKETEER×18 |
| 🟩 | Restless Horde | random | Renaissance 93%, Medieval 7% | 🟢 10/10 (100%) |  | MUSKETEER×21, DRAGOONER×24, NINJA×26, CARGO×21, DRAGOONER×26, DRAGOONER×20, MUSKETEER×16, SAMURAI×21, THE_KING×10, DRAGOONER×24, DRAGOONER×22, CARGO×21, MUSKETEER×24, NINJA×21, MUSKETEER×24 |
| 🟩 | Grumpy Marauders | random | Renaissance 78%, Medieval 22% | 🟢 10/10 (100%) |  | DRAGOONER×18, CARGO×18, CARGO×24, MUSKETEER×16, THE_KING×10, KNIGHT×18, MUSKETEER×19, MUSKETEER×23, NINJA×24, MUSKETEER×25, CARGO×18, SAMURAI×26, DRAGOONER×22, KNIGHT×18 |
| 🟥 | Savage Rabble | random | Renaissance 82%, Industrial 18% | ⬛ 0/10 (0%) | SMALL_TANK×4, MUSKETEER×3 | NINJA×21, THE_KING×10, NINJA×17, CARGO×24, MUSKETEER×24, MUSKETEER×18, CARGO×21, MUSKETEER×25, SMALL_TANK×26, CARGO×27, TRANSPORTER×30, NINJA×25, DRAGOONER×20, CARGO×18 |
| 🟥 | Lazy Raiders | random | Renaissance 75%, Industrial 25% | ⬛ 0/10 (0%) | SOLDIER×10 | SOLDIER×25, MUSKETEER×21, DRAGOONER×18, NINJA×22, CARGO×21, SOLDIER×19, MUSKETEER×21, THE_KING×10, SOLDIER×17, DRAGOONER×22, MUSKETEER×26, NINJA×20 |
| 🟥 | Forgotten Warband | random | Renaissance 72%, Medieval 19%, Industrial 9% | ⬛ 0/10 (0%) | SOLDIER×10 | DRAGOONER×18, NINJA×21, CONDOTTERI×24, NINJA×16, SIEGE_RAM×21, MUSKETEER×24, NINJA×26, DRAGOONER×22, SOLDIER×21, THE_KING×10, DRAGOONER×18, DRAGOONER×18 |
| 🟩 | Stubborn Raiders | random | Renaissance 74%, Medieval 26% | 🟢 8/10 (80%) | MUSKETEER×2 | SAMURAI×16, DRAGOONER×22, DRAGOONER×18, DRAGOONER×22, NINJA×21, CARGO×24, SAMURAI×25, CARGO×24, MUSKETEER×19, CARGO×18, CARGO×18, KNIGHT×24 |
| 🟥 | Unlucky Raiders | random | Renaissance 63%, Medieval 22%, Industrial 15% | ⬛ 0/10 (0%) | SOLDIER×4, MOTORBIKE×2 | CARGO×18, MUSKETEER×20, SAMURAI×23, CARGO×18, MUSKETEER×24, KNIGHT×18, NINJA×26, MUSKETEER×25, SIEGE_RAM×21, MOTORBIKE×21, MUSKETEER×18, THE_KING×10, SOLDIER×21, CARGO×21 |
| 🟥 | Howling Savages | random | Renaissance 69%, Medieval 16%, Industrial 15% | ⬛ 0/10 (0%) | SOLDIER×10 | CARGO×21, SAMURAI×24, TRANSPORTER×20, NINJA×19, THE_KING×10, MOTORBIKE×22, DRAGOONER×18, DRAGOONER×22, MUSKETEER×17, MUSKETEER×22, SIEGE_RAM×21, MUSKETEER×20, MUSKETEER×25, MUSKETEER×21 |
| 🟥 | Desperate Looters | random | Renaissance 87%, Industrial 13% | ⬛ 0/10 (0%) | SOLDIER×9, MOTORBIKE×1 | CARGO×18, DRAGOONER×22, DRAGOONER×24, CARGO×18, DRAGOONER×22, MUSKETEER×20, MUSKETEER×25, NINJA×25, MUSKETEER×21, THE_KING×10, SOLDIER×17, MOTORBIKE×17, DRAGOONER×24 |
| 🟩 | Wandering Pillagers | random | Renaissance 94%, Medieval 6% | 🟢 10/10 (100%) |  | NINJA×16, DRAGOONER×20, NINJA×22, MUSKETEER×18, MUSKETEER×17, THE_KING×10, NINJA×19, MUSKETEER×23, DRAGOONER×24, NINJA×20, DRAGOONER×22, CRUSADER×17, DRAGOONER×20, DRAGOONER×24 |
| 🟥 | Clumsy Attackers | random | Renaissance 74%, Industrial 16%, Medieval 10% | ⬛ 0/10 (0%) | SMALL_TANK×4, MOTORBIKE×1 | NINJA×19, MUSKETEER×24, MUSKETEER×17, CARGO×24, SMALL_TANK×26, NINJA×22, MOTORBIKE×18, SAMURAI×26, CARGO×15, MUSKETEER×23, THE_KING×10, MUSKETEER×25, NINJA×18 |
| 🟩 | Angry Mob | random | Renaissance 85%, Industrial 8%, Medieval 7% | 🟢 10/10 (100%) |  | SAMURAI×16, NINJA×17, CARGO×27, NINJA×17, CARGO×21, MUSKETEER×18, NINJA×16, MOTORBIKE×18, NINJA×20, DRAGOONER×18, DRAGOONER×26, THE_KING×10 |
| 🟥 | Frenzied Pillagers | random | Renaissance 79%, Industrial 21% | ⬛ 0/10 (0%) | SOLDIER×7, MOTORBIKE×1 | NINJA×19, MUSKETEER×20, CARGO×21, NINJA×25, SOLDIER×16, MOTORBIKE×21, DRAGOONER×20, CARGO×18, MUSKETEER×16, MUSKETEER×20, DRAGOONER×24, DRAGOONER×24, THE_KING×10, TRANSPORTER×20 |
| 🟥 | Forgotten Warband | random | Renaissance 85%, Industrial 15% | ⬛ 0/10 (0%) | SOLDIER×10 | MUSKETEER×23, NINJA×18, MUSKETEER×21, DRAGOONER×22, DRAGOONER×24, CARGO×18, TRANSPORTER×20, NINJA×17, DRAGOONER×20, NINJA×24, MOTORBIKE×22, MUSKETEER×21, THE_KING×10, DRAGOONER×22 |
| 🟥 | Frenzied Pillagers | random | Renaissance 66%, Medieval 18%, Industrial 15% | ⬛ 0/10 (0%) | SOLDIER×10 | THE_KING×10, DRAGOONER×18, CARGO×24, MUSKETEER×21, CRUSADER×24, DRAGOONER×18, NINJA×21, CARGO×21, CARGO×21, SOLDIER×18, SOLDIER×22, NINJA×21, KNIGHT×24 |
| 🟩 | Ragged Warband | random | Renaissance 85%, Industrial 7%, Medieval 7% | 🟢 10/10 (100%) |  | MUSKETEER×22, NINJA×22, CRUSADER×17, THE_KING×10, SMALL_TANK×18, DRAGOONER×26, CARGO×18, NINJA×21, DRAGOONER×24, MUSKETEER×21, MUSKETEER×18, NINJA×23 |

### Industrial

#### Flame/Gatling

| Tower Era Distribution (35 towers) | Towers |
|---|---|
| Industrial 91% (32), Iron Age 9% (3) | FLAME_THROWER×16, GATLING_TOWER×16, COLD_TOWER×3 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Industrial March | hardcoded | Industrial 98%, Modern 2% | 🟢 28/28 (100%) |  | SOLDIER×16, SOLDIER×17, MOTORBIKE×17, TRANSPORTER×18, TRANSPORTER×19, SMALL_TANK×19, TRANSPORTER×20, TRANSPORTER×21, SMALL_TANK×21, SMALL_TANK×22, MOTORBIKE×23, MOTORBIKE×23, SPECOPS×10, MOTORBIKE×28, SMALL_TANK×30, SOLDIER×32, SOLDIER×34, MOTORBIKE×36 |
| 🟩 | Mechanized Strike | hardcoded | Industrial 100% | 🟡 17/28 (61%) | SOLDIER×11 | SOLDIER×18, SMALL_TANK×19, TRANSPORTER×19, SMALL_TANK×20, TRANSPORTER×21, SMALL_TANK×21, SOLDIER×22, SOLDIER×22, TRANSPORTER×23, MOTORBIKE×24, SMALL_TANK×24, MOTORBIKE×25, TRANSPORTER×26, TRANSPORTER×26, SOLDIER×27, SOLDIER×27, SMALL_TANK×28, SMALL_TANK×29, SMALL_TANK×29, TRANSPORTER×30 |
| 🟩 | Steam Assault | hardcoded | Industrial 100% | 🟢 24/28 (86%) | SOLDIER×4 | TRANSPORTER×18, SOLDIER×19, SOLDIER×19, SMALL_TANK×20, TRANSPORTER×21, SOLDIER×21, SOLDIER×22, SMALL_TANK×22, TRANSPORTER×23, SMALL_TANK×24, TRANSPORTER×24, SMALL_TANK×25, SOLDIER×26, TRANSPORTER×26, SMALL_TANK×27, MOTORBIKE×27, SOLDIER×28, TRANSPORTER×29, SOLDIER×29, MOTORBIKE×30 |
| 🟩 | Tank Column | hardcoded | Industrial 100% | 🟢 28/28 (100%) |  | SMALL_TANK×18, MOTORBIKE×19, MOTORBIKE×19, TRANSPORTER×20, TRANSPORTER×21, TRANSPORTER×21, SOLDIER×22, MOTORBIKE×22, TRANSPORTER×23, TRANSPORTER×24, SMALL_TANK×24, MOTORBIKE×25, TRANSPORTER×26, SMALL_TANK×26, TRANSPORTER×27, SMALL_TANK×27, TRANSPORTER×28, MOTORBIKE×29, MOTORBIKE×29, SOLDIER×30, SOLDIER×34 |
| 🟩 | Factory Raid | hardcoded | Industrial 88%, Renaissance 12% | 🟡 22/28 (79%) | SOLDIER×6 | MOTORBIKE×18, MOTORBIKE×20, MOTORBIKE×20, MOTORBIKE×22, SOLDIER×20, TRANSPORTER×21, MOTORBIKE×22, SMALL_TANK×22, SMALL_TANK×25, SOLDIER×24, MOTORBIKE×24, TRANSPORTER×25, SMALL_TANK×26, SMALL_TANK×28, MOTORBIKE×30, CARGO×30, TRANSPORTER×32, DRAGOONER×34, SOLDIER×36, SMALL_TANK×33, SMALL_TANK×36 |
| 🟩 | Lazy Raiders | random | Industrial 84%, Renaissance 8%, Modern 8% | 🟢 28/28 (100%) |  | SIEGE_TANK×28, MOTORBIKE×20, MOTORBIKE×21, MUSKETEER×29, SOLDIER×24, TRANSPORTER×30, SOLDIER×19, TRANSPORTER×20, TRANSPORTER×20, MOTORBIKE×27, TRANSPORTER×20, SMALL_TANK×24, SOLDIER×27, MOTORBIKE×26, SOLDIER×25 |
| 🟩 | Lazy Raiders | random | Industrial 84%, Renaissance 8%, Modern 8% | 🟢 28/28 (100%) |  | SIEGE_TANK×28, MOTORBIKE×20, MOTORBIKE×21, MUSKETEER×29, SOLDIER×24, TRANSPORTER×30, SOLDIER×19, TRANSPORTER×20, TRANSPORTER×20, MOTORBIKE×27, TRANSPORTER×20, SMALL_TANK×24, SOLDIER×27, MOTORBIKE×26, SOLDIER×25 |
| 🟩 | Unlucky Raiders | random | Industrial 89%, Renaissance 11% | 🟢 27/28 (96%) | SOLDIER×1 | TRANSPORTER×30, NINJA×25, SOLDIER×24, MOTORBIKE×29, NINJA×19, SOLDIER×29, SOLDIER×27, SOLDIER×20, SOLDIER×18, SMALL_TANK×32, SOLDIER×31, TRANSPORTER×20, SMALL_TANK×30, SMALL_TANK×24, MOTORBIKE×32 |
| 🟥 | Petty Bandits | random | Industrial 87%, Modern 7%, Renaissance 5% | ⬛ 0/28 (0%) | SPECOPS×14 | TRANSPORTER×30, MOTORBIKE×29, SMALL_TANK×20, SOLDIER×22, MOTORBIKE×25, DRAGOONER×20, SMALL_TANK×26, SOLDIER×28, SMALL_TANK×22, MOTORBIKE×31, TRANSPORTER×20, SOLDIER×30, TRANSPORTER×20, SPECOPS×28, SOLDIER×29 |
| 🟩 | Disorganized Mob | random | Industrial 90%, Renaissance 10% | 🟡 18/28 (64%) | SOLDIER×10 | MOTORBIKE×23, SMALL_TANK×28, TRANSPORTER×30, THE_KING×10, SOLDIER×25, TRANSPORTER×30, TRANSPORTER×20, SMALL_TANK×20, TRANSPORTER×30, TRANSPORTER×30, MUSKETEER×29, SOLDIER×21, MOTORBIKE×28, MOTORBIKE×28, SMALL_TANK×24, MOTORBIKE×24 |
| 🟩 | Ragged Warband | random | Industrial 78%, Renaissance 22% | 🟢 28/28 (100%) |  | SOLDIER×25, SOLDIER×22, SMALL_TANK×28, SMALL_TANK×20, SOLDIER×29, THE_KING×10, MUSKETEER×32, MOTORBIKE×29, CARGO×21, SMALL_TANK×22, MOTORBIKE×31, SMALL_TANK×28, SOLDIER×29, NINJA×19, MOTORBIKE×31 |
| 🟥 | Hungry Invaders | random | Industrial 89%, Renaissance 5%, Modern 5% | ⬛ 0/28 (0%) | SOLDIER×28 | SOLDIER×26, SOLDIER×31, TRANSPORTER×20, SOLDIER×18, CARGO×21, SOLDIER×32, TRANSPORTER×30, TRANSPORTER×30, MOTORBIKE×24, SOLDIER×24, TRANSPORTER×30, HELI×20, TRANSPORTER×30, TRANSPORTER×30, MOTORBIKE×18 |
| 🟥 | Bored Mercenaries | random | Industrial 79%, Modern 17%, Renaissance 3% | ⬛ 0/28 (0%) | SPECOPS×14 | MOTORBIKE×25, SOLDIER×26, SMALL_TANK×22, SPECOPS×29, TRANSPORTER×20, SMALL_TANK×20, SOLDIER×29, SMALL_TANK×22, TRANSPORTER×20, SIEGE_TANK×22, MOTORBIKE×22, THE_KING×10, SMALL_TANK×26 |
| 🟩 | Wandering Pillagers | random | Industrial 80%, Renaissance 20% | 🟢 28/28 (100%) |  | MUSKETEER×23, SOLDIER×20, SMALL_TANK×26, SOLDIER×25, SOLDIER×26, SOLDIER×26, DRAGOONER×18, SOLDIER×20, MUSKETEER×22, SOLDIER×25, MOTORBIKE×29, MOTORBIKE×29, TRANSPORTER×30 |
| 🟩 | Crude Invaders | random | Industrial 71%, Renaissance 29% | 🟢 24/28 (86%) | SOLDIER×4 | SMALL_TANK×22, TRANSPORTER×30, SMALL_TANK×28, DRAGOONER×22, NINJA×30, MUSKETEER×30, SMALL_TANK×22, THE_KING×10, MOTORBIKE×25, TRANSPORTER×30, TRANSPORTER×20, SMALL_TANK×26, TRANSPORTER×20 |
| 🟩 | Grumpy Marauders | random | Industrial 62%, Renaissance 26%, Modern 11% | 🟢 27/28 (96%) | SOLDIER×1 | TRANSPORTER×30, TRANSPORTER×30, SOLDIER×23, TRANSPORTER×20, NINJA×23, SIEGE_TANK×20, MUSKETEER×19, TRANSPORTER×20, MUSKETEER×22, SOLDIER×23, MOTORBIKE×24, DRAGOONER×24, HELI×18, MOTORBIKE×21, SOLDIER×18 |
| 🟩 | Rampaging Rabble | random | Industrial 73%, Renaissance 20%, Modern 8% | 🟢 28/28 (100%) |  | SMALL_TANK×24, SMALL_TANK×26, SMALL_TANK×30, MOTORBIKE×24, DRAGOONER×22, CARGO×30, DRAGOONER×22, SOLDIER×20, SOLDIER×26, SMALL_TANK×28, MOTORBIKE×25, MOTORBIKE×26, SMALL_TANK×20, TRANSPORTER×20, SIEGE_TANK×28 |
| 🟩 | Frenzied Pillagers | random | Industrial 90%, Modern 7%, Renaissance 3% | 🟠 13/28 (46%) | SOLDIER×15 | SMALL_TANK×28, MOTORBIKE×21, SOLDIER×22, TRANSPORTER×20, SMALL_TANK×18, SOLDIER×24, SOLDIER×28, TRANSPORTER×20, SIEGE_TANK×22, THE_KING×10, SMALL_TANK×26, TRANSPORTER×30, SMALL_TANK×26, TRANSPORTER×20 |
| 🟩 | Unlucky Raiders | random | Industrial 88%, Renaissance 12% | 🟢 27/28 (96%) | SOLDIER×1 | MUSKETEER×31, SMALL_TANK×22, THE_KING×10, MOTORBIKE×26, MOTORBIKE×19, SOLDIER×19, SMALL_TANK×24, MOTORBIKE×19, SOLDIER×19, SMALL_TANK×20, TRANSPORTER×30, TRANSPORTER×20, MOTORBIKE×26, SOLDIER×28, SOLDIER×26 |
| 🟩 | Bored Mercenaries | random | Industrial 81%, Renaissance 12%, Modern 7% | 🟢 28/28 (100%) |  | HELI×22, TRANSPORTER×30, NINJA×19, SOLDIER×29, MOTORBIKE×27, CARGO×21, SMALL_TANK×22, MOTORBIKE×24, SOLDIER×20, TRANSPORTER×20, MOTORBIKE×21, TRANSPORTER×20, TRANSPORTER×20, SOLDIER×31 |
| 🟩 | Muddy Marauders | random | Industrial 82%, Renaissance 11%, Modern 7% | 🟢 28/28 (100%) |  | MOTORBIKE×23, SMALL_TANK×32, MOTORBIKE×19, THE_KING×10, HELI×20, TRANSPORTER×20, MUSKETEER×20, SOLDIER×25, MOTORBIKE×21, SMALL_TANK×22, MOTORBIKE×19, MOTORBIKE×18, TRANSPORTER×30 |
| 🟩 | Weary Plunderers | random | Industrial 79%, Modern 16%, Renaissance 5% | 🟢 23/28 (82%) | SOLDIER×5 | SMALL_TANK×30, SOLDIER×31, SOLDIER×28, MOTORBIKE×23, SMALL_TANK×20, SOLDIER×22, MOTORBIKE×26, SIEGE_TANK×30, TRANSPORTER×20, SIEGE_TANK×30, MOTORBIKE×30, DRAGOONER×20, TRANSPORTER×20, TRANSPORTER×20, MOTORBIKE×27 |
| 🟩 | Restless Horde | random | Industrial 87%, Renaissance 7%, Modern 6% | 🟢 28/28 (100%) |  | MOTORBIKE×21, SMALL_TANK×26, SMALL_TANK×22, SMALL_TANK×22, SMALL_TANK×26, SOLDIER×19, SOLDIER×27, SOLDIER×30, MOTORBIKE×19, MOTORBIKE×28, DRAGOONER×26, SMALL_TANK×30, SIEGE_TANK×22, TRANSPORTER×20, MOTORBIKE×24 |
| 🟩 | Crude Invaders | random | Industrial 73%, Renaissance 20%, Modern 6% | 🔴 4/28 (14%) | SPECOPS×12 | SMALL_TANK×24, SMALL_TANK×20, SMALL_TANK×28, SOLDIER×29, SOLDIER×31, CARGO×21, DRAGOONER×20, SMALL_TANK×30, SPECOPS×22, MOTORBIKE×20, TRANSPORTER×20, SOLDIER×20, NINJA×29, MOTORBIKE×27 |
| 🟩 | Disorganized Mob | random | Industrial 80%, Renaissance 11%, Modern 10% | 🟡 14/28 (50%) | SOLDIER×12, SIEGE_TANK×1 | SOLDIER×19, SIEGE_TANK×30, SMALL_TANK×28, TRANSPORTER×20, TRANSPORTER×30, MOTORBIKE×26, SOLDIER×19, SMALL_TANK×26, MOTORBIKE×27, MOTORBIKE×26, THE_KING×10, DRAGOONER×22, TRANSPORTER×20 |

#### Indy / Renaissance

| Tower Era Distribution (28 towers) | Towers |
|---|---|
| Renaissance 46% (13), Industrial 46% (13), Iron Age 7% (2) | RIFLE_TOWER×10, FLAME_THROWER×8, GATLING_TOWER×5, ICE_TOWER×3, COLD_TOWER×2 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟥 | Industrial March | hardcoded | Industrial 98%, Modern 2% | ⬛ 0/16 (0%) | MOTORBIKE×5, SOLDIER×1 | SOLDIER×16, SOLDIER×17, MOTORBIKE×17, TRANSPORTER×18, TRANSPORTER×19, SMALL_TANK×19, TRANSPORTER×20, TRANSPORTER×21, SMALL_TANK×21, SMALL_TANK×22, MOTORBIKE×23, MOTORBIKE×23, SPECOPS×10, MOTORBIKE×28, SMALL_TANK×30, SOLDIER×32, SOLDIER×34, MOTORBIKE×36 |
| 🟥 | Mechanized Strike | hardcoded | Industrial 100% | ⬛ 0/16 (0%) | SOLDIER×16 | SOLDIER×18, SMALL_TANK×19, TRANSPORTER×19, SMALL_TANK×20, TRANSPORTER×21, SMALL_TANK×21, SOLDIER×22, SOLDIER×22, TRANSPORTER×23, MOTORBIKE×24, SMALL_TANK×24, MOTORBIKE×25, TRANSPORTER×26, TRANSPORTER×26, SOLDIER×27, SOLDIER×27, SMALL_TANK×28, SMALL_TANK×29, SMALL_TANK×29, TRANSPORTER×30 |
| 🟥 | Steam Assault | hardcoded | Industrial 100% | ⬛ 0/16 (0%) | SOLDIER×16 | TRANSPORTER×18, SOLDIER×19, SOLDIER×19, SMALL_TANK×20, TRANSPORTER×21, SOLDIER×21, SOLDIER×22, SMALL_TANK×22, TRANSPORTER×23, SMALL_TANK×24, TRANSPORTER×24, SMALL_TANK×25, SOLDIER×26, TRANSPORTER×26, SMALL_TANK×27, MOTORBIKE×27, SOLDIER×28, TRANSPORTER×29, SOLDIER×29, MOTORBIKE×30 |
| 🟥 | Tank Column | hardcoded | Industrial 100% | ⬛ 0/16 (0%) | SOLDIER×10, MOTORBIKE×2 | SMALL_TANK×18, MOTORBIKE×19, MOTORBIKE×19, TRANSPORTER×20, TRANSPORTER×21, TRANSPORTER×21, SOLDIER×22, MOTORBIKE×22, TRANSPORTER×23, TRANSPORTER×24, SMALL_TANK×24, MOTORBIKE×25, TRANSPORTER×26, SMALL_TANK×26, TRANSPORTER×27, SMALL_TANK×27, TRANSPORTER×28, MOTORBIKE×29, MOTORBIKE×29, SOLDIER×30, SOLDIER×34 |
| 🟥 | Factory Raid | hardcoded | Industrial 88%, Renaissance 12% | ⬛ 0/16 (0%) | SOLDIER×16 | MOTORBIKE×18, MOTORBIKE×20, MOTORBIKE×20, MOTORBIKE×22, SOLDIER×20, TRANSPORTER×21, MOTORBIKE×22, SMALL_TANK×22, SMALL_TANK×25, SOLDIER×24, MOTORBIKE×24, TRANSPORTER×25, SMALL_TANK×26, SMALL_TANK×28, MOTORBIKE×30, CARGO×30, TRANSPORTER×32, DRAGOONER×34, SOLDIER×36, SMALL_TANK×33, SMALL_TANK×36 |
| 🟥 | Lazy Raiders | random | Industrial 84%, Renaissance 8%, Modern 8% | ⬛ 0/16 (0%) | SOLDIER×16 | SIEGE_TANK×28, MOTORBIKE×20, MOTORBIKE×21, MUSKETEER×29, SOLDIER×24, TRANSPORTER×30, SOLDIER×19, TRANSPORTER×20, TRANSPORTER×20, MOTORBIKE×27, TRANSPORTER×20, SMALL_TANK×24, SOLDIER×27, MOTORBIKE×26, SOLDIER×25 |
| 🟥 | Lazy Raiders | random | Industrial 84%, Renaissance 8%, Modern 8% | ⬛ 0/16 (0%) | SOLDIER×16 | SIEGE_TANK×28, MOTORBIKE×20, MOTORBIKE×21, MUSKETEER×29, SOLDIER×24, TRANSPORTER×30, SOLDIER×19, TRANSPORTER×20, TRANSPORTER×20, MOTORBIKE×27, TRANSPORTER×20, SMALL_TANK×24, SOLDIER×27, MOTORBIKE×26, SOLDIER×25 |
| 🟩 | Unlucky Raiders | random | Industrial 89%, Renaissance 11% | 🟡 12/16 (75%) | SOLDIER×4 | TRANSPORTER×30, NINJA×25, SOLDIER×24, MOTORBIKE×29, NINJA×19, SOLDIER×29, SOLDIER×27, SOLDIER×20, SOLDIER×18, SMALL_TANK×32, SOLDIER×31, TRANSPORTER×20, SMALL_TANK×30, SMALL_TANK×24, MOTORBIKE×32 |
| 🟥 | Petty Bandits | random | Industrial 87%, Modern 7%, Renaissance 5% | ⬛ 0/16 (0%) | SPECOPS×8, SOLDIER×2 | TRANSPORTER×30, MOTORBIKE×29, SMALL_TANK×20, SOLDIER×22, MOTORBIKE×25, DRAGOONER×20, SMALL_TANK×26, SOLDIER×28, SMALL_TANK×22, MOTORBIKE×31, TRANSPORTER×20, SOLDIER×30, TRANSPORTER×20, SPECOPS×28, SOLDIER×29 |
| 🟥 | Disorganized Mob | random | Industrial 90%, Renaissance 10% | ⬛ 0/16 (0%) | SOLDIER×16 | MOTORBIKE×23, SMALL_TANK×28, TRANSPORTER×30, THE_KING×10, SOLDIER×25, TRANSPORTER×30, TRANSPORTER×20, SMALL_TANK×20, TRANSPORTER×30, TRANSPORTER×30, MUSKETEER×29, SOLDIER×21, MOTORBIKE×28, MOTORBIKE×28, SMALL_TANK×24, MOTORBIKE×24 |
| 🟩 | Ragged Warband | random | Industrial 78%, Renaissance 22% | 🟢 13/16 (81%) | SOLDIER×3 | SOLDIER×25, SOLDIER×22, SMALL_TANK×28, SMALL_TANK×20, SOLDIER×29, THE_KING×10, MUSKETEER×32, MOTORBIKE×29, CARGO×21, SMALL_TANK×22, MOTORBIKE×31, SMALL_TANK×28, SOLDIER×29, NINJA×19, MOTORBIKE×31 |
| 🟥 | Hungry Invaders | random | Industrial 89%, Renaissance 5%, Modern 5% | ⬛ 0/16 (0%) | SOLDIER×13, HELI×1 | SOLDIER×26, SOLDIER×31, TRANSPORTER×20, SOLDIER×18, CARGO×21, SOLDIER×32, TRANSPORTER×30, TRANSPORTER×30, MOTORBIKE×24, SOLDIER×24, TRANSPORTER×30, HELI×20, TRANSPORTER×30, TRANSPORTER×30, MOTORBIKE×18 |
| 🟥 | Bored Mercenaries | random | Industrial 79%, Modern 17%, Renaissance 3% | ⬛ 0/16 (0%) | SPECOPS×8 | MOTORBIKE×25, SOLDIER×26, SMALL_TANK×22, SPECOPS×29, TRANSPORTER×20, SMALL_TANK×20, SOLDIER×29, SMALL_TANK×22, TRANSPORTER×20, SIEGE_TANK×22, MOTORBIKE×22, THE_KING×10, SMALL_TANK×26 |
| 🟥 | Wandering Pillagers | random | Industrial 80%, Renaissance 20% | ⬛ 0/16 (0%) | SOLDIER×14, SMALL_TANK×1 | MUSKETEER×23, SOLDIER×20, SMALL_TANK×26, SOLDIER×25, SOLDIER×26, SOLDIER×26, DRAGOONER×18, SOLDIER×20, MUSKETEER×22, SOLDIER×25, MOTORBIKE×29, MOTORBIKE×29, TRANSPORTER×30 |
| 🟩 | Crude Invaders | random | Industrial 71%, Renaissance 29% | 🟢 13/16 (81%) | SOLDIER×3 | SMALL_TANK×22, TRANSPORTER×30, SMALL_TANK×28, DRAGOONER×22, NINJA×30, MUSKETEER×30, SMALL_TANK×22, THE_KING×10, MOTORBIKE×25, TRANSPORTER×30, TRANSPORTER×20, SMALL_TANK×26, TRANSPORTER×20 |
| 🟥 | Grumpy Marauders | random | Industrial 62%, Renaissance 26%, Modern 11% | ⬛ 0/16 (0%) | SOLDIER×16 | TRANSPORTER×30, TRANSPORTER×30, SOLDIER×23, TRANSPORTER×20, NINJA×23, SIEGE_TANK×20, MUSKETEER×19, TRANSPORTER×20, MUSKETEER×22, SOLDIER×23, MOTORBIKE×24, DRAGOONER×24, HELI×18, MOTORBIKE×21, SOLDIER×18 |
| 🟩 | Rampaging Rabble | random | Industrial 73%, Renaissance 20%, Modern 8% | 🟢 16/16 (100%) |  | SMALL_TANK×24, SMALL_TANK×26, SMALL_TANK×30, MOTORBIKE×24, DRAGOONER×22, CARGO×30, DRAGOONER×22, SOLDIER×20, SOLDIER×26, SMALL_TANK×28, MOTORBIKE×25, MOTORBIKE×26, SMALL_TANK×20, TRANSPORTER×20, SIEGE_TANK×28 |
| 🟩 | Frenzied Pillagers | random | Industrial 90%, Modern 7%, Renaissance 3% | 🟡 12/16 (75%) | SOLDIER×4 | SMALL_TANK×28, MOTORBIKE×21, SOLDIER×22, TRANSPORTER×20, SMALL_TANK×18, SOLDIER×24, SOLDIER×28, TRANSPORTER×20, SIEGE_TANK×22, THE_KING×10, SMALL_TANK×26, TRANSPORTER×30, SMALL_TANK×26, TRANSPORTER×20 |
| 🟥 | Unlucky Raiders | random | Industrial 88%, Renaissance 12% | ⬛ 0/16 (0%) | SOLDIER×16 | MUSKETEER×31, SMALL_TANK×22, THE_KING×10, MOTORBIKE×26, MOTORBIKE×19, SOLDIER×19, SMALL_TANK×24, MOTORBIKE×19, SOLDIER×19, SMALL_TANK×20, TRANSPORTER×30, TRANSPORTER×20, MOTORBIKE×26, SOLDIER×28, SOLDIER×26 |
| 🟩 | Bored Mercenaries | random | Industrial 81%, Renaissance 12%, Modern 7% | 🟢 14/16 (88%) | SOLDIER×2 | HELI×22, TRANSPORTER×30, NINJA×19, SOLDIER×29, MOTORBIKE×27, CARGO×21, SMALL_TANK×22, MOTORBIKE×24, SOLDIER×20, TRANSPORTER×20, MOTORBIKE×21, TRANSPORTER×20, TRANSPORTER×20, SOLDIER×31 |
| 🟩 | Muddy Marauders | random | Industrial 82%, Renaissance 11%, Modern 7% | 🟡 10/16 (62%) | SOLDIER×6 | MOTORBIKE×23, SMALL_TANK×32, MOTORBIKE×19, THE_KING×10, HELI×20, TRANSPORTER×20, MUSKETEER×20, SOLDIER×25, MOTORBIKE×21, SMALL_TANK×22, MOTORBIKE×19, MOTORBIKE×18, TRANSPORTER×30 |
| 🟥 | Weary Plunderers | random | Industrial 79%, Modern 16%, Renaissance 5% | ⬛ 0/16 (0%) | SOLDIER×10, SIEGE_TANK×3 | SMALL_TANK×30, SOLDIER×31, SOLDIER×28, MOTORBIKE×23, SMALL_TANK×20, SOLDIER×22, MOTORBIKE×26, SIEGE_TANK×30, TRANSPORTER×20, SIEGE_TANK×30, MOTORBIKE×30, DRAGOONER×20, TRANSPORTER×20, TRANSPORTER×20, MOTORBIKE×27 |
| 🟥 | Restless Horde | random | Industrial 87%, Renaissance 7%, Modern 6% | ⬛ 0/16 (0%) | MOTORBIKE×4, SOLDIER×4 | MOTORBIKE×21, SMALL_TANK×26, SMALL_TANK×22, SMALL_TANK×22, SMALL_TANK×26, SOLDIER×19, SOLDIER×27, SOLDIER×30, MOTORBIKE×19, MOTORBIKE×28, DRAGOONER×26, SMALL_TANK×30, SIEGE_TANK×22, TRANSPORTER×20, MOTORBIKE×24 |
| 🟥 | Crude Invaders | random | Industrial 73%, Renaissance 20%, Modern 6% | ⬛ 0/16 (0%) | SPECOPS×8 | SMALL_TANK×24, SMALL_TANK×20, SMALL_TANK×28, SOLDIER×29, SOLDIER×31, CARGO×21, DRAGOONER×20, SMALL_TANK×30, SPECOPS×22, MOTORBIKE×20, TRANSPORTER×20, SOLDIER×20, NINJA×29, MOTORBIKE×27 |
| 🟥 | Disorganized Mob | random | Industrial 80%, Renaissance 11%, Modern 10% | ⬛ 0/16 (0%) | SOLDIER×16 | SOLDIER×19, SIEGE_TANK×30, SMALL_TANK×28, TRANSPORTER×20, TRANSPORTER×30, MOTORBIKE×26, SOLDIER×19, SMALL_TANK×26, MOTORBIKE×27, MOTORBIKE×26, THE_KING×10, DRAGOONER×22, TRANSPORTER×20 |

#### Full Gatling

| Tower Era Distribution (60 towers) | Towers |
|---|---|
| Industrial 82% (49), Renaissance 17% (10), Iron Age 2% (1) | GATLING_TOWER×42, ICE_TOWER×10, FLAME_THROWER×4, SHOCK_TOWER×3, COLD_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Industrial March | hardcoded | Industrial 98%, Modern 2% | 🟢 58/58 (100%) |  | SOLDIER×16, SOLDIER×17, MOTORBIKE×17, TRANSPORTER×18, TRANSPORTER×19, SMALL_TANK×19, TRANSPORTER×20, TRANSPORTER×21, SMALL_TANK×21, SMALL_TANK×22, MOTORBIKE×23, MOTORBIKE×23, SPECOPS×10, MOTORBIKE×28, SMALL_TANK×30, SOLDIER×32, SOLDIER×34, MOTORBIKE×36 |
| 🟩 | Mechanized Strike | hardcoded | Industrial 100% | 🟢 58/58 (100%) |  | SOLDIER×18, SMALL_TANK×19, TRANSPORTER×19, SMALL_TANK×20, TRANSPORTER×21, SMALL_TANK×21, SOLDIER×22, SOLDIER×22, TRANSPORTER×23, MOTORBIKE×24, SMALL_TANK×24, MOTORBIKE×25, TRANSPORTER×26, TRANSPORTER×26, SOLDIER×27, SOLDIER×27, SMALL_TANK×28, SMALL_TANK×29, SMALL_TANK×29, TRANSPORTER×30 |
| 🟩 | Steam Assault | hardcoded | Industrial 100% | 🟢 58/58 (100%) |  | TRANSPORTER×18, SOLDIER×19, SOLDIER×19, SMALL_TANK×20, TRANSPORTER×21, SOLDIER×21, SOLDIER×22, SMALL_TANK×22, TRANSPORTER×23, SMALL_TANK×24, TRANSPORTER×24, SMALL_TANK×25, SOLDIER×26, TRANSPORTER×26, SMALL_TANK×27, MOTORBIKE×27, SOLDIER×28, TRANSPORTER×29, SOLDIER×29, MOTORBIKE×30 |
| 🟩 | Tank Column | hardcoded | Industrial 100% | 🟢 58/58 (100%) |  | SMALL_TANK×18, MOTORBIKE×19, MOTORBIKE×19, TRANSPORTER×20, TRANSPORTER×21, TRANSPORTER×21, SOLDIER×22, MOTORBIKE×22, TRANSPORTER×23, TRANSPORTER×24, SMALL_TANK×24, MOTORBIKE×25, TRANSPORTER×26, SMALL_TANK×26, TRANSPORTER×27, SMALL_TANK×27, TRANSPORTER×28, MOTORBIKE×29, MOTORBIKE×29, SOLDIER×30, SOLDIER×34 |
| 🟩 | Factory Raid | hardcoded | Industrial 88%, Renaissance 12% | 🟢 58/58 (100%) |  | MOTORBIKE×18, MOTORBIKE×20, MOTORBIKE×20, MOTORBIKE×22, SOLDIER×20, TRANSPORTER×21, MOTORBIKE×22, SMALL_TANK×22, SMALL_TANK×25, SOLDIER×24, MOTORBIKE×24, TRANSPORTER×25, SMALL_TANK×26, SMALL_TANK×28, MOTORBIKE×30, CARGO×30, TRANSPORTER×32, DRAGOONER×34, SOLDIER×36, SMALL_TANK×33, SMALL_TANK×36 |
| 🟩 | Lazy Raiders | random | Industrial 84%, Renaissance 8%, Modern 8% | 🟢 58/58 (100%) |  | SIEGE_TANK×28, MOTORBIKE×20, MOTORBIKE×21, MUSKETEER×29, SOLDIER×24, TRANSPORTER×30, SOLDIER×19, TRANSPORTER×20, TRANSPORTER×20, MOTORBIKE×27, TRANSPORTER×20, SMALL_TANK×24, SOLDIER×27, MOTORBIKE×26, SOLDIER×25 |
| 🟩 | Lazy Raiders | random | Industrial 84%, Renaissance 8%, Modern 8% | 🟢 58/58 (100%) |  | SIEGE_TANK×28, MOTORBIKE×20, MOTORBIKE×21, MUSKETEER×29, SOLDIER×24, TRANSPORTER×30, SOLDIER×19, TRANSPORTER×20, TRANSPORTER×20, MOTORBIKE×27, TRANSPORTER×20, SMALL_TANK×24, SOLDIER×27, MOTORBIKE×26, SOLDIER×25 |
| 🟩 | Unlucky Raiders | random | Industrial 89%, Renaissance 11% | 🟢 58/58 (100%) |  | TRANSPORTER×30, NINJA×25, SOLDIER×24, MOTORBIKE×29, NINJA×19, SOLDIER×29, SOLDIER×27, SOLDIER×20, SOLDIER×18, SMALL_TANK×32, SOLDIER×31, TRANSPORTER×20, SMALL_TANK×30, SMALL_TANK×24, MOTORBIKE×32 |
| 🟩 | Petty Bandits | random | Industrial 87%, Modern 7%, Renaissance 5% | 🟢 50/58 (86%) | SPECOPS×4 | TRANSPORTER×30, MOTORBIKE×29, SMALL_TANK×20, SOLDIER×22, MOTORBIKE×25, DRAGOONER×20, SMALL_TANK×26, SOLDIER×28, SMALL_TANK×22, MOTORBIKE×31, TRANSPORTER×20, SOLDIER×30, TRANSPORTER×20, SPECOPS×28, SOLDIER×29 |
| 🟩 | Disorganized Mob | random | Industrial 90%, Renaissance 10% | 🟢 58/58 (100%) |  | MOTORBIKE×23, SMALL_TANK×28, TRANSPORTER×30, THE_KING×10, SOLDIER×25, TRANSPORTER×30, TRANSPORTER×20, SMALL_TANK×20, TRANSPORTER×30, TRANSPORTER×30, MUSKETEER×29, SOLDIER×21, MOTORBIKE×28, MOTORBIKE×28, SMALL_TANK×24, MOTORBIKE×24 |
| 🟩 | Ragged Warband | random | Industrial 78%, Renaissance 22% | 🟢 58/58 (100%) |  | SOLDIER×25, SOLDIER×22, SMALL_TANK×28, SMALL_TANK×20, SOLDIER×29, THE_KING×10, MUSKETEER×32, MOTORBIKE×29, CARGO×21, SMALL_TANK×22, MOTORBIKE×31, SMALL_TANK×28, SOLDIER×29, NINJA×19, MOTORBIKE×31 |
| 🟩 | Hungry Invaders | random | Industrial 89%, Renaissance 5%, Modern 5% | 🟢 58/58 (100%) |  | SOLDIER×26, SOLDIER×31, TRANSPORTER×20, SOLDIER×18, CARGO×21, SOLDIER×32, TRANSPORTER×30, TRANSPORTER×30, MOTORBIKE×24, SOLDIER×24, TRANSPORTER×30, HELI×20, TRANSPORTER×30, TRANSPORTER×30, MOTORBIKE×18 |
| 🟩 | Bored Mercenaries | random | Industrial 79%, Modern 17%, Renaissance 3% | 🟡 40/58 (69%) | SPECOPS×9 | MOTORBIKE×25, SOLDIER×26, SMALL_TANK×22, SPECOPS×29, TRANSPORTER×20, SMALL_TANK×20, SOLDIER×29, SMALL_TANK×22, TRANSPORTER×20, SIEGE_TANK×22, MOTORBIKE×22, THE_KING×10, SMALL_TANK×26 |
| 🟩 | Wandering Pillagers | random | Industrial 80%, Renaissance 20% | 🟢 58/58 (100%) |  | MUSKETEER×23, SOLDIER×20, SMALL_TANK×26, SOLDIER×25, SOLDIER×26, SOLDIER×26, DRAGOONER×18, SOLDIER×20, MUSKETEER×22, SOLDIER×25, MOTORBIKE×29, MOTORBIKE×29, TRANSPORTER×30 |
| 🟩 | Crude Invaders | random | Industrial 71%, Renaissance 29% | 🟢 58/58 (100%) |  | SMALL_TANK×22, TRANSPORTER×30, SMALL_TANK×28, DRAGOONER×22, NINJA×30, MUSKETEER×30, SMALL_TANK×22, THE_KING×10, MOTORBIKE×25, TRANSPORTER×30, TRANSPORTER×20, SMALL_TANK×26, TRANSPORTER×20 |
| 🟩 | Grumpy Marauders | random | Industrial 62%, Renaissance 26%, Modern 11% | 🟢 58/58 (100%) |  | TRANSPORTER×30, TRANSPORTER×30, SOLDIER×23, TRANSPORTER×20, NINJA×23, SIEGE_TANK×20, MUSKETEER×19, TRANSPORTER×20, MUSKETEER×22, SOLDIER×23, MOTORBIKE×24, DRAGOONER×24, HELI×18, MOTORBIKE×21, SOLDIER×18 |
| 🟩 | Rampaging Rabble | random | Industrial 73%, Renaissance 20%, Modern 8% | 🟢 58/58 (100%) |  | SMALL_TANK×24, SMALL_TANK×26, SMALL_TANK×30, MOTORBIKE×24, DRAGOONER×22, CARGO×30, DRAGOONER×22, SOLDIER×20, SOLDIER×26, SMALL_TANK×28, MOTORBIKE×25, MOTORBIKE×26, SMALL_TANK×20, TRANSPORTER×20, SIEGE_TANK×28 |
| 🟩 | Frenzied Pillagers | random | Industrial 90%, Modern 7%, Renaissance 3% | 🟢 58/58 (100%) |  | SMALL_TANK×28, MOTORBIKE×21, SOLDIER×22, TRANSPORTER×20, SMALL_TANK×18, SOLDIER×24, SOLDIER×28, TRANSPORTER×20, SIEGE_TANK×22, THE_KING×10, SMALL_TANK×26, TRANSPORTER×30, SMALL_TANK×26, TRANSPORTER×20 |
| 🟩 | Unlucky Raiders | random | Industrial 88%, Renaissance 12% | 🟢 58/58 (100%) |  | MUSKETEER×31, SMALL_TANK×22, THE_KING×10, MOTORBIKE×26, MOTORBIKE×19, SOLDIER×19, SMALL_TANK×24, MOTORBIKE×19, SOLDIER×19, SMALL_TANK×20, TRANSPORTER×30, TRANSPORTER×20, MOTORBIKE×26, SOLDIER×28, SOLDIER×26 |
| 🟩 | Bored Mercenaries | random | Industrial 81%, Renaissance 12%, Modern 7% | 🟢 58/58 (100%) |  | HELI×22, TRANSPORTER×30, NINJA×19, SOLDIER×29, MOTORBIKE×27, CARGO×21, SMALL_TANK×22, MOTORBIKE×24, SOLDIER×20, TRANSPORTER×20, MOTORBIKE×21, TRANSPORTER×20, TRANSPORTER×20, SOLDIER×31 |
| 🟩 | Muddy Marauders | random | Industrial 82%, Renaissance 11%, Modern 7% | 🟢 58/58 (100%) |  | MOTORBIKE×23, SMALL_TANK×32, MOTORBIKE×19, THE_KING×10, HELI×20, TRANSPORTER×20, MUSKETEER×20, SOLDIER×25, MOTORBIKE×21, SMALL_TANK×22, MOTORBIKE×19, MOTORBIKE×18, TRANSPORTER×30 |
| 🟩 | Weary Plunderers | random | Industrial 79%, Modern 16%, Renaissance 5% | 🟢 54/58 (93%) | SIEGE_TANK×2 | SMALL_TANK×30, SOLDIER×31, SOLDIER×28, MOTORBIKE×23, SMALL_TANK×20, SOLDIER×22, MOTORBIKE×26, SIEGE_TANK×30, TRANSPORTER×20, SIEGE_TANK×30, MOTORBIKE×30, DRAGOONER×20, TRANSPORTER×20, TRANSPORTER×20, MOTORBIKE×27 |
| 🟩 | Restless Horde | random | Industrial 87%, Renaissance 7%, Modern 6% | 🟢 58/58 (100%) |  | MOTORBIKE×21, SMALL_TANK×26, SMALL_TANK×22, SMALL_TANK×22, SMALL_TANK×26, SOLDIER×19, SOLDIER×27, SOLDIER×30, MOTORBIKE×19, MOTORBIKE×28, DRAGOONER×26, SMALL_TANK×30, SIEGE_TANK×22, TRANSPORTER×20, MOTORBIKE×24 |
| 🟩 | Crude Invaders | random | Industrial 73%, Renaissance 20%, Modern 6% | 🟢 58/58 (100%) |  | SMALL_TANK×24, SMALL_TANK×20, SMALL_TANK×28, SOLDIER×29, SOLDIER×31, CARGO×21, DRAGOONER×20, SMALL_TANK×30, SPECOPS×22, MOTORBIKE×20, TRANSPORTER×20, SOLDIER×20, NINJA×29, MOTORBIKE×27 |
| 🟩 | Disorganized Mob | random | Industrial 80%, Renaissance 11%, Modern 10% | 🟡 40/58 (69%) | SIEGE_TANK×9 | SOLDIER×19, SIEGE_TANK×30, SMALL_TANK×28, TRANSPORTER×20, TRANSPORTER×30, MOTORBIKE×26, SOLDIER×19, SMALL_TANK×26, MOTORBIKE×27, MOTORBIKE×26, THE_KING×10, DRAGOONER×22, TRANSPORTER×20 |

#### Mixed

| Tower Era Distribution (61 towers) | Towers |
|---|---|
| Industrial 92% (56), Renaissance 7% (4), Iron Age 2% (1) | FLAME_THROWER×26, SHOCK_TOWER×19, GATLING_TOWER×11, ICE_TOWER×4, COLD_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Industrial March | hardcoded | Industrial 98%, Modern 2% | 🟢 28/28 (100%) |  | SOLDIER×16, SOLDIER×17, MOTORBIKE×17, TRANSPORTER×18, TRANSPORTER×19, SMALL_TANK×19, TRANSPORTER×20, TRANSPORTER×21, SMALL_TANK×21, SMALL_TANK×22, MOTORBIKE×23, MOTORBIKE×23, SPECOPS×10, MOTORBIKE×28, SMALL_TANK×30, SOLDIER×32, SOLDIER×34, MOTORBIKE×36 |
| 🟩 | Mechanized Strike | hardcoded | Industrial 100% | 🟢 28/28 (100%) |  | SOLDIER×18, SMALL_TANK×19, TRANSPORTER×19, SMALL_TANK×20, TRANSPORTER×21, SMALL_TANK×21, SOLDIER×22, SOLDIER×22, TRANSPORTER×23, MOTORBIKE×24, SMALL_TANK×24, MOTORBIKE×25, TRANSPORTER×26, TRANSPORTER×26, SOLDIER×27, SOLDIER×27, SMALL_TANK×28, SMALL_TANK×29, SMALL_TANK×29, TRANSPORTER×30 |
| 🟩 | Steam Assault | hardcoded | Industrial 100% | 🟢 28/28 (100%) |  | TRANSPORTER×18, SOLDIER×19, SOLDIER×19, SMALL_TANK×20, TRANSPORTER×21, SOLDIER×21, SOLDIER×22, SMALL_TANK×22, TRANSPORTER×23, SMALL_TANK×24, TRANSPORTER×24, SMALL_TANK×25, SOLDIER×26, TRANSPORTER×26, SMALL_TANK×27, MOTORBIKE×27, SOLDIER×28, TRANSPORTER×29, SOLDIER×29, MOTORBIKE×30 |
| 🟩 | Tank Column | hardcoded | Industrial 100% | 🟢 28/28 (100%) |  | SMALL_TANK×18, MOTORBIKE×19, MOTORBIKE×19, TRANSPORTER×20, TRANSPORTER×21, TRANSPORTER×21, SOLDIER×22, MOTORBIKE×22, TRANSPORTER×23, TRANSPORTER×24, SMALL_TANK×24, MOTORBIKE×25, TRANSPORTER×26, SMALL_TANK×26, TRANSPORTER×27, SMALL_TANK×27, TRANSPORTER×28, MOTORBIKE×29, MOTORBIKE×29, SOLDIER×30, SOLDIER×34 |
| 🟩 | Factory Raid | hardcoded | Industrial 88%, Renaissance 12% | 🟢 28/28 (100%) |  | MOTORBIKE×18, MOTORBIKE×20, MOTORBIKE×20, MOTORBIKE×22, SOLDIER×20, TRANSPORTER×21, MOTORBIKE×22, SMALL_TANK×22, SMALL_TANK×25, SOLDIER×24, MOTORBIKE×24, TRANSPORTER×25, SMALL_TANK×26, SMALL_TANK×28, MOTORBIKE×30, CARGO×30, TRANSPORTER×32, DRAGOONER×34, SOLDIER×36, SMALL_TANK×33, SMALL_TANK×36 |
| 🟩 | Lazy Raiders | random | Industrial 84%, Renaissance 8%, Modern 8% | 🟢 28/28 (100%) |  | SIEGE_TANK×28, MOTORBIKE×20, MOTORBIKE×21, MUSKETEER×29, SOLDIER×24, TRANSPORTER×30, SOLDIER×19, TRANSPORTER×20, TRANSPORTER×20, MOTORBIKE×27, TRANSPORTER×20, SMALL_TANK×24, SOLDIER×27, MOTORBIKE×26, SOLDIER×25 |
| 🟩 | Lazy Raiders | random | Industrial 84%, Renaissance 8%, Modern 8% | 🟢 28/28 (100%) |  | SIEGE_TANK×28, MOTORBIKE×20, MOTORBIKE×21, MUSKETEER×29, SOLDIER×24, TRANSPORTER×30, SOLDIER×19, TRANSPORTER×20, TRANSPORTER×20, MOTORBIKE×27, TRANSPORTER×20, SMALL_TANK×24, SOLDIER×27, MOTORBIKE×26, SOLDIER×25 |
| 🟩 | Unlucky Raiders | random | Industrial 89%, Renaissance 11% | 🟢 28/28 (100%) |  | TRANSPORTER×30, NINJA×25, SOLDIER×24, MOTORBIKE×29, NINJA×19, SOLDIER×29, SOLDIER×27, SOLDIER×20, SOLDIER×18, SMALL_TANK×32, SOLDIER×31, TRANSPORTER×20, SMALL_TANK×30, SMALL_TANK×24, MOTORBIKE×32 |
| 🟩 | Petty Bandits | random | Industrial 87%, Modern 7%, Renaissance 5% | 🟢 28/28 (100%) |  | TRANSPORTER×30, MOTORBIKE×29, SMALL_TANK×20, SOLDIER×22, MOTORBIKE×25, DRAGOONER×20, SMALL_TANK×26, SOLDIER×28, SMALL_TANK×22, MOTORBIKE×31, TRANSPORTER×20, SOLDIER×30, TRANSPORTER×20, SPECOPS×28, SOLDIER×29 |
| 🟩 | Disorganized Mob | random | Industrial 90%, Renaissance 10% | 🟢 28/28 (100%) |  | MOTORBIKE×23, SMALL_TANK×28, TRANSPORTER×30, THE_KING×10, SOLDIER×25, TRANSPORTER×30, TRANSPORTER×20, SMALL_TANK×20, TRANSPORTER×30, TRANSPORTER×30, MUSKETEER×29, SOLDIER×21, MOTORBIKE×28, MOTORBIKE×28, SMALL_TANK×24, MOTORBIKE×24 |
| 🟩 | Ragged Warband | random | Industrial 78%, Renaissance 22% | 🟢 28/28 (100%) |  | SOLDIER×25, SOLDIER×22, SMALL_TANK×28, SMALL_TANK×20, SOLDIER×29, THE_KING×10, MUSKETEER×32, MOTORBIKE×29, CARGO×21, SMALL_TANK×22, MOTORBIKE×31, SMALL_TANK×28, SOLDIER×29, NINJA×19, MOTORBIKE×31 |
| 🟩 | Hungry Invaders | random | Industrial 89%, Renaissance 5%, Modern 5% | 🟢 28/28 (100%) |  | SOLDIER×26, SOLDIER×31, TRANSPORTER×20, SOLDIER×18, CARGO×21, SOLDIER×32, TRANSPORTER×30, TRANSPORTER×30, MOTORBIKE×24, SOLDIER×24, TRANSPORTER×30, HELI×20, TRANSPORTER×30, TRANSPORTER×30, MOTORBIKE×18 |
| 🟩 | Bored Mercenaries | random | Industrial 79%, Modern 17%, Renaissance 3% | 🟢 28/28 (100%) |  | MOTORBIKE×25, SOLDIER×26, SMALL_TANK×22, SPECOPS×29, TRANSPORTER×20, SMALL_TANK×20, SOLDIER×29, SMALL_TANK×22, TRANSPORTER×20, SIEGE_TANK×22, MOTORBIKE×22, THE_KING×10, SMALL_TANK×26 |
| 🟩 | Wandering Pillagers | random | Industrial 80%, Renaissance 20% | 🟢 28/28 (100%) |  | MUSKETEER×23, SOLDIER×20, SMALL_TANK×26, SOLDIER×25, SOLDIER×26, SOLDIER×26, DRAGOONER×18, SOLDIER×20, MUSKETEER×22, SOLDIER×25, MOTORBIKE×29, MOTORBIKE×29, TRANSPORTER×30 |
| 🟩 | Crude Invaders | random | Industrial 71%, Renaissance 29% | 🟢 28/28 (100%) |  | SMALL_TANK×22, TRANSPORTER×30, SMALL_TANK×28, DRAGOONER×22, NINJA×30, MUSKETEER×30, SMALL_TANK×22, THE_KING×10, MOTORBIKE×25, TRANSPORTER×30, TRANSPORTER×20, SMALL_TANK×26, TRANSPORTER×20 |
| 🟩 | Grumpy Marauders | random | Industrial 62%, Renaissance 26%, Modern 11% | 🟢 28/28 (100%) |  | TRANSPORTER×30, TRANSPORTER×30, SOLDIER×23, TRANSPORTER×20, NINJA×23, SIEGE_TANK×20, MUSKETEER×19, TRANSPORTER×20, MUSKETEER×22, SOLDIER×23, MOTORBIKE×24, DRAGOONER×24, HELI×18, MOTORBIKE×21, SOLDIER×18 |
| 🟩 | Rampaging Rabble | random | Industrial 73%, Renaissance 20%, Modern 8% | 🟢 28/28 (100%) |  | SMALL_TANK×24, SMALL_TANK×26, SMALL_TANK×30, MOTORBIKE×24, DRAGOONER×22, CARGO×30, DRAGOONER×22, SOLDIER×20, SOLDIER×26, SMALL_TANK×28, MOTORBIKE×25, MOTORBIKE×26, SMALL_TANK×20, TRANSPORTER×20, SIEGE_TANK×28 |
| 🟩 | Frenzied Pillagers | random | Industrial 90%, Modern 7%, Renaissance 3% | 🟢 28/28 (100%) |  | SMALL_TANK×28, MOTORBIKE×21, SOLDIER×22, TRANSPORTER×20, SMALL_TANK×18, SOLDIER×24, SOLDIER×28, TRANSPORTER×20, SIEGE_TANK×22, THE_KING×10, SMALL_TANK×26, TRANSPORTER×30, SMALL_TANK×26, TRANSPORTER×20 |
| 🟩 | Unlucky Raiders | random | Industrial 88%, Renaissance 12% | 🟢 28/28 (100%) |  | MUSKETEER×31, SMALL_TANK×22, THE_KING×10, MOTORBIKE×26, MOTORBIKE×19, SOLDIER×19, SMALL_TANK×24, MOTORBIKE×19, SOLDIER×19, SMALL_TANK×20, TRANSPORTER×30, TRANSPORTER×20, MOTORBIKE×26, SOLDIER×28, SOLDIER×26 |
| 🟩 | Bored Mercenaries | random | Industrial 81%, Renaissance 12%, Modern 7% | 🟢 28/28 (100%) |  | HELI×22, TRANSPORTER×30, NINJA×19, SOLDIER×29, MOTORBIKE×27, CARGO×21, SMALL_TANK×22, MOTORBIKE×24, SOLDIER×20, TRANSPORTER×20, MOTORBIKE×21, TRANSPORTER×20, TRANSPORTER×20, SOLDIER×31 |
| 🟩 | Muddy Marauders | random | Industrial 82%, Renaissance 11%, Modern 7% | 🟢 28/28 (100%) |  | MOTORBIKE×23, SMALL_TANK×32, MOTORBIKE×19, THE_KING×10, HELI×20, TRANSPORTER×20, MUSKETEER×20, SOLDIER×25, MOTORBIKE×21, SMALL_TANK×22, MOTORBIKE×19, MOTORBIKE×18, TRANSPORTER×30 |
| 🟩 | Weary Plunderers | random | Industrial 79%, Modern 16%, Renaissance 5% | 🟢 28/28 (100%) |  | SMALL_TANK×30, SOLDIER×31, SOLDIER×28, MOTORBIKE×23, SMALL_TANK×20, SOLDIER×22, MOTORBIKE×26, SIEGE_TANK×30, TRANSPORTER×20, SIEGE_TANK×30, MOTORBIKE×30, DRAGOONER×20, TRANSPORTER×20, TRANSPORTER×20, MOTORBIKE×27 |
| 🟩 | Restless Horde | random | Industrial 87%, Renaissance 7%, Modern 6% | 🟢 28/28 (100%) |  | MOTORBIKE×21, SMALL_TANK×26, SMALL_TANK×22, SMALL_TANK×22, SMALL_TANK×26, SOLDIER×19, SOLDIER×27, SOLDIER×30, MOTORBIKE×19, MOTORBIKE×28, DRAGOONER×26, SMALL_TANK×30, SIEGE_TANK×22, TRANSPORTER×20, MOTORBIKE×24 |
| 🟩 | Crude Invaders | random | Industrial 73%, Renaissance 20%, Modern 6% | 🟢 28/28 (100%) |  | SMALL_TANK×24, SMALL_TANK×20, SMALL_TANK×28, SOLDIER×29, SOLDIER×31, CARGO×21, DRAGOONER×20, SMALL_TANK×30, SPECOPS×22, MOTORBIKE×20, TRANSPORTER×20, SOLDIER×20, NINJA×29, MOTORBIKE×27 |
| 🟩 | Disorganized Mob | random | Industrial 80%, Renaissance 11%, Modern 10% | 🟢 28/28 (100%) |  | SOLDIER×19, SIEGE_TANK×30, SMALL_TANK×28, TRANSPORTER×20, TRANSPORTER×30, MOTORBIKE×26, SOLDIER×19, SMALL_TANK×26, MOTORBIKE×27, MOTORBIKE×26, THE_KING×10, DRAGOONER×22, TRANSPORTER×20 |

### Modern

#### Short Mixed Modern

| Tower Era Distribution (51 towers) | Towers |
|---|---|
| Modern 88% (45), Industrial 12% (6) | MG_TOWER×21, RADAR_TOWER×12, NAPALM_THROWER×6, SHOCK_TOWER×6, PARALYZNG_TOWER×6 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Modern Warfare | hardcoded | Modern 82%, Industrial 14%, Future 4% | 🟠 21/48 (44%) | SPECOPS×10, SOLDIER×7 | SPECOPS×18, SIEGE_TANK×18, SIEGE_TANK×19, HELI×20, HELI×20, SIEGE_TANK×20, SPECOPS×21, SIEGE_TANK×22, SPECOPS×22, SPECOPS×22, SPECOPS×23, SIEGE_TANK×24, HELI×24, SIEGE_TANK×24, DRONE×25, SIEGE_TANK×26, SPECOPS×26, TRANSPORTER×26, HELI×27, SIEGE_TANK×28, TRANSPORTER×28, SPECOPS×28, HELI×29, SMALL_TANK×30, THE_GENERAL×40 |
| 🟩 | Special Ops | hardcoded | Modern 91%, Industrial 5%, Future 4% | 🔴 8/48 (17%) | SPECOPS×9, SOLDIER×6, MECH_WARRIOR×4 | HELI×18, HELI×18, SPECOPS×19, SIEGE_TANK×20, SIEGE_TANK×20, SIEGE_TANK×20, SPECOPS×21, SPECOPS×22, SPECOPS×22, HELI×22, SIEGE_TANK×23, SPECOPS×24, SIEGE_TANK×24, HELI×24, HELI×25, MECH_WARRIOR×26, SPECOPS×26, SIEGE_TANK×26, SPECOPS×27, HELI×28, SPECOPS×28, TRANSPORTER×28, HELI×29, SIEGE_TANK×30, THE_GENERAL×36 |
| 🟩 | Heli Strike | hardcoded | Modern 84%, Industrial 16% | 🟢 48/48 (100%) |  | HELI×18, SPECOPS×18, HELI×19, SPECOPS×20, HELI×20, SPECOPS×20, SPECOPS×21, SPECOPS×22, TRANSPORTER×22, SPECOPS×22, SPECOPS×23, SIEGE_TANK×24, HELI×24, TRANSPORTER×24, SIEGE_TANK×25, HELI×26, SPECOPS×26, MOTORBIKE×26, SPECOPS×27, HELI×28, TRANSPORTER×28, HELI×28, HELI×29, SIEGE_TANK×30, SPECOPS×30, THE_GENERAL×35 |
| 🟩 | Siege Assault | hardcoded | Modern 84%, Industrial 13%, Renaissance 4% | 🟡 31/48 (65%) | SOLDIER×7, SPECOPS×5 | SIEGE_TANK×18, SIEGE_TANK×18, SIEGE_TANK×19, SPECOPS×20, HELI×20, SPECOPS×20, TRANSPORTER×21, SIEGE_TANK×22, NINJA×22, HELI×22, SIEGE_TANK×23, SIEGE_TANK×24, SOLDIER×24, SPECOPS×24, SIEGE_TANK×25, SPECOPS×26, SPECOPS×26, HELI×26, SIEGE_TANK×27, TRANSPORTER×28, HELI×28, SIEGE_TANK×29, SPECOPS×30, THE_GENERAL×40 |
| 🟩 | Urban Combat | hardcoded | Modern 91%, Industrial 9% | 🟡 28/48 (58%) | SOLDIER×8, SPECOPS×6 | SPECOPS×18, SIEGE_TANK×18, SPECOPS×19, THE_GENERAL×20, SPECOPS×20, SPECOPS×20, HELI×21, SPECOPS×22, SPECOPS×22, SIEGE_TANK×22, SIEGE_TANK×23, SIEGE_TANK×24, SPECOPS×24, SOLDIER×24, SPECOPS×25, SPECOPS×26, SIEGE_TANK×26, HELI×26, SPECOPS×27, HELI×28, SPECOPS×28, HELI×28, TRANSPORTER×29, HELI×30 |
| 🟩 | Cyber Strike | hardcoded | Modern 100% | 🟡 25/48 (52%) | SPECOPS×8, SOLDIER×7 | SIEGE_TANK×18, HELI×18, HELI×19, SPECOPS×19, SPECOPS×20, SPECOPS×20, SIEGE_TANK×21, SPECOPS×21, SPECOPS×21, SIEGE_TANK×22, SPECOPS×22, SPECOPS×23, SPECOPS×23, SIEGE_TANK×24, SIEGE_TANK×24, SIEGE_TANK×24, HELI×25, SPECOPS×25, HELI×26, SIEGE_TANK×26, SPECOPS×27, SPECOPS×27, HELI×27, SIEGE_TANK×28, THE_GENERAL×35 |
| 🟥 | Rampaging Rabble | random | Modern 87%, Future 13% | ⬛ 0/48 (0%) | SPECOPS×8, MECH_WARRIOR×7, THE_GENERAL×1 | SPECOPS×31, SIEGE_TANK×22, MECH_WARRIOR×28, SPECOPS×21, THE_GENERAL×18, SIEGE_TANK×26, SIEGE_TANK×26, SPECOPS×31, SPECOPS×30, SPECOPS×27, SPECOPS×28, HELI×24, SIEGE_TANK×22, SPECOPS×34, MECH_WARRIOR×24, SIEGE_TANK×22 |
| 🟥 | Rampaging Rabble | random | Modern 87%, Future 13% | ⬛ 0/48 (0%) | SPECOPS×8, MECH_WARRIOR×7, THE_GENERAL×1 | SPECOPS×31, SIEGE_TANK×22, MECH_WARRIOR×28, SPECOPS×21, THE_GENERAL×18, SIEGE_TANK×26, SIEGE_TANK×26, SPECOPS×31, SPECOPS×30, SPECOPS×27, SPECOPS×28, HELI×24, SIEGE_TANK×22, SPECOPS×34, MECH_WARRIOR×24, SIEGE_TANK×22 |
| 🟩 | Petty Bandits | random | Modern 87%, Future 7%, Industrial 6% | 🟢 48/48 (100%) |  | THE_GENERAL×18, SPECOPS×22, SPECOPS×31, SIEGE_TANK×32, HELI×20, HELI×26, DRONE×27, SIEGE_TANK×26, HELI×20, SIEGE_TANK×34, SPECOPS×29, MOTORBIKE×25, SIEGE_TANK×22, HELI×24, HELI×32, HELI×26 |
| 🟥 | Savage Rabble | random | Modern 95%, Future 5% | ⬛ 0/48 (0%) | SPECOPS×12, MECH_WARRIOR×5, SOLDIER×4 | THE_GENERAL×18, SPECOPS×30, SPECOPS×20, SPECOPS×27, SIEGE_TANK×30, HELI×22, SIEGE_TANK×24, MECH_WARRIOR×20, SPECOPS×32, SPECOPS×31, HELI×24, SIEGE_TANK×30, SIEGE_TANK×26, HELI×30, SIEGE_TANK×30, SIEGE_TANK×30 |
| 🟩 | Noisy Barbarians | random | Modern 90%, Future 5%, Industrial 4% | 🔴 3/48 (6%) | SPECOPS×12, MECH_WARRIOR×5, SOLDIER×1 | SIEGE_TANK×30, HELI×26, SPECOPS×28, MECH_WARRIOR×24, SPECOPS×25, SPECOPS×31, THE_GENERAL×18, SPECOPS×20, SPECOPS×27, HELI×26, HELI×22, SPECOPS×30, SPECOPS×30, TRANSPORTER×20, SIEGE_TANK×24, HELI×34, HELI×32 |
| 🟩 | Unlucky Raiders | random | Modern 77%, Industrial 18%, Future 5% | 🟠 18/48 (38%) | SPECOPS×9, MECH_WARRIOR×3 | SPECOPS×33, HELI×22, MECH_WARRIOR×24, SOLDIER×32, SPECOPS×31, MOTORBIKE×26, HELI×30, HELI×30, SIEGE_TANK×26, HELI×24, SIEGE_TANK×26, SIEGE_TANK×24, SIEGE_TANK×32, TRANSPORTER×20, SIEGE_TANK×30, SPECOPS×33 |
| 🟩 | Restless Horde | random | Modern 88%, Future 12% | 🟢 39/48 (81%) | SOLDIER×9 | SPECOPS×23, THE_GENERAL×18, SIEGE_TANK×28, DRONE×24, HELI×34, SIEGE_TANK×20, HELI×26, SIEGE_TANK×34, DRONE×28, HELI×34, HELI×34, SPECOPS×31, SPECOPS×27, SIEGE_TANK×20, HELI×34, HELI×22 |
| 🟥 | Blundering Invaders | random | Modern 82%, Future 18% | ⬛ 0/48 (0%) | SPECOPS×7, MECH_WARRIOR×7, SOLDIER×6 | HELI×24, SIEGE_TANK×28, DRONE×33, SIEGE_TANK×30, HELI×22, SPECOPS×27, HELI×28, SIEGE_TANK×32, SIEGE_TANK×24, SPECOPS×24, SIEGE_TANK×22, MECH_WARRIOR×32, THE_GENERAL×18, HELI×24 |
| 🟩 | Relentless Mob | random | Modern 70%, Industrial 23%, Future 7% | 🟠 14/48 (29%) | SPECOPS×7, SIEGE_TANK×1, THE_GENERAL×1 | THE_GENERAL×18, SIEGE_TANK×28, HELI×28, SPECOPS×26, DRONE×27, MOTORBIKE×27, HELI×22, SIEGE_TANK×22, SIEGE_TANK×28, TRANSPORTER×30, SIEGE_TANK×20, SIEGE_TANK×28, SOLDIER×26, SPECOPS×31 |
| 🟩 | Grumpy Marauders | random | Modern 66%, Industrial 27%, Future 7% | 🟢 40/48 (83%) | SPECOPS×3, SOLDIER×2 | SPECOPS×33, HELI×28, SIEGE_TANK×34, DRONE×28, TRANSPORTER×30, SMALL_TANK×24, SIEGE_TANK×32, SIEGE_TANK×28, SOLDIER×32, HELI×30, SPECOPS×25, TRANSPORTER×20, THE_GENERAL×18, SIEGE_TANK×30 |
| 🟩 | Weary Plunderers | random | Modern 64%, Industrial 25%, Future 10% | 🟢 44/48 (92%) | SPECOPS×2 | HELI×22, MOTORBIKE×25, THE_GENERAL×18, DRONE×21, SPECOPS×30, HELI×22, SOLDIER×27, SIEGE_TANK×34, DRONE×22, SIEGE_TANK×32, MOTORBIKE×27, SPECOPS×25, SPECOPS×33, SMALL_TANK×26, SIEGE_TANK×22, SPECOPS×26 |
| 🟩 | Frenzied Pillagers | random | Modern 73%, Industrial 14%, Future 13% | 🔴 2/48 (4%) | MECH_WARRIOR×8, SPECOPS×5, SOLDIER×4 | SPECOPS×22, SPECOPS×27, SIEGE_TANK×24, TRANSPORTER×30, HELI×32, DRONE×21, SPECOPS×29, MOTORBIKE×29, HELI×22, SPECOPS×25, SPECOPS×32, HELI×22, MECH_WARRIOR×32, SPECOPS×28, HELI×28, THE_GENERAL×18 |
| 🟩 | Reckless Looters | random | Modern 88%, Future 12% | 🟠 15/48 (31%) | SPECOPS×6, SOLDIER×3, THE_GENERAL×1 | SPECOPS×31, DRONE×24, SIEGE_TANK×28, SIEGE_TANK×32, DRONE×22, THE_GENERAL×18, SIEGE_TANK×20, SIEGE_TANK×22, SPECOPS×26, HELI×28, SPECOPS×21, HELI×30, SPECOPS×30, HELI×24, SIEGE_TANK×32 |
| 🟩 | Forgotten Warband | random | Modern 85%, Industrial 8%, Future 7% | 🟢 48/48 (100%) |  | SIEGE_TANK×20, SPECOPS×28, SPECOPS×25, SPECOPS×29, SPECOPS×21, SIEGE_TANK×30, SIEGE_TANK×24, DRONE×30, SIEGE_TANK×22, HELI×26, MOTORBIKE×33, SIEGE_TANK×20, SPECOPS×29, SPECOPS×31, SIEGE_TANK×22, THE_GENERAL×18 |
| 🟩 | Blundering Invaders | random | Modern 74%, Industrial 14%, Future 13% | 🟡 26/48 (54%) | SPECOPS×11 | THE_GENERAL×18, DRONE×29, SPECOPS×29, MOTORBIKE×23, SIEGE_TANK×30, DRONE×22, SIEGE_TANK×34, HELI×20, SPECOPS×33, SPECOPS×33, SIEGE_TANK×24, SMALL_TANK×32, SPECOPS×23, SPECOPS×21, SIEGE_TANK×30 |
| 🟩 | Rude Barbarians | random | Modern 80%, Industrial 13%, Future 7% | 🟡 28/48 (58%) | MECH_WARRIOR×5 | SPECOPS×21, SPECOPS×20, SPECOPS×20, SPECOPS×21, SPECOPS×25, HELI×24, MOTORBIKE×22, MECH_WARRIOR×24, HELI×34, SPECOPS×21, TRANSPORTER×20, SPECOPS×23, THE_GENERAL×18, HELI×32 |
| 🟥 | Clumsy Attackers | random | Modern 87%, Future 13% | ⬛ 0/48 (0%) | MECH_WARRIOR×9, SPECOPS×3, SOLDIER×2, SIEGE_TANK×2 | SPECOPS×31, SPECOPS×25, HELI×22, SPECOPS×32, HELI×32, SIEGE_TANK×34, THE_GENERAL×18, SIEGE_TANK×26, SIEGE_TANK×20, MECH_WARRIOR×28, SPECOPS×20, HELI×24, HELI×22, MECH_WARRIOR×24, SPECOPS×26, SPECOPS×27 |
| 🟥 | Hungry Invaders | random | Modern 87%, Future 13% | ⬛ 0/48 (0%) | SPECOPS×14, SOLDIER×10, SIEGE_TANK×3, MECH_WARRIOR×1 | SPECOPS×26, SIEGE_TANK×26, SIEGE_TANK×20, SPECOPS×29, SPECOPS×29, HELI×24, SIEGE_TANK×22, SIEGE_TANK×22, SPECOPS×30, SIEGE_TANK×30, SIEGE_TANK×28, HELI×30, DRONE×31, HELI×24, MECH_WARRIOR×20, THE_GENERAL×18 |
| 🟩 | Clumsy Attackers | random | Modern 67%, Industrial 21%, Future 12% | 🔴 1/48 (2%) | SOLDIER×5, MECH_WARRIOR×5, SPECOPS×2, THE_GENERAL×1 | HELI×22, SPECOPS×29, HELI×30, HELI×32, SIEGE_TANK×22, SIEGE_TANK×32, THE_GENERAL×18, SOLDIER×28, MECH_WARRIOR×24, SPECOPS×22, SIEGE_TANK×34, SOLDIER×23, SOLDIER×32, HELI×26, DRONE×26 |
| 🟩 | Clumsy Attackers | random | Modern 82%, Future 9%, Industrial 9% | 🔴 7/48 (15%) | SPECOPS×8, SOLDIER×7, THE_GENERAL×1 | SOLDIER×32, HELI×32, SPECOPS×32, SPECOPS×24, SIEGE_TANK×26, SPECOPS×26, SIEGE_TANK×22, THE_GENERAL×18, SIEGE_TANK×28, SPECOPS×23, SPECOPS×27, HELI×24, SPECOPS×21, DRONE×34 |

#### S2 Wicked$Kingdom

| Tower Era Distribution (62 towers) | Towers |
|---|---|
| Industrial 48% (30), Modern 34% (21), Iron Age 16% (10), Renaissance 2% (1) | RADAR_TOWER×21, GATLING_TOWER×19, FLAME_THROWER×11, COLD_TOWER×10, ICE_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Modern Warfare | hardcoded | Modern 82%, Industrial 14%, Future 4% | 🔴 1/38 (3%) | SPECOPS×14, SOLDIER×9 | SPECOPS×18, SIEGE_TANK×18, SIEGE_TANK×19, HELI×20, HELI×20, SIEGE_TANK×20, SPECOPS×21, SIEGE_TANK×22, SPECOPS×22, SPECOPS×22, SPECOPS×23, SIEGE_TANK×24, HELI×24, SIEGE_TANK×24, DRONE×25, SIEGE_TANK×26, SPECOPS×26, TRANSPORTER×26, HELI×27, SIEGE_TANK×28, TRANSPORTER×28, SPECOPS×28, HELI×29, SMALL_TANK×30, THE_GENERAL×40 |
| 🟥 | Special Ops | hardcoded | Modern 91%, Industrial 5%, Future 4% | ⬛ 0/38 (0%) | SPECOPS×8, MECH_WARRIOR×5, SOLDIER×2 | HELI×18, HELI×18, SPECOPS×19, SIEGE_TANK×20, SIEGE_TANK×20, SIEGE_TANK×20, SPECOPS×21, SPECOPS×22, SPECOPS×22, HELI×22, SIEGE_TANK×23, SPECOPS×24, SIEGE_TANK×24, HELI×24, HELI×25, MECH_WARRIOR×26, SPECOPS×26, SIEGE_TANK×26, SPECOPS×27, HELI×28, SPECOPS×28, TRANSPORTER×28, HELI×29, SIEGE_TANK×30, THE_GENERAL×36 |
| 🟥 | Heli Strike | hardcoded | Modern 84%, Industrial 16% | ⬛ 0/38 (0%) | SPECOPS×17, SOLDIER×4 | HELI×18, SPECOPS×18, HELI×19, SPECOPS×20, HELI×20, SPECOPS×20, SPECOPS×21, SPECOPS×22, TRANSPORTER×22, SPECOPS×22, SPECOPS×23, SIEGE_TANK×24, HELI×24, TRANSPORTER×24, SIEGE_TANK×25, HELI×26, SPECOPS×26, MOTORBIKE×26, SPECOPS×27, HELI×28, TRANSPORTER×28, HELI×28, HELI×29, SIEGE_TANK×30, SPECOPS×30, THE_GENERAL×35 |
| 🟥 | Siege Assault | hardcoded | Modern 84%, Industrial 13%, Renaissance 4% | ⬛ 0/38 (0%) | SPECOPS×15, SOLDIER×8 | SIEGE_TANK×18, SIEGE_TANK×18, SIEGE_TANK×19, SPECOPS×20, HELI×20, SPECOPS×20, TRANSPORTER×21, SIEGE_TANK×22, NINJA×22, HELI×22, SIEGE_TANK×23, SIEGE_TANK×24, SOLDIER×24, SPECOPS×24, SIEGE_TANK×25, SPECOPS×26, SPECOPS×26, HELI×26, SIEGE_TANK×27, TRANSPORTER×28, HELI×28, SIEGE_TANK×29, SPECOPS×30, THE_GENERAL×40 |
| 🟥 | Urban Combat | hardcoded | Modern 91%, Industrial 9% | ⬛ 0/38 (0%) | SPECOPS×17, SOLDIER×4 | SPECOPS×18, SIEGE_TANK×18, SPECOPS×19, THE_GENERAL×20, SPECOPS×20, SPECOPS×20, HELI×21, SPECOPS×22, SPECOPS×22, SIEGE_TANK×22, SIEGE_TANK×23, SIEGE_TANK×24, SPECOPS×24, SOLDIER×24, SPECOPS×25, SPECOPS×26, SIEGE_TANK×26, HELI×26, SPECOPS×27, HELI×28, SPECOPS×28, HELI×28, TRANSPORTER×29, HELI×30 |
| 🟥 | Cyber Strike | hardcoded | Modern 100% | ⬛ 0/38 (0%) | SPECOPS×14, SOLDIER×10 | SIEGE_TANK×18, HELI×18, HELI×19, SPECOPS×19, SPECOPS×20, SPECOPS×20, SIEGE_TANK×21, SPECOPS×21, SPECOPS×21, SIEGE_TANK×22, SPECOPS×22, SPECOPS×23, SPECOPS×23, SIEGE_TANK×24, SIEGE_TANK×24, SIEGE_TANK×24, HELI×25, SPECOPS×25, HELI×26, SIEGE_TANK×26, SPECOPS×27, SPECOPS×27, HELI×27, SIEGE_TANK×28, THE_GENERAL×35 |
| 🟥 | Rampaging Rabble | random | Modern 87%, Future 13% | ⬛ 0/38 (0%) | SPECOPS×7, MECH_WARRIOR×6 | SPECOPS×31, SIEGE_TANK×22, MECH_WARRIOR×28, SPECOPS×21, THE_GENERAL×18, SIEGE_TANK×26, SIEGE_TANK×26, SPECOPS×31, SPECOPS×30, SPECOPS×27, SPECOPS×28, HELI×24, SIEGE_TANK×22, SPECOPS×34, MECH_WARRIOR×24, SIEGE_TANK×22 |
| 🟥 | Rampaging Rabble | random | Modern 87%, Future 13% | ⬛ 0/38 (0%) | SPECOPS×7, MECH_WARRIOR×6 | SPECOPS×31, SIEGE_TANK×22, MECH_WARRIOR×28, SPECOPS×21, THE_GENERAL×18, SIEGE_TANK×26, SIEGE_TANK×26, SPECOPS×31, SPECOPS×30, SPECOPS×27, SPECOPS×28, HELI×24, SIEGE_TANK×22, SPECOPS×34, MECH_WARRIOR×24, SIEGE_TANK×22 |
| 🟥 | Petty Bandits | random | Modern 87%, Future 7%, Industrial 6% | ⬛ 0/38 (0%) | DRONE×9, SOLDIER×7, SPECOPS×2, THE_GENERAL×1 | THE_GENERAL×18, SPECOPS×22, SPECOPS×31, SIEGE_TANK×32, HELI×20, HELI×26, DRONE×27, SIEGE_TANK×26, HELI×20, SIEGE_TANK×34, SPECOPS×29, MOTORBIKE×25, SIEGE_TANK×22, HELI×24, HELI×32, HELI×26 |
| 🟥 | Savage Rabble | random | Modern 95%, Future 5% | ⬛ 0/38 (0%) | SPECOPS×7, SOLDIER×7, THE_GENERAL×1 | THE_GENERAL×18, SPECOPS×30, SPECOPS×20, SPECOPS×27, SIEGE_TANK×30, HELI×22, SIEGE_TANK×24, MECH_WARRIOR×20, SPECOPS×32, SPECOPS×31, HELI×24, SIEGE_TANK×30, SIEGE_TANK×26, HELI×30, SIEGE_TANK×30, SIEGE_TANK×30 |
| 🟥 | Noisy Barbarians | random | Modern 90%, Future 5%, Industrial 4% | ⬛ 0/38 (0%) | SPECOPS×11, MECH_WARRIOR×4 | SIEGE_TANK×30, HELI×26, SPECOPS×28, MECH_WARRIOR×24, SPECOPS×25, SPECOPS×31, THE_GENERAL×18, SPECOPS×20, SPECOPS×27, HELI×26, HELI×22, SPECOPS×30, SPECOPS×30, TRANSPORTER×20, SIEGE_TANK×24, HELI×34, HELI×32 |
| 🟥 | Unlucky Raiders | random | Modern 77%, Industrial 18%, Future 5% | ⬛ 0/38 (0%) | SPECOPS×13, MECH_WARRIOR×3 | SPECOPS×33, HELI×22, MECH_WARRIOR×24, SOLDIER×32, SPECOPS×31, MOTORBIKE×26, HELI×30, HELI×30, SIEGE_TANK×26, HELI×24, SIEGE_TANK×26, SIEGE_TANK×24, SIEGE_TANK×32, TRANSPORTER×20, SIEGE_TANK×30, SPECOPS×33 |
| 🟥 | Restless Horde | random | Modern 88%, Future 12% | ⬛ 0/38 (0%) | SOLDIER×9, SPECOPS×6, THE_GENERAL×1 | SPECOPS×23, THE_GENERAL×18, SIEGE_TANK×28, DRONE×24, HELI×34, SIEGE_TANK×20, HELI×26, SIEGE_TANK×34, DRONE×28, HELI×34, HELI×34, SPECOPS×31, SPECOPS×27, SIEGE_TANK×20, HELI×34, HELI×22 |
| 🟥 | Blundering Invaders | random | Modern 82%, Future 18% | ⬛ 0/38 (0%) | SPECOPS×15, SOLDIER×7, MECH_WARRIOR×1 | HELI×24, SIEGE_TANK×28, DRONE×33, SIEGE_TANK×30, HELI×22, SPECOPS×27, HELI×28, SIEGE_TANK×32, SIEGE_TANK×24, SPECOPS×24, SIEGE_TANK×22, MECH_WARRIOR×32, THE_GENERAL×18, HELI×24 |
| 🟩 | Relentless Mob | random | Modern 70%, Industrial 23%, Future 7% | 🟠 11/38 (29%) | SPECOPS×13, SOLDIER×1 | THE_GENERAL×18, SIEGE_TANK×28, HELI×28, SPECOPS×26, DRONE×27, MOTORBIKE×27, HELI×22, SIEGE_TANK×22, SIEGE_TANK×28, TRANSPORTER×30, SIEGE_TANK×20, SIEGE_TANK×28, SOLDIER×26, SPECOPS×31 |
| 🟩 | Grumpy Marauders | random | Modern 66%, Industrial 27%, Future 7% | 🟠 14/38 (37%) | SPECOPS×11, SOLDIER×2 | SPECOPS×33, HELI×28, SIEGE_TANK×34, DRONE×28, TRANSPORTER×30, SMALL_TANK×24, SIEGE_TANK×32, SIEGE_TANK×28, SOLDIER×32, HELI×30, SPECOPS×25, TRANSPORTER×20, THE_GENERAL×18, SIEGE_TANK×30 |
| 🟩 | Weary Plunderers | random | Modern 64%, Industrial 25%, Future 10% | 🟡 19/38 (50%) | SPECOPS×9, SOLDIER×1 | HELI×22, MOTORBIKE×25, THE_GENERAL×18, DRONE×21, SPECOPS×30, HELI×22, SOLDIER×27, SIEGE_TANK×34, DRONE×22, SIEGE_TANK×32, MOTORBIKE×27, SPECOPS×25, SPECOPS×33, SMALL_TANK×26, SIEGE_TANK×22, SPECOPS×26 |
| 🟥 | Frenzied Pillagers | random | Modern 73%, Industrial 14%, Future 13% | ⬛ 0/38 (0%) | SOLDIER×12, SPECOPS×11, DRONE×4 | SPECOPS×22, SPECOPS×27, SIEGE_TANK×24, TRANSPORTER×30, HELI×32, DRONE×21, SPECOPS×29, MOTORBIKE×29, HELI×22, SPECOPS×25, SPECOPS×32, HELI×22, MECH_WARRIOR×32, SPECOPS×28, HELI×28, THE_GENERAL×18 |
| 🟥 | Reckless Looters | random | Modern 88%, Future 12% | ⬛ 0/38 (0%) | SPECOPS×14, SOLDIER×10 | SPECOPS×31, DRONE×24, SIEGE_TANK×28, SIEGE_TANK×32, DRONE×22, THE_GENERAL×18, SIEGE_TANK×20, SIEGE_TANK×22, SPECOPS×26, HELI×28, SPECOPS×21, HELI×30, SPECOPS×30, HELI×24, SIEGE_TANK×32 |
| 🟩 | Forgotten Warband | random | Modern 85%, Industrial 8%, Future 7% | 🟠 10/38 (26%) | SPECOPS×14 | SIEGE_TANK×20, SPECOPS×28, SPECOPS×25, SPECOPS×29, SPECOPS×21, SIEGE_TANK×30, SIEGE_TANK×24, DRONE×30, SIEGE_TANK×22, HELI×26, MOTORBIKE×33, SIEGE_TANK×20, SPECOPS×29, SPECOPS×31, SIEGE_TANK×22, THE_GENERAL×18 |
| 🟩 | Blundering Invaders | random | Modern 74%, Industrial 14%, Future 13% | 🟠 10/38 (26%) | SPECOPS×14 | THE_GENERAL×18, DRONE×29, SPECOPS×29, MOTORBIKE×23, SIEGE_TANK×30, DRONE×22, SIEGE_TANK×34, HELI×20, SPECOPS×33, SPECOPS×33, SIEGE_TANK×24, SMALL_TANK×32, SPECOPS×23, SPECOPS×21, SIEGE_TANK×30 |
| 🟥 | Rude Barbarians | random | Modern 80%, Industrial 13%, Future 7% | ⬛ 0/38 (0%) | SPECOPS×13, MECH_WARRIOR×3, SOLDIER×1 | SPECOPS×21, SPECOPS×20, SPECOPS×20, SPECOPS×21, SPECOPS×25, HELI×24, MOTORBIKE×22, MECH_WARRIOR×24, HELI×34, SPECOPS×21, TRANSPORTER×20, SPECOPS×23, THE_GENERAL×18, HELI×32 |
| 🟥 | Clumsy Attackers | random | Modern 87%, Future 13% | ⬛ 0/38 (0%) | SPECOPS×14, SOLDIER×10 | SPECOPS×31, SPECOPS×25, HELI×22, SPECOPS×32, HELI×32, SIEGE_TANK×34, THE_GENERAL×18, SIEGE_TANK×26, SIEGE_TANK×20, MECH_WARRIOR×28, SPECOPS×20, HELI×24, HELI×22, MECH_WARRIOR×24, SPECOPS×26, SPECOPS×27 |
| 🟥 | Hungry Invaders | random | Modern 87%, Future 13% | ⬛ 0/38 (0%) | SPECOPS×14, SOLDIER×7, HELI×1 | SPECOPS×26, SIEGE_TANK×26, SIEGE_TANK×20, SPECOPS×29, SPECOPS×29, HELI×24, SIEGE_TANK×22, SIEGE_TANK×22, SPECOPS×30, SIEGE_TANK×30, SIEGE_TANK×28, HELI×30, DRONE×31, HELI×24, MECH_WARRIOR×20, THE_GENERAL×18 |
| 🟥 | Clumsy Attackers | random | Modern 67%, Industrial 21%, Future 12% | ⬛ 0/38 (0%) | SPECOPS×17, SOLDIER×4 | HELI×22, SPECOPS×29, HELI×30, HELI×32, SIEGE_TANK×22, SIEGE_TANK×32, THE_GENERAL×18, SOLDIER×28, MECH_WARRIOR×24, SPECOPS×22, SIEGE_TANK×34, SOLDIER×23, SOLDIER×32, HELI×26, DRONE×26 |
| 🟥 | Clumsy Attackers | random | Modern 82%, Future 9%, Industrial 9% | ⬛ 0/38 (0%) | SPECOPS×16, SOLDIER×6 | SOLDIER×32, HELI×32, SPECOPS×32, SPECOPS×24, SIEGE_TANK×26, SPECOPS×26, SIEGE_TANK×22, THE_GENERAL×18, SIEGE_TANK×28, SPECOPS×23, SPECOPS×27, HELI×24, SPECOPS×21, DRONE×34 |

### Future

#### Weak Modern

| Tower Era Distribution (33 towers) | Towers |
|---|---|
| Modern 48% (16), Industrial 30% (10), Future 12% (4), Iron Age 6% (2), Renaissance 3% (1) | FLAME_THROWER×10, MG_TOWER×7, RADAR_TOWER×5, ANTI_AIR_TOWER×4, LASER_TOWER×4, COLD_TOWER×2, ICE_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟥 | Mech Uprising | hardcoded | Future 100% | ⬛ 0/28 (0%) | SPECOPS×9, DRONE×7, MECH_WARRIOR×1 | MECH_WARRIOR×18, DRONE×18, MECH_WARRIOR×19, MECH_WARRIOR×19, MECH_WARRIOR×20, DRONE×20, MECH_WARRIOR×21, DRONE×21, MECH_WARRIOR×21, DRONE×22, MECH_WARRIOR×22, DRONE×23, MECH_WARRIOR×23, MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×24, DRONE×25, MECH_WARRIOR×25, DRONE×26, DRONE×26, MECH_WARRIOR×27, DRONE×27, DRONE×27, MECH_WARRIOR×28, DRONE×28, MECH_WARRIOR×29, DRONE×29, MECH_WARRIOR×30, DRONE×30 |
| 🟥 | Drone Swarm | hardcoded | Future 100% | ⬛ 0/28 (0%) | DRONE×13, SPECOPS×8 | DRONE×18, MECH_WARRIOR×18, MECH_WARRIOR×19, DRONE×19, DRONE×20, DRONE×20, MECH_WARRIOR×21, MECH_WARRIOR×21, MECH_WARRIOR×22, MECH_WARRIOR×22, DRONE×22, MECH_WARRIOR×23, MECH_WARRIOR×23, DRONE×24, MECH_WARRIOR×24, DRONE×25, MECH_WARRIOR×25, MECH_WARRIOR×26, MECH_WARRIOR×26, DRONE×26, MECH_WARRIOR×27, MECH_WARRIOR×27, MECH_WARRIOR×28, DRONE×28, DRONE×29, DRONE×29, DRONE×30, DRONE×30 |
| 🟥 | Future Shock | hardcoded | Future 100% | ⬛ 0/28 (0%) | DRONE×15, SPECOPS×5, MECH_WARRIOR×1 | MECH_WARRIOR×18, MECH_WARRIOR×18, DRONE×19, DRONE×19, MECH_WARRIOR×20, DRONE×20, MECH_WARRIOR×21, MECH_WARRIOR×21, MECH_WARRIOR×21, DRONE×22, MECH_WARRIOR×22, MECH_WARRIOR×23, DRONE×23, MECH_WARRIOR×24, DRONE×24, DRONE×24, MECH_WARRIOR×25, DRONE×25, MECH_WARRIOR×26, DRONE×26, DRONE×27, MECH_WARRIOR×27, DRONE×27, DRONE×28, DRONE×28, MECH_WARRIOR×29, DRONE×29, MECH_WARRIOR×30 |
| 🟥 | Rowdy Plunderers | random | Future 93%, Modern 7% | ⬛ 0/28 (0%) | DRONE×16, SPECOPS×4, MECH_WARRIOR×1 | MECH_WARRIOR×24, DRONE×20, DRONE×27, DRONE×26, MECH_WARRIOR×24, MECH_WARRIOR×32, MECH_WARRIOR×32, DRONE×23, DRONE×29, MECH_WARRIOR×24, DRONE×22, DRONE×30, DRONE×29, DRONE×28, MECH_WARRIOR×28, SPECOPS×31 |
| 🟥 | Rowdy Plunderers | random | Future 93%, Modern 7% | ⬛ 0/28 (0%) | DRONE×16, SPECOPS×4, MECH_WARRIOR×1 | MECH_WARRIOR×24, DRONE×20, DRONE×27, DRONE×26, MECH_WARRIOR×24, MECH_WARRIOR×32, MECH_WARRIOR×32, DRONE×23, DRONE×29, MECH_WARRIOR×24, DRONE×22, DRONE×30, DRONE×29, DRONE×28, MECH_WARRIOR×28, SPECOPS×31 |
| 🟥 | Relentless Mob | random | Future 93%, Modern 7% | ⬛ 0/28 (0%) | DRONE×23, SPECOPS×3 | MECH_WARRIOR×28, SIEGE_TANK×34, DRONE×33, DRONE×31, DRONE×20, DRONE×26, DRONE×34, DRONE×22, MECH_WARRIOR×20, MECH_WARRIOR×28, DRONE×31, DRONE×29, MECH_WARRIOR×32, MECH_WARRIOR×28, DRONE×21, MECH_WARRIOR×32, DRONE×26 |
| 🟥 | Drunken Raiders | random | Future 93%, Modern 7% | ⬛ 0/28 (0%) | DRONE×18, MECH_WARRIOR×2, SPECOPS×1 | DRONE×30, DRONE×27, DRONE×20, MECH_WARRIOR×24, MECH_WARRIOR×28, DRONE×23, MECH_WARRIOR×24, MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×31, DRONE×30, DRONE×31, MECH_WARRIOR×24, MECH_WARRIOR×28, DRONE×33, SPECOPS×32, DRONE×32 |
| 🟥 | Shrieking Horde | random | Future 96%, Modern 4% | ⬛ 0/28 (0%) | DRONE×24, MECH_WARRIOR×1 | DRONE×31, MECH_WARRIOR×32, DRONE×25, MECH_WARRIOR×24, DRONE×31, DRONE×25, DRONE×23, MECH_WARRIOR×24, MECH_WARRIOR×28, MECH_WARRIOR×20, MECH_WARRIOR×32, DRONE×26, HELI×20, DRONE×27, MECH_WARRIOR×28, MECH_WARRIOR×32, DRONE×30, MECH_WARRIOR×28 |
| 🟥 | Restless Horde | random | Future 85%, Modern 15% | ⬛ 0/28 (0%) | DRONE×24, SPECOPS×2 | DRONE×26, MECH_WARRIOR×24, THE_GENERAL×18, MECH_WARRIOR×20, SIEGE_TANK×26, SPECOPS×26, DRONE×32, MECH_WARRIOR×28, DRONE×26, MECH_WARRIOR×32, DRONE×31, DRONE×31, DRONE×32, MECH_WARRIOR×24, DRONE×24, DRONE×32, DRONE×31 |
| 🟥 | Stubborn Raiders | random | Future 95%, Modern 5% | ⬛ 0/28 (0%) | DRONE×13, MECH_WARRIOR×3, SPECOPS×2 | MECH_WARRIOR×32, DRONE×33, MECH_WARRIOR×24, DRONE×28, MECH_WARRIOR×32, DRONE×26, DRONE×20, DRONE×20, MECH_WARRIOR×28, SPECOPS×23, MECH_WARRIOR×24, MECH_WARRIOR×32, DRONE×26, DRONE×34, MECH_WARRIOR×28, MECH_WARRIOR×24 |
| 🟥 | Bored Mercenaries | random | Future 94%, Modern 6% | ⬛ 0/28 (0%) | DRONE×12, MECH_WARRIOR×3, SPECOPS×2 | DRONE×26, DRONE×28, MECH_WARRIOR×24, THE_GENERAL×18, MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×31, MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×28, DRONE×24, DRONE×22, MECH_WARRIOR×28 |
| 🟥 | Wandering Pillagers | random | Future 86%, Modern 14% | ⬛ 0/28 (0%) | DRONE×16, SPECOPS×6 | SPECOPS×25, DRONE×22, MECH_WARRIOR×28, DRONE×27, DRONE×28, DRONE×28, MECH_WARRIOR×20, DRONE×22, HELI×24, DRONE×27, DRONE×31, DRONE×31, MECH_WARRIOR×28 |
| 🟥 | Grumpy Marauders | random | Future 82%, Modern 18% | ⬛ 0/28 (0%) | DRONE×19, SPECOPS×3, MECH_WARRIOR×1 | MECH_WARRIOR×32, MECH_WARRIOR×24, MECH_WARRIOR×24, SIEGE_TANK×28, DRONE×32, SPECOPS×21, MECH_WARRIOR×20, MECH_WARRIOR×28, THE_GENERAL×18, MECH_WARRIOR×24, DRONE×28, DRONE×29, MECH_WARRIOR×32, MECH_WARRIOR×28 |
| 🟥 | Savage Rabble | random | Future 84%, Modern 16% | ⬛ 0/28 (0%) | SPECOPS×9, DRONE×6, MECH_WARRIOR×1 | MECH_WARRIOR×20, SIEGE_TANK×22, HELI×20, MECH_WARRIOR×28, MECH_WARRIOR×32, DRONE×24, MECH_WARRIOR×28, SIEGE_TANK×22, DRONE×25, DRONE×23, DRONE×25, MECH_WARRIOR×32, DRONE×26, MECH_WARRIOR×24, DRONE×25, DRONE×20 |
| 🟥 | Frenzied Pillagers | random | Future 88%, Modern 12% | ⬛ 0/28 (0%) | DRONE×18, SPECOPS×5 | DRONE×28, DRONE×27, DRONE×26, MECH_WARRIOR×24, MECH_WARRIOR×32, SIEGE_TANK×30, MECH_WARRIOR×28, MECH_WARRIOR×24, MECH_WARRIOR×20, DRONE×28, MECH_WARRIOR×32, DRONE×22, THE_GENERAL×18, MECH_WARRIOR×24, MECH_WARRIOR×28, MECH_WARRIOR×24 |
| 🟥 | Grumpy Marauders | random | Future 93%, Modern 7% | ⬛ 0/28 (0%) | DRONE×16, SPECOPS×4, MECH_WARRIOR×1 | DRONE×24, MECH_WARRIOR×28, DRONE×26, MECH_WARRIOR×24, MECH_WARRIOR×24, MECH_WARRIOR×24, SPECOPS×25, DRONE×30, DRONE×23, MECH_WARRIOR×32, MECH_WARRIOR×20, DRONE×24, MECH_WARRIOR×32, MECH_WARRIOR×28 |
| 🟥 | Forgotten Warband | random | Future 88%, Modern 12% | ⬛ 0/28 (0%) | DRONE×19, SPECOPS×5 | DRONE×24, DRONE×28, DRONE×28, MECH_WARRIOR×20, DRONE×31, MECH_WARRIOR×28, DRONE×20, SPECOPS×30, DRONE×21, DRONE×21, THE_GENERAL×18, DRONE×20, MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×28, MECH_WARRIOR×28 |
| 🟥 | Hungry Invaders | random | Future 86%, Modern 14% | ⬛ 0/28 (0%) | DRONE×10, SOLDIER×3, MECH_WARRIOR×2, SPECOPS×2, HELI×2 | SIEGE_TANK×28, MECH_WARRIOR×28, MECH_WARRIOR×24, DRONE×29, HELI×24, MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×33, DRONE×22, MECH_WARRIOR×20, MECH_WARRIOR×24, DRONE×26, DRONE×21, DRONE×23, DRONE×31 |
| 🟥 | Howling Savages | random | Future 84%, Modern 16% | ⬛ 0/28 (0%) | DRONE×16, SPECOPS×4, MECH_WARRIOR×1 | DRONE×31, DRONE×26, MECH_WARRIOR×24, DRONE×21, DRONE×25, DRONE×20, DRONE×22, SIEGE_TANK×28, DRONE×27, MECH_WARRIOR×32, MECH_WARRIOR×32, SPECOPS×29, DRONE×23, MECH_WARRIOR×24 |
| 🟥 | Rowdy Plunderers | random | Future 93%, Modern 7% | ⬛ 0/28 (0%) | DRONE×17, SOLDIER×7, SPECOPS×2 | DRONE×28, MECH_WARRIOR×24, DRONE×25, MECH_WARRIOR×28, HELI×30, DRONE×32, DRONE×33, MECH_WARRIOR×32, MECH_WARRIOR×24, DRONE×33, MECH_WARRIOR×24, DRONE×24, MECH_WARRIOR×28, DRONE×29, DRONE×30, DRONE×32 |
| 🟥 | Reckless Looters | random | Future 96%, Modern 4% | ⬛ 0/28 (0%) | DRONE×14, SPECOPS×5, MECH_WARRIOR×1 | MECH_WARRIOR×32, MECH_WARRIOR×20, DRONE×26, DRONE×23, DRONE×23, DRONE×32, MECH_WARRIOR×28, MECH_WARRIOR×24, MECH_WARRIOR×28, DRONE×29, DRONE×21, MECH_WARRIOR×28, THE_GENERAL×18, MECH_WARRIOR×24, DRONE×21, MECH_WARRIOR×24, DRONE×29 |
| 🟥 | Rampaging Rabble | random | Future 86%, Modern 14% | ⬛ 0/28 (0%) | DRONE×20, SPECOPS×2, MECH_WARRIOR×1 | DRONE×22, DRONE×33, MECH_WARRIOR×32, DRONE×29, DRONE×31, DRONE×22, DRONE×31, MECH_WARRIOR×24, SPECOPS×24, SPECOPS×33, MECH_WARRIOR×24, MECH_WARRIOR×32, MECH_WARRIOR×24, MECH_WARRIOR×24, MECH_WARRIOR×24 |
| 🟥 | Disorganized Mob | random | Future 95%, Modern 5% | ⬛ 0/28 (0%) | DRONE×22, SPECOPS×3 | DRONE×21, THE_GENERAL×18, MECH_WARRIOR×28, MECH_WARRIOR×28, MECH_WARRIOR×32, DRONE×28, DRONE×22, MECH_WARRIOR×28, DRONE×29, DRONE×28, DRONE×29, DRONE×22, MECH_WARRIOR×20 |

#### S1 Limperium

| Tower Era Distribution (58 towers) | Towers |
|---|---|
| Modern 69% (40), Future 17% (10), Iron Age 14% (8) | MG_TOWER×35, ROCKET_TOWER×10, COLD_TOWER×8, NAPALM_THROWER×5 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟥 | Mech Uprising | hardcoded | Future 100% | ⬛ 0/48 (0%) | MECH_WARRIOR×12 | MECH_WARRIOR×18, DRONE×18, MECH_WARRIOR×19, MECH_WARRIOR×19, MECH_WARRIOR×20, DRONE×20, MECH_WARRIOR×21, DRONE×21, MECH_WARRIOR×21, DRONE×22, MECH_WARRIOR×22, DRONE×23, MECH_WARRIOR×23, MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×24, DRONE×25, MECH_WARRIOR×25, DRONE×26, DRONE×26, MECH_WARRIOR×27, DRONE×27, DRONE×27, MECH_WARRIOR×28, DRONE×28, MECH_WARRIOR×29, DRONE×29, MECH_WARRIOR×30, DRONE×30 |
| 🟥 | Drone Swarm | hardcoded | Future 100% | ⬛ 0/48 (0%) | MECH_WARRIOR×10, SPECOPS×4 | DRONE×18, MECH_WARRIOR×18, MECH_WARRIOR×19, DRONE×19, DRONE×20, DRONE×20, MECH_WARRIOR×21, MECH_WARRIOR×21, MECH_WARRIOR×22, MECH_WARRIOR×22, DRONE×22, MECH_WARRIOR×23, MECH_WARRIOR×23, DRONE×24, MECH_WARRIOR×24, DRONE×25, MECH_WARRIOR×25, MECH_WARRIOR×26, MECH_WARRIOR×26, DRONE×26, MECH_WARRIOR×27, MECH_WARRIOR×27, MECH_WARRIOR×28, DRONE×28, DRONE×29, DRONE×29, DRONE×30, DRONE×30 |
| 🟩 | Future Shock | hardcoded | Future 100% | 🟠 22/48 (46%) | MECH_WARRIOR×6, SPECOPS×1 | MECH_WARRIOR×18, MECH_WARRIOR×18, DRONE×19, DRONE×19, MECH_WARRIOR×20, DRONE×20, MECH_WARRIOR×21, MECH_WARRIOR×21, MECH_WARRIOR×21, DRONE×22, MECH_WARRIOR×22, MECH_WARRIOR×23, DRONE×23, MECH_WARRIOR×24, DRONE×24, DRONE×24, MECH_WARRIOR×25, DRONE×25, MECH_WARRIOR×26, DRONE×26, DRONE×27, MECH_WARRIOR×27, DRONE×27, DRONE×28, DRONE×28, MECH_WARRIOR×29, DRONE×29, MECH_WARRIOR×30 |
| 🟥 | Rowdy Plunderers | random | Future 93%, Modern 7% | ⬛ 0/48 (0%) | MECH_WARRIOR×10, SPECOPS×5 | MECH_WARRIOR×24, DRONE×20, DRONE×27, DRONE×26, MECH_WARRIOR×24, MECH_WARRIOR×32, MECH_WARRIOR×32, DRONE×23, DRONE×29, MECH_WARRIOR×24, DRONE×22, DRONE×30, DRONE×29, DRONE×28, MECH_WARRIOR×28, SPECOPS×31 |
| 🟥 | Rowdy Plunderers | random | Future 93%, Modern 7% | ⬛ 0/48 (0%) | MECH_WARRIOR×10, SPECOPS×5 | MECH_WARRIOR×24, DRONE×20, DRONE×27, DRONE×26, MECH_WARRIOR×24, MECH_WARRIOR×32, MECH_WARRIOR×32, DRONE×23, DRONE×29, MECH_WARRIOR×24, DRONE×22, DRONE×30, DRONE×29, DRONE×28, MECH_WARRIOR×28, SPECOPS×31 |
| 🟩 | Relentless Mob | random | Future 93%, Modern 7% | 🔴 6/48 (12%) | MECH_WARRIOR×9, SPECOPS×3 | MECH_WARRIOR×28, SIEGE_TANK×34, DRONE×33, DRONE×31, DRONE×20, DRONE×26, DRONE×34, DRONE×22, MECH_WARRIOR×20, MECH_WARRIOR×28, DRONE×31, DRONE×29, MECH_WARRIOR×32, MECH_WARRIOR×28, DRONE×21, MECH_WARRIOR×32, DRONE×26 |
| 🟥 | Drunken Raiders | random | Future 93%, Modern 7% | ⬛ 0/48 (0%) | MECH_WARRIOR×11, SPECOPS×2 | DRONE×30, DRONE×27, DRONE×20, MECH_WARRIOR×24, MECH_WARRIOR×28, DRONE×23, MECH_WARRIOR×24, MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×31, DRONE×30, DRONE×31, MECH_WARRIOR×24, MECH_WARRIOR×28, DRONE×33, SPECOPS×32, DRONE×32 |
| 🟥 | Shrieking Horde | random | Future 96%, Modern 4% | ⬛ 0/48 (0%) | MECH_WARRIOR×9, SPECOPS×6 | DRONE×31, MECH_WARRIOR×32, DRONE×25, MECH_WARRIOR×24, DRONE×31, DRONE×25, DRONE×23, MECH_WARRIOR×24, MECH_WARRIOR×28, MECH_WARRIOR×20, MECH_WARRIOR×32, DRONE×26, HELI×20, DRONE×27, MECH_WARRIOR×28, MECH_WARRIOR×32, DRONE×30, MECH_WARRIOR×28 |
| 🟩 | Restless Horde | random | Future 85%, Modern 15% | 🟡 30/48 (62%) | MECH_WARRIOR×4, SPECOPS×1 | DRONE×26, MECH_WARRIOR×24, THE_GENERAL×18, MECH_WARRIOR×20, SIEGE_TANK×26, SPECOPS×26, DRONE×32, MECH_WARRIOR×28, DRONE×26, MECH_WARRIOR×32, DRONE×31, DRONE×31, DRONE×32, MECH_WARRIOR×24, DRONE×24, DRONE×32, DRONE×31 |
| 🟥 | Stubborn Raiders | random | Future 95%, Modern 5% | ⬛ 0/48 (0%) | MECH_WARRIOR×10, SPECOPS×4 | MECH_WARRIOR×32, DRONE×33, MECH_WARRIOR×24, DRONE×28, MECH_WARRIOR×32, DRONE×26, DRONE×20, DRONE×20, MECH_WARRIOR×28, SPECOPS×23, MECH_WARRIOR×24, MECH_WARRIOR×32, DRONE×26, DRONE×34, MECH_WARRIOR×28, MECH_WARRIOR×24 |
| 🟩 | Bored Mercenaries | random | Future 94%, Modern 6% | 🟡 24/48 (50%) | MECH_WARRIOR×5, SPECOPS×2 | DRONE×26, DRONE×28, MECH_WARRIOR×24, THE_GENERAL×18, MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×31, MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×28, DRONE×24, DRONE×22, MECH_WARRIOR×28 |
| 🟩 | Wandering Pillagers | random | Future 86%, Modern 14% | 🟢 40/48 (83%) | MECH_WARRIOR×2 | SPECOPS×25, DRONE×22, MECH_WARRIOR×28, DRONE×27, DRONE×28, DRONE×28, MECH_WARRIOR×20, DRONE×22, HELI×24, DRONE×27, DRONE×31, DRONE×31, MECH_WARRIOR×28 |
| 🟥 | Grumpy Marauders | random | Future 82%, Modern 18% | ⬛ 0/48 (0%) | MECH_WARRIOR×10, THE_GENERAL×1 | MECH_WARRIOR×32, MECH_WARRIOR×24, MECH_WARRIOR×24, SIEGE_TANK×28, DRONE×32, SPECOPS×21, MECH_WARRIOR×20, MECH_WARRIOR×28, THE_GENERAL×18, MECH_WARRIOR×24, DRONE×28, DRONE×29, MECH_WARRIOR×32, MECH_WARRIOR×28 |
| 🟩 | Savage Rabble | random | Future 84%, Modern 16% | 🟠 10/48 (21%) | MECH_WARRIOR×7, SPECOPS×5 | MECH_WARRIOR×20, SIEGE_TANK×22, HELI×20, MECH_WARRIOR×28, MECH_WARRIOR×32, DRONE×24, MECH_WARRIOR×28, SIEGE_TANK×22, DRONE×25, DRONE×23, DRONE×25, MECH_WARRIOR×32, DRONE×26, MECH_WARRIOR×24, DRONE×25, DRONE×20 |
| 🟥 | Frenzied Pillagers | random | Future 88%, Modern 12% | ⬛ 0/48 (0%) | MECH_WARRIOR×11, SPECOPS×2 | DRONE×28, DRONE×27, DRONE×26, MECH_WARRIOR×24, MECH_WARRIOR×32, SIEGE_TANK×30, MECH_WARRIOR×28, MECH_WARRIOR×24, MECH_WARRIOR×20, DRONE×28, MECH_WARRIOR×32, DRONE×22, THE_GENERAL×18, MECH_WARRIOR×24, MECH_WARRIOR×28, MECH_WARRIOR×24 |
| 🟥 | Grumpy Marauders | random | Future 93%, Modern 7% | ⬛ 0/48 (0%) | MECH_WARRIOR×12 | DRONE×24, MECH_WARRIOR×28, DRONE×26, MECH_WARRIOR×24, MECH_WARRIOR×24, MECH_WARRIOR×24, SPECOPS×25, DRONE×30, DRONE×23, MECH_WARRIOR×32, MECH_WARRIOR×20, DRONE×24, MECH_WARRIOR×32, MECH_WARRIOR×28 |
| 🟩 | Forgotten Warband | random | Future 88%, Modern 12% | 🟡 32/48 (67%) | MECH_WARRIOR×4 | DRONE×24, DRONE×28, DRONE×28, MECH_WARRIOR×20, DRONE×31, MECH_WARRIOR×28, DRONE×20, SPECOPS×30, DRONE×21, DRONE×21, THE_GENERAL×18, DRONE×20, MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×28, MECH_WARRIOR×28 |
| 🟥 | Hungry Invaders | random | Future 86%, Modern 14% | ⬛ 0/48 (0%) | MECH_WARRIOR×9, SPECOPS×6 | SIEGE_TANK×28, MECH_WARRIOR×28, MECH_WARRIOR×24, DRONE×29, HELI×24, MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×33, DRONE×22, MECH_WARRIOR×20, MECH_WARRIOR×24, DRONE×26, DRONE×21, DRONE×23, DRONE×31 |
| 🟩 | Howling Savages | random | Future 84%, Modern 16% | 🔴 8/48 (17%) | MECH_WARRIOR×9, SPECOPS×2 | DRONE×31, DRONE×26, MECH_WARRIOR×24, DRONE×21, DRONE×25, DRONE×20, DRONE×22, SIEGE_TANK×28, DRONE×27, MECH_WARRIOR×32, MECH_WARRIOR×32, SPECOPS×29, DRONE×23, MECH_WARRIOR×24 |
| 🟩 | Rowdy Plunderers | random | Future 93%, Modern 7% | 🔴 6/48 (12%) | MECH_WARRIOR×9, SPECOPS×3 | DRONE×28, MECH_WARRIOR×24, DRONE×25, MECH_WARRIOR×28, HELI×30, DRONE×32, DRONE×33, MECH_WARRIOR×32, MECH_WARRIOR×24, DRONE×33, MECH_WARRIOR×24, DRONE×24, MECH_WARRIOR×28, DRONE×29, DRONE×30, DRONE×32 |
| 🟥 | Reckless Looters | random | Future 96%, Modern 4% | ⬛ 0/48 (0%) | MECH_WARRIOR×12 | MECH_WARRIOR×32, MECH_WARRIOR×20, DRONE×26, DRONE×23, DRONE×23, DRONE×32, MECH_WARRIOR×28, MECH_WARRIOR×24, MECH_WARRIOR×28, DRONE×29, DRONE×21, MECH_WARRIOR×28, THE_GENERAL×18, MECH_WARRIOR×24, DRONE×21, MECH_WARRIOR×24, DRONE×29 |
| 🟥 | Rampaging Rabble | random | Future 86%, Modern 14% | ⬛ 0/48 (0%) | MECH_WARRIOR×9, SPECOPS×7 | DRONE×22, DRONE×33, MECH_WARRIOR×32, DRONE×29, DRONE×31, DRONE×22, DRONE×31, MECH_WARRIOR×24, SPECOPS×24, SPECOPS×33, MECH_WARRIOR×24, MECH_WARRIOR×32, MECH_WARRIOR×24, MECH_WARRIOR×24, MECH_WARRIOR×24 |
| 🟥 | Disorganized Mob | random | Future 95%, Modern 5% | ⬛ 0/48 (0%) | MECH_WARRIOR×11, SPECOPS×2 | DRONE×21, THE_GENERAL×18, MECH_WARRIOR×28, MECH_WARRIOR×28, MECH_WARRIOR×32, DRONE×28, DRONE×22, MECH_WARRIOR×28, DRONE×29, DRONE×28, DRONE×29, DRONE×22, MECH_WARRIOR×20 |

#### S2 Gempire

| Tower Era Distribution (66 towers) | Towers |
|---|---|
| Modern 61% (40), Industrial 21% (14), Iron Age 12% (8), Future 5% (3), Renaissance 2% (1) | RADAR_TOWER×29, FLAME_THROWER×13, ANTI_AIR_TOWER×11, COLD_TOWER×8, LASER_TOWER×3, ICE_TOWER×1, SHOCK_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟥 | Mech Uprising | hardcoded | Future 100% | ⬛ 0/38 (0%) | DRONE×13, SPECOPS×7, MECH_WARRIOR×3 | MECH_WARRIOR×18, DRONE×18, MECH_WARRIOR×19, MECH_WARRIOR×19, MECH_WARRIOR×20, DRONE×20, MECH_WARRIOR×21, DRONE×21, MECH_WARRIOR×21, DRONE×22, MECH_WARRIOR×22, DRONE×23, MECH_WARRIOR×23, MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×24, DRONE×25, MECH_WARRIOR×25, DRONE×26, DRONE×26, MECH_WARRIOR×27, DRONE×27, DRONE×27, MECH_WARRIOR×28, DRONE×28, MECH_WARRIOR×29, DRONE×29, MECH_WARRIOR×30, DRONE×30 |
| 🟥 | Drone Swarm | hardcoded | Future 100% | ⬛ 0/38 (0%) | SPECOPS×15, DRONE×8 | DRONE×18, MECH_WARRIOR×18, MECH_WARRIOR×19, DRONE×19, DRONE×20, DRONE×20, MECH_WARRIOR×21, MECH_WARRIOR×21, MECH_WARRIOR×22, MECH_WARRIOR×22, DRONE×22, MECH_WARRIOR×23, MECH_WARRIOR×23, DRONE×24, MECH_WARRIOR×24, DRONE×25, MECH_WARRIOR×25, MECH_WARRIOR×26, MECH_WARRIOR×26, DRONE×26, MECH_WARRIOR×27, MECH_WARRIOR×27, MECH_WARRIOR×28, DRONE×28, DRONE×29, DRONE×29, DRONE×30, DRONE×30 |
| 🟥 | Future Shock | hardcoded | Future 100% | ⬛ 0/38 (0%) | DRONE×13, SPECOPS×9, MECH_WARRIOR×2 | MECH_WARRIOR×18, MECH_WARRIOR×18, DRONE×19, DRONE×19, MECH_WARRIOR×20, DRONE×20, MECH_WARRIOR×21, MECH_WARRIOR×21, MECH_WARRIOR×21, DRONE×22, MECH_WARRIOR×22, MECH_WARRIOR×23, DRONE×23, MECH_WARRIOR×24, DRONE×24, DRONE×24, MECH_WARRIOR×25, DRONE×25, MECH_WARRIOR×26, DRONE×26, DRONE×27, MECH_WARRIOR×27, DRONE×27, DRONE×28, DRONE×28, MECH_WARRIOR×29, DRONE×29, MECH_WARRIOR×30 |
| 🟥 | Rowdy Plunderers | random | Future 93%, Modern 7% | ⬛ 0/38 (0%) | DRONE×12, SPECOPS×5, MECH_WARRIOR×4 | MECH_WARRIOR×24, DRONE×20, DRONE×27, DRONE×26, MECH_WARRIOR×24, MECH_WARRIOR×32, MECH_WARRIOR×32, DRONE×23, DRONE×29, MECH_WARRIOR×24, DRONE×22, DRONE×30, DRONE×29, DRONE×28, MECH_WARRIOR×28, SPECOPS×31 |
| 🟥 | Rowdy Plunderers | random | Future 93%, Modern 7% | ⬛ 0/38 (0%) | DRONE×12, SPECOPS×5, MECH_WARRIOR×4 | MECH_WARRIOR×24, DRONE×20, DRONE×27, DRONE×26, MECH_WARRIOR×24, MECH_WARRIOR×32, MECH_WARRIOR×32, DRONE×23, DRONE×29, MECH_WARRIOR×24, DRONE×22, DRONE×30, DRONE×29, DRONE×28, MECH_WARRIOR×28, SPECOPS×31 |
| 🟥 | Relentless Mob | random | Future 93%, Modern 7% | ⬛ 0/38 (0%) | DRONE×18, SPECOPS×6, MECH_WARRIOR×2 | MECH_WARRIOR×28, SIEGE_TANK×34, DRONE×33, DRONE×31, DRONE×20, DRONE×26, DRONE×34, DRONE×22, MECH_WARRIOR×20, MECH_WARRIOR×28, DRONE×31, DRONE×29, MECH_WARRIOR×32, MECH_WARRIOR×28, DRONE×21, MECH_WARRIOR×32, DRONE×26 |
| 🟥 | Drunken Raiders | random | Future 93%, Modern 7% | ⬛ 0/38 (0%) | DRONE×25, SPECOPS×4, MECH_WARRIOR×2 | DRONE×30, DRONE×27, DRONE×20, MECH_WARRIOR×24, MECH_WARRIOR×28, DRONE×23, MECH_WARRIOR×24, MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×31, DRONE×30, DRONE×31, MECH_WARRIOR×24, MECH_WARRIOR×28, DRONE×33, SPECOPS×32, DRONE×32 |
| 🟥 | Shrieking Horde | random | Future 96%, Modern 4% | ⬛ 0/38 (0%) | DRONE×18, SPECOPS×8, MECH_WARRIOR×1 | DRONE×31, MECH_WARRIOR×32, DRONE×25, MECH_WARRIOR×24, DRONE×31, DRONE×25, DRONE×23, MECH_WARRIOR×24, MECH_WARRIOR×28, MECH_WARRIOR×20, MECH_WARRIOR×32, DRONE×26, HELI×20, DRONE×27, MECH_WARRIOR×28, MECH_WARRIOR×32, DRONE×30, MECH_WARRIOR×28 |
| 🟥 | Restless Horde | random | Future 85%, Modern 15% | ⬛ 0/38 (0%) | SPECOPS×14, DRONE×10 | DRONE×26, MECH_WARRIOR×24, THE_GENERAL×18, MECH_WARRIOR×20, SIEGE_TANK×26, SPECOPS×26, DRONE×32, MECH_WARRIOR×28, DRONE×26, MECH_WARRIOR×32, DRONE×31, DRONE×31, DRONE×32, MECH_WARRIOR×24, DRONE×24, DRONE×32, DRONE×31 |
| 🟥 | Stubborn Raiders | random | Future 95%, Modern 5% | ⬛ 0/38 (0%) | DRONE×16, MECH_WARRIOR×4, SPECOPS×4 | MECH_WARRIOR×32, DRONE×33, MECH_WARRIOR×24, DRONE×28, MECH_WARRIOR×32, DRONE×26, DRONE×20, DRONE×20, MECH_WARRIOR×28, SPECOPS×23, MECH_WARRIOR×24, MECH_WARRIOR×32, DRONE×26, DRONE×34, MECH_WARRIOR×28, MECH_WARRIOR×24 |
| 🟥 | Bored Mercenaries | random | Future 94%, Modern 6% | ⬛ 0/38 (0%) | DRONE×15, SPECOPS×10, MECH_WARRIOR×1 | DRONE×26, DRONE×28, MECH_WARRIOR×24, THE_GENERAL×18, MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×31, MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×28, DRONE×24, DRONE×22, MECH_WARRIOR×28 |
| 🟩 | Wandering Pillagers | random | Future 86%, Modern 14% | 🟠 13/38 (34%) | SPECOPS×9, DRONE×7 | SPECOPS×25, DRONE×22, MECH_WARRIOR×28, DRONE×27, DRONE×28, DRONE×28, MECH_WARRIOR×20, DRONE×22, HELI×24, DRONE×27, DRONE×31, DRONE×31, MECH_WARRIOR×28 |
| 🟥 | Grumpy Marauders | random | Future 82%, Modern 18% | ⬛ 0/38 (0%) | SPECOPS×11, DRONE×5, MECH_WARRIOR×3 | MECH_WARRIOR×32, MECH_WARRIOR×24, MECH_WARRIOR×24, SIEGE_TANK×28, DRONE×32, SPECOPS×21, MECH_WARRIOR×20, MECH_WARRIOR×28, THE_GENERAL×18, MECH_WARRIOR×24, DRONE×28, DRONE×29, MECH_WARRIOR×32, MECH_WARRIOR×28 |
| 🟥 | Savage Rabble | random | Future 84%, Modern 16% | ⬛ 0/38 (0%) | DRONE×16, SPECOPS×9, MECH_WARRIOR×1 | MECH_WARRIOR×20, SIEGE_TANK×22, HELI×20, MECH_WARRIOR×28, MECH_WARRIOR×32, DRONE×24, MECH_WARRIOR×28, SIEGE_TANK×22, DRONE×25, DRONE×23, DRONE×25, MECH_WARRIOR×32, DRONE×26, MECH_WARRIOR×24, DRONE×25, DRONE×20 |
| 🟥 | Frenzied Pillagers | random | Future 88%, Modern 12% | ⬛ 0/38 (0%) | DRONE×17, SPECOPS×6, MECH_WARRIOR×3 | DRONE×28, DRONE×27, DRONE×26, MECH_WARRIOR×24, MECH_WARRIOR×32, SIEGE_TANK×30, MECH_WARRIOR×28, MECH_WARRIOR×24, MECH_WARRIOR×20, DRONE×28, MECH_WARRIOR×32, DRONE×22, THE_GENERAL×18, MECH_WARRIOR×24, MECH_WARRIOR×28, MECH_WARRIOR×24 |
| 🟥 | Grumpy Marauders | random | Future 93%, Modern 7% | ⬛ 0/38 (0%) | DRONE×15, SPECOPS×10, MECH_WARRIOR×1 | DRONE×24, MECH_WARRIOR×28, DRONE×26, MECH_WARRIOR×24, MECH_WARRIOR×24, MECH_WARRIOR×24, SPECOPS×25, DRONE×30, DRONE×23, MECH_WARRIOR×32, MECH_WARRIOR×20, DRONE×24, MECH_WARRIOR×32, MECH_WARRIOR×28 |
| 🟥 | Forgotten Warband | random | Future 88%, Modern 12% | ⬛ 0/38 (0%) | SPECOPS×17, DRONE×4 | DRONE×24, DRONE×28, DRONE×28, MECH_WARRIOR×20, DRONE×31, MECH_WARRIOR×28, DRONE×20, SPECOPS×30, DRONE×21, DRONE×21, THE_GENERAL×18, DRONE×20, MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×28, MECH_WARRIOR×28 |
| 🟥 | Hungry Invaders | random | Future 86%, Modern 14% | ⬛ 0/38 (0%) | DRONE×7, SPECOPS×6, MECH_WARRIOR×5 | SIEGE_TANK×28, MECH_WARRIOR×28, MECH_WARRIOR×24, DRONE×29, HELI×24, MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×33, DRONE×22, MECH_WARRIOR×20, MECH_WARRIOR×24, DRONE×26, DRONE×21, DRONE×23, DRONE×31 |
| 🟥 | Howling Savages | random | Future 84%, Modern 16% | ⬛ 0/38 (0%) | SPECOPS×14, MECH_WARRIOR×3 | DRONE×31, DRONE×26, MECH_WARRIOR×24, DRONE×21, DRONE×25, DRONE×20, DRONE×22, SIEGE_TANK×28, DRONE×27, MECH_WARRIOR×32, MECH_WARRIOR×32, SPECOPS×29, DRONE×23, MECH_WARRIOR×24 |
| 🟥 | Rowdy Plunderers | random | Future 93%, Modern 7% | ⬛ 0/38 (0%) | DRONE×18, SPECOPS×6, MECH_WARRIOR×2, SOLDIER×1 | DRONE×28, MECH_WARRIOR×24, DRONE×25, MECH_WARRIOR×28, HELI×30, DRONE×32, DRONE×33, MECH_WARRIOR×32, MECH_WARRIOR×24, DRONE×33, MECH_WARRIOR×24, DRONE×24, MECH_WARRIOR×28, DRONE×29, DRONE×30, DRONE×32 |
| 🟥 | Reckless Looters | random | Future 96%, Modern 4% | ⬛ 0/38 (0%) | DRONE×15, MECH_WARRIOR×4, SPECOPS×4 | MECH_WARRIOR×32, MECH_WARRIOR×20, DRONE×26, DRONE×23, DRONE×23, DRONE×32, MECH_WARRIOR×28, MECH_WARRIOR×24, MECH_WARRIOR×28, DRONE×29, DRONE×21, MECH_WARRIOR×28, THE_GENERAL×18, MECH_WARRIOR×24, DRONE×21, MECH_WARRIOR×24, DRONE×29 |
| 🟥 | Rampaging Rabble | random | Future 86%, Modern 14% | ⬛ 0/38 (0%) | SPECOPS×10, DRONE×9, MECH_WARRIOR×3 | DRONE×22, DRONE×33, MECH_WARRIOR×32, DRONE×29, DRONE×31, DRONE×22, DRONE×31, MECH_WARRIOR×24, SPECOPS×24, SPECOPS×33, MECH_WARRIOR×24, MECH_WARRIOR×32, MECH_WARRIOR×24, MECH_WARRIOR×24, MECH_WARRIOR×24 |
| 🟥 | Disorganized Mob | random | Future 95%, Modern 5% | ⬛ 0/38 (0%) | DRONE×12, SPECOPS×9, MECH_WARRIOR×2 | DRONE×21, THE_GENERAL×18, MECH_WARRIOR×28, MECH_WARRIOR×28, MECH_WARRIOR×32, DRONE×28, DRONE×22, MECH_WARRIOR×28, DRONE×29, DRONE×28, DRONE×29, DRONE×22, MECH_WARRIOR×20 |

## Flagged Critters/Towers

### Stone Age
- **Critters UP (rarely reach the castle):** SLAVE (reach_rate=0.2%, era_mean=11.8%)

### Neolithic
- **Towers UP (damage share far below placement share):** SPIKE_TRAP (damage_share=6.5% vs placement_share=25.0%, ratio=0.26)

### Bronze Age
- **Towers UP (damage share far below placement share):** SPIKE_TRAP (damage_share=2.9% vs placement_share=16.7%, ratio=0.18); DOUBLE_SLING_TOWER (damage_share=2.7% vs placement_share=8.3%, ratio=0.33)

### Iron Age
- **Critters OP (reach rate far above era mean):** THE_SWORDMASTER (reach_rate=24.0%, era_mean=5.5%)
- **Critters UP (rarely reach the castle):** HORSEMAN_SLOW (reach_rate=0.1%, era_mean=5.5%); LARGE_CART (reach_rate=0.0%, era_mean=5.5%)

### Medieval
- **Towers OP (damage share far above placement share):** HEAVY_TOWER (damage_share=41.3% vs placement_share=19.2%, ratio=2.15); CANNON_TOWER (damage_share=13.0% vs placement_share=3.8%, ratio=3.38)
- **Towers UP (damage share far below placement share):** TAR_TOWER (damage_share=5.2% vs placement_share=19.2%, ratio=0.27); FIRE_TOWER (damage_share=0.8% vs placement_share=7.7%, ratio=0.11); BALLISTA_TOWER (damage_share=0.8% vs placement_share=7.7%, ratio=0.10); CATAPULTS (damage_share=1.0% vs placement_share=7.7%, ratio=0.13); DOUBLE_SLING_TOWER (damage_share=0.2% vs placement_share=3.8%, ratio=0.06); ARROW_TOWER (damage_share=0.1% vs placement_share=3.8%, ratio=0.02)

### Renaissance
- **Critters UP (rarely reach the castle):** NINJA (reach_rate=0.3%, era_mean=2.4%); DRAGOONER (reach_rate=0.3%, era_mean=2.4%); CARGO (reach_rate=0.0%, era_mean=2.4%)
- **Towers OP (damage share far above placement share):** RIFLE_TOWER (damage_share=55.5% vs placement_share=25.0%, ratio=2.22); HEAVY_TOWER (damage_share=24.3% vs placement_share=8.3%, ratio=2.91)
- **Towers UP (damage share far below placement share):** CANNON_TOWER (damage_share=6.3% vs placement_share=16.7%, ratio=0.38); ICE_TOWER (damage_share=3.8% vs placement_share=16.7%, ratio=0.23); COLD_TOWER (damage_share=0.1% vs placement_share=8.3%, ratio=0.01); TAR_TOWER (damage_share=1.3% vs placement_share=16.7%, ratio=0.08)

### Industrial
- **Towers OP (damage share far above placement share):** GATLING_TOWER (damage_share=53.8% vs placement_share=22.2%, ratio=2.42)
- **Towers UP (damage share far below placement share):** COLD_TOWER (damage_share=0.2% vs placement_share=22.2%, ratio=0.01); ICE_TOWER (damage_share=1.0% vs placement_share=16.7%, ratio=0.06); SHOCK_TOWER (damage_share=2.7% vs placement_share=11.1%, ratio=0.24)

### Modern
- **Critters UP (rarely reach the castle):** SIEGE_TANK (reach_rate=0.2%, era_mean=6.7%); HELI (reach_rate=0.0%, era_mean=6.7%)
- **Towers OP (damage share far above placement share):** MG_TOWER (damage_share=28.1% vs placement_share=10.0%, ratio=2.81)
- **Towers UP (damage share far below placement share):** SHOCK_TOWER (damage_share=1.5% vs placement_share=10.0%, ratio=0.15); PARALYZNG_TOWER (damage_share=1.2% vs placement_share=10.0%, ratio=0.12); COLD_TOWER (damage_share=0.2% vs placement_share=10.0%, ratio=0.02); ICE_TOWER (damage_share=0.1% vs placement_share=10.0%, ratio=0.01)

### Future
- **Towers OP (damage share far above placement share):** MG_TOWER (damage_share=31.2% vs placement_share=11.1%, ratio=2.81)
- **Towers UP (damage share far below placement share):** COLD_TOWER (damage_share=0.4% vs placement_share=16.7%, ratio=0.03); ICE_TOWER (damage_share=0.1% vs placement_share=11.1%, ratio=0.01); SHOCK_TOWER (damage_share=0.2% vs placement_share=5.6%, ratio=0.04)
