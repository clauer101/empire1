# Fehlende Nachrichten-Handler

Vergleich Java `Request`-Typen / `GameEngine.HandleRequestQueue()` / `GameServer.handleRequest()` mit Python `handlers.py`.

**Legende:** ✅ registriert (ggf. Stub) · ❌ fehlt komplett

## Engine-Nachrichten (Client → Engine)

| Java Request-Typ | Python Handler | Status |
|---|---|---|
| `SummaryRequest` | `summary_request` | ✅ implementiert |
| `ItemRequest` | `item_request` | ✅ Stub (keine Items aus UpgradeProvider) |
| `CritterRequest` (MilitaryRequest) | `military_request` | ✅ Stub (attacks/critters leer) |
| `NewItemCommand` | `new_item` | ✅ Stub |
| `NewStructure` | `new_structure` | ✅ Stub |
| `DeleteStructure` | `delete_structure` | ✅ Stub |
| `UpgradeStructure` | — | ❌ |
| `CitizenUpgradeRequest` | `citizen_upgrade` | ✅ Stub |
| `ChangeCitizenRequest` | `change_citizen` | ✅ Stub |
| `IncreaseHealthRequest` | — | ❌ |
| `NewArmy` | `new_army` | ✅ Stub |
| `ChangeArmy` | — | ❌ |
| `NewWave` | — | ❌ |
| `ChangeWave` | — | ❌ |
| `NewAttackRequest` | `new_attack_request` | ✅ Stub |
| `EndSiegeRequest` | — | ❌ |
| `BattleRegisterRequest` | — | ❌ |
| `BattleUnRegisterRequest` | — | ❌ |
| `NextWaveRequest` | — | ❌ |
| `CreateEmpire` | — | ❌ |

## Server-Nachrichten (Client → Server)

| Java Request-Typ | Python Handler | Status |
|---|---|---|
| `Auth` | — | ❌ |
| `Signup` | — | ❌ |
| `ChangePreferences` | — | ❌ |
| `PreferencesRequest` | — | ❌ |
| `UserInfoRequest` | — | ❌ |
| `HallOfFameRequest` | — | ❌ |
| `TimelineRequest` | — | ❌ |
| `UserMessage` | — | ❌ |
| `NotificationRequest` | — | ❌ |

---

## Was zu implementieren ist

### `upgrade_structure`
IID + TilePosition vom Client. Prüfe Requirements & Ressourcen, ersetze Structure auf dem Tile durch Upgrade-Variante. Kosten abziehen.

### `increase_life`
Erhöhe `empire.max_life` um 1. Koste Culture (progressiv nach aktuellem max_life). Prüfe ob `max_life < effect(LIFE_MAXIMUM)`.

### `change_army`
AID + neuer Name + neue Direction. Ändere Name/Direction der Army, sofern sie nicht gerade in Battle/Travelling ist.

### `new_wave`
AID + IID. Füge eine Welle zur Army hinzu. Prüfe max. Wellen-Limit (aus Effects), ggf. Gold-Kosten für zusätzlichen Wellen-Slot. Boss-Critter darf nur einmal vorkommen.

### `change_wave`
AID + WaveNumber + neue IID. Ändere den Critter-Typ einer bestehenden Welle. Army darf nicht im Kampf sein.

### `end_siege`
Sender-UID. Beende die laufende Belagerung des eigenen Empires.

### `battle_register`
Sender + UID des Battles. Registriere den Sender als Beobachter eines laufenden Battles (erhält BattleUpdates).

### `battle_unregister`
Sender + UID. Entferne den Sender als Battle-Beobachter.

### `battle_next_wave`
Sender-UID (= Battle-UID). Triggere die nächste Angriffs-Welle im laufenden Battle. Antwort: `NextWaveResponse` mit WavePreview.

### `create_empire`
UID für neues Empire. Erstelle ein frisches Empire-Objekt und registriere es im EmpireService.

### `auth_request`
Username + Passwort. Prüfe Credentials gegen DB, antworte mit `AuthResponse` (success + UID oder fail). Bei Erfolg: registriere Connection mit UID.

### `signup`
Username + Passwort (MD5) + E-Mail. Erstelle DB-Eintrag, dann `CreateEmpire` + automatischer Auth-Flow.

### `change_preferences`
Statement + E-Mail. Aktualisiere Spieler-Profildaten in der DB.

### `preferences_request`
Sender-UID. Lade E-Mail/Statement aus DB, antworte mit `PreferencesResponse`.

### `userinfo_request`
Optionale Liste von UIDs (oder alle). Lade UserInfo (TAI, currBuilding, currResearching, Citizen-Anzahl etc.) und antworte mit `UserInfoResponse`.

### `hall_of_fame_request`
Sender-UID. Lade Ranking, Winners, Prosperity, DefenseGod, TreasureHunter, WorldWonder Listen. Antworte mit `HallOfFameResponse`.

### `timeline_request`
UID + Liste zu markierender gelesener Nachrichten. Lade Postfach (letzte 25 Nachrichten, max 10 Tage alt). Antworte mit `TimelineResponse`.

### `user_message`
Sender + Empfänger-UID + Body. Speichere private Nachricht in DB als `private_unread`.

### `notification_request`
Sender-UID. Liefere ausstehende Notification (aus NotificationMap) oder fallback SummaryRequest.
