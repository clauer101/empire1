> **Status: active** — analysis notes for next season's balance pass. No code changes made.

# Season Balance: Order-of-Magnitude Notes

Goal (from discussion): sharper specialization (fast critters faster, tanks tankier,
bulk more clustered, strong towers stronger at equal DPS) while avoiding the recurring
splash-tower / single-unit OP problem from prior seasons. This doc answers: *roughly
how much does X need to change to compensate for Y*, using the actual in-engine formula
— not concrete value proposals.

## 1. The core mechanic that drives all of this

`battle_service.py::_apply_shot_damage` (~line 293):

```python
eff_armour = critter.armour * (1.0 + critter.aura_armour_modifier)
damage = max(1.0, shot.damage - eff_armour)   # FLAT subtraction, floor 1
```

- Armor is a **flat subtractor**, not a percentage reducer. `net = damage - armor`, min 1.
- Burn/DoT **ignores armor completely**.
- Splash hits every critter in `splash_radius` for **full, un-reduced, no-falloff**
  damage — this is mechanically *why* splash was OP before: it's not "AoE with a
  penalty," it's N free extra full-damage hits per shot.

**This flips the intuition many tower-defense balancers default to.** Because
reduction is flat, a **% increase in armor is not compensated by the same % increase
in damage** — the required damage compensation is *always smaller* than the armor
increase, and shrinks further the higher the tower's raw damage already is relative
to that armor. Conversely, low-damage/fast towers are extremely sensitive to armor
buffs (near the floor of 1 already).

## 2. The formula for "how much more damage compensates for more armor"

To keep `net_damage` constant when armor rises by factor `(1+a)`:

```
required_damage = net_damage_before + armor_after
%_damage_increase ≈ a × armor / (damage - armor)
```

The ratio `armor / (damage - armor)` is the multiplier — call it the **"armor bite"**
of that specific tower-vs-critter pairing. Low bite (damage ≫ armor) → cheap to
compensate. High bite (damage ≈ armor) → expensive, and near the 1-damage floor it
becomes *impossible* to compensate by raising damage alone (you hit diminishing/zero
returns and must either lower armor elsewhere or accept the tower is countered).

## 3. Concrete magnitudes (computed from current `structures.yaml` / `critters.yaml`)

Using representative era-matched pairs (heavy/strong tower vs. tank critter of similar
era), for a few candidate armor buffs:

| Armor buff | Heavy tower vs. same-era tank | Effective DPS lost | Damage increase needed |
|---|---|---|---|
| +25% | HEAVY_TOWER vs KNIGHT | −12% | **+8%** |
| +25% | LASER_TOWER vs SIEGE_TANK | −7% | **+6%** |
| +50% | HEAVY_TOWER vs KNIGHT | −23% | **+16%** |
| +50% | LASER_TOWER vs SIEGE_TANK | −15% | **+11%** |
| +50% | ANTI_AIR_TOWER vs MECH_WARRIOR | −35% | **+21%** |
| +100% | HEAVY_TOWER vs KNIGHT | −46% | **+31%** |
| +100% | LASER_TOWER vs SIEGE_TANK | −29% | **+23%** |
| +100% | ROCKET_TOWER vs MECH_WARRIOR | −14% | **+12%** |

**Rule of thumb**: for the strong/heavy tower tier against its intended same-era tank,
a tank armor buff of **+X%** currently needs roughly **0.5–0.7×X%** more heavy-tower
damage to fully compensate — *not* 1:1. The exact multiplier depends on how far the
pairing already is from the 1-damage floor:

- **Cheap to compensate** (tower damage ≫ armor, e.g. ROCKET_TOWER dmg 200 vs armor
  24): even +100% armor only needs ~+12% damage. High headroom — you can push tank
  armor hard here without heavy towers needing much of a buff, meaning **fast-attack
  and splash towers become relatively much worse against these tanks without any
  change to them** — which is exactly the "tanks counter splash/fast mazes" lever
  you're looking for.
