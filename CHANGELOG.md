# Changelog

## 2026-08-20

### Season 4 balance pass: sharper roles, and a reason to trust someone

Season 4, "Love and Betrayal," arrives with the biggest rebalance we've shipped.

**Rulers.** Every ruler had skills moved between slots, so check your build —
your points may now sit on a different effect. **Maja**
swapped her workshop discount and her research payout; the payout at max is now
1M gold. **Borin** traded life restoration for artifact retention, and his
ultimate now grants bonus gold per critter killed. **Alric** moved the artifact
stealing package to his ultimate and now slows enemy sieges earlier in the tree.
**Nandi** and **Lucien** kept their layouts but had every tier rescaled.

**Units and towers.** The goal was to make each class feel like its class. Tanks
are genuinely hard to kill now — the Mech Warrior went from 18 to 35 armor, out
of reach of most single-shot towers. Fast units are faster and arrive in tighter
packs; the Helicopter now spawns every 500ms instead of 900ms. Carriers move
quicker, and the Cargo dropped to three wave slots while gaining armor. Because
armor subtracts flat damage, the counter to all this armor is
fire: burn damage ignores armor entirely, and every burn tower got a serious
lift — the Fire Tower's burn went from 1.25 to 4 damage per second. The Rocket
Tower changed job completely, from a single heavy hit to splash damage, and the
Laser Tower is now a future-era tower.

Most units also lost their building prerequisites and now unlock from research
alone, so armies come online much earlier.

**Economy and diplomacy.** Late-era upgrades cost far more — the last era step
went from 730k to 2.73M — while early citizens got cheaper, so the opening is
faster and the endgame is a real grind. Artifacts are more common but
individually weaker, and now mostly grant culture. Spy intel is no longer bought
with gold; you send a spy army instead. And you can now ally with one other
empire: allies can't attack each other, they're ranked together by combined
culture, and forming or breaking the pact costs 5% of your culture.

## 2026-08-15

### Season 3 wrap-up: The Rise of the Robots

Season 3 has come to a close! Final standings by culture:

1. 🥇 **Zornbolds** — ~115.5M culture. Zornbolds also triggered the season-end
   criterion outright, closing out the season on their own terms.
2. 🥈 Empire strikes back — ~94.0M culture
3. 🥉 500: InternAal Server Error — ~91.6M culture
4. Proxmoxia — ~84.0M culture
5. Limperium — ~51.6M culture

The final stretch got a real jolt of energy from the **Mech Warrior**, the
future-era heavy tank unit — 937 HP, 24 armor, and two Special Ops released on
death. It turned into a serious wall for attackers to chew through, and a
serious hammer for whoever fielded it well. Mech Warrior-driven pushes were a
big part of what kept the final rally so contested and unpredictable right up
to the wire.

To everyone who built, defended, raided, and pushed through Season 3 — thank
you. Whether you were fighting for first place or just trying to survive one
more wave, you're what made this season worth playing. Season 4, "Love and
Betrayal," kicks off soon. See you on the battlefield.

## 2026-07-16

### Bully protection: repeated attacks on the same defender now pay off less

If you beat the same opponent more than 3 times within 24 hours, every
attack after that against them earns **no ruler XP** and only **33% of the
normal culture loot** — your battle report will tell you exactly when this
kicks in. Beating a weaker empire once or twice is fine; parking an army on
someone's doorstep all day is not.

The flip side: the defender getting farmed isn't left empty-handed. While
the protection is active, they earn **triple gold** for every wave they
repel against that attacker — a direct reward for being repeatedly
targeted, credited live during the siege.

This only applies to player-vs-player fights. Grinding AI waves is
unaffected — go nuts.

## 2026-07-14

### TL;DR: OP settings get nerfed

Found something that feels too strong? Use it — that's smart play, not
cheating. But don't build your whole empire around a single loophole: if a
setting is OP, it gets nerfed, no exceptions. Full policy on the new
[Fair Play page](/fairplay.html).

## 2026-07-13

### Ruler balance pass

Several rulers received skill tuning:

- **Maja** — gold rewards from Erudite Synergy (gold bonus after research)
  increased significantly, in some tiers up to 10x.
- **Nandi** — base speed slightly reduced; the Cultural Footprint bonus was
  split into finer tiers and slightly weakened at the top end.
- **Lucien** — gold bonus on skill-up doubled.
- **Borin** — two skills reworked: one skill now delays enemy waves instead
  of refunding tower sell value, and Undying Defiance now grants a longer
  artifact retention time instead of a wave-delay bonus.

## 2026-07-12

### Season 3: The Rise of the Robots

Tomorrow Season 3: The Rise of the Robots starts! This season brings trophies,
tech tree branches, and a wide balance pass across towers and critters.

**Trophies** now reward sustained defensive performance, not just single wins.
Each trophy tracks a running total — battles won, AI waves repelled, human
attackers turned away — and unlocks at set thresholds, with higher tiers
granting small permanent bonuses on top of the bragging rights. Unbroken is
your first taste of it: win a single defense and it's yours. Keep winning and
you'll climb through Centurion (100 defensive wins) all the way to Iron Wall
(500 wins), which also shaves 2% off your outgoing travel time — a trophy that
pays for itself.

**The knowledge tree** is now split into a main branch and optional side
branches. Main-branch techs are the required backbone — you'll eventually need
all of them to keep advancing eras, including the tech that unlocks your
ruler. Left and right branches (Trade, Military, Science, Culture, and more)
are where the real power spikes live: Caravan Networks, for instance, adds a
flat +0.3 gold/s once researched. But every hour spent down a branch is an
hour not spent pushing toward the next era's tech — branches make you
stronger now at the cost of getting there later. Choosing when to detour, and
how far, is the new strategic knob.

**Towers and critters** also saw dozens of balance changes this cycle —
damage, reload times, health, new units, and a few retirements. The full
list, era by era, is up on the
[tower & critter changes page](/tower-critter-changes.html).

## 2026-06-10

### Culture Raiding — fairer loot even for lost attacks

When attacking another empire, culture is now stolen even if the attack fails —
as long as the defender lost lives in the process.

**New calculation:**

The stolen culture amount consists of two parts:

1. **Lives share** (always applies, even on attacker defeat):
   `defender's lost lives × era factor × rate`
   The more lives the defender lost and the more advanced their era, the more
   culture is stolen.

2. **Pool share** (only on attacker victory):
   Additionally a random percentage (1–5%) of the defender's total culture pool.

**Era penalty:** If a player attacks an empire in a lower era, they receive only
50% of the stolen culture — cultural progress protects.
