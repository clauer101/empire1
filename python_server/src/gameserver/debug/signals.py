"""Signal catalog — complete list of all client→server messages for the debug dashboard.

Each entry defines the message type, its parameters, description, and category.
The dashboard uses this to render a form for each signal.
"""

from __future__ import annotations

from typing import Any

# Parameter types used in the forms
TEXT = "text"
INT = "int"
FLOAT = "float"
JSON = "json"  # free-form JSON object


def _p(name: str, ptype: str = TEXT, default: Any = "", desc: str = "") -> dict:
    """Shorthand for a parameter definition."""
    return {"name": name, "type": ptype, "default": default, "description": desc}


# -------------------------------------------------------------------
# Signal catalog — every client→server message that can be sent
# -------------------------------------------------------------------

SIGNAL_CATALOG: list[dict[str, Any]] = [

    # ── Auth ───────────────────────────────────────────────────────
    {
        "category": "Auth",
        "type": "auth_request",
        "description": "Login mit Benutzername und Passwort",
        "params": [
            _p("username", TEXT, "testuser", "Benutzername"),
            _p("password", TEXT, "test123", "Passwort"),
        ],
    },
    {
        "category": "Auth",
        "type": "signup",
        "description": "Neuen Account registrieren",
        "params": [
            _p("username", TEXT, "", "Benutzername"),
            _p("password", TEXT, "", "Passwort"),
            _p("email", TEXT, "", "E-Mail (optional)"),
        ],
    },

    # ── Empire / Economy ───────────────────────────────────────────
    {
        "category": "Empire",
        "type": "summary_request",
        "description": "Empire-Übersicht anfordern (Ressourcen, Bürger, Artefakte)",
        "params": [],
    },
    {
        "category": "Empire",
        "type": "citizen_upgrade",
        "description": "Bürger-Kapazität erhöhen",
        "params": [],
    },
    {
        "category": "Empire",
        "type": "change_citizen",
        "description": "Bürger auf Rollen verteilen",
        "params": [
            _p("citizens", JSON, '{"merchant": 2, "scientist": 1, "artist": 0}',
               "Verteilung {Rolle: Anzahl}"),
        ],
    },
    {
        "category": "Empire",
        "type": "increase_life",
        "description": "Max-Leben um 1 erhöhen (kostet Kultur)",
        "params": [],
    },

    # ── Items / Buildings / Research ───────────────────────────────
    {
        "category": "Items",
        "type": "item_request",
        "description": "Gebäude-/Forschungsstatus anfordern",
        "params": [],
    },
    {
        "category": "Items",
        "type": "new_item",
        "description": "Neues Gebäude/Wissen entwickeln",
        "params": [
            _p("iid", TEXT, "", "Item-ID (z.B. 'farm', 'archery')"),
        ],
    },

    # ── Structures (Türme) ─────────────────────────────────────────
    {
        "category": "Structures",
        "type": "new_structure",
        "description": "Neuen Turm auf der Karte platzieren",
        "params": [
            _p("iid", TEXT, "", "Turm-Typ ID"),
            _p("hex_q", INT, 0, "Hex-Koordinate Q"),
            _p("hex_r", INT, 0, "Hex-Koordinate R"),
        ],
    },
    {
        "category": "Structures",
        "type": "delete_structure",
        "description": "Turm entfernen (teilweise Gold-Erstattung)",
        "params": [
            _p("sid", INT, 0, "Structure-ID"),
        ],
    },
    {
        "category": "Structures",
        "type": "upgrade_structure",
        "description": "Turm upgraden",
        "params": [
            _p("sid", INT, 0, "Structure-ID"),
        ],
    },

    # ── Military / Armies ──────────────────────────────────────────
    {
        "category": "Military",
        "type": "military_request",
        "description": "Militärstatus anfordern (Armeen, Critter, Angriffe)",
        "params": [],
    },
    {
        "category": "Military",
        "type": "new_army",
        "description": "Neuen Armee-Slot erstellen",
        "params": [
            _p("name", TEXT, "", "Armee-Name"),
            _p("direction", TEXT, "north", "Angriffsrichtung (north/south/east/west)"),
        ],
    },
    {
        "category": "Military",
        "type": "change_army",
        "description": "Armee umbenennen oder Richtung ändern",
        "params": [
            _p("aid", INT, 0, "Armee-ID"),
            _p("name", TEXT, "", "Neuer Name"),
            _p("direction", TEXT, "", "Neue Richtung"),
        ],
    },
    {
        "category": "Military",
        "type": "new_wave",
        "description": "Neue Welle zu einer Armee hinzufügen",
        "params": [
            _p("aid", INT, 0, "Armee-ID"),
            _p("critter_iid", TEXT, "", "Critter-Typ ID"),
        ],
    },
    {
        "category": "Military",
        "type": "change_wave",
        "description": "Critter-Typ einer bestehenden Welle ändern",
        "params": [
            _p("aid", INT, 0, "Armee-ID"),
            _p("wave_number", INT, 0, "Wellen-Nummer"),
            _p("critter_iid", TEXT, "", "Neuer Critter-Typ"),
        ],
    },

    # ── Attacks ────────────────────────────────────────────────────
    {
        "category": "Attacks",
        "type": "new_attack_request",
        "description": "Angriff auf ein anderes Imperium starten",
        "params": [
            _p("target_uid", INT, 0, "Ziel-UID"),
            _p("army_aid", INT, 0, "Armee-ID"),
            _p("spy_options", JSON, "[]", "Spionage-Optionen (JSON-Array)"),
        ],
    },
    {
        "category": "Attacks",
        "type": "end_siege",
        "description": "Belagerung des eigenen Imperiums beenden",
        "params": [],
    },

    # ── Battle ─────────────────────────────────────────────────────
    {
        "category": "Battle",
        "type": "battle_register",
        "description": "Als Beobachter für ein Battle registrieren",
        "params": [
            _p("bid", INT, 0, "Battle-ID"),
        ],
    },
    {
        "category": "Battle",
        "type": "battle_unregister",
        "description": "Battle-Beobachtung beenden",
        "params": [
            _p("bid", INT, 0, "Battle-ID"),
        ],
    },
    {
        "category": "Battle",
        "type": "battle_next_wave_request",
        "description": "Nächste Welle im Battle auslösen",
        "params": [
            _p("bid", INT, 0, "Battle-ID"),
        ],
    },

    # ── Social / Messaging ─────────────────────────────────────────
    {
        "category": "Social",
        "type": "user_message",
        "description": "Nachricht an einen anderen Spieler senden",
        "params": [
            _p("target_uid", INT, 0, "Empfänger-UID"),
            _p("body", TEXT, "", "Nachrichtentext"),
        ],
    },
    {
        "category": "Social",
        "type": "timeline_request",
        "description": "Posteingang/Timeline abrufen",
        "params": [
            _p("target_uid", INT, 0, "Wessen Timeline"),
            _p("mark_read", JSON, "[]", "Message-IDs als gelesen markieren"),
            _p("mark_unread", JSON, "[]", "Message-IDs als ungelesen markieren"),
        ],
    },
    {
        "category": "Social",
        "type": "notification_request",
        "description": "Benachrichtigungen abrufen",
        "params": [],
    },

    # ── User Info / Ranking ────────────────────────────────────────
    {
        "category": "Info",
        "type": "userinfo_request",
        "description": "Spieler-Profilinformationen abfragen",
        "params": [
            _p("uids", JSON, "[100]", "Liste von UIDs (JSON-Array)"),
        ],
    },
    {
        "category": "Info",
        "type": "hall_of_fame_request",
        "description": "Globale Rangliste anfordern",
        "params": [],
    },

    # ── Preferences ────────────────────────────────────────────────
    {
        "category": "Preferences",
        "type": "preferences_request",
        "description": "Aktuelle Einstellungen anfordern",
        "params": [],
    },
    {
        "category": "Preferences",
        "type": "change_preferences",
        "description": "Profil-Statement und E-Mail ändern",
        "params": [
            _p("statement", TEXT, "", "Profil-Spruch"),
            _p("email", TEXT, "", "E-Mail-Adresse"),
        ],
    },
]


def get_categories() -> list[str]:
    """Return sorted unique category names."""
    seen: list[str] = []
    for sig in SIGNAL_CATALOG:
        if sig["category"] not in seen:
            seen.append(sig["category"])
    return seen


def get_signals_by_category() -> dict[str, list[dict]]:
    """Group signals by category, preserving order."""
    result: dict[str, list[dict]] = {}
    for sig in SIGNAL_CATALOG:
        cat = sig["category"]
        if cat not in result:
            result[cat] = []
        result[cat].append(sig)
    return result
