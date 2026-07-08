"""Tool Registry - Dynamic tool registration and execution for AI use."""
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
@dataclass
class ToolDefinition:
    """Definition of a tool the AI can use."""
    name: str
    description: str
    parameters: Dict[str, str] = field(default_factory=dict)
    returns: str = "Any"
    category: str = "general"
    callable: Any = None

class ToolRegistry:
    """Registry of tools that the AI can discover and use dynamically."""

    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}
        self._init_builtin_tools()

    def _init_builtin_tools(self):
        """Register built-in tools."""
        self.register(
            "execute_command",
            "Run a shell command and get output",
            {"command": "string"},
            "string"
        )
        self.register(
            "read_file",
            "Read contents of a file",
            {"path": "string"}
        )
        self.register(
            "write_file",
            "Write content to a file",
            {"path": "string", "content": "string"}
        )
        self.register(
            "search_files",
            "Search for files matching a pattern",
            {"pattern": "string", "path": "string"}
        )
        self.register(
            "list_directory",
            "List contents of a directory",
            {"path": "string"}
        )
        self.register(
            "system_info",
            "Get system information",
            {"category": "string"}
        )
        self.register(
            "memory_search",
            "Search through AI memory",
            {"query": "string"}
        )
        self.register(
            "offline_storage",
            "Store or retrieve web content offline",
            {"action": "string", "url": "string"}
        )

    def register(self, name: str, description: str, 
                 parameters: Dict[str, str] = None,
                 returns: str = "Any",
                 func: Optional[Callable] = None) -> bool:
        """Register a new tool."""
        self.tools[name] = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters or {},
            returns=returns,
            callable=func
        )
        return True

    def execute(self, tool_name: str, **params) -> Any:
        """Execute a tool by name with parameters."""
        if tool_name not in self.tools:
            return {"error": f"Tool '{tool_name}' not found"}
        
        tool = self.tools[tool_name]
        if tool.callable:
            try:
                return tool.callable(**params)
            except Exception as e:
                return {"error": str(e)}
        
        return {"warning": f"Tool '{tool_name}' registered but no function bound"}

    def list_tools(self) -> List[Dict]:
        """List all registered tools."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
                "returns": t.returns,
                "bound": t.callable is not None
            }
            for t in self.tools.values()
        ]

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool by name."""
        return self.tools.get(name)

    def to_prompt_context(self) -> str:
        """Format tools as AI context."""
        if not self.tools:
            return ""
        parts = ["[AVAILABLE TOOLS]"]
        for t in self.tools.values():
            params = ", ".join(f"{k}:{v}" for k, v in t.parameters.items())
            parts.append(f"  • {t.name}({params}) - {t.description}")
        return "\n".join(parts)
