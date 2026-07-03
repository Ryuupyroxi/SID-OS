"""SID Offline Cache - Automatic caching and offline fallback for web/media.
When online, caches content. When offline, seamlessly serves cached versions."""
import os
import json
import time
import hashlib
import sqlite3
import threading
import urllib.request
from pathlib import Path
from typing import Optional, Dict, List, Any, Callable
from datetime import datetime, timedelta

class OfflineCache:
    """Intelligent offline cache that auto-switches between online/offline."""

    def __init__(self, cache_path: str = "/var/lib/sid/cache"):
        self.cache_path = Path(cache_path)
        self.db_path = self.cache_path / "cache.db"
        self.content_path = self.cache_path / "content"
        self._online = True
        self._cache_hits = 0
        self._cache_misses = 0
        self._init_db()
        self._start_monitor()

    def _init_db(self):
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self.content_path.mkdir(exist_ok=True)
        
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                url TEXT,
                content_type TEXT,
                size INTEGER,
                cached_at REAL,
                expires_at REAL,
                access_count INTEGER DEFAULT 0,
                last_accessed REAL,
                headers TEXT,
                tags TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_url ON cache(url)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache(expires_at)")
        conn.commit()
        conn.close()

    def _start_monitor(self):
        """Start background thread to monitor connectivity."""
        def monitor():
            while True:
                self._check_connectivity()
                time.sleep(30)
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()

    def _check_connectivity(self):
        """Check internet connectivity."""
        try:
            urllib.request.urlopen("http://clients3.google.com/generate_204", timeout=3)
            self._online = True
        except:
            self._online = False

    @property
    def is_online(self) -> bool:
        return self._online

    def get(self, url: str, max_age: int = 86400) -> Optional[Dict]:
        """Retrieve cached content. Returns None if not cached or expired."""
        key = self._make_key(url)
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        
        row = conn.execute(
            "SELECT * FROM cache WHERE key = ? AND (expires_at IS NULL OR expires_at > ?)",
            (key, time.time())
        ).fetchone()
        
        if row:
            # Update access stats
            conn.execute(
                "UPDATE cache SET access_count = access_count + 1, last_accessed = ? WHERE key = ?",
                (time.time(), key)
            )
            conn.commit()
            
            content_file = self.content_path / f"{key}.dat"
            if content_file.exists():
                self._cache_hits += 1
                result = {
                    "url": row["url"],
                    "content": content_file.read_bytes(),
                    "content_type": row["content_type"],
                    "headers": json.loads(row["headers"] or "{}"),
                    "cached": True,
                    "mode": "offline" if not self._online else "cached"
                }
                conn.close()
                return result
        
        conn.close()
        self._cache_misses += 1
        return None

    def put(self, url: str, content: bytes, content_type: str = "",
            headers: Dict = None, tags: str = "", max_age: int = 86400):
        """Cache content for offline use."""
        key = self._make_key(url)
        
        # Save content to file
        content_file = self.content_path / f"{key}.dat"
        content_file.write_bytes(content)
        
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            INSERT OR REPLACE INTO cache 
            (key, url, content_type, size, cached_at, expires_at, headers, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            key, url, content_type, len(content),
            time.time(), time.time() + max_age,
            json.dumps(headers or {}), tags
        ))
        conn.commit()
        conn.close()

    def fetch_with_cache(self, url: str, max_age: int = 86400, 
                         headers: Dict = None) -> Dict:
        """Fetch URL with automatic caching and offline fallback.
        
        Online: Fetch and cache. Offline: Return cached version.
        """
        # Check cache first
        cached = self.get(url, max_age)
        if cached:
            return cached
        
        # Try online fetch
        if self._online:
            try:
                req = urllib.request.Request(
                    url, headers=headers or {"User-Agent": "SID-OS/1.0"}
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    content = resp.read()
                    content_type = resp.headers.get("Content-Type", "")
                    resp_headers = dict(resp.headers)
                    
                    # Cache it
                    self.put(url, content, content_type, resp_headers, max_age=max_age)
                    
                    return {
                        "url": url,
                        "content": content,
                        "content_type": content_type,
                        "headers": resp_headers,
                        "cached": False,
                        "mode": "online"
                    }
            except Exception as e:
                return {"error": str(e), "mode": "failed", "url": url}
        else:
            return {"error": "Offline and no cached version", "mode": "offline", "url": url}

    def cache_webpage(self, url: str) -> bool:
        """Cache a webpage for offline reading."""
        result = self.fetch_with_cache(url, max_age=7*86400)  # 7 days
        return "error" not in result

    def search(self, query: str) -> List[Dict]:
        """Search cached content."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT url, content_type, size, cached_at, access_count, tags "
            "FROM cache WHERE url LIKE ? OR tags LIKE ? ORDER BY access_count DESC LIMIT 20",
            (f"%{query}%", f"%{query}%")
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def preload(self, urls: List[str]):
        """Preload multiple URLs into cache."""
        def worker(url):
            try:
                self.fetch_with_cache(url, max_age=7*86400)
            except:
                pass
        
        threads = []
        for url in urls:
            t = threading.Thread(target=worker, args=(url,), daemon=True)
            t.start()
            threads.append(t)
        
        for t in threads:
            t.join(timeout=30)

    def stats(self) -> Dict:
        """Get cache statistics."""
        conn = sqlite3.connect(str(self.db_path))
        total = conn.execute("SELECT COUNT(*) FROM cache").fetchone()[0]
        total_size = conn.execute("SELECT COALESCE(SUM(size), 0) FROM cache").fetchone()[0]
        top = conn.execute(
            "SELECT url, size, access_count FROM cache ORDER BY access_count DESC LIMIT 5"
        ).fetchall()
        conn.close()
        
        return {
            "total_items": total,
            "total_size_bytes": total_size,
            "online": self._online,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_ratio": self._cache_hits / max(self._cache_hits + self._cache_misses, 1),
            "top_cached": [{"url": r[0], "size": r[1], "accesses": r[2]} for r in top],
            "path": str(self.cache_path)
        }

    def clear_expired(self):
        """Clear expired cache entries."""
        conn = sqlite3.connect(str(self.db_path))
        expired = conn.execute(
            "SELECT key FROM cache WHERE expires_at < ?", (time.time(),)
        ).fetchall()
        
        for (key,) in expired:
            content_file = self.content_path / f"{key}.dat"
            if content_file.exists():
                content_file.unlink()
        
        conn.execute("DELETE FROM cache WHERE expires_at < ?", (time.time(),))
        conn.commit()
        conn.close()
        # VACUUM in auto-commit mode
        try:
            conn2 = sqlite3.connect(str(self.db_path))
            conn2.isolation_level = None
            conn2.execute("VACUUM")
            conn2.close()
        except:
            pass

    def _make_key(self, url: str) -> str:
        return hashlib.sha256(url.encode()).hexdigest()[:16]
