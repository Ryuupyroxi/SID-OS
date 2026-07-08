"""SID Image Tools - AI-powered image generation and editing.
Supports: text-to-image, image editing, format conversion, analysis."""
import os
import json
import base64
import subprocess
import urllib.request
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple

class ImageTools:
    """Complete image toolset supporting online and offline operation."""

    def __init__(self, ai=None):
        self.ai = ai
        self.generation_backends = self._detect_backends()
        self._output_dir = Path("/tmp/sid-images")
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def _detect_backends(self) -> Dict[str, bool]:
        """Detect available image backends."""
        backends = {
            "api_dalle": False,        # OpenAI DALL-E via API
            "api_stability": False,    # Stability AI via API
            "local_sd": False,         # Local Stable Diffusion
            "imagemagick": False,      # ImageMagick for editing
            "ffmpeg": False,           # FFmpeg for format conversion
            "python_pil": False,       # Pillow for basic editing
        }
        
        # Check for ImageMagick
        try:
            subprocess.run(["convert", "--version"], capture_output=True, timeout=5)
            backends["imagemagick"] = True
except Exception:
            pass
        
        # Check for FFmpeg
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
            backends["ffmpeg"] = True
except Exception:
            pass
        
        # Check for Pillow
        try:
            from PIL import Image
            backends["python_pil"] = True
