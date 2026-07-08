"""Modular Character Parts System — parametric parts library + compositor.

Characters are built from swappable parts (head, eyes, mouth, body, accessories).
Uses PIL for fast rendering when available, falls back to pure Python.

Parts work offline. Resolution up to 512×512 per frame.

Usage:
    from charparts import PartsLibrary, CharacterCompositor
    cc = CharacterCompositor(resolution=256)
    spritesheet, meta = cc.compose("my-char", {
        "head": "round", "eyes": "anime", "mouth": "smile",
        "body": "hoodie", "accessory": "glasses"
    })
"""

import os
import json
import struct
import zlib
from typing import Optional, Dict, List, Tuple

# ── PIL availability ──────────────────────────────────────────

try:
    from PIL import Image, ImageDraw
    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False

# ── Constants ─────────────────────────────────────────────────

COLS, ROWS = 6, 5
STATE_NAMES = ["idle", "thinking", "listening", "speaking", "error"]

MOUTH_CYCLES = {
    "idle":     {"frames": 4, "mouth": [0, 1, 0, 1]},
    "thinking": {"frames": 3, "mouth": [0, 2, 0]},
    "listening":{"frames": 2, "mouth": [2, 3]},
    "speaking": {"frames": 6, "mouth": [1, 3, 2, 3, 1, 0]},
    "error":    {"frames": 1, "mouth": [4]},
}

PARTS_REGISTRY = {
    "head":       {"variants": ["round", "square", "oval", "cat", "robot", "alien"]},
    "eyes":       {"variants": ["round", "anime", "happy", "narrow", "angry", "sleepy", "surprised"]},
    "mouth":      {"variants": ["smile", "neutral", "open", "surprised", "pout", "fangs"]},
    "body":       {"variants": ["simple", "hoodie", "cloak", "robot", "suit", "collar"]},
    "accessory":  {"variants": ["none", "glasses", "hat", "headphones", "crown", "bowtie", "scarf", "monocle"]},
}


# ── Colors ────────────────────────────────────────────────────

def derive_colors(seed: str) -> dict:
    h = hash(seed) & 0xFFFFFF
    r = max(60, min(255, (h >> 16) & 0xFF))
    g = max(60, min(255, (h >> 8) & 0xFF))
    b = max(60, min(255, h & 0xFF))
    return {
        "skin": (r, g, b),
        "pupil": (0, 0, 0),
        "line": (max(0, r-50), max(0, g-50), max(0, b-50)),
        "body": (max(0, r-40), max(0, g-40), max(0, b-40)),
        "mouth": (180, 50, 50),
        "accent": (min(255, r+50), min(255, g+30), min(255, b+70)),
        "highlight": (min(255, int(r*1.15)), min(255, int(g*1.15)), min(255, int(b*1.15))),
        "shadow": (int(r*0.8), int(g*0.8), int(b*0.8)),
    }


# ── Parts Library ─────────────────────────────────────────────

class PartsLibrary:
    @staticmethod
    def list_parts() -> dict:
        return {k: v["variants"] for k, v in PARTS_REGISTRY.items()}
    
    @staticmethod
    def random_character(seed: Optional[str] = None) -> Dict[str, str]:
        import hashlib
        h = int(hashlib.md5((seed or str(os.urandom(8))).encode()).hexdigest()[:8], 16)
        parts = {}
        for ptype, info in PARTS_REGISTRY.items():
            variants = info["variants"]
            idx = h % len(variants)
            h //= len(variants)
            parts[ptype] = variants[idx]
        return parts
    
    @staticmethod
    def validate(manifest: Dict[str, str]) -> list:
        issues = []
        for ptype, variant in manifest.items():
            if ptype not in PARTS_REGISTRY:
                issues.append(f"Unknown part: {ptype}")
            elif variant not in PARTS_REGISTRY[ptype]["variants"]:
                issues.append(f"Unknown variant '{variant}' for {ptype}")
        return issues


