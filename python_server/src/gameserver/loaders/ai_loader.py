"""AI template loader — parses ai_templates.yaml.

Loads AI army templates and difficulty tier definitions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_ai_templates(path: str | Path = "config/ai_templates.yaml") -> dict[str, Any]:
    """Load AI army templates and difficulty tiers.

    Args:
        path: Path to the AI templates YAML file.

    Returns:
        Dict with 'difficulty_tiers' and 'templates' keys.
    """
    path = Path(path)
    with path.open() as f:
        data = yaml.safe_load(f) or {}
    return data
