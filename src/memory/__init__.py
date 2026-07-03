"""SID Memory System - Persistent memory with compression and recall."""
from typing import List, Dict
from .short.working import WorkingMemory
from .long.episodic import EpisodicMemory
from .long.semantic import SemanticMemory
from .compression.engine import MemoryCompressor

class MemorySystem:
    """Integrated memory system with multiple memory types."""

    def __init__(self, storage_path: str = "/var/lib/sid/memory"):
        self.storage_path = storage_path
        self.working = WorkingMemory(capacity=50)
        self.episodic = EpisodicMemory(storage_path)
        self.semantic = SemanticMemory(storage_path)
        self.compressor = MemoryCompressor()
        self._init_storage()

    def _init_storage(self):
        import os
        os.makedirs(self.storage_path, exist_ok=True)

    def store(self, session_id: str, user_input: str, response: str):
        """Store an interaction in memory."""
        # Working memory (short-term, recent context)
        self.working.add({"user": user_input, "assistant": response})

        # Episodic memory (long-term, event-based)
        if len(user_input) > 10:  # Only store meaningful interactions
            self.episodic.store(session_id, user_input, response)

        # Semantic memory (extract and store knowledge)
        knowledge = self.compressor.extract_knowledge(user_input, response)
        if knowledge:
            self.semantic.store(knowledge)

    def recall(self, user_id: str = "", limit: int = 5) -> List[Dict]:
        """Recall relevant memories for context building."""
        memories = []

        # Get recent working memory
        working = self.working.get_recent(3)
        for m in working:
            memories.append({"type": "recent", "content": m})

        # Get relevant episodic memories
        if user_id:
            episodic = self.episodic.recall(user_id, limit=2)
            for m in episodic:
                memories.append({"type": "past", "content": m})

        return memories[-limit:]

    def search(self, query: str) -> List[Dict]:
        """Search across all memory types."""
        results = []
        results.extend(self.episodic.search(query, limit=3))
        results.extend(self.semantic.search(query, limit=3))
        return results

    def optimize(self):
        """Run memory optimization and compression."""
        self.working.prune()
        self.episodic.compress()
        self.semantic.deduplicate()

    def stats(self) -> Dict:
        return {
            "working": len(self.working.items),
            "episodic": self.episodic.count(),
            "semantic": self.semantic.count(),
            "path": self.storage_path
        }

