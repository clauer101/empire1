"""String loader — loads localized string dictionaries.

Simple key→value mapping for UI text, descriptions, etc.
"""

from __future__ import annotations

from pathlib import Path

import yaml


def load_strings(path: str | Path) -> dict[str, str]:
    """Load a string dictionary from a YAML file.

    Args:
        path: Path to the strings YAML file.

    Returns:
        Dict mapping string keys to localized values.
    """
    path = Path(path)
    with path.open() as f:
        data = yaml.safe_load(f) or {}
    return {str(k): str(v) for k, v in data.items()}
