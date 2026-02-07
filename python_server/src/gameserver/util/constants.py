"""Game constants — timing, costs, thresholds.

All magic numbers from the Java Constants class, centralized here.
"""

# -- Timing --------------------------------------------------------------

STEP_LENGTH_MS: float = 1000.0
"""Main game loop tick interval in milliseconds."""

BATTLE_TICK_MS: float = 15.0
"""Battle simulation tick interval in milliseconds."""

BROADCAST_INTERVAL_MS: float = 250.0
"""Minimum interval between battle broadcast updates."""

MIN_KEEP_ALIVE_MS: float = 10_000.0
"""Minimum battle duration before finish check."""

INITIAL_WAVE_DELAY_MS: float = 25_000.0
"""Delay before the first wave is dispatched in a battle."""

SPLASH_FLIGHT_MS: float = 500.0
"""Flight time for splash sub-shots."""

# -- Travel & Siege ------------------------------------------------------

BASE_TRAVEL_OFFSET: float = 5400.0
"""Base travel time in seconds (~90 minutes)."""

# -- Economy -------------------------------------------------------------

CITIZEN_EFFECT: float = 0.03
"""Per-citizen modifier for resource generation."""

MIN_LOSE_KNOWLEDGE: float = 0.03
"""Floor for knowledge theft percentage on battle loss."""

# -- Army & Waves --------------------------------------------------------

WAVES_PER_LEVEL: float = 1.0
"""Number of waves per slot-scaling level."""

SLOT_ADDER_PER_AI_LEVEL: float = 2.0
"""Additional slots per AI army level."""

# -- UIDs ----------------------------------------------------------------

UID_GAME_SERVER: int = 0
UID_GAME_ENGINE: int = 1
UID_AI: int = 2
UID_MIN_PLAYER: int = 1000
