"""Memory compression engine - extracts and condenses knowledge."""
import re
from typing import Dict, List, Optional

class MemoryCompressor:
    """Extracts and compresses knowledge from interactions."""

    def extract_knowledge(self, user_input: str, response: str) -> Optional[Dict]:
        """Extract learnable knowledge from an interaction."""
        knowledge = None

        # Check for commands and their results
        commands = re.findall(r'`([^`]+)`', response)
        if commands:
            knowledge = {
                "key": commands[0],
                "type": "command",
                "value": commands[0],
                "category": "system",
                "confidence": 0.8
            }

        # Check for factual information
        facts = re.findall(r'(?:is|are|was|were|means?)\s+([^.]{10,100})', response)
        if facts and not knowledge:
            knowledge = {
                "key": facts[0][:50],
                "type": "fact",
                "value": facts[0][:100],
                "category": "knowledge",
                "confidence": 0.6
            }

        return knowledge

    def compress_interaction(self, text: str) -> str:
        """Compress interaction text for efficient storage."""
        # Remove filler words
        text = re.sub(r'\b(?:the|a|an|in|on|at|to|for|of|and|or|is|was|are|were|been|being|have|has|had|do|does|did|will|would|can|could|shall|should|may|might|about|into|through|during|before|after|above|below|between|under|again|further|then|once|here|there|when|where|why|how|all|each|every|both|few|more|most|other|some|such|no|nor|not|only|own|same|so|than|too|very|just|also|now)\b', '', text, flags=re.IGNORECASE)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:200]  # Keep max 200 chars
