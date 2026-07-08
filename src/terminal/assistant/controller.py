"""Assistant controller — state machine + AI integration."""

from typing import Optional
from .character import Character, load_character, list_characters
from .renderer import get_renderer, BaseRenderer, detect_best_renderer

STATE_LABELS = {
    "idle": "∘", "thinking": "◎", "listening": "○",
    "speaking": "◉", "error": "⊗",
}


class AssistantController:
    """Orchestrates character + renderer + state.
    
    Usage:
        a = AssistantController("sid-bot")
        a.enabled = True
        a.state = "thinking"   # auto-renders
        a.tick()               # advance to next frame
        a.state = "idle"
        a.enabled = False
    """

    def __init__(self, character: str = "sid-bot", renderer: Optional[str] = None):
        self._character = load_character(character)
        self._renderer = get_renderer(renderer)
        self._state = "idle"
        self._frame_idx = 0
        self._enabled = False

    # ── Properties ────────────────────────────────────────────

    @property
    def character(self) -> Character:
        return self._character

    @character.setter
    def character(self, name: str):
        self._character = load_character(name)
        self._frame_idx = 0

    @property
    def renderer(self) -> BaseRenderer:
        return self._renderer

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, val: bool):
        self._enabled = val
        if not val:
            self._renderer.clear_frames(8)  # Clear display

    @property
    def state(self) -> str:
        return self._state

    @state.setter
    def state(self, new_state: str):
        if new_state != self._state:
            self._state = new_state
            self._frame_idx = 0
            if self._enabled:
                self._render()

    # ── Frame Control ─────────────────────────────────────────

    def tick(self):
        """Advance to next frame and re-render."""
        if self._enabled:
            self._frame_idx += 1
            self._render()

    def _render(self):
        self._renderer.render_char(
            self._character, self._state, self._frame_idx
        )

    # ── Info ──────────────────────────────────────────────────

    def indicator(self) -> str:
        """One-line state indicator."""
        label = STATE_LABELS.get(self._state, "?")
        return f"\033[90m{self._character.display_name} [{label}]\033[0m"

    def prompt_label(self) -> str:
        """Compact label for embedding in prompt."""
        label = STATE_LABELS.get(self._state, "?")
        return f"[{label}]"

    @staticmethod
    def list_chars() -> list:
        return list_characters()

    @staticmethod
    def list_renderers() -> list:
        return ["ascii", "kitty", "iterm2", "sixel", "chafa", "catimg"]

    @staticmethod
    def best_renderer() -> str:
        return detect_best_renderer()
