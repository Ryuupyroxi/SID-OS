"""SID Shell - AI-First OS Interface with 80s hacking aesthetic.
Every command routes through AI for natural language understanding.
Users navigate the OS primarily through conversation with AI."""
import os
import sys
import time
import json
import cmd
import shlex
import threading
import readline
import subprocess
import signal
from terminal.assistant.controller import AssistantController
from pathlib import Path
from typing import Optional, Dict, List, Callable, Any, Union
from datetime import datetime

# ANSI color constants
C = {
    'G': '\033[32m', 'A': '\033[33m', 'B': '\033[34m', 'P': '\033[35m',
    'C': '\033[36m', 'W': '\033[37m', 'D': '\033[2m', 'BOLD': '\033[1m',
    'RESET': '\033[0m', 'CLR': '\033[H\033[J', 'RED': '\033[31m',
}

class SIDShell(cmd.Cmd):
    """SID Interactive Shell - AI-first OS navigation.
    The shell intercepts all input, routes through AI, and provides
    intelligent responses. Users can type natural language or commands."""

    intro = f"""
{C['G']}╔══════════════════════════════════════════════════╗
║       SID v1.2.0 - SUPER INTELLIGENT DISTRO        ║
║       ═══════════════════════════════════════     ║
║       Type anything - AI will understand          ║
║       Try: "what can you do?" or "show system"   ║
║       Say "help" for commands                     ║
╚══════════════════════════════════════════════════╝{C['RESET']}
"""

    prompt = f"{C['G']}sid⏣{C['RESET']} "

    def __init__(self, ai_orchestrator=None, voice_system=None, tools=None, 
                 media_player=None, offline_storage=None, browser_fs=None):
        super().__init__()
        self.ai = ai_orchestrator
        self.voice = voice_system
        self.tools = tools
        self.media_player = media_player
        self.offline_storage = offline_storage
        self.browser_fs = browser_fs
        self.theme_manager = None
        self._history_file = os.path.expanduser("~/.sid_history")
        self._ai_mode_active = False
        self._auto_route = True  # Automatically route through AI
        self._direct_mode = False  # True = normal shell, False = AI-first
        self._assistant = AssistantController("sid-bot")
        self._assistant_enabled = False
        self._load_history()

    def _load_history(self):
        try:
            readline.read_history_file(self._history_file)
except Exception:
            pass

    def _save_history(self):
        try:
            readline.write_history_file(self._history_file)
except Exception:
            pass

    def precmd(self, line):
        self._save_history()
        return line

    def emptyline(self):
        """Don't repeat last command on empty input."""
        pass

    def onecmd(self, line):
        """Override: Route all input through AI first, then fallback to cmd dispatch."""
        if not line:
            return
        
        line = line.strip()
        
        # Direct commands that bypass AI
        if line.startswith('!') or line.startswith('/'):
            # Force direct shell command: !command or /command
            return self._run_shell(line[1:])
        
        if line.lower() in ('exit', 'quit', 'q'):
            return self.do_exit(line)
        
        if line.lower() == 'clear':
            return self.do_clear(line)

        # AI-First routing: Use default cmd dispatch for known commands
        known_commands = set(self.get_names())
        cmd_name = line.split()[0].lower() if line.split() else ""
        cmd_func = "do_" + cmd_name
        
        if cmd_func in known_commands and cmd_name != 'ai':
            # Known command - execute directly (but wrap with AI context)
            if self._direct_mode:
                return super().onecmd(line)
            else:
                # Run command and enhance with AI
                result = super().onecmd(line)
                return result
        else:
            # Unknown command → route through AI
            if self.ai and self._auto_route:
                return self._ai_process(line)
            else:
                # Fallback to shell
                return self._run_shell(line)

    def _ai_process(self, user_input: str) -> bool:
        """Route input through AI orchestration."""
        if not self.ai:
            print(f"{C['A']}◆ AI engine not loaded. Type 'help' for commands.{C['RESET']}")
            return False

        # Show thinking indicator
        print(f"{C['D']}▸ thinking...{C['RESET']}", end='\r')
        sys.stdout.flush()

        try:
            # Build context from current system state
            context = self._build_current_context()
            
            # Process through AI
            result = self.ai.process(user_input, context=context)
            
            # Clear thinking indicator
            print(" " * 30, end='\r')

            if "error" in result:
                print(f"{C['RED']}✖ {result['error']}{C['RESET']}")
            else:
                response = result.get("response", "")
                intent = result.get("intent", "general")
                
                # Format response based on intent
                if intent == "system":
                    print(f"{C['G']}{response}{C['RESET']}")
                elif intent == "file":
                    print(f"{C['B']}{response}{C['RESET']}")
                elif intent == "code":
                    print(f"{C['P']}{response}{C['RESET']}")
                elif intent == "media":
                    print(f"{C['C']}{response}{C['RESET']}")
                else:
                    print(f"{C['W']}{response}{C['RESET']}")

        except Exception as e:
            print(" " * 30, end='\r')
            print(f"{C['RED']}✖ Error: {e}{C['RESET']}")

        return False

    def _run_shell(self, command: str) -> bool:
        """Execute a shell command and display output."""
        try:
            result = subprocess.run(
                command, shell=True, capture_output=False, timeout=30
            )
        except subprocess.TimeoutExpired:
            print(f"{C['RED']}Command timed out{C['RESET']}")
        except Exception as e:
            print(f"{C['RED']}Error: {e}{C['RESET']}")
        return False

    def _build_current_context(self) -> Dict:
        """Build context from current system state for AI."""
        context = {}
        
        # Get hardware info
        if hasattr(self.ai, '_hardware_context') and self.ai._hardware_context:
            context['hardware'] = self.ai._hardware_context
        
        # Get working directory
        context['cwd'] = os.getcwd()
        
        # Get recent commands
        try:
            history = []
            hlen = readline.get_current_history_length()
            for i in range(max(0, hlen - 5), hlen):
                try:
                    history.append(readline.get_history_item(i))
except Exception:
                    pass
            context['recent_commands'] = history
