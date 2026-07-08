"""Base class for all SID skills."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
import json

@dataclass
class SkillMetadata:
    """Metadata about a skill."""
    name: str
    version: str = "1.6.1"
    description: str = ""
    author: str = "SID"
    requires: List[str] = field(default_factory=list)
    provides: List[str] = field(default_factory=list)
    memory_tags: List[str] = field(default_factory=list)
    source: str = "built-in"

class BaseSkill:
    """Base class that all SID skills extend."""
    
    def __init__(self):
        self.metadata = SkillMetadata(name=self.__class__.__name__)
        self._initialized = False
    
    def initialize(self):
        """Initialize the skill. Override to add setup logic."""
        self._initialized = True
    
    def execute(self, **params) -> Dict[str, Any]:
        """Execute the skill. Override in subclass."""
        raise NotImplementedError("Skills must implement execute()")
    
    def validate(self, **params) -> bool:
        """Validate parameters before execution."""
        return True
    
    def cleanup(self):
        """Clean up resources. Override if needed."""
        pass

    def to_dict(self) -> Dict:
        return {
            "name": self.metadata.name,
            "version": self.metadata.version,
            "description": self.metadata.description,
            "requires": self.metadata.requires,
            "provides": self.metadata.provides,
        }
