"""Character data model + template registry.
Supports ASCII art templates and sprite-sheet based characters."""

import os
import json
from typing import Optional

# ── Frame Types ───────────────────────────────────────────────
# ASCII frame: list[str]  (lines of text)
# Image frame: str        (path to PNG/GIF frame file)
# Spritesheet: dict       (path + grid coords)

REQUIRED_STATES = {"idle", "thinking", "listening", "speaking", "error"}

# ── ASCII Character Templates ─────────────────────────────────
CHARACTERS = {
    "sid-bot": {
        "type": "ascii",
        "name": "SID Bot",
        "states": {
            "idle": [
                [" ╭───╮ ", " │◉ ◉│ ", " │ ◡ │ ", " ╰───╯ "],
                [" ╭───╮ ", " │◉ ◉│ ", " │ ◠ │ ", " ╰───╯ "],
                [" ╭───╮ ", " │◉ ◉│ ", " │ ◡ │ ", " ╰───╯ "],
                [" ╭───╮ ", " │◉ ◉│ ", " │ ◡ │ ", " ╰─┬─╯ "],
            ],
            "thinking": [
                [" ╭───╮ ", " │● ●│ ", " │ ⟋ \\│ ", " ╰───╯ "],
                [" ╭───╮ ", " │● ●│ ", " │ \\ ⟋│ ", " ╰───╯ "],
            ],
            "listening": [
                [" ╭───╮ ", " │◉ ◉│ ", " │ ◡ │ ", " ╰─┬─╯ ", "  /│\\  "],
                [" ╭───╮ ", " │◉ ◉│ ", " │ ◇ │ ", " ╰─┬─╯ ", "  /│\\  "],
            ],
            "speaking": [
                [" ╭───╮ ", " │◉ ◉│ ", " │   │ ", " ╰─┬─╯ ", " ╱ │ ╲ "],
                [" ╭───╮ ", " │◉ ◉│ ", " │ ◡ │ ", " ╰─┬─╯ ", " ╱ │ ╲ "],
                [" ╭───╮ ", " │◉ ◉│ ", " │ ◇ │ ", " ╰─┬─╯ ", " ╱ │ ╲ "],
                [" ╭───╮ ", " │◉ ◉│ ", " │ ◠ │ ", " ╰─┬─╯ ", " ╱ │ ╲ "],
                [" ╭───╮ ", " │◉ ◉│ ", " │ ◇ │ ", " ╰─┬─╯ ", " ╱ │ ╲ "],
                [" ╭───╮ ", " │◉ ◉│ ", " │ ◡ │ ", " ╰─┬─╯ ", " ╱ │ ╲ "],
            ],
            "error": [
                [" ╭───╮ ", " │× ×│ ", " │ ─ │ ", " ╰───╯ "],
            ],
        },
        "frame_ms": {"idle": 1000, "thinking": 500, "listening": 600,
                     "speaking": 350, "error": 1500},
    },
    "neko": {
        "type": "ascii",
        "name": "Neko",
        "states": {
            "idle":    [[" ╱￣￣╲ ", " |◉ ◉| ", " | ◡ | ", " ╲___╱ "]],
            "thinking":[[" ╱￣￣╲ ", " |● ●| ", " | ⟋⟍| ", " ╲___╱ "]],
            "listening":[[" ╱^ ^╲ ", " |◉ ◉| ", " | ⊙ | ", " ╲___╱ "]],
            "speaking":[
                [" ╱￣￣╲ ", " |◉ ◉| ", " | ◇ | ", " ╲___╱ "],
                [" ╱￣￣╲ ", " |◉ ◉| ", " |   | ", " ╲___╱ "],
                [" ╱￣￣╲ ", " |◉ ◉| ", " | ◠ | ", " ╲___╱ "],
            ],
            "error":   [[" ╱￣￣╲ ", " |× ×| ", " | ─ | ", " ╲___╱ "]],
        },
        "frame_ms": {"idle": 1200, "thinking": 600, "listening": 700,
                     "speaking": 400, "error": 1500},
    },
    "droid": {
        "type": "ascii",
        "name": "Droid",
        "states": {
            "idle":    [["  ┌────────┐  ","  │  ◉  ◉  │  ","  │   ◡   │  ","  └───┬───┘  "]],
            "thinking":[["  ┌────────┐  ","  │  ●  ●  │  ","  │  ⟋⟍  │  ","  └───┬───┘  "]],
            "listening":[["  ┌────────┐  ","  │  ◉  ◉  │  ","  │   ◇   │  ","  └───┬───┘  ","     ─┼─     "]],
            "speaking":[
                ["  ┌────────┐  ","  │  ◉  ◉  │  ","  │   ◡   │  ","  └───┬───┘  ","    ╱ │ ╲   "],
                ["  ┌────────┐  ","  │  ◉  ◉  │  ","  │  ───  │  ","  └───┬───┘  ","    ╱ │ ╲   "],
                ["  ┌────────┐  ","  │  ◉  ◉  │  ","  │  ╲─╱  │  ","  └───┬───┘  ","    ╱ │ ╲   "],
            ],
            "error":   [["  ┌────────┐  ","  │  ×  ×  │  ","  │   ─   │  ","  └───┬───┘  "]],
        },
        "frame_ms": {"idle": 1000, "thinking": 600, "listening": 700,
                     "speaking": 400, "error": 1500},
    },
}

