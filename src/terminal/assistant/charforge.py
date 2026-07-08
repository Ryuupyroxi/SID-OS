#!/usr/bin/env python3
"""SID Character Forge — Generate animated character frames from photos or prompts.
Creates sprite sheets with mouth-shape animations for the assistant system.

Usage:
    python3 charforge.py from-photo <photo.jpg> <name>
    python3 charforge.py from-prompt "description" <name>
    python3 charforge.py list
    python3 charforge.py test <name>

Output: /etc/sid/characters/<name>/  (spritesheet.png + metadata.json)
"""

import os
import sys
import json
import shutil
import struct
import zlib
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

CHARS_DIR = "/etc/sid/characters"
SPRITESHEET_COLS = 6  # frames per state
SPRITESHEET_ROWS = 5  # one row per state (idle, thinking, listening, speaking, error)
FRAME_WIDTH = 64
FRAME_HEIGHT = 64


class CharForge:
    """Character frame generator. Uses imagegen when available,
    falls back to procedural test sprites."""

    @staticmethod
    def from_photo(photo_path: str, name: str) -> str:
        """Generate a character spritesheet from a photo.
        
        Pipeline:
        1. Detect if imagegen is available
        2. Center-crop the photo to a square
        3. Define mouth region (lower 20% of face area)
        4. Generate mouth-shape variant PNGs
        5. Arrange into spritesheet
        6. Output metadata
        
        Returns path to character directory.
        """
        outdir = os.path.join(CHARS_DIR, name)
        os.makedirs(outdir, exist_ok=True)

        if CharForge._has_imagegen():
            return CharForge._gen_via_imagegen(photo_path, name, outdir)
        else:
            return CharForge._gen_procedural(name, outdir)

    @staticmethod
    def from_prompt(prompt: str, name: str) -> str:
        """Generate a character from a text prompt."""
        outdir = os.path.join(CHARS_DIR, name)
        os.makedirs(outdir, exist_ok=True)

        if CharForge._has_imagegen():
            return CharForge._gen_via_prompt(prompt, name, outdir)
        else:
            return CharForge._gen_procedural(name, outdir)

    @staticmethod
    def _has_imagegen() -> bool:
        """Check if imagegen skill is available."""
        # Try importing the Codex imagegen skill
        try:
            import importlib
            # Check if imagegen is in the shared skills
            skill_path = os.path.expanduser("~/.codex/skills/imagegen")
            if os.path.isdir(skill_path):
                return True
            skill_path = "/root/.shared-skills/.system/imagegen"
            if os.path.isdir(skill_path):
                return True
        except Exception:
            pass
        return False

    @staticmethod
    def _gen_via_imagegen(photo_path: str, name: str, outdir: str) -> str:
        """Use imagegen skill to create character frames from a photo.
        
        This calls the imagegen system to:
        1. Create a clean front-facing portrait from the photo
        2. Generate 5 mouth-variant frames per state
        3. Compose into a grid sprite sheet
        """
        print(f"  🎨 Using imagegen to create character '{name}' from photo...")
        
        # The imagegen integration goes here.
        # For now, fall through to procedural.
        print(f"  ⚠️ imagegen detected but integration is a TODO — use procedural fallback")
        return CharForge._gen_procedural(name, outdir)

    @staticmethod
    def _gen_via_prompt(prompt: str, name: str, outdir: str) -> str:
        """Use imagegen to generate character from prompt."""
        print(f"  🎨 Generating character '{name}' from prompt via imagegen...")
        print(f"     Prompt: {prompt}")
        try:
        from imagegen import generate_image
        img = generate_image(f"front-facing character portrait from {photo_path}")
        img.save(os.path.join(outdir, "base.png"))
        print(f"  ✅ imagegen generated base portrait")
    except Exception as e:
        print(f"  ⚠️ imagegen failed: {e}")
        return CharForge._gen_procedural(name, outdir)
        return CharForge._gen_procedural(name, outdir)

    @staticmethod
    def _gen_procedural(name: str, outdir: str) -> str:
        """Generate a procedural test character with mouth-shape frames.
        
        Creates a simple colored face with animated mouth positions.
        Used as fallback when imagegen isn't available.
        """
        print(f"  🔧 Generating procedural test character '{name}'...")
        
        fw, fh = FRAME_WIDTH, FRAME_HEIGHT
        cols, rows = SPRITESHEET_COLS, SPRITESHEET_ROWS
        sw, sh = fw * cols, fh * rows  # spritesheet dimensions
        
        pixels = bytearray()
        state_colors = [
            (100, 180, 255),  # 0: idle - blue
            (255, 200, 80),   # 1: thinking - orange
            (80, 255, 140),   # 2: listening - green
            (255, 140, 80),   # 3: speaking - red-orange
            (255, 80, 80),    # 4: error - red
        ]
        
        for row in range(rows):
            r, g, b = state_colors[row] if row < len(state_colors) else (180, 180, 180)
            mouth_state = row  # 0=closed, 1=half, 2=open, 3=animating, 4=frown
            
            for fy in range(fh):
                for frame in range(cols):
                    for fx in range(fw):
                        # Face circle (centered)
                        cx, cy = fx - fw//2, fy - fh//2
                        dist = (cx*cx + cy*cy) ** 0.5
                        
                        if dist < fw//3:  # Face
                            pr, pg, pb = r, g, b
                            
                            # Eyes (two white dots)
                            if 6 < abs(cy) < 12 and abs(cx) > 8:
                                pr, pg, pb = 255, 255, 255
                            # Pupils
                            if 7 < abs(cy) < 11 and abs(cx) > 9:
                                pr, pg, pb = 0, 0, 0
                            
                            # Mouth — varies by state and frame
                            mouth_size = 0
                            if mouth_state == 0:  # idle - closed
                                mouth_size = 1
                            elif mouth_state == 1:  # thinking - tight
                                mouth_size = 2
                            elif mouth_state == 2:  # listening - open
                                mouth_size = 3 + frame % 2
                            elif mouth_state == 3:  # speaking - animates
                                mouth_size = [1, 2, 3, 2, 1, 0][frame % 6]
                            elif mouth_state == 4:  # error - frown
                                mouth_size = 0
                            
                            if cy > fh//6 and cy < fh//6 + mouth_size * 3 and abs(cx) < fw//6:
                                pr, pg, pb = 0, 0, 0  # mouth
                            
                            pixels.extend([pr, pg, pb, 255])
                        else:
                            pixels.extend([0, 0, 0, 0])  # transparent

        # Write PNG
        def png_chunk(t, d):
            c = t + d
            return struct.pack('>I', len(d)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)

        raw = b'\x08\x00\x00\x00\x00'
        raw_data = bytearray()
        for y in range(sh):
            raw_data.append(0)
            raw_data.extend(pixels[y * sw * 4 : (y + 1) * sw * 4])

        spritesheet_path = os.path.join(outdir, "spritesheet.png")
        with open(spritesheet_path, 'wb') as f:
            f.write(b'\x89PNG\r\n\x1a\n')
            f.write(png_chunk(b'IHDR', struct.pack('>IIBBBBB', sw, sh, 8, 6, 0, 0, 0)))
            f.write(png_chunk(b'IDAT', zlib.compress(bytes(raw_data))))
            f.write(png_chunk(b'IEND', b''))

        # Write metadata
        meta = {
            "type": "spritesheet",
            "name": name,
            "source": spritesheet_path,
            "grid": {"cols": cols, "rows": rows},
            "state_rows": {
                "idle": 0,
                "thinking": 1,
                "listening": 2,
                "speaking": 3,
                "error": 4,
            },
            "frames_per_state": {
                "idle": cols, "thinking": cols, "listening": cols,
                "speaking": cols, "error": cols,
            },
            "frame_ms": {
                "idle": 1000, "thinking": 500, "listening": 600,
                "speaking": 350, "error": 1500,
            },
            "mouth_frames": {
                "closed": [0],
                "half": [1, 3],
                "open": [2, 4],
            },
        }
        meta_path = os.path.join(outdir, "metadata.json")
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        # Create cache
        cache_dir = os.path.join(outdir, ".cache")
        os.makedirs(cache_dir, exist_ok=True)
        for state, row_idx in meta["state_rows"].items():
            n = meta["frames_per_state"].get(state, 1)
            for i in range(min(n, cols)):
                # Create individual frame PNG (simplified - just copy region)
                cache_path = os.path.join(cache_dir, f"{state}_{i:02d}.png")
                if not os.path.isfile(cache_path):
                    # For now, reference the spritesheet. Full slicing needs PIL.
                    with open(cache_path + ".ref", "w") as ref:
                        ref.write(f"{spritesheet_path},{i},{row_idx}")

        size = os.path.getsize(spritesheet_path)
        print(f"  ✅ Character '{name}' created: {spritesheet_path} ({sw}x{sh}, {size} bytes)")
        print(f"  📁 {outdir}/")
        print(f"     ├── spritesheet.png")
        print(f"     ├── metadata.json")
        print(f"     └── .cache/")
        
        return outdir

    @staticmethod
    def list_characters() -> list:
        """List all installed characters (both built-in ASCII and custom spritesheets)."""
        chars = set()
        # Built-in ASCII
        try:
            from .character import list_characters as list_builtin
            chars.update(list_builtin())
        except ImportError:
            chars.update(["sid-bot", "neko", "droid"])
        
        # Custom sprites from filesystem
        if os.path.isdir(CHARS_DIR):
            for name in os.listdir(CHARS_DIR):
                meta_path = os.path.join(CHARS_DIR, name, "metadata.json")
                if os.path.isfile(meta_path):
                    chars.add(name)
        
        return sorted(chars)

    @staticmethod
    def test_character(name: str):
        """Print diagnostic info about a character."""
        print(f"\nCharacter: {name}")
        print("=" * 40)
        
        # Check built-in
        try:
            from .character import load_character
            c = load_character(name)
            print(f"  Type: {c.char_type}")
            print(f"  States: {c.states}")
            for s in c.states:
                print(f"  {s}: {c.frame_count(s)} frames @ {c.frame_ms(s)}ms")
            return
        except (ImportError, ValueError):
            pass
        
        # Check filesystem
        char_dir = os.path.join(CHARS_DIR, name)
        meta_path = os.path.join(char_dir, "metadata.json")
        sprite_path = os.path.join(char_dir, "spritesheet.png")
        
        if os.path.isfile(meta_path):
            with open(meta_path) as f:
                meta = json.load(f)
            print(f"  Type: spritesheet")
            print(f"  Source: {meta.get('source', '?')}")
            print(f"  Grid: {meta.get('grid', {})}")
            print(f"  States: {list(meta.get('state_rows', {}).keys())}")
            if os.path.isfile(sprite_path):
                print(f"  Size: {os.path.getsize(sprite_path)} bytes")
            else:
                print(f"  ⚠️ Spritesheet not found!")
        else:
            print(f"  ⚠️ Character '{name}' not found")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    cmd = sys.argv[1]
    
    if cmd == "from-photo" and len(sys.argv) >= 4:
        CharForge.from_photo(sys.argv[2], sys.argv[3])
    elif cmd == "from-prompt" and len(sys.argv) >= 4:
        CharForge.from_prompt(sys.argv[2], sys.argv[3])
    elif cmd == "list":
        chars = CharForge.list_characters()
        print("Available characters:")
        for c in chars:
            print(f"  • {c}")
    elif cmd == "test" and len(sys.argv) >= 3:
        CharForge.test_character(sys.argv[2])
    elif cmd == "generate-test":
        name = sys.argv[2] if len(sys.argv) >= 3 else "test-char"
        CharForge._gen_procedural(name, CHARS_DIR)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()

# imagegen_registered = True
