"""Semantic memory - extracted knowledge and patterns."""
import json
import sqlite3
import time
import hashlib
from typing import List, Dict, Optional
from pathlib import Path

class SemanticMemory:
    """Long-term semantic knowledge storage."""

    def __init__(self, storage_path: str):
        self.db_path = Path(storage_path) / "semantic.db"
        self._init_db()

    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE,
                value TEXT,
                category TEXT DEFAULT 'general',
                confidence REAL DEFAULT 1.0,
                timestamp REAL,
                access_count INTEGER DEFAULT 0
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_key ON knowledge(key)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cat ON knowledge(category)")
        conn.commit()
        conn.close()

    def store(self, knowledge: Dict):
        conn = sqlite3.connect(str(self.db_path))
        key_hash = hashlib.md5(knowledge.get('key', '').encode()).hexdigest()
        conn.execute(
            """INSERT OR REPLACE INTO knowledge (key, value, category, confidence, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (key_hash, json.dumps(knowledge), knowledge.get('category', 'general'),
             knowledge.get('confidence', 1.0), time.time())
        )
        conn.commit()
        conn.close()

    def search(self, query: str, limit: int = 5) -> List[Dict]:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT * FROM knowledge WHERE value LIKE ? ORDER BY confidence DESC, access_count DESC LIMIT ?",
            (f"%{query}%", limit)
        )
        results = []
        for row in cursor.fetchall():
            item = dict(row)
            item['value'] = json.loads(item['value'])
            results.append(item)
        conn.close()
        return results

    def deduplicate(self):
        """Remove duplicate knowledge entries."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            DELETE FROM knowledge WHERE id NOT IN (
                SELECT MIN(id) FROM knowledge GROUP BY key
            )
        """)
        conn.commit()
        conn.close()
        # VACUUM in a separate connection with auto-commit (non-critical)
        try:
            conn2 = sqlite3.connect(str(self.db_path))
            conn2.isolation_level = None
            conn2.execute("VACUUM")
            conn2.close()
        except:
            pass

    def count(self) -> int:
        conn = sqlite3.connect(str(self.db_path))
        count = conn.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0]
        conn.close()
        return count