- **Expensive / fragile to compensate** (tower damage close to armor, e.g. HEAVY_TOWER
  dmg 27 vs SIEGE_TANK armor 18 → net already only 9): +50% armor needs +33% damage,
  +100% needs +67%, and beyond that you hit the floor — the pairing stops being a
  fight and becomes "heavy tower ignores this tank" or "heavy tower can't touch it."
  **This is the danger zone**: pairs already near damage≈armor break fast under
  further armor buffs and need disproportionate compensation, or a floor-mechanic
  rework, to stay meaningful.

## 4. Implication for fast towers vs. fast critters (the other axis)

Fast towers (ARROW/CROSSBOW/RIFLE/GATLING/MG/SNIPER) already have low per-hit damage
(1–65) at very high fire rate — their whole identity is DPS-through-volume against
low-armor/fast critters. Because armor is flat-subtracted **per hit**, fast towers are
the most sensitive class to *any* armor increase on the critters they're supposed to
counter (fast critters currently have very low armor, 0.5–3.5). If "fast critters
faster" also means "keep fast-critter armor near zero," fast towers stay strong
against them by design — the lever for fast-critter specialization should be **speed**,
not armor, to avoid accidentally breaking the fast-tower/fast-critter matchup.

Conversely, if bulk/swarm critters get moderate armor bumps to resist fast towers
(the "fast-tower-only mazes struggle vs tanks" goal extends naturally to bulk too,
since fast towers hit hardest per-shot-count, weakest per-shot-damage), expect the
same cheap/expensive split as section 3: fast towers vs. low-armor swarm stay
cheap to rebalance, fast towers vs. armored bulk becomes expensive fast because fast
tower damage values are already close to the 1-floor.

## 5. Splash: the real fix is structural, not a %-damage tweak

All three splash towers (CATAPULTS, CANNON_TOWER, RADAR_TOWER) use the same
`splash_radius: 0.3` with **zero falloff and zero target cap** — a splash hit is
`(damage − armor) × N_critters_in_radius`, scaling linearly and for free with cluster
density. No amount of nerfing splash `damage` fixes this cleanly, because the OP-ness
scales with *how clustered the maze is*, which the tower doesn't control — the player
does, by choice of maze design. Two structural levers (for later discussion, not
proposed here) that change the shape of the problem rather than its magnitude:
a max-targets-per-shot cap, or distance-based falloff — either one turns "splash
strength" into something a %-damage number can actually balance against tank armor
using the same math as section 3. Until one of those lands, tuning splash via
`damage` alone will keep reproducing the "splash too strong" finding already on
record in `tasks/TODO.md` ("cannon tower too strong").

## 6. Baseline data available

- Prior full baseline run: `data/balancing/20260711_084424/report.md` (win rates,
  OP/UP flags per era, already shows Medieval defender win rate at 52%/23% hardcoded
  — Cannon Tower era — consistent with the recorded "cannon tower too strong" note).
- To regenerate a fresh baseline before making changes:
  `python3 scripts/balance_sim.py --era all --n 20 --seed <fixed>`
- `scripts/sim_map.py <map> <era> <n> [out] [tower_override] [critter_override]` lets
  you isolate one tower vs. one critter type directly — useful for validating the
  specific % numbers above empirically rather than analytically once real value
  changes are chosen.

## Summary

- Damage-armor is flat, not %, so **compensation is sub-linear**: a tank armor buff
  needs roughly 0.1×–0.7× the same percentage in heavy-tower damage, depending on how
  close that pairing already sits to the floor.
- Pairs far from the floor (high tower damage vs. moderate armor) have room to push
  tank specialization hard with cheap compensation — good, this is the lever for
  "splash/fast mazes struggle vs tanks."
- Pairs near the floor (heavy tower ≈ tank armor) are fragile — armor buffs there
  get disproportionately expensive to compensate and risk breaking the matchup
  entirely (net damage hits the 1-floor).
- Splash's OP potential is structural (no falloff, no target cap), not a damage-value
  problem — a %-damage nerf alone won't fix cluster-scaling; that needs a rule change
  before the same magnitude math in section 3 applies to it.