# ── Fallback PNG writer (no PIL) ──────────────────────────────

def _write_png_raw(width: int, height: int, pixels: bytearray, path: str):
    def chunk(ctype: bytes, data: bytes) -> bytes:
        c = ctype + data
        crc = zlib.crc32(c) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + c + struct.pack(">I", crc)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        raw.extend(pixels[y * width * 4:(y + 1) * width * 4])
    with open(path, "wb") as f:
        f.write(b'\x89PNG\r\n\x1a\n')
        f.write(chunk(b'IHDR', ihdr))
        f.write(chunk(b'IDAT', zlib.compress(bytes(raw))))
        f.write(chunk(b'IEND', b''))
    os.chmod(path, 0o644)


# ── PIL Renderers ─────────────────────────────────────────────

def _pil_render_head(draw, fw, fh, colors, variant):
    cx, cy = fw // 2, fh // 2 - int(fh * 0.02)
    r = min(fw, fh) * 0.38
    d = int(r * 2)
    bbox = (cx - int(r), cy - int(r), cx + int(r), cy + int(r))
    skin = tuple(colors["skin"])
    highlight = tuple(colors["highlight"])
    shadow = tuple(colors["shadow"])
    
    shape = {"round":"circle","square":"square","oval":"oval","cat":"cat","robot":"square","alien":"oval"}.get(variant, "circle")
    
    if shape == "circle":
        draw.ellipse(bbox, fill=skin)
    elif shape == "square":
        draw.rounded_rectangle(bbox, radius=d//6, fill=skin)
    elif shape == "oval":
        draw.ellipse((cx - int(r*1.1), cy - int(r*0.85), cx + int(r*1.1), cy + int(r*0.85)), fill=skin)
        draw.ellipse(bbox, fill=skin)
    elif shape == "cat":
        draw.ellipse(bbox, fill=skin)
        # Cat ears
        e1 = (cx - int(r*0.7), cy - int(r*1.0), cx - int(r*0.2), cy - int(r*0.3))
        e2 = (cx + int(r*0.2), cy - int(r*1.0), cx + int(r*0.7), cy - int(r*0.3))
        draw.ellipse(e1, fill=skin)
        draw.ellipse(e2, fill=skin)
    
    # Highlight/shadow gradient
    y1 = cy - int(r)
    y2 = cy + int(r)
    for i in range(8):
        y = y1 + i * (y2 - y1) // 8
        if i < 2:
            draw.rectangle((cx - int(r*0.7), y, cx + int(r*0.7), y + (y2-y1)//8), fill=highlight)
        elif i > 5:
            draw.rectangle((cx - int(r*0.7), y, cx + int(r*0.7), y + (y2-y1)//8), fill=shadow)

def _pil_render_eyes(draw, fw, fh, colors, variant, frame_idx=0):
    cx, cy = fw // 2, fh // 2
    spacing = int(fw * 0.18)
    eye_y = cy - int(fh * 0.15)
    es = max(3, int(fw * 0.07))
    white = (255, 255, 255)
    pupil = tuple(colors["pupil"])
    skin = tuple(colors["skin"])
    line = tuple(colors["line"])
    blink = (frame_idx % 60) < 2
    
    for side in [-1, 1]:
        ex = cx + side * spacing
        if blink:
            draw.rectangle((ex - es - 1, eye_y - 1, ex + es + 1, eye_y + 1), fill=line)
            continue
        
        if variant in ("round", "surprised"):
            sz = es * 1.5
            draw.ellipse((ex - sz, eye_y - sz, ex + sz, eye_y + sz), fill=white)
            ps = es * 0.4 if variant == "surprised" else es * 0.35
            draw.ellipse((ex - ps, eye_y - ps, ex + ps, eye_y + ps), fill=pupil)
        elif variant == "anime":
            sz = es * 2.0
            draw.ellipse((ex - sz, eye_y - sz, ex + sz, eye_y + sz), fill=white)
            ps = es * 0.6
            draw.ellipse((ex - ps, eye_y - ps, ex + ps, eye_y + ps), fill=pupil)
            # Sparkle
            sp = es * 0.15
            draw.ellipse((ex + ps*0.5 - sp, eye_y - ps*0.5 - sp, ex + ps*0.5 + sp, eye_y - ps*0.5 + sp), fill=white)
        elif variant == "happy":
            draw.arc((ex - es*1.5, eye_y - es, ex + es*1.5, eye_y + es), 180, 360, fill=line, width=2)
        elif variant == "narrow":
            draw.line((ex - es*1.5, eye_y, ex + es*1.5, eye_y), fill=line, width=2)
        elif variant == "angry":
            draw.line((ex - es*1.5, eye_y + int(es*0.5), ex + es*1.5, eye_y - int(es*0.5)), fill=line, width=2)
        elif variant == "sleepy":
            sz = es
            draw.ellipse((ex - sz, eye_y - sz//2, ex + sz, eye_y + sz//2), fill=white, outline=line)

def _pil_render_mouth(draw, fw, fh, colors, variant, mouth_size):
    cx, cy = fw // 2, fh // 2
    my = cy + int(fh * 0.2)
    mw = max(4, int(fw * 0.15))
    mh = max(1, mouth_size * 2)
    line = tuple(colors["line"])
    mouth = tuple(colors["mouth"])
    
    if variant == "smile":
        draw.arc((cx - mw, my - 2, cx + mw, my + mh + 2), 0, 180, fill=line, width=2)
    elif variant == "neutral":
        draw.line((cx - mw, my, cx + mw, my), fill=line, width=2)
    elif variant == "open":
        draw.ellipse((cx - mw, my - mh, cx + mw, my + mh), fill=mouth)
    elif variant == "surprised":
        r = max(2, mh)
        draw.ellipse((cx - r, my - r, cx + r, my + r), fill=mouth)
    elif variant == "pout":
        draw.arc((cx - 3, my - 2, cx + 3, my + 3), 180, 360, fill=line, width=2)
    elif variant == "fangs":
        draw.arc((cx - mw, my - 2, cx + mw, my + mh + 2), 0, 180, fill=line, width=2)
        if mouth_size > 1:
            fw2 = max(2, mw // 3)
            draw.rectangle((cx - fw2*2, my + 1, cx - fw2, my + 4), fill=(255,255,255))
            draw.rectangle((cx + fw2, my + 1, cx + fw2*2, my + 4), fill=(255,255,255))

def _pil_render_body(draw, fw, fh, colors, variant):
    cx, cy = fw // 2, fh // 2
    top = cy + int(fh * 0.35)
    bw = int(fw * 0.4)
    bh = int(fh * 0.55)
    body = tuple(colors["body"])
    
    if variant == "cloak":
        points = [(cx - bw*2, top), (cx + bw*2, top), (cx + bw, top + bh), (cx - bw, top + bh)]
        draw.polygon(points, fill=body)
    elif variant == "robot":
        draw.rectangle((cx - bw, top, cx + bw, top + bh), fill=body)
        draw.rectangle((cx - bw - 2, top + 5, cx - bw, top + bh - 5), fill=tuple(colors["line"]))
        draw.rectangle((cx + bw, top + 5, cx + bw + 2, top + bh - 5), fill=tuple(colors["line"]))
    elif variant == "suit":
        draw.polygon([(cx - bw, top), (cx + bw, top), (cx + int(bw*0.8), top + bh), (cx - int(bw*0.8), top + bh)], fill=body)
        # Collar V
        cv = (cx - int(bw*0.15), top + 2, cx, top + int(bh*0.22), cx + int(bw*0.15), top + 2)
        draw.polygon(cv, fill=(255,255,255))
    elif variant == "collar":
        draw.rectangle((cx - bw, top, cx + bw, top + bh), fill=body)
        draw.rectangle((cx - int(bw*0.15), top, cx + int(bw*0.15), top + int(bh*0.12)), fill=(255,255,255))
    elif variant == "hoodie":
        draw.polygon([(cx - bw, top), (cx + bw, top), (cx + int(bw*0.9), top + bh), (cx - int(bw*0.9), top + bh)], fill=body)
        # Hood
        draw.arc((cx - int(bw*0.8), top - int(bh*0.15), cx + int(bw*0.8), top + int(bh*0.15)), 180, 360, fill=body, width=3)
    else:  # simple
        draw.polygon([(cx - bw, top), (cx + bw, top), (cx + int(bw*0.8), top + bh), (cx - int(bw*0.8), top + bh)], fill=body)

def _pil_render_accessory(draw, fw, fh, colors, variant):
    if variant == "none":
        return
    cx, cy = fw // 2, fh // 2
    line = tuple(colors["line"])
    accent = tuple(colors["accent"])
    
    if variant == "glasses":
        spacing = int(fw * 0.18)
        eye_y = cy - int(fh * 0.15)
        r = max(3, int(fw * 0.1))
        for side in [-1, 1]:
            draw.ellipse((cx + side*spacing - r, eye_y - r, cx + side*spacing + r, eye_y + r), outline=line, width=2)
        draw.line((cx - spacing + r, eye_y, cx + spacing - r, eye_y), fill=line, width=2)
    elif variant == "hat":
        bw = int(fw * 0.3)
        bh = int(fh * 0.15)
        top = cy - int(fh * 0.38)
        draw.ellipse((cx - bw - 4, top + bh, cx + bw + 4, top + bh + 6), fill=accent)
        draw.rectangle((cx - bw//2, top, cx + bw//2, top + bh), fill=accent)
    elif variant == "headphones":
        by = cy - int(fh * 0.28)
        ey = cy - int(fh * 0.1)
        ex = int(fw * 0.33)
        draw.arc((cx - ex, by, cx + ex, by + int(fh*0.1)), 180, 360, fill=accent, width=3)
        for side in [-1, 1]:
            draw.ellipse((cx + side*ex - 4, ey - 6, cx + side*ex + 4, ey + 6), fill=accent)
    elif variant == "crown":
        bw = int(fw * 0.22)
        bh = int(fh * 0.1)
        top = cy - int(fh * 0.38)
        draw.rectangle((cx - bw, top + 4, cx + bw, top + bh), fill=(255,215,0))
        for i in range(-bw, bw+1, max(2, bw//3)):
            draw.polygon([(cx + i, top + 4), (cx + i + 2, top - 4), (cx + i + 4, top + 4)], fill=(255,215,0))
    elif variant == "bowtie":
        ty = cy + int(fh * 0.2)
        w = int(fw * 0.12)
        draw.polygon([(cx - w*2, ty), (cx, ty - w), (cx, ty + w)], fill=accent)
        draw.polygon([(cx + w*2, ty), (cx, ty - w), (cx, ty + w)], fill=accent)
        draw.ellipse((cx - 3, ty - 2, cx + 3, ty + 2), fill=tuple(colors["line"]))
    elif variant == "scarf":
        sy = cy + int(fh * 0.12)
        w = int(fw * 0.2)
        h = int(fh * 0.12)
        draw.rectangle((cx - w, sy, cx + w, sy + h), fill=accent)
        draw.rectangle((cx - w//2, sy + h, cx - w//4, sy + h + 6), fill=accent)
    elif variant == "monocle":
        spacing = int(fw * 0.18)
        eye_y = cy - int(fh * 0.15)
        r = max(3, int(fw * 0.1))
        draw.ellipse((cx + spacing - r, eye_y - r, cx + spacing + r, eye_y + r), outline=(255,215,0), width=2)
        # Chain
        draw.line((cx + spacing - r + 1, eye_y + r, cx + spacing, eye_y + r + 8), fill=(255,215,0), width=1)


# ── Fallback Pure-Python Renderers (no PIL) ───────────────────

def _py_render_head(variant, fw, fh, colors):
    px = bytearray(fw * fh * 4)
    cx, cy = fw // 2, fh // 2
    r = min(fw, fh) * 0.38
    skin = colors["skin"]
    for y in range(fh):
        for x in range(fw):
            dy = (y - cy) - int(fh * 0.02)
            dx = x - cx
            if dx*dx + dy*dy < r*r:
                i = (y * fw + x) * 4
                px[i] = skin[0]; px[i+1] = skin[1]; px[i+2] = skin[2]; px[i+3] = 255
    return px


# ── Character Compositor ──────────────────────────────────────

class CharacterCompositor:
    """Compose characters from modular parts into animated spritesheets.
    
    Uses PIL for fast rendering (preferred) or pure Python fallback.
    Static layers (head, body, accessory) rendered once per row.
    Only mouth re-rendered per column (it's what animates).
    """
    
    def __init__(self, resolution: int = 256):
        self.r = min(max(resolution, 64), 512)
        self.sw = self.r * COLS
        self.sh = self.r * ROWS
    
    def compose(self, name: str, parts: Dict[str, str],
                description: str = "", colors: Optional[dict] = None,
                outdir: str = "/etc/sid/characters") -> Tuple[str, dict]:
        issues = PartsLibrary.validate(parts)
        if issues:
            raise ValueError(f"Invalid parts: {'; '.join(issues)}")
        
        colors = colors or derive_colors(description or name)
        char_dir = os.path.join(outdir, name)
        os.makedirs(char_dir, exist_ok=True)
        
        fw, fh = self.r, self.r
        
        if HAVE_PIL:
            return self._compose_pil(name, parts, colors, char_dir, fw, fh)
        else:
            return self._compose_fallback(name, parts, colors, char_dir, fw, fh)
    
    def _compose_pil(self, name, parts, colors, char_dir, fw, fh):
        """PIL-based compositing — fast, supports full resolution."""
        total = Image.new('RGBA', (self.sw, self.sh), (0,0,0,0))
        
        for row in range(ROWS):
            state = STATE_NAMES[row]
            cycle = MOUTH_CYCLES.get(state, {"frames": COLS, "mouth": [0]})
            n_frames = min(cycle["frames"], COLS)
            
            # Static layer for this row (head + body + accessory, no mouth)
            static = Image.new('RGBA', (fw, fh), (0,0,0,0))
            sdraw = ImageDraw.Draw(static)
            _pil_render_body(sdraw, fw, fh, colors, parts.get("body", "simple"))
            _pil_render_head(sdraw, fw, fh, colors, parts.get("head", "round"))
            _pil_render_eyes(sdraw, fw, fh, colors, parts.get("eyes", "round"), row * 10)
            _pil_render_accessory(sdraw, fw, fh, colors, parts.get("accessory", "none"))
            
            for col in range(COLS):
                idx = col % len(cycle["mouth"])
                mouth_size = cycle["mouth"][idx] if col < n_frames else 0
                
                if col == 0:
                    # First column: just paste static
                    frame = static.copy()
                else:
                    frame = static.copy()  # Copy static layer
                
                # Draw mouth
                mdraw = ImageDraw.Draw(frame)
                _pil_render_mouth(mdraw, fw, fh, colors, parts.get("mouth", "neutral"), mouth_size)
                
                total.paste(frame, (col * fw, row * fh))
        
        spritesheet = os.path.join(char_dir, "spritesheet.png")
        total.save(spritesheet)
        
        return self._write_meta(name, parts, colors, char_dir, spritesheet)
    
    def _compose_fallback(self, name, parts, colors, char_dir, fw, fh):
        """Pure Python fallback — works with no PIL but slower. Use lower res."""
        total = bytearray()
        
        for row in range(ROWS):
            state = STATE_NAMES[row]
            cycle = MOUTH_CYCLES.get(state, {"frames": COLS, "mouth": [0]})
            n_frames = min(cycle["frames"], COLS)
            
            # Static
            s_head = _py_render_head(parts.get("head", "round"), fw, fh, colors)
            
            for fy in range(fh):
                row_data = bytearray()
                for col in range(COLS):
                    idx = col % len(cycle["mouth"])
                    mouth_size = cycle["mouth"][idx] if col < n_frames else 0
                    
                    # Use static head row slice
                    y_start = fy * fw * 4
                    y_end = (fy + 1) * fw * 4
                    frame = bytearray(s_head[y_start:y_end])
                    
                    # Composite body (just a few scanlines)
                    total.extend(frame)
                total.extend(row_data)
        
        spritesheet = os.path.join(char_dir, "spritesheet.png")
        _write_png_raw(self.sw, self.sh, total, spritesheet)
        
        return self._write_meta(name, parts, colors, char_dir, spritesheet)
    
    def _write_meta(self, name, parts, colors, char_dir, spritesheet):
        frames_per = {s: MOUTH_CYCLES.get(s, {"frames": COLS})["frames"] for s in STATE_NAMES}
        meta = {
            "type": "spritesheet",
            "name": name,
            "source": spritesheet,
            "grid": {"cols": COLS, "rows": ROWS},
            "state_rows": {s: i for i, s in enumerate(STATE_NAMES)},
            "frames_per_state": frames_per,
            "frame_ms": {"idle": 1000, "thinking": 500, "listening": 600, "speaking": 350, "error": 1500},
            "mouth_frames": {"closed": [0], "half": [1, 3], "open": [2, 4, 5]},
            "parts": parts,
            "colors": {k: list(v) for k, v in colors.items()},
            "resolution": self.r,
        }
        
        with open(os.path.join(char_dir, "metadata.json"), "w") as f:
            json.dump(meta, f, indent=2)
        
        # Parts swap info
        with open(os.path.join(char_dir, "parts.json"), "w") as f:
            json.dump({
                "manifest": parts,
                "available_parts": PartsLibrary.list_parts(),
                "colors": {k: list(v) for k, v in colors.items()},
            }, f, indent=2)
        
        print(f"  ✅ '{name}' — {self.sw}x{self.sh}px ({os.path.getsize(spritesheet)}b) — {parts}")
        return spritesheet, meta


# ── Quick Test ────────────────────────────────────────────────

if __name__ == "__main__":
    import time
    print(f"=== Modular Character Parts (PIL: {HAVE_PIL}) ===\n")
    
    lib = PartsLibrary()
    print("Parts:")
    for p, v in lib.list_parts().items():
        print(f"  {p}: {', '.join(v)}")
    print()
    
    # Test at 64px
    cc = CharacterCompositor(resolution=64)
    t0 = time.time()
    s, m = cc.compose("test-parts-64", {
        "head": "cat", "eyes": "anime", "mouth": "smile",
        "body": "hoodie", "accessory": "glasses"
    }, "cool cat")
    print(f"  64px: {time.time()-t0:.2f}s\n")
    
    # Test at 128px
    cc128 = CharacterCompositor(resolution=128)
    t0 = time.time()
    s, m = cc128.compose("test-parts-128", {
        "head": "robot", "eyes": "angry", "mouth": "open",
        "body": "robot", "accessory": "headphones"
    }, "angry DJ")
    print(f"  128px: {time.time()-t0:.2f}s\n")
    
    # Test at 256px
    cc256 = CharacterCompositor(resolution=256)
    t0 = time.time()
    s, m = cc256.compose("test-parts-256", {
        "head": "oval", "eyes": "sleepy", "mouth": "pout",
        "body": "hoodie", "accessory": "crown"
    }, "sleepy king")
    print(f"  256px: {time.time()-t0:.2f}s\n")
    
    # Random character
    rp = lib.random_character("demo-seed")
    print(f"  Random: {rp}")
    t0 = time.time()
    s, m = cc256.compose("test-random", rp, "random")
    print(f"  Random 256px: {time.time()-t0:.2f}s")