except Exception:
            pass

        return context

    # ==================== COMMANDS ====================

    def do_ai(self, arg):
        """Enter full AI assistant chat mode.
        Type naturally - AI understands and responds. Type 'exit' to return."""
        if not self.ai:
            print(f"{C['A']}[SID] AI engine not initialized{C['RESET']}")
            return

        self._ai_mode_active = True
        old_prompt = self.prompt
        
        print(f"\n{C['C']}╔══ SID AI ASSISTANT ══╗{C['RESET']}")
        print(f"{C['D']}I'm integrated into every part of the OS.{C['RESET']}")
        print(f"{C['D']}I can: control system • manage files • write code • play media • browse web{C['RESET']}")
        print(f"{C['D']}Type 'exit' to return to shell. Type 'help' for AI commands.{C['RESET']}\n")
        
        self.prompt = f"{C['G']}sid-ai>{C['RESET']} "
        
        while self._ai_mode_active:
            try:
                inp = input(self.prompt).strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not inp:
                continue
            
            if inp.lower() in ('exit', 'quit', 'q', '..'):
                break
            
            # Handle special AI commands
            if inp.startswith('/'):
                self._handle_ai_command(inp[1:])
            else:
                self._ai_process(inp)

        self._ai_mode_active = False
        self.prompt = old_prompt
        print(f"\n{C['D']}Returned to SID shell{C['RESET']}")

    def _handle_ai_command(self, cmd: str):
        """Handle special commands within AI mode."""
        parts = cmd.split(maxsplit=1)
        action = parts[0].lower() if parts else ""
        rest = parts[1] if len(parts) > 1 else ""

        if action in ("model", "m"):
            if self.ai and self.ai.model_manager:
                models = self.ai.model_manager.list_available()
                print(f"\n{C['C']}Available Models:{C['RESET']}")
                for m in models.get("available", []):
                    name = m.name.replace(" ✅", "")
                    print(f"  {C['G']}✓{C['RESET']} {name}")
                for m in models.get("downloadable", []):
                    name = m.name.replace(" ⬇️ (download)", "")
                    print(f"  {C['A']}⬇{C['RESET']} {name}")
                print(f"\n{C['D']}Install: install model <name>{C['RESET']}")
        
        elif action in ("config", "c"):
            if self.ai:
                stats = self.ai.get_stats()
                print(f"\n{C['C']}AI Configuration:{C['RESET']}")
                for k, v in stats.items():
                    if isinstance(v, dict):
                        continue
                    print(f"  {k}: {v}")
        
        elif action in ("memory", "mem"):
            if self.ai and self.ai.memory_system:
                stats = self.ai.memory_system.stats()
                print(f"\n{C['C']}Memory System:{C['RESET']}")
                for k, v in stats.items():
                    print(f"  {k}: {v}")

        elif action == "voice":
            self._handle_voice_input()
        elif action == "profile":
            self._handle_profile()

        elif action == "clear":
            print(C['CLR'], end='')

        elif action in ("help", "h", "?"):
            print(f"\n{C['D']}AI Commands:{C['RESET']}")
            print(f"  {C['G']}/model{C['RESET']}    - Show available AI models")
            print(f"  {C['G']}/config{C['RESET']}   - Show AI configuration")
            print(f"  {C['G']}/memory{C['RESET']}   - Show memory stats")
            print(f"  {C['G']}/voice{C['RESET']}    - Voice input mode")
            print(f"  {C['G']}config set assistant on{C['RESET']}  - Animated terminal mascot")
            print(f"  {C['G']}/clear{C['RESET']}    - Clear screen")
            print(f"  {C['G']}exit{C['RESET']}      - Return to shell\n")
            print(f"  {C['A']}Or just type naturally. I understand commands like:{C['RESET']}")
            print(f"  \"what's my CPU temperature?\"")
            print(f"  \"show files in this directory\"")
            print(f"  \"write a python script to sort files\"")
            print(f"  \"play some music from ~/Music\"")
            print(f"  \"install a new AI model\"")
        else:
            print(f"{C['A']}Unknown AI command: /{action}{C['RESET']}")

    def do_shell(self, arg):
        """Execute a shell command: shell <command>"""
        if not arg:
            print("Usage: shell <command>")
            return
        self._run_shell(arg)

    def do_install(self, arg):
        """Install packages, AI models, or quick setups.
        Usage: install model <name> | install pkg <name> | install quick <2gb|4gb|6gb>"""
        args = shlex.split(arg)
        if not args:
            print("Usage: install model <name> | install pkg <name> | install quick <2gb|4gb|6gb>")
            return

        if args[0] == "model":
            if len(args) > 1:
                self._install_model(args[1])
            else:
                self._list_installable_models()
        elif args[0] == "pkg" and len(args) > 1:
            self._install_package(args[1])
        elif args[0] == "quick" and len(args) > 1:
            self._quick_setup(args[1])
        elif args[0] == "auto":
            self._quick_setup(self.ai.config.ram_tier if self.ai else "4gb")
        else:
            print("Usage: install <model|pkg|quick|auto> [name]")

    def _list_installable_models(self):
        """List models available for download."""
        if not self.ai or not self.ai.model_manager:
            return
        models = self.ai.model_manager.list_available()
        printable = models.get("downloadable", [])
        if not printable:
            print(f"{C['A']}No downloadable models found{C['RESET']}")
            return
        
        print(f"\n{C['C']}Available for download:{C['RESET']}")
        for m in printable:
            name = m.name.replace(" ⬇️ (download)", "")
            print(f"  {C['A']}⬇{C['RESET']} {name:<35} {m.description}")

    def _install_model(self, name: str):
        """Download and install an AI model."""
        if not self.ai or not self.ai.model_manager:
            print(f"{C['RED']}AI engine not available{C['RESET']}")
            return
        
        print(f"{C['A']}Downloading {name}...{C['RESET']}")
        success = self.ai.model_manager.download_model(name)
        if success:
            print(f"{C['G']}✓ Model downloaded! Loading...{C['RESET']}")
            # Auto-load the downloaded model
            for category in self.ai.model_manager.KNOWN_MODELS.values():
                if isinstance(category, list):
                    for m in category:
                        if name.lower() in m.name.lower() and m.path:
                            self.ai.set_local_model(m.path)
                            return
        else:
            print(f"{C['RED']}Download failed. Try a different model or check your connection.{C['RESET']}")

    def _install_package(self, name: str):
        """Install a system package."""
        if not name:
            print("Package name required")
            return
        print(f"{C['A']}Installing {name}...{C['RESET']}")
        
        # Try apt, apk, or pip
        for pkg_manager, install_cmd in [
            ('apt-get', ['apt-get', 'install', '-y', name]),
            ('apk', ['apk', 'add', name]),
            ('pip3', ['pip3', 'install', name]),
        ]:
            try:
                result = subprocess.run(
                    install_cmd, capture_output=True, timeout=120
                )
                if result.returncode == 0:
                    print(f"{C['G']}✓ {name} installed via {pkg_manager}{C['RESET']}")
                    return
