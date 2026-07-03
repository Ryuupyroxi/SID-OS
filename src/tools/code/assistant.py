"""AI-powered code assistant for writing, reviewing, and debugging code."""
from typing import Optional, Dict, List
from pathlib import Path

class CodeAssistant:
    """AI code assistant for development tasks."""

    SUPPORTED_LANGUAGES = [
        "python", "c", "cpp", "bash", "javascript", "typescript",
        "rust", "go", "lua", "perl", "ruby", "java", "sql"
    ]

    def __init__(self, ai=None):
        self.ai = ai

    def generate(self, task: str, language: str = "python", requirements: str = "") -> str:
        """Generate code from description."""
        if not self.ai:
            return "[SID] AI engine not available"
        prompt = (
            f"Write {language} code for: {task}\n"
            f"Requirements: {requirements}\n"
            f"Return ONLY code, no markdown, no explanation."
        )
        result = self.ai.process(prompt)
        return result.get("response", "Error generating code")

    def explain(self, code: str) -> str:
        """Explain what code does."""
        if not self.ai:
            return "[SID] AI engine not available"
        prompt = f"Explain this code briefly:\n```\n{code[:2000]}\n```\n"
        result = self.ai.process(prompt)
        return result.get("response", "Error explaining code")

    def review(self, code: str) -> str:
        """Review code for issues and improvements."""
        if not self.ai:
            return "[SID] AI engine not available"
        prompt = (
            f"Review this code for bugs, security issues, and improvements:\n"
            f"```\n{code[:2000]}\n```\n"
            f"Be concise."
        )
        result = self.ai.process(prompt)
        return result.get("response", "Error reviewing code")

    def debug(self, error: str, context: str = "") -> str:
        """Debug an error message."""
        if not self.ai:
            return "[SID] AI engine not available"
        prompt = (
            f"Debug this error:\nError: {error}\n"
            f"Context: {context}\nDiagnose and suggest fix."
        )
        result = self.ai.process(prompt)
        return result.get("response", "Error debugging")

    def refactor(self, code: str, target: str) -> str:
        """Refactor code to meet a target."""
        if not self.ai:
            return "[SID] AI engine not available"
        prompt = f"Refactor this code to: {target}\n```\n{code[:2000]}\n```\n"
        result = self.ai.process(prompt)
        return result.get("response", "Error refactoring code")
