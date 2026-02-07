# engine/ — Schnittstellen

## Rolle
Spiellogik-Services. Jeder Service bekommt Abhängigkeiten per Constructor Injection.
Services sind zustandslos wo möglich — der Zustand lebt in den `models/`.

## Abhängigkeiten

```
engine/
├── game_loop.py        → empire_service, attack_service, statistics, EventBus
├── empire_service.py   → upgrade_provider, EventBus
├── battle_service.py   → upgrade_provider, EventBus
├── attack_service.py   → EventBus
├── army_service.py     → upgrade_provider, EventBus
├── ai_service.py       → upgrade_provider
├── statistics.py       → (keine Service-Abhängigkeiten)
├── upgrade_provider.py → (keine Service-Abhängigkeiten)
└── hex_pathfinding.py  → (nur models/hex)
```

## Wird verwendet von

| Konsument | Welche Services |
|-----------|-----------------|
| `main.py` | Alle — instanziiert und verdrahtet |
| `network/router.py` | Ruft Service-Methoden über Message-Handler auf |
| `engine/game_loop.py` | `empire_service.step()`, `attack_service.step()`, `statistics` |

## Service-Schnittstellen

### GameLoop
```python
async run() -> None        # Startet den 1s-Tick-Loop
stop() -> None             # Stoppt den Loop
```

### EmpireService
```python
step(empire, dt) -> None                            # 1s Tick
build_item(empire, iid) -> str | None               # Bau starten
place_structure(empire, iid, q, r) -> str | None     # Turm platzieren
remove_structure(empire, sid) -> str | None           # Turm abreißen
upgrade_citizen(empire) -> str | None                 # +1 Bürger
change_citizens(empire, distribution) -> str | None   # Umverteilen
```
Rückgabe: `None` = Erfolg, `str` = Fehlermeldung.

### BattleService
```python
async run_battle(battle) -> None       # Battle als asyncio-Task
tick(battle, dt_ms) -> None            # Deterministischer Tick (für Tests)
loot_defender(battle, defender, attackers) -> None  # Loot bei Niederlage
```

### AttackService
```python
step(attack, dt) -> None                                    # ETA-Countdown
start_attack(attacker_uid, defender_uid, army_aid) -> Attack | str
```

### ArmyService
```python
create_army(empire, direction, name) -> Army | str
calculate_cost(army) -> float
calculate_slots(wave_index, empire) -> int
```

### AIService
```python
generate_army(effort_level) -> Army | None
get_difficulty_tier(effort_level) -> str
```

### StatisticsService
```python
calc_tai(empire) -> float
check_win_conditions(empire) -> str | None
```

### UpgradeProvider
```python
load(items) -> None
get(iid) -> ItemDetails | None
get_by_type(item_type) -> list[ItemDetails]
check_requirements(iid, completed) -> bool
get_costs(iid) -> dict[str, float]
get_effects(iid) -> dict[str, float]
available_critters(completed) -> list[ItemDetails]
```

## Kommunikation zwischen Services

Services kommunizieren **nicht direkt** miteinander. Zwei Wege:

1. **EventBus** — für asynchrone Benachrichtigungen (z.B. `ItemCompleted`, `BattleFinished`)
2. **GameLoop** — orchestriert die Aufrufreihenfolge explizit

```
Router → Service-Methode → Zustandsänderung auf Model → EventBus.emit()
                                                              │
GameLoop lauscht auf Events → reagiert im nächsten Tick ◄─────┘
```

## Battle-Service Tick-Reihenfolge

**Muss eingehalten werden** (Reihenfolge beeinflusst Spielmechanik):

```
1. _step_shots(battle, dt_ms)     # Flugzeit, Schadens-Anwendung
2. _step_critters(battle, dt_ms)  # Bewegung, Burn-Tick
3. _step_towers(battle, dt_ms)    # Targeting, Feuern
4. _step_armies(battle, dt_ms)    # Wellen-Timer, Critter-Spawn
```