# ── Sprite Sheet Character Template ───────────────────────────
# Future: image-based characters use this format instead.
# A sprite sheet is a single PNG with all frames in a grid.
# Each row = one state, each column = one animation frame.
# Mouth shapes defined as per-frame metadata.
#
# "my-photo-char": {
#     "type": "spritesheet",
#     "name": "My Character",
#     "source": "/etc/sid/characters/my-char.png",
#     "grid": {"cols": 6, "rows": 5},
#     "state_rows": {
#         "idle": 0, "thinking": 1, "listening": 2,
#         "speaking": 3, "error": 4
#     },
#     "frames_per_state": {
#         "idle": 4, "thinking": 3, "listening": 2,
#         "speaking": 6, "error": 1
#     },
#     "frame_ms": {
#         "idle": 1000, "thinking": 500, "listening": 600,
#         "speaking": 350, "error": 1500
#     },
#     "mouth_frames": {
#         # For lip-sync: which frames map to which mouth shapes
#         "closed": [0, 2],
#         "half": [1, 3],
#         "open": [4, 5],
#     }
# }


def load_spritesheet(name: str, data: dict) -> dict:
    """Load a spritesheet character: slice PNG into frame cache.
    Returns a dict of {state: [[frame_path]]} for the renderer.
    """
    source = data.get("source", "")
    if not source or not os.path.isfile(source):
        raise FileNotFoundError(f"Spritesheet not found: {source}")
    
    state_rows = data.get("state_rows", {})
    frames_per = data.get("frames_per_state", {})
    
    cache_dir = os.path.join(os.path.dirname(source), ".cache", name)
    
    # If cache is empty, slice the spritesheet now
    has_cache = os.path.isdir(cache_dir) and any(
        f.endswith(".png") for f in os.listdir(cache_dir) if not f.endswith(".ref")
    )
    if not has_cache:
        cache_spritesheet_frames(name, data)
    
    # Load cached frames
    result = {}
    for state in state_rows:
        result[state] = []
        n = frames_per.get(state, 1)
        for i in range(n):
            fp = os.path.join(cache_dir, f"{state}_{i:02d}.png")
            if os.path.isfile(fp):
                result[state].append([fp])
            else:
                result[state].append([source])
    
    return result


