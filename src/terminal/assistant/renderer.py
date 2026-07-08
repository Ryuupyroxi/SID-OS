"""Render backends for the animated assistant.
ASCII — always works. Image — if terminal supports kitty/sixel. SDL2 — future."""

import os
import sys
import shutil
import base64
from typing import Optional
from .character import Character


def detect_best_renderer() -> str:
    """Auto-detect the best available renderer for this terminal."""
    # Check Kitty protocol
    if os.environ.get("KITTY_WINDOW_ID"):
        return "kitty"
    # Check iTerm2
    if os.environ.get("TERM_PROGRAM") == "iTerm.app":
        return "iterm2"
    # Check sixel (xterm, mlterm, etc.)
    term = os.environ.get("TERM", "")
    if "xterm" in term or "sixel" in term:
        # Test if sixel is supported by checking terminal response
        return "sixel"
    # Check if chafa is available for image→ASCII
    if shutil.which("chafa"):
        return "chafa"
    if shutil.which("catimg"):
        return "catimg"
    if shutil.which("img2txt"):
        return "img2txt"
    # Fallback: ASCII art
    return "ascii"


def get_renderer(renderer_name: Optional[str] = None):
    """Get the best available renderer instance."""
    name = renderer_name or detect_best_renderer()
    renderers = {
        "ascii": ASCIIRenderer,
        "kitty": KittyRenderer,
        "iterm2": Iterm2Renderer,
        "sixel": SixelRenderer,
        "chafa": ChafaRenderer,
        "catimg": CatimgRenderer,
    }
    cls = renderers.get(name, ASCIIRenderer)
    return cls()


# ── Abstract Base ─────────────────────────────────────────────

class BaseRenderer:
    """Base renderer — subclasses implement render_frame()."""

    name = "base"

    def render_frame(self, lines: list, y_offset: Optional[int] = None):
        """Render a single frame at current or specified position."""
        raise NotImplementedError

    def clear_frames(self, height: int):
        """Clear previously rendered frames from terminal."""
        raise NotImplementedError

    def render_char(self, char: Character, state: str, frame_idx: int = 0,
                    y_offset: Optional[int] = None) -> int:
        """Render one frame of a character. Returns height rendered."""
        frames = char.frames(state)
        if not frames:
            return 0
        idx = frame_idx % len(frames)
        frame = frames[idx]
        self.render_frame(frame, y_offset)
        return len(frame)

    def can_render_images(self) -> bool:
        """Whether this renderer supports image/PNG display."""
        return False

    def frame_interval(self, char: Character, state: str) -> float:
        """Seconds between frames for this state."""
        return char.frame_ms(state) / 1000.0


# ── ASCII Renderer (always works) ─────────────────────────────

class ASCIIRenderer(BaseRenderer):
    """Render ASCII art frames using ANSI escape codes."""

    name = "ascii"
    _last_height = 0
    _color = "90"  # Dark gray — can be themed

    def render_frame(self, lines: list, y_offset: Optional[int] = None):
        h = self._last_height
        if h > 0:
            sys.stdout.write(f"\033[{h}A")
        for i, line in enumerate(lines):
            if i > 0:
                sys.stdout.write("\n")
            sys.stdout.write(f"\033[{self._color}m{line}\033[0m")
        sys.stdout.flush()
        self._last_height = len(lines)

    def clear_frames(self, height: int):
        if height > 0:
            sys.stdout.write(f"\033[{height}A")
            for _ in range(height):
                sys.stdout.write("\033[2K\033[1B")
            sys.stdout.write(f"\033[{height}A")
            sys.stdout.flush()
        self._last_height = 0


# ── Kitty Terminal Image Renderer ─────────────────────────────
# Uses the Kitty graphics protocol to display PNG frames.
# https://sw.kovidgoyal.net/kitty/graphics-protocol/

class KittyRenderer(BaseRenderer):
    """Render PNG frame files using Kitty's terminal graphics protocol."""

    name = "kitty"

    def __init__(self):
        self._last_height = 4  # Kitty images render ~4 text-lines tall
        self._image_cache = {}

    def _send_kitty(self, path: str):
        """Send a PNG file to the terminal via Kitty protocol."""
        try:
            with open(path, "rb") as f:
                data = base64.b64encode(f.read()).decode()
            # Delete previous image, then display new one
            sys.stdout.write("\033_Ga=d,d=i\033\\")  # delete
            sys.stdout.write(f"\033_Ga=T,f=100,s={os.path.getsize(path)},m=1\033\\{data}\033_Gm=0\033\\")
            sys.stdout.flush()
        except Exception:
            pass  # Fall through silently

    def render_frame(self, lines: list, y_offset: Optional[int] = None):
        """lines[0] should be a file path to a PNG."""
        if lines and os.path.isfile(lines[0]):
            self._send_kitty(lines[0])

    def clear_frames(self, height: int):
        sys.stdout.write("\033_Ga=d,d=i\033\\")
        sys.stdout.flush()

    def can_render_images(self) -> bool:
        return True


# ── iTerm2 Image Renderer ─────────────────────────────────────

class Iterm2Renderer(BaseRenderer):
    """Render PNG frames using iTerm2's inline image protocol."""

    name = "iterm2"

    def __init__(self):
        self._last_height = 4

    def _send_iterm2(self, path: str):
        try:
            with open(path, "rb") as f:
                data = base64.b64encode(f.read()).decode()
            sys.stdout.write(f"\033]1337;File=inline=1;width=auto;height=auto:{data}\a")
            sys.stdout.flush()
        except Exception:
            pass

    def render_frame(self, lines: list, y_offset: Optional[int] = None):
        if lines and os.path.isfile(lines[0]):
            self._send_iterm2(lines[0])

    def clear_frames(self, height: int):
        pass

    def can_render_images(self) -> bool:
        return True


# ── Sixel Renderer ────────────────────────────────────────────

class SixelRenderer(BaseRenderer):
    """Render sixel-encoded images (xterm, mlterm)."""

    name = "sixel"

    def __init__(self):
        self._last_height = 4

    def can_render_images(self) -> bool:
        return True

    def render_frame(self, lines: list, y_offset: Optional[int] = None):
        # Sixel data would be passed directly as lines
        if lines:
            for line in lines:
                sys.stdout.write(line)
                sys.stdout.write("\n")
            sys.stdout.flush()

    def clear_frames(self, height: int):
        pass


# ── chafa / catimg / img2txt ASCII-conversion Renderers ──────

class ChafaRenderer(ASCIIRenderer):
    """Convert PNG to ASCII/block art using chafa, then render."""

    name = "chafa"
    _last_height = 0

    def render_frame(self, lines: list, y_offset: Optional[int] = None):
        if not lines or not os.path.isfile(lines[0]):
            return
        try:
            import subprocess
            result = subprocess.run(
                ["chafa", "--symbols", "block", "--size", "15x6", lines[0]],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                art_lines = result.stdout.rstrip().split("\n")
                super().render_frame(art_lines, y_offset)
        except Exception:
            pass


class CatimgRenderer(ASCIIRenderer):
    """Convert PNG to ASCII using catimg."""
    name = "catimg"

    def render_frame(self, lines: list, y_offset: Optional[int] = None):
        if not lines or not os.path.isfile(lines[0]):
            return
        try:
            import subprocess
            result = subprocess.run(
                ["catimg", "-w", "20", lines[0]],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                art_lines = result.stdout.rstrip().split("\n")
                super().render_frame(art_lines, y_offset)
        except Exception:
            pass
