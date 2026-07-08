"""Character frame generator — auto-create characters using AI image gen.
Takes a photo or prompt, generates mouth-shape frames, outputs a template."""

SPRITESHEET_TEMPLATE = '''{
    "type": "spritesheet",
    "name": "%(name)s",
    "source": "%(source)s",
    "grid": {"cols": %(cols)d, "rows": %(rows)d},
    "state_rows": {
        "idle": 0,
        "thinking": 1,
        "listening": 2,
        "speaking": 3,
        "error": 4
    },
    "frames_per_state": {
        "idle": 4,
        "thinking": 3,
        "listening": 2,
        "speaking": 6,
        "error": 1
    },
    "frame_ms": {
        "idle": 1000,
        "thinking": 500,
        "listening": 600,
        "speaking": 350,
        "error": 1500
    },
    "mouth_frames": {
        "closed": [0, 2],
        "half": [1, 3],
        "open": [4, 5]
    }
}'''


def generate_from_photo(photo_path: str, name: str, output_dir: str = "/etc/sid/characters"):
    """Generate a character spritesheet from a photo using AI image generation.
    
    Pipeline:
    1. Take the photo as reference
    2. Call imagegen to create a clean front-facing character portrait
    3. Define mouth regions and generate frame variants
    4. Compose into a sprite sheet
    5. Output metadata JSON + PNG
    
    Usage:
        generate_from_photo("photo.jpg", "my-friend")
        # Output: /etc/sid/characters/my-friend/
        #   spritesheet.png
        #   metadata.json
    
    This is a pipeline definition. Actual implementation depends on
    the imagegen skill being available in the runtime environment.
    """
    raise NotImplementedError(
        "Photo-to-character generation requires the imagegen skill.\n"
        "Run inside Codex with `imagegen` installed:\n\n"
        "  from src.terminal.assistant.generator import generate_from_photo\n"
        "  generate_from_photo('photo.png', 'my-char')\n\n"
        "This will produce a spritesheet + metadata you can load."
    )


def generate_from_prompt(prompt: str, name: str, output_dir: str = "/etc/sid/characters"):
    """Generate a character from a text prompt using AI image generation.
    
    Pipeline:
    1. Send prompt to imagegen (e.g. "cute pixel-art robot assistant")
    2. Generate base character portrait  
    3. Generate mouth-shape variants as individual frames
    4. Arrange into sprite sheet grid
    5. Output metadata JSON + PNG
    
    Usage:
        generate_from_prompt("retro-futuristic AI assistant", "my-ai")
    """
    raise NotImplementedError(
        "Prompt-to-character generation requires the imagegen skill.\n"
        "Run inside Codex with `imagegen` installed."
    )


def generate_ascii_from_image(image_path: str, name: str) -> dict:
    """Convert an image to ASCII art character frames.
    
    Uses chafa or similar to convert image to block-art ASCII,
    then defines mouth regions on the resulting art.
    Returns a character template dict ready for CHARACTERS registry.
    """
    raise NotImplementedError("ASCII conversion from image: coming soon")


def validate_spritesheet(path: str, metadata: dict) -> list:
    """Validate a spritesheet PNG matches its metadata.
    Returns list of issues found (empty = valid)."""
    issues = []
    required_keys = ["type", "name", "source", "grid", "state_rows",
                     "frames_per_state", "frame_ms", "mouth_frames"]
    for k in required_keys:
        if k not in metadata:
            issues.append(f"Missing key: {k}")
    if metadata.get("type") != "spritesheet":
        issues.append("Type must be 'spritesheet'")
    if not os.path.isfile(path):
        issues.append(f"File not found: {path}")
    return issues

# ── CODER NOTES (for Alpine Linux session) ────────────────────
# 
# What needs implementing:
#
# 1. generate_from_photo():
#    - Accept photo path → use imagegen to create front-facing portrait
#    - Define mouth region coordinates on the portrait
#    - Generate 6 mouth-shape variants: closed, half-open, open (×2 for animation)
#    - Arrange into 5-row × 6-column spritesheet PNG
#    - Output metadata JSON matching spritesheet template above
#    - Register into CHARACTERS dict dynamically
#
# 2. generate_from_prompt():
#    - Same pipeline but start from text prompt instead of photo
#    - Prompt should describe character style (e.g. "pixel art", "semi-realistic")
#
# 3. Terminal detection:
#    - Make `detect_best_renderer()` probe terminal capabilities at runtime
#    - Kitty protocol: check KITTY_WINDOW_ID env var
#    - Sixel: try writing escape sequence, read response
#    - Fall back gracefully through chain: kitty → sixel → chafa → ascii
#
# 4. Sprite sheet loader:
#    - Write load_spritesheet(path, metadata) that slices PNG by grid coords
#    - Cache individual frame images for fast render switching
#    - Feed frames into KittyRenderer/SixelRenderer
#
# 5. Testing:
#    - Create a test character PNG (simple colored squares as frames)
#    - Verify frame cycling in all render backends
#    - Test terminal detection on different terminal types
#
# For imagegen integration reference, see:
#   /root/.shared-skills/.system/imagegen/SKILL.md
#   /root/.shared-skills/generate2dsprite/SKILL.md
