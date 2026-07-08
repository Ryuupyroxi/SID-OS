#!/usr/bin/env python3
"""SID OS - Super Intelligent Distro Main Entry Point.
Initializes AI engine, voice, media, storage, and terminal."""
import os
import sys
import time
import json
import signal
import argparse
import subprocess
import threading
from pathlib import Path


def check_dependencies():
    """Auto-detect and install missing Python dependencies on first run."""
    import importlib, shutil
    required = {"numpy": "numpy", "psutil": "psutil", "PIL": "pillow", "yaml": "pyyaml"}
    missing = []
    for imp_name, pkg_name in required.items():
        try:
            importlib.import_module(imp_name)
        except ImportError:
            missing.append(pkg_name)
    if missing:
        pkg_str = ", ".join(missing)
        print(f"\033[33m[SID] Installing required deps: {pkg_str}\033[0m")
        try:
            import subprocess as sp
            sp.check_call([sys.executable, "-m", "pip", "install", "--quiet"] + missing,
                         stdout=sp.DEVNULL, stderr=sp.DEVNULL, timeout=120)
            print(f"\033[32m[SID] Dependencies installed \u2713\033[0m")
        except Exception as e:
            print(f"\033[31m[SID] Warning: {e}\033[0m")
    # Check system tools (non-critical, informational)
    system_tools = {"mpv": "media playback", "espeak-ng": "text-to-speech", "w3m": "web viewer"}
    for tool, purpose in system_tools.items():
        if not shutil.which(tool):
            print(f"  \033[2mNote: {tool} not found ({purpose})\033[0m")

def main():
    check_dependencies()
    parser = argparse.ArgumentParser(
        description="SID - Super Intelligent Distro: AI-First OS for Old Hardware",
        epilog="Just run it. The AI will guide you."
    )
    parser.add_argument("--no-ai", action="store_true", help="Disable AI engine")
    parser.add_argument("--no-voice", action="store_true", help="Disable voice system")
    parser.add_argument("--config", type=str, help="Config file path")
    parser.add_argument("--boot", action="store_true", help="Run boot sequence")
    parser.add_argument("--install", action="store_true", help="Run installer")
    parser.add_argument("--theme", type=str, help="Terminal theme (green, amber, etc.)")
    parser.add_argument("--ram-tier", type=str, choices=["2gb", "4gb", "6gb"], 
                       help="RAM tier for model selection")
    parser.add_argument("--quick-setup", type=str, choices=["2gb", "4gb", "6gb"],
                       help="Quick setup for RAM tier")
    parser.add_argument("--benchmark", action="store_true", help="Run hardware benchmark")
    parser.add_argument("--soul", type=str, help="Soul/personality file path")
    parser.add_argument("--skills", type=str, help="Skills directory path")
    args = parser.parse_args()

    # Handle benchmark mode
    if args.benchmark:
        from tools.benchmark import HardwareBenchmark
        bench = HardwareBenchmark()
        results = bench.run_all()
        print(json.dumps(results, indent=2))
        return

    # Handle installer mode
    if args.install:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from installer.scripts.install import SIDInstaller
        installer = SIDInstaller()
        installer.run()
        return

    # Setup paths
    SID_ROOT = Path(__file__).parent.parent
    sys.path.insert(0, str(SID_ROOT / "src"))

    # Handle boot mode
    if args.boot:
        from system.init.boot import BootManager
        boot = BootManager()
        boot.boot()

    # Initialize theme
    from terminal.theme.manager import ThemeManager
    theme_manager = ThemeManager()
    if args.theme:
        theme_manager.set_theme(args.theme)

    # Initialize AI (the heart of SID)
    ai = None
    if not args.no_ai:
        print("\033[2m[SID] Initializing AI engine...\033[0m", end=" ", flush=True)
        try:
            from ai.engine.orchestrator import AIOrchestrator
            config_path = args.config or str(SID_ROOT / "config/ai.json")
            ai = AIOrchestrator(config_path)
            
            # Apply RAM tier if specified
            if args.ram_tier and ai:
                ai.set_ram_tier(args.ram_tier)
            
            # Initialize memory
            from memory import MemorySystem
            ai.memory_system = MemorySystem("/var/lib/sid/memory")
            
            print("\033[32m✓\033[0m")
        except Exception as e:
            print(f"\033[31m✖ ({e})\033[0m")

    # Initialize tools
    tools = None
    media_player = None
    offline_storage = None
    browser_fs = None

    if ai:
        from tools import ToolSuite
        tools = ToolSuite(ai)
        
        # Initialize media player
        try:
            from tools.media_player import MediaPlayer
            media_player = MediaPlayer(ai)
            ai.media_player = media_player
        except Exception as e:
            pass

        # Initialize offline storage
        try:
            from tools.offline_storage import OfflineStorage
            offline_storage = OfflineStorage("/var/lib/sid/offline")
            ai.offline_storage = offline_storage
        except Exception as e:
            pass

        # Initialize browser-based file explorer
        try:
            from tools.browser_fs import BrowserFileExplorer
            browser_fs = BrowserFileExplorer(port=2025, root="/")
            ai.browser_fs = browser_fs
        except Exception as e:
            pass

        # Initialize offline cache (auto-switching)
        offline_cache = None
        try:
            from tools.offline_cache import OfflineCache
            offline_cache = OfflineCache()
            print("\033[2m  [SID] Offline cache ready\033[0m")
        except Exception as e:
            pass

        # Initialize image tools
        image_tools = None
        try:
            from tools.image_tools import ImageTools
            image_tools = ImageTools(ai)
            print("\033[2m  [SID] Image tools ready\033[0m")
        except Exception as e:
            pass

        # Initialize settings manager
        settings_mgr = None
        try:
            from tools.settings import SettingsManager
            settings_mgr = SettingsManager()
        except Exception as e:
            pass

        # Initialize agent system (Hermes-inspired)
        agent_system = None
        try:
            from agent import AgentSystem
            agent_system = AgentSystem(ai)
            ai.agent_system = agent_system
        except Exception as e:
            pass

    # Initialize voice
    voice = None
    if not args.no_voice:
        print("\033[2m[SID] Initializing voice system...\033[0m", end=" ", flush=True)
        try:
            from voice import VoiceSystem
            voice = VoiceSystem()
            if voice.is_available():
                # Start voice button in background if display available
                if os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY'):
                    try:
                        from terminal.ui.voice_button import VoiceButton
                        vb = VoiceButton(on_text=lambda t: ai.process(t) if ai else None)
                        threading.Thread(target=vb.show, daemon=True).start()
