"""Episodic memory - long-term storage of interactions."""
import json
import os
import sqlite3
import time
from typing import List, Dict, Optional
from pathlib import Path

class EpisodicMemory:
    """Persistent event-based memory using SQLite."""

    def __init__(self, storage_path: str):
        self.db_path = Path(storage_path) / "episodic.db"
        self._init_db()

    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                timestamp REAL,
                user_input TEXT,
                response TEXT,
                summary TEXT,
                tokens_used INTEGER DEFAULT 0
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_session ON episodes(session_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_time ON episodes(timestamp)")
        conn.commit()
        conn.close()

    def store(self, session_id: str, user_input: str, response: str):
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            "INSERT INTO episodes (session_id, timestamp, user_input, response, summary) VALUES (?, ?, ?, ?, ?)",
            (session_id, time.time(), user_input, response, user_input[:100])
        )
        conn.commit()
        conn.close()

    def recall(self, session_id: str, limit: int = 5) -> List[Dict]:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT * FROM episodes WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?",
            (session_id, limit)
        )
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def search(self, query: str, limit: int = 5) -> List[Dict]:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT * FROM episodes WHERE user_input LIKE ? OR response LIKE ? ORDER BY timestamp DESC LIMIT ?",
            (f"%{query}%", f"%{query}%", limit)
        )
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def compress(self):
        """Archive very old episodes to reduce DB size."""
        cutoff = time.time() - (30 * 24 * 3600)  # 30 days
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("DELETE FROM episodes WHERE timestamp < ?", (cutoff,))
        conn.commit()
        conn.close()
        # VACUUM in a separate connection to avoid transaction issues
        conn2 = sqlite3.connect(str(self.db_path))
        conn2.isolation_level = None  # Auto-commit mode
        try:
            conn2.execute("VACUUM")
except Exception:
            pass
        conn2.close()

    def count(self) -> int:
        conn = sqlite3.connect(str(self.db_path))
        count = conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
        conn.close()
        return count
