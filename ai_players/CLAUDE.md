# CLAUDE.md — ai_players

Autonomous bot players that play empire1 via the public REST API. **Dev only** —
`run_bot.py` refuses non-localhost server URLs. See `README.md` for usage.

## Spec-Synced Strategy Docs

The markdown files in `docs/strategies/` (`baseline.md`, `attack.md`,
`defense.md`, `growth.md`, `artifact.md`) are the **spec** for the planner
classes in `bot/planners/`. Any behavior change must update code and the
matching strategy doc together — they are kept 1:1 in sync. `docs/bot-flow.md`
describes the overall decision loop.

## Layout

- `run_bot.py` — single bot entry point; `fleet.py` — run N bots
- `bot/` — strategy, planners, analyzer, army building, simulation
- `states/<name>.yaml` — per-bot persisted state (credentials, strategy, memory)

## Tests

```bash
rtk run_tests.sh ai_players/tests/          # or --match=<pattern>
```
