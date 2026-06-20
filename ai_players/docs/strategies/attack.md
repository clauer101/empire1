# Attack Strategy

> **Implementation:** `ai_players/bot/planners/attack.py` — `AttackPlanner.propose()`
> (phase machine in `strategy.params["phase"]`), success test `_goal_reached()`.
> Army decisions (ruler + strengthening): `bot/army_building.py`.
> Target scoring: `bot/analyzer.py::score_targets` (era guard via `ERA_RANK`).
> Weights/durations: `config.yaml`; no-army gating: `bot/strategy.py::roll_strategy`.
> This file is the spec — when the planner changes, update it (and vice versa).

**Goal:** Defeat a deliberately chosen weak opponent to loot culture (and possibly knowledge/artifacts).

Default weight: 3. Duration: 1–3 hours. Without an army the weight is set to 0 only when an army is financially out of reach (gold < 30% of the next army price); otherwise it is halved until the first army exists (the planner creates one, saving toward it if needed). Targets are scored from the leaderboard and past battle reports (`bot/analyzer.py`); higher-era empires are never attacked.

## Revenge after a lost attack

Offensive analog to the [breach response](defense.md): when a battle report shows
a **lost attack** (`role == "attacker"`, not won), the bot force-switches back to
the attack strategy against the same opponent (`source: "revenge"`, phase `spy`),
provided no breach occurred in the same cycle (defense wins), the current
strategy is not already `attack`, the personality's
`attack_defeat_response_chance` roll passes (config.yaml: aggressive 0.9,
balanced 0.6, economy 0.3, defensive 0.2), and the opponent's uid can be
resolved from the leaderboard by name.

Independent of the forced switch, the defeat is marked in
`memory.recent_attack_defeat`; the next regular strategy roll doubles the attack
weight once (mirror of the defense boost after a lost defense), then the flag is
cleared.

## Objectives

1. **Build an army** — create one if none exists; if unaffordable, declare a
   [savings goal](baseline.md) for the army price so other spending pauses until
   it can be bought. Then fill empty waves with the strongest unlocked critter.
2. **Deploy the ruler** — see below.
3. **Build up** — proactively strengthen the army to a power target *before* the
   first spy (see below).
4. **Spy first** — run a spy attack on the target to gather intel.
5. **Attack** — launch the army once no outgoing attack is pending.
6. **Evaluate result** — read the battle report from `memory.attack_history`;
   on defeat, strengthen the army and try again (see below).

## Build toward the era template

While the attack strategy is active the bot strengthens its army toward an
**era-matched template** before spying, so the first attack fields a structured
army instead of a single weak wave. The template is derived from the server's
`python_server/config/ai_waves.yaml`: one representative army per era (median by
total slots), condensed by `ai_players/scripts/gen_army_templates.py` into
`ai_players/config/army_templates.yaml` and loaded via
`army_templates.load_templates()`. `template_for_era(era_rank)` picks the
template for the bot's current era (clamping down if the exact era is absent).

The template is a **loose guideline**, not a rigid copy. It supplies three
things to `army_building.strengthen_plan(..., template, defeats)`:

- **Critter type per wave** — each wave aims at its template critter
  (`resolve_template_critter`): use it when unlocked and era-fitting, otherwise
  fall back to the strongest fitting critter (best-effort).
- **Slots per wave** — `buy_slot` stops once a wave reaches its template slot
  count.
- **Wave count** — `add_wave` grows the army toward `len(template)` waves.

Era climbing (`buy_wave_era`) stays template-independent so an outdated wave
always advances toward current-era critters first.

The build-up **power target** is `army_building.template_target_power()` — the
sum of `critter_power(resolved) × slots` over the template's waves. Strengthening
ends and moves to `spy` when current `army_building.army_power()` meets that
target, when `strengthen_plan` has no more options, or when the cheapest option
exceeds `STRENGTHEN_GOLD_CAP` and is unaffordable. Unaffordable options declare a
(sticky) savings goal.

