> **Status: active** — mechanic analysis of the diplomacy/alliance system and the
> pooled-culture ranking, both introduced in commit `7736db7` (2026-08-20).
> Describes how it works and which gaps exist.
>
> **Update 2026-08-23:** §4.1 / §5.3a resolved — the season snapshot
> (`game_loop.py`) and `/api/season-results` now rank on the same
> alliance-pooled culture as the live leaderboard, via the shared
> `util/alliance_grouping.group_by_pooled_culture()` helper. A place (podium
> position) can now be shared by a mutually-allied pair. §5.1 (missing
> `ally_effects` in `rulers.yaml`) and §5.2 (break/re-form drain exploit)
> remain open.

# Diplomacy & Pooled Score — How It Works

Companion to `tasks/season_balance_diff_analysis_20260820.md`. Everything here
landed in the same commit, `7736db7` "pre bala changes" — `diplomacy.py` is a new
file added in that commit.

## 1. Data model — declarations, not alliances

There is no "alliance" record. There is a single directed table:

```sql
CREATE TABLE alliance_declarations (from_uid, to_uid, created_at)
```

An **alliance exists only as an emergent property**: A and B are allied iff both
`(A,B)` and `(B,A)` rows exist. Derived in
`_alliance_status()` (`network/routers/diplomacy.py:17`) into four states:

| declared_to | declared_by | status |
|---|---|---|
| ✓ | ✓ | `allied` |
| ✓ | — | `pending_sent` |
| — | ✓ | `pending_received` |
| — | — | `none` |

One endpoint drives all of it: `POST /api/diplomacy/alliance` with a `target_uid`,
which **toggles** the caller's own row (`toggle_alliance_declaration`, rate-limited
to 20/minute). Request, accept, cancel and break are all the same call — the
meaning depends only on the state before the toggle.

`Empire.allied_uids` is an in-memory cache of the mutual set, not persisted
(rebuilt from the DB at startup in `main.py:699`), used for effect recalculation.

## 2. Costs — a symmetric culture swap

From `game.yaml`: `alliance_culture_cost: 0.05`, `max_alliances: 1`.

**On forming** (the toggle that completes mutuality), both sides pay 5 % of *their
own* culture **to each other** — `diplomacy.py:88–94`. Both payments are computed
before either is applied, so it is a clean simultaneous swap:

```
A_after = 0.95·A + 0.05·B
B_after = 0.95·B + 0.05·A
```

Net for A: `0.05·(B − A)`. The **poorer partner gains, the richer partner loses** —
this is an equalizing transfer, not a cost in the usual sense. Total culture is
conserved on formation.

**On breaking**, only the breaking player pays 5 % of their own culture, and that
amount is **destroyed**, not transferred (`diplomacy.py:95–99`). The partner who
gets left pays nothing.

**Capacity**: forming a *new* mutual alliance is rejected if either side already
has one (`get_max_alliances`, `empire_service.py:591` — flat 1 from `game.yaml`,
with a `max_alliances_offset` effect hook already wired for future content).

## 3. What an alliance actually does

| Effect | Where | Status |
|---|---|---|
| Cannot attack each other | `handlers/military.py:281–289`; `can_attack: false` in `/api/empire/list` | ✅ works |
| Ranked as a block by pooled culture | `routers/empire.py:256–298` | ✅ works |
| Ally's ruler grants bonus effects | `get_ally_effects` (`empire_service.py:571`) | ⚠️ **inert — see §5.1** |

Note what is **not** there: no shared vision, no assisting in battle, no shared
armies, no shared artifacts, no joint defense. The alliance is a non-aggression
pact plus a ranking bracket.

## 4. The pooled score — display only

`GET /api/empire/list` (`routers/empire.py:135`) does the grouping:

1. Build connected clusters over the mutual-alliance graph (flood fill,
   `empire.py:259–274`). With `max_alliances: 1` a cluster is always a pair, but
   the code is written for arbitrary cluster sizes.
