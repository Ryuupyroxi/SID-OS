"""Working memory - short-term conversation context."""
from collections import deque

class WorkingMemory:
    """Short-term working memory with FIFO eviction."""

    def __init__(self, capacity: int = 50):
        self.items = deque(maxlen=capacity)
        self.capacity = capacity

    def add(self, item: Dict):
        self.items.append(item)

    def get_recent(self, n: int = 5) -> List[Dict]:
        return list(self.items)[-n:]

    def clear(self):
        self.items.clear()

    def prune(self):
        """Prune old items when over capacity."""
        while len(self.items) > self.capacity:
            self.items.popleft()
