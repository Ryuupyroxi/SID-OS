"""SID Offline Storage - Store webpages, wikis, webapps with compression."""
import os
import json
import gzip
import zlib
import hashlib
import time
import sqlite3
import re
import subprocess
from pathlib import Path
from typing import Optional, Dict, List, Any, Set, Tuple
from urllib.parse import urlparse, quote

class OfflineStorage:
    """Offline storage system with intelligent compression for web content."""

    def __init__(self, storage_path: str = "/var/lib/sid/offline"):
        self.storage_path = Path(storage_path)
        self.db_path = self.storage_path / "offline.db"
        self.content_path = self.storage_path / "content"
        self.compress_path = self.storage_path / "compressed"
        self._init_storage()

    def _init_storage(self):
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.content_path.mkdir(exist_ok=True)
        self.compress_path.mkdir(exist_ok=True)
        
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stored_items (
                id TEXT PRIMARY KEY,
                url TEXT UNIQUE,
                title TEXT,
                type TEXT,  -- webpage, wiki, webapp, document
                size_bytes INTEGER,
                compressed_bytes INTEGER,
                compression_ratio REAL,
                stored_at REAL,
                last_accessed REAL,
                access_count INTEGER DEFAULT 0,
                tags TEXT,
                summary TEXT,
                content_hash TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_url ON stored_items(url)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_type ON stored_items(type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tags ON stored_items(tags)")
        conn.commit()
        conn.close()

    def store_webpage(self, url: str, html: str, title: str = "", tags: str = "") -> Dict:
        """Store a webpage with compression."""
        content_id = hashlib.sha256(url.encode()).hexdigest()[:16]
        summary = self._extract_text(html)[:500]
        
        # Intelligent compression pipeline
        compressed = self._compress_content(html, "webpage")
        content_file = self.content_path / f"{content_id}.html"
        comp_file = self.compress_path / f"{content_id}.sidz"

        # Save compressed
        comp_file.write_bytes(compressed)
        
        metadata = {
            "id": content_id,
            "url": url,
            "title": title or url,
            "type": "webpage",
            "size_bytes": len(html.encode()),
            "compressed_bytes": len(compressed),
            "compression_ratio": len(compressed) / max(len(html.encode()), 1),
            "stored_at": time.time(),
            "last_accessed": time.time(),
            "tags": tags,
            "summary": summary,
            "content_hash": hashlib.md5(html.encode()).hexdigest()
        }

        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            INSERT OR REPLACE INTO stored_items 
            (id, url, title, type, size_bytes, compressed_bytes, compression_ratio,
             stored_at, last_accessed, tags, summary, content_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            content_id, url, title or url, "webpage",
            metadata["size_bytes"], metadata["compressed_bytes"],
            metadata["compression_ratio"], time.time(), time.time(),
            tags, summary, metadata["content_hash"]
        ))
        conn.commit()
        conn.close()

        return metadata

    def store_wiki(self, url: str, content: str, title: str = "") -> Dict:
        """Store wiki content with specialized compression."""
        # Wiki content has different structure - use markdown/text compression
        compressed = self._compress_content(content, "wiki")
        content_id = hashlib.sha256(url.encode()).hexdigest()[:16]
        
        (self.compress_path / f"{content_id}.wiki.sidz").write_bytes(compressed)
        
        # Extract wiki links for cross-reference
        links = re.findall(r'\[\[([^\]]+)\]\]', content)

        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            INSERT OR REPLACE INTO stored_items 
            (id, url, title, type, size_bytes, compressed_bytes, compression_ratio,
             stored_at, last_accessed, tags, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            content_id, url, title or url, "wiki",
            len(content.encode()), len(compressed),
            len(compressed) / max(len(content.encode()), 1),
            time.time(), time.time(),
            "wiki," + ",".join(links[:10]),
            content[:300]
        ))
        conn.commit()
        conn.close()

        return {"id": content_id, "title": title, "links": len(links)}

    def store_webapp(self, manifest: Dict, files: Dict[str, str]) -> Dict:
        """Store a webapp (HTML/CSS/JS bundle) with compression."""
        app_id = hashlib.sha256(manifest.get("name", "").encode()).hexdigest()[:16]
        
        # Bundle and compress
        bundle = json.dumps({
            "manifest": manifest,
            "files": files,
            "stored_at": time.time()
        })
        
        compressed = self._compress_content(bundle, "webapp")
        (self.compress_path / f"{app_id}.app.sidz").write_bytes(compressed)

        total_size = sum(len(c.encode()) for c in files.values()) + len(json.dumps(manifest))

        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            INSERT OR REPLACE INTO stored_items 
            (id, url, title, type, size_bytes, compressed_bytes, compression_ratio,
             stored_at, last_accessed, tags, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            app_id, manifest.get("url", ""), manifest.get("name", "Unknown App"),
            "webapp", total_size, len(compressed),
            len(compressed) / max(total_size, 1),
            time.time(), time.time(),
            "webapp," + manifest.get("category", ""),
            manifest.get("description", "")[:300]
        ))
        conn.commit()
        conn.close()

        return {"id": app_id, "name": manifest.get("name"), "files": len(files)}

    def retrieve(self, url_or_id: str) -> Optional[str]:
        """Retrieve and decompress stored content."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        
        # Try by URL or ID
        row = conn.execute(
            "SELECT * FROM stored_items WHERE url = ? OR id = ?",
            (url_or_id, url_or_id)
        ).fetchone()
        conn.close()

        if not row:
            return None

        row = dict(row)
        content_id = row["id"]
        content_type = row["type"]

        # Find compressed file
        patterns = [
            self.compress_path / f"{content_id}.sidz",
            self.compress_path / f"{content_id}.wiki.sidz",
            self.compress_path / f"{content_id}.app.sidz",
        ]
        
        for p in patterns:
            if p.exists():
                compressed = p.read_bytes()
                decompressed = self._decompress_content(compressed, content_type)
                
                # Update access stats
                conn = sqlite3.connect(str(self.db_path))
                conn.execute(
                    "UPDATE stored_items SET last_accessed = ?, access_count = access_count + 1 WHERE id = ?",
                    (time.time(), content_id)
                )
                conn.commit()
                conn.close()
                
                return decompressed

        return None

    def search(self, query: str, type_filter: str = "") -> List[Dict]:
        """Search stored content."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        
        sql = "SELECT * FROM stored_items WHERE (title LIKE ? OR url LIKE ? OR tags LIKE ? OR summary LIKE ?)"
        params = [f"%{query}%"] * 4
        
        if type_filter:
            sql += " AND type = ?"
            params.append(type_filter)
        
        sql += " ORDER BY access_count DESC, last_accessed DESC LIMIT 20"
        
        rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
        conn.close()
        return rows

    def list_by_type(self, content_type: str) -> List[Dict]:
        """List all stored items of a type."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        rows = [dict(r) for r in conn.execute(
            "SELECT id, url, title, size_bytes, compressed_bytes, compression_ratio, stored_at, tags, summary FROM stored_items WHERE type = ? ORDER BY stored_at DESC",
            (content_type,)
        ).fetchall()]
        conn.close()
        return rows

    def stats(self) -> Dict:
        """Get storage statistics."""
        conn = sqlite3.connect(str(self.db_path))
        
        total = conn.execute("SELECT COUNT(*) FROM stored_items").fetchone()[0]
        total_raw = conn.execute("SELECT COALESCE(SUM(size_bytes), 0) FROM stored_items").fetchone()[0]
        total_comp = conn.execute("SELECT COALESCE(SUM(compressed_bytes), 0) FROM stored_items").fetchone()[0]
        
        types = {}
        for row in conn.execute("SELECT type, COUNT(*) as c, SUM(size_bytes) as s FROM stored_items GROUP BY type").fetchall():
            types[row[0]] = {"count": row[1], "size_bytes": row[2]}
        
        conn.close()
        
        return {
            "total_items": total,
            "raw_size_bytes": total_raw,
            "compressed_size_bytes": total_comp,
            "saved_bytes": total_raw - total_comp,
            "overall_ratio": total_comp / max(total_raw, 1),
            "by_type": types,
            "storage_path": str(self.storage_path)
        }

    def _compress_content(self, content: str, content_type: str) -> bytes:
        """Intelligent multi-level compression based on content type."""
        # Stage 1: Content-specific optimization
        if content_type == "webpage":
            # Strip unnecessary whitespace from HTML
            content = re.sub(r'>\s+<', '><', content)
            content = re.sub(r'\s{2,}', ' ', content)
        elif content_type == "wiki":
            # Compact wiki markup
            content = re.sub(r'\n{3,}', '\n\n', content)
        elif content_type == "webapp":
            # Minify JS-like content
            content = re.sub(r'//.*?\n', '\n', content)
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)

        # Stage 2: zlib compression with optimal level
        compressed = zlib.compress(content.encode('utf-8'), level=9)
        
        # Stage 3: Check if gzip gives better ratio for text
        gzipped = gzip.compress(content.encode('utf-8'), compresslevel=9)
        
        return compressed if len(compressed) <= len(gzipped) else gzipped

    def _decompress_content(self, data: bytes, content_type: str) -> str:
        """Decompress content, auto-detecting method."""
        # Try zlib first
        try:
            return zlib.decompress(data).decode('utf-8')
except Exception:
            pass
        # Try gzip
        try:
            return gzip.decompress(data).decode('utf-8')
except Exception:
            pass
        return data.decode('utf-8', errors='replace')

    def _extract_text(self, html: str) -> str:
        """Extract readable text from HTML."""
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', text).strip()
        # Remove common noise
        text = re.sub(r'(javascript|function|var|let|const)\s*\([^)]*\)', '', text)
        return text[:1000]

    def import_wikipedia(self, article_title: str, lang: str = "en") -> Dict:
        """Download and store a Wikipedia article offline."""
        import urllib.request
        
        url = f"https://{lang}.wikipedia.org/w/api.php?action=query&titles={quote(article_title)}&prop=extracts&explaintext&format=json"
        
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SID-OS/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
            
            pages = data.get("query", {}).get("pages", {})
            for page_id, page in pages.items():
                if page_id != "-1":
                    title = page.get("title", article_title)
                    extract = page.get("extract", "")
                    
                    result = self.store_wiki(
                        f"https://{lang}.wikipedia.org/wiki/{quote(article_title.replace(' ', '_'))}",
                        extract,
                        title
                    )
                    result["title"] = title
                    result["length"] = len(extract)
                    return result
            
            return {"error": f"Article '{article_title}' not found"}
        except Exception as e:
            return {"error": str(e)}

    def export_snapshot(self, output_path: str) -> str:
        """Export all stored data as a portable snapshot."""
        import tarfile
        import io
        
        snap_path = Path(output_path)
        if snap_path.suffix != '.sidbak':
            snap_path = snap_path.with_suffix('.sidbak')
        
        with tarfile.open(str(snap_path), 'w:gz') as tar:
            # Add database
            tar.add(str(self.db_path), arcname='offline.db')
            # Add compressed content
            tar.add(str(self.compress_path), arcname='compressed')
            # Add metadata
            meta = json.dumps(self.stats(), indent=2)
            meta_io = io.BytesIO(meta.encode())
            tarinfo = tarfile.TarInfo(name='metadata.json')
            tarinfo.size = len(meta.encode())
            tar.addfile(tarinfo, meta_io)
        
        return str(snap_path)

    def import_snapshot(self, snapshot_path: str) -> bool:
        """Import a .sidbak snapshot."""
        import tarfile
        
        try:
            with tarfile.open(snapshot_path, 'r:gz') as tar:
                tar.extractall(path=self.storage_path)
            return True
        except Exception as e:
            print(f"[SID] Snapshot import error: {e}")
            return False
