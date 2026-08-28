# Documentation Index

| Doc | Contents |
|---|---|
| [AI_WORKFLOW.md](AI_WORKFLOW.md) | How this project uses Claude Code — layered rules, skills, permissions, and guardrails |
| [API.md](API.md) | REST/WebSocket API reference — single source of truth; generates `web/api.html` |
| [DEVLOG.md](DEVLOG.md) | How the public devlog page is generated from `CHANGELOG.md` |
| [CODINGGUIDELINE.md](CODINGGUIDELINE.md) | Coding standards for backend and frontend |
| [EFFECTSGUIDE.md](EFFECTSGUIDE.md) | Effects system (burn, slow, splash, …) — config keys and semantics |
| [YAMLATTRIBUTEGUIDE.md](YAMLATTRIBUTEGUIDE.md) | Attribute reference for the game config YAMLs |
| [SEASONENDFLOW.md](SEASONENDFLOW.md) | Season-end flow (reset, trophies, carry-over) |
| [RUNTIMESTATS.md](RUNTIMESTATS.md) | Runtime statistics and monitoring |
| [FAIRPLAY.md](FAIRPLAY.md) | Fair-play policy — strong strategies get used, not banned; overpowered ones get balanced |

## Related documentation elsewhere

- `python_server/src/gameserver/*/INTERFACES.md` — public interface per backend package
- `ai_players/docs/` — bot flow + strategy specs (synced 1:1 with `ai_players/bot/planners/`)
- `web/scripts/AGENTS.md` — Node build scripts
- `tasks/` — planning/working notes with status headers
- `CLAUDE.md` + `.claude/rules/` — Claude Code behavior rules
