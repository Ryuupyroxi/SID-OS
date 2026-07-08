"""Character data model + template registry.
Supports ASCII art templates and sprite-sheet based characters."""

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


def load_character(name: str) -> Character:
    """Load a character by name from the registry."""
    if name not in CHARACTERS:
        name = "sid-bot"
    return Character(name, CHARACTERS[name])


def list_characters() -> list[str]:
    """Get all available character names."""
    return list(CHARACTERS.keys())


def register_character(name: str, data: dict):
    """Register a new character at runtime."""
    CHARACTERS[name] = data