except Exception:
                continue
        
        print(f"{C['RED']}Failed to install {name}. Try a different package name.{C['RESET']}")

    def _quick_setup(self, tier: str = "4gb"):
        """Quick setup for a specific RAM tier - downloads and configures everything."""
        if not self.ai:
            print(f"{C['RED']}AI engine not available{C['RESET']}")
            return

        if tier not in ("2gb", "4gb", "6gb"):
            tier = "4gb"

        tier_names = {"2gb": "2GB (Ultra Light)", "4gb": "4GB (Default)", "6gb": "6GB (Power User)"}
        print(f"\n{C['C']}═══ SID Quick Setup: {tier_names[tier]} ═══{C['RESET']}\n")

        # Load the setup config from registry
        setup_config_path = Path("config/models/registry.json")
        if setup_config_path.exists():
            registry = json.loads(setup_config_path.read_text())
            setup = registry.get("quick_setups", {}).get(f"{tier}_plugandplay", {})
            
            if setup:
                print(f"{C['A']}This will set up: {setup.get('features', '')}{C['RESET']}")
                print(f"{C['A']}Estimated download: {setup.get('total_disk_mb', 0)}MB{C['RESET']}")
                print()
                
                # Set RAM tier
                self.ai.set_ram_tier(tier)
                
                # Download router model
                router = setup.get("router", "")
                if router:
                    print(f"{C['D']}Downloading router model...{C['RESET']}")
                    self.ai.model_manager.download_model(router)

                # Download primary model
                primary = setup.get("primary", "")
                if primary:
                    print(f"{C['D']}Downloading primary model...{C['RESET']}")
                    self.ai.model_manager.download_model(primary)

                # Download specialty models
                for spec in setup.get("specialty", []):
                    print(f"{C['D']}Downloading specialist: {spec}...{C['RESET']}")
                    self.ai.model_manager.download_model(spec)

                print(f"\n{C['G']}✓ Quick setup complete for {tier_names[tier]}!{C['RESET']}")
                print(f"{C['D']}Type 'ai' to start using SID with your new AI models.{C['RESET']}")
                return

        print(f"{C['A']}No quick setup config found for {tier}. Installing default model...{C['RESET']}")
        self.ai.set_ram_tier(tier)
        models = self.ai.model_manager.get_tier_models(tier)
        if models and models[0].url:
            self.ai.model_manager.download_model(models[0].name)

    def do_models(self, arg):
        """List available AI models for your RAM tier."""
        if not self.ai or not self.ai.model_manager:
            print(f"{C['A']}AI engine not available{C['RESET']}")
            return

        tier = self.ai.config.ram_tier if hasattr(self.ai.config, 'ram_tier') else "4gb"
        print(f"\n{C['C']}═══ Models for {tier.upper()} RAM ═══{C['RESET']}")
        
        available = self.ai.model_manager.list_available()
        
        print(f"\n{C['BOLD']}Loaded/Ready:{C['RESET']}")
        for m in available.get("available", []):
            name = m.name.replace(" ✅", "")
            ram = f"[{m.ram_required}MB]"
            ctx = f"ctx:{m.context_length}"
            tier_tag = f"tier:{getattr(m, 'tier', '?')}"
            abli = "🔓" if getattr(m, 'is_abliterated', False) else ""
            spec = f"[{m.specialty}]" if m.specialty != "general" else ""
            print(f"  {C['G']}✓{C['RESET']} {abli} {name:<35} {ram:<8} {ctx:<12} {tier_tag} {spec}")
        
        print(f"\n{C['A']}Available for Download:{C['RESET']}")
        for m in available.get("downloadable", []):
            name = m.name.replace(" ⬇️ (download)", "")
            ram = f"[{m.ram_required}MB]"
            abli = "🔓" if getattr(m, 'is_abliterated', False) else ""
            spec = f"[{m.specialty}]" if m.specialty != "general" else ""
            print(f"  {C['A']}⬇{C['RESET']} {abli} {name:<35} {ram:<8} {spec}")
        
        print(f"\n{C['D']}Commands:{C['RESET']}")
        print(f"  install model <name>       - Download a model")
        print(f"  install quick {tier}        - Quick setup for your tier{C['RESET']}")
        print(f"  model use <name>            - Switch to a model")

    def do_model(self, arg):
        """Manage AI models: use, info, list."""
        args = shlex.split(arg)
        if not args:
            print("Usage: model <use|info|list> [name]")
            return

        cmd = args[0]
        if cmd == "use" and len(args) > 1:
            if self.ai:
                name = args[1]
                # Find the model path
                for category in self.ai.model_manager.KNOWN_MODELS.values():
                    if isinstance(category, list):
                        for m in category:
                            if name.lower() in m.name.lower() and m.path:
                                path = self.ai.model_manager.model_paths.get(m.path)
                                if path:
                                    self.ai.set_local_model(path)
                                    print(f"{C['G']}✓ Switched to: {m.name}{C['RESET']}")
                                    return
                print(f"{C['A']}Model not found. Try 'install model {name}' first.{C['RESET']}")
        elif cmd == "info" and len(args) > 1:
            self._show_model_info(args[1])
        elif cmd == "list":
            self.do_models("")
        else:
            print("Usage: model <use|info|list> [name]")

    def _show_model_info(self, name: str):
        """Show detailed info about a model."""
        if not self.ai or not self.ai.model_manager:
            return
        
        for category in self.ai.model_manager.KNOWN_MODELS.values():
            if isinstance(category, list):
                for m in category:
                    if name.lower() in m.name.lower():
                        print(f"\n{C['C']}Model: {m.name}{C['RESET']}")
                        for field in ['family', 'size', 'ram_required', 'context_length', 
                                     'quantization', 'description', 'specialty', 'tier',
                                     'is_abliterated', 'url']:
                            val = getattr(m, field, "")
                            if val:
                                label = field.replace('_', ' ').title()
                                if isinstance(val, bool):
                                    val = "Yes" if val else "No"
                                print(f"  {label}: {val}")
                        return
        print(f"{C['A']}Model not found: {name}{C['RESET']}")

    def do_config(self, arg):
        """Configure SID: config <set|show|reset|theme> [args].
        
        Key settings:
          set api_key <key> [endpoint]   - Use cloud AI
          set theme <name>               - Change terminal theme
          set ram_tier <2gb|4gb|6gb>     - Set RAM tier
          set model <name>               - Set AI model"""
        args = shlex.split(arg)
        if not args:
            print(f"{C['A']}Usage: config <set|show|reset|theme> [args]{C['RESET']}")
            print(f"  config show              - Show current config")
            print(f"  config set api_key <key> - Use cloud AI API")
            print(f"  config set theme <name>  - Change theme")
            print(f"  config set ram_tier <t>  - Set RAM tier")
            return

        if args[0] == "show":
            if self.ai:
                stats = self.ai.get_stats()
                print(f"\n{C['BOLD']}═══ SID Configuration ═══{C['RESET']}")
                flat_stats = {k: v for k, v in stats.items() if not isinstance(v, dict)}
                for k, v in flat_stats.items():
                    print(f"  {k.replace('_',' ').title()}: {v}")

        elif args[0] == "set" and len(args) >= 2:
            key, value = args[1], " ".join(args[2:]) if len(args) > 2 else ""
            
            if key == "api_key":
                endpoint = ""
                if len(args) > 3:
                    endpoint = args[3]
                if self.ai:
                    self.ai.set_api_key(value, endpoint)
                print(f"{C['G']}✓ API key configured. Using online AI.{C['RESET']}")
            
            elif key == "assistant":
                if value in ("on", "1", "true", "yes"):
                    self._assistant_enabled = True
                    self._assistant.enabled = True
                    self._assistant.state = "idle"
                elif value in ("off", "0", "false", "no"):
                    self._assistant_enabled = False
                    self._assistant.enabled = False
                else:
                    print(f"{C['Y']}Usage: config set assistant on|off{C['RESET']}")
                return True
            elif key == "theme" and self.theme_manager:
                if self.theme_manager.set_theme(value):
                    print(f"{C['G']}✓ Theme set to: {value}{C['RESET']}")
                else:
                    themes = self.theme_manager.list_themes()
                    print(f"{C['A']}Available themes: {', '.join(themes)}{C['RESET']}")
            
            elif key == "ram_tier":
                if self.ai and self.ai.set_ram_tier(value):
                    print(f"{C['G']}✓ RAM tier set to: {value}{C['RESET']}")
                    print(f"{C['D']}Run 'install quick {value}' for recommended model setup{C['RESET']}")
                else:
                    print(f"{C['A']}Use: 2gb, 4gb, or 6gb{C['RESET']}")
            
            elif key == "model":
                if self.ai:
                    self.ai.set_local_model(value)
                print(f"{C['G']}✓ Model set to: {value}{C['RESET']}")
            
            else:
                print(f"{C['A']}Unknown setting: {key}{C['RESET']}")

        elif args[0] == "theme":
            if self.theme_manager:
                if len(args) > 1:
                    if self.theme_manager.set_theme(args[1]):
                        print(f"{C['G']}✓ Theme set to: {args[1]}{C['RESET']}")
                else:
                    themes = self.theme_manager.list_themes()
                    current = self.theme_manager.current
                    print(f"{C['C']}Current theme: {current}{C['RESET']}")
                    print(f"Available: {', '.join(themes)}")

        elif args[0] == "reset":
            if self.ai:
                self.ai.config = self.ai._load_config()
                self.ai.save_config()
                print(f"{C['G']}✓ Config reset to defaults{C['RESET']}")

    def do_memory(self, arg):
        """View and manage AI memory: memory <stats|clear|search <query>>"""
        if not self.ai or not self.ai.memory_system:
            print(f"{C['A']}Memory system not available{C['RESET']}")
            return

        args = shlex.split(arg)
        
        if not args or args[0] == "stats":
            stats = self.ai.memory_system.stats()
            print(f"\n{C['BOLD']}═══ Memory Stats ═══{C['RESET']}")
            for k, v in stats.items():
                print(f"  {k.replace('_',' ').title()}: {v}")
        
        elif args[0] == "clear":
            if self.ai.memory_system.working:
                self.ai.memory_system.working.clear()
            print(f"{C['G']}✓ Working memory cleared{C['RESET']}")
        
        elif args[0] == "optimize":
            if self.ai.memory_system:
                self.ai.memory_system.optimize()
            print(f"{C['G']}✓ Memory optimized{C['RESET']}")
        
        elif args[0] == "search" and len(args) > 1:
            query = " ".join(args[1:])
            results = self.ai.memory_system.search(query)
            if results:
                print(f"\n{C['C']}Memory results for '{query}':{C['RESET']}")
                for r in results[:5]:
                    print(f"  {r}")
            else:
                print(f"{C['A']}No memories found for: {query}{C['RESET']}")

    def do_sys(self, arg):
        """System information and management.
        Usage: sys <info|temp|disk|mem|processes|optimize|update>"""
        args = shlex.split(arg)
        cmd = args[0] if args else "info"

        if cmd == "info":
            self._show_system_info()
        elif cmd == "temp":
            self._show_temperature()
        elif cmd == "disk":
            self._show_disk()
        elif cmd == "mem":
            self._show_memory()
        elif cmd == "processes":
            self._show_processes()
        elif cmd == "optimize":
            self._optimize_system()
        elif cmd == "update":
            self._update_system()
        else:
            # Route unknown sys commands through AI
            if self.ai:
                self._ai_process(f"system {arg}")

    def _show_system_info(self):
        print(f"\n{C['BOLD']}═══ SID SYSTEM ═══{C['RESET']}")
        try:
            cpu = subprocess.run(
                ["sh", "-c", "lscpu | grep 'Model name' | head -1 | cut -d: -f2- | xargs"],
                capture_output=True, text=True, timeout=5
            ).stdout.strip() or "Unknown"
            
            mem = subprocess.run(
                ["sh", "-c", "free -h | grep Mem | awk '{print $3\"/\"$2}'"],
                capture_output=True, text=True, timeout=5
            ).stdout.strip() or "Unknown"

            uptime = subprocess.run(["uptime", "-p"], capture_output=True, text=True).stdout.strip()
            kernel = subprocess.run(["uname", "-r"], capture_output=True, text=True).stdout.strip()
            
            # AI stats if available
            ai_stats = ""
            if self.ai:
                s = self.ai.get_stats()
                ai_stats = f"  AI: {s.get('mode','?')} | {s.get('model','none')} | {s.get('ram_tier','?')} RAM | {s.get('total_interactions',0)} intents"

            print(f"  CPU:    {cpu}")
            print(f"  RAM:    {mem}")
            print(f"  Kernel: {kernel}")
            print(f"  Uptime: {uptime}")
            print(f"  Shell:  SID v1.2.0 | AI-First Mode")
            asst = "ON" if self._assistant_enabled else "OFF"
            print(f"  Mascot: {asst} (config set assistant on|off)")
            if ai_stats:
                print(f"  {C['D']}{ai_stats}{C['RESET']}")
        except Exception as e:
            print(f"  Error: {e}")

    def _show_temperature(self):
        try:
            temp = subprocess.run(
                ["sh", "-c", "cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null | head -1"],
                capture_output=True, text=True, timeout=5
            ).stdout.strip()
            if temp:
                c = int(temp) / 1000
                bar = "█" * int(c / 10) + "░" * (10 - int(c / 10))
                color = C['G'] if c < 60 else (C['A'] if c < 80 else C['RED'])
                print(f"  CPU Temp: {color}{c:.1f}°C {bar}{C['RESET']}")
            else:
                print(f"  {C['A']}Temperature: N/A (no sensors){C['RESET']}")
