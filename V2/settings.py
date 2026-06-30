# settings.py
import json
import os

SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "theme":           "dark",
    "font_size":       10,
    "email_limit":     30,
    "auto_refresh":    True,
    "refresh_interval": 300,   # seconds
    "save_email":      True,
    "last_email":      "",
    "window_width":    1150,
    "window_height":   720,
    "language":        "en"
}


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                saved = json.load(f)
                # Merge with defaults (in case new settings were added)
                return {**DEFAULT_SETTINGS, **saved}
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False


def get(key):
    return load_settings().get(key, DEFAULT_SETTINGS.get(key))


def set(key, value):
    s = load_settings()
    s[key] = value
    save_settings(s)