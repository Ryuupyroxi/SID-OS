"""Agentic Loop - Plan, execute, observe, adapt cycle for complex tasks.
Inspired by Hermes agentic frameworks. The AI plans a task, executes tools,
observes results, and adapts its approach."""
import json
import time
import traceback
from typing import Dict, List, Optional, Any, Callable

class AgentLoop:
    """Plan-execute-observe-adapt agent loop for complex AI tasks."""

    def __init__(self, ai=None, tool_registry=None, skill_manager=None):
        self.ai = ai
        self.tools = tool_registry
        self.skills = skill_manager
        self.max_iterations = 10
        self.history = []

    def run(self, task: str, context: Optional[Dict] = None) -> Dict:
        """Run a task through the agentic loop."""
        plan = self._plan(task, context or {})
        results = []
        
        for step in plan.get("steps", []):
            result = self._execute_step(step)
            results.append({"step": step, "result": result})
            
            if result.get("error"):
                adapted = self._adapt(step, result)
                results.append({"step": adapted, "result": self._execute_step(adapted)})

        return {
            "task": task,
            "plan": plan,
            "results": results,
            "summary": self._summarize(results)
        }

    def _plan(self, task: str, context: Dict) -> Dict:
        """Create a step-by-step plan for a task."""
        if not self.ai:
            return {"steps": [{"action": "direct", "description": task}], "reasoning": ""}
        
        prompt = (
            f"Create a step-by-step plan for: {task}\n"
            f"Available tools: {self._list_tools()}\n"
            f"Available skills: {self._list_skills()}\n"
            f"Return as JSON: {{\"steps\": [{{\"action\": \"...\", \"description\": \"...\", \"tool\": \"...\", \"params\": {{}}}}]}}"
        )
        result = self.ai.process(prompt)
        try:
            return json.loads(result.get("response", "{}"))
        except:
            return {"steps": [{"action": "direct", "description": task}], "reasoning": result.get("response", "")}

    def _execute_step(self, step: Dict) -> Dict:
        """Execute a single step in the plan."""
        start = time.time()
        
        # Try tool execution
        if step.get("tool") and self.tools:
            tool = self.tools.get(step["tool"])
            if tool:
                try:
                    result = tool(**step.get("params", {}))
                    return {"success": True, "output": result, "duration": time.time() - start}
                except Exception as e:
                    return {"error": str(e), "duration": time.time() - start}

        # Try skill execution
        if step.get("skill") and self.skills:
            try:
                result = self.skills.execute(step["skill"], **step.get("params", {}))
                return {"success": result.get("success", False), "output": result, "duration": time.time() - start}
            except Exception as e:
                return {"error": str(e), "duration": time.time() - start}

        # Direct AI generation
        if self.ai and step.get("action") in ("ask", "generate", "direct"):
            result = self.ai.process(step.get("description", ""))
            return {"success": True, "output": result.get("response", ""), "duration": time.time() - start}

        return {"error": f"Cannot execute step: {step}", "duration": time.time() - start}

    def _adapt(self, failed_step: Dict, result: Dict) -> Dict:
        """Adapt the plan when a step fails."""
        if not self.ai:
            return {"action": "fallback", "description": f"Retrying: {failed_step.get('description', '')}"}
        
        prompt = (
            f"Step failed: {failed_step}\n"
            f"Error: {result.get('error', '')}\n"
            f"Suggest an adapted step."
        )
        response = self.ai.process(prompt)
        return {
            "action": "adapted",
            "description": response.get("response", "Retry"),
            "previous_error": result.get("error", "")
        }

    def _summarize(self, results: List) -> str:
        """Summarize the results of all steps."""
        successes = sum(1 for r in results if r.get("result", {}).get("success"))
        failures = sum(1 for r in results if r.get("result", {}).get("error"))
        total_time = sum(r.get("result", {}).get("duration", 0) for r in results)
        return f"Completed {successes}/{len(results)} steps successfully in {total_time:.1f}s ({failures} failures)"

    def _list_tools(self) -> str:
        if not self.tools:
            return "none"
        return ", ".join(self.tools.list_tools()[:10]) if hasattr(self.tools, 'list_tools') else "available"

    def _list_skills(self) -> str:
        if not self.skills:
            return "none"
        skills = self.skills.list_skills()
        return ", ".join(s.get("name", "?") for s in skills[:10]) if skills else "none"