except Exception:
            print(f"  {C['A']}Temperature: N/A{C['RESET']}")

    def _show_memory(self):
        try:
            result = subprocess.run(
                ["sh", "-c", "free -m | grep Mem | awk '{print $2,$3,$4}'"],
                capture_output=True, text=True, timeout=5
            ).stdout.strip()
            if result:
                parts = result.split()
                total, used, free = int(parts[0]), int(parts[1]), int(parts[2])
                pct = (used / max(total, 1)) * 100
                
                bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
                color = C['G'] if pct < 70 else (C['A'] if pct < 85 else C['RED'])
                print(f"  RAM:  {color}{pct:.0f}% {bar}{C['RESET']}  ({used}MB/{total}MB)")
                
                # Show AI model RAM if available
                if self.ai and self.ai.model_manager and self.ai.model_manager.current_model_name:
                    for category in self.ai.model_manager.KNOWN_MODELS.values():
                        if isinstance(category, list):
                            for m in category:
                                if m.name and m.name in self.ai.model_manager.current_model_name:
                                    print(f"  {C['D']}AI Model: {m.name} ({m.ram_required}MB RAM){C['RESET']}")
                                    break
except Exception:
            subprocess.run(["free", "-h"])

    def _show_disk(self):
        try:
            subprocess.run(["df", "-h", "/", "--output=source,size,used,avail,pcent,target"], 
                         capture_output=False)
