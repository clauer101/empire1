# Attack Strategy

> **Implementation:** `ai_players/bot/planners/attack.py` — `AttackPlanner.propose_options()`
> (phase machine in `strategy.params["phase"]` when attack is active, or
> `memory["attack_state"]` when it isn't — see "Always attacking" below).
> Ruler helpers: `bot/army_building.py` (`pick_ruler`, `next_skill`, `ruler_wave_target`, `critter_power`).
> Target scoring: `bot/analyzer.py::score_targets` (era guard via `ERA_RANK`).
> Strategy selection: `bot/strategy.py::roll_strategy` (weighted-random
> between attack and growth, reached only after a defense-win-streak — see
> `bot-flow.md`'s Strategy System section).
> This file is the spec — when the planner changes, update it (and vice versa).

**Goal:** Defeat a deliberately chosen weak opponent to loot culture (and possibly knowledge/artifacts).

`roll_strategy()` is only ever called after `DEFENSE_WIN_STREAK_TARGET`
consecutive defense wins; it picks attack (vs. growth) weighted by
`config.yaml` and personality, when an attackable target exists. If no
target exists, attack is excluded from that roll — falling back to growth,
or (if growth also has zero weight) a short-lived (5 minute) `defense`
placeholder that re-checks soon rather than parking on defense for hours.
Targets are scored from the leaderboard and past battle reports
(`bot/analyzer.py::score_targets`); higher-era empires are never attacked.

**Target selection spreads bots across different opponents:** weaker
(lower-culture) empires score higher, but the target is sampled with
`weighted_top_n` across the **whole** viable pool (not just the single
top-scored one) — otherwise every bot's independent scoring converges on
whichever single empire is globally weakest, and they all pile onto the same
target. `memory["last_beaten_name"]` (the single most recent attack victory,
set in `process_new_reports`) gets a moderate bonus (`LAST_BEATEN_BONUS =
1.0`) so a bot tends to keep re-attacking an opponent it already has a proven
easy win against — without being so dominant that it overrides the
weighted sampling and locks every bot onto the same first-drawn target.
Defense only takes over reactively — see
[when a defense is fully lost](defense.md) — as a temporary, necessary
detour before the bot resumes attacking.

## Always attacking for free — even while defense is the active strategy

Spying/attacking/wave-fill cost no gold, so this planner's phase machine
(spy, attack, result) and its free army maintenance (ruler placement,
filling/refreshing waves with already-unlocked critters) run **every cycle
regardless of which strategy is nominally active** —
`bot/dispatch.py::gather_options` includes the attack planner unconditionally
unless [growth](growth.md) is active (growth means "invest in nothing, not
even free"). `advance_phase` gates only the phase-sequencing/self-selection
behavior below, not whether the planner runs at all.

- When `strategy.type == "attack"`, the target/phase live in `strategy.params`
  as usual (a fresh roll/override controls them), and `is_active` (see below)
  is `True` — gold-spending army growth is allowed.
- Otherwise (e.g. `defense` is active), this planner keeps its **own**
  persistent target/phase in `memory["attack_state"]`, and **self-selects a
  target** via `bot/analyzer.py::score_targets` when it doesn't have one yet.
  It never touches `strategy.completed` in this case (that belongs to the
  other, actually-active strategy) — on victory it just clears
  `memory["attack_state"]` so a fresh target is picked next cycle. `is_active`
  is `False` here — see below for what that gates.

## Gold-spending army growth is active-only

Creating an army, adding the first wave, buying critter slots, workshop
upgrades, and era-upgrading waves all cost gold — these only run when
`strategy.type == "attack"` (`is_active` in the code). A bot sitting in
`defense` (or any strategy other than `attack`) must not fund an army from
that strategy's gold budget just because this planner free-rides in the
background. Only the genuinely free actions (ruler placement, wave-fill with
an already-unlocked critter, spy/attack calls) run unconditionally — see
"Army composition" below for exactly which steps are gated.

## Army composition (single army, always current-best critters)

The bot builds and maintains **exactly one** army. Every cycle, regardless of
which strategy is active (free steps only — see the `is_active` gate above
for what's gold-gated):

**Free — run regardless of `is_active`:**

1. **Fill any empty wave** with the best unlocked critter that wave's own
   `max_era` cap allows. When several critters tie at the highest reachable
   era, one is picked **uniformly at random** (`_top_era_pick()`) — bots don't
   all field an identical army.
2. **Refresh outdated waves:** an already-filled wave whose critter's era is
   *below* the top era that wave could now hold gets swapped to a fresh
   (again randomly tie-broken) top-era critter — the "always the best critter"
   rule is not limited to freshly-added waves.

**Gold-spending — only when `is_active` (`strategy.type == "attack"`):**

3. **Create the army** and **add its first wave** if either doesn't exist yet.
4. **Target wave count:** `max(2, ceil(era_rank * 1.5))` — e.g. stone/neolithic
   → 2, bronze → 3, iron → 5, medieval → 6, renaissance → 8, industrial → 9,
   modern → 11, future → 12 (`_target_waves()`). **Grow toward it** (`add_wave`)
   once gold allows.
5. **Raise a wave's era cap** (`buy_wave_era`) toward — never above — the
   empire's own `era_rank`.
6. **Buy a slot** — always on the wave with the **fewest** current slots
   (never the ruler's wave), so slot counts grow evenly across
   waves instead of piling onto whichever slot happens to be cheapest.
7. **Workshop upgrade** — absolute last priority (`PRIO_CRITTER_UPG`), only
   proposed once nothing above is available/affordable this cycle. Targets
   the critter type most represented across the army's waves
   (`_most_common_wave_critter()`). Commits to **one** randomly-picked stat
   per critter type at a time (`_focus_upgrade_stat()`, remembered in
   `memory["upgrade_focus"]`) instead of always maxing the same stat first —
   once that stat hits its cap it rotates to a different one. Cap is
   `3 × (era_rank + 1)` of the critter's own era (`_max_upgrade_level()`), so
   later-era critters allow deeper investment.

Steps 4-7 (`_growth_options()`) compete purely on `Option.priority` (add-wave
ranks above era-upgrade) — whichever is affordable first gets bought; if a
step is unaffordable it declares a [savings goal](baseline.md) via
`saves_for`/`goal_meta`. None of this **blocks** spy/attack (see Phase
machine below) — attacking is free, so the bot attacks with whatever army it
currently has while these (when active) keep improving it, indefinitely.

## Ruler deployment

Runs every cycle once an army with at least one wave exists, before the phase
machine (one action per cycle):

1. **Choose** — once `effects.ruler_unlock > 0` and no ruler is chosen
   (`summary.ruler.type` empty), pick a uniformly random ruler from the
   catalog (`army_building.pick_ruler`) via `POST /api/empire/ruler/choose` —
   random so the bot population spreads over all rulers.
2. **Skill up** — handled by baseline (`SKILL_ORDER` Q→W→E→R, caps 5/5/5/3,
   `army_building.next_skill`), not by this planner.
3. **Place in a wave** — if no wave carries the ruler yet, place it in a
   **uniformly random** existing wave of the (single) army
   (`army_building.ruler_wave_target`) via `POST /api/army/set-ruler-wave`.
   The ruler's wave is never touched by the fill/swap/slot logic above.

## Phase machine

Stored in `strategy.params.phase`:

```
strengthen → spy → wait_spy → attack → wait_result ──victory──▶ completed
    ▲                            ▲                  └─defeat──▶ strengthen ─┘
    └────────────────────────────┘
```

- **strengthen** — advances to `spy` as soon as **any** non-ruler wave carries
  a critter (any era) — it does *not* wait for every wave to reach `era_rank`
  or for the wave count to meet the target. That used to be the gate, but
  both are gold-gated and the era target keeps moving as the empire advances,
  so it could block attacking indefinitely; since attacking is free there is
  no reason to wait. Army growth (steps 3-7 above, when `is_active`) keeps
  happening in the background regardless of phase.
- **spy** — runs a spy attack on the target, advances to `wait_spy`.
- **wait_spy** — waits for the spy attack to resolve (no outgoing attacks
  left), then advances to `attack`.
- **attack** — launches the army once no outgoing attack is pending, advances
  to `wait_result`.
- **wait_result** — reads the battle report from `memory.attack_history` for
  the target: victory while `is_active` → `strategy.completed = True` (read by
  `run_bot.py` to immediately roll a fresh attack/growth strategy, independent
  of the defense-win-streak mechanism); victory while *not* active → just
  clears the self-selected target in `memory["attack_state"]` so a fresh one
  is picked next cycle; anything else → back to `strengthen` (no defeat
  counter or give-up limit — the bot keeps trying against the same target
  until it wins or the strategy is overridden by a lost defense).

## Success / termination criteria

- **Victory while attack is active** → `strategy.completed = True`, `run_bot.py`
  immediately rolls a new attack/growth strategy (see `bot-flow.md`) — this is
  the one strategy transition outside the defense-win-streak rules.
- **Victory while self-selecting in the background** → just picks a new target,
  no strategy-level effect.
- A lost defense always overrides attack, active or not — see `defense.md`.

## Baseline obligations

Like defense and growth, this strategy is subject to the
[baseline obligations](baseline.md): defense is never neglected (breach
response plus an era-scaled minimum tower count — except while
[growth](growth.md) is active, which suspends both), idle time on building
and research is minimized (empty queues are filled with the cheapest
affordable item each cycle), and active savings goals are respected.
