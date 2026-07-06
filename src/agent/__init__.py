"""SID Agentic Skill Framework - Inspired by Hermes agentic architecture.
Skills are modular capabilities the AI can learn, add, and use dynamically."""
from typing import Dict
from .skill_manager import SkillManager
from .tool_registry import ToolRegistry
from .skill_base import BaseSkill

class AgentSystem:
    """Complete agentic system with skill management and tool registry."""
    
    def __init__(self, ai_orchestrator=None):
        self.skills = SkillManager()
        self.tools = ToolRegistry()
        self.ai = ai_orchestrator
    
    def learn_skill(self, skill_name: str, source: str = "") -> bool:
        """Learn a new skill from source or registry."""
        return self.skills.learn(skill_name, source)
    
    def execute_skill(self, skill_name: str, **params) -> Dict:
        """Execute a skill with parameters."""
        return self.skills.execute(skill_name, **params)
    
    def register_tool(self, name: str, func, description: str):
        """Register a new tool for AI use."""
        return self.tools.register(name, func, description)
    
    def get_capabilities(self) -> list:
        """Get list of all capabilities (skills + tools)."""
        return self.skills.list_skills() + self.tools.list_tools()