2. Each empire gets `alliance_group_id` and `alliance_group_culture`
   (= sum of the cluster's culture), both `null` for unallied players.
3. **Clusters are sorted by pooled culture descending**; within a cluster, members
   by their own culture descending. The flat list is then emitted in that order.

The frontend does *not* re-sort (`globalempires.js` explicitly notes this would
break group contiguity) and draws a box around each contiguous group
(`_allianceGroupBorderStyle`), showing the pooled total in accent color next to
each member's own culture.

**Culture is the season score** — the empire detail view renders it literally as
`${points} ✦ points` (`views/empire.js:304`).

### 4.1 The pooled ranking does not decide the season

`GameLoop._season_snapshot` (`engine/game_loop.py:208–229`) records the top 3 by
**individual** culture:

```python
ranked = sorted(empires, key=lambda e: e.resources.get("culture", 0.0), reverse=True)
winners = [... for i, e in enumerate(ranked[:3])]
```

No pooling, no alliance awareness. `seasonresults.js` is likewise per-empire.

So there are **two different rankings in the game at the same time**: the live
leaderboard ranks alliance groups by pooled culture, and the season result ranks
individuals. An allied pair can sit visibly at the top of the leaderboard on a
pooled total while neither member is in the individual top 3. Whether that is
intended is a design decision — but as it stands, the pooled number is decoration.

## 5. Findings

### 5.1 `ally_effects` does not exist in `rulers.yaml` — the alliance bonus is dead code

The whole ally-bonus path is wired end to end:

- `empire_service.get_ally_effects()` reads `self._rulers[ruler_type]["ally_effects"]`
- it is folded into `empire.effects` in `recalculate_effects` (`empire_service.py:530`)
- `auth.py:406` labels those effects with source `"alliance"` for the effects overlay
- `/api/empire/list` returns `ally_ruler_bonus` per empire (`empire.py:218–224`)
- `views/empire.js:279–286` renders a "🤝 Alliance Bonus from …" panel

But **`rulers.yaml` contains no `ally_effects` key for any of the five rulers**
(`grep -c ally_effects python_server/config/rulers.yaml` → 0). So
`get_ally_effects()` always returns `{}`, `ally_ruler_bonus` is always `{}`, and
the bonus panel never renders. Players currently get **zero mechanical benefit**
from an alliance beyond mutual non-aggression — while paying 5 % of their culture
for it.

This is the single most important gap: the feature's designed payoff is missing
from config. Adding an `ally_effects: {…}` block per ruler in `rulers.yaml` is all
that is needed — no code change.

### 5.2 Break/re-form can be cycled to drain a partner's score

Three facts combine badly:

1. Breaking removes **only the breaker's** row. The partner's declaration stays.
2. Therefore the breaker can re-form the alliance **alone**, with a second toggle —
   the partner never has to consent again.
3. There is **no cooldown**. `created_at` is stored but never read. The only limit
   is the 20/minute rate limit ≈ 10 full cycles per minute.

One cycle for the poorer player A against a consenting-once partner B:

```
break:    A = 0.95·A                    (5 % destroyed)
re-form:  A = 0.95·A + 0.05·B ,  B = 0.95·B + 0.05·A
```

A gains whenever `B > 2·A`. Simulated from A = 100, B = 10 000:

| cycle | A | B | total |
|---:|---:|---:|---:|
| 0 | 100 | 10 000 | 10 100 |
| 1 | 590 | 9 505 | 10 095 |
| 5 | 1 914 | 7 949 | 9 864 |
| 10 | 2 654 | 6 642 | 9 297 |
| 15 | 2 869 | 5 736 | 8 604 |

**≈ 90 seconds of toggling costs B 43 % of their season score**, with no action or
consent from B after the initial accept, and B has no way to stop it except
breaking first (which costs B 5 % as well). The system converges toward
`A = B/2`, so a bottom-ranked player can pull any top player down to a 2:1 ratio.

Cheapest fixes, in increasing strictness: read `created_at` and enforce a cooldown
before a re-form charges again; make breaking delete **both** rows so re-forming
needs fresh consent; or charge the formation cost only once per unique pair per
season.

### 5.3 The pooled score is the mutual benefit — and formation costs the group nothing

The pooled ranking is itself the payoff, for **both** sides including the leader:
an allied pair is ranked on `A + B`, a total no solo player can match without
actually having that much culture. The leader gains a standing they cannot reach
alone.

Two properties make this work cleanly:

- **Formation is exactly pool-neutral.** `A_after + B_after = 0.95·A + 0.05·B +
  0.95·B + 0.05·A = A + B`. The 5 % swap only redistributes *inside* the group; the
  number the group is ranked on does not move at all. Joining costs the alliance
  nothing.
- **The benefit is largest between equals, and there the cost is smallest.** The
  pooled gain is `B/A`: a 10 000-culture leader allying with an equal roughly
  doubles their standing (+90 % or so), while allying with a 100-culture player
  gains 1 %. The transfer runs the other way — near zero between equals, large when
  allying downward. Both gradients point at the same thing: **ally with a peer, not
  with someone you carry.** That is a coherent design, and it pushes top players
  toward each other rather than toward farming a weak partner.

The individual side of the transfer is not cosmetic, though, because of §5.5:
culture is never otherwise spent, so the 5 % a leader gives up allying downward is
a permanent individual setback that nothing else in the game can inflict.

### 5.3a …but the season result doesn't pool, so the benefit disappears when it counts

This is the direct consequence of §4.1. All season long the leaderboard shows the
alliance on `A + B`. At season end `record_season_winners` sorts **individual**
culture and records the top 3 from that. The shared score the two players allied
for is not what gets written down.

If the pooled score is meant to be the benefit — and per §5.3 it is the *only*
benefit right now — then `game_loop.py:212` should rank on the same pooled totals
the leaderboard uses, or the design should state explicitly that pooling is a live
standing only. As it stands the two rankings disagree, and they disagree at exactly
the moment that decides the season.

It also explains the incentive behind §5.2: cycling break/re-form **destroys**
pooled culture (10 100 → 8 604 in the simulation) while raising the cycler's
individual total. A player only benefits from that if individual standing is what
counts. Make the season pool, and the exploit loses most of its motive — the
cooldown is still worth adding, but it stops being profitable by design.

### 5.5 Diplomacy is the only thing in the game that reduces culture

`grep` for every place culture is decremented across the backend returns **three
lines, all in `diplomacy.py`** (the two formation payments and the break penalty).
Nothing else ever subtracts it: `upgrade_citizen` (`empire_service.py:717`) compares
culture against the price and refuses below it, but **never deducts** — the same
for tiles. Culture is a monotonically rising score that *gates* purchases by
threshold rather than being spent on them.

That makes the alliance transfer heavier than a normal cost. Losing 5 % does not
just lower a displayed number, it can drop a player back below a citizen or tile
threshold they had already cleared — the only backwards movement in the game. It
is also why the §5.2 cycle is so damaging: it attacks the one resource that has no
other sink and no way to be re-earned except slowly.

### 5.4 Smaller observations

- **The formation cost is paid by both, the break penalty by one.** Leaving an
  alliance is therefore cheaper than entering it, and being left costs nothing.
  That is a reasonable asymmetry, but combined with §5.2 it is the wrong way round —
  the *breaker* should carry more friction, not less.
- **`max_alliances` is checked only when completing a mutual pair**, not when
  declaring. A player can have unlimited outstanding `pending_sent` declarations
  and only hits the cap at accept time — that is fine, but it means the UI must
  handle "your request was accepted but rejected server-side". `views/empire.js:144`
  already pre-warns on the *receiving* side; the sending side does not.
- **`get_all_mutual_alliances()` loads the entire table on every
  `/api/empire/list` call** (120/minute rate limit, called on every leaderboard
  view). Fine at current player counts, worth watching.
- The cluster code (`empire.py:259–274`) is a general flood fill, so raising
  `max_alliances` above 1 will produce transitive blocks — A–B and B–C puts A, B
  and C in one pooled group even though A and C never allied. Worth deciding
  whether that is intended before raising the cap.
- The `spy_costs` removal (see the balance doc §1) and this feature ship together:
  intel is now a spy *army* (`/api/spy-attack`, `max_spy_armies: 1`) and
  aggression is now diplomatically gated. Both push the same direction — more
  player-to-player interaction, fewer pure gold sinks.
