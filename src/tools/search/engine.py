"""AI-powered search across files, web, and system."""
import os
import subprocess
from typing import Optional, Dict, List
from pathlib import Path

class SearchEngine:
    """Unified search with AI assistance."""

    def __init__(self, ai=None):
        self.ai = ai

    def files(self, query: str, path: str = ".") -> List[str]:
        """Search file contents using ripgrep."""
        try:
            result = subprocess.run(
                ["rg", "-l", "-i", query, path],
                capture_output=True, text=True, timeout=30
            )
            return result.stdout.strip().split('\n') if result.stdout else []
        except:
            return []

    def text(self, query: str, path: str = ".") -> Dict[str, List[str]]:
        """Search for text with context."""
        try:
            result = subprocess.run(
                ["rg", "-n", "-i", query, path],
                capture_output=True, text=True, timeout=30
            )
            lines = result.stdout.strip().split('\n') if result.stdout else []
            return {"results": lines[:50], "total": len(lines)}
        except:
            return {"results": [], "total": 0}

    def ai_search(self, query: str, context: str = "") -> str:
        """Search using AI understanding."""
        if not self.ai:
            return "[SID] AI engine not available"
        prompt = f"Search: {query}\nContext: {context}\nAnswer concisely."
        result = self.ai.process(prompt)
        return result.get("response", "Error searching")

    def web(self, query: str) -> str:
        """Search the web (requires connectivity)."""
        if not self.ai or not self.ai.config.api_key:
            return "[SID] Web search requires API key. Use 'config set api_key <key>'"
        prompt = f"Search the web for: {query}\nReturn a concise summary with sources."
        result = self.ai.process(prompt)
        return result.get("response", "Error searching web")