except Exception:
            subprocess.run(["df", "-h", "/"])

    def _show_processes(self):
        try:
            subprocess.run(["ps", "aux", "--sort=-%mem", "|", "head", "-15"])
except Exception:
            subprocess.run(["ps", "aux", "|", "head", "-15"])

    def _optimize_system(self):
        """Run system optimization (free memory, clean temp, adjust swappiness)."""
        print(f"{C['A']}Optimizing system...{C['RESET']}")
        
        # Clear page cache
        try:
            with open("/proc/sys/vm/drop_caches", "w") as f:
                f.write("3")
            print(f"  {C['G']}✓{C['RESET']} Memory caches cleared")
except Exception:
            pass
        
        # Clean temp files
        try:
            subprocess.run(["rm", "-rf", "/tmp/*"], capture_output=True)
            print(f"  {C['G']}✓{C['RESET']} Temp files cleaned")
except Exception:
            pass
        
        # Optimize AI memory
        if self.ai and self.ai.memory_system:
            self.ai.memory_system.optimize()
            print(f"  {C['G']}✓{C['RESET']} AI memory optimized")
        
        print(f"{C['G']}✓ System optimized{C['RESET']}")

    def _update_system(self):
        print(f"{C['A']}Checking for updates...{C['RESET']}")
        try:
            subprocess.run(["apt-get", "update"], capture_output=False, timeout=120)
            subprocess.run(["apt-get", "upgrade", "-y", "--quiet=2"], capture_output=True, timeout=300)
            print(f"{C['G']}✓ System updated{C['RESET']}")
except Exception:
            try:
                subprocess.run(["apk", "update"], capture_output=False, timeout=60)
                print(f"{C['G']}✓ System updated{C['RESET']}")
