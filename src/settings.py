import os
import json
import logging
from pathlib import Path

# Settings file location
SETTINGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.json")

# Default settings
DEFAULT_SETTINGS = {
    "remote_control": {
        "enabled": False,
        "port": 40100,
        "auth_key": None
    },
    "ui": {
        "last_tab": 0
    }
}

def ensure_settings_dir():
    """Ensure the settings directory exists"""
    Path(SETTINGS_DIR).mkdir(parents=True, exist_ok=True)

def load_settings():
    """Load settings from file or create with defaults if not exists"""
    ensure_settings_dir()
    
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
                
            # Ensure all required settings exist by merging with defaults
            merged_settings = DEFAULT_SETTINGS.copy()
            for category, values in settings.items():
                if category in merged_settings:
                    merged_settings[category].update(values)
                else:
                    merged_settings[category] = values
                    
            return merged_settings
        except Exception as e:
            logging.error(f"Failed to load settings: {e}")
            return DEFAULT_SETTINGS.copy()
    else:
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    """Save settings to file"""
    ensure_settings_dir()
    
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
        return True
    except Exception as e:
        logging.error(f"Failed to save settings: {e}")
        return False

def update_setting(category, key, value):
    """Update a specific setting"""
    settings = load_settings()
    
    if category not in settings:
        settings[category] = {}
    
    settings[category][key] = value
    return save_settings(settings)

def get_setting(category, key, default=None):
    """Get a specific setting"""
    settings = load_settings()
    return settings.get(category, {}).get(key, default)

# Initialize settings object
settings = load_settings()
