"""SID Web Viewer Engine - Offline-capable CLI web browser.
Automatically caches pages when online, serves cached when offline."""
import os
import json
import re
import time
import hashlib
import subprocess
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple

class WebViewerEngine:
    """CLI web browser with intelligent offline cache."""

    def __init__(self, cache_dir: str = "/var/lib/sid/cache/web"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.backend = self._detect_backend()
        self._online = self._check_connectivity()

    def _detect_backend(self) -> str:
        """Detect available CLI web browser."""
        for cmd in ['w3m', 'lynx', 'links2', 'links', 'elinks']:
            if self._find_binary(cmd):
                return cmd
        # Fallback: use curl/wget to fetch HTML, strip tags
        if self._find_binary('curl') or self._find_binary('wget'):
            return "curl_fallback"
        return "none"

    def _find_binary(self, name: str) -> Optional[str]:
        import shutil
        return shutil.which(name)

    def _check_connectivity(self) -> bool:
        """Check internet connectivity."""
        try:
            urllib.request.urlopen("http://clients3.google.com/generate_204", timeout=3)
            return True
except Exception:
            return False

    def view(self, url: str, force_refresh: bool = False) -> Dict:
        """View a URL. Uses cache when offline, caches when online."""
        self._online = self._check_connectivity()
        cache_key = hashlib.sha256(url.encode()).hexdigest()[:16]
        cache_file = self.cache_dir / f"{cache_key}.html"
        meta_file = self.cache_dir / f"{cache_key}.json"

        # Check cache first
        if not force_refresh and cache_file.exists() and meta_file.exists():
            metadata = json.loads(meta_file.read_text())
            cached_time = metadata.get("cached_at", 0)
            
            # Serve cached if offline or cache is fresh (< 24h)
            if not self._online or (time.time() - cached_time < 86400):
                content = cache_file.read_text(encoding='utf-8', errors='replace')
                return {
                    "url": url,
                    "content": content,
                    "cached": True,
                    "cached_at": cached_time,
                    "backend": self.backend,
                    "online": self._online
                }

        # Try to fetch fresh content
        if self._online:
            result = self._fetch(url)
            if not result.get("error"):
                # Cache the result
                cache_file.write_bytes(result.get("raw", b""))
                meta_file.write_text(json.dumps({
                    "url": url,
                    "cached_at": time.time(),
                    "content_type": result.get("content_type", "text/html")
                }))
                return result

        # Offline and no cache
        return {
            "url": url,
            "error": "Cannot fetch URL and no cached version available",
            "online": False,
            "cached": False
        }

    def _fetch(self, url: str) -> Dict:
        """Fetch a URL and return content."""
        try:
            if self.backend == "w3m":
                result = subprocess.run(
                    ["w3m", "-dump", "-cols", "120", url],
                    capture_output=True, text=True, timeout=30
                )
                return {
                    "url": url,
                    "content": result.stdout,
                    "error": result.stderr if result.returncode != 0 else "",
                    "cached": False,
                    "online": True,
                    "backend": "w3m"
                }
            elif self.backend == "lynx":
                result = subprocess.run(
                    ["lynx", "-dump", "-nolist", "-width=120", url],
                    capture_output=True, text=True, timeout=30
                )
                return {
                    "url": url,
                    "content": result.stdout,
                    "error": result.stderr if result.returncode != 0 else "",
                    "cached": False,
                    "online": True,
                    "backend": "lynx"
                }
            elif self.backend in ("links2", "links", "elinks"):
                result = subprocess.run(
                    [self.backend, "-dump", "-width", "120", url],
                    capture_output=True, text=True, timeout=30
                )
                return {
                    "url": url,
                    "content": result.stdout,
                    "error": result.stderr if result.returncode != 0 else "",
                    "cached": False,
                    "online": True,
                    "backend": self.backend
                }
            else:
                # Curl fallback - fetch and strip HTML
                result = subprocess.run(
                    ["curl", "-sL", url],
                    capture_output=True, timeout=30
                )
                html = result.stdout.decode('utf-8', errors='replace')
                text = self._strip_html(html)
                return {
                    "url": url,
                    "content": text,
                    "raw": html.encode('utf-8'),
                    "content_type": "text/html",
                    "cached": False,
                    "online": True,
                    "backend": "curl"
                }
        except subprocess.TimeoutExpired:
            return {"error": "Request timed out", "url": url}
        except Exception as e:
            return {"error": str(e), "url": url}

    def _strip_html(self, html: str) -> str:
        """Strip HTML tags to get readable text."""
        # Remove scripts and styles
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        # Remove tags
        text = re.sub(r'<[^>]+>', ' ', text)
        # Decode HTML entities
        text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        text = text.replace('&quot;', '"').replace('&#39;', "'")
        # Clean whitespace
        text = re.sub(r'&nbsp;', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:10000]  # Limit to 10k chars

    def search_wikipedia(self, query: str, lang: str = "en") -> Dict:
        """Search and view Wikipedia articles (auto-cached)."""
        import urllib.parse
        url = f"https://{lang}.m.wikipedia.org/w/index.php?search={urllib.parse.quote(query)}"
        return self.view(url)

    def get_cached_pages(self) -> List[Dict]:
        """List all cached pages."""
        pages = []
        for f in self.cache_dir.glob("*.json"):
            try:
                meta = json.loads(f.read_text())
                pages.append(meta)
except Exception:
                pass
        return sorted(pages, key=lambda x: x.get("cached_at", 0), reverse=True)

    def clear_cache(self, older_than_days: int = 7):
        """Clear cached pages older than specified days."""
        cutoff = time.time() - (older_than_days * 86400)
        for f in self.cache_dir.glob("*"):
            if f.stat().st_mtime < cutoff:
                f.unlink()

    def ai_read(self, url: str, ai=None) -> str:
        """Fetch a page and have AI summarize it."""
        result = self.view(url)
        if result.get("error"):
            return f"[SID] Error: {result['error']}"
        
        content = result.get("content", "")
        if not content or len(content) < 50:
            return "[SID] Page appears to be empty or inaccessible"

        if ai:
            prompt = f"Summarize this web content in 3-4 sentences:\n\n{content[:3000]}"
            resp = ai.process(prompt)
            return resp.get("response", content[:500])
        
        return content[:500]

    def status(self) -> Dict:
        """Get web viewer status."""
        pages = self.get_cached_pages()
        return {
            "online": self._online,
            "backend": self.backend,
            "cached_pages": len(pages),
            "cache_dir": str(self.cache_dir),
            "backends_available": self.backend != "none"
        }
