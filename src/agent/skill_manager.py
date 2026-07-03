"""Skill Manager - Dynamic skill loading, learning, and execution."""
import os
import json
import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from .skill_base import BaseSkill, SkillMetadata

class SkillManager:
    """Manages AI skills - abilities the AI can learn and use dynamically."""

    SKILL_DIRS = [
        "/sid/skills",
        "/usr/share/sid/skills",
        os.path.expanduser("~/.sid/skills"),
    ]

    def __init__(self):
        self.skills: Dict[str, BaseSkill] = {}
        self.skill_metadata: Dict[str, SkillMetadata] = {}
        self._discover_skills()

    def _discover_skills(self):
        """Discover installed skills from skill directories."""
        for skill_dir in self.SKILL_DIRS:
            p = Path(skill_dir)
            if p.exists():
                for f in p.glob("*.py"):
                    try:
                        spec = importlib.util.spec_from_file_location(
                            f"skill_{f.stem}", str(f)
                        )
                        mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(mod)
                        
                        # Find skill classes
                        for name, obj in inspect.getmembers(mod):
                            if (inspect.isclass(obj) and 
                                issubclass(obj, BaseSkill) and 
                                obj != BaseSkill):
                                skill = obj()
                                self.skills[skill.metadata.name] = skill
                                self.skill_metadata[skill.metadata.name] = skill.metadata
                    except Exception as e:
                        print(f"[SID Skills] Load error {f.name}: {e}")

    def learn(self, skill_name: str, source: str = "") -> bool:
        """Learn a new skill from a source (URL, file path, or registry)."""
        # Check if skill is already loaded
        if skill_name in self.skills:
            return True

        # Try to find and download the skill
        if source and source.startswith(("http://", "https://")):
            return self._download_skill(skill_name, source)
        
        # Try from built-in registry
        from ..config.skills_registry import BUILTIN_SKILLS
        if skill_name in BUILTIN_SKILLS:
            skill_info = BUILTIN_SKILLS[skill_name]
            if skill_info.get("url"):
                return self._download_skill(skill_name, skill_info["url"])
        
        return False

    def _download_skill(self, name: str, url: str) -> bool:
        """Download a skill from URL."""
        import urllib.request
        
        skill_dir = Path(self.SKILL_DIRS[1])  # /usr/share/sid/skills
        skill_dir.mkdir(parents=True, exist_ok=True)
        
        dest = skill_dir / f"{name.lower().replace(' ', '_')}.py"
        
        try:
            urllib.request.urlretrieve(url, dest)
            # Reload skills
            self._discover_skills()
            return name in self.skills
        except Exception as e:
            print(f"[SID Skills] Download error: {e}")
            return False

    def execute(self, skill_name: str, **params) -> Dict:
        """Execute a skill with parameters."""
        if skill_name not in self.skills:
            return {"error": f"Skill '{skill_name}' not found", "success": False}
        
        skill = self.skills[skill_name]
        if not skill.validate(**params):
            return {"error": "Invalid parameters", "success": False}
        
        try:
            result = skill.execute(**params)
            return {"result": result, "success": True, "skill": skill_name}
        except Exception as e:
            return {"error": str(e), "success": False}

    def list_skills(self) -> List[Dict]:
        """List all available skills."""
        return [
            {
                "name": name,
                "metadata": meta.__dict__ if hasattr(meta, '__dict__') else {},
                "loaded": name in self.skills
            }
            for name, meta in self.skill_metadata.items()
        ]

    def get_skill(self, name: str) -> Optional[BaseSkill]:
        """Get a skill by name."""
        return self.skills.get(name)

    def get_capability_summary(self) -> str:
        """Get a summary of all skills for AI context."""
        if not self.skills:
            return ""
        parts = ["[AVAILABLE SKILLS]"]
        for name, skill in self.skills.items():
            parts.append(f"  • {name}: {skill.metadata.description}")
        return "\n".join(parts)
