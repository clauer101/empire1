# Balancing Report

Generated: 2026-08-20T20:08:02.649065+00:00

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
| Neolithic | 48 | 56% | 88% | 50% |
| Bronze Age | 96 | 52% | 44% | 54% |
| Iron Age | 125 | 63% | 56% | 65% |
| Medieval | 130 | 61% | 53% | 63% |
| Renaissance | 96 | 28% | 6% | 32% |
| Industrial | 100 | 65% | 60% | 66% |
| Modern | 52 | 15% | 25% | 12% |
| Future | 69 | 0% | 0% | 0% |

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
| 🟥 | Drunken Raiders | random | Neolithic 100% | ⬛ 0/10 (0%) | WARRIOR×4, CLUBMAN×4, CART×1 | WARRIOR×9, CART×6, CART×9, WARRIOR×9, WARRIOR×7 |
| 🟥 | Shrieking Horde | random | Neolithic 100% | ⬛ 0/10 (0%) | WARRIOR×6, CART×2 | WARRIOR×7, WARRIOR×9, WARRIOR×9, CART×6, WARRIOR×6 |
| 🟥 | Disorganized Mob | random | Neolithic 100% | ⬛ 0/10 (0%) | CLUBMAN×9, WARRIOR×1 | CART×6, WARRIOR×6, CART×9, CART×9, WARRIOR×9 |
| 🟥 | Clumsy Attackers | random | Neolithic 81%, Stone Age 19% | ⬛ 0/10 (0%) | WARRIOR×7, SCOUT×3 | WARRIOR×10, WARRIOR×9, SCOUT×8, CART×9, CART×6 |
| 🟥 | Petty Bandits | random | Neolithic 69%, Bronze Age 31% | ⬛ 0/10 (0%) | BOWMAN×5 | BOWMAN×10, CART×9, WARRIOR×8, WARRIOR×5 |
| 🟥 | Grumpy Marauders | random | Neolithic 67%, Bronze Age 33% | ⬛ 0/10 (0%) | CLUBMAN×7, WARRIOR×1, BOWMAN×1 | WARRIOR×7, CART×9, BOWMAN×8 |
| 🟥 | Angry Mob | random | Neolithic 69%, Stone Age 31% | ⬛ 0/10 (0%) | CLUBMAN×5, WARRIOR×3, CART×1 | SLAVE×8, WARRIOR×9, CART×9 |
| 🟩 | Savage Rabble | random | Neolithic 71%, Stone Age 29% | 🟢 10/10 (100%) |  | CART×9, SCOUT×6, CART×6 |
| 🟥 | Petty Bandits | random | Neolithic 44%, Bronze Age 37%, Stone Age 19% | ⬛ 0/10 (0%) | CHARIOT×10 | SLAVE×5, CHARIOT×10, WARRIOR×6, CART×6 |
| 🟩 | Shrieking Horde | random | Neolithic 48%, Stone Age 26%, Bronze Age 26% | 🟠 2/10 (20%) | SWORDMAN×4 | CART×9, CLUBMAN×8, CART×6, SWORDMAN×8 |
| 🟥 | Unlucky Raiders | random | Neolithic 64%, Bronze Age 36% | ⬛ 0/10 (0%) | WARRIOR×5, CLUBMAN×4, SWORDMAN×1 | WARRIOR×8, CART×6, SWORDMAN×8 |
| 🟥 | Crude Invaders | random | Neolithic 100% | ⬛ 0/10 (0%) | WARRIOR×6, CART×2 | WARRIOR×5, WARRIOR×8, WARRIOR×5, CART×9 |
| 🟥 | Grumpy Marauders | random | Neolithic 77%, Bronze Age 23% | ⬛ 0/10 (0%) | CHARIOT×7, WARRIOR×3 | WARRIOR×8, CHARIOT×7, WARRIOR×10, WARRIOR×6 |
| 🟥 | Ragged Warband | random | Neolithic 100% | ⬛ 0/10 (0%) | WARRIOR×5, CART×2, CLUBMAN×1 | WARRIOR×5, WARRIOR×6, CART×9 |
| 🟥 | Savage Rabble | random | Neolithic 77%, Bronze Age 23% | ⬛ 0/10 (0%) | CHARIOT×7, CLUBMAN×3 | WARRIOR×10, CART×6, CHARIOT×7, WARRIOR×7 |
| 🟥 | Disorganized Mob | random | Neolithic 81%, Bronze Age 19% | ⬛ 0/10 (0%) | BOWMAN×5 | CART×6, BOWMAN×6, CART×9, CART×6, WARRIOR×5 |
| 🟥 | Muddy Marauders | random | Neolithic 60%, Bronze Age 20%, Stone Age 20% | ⬛ 0/10 (0%) | SWORDMAN×3, WARRIOR×3, SLAVE×1 | CART×9, SWORDMAN×6, WARRIOR×9, SLAVE×6 |
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
| 🟩 | Rowdy Plunderers | random | Neolithic 77%, Bronze Age 23% | 🟠 4/10 (40%) | CHARIOT×6 | CHARIOT×7, CART×6, CART×9, WARRIOR×8 |
| 🟩 | Rowdy Plunderers | random | Neolithic 77%, Bronze Age 23% | 🟠 4/10 (40%) | CHARIOT×6 | CHARIOT×7, CART×6, CART×9, WARRIOR×8 |
| 🟩 | Drunken Raiders | random | Neolithic 100% | 🟢 10/10 (100%) |  | WARRIOR×9, CART×6, CART×9, WARRIOR×9, WARRIOR×7 |
| 🟩 | Shrieking Horde | random | Neolithic 100% | 🟢 10/10 (100%) |  | WARRIOR×7, WARRIOR×9, WARRIOR×9, CART×6, WARRIOR×6 |
| 🟩 | Disorganized Mob | random | Neolithic 100% | 🟢 10/10 (100%) |  | CART×6, WARRIOR×6, CART×9, CART×9, WARRIOR×9 |
| 🟩 | Clumsy Attackers | random | Neolithic 81%, Stone Age 19% | 🟢 10/10 (100%) |  | WARRIOR×10, WARRIOR×9, SCOUT×8, CART×9, CART×6 |
| 🟥 | Petty Bandits | random | Neolithic 69%, Bronze Age 31% | ⬛ 0/10 (0%) | BOWMAN×5 | BOWMAN×10, CART×9, WARRIOR×8, WARRIOR×5 |
| 🟥 | Grumpy Marauders | random | Neolithic 67%, Bronze Age 33% | ⬛ 0/10 (0%) | BOWMAN×5 | WARRIOR×7, CART×9, BOWMAN×8 |
| 🟩 | Angry Mob | random | Neolithic 69%, Stone Age 31% | 🟢 10/10 (100%) |  | SLAVE×8, WARRIOR×9, CART×9 |
| 🟩 | Savage Rabble | random | Neolithic 71%, Stone Age 29% | 🟢 10/10 (100%) |  | CART×9, SCOUT×6, CART×6 |
| 🟩 | Petty Bandits | random | Neolithic 44%, Bronze Age 37%, Stone Age 19% | 🔴 1/10 (10%) | CHARIOT×9 | SLAVE×5, CHARIOT×10, WARRIOR×6, CART×6 |
| 🟩 | Shrieking Horde | random | Neolithic 48%, Stone Age 26%, Bronze Age 26% | 🟢 8/10 (80%) | SWORDMAN×1 | CART×9, CLUBMAN×8, CART×6, SWORDMAN×8 |
| 🟩 | Unlucky Raiders | random | Neolithic 64%, Bronze Age 36% | 🟡 6/10 (60%) | SWORDMAN×2 | WARRIOR×8, CART×6, SWORDMAN×8 |
| 🟩 | Crude Invaders | random | Neolithic 100% | 🟢 10/10 (100%) |  | WARRIOR×5, WARRIOR×8, WARRIOR×5, CART×9 |
| 🟩 | Grumpy Marauders | random | Neolithic 77%, Bronze Age 23% | 🟠 4/10 (40%) | CHARIOT×6 | WARRIOR×8, CHARIOT×7, WARRIOR×10, WARRIOR×6 |
| 🟩 | Ragged Warband | random | Neolithic 100% | 🟢 10/10 (100%) |  | WARRIOR×5, WARRIOR×6, CART×9 |
| 🟩 | Savage Rabble | random | Neolithic 77%, Bronze Age 23% | 🟠 3/10 (30%) | CHARIOT×7 | WARRIOR×10, CART×6, CHARIOT×7, WARRIOR×7 |
| 🟩 | Disorganized Mob | random | Neolithic 81%, Bronze Age 19% | 🟢 8/10 (80%) | BOWMAN×1 | CART×6, BOWMAN×6, CART×9, CART×6, WARRIOR×5 |
| 🟩 | Muddy Marauders | random | Neolithic 60%, Bronze Age 20%, Stone Age 20% | 🟢 10/10 (100%) |  | CART×9, SWORDMAN×6, WARRIOR×9, SLAVE×6 |
| 🟩 | Disorganized Mob | random | Neolithic 100% | 🟢 10/10 (100%) |  | WARRIOR×8, CART×9, CART×9 |

### Bronze Age

#### Arrow Bronze (len: 8)

| Tower Era Distribution (10 towers) | Towers |
|---|---|
| Bronze Age 100% (10) | ARROW_TOWER×7, FIRE_TOWER×3 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Bronze Warriors | hardcoded | Bronze Age 97%, Iron Age 3% | 🟡 7/13 (54%) | CHARIOT×6 | BOWMAN×6, BOWMAN×8, SWORDMAN×10, PIKENEER×2, SWORDMAN×10, CHARIOT×12, SWORDMAN×14 |
| 🟥 | Chariot Rush | hardcoded | Bronze Age 100% | ⬛ 0/13 (0%) | SWORDMAN×6, BOWMAN×1 | BOWMAN×12, SWORDMAN×12, SWORDMAN×12, BOWMAN×13, SWORDMAN×9, BOWMAN×12, SWORDMAN×14, SWORDMAN×16 |
| 🟥 | Copper Blades | hardcoded | Bronze Age 100% | ⬛ 0/13 (0%) | CHARIOT×13 | SWORDMAN×11, CHARIOT×12, CHARIOT×13, CHARIOT×14, SWORDMAN×14, CHARIOT×12, BOWMAN×14, CHARIOT×16 |
| 🟥 | Harbor Raiders | hardcoded | Bronze Age 100% | ⬛ 0/13 (0%) | BOWMAN×7 | BOWMAN×13, BOWMAN×14, BOWMAN×14, CHARIOT×15, SWORDMAN×15, BOWMAN×16, BOWMAN×14, BOWMAN×16, SWORDMAN×18 |
| 🟥 | Clumsy Attackers | random | Bronze Age 76%, Neolithic 13%, Iron Age 11% | ⬛ 0/13 (0%) | CHARIOT×8, PIKENEER×5 | SWORDMAN×8, PIKENEER×9, CHARIOT×10, SWORDMAN×8, CHARIOT×13, BOWMAN×11, CHARIOT×10, WARRIOR×10 |
| 🟥 | Clumsy Attackers | random | Bronze Age 76%, Neolithic 13%, Iron Age 11% | ⬛ 0/13 (0%) | CHARIOT×8, PIKENEER×5 | SWORDMAN×8, PIKENEER×9, CHARIOT×10, SWORDMAN×8, CHARIOT×13, BOWMAN×11, CHARIOT×10, WARRIOR×10 |
| 🟥 | Petty Bandits | random | Bronze Age 86%, Neolithic 14% | ⬛ 0/13 (0%) | BOWMAN×6, CHARIOT×1 | SWORDMAN×12, SWORDMAN×10, BOWMAN×12, BOWMAN×10, CHARIOT×10, WARRIOR×13, BOWMAN×11, SWORDMAN×12 |
| 🟥 | Noisy Barbarians | random | Bronze Age 89%, Neolithic 11% | ⬛ 0/13 (0%) | BOWMAN×5, CHARIOT×3 | SWORDMAN×10, CHARIOT×9, CART×9, BOWMAN×12, BOWMAN×9, BOWMAN×11, SWORDMAN×8, SWORDMAN×12 |
| 🟥 | Rude Barbarians | random | Bronze Age 87%, Neolithic 13% | ⬛ 0/13 (0%) | CHARIOT×13 | CART×12, BOWMAN×8, CHARIOT×10, SWORDMAN×12, CHARIOT×12, SWORDMAN×8, CHARIOT×10, CHARIOT×11, SWORDMAN×12 |
| 🟥 | Disorganized Mob | random | Bronze Age 73%, Neolithic 27% | ⬛ 0/13 (0%) | CHARIOT×9, SWORDMAN×2 | WARRIOR×12, SWORDMAN×12, CHARIOT×11, WARRIOR×12, BOWMAN×12, SWORDMAN×8, SWORDMAN×12, BOWMAN×10 |
| 🟥 | Shrieking Horde | random | Bronze Age 74%, Neolithic 15%, Iron Age 11% | ⬛ 0/13 (0%) | CHARIOT×11, SWORDMAN×1 | BOWMAN×10, SWORDMAN×8, CHARIOT×13, BOWMAN×13, HORSEMAN_FAST×9, BOWMAN×10, CART×12, BOWMAN×7 |
| 🟥 | Rowdy Plunderers | random | Bronze Age 66%, Neolithic 20%, Iron Age 14% | ⬛ 0/13 (0%) | CHARIOT×6, LEGIONARY×5, SWORDMAN×1 | CHARIOT×9, WARRIOR×12, CHARIOT×10, LEGIONARY×8, SWORDMAN×10, BOWMAN×10 |
| 🟩 | Crude Invaders | random | Bronze Age 70%, Neolithic 30% | 🟠 5/13 (38%) | CHARIOT×8 | SWORDMAN×12, BOWMAN×10, WARRIOR×10, CHARIOT×11, BOWMAN×10, WARRIOR×8 |
| 🟩 | Rampaging Rabble | random | Bronze Age 69%, Neolithic 31% | 🟠 3/13 (23%) | CHARIOT×10 | CHARIOT×11, CHARIOT×8, CART×9, CHARIOT×9, SWORDMAN×12, CART×9 |
| 🟥 | Drunken Raiders | random | Bronze Age 60%, Neolithic 24%, Iron Age 15% | ⬛ 0/13 (0%) | CHARIOT×7, PIKENEER×6 | CHARIOT×13, WARRIOR×10, CHARIOT×10, LARGE_CART×12, CART×9, BOWMAN×9, BOWMAN×7, SWORDMAN×8 |
| 🟩 | Howling Savages | random | Bronze Age 63%, Neolithic 25%, Iron Age 11% | 🔴 1/13 (8%) | CHARIOT×8, SWORDMAN×2 | CART×12, HORSEMAN_SLOW×9, SWORDMAN×8, WARRIOR×8, SWORDMAN×10, SWORDMAN×12, CHARIOT×10, SWORDMAN×10 |
| 🟥 | Bored Mercenaries | random | Bronze Age 67%, Neolithic 18%, Iron Age 15% | ⬛ 0/13 (0%) | LEGIONARY×8, CHARIOT×5 | CHARIOT×7, CHARIOT×8, SWORDMAN×10, CHARIOT×9, BOWMAN×11, LEGIONARY×10, CART×12 |
| 🟩 | Angry Mob | random | Bronze Age 88%, Neolithic 12% | 🔴 2/13 (15%) | CHARIOT×9, SWORDMAN×1 | CHARIOT×9, CART×9, SWORDMAN×10, BOWMAN×7, BOWMAN×8, SWORDMAN×10, CHARIOT×11, BOWMAN×10 |
| 🟥 | Noisy Barbarians | random | Bronze Age 75%, Iron Age 14%, Neolithic 11% | ⬛ 0/13 (0%) | CHARIOT×8, SWORDMAN×3 | BOWMAN×12, WARRIOR×8, BOWMAN×13, SWORDMAN×12, CHARIOT×9, SWORDMAN×8, HORSEMAN_FAST×10 |
| 🟩 | Restless Horde | random | Bronze Age 83%, Neolithic 17% | 🟢 13/13 (100%) |  | BOWMAN×7, CART×9, BOWMAN×7, SWORDMAN×10, SWORDMAN×8, SWORDMAN×12 |
| 🟥 | Howling Savages | random | Bronze Age 74%, Iron Age 15%, Neolithic 11% | ⬛ 0/13 (0%) | HORSEMAN_FAST×9, CHARIOT×4 | SWORDMAN×10, SWORDMAN×8, SWORDMAN×10, CART×9, CHARIOT×10, HORSEMAN_FAST×12, BOWMAN×9, BOWMAN×13 |
| 🟥 | Weary Plunderers | random | Bronze Age 74%, Iron Age 14%, Neolithic 12% | ⬛ 0/13 (0%) | HORSEMAN_FAST×7, CHARIOT×6 | HORSEMAN_FAST×11, BOWMAN×8, BOWMAN×8, CHARIOT×9, SWORDMAN×8, CART×9, CHARIOT×12, BOWMAN×11 |
| 🟥 | Weary Plunderers | random | Bronze Age 56%, Neolithic 27%, Iron Age 17% | ⬛ 0/13 (0%) | PIKENEER×8, SWORDMAN×2, BOWMAN×1 | SWORDMAN×12, SWORDMAN×10, PIKENEER×13, BOWMAN×12, BOWMAN×8, WARRIOR×11, CART×9 |
| 🟥 | Disorganized Mob | random | Bronze Age 84%, Neolithic 16% | ⬛ 0/13 (0%) | CHARIOT×9, BOWMAN×2 | SWORDMAN×10, BOWMAN×11, CHARIOT×8, SWORDMAN×10, WARRIOR×10, CHARIOT×13 |

#### Late Bronze

| Tower Era Distribution (14 towers) | Towers |
|---|---|
| Bronze Age 86% (12), Neolithic 14% (2) | ARROW_TOWER×5, BALLISTA_TOWER×4, FIRE_TOWER×3, SPIKE_TRAP×2 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Bronze Warriors | hardcoded | Bronze Age 97%, Iron Age 3% | 🟡 7/13 (54%) | CHARIOT×6 | BOWMAN×6, BOWMAN×8, SWORDMAN×10, PIKENEER×2, SWORDMAN×10, CHARIOT×12, SWORDMAN×14 |
| 🟩 | Chariot Rush | hardcoded | Bronze Age 100% | 🟢 11/13 (85%) | SWORDMAN×1 | BOWMAN×12, SWORDMAN×12, SWORDMAN×12, BOWMAN×13, SWORDMAN×9, BOWMAN×12, SWORDMAN×14, SWORDMAN×16 |
| 🟥 | Copper Blades | hardcoded | Bronze Age 100% | ⬛ 0/13 (0%) | CHARIOT×9, SWORDMAN×2 | SWORDMAN×11, CHARIOT×12, CHARIOT×13, CHARIOT×14, SWORDMAN×14, CHARIOT×12, BOWMAN×14, CHARIOT×16 |
| 🟥 | Harbor Raiders | hardcoded | Bronze Age 100% | ⬛ 0/13 (0%) | CHARIOT×5, BOWMAN×4 | BOWMAN×13, BOWMAN×14, BOWMAN×14, CHARIOT×15, SWORDMAN×15, BOWMAN×16, BOWMAN×14, BOWMAN×16, SWORDMAN×18 |
| 🟩 | Clumsy Attackers | random | Bronze Age 76%, Neolithic 13%, Iron Age 11% | 🟠 5/13 (38%) | CHARIOT×6, PIKENEER×2 | SWORDMAN×8, PIKENEER×9, CHARIOT×10, SWORDMAN×8, CHARIOT×13, BOWMAN×11, CHARIOT×10, WARRIOR×10 |
| 🟩 | Clumsy Attackers | random | Bronze Age 76%, Neolithic 13%, Iron Age 11% | 🟠 5/13 (38%) | CHARIOT×6, PIKENEER×2 | SWORDMAN×8, PIKENEER×9, CHARIOT×10, SWORDMAN×8, CHARIOT×13, BOWMAN×11, CHARIOT×10, WARRIOR×10 |
| 🟥 | Petty Bandits | random | Bronze Age 86%, Neolithic 14% | ⬛ 0/13 (0%) | CHARIOT×5, BOWMAN×4 | SWORDMAN×12, SWORDMAN×10, BOWMAN×12, BOWMAN×10, CHARIOT×10, WARRIOR×13, BOWMAN×11, SWORDMAN×12 |
| 🟩 | Noisy Barbarians | random | Bronze Age 89%, Neolithic 11% | 🟡 10/13 (77%) | CHARIOT×1, BOWMAN×1 | SWORDMAN×10, CHARIOT×9, CART×9, BOWMAN×12, BOWMAN×9, BOWMAN×11, SWORDMAN×8, SWORDMAN×12 |
| 🟩 | Rude Barbarians | random | Bronze Age 87%, Neolithic 13% | 🟠 3/13 (23%) | CHARIOT×10 | CART×12, BOWMAN×8, CHARIOT×10, SWORDMAN×12, CHARIOT×12, SWORDMAN×8, CHARIOT×10, CHARIOT×11, SWORDMAN×12 |
| 🟩 | Disorganized Mob | random | Bronze Age 73%, Neolithic 27% | 🟠 5/13 (38%) | CHARIOT×6, SWORDMAN×1 | WARRIOR×12, SWORDMAN×12, CHARIOT×11, WARRIOR×12, BOWMAN×12, SWORDMAN×8, SWORDMAN×12, BOWMAN×10 |
| 🟩 | Shrieking Horde | random | Bronze Age 74%, Neolithic 15%, Iron Age 11% | 🔴 1/13 (8%) | HORSEMAN_FAST×9, CHARIOT×3 | BOWMAN×10, SWORDMAN×8, CHARIOT×13, BOWMAN×13, HORSEMAN_FAST×9, BOWMAN×10, CART×12, BOWMAN×7 |
| 🟩 | Rowdy Plunderers | random | Bronze Age 66%, Neolithic 20%, Iron Age 14% | 🟢 11/13 (85%) | SWORDMAN×1 | CHARIOT×9, WARRIOR×12, CHARIOT×10, LEGIONARY×8, SWORDMAN×10, BOWMAN×10 |
| 🟩 | Crude Invaders | random | Bronze Age 70%, Neolithic 30% | 🟢 11/13 (85%) | CHARIOT×2 | SWORDMAN×12, BOWMAN×10, WARRIOR×10, CHARIOT×11, BOWMAN×10, WARRIOR×8 |
| 🟩 | Rampaging Rabble | random | Bronze Age 69%, Neolithic 31% | 🟢 13/13 (100%) |  | CHARIOT×11, CHARIOT×8, CART×9, CHARIOT×9, SWORDMAN×12, CART×9 |
| 🟩 | Drunken Raiders | random | Bronze Age 60%, Neolithic 24%, Iron Age 15% | 🟡 7/13 (54%) | PIKENEER×5, CHARIOT×1 | CHARIOT×13, WARRIOR×10, CHARIOT×10, LARGE_CART×12, CART×9, BOWMAN×9, BOWMAN×7, SWORDMAN×8 |
| 🟩 | Howling Savages | random | Bronze Age 63%, Neolithic 25%, Iron Age 11% | 🟡 10/13 (77%) | CHARIOT×3 | CART×12, HORSEMAN_SLOW×9, SWORDMAN×8, WARRIOR×8, SWORDMAN×10, SWORDMAN×12, CHARIOT×10, SWORDMAN×10 |
| 🟩 | Bored Mercenaries | random | Bronze Age 67%, Neolithic 18%, Iron Age 15% | 🟡 8/13 (62%) | LEGIONARY×4, CHARIOT×1 | CHARIOT×7, CHARIOT×8, SWORDMAN×10, CHARIOT×9, BOWMAN×11, LEGIONARY×10, CART×12 |
| 🟩 | Angry Mob | random | Bronze Age 88%, Neolithic 12% | 🟢 11/13 (85%) | CHARIOT×2 | CHARIOT×9, CART×9, SWORDMAN×10, BOWMAN×7, BOWMAN×8, SWORDMAN×10, CHARIOT×11, BOWMAN×10 |
| 🟥 | Noisy Barbarians | random | Bronze Age 75%, Iron Age 14%, Neolithic 11% | ⬛ 0/13 (0%) | CHARIOT×6, HORSEMAN_FAST×3, SWORDMAN×2 | BOWMAN×12, WARRIOR×8, BOWMAN×13, SWORDMAN×12, CHARIOT×9, SWORDMAN×8, HORSEMAN_FAST×10 |
| 🟩 | Restless Horde | random | Bronze Age 83%, Neolithic 17% | 🟢 13/13 (100%) |  | BOWMAN×7, CART×9, BOWMAN×7, SWORDMAN×10, SWORDMAN×8, SWORDMAN×12 |
| 🟩 | Howling Savages | random | Bronze Age 74%, Iron Age 15%, Neolithic 11% | 🟠 6/13 (46%) | HORSEMAN_FAST×5, CHARIOT×2 | SWORDMAN×10, SWORDMAN×8, SWORDMAN×10, CART×9, CHARIOT×10, HORSEMAN_FAST×12, BOWMAN×9, BOWMAN×13 |
| 🟩 | Weary Plunderers | random | Bronze Age 74%, Iron Age 14%, Neolithic 12% | 🟠 4/13 (31%) | CHARIOT×5, HORSEMAN_FAST×4 | HORSEMAN_FAST×11, BOWMAN×8, BOWMAN×8, CHARIOT×9, SWORDMAN×8, CART×9, CHARIOT×12, BOWMAN×11 |
| 🟩 | Weary Plunderers | random | Bronze Age 56%, Neolithic 27%, Iron Age 17% | 🟠 6/13 (46%) | PIKENEER×3, SWORDMAN×1, BOWMAN×1 | SWORDMAN×12, SWORDMAN×10, PIKENEER×13, BOWMAN×12, BOWMAN×8, WARRIOR×11, CART×9 |
| 🟩 | Disorganized Mob | random | Bronze Age 84%, Neolithic 16% | 🟠 5/13 (38%) | CHARIOT×8 | SWORDMAN×10, BOWMAN×11, CHARIOT×8, SWORDMAN×10, WARRIOR×10, CHARIOT×13 |

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
| 🟩 | Drunken Raiders | random | Bronze Age 60%, Neolithic 24%, Iron Age 15% | 🟢 12/13 (92%) | PIKENEER×1 | CHARIOT×13, WARRIOR×10, CHARIOT×10, LARGE_CART×12, CART×9, BOWMAN×9, BOWMAN×7, SWORDMAN×8 |
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
| 🟥 | Bronze Warriors | hardcoded | Bronze Age 97%, Iron Age 3% | ⬛ 0/13 (0%) | BOWMAN×7 | BOWMAN×6, BOWMAN×8, SWORDMAN×10, PIKENEER×2, SWORDMAN×10, CHARIOT×12, SWORDMAN×14 |
| 🟥 | Chariot Rush | hardcoded | Bronze Age 100% | ⬛ 0/13 (0%) | BOWMAN×7 | BOWMAN×12, SWORDMAN×12, SWORDMAN×12, BOWMAN×13, SWORDMAN×9, BOWMAN×12, SWORDMAN×14, SWORDMAN×16 |
| 🟥 | Copper Blades | hardcoded | Bronze Age 100% | ⬛ 0/13 (0%) | CHARIOT×10, SWORDMAN×2 | SWORDMAN×11, CHARIOT×12, CHARIOT×13, CHARIOT×14, SWORDMAN×14, CHARIOT×12, BOWMAN×14, CHARIOT×16 |
| 🟥 | Harbor Raiders | hardcoded | Bronze Age 100% | ⬛ 0/13 (0%) | BOWMAN×7 | BOWMAN×13, BOWMAN×14, BOWMAN×14, CHARIOT×15, SWORDMAN×15, BOWMAN×16, BOWMAN×14, BOWMAN×16, SWORDMAN×18 |
| 🟥 | Clumsy Attackers | random | Bronze Age 76%, Neolithic 13%, Iron Age 11% | ⬛ 0/13 (0%) | PIKENEER×6, CHARIOT×5, SWORDMAN×1 | SWORDMAN×8, PIKENEER×9, CHARIOT×10, SWORDMAN×8, CHARIOT×13, BOWMAN×11, CHARIOT×10, WARRIOR×10 |
| 🟥 | Clumsy Attackers | random | Bronze Age 76%, Neolithic 13%, Iron Age 11% | ⬛ 0/13 (0%) | PIKENEER×6, CHARIOT×5, SWORDMAN×1 | SWORDMAN×8, PIKENEER×9, CHARIOT×10, SWORDMAN×8, CHARIOT×13, BOWMAN×11, CHARIOT×10, WARRIOR×10 |
| 🟥 | Petty Bandits | random | Bronze Age 86%, Neolithic 14% | ⬛ 0/13 (0%) | SWORDMAN×6, BOWMAN×1 | SWORDMAN×12, SWORDMAN×10, BOWMAN×12, BOWMAN×10, CHARIOT×10, WARRIOR×13, BOWMAN×11, SWORDMAN×12 |
| 🟥 | Noisy Barbarians | random | Bronze Age 89%, Neolithic 11% | ⬛ 0/13 (0%) | CHARIOT×8, SWORDMAN×3 | SWORDMAN×10, CHARIOT×9, CART×9, BOWMAN×12, BOWMAN×9, BOWMAN×11, SWORDMAN×8, SWORDMAN×12 |
| 🟥 | Rude Barbarians | random | Bronze Age 87%, Neolithic 13% | ⬛ 0/13 (0%) | CHARIOT×5, BOWMAN×4 | CART×12, BOWMAN×8, CHARIOT×10, SWORDMAN×12, CHARIOT×12, SWORDMAN×8, CHARIOT×10, CHARIOT×11, SWORDMAN×12 |
| 🟥 | Disorganized Mob | random | Bronze Age 73%, Neolithic 27% | ⬛ 0/13 (0%) | CHARIOT×10, SWORDMAN×2 | WARRIOR×12, SWORDMAN×12, CHARIOT×11, WARRIOR×12, BOWMAN×12, SWORDMAN×8, SWORDMAN×12, BOWMAN×10 |
| 🟥 | Shrieking Horde | random | Bronze Age 74%, Neolithic 15%, Iron Age 11% | ⬛ 0/13 (0%) | BOWMAN×6, CHARIOT×1 | BOWMAN×10, SWORDMAN×8, CHARIOT×13, BOWMAN×13, HORSEMAN_FAST×9, BOWMAN×10, CART×12, BOWMAN×7 |
| 🟥 | Rowdy Plunderers | random | Bronze Age 66%, Neolithic 20%, Iron Age 14% | ⬛ 0/13 (0%) | CHARIOT×13 | CHARIOT×9, WARRIOR×12, CHARIOT×10, LEGIONARY×8, SWORDMAN×10, BOWMAN×10 |
| 🟥 | Crude Invaders | random | Bronze Age 70%, Neolithic 30% | ⬛ 0/13 (0%) | BOWMAN×4, SWORDMAN×3 | SWORDMAN×12, BOWMAN×10, WARRIOR×10, CHARIOT×11, BOWMAN×10, WARRIOR×8 |
| 🟥 | Rampaging Rabble | random | Bronze Age 69%, Neolithic 31% | ⬛ 0/13 (0%) | CHARIOT×13 | CHARIOT×11, CHARIOT×8, CART×9, CHARIOT×9, SWORDMAN×12, CART×9 |
| 🟥 | Drunken Raiders | random | Bronze Age 60%, Neolithic 24%, Iron Age 15% | ⬛ 0/13 (0%) | CHARIOT×13 | CHARIOT×13, WARRIOR×10, CHARIOT×10, LARGE_CART×12, CART×9, BOWMAN×9, BOWMAN×7, SWORDMAN×8 |
| 🟥 | Howling Savages | random | Bronze Age 63%, Neolithic 25%, Iron Age 11% | ⬛ 0/13 (0%) | SWORDMAN×4, HORSEMAN_SLOW×3 | CART×12, HORSEMAN_SLOW×9, SWORDMAN×8, WARRIOR×8, SWORDMAN×10, SWORDMAN×12, CHARIOT×10, SWORDMAN×10 |
| 🟥 | Bored Mercenaries | random | Bronze Age 67%, Neolithic 18%, Iron Age 15% | ⬛ 0/13 (0%) | CHARIOT×13 | CHARIOT×7, CHARIOT×8, SWORDMAN×10, CHARIOT×9, BOWMAN×11, LEGIONARY×10, CART×12 |
| 🟥 | Angry Mob | random | Bronze Age 88%, Neolithic 12% | ⬛ 0/13 (0%) | CHARIOT×6, SWORDMAN×3, BOWMAN×1 | CHARIOT×9, CART×9, SWORDMAN×10, BOWMAN×7, BOWMAN×8, SWORDMAN×10, CHARIOT×11, BOWMAN×10 |
| 🟥 | Noisy Barbarians | random | Bronze Age 75%, Iron Age 14%, Neolithic 11% | ⬛ 0/13 (0%) | BOWMAN×7 | BOWMAN×12, WARRIOR×8, BOWMAN×13, SWORDMAN×12, CHARIOT×9, SWORDMAN×8, HORSEMAN_FAST×10 |
| 🟥 | Restless Horde | random | Bronze Age 83%, Neolithic 17% | ⬛ 0/13 (0%) | BOWMAN×7 | BOWMAN×7, CART×9, BOWMAN×7, SWORDMAN×10, SWORDMAN×8, SWORDMAN×12 |
| 🟥 | Howling Savages | random | Bronze Age 74%, Iron Age 15%, Neolithic 11% | ⬛ 0/13 (0%) | SWORDMAN×6, CHARIOT×1 | SWORDMAN×10, SWORDMAN×8, SWORDMAN×10, CART×9, CHARIOT×10, HORSEMAN_FAST×12, BOWMAN×9, BOWMAN×13 |
| 🟥 | Weary Plunderers | random | Bronze Age 74%, Iron Age 14%, Neolithic 12% | ⬛ 0/13 (0%) | HORSEMAN_FAST×10, BOWMAN×2 | HORSEMAN_FAST×11, BOWMAN×8, BOWMAN×8, CHARIOT×9, SWORDMAN×8, CART×9, CHARIOT×12, BOWMAN×11 |
| 🟥 | Weary Plunderers | random | Bronze Age 56%, Neolithic 27%, Iron Age 17% | ⬛ 0/13 (0%) | PIKENEER×5, SWORDMAN×4 | SWORDMAN×12, SWORDMAN×10, PIKENEER×13, BOWMAN×12, BOWMAN×8, WARRIOR×11, CART×9 |
| 🟥 | Disorganized Mob | random | Bronze Age 84%, Neolithic 16% | ⬛ 0/13 (0%) | BOWMAN×3, CHARIOT×3, SWORDMAN×2 | SWORDMAN×10, BOWMAN×11, CHARIOT×8, SWORDMAN×10, WARRIOR×10, CHARIOT×13 |

### Iron Age

#### Schafshügel (Bronze)

| Tower Era Distribution (13 towers) | Towers |
|---|---|
| Bronze Age 77% (10), Iron Age 23% (3) | BALLISTA_TOWER×5, FIRE_TOWER×4, CATAPULTS×3, ARROW_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟥 | Iron Legion | hardcoded | Iron Age 100% | ⬛ 0/12 (0%) | PIKENEER×7, LEGIONARY×5 | HORSEMAN_SLOW×10, HORSEMAN_SLOW×10, LEGIONARY×11, PIKENEER×12, HORSEMAN_SLOW×12, PIKENEER×13, LEGIONARY×15, HORSEMAN_FAST×16, THE_SWORDMASTER×18, LEGIONARY×20, LEGIONARY×22, PIKENEER×24 |
| 🟥 | Cavalry Strike | hardcoded | Iron Age 96%, Medieval 4% | ⬛ 0/12 (0%) | PIKENEER×7, HORSEMAN_FAST×5 | LEGIONARY×14, PIKENEER×15, HORSEMAN_FAST×16, LARGE_CART×17, LEGIONARY×17, LEGIONARY×18, KNIGHT×9, PIKENEER×22, LARGE_CART×18, HORSEMAN_SLOW×20, HORSEMAN_SLOW×22, PIKENEER×24, LEGIONARY×26 |
| 🟥 | Legionary March | hardcoded | Iron Age 96%, Medieval 4% | ⬛ 0/12 (0%) | PIKENEER×7, LEGIONARY×2, HORSEMAN_SLOW×1, HORSEMAN_FAST×1 | LEGIONARY×14, HORSEMAN_SLOW×15, PIKENEER×16, HORSEMAN_FAST×17, HORSEMAN_FAST×17, HORSEMAN_SLOW×18, CRUSADER×9, LARGE_CART×20, LEGIONARY×18, HORSEMAN_FAST×20, LEGIONARY×22, HORSEMAN_FAST×24, THE_SWORDMASTER×26 |
| 🟥 | Iron Tide | hardcoded | Iron Age 95%, Medieval 5% | ⬛ 0/12 (0%) | HORSEMAN_FAST×12 | LEGIONARY×14, HORSEMAN_FAST×15, LARGE_CART×16, HORSEMAN_SLOW×16, LARGE_CART×17, HORSEMAN_FAST×18, LEGIONARY×18, THE_SWORDMASTER×19, PIKENEER×20, THE_SWORDMASTER×20, LARGE_CART×22, CRUSADER×12, THE_SWORDMASTER×26, LEGIONARY×28 |
| 🟥 | Quartermaster Force | hardcoded | Iron Age 92%, Bronze Age 8% | ⬛ 0/12 (0%) | PIKENEER×3, LEGIONARY×2, THE_SWORDMASTER×1 | THE_SWORDMASTER×16, LEGIONARY×17, HORSEMAN_SLOW×18, LARGE_CART×19, PIKENEER×20, LARGE_CART×21, LARGE_CART×22, LEGIONARY×16, PIKENEER×18, LARGE_CART×20, HORSEMAN_SLOW×22, HORSEMAN_SLOW×24, HORSEMAN_FAST×26, SWORDMAN×28, PIKENEER×28, LEGIONARY×28 |
| 🟥 | Desperate Looters | random | Iron Age 91%, Medieval 9% | ⬛ 0/12 (0%) | HORSEMAN_FAST×5, KNIGHT×3, PIKENEER×3, LEGIONARY×1 | KNIGHT×9, HORSEMAN_SLOW×13, HORSEMAN_FAST×8, LEGIONARY×13, HORSEMAN_SLOW×9, LARGE_CART×8, PIKENEER×11, HORSEMAN_FAST×11, HORSEMAN_FAST×15, THE_SWORDMASTER×7 |
| 🟥 | Desperate Looters | random | Iron Age 91%, Medieval 9% | ⬛ 0/12 (0%) | HORSEMAN_FAST×5, KNIGHT×3, PIKENEER×3, LEGIONARY×1 | KNIGHT×9, HORSEMAN_SLOW×13, HORSEMAN_FAST×8, LEGIONARY×13, HORSEMAN_SLOW×9, LARGE_CART×8, PIKENEER×11, HORSEMAN_FAST×11, HORSEMAN_FAST×15, THE_SWORDMASTER×7 |
| 🟥 | Restless Horde | random | Iron Age 92%, Bronze Age 8% | ⬛ 0/12 (0%) | PIKENEER×4, THE_SWORDMASTER×1, HORSEMAN_FAST×1 | LARGE_CART×8, THE_SWORDMASTER×7, LEGIONARY×11, HORSEMAN_SLOW×11, PIKENEER×14, HORSEMAN_FAST×13, HORSEMAN_FAST×9, LEGIONARY×14, CHARIOT×8, LEGIONARY×11 |
| 🟥 | Drunken Raiders | random | Iron Age 87%, Medieval 13% | ⬛ 0/12 (0%) | HORSEMAN_FAST×4, PIKENEER×1, THE_SWORDMASTER×1 | PIKENEER×13, HORSEMAN_SLOW×13, THE_SWORDMASTER×7, HORSEMAN_FAST×11, LEGIONARY×9, SIEGE_RAM×15, PIKENEER×10, HORSEMAN_SLOW×13, PIKENEER×13, HORSEMAN_FAST×14 |
| 🟥 | Howling Savages | random | Iron Age 89%, Bronze Age 11% | ⬛ 0/12 (0%) | HORSEMAN_FAST×11, LEGIONARY×1 | LEGIONARY×9, LEGIONARY×14, HORSEMAN_FAST×13, LEGIONARY×15, LARGE_CART×12, PIKENEER×10, LEGIONARY×13, SWORDMAN×14, LEGIONARY×11, HORSEMAN_FAST×11, THE_SWORDMASTER×7 |
| 🟥 | Bored Mercenaries | random | Iron Age 70%, Bronze Age 30% | ⬛ 0/12 (0%) | PIKENEER×7, LEGIONARY×4, CHARIOT×1 | LARGE_CART×12, HORSEMAN_SLOW×14, CHARIOT×10, BOWMAN×13, LEGIONARY×13, PIKENEER×11, HORSEMAN_SLOW×13, LEGIONARY×9, BOWMAN×14, HORSEMAN_FAST×14 |
| 🟥 | Crude Invaders | random | Iron Age 85%, Medieval 15% | ⬛ 0/12 (0%) | HANDGUNNER×12 | PIKENEER×8, HORSEMAN_SLOW×12, HANDGUNNER×15, LARGE_CART×8, PIKENEER×8, LARGE_CART×12, LEGIONARY×11, HORSEMAN_FAST×13, HORSEMAN_FAST×9, THE_SWORDMASTER×7 |
| 🟥 | Crude Invaders | random | Iron Age 77%, Medieval 23% | ⬛ 0/12 (0%) | SAMURAI×9, PIKENEER×3 | SAMURAI×10, HORSEMAN_SLOW×12, LARGE_CART×8, PIKENEER×13, LARGE_CART×12, LEGIONARY×9, HORSEMAN_FAST×11, SIEGE_RAM×9 |
| 🟩 | Restless Horde | random | Iron Age 76%, Bronze Age 24% | 🔴 2/12 (17%) | HORSEMAN_FAST×5, PIKENEER×5 | HORSEMAN_FAST×14, HORSEMAN_SLOW×9, BOWMAN×9, PIKENEER×12, CHARIOT×13, HORSEMAN_SLOW×12, PIKENEER×12, LARGE_CART×12 |
| 🟥 | Restless Horde | random | Iron Age 57%, Bronze Age 43% | ⬛ 0/12 (0%) | PIKENEER×3, BOWMAN×1, THE_SWORDMASTER×1 | SWORDMAN×10, LARGE_CART×8, LARGE_CART×12, PIKENEER×12, THE_SWORDMASTER×7, BOWMAN×15, BOWMAN×13, LEGIONARY×12 |
| 🟥 | Angry Mob | random | Iron Age 42%, Bronze Age 37%, Medieval 21% | ⬛ 0/12 (0%) | HANDGUNNER×7, HORSEMAN_FAST×2, THE_SWORDMASTER×1 | HANDGUNNER×9, THE_SWORDMASTER×7, HORSEMAN_FAST×9, LARGE_CART×12, SAMURAI×13, SWORDMAN×14, BOWMAN×14, PIKENEER×8, LARGE_CART×8, SWORDMAN×10 |
| 🟥 | Lazy Raiders | random | Iron Age 72%, Bronze Age 19%, Medieval 9% | ⬛ 0/12 (0%) | LEGIONARY×12 | LEGIONARY×12, LEGIONARY×14, LEGIONARY×9, LEGIONARY×9, BOWMAN×10, THE_SWORDMASTER×7, SWORDMAN×10, HORSEMAN_FAST×11, SIEGE_RAM×9, HORSEMAN_FAST×13 |
| 🟥 | Clumsy Attackers | random | Iron Age 90%, Medieval 10% | ⬛ 0/12 (0%) | HORSEMAN_FAST×9, PIKENEER×3 | HORSEMAN_SLOW×12, HORSEMAN_FAST×13, PIKENEER×14, THE_SWORDMASTER×7, PIKENEER×8, LEGIONARY×13, HANDGUNNER×10, HORSEMAN_FAST×14, LEGIONARY×12 |
| 🟥 | Unlucky Raiders | random | Iron Age 89%, Bronze Age 11% | ⬛ 0/12 (0%) | HORSEMAN_FAST×10, LEGIONARY×2 | LEGIONARY×13, HORSEMAN_FAST×11, SWORDMAN×12, HORSEMAN_FAST×12, PIKENEER×9, PIKENEER×13, HORSEMAN_FAST×12, HORSEMAN_SLOW×9, PIKENEER×8, THE_SWORDMASTER×7 |
| 🟥 | Lazy Raiders | random | Iron Age 72%, Bronze Age 14%, Medieval 13% | ⬛ 0/12 (0%) | HORSEMAN_FAST×6, THE_SWORDMASTER×1 | HORSEMAN_FAST×13, SWORDMAN×14, HORSEMAN_FAST×9, HORSEMAN_SLOW×8, THE_SWORDMASTER×7, LEGIONARY×8, CRUSADER×13, PIKENEER×10, PIKENEER×15 |
| 🟥 | Forgotten Warband | random | Iron Age 71%, Medieval 18%, Bronze Age 11% | ⬛ 0/12 (0%) | HORSEMAN_FAST×6, PIKENEER×5, LEGIONARY×1 | HORSEMAN_SLOW×8, HORSEMAN_FAST×11, LEGIONARY×15, LARGE_CART×8, HANDGUNNER×15, HORSEMAN_FAST×10, HORSEMAN_SLOW×8, BOWMAN×9 |
| 🟥 | Grumpy Marauders | random | Iron Age 82%, Medieval 18% | ⬛ 0/12 (0%) | PIKENEER×5, LEGIONARY×4, HORSEMAN_FAST×3 | LEGIONARY×9, PIKENEER×15, HORSEMAN_SLOW×11, HORSEMAN_FAST×10, HANDGUNNER×9, HORSEMAN_FAST×8, HORSEMAN_SLOW×11, THE_SWORDMASTER×7, CONDOTTERI×10, HORSEMAN_FAST×14 |
| 🟥 | Hungry Invaders | random | Iron Age 89%, Medieval 11% | ⬛ 0/12 (0%) | HORSEMAN_FAST×6, CRUSADER×3, PIKENEER×1 | LARGE_CART×12, HORSEMAN_FAST×13, HORSEMAN_SLOW×12, SIEGE_RAM×12, LEGIONARY×10, LARGE_CART×8, LARGE_CART×12, LARGE_CART×12, PIKENEER×9, HORSEMAN_SLOW×10 |
| 🟥 | Clumsy Attackers | random | Iron Age 64%, Bronze Age 27%, Medieval 8% | ⬛ 0/12 (0%) | HORSEMAN_FAST×7, CHARIOT×5 | HORSEMAN_SLOW×9, HORSEMAN_FAST×12, LEGIONARY×9, HORSEMAN_SLOW×14, LEGIONARY×11, CHARIOT×14, SAMURAI×9, LEGIONARY×13, BOWMAN×15 |
| 🟥 | Grumpy Marauders | random | Iron Age 78%, Medieval 13%, Bronze Age 10% | ⬛ 0/12 (0%) | CRUSADER×3, SIEGE_RAM×2 | LEGIONARY×12, SIEGE_RAM×12, HORSEMAN_FAST×12, HORSEMAN_FAST×12, LARGE_CART×16, HORSEMAN_SLOW×13, LARGE_CART×8, BOWMAN×9 |

#### Mixed Iron/Bronze

| Tower Era Distribution (31 towers) | Towers |
|---|---|
| Bronze Age 68% (21), Iron Age 32% (10) | FIRE_TOWER×9, CATAPULTS×8, ARROW_TOWER×6, BALLISTA_TOWER×6, ARBELESTE_TOWER×2 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Iron Legion | hardcoded | Iron Age 100% | 🟢 16/16 (100%) |  | HORSEMAN_SLOW×10, HORSEMAN_SLOW×10, LEGIONARY×11, PIKENEER×12, HORSEMAN_SLOW×12, PIKENEER×13, LEGIONARY×15, HORSEMAN_FAST×16, THE_SWORDMASTER×18, LEGIONARY×20, LEGIONARY×22, PIKENEER×24 |
| 🟩 | Cavalry Strike | hardcoded | Iron Age 96%, Medieval 4% | 🟢 13/16 (81%) | KNIGHT×3 | LEGIONARY×14, PIKENEER×15, HORSEMAN_FAST×16, LARGE_CART×17, LEGIONARY×17, LEGIONARY×18, KNIGHT×9, PIKENEER×22, LARGE_CART×18, HORSEMAN_SLOW×20, HORSEMAN_SLOW×22, PIKENEER×24, LEGIONARY×26 |
| 🟥 | Legionary March | hardcoded | Iron Age 96%, Medieval 4% | ⬛ 0/16 (0%) | CRUSADER×5, THE_SWORDMASTER×1 | LEGIONARY×14, HORSEMAN_SLOW×15, PIKENEER×16, HORSEMAN_FAST×17, HORSEMAN_FAST×17, HORSEMAN_SLOW×18, CRUSADER×9, LARGE_CART×20, LEGIONARY×18, HORSEMAN_FAST×20, LEGIONARY×22, HORSEMAN_FAST×24, THE_SWORDMASTER×26 |
| 🟩 | Iron Tide | hardcoded | Iron Age 95%, Medieval 5% | 🔴 3/16 (19%) | CRUSADER×3, THE_SWORDMASTER×1 | LEGIONARY×14, HORSEMAN_FAST×15, LARGE_CART×16, HORSEMAN_SLOW×16, LARGE_CART×17, HORSEMAN_FAST×18, LEGIONARY×18, THE_SWORDMASTER×19, PIKENEER×20, THE_SWORDMASTER×20, LARGE_CART×22, CRUSADER×12, THE_SWORDMASTER×26, LEGIONARY×28 |
| 🟩 | Quartermaster Force | hardcoded | Iron Age 92%, Bronze Age 8% | 🟢 16/16 (100%) |  | THE_SWORDMASTER×16, LEGIONARY×17, HORSEMAN_SLOW×18, LARGE_CART×19, PIKENEER×20, LARGE_CART×21, LARGE_CART×22, LEGIONARY×16, PIKENEER×18, LARGE_CART×20, HORSEMAN_SLOW×22, HORSEMAN_SLOW×24, HORSEMAN_FAST×26, SWORDMAN×28, PIKENEER×28, LEGIONARY×28 |
| 🟩 | Desperate Looters | random | Iron Age 91%, Medieval 9% | 🟢 14/16 (88%) | KNIGHT×2 | KNIGHT×9, HORSEMAN_SLOW×13, HORSEMAN_FAST×8, LEGIONARY×13, HORSEMAN_SLOW×9, LARGE_CART×8, PIKENEER×11, HORSEMAN_FAST×11, HORSEMAN_FAST×15, THE_SWORDMASTER×7 |
| 🟩 | Desperate Looters | random | Iron Age 91%, Medieval 9% | 🟢 14/16 (88%) | KNIGHT×2 | KNIGHT×9, HORSEMAN_SLOW×13, HORSEMAN_FAST×8, LEGIONARY×13, HORSEMAN_SLOW×9, LARGE_CART×8, PIKENEER×11, HORSEMAN_FAST×11, HORSEMAN_FAST×15, THE_SWORDMASTER×7 |
| 🟩 | Restless Horde | random | Iron Age 92%, Bronze Age 8% | 🟢 16/16 (100%) |  | LARGE_CART×8, THE_SWORDMASTER×7, LEGIONARY×11, HORSEMAN_SLOW×11, PIKENEER×14, HORSEMAN_FAST×13, HORSEMAN_FAST×9, LEGIONARY×14, CHARIOT×8, LEGIONARY×11 |
| 🟥 | Drunken Raiders | random | Iron Age 87%, Medieval 13% | ⬛ 0/16 (0%) | CRUSADER×3, THE_SWORDMASTER×1, SIEGE_RAM×1 | PIKENEER×13, HORSEMAN_SLOW×13, THE_SWORDMASTER×7, HORSEMAN_FAST×11, LEGIONARY×9, SIEGE_RAM×15, PIKENEER×10, HORSEMAN_SLOW×13, PIKENEER×13, HORSEMAN_FAST×14 |
| 🟩 | Howling Savages | random | Iron Age 89%, Bronze Age 11% | 🟢 16/16 (100%) |  | LEGIONARY×9, LEGIONARY×14, HORSEMAN_FAST×13, LEGIONARY×15, LARGE_CART×12, PIKENEER×10, LEGIONARY×13, SWORDMAN×14, LEGIONARY×11, HORSEMAN_FAST×11, THE_SWORDMASTER×7 |
| 🟩 | Bored Mercenaries | random | Iron Age 70%, Bronze Age 30% | 🟢 16/16 (100%) |  | LARGE_CART×12, HORSEMAN_SLOW×14, CHARIOT×10, BOWMAN×13, LEGIONARY×13, PIKENEER×11, HORSEMAN_SLOW×13, LEGIONARY×9, BOWMAN×14, HORSEMAN_FAST×14 |
| 🟩 | Crude Invaders | random | Iron Age 85%, Medieval 15% | 🔴 3/16 (19%) | HANDGUNNER×13 | PIKENEER×8, HORSEMAN_SLOW×12, HANDGUNNER×15, LARGE_CART×8, PIKENEER×8, LARGE_CART×12, LEGIONARY×11, HORSEMAN_FAST×13, HORSEMAN_FAST×9, THE_SWORDMASTER×7 |
| 🟩 | Crude Invaders | random | Iron Age 77%, Medieval 23% | 🟠 7/16 (44%) | CRUSADER×2, SAMURAI×1, SIEGE_RAM×1 | SAMURAI×10, HORSEMAN_SLOW×12, LARGE_CART×8, PIKENEER×13, LARGE_CART×12, LEGIONARY×9, HORSEMAN_FAST×11, SIEGE_RAM×9 |
| 🟩 | Restless Horde | random | Iron Age 76%, Bronze Age 24% | 🟢 16/16 (100%) |  | HORSEMAN_FAST×14, HORSEMAN_SLOW×9, BOWMAN×9, PIKENEER×12, CHARIOT×13, HORSEMAN_SLOW×12, PIKENEER×12, LARGE_CART×12 |
| 🟩 | Restless Horde | random | Iron Age 57%, Bronze Age 43% | 🟢 16/16 (100%) |  | SWORDMAN×10, LARGE_CART×8, LARGE_CART×12, PIKENEER×12, THE_SWORDMASTER×7, BOWMAN×15, BOWMAN×13, LEGIONARY×12 |
| 🟩 | Angry Mob | random | Iron Age 42%, Bronze Age 37%, Medieval 21% | 🟡 8/16 (50%) | HANDGUNNER×5, SAMURAI×3 | HANDGUNNER×9, THE_SWORDMASTER×7, HORSEMAN_FAST×9, LARGE_CART×12, SAMURAI×13, SWORDMAN×14, BOWMAN×14, PIKENEER×8, LARGE_CART×8, SWORDMAN×10 |
| 🟩 | Lazy Raiders | random | Iron Age 72%, Bronze Age 19%, Medieval 9% | 🟠 6/16 (38%) | CRUSADER×3, SIEGE_RAM×1 | LEGIONARY×12, LEGIONARY×14, LEGIONARY×9, LEGIONARY×9, BOWMAN×10, THE_SWORDMASTER×7, SWORDMAN×10, HORSEMAN_FAST×11, SIEGE_RAM×9, HORSEMAN_FAST×13 |
| 🟩 | Clumsy Attackers | random | Iron Age 90%, Medieval 10% | 🟡 8/16 (50%) | HANDGUNNER×8 | HORSEMAN_SLOW×12, HORSEMAN_FAST×13, PIKENEER×14, THE_SWORDMASTER×7, PIKENEER×8, LEGIONARY×13, HANDGUNNER×10, HORSEMAN_FAST×14, LEGIONARY×12 |
| 🟩 | Unlucky Raiders | random | Iron Age 89%, Bronze Age 11% | 🟢 16/16 (100%) |  | LEGIONARY×13, HORSEMAN_FAST×11, SWORDMAN×12, HORSEMAN_FAST×12, PIKENEER×9, PIKENEER×13, HORSEMAN_FAST×12, HORSEMAN_SLOW×9, PIKENEER×8, THE_SWORDMASTER×7 |
| 🟩 | Lazy Raiders | random | Iron Age 72%, Bronze Age 14%, Medieval 13% | 🟡 11/16 (69%) | CRUSADER×2, PIKENEER×1 | HORSEMAN_FAST×13, SWORDMAN×14, HORSEMAN_FAST×9, HORSEMAN_SLOW×8, THE_SWORDMASTER×7, LEGIONARY×8, CRUSADER×13, PIKENEER×10, PIKENEER×15 |
| 🟩 | Forgotten Warband | random | Iron Age 71%, Medieval 18%, Bronze Age 11% | 🟠 4/16 (25%) | HANDGUNNER×12 | HORSEMAN_SLOW×8, HORSEMAN_FAST×11, LEGIONARY×15, LARGE_CART×8, HANDGUNNER×15, HORSEMAN_FAST×10, HORSEMAN_SLOW×8, BOWMAN×9 |
| 🟥 | Grumpy Marauders | random | Iron Age 82%, Medieval 18% | ⬛ 0/16 (0%) | HANDGUNNER×5, CONDOTTERI×2, HORSEMAN_FAST×1, THE_SWORDMASTER×1 | LEGIONARY×9, PIKENEER×15, HORSEMAN_SLOW×11, HORSEMAN_FAST×10, HANDGUNNER×9, HORSEMAN_FAST×8, HORSEMAN_SLOW×11, THE_SWORDMASTER×7, CONDOTTERI×10, HORSEMAN_FAST×14 |
| 🟥 | Hungry Invaders | random | Iron Age 89%, Medieval 11% | ⬛ 0/16 (0%) | CRUSADER×6, SIEGE_RAM×1 | LARGE_CART×12, HORSEMAN_FAST×13, HORSEMAN_SLOW×12, SIEGE_RAM×12, LEGIONARY×10, LARGE_CART×8, LARGE_CART×12, LARGE_CART×12, PIKENEER×9, HORSEMAN_SLOW×10 |
| 🟩 | Clumsy Attackers | random | Iron Age 64%, Bronze Age 27%, Medieval 8% | 🟢 14/16 (88%) | SAMURAI×2 | HORSEMAN_SLOW×9, HORSEMAN_FAST×12, LEGIONARY×9, HORSEMAN_SLOW×14, LEGIONARY×11, CHARIOT×14, SAMURAI×9, LEGIONARY×13, BOWMAN×15 |
| 🟥 | Grumpy Marauders | random | Iron Age 78%, Medieval 13%, Bronze Age 10% | ⬛ 0/16 (0%) | CRUSADER×6, SIEGE_RAM×1 | LEGIONARY×12, SIEGE_RAM×12, HORSEMAN_FAST×12, HORSEMAN_FAST×12, LARGE_CART×16, HORSEMAN_SLOW×13, LARGE_CART×8, BOWMAN×9 |

#### Almost Bronze

| Tower Era Distribution (25 towers) | Towers |
|---|---|
| Bronze Age 92% (23), Iron Age 8% (2) | ARROW_TOWER×14, BALLISTA_TOWER×7, FIRE_TOWER×2, ARBELESTE_TOWER×2 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟥 | Iron Legion | hardcoded | Iron Age 100% | ⬛ 0/13 (0%) | LEGIONARY×10, PIKENEER×3 | HORSEMAN_SLOW×10, HORSEMAN_SLOW×10, LEGIONARY×11, PIKENEER×12, HORSEMAN_SLOW×12, PIKENEER×13, LEGIONARY×15, HORSEMAN_FAST×16, THE_SWORDMASTER×18, LEGIONARY×20, LEGIONARY×22, PIKENEER×24 |
| 🟥 | Cavalry Strike | hardcoded | Iron Age 96%, Medieval 4% | ⬛ 0/13 (0%) | PIKENEER×5, LEGIONARY×3, KNIGHT×3, HORSEMAN_FAST×2 | LEGIONARY×14, PIKENEER×15, HORSEMAN_FAST×16, LARGE_CART×17, LEGIONARY×17, LEGIONARY×18, KNIGHT×9, PIKENEER×22, LARGE_CART×18, HORSEMAN_SLOW×20, HORSEMAN_SLOW×22, PIKENEER×24, LEGIONARY×26 |
| 🟥 | Legionary March | hardcoded | Iron Age 96%, Medieval 4% | ⬛ 0/13 (0%) | CRUSADER×6, HORSEMAN_FAST×1 | LEGIONARY×14, HORSEMAN_SLOW×15, PIKENEER×16, HORSEMAN_FAST×17, HORSEMAN_FAST×17, HORSEMAN_SLOW×18, CRUSADER×9, LARGE_CART×20, LEGIONARY×18, HORSEMAN_FAST×20, LEGIONARY×22, HORSEMAN_FAST×24, THE_SWORDMASTER×26 |
| 🟥 | Iron Tide | hardcoded | Iron Age 95%, Medieval 5% | ⬛ 0/13 (0%) | CRUSADER×2, HORSEMAN_FAST×1, PIKENEER×1, THE_SWORDMASTER×1 | LEGIONARY×14, HORSEMAN_FAST×15, LARGE_CART×16, HORSEMAN_SLOW×16, LARGE_CART×17, HORSEMAN_FAST×18, LEGIONARY×18, THE_SWORDMASTER×19, PIKENEER×20, THE_SWORDMASTER×20, LARGE_CART×22, CRUSADER×12, THE_SWORDMASTER×26, LEGIONARY×28 |
| 🟥 | Quartermaster Force | hardcoded | Iron Age 92%, Bronze Age 8% | ⬛ 0/13 (0%) | PIKENEER×9, HORSEMAN_FAST×4 | THE_SWORDMASTER×16, LEGIONARY×17, HORSEMAN_SLOW×18, LARGE_CART×19, PIKENEER×20, LARGE_CART×21, LARGE_CART×22, LEGIONARY×16, PIKENEER×18, LARGE_CART×20, HORSEMAN_SLOW×22, HORSEMAN_SLOW×24, HORSEMAN_FAST×26, SWORDMAN×28, PIKENEER×28, LEGIONARY×28 |
| 🟩 | Desperate Looters | random | Iron Age 91%, Medieval 9% | 🟢 11/13 (85%) | KNIGHT×2 | KNIGHT×9, HORSEMAN_SLOW×13, HORSEMAN_FAST×8, LEGIONARY×13, HORSEMAN_SLOW×9, LARGE_CART×8, PIKENEER×11, HORSEMAN_FAST×11, HORSEMAN_FAST×15, THE_SWORDMASTER×7 |
| 🟩 | Desperate Looters | random | Iron Age 91%, Medieval 9% | 🟢 11/13 (85%) | KNIGHT×2 | KNIGHT×9, HORSEMAN_SLOW×13, HORSEMAN_FAST×8, LEGIONARY×13, HORSEMAN_SLOW×9, LARGE_CART×8, PIKENEER×11, HORSEMAN_FAST×11, HORSEMAN_FAST×15, THE_SWORDMASTER×7 |
| 🟩 | Restless Horde | random | Iron Age 92%, Bronze Age 8% | 🟢 13/13 (100%) |  | LARGE_CART×8, THE_SWORDMASTER×7, LEGIONARY×11, HORSEMAN_SLOW×11, PIKENEER×14, HORSEMAN_FAST×13, HORSEMAN_FAST×9, LEGIONARY×14, CHARIOT×8, LEGIONARY×11 |
| 🟥 | Drunken Raiders | random | Iron Age 87%, Medieval 13% | ⬛ 0/13 (0%) | CRUSADER×3, THE_SWORDMASTER×1 | PIKENEER×13, HORSEMAN_SLOW×13, THE_SWORDMASTER×7, HORSEMAN_FAST×11, LEGIONARY×9, SIEGE_RAM×15, PIKENEER×10, HORSEMAN_SLOW×13, PIKENEER×13, HORSEMAN_FAST×14 |
| 🟩 | Howling Savages | random | Iron Age 89%, Bronze Age 11% | 🟢 13/13 (100%) |  | LEGIONARY×9, LEGIONARY×14, HORSEMAN_FAST×13, LEGIONARY×15, LARGE_CART×12, PIKENEER×10, LEGIONARY×13, SWORDMAN×14, LEGIONARY×11, HORSEMAN_FAST×11, THE_SWORDMASTER×7 |
| 🟩 | Bored Mercenaries | random | Iron Age 70%, Bronze Age 30% | 🟢 13/13 (100%) |  | LARGE_CART×12, HORSEMAN_SLOW×14, CHARIOT×10, BOWMAN×13, LEGIONARY×13, PIKENEER×11, HORSEMAN_SLOW×13, LEGIONARY×9, BOWMAN×14, HORSEMAN_FAST×14 |
| 🟥 | Crude Invaders | random | Iron Age 85%, Medieval 15% | ⬛ 0/13 (0%) | HANDGUNNER×13 | PIKENEER×8, HORSEMAN_SLOW×12, HANDGUNNER×15, LARGE_CART×8, PIKENEER×8, LARGE_CART×12, LEGIONARY×11, HORSEMAN_FAST×13, HORSEMAN_FAST×9, THE_SWORDMASTER×7 |
| 🟥 | Crude Invaders | random | Iron Age 77%, Medieval 23% | ⬛ 0/13 (0%) | SAMURAI×4, CRUSADER×3, SIEGE_RAM×1 | SAMURAI×10, HORSEMAN_SLOW×12, LARGE_CART×8, PIKENEER×13, LARGE_CART×12, LEGIONARY×9, HORSEMAN_FAST×11, SIEGE_RAM×9 |
| 🟩 | Restless Horde | random | Iron Age 76%, Bronze Age 24% | 🟢 13/13 (100%) |  | HORSEMAN_FAST×14, HORSEMAN_SLOW×9, BOWMAN×9, PIKENEER×12, CHARIOT×13, HORSEMAN_SLOW×12, PIKENEER×12, LARGE_CART×12 |
| 🟩 | Restless Horde | random | Iron Age 57%, Bronze Age 43% | 🟢 13/13 (100%) |  | SWORDMAN×10, LARGE_CART×8, LARGE_CART×12, PIKENEER×12, THE_SWORDMASTER×7, BOWMAN×15, BOWMAN×13, LEGIONARY×12 |
| 🟩 | Angry Mob | random | Iron Age 42%, Bronze Age 37%, Medieval 21% | 🔴 1/13 (8%) | SAMURAI×7, HANDGUNNER×5 | HANDGUNNER×9, THE_SWORDMASTER×7, HORSEMAN_FAST×9, LARGE_CART×12, SAMURAI×13, SWORDMAN×14, BOWMAN×14, PIKENEER×8, LARGE_CART×8, SWORDMAN×10 |
| 🟥 | Lazy Raiders | random | Iron Age 72%, Bronze Age 19%, Medieval 9% | ⬛ 0/13 (0%) | THE_SWORDMASTER×1, SIEGE_RAM×1, CRUSADER×1 | LEGIONARY×12, LEGIONARY×14, LEGIONARY×9, LEGIONARY×9, BOWMAN×10, THE_SWORDMASTER×7, SWORDMAN×10, HORSEMAN_FAST×11, SIEGE_RAM×9, HORSEMAN_FAST×13 |
| 🟩 | Clumsy Attackers | random | Iron Age 90%, Medieval 10% | 🟠 3/13 (23%) | HANDGUNNER×9, HORSEMAN_FAST×1 | HORSEMAN_SLOW×12, HORSEMAN_FAST×13, PIKENEER×14, THE_SWORDMASTER×7, PIKENEER×8, LEGIONARY×13, HANDGUNNER×10, HORSEMAN_FAST×14, LEGIONARY×12 |
| 🟩 | Unlucky Raiders | random | Iron Age 89%, Bronze Age 11% | 🟢 13/13 (100%) |  | LEGIONARY×13, HORSEMAN_FAST×11, SWORDMAN×12, HORSEMAN_FAST×12, PIKENEER×9, PIKENEER×13, HORSEMAN_FAST×12, HORSEMAN_SLOW×9, PIKENEER×8, THE_SWORDMASTER×7 |
| 🟥 | Lazy Raiders | random | Iron Age 72%, Bronze Age 14%, Medieval 13% | ⬛ 0/13 (0%) | CRUSADER×7 | HORSEMAN_FAST×13, SWORDMAN×14, HORSEMAN_FAST×9, HORSEMAN_SLOW×8, THE_SWORDMASTER×7, LEGIONARY×8, CRUSADER×13, PIKENEER×10, PIKENEER×15 |
| 🟥 | Forgotten Warband | random | Iron Age 71%, Medieval 18%, Bronze Age 11% | ⬛ 0/13 (0%) | HANDGUNNER×13 | HORSEMAN_SLOW×8, HORSEMAN_FAST×11, LEGIONARY×15, LARGE_CART×8, HANDGUNNER×15, HORSEMAN_FAST×10, HORSEMAN_SLOW×8, BOWMAN×9 |
| 🟥 | Grumpy Marauders | random | Iron Age 82%, Medieval 18% | ⬛ 0/13 (0%) | HANDGUNNER×6, HORSEMAN_FAST×2, THE_SWORDMASTER×1 | LEGIONARY×9, PIKENEER×15, HORSEMAN_SLOW×11, HORSEMAN_FAST×10, HANDGUNNER×9, HORSEMAN_FAST×8, HORSEMAN_SLOW×11, THE_SWORDMASTER×7, CONDOTTERI×10, HORSEMAN_FAST×14 |
| 🟥 | Hungry Invaders | random | Iron Age 89%, Medieval 11% | ⬛ 0/13 (0%) | CRUSADER×5, SIEGE_RAM×1 | LARGE_CART×12, HORSEMAN_FAST×13, HORSEMAN_SLOW×12, SIEGE_RAM×12, LEGIONARY×10, LARGE_CART×8, LARGE_CART×12, LARGE_CART×12, PIKENEER×9, HORSEMAN_SLOW×10 |
| 🟩 | Clumsy Attackers | random | Iron Age 64%, Bronze Age 27%, Medieval 8% | 🟠 6/13 (46%) | SAMURAI×7 | HORSEMAN_SLOW×9, HORSEMAN_FAST×12, LEGIONARY×9, HORSEMAN_SLOW×14, LEGIONARY×11, CHARIOT×14, SAMURAI×9, LEGIONARY×13, BOWMAN×15 |
| 🟥 | Grumpy Marauders | random | Iron Age 78%, Medieval 13%, Bronze Age 10% | ⬛ 0/13 (0%) | CRUSADER×4, HORSEMAN_FAST×2, SIEGE_RAM×1 | LEGIONARY×12, SIEGE_RAM×12, HORSEMAN_FAST×12, HORSEMAN_FAST×12, LARGE_CART×16, HORSEMAN_SLOW×13, LARGE_CART×8, BOWMAN×9 |

#### S2 Baumhaus

| Tower Era Distribution (22 towers) | Towers |
|---|---|
| Bronze Age 64% (14), Iron Age 36% (8) | ARROW_TOWER×8, CATAPULTS×4, FIRE_TOWER×4, ARBELESTE_TOWER×4, BALLISTA_TOWER×2 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Iron Legion | hardcoded | Iron Age 100% | 🟢 16/16 (100%) |  | HORSEMAN_SLOW×10, HORSEMAN_SLOW×10, LEGIONARY×11, PIKENEER×12, HORSEMAN_SLOW×12, PIKENEER×13, LEGIONARY×15, HORSEMAN_FAST×16, THE_SWORDMASTER×18, LEGIONARY×20, LEGIONARY×22, PIKENEER×24 |
| 🟩 | Cavalry Strike | hardcoded | Iron Age 96%, Medieval 4% | 🟢 14/16 (88%) | KNIGHT×2 | LEGIONARY×14, PIKENEER×15, HORSEMAN_FAST×16, LARGE_CART×17, LEGIONARY×17, LEGIONARY×18, KNIGHT×9, PIKENEER×22, LARGE_CART×18, HORSEMAN_SLOW×20, HORSEMAN_SLOW×22, PIKENEER×24, LEGIONARY×26 |
| 🟩 | Legionary March | hardcoded | Iron Age 96%, Medieval 4% | 🟡 9/16 (56%) | THE_SWORDMASTER×1 | LEGIONARY×14, HORSEMAN_SLOW×15, PIKENEER×16, HORSEMAN_FAST×17, HORSEMAN_FAST×17, HORSEMAN_SLOW×18, CRUSADER×9, LARGE_CART×20, LEGIONARY×18, HORSEMAN_FAST×20, LEGIONARY×22, HORSEMAN_FAST×24, THE_SWORDMASTER×26 |
| 🟩 | Iron Tide | hardcoded | Iron Age 95%, Medieval 5% | 🟢 14/16 (88%) | CRUSADER×1 | LEGIONARY×14, HORSEMAN_FAST×15, LARGE_CART×16, HORSEMAN_SLOW×16, LARGE_CART×17, HORSEMAN_FAST×18, LEGIONARY×18, THE_SWORDMASTER×19, PIKENEER×20, THE_SWORDMASTER×20, LARGE_CART×22, CRUSADER×12, THE_SWORDMASTER×26, LEGIONARY×28 |
| 🟩 | Quartermaster Force | hardcoded | Iron Age 92%, Bronze Age 8% | 🟢 16/16 (100%) |  | THE_SWORDMASTER×16, LEGIONARY×17, HORSEMAN_SLOW×18, LARGE_CART×19, PIKENEER×20, LARGE_CART×21, LARGE_CART×22, LEGIONARY×16, PIKENEER×18, LARGE_CART×20, HORSEMAN_SLOW×22, HORSEMAN_SLOW×24, HORSEMAN_FAST×26, SWORDMAN×28, PIKENEER×28, LEGIONARY×28 |
| 🟩 | Desperate Looters | random | Iron Age 91%, Medieval 9% | 🟢 16/16 (100%) |  | KNIGHT×9, HORSEMAN_SLOW×13, HORSEMAN_FAST×8, LEGIONARY×13, HORSEMAN_SLOW×9, LARGE_CART×8, PIKENEER×11, HORSEMAN_FAST×11, HORSEMAN_FAST×15, THE_SWORDMASTER×7 |
| 🟩 | Desperate Looters | random | Iron Age 91%, Medieval 9% | 🟢 16/16 (100%) |  | KNIGHT×9, HORSEMAN_SLOW×13, HORSEMAN_FAST×8, LEGIONARY×13, HORSEMAN_SLOW×9, LARGE_CART×8, PIKENEER×11, HORSEMAN_FAST×11, HORSEMAN_FAST×15, THE_SWORDMASTER×7 |
| 🟩 | Restless Horde | random | Iron Age 92%, Bronze Age 8% | 🟢 16/16 (100%) |  | LARGE_CART×8, THE_SWORDMASTER×7, LEGIONARY×11, HORSEMAN_SLOW×11, PIKENEER×14, HORSEMAN_FAST×13, HORSEMAN_FAST×9, LEGIONARY×14, CHARIOT×8, LEGIONARY×11 |
| 🟥 | Drunken Raiders | random | Iron Age 87%, Medieval 13% | ⬛ 0/16 (0%) | CRUSADER×8 | PIKENEER×13, HORSEMAN_SLOW×13, THE_SWORDMASTER×7, HORSEMAN_FAST×11, LEGIONARY×9, SIEGE_RAM×15, PIKENEER×10, HORSEMAN_SLOW×13, PIKENEER×13, HORSEMAN_FAST×14 |
| 🟩 | Howling Savages | random | Iron Age 89%, Bronze Age 11% | 🟢 16/16 (100%) |  | LEGIONARY×9, LEGIONARY×14, HORSEMAN_FAST×13, LEGIONARY×15, LARGE_CART×12, PIKENEER×10, LEGIONARY×13, SWORDMAN×14, LEGIONARY×11, HORSEMAN_FAST×11, THE_SWORDMASTER×7 |
| 🟩 | Bored Mercenaries | random | Iron Age 70%, Bronze Age 30% | 🟢 16/16 (100%) |  | LARGE_CART×12, HORSEMAN_SLOW×14, CHARIOT×10, BOWMAN×13, LEGIONARY×13, PIKENEER×11, HORSEMAN_SLOW×13, LEGIONARY×9, BOWMAN×14, HORSEMAN_FAST×14 |
| 🟩 | Crude Invaders | random | Iron Age 85%, Medieval 15% | 🟠 6/16 (38%) | HANDGUNNER×10 | PIKENEER×8, HORSEMAN_SLOW×12, HANDGUNNER×15, LARGE_CART×8, PIKENEER×8, LARGE_CART×12, LEGIONARY×11, HORSEMAN_FAST×13, HORSEMAN_FAST×9, THE_SWORDMASTER×7 |
| 🟩 | Crude Invaders | random | Iron Age 77%, Medieval 23% | 🔴 3/16 (19%) | CRUSADER×6, SAMURAI×1 | SAMURAI×10, HORSEMAN_SLOW×12, LARGE_CART×8, PIKENEER×13, LARGE_CART×12, LEGIONARY×9, HORSEMAN_FAST×11, SIEGE_RAM×9 |
| 🟩 | Restless Horde | random | Iron Age 76%, Bronze Age 24% | 🟢 16/16 (100%) |  | HORSEMAN_FAST×14, HORSEMAN_SLOW×9, BOWMAN×9, PIKENEER×12, CHARIOT×13, HORSEMAN_SLOW×12, PIKENEER×12, LARGE_CART×12 |
| 🟩 | Restless Horde | random | Iron Age 57%, Bronze Age 43% | 🟢 16/16 (100%) |  | SWORDMAN×10, LARGE_CART×8, LARGE_CART×12, PIKENEER×12, THE_SWORDMASTER×7, BOWMAN×15, BOWMAN×13, LEGIONARY×12 |
| 🟩 | Angry Mob | random | Iron Age 42%, Bronze Age 37%, Medieval 21% | 🟡 12/16 (75%) | HANDGUNNER×2, SAMURAI×2 | HANDGUNNER×9, THE_SWORDMASTER×7, HORSEMAN_FAST×9, LARGE_CART×12, SAMURAI×13, SWORDMAN×14, BOWMAN×14, PIKENEER×8, LARGE_CART×8, SWORDMAN×10 |
| 🟩 | Lazy Raiders | random | Iron Age 72%, Bronze Age 19%, Medieval 9% | 🟠 6/16 (38%) | CRUSADER×5 | LEGIONARY×12, LEGIONARY×14, LEGIONARY×9, LEGIONARY×9, BOWMAN×10, THE_SWORDMASTER×7, SWORDMAN×10, HORSEMAN_FAST×11, SIEGE_RAM×9, HORSEMAN_FAST×13 |
| 🟩 | Clumsy Attackers | random | Iron Age 90%, Medieval 10% | 🟡 8/16 (50%) | HANDGUNNER×7, HORSEMAN_FAST×1 | HORSEMAN_SLOW×12, HORSEMAN_FAST×13, PIKENEER×14, THE_SWORDMASTER×7, PIKENEER×8, LEGIONARY×13, HANDGUNNER×10, HORSEMAN_FAST×14, LEGIONARY×12 |
| 🟩 | Unlucky Raiders | random | Iron Age 89%, Bronze Age 11% | 🟢 16/16 (100%) |  | LEGIONARY×13, HORSEMAN_FAST×11, SWORDMAN×12, HORSEMAN_FAST×12, PIKENEER×9, PIKENEER×13, HORSEMAN_FAST×12, HORSEMAN_SLOW×9, PIKENEER×8, THE_SWORDMASTER×7 |
| 🟩 | Lazy Raiders | random | Iron Age 72%, Bronze Age 14%, Medieval 13% | 🟡 10/16 (62%) | CRUSADER×3 | HORSEMAN_FAST×13, SWORDMAN×14, HORSEMAN_FAST×9, HORSEMAN_SLOW×8, THE_SWORDMASTER×7, LEGIONARY×8, CRUSADER×13, PIKENEER×10, PIKENEER×15 |
| 🟩 | Forgotten Warband | random | Iron Age 71%, Medieval 18%, Bronze Age 11% | 🔴 3/16 (19%) | HANDGUNNER×12, HORSEMAN_FAST×1 | HORSEMAN_SLOW×8, HORSEMAN_FAST×11, LEGIONARY×15, LARGE_CART×8, HANDGUNNER×15, HORSEMAN_FAST×10, HORSEMAN_SLOW×8, BOWMAN×9 |
| 🟩 | Grumpy Marauders | random | Iron Age 82%, Medieval 18% | 🟠 6/16 (38%) | HANDGUNNER×4, CONDOTTERI×3 | LEGIONARY×9, PIKENEER×15, HORSEMAN_SLOW×11, HORSEMAN_FAST×10, HANDGUNNER×9, HORSEMAN_FAST×8, HORSEMAN_SLOW×11, THE_SWORDMASTER×7, CONDOTTERI×10, HORSEMAN_FAST×14 |
| 🟥 | Hungry Invaders | random | Iron Age 89%, Medieval 11% | ⬛ 0/16 (0%) | CRUSADER×6, SIEGE_RAM×1 | LARGE_CART×12, HORSEMAN_FAST×13, HORSEMAN_SLOW×12, SIEGE_RAM×12, LEGIONARY×10, LARGE_CART×8, LARGE_CART×12, LARGE_CART×12, PIKENEER×9, HORSEMAN_SLOW×10 |
| 🟩 | Clumsy Attackers | random | Iron Age 64%, Bronze Age 27%, Medieval 8% | 🟡 9/16 (56%) | SAMURAI×7 | HORSEMAN_SLOW×9, HORSEMAN_FAST×12, LEGIONARY×9, HORSEMAN_SLOW×14, LEGIONARY×11, CHARIOT×14, SAMURAI×9, LEGIONARY×13, BOWMAN×15 |
| 🟥 | Grumpy Marauders | random | Iron Age 78%, Medieval 13%, Bronze Age 10% | ⬛ 0/16 (0%) | CRUSADER×6, SIEGE_RAM×1, HORSEMAN_FAST×1 | LEGIONARY×12, SIEGE_RAM×12, HORSEMAN_FAST×12, HORSEMAN_FAST×12, LARGE_CART×16, HORSEMAN_SLOW×13, LARGE_CART×8, BOWMAN×9 |

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
| 🟩 | Desperate Looters | random | Iron Age 91%, Medieval 9% | 🟢 16/16 (100%) |  | KNIGHT×9, HORSEMAN_SLOW×13, HORSEMAN_FAST×8, LEGIONARY×13, HORSEMAN_SLOW×9, LARGE_CART×8, PIKENEER×11, HORSEMAN_FAST×11, HORSEMAN_FAST×15, THE_SWORDMASTER×7 |
| 🟩 | Desperate Looters | random | Iron Age 91%, Medieval 9% | 🟢 16/16 (100%) |  | KNIGHT×9, HORSEMAN_SLOW×13, HORSEMAN_FAST×8, LEGIONARY×13, HORSEMAN_SLOW×9, LARGE_CART×8, PIKENEER×11, HORSEMAN_FAST×11, HORSEMAN_FAST×15, THE_SWORDMASTER×7 |
| 🟩 | Restless Horde | random | Iron Age 92%, Bronze Age 8% | 🟢 16/16 (100%) |  | LARGE_CART×8, THE_SWORDMASTER×7, LEGIONARY×11, HORSEMAN_SLOW×11, PIKENEER×14, HORSEMAN_FAST×13, HORSEMAN_FAST×9, LEGIONARY×14, CHARIOT×8, LEGIONARY×11 |
| 🟩 | Drunken Raiders | random | Iron Age 87%, Medieval 13% | 🟢 16/16 (100%) |  | PIKENEER×13, HORSEMAN_SLOW×13, THE_SWORDMASTER×7, HORSEMAN_FAST×11, LEGIONARY×9, SIEGE_RAM×15, PIKENEER×10, HORSEMAN_SLOW×13, PIKENEER×13, HORSEMAN_FAST×14 |
| 🟩 | Howling Savages | random | Iron Age 89%, Bronze Age 11% | 🟢 16/16 (100%) |  | LEGIONARY×9, LEGIONARY×14, HORSEMAN_FAST×13, LEGIONARY×15, LARGE_CART×12, PIKENEER×10, LEGIONARY×13, SWORDMAN×14, LEGIONARY×11, HORSEMAN_FAST×11, THE_SWORDMASTER×7 |
| 🟩 | Bored Mercenaries | random | Iron Age 70%, Bronze Age 30% | 🟢 16/16 (100%) |  | LARGE_CART×12, HORSEMAN_SLOW×14, CHARIOT×10, BOWMAN×13, LEGIONARY×13, PIKENEER×11, HORSEMAN_SLOW×13, LEGIONARY×9, BOWMAN×14, HORSEMAN_FAST×14 |
| 🟩 | Crude Invaders | random | Iron Age 85%, Medieval 15% | 🟢 16/16 (100%) |  | PIKENEER×8, HORSEMAN_SLOW×12, HANDGUNNER×15, LARGE_CART×8, PIKENEER×8, LARGE_CART×12, LEGIONARY×11, HORSEMAN_FAST×13, HORSEMAN_FAST×9, THE_SWORDMASTER×7 |
| 🟩 | Crude Invaders | random | Iron Age 77%, Medieval 23% | 🟢 16/16 (100%) |  | SAMURAI×10, HORSEMAN_SLOW×12, LARGE_CART×8, PIKENEER×13, LARGE_CART×12, LEGIONARY×9, HORSEMAN_FAST×11, SIEGE_RAM×9 |
| 🟩 | Restless Horde | random | Iron Age 76%, Bronze Age 24% | 🟢 16/16 (100%) |  | HORSEMAN_FAST×14, HORSEMAN_SLOW×9, BOWMAN×9, PIKENEER×12, CHARIOT×13, HORSEMAN_SLOW×12, PIKENEER×12, LARGE_CART×12 |
| 🟩 | Restless Horde | random | Iron Age 57%, Bronze Age 43% | 🟢 16/16 (100%) |  | SWORDMAN×10, LARGE_CART×8, LARGE_CART×12, PIKENEER×12, THE_SWORDMASTER×7, BOWMAN×15, BOWMAN×13, LEGIONARY×12 |
| 🟩 | Angry Mob | random | Iron Age 42%, Bronze Age 37%, Medieval 21% | 🟢 16/16 (100%) |  | HANDGUNNER×9, THE_SWORDMASTER×7, HORSEMAN_FAST×9, LARGE_CART×12, SAMURAI×13, SWORDMAN×14, BOWMAN×14, PIKENEER×8, LARGE_CART×8, SWORDMAN×10 |
| 🟩 | Lazy Raiders | random | Iron Age 72%, Bronze Age 19%, Medieval 9% | 🟢 16/16 (100%) |  | LEGIONARY×12, LEGIONARY×14, LEGIONARY×9, LEGIONARY×9, BOWMAN×10, THE_SWORDMASTER×7, SWORDMAN×10, HORSEMAN_FAST×11, SIEGE_RAM×9, HORSEMAN_FAST×13 |
| 🟩 | Clumsy Attackers | random | Iron Age 90%, Medieval 10% | 🟢 16/16 (100%) |  | HORSEMAN_SLOW×12, HORSEMAN_FAST×13, PIKENEER×14, THE_SWORDMASTER×7, PIKENEER×8, LEGIONARY×13, HANDGUNNER×10, HORSEMAN_FAST×14, LEGIONARY×12 |
| 🟩 | Unlucky Raiders | random | Iron Age 89%, Bronze Age 11% | 🟢 16/16 (100%) |  | LEGIONARY×13, HORSEMAN_FAST×11, SWORDMAN×12, HORSEMAN_FAST×12, PIKENEER×9, PIKENEER×13, HORSEMAN_FAST×12, HORSEMAN_SLOW×9, PIKENEER×8, THE_SWORDMASTER×7 |
| 🟩 | Lazy Raiders | random | Iron Age 72%, Bronze Age 14%, Medieval 13% | 🟢 16/16 (100%) |  | HORSEMAN_FAST×13, SWORDMAN×14, HORSEMAN_FAST×9, HORSEMAN_SLOW×8, THE_SWORDMASTER×7, LEGIONARY×8, CRUSADER×13, PIKENEER×10, PIKENEER×15 |
| 🟩 | Forgotten Warband | random | Iron Age 71%, Medieval 18%, Bronze Age 11% | 🟢 16/16 (100%) |  | HORSEMAN_SLOW×8, HORSEMAN_FAST×11, LEGIONARY×15, LARGE_CART×8, HANDGUNNER×15, HORSEMAN_FAST×10, HORSEMAN_SLOW×8, BOWMAN×9 |
| 🟩 | Grumpy Marauders | random | Iron Age 82%, Medieval 18% | 🟢 16/16 (100%) |  | LEGIONARY×9, PIKENEER×15, HORSEMAN_SLOW×11, HORSEMAN_FAST×10, HANDGUNNER×9, HORSEMAN_FAST×8, HORSEMAN_SLOW×11, THE_SWORDMASTER×7, CONDOTTERI×10, HORSEMAN_FAST×14 |
| 🟩 | Hungry Invaders | random | Iron Age 89%, Medieval 11% | 🟢 16/16 (100%) |  | LARGE_CART×12, HORSEMAN_FAST×13, HORSEMAN_SLOW×12, SIEGE_RAM×12, LEGIONARY×10, LARGE_CART×8, LARGE_CART×12, LARGE_CART×12, PIKENEER×9, HORSEMAN_SLOW×10 |
| 🟩 | Clumsy Attackers | random | Iron Age 64%, Bronze Age 27%, Medieval 8% | 🟢 16/16 (100%) |  | HORSEMAN_SLOW×9, HORSEMAN_FAST×12, LEGIONARY×9, HORSEMAN_SLOW×14, LEGIONARY×11, CHARIOT×14, SAMURAI×9, LEGIONARY×13, BOWMAN×15 |
| 🟩 | Grumpy Marauders | random | Iron Age 78%, Medieval 13%, Bronze Age 10% | 🟢 16/16 (100%) |  | LEGIONARY×12, SIEGE_RAM×12, HORSEMAN_FAST×12, HORSEMAN_FAST×12, LARGE_CART×16, HORSEMAN_SLOW×13, LARGE_CART×8, BOWMAN×9 |

### Medieval

#### Early

| Tower Era Distribution (18 towers) | Towers |
|---|---|
| Medieval 61% (11), Bronze Age 22% (4), Iron Age 17% (3) | HEAVY_TOWER×5, TAR_TOWER×3, BOILING_OIL×3, FIRE_TOWER×2, BALLISTA_TOWER×2, ARBELESTE_TOWER×2, CATAPULTS×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟥 | Medieval Siege | hardcoded | Medieval 96%, Renaissance 4% | ⬛ 0/13 (0%) | NINJA×4, CRUSADER×3 | CRUSADER×12, CONDOTTERI×13, KNIGHT×14, SAMURAI×15, SIEGE_RAM×15, KNIGHT×16, CONDOTTERI×17, CRUSADER×18, NINJA×11, SIEGE_RAM×20, HANDGUNNER×22, HANDGUNNER×24, HANDGUNNER×26, SAMURAI×28 |
| 🟥 | Knights' Charge | hardcoded | Medieval 91%, Renaissance 9% | ⬛ 0/13 (0%) | CRUSADER×4, SIEGE_RAM×1, SAMURAI×1 | CRUSADER×16, SIEGE_RAM×17, CRUSADER×18, SIEGE_RAM×19, SAMURAI×20, KNIGHT×21, SAMURAI×22, CRUSADER×16, SAMURAI×18, KNIGHT×20, KNIGHT×22, CRUSADER×24, KNIGHT×26, KNIGHT×28, NINJA×30 |
| 🟥 | Crusader Host | hardcoded | Medieval 82%, Iron Age 18% | ⬛ 0/13 (0%) | CRUSADER×4, SIEGE_RAM×1, SAMURAI×1 | CRUSADER×16, SIEGE_RAM×17, SAMURAI×18, SIEGE_RAM×19, SIEGE_RAM×20, SAMURAI×21, CRUSADER×22, KNIGHT×16, KNIGHT×18, CRUSADER×20, CRUSADER×22, HANDGUNNER×24, CONDOTTERI×26, SAMURAI×28, THE_SWORDMASTER×30, LARGE_CART×31 |
| 🟥 | Castle Assault | hardcoded | Medieval 84%, Iron Age 16% | ⬛ 0/13 (0%) | SAMURAI×9, CRUSADER×2 | SAMURAI×16, KNIGHT×17, KNIGHT×18, KNIGHT×19, CRUSADER×20, CRUSADER×21, SIEGE_RAM×22, SAMURAI×16, CRUSADER×18, CRUSADER×20, CRUSADER×22, SAMURAI×24, SIEGE_RAM×26, LEGIONARY×28, CRUSADER×30, SAMURAI×32, HORSEMAN_FAST×32 |
| 🟥 | Feudal Army | hardcoded | Medieval 92%, Iron Age 8% | ⬛ 0/13 (0%) | CRUSADER×7 | KNIGHT×16, SIEGE_RAM×17, KNIGHT×18, SIEGE_RAM×19, CRUSADER×20, CRUSADER×21, CONDOTTERI×22, HANDGUNNER×16, CRUSADER×18, SIEGE_RAM×20, SIEGE_RAM×22, CRUSADER×24, KNIGHT×26, CONDOTTERI×28, KNIGHT×30, LARGE_CART×32, CRUSADER×31 |
| 🟥 | Holy Crusade | hardcoded | Medieval 73%, Iron Age 24%, Renaissance 3% | ⬛ 0/13 (0%) | HANDGUNNER×8, CONDOTTERI×3 | SAMURAI×16, CONDOTTERI×17, HANDGUNNER×17, KNIGHT×18, THE_SWORDMASTER×19, CONDOTTERI×19, CONDOTTERI×20, HANDGUNNER×21, KNIGHT×21, LARGE_CART×22, LEGIONARY×23, MUSKETEER×12, THE_SWORDMASTER×24, SIEGE_RAM×28, SIEGE_RAM×30, HANDGUNNER×31, CRUSADER×34 |
| 🟩 | Grumpy Marauders | random | Medieval 92%, Renaissance 8% | 🔴 2/13 (15%) | HANDGUNNER×9, DRAGOONER×1 | CONDOTTERI×13, SAMURAI×15, HANDGUNNER×18, SAMURAI×12, HANDGUNNER×14, DRAGOONER×13, KNIGHT×12, KNIGHT×15, CRUSADER×14, SAMURAI×13, CRUSADER×14, CONDOTTERI×14 |
| 🟩 | Grumpy Marauders | random | Medieval 92%, Renaissance 8% | 🔴 2/13 (15%) | HANDGUNNER×9, DRAGOONER×1 | CONDOTTERI×13, SAMURAI×15, HANDGUNNER×18, SAMURAI×12, HANDGUNNER×14, DRAGOONER×13, KNIGHT×12, KNIGHT×15, CRUSADER×14, SAMURAI×13, CRUSADER×14, CONDOTTERI×14 |
| 🟥 | Howling Savages | random | Medieval 96%, Iron Age 4% | ⬛ 0/13 (0%) | CRUSADER×6, SAMURAI×1 | KNIGHT×15, SIEGE_RAM×15, SAMURAI×18, THE_SWORDMASTER×7, KNIGHT×12, SIEGE_RAM×18, CRUSADER×17, CRUSADER×17, SAMURAI×16, CRUSADER×12, CRUSADER×16, HANDGUNNER×15 |
| 🟥 | Shrieking Horde | random | Medieval 90%, Renaissance 10% | ⬛ 0/13 (0%) | NINJA×7 | CRUSADER×17, SIEGE_RAM×12, NINJA×18, CONDOTTERI×15, HANDGUNNER×13, CRUSADER×16, SAMURAI×17, CRUSADER×13, SAMURAI×14, CONDOTTERI×13, CRUSADER×16, CONDOTTERI×15 |
| 🟥 | Crude Invaders | random | Medieval 93%, Iron Age 7% | ⬛ 0/13 (0%) | SAMURAI×5, HANDGUNNER×4, CONDOTTERI×2 | SAMURAI×16, CONDOTTERI×16, CONDOTTERI×13, HANDGUNNER×18, SAMURAI×13, SIEGE_RAM×12, HANDGUNNER×15, CONDOTTERI×14, HORSEMAN_FAST×14, SAMURAI×16, CONDOTTERI×15, HANDGUNNER×15, CRUSADER×13 |
| 🟥 | Reckless Looters | random | Medieval 75%, Iron Age 25% | ⬛ 0/13 (0%) | CRUSADER×4, CONDOTTERI×3 | KNIGHT×18, KNIGHT×15, PIKENEER×17, CONDOTTERI×16, SIEGE_RAM×15, CRUSADER×14, CONDOTTERI×13, HORSEMAN_SLOW×13, KNIGHT×15, SIEGE_RAM×12, SAMURAI×17, PIKENEER×14 |
| 🟥 | Howling Savages | random | Medieval 89%, Renaissance 11% | ⬛ 0/13 (0%) | HANDGUNNER×5, KNIGHT×3, CRUSADER×2, SAMURAI×1 | CRUSADER×14, SAMURAI×11, KNIGHT×18, KNIGHT×15, HANDGUNNER×18, CRUSADER×11, HANDGUNNER×13, SAMURAI×14, KNIGHT×18, CONDOTTERI×15, CARGO×18 |
| 🟥 | Unlucky Raiders | random | Medieval 80%, Renaissance 20% | ⬛ 0/13 (0%) | CRUSADER×5, SIEGE_RAM×1 | CRUSADER×16, SIEGE_RAM×12, CONDOTTERI×13, KNIGHT×15, SAMURAI×13, CONDOTTERI×15, CARGO×12, SAMURAI×14, MUSKETEER×13 |
| 🟩 | Frenzied Pillagers | random | Medieval 80%, Iron Age 20% | 🟢 11/13 (85%) | HANDGUNNER×2 | CRUSADER×15, PIKENEER×12, PIKENEER×15, SAMURAI×17, KNIGHT×15, CONDOTTERI×15, KNIGHT×12, HANDGUNNER×16, CRUSADER×15 |
| 🟥 | Hungry Invaders | random | Medieval 68%, Iron Age 32% | ⬛ 0/13 (0%) | HANDGUNNER×7, CONDOTTERI×3 | HANDGUNNER×12, SIEGE_RAM×12, CONDOTTERI×16, HANDGUNNER×13, THE_SWORDMASTER×7, CONDOTTERI×13, LARGE_CART×16, SIEGE_RAM×15, HORSEMAN_FAST×15 |
| 🟥 | Angry Mob | random | Medieval 55%, Iron Age 24%, Renaissance 21% | ⬛ 0/13 (0%) | MUSKETEER×11, CRUSADER×1 | SAMURAI×12, CRUSADER×11, SAMURAI×14, HORSEMAN_SLOW×17, THE_SWORDMASTER×7, LARGE_CART×12, CONDOTTERI×14, CRUSADER×14, MUSKETEER×16, DRAGOONER×15, HANDGUNNER×17 |
| 🟥 | Grumpy Marauders | random | Medieval 72%, Iron Age 19%, Renaissance 9% | ⬛ 0/13 (0%) | MUSKETEER×10, CONDOTTERI×1, SAMURAI×1 | CONDOTTERI×16, MUSKETEER×14, SAMURAI×14, KNIGHT×15, SIEGE_RAM×18, SIEGE_RAM×12, HANDGUNNER×14, SIEGE_RAM×15, CRUSADER×12, HORSEMAN_FAST×15, PIKENEER×15 |
| 🟥 | Muddy Marauders | random | Medieval 89%, Renaissance 11% | ⬛ 0/13 (0%) | MUSKETEER×5, CRUSADER×4 | CONDOTTERI×11, SIEGE_RAM×15, SIEGE_RAM×15, CARGO×15, CONDOTTERI×18, HANDGUNNER×12, KNIGHT×12, CRUSADER×16, SIEGE_RAM×15, HANDGUNNER×13 |
| 🟥 | Restless Horde | random | Medieval 89%, Iron Age 11% | ⬛ 0/13 (0%) | CRUSADER×5, HANDGUNNER×3 | HANDGUNNER×16, SAMURAI×15, SIEGE_RAM×15, CRUSADER×15, PIKENEER×16, CRUSADER×12, SIEGE_RAM×12, SIEGE_RAM×12, SAMURAI×15, CRUSADER×11, CONDOTTERI×13 |
| 🟥 | Noisy Barbarians | random | Medieval 82%, Renaissance 10%, Iron Age 8% | ⬛ 0/13 (0%) | SAMURAI×7, CRUSADER×2, HANDGUNNER×2 | CRUSADER×12, HANDGUNNER×14, SAMURAI×14, LARGE_CART×12, HANDGUNNER×11, SIEGE_RAM×12, CRUSADER×16, SAMURAI×12, SAMURAI×16, CRUSADER×18, CARGO×15 |
| 🟥 | Savage Rabble | random | Medieval 86%, Renaissance 8%, Iron Age 5% | ⬛ 0/13 (0%) | MUSKETEER×5, HANDGUNNER×4, CRUSADER×2, SAMURAI×1 | CONDOTTERI×13, HANDGUNNER×18, KNIGHT×12, KNIGHT×12, THE_SWORDMASTER×7, MUSKETEER×11, SIEGE_RAM×18, SAMURAI×14, SAMURAI×13, KNIGHT×12 |
| 🟥 | Blundering Invaders | random | Medieval 82%, Renaissance 18% | ⬛ 0/13 (0%) | MUSKETEER×10, CRUSADER×2 | MUSKETEER×17, SIEGE_RAM×12, CRUSADER×13, CRUSADER×16, SAMURAI×15, HANDGUNNER×14, HANDGUNNER×13, DRAGOONER×15, SAMURAI×17, SAMURAI×13, CRUSADER×18, KNIGHT×15 |
| 🟥 | Wandering Pillagers | random | Medieval 94%, Renaissance 6% | ⬛ 0/13 (0%) | CRUSADER×1, THE_KING×1, SAMURAI×1 | CONDOTTERI×15, THE_KING×10, SIEGE_RAM×12, CONDOTTERI×13, SAMURAI×16, CONDOTTERI×13, CRUSADER×12, SIEGE_RAM×15, KNIGHT×15, KNIGHT×12, CONDOTTERI×17, SAMURAI×11 |
| 🟥 | Noisy Barbarians | random | Medieval 72%, Iron Age 19%, Renaissance 9% | ⬛ 0/13 (0%) | CRUSADER×5, DRAGOONER×2 | SIEGE_RAM×15, KNIGHT×12, KNIGHT×18, SAMURAI×15, LARGE_CART×16, CRUSADER×18, DRAGOONER×13, SIEGE_RAM×12, SIEGE_RAM×15, HORSEMAN_FAST×12 |
| 🟥 | Noisy Barbarians | random | Medieval 77%, Iron Age 12%, Renaissance 11% | ⬛ 0/13 (0%) | CRUSADER×7 | SAMURAI×15, SAMURAI×15, SIEGE_RAM×15, CRUSADER×12, CARGO×15, CONDOTTERI×12, LEGIONARY×16, CONDOTTERI×18, KNIGHT×15 |

#### Mixed Early

| Tower Era Distribution (27 towers) | Towers |
|---|---|
| Medieval 48% (13), Iron Age 22% (6), Bronze Age 22% (6), Neolithic 7% (2) | TAR_TOWER×7, HEAVY_TOWER×6, CATAPULTS×4, BALLISTA_TOWER×3, DOUBLE_SLING_TOWER×2, ARBELESTE_TOWER×2, ARROW_TOWER×2, FIRE_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟥 | Medieval Siege | hardcoded | Medieval 96%, Renaissance 4% | ⬛ 0/16 (0%) | SAMURAI×6, CRUSADER×3, KNIGHT×3, CONDOTTERI×1 | CRUSADER×12, CONDOTTERI×13, KNIGHT×14, SAMURAI×15, SIEGE_RAM×15, KNIGHT×16, CONDOTTERI×17, CRUSADER×18, NINJA×11, SIEGE_RAM×20, HANDGUNNER×22, HANDGUNNER×24, HANDGUNNER×26, SAMURAI×28 |
| 🟥 | Knights' Charge | hardcoded | Medieval 91%, Renaissance 9% | ⬛ 0/16 (0%) | CRUSADER×6, SIEGE_RAM×1 | CRUSADER×16, SIEGE_RAM×17, CRUSADER×18, SIEGE_RAM×19, SAMURAI×20, KNIGHT×21, SAMURAI×22, CRUSADER×16, SAMURAI×18, KNIGHT×20, KNIGHT×22, CRUSADER×24, KNIGHT×26, KNIGHT×28, NINJA×30 |
| 🟥 | Crusader Host | hardcoded | Medieval 82%, Iron Age 18% | ⬛ 0/16 (0%) | SAMURAI×8, CRUSADER×4 | CRUSADER×16, SIEGE_RAM×17, SAMURAI×18, SIEGE_RAM×19, SIEGE_RAM×20, SAMURAI×21, CRUSADER×22, KNIGHT×16, KNIGHT×18, CRUSADER×20, CRUSADER×22, HANDGUNNER×24, CONDOTTERI×26, SAMURAI×28, THE_SWORDMASTER×30, LARGE_CART×31 |
| 🟥 | Castle Assault | hardcoded | Medieval 84%, Iron Age 16% | ⬛ 0/16 (0%) | KNIGHT×7, CRUSADER×5 | SAMURAI×16, KNIGHT×17, KNIGHT×18, KNIGHT×19, CRUSADER×20, CRUSADER×21, SIEGE_RAM×22, SAMURAI×16, CRUSADER×18, CRUSADER×20, CRUSADER×22, SAMURAI×24, SIEGE_RAM×26, LEGIONARY×28, CRUSADER×30, SAMURAI×32, HORSEMAN_FAST×32 |
| 🟥 | Feudal Army | hardcoded | Medieval 92%, Iron Age 8% | ⬛ 0/16 (0%) | CRUSADER×5, KNIGHT×3, SIEGE_RAM×1 | KNIGHT×16, SIEGE_RAM×17, KNIGHT×18, SIEGE_RAM×19, CRUSADER×20, CRUSADER×21, CONDOTTERI×22, HANDGUNNER×16, CRUSADER×18, SIEGE_RAM×20, SIEGE_RAM×22, CRUSADER×24, KNIGHT×26, CONDOTTERI×28, KNIGHT×30, LARGE_CART×32, CRUSADER×31 |
| 🟥 | Holy Crusade | hardcoded | Medieval 73%, Iron Age 24%, Renaissance 3% | ⬛ 0/16 (0%) | HANDGUNNER×6, CONDOTTERI×5 | SAMURAI×16, CONDOTTERI×17, HANDGUNNER×17, KNIGHT×18, THE_SWORDMASTER×19, CONDOTTERI×19, CONDOTTERI×20, HANDGUNNER×21, KNIGHT×21, LARGE_CART×22, LEGIONARY×23, MUSKETEER×12, THE_SWORDMASTER×24, SIEGE_RAM×28, SIEGE_RAM×30, HANDGUNNER×31, CRUSADER×34 |
| 🟥 | Grumpy Marauders | random | Medieval 92%, Renaissance 8% | ⬛ 0/16 (0%) | SAMURAI×10, HANDGUNNER×4, CONDOTTERI×1 | CONDOTTERI×13, SAMURAI×15, HANDGUNNER×18, SAMURAI×12, HANDGUNNER×14, DRAGOONER×13, KNIGHT×12, KNIGHT×15, CRUSADER×14, SAMURAI×13, CRUSADER×14, CONDOTTERI×14 |
| 🟥 | Grumpy Marauders | random | Medieval 92%, Renaissance 8% | ⬛ 0/16 (0%) | SAMURAI×10, HANDGUNNER×4, CONDOTTERI×1 | CONDOTTERI×13, SAMURAI×15, HANDGUNNER×18, SAMURAI×12, HANDGUNNER×14, DRAGOONER×13, KNIGHT×12, KNIGHT×15, CRUSADER×14, SAMURAI×13, CRUSADER×14, CONDOTTERI×14 |
| 🟥 | Howling Savages | random | Medieval 96%, Iron Age 4% | ⬛ 0/16 (0%) | SAMURAI×7, CRUSADER×2, SIEGE_RAM×1, KNIGHT×1 | KNIGHT×15, SIEGE_RAM×15, SAMURAI×18, THE_SWORDMASTER×7, KNIGHT×12, SIEGE_RAM×18, CRUSADER×17, CRUSADER×17, SAMURAI×16, CRUSADER×12, CRUSADER×16, HANDGUNNER×15 |
| 🟥 | Shrieking Horde | random | Medieval 90%, Renaissance 10% | ⬛ 0/16 (0%) | NINJA×8 | CRUSADER×17, SIEGE_RAM×12, NINJA×18, CONDOTTERI×15, HANDGUNNER×13, CRUSADER×16, SAMURAI×17, CRUSADER×13, SAMURAI×14, CONDOTTERI×13, CRUSADER×16, CONDOTTERI×15 |
| 🟥 | Crude Invaders | random | Medieval 93%, Iron Age 7% | ⬛ 0/16 (0%) | CONDOTTERI×5, HANDGUNNER×5, SAMURAI×1 | SAMURAI×16, CONDOTTERI×16, CONDOTTERI×13, HANDGUNNER×18, SAMURAI×13, SIEGE_RAM×12, HANDGUNNER×15, CONDOTTERI×14, HORSEMAN_FAST×14, SAMURAI×16, CONDOTTERI×15, HANDGUNNER×15, CRUSADER×13 |
| 🟥 | Reckless Looters | random | Medieval 75%, Iron Age 25% | ⬛ 0/16 (0%) | KNIGHT×4, CRUSADER×4, SIEGE_RAM×1 | KNIGHT×18, KNIGHT×15, PIKENEER×17, CONDOTTERI×16, SIEGE_RAM×15, CRUSADER×14, CONDOTTERI×13, HORSEMAN_SLOW×13, KNIGHT×15, SIEGE_RAM×12, SAMURAI×17, PIKENEER×14 |
| 🟥 | Howling Savages | random | Medieval 89%, Renaissance 11% | ⬛ 0/16 (0%) | HANDGUNNER×10, SAMURAI×3, KNIGHT×3 | CRUSADER×14, SAMURAI×11, KNIGHT×18, KNIGHT×15, HANDGUNNER×18, CRUSADER×11, HANDGUNNER×13, SAMURAI×14, KNIGHT×18, CONDOTTERI×15, CARGO×18 |
| 🟥 | Unlucky Raiders | random | Medieval 80%, Renaissance 20% | ⬛ 0/16 (0%) | CRUSADER×7, SIEGE_RAM×1 | CRUSADER×16, SIEGE_RAM×12, CONDOTTERI×13, KNIGHT×15, SAMURAI×13, CONDOTTERI×15, CARGO×12, SAMURAI×14, MUSKETEER×13 |
| 🟥 | Frenzied Pillagers | random | Medieval 80%, Iron Age 20% | ⬛ 0/16 (0%) | CONDOTTERI×7, SAMURAI×2, KNIGHT×1 | CRUSADER×15, PIKENEER×12, PIKENEER×15, SAMURAI×17, KNIGHT×15, CONDOTTERI×15, KNIGHT×12, HANDGUNNER×16, CRUSADER×15 |
| 🟥 | Hungry Invaders | random | Medieval 68%, Iron Age 32% | ⬛ 0/16 (0%) | CRUSADER×4, CONDOTTERI×3, HANDGUNNER×2 | HANDGUNNER×12, SIEGE_RAM×12, CONDOTTERI×16, HANDGUNNER×13, THE_SWORDMASTER×7, CONDOTTERI×13, LARGE_CART×16, SIEGE_RAM×15, HORSEMAN_FAST×15 |
| 🟥 | Angry Mob | random | Medieval 55%, Iron Age 24%, Renaissance 21% | ⬛ 0/16 (0%) | MUSKETEER×7, SAMURAI×3, CRUSADER×3 | SAMURAI×12, CRUSADER×11, SAMURAI×14, HORSEMAN_SLOW×17, THE_SWORDMASTER×7, LARGE_CART×12, CONDOTTERI×14, CRUSADER×14, MUSKETEER×16, DRAGOONER×15, HANDGUNNER×17 |
| 🟥 | Grumpy Marauders | random | Medieval 72%, Iron Age 19%, Renaissance 9% | ⬛ 0/16 (0%) | MUSKETEER×10, CONDOTTERI×3 | CONDOTTERI×16, MUSKETEER×14, SAMURAI×14, KNIGHT×15, SIEGE_RAM×18, SIEGE_RAM×12, HANDGUNNER×14, SIEGE_RAM×15, CRUSADER×12, HORSEMAN_FAST×15, PIKENEER×15 |
| 🟥 | Muddy Marauders | random | Medieval 89%, Renaissance 11% | ⬛ 0/16 (0%) | CRUSADER×8 | CONDOTTERI×11, SIEGE_RAM×15, SIEGE_RAM×15, CARGO×15, CONDOTTERI×18, HANDGUNNER×12, KNIGHT×12, CRUSADER×16, SIEGE_RAM×15, HANDGUNNER×13 |
| 🟥 | Restless Horde | random | Medieval 89%, Iron Age 11% | ⬛ 0/16 (0%) | HANDGUNNER×6, SAMURAI×5, CRUSADER×3 | HANDGUNNER×16, SAMURAI×15, SIEGE_RAM×15, CRUSADER×15, PIKENEER×16, CRUSADER×12, SIEGE_RAM×12, SIEGE_RAM×12, SAMURAI×15, CRUSADER×11, CONDOTTERI×13 |
| 🟥 | Noisy Barbarians | random | Medieval 82%, Renaissance 10%, Iron Age 8% | ⬛ 0/16 (0%) | HANDGUNNER×8, SAMURAI×3, CRUSADER×1, SIEGE_RAM×1 | CRUSADER×12, HANDGUNNER×14, SAMURAI×14, LARGE_CART×12, HANDGUNNER×11, SIEGE_RAM×12, CRUSADER×16, SAMURAI×12, SAMURAI×16, CRUSADER×18, CARGO×15 |
| 🟥 | Savage Rabble | random | Medieval 86%, Renaissance 8%, Iron Age 5% | ⬛ 0/16 (0%) | HANDGUNNER×13, CONDOTTERI×1, KNIGHT×1 | CONDOTTERI×13, HANDGUNNER×18, KNIGHT×12, KNIGHT×12, THE_SWORDMASTER×7, MUSKETEER×11, SIEGE_RAM×18, SAMURAI×14, SAMURAI×13, KNIGHT×12 |
| 🟥 | Blundering Invaders | random | Medieval 82%, Renaissance 18% | ⬛ 0/16 (0%) | MUSKETEER×10, CRUSADER×3 | MUSKETEER×17, SIEGE_RAM×12, CRUSADER×13, CRUSADER×16, SAMURAI×15, HANDGUNNER×14, HANDGUNNER×13, DRAGOONER×15, SAMURAI×17, SAMURAI×13, CRUSADER×18, KNIGHT×15 |
| 🟥 | Wandering Pillagers | random | Medieval 94%, Renaissance 6% | ⬛ 0/16 (0%) | CRUSADER×3, THE_KING×1 | CONDOTTERI×15, THE_KING×10, SIEGE_RAM×12, CONDOTTERI×13, SAMURAI×16, CONDOTTERI×13, CRUSADER×12, SIEGE_RAM×15, KNIGHT×15, KNIGHT×12, CONDOTTERI×17, SAMURAI×11 |
| 🟥 | Noisy Barbarians | random | Medieval 72%, Iron Age 19%, Renaissance 9% | ⬛ 0/16 (0%) | CRUSADER×7, SAMURAI×2 | SIEGE_RAM×15, KNIGHT×12, KNIGHT×18, SAMURAI×15, LARGE_CART×16, CRUSADER×18, DRAGOONER×13, SIEGE_RAM×12, SIEGE_RAM×15, HORSEMAN_FAST×12 |
| 🟥 | Noisy Barbarians | random | Medieval 77%, Iron Age 12%, Renaissance 11% | ⬛ 0/16 (0%) | CRUSADER×8, SAMURAI×1 | SAMURAI×15, SAMURAI×15, SIEGE_RAM×15, CRUSADER×12, CARGO×15, CONDOTTERI×12, LEGIONARY×16, CONDOTTERI×18, KNIGHT×15 |

#### Full Heavy

| Tower Era Distribution (32 towers) | Towers |
|---|---|
| Medieval 100% (32) | HEAVY_TOWER×29, BOILING_OIL×2, TAR_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Medieval Siege | hardcoded | Medieval 96%, Renaissance 4% | 🟢 23/23 (100%) |  | CRUSADER×12, CONDOTTERI×13, KNIGHT×14, SAMURAI×15, SIEGE_RAM×15, KNIGHT×16, CONDOTTERI×17, CRUSADER×18, NINJA×11, SIEGE_RAM×20, HANDGUNNER×22, HANDGUNNER×24, HANDGUNNER×26, SAMURAI×28 |
| 🟩 | Knights' Charge | hardcoded | Medieval 91%, Renaissance 9% | 🟢 19/23 (83%) | CRUSADER×2 | CRUSADER×16, SIEGE_RAM×17, CRUSADER×18, SIEGE_RAM×19, SAMURAI×20, KNIGHT×21, SAMURAI×22, CRUSADER×16, SAMURAI×18, KNIGHT×20, KNIGHT×22, CRUSADER×24, KNIGHT×26, KNIGHT×28, NINJA×30 |
| 🟩 | Crusader Host | hardcoded | Medieval 82%, Iron Age 18% | 🟡 18/23 (78%) | CRUSADER×2, HANDGUNNER×1 | CRUSADER×16, SIEGE_RAM×17, SAMURAI×18, SIEGE_RAM×19, SIEGE_RAM×20, SAMURAI×21, CRUSADER×22, KNIGHT×16, KNIGHT×18, CRUSADER×20, CRUSADER×22, HANDGUNNER×24, CONDOTTERI×26, SAMURAI×28, THE_SWORDMASTER×30, LARGE_CART×31 |
| 🟩 | Castle Assault | hardcoded | Medieval 84%, Iron Age 16% | 🟠 8/23 (35%) | CRUSADER×6, SAMURAI×2, HORSEMAN_FAST×1 | SAMURAI×16, KNIGHT×17, KNIGHT×18, KNIGHT×19, CRUSADER×20, CRUSADER×21, SIEGE_RAM×22, SAMURAI×16, CRUSADER×18, CRUSADER×20, CRUSADER×22, SAMURAI×24, SIEGE_RAM×26, LEGIONARY×28, CRUSADER×30, SAMURAI×32, HORSEMAN_FAST×32 |
| 🟩 | Feudal Army | hardcoded | Medieval 92%, Iron Age 8% | 🟡 12/23 (52%) | CONDOTTERI×3, CRUSADER×2, HANDGUNNER×1 | KNIGHT×16, SIEGE_RAM×17, KNIGHT×18, SIEGE_RAM×19, CRUSADER×20, CRUSADER×21, CONDOTTERI×22, HANDGUNNER×16, CRUSADER×18, SIEGE_RAM×20, SIEGE_RAM×22, CRUSADER×24, KNIGHT×26, CONDOTTERI×28, KNIGHT×30, LARGE_CART×32, CRUSADER×31 |
| 🟥 | Holy Crusade | hardcoded | Medieval 73%, Iron Age 24%, Renaissance 3% | ⬛ 0/23 (0%) | CRUSADER×7, CONDOTTERI×2, MUSKETEER×1, SIEGE_RAM×1 | SAMURAI×16, CONDOTTERI×17, HANDGUNNER×17, KNIGHT×18, THE_SWORDMASTER×19, CONDOTTERI×19, CONDOTTERI×20, HANDGUNNER×21, KNIGHT×21, LARGE_CART×22, LEGIONARY×23, MUSKETEER×12, THE_SWORDMASTER×24, SIEGE_RAM×28, SIEGE_RAM×30, HANDGUNNER×31, CRUSADER×34 |
| 🟩 | Grumpy Marauders | random | Medieval 92%, Renaissance 8% | 🟢 23/23 (100%) |  | CONDOTTERI×13, SAMURAI×15, HANDGUNNER×18, SAMURAI×12, HANDGUNNER×14, DRAGOONER×13, KNIGHT×12, KNIGHT×15, CRUSADER×14, SAMURAI×13, CRUSADER×14, CONDOTTERI×14 |
| 🟩 | Grumpy Marauders | random | Medieval 92%, Renaissance 8% | 🟢 23/23 (100%) |  | CONDOTTERI×13, SAMURAI×15, HANDGUNNER×18, SAMURAI×12, HANDGUNNER×14, DRAGOONER×13, KNIGHT×12, KNIGHT×15, CRUSADER×14, SAMURAI×13, CRUSADER×14, CONDOTTERI×14 |
| 🟩 | Howling Savages | random | Medieval 96%, Iron Age 4% | 🟢 23/23 (100%) |  | KNIGHT×15, SIEGE_RAM×15, SAMURAI×18, THE_SWORDMASTER×7, KNIGHT×12, SIEGE_RAM×18, CRUSADER×17, CRUSADER×17, SAMURAI×16, CRUSADER×12, CRUSADER×16, HANDGUNNER×15 |
| 🟩 | Shrieking Horde | random | Medieval 90%, Renaissance 10% | 🟢 21/23 (91%) | CRUSADER×1 | CRUSADER×17, SIEGE_RAM×12, NINJA×18, CONDOTTERI×15, HANDGUNNER×13, CRUSADER×16, SAMURAI×17, CRUSADER×13, SAMURAI×14, CONDOTTERI×13, CRUSADER×16, CONDOTTERI×15 |
| 🟩 | Crude Invaders | random | Medieval 93%, Iron Age 7% | 🟢 23/23 (100%) |  | SAMURAI×16, CONDOTTERI×16, CONDOTTERI×13, HANDGUNNER×18, SAMURAI×13, SIEGE_RAM×12, HANDGUNNER×15, CONDOTTERI×14, HORSEMAN_FAST×14, SAMURAI×16, CONDOTTERI×15, HANDGUNNER×15, CRUSADER×13 |
| 🟩 | Reckless Looters | random | Medieval 75%, Iron Age 25% | 🟢 23/23 (100%) |  | KNIGHT×18, KNIGHT×15, PIKENEER×17, CONDOTTERI×16, SIEGE_RAM×15, CRUSADER×14, CONDOTTERI×13, HORSEMAN_SLOW×13, KNIGHT×15, SIEGE_RAM×12, SAMURAI×17, PIKENEER×14 |
| 🟩 | Howling Savages | random | Medieval 89%, Renaissance 11% | 🟡 18/23 (78%) | MUSKETEER×5 | CRUSADER×14, SAMURAI×11, KNIGHT×18, KNIGHT×15, HANDGUNNER×18, CRUSADER×11, HANDGUNNER×13, SAMURAI×14, KNIGHT×18, CONDOTTERI×15, CARGO×18 |
| 🟩 | Unlucky Raiders | random | Medieval 80%, Renaissance 20% | 🟢 20/23 (87%) | MUSKETEER×3 | CRUSADER×16, SIEGE_RAM×12, CONDOTTERI×13, KNIGHT×15, SAMURAI×13, CONDOTTERI×15, CARGO×12, SAMURAI×14, MUSKETEER×13 |
| 🟩 | Frenzied Pillagers | random | Medieval 80%, Iron Age 20% | 🟢 23/23 (100%) |  | CRUSADER×15, PIKENEER×12, PIKENEER×15, SAMURAI×17, KNIGHT×15, CONDOTTERI×15, KNIGHT×12, HANDGUNNER×16, CRUSADER×15 |
| 🟩 | Hungry Invaders | random | Medieval 68%, Iron Age 32% | 🟢 23/23 (100%) |  | HANDGUNNER×12, SIEGE_RAM×12, CONDOTTERI×16, HANDGUNNER×13, THE_SWORDMASTER×7, CONDOTTERI×13, LARGE_CART×16, SIEGE_RAM×15, HORSEMAN_FAST×15 |
| 🟩 | Angry Mob | random | Medieval 55%, Iron Age 24%, Renaissance 21% | 🟡 18/23 (78%) | MUSKETEER×5 | SAMURAI×12, CRUSADER×11, SAMURAI×14, HORSEMAN_SLOW×17, THE_SWORDMASTER×7, LARGE_CART×12, CONDOTTERI×14, CRUSADER×14, MUSKETEER×16, DRAGOONER×15, HANDGUNNER×17 |
| 🟩 | Grumpy Marauders | random | Medieval 72%, Iron Age 19%, Renaissance 9% | 🟡 13/23 (57%) | MUSKETEER×6, CONDOTTERI×2 | CONDOTTERI×16, MUSKETEER×14, SAMURAI×14, KNIGHT×15, SIEGE_RAM×18, SIEGE_RAM×12, HANDGUNNER×14, SIEGE_RAM×15, CRUSADER×12, HORSEMAN_FAST×15, PIKENEER×15 |
| 🟩 | Muddy Marauders | random | Medieval 89%, Renaissance 11% | 🟢 20/23 (87%) | MUSKETEER×3 | CONDOTTERI×11, SIEGE_RAM×15, SIEGE_RAM×15, CARGO×15, CONDOTTERI×18, HANDGUNNER×12, KNIGHT×12, CRUSADER×16, SIEGE_RAM×15, HANDGUNNER×13 |
| 🟩 | Restless Horde | random | Medieval 89%, Iron Age 11% | 🟢 23/23 (100%) |  | HANDGUNNER×16, SAMURAI×15, SIEGE_RAM×15, CRUSADER×15, PIKENEER×16, CRUSADER×12, SIEGE_RAM×12, SIEGE_RAM×12, SAMURAI×15, CRUSADER×11, CONDOTTERI×13 |
| 🟩 | Noisy Barbarians | random | Medieval 82%, Renaissance 10%, Iron Age 8% | 🟡 15/23 (65%) | MUSKETEER×4, CRUSADER×2 | CRUSADER×12, HANDGUNNER×14, SAMURAI×14, LARGE_CART×12, HANDGUNNER×11, SIEGE_RAM×12, CRUSADER×16, SAMURAI×12, SAMURAI×16, CRUSADER×18, CARGO×15 |
| 🟩 | Savage Rabble | random | Medieval 86%, Renaissance 8%, Iron Age 5% | 🟢 23/23 (100%) |  | CONDOTTERI×13, HANDGUNNER×18, KNIGHT×12, KNIGHT×12, THE_SWORDMASTER×7, MUSKETEER×11, SIEGE_RAM×18, SAMURAI×14, SAMURAI×13, KNIGHT×12 |
| 🟩 | Blundering Invaders | random | Medieval 82%, Renaissance 18% | 🟢 19/23 (83%) | MUSKETEER×4 | MUSKETEER×17, SIEGE_RAM×12, CRUSADER×13, CRUSADER×16, SAMURAI×15, HANDGUNNER×14, HANDGUNNER×13, DRAGOONER×15, SAMURAI×17, SAMURAI×13, CRUSADER×18, KNIGHT×15 |
| 🟩 | Wandering Pillagers | random | Medieval 94%, Renaissance 6% | 🟡 13/23 (57%) | THE_KING×1 | CONDOTTERI×15, THE_KING×10, SIEGE_RAM×12, CONDOTTERI×13, SAMURAI×16, CONDOTTERI×13, CRUSADER×12, SIEGE_RAM×15, KNIGHT×15, KNIGHT×12, CONDOTTERI×17, SAMURAI×11 |
| 🟩 | Noisy Barbarians | random | Medieval 72%, Iron Age 19%, Renaissance 9% | 🟢 23/23 (100%) |  | SIEGE_RAM×15, KNIGHT×12, KNIGHT×18, SAMURAI×15, LARGE_CART×16, CRUSADER×18, DRAGOONER×13, SIEGE_RAM×12, SIEGE_RAM×15, HORSEMAN_FAST×12 |
| 🟩 | Noisy Barbarians | random | Medieval 77%, Iron Age 12%, Renaissance 11% | 🟢 20/23 (87%) | MUSKETEER×3 | SAMURAI×15, SAMURAI×15, SIEGE_RAM×15, CRUSADER×12, CARGO×15, CONDOTTERI×12, LEGIONARY×16, CONDOTTERI×18, KNIGHT×15 |

#### Big Mixed

| Tower Era Distribution (41 towers) | Towers |
|---|---|
| Medieval 100% (41) | CANNON_TOWER×17, TAR_TOWER×10, HEAVY_TOWER×8, BOILING_OIL×6 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Medieval Siege | hardcoded | Medieval 96%, Renaissance 4% | 🟢 23/23 (100%) |  | CRUSADER×12, CONDOTTERI×13, KNIGHT×14, SAMURAI×15, SIEGE_RAM×15, KNIGHT×16, CONDOTTERI×17, CRUSADER×18, NINJA×11, SIEGE_RAM×20, HANDGUNNER×22, HANDGUNNER×24, HANDGUNNER×26, SAMURAI×28 |
| 🟩 | Knights' Charge | hardcoded | Medieval 91%, Renaissance 9% | 🟢 23/23 (100%) |  | CRUSADER×16, SIEGE_RAM×17, CRUSADER×18, SIEGE_RAM×19, SAMURAI×20, KNIGHT×21, SAMURAI×22, CRUSADER×16, SAMURAI×18, KNIGHT×20, KNIGHT×22, CRUSADER×24, KNIGHT×26, KNIGHT×28, NINJA×30 |
| 🟩 | Crusader Host | hardcoded | Medieval 82%, Iron Age 18% | 🟢 23/23 (100%) |  | CRUSADER×16, SIEGE_RAM×17, SAMURAI×18, SIEGE_RAM×19, SIEGE_RAM×20, SAMURAI×21, CRUSADER×22, KNIGHT×16, KNIGHT×18, CRUSADER×20, CRUSADER×22, HANDGUNNER×24, CONDOTTERI×26, SAMURAI×28, THE_SWORDMASTER×30, LARGE_CART×31 |
| 🟩 | Castle Assault | hardcoded | Medieval 84%, Iron Age 16% | 🟢 23/23 (100%) |  | SAMURAI×16, KNIGHT×17, KNIGHT×18, KNIGHT×19, CRUSADER×20, CRUSADER×21, SIEGE_RAM×22, SAMURAI×16, CRUSADER×18, CRUSADER×20, CRUSADER×22, SAMURAI×24, SIEGE_RAM×26, LEGIONARY×28, CRUSADER×30, SAMURAI×32, HORSEMAN_FAST×32 |
| 🟩 | Feudal Army | hardcoded | Medieval 92%, Iron Age 8% | 🟢 23/23 (100%) |  | KNIGHT×16, SIEGE_RAM×17, KNIGHT×18, SIEGE_RAM×19, CRUSADER×20, CRUSADER×21, CONDOTTERI×22, HANDGUNNER×16, CRUSADER×18, SIEGE_RAM×20, SIEGE_RAM×22, CRUSADER×24, KNIGHT×26, CONDOTTERI×28, KNIGHT×30, LARGE_CART×32, CRUSADER×31 |
| 🟩 | Holy Crusade | hardcoded | Medieval 73%, Iron Age 24%, Renaissance 3% | 🟢 23/23 (100%) |  | SAMURAI×16, CONDOTTERI×17, HANDGUNNER×17, KNIGHT×18, THE_SWORDMASTER×19, CONDOTTERI×19, CONDOTTERI×20, HANDGUNNER×21, KNIGHT×21, LARGE_CART×22, LEGIONARY×23, MUSKETEER×12, THE_SWORDMASTER×24, SIEGE_RAM×28, SIEGE_RAM×30, HANDGUNNER×31, CRUSADER×34 |
| 🟩 | Grumpy Marauders | random | Medieval 92%, Renaissance 8% | 🟢 23/23 (100%) |  | CONDOTTERI×13, SAMURAI×15, HANDGUNNER×18, SAMURAI×12, HANDGUNNER×14, DRAGOONER×13, KNIGHT×12, KNIGHT×15, CRUSADER×14, SAMURAI×13, CRUSADER×14, CONDOTTERI×14 |
| 🟩 | Grumpy Marauders | random | Medieval 92%, Renaissance 8% | 🟢 23/23 (100%) |  | CONDOTTERI×13, SAMURAI×15, HANDGUNNER×18, SAMURAI×12, HANDGUNNER×14, DRAGOONER×13, KNIGHT×12, KNIGHT×15, CRUSADER×14, SAMURAI×13, CRUSADER×14, CONDOTTERI×14 |
| 🟩 | Howling Savages | random | Medieval 96%, Iron Age 4% | 🟢 23/23 (100%) |  | KNIGHT×15, SIEGE_RAM×15, SAMURAI×18, THE_SWORDMASTER×7, KNIGHT×12, SIEGE_RAM×18, CRUSADER×17, CRUSADER×17, SAMURAI×16, CRUSADER×12, CRUSADER×16, HANDGUNNER×15 |
| 🟩 | Shrieking Horde | random | Medieval 90%, Renaissance 10% | 🟢 23/23 (100%) |  | CRUSADER×17, SIEGE_RAM×12, NINJA×18, CONDOTTERI×15, HANDGUNNER×13, CRUSADER×16, SAMURAI×17, CRUSADER×13, SAMURAI×14, CONDOTTERI×13, CRUSADER×16, CONDOTTERI×15 |
| 🟩 | Crude Invaders | random | Medieval 93%, Iron Age 7% | 🟢 23/23 (100%) |  | SAMURAI×16, CONDOTTERI×16, CONDOTTERI×13, HANDGUNNER×18, SAMURAI×13, SIEGE_RAM×12, HANDGUNNER×15, CONDOTTERI×14, HORSEMAN_FAST×14, SAMURAI×16, CONDOTTERI×15, HANDGUNNER×15, CRUSADER×13 |
| 🟩 | Reckless Looters | random | Medieval 75%, Iron Age 25% | 🟢 23/23 (100%) |  | KNIGHT×18, KNIGHT×15, PIKENEER×17, CONDOTTERI×16, SIEGE_RAM×15, CRUSADER×14, CONDOTTERI×13, HORSEMAN_SLOW×13, KNIGHT×15, SIEGE_RAM×12, SAMURAI×17, PIKENEER×14 |
| 🟩 | Howling Savages | random | Medieval 89%, Renaissance 11% | 🟢 23/23 (100%) |  | CRUSADER×14, SAMURAI×11, KNIGHT×18, KNIGHT×15, HANDGUNNER×18, CRUSADER×11, HANDGUNNER×13, SAMURAI×14, KNIGHT×18, CONDOTTERI×15, CARGO×18 |
| 🟩 | Unlucky Raiders | random | Medieval 80%, Renaissance 20% | 🟢 23/23 (100%) |  | CRUSADER×16, SIEGE_RAM×12, CONDOTTERI×13, KNIGHT×15, SAMURAI×13, CONDOTTERI×15, CARGO×12, SAMURAI×14, MUSKETEER×13 |
| 🟩 | Frenzied Pillagers | random | Medieval 80%, Iron Age 20% | 🟢 23/23 (100%) |  | CRUSADER×15, PIKENEER×12, PIKENEER×15, SAMURAI×17, KNIGHT×15, CONDOTTERI×15, KNIGHT×12, HANDGUNNER×16, CRUSADER×15 |
| 🟩 | Hungry Invaders | random | Medieval 68%, Iron Age 32% | 🟢 23/23 (100%) |  | HANDGUNNER×12, SIEGE_RAM×12, CONDOTTERI×16, HANDGUNNER×13, THE_SWORDMASTER×7, CONDOTTERI×13, LARGE_CART×16, SIEGE_RAM×15, HORSEMAN_FAST×15 |
| 🟩 | Angry Mob | random | Medieval 55%, Iron Age 24%, Renaissance 21% | 🟢 23/23 (100%) |  | SAMURAI×12, CRUSADER×11, SAMURAI×14, HORSEMAN_SLOW×17, THE_SWORDMASTER×7, LARGE_CART×12, CONDOTTERI×14, CRUSADER×14, MUSKETEER×16, DRAGOONER×15, HANDGUNNER×17 |
| 🟩 | Grumpy Marauders | random | Medieval 72%, Iron Age 19%, Renaissance 9% | 🟢 23/23 (100%) |  | CONDOTTERI×16, MUSKETEER×14, SAMURAI×14, KNIGHT×15, SIEGE_RAM×18, SIEGE_RAM×12, HANDGUNNER×14, SIEGE_RAM×15, CRUSADER×12, HORSEMAN_FAST×15, PIKENEER×15 |
| 🟩 | Muddy Marauders | random | Medieval 89%, Renaissance 11% | 🟢 23/23 (100%) |  | CONDOTTERI×11, SIEGE_RAM×15, SIEGE_RAM×15, CARGO×15, CONDOTTERI×18, HANDGUNNER×12, KNIGHT×12, CRUSADER×16, SIEGE_RAM×15, HANDGUNNER×13 |
| 🟩 | Restless Horde | random | Medieval 89%, Iron Age 11% | 🟢 23/23 (100%) |  | HANDGUNNER×16, SAMURAI×15, SIEGE_RAM×15, CRUSADER×15, PIKENEER×16, CRUSADER×12, SIEGE_RAM×12, SIEGE_RAM×12, SAMURAI×15, CRUSADER×11, CONDOTTERI×13 |
| 🟩 | Noisy Barbarians | random | Medieval 82%, Renaissance 10%, Iron Age 8% | 🟢 23/23 (100%) |  | CRUSADER×12, HANDGUNNER×14, SAMURAI×14, LARGE_CART×12, HANDGUNNER×11, SIEGE_RAM×12, CRUSADER×16, SAMURAI×12, SAMURAI×16, CRUSADER×18, CARGO×15 |
| 🟩 | Savage Rabble | random | Medieval 86%, Renaissance 8%, Iron Age 5% | 🟢 23/23 (100%) |  | CONDOTTERI×13, HANDGUNNER×18, KNIGHT×12, KNIGHT×12, THE_SWORDMASTER×7, MUSKETEER×11, SIEGE_RAM×18, SAMURAI×14, SAMURAI×13, KNIGHT×12 |
| 🟩 | Blundering Invaders | random | Medieval 82%, Renaissance 18% | 🟢 23/23 (100%) |  | MUSKETEER×17, SIEGE_RAM×12, CRUSADER×13, CRUSADER×16, SAMURAI×15, HANDGUNNER×14, HANDGUNNER×13, DRAGOONER×15, SAMURAI×17, SAMURAI×13, CRUSADER×18, KNIGHT×15 |
| 🟩 | Wandering Pillagers | random | Medieval 94%, Renaissance 6% | 🟢 23/23 (100%) |  | CONDOTTERI×15, THE_KING×10, SIEGE_RAM×12, CONDOTTERI×13, SAMURAI×16, CONDOTTERI×13, CRUSADER×12, SIEGE_RAM×15, KNIGHT×15, KNIGHT×12, CONDOTTERI×17, SAMURAI×11 |
| 🟩 | Noisy Barbarians | random | Medieval 72%, Iron Age 19%, Renaissance 9% | 🟢 23/23 (100%) |  | SIEGE_RAM×15, KNIGHT×12, KNIGHT×18, SAMURAI×15, LARGE_CART×16, CRUSADER×18, DRAGOONER×13, SIEGE_RAM×12, SIEGE_RAM×15, HORSEMAN_FAST×12 |
| 🟩 | Noisy Barbarians | random | Medieval 77%, Iron Age 12%, Renaissance 11% | 🟢 23/23 (100%) |  | SAMURAI×15, SAMURAI×15, SIEGE_RAM×15, CRUSADER×12, CARGO×15, CONDOTTERI×12, LEGIONARY×16, CONDOTTERI×18, KNIGHT×15 |

#### Long Early

| Tower Era Distribution (28 towers) | Towers |
|---|---|
| Iron Age 50% (14), Medieval 50% (14) | ARBELESTE_TOWER×14, BOILING_OIL×5, HEAVY_TOWER×5, TAR_TOWER×4 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Medieval Siege | hardcoded | Medieval 96%, Renaissance 4% | 🟠 5/23 (22%) | HANDGUNNER×11, SAMURAI×5, CRUSADER×1 | CRUSADER×12, CONDOTTERI×13, KNIGHT×14, SAMURAI×15, SIEGE_RAM×15, KNIGHT×16, CONDOTTERI×17, CRUSADER×18, NINJA×11, SIEGE_RAM×20, HANDGUNNER×22, HANDGUNNER×24, HANDGUNNER×26, SAMURAI×28 |
| 🟩 | Knights' Charge | hardcoded | Medieval 91%, Renaissance 9% | 🟡 17/23 (74%) | NINJA×3 | CRUSADER×16, SIEGE_RAM×17, CRUSADER×18, SIEGE_RAM×19, SAMURAI×20, KNIGHT×21, SAMURAI×22, CRUSADER×16, SAMURAI×18, KNIGHT×20, KNIGHT×22, CRUSADER×24, KNIGHT×26, KNIGHT×28, NINJA×30 |
| 🟩 | Crusader Host | hardcoded | Medieval 82%, Iron Age 18% | 🔴 2/23 (9%) | CRUSADER×6, SAMURAI×5, HANDGUNNER×4 | CRUSADER×16, SIEGE_RAM×17, SAMURAI×18, SIEGE_RAM×19, SIEGE_RAM×20, SAMURAI×21, CRUSADER×22, KNIGHT×16, KNIGHT×18, CRUSADER×20, CRUSADER×22, HANDGUNNER×24, CONDOTTERI×26, SAMURAI×28, THE_SWORDMASTER×30, LARGE_CART×31 |
| 🟩 | Castle Assault | hardcoded | Medieval 84%, Iron Age 16% | 🟡 13/23 (57%) | CRUSADER×3, SIEGE_RAM×1 | SAMURAI×16, KNIGHT×17, KNIGHT×18, KNIGHT×19, CRUSADER×20, CRUSADER×21, SIEGE_RAM×22, SAMURAI×16, CRUSADER×18, CRUSADER×20, CRUSADER×22, SAMURAI×24, SIEGE_RAM×26, LEGIONARY×28, CRUSADER×30, SAMURAI×32, HORSEMAN_FAST×32 |
| 🟩 | Feudal Army | hardcoded | Medieval 92%, Iron Age 8% | 🟡 15/23 (65%) | CRUSADER×2, CONDOTTERI×2 | KNIGHT×16, SIEGE_RAM×17, KNIGHT×18, SIEGE_RAM×19, CRUSADER×20, CRUSADER×21, CONDOTTERI×22, HANDGUNNER×16, CRUSADER×18, SIEGE_RAM×20, SIEGE_RAM×22, CRUSADER×24, KNIGHT×26, CONDOTTERI×28, KNIGHT×30, LARGE_CART×32, CRUSADER×31 |
| 🟥 | Holy Crusade | hardcoded | Medieval 73%, Iron Age 24%, Renaissance 3% | ⬛ 0/23 (0%) | CRUSADER×10, HANDGUNNER×3 | SAMURAI×16, CONDOTTERI×17, HANDGUNNER×17, KNIGHT×18, THE_SWORDMASTER×19, CONDOTTERI×19, CONDOTTERI×20, HANDGUNNER×21, KNIGHT×21, LARGE_CART×22, LEGIONARY×23, MUSKETEER×12, THE_SWORDMASTER×24, SIEGE_RAM×28, SIEGE_RAM×30, HANDGUNNER×31, CRUSADER×34 |
| 🟩 | Grumpy Marauders | random | Medieval 92%, Renaissance 8% | 🟢 23/23 (100%) |  | CONDOTTERI×13, SAMURAI×15, HANDGUNNER×18, SAMURAI×12, HANDGUNNER×14, DRAGOONER×13, KNIGHT×12, KNIGHT×15, CRUSADER×14, SAMURAI×13, CRUSADER×14, CONDOTTERI×14 |
| 🟩 | Grumpy Marauders | random | Medieval 92%, Renaissance 8% | 🟢 23/23 (100%) |  | CONDOTTERI×13, SAMURAI×15, HANDGUNNER×18, SAMURAI×12, HANDGUNNER×14, DRAGOONER×13, KNIGHT×12, KNIGHT×15, CRUSADER×14, SAMURAI×13, CRUSADER×14, CONDOTTERI×14 |
| 🟩 | Howling Savages | random | Medieval 96%, Iron Age 4% | 🟢 23/23 (100%) |  | KNIGHT×15, SIEGE_RAM×15, SAMURAI×18, THE_SWORDMASTER×7, KNIGHT×12, SIEGE_RAM×18, CRUSADER×17, CRUSADER×17, SAMURAI×16, CRUSADER×12, CRUSADER×16, HANDGUNNER×15 |
| 🟩 | Shrieking Horde | random | Medieval 90%, Renaissance 10% | 🟢 21/23 (91%) | CONDOTTERI×1 | CRUSADER×17, SIEGE_RAM×12, NINJA×18, CONDOTTERI×15, HANDGUNNER×13, CRUSADER×16, SAMURAI×17, CRUSADER×13, SAMURAI×14, CONDOTTERI×13, CRUSADER×16, CONDOTTERI×15 |
| 🟩 | Crude Invaders | random | Medieval 93%, Iron Age 7% | 🟢 23/23 (100%) |  | SAMURAI×16, CONDOTTERI×16, CONDOTTERI×13, HANDGUNNER×18, SAMURAI×13, SIEGE_RAM×12, HANDGUNNER×15, CONDOTTERI×14, HORSEMAN_FAST×14, SAMURAI×16, CONDOTTERI×15, HANDGUNNER×15, CRUSADER×13 |
| 🟩 | Reckless Looters | random | Medieval 75%, Iron Age 25% | 🟢 23/23 (100%) |  | KNIGHT×18, KNIGHT×15, PIKENEER×17, CONDOTTERI×16, SIEGE_RAM×15, CRUSADER×14, CONDOTTERI×13, HORSEMAN_SLOW×13, KNIGHT×15, SIEGE_RAM×12, SAMURAI×17, PIKENEER×14 |
| 🟩 | Howling Savages | random | Medieval 89%, Renaissance 11% | 🟢 20/23 (87%) | MUSKETEER×2, KNIGHT×1 | CRUSADER×14, SAMURAI×11, KNIGHT×18, KNIGHT×15, HANDGUNNER×18, CRUSADER×11, HANDGUNNER×13, SAMURAI×14, KNIGHT×18, CONDOTTERI×15, CARGO×18 |
| 🟩 | Unlucky Raiders | random | Medieval 80%, Renaissance 20% | 🟢 21/23 (91%) | MUSKETEER×2 | CRUSADER×16, SIEGE_RAM×12, CONDOTTERI×13, KNIGHT×15, SAMURAI×13, CONDOTTERI×15, CARGO×12, SAMURAI×14, MUSKETEER×13 |
| 🟩 | Frenzied Pillagers | random | Medieval 80%, Iron Age 20% | 🟢 23/23 (100%) |  | CRUSADER×15, PIKENEER×12, PIKENEER×15, SAMURAI×17, KNIGHT×15, CONDOTTERI×15, KNIGHT×12, HANDGUNNER×16, CRUSADER×15 |
| 🟩 | Hungry Invaders | random | Medieval 68%, Iron Age 32% | 🟢 23/23 (100%) |  | HANDGUNNER×12, SIEGE_RAM×12, CONDOTTERI×16, HANDGUNNER×13, THE_SWORDMASTER×7, CONDOTTERI×13, LARGE_CART×16, SIEGE_RAM×15, HORSEMAN_FAST×15 |
| 🟩 | Angry Mob | random | Medieval 55%, Iron Age 24%, Renaissance 21% | 🟢 21/23 (91%) | MUSKETEER×2 | SAMURAI×12, CRUSADER×11, SAMURAI×14, HORSEMAN_SLOW×17, THE_SWORDMASTER×7, LARGE_CART×12, CONDOTTERI×14, CRUSADER×14, MUSKETEER×16, DRAGOONER×15, HANDGUNNER×17 |
| 🟩 | Grumpy Marauders | random | Medieval 72%, Iron Age 19%, Renaissance 9% | 🟢 21/23 (91%) | MUSKETEER×2 | CONDOTTERI×16, MUSKETEER×14, SAMURAI×14, KNIGHT×15, SIEGE_RAM×18, SIEGE_RAM×12, HANDGUNNER×14, SIEGE_RAM×15, CRUSADER×12, HORSEMAN_FAST×15, PIKENEER×15 |
| 🟩 | Muddy Marauders | random | Medieval 89%, Renaissance 11% | 🟢 21/23 (91%) | MUSKETEER×2 | CONDOTTERI×11, SIEGE_RAM×15, SIEGE_RAM×15, CARGO×15, CONDOTTERI×18, HANDGUNNER×12, KNIGHT×12, CRUSADER×16, SIEGE_RAM×15, HANDGUNNER×13 |
| 🟩 | Restless Horde | random | Medieval 89%, Iron Age 11% | 🟢 23/23 (100%) |  | HANDGUNNER×16, SAMURAI×15, SIEGE_RAM×15, CRUSADER×15, PIKENEER×16, CRUSADER×12, SIEGE_RAM×12, SIEGE_RAM×12, SAMURAI×15, CRUSADER×11, CONDOTTERI×13 |
| 🟩 | Noisy Barbarians | random | Medieval 82%, Renaissance 10%, Iron Age 8% | 🟢 19/23 (83%) | MUSKETEER×4 | CRUSADER×12, HANDGUNNER×14, SAMURAI×14, LARGE_CART×12, HANDGUNNER×11, SIEGE_RAM×12, CRUSADER×16, SAMURAI×12, SAMURAI×16, CRUSADER×18, CARGO×15 |
| 🟩 | Savage Rabble | random | Medieval 86%, Renaissance 8%, Iron Age 5% | 🟢 23/23 (100%) |  | CONDOTTERI×13, HANDGUNNER×18, KNIGHT×12, KNIGHT×12, THE_SWORDMASTER×7, MUSKETEER×11, SIEGE_RAM×18, SAMURAI×14, SAMURAI×13, KNIGHT×12 |
| 🟩 | Blundering Invaders | random | Medieval 82%, Renaissance 18% | 🟢 23/23 (100%) |  | MUSKETEER×17, SIEGE_RAM×12, CRUSADER×13, CRUSADER×16, SAMURAI×15, HANDGUNNER×14, HANDGUNNER×13, DRAGOONER×15, SAMURAI×17, SAMURAI×13, CRUSADER×18, KNIGHT×15 |
| 🟩 | Wandering Pillagers | random | Medieval 94%, Renaissance 6% | 🟢 23/23 (100%) |  | CONDOTTERI×15, THE_KING×10, SIEGE_RAM×12, CONDOTTERI×13, SAMURAI×16, CONDOTTERI×13, CRUSADER×12, SIEGE_RAM×15, KNIGHT×15, KNIGHT×12, CONDOTTERI×17, SAMURAI×11 |
| 🟩 | Noisy Barbarians | random | Medieval 72%, Iron Age 19%, Renaissance 9% | 🟢 23/23 (100%) |  | SIEGE_RAM×15, KNIGHT×12, KNIGHT×18, SAMURAI×15, LARGE_CART×16, CRUSADER×18, DRAGOONER×13, SIEGE_RAM×12, SIEGE_RAM×15, HORSEMAN_FAST×12 |
| 🟩 | Noisy Barbarians | random | Medieval 77%, Iron Age 12%, Renaissance 11% | 🟢 23/23 (100%) |  | SAMURAI×15, SAMURAI×15, SIEGE_RAM×15, CRUSADER×12, CARGO×15, CONDOTTERI×12, LEGIONARY×16, CONDOTTERI×18, KNIGHT×15 |

### Renaissance

#### Mixed late

| Tower Era Distribution (32 towers) | Towers |
|---|---|
| Renaissance 78% (25), Medieval 19% (6), Iron Age 3% (1) | RIFLE_TOWER×18, ICE_TOWER×7, CANNON_TOWER×6, COLD_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟥 | Renaissance Force | hardcoded | Renaissance 96%, Industrial 4% | ⬛ 0/24 (0%) | DRAGOONER×6, SMALL_TANK×6 | MUSKETEER×16, DRAGOONER×17, NINJA×17, NINJA×18, MUSKETEER×19, MUSKETEER×19, MUSKETEER×20, SMALL_TANK×22, MUSKETEER×21, DRAGOONER×22, NINJA×23, DRAGOONER×20, DRAGOONER×24, NINJA×28, DRAGOONER×30, DRAGOONER×32, CARGO×32, CARGO×34, THE_KING×36, MUSKETEER×35, DRAGOONER×36, DRAGOONER×35 |
| 🟥 | Musketeer Brigade | hardcoded | Renaissance 98%, Industrial 2% | ⬛ 0/24 (0%) | DRAGOONER×12 | MUSKETEER×16, DRAGOONER×17, DRAGOONER×17, CARGO×18, DRAGOONER×19, NINJA×19, MUSKETEER×20, CARGO×21, MUSKETEER×21, DRAGOONER×22, MOTORBIKE×12, NINJA×23, MUSKETEER×24, CARGO×28, THE_KING×30, CARGO×32, NINJA×34, MUSKETEER×36, MUSKETEER×36, NINJA×35, NINJA×38, DRAGOONER×34 |
| 🟥 | Ninja Infiltration | hardcoded | Renaissance 96%, Industrial 4% | ⬛ 0/24 (0%) | DRAGOONER×11, MUSKETEER×2 | NINJA×16, DRAGOONER×17, DRAGOONER×17, NINJA×18, MUSKETEER×19, CARGO×19, DRAGOONER×20, DRAGOONER×21, DRAGOONER×21, MUSKETEER×22, CARGO×23, CARGO×23, NINJA×33, NINJA×28, CARGO×30, CARGO×32, MUSKETEER×34, DRAGOONER×36, THE_KING×38, NINJA×36, NINJA×35, SOLDIER×22 |
| 🟥 | Cannon Barrage | hardcoded | Renaissance 96%, Industrial 4% | ⬛ 0/24 (0%) | DRAGOONER×6, SOLDIER×2, THE_KING×1 | MUSKETEER×16, DRAGOONER×17, CARGO×17, MUSKETEER×18, NINJA×19, NINJA×19, MUSKETEER×20, DRAGOONER×21, NINJA×21, NINJA×22, DRAGOONER×23, NINJA×23, MUSKETEER×24, MUSKETEER×28, THE_KING×30, NINJA×32, SOLDIER×20, DRAGOONER×36, DRAGOONER×36, DRAGOONER×36, MUSKETEER×36, MUSKETEER×35 |
| 🟥 | Rampaging Rabble | random | Renaissance 87%, Industrial 13% | ⬛ 0/24 (0%) | SMALL_TANK×8, MUSKETEER×4, NINJA×2 | MUSKETEER×24, THE_KING×10, SMALL_TANK×20, MUSKETEER×17, CARGO×27, NINJA×20, MUSKETEER×18, DRAGOONER×24, DRAGOONER×20, MUSKETEER×17, DRAGOONER×22, NINJA×22, MUSKETEER×18, CARGO×21, TRANSPORTER×20, MUSKETEER×18 |
| 🟥 | Rampaging Rabble | random | Renaissance 87%, Industrial 13% | ⬛ 0/24 (0%) | SMALL_TANK×8, MUSKETEER×4, NINJA×2 | MUSKETEER×24, THE_KING×10, SMALL_TANK×20, MUSKETEER×17, CARGO×27, NINJA×20, MUSKETEER×18, DRAGOONER×24, DRAGOONER×20, MUSKETEER×17, DRAGOONER×22, NINJA×22, MUSKETEER×18, CARGO×21, TRANSPORTER×20, MUSKETEER×18 |
| 🟥 | Petty Bandits | random | Renaissance 87%, Industrial 7%, Medieval 6% | ⬛ 0/24 (0%) | SOLDIER×12, DRAGOONER×6 | MUSKETEER×24, DRAGOONER×18, NINJA×24, THE_KING×10, CARGO×18, DRAGOONER×20, SOLDIER×21, CARGO×18, CARGO×15, NINJA×25, MUSKETEER×22, SAMURAI×19, NINJA×18, CARGO×18, MUSKETEER×25, DRAGOONER×22 |
| 🟥 | Savage Rabble | random | Renaissance 95%, Industrial 5% | ⬛ 0/24 (0%) | DRAGOONER×11, MUSKETEER×3 | CARGO×24, MUSKETEER×23, DRAGOONER×15, CARGO×21, NINJA×17, MUSKETEER×22, MUSKETEER×18, SMALL_TANK×16, DRAGOONER×24, DRAGOONER×20, CARGO×18, MUSKETEER×23, NINJA×20, CARGO×24, MUSKETEER×23, THE_KING×10 |
| 🟥 | Noisy Barbarians | random | Renaissance 94%, Medieval 6% | ⬛ 0/24 (0%) | MUSKETEER×8, DRAGOONER×8 | MUSKETEER×24, CARGO×21, MUSKETEER×21, CONDOTTERI×20, DRAGOONER×20, MUSKETEER×24, NINJA×26, MUSKETEER×16, MUSKETEER×21, CARGO×21, NINJA×21, DRAGOONER×24, DRAGOONER×22, CARGO×18, THE_KING×10, DRAGOONER×26, DRAGOONER×24 |
| 🟥 | Rude Barbarians | random | Renaissance 80%, Medieval 20% | ⬛ 0/24 (0%) | MUSKETEER×8, KNIGHT×6, DRAGOONER×5 | MUSKETEER×19, MUSKETEER×26, SAMURAI×26, MUSKETEER×23, MUSKETEER×25, KNIGHT×18, DRAGOONER×18, CARGO×18, CARGO×18, HANDGUNNER×19, MUSKETEER×16, CARGO×24, MUSKETEER×17, NINJA×24, THE_KING×10, DRAGOONER×22 |
| 🟥 | Restless Horde | random | Renaissance 88%, Industrial 12% | ⬛ 0/24 (0%) | SOLDIER×12, MUSKETEER×2, THE_KING×1 | MUSKETEER×18, NINJA×25, NINJA×21, SOLDIER×19, CARGO×27, THE_KING×10, CARGO×21, MUSKETEER×25, SOLDIER×22, CARGO×24, CARGO×24, MUSKETEER×24, DRAGOONER×20, NINJA×17, DRAGOONER×26, CARGO×18 |
| 🟥 | Blundering Invaders | random | Renaissance 77%, Industrial 23% | ⬛ 0/24 (0%) | SOLDIER×22, MUSKETEER×2 | DRAGOONER×18, NINJA×22, SOLDIER×25, THE_KING×10, CARGO×21, MUSKETEER×21, DRAGOONER×22, NINJA×25, SOLDIER×19, NINJA×20, NINJA×17, SMALL_TANK×24, MUSKETEER×26, MUSKETEER×21 |
| 🟥 | Relentless Mob | random | Renaissance 77%, Medieval 15%, Industrial 8% | ⬛ 0/24 (0%) | DRAGOONER×8, MOTORBIKE×3 | NINJA×26, NINJA×21, DRAGOONER×22, DRAGOONER×20, MOTORBIKE×21, SAMURAI×21, DRAGOONER×18, DRAGOONER×18, DRAGOONER×18, CARGO×24, NINJA×16, THE_KING×10, CRUSADER×21, MUSKETEER×24 |
| 🟥 | Grumpy Marauders | random | Renaissance 77%, Medieval 23% | ⬛ 0/24 (0%) | MUSKETEER×7, KNIGHT×7, DRAGOONER×5 | CARGO×24, MUSKETEER×19, CARGO×18, KNIGHT×21, MUSKETEER×25, CONDOTTERI×19, CARGO×18, DRAGOONER×22, CRUSADER×25, DRAGOONER×18, NINJA×21, THE_KING×10, CARGO×24, DRAGOONER×22 |
| 🟥 | Weary Plunderers | random | Renaissance 70%, Medieval 19%, Industrial 11% | ⬛ 0/24 (0%) | SOLDIER×17, KNIGHT×6, MUSKETEER×1 | CARGO×18, KNIGHT×18, CARGO×21, SOLDIER×17, MUSKETEER×23, CARGO×18, CRUSADER×21, NINJA×26, SOLDIER×17, MUSKETEER×24, SAMURAI×21, MUSKETEER×20, MUSKETEER×25, DRAGOONER×20, THE_KING×10, MUSKETEER×18 |
| 🟥 | Frenzied Pillagers | random | Renaissance 73%, Medieval 14%, Industrial 13% | ⬛ 0/24 (0%) | MUSKETEER×9, KNIGHT×7, DRAGOONER×2, CONDOTTERI×1, MOTORBIKE×1 | DRAGOONER×18, MUSKETEER×21, NINJA×19, CONDOTTERI×24, MUSKETEER×25, MOTORBIKE×17, DRAGOONER×22, KNIGHT×21, MUSKETEER×17, MUSKETEER×20, MUSKETEER×24, THE_KING×10, SMALL_TANK×26, DRAGOONER×22, MUSKETEER×22, CARGO×21 |
| 🟥 | Reckless Looters | random | Renaissance 88%, Industrial 12% | ⬛ 0/24 (0%) | DRAGOONER×11, MOTORBIKE×1 | DRAGOONER×24, MOTORBIKE×19, MUSKETEER×21, NINJA×25, MOTORBIKE×18, CARGO×18, THE_KING×10, NINJA×17, MUSKETEER×20, DRAGOONER×22, MUSKETEER×17, DRAGOONER×22, DRAGOONER×24, CARGO×18, MUSKETEER×25 |
| 🟥 | Forgotten Warband | random | Renaissance 93%, Medieval 7% | ⬛ 0/24 (0%) | DRAGOONER×9, MUSKETEER×5, NINJA×1 | NINJA×17, NINJA×20, DRAGOONER×20, DRAGOONER×22, MUSKETEER×17, NINJA×22, NINJA×19, SAMURAI×23, NINJA×16, DRAGOONER×20, MUSKETEER×25, THE_KING×10, MUSKETEER×23, DRAGOONER×24, MUSKETEER×18, DRAGOONER×24 |
| 🟥 | Blundering Invaders | random | Renaissance 81%, Industrial 13%, Medieval 6% | ⬛ 0/24 (0%) | SOLDIER×23, MUSKETEER×1 | CARGO×24, SOLDIER×22, MUSKETEER×23, KNIGHT×18, MUSKETEER×24, SOLDIER×18, THE_KING×10, CARGO×15, MUSKETEER×26, MUSKETEER×25, NINJA×19, DRAGOONER×24, NINJA×18, MUSKETEER×17, NINJA×22 |
| 🟥 | Rude Barbarians | random | Renaissance 86%, Industrial 8%, Medieval 7% | ⬛ 0/24 (0%) | DRAGOONER×11, SMALL_TANK×1 | THE_KING×10, NINJA×16, MUSKETEER×16, NINJA×17, NINJA×20, DRAGOONER×18, MUSKETEER×18, SMALL_TANK×20, DRAGOONER×26, NINJA×17, CONDOTTERI×17, MUSKETEER×18, CARGO×27, CARGO×21 |
| 🟥 | Clumsy Attackers | random | Renaissance 82%, Industrial 18% | ⬛ 0/24 (0%) | DRAGOONER×7, MUSKETEER×7, THE_KING×1 | DRAGOONER×24, NINJA×19, CARGO×21, DRAGOONER×24, CARGO×24, THE_KING×10, NINJA×25, MUSKETEER×20, SOLDIER×16, TRANSPORTER×20, MUSKETEER×16, DRAGOONER×20, CARGO×18, TRANSPORTER×20, MUSKETEER×20, MUSKETEER×21 |
| 🟥 | Hungry Invaders | random | Renaissance 88%, Industrial 12% | ⬛ 0/24 (0%) | MUSKETEER×5, DRAGOONER×4, THE_KING×1, SOLDIER×1 | DRAGOONER×20, MUSKETEER×21, NINJA×17, DRAGOONER×22, MUSKETEER×22, CARGO×18, NINJA×18, THE_KING×10, DRAGOONER×24, MUSKETEER×23, MUSKETEER×21, DRAGOONER×22, SOLDIER×24, CARGO×18, SMALL_TANK×16, NINJA×24 |
| 🟥 | Clumsy Attackers | random | Renaissance 74%, Industrial 13%, Medieval 13% | ⬛ 0/24 (0%) | SOLDIER×16, MUSKETEER×5, DRAGOONER×1, KNIGHT×1 | MUSKETEER×21, NINJA×21, CARGO×21, CARGO×24, DRAGOONER×18, THE_KING×10, NINJA×24, KNIGHT×21, TRANSPORTER×20, CARGO×21, DRAGOONER×18, KNIGHT×18, NINJA×25, NINJA×21, MOTORBIKE×20 |
| 🟥 | Clumsy Attackers | random | Renaissance 83%, Industrial 9%, Medieval 9% | ⬛ 0/24 (0%) | DRAGOONER×8, MUSKETEER×8 | CRUSADER×25, DRAGOONER×24, CARGO×18, DRAGOONER×20, MUSKETEER×22, NINJA×22, NINJA×17, DRAGOONER×26, NINJA×21, MUSKETEER×18, MUSKETEER×21, NINJA×23, THE_KING×10, MOTORBIKE×26 |

#### Full Heavy Medieval

| Tower Era Distribution (45 towers) | Towers |
|---|---|
| Medieval 84% (38), Renaissance 16% (7) | HEAVY_TOWER×38, ICE_TOWER×7 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟥 | Renaissance Force | hardcoded | Renaissance 96%, Industrial 4% | ⬛ 0/28 (0%) | MUSKETEER×10, SMALL_TANK×9 | MUSKETEER×16, DRAGOONER×17, NINJA×17, NINJA×18, MUSKETEER×19, MUSKETEER×19, MUSKETEER×20, SMALL_TANK×22, MUSKETEER×21, DRAGOONER×22, NINJA×23, DRAGOONER×20, DRAGOONER×24, NINJA×28, DRAGOONER×30, DRAGOONER×32, CARGO×32, CARGO×34, THE_KING×36, MUSKETEER×35, DRAGOONER×36, DRAGOONER×35 |
| 🟥 | Musketeer Brigade | hardcoded | Renaissance 98%, Industrial 2% | ⬛ 0/28 (0%) | MUSKETEER×10, NINJA×4, THE_KING×1 | MUSKETEER×16, DRAGOONER×17, DRAGOONER×17, CARGO×18, DRAGOONER×19, NINJA×19, MUSKETEER×20, CARGO×21, MUSKETEER×21, DRAGOONER×22, MOTORBIKE×12, NINJA×23, MUSKETEER×24, CARGO×28, THE_KING×30, CARGO×32, NINJA×34, MUSKETEER×36, MUSKETEER×36, NINJA×35, NINJA×38, DRAGOONER×34 |
| 🟥 | Ninja Infiltration | hardcoded | Renaissance 96%, Industrial 4% | ⬛ 0/28 (0%) | MUSKETEER×26, NINJA×1 | NINJA×16, DRAGOONER×17, DRAGOONER×17, NINJA×18, MUSKETEER×19, CARGO×19, DRAGOONER×20, DRAGOONER×21, DRAGOONER×21, MUSKETEER×22, CARGO×23, CARGO×23, NINJA×33, NINJA×28, CARGO×30, CARGO×32, MUSKETEER×34, DRAGOONER×36, THE_KING×38, NINJA×36, NINJA×35, SOLDIER×22 |
| 🟥 | Cannon Barrage | hardcoded | Renaissance 96%, Industrial 4% | ⬛ 0/28 (0%) | SOLDIER×15, MUSKETEER×3, THE_KING×1 | MUSKETEER×16, DRAGOONER×17, CARGO×17, MUSKETEER×18, NINJA×19, NINJA×19, MUSKETEER×20, DRAGOONER×21, NINJA×21, NINJA×22, DRAGOONER×23, NINJA×23, MUSKETEER×24, MUSKETEER×28, THE_KING×30, NINJA×32, SOLDIER×20, DRAGOONER×36, DRAGOONER×36, DRAGOONER×36, MUSKETEER×36, MUSKETEER×35 |
| 🟥 | Rampaging Rabble | random | Renaissance 87%, Industrial 13% | ⬛ 0/28 (0%) | MUSKETEER×10, SMALL_TANK×7, SOLDIER×2, NINJA×1 | MUSKETEER×24, THE_KING×10, SMALL_TANK×20, MUSKETEER×17, CARGO×27, NINJA×20, MUSKETEER×18, DRAGOONER×24, DRAGOONER×20, MUSKETEER×17, DRAGOONER×22, NINJA×22, MUSKETEER×18, CARGO×21, TRANSPORTER×20, MUSKETEER×18 |
| 🟥 | Rampaging Rabble | random | Renaissance 87%, Industrial 13% | ⬛ 0/28 (0%) | MUSKETEER×10, SMALL_TANK×7, SOLDIER×2, NINJA×1 | MUSKETEER×24, THE_KING×10, SMALL_TANK×20, MUSKETEER×17, CARGO×27, NINJA×20, MUSKETEER×18, DRAGOONER×24, DRAGOONER×20, MUSKETEER×17, DRAGOONER×22, NINJA×22, MUSKETEER×18, CARGO×21, TRANSPORTER×20, MUSKETEER×18 |
| 🟩 | Petty Bandits | random | Renaissance 87%, Industrial 7%, Medieval 6% | 🟠 12/28 (43%) | SOLDIER×16 | MUSKETEER×24, DRAGOONER×18, NINJA×24, THE_KING×10, CARGO×18, DRAGOONER×20, SOLDIER×21, CARGO×18, CARGO×15, NINJA×25, MUSKETEER×22, SAMURAI×19, NINJA×18, CARGO×18, MUSKETEER×25, DRAGOONER×22 |
| 🟩 | Savage Rabble | random | Renaissance 95%, Industrial 5% | 🟠 11/28 (39%) | MUSKETEER×9, SMALL_TANK×4 | CARGO×24, MUSKETEER×23, DRAGOONER×15, CARGO×21, NINJA×17, MUSKETEER×22, MUSKETEER×18, SMALL_TANK×16, DRAGOONER×24, DRAGOONER×20, CARGO×18, MUSKETEER×23, NINJA×20, CARGO×24, MUSKETEER×23, THE_KING×10 |
| 🟩 | Noisy Barbarians | random | Renaissance 94%, Medieval 6% | 🟡 21/28 (75%) | MUSKETEER×5, DRAGOONER×1 | MUSKETEER×24, CARGO×21, MUSKETEER×21, CONDOTTERI×20, DRAGOONER×20, MUSKETEER×24, NINJA×26, MUSKETEER×16, MUSKETEER×21, CARGO×21, NINJA×21, DRAGOONER×24, DRAGOONER×22, CARGO×18, THE_KING×10, DRAGOONER×26, DRAGOONER×24 |
| 🟩 | Rude Barbarians | random | Renaissance 80%, Medieval 20% | 🟡 21/28 (75%) | MUSKETEER×5, NINJA×1 | MUSKETEER×19, MUSKETEER×26, SAMURAI×26, MUSKETEER×23, MUSKETEER×25, KNIGHT×18, DRAGOONER×18, CARGO×18, CARGO×18, HANDGUNNER×19, MUSKETEER×16, CARGO×24, MUSKETEER×17, NINJA×24, THE_KING×10, DRAGOONER×22 |
| 🟥 | Restless Horde | random | Renaissance 88%, Industrial 12% | ⬛ 0/28 (0%) | SOLDIER×14, MUSKETEER×6, THE_KING×1 | MUSKETEER×18, NINJA×25, NINJA×21, SOLDIER×19, CARGO×27, THE_KING×10, CARGO×21, MUSKETEER×25, SOLDIER×22, CARGO×24, CARGO×24, MUSKETEER×24, DRAGOONER×20, NINJA×17, DRAGOONER×26, CARGO×18 |
| 🟥 | Blundering Invaders | random | Renaissance 77%, Industrial 23% | ⬛ 0/28 (0%) | SOLDIER×24, MUSKETEER×2, NINJA×1 | DRAGOONER×18, NINJA×22, SOLDIER×25, THE_KING×10, CARGO×21, MUSKETEER×21, DRAGOONER×22, NINJA×25, SOLDIER×19, NINJA×20, NINJA×17, SMALL_TANK×24, MUSKETEER×26, MUSKETEER×21 |
| 🟩 | Relentless Mob | random | Renaissance 77%, Medieval 15%, Industrial 8% | 🟢 24/28 (86%) | MUSKETEER×4 | NINJA×26, NINJA×21, DRAGOONER×22, DRAGOONER×20, MOTORBIKE×21, SAMURAI×21, DRAGOONER×18, DRAGOONER×18, DRAGOONER×18, CARGO×24, NINJA×16, THE_KING×10, CRUSADER×21, MUSKETEER×24 |
| 🟩 | Grumpy Marauders | random | Renaissance 77%, Medieval 23% | 🟡 18/28 (64%) | MUSKETEER×10 | CARGO×24, MUSKETEER×19, CARGO×18, KNIGHT×21, MUSKETEER×25, CONDOTTERI×19, CARGO×18, DRAGOONER×22, CRUSADER×25, DRAGOONER×18, NINJA×21, THE_KING×10, CARGO×24, DRAGOONER×22 |
| 🟥 | Weary Plunderers | random | Renaissance 70%, Medieval 19%, Industrial 11% | ⬛ 0/28 (0%) | SOLDIER×26, MUSKETEER×2 | CARGO×18, KNIGHT×18, CARGO×21, SOLDIER×17, MUSKETEER×23, CARGO×18, CRUSADER×21, NINJA×26, SOLDIER×17, MUSKETEER×24, SAMURAI×21, MUSKETEER×20, MUSKETEER×25, DRAGOONER×20, THE_KING×10, MUSKETEER×18 |
| 🟥 | Frenzied Pillagers | random | Renaissance 73%, Medieval 14%, Industrial 13% | ⬛ 0/28 (0%) | MUSKETEER×8, CONDOTTERI×4, SMALL_TANK×3, MOTORBIKE×2 | DRAGOONER×18, MUSKETEER×21, NINJA×19, CONDOTTERI×24, MUSKETEER×25, MOTORBIKE×17, DRAGOONER×22, KNIGHT×21, MUSKETEER×17, MUSKETEER×20, MUSKETEER×24, THE_KING×10, SMALL_TANK×26, DRAGOONER×22, MUSKETEER×22, CARGO×21 |
| 🟩 | Reckless Looters | random | Renaissance 88%, Industrial 12% | 🟢 28/28 (100%) |  | DRAGOONER×24, MOTORBIKE×19, MUSKETEER×21, NINJA×25, MOTORBIKE×18, CARGO×18, THE_KING×10, NINJA×17, MUSKETEER×20, DRAGOONER×22, MUSKETEER×17, DRAGOONER×22, DRAGOONER×24, CARGO×18, MUSKETEER×25 |
| 🟩 | Forgotten Warband | random | Renaissance 93%, Medieval 7% | 🟢 25/28 (89%) | MUSKETEER×3 | NINJA×17, NINJA×20, DRAGOONER×20, DRAGOONER×22, MUSKETEER×17, NINJA×22, NINJA×19, SAMURAI×23, NINJA×16, DRAGOONER×20, MUSKETEER×25, THE_KING×10, MUSKETEER×23, DRAGOONER×24, MUSKETEER×18, DRAGOONER×24 |
| 🟥 | Blundering Invaders | random | Renaissance 81%, Industrial 13%, Medieval 6% | ⬛ 0/28 (0%) | SOLDIER×22, MUSKETEER×6 | CARGO×24, SOLDIER×22, MUSKETEER×23, KNIGHT×18, MUSKETEER×24, SOLDIER×18, THE_KING×10, CARGO×15, MUSKETEER×26, MUSKETEER×25, NINJA×19, DRAGOONER×24, NINJA×18, MUSKETEER×17, NINJA×22 |
| 🟩 | Rude Barbarians | random | Renaissance 86%, Industrial 8%, Medieval 7% | 🔴 3/28 (11%) | MUSKETEER×13, SMALL_TANK×6 | THE_KING×10, NINJA×16, MUSKETEER×16, NINJA×17, NINJA×20, DRAGOONER×18, MUSKETEER×18, SMALL_TANK×20, DRAGOONER×26, NINJA×17, CONDOTTERI×17, MUSKETEER×18, CARGO×27, CARGO×21 |
| 🟥 | Clumsy Attackers | random | Renaissance 82%, Industrial 18% | ⬛ 0/28 (0%) | SOLDIER×16, MUSKETEER×2, THE_KING×1 | DRAGOONER×24, NINJA×19, CARGO×21, DRAGOONER×24, CARGO×24, THE_KING×10, NINJA×25, MUSKETEER×20, SOLDIER×16, TRANSPORTER×20, MUSKETEER×16, DRAGOONER×20, CARGO×18, TRANSPORTER×20, MUSKETEER×20, MUSKETEER×21 |
| 🟩 | Hungry Invaders | random | Renaissance 88%, Industrial 12% | 🔴 5/28 (18%) | SOLDIER×21, SMALL_TANK×1 | DRAGOONER×20, MUSKETEER×21, NINJA×17, DRAGOONER×22, MUSKETEER×22, CARGO×18, NINJA×18, THE_KING×10, DRAGOONER×24, MUSKETEER×23, MUSKETEER×21, DRAGOONER×22, SOLDIER×24, CARGO×18, SMALL_TANK×16, NINJA×24 |
| 🟩 | Clumsy Attackers | random | Renaissance 74%, Industrial 13%, Medieval 13% | 🟡 18/28 (64%) | SOLDIER×10 | MUSKETEER×21, NINJA×21, CARGO×21, CARGO×24, DRAGOONER×18, THE_KING×10, NINJA×24, KNIGHT×21, TRANSPORTER×20, CARGO×21, DRAGOONER×18, KNIGHT×18, NINJA×25, NINJA×21, MOTORBIKE×20 |
| 🟩 | Clumsy Attackers | random | Renaissance 83%, Industrial 9%, Medieval 9% | 🟢 24/28 (86%) | MUSKETEER×4 | CRUSADER×25, DRAGOONER×24, CARGO×18, DRAGOONER×20, MUSKETEER×22, NINJA×22, NINJA×17, DRAGOONER×26, NINJA×21, MUSKETEER×18, MUSKETEER×21, NINJA×23, THE_KING×10, MOTORBIKE×26 |

#### Full Rifle

| Tower Era Distribution (35 towers) | Towers |
|---|---|
| Renaissance 80% (28), Medieval 20% (7) | RIFLE_TOWER×28, TAR_TOWER×7 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟥 | Renaissance Force | hardcoded | Renaissance 96%, Industrial 4% | ⬛ 0/16 (0%) | SMALL_TANK×8 | MUSKETEER×16, DRAGOONER×17, NINJA×17, NINJA×18, MUSKETEER×19, MUSKETEER×19, MUSKETEER×20, SMALL_TANK×22, MUSKETEER×21, DRAGOONER×22, NINJA×23, DRAGOONER×20, DRAGOONER×24, NINJA×28, DRAGOONER×30, DRAGOONER×32, CARGO×32, CARGO×34, THE_KING×36, MUSKETEER×35, DRAGOONER×36, DRAGOONER×35 |
| 🟩 | Musketeer Brigade | hardcoded | Renaissance 98%, Industrial 2% | 🟢 16/16 (100%) |  | MUSKETEER×16, DRAGOONER×17, DRAGOONER×17, CARGO×18, DRAGOONER×19, NINJA×19, MUSKETEER×20, CARGO×21, MUSKETEER×21, DRAGOONER×22, MOTORBIKE×12, NINJA×23, MUSKETEER×24, CARGO×28, THE_KING×30, CARGO×32, NINJA×34, MUSKETEER×36, MUSKETEER×36, NINJA×35, NINJA×38, DRAGOONER×34 |
| 🟥 | Ninja Infiltration | hardcoded | Renaissance 96%, Industrial 4% | ⬛ 0/16 (0%) | SOLDIER×6, THE_KING×1 | NINJA×16, DRAGOONER×17, DRAGOONER×17, NINJA×18, MUSKETEER×19, CARGO×19, DRAGOONER×20, DRAGOONER×21, DRAGOONER×21, MUSKETEER×22, CARGO×23, CARGO×23, NINJA×33, NINJA×28, CARGO×30, CARGO×32, MUSKETEER×34, DRAGOONER×36, THE_KING×38, NINJA×36, NINJA×35, SOLDIER×22 |
| 🟥 | Cannon Barrage | hardcoded | Renaissance 96%, Industrial 4% | ⬛ 0/16 (0%) | SOLDIER×8, DRAGOONER×4 | MUSKETEER×16, DRAGOONER×17, CARGO×17, MUSKETEER×18, NINJA×19, NINJA×19, MUSKETEER×20, DRAGOONER×21, NINJA×21, NINJA×22, DRAGOONER×23, NINJA×23, MUSKETEER×24, MUSKETEER×28, THE_KING×30, NINJA×32, SOLDIER×20, DRAGOONER×36, DRAGOONER×36, DRAGOONER×36, MUSKETEER×36, MUSKETEER×35 |
| 🟥 | Rampaging Rabble | random | Renaissance 87%, Industrial 13% | ⬛ 0/16 (0%) | SMALL_TANK×8 | MUSKETEER×24, THE_KING×10, SMALL_TANK×20, MUSKETEER×17, CARGO×27, NINJA×20, MUSKETEER×18, DRAGOONER×24, DRAGOONER×20, MUSKETEER×17, DRAGOONER×22, NINJA×22, MUSKETEER×18, CARGO×21, TRANSPORTER×20, MUSKETEER×18 |
| 🟥 | Rampaging Rabble | random | Renaissance 87%, Industrial 13% | ⬛ 0/16 (0%) | SMALL_TANK×8 | MUSKETEER×24, THE_KING×10, SMALL_TANK×20, MUSKETEER×17, CARGO×27, NINJA×20, MUSKETEER×18, DRAGOONER×24, DRAGOONER×20, MUSKETEER×17, DRAGOONER×22, NINJA×22, MUSKETEER×18, CARGO×21, TRANSPORTER×20, MUSKETEER×18 |
| 🟩 | Petty Bandits | random | Renaissance 87%, Industrial 7%, Medieval 6% | 🟡 9/16 (56%) | SOLDIER×7 | MUSKETEER×24, DRAGOONER×18, NINJA×24, THE_KING×10, CARGO×18, DRAGOONER×20, SOLDIER×21, CARGO×18, CARGO×15, NINJA×25, MUSKETEER×22, SAMURAI×19, NINJA×18, CARGO×18, MUSKETEER×25, DRAGOONER×22 |
| 🟥 | Savage Rabble | random | Renaissance 95%, Industrial 5% | ⬛ 0/16 (0%) | SMALL_TANK×8 | CARGO×24, MUSKETEER×23, DRAGOONER×15, CARGO×21, NINJA×17, MUSKETEER×22, MUSKETEER×18, SMALL_TANK×16, DRAGOONER×24, DRAGOONER×20, CARGO×18, MUSKETEER×23, NINJA×20, CARGO×24, MUSKETEER×23, THE_KING×10 |
| 🟩 | Noisy Barbarians | random | Renaissance 94%, Medieval 6% | 🟢 16/16 (100%) |  | MUSKETEER×24, CARGO×21, MUSKETEER×21, CONDOTTERI×20, DRAGOONER×20, MUSKETEER×24, NINJA×26, MUSKETEER×16, MUSKETEER×21, CARGO×21, NINJA×21, DRAGOONER×24, DRAGOONER×22, CARGO×18, THE_KING×10, DRAGOONER×26, DRAGOONER×24 |
| 🟩 | Rude Barbarians | random | Renaissance 80%, Medieval 20% | 🟢 14/16 (88%) | KNIGHT×2 | MUSKETEER×19, MUSKETEER×26, SAMURAI×26, MUSKETEER×23, MUSKETEER×25, KNIGHT×18, DRAGOONER×18, CARGO×18, CARGO×18, HANDGUNNER×19, MUSKETEER×16, CARGO×24, MUSKETEER×17, NINJA×24, THE_KING×10, DRAGOONER×22 |
| 🟥 | Restless Horde | random | Renaissance 88%, Industrial 12% | ⬛ 0/16 (0%) | SOLDIER×6, THE_KING×1 | MUSKETEER×18, NINJA×25, NINJA×21, SOLDIER×19, CARGO×27, THE_KING×10, CARGO×21, MUSKETEER×25, SOLDIER×22, CARGO×24, CARGO×24, MUSKETEER×24, DRAGOONER×20, NINJA×17, DRAGOONER×26, CARGO×18 |
| 🟥 | Blundering Invaders | random | Renaissance 77%, Industrial 23% | ⬛ 0/16 (0%) | SOLDIER×14, SMALL_TANK×1 | DRAGOONER×18, NINJA×22, SOLDIER×25, THE_KING×10, CARGO×21, MUSKETEER×21, DRAGOONER×22, NINJA×25, SOLDIER×19, NINJA×20, NINJA×17, SMALL_TANK×24, MUSKETEER×26, MUSKETEER×21 |
| 🟩 | Relentless Mob | random | Renaissance 77%, Medieval 15%, Industrial 8% | 🟢 16/16 (100%) |  | NINJA×26, NINJA×21, DRAGOONER×22, DRAGOONER×20, MOTORBIKE×21, SAMURAI×21, DRAGOONER×18, DRAGOONER×18, DRAGOONER×18, CARGO×24, NINJA×16, THE_KING×10, CRUSADER×21, MUSKETEER×24 |
| 🟩 | Grumpy Marauders | random | Renaissance 77%, Medieval 23% | 🟡 12/16 (75%) | KNIGHT×4 | CARGO×24, MUSKETEER×19, CARGO×18, KNIGHT×21, MUSKETEER×25, CONDOTTERI×19, CARGO×18, DRAGOONER×22, CRUSADER×25, DRAGOONER×18, NINJA×21, THE_KING×10, CARGO×24, DRAGOONER×22 |
| 🟥 | Weary Plunderers | random | Renaissance 70%, Medieval 19%, Industrial 11% | ⬛ 0/16 (0%) | SOLDIER×11, KNIGHT×5 | CARGO×18, KNIGHT×18, CARGO×21, SOLDIER×17, MUSKETEER×23, CARGO×18, CRUSADER×21, NINJA×26, SOLDIER×17, MUSKETEER×24, SAMURAI×21, MUSKETEER×20, MUSKETEER×25, DRAGOONER×20, THE_KING×10, MUSKETEER×18 |
| 🟥 | Frenzied Pillagers | random | Renaissance 73%, Medieval 14%, Industrial 13% | ⬛ 0/16 (0%) | SMALL_TANK×6, KNIGHT×4 | DRAGOONER×18, MUSKETEER×21, NINJA×19, CONDOTTERI×24, MUSKETEER×25, MOTORBIKE×17, DRAGOONER×22, KNIGHT×21, MUSKETEER×17, MUSKETEER×20, MUSKETEER×24, THE_KING×10, SMALL_TANK×26, DRAGOONER×22, MUSKETEER×22, CARGO×21 |
| 🟩 | Reckless Looters | random | Renaissance 88%, Industrial 12% | 🟢 16/16 (100%) |  | DRAGOONER×24, MOTORBIKE×19, MUSKETEER×21, NINJA×25, MOTORBIKE×18, CARGO×18, THE_KING×10, NINJA×17, MUSKETEER×20, DRAGOONER×22, MUSKETEER×17, DRAGOONER×22, DRAGOONER×24, CARGO×18, MUSKETEER×25 |
| 🟩 | Forgotten Warband | random | Renaissance 93%, Medieval 7% | 🟢 16/16 (100%) |  | NINJA×17, NINJA×20, DRAGOONER×20, DRAGOONER×22, MUSKETEER×17, NINJA×22, NINJA×19, SAMURAI×23, NINJA×16, DRAGOONER×20, MUSKETEER×25, THE_KING×10, MUSKETEER×23, DRAGOONER×24, MUSKETEER×18, DRAGOONER×24 |
| 🟥 | Blundering Invaders | random | Renaissance 81%, Industrial 13%, Medieval 6% | ⬛ 0/16 (0%) | SOLDIER×16 | CARGO×24, SOLDIER×22, MUSKETEER×23, KNIGHT×18, MUSKETEER×24, SOLDIER×18, THE_KING×10, CARGO×15, MUSKETEER×26, MUSKETEER×25, NINJA×19, DRAGOONER×24, NINJA×18, MUSKETEER×17, NINJA×22 |
| 🟥 | Rude Barbarians | random | Renaissance 86%, Industrial 8%, Medieval 7% | ⬛ 0/16 (0%) | SMALL_TANK×8 | THE_KING×10, NINJA×16, MUSKETEER×16, NINJA×17, NINJA×20, DRAGOONER×18, MUSKETEER×18, SMALL_TANK×20, DRAGOONER×26, NINJA×17, CONDOTTERI×17, MUSKETEER×18, CARGO×27, CARGO×21 |
| 🟩 | Clumsy Attackers | random | Renaissance 82%, Industrial 18% | 🟡 9/16 (56%) | SOLDIER×7 | DRAGOONER×24, NINJA×19, CARGO×21, DRAGOONER×24, CARGO×24, THE_KING×10, NINJA×25, MUSKETEER×20, SOLDIER×16, TRANSPORTER×20, MUSKETEER×16, DRAGOONER×20, CARGO×18, TRANSPORTER×20, MUSKETEER×20, MUSKETEER×21 |
| 🟥 | Hungry Invaders | random | Renaissance 88%, Industrial 12% | ⬛ 0/16 (0%) | SOLDIER×13, SMALL_TANK×2 | DRAGOONER×20, MUSKETEER×21, NINJA×17, DRAGOONER×22, MUSKETEER×22, CARGO×18, NINJA×18, THE_KING×10, DRAGOONER×24, MUSKETEER×23, MUSKETEER×21, DRAGOONER×22, SOLDIER×24, CARGO×18, SMALL_TANK×16, NINJA×24 |
| 🟩 | Clumsy Attackers | random | Renaissance 74%, Industrial 13%, Medieval 13% | 🔴 3/16 (19%) | SOLDIER×7, KNIGHT×6 | MUSKETEER×21, NINJA×21, CARGO×21, CARGO×24, DRAGOONER×18, THE_KING×10, NINJA×24, KNIGHT×21, TRANSPORTER×20, CARGO×21, DRAGOONER×18, KNIGHT×18, NINJA×25, NINJA×21, MOTORBIKE×20 |
| 🟩 | Clumsy Attackers | random | Renaissance 83%, Industrial 9%, Medieval 9% | 🟢 16/16 (100%) |  | CRUSADER×25, DRAGOONER×24, CARGO×18, DRAGOONER×20, MUSKETEER×22, NINJA×22, NINJA×17, DRAGOONER×26, NINJA×21, MUSKETEER×18, MUSKETEER×21, NINJA×23, THE_KING×10, MOTORBIKE×26 |

#### Mixed early ren

| Tower Era Distribution (33 towers) | Towers |
|---|---|
| Medieval 82% (27), Renaissance 18% (6) | BOILING_OIL×9, TAR_TOWER×9, CANNON_TOWER×9, RIFLE_TOWER×6 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟥 | Renaissance Force | hardcoded | Renaissance 96%, Industrial 4% | ⬛ 0/10 (0%) | SMALL_TANK×4, MUSKETEER×2 | MUSKETEER×16, DRAGOONER×17, NINJA×17, NINJA×18, MUSKETEER×19, MUSKETEER×19, MUSKETEER×20, SMALL_TANK×22, MUSKETEER×21, DRAGOONER×22, NINJA×23, DRAGOONER×20, DRAGOONER×24, NINJA×28, DRAGOONER×30, DRAGOONER×32, CARGO×32, CARGO×34, THE_KING×36, MUSKETEER×35, DRAGOONER×36, DRAGOONER×35 |
| 🟥 | Musketeer Brigade | hardcoded | Renaissance 98%, Industrial 2% | ⬛ 0/10 (0%) | MUSKETEER×4, THE_KING×1 | MUSKETEER×16, DRAGOONER×17, DRAGOONER×17, CARGO×18, DRAGOONER×19, NINJA×19, MUSKETEER×20, CARGO×21, MUSKETEER×21, DRAGOONER×22, MOTORBIKE×12, NINJA×23, MUSKETEER×24, CARGO×28, THE_KING×30, CARGO×32, NINJA×34, MUSKETEER×36, MUSKETEER×36, NINJA×35, NINJA×38, DRAGOONER×34 |
| 🟥 | Ninja Infiltration | hardcoded | Renaissance 96%, Industrial 4% | ⬛ 0/10 (0%) | MUSKETEER×8, NINJA×1 | NINJA×16, DRAGOONER×17, DRAGOONER×17, NINJA×18, MUSKETEER×19, CARGO×19, DRAGOONER×20, DRAGOONER×21, DRAGOONER×21, MUSKETEER×22, CARGO×23, CARGO×23, NINJA×33, NINJA×28, CARGO×30, CARGO×32, MUSKETEER×34, DRAGOONER×36, THE_KING×38, NINJA×36, NINJA×35, SOLDIER×22 |
| 🟥 | Cannon Barrage | hardcoded | Renaissance 96%, Industrial 4% | ⬛ 0/10 (0%) | MUSKETEER×5, THE_KING×1 | MUSKETEER×16, DRAGOONER×17, CARGO×17, MUSKETEER×18, NINJA×19, NINJA×19, MUSKETEER×20, DRAGOONER×21, NINJA×21, NINJA×22, DRAGOONER×23, NINJA×23, MUSKETEER×24, MUSKETEER×28, THE_KING×30, NINJA×32, SOLDIER×20, DRAGOONER×36, DRAGOONER×36, DRAGOONER×36, MUSKETEER×36, MUSKETEER×35 |
| 🟥 | Rampaging Rabble | random | Renaissance 87%, Industrial 13% | ⬛ 0/10 (0%) | SMALL_TANK×4, MUSKETEER×2 | MUSKETEER×24, THE_KING×10, SMALL_TANK×20, MUSKETEER×17, CARGO×27, NINJA×20, MUSKETEER×18, DRAGOONER×24, DRAGOONER×20, MUSKETEER×17, DRAGOONER×22, NINJA×22, MUSKETEER×18, CARGO×21, TRANSPORTER×20, MUSKETEER×18 |
| 🟥 | Rampaging Rabble | random | Renaissance 87%, Industrial 13% | ⬛ 0/10 (0%) | SMALL_TANK×4, MUSKETEER×2 | MUSKETEER×24, THE_KING×10, SMALL_TANK×20, MUSKETEER×17, CARGO×27, NINJA×20, MUSKETEER×18, DRAGOONER×24, DRAGOONER×20, MUSKETEER×17, DRAGOONER×22, NINJA×22, MUSKETEER×18, CARGO×21, TRANSPORTER×20, MUSKETEER×18 |
| 🟥 | Petty Bandits | random | Renaissance 87%, Industrial 7%, Medieval 6% | ⬛ 0/10 (0%) | SOLDIER×10 | MUSKETEER×24, DRAGOONER×18, NINJA×24, THE_KING×10, CARGO×18, DRAGOONER×20, SOLDIER×21, CARGO×18, CARGO×15, NINJA×25, MUSKETEER×22, SAMURAI×19, NINJA×18, CARGO×18, MUSKETEER×25, DRAGOONER×22 |
| 🟥 | Savage Rabble | random | Renaissance 95%, Industrial 5% | ⬛ 0/10 (0%) | MUSKETEER×8, DRAGOONER×1 | CARGO×24, MUSKETEER×23, DRAGOONER×15, CARGO×21, NINJA×17, MUSKETEER×22, MUSKETEER×18, SMALL_TANK×16, DRAGOONER×24, DRAGOONER×20, CARGO×18, MUSKETEER×23, NINJA×20, CARGO×24, MUSKETEER×23, THE_KING×10 |
| 🟥 | Noisy Barbarians | random | Renaissance 94%, Medieval 6% | ⬛ 0/10 (0%) | MUSKETEER×5, THE_KING×1 | MUSKETEER×24, CARGO×21, MUSKETEER×21, CONDOTTERI×20, DRAGOONER×20, MUSKETEER×24, NINJA×26, MUSKETEER×16, MUSKETEER×21, CARGO×21, NINJA×21, DRAGOONER×24, DRAGOONER×22, CARGO×18, THE_KING×10, DRAGOONER×26, DRAGOONER×24 |
| 🟥 | Rude Barbarians | random | Renaissance 80%, Medieval 20% | ⬛ 0/10 (0%) | MUSKETEER×10 | MUSKETEER×19, MUSKETEER×26, SAMURAI×26, MUSKETEER×23, MUSKETEER×25, KNIGHT×18, DRAGOONER×18, CARGO×18, CARGO×18, HANDGUNNER×19, MUSKETEER×16, CARGO×24, MUSKETEER×17, NINJA×24, THE_KING×10, DRAGOONER×22 |
| 🟥 | Restless Horde | random | Renaissance 88%, Industrial 12% | ⬛ 0/10 (0%) | SOLDIER×10 | MUSKETEER×18, NINJA×25, NINJA×21, SOLDIER×19, CARGO×27, THE_KING×10, CARGO×21, MUSKETEER×25, SOLDIER×22, CARGO×24, CARGO×24, MUSKETEER×24, DRAGOONER×20, NINJA×17, DRAGOONER×26, CARGO×18 |
| 🟥 | Blundering Invaders | random | Renaissance 77%, Industrial 23% | ⬛ 0/10 (0%) | SOLDIER×10 | DRAGOONER×18, NINJA×22, SOLDIER×25, THE_KING×10, CARGO×21, MUSKETEER×21, DRAGOONER×22, NINJA×25, SOLDIER×19, NINJA×20, NINJA×17, SMALL_TANK×24, MUSKETEER×26, MUSKETEER×21 |
| 🟩 | Relentless Mob | random | Renaissance 77%, Medieval 15%, Industrial 8% | 🟡 7/10 (70%) | MUSKETEER×3 | NINJA×26, NINJA×21, DRAGOONER×22, DRAGOONER×20, MOTORBIKE×21, SAMURAI×21, DRAGOONER×18, DRAGOONER×18, DRAGOONER×18, CARGO×24, NINJA×16, THE_KING×10, CRUSADER×21, MUSKETEER×24 |
| 🟥 | Grumpy Marauders | random | Renaissance 77%, Medieval 23% | ⬛ 0/10 (0%) | MUSKETEER×10 | CARGO×24, MUSKETEER×19, CARGO×18, KNIGHT×21, MUSKETEER×25, CONDOTTERI×19, CARGO×18, DRAGOONER×22, CRUSADER×25, DRAGOONER×18, NINJA×21, THE_KING×10, CARGO×24, DRAGOONER×22 |
| 🟥 | Weary Plunderers | random | Renaissance 70%, Medieval 19%, Industrial 11% | ⬛ 0/10 (0%) | SOLDIER×10 | CARGO×18, KNIGHT×18, CARGO×21, SOLDIER×17, MUSKETEER×23, CARGO×18, CRUSADER×21, NINJA×26, SOLDIER×17, MUSKETEER×24, SAMURAI×21, MUSKETEER×20, MUSKETEER×25, DRAGOONER×20, THE_KING×10, MUSKETEER×18 |
| 🟥 | Frenzied Pillagers | random | Renaissance 73%, Medieval 14%, Industrial 13% | ⬛ 0/10 (0%) | MOTORBIKE×3, MUSKETEER×1 | DRAGOONER×18, MUSKETEER×21, NINJA×19, CONDOTTERI×24, MUSKETEER×25, MOTORBIKE×17, DRAGOONER×22, KNIGHT×21, MUSKETEER×17, MUSKETEER×20, MUSKETEER×24, THE_KING×10, SMALL_TANK×26, DRAGOONER×22, MUSKETEER×22, CARGO×21 |
| 🟩 | Reckless Looters | random | Renaissance 88%, Industrial 12% | 🟡 6/10 (60%) | MOTORBIKE×1, MUSKETEER×1 | DRAGOONER×24, MOTORBIKE×19, MUSKETEER×21, NINJA×25, MOTORBIKE×18, CARGO×18, THE_KING×10, NINJA×17, MUSKETEER×20, DRAGOONER×22, MUSKETEER×17, DRAGOONER×22, DRAGOONER×24, CARGO×18, MUSKETEER×25 |
| 🟩 | Forgotten Warband | random | Renaissance 93%, Medieval 7% | 🟢 9/10 (90%) | MUSKETEER×1 | NINJA×17, NINJA×20, DRAGOONER×20, DRAGOONER×22, MUSKETEER×17, NINJA×22, NINJA×19, SAMURAI×23, NINJA×16, DRAGOONER×20, MUSKETEER×25, THE_KING×10, MUSKETEER×23, DRAGOONER×24, MUSKETEER×18, DRAGOONER×24 |
| 🟥 | Blundering Invaders | random | Renaissance 81%, Industrial 13%, Medieval 6% | ⬛ 0/10 (0%) | SOLDIER×8, MUSKETEER×2 | CARGO×24, SOLDIER×22, MUSKETEER×23, KNIGHT×18, MUSKETEER×24, SOLDIER×18, THE_KING×10, CARGO×15, MUSKETEER×26, MUSKETEER×25, NINJA×19, DRAGOONER×24, NINJA×18, MUSKETEER×17, NINJA×22 |
| 🟥 | Rude Barbarians | random | Renaissance 86%, Industrial 8%, Medieval 7% | ⬛ 0/10 (0%) | SMALL_TANK×5 | THE_KING×10, NINJA×16, MUSKETEER×16, NINJA×17, NINJA×20, DRAGOONER×18, MUSKETEER×18, SMALL_TANK×20, DRAGOONER×26, NINJA×17, CONDOTTERI×17, MUSKETEER×18, CARGO×27, CARGO×21 |
| 🟥 | Clumsy Attackers | random | Renaissance 82%, Industrial 18% | ⬛ 0/10 (0%) | MUSKETEER×5, THE_KING×1 | DRAGOONER×24, NINJA×19, CARGO×21, DRAGOONER×24, CARGO×24, THE_KING×10, NINJA×25, MUSKETEER×20, SOLDIER×16, TRANSPORTER×20, MUSKETEER×16, DRAGOONER×20, CARGO×18, TRANSPORTER×20, MUSKETEER×20, MUSKETEER×21 |
| 🟥 | Hungry Invaders | random | Renaissance 88%, Industrial 12% | ⬛ 0/10 (0%) | SOLDIER×9, MUSKETEER×1 | DRAGOONER×20, MUSKETEER×21, NINJA×17, DRAGOONER×22, MUSKETEER×22, CARGO×18, NINJA×18, THE_KING×10, DRAGOONER×24, MUSKETEER×23, MUSKETEER×21, DRAGOONER×22, SOLDIER×24, CARGO×18, SMALL_TANK×16, NINJA×24 |
| 🟥 | Clumsy Attackers | random | Renaissance 74%, Industrial 13%, Medieval 13% | ⬛ 0/10 (0%) | SOLDIER×7, MUSKETEER×3 | MUSKETEER×21, NINJA×21, CARGO×21, CARGO×24, DRAGOONER×18, THE_KING×10, NINJA×24, KNIGHT×21, TRANSPORTER×20, CARGO×21, DRAGOONER×18, KNIGHT×18, NINJA×25, NINJA×21, MOTORBIKE×20 |
| 🟩 | Clumsy Attackers | random | Renaissance 83%, Industrial 9%, Medieval 9% | 🟡 5/10 (50%) | MUSKETEER×3, NINJA×1 | CRUSADER×25, DRAGOONER×24, CARGO×18, DRAGOONER×20, MUSKETEER×22, NINJA×22, NINJA×17, DRAGOONER×26, NINJA×21, MUSKETEER×18, MUSKETEER×21, NINJA×23, THE_KING×10, MOTORBIKE×26 |

### Industrial

#### Flame/Gatling

| Tower Era Distribution (35 towers) | Towers |
|---|---|
| Industrial 91% (32), Iron Age 9% (3) | FLAME_THROWER×16, GATLING_TOWER×16, COLD_TOWER×3 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟥 | Industrial March | hardcoded | Industrial 98%, Modern 2% | ⬛ 0/28 (0%) | SOLDIER×24, SMALL_TANK×2 | SOLDIER×16, SOLDIER×17, MOTORBIKE×17, TRANSPORTER×18, TRANSPORTER×19, SMALL_TANK×19, TRANSPORTER×20, TRANSPORTER×21, SMALL_TANK×21, SMALL_TANK×22, MOTORBIKE×23, MOTORBIKE×23, SPECOPS×10, MOTORBIKE×28, SMALL_TANK×30, SOLDIER×32, SOLDIER×34, TRANSPORTER×36, TRANSPORTER×38, TRANSPORTER×40, MOTORBIKE×36 |
| 🟩 | Mechanized Strike | hardcoded | Industrial 100% | 🟠 10/28 (36%) | SOLDIER×18 | SOLDIER×18, SMALL_TANK×19, TRANSPORTER×19, SMALL_TANK×20, TRANSPORTER×21, SMALL_TANK×21, SOLDIER×22, SOLDIER×22, TRANSPORTER×23, MOTORBIKE×24, SMALL_TANK×24, MOTORBIKE×25, TRANSPORTER×26, TRANSPORTER×26, SOLDIER×27, SOLDIER×27, SMALL_TANK×28, SMALL_TANK×29, SMALL_TANK×29, TRANSPORTER×30, MOTORBIKE×34, SMALL_TANK×35, SOLDIER×35 |
| 🟥 | Steam Assault | hardcoded | Industrial 100% | ⬛ 0/28 (0%) | SOLDIER×28 | TRANSPORTER×18, SOLDIER×19, SOLDIER×19, SMALL_TANK×20, TRANSPORTER×21, SOLDIER×21, SOLDIER×22, SMALL_TANK×22, TRANSPORTER×23, SMALL_TANK×24, TRANSPORTER×24, SMALL_TANK×25, SOLDIER×26, TRANSPORTER×26, SMALL_TANK×27, MOTORBIKE×27, SOLDIER×28, TRANSPORTER×29, SOLDIER×29, MOTORBIKE×30, SMALL_TANK×33, TRANSPORTER×35, TRANSPORTER×37 |
| 🟥 | Tank Column | hardcoded | Industrial 100% | ⬛ 0/28 (0%) | SOLDIER×28 | SMALL_TANK×18, MOTORBIKE×19, MOTORBIKE×19, TRANSPORTER×20, TRANSPORTER×21, TRANSPORTER×21, SOLDIER×22, MOTORBIKE×22, TRANSPORTER×23, TRANSPORTER×24, SMALL_TANK×24, MOTORBIKE×25, TRANSPORTER×26, SMALL_TANK×26, TRANSPORTER×27, SMALL_TANK×27, TRANSPORTER×28, MOTORBIKE×29, MOTORBIKE×29, SOLDIER×30, SOLDIER×34, SOLDIER×36, TRANSPORTER×38, SOLDIER×34 |
| 🟩 | Factory Raid | hardcoded | Industrial 88%, Renaissance 10%, Modern 2% | 🟠 6/28 (21%) | SOLDIER×21, MUSKETEER×1 | MOTORBIKE×18, MOTORBIKE×20, MOTORBIKE×20, MOTORBIKE×22, SOLDIER×20, TRANSPORTER×21, MOTORBIKE×22, SMALL_TANK×22, SMALL_TANK×25, SOLDIER×24, MOTORBIKE×24, TRANSPORTER×25, SMALL_TANK×26, SMALL_TANK×28, MOTORBIKE×30, CARGO×30, TRANSPORTER×32, DRAGOONER×34, HELI×13, TRANSPORTER×38, SMALL_TANK×38, SOLDIER×36, SMALL_TANK×33, SMALL_TANK×36 |
| 🟩 | Reckless Looters | random | Industrial 88%, Renaissance 7%, Modern 4% | 🟠 13/28 (46%) | SOLDIER×15 | TRANSPORTER×20, SOLDIER×25, TRANSPORTER×20, SMALL_TANK×28, TRANSPORTER×20, TRANSPORTER×30, SOLDIER×19, MOTORBIKE×26, MUSKETEER×29, SOLDIER×24, MOTORBIKE×27, SOLDIER×28, MOTORBIKE×21, THE_GENERAL×18, SMALL_TANK×24, SOLDIER×27, MOTORBIKE×20 |
| 🟩 | Reckless Looters | random | Industrial 88%, Renaissance 7%, Modern 4% | 🟠 13/28 (46%) | SOLDIER×15 | TRANSPORTER×20, SOLDIER×25, TRANSPORTER×20, SMALL_TANK×28, TRANSPORTER×20, TRANSPORTER×30, SOLDIER×19, MOTORBIKE×26, MUSKETEER×29, SOLDIER×24, MOTORBIKE×27, SOLDIER×28, MOTORBIKE×21, THE_GENERAL×18, SMALL_TANK×24, SOLDIER×27, MOTORBIKE×20 |
| 🟩 | Reckless Looters | random | Industrial 93%, Renaissance 7% | 🟠 11/28 (39%) | SOLDIER×17 | SOLDIER×29, MOTORBIKE×32, MOTORBIKE×29, SOLDIER×20, SOLDIER×24, SOLDIER×31, SOLDIER×18, MUSKETEER×19, SOLDIER×27, SMALL_TANK×24, TRANSPORTER×30, TRANSPORTER×20, MOTORBIKE×19, SOLDIER×25, SMALL_TANK×30, SMALL_TANK×32, THE_KING×10 |
| 🟩 | Stubborn Raiders | random | Industrial 92%, Modern 6%, Renaissance 2% | 🟡 15/28 (54%) | SOLDIER×13 | SIEGE_TANK×24, MOTORBIKE×25, THE_KING×10, SMALL_TANK×26, MOTORBIKE×29, TRANSPORTER×20, SOLDIER×22, SMALL_TANK×20, SOLDIER×28, SMALL_TANK×20, SOLDIER×29, TRANSPORTER×20, SMALL_TANK×22, MOTORBIKE×31, SOLDIER×30, TRANSPORTER×30, MOTORBIKE×28 |
| 🟩 | Shrieking Horde | random | Industrial 91%, Renaissance 9% | 🔴 3/28 (11%) | SOLDIER×25 | MOTORBIKE×28, SMALL_TANK×28, MOTORBIKE×23, SMALL_TANK×24, SOLDIER×29, MUSKETEER×23, SOLDIER×21, TRANSPORTER×20, TRANSPORTER×30, SMALL_TANK×20, SMALL_TANK×28, MOTORBIKE×24, MUSKETEER×19, SOLDIER×25, TRANSPORTER×30, TRANSPORTER×30, MOTORBIKE×28, TRANSPORTER×30 |
| 🟩 | Restless Horde | random | Industrial 80%, Renaissance 20% | 🟢 25/28 (89%) | SOLDIER×3 | SOLDIER×25, SMALL_TANK×22, MUSKETEER×32, SMALL_TANK×20, MUSKETEER×23, CARGO×21, MOTORBIKE×31, SMALL_TANK×28, SOLDIER×25, SMALL_TANK×28, MOTORBIKE×29, SOLDIER×29, MOTORBIKE×31, TRANSPORTER×20, SOLDIER×22, THE_KING×10, SOLDIER×29 |
| 🟥 | Ragged Warband | random | Industrial 91%, Renaissance 5%, Modern 4% | ⬛ 0/28 (0%) | SOLDIER×17, THE_GENERAL×1 | MOTORBIKE×18, SOLDIER×26, SOLDIER×31, TRANSPORTER×30, SMALL_TANK×20, SOLDIER×18, NINJA×21, THE_GENERAL×18, TRANSPORTER×30, SOLDIER×24, TRANSPORTER×20, TRANSPORTER×30, MOTORBIKE×24, TRANSPORTER×30, SOLDIER×32, TRANSPORTER×20, TRANSPORTER×30 |
| 🟥 | Disorganized Mob | random | Industrial 81%, Modern 13%, Renaissance 6% | ⬛ 0/28 (0%) | SPECOPS×14 | MOTORBIKE×22, SOLDIER×29, DRAGOONER×20, SMALL_TANK×22, SMALL_TANK×20, SPECOPS×27, SMALL_TANK×22, SOLDIER×26, MOTORBIKE×25, SMALL_TANK×26, TRANSPORTER×20, MOTORBIKE×26, TRANSPORTER×20, THE_GENERAL×18, SOLDIER×20 |
| 🟩 | Petty Bandits | random | Industrial 82%, Renaissance 18% | 🟡 17/28 (61%) | SOLDIER×11 | SOLDIER×25, MOTORBIKE×29, SOLDIER×20, SOLDIER×20, SOLDIER×26, MOTORBIKE×29, SMALL_TANK×26, CARGO×24, SOLDIER×25, MUSKETEER×20, MOTORBIKE×23, SOLDIER×26, TRANSPORTER×30, MUSKETEER×22, TRANSPORTER×20 |
| 🟩 | Crude Invaders | random | Industrial 79%, Renaissance 21% | 🟠 7/28 (25%) | SOLDIER×21 | SMALL_TANK×22, SMALL_TANK×26, SMALL_TANK×22, NINJA×19, MOTORBIKE×25, TRANSPORTER×30, MUSKETEER×25, THE_KING×10, SOLDIER×27, SMALL_TANK×28, TRANSPORTER×20, TRANSPORTER×30, TRANSPORTER×20, MOTORBIKE×30, CARGO×21 |
| 🟩 | Forgotten Warband | random | Industrial 70%, Renaissance 19%, Modern 11% | 🟡 18/28 (64%) | SOLDIER×10 | SIEGE_TANK×20, MOTORBIKE×24, NINJA×23, TRANSPORTER×30, SIEGE_TANK×20, TRANSPORTER×20, MUSKETEER×19, THE_KING×10, SOLDIER×18, SMALL_TANK×26, SOLDIER×23, MOTORBIKE×21, MOTORBIKE×22, SOLDIER×23, TRANSPORTER×20, TRANSPORTER×30, MUSKETEER×19 |
| 🟩 | Forgotten Warband | random | Industrial 79%, Renaissance 16%, Modern 5% | 🟠 12/28 (43%) | SOLDIER×16 | SIEGE_TANK×20, TRANSPORTER×30, SOLDIER×20, TRANSPORTER×20, SMALL_TANK×26, DRAGOONER×31, MOTORBIKE×24, SMALL_TANK×30, MOTORBIKE×25, DRAGOONER×22, SOLDIER×26, SMALL_TANK×20, SMALL_TANK×24, THE_KING×10, MOTORBIKE×26, SMALL_TANK×28, TRANSPORTER×20 |
| 🟥 | Drunken Raiders | random | Industrial 90%, Modern 7%, Renaissance 3% | ⬛ 0/28 (0%) | SPECOPS×15, SOLDIER×1 | SMALL_TANK×26, THE_KING×10, TRANSPORTER×20, SMALL_TANK×26, SMALL_TANK×28, MOTORBIKE×21, SOLDIER×22, SOLDIER×24, TRANSPORTER×20, SOLDIER×28, SOLDIER×22, MOTORBIKE×23, SMALL_TANK×18, SPECOPS×27, TRANSPORTER×30, TRANSPORTER×20 |
| 🟩 | Unlucky Raiders | random | Industrial 89%, Renaissance 11% | 🟡 21/28 (75%) | SOLDIER×7 | SOLDIER×26, SMALL_TANK×24, NINJA×22, MOTORBIKE×26, TRANSPORTER×30, SMALL_TANK×22, DRAGOONER×22, TRANSPORTER×20, MOTORBIKE×19, SOLDIER×28, SOLDIER×22, TRANSPORTER×20, MOTORBIKE×26, SOLDIER×19, SMALL_TANK×20, SOLDIER×19, MOTORBIKE×19 |
| 🟥 | Angry Mob | random | Industrial 85%, Renaissance 9%, Modern 6% | ⬛ 0/28 (0%) | SPECOPS×12, SOLDIER×4 | MOTORBIKE×27, SOLDIER×20, MOTORBIKE×24, SOLDIER×19, TRANSPORTER×20, TRANSPORTER×20, SPECOPS×22, SMALL_TANK×22, SOLDIER×29, SOLDIER×31, DRAGOONER×22, TRANSPORTER×20, TRANSPORTER×30, TRANSPORTER×20, THE_KING×10, MOTORBIKE×21 |
| 🟥 | Angry Mob | random | Industrial 83%, Renaissance 9%, Modern 8% | ⬛ 0/28 (0%) | SPECOPS×11, SOLDIER×7 | SOLDIER×24, TRANSPORTER×30, MOTORBIKE×19, DRAGOONER×22, MOTORBIKE×19, MOTORBIKE×23, MOTORBIKE×18, SMALL_TANK×22, THE_KING×10, MOTORBIKE×21, SOLDIER×29, SPECOPS×26, TRANSPORTER×20, SOLDIER×25, SMALL_TANK×32 |
| 🟥 | Shrieking Horde | random | Industrial 85%, Modern 12%, Renaissance 2% | ⬛ 0/28 (0%) | SOLDIER×22, HELI×2 | TRANSPORTER×20, SMALL_TANK×20, SOLDIER×22, HELI×26, MOTORBIKE×23, TRANSPORTER×20, TRANSPORTER×20, SOLDIER×28, SOLDIER×31, SOLDIER×30, MOTORBIKE×30, HELI×24, THE_KING×10, MOTORBIKE×26, SMALL_TANK×30, TRANSPORTER×20, MOTORBIKE×27 |
| 🟩 | Reckless Looters | random | Industrial 91%, Renaissance 5%, Modern 5% | 🟢 28/28 (100%) |  | SMALL_TANK×30, CARGO×18, MOTORBIKE×24, MOTORBIKE×21, SOLDIER×21, SOLDIER×30, SMALL_TANK×26, SMALL_TANK×22, SMALL_TANK×26, MOTORBIKE×28, SOLDIER×19, SMALL_TANK×26, THE_GENERAL×18, SMALL_TANK×22, MOTORBIKE×19, TRANSPORTER×20, SOLDIER×27 |
| 🟩 | Noisy Barbarians | random | Industrial 72%, Renaissance 20%, Modern 7% | 🟡 16/28 (57%) | SOLDIER×12 | MOTORBIKE×20, SOLDIER×29, SMALL_TANK×20, SMALL_TANK×30, NINJA×31, SOLDIER×20, SMALL_TANK×24, SOLDIER×31, SIEGE_TANK×30, SMALL_TANK×28, MOTORBIKE×27, TRANSPORTER×20, SMALL_TANK×20, NINJA×29, TRANSPORTER×20, NINJA×22 |
| 🟥 | Frenzied Pillagers | random | Industrial 80%, Renaissance 14%, Modern 6% | ⬛ 0/28 (0%) | SPECOPS×10, SOLDIER×8 | MOTORBIKE×26, SOLDIER×19, CARGO×30, SMALL_TANK×28, MOTORBIKE×26, MOTORBIKE×27, SMALL_TANK×26, SOLDIER×27, TRANSPORTER×20, SOLDIER×19, SPECOPS×20, TRANSPORTER×30, MOTORBIKE×20, CARGO×21, TRANSPORTER×20 |

#### Indy / Renaissance

| Tower Era Distribution (28 towers) | Towers |
|---|---|
| Renaissance 46% (13), Industrial 46% (13), Iron Age 7% (2) | RIFLE_TOWER×10, FLAME_THROWER×8, GATLING_TOWER×5, ICE_TOWER×3, COLD_TOWER×2 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟥 | Industrial March | hardcoded | Industrial 98%, Modern 2% | ⬛ 0/16 (0%) | SPECOPS×6, SOLDIER×4 | SOLDIER×16, SOLDIER×17, MOTORBIKE×17, TRANSPORTER×18, TRANSPORTER×19, SMALL_TANK×19, TRANSPORTER×20, TRANSPORTER×21, SMALL_TANK×21, SMALL_TANK×22, MOTORBIKE×23, MOTORBIKE×23, SPECOPS×10, MOTORBIKE×28, SMALL_TANK×30, SOLDIER×32, SOLDIER×34, TRANSPORTER×36, TRANSPORTER×38, TRANSPORTER×40, MOTORBIKE×36 |
| 🟥 | Mechanized Strike | hardcoded | Industrial 100% | ⬛ 0/16 (0%) | SOLDIER×16 | SOLDIER×18, SMALL_TANK×19, TRANSPORTER×19, SMALL_TANK×20, TRANSPORTER×21, SMALL_TANK×21, SOLDIER×22, SOLDIER×22, TRANSPORTER×23, MOTORBIKE×24, SMALL_TANK×24, MOTORBIKE×25, TRANSPORTER×26, TRANSPORTER×26, SOLDIER×27, SOLDIER×27, SMALL_TANK×28, SMALL_TANK×29, SMALL_TANK×29, TRANSPORTER×30, MOTORBIKE×34, SMALL_TANK×35, SOLDIER×35 |
| 🟥 | Steam Assault | hardcoded | Industrial 100% | ⬛ 0/16 (0%) | SOLDIER×16 | TRANSPORTER×18, SOLDIER×19, SOLDIER×19, SMALL_TANK×20, TRANSPORTER×21, SOLDIER×21, SOLDIER×22, SMALL_TANK×22, TRANSPORTER×23, SMALL_TANK×24, TRANSPORTER×24, SMALL_TANK×25, SOLDIER×26, TRANSPORTER×26, SMALL_TANK×27, MOTORBIKE×27, SOLDIER×28, TRANSPORTER×29, SOLDIER×29, MOTORBIKE×30, SMALL_TANK×33, TRANSPORTER×35, TRANSPORTER×37 |
| 🟥 | Tank Column | hardcoded | Industrial 100% | ⬛ 0/16 (0%) | SOLDIER×16 | SMALL_TANK×18, MOTORBIKE×19, MOTORBIKE×19, TRANSPORTER×20, TRANSPORTER×21, TRANSPORTER×21, SOLDIER×22, MOTORBIKE×22, TRANSPORTER×23, TRANSPORTER×24, SMALL_TANK×24, MOTORBIKE×25, TRANSPORTER×26, SMALL_TANK×26, TRANSPORTER×27, SMALL_TANK×27, TRANSPORTER×28, MOTORBIKE×29, MOTORBIKE×29, SOLDIER×30, SOLDIER×34, SOLDIER×36, TRANSPORTER×38, SOLDIER×34 |
| 🟥 | Factory Raid | hardcoded | Industrial 88%, Renaissance 10%, Modern 2% | ⬛ 0/16 (0%) | SOLDIER×14, HELI×1 | MOTORBIKE×18, MOTORBIKE×20, MOTORBIKE×20, MOTORBIKE×22, SOLDIER×20, TRANSPORTER×21, MOTORBIKE×22, SMALL_TANK×22, SMALL_TANK×25, SOLDIER×24, MOTORBIKE×24, TRANSPORTER×25, SMALL_TANK×26, SMALL_TANK×28, MOTORBIKE×30, CARGO×30, TRANSPORTER×32, DRAGOONER×34, HELI×13, TRANSPORTER×38, SMALL_TANK×38, SOLDIER×36, SMALL_TANK×33, SMALL_TANK×36 |
| 🟥 | Reckless Looters | random | Industrial 88%, Renaissance 7%, Modern 4% | ⬛ 0/16 (0%) | SOLDIER×10, MOTORBIKE×3 | TRANSPORTER×20, SOLDIER×25, TRANSPORTER×20, SMALL_TANK×28, TRANSPORTER×20, TRANSPORTER×30, SOLDIER×19, MOTORBIKE×26, MUSKETEER×29, SOLDIER×24, MOTORBIKE×27, SOLDIER×28, MOTORBIKE×21, THE_GENERAL×18, SMALL_TANK×24, SOLDIER×27, MOTORBIKE×20 |
| 🟥 | Reckless Looters | random | Industrial 88%, Renaissance 7%, Modern 4% | ⬛ 0/16 (0%) | SOLDIER×10, MOTORBIKE×3 | TRANSPORTER×20, SOLDIER×25, TRANSPORTER×20, SMALL_TANK×28, TRANSPORTER×20, TRANSPORTER×30, SOLDIER×19, MOTORBIKE×26, MUSKETEER×29, SOLDIER×24, MOTORBIKE×27, SOLDIER×28, MOTORBIKE×21, THE_GENERAL×18, SMALL_TANK×24, SOLDIER×27, MOTORBIKE×20 |
| 🟥 | Reckless Looters | random | Industrial 93%, Renaissance 7% | ⬛ 0/16 (0%) | SOLDIER×10, MOTORBIKE×2 | SOLDIER×29, MOTORBIKE×32, MOTORBIKE×29, SOLDIER×20, SOLDIER×24, SOLDIER×31, SOLDIER×18, MUSKETEER×19, SOLDIER×27, SMALL_TANK×24, TRANSPORTER×30, TRANSPORTER×20, MOTORBIKE×19, SOLDIER×25, SMALL_TANK×30, SMALL_TANK×32, THE_KING×10 |
| 🟥 | Stubborn Raiders | random | Industrial 92%, Modern 6%, Renaissance 2% | ⬛ 0/16 (0%) | SOLDIER×16 | SIEGE_TANK×24, MOTORBIKE×25, THE_KING×10, SMALL_TANK×26, MOTORBIKE×29, TRANSPORTER×20, SOLDIER×22, SMALL_TANK×20, SOLDIER×28, SMALL_TANK×20, SOLDIER×29, TRANSPORTER×20, SMALL_TANK×22, MOTORBIKE×31, SOLDIER×30, TRANSPORTER×30, MOTORBIKE×28 |
| 🟥 | Shrieking Horde | random | Industrial 91%, Renaissance 9% | ⬛ 0/16 (0%) | SOLDIER×16 | MOTORBIKE×28, SMALL_TANK×28, MOTORBIKE×23, SMALL_TANK×24, SOLDIER×29, MUSKETEER×23, SOLDIER×21, TRANSPORTER×20, TRANSPORTER×30, SMALL_TANK×20, SMALL_TANK×28, MOTORBIKE×24, MUSKETEER×19, SOLDIER×25, TRANSPORTER×30, TRANSPORTER×30, MOTORBIKE×28, TRANSPORTER×30 |
| 🟥 | Restless Horde | random | Industrial 80%, Renaissance 20% | ⬛ 0/16 (0%) | SOLDIER×13, MOTORBIKE×1 | SOLDIER×25, SMALL_TANK×22, MUSKETEER×32, SMALL_TANK×20, MUSKETEER×23, CARGO×21, MOTORBIKE×31, SMALL_TANK×28, SOLDIER×25, SMALL_TANK×28, MOTORBIKE×29, SOLDIER×29, MOTORBIKE×31, TRANSPORTER×20, SOLDIER×22, THE_KING×10, SOLDIER×29 |
| 🟥 | Ragged Warband | random | Industrial 91%, Renaissance 5%, Modern 4% | ⬛ 0/16 (0%) | SOLDIER×16 | MOTORBIKE×18, SOLDIER×26, SOLDIER×31, TRANSPORTER×30, SMALL_TANK×20, SOLDIER×18, NINJA×21, THE_GENERAL×18, TRANSPORTER×30, SOLDIER×24, TRANSPORTER×20, TRANSPORTER×30, MOTORBIKE×24, TRANSPORTER×30, SOLDIER×32, TRANSPORTER×20, TRANSPORTER×30 |
| 🟥 | Disorganized Mob | random | Industrial 81%, Modern 13%, Renaissance 6% | ⬛ 0/16 (0%) | SPECOPS×7, SOLDIER×2 | MOTORBIKE×22, SOLDIER×29, DRAGOONER×20, SMALL_TANK×22, SMALL_TANK×20, SPECOPS×27, SMALL_TANK×22, SOLDIER×26, MOTORBIKE×25, SMALL_TANK×26, TRANSPORTER×20, MOTORBIKE×26, TRANSPORTER×20, THE_GENERAL×18, SOLDIER×20 |
| 🟥 | Petty Bandits | random | Industrial 82%, Renaissance 18% | ⬛ 0/16 (0%) | SOLDIER×13, MOTORBIKE×1 | SOLDIER×25, MOTORBIKE×29, SOLDIER×20, SOLDIER×20, SOLDIER×26, MOTORBIKE×29, SMALL_TANK×26, CARGO×24, SOLDIER×25, MUSKETEER×20, MOTORBIKE×23, SOLDIER×26, TRANSPORTER×30, MUSKETEER×22, TRANSPORTER×20 |
| 🟥 | Crude Invaders | random | Industrial 79%, Renaissance 21% | ⬛ 0/16 (0%) | SOLDIER×16 | SMALL_TANK×22, SMALL_TANK×26, SMALL_TANK×22, NINJA×19, MOTORBIKE×25, TRANSPORTER×30, MUSKETEER×25, THE_KING×10, SOLDIER×27, SMALL_TANK×28, TRANSPORTER×20, TRANSPORTER×30, TRANSPORTER×20, MOTORBIKE×30, CARGO×21 |
| 🟥 | Forgotten Warband | random | Industrial 70%, Renaissance 19%, Modern 11% | ⬛ 0/16 (0%) | SOLDIER×16 | SIEGE_TANK×20, MOTORBIKE×24, NINJA×23, TRANSPORTER×30, SIEGE_TANK×20, TRANSPORTER×20, MUSKETEER×19, THE_KING×10, SOLDIER×18, SMALL_TANK×26, SOLDIER×23, MOTORBIKE×21, MOTORBIKE×22, SOLDIER×23, TRANSPORTER×20, TRANSPORTER×30, MUSKETEER×19 |
| 🟥 | Forgotten Warband | random | Industrial 79%, Renaissance 16%, Modern 5% | ⬛ 0/16 (0%) | SOLDIER×16 | SIEGE_TANK×20, TRANSPORTER×30, SOLDIER×20, TRANSPORTER×20, SMALL_TANK×26, DRAGOONER×31, MOTORBIKE×24, SMALL_TANK×30, MOTORBIKE×25, DRAGOONER×22, SOLDIER×26, SMALL_TANK×20, SMALL_TANK×24, THE_KING×10, MOTORBIKE×26, SMALL_TANK×28, TRANSPORTER×20 |
| 🟥 | Drunken Raiders | random | Industrial 90%, Modern 7%, Renaissance 3% | ⬛ 0/16 (0%) | SOLDIER×16 | SMALL_TANK×26, THE_KING×10, TRANSPORTER×20, SMALL_TANK×26, SMALL_TANK×28, MOTORBIKE×21, SOLDIER×22, SOLDIER×24, TRANSPORTER×20, SOLDIER×28, SOLDIER×22, MOTORBIKE×23, SMALL_TANK×18, SPECOPS×27, TRANSPORTER×30, TRANSPORTER×20 |
| 🟥 | Unlucky Raiders | random | Industrial 89%, Renaissance 11% | ⬛ 0/16 (0%) | SOLDIER×16 | SOLDIER×26, SMALL_TANK×24, NINJA×22, MOTORBIKE×26, TRANSPORTER×30, SMALL_TANK×22, DRAGOONER×22, TRANSPORTER×20, MOTORBIKE×19, SOLDIER×28, SOLDIER×22, TRANSPORTER×20, MOTORBIKE×26, SOLDIER×19, SMALL_TANK×20, SOLDIER×19, MOTORBIKE×19 |
| 🟥 | Angry Mob | random | Industrial 85%, Renaissance 9%, Modern 6% | ⬛ 0/16 (0%) | SPECOPS×6, SOLDIER×5 | MOTORBIKE×27, SOLDIER×20, MOTORBIKE×24, SOLDIER×19, TRANSPORTER×20, TRANSPORTER×20, SPECOPS×22, SMALL_TANK×22, SOLDIER×29, SOLDIER×31, DRAGOONER×22, TRANSPORTER×20, TRANSPORTER×30, TRANSPORTER×20, THE_KING×10, MOTORBIKE×21 |
| 🟥 | Angry Mob | random | Industrial 83%, Renaissance 9%, Modern 8% | ⬛ 0/16 (0%) | SOLDIER×14, SPECOPS×2 | SOLDIER×24, TRANSPORTER×30, MOTORBIKE×19, DRAGOONER×22, MOTORBIKE×19, MOTORBIKE×23, MOTORBIKE×18, SMALL_TANK×22, THE_KING×10, MOTORBIKE×21, SOLDIER×29, SPECOPS×26, TRANSPORTER×20, SOLDIER×25, SMALL_TANK×32 |
| 🟥 | Shrieking Horde | random | Industrial 85%, Modern 12%, Renaissance 2% | ⬛ 0/16 (0%) | SOLDIER×10, HELI×2 | TRANSPORTER×20, SMALL_TANK×20, SOLDIER×22, HELI×26, MOTORBIKE×23, TRANSPORTER×20, TRANSPORTER×20, SOLDIER×28, SOLDIER×31, SOLDIER×30, MOTORBIKE×30, HELI×24, THE_KING×10, MOTORBIKE×26, SMALL_TANK×30, TRANSPORTER×20, MOTORBIKE×27 |
| 🟥 | Reckless Looters | random | Industrial 91%, Renaissance 5%, Modern 5% | ⬛ 0/16 (0%) | SOLDIER×16 | SMALL_TANK×30, CARGO×18, MOTORBIKE×24, MOTORBIKE×21, SOLDIER×21, SOLDIER×30, SMALL_TANK×26, SMALL_TANK×22, SMALL_TANK×26, MOTORBIKE×28, SOLDIER×19, SMALL_TANK×26, THE_GENERAL×18, SMALL_TANK×22, MOTORBIKE×19, TRANSPORTER×20, SOLDIER×27 |
| 🟥 | Noisy Barbarians | random | Industrial 72%, Renaissance 20%, Modern 7% | ⬛ 0/16 (0%) | SOLDIER×16 | MOTORBIKE×20, SOLDIER×29, SMALL_TANK×20, SMALL_TANK×30, NINJA×31, SOLDIER×20, SMALL_TANK×24, SOLDIER×31, SIEGE_TANK×30, SMALL_TANK×28, MOTORBIKE×27, TRANSPORTER×20, SMALL_TANK×20, NINJA×29, TRANSPORTER×20, NINJA×22 |
| 🟥 | Frenzied Pillagers | random | Industrial 80%, Renaissance 14%, Modern 6% | ⬛ 0/16 (0%) | SOLDIER×16 | MOTORBIKE×26, SOLDIER×19, CARGO×30, SMALL_TANK×28, MOTORBIKE×26, MOTORBIKE×27, SMALL_TANK×26, SOLDIER×27, TRANSPORTER×20, SOLDIER×19, SPECOPS×20, TRANSPORTER×30, MOTORBIKE×20, CARGO×21, TRANSPORTER×20 |

#### Full Gatling

| Tower Era Distribution (60 towers) | Towers |
|---|---|
| Industrial 82% (49), Renaissance 17% (10), Iron Age 2% (1) | GATLING_TOWER×42, ICE_TOWER×10, FLAME_THROWER×4, SHOCK_TOWER×3, COLD_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Industrial March | hardcoded | Industrial 98%, Modern 2% | 🟢 58/58 (100%) |  | SOLDIER×16, SOLDIER×17, MOTORBIKE×17, TRANSPORTER×18, TRANSPORTER×19, SMALL_TANK×19, TRANSPORTER×20, TRANSPORTER×21, SMALL_TANK×21, SMALL_TANK×22, MOTORBIKE×23, MOTORBIKE×23, SPECOPS×10, MOTORBIKE×28, SMALL_TANK×30, SOLDIER×32, SOLDIER×34, TRANSPORTER×36, TRANSPORTER×38, TRANSPORTER×40, MOTORBIKE×36 |
| 🟩 | Mechanized Strike | hardcoded | Industrial 100% | 🟢 49/58 (84%) | SOLDIER×9 | SOLDIER×18, SMALL_TANK×19, TRANSPORTER×19, SMALL_TANK×20, TRANSPORTER×21, SMALL_TANK×21, SOLDIER×22, SOLDIER×22, TRANSPORTER×23, MOTORBIKE×24, SMALL_TANK×24, MOTORBIKE×25, TRANSPORTER×26, TRANSPORTER×26, SOLDIER×27, SOLDIER×27, SMALL_TANK×28, SMALL_TANK×29, SMALL_TANK×29, TRANSPORTER×30, MOTORBIKE×34, SMALL_TANK×35, SOLDIER×35 |
| 🟩 | Steam Assault | hardcoded | Industrial 100% | 🟢 58/58 (100%) |  | TRANSPORTER×18, SOLDIER×19, SOLDIER×19, SMALL_TANK×20, TRANSPORTER×21, SOLDIER×21, SOLDIER×22, SMALL_TANK×22, TRANSPORTER×23, SMALL_TANK×24, TRANSPORTER×24, SMALL_TANK×25, SOLDIER×26, TRANSPORTER×26, SMALL_TANK×27, MOTORBIKE×27, SOLDIER×28, TRANSPORTER×29, SOLDIER×29, MOTORBIKE×30, SMALL_TANK×33, TRANSPORTER×35, TRANSPORTER×37 |
| 🟩 | Tank Column | hardcoded | Industrial 100% | 🟢 58/58 (100%) |  | SMALL_TANK×18, MOTORBIKE×19, MOTORBIKE×19, TRANSPORTER×20, TRANSPORTER×21, TRANSPORTER×21, SOLDIER×22, MOTORBIKE×22, TRANSPORTER×23, TRANSPORTER×24, SMALL_TANK×24, MOTORBIKE×25, TRANSPORTER×26, SMALL_TANK×26, TRANSPORTER×27, SMALL_TANK×27, TRANSPORTER×28, MOTORBIKE×29, MOTORBIKE×29, SOLDIER×30, SOLDIER×34, SOLDIER×36, TRANSPORTER×38, SOLDIER×34 |
| 🟩 | Factory Raid | hardcoded | Industrial 88%, Renaissance 10%, Modern 2% | 🟢 58/58 (100%) |  | MOTORBIKE×18, MOTORBIKE×20, MOTORBIKE×20, MOTORBIKE×22, SOLDIER×20, TRANSPORTER×21, MOTORBIKE×22, SMALL_TANK×22, SMALL_TANK×25, SOLDIER×24, MOTORBIKE×24, TRANSPORTER×25, SMALL_TANK×26, SMALL_TANK×28, MOTORBIKE×30, CARGO×30, TRANSPORTER×32, DRAGOONER×34, HELI×13, TRANSPORTER×38, SMALL_TANK×38, SOLDIER×36, SMALL_TANK×33, SMALL_TANK×36 |
| 🟩 | Reckless Looters | random | Industrial 88%, Renaissance 7%, Modern 4% | 🟢 58/58 (100%) |  | TRANSPORTER×20, SOLDIER×25, TRANSPORTER×20, SMALL_TANK×28, TRANSPORTER×20, TRANSPORTER×30, SOLDIER×19, MOTORBIKE×26, MUSKETEER×29, SOLDIER×24, MOTORBIKE×27, SOLDIER×28, MOTORBIKE×21, THE_GENERAL×18, SMALL_TANK×24, SOLDIER×27, MOTORBIKE×20 |
| 🟩 | Reckless Looters | random | Industrial 88%, Renaissance 7%, Modern 4% | 🟢 58/58 (100%) |  | TRANSPORTER×20, SOLDIER×25, TRANSPORTER×20, SMALL_TANK×28, TRANSPORTER×20, TRANSPORTER×30, SOLDIER×19, MOTORBIKE×26, MUSKETEER×29, SOLDIER×24, MOTORBIKE×27, SOLDIER×28, MOTORBIKE×21, THE_GENERAL×18, SMALL_TANK×24, SOLDIER×27, MOTORBIKE×20 |
| 🟩 | Reckless Looters | random | Industrial 93%, Renaissance 7% | 🟢 58/58 (100%) |  | SOLDIER×29, MOTORBIKE×32, MOTORBIKE×29, SOLDIER×20, SOLDIER×24, SOLDIER×31, SOLDIER×18, MUSKETEER×19, SOLDIER×27, SMALL_TANK×24, TRANSPORTER×30, TRANSPORTER×20, MOTORBIKE×19, SOLDIER×25, SMALL_TANK×30, SMALL_TANK×32, THE_KING×10 |
| 🟩 | Stubborn Raiders | random | Industrial 92%, Modern 6%, Renaissance 2% | 🟢 58/58 (100%) |  | SIEGE_TANK×24, MOTORBIKE×25, THE_KING×10, SMALL_TANK×26, MOTORBIKE×29, TRANSPORTER×20, SOLDIER×22, SMALL_TANK×20, SOLDIER×28, SMALL_TANK×20, SOLDIER×29, TRANSPORTER×20, SMALL_TANK×22, MOTORBIKE×31, SOLDIER×30, TRANSPORTER×30, MOTORBIKE×28 |
| 🟩 | Shrieking Horde | random | Industrial 91%, Renaissance 9% | 🟢 58/58 (100%) |  | MOTORBIKE×28, SMALL_TANK×28, MOTORBIKE×23, SMALL_TANK×24, SOLDIER×29, MUSKETEER×23, SOLDIER×21, TRANSPORTER×20, TRANSPORTER×30, SMALL_TANK×20, SMALL_TANK×28, MOTORBIKE×24, MUSKETEER×19, SOLDIER×25, TRANSPORTER×30, TRANSPORTER×30, MOTORBIKE×28, TRANSPORTER×30 |
| 🟩 | Restless Horde | random | Industrial 80%, Renaissance 20% | 🟢 58/58 (100%) |  | SOLDIER×25, SMALL_TANK×22, MUSKETEER×32, SMALL_TANK×20, MUSKETEER×23, CARGO×21, MOTORBIKE×31, SMALL_TANK×28, SOLDIER×25, SMALL_TANK×28, MOTORBIKE×29, SOLDIER×29, MOTORBIKE×31, TRANSPORTER×20, SOLDIER×22, THE_KING×10, SOLDIER×29 |
| 🟩 | Ragged Warband | random | Industrial 91%, Renaissance 5%, Modern 4% | 🟢 58/58 (100%) |  | MOTORBIKE×18, SOLDIER×26, SOLDIER×31, TRANSPORTER×30, SMALL_TANK×20, SOLDIER×18, NINJA×21, THE_GENERAL×18, TRANSPORTER×30, SOLDIER×24, TRANSPORTER×20, TRANSPORTER×30, MOTORBIKE×24, TRANSPORTER×30, SOLDIER×32, TRANSPORTER×20, TRANSPORTER×30 |
| 🟩 | Disorganized Mob | random | Industrial 81%, Modern 13%, Renaissance 6% | 🟡 40/58 (69%) | SPECOPS×9 | MOTORBIKE×22, SOLDIER×29, DRAGOONER×20, SMALL_TANK×22, SMALL_TANK×20, SPECOPS×27, SMALL_TANK×22, SOLDIER×26, MOTORBIKE×25, SMALL_TANK×26, TRANSPORTER×20, MOTORBIKE×26, TRANSPORTER×20, THE_GENERAL×18, SOLDIER×20 |
| 🟩 | Petty Bandits | random | Industrial 82%, Renaissance 18% | 🟢 58/58 (100%) |  | SOLDIER×25, MOTORBIKE×29, SOLDIER×20, SOLDIER×20, SOLDIER×26, MOTORBIKE×29, SMALL_TANK×26, CARGO×24, SOLDIER×25, MUSKETEER×20, MOTORBIKE×23, SOLDIER×26, TRANSPORTER×30, MUSKETEER×22, TRANSPORTER×20 |
| 🟩 | Crude Invaders | random | Industrial 79%, Renaissance 21% | 🟢 58/58 (100%) |  | SMALL_TANK×22, SMALL_TANK×26, SMALL_TANK×22, NINJA×19, MOTORBIKE×25, TRANSPORTER×30, MUSKETEER×25, THE_KING×10, SOLDIER×27, SMALL_TANK×28, TRANSPORTER×20, TRANSPORTER×30, TRANSPORTER×20, MOTORBIKE×30, CARGO×21 |
| 🟩 | Forgotten Warband | random | Industrial 70%, Renaissance 19%, Modern 11% | 🟢 58/58 (100%) |  | SIEGE_TANK×20, MOTORBIKE×24, NINJA×23, TRANSPORTER×30, SIEGE_TANK×20, TRANSPORTER×20, MUSKETEER×19, THE_KING×10, SOLDIER×18, SMALL_TANK×26, SOLDIER×23, MOTORBIKE×21, MOTORBIKE×22, SOLDIER×23, TRANSPORTER×20, TRANSPORTER×30, MUSKETEER×19 |
| 🟩 | Forgotten Warband | random | Industrial 79%, Renaissance 16%, Modern 5% | 🟢 58/58 (100%) |  | SIEGE_TANK×20, TRANSPORTER×30, SOLDIER×20, TRANSPORTER×20, SMALL_TANK×26, DRAGOONER×31, MOTORBIKE×24, SMALL_TANK×30, MOTORBIKE×25, DRAGOONER×22, SOLDIER×26, SMALL_TANK×20, SMALL_TANK×24, THE_KING×10, MOTORBIKE×26, SMALL_TANK×28, TRANSPORTER×20 |
| 🟩 | Drunken Raiders | random | Industrial 90%, Modern 7%, Renaissance 3% | 🟢 50/58 (86%) | SPECOPS×4 | SMALL_TANK×26, THE_KING×10, TRANSPORTER×20, SMALL_TANK×26, SMALL_TANK×28, MOTORBIKE×21, SOLDIER×22, SOLDIER×24, TRANSPORTER×20, SOLDIER×28, SOLDIER×22, MOTORBIKE×23, SMALL_TANK×18, SPECOPS×27, TRANSPORTER×30, TRANSPORTER×20 |
| 🟩 | Unlucky Raiders | random | Industrial 89%, Renaissance 11% | 🟢 58/58 (100%) |  | SOLDIER×26, SMALL_TANK×24, NINJA×22, MOTORBIKE×26, TRANSPORTER×30, SMALL_TANK×22, DRAGOONER×22, TRANSPORTER×20, MOTORBIKE×19, SOLDIER×28, SOLDIER×22, TRANSPORTER×20, MOTORBIKE×26, SOLDIER×19, SMALL_TANK×20, SOLDIER×19, MOTORBIKE×19 |
| 🟩 | Angry Mob | random | Industrial 85%, Renaissance 9%, Modern 6% | 🟢 58/58 (100%) |  | MOTORBIKE×27, SOLDIER×20, MOTORBIKE×24, SOLDIER×19, TRANSPORTER×20, TRANSPORTER×20, SPECOPS×22, SMALL_TANK×22, SOLDIER×29, SOLDIER×31, DRAGOONER×22, TRANSPORTER×20, TRANSPORTER×30, TRANSPORTER×20, THE_KING×10, MOTORBIKE×21 |
| 🟩 | Angry Mob | random | Industrial 83%, Renaissance 9%, Modern 8% | 🟢 48/58 (83%) | SPECOPS×5 | SOLDIER×24, TRANSPORTER×30, MOTORBIKE×19, DRAGOONER×22, MOTORBIKE×19, MOTORBIKE×23, MOTORBIKE×18, SMALL_TANK×22, THE_KING×10, MOTORBIKE×21, SOLDIER×29, SPECOPS×26, TRANSPORTER×20, SOLDIER×25, SMALL_TANK×32 |
| 🟩 | Shrieking Horde | random | Industrial 85%, Modern 12%, Renaissance 2% | 🟢 47/58 (81%) | SOLDIER×11 | TRANSPORTER×20, SMALL_TANK×20, SOLDIER×22, HELI×26, MOTORBIKE×23, TRANSPORTER×20, TRANSPORTER×20, SOLDIER×28, SOLDIER×31, SOLDIER×30, MOTORBIKE×30, HELI×24, THE_KING×10, MOTORBIKE×26, SMALL_TANK×30, TRANSPORTER×20, MOTORBIKE×27 |
| 🟩 | Reckless Looters | random | Industrial 91%, Renaissance 5%, Modern 5% | 🟢 58/58 (100%) |  | SMALL_TANK×30, CARGO×18, MOTORBIKE×24, MOTORBIKE×21, SOLDIER×21, SOLDIER×30, SMALL_TANK×26, SMALL_TANK×22, SMALL_TANK×26, MOTORBIKE×28, SOLDIER×19, SMALL_TANK×26, THE_GENERAL×18, SMALL_TANK×22, MOTORBIKE×19, TRANSPORTER×20, SOLDIER×27 |
| 🟩 | Noisy Barbarians | random | Industrial 72%, Renaissance 20%, Modern 7% | 🟡 42/58 (72%) | SIEGE_TANK×8 | MOTORBIKE×20, SOLDIER×29, SMALL_TANK×20, SMALL_TANK×30, NINJA×31, SOLDIER×20, SMALL_TANK×24, SOLDIER×31, SIEGE_TANK×30, SMALL_TANK×28, MOTORBIKE×27, TRANSPORTER×20, SMALL_TANK×20, NINJA×29, TRANSPORTER×20, NINJA×22 |
| 🟩 | Frenzied Pillagers | random | Industrial 80%, Renaissance 14%, Modern 6% | 🟢 58/58 (100%) |  | MOTORBIKE×26, SOLDIER×19, CARGO×30, SMALL_TANK×28, MOTORBIKE×26, MOTORBIKE×27, SMALL_TANK×26, SOLDIER×27, TRANSPORTER×20, SOLDIER×19, SPECOPS×20, TRANSPORTER×30, MOTORBIKE×20, CARGO×21, TRANSPORTER×20 |

#### Mixed

| Tower Era Distribution (61 towers) | Towers |
|---|---|
| Industrial 92% (56), Renaissance 7% (4), Iron Age 2% (1) | FLAME_THROWER×26, SHOCK_TOWER×19, GATLING_TOWER×11, ICE_TOWER×4, COLD_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Industrial March | hardcoded | Industrial 98%, Modern 2% | 🟢 25/28 (89%) | SOLDIER×3 | SOLDIER×16, SOLDIER×17, MOTORBIKE×17, TRANSPORTER×18, TRANSPORTER×19, SMALL_TANK×19, TRANSPORTER×20, TRANSPORTER×21, SMALL_TANK×21, SMALL_TANK×22, MOTORBIKE×23, MOTORBIKE×23, SPECOPS×10, MOTORBIKE×28, SMALL_TANK×30, SOLDIER×32, SOLDIER×34, TRANSPORTER×36, TRANSPORTER×38, TRANSPORTER×40, MOTORBIKE×36 |
| 🟩 | Mechanized Strike | hardcoded | Industrial 100% | 🟢 28/28 (100%) |  | SOLDIER×18, SMALL_TANK×19, TRANSPORTER×19, SMALL_TANK×20, TRANSPORTER×21, SMALL_TANK×21, SOLDIER×22, SOLDIER×22, TRANSPORTER×23, MOTORBIKE×24, SMALL_TANK×24, MOTORBIKE×25, TRANSPORTER×26, TRANSPORTER×26, SOLDIER×27, SOLDIER×27, SMALL_TANK×28, SMALL_TANK×29, SMALL_TANK×29, TRANSPORTER×30, MOTORBIKE×34, SMALL_TANK×35, SOLDIER×35 |
| 🟩 | Steam Assault | hardcoded | Industrial 100% | 🟢 28/28 (100%) |  | TRANSPORTER×18, SOLDIER×19, SOLDIER×19, SMALL_TANK×20, TRANSPORTER×21, SOLDIER×21, SOLDIER×22, SMALL_TANK×22, TRANSPORTER×23, SMALL_TANK×24, TRANSPORTER×24, SMALL_TANK×25, SOLDIER×26, TRANSPORTER×26, SMALL_TANK×27, MOTORBIKE×27, SOLDIER×28, TRANSPORTER×29, SOLDIER×29, MOTORBIKE×30, SMALL_TANK×33, TRANSPORTER×35, TRANSPORTER×37 |
| 🟩 | Tank Column | hardcoded | Industrial 100% | 🟢 28/28 (100%) |  | SMALL_TANK×18, MOTORBIKE×19, MOTORBIKE×19, TRANSPORTER×20, TRANSPORTER×21, TRANSPORTER×21, SOLDIER×22, MOTORBIKE×22, TRANSPORTER×23, TRANSPORTER×24, SMALL_TANK×24, MOTORBIKE×25, TRANSPORTER×26, SMALL_TANK×26, TRANSPORTER×27, SMALL_TANK×27, TRANSPORTER×28, MOTORBIKE×29, MOTORBIKE×29, SOLDIER×30, SOLDIER×34, SOLDIER×36, TRANSPORTER×38, SOLDIER×34 |
| 🟩 | Factory Raid | hardcoded | Industrial 88%, Renaissance 10%, Modern 2% | 🟢 28/28 (100%) |  | MOTORBIKE×18, MOTORBIKE×20, MOTORBIKE×20, MOTORBIKE×22, SOLDIER×20, TRANSPORTER×21, MOTORBIKE×22, SMALL_TANK×22, SMALL_TANK×25, SOLDIER×24, MOTORBIKE×24, TRANSPORTER×25, SMALL_TANK×26, SMALL_TANK×28, MOTORBIKE×30, CARGO×30, TRANSPORTER×32, DRAGOONER×34, HELI×13, TRANSPORTER×38, SMALL_TANK×38, SOLDIER×36, SMALL_TANK×33, SMALL_TANK×36 |
| 🟩 | Reckless Looters | random | Industrial 88%, Renaissance 7%, Modern 4% | 🟢 28/28 (100%) |  | TRANSPORTER×20, SOLDIER×25, TRANSPORTER×20, SMALL_TANK×28, TRANSPORTER×20, TRANSPORTER×30, SOLDIER×19, MOTORBIKE×26, MUSKETEER×29, SOLDIER×24, MOTORBIKE×27, SOLDIER×28, MOTORBIKE×21, THE_GENERAL×18, SMALL_TANK×24, SOLDIER×27, MOTORBIKE×20 |
| 🟩 | Reckless Looters | random | Industrial 88%, Renaissance 7%, Modern 4% | 🟢 28/28 (100%) |  | TRANSPORTER×20, SOLDIER×25, TRANSPORTER×20, SMALL_TANK×28, TRANSPORTER×20, TRANSPORTER×30, SOLDIER×19, MOTORBIKE×26, MUSKETEER×29, SOLDIER×24, MOTORBIKE×27, SOLDIER×28, MOTORBIKE×21, THE_GENERAL×18, SMALL_TANK×24, SOLDIER×27, MOTORBIKE×20 |
| 🟩 | Reckless Looters | random | Industrial 93%, Renaissance 7% | 🟢 28/28 (100%) |  | SOLDIER×29, MOTORBIKE×32, MOTORBIKE×29, SOLDIER×20, SOLDIER×24, SOLDIER×31, SOLDIER×18, MUSKETEER×19, SOLDIER×27, SMALL_TANK×24, TRANSPORTER×30, TRANSPORTER×20, MOTORBIKE×19, SOLDIER×25, SMALL_TANK×30, SMALL_TANK×32, THE_KING×10 |
| 🟩 | Stubborn Raiders | random | Industrial 92%, Modern 6%, Renaissance 2% | 🟢 28/28 (100%) |  | SIEGE_TANK×24, MOTORBIKE×25, THE_KING×10, SMALL_TANK×26, MOTORBIKE×29, TRANSPORTER×20, SOLDIER×22, SMALL_TANK×20, SOLDIER×28, SMALL_TANK×20, SOLDIER×29, TRANSPORTER×20, SMALL_TANK×22, MOTORBIKE×31, SOLDIER×30, TRANSPORTER×30, MOTORBIKE×28 |
| 🟩 | Shrieking Horde | random | Industrial 91%, Renaissance 9% | 🟢 28/28 (100%) |  | MOTORBIKE×28, SMALL_TANK×28, MOTORBIKE×23, SMALL_TANK×24, SOLDIER×29, MUSKETEER×23, SOLDIER×21, TRANSPORTER×20, TRANSPORTER×30, SMALL_TANK×20, SMALL_TANK×28, MOTORBIKE×24, MUSKETEER×19, SOLDIER×25, TRANSPORTER×30, TRANSPORTER×30, MOTORBIKE×28, TRANSPORTER×30 |
| 🟩 | Restless Horde | random | Industrial 80%, Renaissance 20% | 🟢 28/28 (100%) |  | SOLDIER×25, SMALL_TANK×22, MUSKETEER×32, SMALL_TANK×20, MUSKETEER×23, CARGO×21, MOTORBIKE×31, SMALL_TANK×28, SOLDIER×25, SMALL_TANK×28, MOTORBIKE×29, SOLDIER×29, MOTORBIKE×31, TRANSPORTER×20, SOLDIER×22, THE_KING×10, SOLDIER×29 |
| 🟩 | Ragged Warband | random | Industrial 91%, Renaissance 5%, Modern 4% | 🟢 28/28 (100%) |  | MOTORBIKE×18, SOLDIER×26, SOLDIER×31, TRANSPORTER×30, SMALL_TANK×20, SOLDIER×18, NINJA×21, THE_GENERAL×18, TRANSPORTER×30, SOLDIER×24, TRANSPORTER×20, TRANSPORTER×30, MOTORBIKE×24, TRANSPORTER×30, SOLDIER×32, TRANSPORTER×20, TRANSPORTER×30 |
| 🟩 | Disorganized Mob | random | Industrial 81%, Modern 13%, Renaissance 6% | 🟢 28/28 (100%) |  | MOTORBIKE×22, SOLDIER×29, DRAGOONER×20, SMALL_TANK×22, SMALL_TANK×20, SPECOPS×27, SMALL_TANK×22, SOLDIER×26, MOTORBIKE×25, SMALL_TANK×26, TRANSPORTER×20, MOTORBIKE×26, TRANSPORTER×20, THE_GENERAL×18, SOLDIER×20 |
| 🟩 | Petty Bandits | random | Industrial 82%, Renaissance 18% | 🟢 28/28 (100%) |  | SOLDIER×25, MOTORBIKE×29, SOLDIER×20, SOLDIER×20, SOLDIER×26, MOTORBIKE×29, SMALL_TANK×26, CARGO×24, SOLDIER×25, MUSKETEER×20, MOTORBIKE×23, SOLDIER×26, TRANSPORTER×30, MUSKETEER×22, TRANSPORTER×20 |
| 🟩 | Crude Invaders | random | Industrial 79%, Renaissance 21% | 🟢 28/28 (100%) |  | SMALL_TANK×22, SMALL_TANK×26, SMALL_TANK×22, NINJA×19, MOTORBIKE×25, TRANSPORTER×30, MUSKETEER×25, THE_KING×10, SOLDIER×27, SMALL_TANK×28, TRANSPORTER×20, TRANSPORTER×30, TRANSPORTER×20, MOTORBIKE×30, CARGO×21 |
| 🟩 | Forgotten Warband | random | Industrial 70%, Renaissance 19%, Modern 11% | 🟢 28/28 (100%) |  | SIEGE_TANK×20, MOTORBIKE×24, NINJA×23, TRANSPORTER×30, SIEGE_TANK×20, TRANSPORTER×20, MUSKETEER×19, THE_KING×10, SOLDIER×18, SMALL_TANK×26, SOLDIER×23, MOTORBIKE×21, MOTORBIKE×22, SOLDIER×23, TRANSPORTER×20, TRANSPORTER×30, MUSKETEER×19 |
| 🟩 | Forgotten Warband | random | Industrial 79%, Renaissance 16%, Modern 5% | 🟢 28/28 (100%) |  | SIEGE_TANK×20, TRANSPORTER×30, SOLDIER×20, TRANSPORTER×20, SMALL_TANK×26, DRAGOONER×31, MOTORBIKE×24, SMALL_TANK×30, MOTORBIKE×25, DRAGOONER×22, SOLDIER×26, SMALL_TANK×20, SMALL_TANK×24, THE_KING×10, MOTORBIKE×26, SMALL_TANK×28, TRANSPORTER×20 |
| 🟩 | Drunken Raiders | random | Industrial 90%, Modern 7%, Renaissance 3% | 🟢 28/28 (100%) |  | SMALL_TANK×26, THE_KING×10, TRANSPORTER×20, SMALL_TANK×26, SMALL_TANK×28, MOTORBIKE×21, SOLDIER×22, SOLDIER×24, TRANSPORTER×20, SOLDIER×28, SOLDIER×22, MOTORBIKE×23, SMALL_TANK×18, SPECOPS×27, TRANSPORTER×30, TRANSPORTER×20 |
| 🟩 | Unlucky Raiders | random | Industrial 89%, Renaissance 11% | 🟢 28/28 (100%) |  | SOLDIER×26, SMALL_TANK×24, NINJA×22, MOTORBIKE×26, TRANSPORTER×30, SMALL_TANK×22, DRAGOONER×22, TRANSPORTER×20, MOTORBIKE×19, SOLDIER×28, SOLDIER×22, TRANSPORTER×20, MOTORBIKE×26, SOLDIER×19, SMALL_TANK×20, SOLDIER×19, MOTORBIKE×19 |
| 🟩 | Angry Mob | random | Industrial 85%, Renaissance 9%, Modern 6% | 🟢 28/28 (100%) |  | MOTORBIKE×27, SOLDIER×20, MOTORBIKE×24, SOLDIER×19, TRANSPORTER×20, TRANSPORTER×20, SPECOPS×22, SMALL_TANK×22, SOLDIER×29, SOLDIER×31, DRAGOONER×22, TRANSPORTER×20, TRANSPORTER×30, TRANSPORTER×20, THE_KING×10, MOTORBIKE×21 |
| 🟩 | Angry Mob | random | Industrial 83%, Renaissance 9%, Modern 8% | 🟢 28/28 (100%) |  | SOLDIER×24, TRANSPORTER×30, MOTORBIKE×19, DRAGOONER×22, MOTORBIKE×19, MOTORBIKE×23, MOTORBIKE×18, SMALL_TANK×22, THE_KING×10, MOTORBIKE×21, SOLDIER×29, SPECOPS×26, TRANSPORTER×20, SOLDIER×25, SMALL_TANK×32 |
| 🟩 | Shrieking Horde | random | Industrial 85%, Modern 12%, Renaissance 2% | 🟢 28/28 (100%) |  | TRANSPORTER×20, SMALL_TANK×20, SOLDIER×22, HELI×26, MOTORBIKE×23, TRANSPORTER×20, TRANSPORTER×20, SOLDIER×28, SOLDIER×31, SOLDIER×30, MOTORBIKE×30, HELI×24, THE_KING×10, MOTORBIKE×26, SMALL_TANK×30, TRANSPORTER×20, MOTORBIKE×27 |
| 🟩 | Reckless Looters | random | Industrial 91%, Renaissance 5%, Modern 5% | 🟢 28/28 (100%) |  | SMALL_TANK×30, CARGO×18, MOTORBIKE×24, MOTORBIKE×21, SOLDIER×21, SOLDIER×30, SMALL_TANK×26, SMALL_TANK×22, SMALL_TANK×26, MOTORBIKE×28, SOLDIER×19, SMALL_TANK×26, THE_GENERAL×18, SMALL_TANK×22, MOTORBIKE×19, TRANSPORTER×20, SOLDIER×27 |
| 🟩 | Noisy Barbarians | random | Industrial 72%, Renaissance 20%, Modern 7% | 🟢 28/28 (100%) |  | MOTORBIKE×20, SOLDIER×29, SMALL_TANK×20, SMALL_TANK×30, NINJA×31, SOLDIER×20, SMALL_TANK×24, SOLDIER×31, SIEGE_TANK×30, SMALL_TANK×28, MOTORBIKE×27, TRANSPORTER×20, SMALL_TANK×20, NINJA×29, TRANSPORTER×20, NINJA×22 |
| 🟩 | Frenzied Pillagers | random | Industrial 80%, Renaissance 14%, Modern 6% | 🟢 28/28 (100%) |  | MOTORBIKE×26, SOLDIER×19, CARGO×30, SMALL_TANK×28, MOTORBIKE×26, MOTORBIKE×27, SMALL_TANK×26, SOLDIER×27, TRANSPORTER×20, SOLDIER×19, SPECOPS×20, TRANSPORTER×30, MOTORBIKE×20, CARGO×21, TRANSPORTER×20 |

### Modern

#### Short Mixed Modern

| Tower Era Distribution (51 towers) | Towers |
|---|---|
| Modern 88% (45), Industrial 12% (6) | MG_TOWER×21, RADAR_TOWER×12, NAPALM_THROWER×6, SHOCK_TOWER×6, PARALYZNG_TOWER×6 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Modern Warfare | hardcoded | Modern 85%, Industrial 12%, Future 4% | 🔴 6/48 (12%) | SPECOPS×9, SOLDIER×6, THE_GENERAL×1 | SPECOPS×18, SIEGE_TANK×18, SIEGE_TANK×19, HELI×20, HELI×20, SIEGE_TANK×20, SPECOPS×21, SIEGE_TANK×22, SPECOPS×22, SPECOPS×22, SPECOPS×23, SIEGE_TANK×24, HELI×24, SIEGE_TANK×24, DRONE×25, SIEGE_TANK×26, SPECOPS×26, TRANSPORTER×26, HELI×27, SIEGE_TANK×28, TRANSPORTER×28, SPECOPS×28, HELI×29, SMALL_TANK×30, HELI×30, SIEGE_TANK×33, THE_GENERAL×40, HELI×34 |
| 🟥 | Special Ops | hardcoded | Modern 88%, Industrial 9%, Future 4% | ⬛ 0/48 (0%) | MECH_WARRIOR×8, SPECOPS×7, SOLDIER×2 | HELI×18, HELI×18, SPECOPS×19, SIEGE_TANK×20, SIEGE_TANK×20, SIEGE_TANK×20, SPECOPS×21, SPECOPS×22, SPECOPS×22, HELI×22, SIEGE_TANK×23, SPECOPS×24, SIEGE_TANK×24, HELI×24, HELI×25, MECH_WARRIOR×26, SPECOPS×26, SIEGE_TANK×26, SPECOPS×27, HELI×28, SPECOPS×28, TRANSPORTER×28, HELI×29, SIEGE_TANK×30, HELI×30, SMALL_TANK×32, SIEGE_TANK×33, THE_GENERAL×36 |
| 🟩 | Heli Strike | hardcoded | Modern 82%, Industrial 13%, Future 5% | 🟠 18/48 (38%) | SOLDIER×10, SPECOPS×1, THE_GENERAL×1 | HELI×18, SPECOPS×18, HELI×19, SPECOPS×20, HELI×20, SPECOPS×20, SPECOPS×21, SPECOPS×22, TRANSPORTER×22, SPECOPS×22, SPECOPS×23, SIEGE_TANK×24, HELI×24, TRANSPORTER×24, SIEGE_TANK×25, HELI×26, SPECOPS×26, MOTORBIKE×26, SPECOPS×27, HELI×28, TRANSPORTER×28, HELI×28, HELI×29, SIEGE_TANK×30, SPECOPS×30, THE_GENERAL×35, DRONE×36, SIEGE_TANK×36, HELI×40 |
| 🟥 | Siege Assault | hardcoded | Modern 82%, Industrial 11%, Future 4%, Renaissance 3% | ⬛ 0/48 (0%) | SOLDIER×12, SPECOPS×9, MECH_WARRIOR×5 | SIEGE_TANK×18, SIEGE_TANK×18, SIEGE_TANK×19, SPECOPS×20, HELI×20, SPECOPS×20, TRANSPORTER×21, SIEGE_TANK×22, NINJA×22, HELI×22, SIEGE_TANK×23, SIEGE_TANK×24, SOLDIER×24, SPECOPS×24, SIEGE_TANK×25, SPECOPS×26, SPECOPS×26, HELI×26, SIEGE_TANK×27, TRANSPORTER×28, HELI×28, HELI×28, SIEGE_TANK×29, MECH_WARRIOR×30, SPECOPS×30, THE_GENERAL×40, SIEGE_TANK×40 |
| 🟩 | Urban Combat | hardcoded | Modern 83%, Industrial 12%, Future 5% | 🟠 19/48 (40%) | SPECOPS×11, SOLDIER×5, SIEGE_TANK×1 | SPECOPS×18, SIEGE_TANK×18, SPECOPS×19, THE_GENERAL×20, SPECOPS×20, SPECOPS×20, HELI×21, SPECOPS×22, SPECOPS×22, SIEGE_TANK×22, SIEGE_TANK×23, SIEGE_TANK×24, SPECOPS×24, SOLDIER×24, SPECOPS×25, SPECOPS×26, SIEGE_TANK×26, HELI×26, SPECOPS×27, HELI×28, SPECOPS×28, HELI×28, TRANSPORTER×29, HELI×30, SMALL_TANK×30, DRONE×34, SIEGE_TANK×36, SPECOPS×37 |
| 🟥 | Cyber Strike | hardcoded | Modern 91%, Future 4%, Industrial 4% | ⬛ 0/48 (0%) | SOLDIER×20, SPECOPS×11, SIEGE_TANK×3 | SIEGE_TANK×18, HELI×18, HELI×19, SPECOPS×19, SPECOPS×20, SPECOPS×20, SIEGE_TANK×21, SPECOPS×21, SPECOPS×21, SIEGE_TANK×22, SPECOPS×22, SPECOPS×23, SPECOPS×23, SIEGE_TANK×24, SIEGE_TANK×24, SIEGE_TANK×24, HELI×25, SPECOPS×25, HELI×26, SIEGE_TANK×26, SPECOPS×27, SPECOPS×27, HELI×27, SIEGE_TANK×28, SIEGE_TANK×28, SOLDIER×29, DRONE×30, THE_GENERAL×35 |
| 🟥 | Shrieking Horde | random | Modern 87%, Future 13% | ⬛ 0/48 (0%) | SPECOPS×11, MECH_WARRIOR×7 | HELI×22, SPECOPS×31, MECH_WARRIOR×33, SIEGE_TANK×22, SPECOPS×21, SIEGE_TANK×26, SPECOPS×31, SPECOPS×27, THE_GENERAL×18, SPECOPS×28, HELI×24, HELI×26, SIEGE_TANK×22, DRONE×31, SPECOPS×34, SIEGE_TANK×22, SIEGE_TANK×26, SPECOPS×30 |
| 🟥 | Shrieking Horde | random | Modern 87%, Future 13% | ⬛ 0/48 (0%) | SPECOPS×11, MECH_WARRIOR×7 | HELI×22, SPECOPS×31, MECH_WARRIOR×33, SIEGE_TANK×22, SPECOPS×21, SIEGE_TANK×26, SPECOPS×31, SPECOPS×27, THE_GENERAL×18, SPECOPS×28, HELI×24, HELI×26, SIEGE_TANK×22, DRONE×31, SPECOPS×34, SIEGE_TANK×22, SIEGE_TANK×26, SPECOPS×30 |
| 🟥 | Stubborn Raiders | random | Modern 89%, Future 6%, Industrial 5% | ⬛ 0/48 (0%) | SOLDIER×5, SPECOPS×4, MECH_WARRIOR×4, SIEGE_TANK×1, THE_GENERAL×1 | SIEGE_TANK×26, SIEGE_TANK×28, HELI×20, SPECOPS×29, SIEGE_TANK×22, THE_GENERAL×18, SIEGE_TANK×32, SPECOPS×22, SIEGE_TANK×34, HELI×24, MECH_WARRIOR×30, HELI×20, SPECOPS×31, HELI×26, SPECOPS×25, HELI×26, SOLDIER×21, HELI×32 |
| 🟥 | Shrieking Horde | random | Modern 94%, Future 6% | ⬛ 0/48 (0%) | SPECOPS×8, MECH_WARRIOR×8 | SIEGE_TANK×26, HELI×24, SPECOPS×27, SIEGE_TANK×24, SPECOPS×31, SIEGE_TANK×26, SIEGE_TANK×30, HELI×22, SPECOPS×20, MECH_WARRIOR×27, HELI×20, THE_GENERAL×18, SIEGE_TANK×30, SIEGE_TANK×30, SIEGE_TANK×30, SPECOPS×32, SPECOPS×30, HELI×30 |
| 🟥 | Relentless Mob | random | Modern 89%, Future 6%, Industrial 6% | ⬛ 0/48 (0%) | SOLDIER×27, SPECOPS×11 | DRONE×29, HELI×22, HELI×26, SPECOPS×30, SIEGE_TANK×30, HELI×34, MOTORBIKE×28, SPECOPS×30, SIEGE_TANK×24, SPECOPS×20, SPECOPS×27, HELI×26, HELI×26, SPECOPS×28, SPECOPS×25, HELI×22, THE_GENERAL×18, SPECOPS×31, HELI×32 |
| 🟥 | Desperate Looters | random | Modern 77%, Industrial 16%, Future 7% | ⬛ 0/48 (0%) | SPECOPS×14, SOLDIER×12, HELI×3 | DRONE×32, SIEGE_TANK×24, SPECOPS×33, MOTORBIKE×34, MOTORBIKE×25, SIEGE_TANK×26, HELI×22, HELI×30, SIEGE_TANK×26, SIEGE_TANK×30, SPECOPS×33, SPECOPS×31, HELI×30, SIEGE_TANK×32, THE_GENERAL×18, HELI×24, TRANSPORTER×20, SIEGE_TANK×22 |
| 🟥 | Ragged Warband | random | Modern 88%, Future 12% | ⬛ 0/48 (0%) | SOLDIER×13, SPECOPS×8, SIEGE_TANK×1, THE_GENERAL×1 | SIEGE_TANK×20, SPECOPS×31, HELI×26, DRONE×28, SIEGE_TANK×28, HELI×34, THE_GENERAL×18, HELI×34, SIEGE_TANK×20, SPECOPS×23, SIEGE_TANK×28, HELI×22, SPECOPS×27, DRONE×32, HELI×34, HELI×34, SIEGE_TANK×24, SIEGE_TANK×34 |
| 🟥 | Shrieking Horde | random | Modern 85%, Future 15% | ⬛ 0/48 (0%) | SPECOPS×8, MECH_WARRIOR×8 | HELI×24, SIEGE_TANK×22, MECH_WARRIOR×33, SPECOPS×27, SPECOPS×24, MECH_WARRIOR×30, HELI×22, THE_GENERAL×18, SPECOPS×31, SIEGE_TANK×30, HELI×24, SIEGE_TANK×28, HELI×28, SIEGE_TANK×24, SIEGE_TANK×32, SIEGE_TANK×32 |
| 🟩 | Relentless Mob | random | Modern 73%, Industrial 20%, Future 7% | 🟡 33/48 (69%) | SOLDIER×9, SPECOPS×3 | SIEGE_TANK×22, SIEGE_TANK×28, SPECOPS×31, SIEGE_TANK×20, SIEGE_TANK×26, HELI×30, THE_GENERAL×18, MOTORBIKE×27, HELI×28, SIEGE_TANK×28, SIEGE_TANK×28, DRONE×30, MOTORBIKE×27, SPECOPS×26, HELI×22, SOLDIER×32 |
| 🟥 | Muddy Marauders | random | Modern 70%, Industrial 24%, Future 7% | ⬛ 0/48 (0%) | SOLDIER×10, SPECOPS×8, MECH_WARRIOR×6 | THE_GENERAL×18, SMALL_TANK×24, HELI×26, SIEGE_TANK×32, SOLDIER×27, HELI×22, MOTORBIKE×21, SOLDIER×32, SPECOPS×33, SIEGE_TANK×34, MECH_WARRIOR×30, SPECOPS×25, HELI×28, SIEGE_TANK×30, HELI×30, SIEGE_TANK×28 |
| 🟥 | Howling Savages | random | Modern 68%, Industrial 21%, Future 11% | ⬛ 0/48 (0%) | SPECOPS×11, MECH_WARRIOR×6, SOLDIER×3 | MECH_WARRIOR×27, DRONE×22, SPECOPS×25, SOLDIER×22, THE_GENERAL×18, SIEGE_TANK×34, SPECOPS×30, HELI×22, SPECOPS×26, SOLDIER×27, HELI×22, SOLDIER×21, SIEGE_TANK×24, SPECOPS×33, SIEGE_TANK×22, MOTORBIKE×27, SPECOPS×27, SIEGE_TANK×32 |
| 🟥 | Lazy Raiders | random | Modern 78%, Industrial 12%, Future 10% | ⬛ 0/48 (0%) | SOLDIER×18, SPECOPS×10, MECH_WARRIOR×3 | HELI×22, SPECOPS×29, DRONE×22, SMALL_TANK×34, MOTORBIKE×21, HELI×22, SPECOPS×25, SPECOPS×27, SIEGE_TANK×24, HELI×30, HELI×32, THE_GENERAL×18, SPECOPS×28, SPECOPS×32, HELI×28, SIEGE_TANK×28, MECH_WARRIOR×24, SPECOPS×22 |
| 🟥 | Angry Mob | random | Modern 87%, Future 13% | ⬛ 0/48 (0%) | SOLDIER×8, SPECOPS×8, MECH_WARRIOR×6 | SIEGE_TANK×24, SIEGE_TANK×32, MECH_WARRIOR×30, HELI×24, SPECOPS×31, SPECOPS×21, SIEGE_TANK×32, SIEGE_TANK×22, SIEGE_TANK×20, SIEGE_TANK×22, HELI×30, THE_GENERAL×18, HELI×28, SPECOPS×26, DRONE×28, SPECOPS×30, SIEGE_TANK×28 |
| 🟩 | Forgotten Warband | random | Modern 88%, Future 6%, Industrial 5% | 🟠 12/48 (25%) | SPECOPS×7, SOLDIER×4, THE_GENERAL×1 | SPECOPS×31, THE_GENERAL×18, SPECOPS×21, SPECOPS×29, SPECOPS×25, DRONE×30, SIEGE_TANK×20, SIEGE_TANK×30, SIEGE_TANK×24, SOLDIER×25, HELI×26, SIEGE_TANK×32, SPECOPS×30, SIEGE_TANK×22, SPECOPS×28, SIEGE_TANK×22, SPECOPS×29, SIEGE_TANK×20 |
| 🟥 | Drunken Raiders | random | Modern 77%, Future 12%, Industrial 11% | ⬛ 0/48 (0%) | SPECOPS×8, MECH_WARRIOR×7, SIEGE_TANK×3 | SPECOPS×21, SIEGE_TANK×30, SPECOPS×33, SOLDIER×29, SIEGE_TANK×34, SPECOPS×29, SPECOPS×33, SOLDIER×22, MECH_WARRIOR×24, SPECOPS×23, SIEGE_TANK×24, HELI×20, THE_GENERAL×18, DRONE×33, SPECOPS×33, SIEGE_TANK×24, SIEGE_TANK×30 |
| 🟩 | Hungry Invaders | random | Modern 78%, Industrial 14%, Future 8% | 🟢 48/48 (100%) |  | SPECOPS×25, HELI×32, SMALL_TANK×26, SPECOPS×22, HELI×22, SPECOPS×20, SPECOPS×23, SPECOPS×21, HELI×24, SPECOPS×21, THE_GENERAL×18, DRONE×29, HELI×34, SMALL_TANK×28, SPECOPS×21, SPECOPS×20 |
| 🟥 | Lazy Raiders | random | Modern 88%, Future 12% | ⬛ 0/48 (0%) | SOLDIER×16, SPECOPS×12, SIEGE_TANK×3, MECH_WARRIOR×1 | THE_GENERAL×18, SPECOPS×20, SIEGE_TANK×20, SPECOPS×31, SIEGE_TANK×26, HELI×28, SIEGE_TANK×34, SPECOPS×25, SPECOPS×26, HELI×22, SPECOPS×27, HELI×22, MECH_WARRIOR×27, HELI×24, HELI×32, MECH_WARRIOR×30, SPECOPS×32, HELI×22 |
| 🟩 | Unlucky Raiders | random | Modern 88%, Future 12% | 🔴 9/48 (19%) | SPECOPS×10, SOLDIER×1, THE_GENERAL×1 | SIEGE_TANK×32, SPECOPS×21, SIEGE_TANK×22, SIEGE_TANK×22, SIEGE_TANK×20, HELI×24, SIEGE_TANK×26, SPECOPS×29, DRONE×34, DRONE×22, HELI×30, SIEGE_TANK×28, SPECOPS×29, THE_GENERAL×18, SPECOPS×26, SPECOPS×30, SIEGE_TANK×30, HELI×24 |
| 🟥 | Bored Mercenaries | random | Modern 72%, Industrial 15%, Future 13% | ⬛ 0/48 (0%) | MECH_WARRIOR×11, SOLDIER×5 | THE_GENERAL×18, SIEGE_TANK×28, TRANSPORTER×20, SIEGE_TANK×32, SPECOPS×22, MECH_WARRIOR×33, SIEGE_TANK×22, HELI×26, HELI×22, HELI×32, MECH_WARRIOR×24, HELI×30, SIEGE_TANK×34, SOLDIER×23, SPECOPS×29, MOTORBIKE×26, SIEGE_TANK×32 |
| 🟥 | Unlucky Raiders | random | Modern 87%, Industrial 7%, Future 6% | ⬛ 0/48 (0%) | SOLDIER×18, SPECOPS×15 | SPECOPS×23, SPECOPS×21, HELI×32, SIEGE_TANK×28, SIEGE_TANK×34, SPECOPS×26, SPECOPS×27, HELI×24, SPECOPS×32, DRONE×23, SIEGE_TANK×22, SPECOPS×24, SIEGE_TANK×26, THE_GENERAL×18, SIEGE_TANK×32, TRANSPORTER×30 |

#### S2 Wicked$Kingdom

| Tower Era Distribution (62 towers) | Towers |
|---|---|
| Industrial 48% (30), Modern 34% (21), Iron Age 16% (10), Renaissance 2% (1) | RADAR_TOWER×21, GATLING_TOWER×19, FLAME_THROWER×11, COLD_TOWER×10, ICE_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟥 | Modern Warfare | hardcoded | Modern 85%, Industrial 12%, Future 4% | ⬛ 0/38 (0%) | SOLDIER×21, SPECOPS×9 | SPECOPS×18, SIEGE_TANK×18, SIEGE_TANK×19, HELI×20, HELI×20, SIEGE_TANK×20, SPECOPS×21, SIEGE_TANK×22, SPECOPS×22, SPECOPS×22, SPECOPS×23, SIEGE_TANK×24, HELI×24, SIEGE_TANK×24, DRONE×25, SIEGE_TANK×26, SPECOPS×26, TRANSPORTER×26, HELI×27, SIEGE_TANK×28, TRANSPORTER×28, SPECOPS×28, HELI×29, SMALL_TANK×30, HELI×30, SIEGE_TANK×33, THE_GENERAL×40, HELI×34 |
| 🟥 | Special Ops | hardcoded | Modern 88%, Industrial 9%, Future 4% | ⬛ 0/38 (0%) | SPECOPS×14, SOLDIER×11 | HELI×18, HELI×18, SPECOPS×19, SIEGE_TANK×20, SIEGE_TANK×20, SIEGE_TANK×20, SPECOPS×21, SPECOPS×22, SPECOPS×22, HELI×22, SIEGE_TANK×23, SPECOPS×24, SIEGE_TANK×24, HELI×24, HELI×25, MECH_WARRIOR×26, SPECOPS×26, SIEGE_TANK×26, SPECOPS×27, HELI×28, SPECOPS×28, TRANSPORTER×28, HELI×29, SIEGE_TANK×30, HELI×30, SMALL_TANK×32, SIEGE_TANK×33, THE_GENERAL×36 |
| 🟥 | Heli Strike | hardcoded | Modern 82%, Industrial 13%, Future 5% | ⬛ 0/38 (0%) | SPECOPS×15, SOLDIER×11 | HELI×18, SPECOPS×18, HELI×19, SPECOPS×20, HELI×20, SPECOPS×20, SPECOPS×21, SPECOPS×22, TRANSPORTER×22, SPECOPS×22, SPECOPS×23, SIEGE_TANK×24, HELI×24, TRANSPORTER×24, SIEGE_TANK×25, HELI×26, SPECOPS×26, MOTORBIKE×26, SPECOPS×27, HELI×28, TRANSPORTER×28, HELI×28, HELI×29, SIEGE_TANK×30, SPECOPS×30, THE_GENERAL×35, DRONE×36, SIEGE_TANK×36, HELI×40 |
| 🟥 | Siege Assault | hardcoded | Modern 82%, Industrial 11%, Future 4%, Renaissance 3% | ⬛ 0/38 (0%) | SPECOPS×14, SOLDIER×8, HELI×1 | SIEGE_TANK×18, SIEGE_TANK×18, SIEGE_TANK×19, SPECOPS×20, HELI×20, SPECOPS×20, TRANSPORTER×21, SIEGE_TANK×22, NINJA×22, HELI×22, SIEGE_TANK×23, SIEGE_TANK×24, SOLDIER×24, SPECOPS×24, SIEGE_TANK×25, SPECOPS×26, SPECOPS×26, HELI×26, SIEGE_TANK×27, TRANSPORTER×28, HELI×28, HELI×28, SIEGE_TANK×29, MECH_WARRIOR×30, SPECOPS×30, THE_GENERAL×40, SIEGE_TANK×40 |
| 🟥 | Urban Combat | hardcoded | Modern 83%, Industrial 12%, Future 5% | ⬛ 0/38 (0%) | SPECOPS×15, SOLDIER×8 | SPECOPS×18, SIEGE_TANK×18, SPECOPS×19, THE_GENERAL×20, SPECOPS×20, SPECOPS×20, HELI×21, SPECOPS×22, SPECOPS×22, SIEGE_TANK×22, SIEGE_TANK×23, SIEGE_TANK×24, SPECOPS×24, SOLDIER×24, SPECOPS×25, SPECOPS×26, SIEGE_TANK×26, HELI×26, SPECOPS×27, HELI×28, SPECOPS×28, HELI×28, TRANSPORTER×29, HELI×30, SMALL_TANK×30, DRONE×34, SIEGE_TANK×36, SPECOPS×37 |
| 🟥 | Cyber Strike | hardcoded | Modern 91%, Future 4%, Industrial 4% | ⬛ 0/38 (0%) | SPECOPS×14, SOLDIER×11 | SIEGE_TANK×18, HELI×18, HELI×19, SPECOPS×19, SPECOPS×20, SPECOPS×20, SIEGE_TANK×21, SPECOPS×21, SPECOPS×21, SIEGE_TANK×22, SPECOPS×22, SPECOPS×23, SPECOPS×23, SIEGE_TANK×24, SIEGE_TANK×24, SIEGE_TANK×24, HELI×25, SPECOPS×25, HELI×26, SIEGE_TANK×26, SPECOPS×27, SPECOPS×27, HELI×27, SIEGE_TANK×28, SIEGE_TANK×28, SOLDIER×29, DRONE×30, THE_GENERAL×35 |
| 🟥 | Shrieking Horde | random | Modern 87%, Future 13% | ⬛ 0/38 (0%) | SPECOPS×9, MECH_WARRIOR×5 | HELI×22, SPECOPS×31, MECH_WARRIOR×33, SIEGE_TANK×22, SPECOPS×21, SIEGE_TANK×26, SPECOPS×31, SPECOPS×27, THE_GENERAL×18, SPECOPS×28, HELI×24, HELI×26, SIEGE_TANK×22, DRONE×31, SPECOPS×34, SIEGE_TANK×22, SIEGE_TANK×26, SPECOPS×30 |
| 🟥 | Shrieking Horde | random | Modern 87%, Future 13% | ⬛ 0/38 (0%) | SPECOPS×9, MECH_WARRIOR×5 | HELI×22, SPECOPS×31, MECH_WARRIOR×33, SIEGE_TANK×22, SPECOPS×21, SIEGE_TANK×26, SPECOPS×31, SPECOPS×27, THE_GENERAL×18, SPECOPS×28, HELI×24, HELI×26, SIEGE_TANK×22, DRONE×31, SPECOPS×34, SIEGE_TANK×22, SIEGE_TANK×26, SPECOPS×30 |
| 🟥 | Stubborn Raiders | random | Modern 89%, Future 6%, Industrial 5% | ⬛ 0/38 (0%) | SOLDIER×9, SPECOPS×5, THE_GENERAL×1, MECH_WARRIOR×1 | SIEGE_TANK×26, SIEGE_TANK×28, HELI×20, SPECOPS×29, SIEGE_TANK×22, THE_GENERAL×18, SIEGE_TANK×32, SPECOPS×22, SIEGE_TANK×34, HELI×24, MECH_WARRIOR×30, HELI×20, SPECOPS×31, HELI×26, SPECOPS×25, HELI×26, SOLDIER×21, HELI×32 |
| 🟥 | Shrieking Horde | random | Modern 94%, Future 6% | ⬛ 0/38 (0%) | SPECOPS×8, SOLDIER×7, MECH_WARRIOR×4 | SIEGE_TANK×26, HELI×24, SPECOPS×27, SIEGE_TANK×24, SPECOPS×31, SIEGE_TANK×26, SIEGE_TANK×30, HELI×22, SPECOPS×20, MECH_WARRIOR×27, HELI×20, THE_GENERAL×18, SIEGE_TANK×30, SIEGE_TANK×30, SIEGE_TANK×30, SPECOPS×32, SPECOPS×30, HELI×30 |
| 🟥 | Relentless Mob | random | Modern 89%, Future 6%, Industrial 6% | ⬛ 0/38 (0%) | SOLDIER×22, SPECOPS×8, HELI×1 | DRONE×29, HELI×22, HELI×26, SPECOPS×30, SIEGE_TANK×30, HELI×34, MOTORBIKE×28, SPECOPS×30, SIEGE_TANK×24, SPECOPS×20, SPECOPS×27, HELI×26, HELI×26, SPECOPS×28, SPECOPS×25, HELI×22, THE_GENERAL×18, SPECOPS×31, HELI×32 |
| 🟥 | Desperate Looters | random | Modern 77%, Industrial 16%, Future 7% | ⬛ 0/38 (0%) | SOLDIER×13, SPECOPS×8, HELI×3 | DRONE×32, SIEGE_TANK×24, SPECOPS×33, MOTORBIKE×34, MOTORBIKE×25, SIEGE_TANK×26, HELI×22, HELI×30, SIEGE_TANK×26, SIEGE_TANK×30, SPECOPS×33, SPECOPS×31, HELI×30, SIEGE_TANK×32, THE_GENERAL×18, HELI×24, TRANSPORTER×20, SIEGE_TANK×22 |
| 🟥 | Ragged Warband | random | Modern 88%, Future 12% | ⬛ 0/38 (0%) | DRONE×12, SPECOPS×10, SOLDIER×6 | SIEGE_TANK×20, SPECOPS×31, HELI×26, DRONE×28, SIEGE_TANK×28, HELI×34, THE_GENERAL×18, HELI×34, SIEGE_TANK×20, SPECOPS×23, SIEGE_TANK×28, HELI×22, SPECOPS×27, DRONE×32, HELI×34, HELI×34, SIEGE_TANK×24, SIEGE_TANK×34 |
| 🟥 | Shrieking Horde | random | Modern 85%, Future 15% | ⬛ 0/38 (0%) | SPECOPS×11, MECH_WARRIOR×4 | HELI×24, SIEGE_TANK×22, MECH_WARRIOR×33, SPECOPS×27, SPECOPS×24, MECH_WARRIOR×30, HELI×22, THE_GENERAL×18, SPECOPS×31, SIEGE_TANK×30, HELI×24, SIEGE_TANK×28, HELI×28, SIEGE_TANK×24, SIEGE_TANK×32, SIEGE_TANK×32 |
| 🟩 | Relentless Mob | random | Modern 73%, Industrial 20%, Future 7% | 🟠 10/38 (26%) | SPECOPS×11, SOLDIER×6 | SIEGE_TANK×22, SIEGE_TANK×28, SPECOPS×31, SIEGE_TANK×20, SIEGE_TANK×26, HELI×30, THE_GENERAL×18, MOTORBIKE×27, HELI×28, SIEGE_TANK×28, SIEGE_TANK×28, DRONE×30, MOTORBIKE×27, SPECOPS×26, HELI×22, SOLDIER×32 |
| 🟥 | Muddy Marauders | random | Modern 70%, Industrial 24%, Future 7% | ⬛ 0/38 (0%) | SOLDIER×15, SPECOPS×13 | THE_GENERAL×18, SMALL_TANK×24, HELI×26, SIEGE_TANK×32, SOLDIER×27, HELI×22, MOTORBIKE×21, SOLDIER×32, SPECOPS×33, SIEGE_TANK×34, MECH_WARRIOR×30, SPECOPS×25, HELI×28, SIEGE_TANK×30, HELI×30, SIEGE_TANK×28 |
| 🟥 | Howling Savages | random | Modern 68%, Industrial 21%, Future 11% | ⬛ 0/38 (0%) | SPECOPS×11, MECH_WARRIOR×4 | MECH_WARRIOR×27, DRONE×22, SPECOPS×25, SOLDIER×22, THE_GENERAL×18, SIEGE_TANK×34, SPECOPS×30, HELI×22, SPECOPS×26, SOLDIER×27, HELI×22, SOLDIER×21, SIEGE_TANK×24, SPECOPS×33, SIEGE_TANK×22, MOTORBIKE×27, SPECOPS×27, SIEGE_TANK×32 |
| 🟥 | Lazy Raiders | random | Modern 78%, Industrial 12%, Future 10% | ⬛ 0/38 (0%) | SOLDIER×24, SPECOPS×6, HELI×1 | HELI×22, SPECOPS×29, DRONE×22, SMALL_TANK×34, MOTORBIKE×21, HELI×22, SPECOPS×25, SPECOPS×27, SIEGE_TANK×24, HELI×30, HELI×32, THE_GENERAL×18, SPECOPS×28, SPECOPS×32, HELI×28, SIEGE_TANK×28, MECH_WARRIOR×24, SPECOPS×22 |
| 🟥 | Angry Mob | random | Modern 87%, Future 13% | ⬛ 0/38 (0%) | SPECOPS×7, MECH_WARRIOR×6, SOLDIER×1 | SIEGE_TANK×24, SIEGE_TANK×32, MECH_WARRIOR×30, HELI×24, SPECOPS×31, SPECOPS×21, SIEGE_TANK×32, SIEGE_TANK×22, SIEGE_TANK×20, SIEGE_TANK×22, HELI×30, THE_GENERAL×18, HELI×28, SPECOPS×26, DRONE×28, SPECOPS×30, SIEGE_TANK×28 |
| 🟥 | Forgotten Warband | random | Modern 88%, Future 6%, Industrial 5% | ⬛ 0/38 (0%) | SPECOPS×19, DRONE×3 | SPECOPS×31, THE_GENERAL×18, SPECOPS×21, SPECOPS×29, SPECOPS×25, DRONE×30, SIEGE_TANK×20, SIEGE_TANK×30, SIEGE_TANK×24, SOLDIER×25, HELI×26, SIEGE_TANK×32, SPECOPS×30, SIEGE_TANK×22, SPECOPS×28, SIEGE_TANK×22, SPECOPS×29, SIEGE_TANK×20 |
| 🟥 | Drunken Raiders | random | Modern 77%, Future 12%, Industrial 11% | ⬛ 0/38 (0%) | SPECOPS×19 | SPECOPS×21, SIEGE_TANK×30, SPECOPS×33, SOLDIER×29, SIEGE_TANK×34, SPECOPS×29, SPECOPS×33, SOLDIER×22, MECH_WARRIOR×24, SPECOPS×23, SIEGE_TANK×24, HELI×20, THE_GENERAL×18, DRONE×33, SPECOPS×33, SIEGE_TANK×24, SIEGE_TANK×30 |
| 🟥 | Hungry Invaders | random | Modern 78%, Industrial 14%, Future 8% | ⬛ 0/38 (0%) | SPECOPS×16, SOLDIER×7 | SPECOPS×25, HELI×32, SMALL_TANK×26, SPECOPS×22, HELI×22, SPECOPS×20, SPECOPS×23, SPECOPS×21, HELI×24, SPECOPS×21, THE_GENERAL×18, DRONE×29, HELI×34, SMALL_TANK×28, SPECOPS×21, SPECOPS×20 |
| 🟥 | Lazy Raiders | random | Modern 88%, Future 12% | ⬛ 0/38 (0%) | SOLDIER×10, SPECOPS×5, THE_GENERAL×1 | THE_GENERAL×18, SPECOPS×20, SIEGE_TANK×20, SPECOPS×31, SIEGE_TANK×26, HELI×28, SIEGE_TANK×34, SPECOPS×25, SPECOPS×26, HELI×22, SPECOPS×27, HELI×22, MECH_WARRIOR×27, HELI×24, HELI×32, MECH_WARRIOR×30, SPECOPS×32, HELI×22 |
| 🟥 | Unlucky Raiders | random | Modern 88%, Future 12% | ⬛ 0/38 (0%) | SPECOPS×17, DRONE×7 | SIEGE_TANK×32, SPECOPS×21, SIEGE_TANK×22, SIEGE_TANK×22, SIEGE_TANK×20, HELI×24, SIEGE_TANK×26, SPECOPS×29, DRONE×34, DRONE×22, HELI×30, SIEGE_TANK×28, SPECOPS×29, THE_GENERAL×18, SPECOPS×26, SPECOPS×30, SIEGE_TANK×30, HELI×24 |
| 🟥 | Bored Mercenaries | random | Modern 72%, Industrial 15%, Future 13% | ⬛ 0/38 (0%) | SOLDIER×19, MECH_WARRIOR×4, SPECOPS×2 | THE_GENERAL×18, SIEGE_TANK×28, TRANSPORTER×20, SIEGE_TANK×32, SPECOPS×22, MECH_WARRIOR×33, SIEGE_TANK×22, HELI×26, HELI×22, HELI×32, MECH_WARRIOR×24, HELI×30, SIEGE_TANK×34, SOLDIER×23, SPECOPS×29, MOTORBIKE×26, SIEGE_TANK×32 |
| 🟥 | Unlucky Raiders | random | Modern 87%, Industrial 7%, Future 6% | ⬛ 0/38 (0%) | SOLDIER×14, SPECOPS×12 | SPECOPS×23, SPECOPS×21, HELI×32, SIEGE_TANK×28, SIEGE_TANK×34, SPECOPS×26, SPECOPS×27, HELI×24, SPECOPS×32, DRONE×23, SIEGE_TANK×22, SPECOPS×24, SIEGE_TANK×26, THE_GENERAL×18, SIEGE_TANK×32, TRANSPORTER×30 |

### Future

#### Weak Modern

| Tower Era Distribution (33 towers) | Towers |
|---|---|
| Modern 48% (16), Industrial 30% (10), Future 12% (4), Iron Age 6% (2), Renaissance 3% (1) | FLAME_THROWER×10, MG_TOWER×7, RADAR_TOWER×5, ANTI_AIR_TOWER×4, LASER_TOWER×4, COLD_TOWER×2, ICE_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟥 | Mech Uprising | hardcoded | Future 100% | ⬛ 0/28 (0%) | DRONE×13, SPECOPS×5, MECH_WARRIOR×2 | MECH_WARRIOR×18, DRONE×18, MECH_WARRIOR×19, MECH_WARRIOR×19, MECH_WARRIOR×20, DRONE×20, MECH_WARRIOR×21, DRONE×21, MECH_WARRIOR×21, DRONE×22, MECH_WARRIOR×22, DRONE×23, MECH_WARRIOR×23, MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×24, DRONE×25, MECH_WARRIOR×25, DRONE×26, DRONE×26, MECH_WARRIOR×27, DRONE×27, DRONE×27, MECH_WARRIOR×28, DRONE×28, MECH_WARRIOR×29, DRONE×29, MECH_WARRIOR×30, DRONE×30 |
| 🟥 | Drone Swarm | hardcoded | Future 100% | ⬛ 0/28 (0%) | DRONE×17, SPECOPS×4, MECH_WARRIOR×1 | DRONE×18, MECH_WARRIOR×18, MECH_WARRIOR×19, DRONE×19, DRONE×20, DRONE×20, MECH_WARRIOR×21, MECH_WARRIOR×21, MECH_WARRIOR×22, MECH_WARRIOR×22, DRONE×22, MECH_WARRIOR×23, MECH_WARRIOR×23, DRONE×24, MECH_WARRIOR×24, DRONE×25, MECH_WARRIOR×25, MECH_WARRIOR×26, MECH_WARRIOR×26, DRONE×26, MECH_WARRIOR×27, MECH_WARRIOR×27, MECH_WARRIOR×28, DRONE×28, DRONE×29, DRONE×29, DRONE×30, DRONE×30 |
| 🟥 | Future Shock | hardcoded | Future 100% | ⬛ 0/28 (0%) | DRONE×14, SPECOPS×7 | MECH_WARRIOR×18, MECH_WARRIOR×18, DRONE×19, DRONE×19, MECH_WARRIOR×20, DRONE×20, MECH_WARRIOR×21, MECH_WARRIOR×21, MECH_WARRIOR×21, DRONE×22, MECH_WARRIOR×22, MECH_WARRIOR×23, DRONE×23, MECH_WARRIOR×24, DRONE×24, DRONE×24, MECH_WARRIOR×25, DRONE×25, MECH_WARRIOR×26, DRONE×26, DRONE×27, MECH_WARRIOR×27, DRONE×27, DRONE×28, DRONE×28, MECH_WARRIOR×29, DRONE×29, MECH_WARRIOR×30 |
| 🟥 | Shrieking Horde | random | Future 96%, Modern 4% | ⬛ 0/28 (0%) | DRONE×27, SPECOPS×1 | DRONE×30, MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×29, DRONE×26, DRONE×28, MECH_WARRIOR×24, DRONE×22, MECH_WARRIOR×33, MECH_WARRIOR×30, DRONE×29, DRONE×31, DRONE×20, THE_GENERAL×18, MECH_WARRIOR×27, DRONE×27, DRONE×23, MECH_WARRIOR×27 |
| 🟥 | Shrieking Horde | random | Future 96%, Modern 4% | ⬛ 0/28 (0%) | DRONE×27, SPECOPS×1 | DRONE×30, MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×29, DRONE×26, DRONE×28, MECH_WARRIOR×24, DRONE×22, MECH_WARRIOR×33, MECH_WARRIOR×30, DRONE×29, DRONE×31, DRONE×20, THE_GENERAL×18, MECH_WARRIOR×27, DRONE×27, DRONE×23, MECH_WARRIOR×27 |
| 🟥 | Rampaging Rabble | random | Future 96%, Modern 4% | ⬛ 0/28 (0%) | DRONE×19, SPECOPS×3, MECH_WARRIOR×1 | MECH_WARRIOR×21, DRONE×34, THE_GENERAL×18, DRONE×31, DRONE×29, MECH_WARRIOR×27, MECH_WARRIOR×27, DRONE×26, DRONE×34, DRONE×26, DRONE×22, MECH_WARRIOR×33, DRONE×21, MECH_WARRIOR×33, DRONE×20, DRONE×31, DRONE×33, MECH_WARRIOR×21, MECH_WARRIOR×27 |
| 🟥 | Weary Plunderers | random | Future 96%, Modern 4% | ⬛ 0/28 (0%) | DRONE×24, SPECOPS×2 | DRONE×31, DRONE×30, DRONE×32, MECH_WARRIOR×27, MECH_WARRIOR×24, DRONE×23, DRONE×30, MECH_WARRIOR×27, MECH_WARRIOR×24, MECH_WARRIOR×30, MECH_WARRIOR×21, MECH_WARRIOR×27, DRONE×20, THE_GENERAL×18, MECH_WARRIOR×24, DRONE×31, DRONE×27, DRONE×32, DRONE×33 |
| 🟥 | Petty Bandits | random | Future 96%, Modern 4% | ⬛ 0/28 (0%) | DRONE×10, MECH_WARRIOR×3, SPECOPS×3 | MECH_WARRIOR×21, MECH_WARRIOR×27, DRONE×31, MECH_WARRIOR×21, DRONE×27, MECH_WARRIOR×30, MECH_WARRIOR×33, DRONE×31, DRONE×30, DRONE×26, MECH_WARRIOR×24, MECH_WARRIOR×30, DRONE×23, MECH_WARRIOR×27, DRONE×25, MECH_WARRIOR×30, MECH_WARRIOR×27, MECH_WARRIOR×24, DRONE×25, HELI×22 |
| 🟥 | Relentless Mob | random | Future 86%, Modern 14% | ⬛ 0/28 (0%) | DRONE×17, MECH_WARRIOR×2, SPECOPS×2 | MECH_WARRIOR×24, DRONE×31, DRONE×24, SPECOPS×23, MECH_WARRIOR×30, DRONE×26, DRONE×31, MECH_WARRIOR×24, DRONE×32, MECH_WARRIOR×21, DRONE×32, THE_GENERAL×18, MECH_WARRIOR×30, MECH_WARRIOR×24, HELI×32, DRONE×32, DRONE×26, DRONE×26, DRONE×31 |
| 🟥 | Rowdy Plunderers | random | Future 94%, Modern 6% | ⬛ 0/28 (0%) | DRONE×12, MECH_WARRIOR×3, SPECOPS×3 | MECH_WARRIOR×30, DRONE×26, DRONE×26, MECH_WARRIOR×30, DRONE×20, DRONE×28, DRONE×20, MECH_WARRIOR×27, MECH_WARRIOR×33, MECH_WARRIOR×33, MECH_WARRIOR×24, HELI×28, DRONE×33, DRONE×34, MECH_WARRIOR×33, MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×23 |
| 🟥 | Noisy Barbarians | random | Future 92%, Modern 8% | ⬛ 0/28 (0%) | DRONE×16, MECH_WARRIOR×2, SPECOPS×2 | DRONE×28, MECH_WARRIOR×24, DRONE×31, MECH_WARRIOR×21, MECH_WARRIOR×24, DRONE×24, DRONE×22, MECH_WARRIOR×27, MECH_WARRIOR×24, DRONE×26, MECH_WARRIOR×27, MECH_WARRIOR×24, DRONE×28, MECH_WARRIOR×24, HELI×30 |
| 🟥 | Lazy Raiders | random | Future 90%, Modern 10% | ⬛ 0/28 (0%) | DRONE×20, SPECOPS×2, MECH_WARRIOR×1 | DRONE×31, DRONE×28, THE_GENERAL×18, DRONE×27, MECH_WARRIOR×24, MECH_WARRIOR×27, DRONE×31, DRONE×27, DRONE×22, HELI×22, DRONE×22, MECH_WARRIOR×30, DRONE×25, MECH_WARRIOR×21, DRONE×28 |
| 🟥 | Crude Invaders | random | Future 81%, Modern 19% | ⬛ 0/28 (0%) | DRONE×17, SOLDIER×3, SPECOPS×2, MECH_WARRIOR×1 | MECH_WARRIOR×30, HELI×26, MECH_WARRIOR×24, DRONE×29, MECH_WARRIOR×21, SIEGE_TANK×32, DRONE×20, HELI×22, MECH_WARRIOR×24, DRONE×32, MECH_WARRIOR×30, MECH_WARRIOR×30, MECH_WARRIOR×33, MECH_WARRIOR×24, DRONE×28, MECH_WARRIOR×24 |
| 🟥 | Crude Invaders | random | Future 83%, Modern 17% | ⬛ 0/28 (0%) | DRONE×22, MECH_WARRIOR×2 | DRONE×25, DRONE×23, SPECOPS×26, SIEGE_TANK×22, SIEGE_TANK×30, MECH_WARRIOR×27, DRONE×25, DRONE×24, DRONE×26, DRONE×23, MECH_WARRIOR×33, MECH_WARRIOR×27, MECH_WARRIOR×33, MECH_WARRIOR×21, MECH_WARRIOR×24, DRONE×20, MECH_WARRIOR×21, DRONE×25 |
| 🟥 | Petty Bandits | random | Future 88%, Modern 12% | ⬛ 0/28 (0%) | DRONE×8, SPECOPS×6, MECH_WARRIOR×2 | MECH_WARRIOR×24, DRONE×26, DRONE×22, SPECOPS×28, SIEGE_TANK×30, DRONE×27, MECH_WARRIOR×21, DRONE×28, MECH_WARRIOR×27, DRONE×28, MECH_WARRIOR×24, MECH_WARRIOR×33, MECH_WARRIOR×30, MECH_WARRIOR×30, MECH_WARRIOR×24, MECH_WARRIOR×30, DRONE×31, MECH_WARRIOR×27 |
| 🟥 | Bored Mercenaries | random | Future 94%, Modern 6% | ⬛ 0/28 (0%) | SOLDIER×13, SPECOPS×7, DRONE×1 | MECH_WARRIOR×33, MECH_WARRIOR×27, HELI×24, MECH_WARRIOR×27, DRONE×25, DRONE×26, DRONE×23, MECH_WARRIOR×24, DRONE×24, MECH_WARRIOR×21, DRONE×30, MECH_WARRIOR×24, DRONE×28, MECH_WARRIOR×21, MECH_WARRIOR×30, DRONE×24 |
| 🟥 | Wandering Pillagers | random | Future 90%, Modern 10% | ⬛ 0/28 (0%) | MECH_WARRIOR×4, SPECOPS×4, DRONE×3, SOLDIER×1 | DRONE×28, MECH_WARRIOR×24, DRONE×20, DRONE×21, MECH_WARRIOR×21, DRONE×20, MECH_WARRIOR×27, MECH_WARRIOR×24, HELI×20, DRONE×24, DRONE×31, MECH_WARRIOR×24, DRONE×28, SPECOPS×24, DRONE×28, MECH_WARRIOR×30, DRONE×21, MECH_WARRIOR×24 |
| 🟥 | Drunken Raiders | random | Future 91%, Modern 9% | ⬛ 0/28 (0%) | DRONE×24, SPECOPS×2 | DRONE×31, MECH_WARRIOR×24, MECH_WARRIOR×30, MECH_WARRIOR×24, DRONE×33, DRONE×29, MECH_WARRIOR×21, DRONE×28, SPECOPS×21, DRONE×23, DRONE×26, DRONE×22, MECH_WARRIOR×24, THE_GENERAL×18, MECH_WARRIOR×24, DRONE×21, MECH_WARRIOR×24 |
| 🟥 | Howling Savages | random | Future 88%, Modern 12% | ⬛ 0/28 (0%) | DRONE×21, SOLDIER×3, MECH_WARRIOR×1 | DRONE×27, DRONE×20, DRONE×25, HELI×20, DRONE×28, DRONE×29, MECH_WARRIOR×24, DRONE×23, MECH_WARRIOR×33, DRONE×26, DRONE×22, MECH_WARRIOR×24, DRONE×31, MECH_WARRIOR×33, HELI×30, DRONE×21 |
| 🟥 | Clumsy Attackers | random | Future 94%, Modern 6% | ⬛ 0/28 (0%) | DRONE×18, SPECOPS×3, MECH_WARRIOR×1 | DRONE×28, DRONE×24, DRONE×28, DRONE×29, MECH_WARRIOR×27, MECH_WARRIOR×24, DRONE×33, MECH_WARRIOR×30, DRONE×25, DRONE×33, DRONE×30, MECH_WARRIOR×21, MECH_WARRIOR×24, HELI×32, MECH_WARRIOR×27, DRONE×32, MECH_WARRIOR×30, DRONE×32 |
| 🟥 | Blundering Invaders | random | Future 95%, Modern 5% | ⬛ 0/28 (0%) | DRONE×12, SPECOPS×5, MECH_WARRIOR×2 | DRONE×30, MECH_WARRIOR×24, MECH_WARRIOR×21, DRONE×29, SIEGE_TANK×26, DRONE×21, DRONE×21, MECH_WARRIOR×27, DRONE×29, MECH_WARRIOR×27, DRONE×32, MECH_WARRIOR×24, DRONE×23, DRONE×23, MECH_WARRIOR×24, MECH_WARRIOR×30, DRONE×26, MECH_WARRIOR×24, MECH_WARRIOR×27 |
| 🟥 | Bored Mercenaries | random | Future 89%, Modern 11% | ⬛ 0/28 (0%) | DRONE×19, SPECOPS×5 | MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×24, DRONE×31, DRONE×22, THE_GENERAL×18, DRONE×22, MECH_WARRIOR×24, MECH_WARRIOR×24, MECH_WARRIOR×33, SIEGE_TANK×32, MECH_WARRIOR×30, DRONE×33, DRONE×31, DRONE×29, DRONE×34, MECH_WARRIOR×24 |
| 🟥 | Frenzied Pillagers | random | Future 94%, Modern 6% | ⬛ 0/28 (0%) | DRONE×28 | DRONE×28, DRONE×22, MECH_WARRIOR×33, MECH_WARRIOR×30, DRONE×28, DRONE×29, MECH_WARRIOR×27, DRONE×29, MECH_WARRIOR×27, DRONE×21, SPECOPS×22, MECH_WARRIOR×33, DRONE×22, MECH_WARRIOR×24, MECH_WARRIOR×21 |

#### S1 Limperium

| Tower Era Distribution (58 towers) | Towers |
|---|---|
| Modern 69% (40), Future 17% (10), Iron Age 14% (8) | MG_TOWER×35, ROCKET_TOWER×10, COLD_TOWER×8, NAPALM_THROWER×5 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟥 | Mech Uprising | hardcoded | Future 100% | ⬛ 0/48 (0%) | MECH_WARRIOR×11, SPECOPS×2 | MECH_WARRIOR×18, DRONE×18, MECH_WARRIOR×19, MECH_WARRIOR×19, MECH_WARRIOR×20, DRONE×20, MECH_WARRIOR×21, DRONE×21, MECH_WARRIOR×21, DRONE×22, MECH_WARRIOR×22, DRONE×23, MECH_WARRIOR×23, MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×24, DRONE×25, MECH_WARRIOR×25, DRONE×26, DRONE×26, MECH_WARRIOR×27, DRONE×27, DRONE×27, MECH_WARRIOR×28, DRONE×28, MECH_WARRIOR×29, DRONE×29, MECH_WARRIOR×30, DRONE×30 |
| 🟥 | Drone Swarm | hardcoded | Future 100% | ⬛ 0/48 (0%) | MECH_WARRIOR×9, SPECOPS×6 | DRONE×18, MECH_WARRIOR×18, MECH_WARRIOR×19, DRONE×19, DRONE×20, DRONE×20, MECH_WARRIOR×21, MECH_WARRIOR×21, MECH_WARRIOR×22, MECH_WARRIOR×22, DRONE×22, MECH_WARRIOR×23, MECH_WARRIOR×23, DRONE×24, MECH_WARRIOR×24, DRONE×25, MECH_WARRIOR×25, MECH_WARRIOR×26, MECH_WARRIOR×26, DRONE×26, MECH_WARRIOR×27, MECH_WARRIOR×27, MECH_WARRIOR×28, DRONE×28, DRONE×29, DRONE×29, DRONE×30, DRONE×30 |
| 🟥 | Future Shock | hardcoded | Future 100% | ⬛ 0/48 (0%) | MECH_WARRIOR×9, SPECOPS×6 | MECH_WARRIOR×18, MECH_WARRIOR×18, DRONE×19, DRONE×19, MECH_WARRIOR×20, DRONE×20, MECH_WARRIOR×21, MECH_WARRIOR×21, MECH_WARRIOR×21, DRONE×22, MECH_WARRIOR×22, MECH_WARRIOR×23, DRONE×23, MECH_WARRIOR×24, DRONE×24, DRONE×24, MECH_WARRIOR×25, DRONE×25, MECH_WARRIOR×26, DRONE×26, DRONE×27, MECH_WARRIOR×27, DRONE×27, DRONE×28, DRONE×28, MECH_WARRIOR×29, DRONE×29, MECH_WARRIOR×30 |
| 🟥 | Shrieking Horde | random | Future 96%, Modern 4% | ⬛ 0/48 (0%) | MECH_WARRIOR×12, SPECOPS×1 | DRONE×30, MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×29, DRONE×26, DRONE×28, MECH_WARRIOR×24, DRONE×22, MECH_WARRIOR×33, MECH_WARRIOR×30, DRONE×29, DRONE×31, DRONE×20, THE_GENERAL×18, MECH_WARRIOR×27, DRONE×27, DRONE×23, MECH_WARRIOR×27 |
| 🟥 | Shrieking Horde | random | Future 96%, Modern 4% | ⬛ 0/48 (0%) | MECH_WARRIOR×12, SPECOPS×1 | DRONE×30, MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×29, DRONE×26, DRONE×28, MECH_WARRIOR×24, DRONE×22, MECH_WARRIOR×33, MECH_WARRIOR×30, DRONE×29, DRONE×31, DRONE×20, THE_GENERAL×18, MECH_WARRIOR×27, DRONE×27, DRONE×23, MECH_WARRIOR×27 |
| 🟥 | Rampaging Rabble | random | Future 96%, Modern 4% | ⬛ 0/48 (0%) | MECH_WARRIOR×10, SPECOPS×4 | MECH_WARRIOR×21, DRONE×34, THE_GENERAL×18, DRONE×31, DRONE×29, MECH_WARRIOR×27, MECH_WARRIOR×27, DRONE×26, DRONE×34, DRONE×26, DRONE×22, MECH_WARRIOR×33, DRONE×21, MECH_WARRIOR×33, DRONE×20, DRONE×31, DRONE×33, MECH_WARRIOR×21, MECH_WARRIOR×27 |
| 🟥 | Weary Plunderers | random | Future 96%, Modern 4% | ⬛ 0/48 (0%) | MECH_WARRIOR×11, SPECOPS×3 | DRONE×31, DRONE×30, DRONE×32, MECH_WARRIOR×27, MECH_WARRIOR×24, DRONE×23, DRONE×30, MECH_WARRIOR×27, MECH_WARRIOR×24, MECH_WARRIOR×30, MECH_WARRIOR×21, MECH_WARRIOR×27, DRONE×20, THE_GENERAL×18, MECH_WARRIOR×24, DRONE×31, DRONE×27, DRONE×32, DRONE×33 |
| 🟥 | Petty Bandits | random | Future 96%, Modern 4% | ⬛ 0/48 (0%) | MECH_WARRIOR×11, SPECOPS×2 | MECH_WARRIOR×21, MECH_WARRIOR×27, DRONE×31, MECH_WARRIOR×21, DRONE×27, MECH_WARRIOR×30, MECH_WARRIOR×33, DRONE×31, DRONE×30, DRONE×26, MECH_WARRIOR×24, MECH_WARRIOR×30, DRONE×23, MECH_WARRIOR×27, DRONE×25, MECH_WARRIOR×30, MECH_WARRIOR×27, MECH_WARRIOR×24, DRONE×25, HELI×22 |
| 🟥 | Relentless Mob | random | Future 86%, Modern 14% | ⬛ 0/48 (0%) | MECH_WARRIOR×11, SPECOPS×2 | MECH_WARRIOR×24, DRONE×31, DRONE×24, SPECOPS×23, MECH_WARRIOR×30, DRONE×26, DRONE×31, MECH_WARRIOR×24, DRONE×32, MECH_WARRIOR×21, DRONE×32, THE_GENERAL×18, MECH_WARRIOR×30, MECH_WARRIOR×24, HELI×32, DRONE×32, DRONE×26, DRONE×26, DRONE×31 |
| 🟥 | Rowdy Plunderers | random | Future 94%, Modern 6% | ⬛ 0/48 (0%) | MECH_WARRIOR×11, SPECOPS×2 | MECH_WARRIOR×30, DRONE×26, DRONE×26, MECH_WARRIOR×30, DRONE×20, DRONE×28, DRONE×20, MECH_WARRIOR×27, MECH_WARRIOR×33, MECH_WARRIOR×33, MECH_WARRIOR×24, HELI×28, DRONE×33, DRONE×34, MECH_WARRIOR×33, MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×23 |
| 🟥 | Noisy Barbarians | random | Future 92%, Modern 8% | ⬛ 0/48 (0%) | MECH_WARRIOR×11, SPECOPS×2 | DRONE×28, MECH_WARRIOR×24, DRONE×31, MECH_WARRIOR×21, MECH_WARRIOR×24, DRONE×24, DRONE×22, MECH_WARRIOR×27, MECH_WARRIOR×24, DRONE×26, MECH_WARRIOR×27, MECH_WARRIOR×24, DRONE×28, MECH_WARRIOR×24, HELI×30 |
| 🟥 | Lazy Raiders | random | Future 90%, Modern 10% | ⬛ 0/48 (0%) | MECH_WARRIOR×11, SPECOPS×2 | DRONE×31, DRONE×28, THE_GENERAL×18, DRONE×27, MECH_WARRIOR×24, MECH_WARRIOR×27, DRONE×31, DRONE×27, DRONE×22, HELI×22, DRONE×22, MECH_WARRIOR×30, DRONE×25, MECH_WARRIOR×21, DRONE×28 |
| 🟥 | Crude Invaders | random | Future 81%, Modern 19% | ⬛ 0/48 (0%) | MECH_WARRIOR×12, SPECOPS×1 | MECH_WARRIOR×30, HELI×26, MECH_WARRIOR×24, DRONE×29, MECH_WARRIOR×21, SIEGE_TANK×32, DRONE×20, HELI×22, MECH_WARRIOR×24, DRONE×32, MECH_WARRIOR×30, MECH_WARRIOR×30, MECH_WARRIOR×33, MECH_WARRIOR×24, DRONE×28, MECH_WARRIOR×24 |
| 🟥 | Crude Invaders | random | Future 83%, Modern 17% | ⬛ 0/48 (0%) | MECH_WARRIOR×11, SPECOPS×2 | DRONE×25, DRONE×23, SPECOPS×26, SIEGE_TANK×22, SIEGE_TANK×30, MECH_WARRIOR×27, DRONE×25, DRONE×24, DRONE×26, DRONE×23, MECH_WARRIOR×33, MECH_WARRIOR×27, MECH_WARRIOR×33, MECH_WARRIOR×21, MECH_WARRIOR×24, DRONE×20, MECH_WARRIOR×21, DRONE×25 |
| 🟥 | Petty Bandits | random | Future 88%, Modern 12% | ⬛ 0/48 (0%) | MECH_WARRIOR×9, SPECOPS×6 | MECH_WARRIOR×24, DRONE×26, DRONE×22, SPECOPS×28, SIEGE_TANK×30, DRONE×27, MECH_WARRIOR×21, DRONE×28, MECH_WARRIOR×27, DRONE×28, MECH_WARRIOR×24, MECH_WARRIOR×33, MECH_WARRIOR×30, MECH_WARRIOR×30, MECH_WARRIOR×24, MECH_WARRIOR×30, DRONE×31, MECH_WARRIOR×27 |
| 🟥 | Bored Mercenaries | random | Future 94%, Modern 6% | ⬛ 0/48 (0%) | MECH_WARRIOR×12 | MECH_WARRIOR×33, MECH_WARRIOR×27, HELI×24, MECH_WARRIOR×27, DRONE×25, DRONE×26, DRONE×23, MECH_WARRIOR×24, DRONE×24, MECH_WARRIOR×21, DRONE×30, MECH_WARRIOR×24, DRONE×28, MECH_WARRIOR×21, MECH_WARRIOR×30, DRONE×24 |
| 🟥 | Wandering Pillagers | random | Future 90%, Modern 10% | ⬛ 0/48 (0%) | MECH_WARRIOR×12, SPECOPS×1 | DRONE×28, MECH_WARRIOR×24, DRONE×20, DRONE×21, MECH_WARRIOR×21, DRONE×20, MECH_WARRIOR×27, MECH_WARRIOR×24, HELI×20, DRONE×24, DRONE×31, MECH_WARRIOR×24, DRONE×28, SPECOPS×24, DRONE×28, MECH_WARRIOR×30, DRONE×21, MECH_WARRIOR×24 |
| 🟥 | Drunken Raiders | random | Future 91%, Modern 9% | ⬛ 0/48 (0%) | MECH_WARRIOR×10, SPECOPS×4 | DRONE×31, MECH_WARRIOR×24, MECH_WARRIOR×30, MECH_WARRIOR×24, DRONE×33, DRONE×29, MECH_WARRIOR×21, DRONE×28, SPECOPS×21, DRONE×23, DRONE×26, DRONE×22, MECH_WARRIOR×24, THE_GENERAL×18, MECH_WARRIOR×24, DRONE×21, MECH_WARRIOR×24 |
| 🟥 | Howling Savages | random | Future 88%, Modern 12% | ⬛ 0/48 (0%) | MECH_WARRIOR×12 | DRONE×27, DRONE×20, DRONE×25, HELI×20, DRONE×28, DRONE×29, MECH_WARRIOR×24, DRONE×23, MECH_WARRIOR×33, DRONE×26, DRONE×22, MECH_WARRIOR×24, DRONE×31, MECH_WARRIOR×33, HELI×30, DRONE×21 |
| 🟥 | Clumsy Attackers | random | Future 94%, Modern 6% | ⬛ 0/48 (0%) | MECH_WARRIOR×11, SPECOPS×2 | DRONE×28, DRONE×24, DRONE×28, DRONE×29, MECH_WARRIOR×27, MECH_WARRIOR×24, DRONE×33, MECH_WARRIOR×30, DRONE×25, DRONE×33, DRONE×30, MECH_WARRIOR×21, MECH_WARRIOR×24, HELI×32, MECH_WARRIOR×27, DRONE×32, MECH_WARRIOR×30, DRONE×32 |
| 🟥 | Blundering Invaders | random | Future 95%, Modern 5% | ⬛ 0/48 (0%) | MECH_WARRIOR×9, SPECOPS×6 | DRONE×30, MECH_WARRIOR×24, MECH_WARRIOR×21, DRONE×29, SIEGE_TANK×26, DRONE×21, DRONE×21, MECH_WARRIOR×27, DRONE×29, MECH_WARRIOR×27, DRONE×32, MECH_WARRIOR×24, DRONE×23, DRONE×23, MECH_WARRIOR×24, MECH_WARRIOR×30, DRONE×26, MECH_WARRIOR×24, MECH_WARRIOR×27 |
| 🟥 | Bored Mercenaries | random | Future 89%, Modern 11% | ⬛ 0/48 (0%) | MECH_WARRIOR×10, SPECOPS×4 | MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×24, DRONE×31, DRONE×22, THE_GENERAL×18, DRONE×22, MECH_WARRIOR×24, MECH_WARRIOR×24, MECH_WARRIOR×33, SIEGE_TANK×32, MECH_WARRIOR×30, DRONE×33, DRONE×31, DRONE×29, DRONE×34, MECH_WARRIOR×24 |
| 🟥 | Frenzied Pillagers | random | Future 94%, Modern 6% | ⬛ 0/48 (0%) | MECH_WARRIOR×12 | DRONE×28, DRONE×22, MECH_WARRIOR×33, MECH_WARRIOR×30, DRONE×28, DRONE×29, MECH_WARRIOR×27, DRONE×29, MECH_WARRIOR×27, DRONE×21, SPECOPS×22, MECH_WARRIOR×33, DRONE×22, MECH_WARRIOR×24, MECH_WARRIOR×21 |

#### S2 Gempire

| Tower Era Distribution (66 towers) | Towers |
|---|---|
| Modern 61% (40), Industrial 21% (14), Iron Age 12% (8), Future 5% (3), Renaissance 2% (1) | RADAR_TOWER×29, FLAME_THROWER×13, ANTI_AIR_TOWER×11, COLD_TOWER×8, LASER_TOWER×3, ICE_TOWER×1, SHOCK_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟥 | Mech Uprising | hardcoded | Future 100% | ⬛ 0/38 (0%) | DRONE×8, MECH_WARRIOR×5, SPECOPS×5 | MECH_WARRIOR×18, DRONE×18, MECH_WARRIOR×19, MECH_WARRIOR×19, MECH_WARRIOR×20, DRONE×20, MECH_WARRIOR×21, DRONE×21, MECH_WARRIOR×21, DRONE×22, MECH_WARRIOR×22, DRONE×23, MECH_WARRIOR×23, MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×24, DRONE×25, MECH_WARRIOR×25, DRONE×26, DRONE×26, MECH_WARRIOR×27, DRONE×27, DRONE×27, MECH_WARRIOR×28, DRONE×28, MECH_WARRIOR×29, DRONE×29, MECH_WARRIOR×30, DRONE×30 |
| 🟥 | Drone Swarm | hardcoded | Future 100% | ⬛ 0/38 (0%) | SPECOPS×11, DRONE×5, MECH_WARRIOR×3 | DRONE×18, MECH_WARRIOR×18, MECH_WARRIOR×19, DRONE×19, DRONE×20, DRONE×20, MECH_WARRIOR×21, MECH_WARRIOR×21, MECH_WARRIOR×22, MECH_WARRIOR×22, DRONE×22, MECH_WARRIOR×23, MECH_WARRIOR×23, DRONE×24, MECH_WARRIOR×24, DRONE×25, MECH_WARRIOR×25, MECH_WARRIOR×26, MECH_WARRIOR×26, DRONE×26, MECH_WARRIOR×27, MECH_WARRIOR×27, MECH_WARRIOR×28, DRONE×28, DRONE×29, DRONE×29, DRONE×30, DRONE×30 |
| 🟥 | Future Shock | hardcoded | Future 100% | ⬛ 0/38 (0%) | SPECOPS×11, DRONE×6, MECH_WARRIOR×3 | MECH_WARRIOR×18, MECH_WARRIOR×18, DRONE×19, DRONE×19, MECH_WARRIOR×20, DRONE×20, MECH_WARRIOR×21, MECH_WARRIOR×21, MECH_WARRIOR×21, DRONE×22, MECH_WARRIOR×22, MECH_WARRIOR×23, DRONE×23, MECH_WARRIOR×24, DRONE×24, DRONE×24, MECH_WARRIOR×25, DRONE×25, MECH_WARRIOR×26, DRONE×26, DRONE×27, MECH_WARRIOR×27, DRONE×27, DRONE×28, DRONE×28, MECH_WARRIOR×29, DRONE×29, MECH_WARRIOR×30 |
| 🟥 | Shrieking Horde | random | Future 96%, Modern 4% | ⬛ 0/38 (0%) | DRONE×18, SPECOPS×7, MECH_WARRIOR×2 | DRONE×30, MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×29, DRONE×26, DRONE×28, MECH_WARRIOR×24, DRONE×22, MECH_WARRIOR×33, MECH_WARRIOR×30, DRONE×29, DRONE×31, DRONE×20, THE_GENERAL×18, MECH_WARRIOR×27, DRONE×27, DRONE×23, MECH_WARRIOR×27 |
| 🟥 | Shrieking Horde | random | Future 96%, Modern 4% | ⬛ 0/38 (0%) | DRONE×18, SPECOPS×7, MECH_WARRIOR×2 | DRONE×30, MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×29, DRONE×26, DRONE×28, MECH_WARRIOR×24, DRONE×22, MECH_WARRIOR×33, MECH_WARRIOR×30, DRONE×29, DRONE×31, DRONE×20, THE_GENERAL×18, MECH_WARRIOR×27, DRONE×27, DRONE×23, MECH_WARRIOR×27 |
| 🟥 | Rampaging Rabble | random | Future 96%, Modern 4% | ⬛ 0/38 (0%) | DRONE×23, MECH_WARRIOR×3, SPECOPS×3 | MECH_WARRIOR×21, DRONE×34, THE_GENERAL×18, DRONE×31, DRONE×29, MECH_WARRIOR×27, MECH_WARRIOR×27, DRONE×26, DRONE×34, DRONE×26, DRONE×22, MECH_WARRIOR×33, DRONE×21, MECH_WARRIOR×33, DRONE×20, DRONE×31, DRONE×33, MECH_WARRIOR×21, MECH_WARRIOR×27 |
| 🟥 | Weary Plunderers | random | Future 96%, Modern 4% | ⬛ 0/38 (0%) | SPECOPS×7, MECH_WARRIOR×6 | DRONE×31, DRONE×30, DRONE×32, MECH_WARRIOR×27, MECH_WARRIOR×24, DRONE×23, DRONE×30, MECH_WARRIOR×27, MECH_WARRIOR×24, MECH_WARRIOR×30, MECH_WARRIOR×21, MECH_WARRIOR×27, DRONE×20, THE_GENERAL×18, MECH_WARRIOR×24, DRONE×31, DRONE×27, DRONE×32, DRONE×33 |
| 🟥 | Petty Bandits | random | Future 96%, Modern 4% | ⬛ 0/38 (0%) | SPECOPS×8, DRONE×8, MECH_WARRIOR×4 | MECH_WARRIOR×21, MECH_WARRIOR×27, DRONE×31, MECH_WARRIOR×21, DRONE×27, MECH_WARRIOR×30, MECH_WARRIOR×33, DRONE×31, DRONE×30, DRONE×26, MECH_WARRIOR×24, MECH_WARRIOR×30, DRONE×23, MECH_WARRIOR×27, DRONE×25, MECH_WARRIOR×30, MECH_WARRIOR×27, MECH_WARRIOR×24, DRONE×25, HELI×22 |
| 🟥 | Relentless Mob | random | Future 86%, Modern 14% | ⬛ 0/38 (0%) | DRONE×18, SPECOPS×8, MECH_WARRIOR×1 | MECH_WARRIOR×24, DRONE×31, DRONE×24, SPECOPS×23, MECH_WARRIOR×30, DRONE×26, DRONE×31, MECH_WARRIOR×24, DRONE×32, MECH_WARRIOR×21, DRONE×32, THE_GENERAL×18, MECH_WARRIOR×30, MECH_WARRIOR×24, HELI×32, DRONE×32, DRONE×26, DRONE×26, DRONE×31 |
| 🟥 | Rowdy Plunderers | random | Future 94%, Modern 6% | ⬛ 0/38 (0%) | MECH_WARRIOR×7, SPECOPS×5, DRONE×3 | MECH_WARRIOR×30, DRONE×26, DRONE×26, MECH_WARRIOR×30, DRONE×20, DRONE×28, DRONE×20, MECH_WARRIOR×27, MECH_WARRIOR×33, MECH_WARRIOR×33, MECH_WARRIOR×24, HELI×28, DRONE×33, DRONE×34, MECH_WARRIOR×33, MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×23 |
| 🟥 | Noisy Barbarians | random | Future 92%, Modern 8% | ⬛ 0/38 (0%) | DRONE×8, SPECOPS×6, MECH_WARRIOR×5 | DRONE×28, MECH_WARRIOR×24, DRONE×31, MECH_WARRIOR×21, MECH_WARRIOR×24, DRONE×24, DRONE×22, MECH_WARRIOR×27, MECH_WARRIOR×24, DRONE×26, MECH_WARRIOR×27, MECH_WARRIOR×24, DRONE×28, MECH_WARRIOR×24, HELI×30 |
| 🟥 | Lazy Raiders | random | Future 90%, Modern 10% | ⬛ 0/38 (0%) | DRONE×9, SPECOPS×7, MECH_WARRIOR×4 | DRONE×31, DRONE×28, THE_GENERAL×18, DRONE×27, MECH_WARRIOR×24, MECH_WARRIOR×27, DRONE×31, DRONE×27, DRONE×22, HELI×22, DRONE×22, MECH_WARRIOR×30, DRONE×25, MECH_WARRIOR×21, DRONE×28 |
| 🟥 | Crude Invaders | random | Future 81%, Modern 19% | ⬛ 0/38 (0%) | SPECOPS×8, DRONE×7, MECH_WARRIOR×4 | MECH_WARRIOR×30, HELI×26, MECH_WARRIOR×24, DRONE×29, MECH_WARRIOR×21, SIEGE_TANK×32, DRONE×20, HELI×22, MECH_WARRIOR×24, DRONE×32, MECH_WARRIOR×30, MECH_WARRIOR×30, MECH_WARRIOR×33, MECH_WARRIOR×24, DRONE×28, MECH_WARRIOR×24 |
| 🟥 | Crude Invaders | random | Future 83%, Modern 17% | ⬛ 0/38 (0%) | DRONE×10, MECH_WARRIOR×6, SPECOPS×2 | DRONE×25, DRONE×23, SPECOPS×26, SIEGE_TANK×22, SIEGE_TANK×30, MECH_WARRIOR×27, DRONE×25, DRONE×24, DRONE×26, DRONE×23, MECH_WARRIOR×33, MECH_WARRIOR×27, MECH_WARRIOR×33, MECH_WARRIOR×21, MECH_WARRIOR×24, DRONE×20, MECH_WARRIOR×21, DRONE×25 |
| 🟥 | Petty Bandits | random | Future 88%, Modern 12% | ⬛ 0/38 (0%) | SPECOPS×10, MECH_WARRIOR×4, DRONE×4 | MECH_WARRIOR×24, DRONE×26, DRONE×22, SPECOPS×28, SIEGE_TANK×30, DRONE×27, MECH_WARRIOR×21, DRONE×28, MECH_WARRIOR×27, DRONE×28, MECH_WARRIOR×24, MECH_WARRIOR×33, MECH_WARRIOR×30, MECH_WARRIOR×30, MECH_WARRIOR×24, MECH_WARRIOR×30, DRONE×31, MECH_WARRIOR×27 |
| 🟥 | Bored Mercenaries | random | Future 94%, Modern 6% | ⬛ 0/38 (0%) | DRONE×10, MECH_WARRIOR×6, SPECOPS×2 | MECH_WARRIOR×33, MECH_WARRIOR×27, HELI×24, MECH_WARRIOR×27, DRONE×25, DRONE×26, DRONE×23, MECH_WARRIOR×24, DRONE×24, MECH_WARRIOR×21, DRONE×30, MECH_WARRIOR×24, DRONE×28, MECH_WARRIOR×21, MECH_WARRIOR×30, DRONE×24 |
| 🟥 | Wandering Pillagers | random | Future 90%, Modern 10% | ⬛ 0/38 (0%) | DRONE×15, SPECOPS×4, MECH_WARRIOR×3, SOLDIER×3 | DRONE×28, MECH_WARRIOR×24, DRONE×20, DRONE×21, MECH_WARRIOR×21, DRONE×20, MECH_WARRIOR×27, MECH_WARRIOR×24, HELI×20, DRONE×24, DRONE×31, MECH_WARRIOR×24, DRONE×28, SPECOPS×24, DRONE×28, MECH_WARRIOR×30, DRONE×21, MECH_WARRIOR×24 |
| 🟥 | Drunken Raiders | random | Future 91%, Modern 9% | ⬛ 0/38 (0%) | DRONE×22, SPECOPS×5, MECH_WARRIOR×2 | DRONE×31, MECH_WARRIOR×24, MECH_WARRIOR×30, MECH_WARRIOR×24, DRONE×33, DRONE×29, MECH_WARRIOR×21, DRONE×28, SPECOPS×21, DRONE×23, DRONE×26, DRONE×22, MECH_WARRIOR×24, THE_GENERAL×18, MECH_WARRIOR×24, DRONE×21, MECH_WARRIOR×24 |
| 🟥 | Howling Savages | random | Future 88%, Modern 12% | ⬛ 0/38 (0%) | DRONE×14, SPECOPS×8, MECH_WARRIOR×2 | DRONE×27, DRONE×20, DRONE×25, HELI×20, DRONE×28, DRONE×29, MECH_WARRIOR×24, DRONE×23, MECH_WARRIOR×33, DRONE×26, DRONE×22, MECH_WARRIOR×24, DRONE×31, MECH_WARRIOR×33, HELI×30, DRONE×21 |
| 🟥 | Clumsy Attackers | random | Future 94%, Modern 6% | ⬛ 0/38 (0%) | DRONE×10, SPECOPS×6, MECH_WARRIOR×4 | DRONE×28, DRONE×24, DRONE×28, DRONE×29, MECH_WARRIOR×27, MECH_WARRIOR×24, DRONE×33, MECH_WARRIOR×30, DRONE×25, DRONE×33, DRONE×30, MECH_WARRIOR×21, MECH_WARRIOR×24, HELI×32, MECH_WARRIOR×27, DRONE×32, MECH_WARRIOR×30, DRONE×32 |
| 🟥 | Blundering Invaders | random | Future 95%, Modern 5% | ⬛ 0/38 (0%) | DRONE×6, MECH_WARRIOR×6, SPECOPS×4 | DRONE×30, MECH_WARRIOR×24, MECH_WARRIOR×21, DRONE×29, SIEGE_TANK×26, DRONE×21, DRONE×21, MECH_WARRIOR×27, DRONE×29, MECH_WARRIOR×27, DRONE×32, MECH_WARRIOR×24, DRONE×23, DRONE×23, MECH_WARRIOR×24, MECH_WARRIOR×30, DRONE×26, MECH_WARRIOR×24, MECH_WARRIOR×27 |
| 🟥 | Bored Mercenaries | random | Future 89%, Modern 11% | ⬛ 0/38 (0%) | SPECOPS×7, MECH_WARRIOR×6, DRONE×3 | MECH_WARRIOR×24, MECH_WARRIOR×24, DRONE×24, DRONE×31, DRONE×22, THE_GENERAL×18, DRONE×22, MECH_WARRIOR×24, MECH_WARRIOR×24, MECH_WARRIOR×33, SIEGE_TANK×32, MECH_WARRIOR×30, DRONE×33, DRONE×31, DRONE×29, DRONE×34, MECH_WARRIOR×24 |
| 🟥 | Frenzied Pillagers | random | Future 94%, Modern 6% | ⬛ 0/38 (0%) | MECH_WARRIOR×8, DRONE×4, SPECOPS×2 | DRONE×28, DRONE×22, MECH_WARRIOR×33, MECH_WARRIOR×30, DRONE×28, DRONE×29, MECH_WARRIOR×27, DRONE×29, MECH_WARRIOR×27, DRONE×21, SPECOPS×22, MECH_WARRIOR×33, DRONE×22, MECH_WARRIOR×24, MECH_WARRIOR×21 |

## Flagged Critters/Towers

### Stone Age
- **Critters UP (rarely reach the castle):** SLAVE (reach_rate=0.2%, era_mean=11.8%)

### Neolithic
- **Towers UP (damage share far below placement share):** SPIKE_TRAP (damage_share=6.7% vs placement_share=25.0%, ratio=0.27)

### Bronze Age
- **Towers UP (damage share far below placement share):** SPIKE_TRAP (damage_share=3.7% vs placement_share=16.7%, ratio=0.22); DOUBLE_SLING_TOWER (damage_share=2.2% vs placement_share=8.3%, ratio=0.26)

### Iron Age
- **Critters OP (reach rate far above era mean):** THE_SWORDMASTER (reach_rate=18.5%, era_mean=4.6%)
- **Critters UP (rarely reach the castle):** HORSEMAN_SLOW (reach_rate=0.0%, era_mean=4.6%); LARGE_CART (reach_rate=0.0%, era_mean=4.6%)

### Medieval
- **Critters OP (reach rate far above era mean):** HANDGUNNER (reach_rate=6.3%, era_mean=3.1%)
- **Towers OP (damage share far above placement share):** HEAVY_TOWER (damage_share=41.0% vs placement_share=19.2%, ratio=2.13); CANNON_TOWER (damage_share=13.2% vs placement_share=3.8%, ratio=3.44)
- **Towers UP (damage share far below placement share):** TAR_TOWER (damage_share=5.2% vs placement_share=19.2%, ratio=0.27); FIRE_TOWER (damage_share=0.7% vs placement_share=7.7%, ratio=0.10); BALLISTA_TOWER (damage_share=0.7% vs placement_share=7.7%, ratio=0.09); CATAPULTS (damage_share=0.9% vs placement_share=7.7%, ratio=0.12); DOUBLE_SLING_TOWER (damage_share=0.2% vs placement_share=3.8%, ratio=0.06); ARROW_TOWER (damage_share=0.0% vs placement_share=3.8%, ratio=0.01)

### Renaissance
- **Critters UP (rarely reach the castle):** NINJA (reach_rate=0.3%, era_mean=5.3%); CARGO (reach_rate=0.0%, era_mean=5.3%)
- **Towers OP (damage share far above placement share):** RIFLE_TOWER (damage_share=52.4% vs placement_share=25.0%, ratio=2.10); HEAVY_TOWER (damage_share=26.7% vs placement_share=8.3%, ratio=3.20)
- **Towers UP (damage share far below placement share):** CANNON_TOWER (damage_share=6.7% vs placement_share=16.7%, ratio=0.40); ICE_TOWER (damage_share=3.8% vs placement_share=16.7%, ratio=0.23); COLD_TOWER (damage_share=0.1% vs placement_share=8.3%, ratio=0.01); TAR_TOWER (damage_share=1.5% vs placement_share=16.7%, ratio=0.09)

### Industrial
- **Towers OP (damage share far above placement share):** GATLING_TOWER (damage_share=55.4% vs placement_share=22.2%, ratio=2.49)
- **Towers UP (damage share far below placement share):** COLD_TOWER (damage_share=0.1% vs placement_share=22.2%, ratio=0.01); ICE_TOWER (damage_share=1.0% vs placement_share=16.7%, ratio=0.06); SHOCK_TOWER (damage_share=3.7% vs placement_share=11.1%, ratio=0.34)

### Modern
- **Critters UP (rarely reach the castle):** SIEGE_TANK (reach_rate=0.4%, era_mean=7.7%); HELI (reach_rate=0.4%, era_mean=7.7%)
- **Towers OP (damage share far above placement share):** MG_TOWER (damage_share=29.8% vs placement_share=10.0%, ratio=2.98)
- **Towers UP (damage share far below placement share):** SHOCK_TOWER (damage_share=1.5% vs placement_share=10.0%, ratio=0.15); PARALYZNG_TOWER (damage_share=1.2% vs placement_share=10.0%, ratio=0.12); COLD_TOWER (damage_share=0.2% vs placement_share=10.0%, ratio=0.02); ICE_TOWER (damage_share=0.1% vs placement_share=10.0%, ratio=0.01)

### Future
- **Towers OP (damage share far above placement share):** MG_TOWER (damage_share=29.4% vs placement_share=11.1%, ratio=2.65)
- **Towers UP (damage share far below placement share):** COLD_TOWER (damage_share=0.5% vs placement_share=16.7%, ratio=0.03); ICE_TOWER (damage_share=0.1% vs placement_share=11.1%, ratio=0.01); SHOCK_TOWER (damage_share=0.2% vs placement_share=5.6%, ratio=0.04)
