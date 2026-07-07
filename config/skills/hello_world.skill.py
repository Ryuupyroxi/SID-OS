"""Example SID skill - Hello World."""
from src.agent.skill_base import BaseSkill, SkillMetadata

class HelloWorldSkill(BaseSkill):
    """Simple example skill demonstrating the skill system."""

    def __init__(self):
        super().__init__()
        self.metadata = SkillMetadata(
            name="hello_world",
            version="1.0.0",
            description="A simple hello world example skill",
            author="SID OS",
            dependencies=[]
        )

    def execute(self, **params) -> str:
        name = params.get("name", "User")
        return f"Hello, {name}! I'm SID, your AI operating system."

    def validate(self, **params) -> bool:
        return True
