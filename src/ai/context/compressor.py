"""SID Context Compressor - Intelligent context compression for small models.
Uses multiple techniques to maximize limited context windows."""
import re
import hashlib
from dataclasses import dataclass
@dataclass
class CompressedContext:
    """Represents a compressed conversation context."""
    tokens_saved: int
    original_length: int
    compressed_length: int
    summaries: List[str]
    key_points: List[str]
    active_context: List[Dict]
    compression_ratio: float
class ContextCompressor:
    """Multi-strategy context compression engine."""
    def __init__(self, max_tokens: int = 8192, compression_ratio: float = 0.5):
        self.max_tokens = max_tokens
        self.compression_ratio = compression_ratio
        self.strategies = [
            self._summarize_older,
            self._extract_key_points,
            self._deduplicate_context,
            self._trim_redundant,
        ]
    def compress(self, conversation: List[Dict]) -> List[Dict]:
        """Compress a conversation to fit within context window.
        
        Uses progressive compression strategies:
        1. Sliding window with summarization of older messages
        2. Key information extraction
        3. Deduplication
        4. Token-aware trimming
        """
        if len(conversation) <= 4:
            return conversation
        compressed = list(conversation)
        for strategy in self.strategies:
            compressed = strategy(compressed)
            if len(compressed) <= 4:
                break
        return compressed
    def _summarize_older(self, conversation: List[Dict]) -> List[Dict]:
        """Summarize older messages while keeping recent ones intact."""
        if len(conversation) <= 4:
            return conversation
        # Keep last 4 messages intact
        recent = conversation[-4:]
        older = conversation[:-4]
        if not older:
            return conversation
        # Create compressed representation
        summary = self._generate_summary(older)
        compressed_older = [{"role": "system", "content": f"[Previous conversation summary]: {summary}"}]
        return compressed_older + recent
    def _extract_key_points(self, conversation: List[Dict]) -> List[Dict]:
        """Extract and condense key information from messages."""
        result = []
        for msg in conversation:
            content = msg["content"]
            if msg["role"] in ("user", "assistant") and len(content) > 200:
                # Keep only key sentences
                points = self._extract_important(content)
                if points:
                    result.append({**msg, "content": " • ".join(points[:3])})
                else:
                    result.append(msg)
            else:
                result.append(msg)
        return result
    def _deduplicate_context(self, conversation: List[Dict]) -> List[Dict]:
        """Remove duplicate or highly similar messages."""
        if not conversation:
            return conversation
        seen_hashes = set()
        result = []
        for msg in conversation:
            # Create fuzzy hash of content
            content_hash = self._fuzzy_hash(msg["content"])
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                result.append(msg)
            elif msg["role"] == "system":
                # Always keep system messages
                result.append(msg)
        return result
    def _trim_redundant(self, conversation: List[Dict]) -> List[Dict]:
        """Remove redundant system prompts and overly long messages."""
        result = []
        system_count = 0
        for msg in conversation:
            if msg["role"] == "system":
                system_count += 1
                if system_count <= 2:  # Keep only 2 system messages max
                    # Truncate system messages
                    msg = {**msg, "content": msg["content"][:500]}
                    result.append(msg)
            elif msg["role"] in ("user", "assistant"):
                # Truncate very long messages
                if len(msg["content"]) > 1000:
                    msg = {**msg, "content": msg["content"][:1000] + "..."}
                result.append(msg)
            else:
                result.append(msg)
        return result
    def _generate_summary(self, messages: List[Dict]) -> str:
        """Create a compact summary of messages."""
        total_chars = sum(len(m["content"]) for m in messages)
        user_messages = sum(1 for m in messages if m["role"] == "user")
        assistant_messages = sum(1 for m in messages if m["role"] == "assistant")
        # Extract key topics and patterns
        topics = self._extract_topics(messages)
        summary_parts = [
            f"({user_messages} user messages, {assistant_messages} assistant responses)",
            f"topics: {', '.join(topics[:5])}",
        ]
        return " | ".join(summary_parts)
    def _extract_important(self, text: str) -> List[str]:
        """Extract important sentences from text."""
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        important = []
        for s in sentences:
            s = s.strip()
            if len(s) < 20:
                continue
            # Score sentence importance
            score = 0
            # Longer sentences with specific info
            if any(w in s.lower() for w in ['command', 'code', 'run', 'install', 'config']):
                score += 2
            if any(w in s.lower() for w in ['important', 'note', 'warning', 'error']):
                score += 2
            if re.search(r'\d+', s):
                score += 1
            if s.endswith('?'):
                score += 1
            if score >= 1:
                important.append(s.strip())
        return important[:5]
    def _extract_topics(self, messages: List[Dict]) -> List[str]:
        """Extract main topics from conversation."""
        all_text = " ".join(m["content"] for m in messages)
        # Simple keyword extraction
        keywords = re.findall(r'\b[A-Za-z]{4,}\b', all_text.lower())
        freq = {}
        for k in keywords:
            freq[k] = freq.get(k, 0) + 1
        # Return most frequent meaningful words
        stop_words = {'this', 'that', 'with', 'from', 'have', 'been', 'will', 'what', 'when', 'where', 'which', 'their', 'there', 'about', 'would', 'could', 'should', 'into', 'than', 'then', 'also', 'just', 'like', 'over', 'such', 'only', 'even', 'very', 'still', 'your', 'some', 'them', 'than', 'well', 'more', 'also', 'other', 'after', 'before'}
        sorted_words = sorted(
            [(k, v) for k, v in freq.items() if k not in stop_words],
            key=lambda x: -x[1]
        )
        return [w for w, _ in sorted_words[:8]]
    def _fuzzy_hash(self, text: str) -> str:
        """Create a fuzzy hash for similarity detection."""
        # Normalize: lowercase, remove punctuation, sort words
        normalized = re.sub(r'[^\w\s]', '', text.lower())
        words = sorted(set(normalized.split()[:20]))
        return hashlib.md5(" ".join(words).encode()).hexdigest()[:16]
    def analyze(self, conversation: List[Dict]) -> CompressedContext:
        """Analyze and compress, returning detailed stats."""
        original = len(conversation)
        compressed = self.compress(conversation)
        return CompressedContext(
            tokens_saved=original - len(compressed),
            original_length=original,
            compressed_length=len(compressed),
            summaries=self._extract_topics(conversation),
            key_points=self._extract_important(
                " ".join(m["content"] for m in conversation[-4:])
            ),
            active_context=compressed,
            compression_ratio=len(compressed) / max(original, 1)
        )
