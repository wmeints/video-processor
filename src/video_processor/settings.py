"""Settings loader for video-processor configuration."""

import json
from pathlib import Path


def load_settings() -> dict:
    """
    Load settings from ~/.config/video-processor/settings.json.

    Returns
    -------
    dict
        Settings dictionary containing api_key and api_url, or empty dict if file doesn't exist.
    """
    config_path = Path.home() / ".config" / "video-processor" / "settings.json"
    if not config_path.exists():
        return {}
    return json.loads(config_path.read_text())
