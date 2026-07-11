# Balancing Report

Generated: 2026-07-10T19:32:58.246061+00:00

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
modern              5  saved                   14-66
future              1  saved                   23-23
```

## Win Rates

| Era | Battles | Defender Win % | Hardcoded Win % | Random Win % |
|---|---:|---:|---:|---:|
| Bronze Age | 96 | 74% | 75% | 74% |

## Battle-by-Battle Overview

🟩 defender won · 🟥 defender lost. Life % uses a 5-step gradient
(🟢 ≥80% · 🟡 ≥50% · 🟠 ≥20% · 🔴 >0% · ⬛ 0%). "Reached" lists the
critter types that made it to the castle (× count), blank if none.
One table per map, with that map's own tower-era distribution.

### Bronze Age

#### Arrow Bronze (len: 8)

| Tower Era Distribution (10 towers) | Towers |
|---|---|
| Bronze Age 100% (10) | ARROW_TOWER×7, FIRE_TOWER×3 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Bronze Warriors | hardcoded | Bronze Age 97%, Iron Age 3% | 🟢 13/13 (100%) |  | BOWMAN×6, BOWMAN×8, SWORDMAN×10, PIKENEER×2, SWORDMAN×10, CHARIOT×12, SWORDMAN×14 |
| 🟩 | Chariot Rush | hardcoded | Bronze Age 100% | 🟢 13/13 (100%) |  | BOWMAN×12, SWORDMAN×12, SWORDMAN×12, BOWMAN×13, SWORDMAN×9, BOWMAN×12, SWORDMAN×14, SWORDMAN×16 |
| 🟩 | Copper Blades | hardcoded | Bronze Age 100% | 🟠 4/13 (31%) | BOWMAN×4, CHARIOT×1 | SWORDMAN×11, CHARIOT×12, CHARIOT×13, CHARIOT×14, SWORDMAN×14, CHARIOT×12, BOWMAN×14, CHARIOT×16 |
| 🟥 | Harbor Raiders | hardcoded | Bronze Age 100% | ⬛ 0/13 (0%) | BOWMAN×7 | BOWMAN×13, BOWMAN×14, BOWMAN×14, CHARIOT×15, SWORDMAN×15, BOWMAN×16, BOWMAN×14, BOWMAN×16, SWORDMAN×18 |
| 🟩 | Clumsy Attackers | random | Bronze Age 76%, Neolithic 13%, Iron Age 11% | 🟡 9/13 (69%) | PIKENEER×4 | SWORDMAN×8, PIKENEER×9, CHARIOT×10, SWORDMAN×8, CHARIOT×13, BOWMAN×11, CHARIOT×10, WARRIOR×10 |
| 🟩 | Clumsy Attackers | random | Bronze Age 76%, Neolithic 13%, Iron Age 11% | 🟡 9/13 (69%) | PIKENEER×4 | SWORDMAN×8, PIKENEER×9, CHARIOT×10, SWORDMAN×8, CHARIOT×13, BOWMAN×11, CHARIOT×10, WARRIOR×10 |
| 🟥 | Petty Bandits | random | Bronze Age 86%, Neolithic 14% | ⬛ 0/13 (0%) | CHARIOT×5, BOWMAN×4 | SWORDMAN×12, SWORDMAN×10, BOWMAN×12, BOWMAN×10, CHARIOT×10, WARRIOR×13, BOWMAN×11, SWORDMAN×12 |
| 🟩 | Noisy Barbarians | random | Bronze Age 89%, Neolithic 11% | 🟡 7/13 (54%) | BOWMAN×3 | SWORDMAN×10, CHARIOT×9, CART×9, BOWMAN×12, BOWMAN×9, BOWMAN×11, SWORDMAN×8, SWORDMAN×12 |
| 🟩 | Rude Barbarians | random | Bronze Age 87%, Neolithic 13% | 🟢 13/13 (100%) |  | CART×12, BOWMAN×8, CHARIOT×10, SWORDMAN×12, CHARIOT×12, SWORDMAN×8, CHARIOT×10, CHARIOT×11, SWORDMAN×12 |
| 🟩 | Disorganized Mob | random | Bronze Age 73%, Neolithic 27% | 🟡 7/13 (54%) | BOWMAN×3 | WARRIOR×12, SWORDMAN×12, CHARIOT×11, WARRIOR×12, BOWMAN×12, SWORDMAN×8, SWORDMAN×12, BOWMAN×10 |
| 🟩 | Shrieking Horde | random | Bronze Age 74%, Neolithic 15%, Iron Age 11% | 🟠 3/13 (23%) | HORSEMAN_FAST×8, BOWMAN×1 | BOWMAN×10, SWORDMAN×8, CHARIOT×13, BOWMAN×13, HORSEMAN_FAST×9, BOWMAN×10, CART×12, BOWMAN×7 |
| 🟩 | Rowdy Plunderers | random | Bronze Age 66%, Neolithic 20%, Iron Age 14% | 🟡 9/13 (69%) | LEGIONARY×4 | CHARIOT×9, WARRIOR×12, CHARIOT×10, LEGIONARY×8, SWORDMAN×10, BOWMAN×10 |
| 🟩 | Crude Invaders | random | Bronze Age 70%, Neolithic 30% | 🟢 13/13 (100%) |  | SWORDMAN×12, BOWMAN×10, WARRIOR×10, CHARIOT×11, BOWMAN×10, WARRIOR×8 |
| 🟩 | Rampaging Rabble | random | Bronze Age 69%, Neolithic 31% | 🟢 13/13 (100%) |  | CHARIOT×11, CHARIOT×8, CART×9, CHARIOT×9, SWORDMAN×12, CART×9 |
| 🟩 | Drunken Raiders | random | Bronze Age 60%, Neolithic 24%, Iron Age 15% | 🟡 9/13 (69%) | PIKENEER×4 | CHARIOT×13, WARRIOR×10, CHARIOT×10, LARGE_CART×12, CART×9, BOWMAN×9, BOWMAN×7, SWORDMAN×8 |
| 🟩 | Howling Savages | random | Bronze Age 63%, Neolithic 25%, Iron Age 11% | 🟠 3/13 (23%) | HORSEMAN_SLOW×4, CART×1 | CART×12, HORSEMAN_SLOW×9, SWORDMAN×8, WARRIOR×8, SWORDMAN×10, SWORDMAN×12, CHARIOT×10, SWORDMAN×10 |
| 🟩 | Bored Mercenaries | random | Bronze Age 67%, Neolithic 18%, Iron Age 15% | 🟠 5/13 (38%) | LEGIONARY×8 | CHARIOT×7, CHARIOT×8, SWORDMAN×10, CHARIOT×9, BOWMAN×11, LEGIONARY×10, CART×12 |
| 🟩 | Angry Mob | random | Bronze Age 88%, Neolithic 12% | 🟢 13/13 (100%) |  | CHARIOT×9, CART×9, SWORDMAN×10, BOWMAN×7, BOWMAN×8, SWORDMAN×10, CHARIOT×11, BOWMAN×10 |
| 🟩 | Noisy Barbarians | random | Bronze Age 75%, Iron Age 14%, Neolithic 11% | 🔴 2/13 (15%) | CHARIOT×5, SWORDMAN×2, HORSEMAN_FAST×2 | BOWMAN×12, WARRIOR×8, BOWMAN×13, SWORDMAN×12, CHARIOT×9, SWORDMAN×8, HORSEMAN_FAST×10 |
| 🟩 | Restless Horde | random | Bronze Age 83%, Neolithic 17% | 🟢 13/13 (100%) |  | BOWMAN×7, CART×9, BOWMAN×7, SWORDMAN×10, SWORDMAN×8, SWORDMAN×12 |
| 🟩 | Howling Savages | random | Bronze Age 74%, Iron Age 15%, Neolithic 11% | 🟡 10/13 (77%) | HORSEMAN_FAST×3 | SWORDMAN×10, SWORDMAN×8, SWORDMAN×10, CART×9, CHARIOT×10, HORSEMAN_FAST×12, BOWMAN×9, BOWMAN×13 |
| 🟩 | Weary Plunderers | random | Bronze Age 74%, Iron Age 14%, Neolithic 12% | 🟡 9/13 (69%) | HORSEMAN_FAST×4 | HORSEMAN_FAST×11, BOWMAN×8, BOWMAN×8, CHARIOT×9, SWORDMAN×8, CART×9, CHARIOT×12, BOWMAN×11 |
| 🟥 | Weary Plunderers | random | Bronze Age 56%, Neolithic 27%, Iron Age 17% | ⬛ 0/13 (0%) | PIKENEER×9, BOWMAN×2 | SWORDMAN×12, SWORDMAN×10, PIKENEER×13, BOWMAN×12, BOWMAN×8, WARRIOR×11, CART×9 |
| 🟩 | Disorganized Mob | random | Bronze Age 84%, Neolithic 16% | 🟢 13/13 (100%) |  | SWORDMAN×10, BOWMAN×11, CHARIOT×8, SWORDMAN×10, WARRIOR×10, CHARIOT×13 |

#### S1 Formica

| Tower Era Distribution (14 towers) | Towers |
|---|---|
| Bronze Age 86% (12), Neolithic 14% (2) | ARROW_TOWER×5, BALLISTA_TOWER×4, FIRE_TOWER×3, SPIKE_TRAP×2 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Bronze Warriors | hardcoded | Bronze Age 97%, Iron Age 3% | 🟢 13/13 (100%) |  | BOWMAN×6, BOWMAN×8, SWORDMAN×10, PIKENEER×2, SWORDMAN×10, CHARIOT×12, SWORDMAN×14 |
| 🟩 | Chariot Rush | hardcoded | Bronze Age 100% | 🟢 13/13 (100%) |  | BOWMAN×12, SWORDMAN×12, SWORDMAN×12, BOWMAN×13, SWORDMAN×9, BOWMAN×12, SWORDMAN×14, SWORDMAN×16 |
| 🟩 | Copper Blades | hardcoded | Bronze Age 100% | 🟢 13/13 (100%) |  | SWORDMAN×11, CHARIOT×12, CHARIOT×13, CHARIOT×14, SWORDMAN×14, CHARIOT×12, BOWMAN×14, CHARIOT×16 |
| 🟩 | Harbor Raiders | hardcoded | Bronze Age 100% | 🟡 7/13 (54%) | BOWMAN×3 | BOWMAN×13, BOWMAN×14, BOWMAN×14, CHARIOT×15, SWORDMAN×15, BOWMAN×16, BOWMAN×14, BOWMAN×16, SWORDMAN×18 |
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

#### Half Bronze

| Tower Era Distribution (6 towers) | Towers |
|---|---|
| Bronze Age 50% (3), Neolithic 50% (3) | DOUBLE_SLING_TOWER×3, ARROW_TOWER×2, FIRE_TOWER×1 |

| Result | Army | Kind | Army Critter Eras | Life Left | Reached | Killed (army waves) |
|---|---|---|---|---|---|---|
| 🟩 | Bronze Warriors | hardcoded | Bronze Age 97%, Iron Age 3% | 🟠 3/13 (23%) | BOWMAN×5 | BOWMAN×6, BOWMAN×8, SWORDMAN×10, PIKENEER×2, SWORDMAN×10, CHARIOT×12, SWORDMAN×14 |
| 🟥 | Chariot Rush | hardcoded | Bronze Age 100% | ⬛ 0/13 (0%) | BOWMAN×7 | BOWMAN×12, SWORDMAN×12, SWORDMAN×12, BOWMAN×13, SWORDMAN×9, BOWMAN×12, SWORDMAN×14, SWORDMAN×16 |
| 🟥 | Copper Blades | hardcoded | Bronze Age 100% | ⬛ 0/13 (0%) | CHARIOT×4, SWORDMAN×3, BOWMAN×2 | SWORDMAN×11, CHARIOT×12, CHARIOT×13, CHARIOT×14, SWORDMAN×14, CHARIOT×12, BOWMAN×14, CHARIOT×16 |
| 🟥 | Harbor Raiders | hardcoded | Bronze Age 100% | ⬛ 0/13 (0%) | BOWMAN×7 | BOWMAN×13, BOWMAN×14, BOWMAN×14, CHARIOT×15, SWORDMAN×15, BOWMAN×16, BOWMAN×14, BOWMAN×16, SWORDMAN×18 |
| 🟥 | Clumsy Attackers | random | Bronze Age 76%, Neolithic 13%, Iron Age 11% | ⬛ 0/13 (0%) | PIKENEER×6, CHARIOT×3, BOWMAN×2 | SWORDMAN×8, PIKENEER×9, CHARIOT×10, SWORDMAN×8, CHARIOT×13, BOWMAN×11, CHARIOT×10, WARRIOR×10 |
| 🟥 | Clumsy Attackers | random | Bronze Age 76%, Neolithic 13%, Iron Age 11% | ⬛ 0/13 (0%) | PIKENEER×6, CHARIOT×3, BOWMAN×2 | SWORDMAN×8, PIKENEER×9, CHARIOT×10, SWORDMAN×8, CHARIOT×13, BOWMAN×11, CHARIOT×10, WARRIOR×10 |
| 🟥 | Petty Bandits | random | Bronze Age 86%, Neolithic 14% | ⬛ 0/13 (0%) | BOWMAN×7 | SWORDMAN×12, SWORDMAN×10, BOWMAN×12, BOWMAN×10, CHARIOT×10, WARRIOR×13, BOWMAN×11, SWORDMAN×12 |
| 🟥 | Noisy Barbarians | random | Bronze Age 89%, Neolithic 11% | ⬛ 0/13 (0%) | BOWMAN×7 | SWORDMAN×10, CHARIOT×9, CART×9, BOWMAN×12, BOWMAN×9, BOWMAN×11, SWORDMAN×8, SWORDMAN×12 |
| 🟥 | Rude Barbarians | random | Bronze Age 87%, Neolithic 13% | ⬛ 0/13 (0%) | BOWMAN×5, CHARIOT×4 | CART×12, BOWMAN×8, CHARIOT×10, SWORDMAN×12, CHARIOT×12, SWORDMAN×8, CHARIOT×10, CHARIOT×11, SWORDMAN×12 |
| 🟥 | Disorganized Mob | random | Bronze Age 73%, Neolithic 27% | ⬛ 0/13 (0%) | CHARIOT×6, SWORDMAN×4 | WARRIOR×12, SWORDMAN×12, CHARIOT×11, WARRIOR×12, BOWMAN×12, SWORDMAN×8, SWORDMAN×12, BOWMAN×10 |
| 🟥 | Shrieking Horde | random | Bronze Age 74%, Neolithic 15%, Iron Age 11% | ⬛ 0/13 (0%) | BOWMAN×5, HORSEMAN_FAST×2, CHARIOT×1 | BOWMAN×10, SWORDMAN×8, CHARIOT×13, BOWMAN×13, HORSEMAN_FAST×9, BOWMAN×10, CART×12, BOWMAN×7 |
| 🟥 | Rowdy Plunderers | random | Bronze Age 66%, Neolithic 20%, Iron Age 14% | ⬛ 0/13 (0%) | LEGIONARY×7, CHARIOT×3, BOWMAN×2 | CHARIOT×9, WARRIOR×12, CHARIOT×10, LEGIONARY×8, SWORDMAN×10, BOWMAN×10 |
| 🟥 | Crude Invaders | random | Bronze Age 70%, Neolithic 30% | ⬛ 0/13 (0%) | BOWMAN×7 | SWORDMAN×12, BOWMAN×10, WARRIOR×10, CHARIOT×11, BOWMAN×10, WARRIOR×8 |
| 🟩 | Rampaging Rabble | random | Bronze Age 69%, Neolithic 31% | 🟢 12/13 (92%) | CHARIOT×1 | CHARIOT×11, CHARIOT×8, CART×9, CHARIOT×9, SWORDMAN×12, CART×9 |
| 🟥 | Drunken Raiders | random | Bronze Age 60%, Neolithic 24%, Iron Age 15% | ⬛ 0/13 (0%) | PIKENEER×7, CHARIOT×4, BOWMAN×1 | CHARIOT×13, WARRIOR×10, CHARIOT×10, LARGE_CART×12, CART×9, BOWMAN×9, BOWMAN×7, SWORDMAN×8 |
| 🟥 | Howling Savages | random | Bronze Age 63%, Neolithic 25%, Iron Age 11% | ⬛ 0/13 (0%) | HORSEMAN_SLOW×7 | CART×12, HORSEMAN_SLOW×9, SWORDMAN×8, WARRIOR×8, SWORDMAN×10, SWORDMAN×12, CHARIOT×10, SWORDMAN×10 |
| 🟥 | Bored Mercenaries | random | Bronze Age 67%, Neolithic 18%, Iron Age 15% | ⬛ 0/13 (0%) | BOWMAN×6, LEGIONARY×1 | CHARIOT×7, CHARIOT×8, SWORDMAN×10, CHARIOT×9, BOWMAN×11, LEGIONARY×10, CART×12 |
| 🟥 | Angry Mob | random | Bronze Age 88%, Neolithic 12% | ⬛ 0/13 (0%) | BOWMAN×7 | CHARIOT×9, CART×9, SWORDMAN×10, BOWMAN×7, BOWMAN×8, SWORDMAN×10, CHARIOT×11, BOWMAN×10 |
| 🟥 | Noisy Barbarians | random | Bronze Age 75%, Iron Age 14%, Neolithic 11% | ⬛ 0/13 (0%) | BOWMAN×7 | BOWMAN×12, WARRIOR×8, BOWMAN×13, SWORDMAN×12, CHARIOT×9, SWORDMAN×8, HORSEMAN_FAST×10 |
| 🟥 | Restless Horde | random | Bronze Age 83%, Neolithic 17% | ⬛ 0/13 (0%) | BOWMAN×7 | BOWMAN×7, CART×9, BOWMAN×7, SWORDMAN×10, SWORDMAN×8, SWORDMAN×12 |
| 🟥 | Howling Savages | random | Bronze Age 74%, Iron Age 15%, Neolithic 11% | ⬛ 0/13 (0%) | HORSEMAN_FAST×10, BOWMAN×2 | SWORDMAN×10, SWORDMAN×8, SWORDMAN×10, CART×9, CHARIOT×10, HORSEMAN_FAST×12, BOWMAN×9, BOWMAN×13 |
| 🟥 | Weary Plunderers | random | Bronze Age 74%, Iron Age 14%, Neolithic 12% | ⬛ 0/13 (0%) | HORSEMAN_FAST×9, BOWMAN×2 | HORSEMAN_FAST×11, BOWMAN×8, BOWMAN×8, CHARIOT×9, SWORDMAN×8, CART×9, CHARIOT×12, BOWMAN×11 |
| 🟥 | Weary Plunderers | random | Bronze Age 56%, Neolithic 27%, Iron Age 17% | ⬛ 0/13 (0%) | PIKENEER×10, SWORDMAN×2 | SWORDMAN×12, SWORDMAN×10, PIKENEER×13, BOWMAN×12, BOWMAN×8, WARRIOR×11, CART×9 |
| 🟥 | Disorganized Mob | random | Bronze Age 84%, Neolithic 16% | ⬛ 0/13 (0%) | BOWMAN×5, CHARIOT×4 | SWORDMAN×10, BOWMAN×11, CHARIOT×8, SWORDMAN×10, WARRIOR×10, CHARIOT×13 |

## Flagged Critters/Towers

### Bronze Age
- **Towers OP (damage share far above placement share):** ARROW_TOWER (damage_share=68.5% vs placement_share=33.3%, ratio=2.05)
- **Towers UP (damage share far below placement share):** FIRE_TOWER (damage_share=14.6% vs placement_share=33.3%, ratio=0.44); SPIKE_TRAP (damage_share=1.9% vs placement_share=16.7%, ratio=0.11)
