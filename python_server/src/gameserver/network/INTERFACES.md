# network/ — Schnittstellen

## Rolle
WebSocket-Server, Message-Routing, Authentifizierung, Serialisierung.
Einzige Schicht mit Netzwerk-I/O.

## Abhängigkeiten

```
network/
├── server.py         → router.py
├── router.py         → models/messages.py
├── auth.py           → persistence/database.py
└── serialization.py  → (keine)
```

## Wird verwendet von

| Konsument | Was |
|-----------|-----|
| `main.py` | Instanziiert Server, registriert Handler beim Router |
| `engine/battle_service.py` | Nutzt `server.broadcast()` für Battle-Updates (via Callback) |

## Schnittstellen

### Server
```python
async start() -> None                      # WebSocket-Server starten
async send_to(uid, data) -> None            # Nachricht an Client
async broadcast(uids, data) -> None         # Nachricht an mehrere Clients
```

### Router
```python
register(msg_type, handler) -> None         # Handler für Nachrichtentyp registrieren
async route(raw_dict, sender_uid) -> None   # Nachricht parsen und dispatchen
```

Handler-Signatur: `async (GameMessage, int) -> None`

### AuthService
```python
async login(username, password) -> int | None     # UID oder None
async signup(username, password, email) -> int | str  # UID oder Fehler
```

### Serialization
```python
encode(data, compress=False) -> bytes    # Dict → JSON bytes
decode(raw, compressed=False) -> dict    # bytes → Dict
```

## Datenfluss

```
WebSocket ──raw bytes──▶ serialization.decode()
                              │
                         raw dict
                              │
                              ▼
                     router.route(dict, uid)
                              │
                      parse_message(dict)
                              │
                       typed GameMessage
                              │
                   handler(message, uid)
                              │
                    engine.service.method()
                              │
                       result / event
                              │
                              ▼
                     serialization.encode()
                              │
                   server.send_to(uid, data)
                              │
                              ▼
                         WebSocket
```

## Registrierung

In `main.py` werden alle Handler beim Router registriert:

```python
router.register("new_structure", handle_new_structure)
router.register("auth_request", handle_auth)
# ...
```

Die Handler-Funktionen leben **nicht** im network/-Modul, sondern werden
in `main.py` als Glue-Code zwischen Router und Engine-Services definiert.
