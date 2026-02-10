"""Network message models.

Typed Pydantic models for all client ↔ server messages.
Each message type gets its own model with validation.
Replaces the generic HashMap<String,Object> payload from the Java version.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel


# -- Base ----------------------------------------------------------------

class GameMessage(BaseModel):
    """Base class for all game messages."""

    type: str
    sender: int = 0
    receiver: int = 0


# -- Auth ----------------------------------------------------------------

class AuthRequest(GameMessage):
    type: Literal["auth_request"] = "auth_request"
    username: str
    password: str


class AuthResponse(GameMessage):
    type: Literal["auth_response"] = "auth_response"
    success: bool
    uid: int = 0
    reason: str = ""


class SignupRequest(GameMessage):
    type: Literal["signup"] = "signup"
    username: str
    password: str
    email: str = ""
    empire_name: str = ""


class SignupResponse(GameMessage):
    type: Literal["signup_response"] = "signup_response"
    success: bool
    uid: int = 0
    reason: str = ""


# -- Empire queries ------------------------------------------------------

class SummaryRequest(GameMessage):
    type: Literal["summary_request"] = "summary_request"


class SummaryResponse(GameMessage):
    type: Literal["summary_response"] = "summary_response"
    resources: dict[str, float] = {}
    citizens: dict[str, int] = {}
    artefacts: list[str] = []
    effects: dict[str, float] = {}
    max_life: float = 0.0


class ItemRequest(GameMessage):
    type: Literal["item_request"] = "item_request"


class ItemResponse(GameMessage):
    type: Literal["item_response"] = "item_response"
    buildings: dict[str, Any] = {}
    knowledge: dict[str, Any] = {}


class BuildResponse(GameMessage):
    type: Literal["build_response"] = "build_response"
    success: bool = False
    iid: str = ""
    error: str = ""
    build_queue: str = ""  # Current building queue item (for immediate UI update)
    research_queue: str = ""  # Current research queue item (for immediate UI update)


class MilitaryRequest(GameMessage):
    type: Literal["military_request"] = "military_request"
    uid: int = 0  # Optional: query a different empire's armies


class MilitaryResponse(GameMessage):
    type: Literal["military_response"] = "military_response"
    armies: list[dict[str, Any]] = []
    available_critters: list[str] = []
    attacks_incoming: list[dict[str, Any]] = []
    attacks_outgoing: list[dict[str, Any]] = []


# -- Building / Research -------------------------------------------------

class NewItemRequest(GameMessage):
    type: Literal["new_item"] = "new_item"
    iid: str = ""


class NewStructureRequest(GameMessage):
    type: Literal["new_structure"] = "new_structure"
    iid: str = ""
    hex_q: int = 0
    hex_r: int = 0


class DeleteStructureRequest(GameMessage):
    type: Literal["delete_structure"] = "delete_structure"
    sid: int = 0


class UpgradeStructureRequest(GameMessage):
    type: Literal["upgrade_structure"] = "upgrade_structure"
    sid: int = 0


# -- Citizens ------------------------------------------------------------

class CitizenUpgradeRequest(GameMessage):
    type: Literal["citizen_upgrade"] = "citizen_upgrade"


class ChangeCitizenRequest(GameMessage):
    type: Literal["change_citizen"] = "change_citizen"
    citizens: dict[str, int] = {}  # {"merchant": 2, "scientist": 1, "artist": 0}


class IncreaseLifeRequest(GameMessage):
    type: Literal["increase_life"] = "increase_life"


class CitizenUpgradeResponse(GameMessage):
    type: Literal["citizen_upgrade_response"] = "citizen_upgrade_response"
    success: bool = False
    error: str = ""
    citizens: dict[str, int] = {}  # Updated citizen distribution


class ChangeCitizenResponse(GameMessage):
    type: Literal["change_citizen_response"] = "change_citizen_response"
    success: bool = False
    error: str = ""
    citizens: dict[str, int] = {}  # Updated citizen distribution


# -- Army ----------------------------------------------------------------

class NewArmyRequest(GameMessage):
    type: Literal["new_army"] = "new_army"
    name: str = ""


class ChangeArmyRequest(GameMessage):
    type: Literal["change_army"] = "change_army"
    aid: int = 0
    name: str = ""


class NewWaveRequest(GameMessage):
    type: Literal["new_wave"] = "new_wave"
    aid: int = 0


class ChangeWaveRequest(GameMessage):
    type: Literal["change_wave"] = "change_wave"
    aid: int = 0
    wave_number: int = 0
    critter_iid: str = ""
    slots: Optional[int] = None


class NewAttackRequest(GameMessage):
    type: Literal["new_attack_request"] = "new_attack_request"
    target_uid: int = 0
    army_aid: int = 0
    opponent_name: str = ""
    spy_options: list[str] = []


class EndSiegeRequest(GameMessage):
    type: Literal["end_siege"] = "end_siege"


# -- Battle --------------------------------------------------------------

class BattleRegister(GameMessage):
    type: Literal["battle_register"] = "battle_register"
    bid: int = 0


class BattleUnregister(GameMessage):
    type: Literal["battle_unregister"] = "battle_unregister"
    bid: int = 0


class BattleSetup(GameMessage):
    type: Literal["battle_setup"] = "battle_setup"
    bid: int = 0
    defender_uid: int = 0
    structures: list[dict[str, Any]] = []
    paths: dict[str, list[dict[str, int]]] = {}  # direction -> [{q,r}, ...]
    wave_preview: list[dict[str, Any]] = []


class BattleUpdate(GameMessage):
    type: Literal["battle_update"] = "battle_update"
    bid: int = 0
    time: float = 0.0
    new_critters: list[dict[str, Any]] = []
    new_shots: list[dict[str, Any]] = []
    dead_critter_ids: list[int] = []
    finished_critter_ids: list[int] = []


class BattleSummary(GameMessage):
    type: Literal["battle_summary"] = "battle_summary"
    bid: int = 0
    defender_won: bool = True
    attacker_gains: dict[int, dict[str, float]] = {}
    defender_losses: dict[str, float] = {}


class BattleNextWaveRequest(GameMessage):
    type: Literal["battle_next_wave_request"] = "battle_next_wave_request"
    bid: int = 0


class BattleNextWaveResponse(GameMessage):
    type: Literal["battle_next_wave_response"] = "battle_next_wave_response"
    bid: int = 0
    wave_preview: dict[int, dict[str, Any]] = {}


# -- Social / Messaging --------------------------------------------------

class WelcomeMessage(GameMessage):
    type: Literal["welcome"] = "welcome"
    temp_uid: int = 0


class QuickMessage(GameMessage):
    type: Literal["quick_message"] = "quick_message"
    text: str = ""


class NotificationMessage(GameMessage):
    type: Literal["notification"] = "notification"
    text: str = ""
    category: str = ""


class NotificationRequest(GameMessage):
    type: Literal["notification_request"] = "notification_request"


class UserMessage(GameMessage):
    type: Literal["user_message"] = "user_message"
    target_uid: int = 0
    body: str = ""


class TimelineRequest(GameMessage):
    type: Literal["timeline_request"] = "timeline_request"
    target_uid: int = 0
    mark_read: list[int] = []
    mark_unread: list[int] = []


class TimelineResponse(GameMessage):
    type: Literal["timeline_response"] = "timeline_response"
    messages: list[dict[str, Any]] = []


# -- User Info / Hall of Fame --------------------------------------------

class UserInfoRequest(GameMessage):
    type: Literal["userinfo_request"] = "userinfo_request"
    uids: list[int] = []


class UserInfoResponse(GameMessage):
    type: Literal["userinfo_response"] = "userinfo_response"
    users: list[dict[str, Any]] = []


class HallOfFameRequest(GameMessage):
    type: Literal["hall_of_fame_request"] = "hall_of_fame_request"


class HallOfFameResponse(GameMessage):
    type: Literal["hall_of_fame_response"] = "hall_of_fame_response"
    ranking: list[dict[str, Any]] = []
    winners: list[dict[str, Any]] = []
    prosperity: list[dict[str, Any]] = []
    defense_god: list[dict[str, Any]] = []
    treasure_hunter: list[dict[str, Any]] = []
    world_wonder: list[dict[str, Any]] = []


# -- Preferences ---------------------------------------------------------

class ChangePreferencesRequest(GameMessage):
    type: Literal["change_preferences"] = "change_preferences"
    statement: str = ""
    email: str = ""


class PreferencesRequest(GameMessage):
    type: Literal["preferences_request"] = "preferences_request"


class PreferencesResponse(GameMessage):
    type: Literal["preferences_response"] = "preferences_response"
    email: str = ""


# -- Map Editor ----------------------------------------------------------

class MapSaveRequest(GameMessage):
    type: Literal["map_save_request"] = "map_save_request"
    tiles: dict[str, Any] = {}


class MapLoadRequest(GameMessage):
    type: Literal["map_load_request"] = "map_load_request"


class MapSaveResponse(GameMessage):
    type: Literal["map_save_response"] = "map_save_response"
    success: bool = False
    error: str = ""


class MapLoadResponse(GameMessage):
    type: Literal["map_load_response"] = "map_load_response"
    tiles: dict[str, Any] = {}
    error: str = ""


# -- Battle ----------------------------------------------------------------

class BattleRequest(GameMessage):
    type: Literal["battle_request"] = "battle_request"


class BattleResponse(GameMessage):
    type: Literal["battle_response"] = "battle_response"
    success: bool = False
    error: str = ""


# -- Message type registry -----------------------------------------------

MESSAGE_TYPES: dict[str, type[GameMessage]] = {
    # Auth
    "auth_request": AuthRequest,
    "auth_response": AuthResponse,
    "signup": SignupRequest,
    "welcome": WelcomeMessage,
    # Empire
    "summary_request": SummaryRequest,
    "summary_response": SummaryResponse,
    "item_request": ItemRequest,
    "item_response": ItemResponse,
    "build_response": BuildResponse,
    "new_item": NewItemRequest,
    # Citizens
    "citizen_upgrade": CitizenUpgradeRequest,
    "citizen_upgrade_response": CitizenUpgradeResponse,
    "change_citizen": ChangeCitizenRequest,
    "change_citizen_response": ChangeCitizenResponse,
    "increase_life": IncreaseLifeRequest,
    # Structures
    "new_structure": NewStructureRequest,
    "delete_structure": DeleteStructureRequest,
    "upgrade_structure": UpgradeStructureRequest,
    # Military
    "military_request": MilitaryRequest,
    "military_response": MilitaryResponse,
    "new_army": NewArmyRequest,
    "change_army": ChangeArmyRequest,
    "new_wave": NewWaveRequest,
    "change_wave": ChangeWaveRequest,
    "new_attack_request": NewAttackRequest,
    "end_siege": EndSiegeRequest,
    # Battle
    "battle_register": BattleRegister,
    "battle_unregister": BattleUnregister,
    "battle_setup": BattleSetup,
    "battle_update": BattleUpdate,
    "battle_summary": BattleSummary,
    "battle_next_wave_request": BattleNextWaveRequest,
    "battle_next_wave_response": BattleNextWaveResponse,
    # Social / Messaging
    "quick_message": QuickMessage,
    "notification": NotificationMessage,
    "notification_request": NotificationRequest,
    "user_message": UserMessage,
    "timeline_request": TimelineRequest,
    "timeline_response": TimelineResponse,
    # User Info / Hall of Fame
    "userinfo_request": UserInfoRequest,
    "userinfo_response": UserInfoResponse,
    "hall_of_fame_request": HallOfFameRequest,
    "hall_of_fame_response": HallOfFameResponse,
    # Preferences
    "change_preferences": ChangePreferencesRequest,
    "preferences_request": PreferencesRequest,
    "preferences_response": PreferencesResponse,
    # Map Editor
    "map_save_request": MapSaveRequest,
    "map_save_response": MapSaveResponse,
    "map_load_request": MapLoadRequest,
    "map_load_response": MapLoadResponse,
    # Battle
    "battle_request": BattleRequest,
    "battle_response": BattleResponse,
}


def parse_message(data: dict[str, Any]) -> GameMessage:
    """Parse a raw dict into the appropriate typed message model."""
    msg_type = data.get("type", "")
    model_cls = MESSAGE_TYPES.get(msg_type, GameMessage)
    return model_cls.model_validate(data)