**Exceeding the template after a defeat:** the template is the floor, not the
ceiling. Each defeat (`params.defeats`) loosens the caps so the army overshoots
the template — per-wave slot cap grows by `OVERSHOOT_SLOTS_PER_DEFEAT` (×0.25)
per defeat and the wave-count cap rises by one wave per defeat.

The army/wave/build-up savings goals are **sticky** (`savings.set_goal(...,
sticky=True)`): unlike normal goals they survive a strategy-type change and are
not clamped to the attack window's end, so the gold saved toward the army is not
burned by baseline spending when a different strategy rolls between attack
windows (it still expires on its TTL, so no deadlock).

## Ruler deployment

Runs every cycle after an army exists, before the phase machine (one action per cycle):

1. **Choose** — once `effects.ruler_unlock > 0` and no ruler is chosen
   (`summary.ruler.type` empty), pick a uniformly random ruler from the
   catalog (`army_building.pick_ruler`) via `POST /api/empire/ruler/choose` —
   random so the bot population spreads over all rulers.
2. **Skill up** — spend skill points in `SKILL_ORDER` (R, then Q/W/E; caps 5/5/5/3,
   `army_building.next_skill`). A 4xx rejection (no points) sets
   `memory.ruler_skill_blocked_until` and skill-up is retried after 1 hour.
3. **Place in a wave** — if no wave of any army carries the ruler, place it in
   wave 0 of the strongest army (`army_building.ruler_wave_target`) via
   `POST /api/army/set-ruler-wave`. One ruler per army; the ruler spawns once
   per battle and the wave is never modified by strengthening or wave filling.

## Strengthen on defeat

A defeat no longer abandons the target immediately. `strategy.params.defeats`
counts losses against the current target:

- defeats ≤ 6 (`army_building.MAX_STRENGTHEN_ROUNDS`) → phase `strengthen`,
- defeats > 6 → give up, strategy completed (re-roll; recent defeat boosts the
  defense weight).

In phase `strengthen`, `army_building.strengthen_plan()` ranks options by power
gain per gold (free options first), using the per-slot power heuristic
`health × (1+armour) × (1+speed) / slots` that mirrors the server formula:

1. **Switch critter** (free) — set a wave to the strongest available critter that
   fits its `max_era` (`PUT /api/army/{aid}/wave/{n}`).
2. **Buy a critter slot** (`POST /api/army/buy-critter-slot`).
3. **Buy a wave era** when a stronger critter sits one era above the wave's
   `max_era` (`POST /api/army/buy-wave-era`).
4. **Add a wave** when all waves of the first army are filled (`POST /api/army/{aid}/wave`).
5. **Create a second army** once the first has ≥ 3 waves (`POST /api/army`).

The best option is executed and the phase returns to `attack`. If it is
unaffordable, a [savings goal](baseline.md) is declared and the bot waits.
The ruler wave is never touched.

## Phase machine

Stored in `strategy.params.phase`:

```
strengthen → spy → wait_spy → attack → wait_result ──victory──▶ completed
    ▲                            ▲                  └─defeat──▶ strengthen ─┘ (≤6 rounds)
    └────────────────────────────┘
```

The strategy starts in `strengthen` (build toward the era template), advancing
to `spy` once the template power target is met or no affordable option remains.

## Success / termination criteria

- **Victory** → goal reached, strategy completed, new strategy is rolled.
- **4th defeat** against the same target → give up, strategy completed (re-roll).
- **Expiry** before any result → re-roll.

## Baseline obligations

Like every strategy, this one is subject to the [baseline obligations](baseline.md):
defense is never neglected (breach response plus an era-scaled minimum tower
count — tiles are bought and towers built in every strategy), idle time on
building and research is minimized (empty queues are filled with the cheapest
affordable item each cycle), and active savings goals are respected.