def cache_spritesheet_frames(name: str, data: dict):
    """Pre-slice spritesheet into individual frame PNGs.
    Requires PIL (Pillow). Falls back gracefully if not available.
    """
    try:
        from PIL import Image
    except ImportError:
        return False  # No PIL — renderer will slice at display time
    
    source = data.get("source", "")
    if not source or not os.path.isfile(source):
        return False
    
    grid = data.get("grid", {"cols": 6, "rows": 5})
    state_rows = data.get("state_rows", {})
    frames_per = data.get("frames_per_state", {})
    cols, rows = grid["cols"], grid["rows"]
    
    img = Image.open(source)
    fw = img.width // cols
    fh = img.height // rows
    
    cache_dir = os.path.join(os.path.dirname(source), ".cache", name)
    os.makedirs(cache_dir, exist_ok=True)
    
    for state, row_idx in state_rows.items():
        n = frames_per.get(state, 1)
        for i in range(n):
            x, y = i * fw, row_idx * fh
            frame = img.crop((x, y, x + fw, y + fh))
            fp = os.path.join(cache_dir, f"{state}_{i:02d}.png")
            frame.save(fp)
    
    return True

# ── Template for adding new characters ───────────────────────
# Copy this and fill in your frames:
# TEMPLATE = {
#     "type": "ascii",
#     "name": "My Character",
#     "states": {
#         "idle": [["line1","line2","line3"]],
#         "thinking": [...],
#         "listening": [...],
#         "speaking": [...],
#         "error": [...],
#     },
#     "frame_ms": {"idle": 1000, "thinking": 500, "listening": 600,
#                  "speaking": 350, "error": 1500},
# }


class Character:
    """Loaded character with validation and frame access."""

    def __init__(self, name: str, data: dict):
        self.name = name
        self.data = data
        self.char_type = data.get("type", "ascii")
        self.display_name = data.get("name", name)
        self._validate()

    def _validate(self):
        states = self.data.get("states", {})
        missing = REQUIRED_STATES - set(states.keys())
        if missing:
            raise ValueError(f"Character '{self.name}' missing states: {missing}")

    def frames(self, state: str) -> list:
        """Get frames for a state (fall back to idle)."""
        states = self.data.get("states", {})
        frames = states.get(state, states.get("idle", [[]]))
        return frames

    def frame_count(self, state: str) -> int:
        return len(self.frames(state))

    def frame_ms(self, state: str) -> int:
        """Get frame timing for a state."""
        ms = self.data.get("frame_ms", {})
        return ms.get(state, ms.get("idle", 1000))

    @property
    def states(self) -> list:
        return list(self.data.get("states", {}).keys())



def discover_characters() -> dict:
    """Scan /etc/sid/characters/ for spritesheet characters and register them."""
    chars_dir = "/etc/sid/characters"
    discovered = {}
    if not os.path.isdir(chars_dir):
        return discovered
    
    for name in sorted(os.listdir(chars_dir)):
        meta_path = os.path.join(chars_dir, name, "metadata.json")
        if os.path.isfile(meta_path):
            try:
                with open(meta_path) as f:
                    meta = json.load(f)
                if meta.get("type") == "spritesheet":
                    # Fix source path if relative
                    src = meta.get("source", "")
                    if src and not os.path.isabs(src):
                        meta["source"] = os.path.join(chars_dir, name, src)
                    discovered[name] = meta
                    print(f"  📥 Discovered character: {name}")
            except (json.JSONDecodeError, KeyError):
                pass
    
    # Also check for .json files directly in chars_dir
    for fname in sorted(os.listdir(chars_dir)):
        if fname.endswith(".json"):
            fpath = os.path.join(chars_dir, fname)
            try:
                with open(fpath) as f:
                    data = json.load(f)
                char_name = data.get("name", os.path.splitext(fname)[0])
                if char_name not in CHARACTERS and char_name not in discovered:
                    discovered[char_name] = data
            except (json.JSONDecodeError, KeyError):
                pass
    
    for name, data in discovered.items():
        CHARACTERS[name] = data
    
    return discovered

def load_character(name: str) -> Character:
    """Load a character by name from the registry.
    Auto-discovers spritesheet characters from /etc/sid/characters/."""
    if name not in CHARACTERS:
        discover_characters()  # Scan filesystem
        if name not in CHARACTERS:
            name = "sid-bot"
    return Character(name, CHARACTERS[name])


def list_characters() -> list[str]:
    """Get all available character names (built-in + discovered from filesystem)."""
    discover_characters()
    return list(CHARACTERS.keys())


def register_character(name: str, data: dict):
    """Register a new character at runtime."""
    CHARACTERS[name] = data
