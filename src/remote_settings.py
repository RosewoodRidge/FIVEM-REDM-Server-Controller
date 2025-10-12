import os
import sys
import json
import logging
from config_manager import get_data_dir

# Use data directory for settings
SETTINGS_FILE = os.path.join(get_data_dir(), 'remote_config.json')

DEFAULT_SETTINGS = {
    "connection": {
        "server_ip": "127.0.0.1",
        "port": 40100,
        "auth_key": ""
    }
}

def load_settings():
    """Load settings from remote_config.json or return defaults."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
            # Merge with defaults to ensure all keys are present
            for category, values in DEFAULT_SETTINGS.items():
                if category not in settings:
                    settings[category] = values
                else:
                    for key, value in values.items():
                        if key not in settings[category]:
                            settings[category][key] = value
            return settings
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"Failed to load remote settings: {e}")
            return DEFAULT_SETTINGS
    return DEFAULT_SETTINGS

def save_settings(settings):
    """Save settings to remote_config.json."""
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
    except IOError as e:
        logging.error(f"Failed to save remote settings: {e}")

