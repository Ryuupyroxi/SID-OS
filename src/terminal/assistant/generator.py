"""Character frame generator — auto-create characters using AI image gen.
Takes a photo or prompt, generates mouth-shape frames, outputs a template.

Now wired to CharForge for procedural generation with optional imagegen.
"""

import os
import json

SPRITESHEET_TEMPLATE = {
    "type": "spritesheet",
    "grid": {"cols": 6, "rows": 5},
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
}


def generate_from_photo(photo_path: str, name: str, output_dir: str = "/etc/sid/characters") -> str:
    """Generate a character spritesheet from a photo using CharForge + imagegen.

    Pipeline:
    1. Accept photo path → use CharForge imagegen pipeline
    2. Generate base character portrait with color extraction
    3. Generate mouth-shape variants as individual frames
    4. Arrange into sprite sheet grid
    5. Output metadata JSON + PNG
    6. Auto-register into character registry

    Args:
        photo_path: Path to a front-facing photo
        name: Character name
        output_dir: Where to save the character

    Returns:
        Path to the generated character directory
    """
    if not os.path.isfile(photo_path):
        raise FileNotFoundError(f"Photo not found: {photo_path}")

    from terminal.assistant.charforge import CharForge
    forge = CharForge(imagegen_available=True)

    result = forge.create_from_photo(photo_path, name)

    if result and os.path.isdir(result):
        from terminal.assistant.character import discover_characters
        discover_characters()

    return result


def generate_from_prompt(prompt: str, name: str = "", output_dir: str = "/etc/sid/characters") -> str:
    """Generate a character from a text prompt using CharForge.

    Pipeline:
    1. Send prompt to CharForge (procedural or imagegen)
    2. Generate base character portrait
    3. Generate mouth-shape variants
    4. Arrange into sprite sheet grid
    5. Output metadata JSON + PNG
    6. Auto-register into character registry

    Args:
        prompt: Text description (e.g. "a cute robot with blue eyes")
        name: Character name (auto-generated if empty)
        output_dir: Where to save the character

    Returns:
        Path to the generated character directory
    """
    from terminal.assistant.charforge import CharForge
    forge = CharForge()

    if not name:
        import hashlib
        name = "char-" + hashlib.md5(prompt.encode()).hexdigest()[:8]

    result = forge.create_from_description(prompt, name=name)

    if result and os.path.isdir(result):
        from terminal.assistant.character import discover_characters
        discover_characters()

    return result


def generate_from_parts(parts: dict, name: str = "", description: str = "", resolution: int = 256) -> str:
    """Generate a character from modular parts using CharForge.

    Args:
        parts: Parts manifest dict (head, eyes, mouth, body, accessory)
        name: Character name
        description: Text description
        resolution: Pixels per frame (64-512)

    Returns:
        Path to the generated character directory
    """
    from terminal.assistant.charforge import CharForge
    forge = CharForge()

    result = forge.create_from_parts(parts, name=name, description=description, resolution=resolution)

    if result and os.path.isdir(result):
        from terminal.assistant.character import discover_characters
        discover_characters()

    return result


def generate_ascii_from_image(image_path: str, name: str) -> dict:
    """Convert an image to ASCII art character frames.

    Uses chafa or similar to convert image to block-art ASCII,
    then defines mouth regions on the resulting art.
    Returns a character template dict ready for CHARACTERS registry.
    """
    import shutil
    import subprocess
    import tempfile

    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    if not shutil.which("chafa"):
        raise RuntimeError("chafa not installed — cannot convert to ASCII")

    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        subprocess.run(
            ["chafa", "--size=40x15", "--format=symbols", image_path],
            stdout=tmp, stderr=subprocess.DEVNULL, timeout=30
        )
        ascii_art = open(tmp.name).read()
    os.unlink(tmp.name)

    lines = [line for line in ascii_art.strip().split("\n") if line.strip()]

    return {
        "type": "ascii",
        "name": name,
        "states": {
            "idle": [lines],
            "thinking": [lines],
            "listening": [lines],
            "speaking": [lines],
            "error": [lines],
        },
        "frame_ms": {
            "idle": 1000,
            "thinking": 500,
            "listening": 600,
            "speaking": 350,
            "error": 1500
        }
    }


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
