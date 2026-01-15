"""Settings loader for video-processor configuration."""

import json
from pathlib import Path


def load_settings() -> dict:
    """
    Load settings from ~/.config/video-processor/settings.json.

    Returns
    -------
    dict
        Settings dictionary containing api_key and api_url.

    Raises
    ------
    FileNotFoundError
        If the settings file does not exist.
    """
    config_path = Path.home() / ".config" / "video-processor" / "settings.json"
    if not config_path.exists():
        raise FileNotFoundError(
            f"Settings file not found: {config_path}\n"
            'Create it with: {"api_key": "your-key", "api_url": "https://api.anthropic.com"}'
        )
    return json.loads(config_path.read_text())