except Exception:
                print(f"{C['A']}No package manager found for updates{C['RESET']}")

    def do_help(self, arg):
        """Show help information."""
        if arg:
            super().do_help(arg)
        else:
            print(f"""
{C['BOLD']}╔══════════════════════════════════════════════╗
║         SID - AI-First OS Interface        ║
╚══════════════════════════════════════════════╝{C['RESET']}

{C['C']}HOW TO USE:{C['RESET']}
  {C['D']}Just type naturally! The AI understands what you want.{C['RESET']}
  {C['D']}Examples:{C['RESET']}
    "show system info"     - View system status
    "what files are here?" - List directory contents
    "install AI model"     - Set up AI capabilities
    "search memory for ..." - Recall past interactions
    "generate an image"    - AI image generation
    "learn a new skill"    - Dynamic skill acquisition

{C['C']}COMMANDS (type 'ai' for full AI mode):{C['RESET']}
  {C['G']}ai{C['RESET']}              - Enter full AI chat mode
  {C['G']}install{C['RESET']}         - Install models/packages/quick setup
  {C['G']}models{C['RESET']}          - List available AI models
  {C['G']}model{C['RESET']}           - Manage AI models
  {C['G']}config{C['RESET']}          - Configure SID (API key, theme, RAM)
  {C['G']}sys{C['RESET']}             - System info and management
  {C['G']}memory{C['RESET']}          - View/manage AI memory
  {C['G']}play{C['RESET']}            - Media player controls
  {C['G']}browse{C['RESET']}          - Open browser file explorer
  {C['G']}web{C['RESET']}             - Download and store web content
  {C['G']}voice{C['RESET']}           - Voice input mode
  {C['G']}!command{C['RESET']}         - Force shell command execution
  {C['G']}skills{C['RESET']}          - Manage AI skills (list/learn/execute)
  {C['G']}image{C['RESET']}           - Generate and edit images
  {C['G']}soul{C['RESET']}            - View/configure SID personality
  {C['G']}settings{C['RESET']}        - Advanced system settings
  {C['G']}cache{C['RESET']}           - Manage offline cache
  {C['G']}benchmark{C['RESET']}       - Run hardware benchmark
  {C['G']}exit{C['RESET']}            - Exit SID
""")

    def do_play(self, arg):
        """Control media playback: play <file/dir> | pause | stop | volume <0-100> | next"""
        if not self.media_player:
            print(f"{C['A']}Media player not available{C['RESET']}")
            return

        args = shlex.split(arg)
        if not args:
            # Show current status
            status = self.media_player.status()
            print(f"\n{C['C']}═══ Media Player ═══{C['RESET']}")
            if status['playing']:
                print(f"  Playing: {status['current']}")
                print(f"  Volume:  {status['volume']}")
                if status['paused']:
                    print(f"  Status:  ⏸ Paused")
                else:
                    print(f"  Status:  ▶ Playing")
            else:
                print(f"  Status: ⏹ Stopped")
            print(f"  Queue:   {status['queue_length']} items")
            print(f"  Backend: {status['backend']}")
            return

        cmd = args[0].lower()
        if cmd in ("stop", "s"):
            self.media_player.stop()
            print(f"{C['A']}⏹ Stopped{C['RESET']}")
        elif cmd in ("pause", "p"):
            self.media_player.pause()
            print(f"{C['A']}⏯ Pause toggled{C['RESET']}")
        elif cmd in ("volume", "vol"):
            vol = int(args[1]) if len(args) > 1 else 80
            self.media_player.volume(vol)
            print(f"{C['G']}Volume: {vol}{C['RESET']}")
        elif cmd in ("next", "n"):
            result = self.media_player.queue_next()
            print(f"{C['G']}{result}{C['RESET']}")
        elif cmd in ("scan", "list"):
            path = args[1] if len(args) > 1 else "."
            files = self.media_player.scan_directory(path)
            if files:
                print(f"\n{C['C']}Media files in {path}:{C['RESET']}")
                for f in files:
                    print(f"  {'🎵' if f['type']=='audio' else '🎬'} {f['name']}")
            else:
                print(f"{C['A']}No media files found in {path}{C['RESET']}")
        else:
            # Try to play the path
            path = arg
            result = self.media_player.play(path)
            if "error" in result:
                print(f"{C['RED']}{result['error']}{C['RESET']}")
            else:
                print(f"{C['G']}▶ Playing: {path}{C['RESET']}")

    def do_browse(self, arg):
        """Open browser-based file explorer.
        Usage: browse [port] [root_dir]"""
        if not self.browser_fs:
            print(f"{C['A']}File browser not available. Starting...{C['RESET']}")
            from ...tools.browser_fs import BrowserFileExplorer
            self.browser_fs = BrowserFileExplorer(port=2025, root="/")

        args = shlex.split(arg)
        port = int(args[0]) if args and args[0].isdigit() else 2025
        root = args[1] if len(args) > 1 else "/"

        result = self.browser_fs.start()
        if "error" in result:
            print(f"{C['RED']}{result['error']}{C['RESET']}")
        else:
            url = result.get("url", f"http://localhost:{port}")
            print(f"{C['G']}✓ File Explorer: {url}{C['RESET']}")
            self.browser_fs.open()

    def do_web(self, arg):
        """Store web content offline: web <save|search|list|wiki> <url/query>
        Usage: web save <url>        - Save webpage offline
               web wiki <article>    - Download Wikipedia article
               web search <query>    - Search stored content
               web list              - List stored content"""
        if not self.offline_storage:
            print(f"{C['A']}Offline storage not available{C['RESET']}")
            return

        args = shlex.split(arg)
        if not args:
            print("Usage: web <save|wiki|search|list|stats> [args]")
            return

        cmd = args[0].lower()
        if cmd == "save" and len(args) > 1:
            url = args[1]
            print(f"{C['A']}Saving {url}...{C['RESET']}")
            # Currently saves metadata - full HTML download needs requests/curl
            result = self.offline_storage.store_webpage(url, "", title=url, tags="saved")
            print(f"{C['G']}✓ Saved: {result.get('id', url)}{C['RESET']}")

        elif cmd == "wiki" and len(args) > 1:
            article = " ".join(args[1:])
            print(f"{C['A']}Downloading Wikipedia: {article}...{C['RESET']}")
            result = self.offline_storage.import_wikipedia(article)
            if "error" in result:
                print(f"{C['RED']}{result['error']}{C['RESET']}")
            else:
                print(f"{C['G']}✓ Saved: {result.get('title', article)} ({result.get('length', 0)} chars){C['RESET']}")

        elif cmd == "search" and len(args) > 1:
            query = " ".join(args[1:])
            results = self.offline_storage.search(query)
            if results:
                print(f"\n{C['C']}Offline results for '{query}':{C['RESET']}")
                for r in results[:10]:
                    print(f"  📄 {r.get('title','?')} - {r.get('url','')[:60]}")
            else:
                print(f"{C['A']}Nothing found in offline storage{C['RESET']}")

        elif cmd == "list":
            for content_type in ['webpage', 'wiki', 'webapp']:
                items = self.offline_storage.list_by_type(content_type)
                if items:
                    print(f"\n{C['C']}[{content_type.upper()}]{C['RESET']}")
                    for item in items[:5]:
                        print(f"  {item.get('title','?')} ({item.get('size_bytes',0)//1024}KB)")

        elif cmd == "stats":
            stats = self.offline_storage.stats()
            print(f"\n{C['BOLD']}═══ Offline Storage ═══{C['RESET']}")
            for k, v in stats.items():
                if isinstance(v, dict):
                    print(f"  {k}:")
                    for sk, sv in v.items():
                        print(f"    {sk}: {sv}")
                else:
                    print(f"  {k.replace('_',' ').title()}: {v}")

    def do_voice(self, arg):
        """Activate voice input mode."""
        self._handle_voice_input()

    def _handle_voice_input(self):
        if not self.voice:
            print(f"{C['A']}Voice system unavailable{C['RESET']}")
            return

        print(f"{C['A']}🎤 Listening for 5 seconds... (Ctrl+C to cancel){C['RESET']}")
        try:
            if self.voice.stt.start_stream():
                import time
                time.sleep(5)
                text = self.voice.stt.stop_stream()
                if text and text != "[STT unavailable - install whisper.cpp]":
                    print(f"\n{C['A']}You said: {text}{C['RESET']}")
                    self._ai_process(text)
                else:
                    print(f"\n{C['A']}No speech detected. Install whisper.cpp for voice input.{C['RESET']}")
            else:
                print(f"{C['A']}Voice input requires microphone access. Try recording with arecord.{C['RESET']}")
        except KeyboardInterrupt:
            print(f"\n{C['A']}Voice cancelled{C['RESET']}")
        except Exception as e:
            print(f"{C['RED']}Voice error: {e}{C['RESET']}")

    def do_skills(self, arg):
        """Manage AI skills: skills <list|learn|execute|search> [name]
        Skills are AI capabilities that can be learned dynamically.
        Usage: skills list | learn <name> | execute <name> [params] | search <query>"""
        if not self.agent_system:
            print(f"{C['A']}Agent system not available{C['RESET']}")
            return
        
        args = shlex.split(arg) if arg else []
        if not args or args[0] == "list":
            caps = self.agent_system.get_capabilities()
            print(f"\n{C['C']}═══ Skills & Tools ═══{C['RESET']}")
            for c in caps:
                print(f"  {C['G']}•{C['RESET']} {c}")
            print(f"\n{C['D']}Total: {len(caps)} capabilities{C['RESET']}")
        
        elif args[0] == "learn" and len(args) > 1:
            result = self.agent_system.learn_skill(args[1])
            if result:
                print(f"{C['G']}✓ Learned skill: {args[1]}{C['RESET']}")
            else:
                print(f"{C['A']}Could not learn skill: {args[1]}{C['RESET']}")
        
        elif args[0] == "execute" and len(args) > 1:
            result = self.agent_system.execute_skill(args[1])
            print(f"{C['G']}{result}{C['RESET']}")
        
        elif args[0] == "search" and len(args) > 1:
            query = " ".join(args[1:])
            print(f"{C['A']}Searching for skills matching: {query}{C['RESET']}")
            from config.skills_registry import BUILTIN_SKILLS
            matches = {k: v for k, v in BUILTIN_SKILLS.items() 
                      if query.lower() in k.lower() or query.lower() in v.get('description','').lower()}
            if matches:
                for name, info in matches.items():
                    print(f"  {C['G']}•{C['RESET']} {name}: {info.get('description','')}")
            else:
                print(f"{C['A']}No matching skills found. Try: skills list{C['RESET']}")
        else:
            print(f"{C['A']}Usage: skills <list|learn|execute|search> [args]{C['RESET']}")

    def do_image(self, arg):
        """Generate or edit images: image <generate|edit|describe> [prompt]
        Usage: image generate <prompt> | edit <file> <instruction> | describe <file>
        Requires: API key or local stable-diffusion"""
        if not self.image_tools:
            print(f"{C['A']}Image tools not available (needs API key){C['RESET']}")
            return
        
        args = shlex.split(arg) if arg else []
        if not args:
            backends = self.image_tools.generation_backends if hasattr(self.image_tools, 'generation_backends') else {}
            print(f"\n{C['C']}═══ Image Tools ═══{C['RESET']}")
            for name, available in backends.items():
                if available:
                    print(f"  {C['G']}✓{C['RESET']} {name}")
                else:
                    print(f"  {C['A']}○{C['RESET']} {name} (not configured)")
            print(f"\n{C['D']}Usage: image generate <prompt> | describe <file>{C['RESET']}")
            return
        
        if args[0] == "generate" and len(args) > 1:
            prompt = " ".join(args[1:])
            print(f"{C['A']}Generating image: {prompt}{C['RESET']}")
            result = self.image_tools.generate(prompt)
            print(f"{C['G']}{result}{C['RESET']}")
        
        elif args[0] == "describe" and len(args) > 1:
            result = self.image_tools.describe(args[1])
            print(f"{C['G']}{result}{C['RESET']}")
        
        elif args[0] == "edit" and len(args) > 2:
            result = self.image_tools.edit(args[1], " ".join(args[2:]))
            print(f"{C['G']}{result}{C['RESET']}")
        else:
            print(f"{C['A']}Usage: image <generate|describe|edit> [args]{C['RESET']}")

    def do_soul(self, arg):
        """View or configure SID's personality: soul <show|set|user> [args]
        Usage: soul show | soul set <trait> <value> | soul user <name>
        The soul file is /etc/sid/soul.json"""
        if not self.soul:
            print(f"{C['A']}Soul system not available{C['RESET']}")
            return
        
        args = shlex.split(arg) if arg else ["show"]
        
        if args[0] == "show":
            pd = self.soul.get_personality_text()
            print(f"\n{C['C']}═══ SID Soul ═══{C['RESET']}")
            print(f"  {pd}")
            user = self.soul.get_user()
            if user:
                print(f"\n{C['D']}Current user: {user.username}")
                print(f"  Interactions: {user.interaction_count}")
                print(f"  Skill level: {user.skill_level}")
                print(f"  Achievements: {len(user.achievements)}{C['RESET']}")
        
        elif args[0] == "set" and len(args) > 2:
            success = self.soul.set_personality(**{args[1]: args[2]})
            if success:
                print(f"{C['G']}✓ Soul updated: {args[1]} = {args[2]}{C['RESET']}")
            else:
                print(f"{C['A']}Invalid soul setting: {args[1]}{C['RESET']}")
        
        elif args[0] == "user" and len(args) > 1:
            user = self.soul.get_user(args[1])
            print(f"{C['G']}✓ Switched to user: {user.username}{C['RESET']}")
        
        else:
            print(f"{C['A']}Usage: soul <show|set|user> [args]{C['RESET']}")

    def do_settings(self, arg):
        """Advanced settings control: settings <show|set|reset|category>
        Full control over: memory, tools, skills, models, context, caching
        Usage: settings show | set <key> <value> | reset | <category>"""
        if not self.settings_mgr:
            print(f"{C['A']}Settings manager not available{C['RESET']}")
            return
        
        args = shlex.split(arg) if arg else ["show"]
        
        if args[0] == "show":
            settings = self.settings_mgr.get_all() if hasattr(self.settings_mgr, 'get_all') else self.settings_mgr.data
            print(f"\n{C['C']}═══ Advanced Settings ═══{C['RESET']}")
            if isinstance(settings, dict):
                for category, items in settings.items():
                    print(f"\n{C['BOLD']}[{category.upper()}]{C['RESET']}")
                    if isinstance(items, dict):
                        for k, v in items.items():
                            print(f"  {k}: {v}")
                    else:
                        print(f"  {category}: {items}")
        
        elif args[0] == "set" and len(args) > 2:
            self.settings_mgr.set(args[1], " ".join(args[2:]))
            self.settings_mgr.save()
            print(f"{C['G']}✓ Setting updated: {args[1]}{C['RESET']}")
        
        elif args[0] == "reset":
            self.settings_mgr.reset()
            print(f"{C['G']}✓ Settings reset to defaults{C['RESET']}")
        
        else:
            print(f"{C['A']}Usage: settings <show|set|reset> [args]{C['RESET']}")

    def do_cache(self, arg):
        """Manage offline cache: cache <status|clear|list|stats>
        The cache automatically stores web pages and media for offline use.
        Usage: cache <status|clear|list|stats>"""
        if not self.offline_cache:
            print(f"{C['A']}Offline cache not available{C['RESET']}")
            return
        
        args = shlex.split(arg) if arg else ["status"]
        
        if args[0] in ("status", "stats"):
            stats = self.offline_cache.get_stats() if hasattr(self.offline_cache, 'get_stats') else {}
            if not stats:
                stats = {"hits": 0, "misses": 0, "items": 0, "online": False}
            print(f"\n{C['C']}═══ Offline Cache ═══{C['RESET']}")
            print(f"  Online: {'✓' if stats.get('online', False) else '✗'}")
            print(f"  Cache hits: {stats.get('hits', 0)}")
            print(f"  Cache misses: {stats.get('misses', 0)}")
            print(f"  Cached items: {stats.get('items', 0)}")
        
        elif args[0] == "clear":
            days = int(args[1]) if len(args) > 1 else 0
            self.offline_cache.clear()
            print(f"{C['G']}✓ Cache cleared{C['RESET']}")
        
        elif args[0] == "list":
            items = self.offline_cache.list_cached() if hasattr(self.offline_cache, 'list_cached') else []
            if items:
                print(f"\n{C['C']}Cached items:{C['RESET']}")
                for item in items[:20]:
                    print(f"  📄 {item}")
            else:
                print(f"{C['A']}No cached items{C['RESET']}")
        
        else:
            print(f"{C['A']}Usage: cache <status|clear|list|stats>{C['RESET']}")

    def do_benchmark(self, arg):
        """Run hardware benchmark for AI model recommendations.
        Tests CPU, RAM, and disk to recommend optimal configuration.
        Usage: benchmark [quick|full]"""
        print(f"{C['A']}Running hardware benchmark...{C['RESET']}")
        try:
            from tools.benchmark import HardwareBenchmark
            bench = HardwareBenchmark()
            results = bench.run_all()
            print(f"\n{C['C']}═══ Benchmark Results ═══{C['RESET']}")
            for k, v in results.items():
                if isinstance(v, dict):
                    print(f"\n{C['BOLD']}[{k}]{C['RESET']}")
                    for sk, sv in v.items():
                        print(f"  {sk}: {sv}")
                else:
                    print(f"  {k}: {v}")
        except Exception as e:
            print(f"{C['RED']}Benchmark error: {e}{C['RESET']}")

    def do_speak(self, arg):
        """Convert text to speech: speak <text>"""
        if not arg:
            print("Usage: speak <text>")
            return
        if self.voice:
            self.voice.speak(arg)
        else:
            print(f"🔊 {arg}")

    def do_neofetch(self, arg):
        """Display SID logo and system info."""
        print(f"""
{C['G']}        ███████╗██╗██████╗ {C['RESET']}
{C['G']}        ██╔════╝██║██╔══██╗{C['RESET']}
{C['G']}        ███████╗██║██║  ██║{C['RESET']}
{C['G']}        ╚════██║██║██║  ██║{C['RESET']}
{C['G']}        ███████║██║██████╔╝{C['RESET']}
{C['G']}        ╚══════╝╚═╝╚═════╝ {C['RESET']}
{C['A']}   SUPER INTELLIGENT DISTRO{C['RESET']}
        """)
        self._show_system_info()

    def do_clear(self, arg):
        """Clear the terminal screen."""
        print(C['CLR'], end='')

    def do_exit(self, arg):
        """Exit SID OS."""
        print(f"\n{C['A']}Shutting down SID...{C['RESET']}")
        self._save_history()
        
        # Cleanup subsystems
        if self.media_player:
            self.media_player.stop()
        if self.browser_fs:
            self.browser_fs.stop()
        
        return True

    def do_EOF(self, arg):
        return self.do_exit(arg)

    def do_debug(self, arg):
        """Show debug information about the AI system."""
        if not self.ai:
            print(f"{C['A']}AI engine not available{C['RESET']}")
            return

        stats = self.ai.get_stats()
        intent_stats = self.ai.get_intent_stats()
        
        print(f"\n{C['BOLD']}═══ SID Debug Information ═══{C['RESET']}")
        print(f"\n{C['C']}AI Engine:{C['RESET']}")
        for k, v in stats.items():
            if isinstance(v, dict):
                print(f"  {k}:")
                for sk, sv in v.items():
                    print(f"    {sk}: {sv}")
            else:
                print(f"  {k}: {v}")
        
        print(f"\n{C['C']}Intent System:{C['RESET']}")
        for k, v in intent_stats.items():
            if isinstance(v, dict):
                print(f"  {k}:")
                for sk, sv in v.items():
                    print(f"    {sk}: {sv}")
            else:
                print(f"  {k}: {v}")

    # Default handler
    def default(self, line):
        """Handle anything that falls through - route through AI."""
        if self.ai and self._auto_route:
            self._ai_process(line)
        else:
            self._run_shell(line)

    # Convenience aliases
    do_q = do_exit
    do_quit = do_exit
    do_h = do_help
    do_help_question = do_help
    def do_question_mark(self, arg):
        """Show help. (? alias)"""
        return self.do_help(arg)
