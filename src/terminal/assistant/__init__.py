"""SID Animated Assistant — Modular character system.
Renderers: ASCII (always), Kitty/Sixel images (if available), SDL2 (future).
Characters: ASCII art templates or sprite-sheet images with mouth-shape frames."""

from .character import Character, CHARACTERS, list_characters
from .controller import AssistantController
from .renderer import get_renderer, ASCIIRenderer, BaseRenderer

__all__ = [
    "Character", "CHARACTERS", "list_characters",
    "AssistantController",
    "get_renderer", "ASCIIRenderer", "BaseRenderer",
]
