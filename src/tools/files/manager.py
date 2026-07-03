"""AI-powered file management and operations."""
import os
import shutil
from pathlib import Path
from typing import Optional, Dict, List

class FileManager:
    """AI-assisted file operations."""

    def __init__(self, ai=None):
        self.ai = ai

    def find(self, query: str, path: str = ".") -> List[str]:
        """Find files using AI-powered search."""
        import subprocess
        try:
            result = subprocess.run(
                ["find", path, "-iname", f"*{query}*"],
                capture_output=True, text=True, timeout=10
            )
            return result.stdout.strip().split('\n') if result.stdout else []
        except:
            return []

    def organize(self, path: str = ".") -> str:
        """Get AI suggestion for organizing a directory."""
        if not self.ai:
            return "[SID] AI engine not available"
        
        try:
            files = os.listdir(path)
            prompt = f"Suggest how to organize these files: {files[:30]}"
            result = self.ai.process(prompt)
            return result.get("response", "No suggestions")
        except Exception as e:
            return f"Error: {e}"

    def summarize(self, path: str) -> str:
        """Get AI summary of a file's contents."""
        if not self.ai:
            return "[SID] AI engine not available"
        
        try:
            p = Path(path)
            if not p.exists():
                return f"File not found: {path}"
            
            content = p.read_text()[:3000]
            prompt = f"Summarize this file briefly:\n```\n{content}\n```\n"
            result = self.ai.process(prompt)
            return result.get("response", "Error summarizing")
        except Exception as e:
            return f"Error: {e}"

    def batch_rename(self, pattern: str, replacement: str, path: str = "."):
        """Batch rename files matching pattern."""
        try:
            for f in Path(path).iterdir():
                if pattern in f.name:
                    new_name = f.name.replace(pattern, replacement)
                    f.rename(f.parent / new_name)
                    print(f"  Renamed: {f.name} -> {new_name}")
        except Exception as e:
            print(f"Error: {e}")