except Exception:
                        pass
                print("\033[32m✓\033[0m")
            else:
                print("\033[33m⚠ (no backends)\033[0m")
        except Exception as e:
            print(f"\033[31m✖ ({e})\033[0m")

    # Initialize hardware monitor
    try:
        from system.hardware.monitor import HardwareMonitor
        hw_monitor = HardwareMonitor()
        hw_monitor.start()
        if ai:
            ai._hardware_context.update(hw_monitor.get_stats())
except Exception:
        hw_monitor = None

    # Start optimizer
    try:
        from system.optimizer.engine import Optimizer
        optimizer = Optimizer(hw_monitor if 'hw_monitor' in dir() else None)
        optimizer.start()
except Exception:
        optimizer = None

    # Quick setup mode
    if args.quick_setup and ai:
        tier = args.quick_setup
        print(f"\033[33m[SID] Running quick setup for {tier.upper()} RAM...\033[0m")
        ai.set_ram_tier(tier)
        # Try to find and use existing model
        try:
            model_path = ai.model_manager.get_model_for_ram(tier)
            if model_path:
                ai.set_local_model(model_path)
                print(f"\033[32m[SID] Using model: {ai.model_manager.current_model_name}\033[0m")
            else:
                print(f"\033[33m[SID] No model found. Run: install quick {tier}\033[0m")
except Exception:
            pass

    # Set signal handler for clean shutdown
    def shutdown(sig, frame):
        print("\n\033[33m[SID] Shutting down...\033[0m")
        if 'hw_monitor' in dir() and hw_monitor:
            hw_monitor.stop()
        if 'optimizer' in dir() and optimizer:
            optimizer.stop()
        if media_player:
            media_player.stop()
        if browser_fs:
            browser_fs.stop()
        if 'vb' in dir():
            try:
                vb.hide()
except Exception:
                pass
        sys.exit(0)
    
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Show boot screen
    if not args.boot:
        print(theme_manager.boot_screen())
        ai_status = f"\033[32mAI Online\033[0m" if ai else "\033[33mAI Disabled\033[0m"
        voice_status = "\033[32mVoice Ready\033[0m" if (voice and voice.is_available()) else "\033[33mNo Voice\033[0m"
        model_status = f"\033[36m{ai.model_manager.current_model_name}\033[0m" if (ai and ai.model_manager and ai.model_manager.current_model_name != "none") else "\033[33mNo Model\033[0m"
        tier_status = f"\033[36m{ai.config.ram_tier.upper()}\033[0m" if ai else ""
        
        print(f"  {ai_status} | {voice_status} | Model: {model_status} {tier_status}")
        print(f"  \033[2mType anything to interact. Say 'help' or 'ai' for AI mode.\033[0m\n")

    # Start shell
    from terminal.shell.sid_shell import SIDShell
    shell = SIDShell(
        ai_orchestrator=ai,
        voice_system=voice,
        tools=tools,
        media_player=media_player,
        offline_storage=offline_storage,
        browser_fs=browser_fs,
    )
    shell.theme_manager = theme_manager
    shell.soul = ai.soul if ai and hasattr(ai, 'soul') else None
    shell.offline_cache = offline_cache if 'offline_cache' in dir() else None
    shell.image_tools = image_tools if 'image_tools' in dir() else None
    shell.settings_mgr = settings_mgr if 'settings_mgr' in dir() else None
    shell.agent_system = agent_system if 'agent_system' in dir() else None
    shell.cmdloop()

if __name__ == "__main__":
    main()