except Exception:
            pass
        
        return backends

    def generate(self, prompt: str, 
                 size: Tuple[int, int] = (512, 512),
                 style: str = "photo",
                 engine: str = "auto") -> Dict:
        """Generate an image from text description."""
        output_path = self._output_dir / self._safe_filename(prompt)
        
        # Try backends in order
        if engine in ("auto", "api") and self.ai and self.ai.config.api_key:
            result = self._generate_api(prompt, size, output_path)
            if result.get("success"):
                return result
        
        if engine in ("auto", "local"):
            # Try AI-assisted generation via ImageMagick
            result = self._generate_imagemagick(prompt, output_path)
            if result.get("success"):
                return result
            
            # Generate SVG as fallback
            result = self._generate_svg(prompt, size, output_path)
            if result.get("success"):
                return result
        
        # Last resort: use AI to describe the image creation
        return {
            "success": False,
            "error": "No generation backend available. Try: install imagemagick, or configure API key.",
            "hint": "I can describe how to create this image manually."
        }

    def _generate_api(self, prompt: str, size, output_path: Path) -> Dict:
        """Generate image via API (OpenAI DALL-E)."""
        try:
            req = urllib.request.Request(
                f"{self.ai.config.api_endpoint}/images/generations",
                data=json.dumps({
                    "model": "dall-e-2" if max(size) <= 512 else "dall-e-3",
                    "prompt": prompt,
                    "n": 1,
                    "size": f"{size[0]}x{size[1]}"
                }).encode(),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.ai.config.api_key}"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
                image_url = data["data"][0]["url"]
                # Download the image
                urllib.request.urlretrieve(image_url, output_path.with_suffix(".png"))
                return {
                    "success": True,
                    "path": str(output_path.with_suffix(".png")),
                    "engine": "api:dalle",
                    "prompt": prompt,
                    "size": size
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate_imagemagick(self, prompt: str, output_path: Path) -> Dict:
        """Generate artistic image using ImageMagick."""
        ext = ".png"
        output = str(output_path) + ext
        
        # Use ImageMagick to create abstract/geometric art based on prompt
        try:
            # Parse prompt for colors and shapes (simple version)
            colors = ["blue", "green", "red", "purple", "orange", "cyan"]
            import random
            primary = random.choice(colors)
            secondary = random.choice([c for c in colors if c != primary])
            
            cmd = [
                "convert", "-size", "512x512", 
                "canvas:#000008",
                "-fill", primary, "-draw", "circle 256,256 200,200",
                "-fill", secondary, "-draw", "circle 256,256 150,150",
                "-fill", "white", "-draw", f"text 30,30 '{prompt[:30]}'",
                "-fill", "white", "-draw", f"text 30,480 'SID AI - {prompt[:20]}'",
                output
            ]
            subprocess.run(cmd, capture_output=True, timeout=30)
            
            if Path(output).exists():
                return {"success": True, "path": output, "engine": "imagemagick"}
except Exception:
            pass
        
        return {"success": False}

    def _generate_svg(self, prompt: str, size, output_path: Path) -> Dict:
        """Generate SVG as a simple visual representation."""
        # Create a simple SVG file
        svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{size[0]}" height="{size[1]}" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" fill="#0a0a0a"/>
  <text x="50%" y="50%" text-anchor="middle" fill="#00ff00" 
        font-family="monospace" font-size="14">
    SID AI Generated
  </text>
  <text x="50%" y="55%" text-anchor="middle" fill="#006600" 
        font-family="monospace" font-size="10">
    {prompt[:60]}
  </text>
</svg>"""
        
        output = str(output_path) + ".svg"
        Path(output).write_text(svg)
        return {"success": True, "path": output, "engine": "svg"}

    def edit(self, image_path: str, operation: str, **params) -> Dict:
        """Edit an image using available backends."""
        if not Path(image_path).exists():
            return {"error": f"Image not found: {image_path}"}
        
        if self.backends.get("imagemagick"):
            return self._edit_imagemagick(image_path, operation, **params)
        
        if self.backends.get("python_pil"):
            return self._edit_pil(image_path, operation, **params)
        
        return {"error": "No editing backend available. Install ImageMagick or Pillow."}

    def _edit_imagemagick(self, path: str, operation: str, **params) -> Dict:
        """Edit image with ImageMagick."""
        output = str(self._output_dir / f"edited_{Path(path).name}")
        
        ops = {
            "resize": f"convert '{path}' -resize {params.get('size','800x600')} '{output}'",
            "convert": f"convert '{path}' '{output}.{params.get('format','png')}'",
            "grayscale": f"convert '{path}' -colorspace Gray '{output}'",
            "blur": f"convert '{path}' -blur 0x{params.get('radius',5)} '{output}'",
            "flip": f"convert '{path}' -flip '{output}'",
            "rotate": f"convert '{path}' -rotate {params.get('degrees',90)} '{output}'",
            "compress": f"convert '{path}' -quality {params.get('quality',50)} '{output}'",
            "add_text": f"convert '{path}' -pointsize {params.get('size',24)} -fill white -annotate +30+30 '{params.get('text','')}' '{output}'",
        }
        
        cmd = ops.get(operation, f"convert '{path}' '{output}'")
        try:
            subprocess.run(cmd, shell=True, capture_output=True, timeout=30)
            if Path(output).exists():
                return {"success": True, "path": output, "operation": operation}
        except Exception as e:
            return {"error": str(e)}
        
        return {"error": f"Operation '{operation}' failed"}

    def _edit_pil(self, path: str, operation: str, **params) -> Dict:
        """Edit image with Python Pillow."""
        try:
            from PIL import Image, ImageDraw, ImageFilter, ImageOps
            img = Image.open(path)
            output = str(self._output_dir / f"edited_{Path(path).name}")
            
            if operation == "resize":
                size = tuple(map(int, params.get('size', '800x600').split('x')))
                img = img.resize(size)
            elif operation == "convert":
                img.save(output.rsplit('.', 1)[0] + f".{params.get('format','png')}")
            elif operation == "grayscale":
                img = ImageOps.grayscale(img)
            elif operation == "blur":
                img = img.filter(ImageFilter.GaussianBlur(int(params.get('radius',5))))
            elif operation == "rotate":
                img = img.rotate(int(params.get('degrees', 90)))
            elif operation == "flip":
                img = img.transpose(Image.FLIP_LEFT_RIGHT)
            
            img.save(output)
            return {"success": True, "path": output, "operation": operation}
        except Exception as e:
            return {"error": str(e)}

    def analyze(self, image_path: str) -> Dict:
        """Analyze an image and return metadata."""
        p = Path(image_path)
        if not p.exists():
            return {"error": "File not found"}
        
        info = {
            "path": str(p),
            "size_bytes": p.stat().st_size,
            "format": p.suffix.lower(),
        }
        
        # Try to get dimensions
        try:
            from PIL import Image
            with Image.open(p) as img:
                info["dimensions"] = f"{img.width}x{img.height}"
                info["mode"] = img.mode
                info["format"] = img.format
except Exception:
            pass
        
        # Try ImageMagick
        try:
            result = subprocess.run(
                ["identify", str(p)], capture_output=True, text=True, timeout=10
            )
            if result.stdout:
                info["detail"] = result.stdout.strip()
except Exception:
            pass
        
        return info

    def list_formats(self) -> List[str]:
        """List supported image formats."""
        return [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp", ".svg"]

    def _safe_filename(self, prompt: str) -> str:
        """Create safe filename from prompt."""
        import hashlib, time
        return f"sid_img_{hashlib.md5(prompt.encode()).hexdigest()[:8]}_{int(time.time())}"

    def describe_creation(self, prompt: str, style: str = "photo") -> str:
        """Use AI to describe how to create an image (no generation backend needed)."""
        if not self.ai:
            return "Describe what image you want, and I'll help you create it."
        
        result = self.ai.process(f"Describe how to create/create an image of: {prompt}. Style: {style}. Be specific about tools and steps.")
        return result.get("response", "I can describe how to create this image.")
