# Changelog

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
