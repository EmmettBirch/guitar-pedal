# presets.py - Preset data layer
# Handles factory presets, user preset persistence, and applying/snapshotting
# effect chain state.

import os
import json


# Maps effect class names to the attribute names we serialize.
EFFECT_PARAMS = {
    'Overdrive': ['gain', 'tone', 'level'],
    'Fuzz':      ['gain', 'threshold', 'tone', 'level'],
    'Chorus':    ['rate', 'depth', 'mix'],
    'Delay':     ['delay_ms', 'feedback', 'mix'],
    'Reverb':    ['room_size', 'damping', 'mix'],
}

# Factory presets - hardcoded, cannot be deleted.
FACTORY_PRESETS = [
    {
        "name": "Rock",
        "factory": True,
        "effects": {
            "Overdrive": {"enabled": True,  "gain": 8.0, "tone": 0.6, "level": 0.7},
            "Fuzz":      {"enabled": False},
            "Chorus":    {"enabled": False},
            "Delay":     {"enabled": True,  "delay_ms": 320.0, "feedback": 0.25, "mix": 0.25},
            "Reverb":    {"enabled": True,  "room_size": 0.55, "damping": 0.4, "mix": 0.3},
        },
    },
    {
        "name": "Metal",
        "factory": True,
        "effects": {
            "Overdrive": {"enabled": True,  "gain": 16.0, "tone": 0.45, "level": 0.8},
            "Fuzz":      {"enabled": True,  "gain": 22.0, "threshold": 0.2, "tone": 0.4, "level": 0.7},
            "Chorus":    {"enabled": False},
            "Delay":     {"enabled": False},
            "Reverb":    {"enabled": True,  "room_size": 0.35, "damping": 0.7, "mix": 0.15},
        },
    },
    {
        "name": "Hip-Hop",
        "factory": True,
        "effects": {
            "Overdrive": {"enabled": False},
            "Fuzz":      {"enabled": False},
            "Chorus":    {"enabled": True,  "rate": 0.8, "depth": 0.008, "mix": 0.35},
            "Delay":     {"enabled": True,  "delay_ms": 450.0, "feedback": 0.45, "mix": 0.4},
            "Reverb":    {"enabled": True,  "room_size": 0.8, "damping": 0.3, "mix": 0.45},
        },
    },
]

# Path to user presets file (relative to the pi/ directory)
_USER_PRESETS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                  'data', 'user_presets.json')


def load_user_presets():
    """Load user presets from disk. Returns an empty list if none exist."""
    if not os.path.exists(_USER_PRESETS_PATH):
        return []
    try:
        with open(_USER_PRESETS_PATH, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_user_presets(presets):
    """Save user presets list to disk as JSON. Creates the data/ dir if needed."""
    os.makedirs(os.path.dirname(_USER_PRESETS_PATH), exist_ok=True)
    with open(_USER_PRESETS_PATH, 'w') as f:
        json.dump(presets, f, indent=2)


def get_all_presets():
    """Return factory presets followed by user presets."""
    return FACTORY_PRESETS + load_user_presets()


def snapshot_chain(effect_chain, name):
    """Capture the current effect chain state as a user preset dict."""
    effects = {}
    for fx in effect_chain.effects:
        class_name = type(fx).__name__
        params = EFFECT_PARAMS.get(class_name, [])
        entry = {"enabled": fx.enabled}
        for attr in params:
            entry[attr] = getattr(fx, attr)
        effects[class_name] = entry
    return {"name": name, "factory": False, "effects": effects}


def apply_preset(effect_chain, preset):
    """Apply a preset dict to the effect chain, setting enabled and params."""
    effects_data = preset.get("effects", {})
    for fx in effect_chain.effects:
        class_name = type(fx).__name__
        if class_name in effects_data:
            data = effects_data[class_name]
            fx.enabled = data.get("enabled", fx.enabled)
            for attr in EFFECT_PARAMS.get(class_name, []):
                if attr in data:
                    setattr(fx, attr, data[attr])
