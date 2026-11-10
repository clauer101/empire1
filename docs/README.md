# Documentation Index

Use this index to choose the smallest relevant documentation set. Start with
the task routes below; the catalog groups the same files by subject.

## Agent Task Routes

| If the task is about... | Start with... | Then consult... |
|---|---|---|
| Understanding repository architecture, agent instructions, tests, CI, or deployment safety | [AI_WORKFLOW.md](AI_WORKFLOW.md) | Root `CLAUDE.md`, applicable `.claude/rules/`, and the owning package's `INTERFACES.md` |
| Implementing or reviewing code | [CODINGGUIDELINE.md](CODINGGUIDELINE.md) | The relevant domain guide below and the package interface doc |
| Adding or changing a REST/WebSocket endpoint | [API.md](API.md) | `.claude/rules/deployment.md` for nginx routing and [AI_WORKFLOW.md](AI_WORKFLOW.md) for validation scope |
| Changing game effects, config attributes, or balance | [EFFECTSGUIDE.md](EFFECTSGUIDE.md) or [YAMLATTRIBUTEGUIDE.md](YAMLATTRIBUTEGUIDE.md) | [BALANCING.md](BALANCING.md) and the `balancing` skill when testing combat outcomes |
| Changing seasonal resets, trophies, or carry-over | [SEASONENDFLOW.md](SEASONENDFLOW.md) | Relevant season-end tests in `python_server/tests/` |
| Investigating telemetry or interaction logs | [RUNTIMESTATS.md](RUNTIMESTATS.md) | Runtime implementation and tests |
| Editing public changelog/devlog output | [DEVLOG.md](DEVLOG.md) | `CHANGELOG.md` and the frontend build rules |
| Evaluating player strategy or fair-play policy | [FAIRPLAY.md](FAIRPLAY.md) | [BALANCING.md](BALANCING.md) and bot strategy specifications, if relevant |

## Repository Workflow and Engineering

| Document | Use it for |
|---|---|
| [AI_WORKFLOW.md](AI_WORKFLOW.md) | Runtime architecture, test suites and CI scope, Claude Code rules and skills, permissions, bot agents, and operational guardrails |
| [CODINGGUIDELINE.md](CODINGGUIDELINE.md) | Backend and frontend coding conventions, typing, validation, and common implementation patterns |
| [API.md](API.md) | REST/WebSocket contract; this is the source for generated `web/api.html` |
| [DEVLOG.md](DEVLOG.md) | The pipeline that generates the public devlog page from `CHANGELOG.md` |

## Game Rules and Configuration

| Document | Use it for |
|---|---|
| [EFFECTSGUIDE.md](EFFECTSGUIDE.md) | Effect config keys and behavior for towers, critters, and empires |
| [YAMLATTRIBUTEGUIDE.md](YAMLATTRIBUTEGUIDE.md) | YAML config attributes and the checklist for adding an attribute |
| [BALANCING.md](BALANCING.md) | Combat balance goals, era progression, and tower/critter counter expectations |
| [FAIRPLAY.md](FAIRPLAY.md) | Fair-play policy and the distinction between strong strategies and balance problems |
| [SEASONENDFLOW.md](SEASONENDFLOW.md) | Season-end reset, trophies, and state carry-over |

## Operations and Observability

| Document | Use it for |
|---|---|
| [RUNTIMESTATS.md](RUNTIMESTATS.md) | Runtime statistics and empire-interaction logging |
| [AI_WORKFLOW.md](AI_WORKFLOW.md) | Deployment process, environment boundaries, test safety, and agent guardrails |

## Related Documentation Outside `docs/`

- `CLAUDE.md` and `.claude/rules/` — repository-wide and path-scoped agent instructions; read the rule matching the files being changed.
- `python_server/src/gameserver/*/INTERFACES.md` — public interface and ownership boundary for each backend package.
- `ai_players/CLAUDE.md` and `ai_players/docs/` — bot workflow and strategy specifications, kept in sync with `ai_players/bot/planners/`.
- `web/CLAUDE.md` and `web/scripts/AGENTS.md` — frontend layout, build scripts, and generated assets.
- `tasks/` — planning notes and work-in-progress documents; check each note's status before treating it as current guidance.
