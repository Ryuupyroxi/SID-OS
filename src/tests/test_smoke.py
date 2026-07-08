"""SID OS Smoke Test — imports all 46 modules and instantiates core classes."""
import os, sys, importlib, traceback

SRC = os.path.join(os.path.dirname(__file__), '..', '..', 'src')
sys.path.insert(0, os.path.abspath(SRC))

ALL_MODULES = [
    "agent.skill_base", "agent.skill_manager", "agent.tool_registry",
    "ai.context.compressor", "ai.engine.agentic.agent_loop",
    "ai.engine.model_manager", "ai.engine.orchestrator",
    "ai.prompts.templates", "compat", "config.skills_registry",
    "memory.compression.engine", "memory.long.episodic",
    "memory.long.semantic", "memory.short.working",
    "system.hardware.monitor", "system.init.boot",
    "system.optimizer.engine", "terminal.assistant.character",
    "terminal.assistant.charforge", "terminal.assistant.charparts",
    "terminal.assistant.controller", "terminal.assistant.generator",
    "terminal.assistant.renderer", "terminal.theme.manager",
    "tools.benchmark", "tools.browser_fs", "tools.code.assistant",
    "tools.files.manager", "tools.image_gen.engine",
    "tools.image_tools", "tools.media_player",
    "tools.offline_cache", "tools.offline_storage", "tools.profile",
    "tools.search.engine", "tools.settings", "tools.system.analyzer",
    "tools.web_viewer.engine", "voice.stt.engine", "voice.tts.engine",
    "voice.vad.detector",
]

def run():
    ok, fail = 0, []
    for mod in ALL_MODULES:
        try:
            importlib.import_module(mod); ok += 1
        except Exception as e:
            fail.append((mod, str(e)[:80]))
    print(f"Modules: {ok}✓ / {len(fail)}✖")
    for m, e in fail:
        print(f"  ❌ {m}: {e}")
    return len(fail) == 0

if __name__ == "__main__":
    print("=== SID OS Smoke Test ===")
    sys.exit(0 if run() else 1)
