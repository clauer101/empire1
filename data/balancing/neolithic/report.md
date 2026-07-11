# Balancing Report

Generated: 2026-07-10T19:29:39.548447+00:00

## Maze Coverage

```
Era             Mazes  Source(s)               Towers (min-max)    
-------------------------------------------------------------------
stone               6  saved                   1-3
neolithic           3  saved                   4-10
bronze              5  saved                   6-29
iron                5  saved                   13-33
medieval            5  saved                   18-41
renaissance         3  saved                   32-45
industrial          4  saved                   28-61
modern              5  saved                   14-66
future              1  saved                   23-23
```

## Win Rates

| Era | Battles | Defender Win % | Hardcoded Win % | Random Win % |
|---|---:|---:|---:|---:|
| Neolithic | 72 | 40% | 58% | 37% |

## Battle-by-Battle Overview

🟩 defender won · 🟥 defender lost. Life % uses a 5-step gradient
(🟢 ≥80% · 🟡 ≥50% · 🟠 ≥20% · 🔴 >0% · ⬛ 0%). "Reached" lists the
critter types that made it to the castle (× count), blank if none.
One table per map, with that map's own tower-era distribution.

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

#### S1 Tom's Realm

| Tower Era Distribution (5 towers) | Towers |
|---|---|
| Neolithic 100% (5) | SPIKE_TRAP×3, DOUBLE_SLING_TOWER×2 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟥 | Neolithic Horde | hardcoded | Neolithic 100% | ⬛ 0/10 (0%) | CLUBMAN×8, WARRIOR×2 | CART×6, WARRIOR×4, WARRIOR×6, CART×6 |
| 🟥 | Tribal Warband | hardcoded | Neolithic 100% | ⬛ 0/10 (0%) | CLUBMAN×8, WARRIOR×2 | CART×3, WARRIOR×2, CART×5, WARRIOR×6, WARRIOR×5 |
| 🟥 | Harvest Raiders | hardcoded | Neolithic 95%, Bronze Age 5% | ⬛ 0/10 (0%) | CLUBMAN×8, WARRIOR×2 | CART×5, WARRIOR×4, CART×5, BOWMAN×1, WARRIOR×6 |
| 🟥 | Pottery Thieves | hardcoded | Neolithic 100% | ⬛ 0/10 (0%) | WARRIOR×10 | WARRIOR×8, WARRIOR×8, CART×9, WARRIOR×12, WARRIOR×8 |
| 🟥 | Rowdy Plunderers | random | Neolithic 77%, Bronze Age 23% | ⬛ 0/10 (0%) | CHARIOT×7, CLUBMAN×4 | CHARIOT×7, CART×6, CART×9, WARRIOR×8 |
| 🟥 | Rowdy Plunderers | random | Neolithic 77%, Bronze Age 23% | ⬛ 0/10 (0%) | CHARIOT×7, CLUBMAN×4 | CHARIOT×7, CART×6, CART×9, WARRIOR×8 |
| 🟥 | Drunken Raiders | random | Neolithic 100% | ⬛ 0/10 (0%) | WARRIOR×7, CLUBMAN×3, CART×1 | WARRIOR×9, CART×6, CART×9, WARRIOR×9, WARRIOR×7 |
| 🟥 | Shrieking Horde | random | Neolithic 100% | ⬛ 0/10 (0%) | WARRIOR×10 | WARRIOR×7, WARRIOR×9, WARRIOR×9, CART×6, WARRIOR×6 |
| 🟥 | Disorganized Mob | random | Neolithic 100% | ⬛ 0/10 (0%) | CLUBMAN×8, WARRIOR×2 | CART×6, WARRIOR×6, CART×9, CART×9, WARRIOR×9 |
| 🟥 | Clumsy Attackers | random | Neolithic 81%, Stone Age 19% | ⬛ 0/10 (0%) | WARRIOR×10 | WARRIOR×10, WARRIOR×9, SCOUT×8, CART×9, CART×6 |
| 🟥 | Petty Bandits | random | Neolithic 69%, Bronze Age 31% | ⬛ 0/10 (0%) | BOWMAN×5 | BOWMAN×10, CART×9, WARRIOR×8, WARRIOR×5 |
| 🟥 | Grumpy Marauders | random | Neolithic 67%, Bronze Age 33% | ⬛ 0/10 (0%) | WARRIOR×5, CLUBMAN×4, CART×1 | WARRIOR×7, CART×9, BOWMAN×8 |
| 🟥 | Angry Mob | random | Neolithic 69%, Stone Age 31% | ⬛ 0/10 (0%) | WARRIOR×7, CLUBMAN×3, CART×1 | SLAVE×8, WARRIOR×9, CART×9 |
| 🟥 | Savage Rabble | random | Neolithic 71%, Stone Age 29% | ⬛ 0/10 (0%) | CLUBMAN×8, CART×1 | CART×9, SCOUT×6, CART×6 |
| 🟥 | Petty Bandits | random | Neolithic 44%, Bronze Age 37%, Stone Age 19% | ⬛ 0/10 (0%) | CHARIOT×10 | SLAVE×5, CHARIOT×10, WARRIOR×6, CART×6 |
| 🟥 | Shrieking Horde | random | Neolithic 48%, Stone Age 26%, Bronze Age 26% | ⬛ 0/10 (0%) | CLUBMAN×8, CART×1 | CART×9, CLUBMAN×8, CART×6, SWORDMAN×8 |
| 🟥 | Unlucky Raiders | random | Neolithic 64%, Bronze Age 36% | ⬛ 0/10 (0%) | WARRIOR×6, CLUBMAN×4 | WARRIOR×8, CART×6, SWORDMAN×8 |
| 🟥 | Crude Invaders | random | Neolithic 100% | ⬛ 0/10 (0%) | WARRIOR×10 | WARRIOR×5, WARRIOR×8, WARRIOR×5, CART×9 |
| 🟥 | Grumpy Marauders | random | Neolithic 77%, Bronze Age 23% | ⬛ 0/10 (0%) | WARRIOR×6, CHARIOT×4 | WARRIOR×8, CHARIOT×7, WARRIOR×10, WARRIOR×6 |
| 🟥 | Ragged Warband | random | Neolithic 100% | ⬛ 0/10 (0%) | WARRIOR×7, CLUBMAN×4 | WARRIOR×5, WARRIOR×6, CART×9 |
| 🟥 | Savage Rabble | random | Neolithic 77%, Bronze Age 23% | ⬛ 0/10 (0%) | WARRIOR×8, CART×1 | WARRIOR×10, CART×6, CHARIOT×7, WARRIOR×7 |
| 🟥 | Disorganized Mob | random | Neolithic 81%, Bronze Age 19% | ⬛ 0/10 (0%) | CLUBMAN×8, BOWMAN×1 | CART×6, BOWMAN×6, CART×9, CART×6, WARRIOR×5 |
| 🟥 | Muddy Marauders | random | Neolithic 60%, Bronze Age 20%, Stone Age 20% | ⬛ 0/10 (0%) | CLUBMAN×8, CART×1 | CART×9, SWORDMAN×6, WARRIOR×9, SLAVE×6 |
| 🟥 | Disorganized Mob | random | Neolithic 100% | ⬛ 0/10 (0%) | WARRIOR×6, CLUBMAN×4 | WARRIOR×8, CART×9, CART×9 |

## Flagged Critters/Towers

### Neolithic
- **Towers UP (damage share far below placement share):** SPIKE_TRAP (damage_share=11.3% vs placement_share=33.3%, ratio=0.34)
