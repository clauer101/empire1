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

## 7. Fresh baseline (2026-08-20 run) — concrete proposals

Fresh `scripts/balance_sim.py --era all --n 20` run (`data/balancing/20260820_185405/`,
after fixing a log-flooding bug in `_step_armies` — see below) confirms a very
consistent, actionable pattern in the OP/UP flags across every era:

**Every era, without exception:**
- **Slow-effect towers are UP** (SPIKE_TRAP, COLD_TOWER, ICE_TOWER, SHOCK_TOWER,
  PARALYZNG_TOWER, TAR_TOWER) — damage-share/placement-share ratio 0.02–0.33 in every
  single era they appear in.
- **Fast/rapid-fire and "strong" direct-hit towers are OP** (ARROW_TOWER, HEAVY_TOWER,
  RIFLE_TOWER, GATLING_TOWER, FLAME_THROWER, MG_TOWER) — ratio 2.0–3.0 in every era.
- **Splash towers (CANNON_TOWER, CATAPULTS) are currently UP, not OP** — opposite of
  the season-3 "cannon too strong" note in `tasks/TODO.md`. Whatever made splash
  dominant before seems to have already been nerfed; the structural risk in section 5
  above is still latent (no falloff/cap), but the current damage values are too low
  to exploit it, not too high.

**Modern era is a acute failure, not a tuning nit** — defender win rate cratered to
12% (vs. 39% in the pre-fix 2026-07-11 baseline, so this is a real regression, not
noise). Root cause, confirmed by hand-computing `max(1, damage - armor)` for every
Modern tower against SIEGE_TANK (armor 18) and SMALL_TANK (armor 14, industrial
carry-over): **every fast, slow, and burn tower in the Modern tier is floored at 1
net damage per hit** against these two critters — SHOCK_TOWER, PARALYZNG_TOWER,
MG_TOWER, GATLING_TOWER, NAPALM_THROWER, FLAME_THROWER all net exactly 1. Only
ANTI_AIR_TOWER (net 40–44) and LASER_TOWER (net 62–66) — the two "strong" towers —
do meaningful damage, and mazes that under-invest in those two lose completely
(0% life left, repeatedly, in "Weak Modern" / "Short Mixed Modern" test mazes).
SPECOPS is the other half of the problem: a `bulk`-type critter with tank-level
stats (410 HP, armor 8, but only 1 slot, spawns every 300ms) — it's cheap to spam
in volume *and* individually tanky, which is a category error for a "bulk" unit
(bulk should be cheap-and-weak-per-unit, tanky should be slow-and-expensive).

### Concrete proposals (directional, not final values — verify empirically before committing)

1. **Un-floor slow/burn/fast towers against Modern-tier armor.** These towers are
   not just "weaker," they are mechanically dead weight once armor exceeds their
   damage. Two independent levers, don't need both:
   - Raise slow/burn/fast tower `damage` enough that net damage vs. SIEGE_TANK/
     SMALL_TANK clears the floor by a real margin (net ≥ 3-4, not 1) — per section 3's
     math, since these are all currently *at* the floor, this needs a large jump
     (e.g. MG_TOWER damage 14→22+ to clear SIEGE_TANK's 18 armor meaningfully).
   - Or: keep slow/burn towers' direct damage low (that's their identity — they pay
     for damage in utility, not raw numbers) but make their DoT/slow-duration values
     scale up in the Modern tier specifically, since DoT already ignores armor
     entirely (section 1) — this is the cheaper, more surgical fix and reinforces
     the "burn/DoT is the anti-tank answer" identity from earlier in this doc.
2. **Split SPECOPS' identity.** A bulk unit with SIEGE_TANK-level HP defeats the
   purpose of both categories existing. Either lower SPECOPS armor/hp toward what
   "bulk" means elsewhere in the roster (cheap, dies to volume, wins by numbers) and
   let SIEGE_TANK/MECH_WARRIOR alone carry the "hard to kill" role, or raise its
   slot cost so it can't be spammed at the current density (currently 1 slot /
   300ms — extremely cheap wave-capacity-wise for its durability).
3. **ANTI_AIR_TOWER / LASER_TOWER are correctly strong** — do not nerf; the problem
   is everything else in the tier being too weak, not these two being too strong. A
   maze that leans on them wins; the OP/UP flags don't call these out because
   damage-share only measures relative dominance, and their high placement-share in
   losing mazes was low (players under-invested in them in the test data — worth
   checking whether their gold cost is disproportionately high relative to the
   other Modern towers, since that would explain low placement despite them being
   the only towers that work).
4. **Slow-tower chain (SPIKE_TRAP → COLD_TOWER → ICE_TOWER → SHOCK_TOWER →
   PARALYZNG_TOWER) is UP in every era it appears, not just Modern.** This is a
   whole-tower-class problem, not one bad value. Likely fix: slow/stun effects need
   their utility value (time saved for other towers to land more hits) to be
   accounted for outside the raw damage-share metric — but if the intent is for
   slow towers to be viable *as damage dealers too* (not pure support), their direct
   damage or effect potency needs a global increase, not a per-era patch.
5. **Do not touch CANNON_TOWER/CATAPULTS damage upward** given current UP status —
   but do treat the structural no-falloff/no-cap splash mechanic (section 5) as a
   ticking time bomb: any future damage buff to these two towers should come bundled
   with a falloff or target cap, or the season-3 "cannon too strong" problem will
   resurface immediately once their UP status is corrected.

### Bug fixed while producing this baseline

`battle_service.py::_step_armies` was calling `log.exception()` (full traceback) on
every 15ms tick for every army whenever the network-handler `Services` singleton
wasn't initialized — always true in headless simulation. This produced ~16M log
lines and killed the sim process before completion. Fixed by narrowing the
`except Exception` to `except AssertionError: pass` (the only exception `_svc()`
raises), matching the already-correct "ruler_level defaults to 1" fallback
behavior. See `python_server/src/gameserver/engine/battle_service.py` around
line 806.
