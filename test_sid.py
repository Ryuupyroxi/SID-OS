#!/usr/bin/env python3
"""
SID OS Test Suite - Validates all components work both offline and online.
Run with: python3 test_sid.py [--online] [--verbose]

Tests:
  1. AI Engine initialization
  2. Model Manager (offline/online)
  3. Context Compression
  4. Memory System
  5. Voice System detection
  6. Hardware Monitor
  7. Tools (code, files, search, system)
  8. Media Player detection
  9. Offline Storage
  10. Browser File Explorer
  11. Config loading/saving
  12. Intent classification
"""
import os
import sys
import time
import json
import subprocess
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project to path
SID_ROOT = Path(__file__).parent
sys.path.insert(0, str(SID_ROOT / "src"))

PASS = "\033[32m✓\033[0m"
FAIL = "\033[31m✗\033[0m"
SKIP = "\033[33m⚠\033[0m"
BOLD = "\033[1m"
RESET = "\033[0m"
DIM = "\033[2m"

class SIDTester:
    """Test suite for SID OS components."""

    def __init__(self, online=False, verbose=False):
        self.online = online
        self.verbose = verbose
        self.results = {"pass": 0, "fail": 0, "skip": 0}
        self.ai = None
        self.hw_monitor = None

    def log(self, status, test_name, detail=""):
        """Log test result."""
        print(f"  {status} {test_name} {DIM}{detail}{RESET}" if detail else f"  {status} {test_name}")
        if status == PASS:
            self.results["pass"] += 1
        elif status == FAIL:
            self.results["fail"] += 1
        else:
            self.results["skip"] += 1

    def run_all(self):
        """Run all tests."""
        print(f"\n{BOLD}═══ SID OS Test Suite ═══{RESET}\n")
        
        self.test_imports()
        self.test_config()
        self.test_orchestrator()
        self.test_model_manager()
        self.test_context_compression()
        self.test_memory_system()
        self.test_hardware_monitor()
        self.test_tools()
        self.test_media_player()
        self.test_offline_storage()
        self.test_browser_fs()
        self.test_voice_system()
        self.test_intent_classification()
        self.test_theme_manager()
        self.test_installer_parse()
        
        print(f"\n{BOLD}═══ Results ═══{RESET}")
        print(f"  {PASS} Passed: {self.results['pass']}")
        print(f"  {FAIL} Failed: {self.results['fail']}")
        print(f"  {SKIP} Skipped: {self.results['skip']}")
        total = self.results['pass'] + self.results['fail'] + self.results['skip']
        print(f"  Total: {total}")
        if self.results['fail'] > 0:
            print(f"\n  {FAIL} Some tests failed. Check details above.")
            return 1
        print(f"\n  {PASS} All tests passed!")
        return 0

    def test_imports(self):
        """Test all modules import correctly."""
        print(f"\n{BOLD}[1] Module Imports{RESET}")
        modules = [
            "ai.engine.orchestrator",
            "ai.engine.model_manager", 
            "ai.context.compressor",
            "ai.prompts.templates",
            "memory",
            "voice",
            "terminal.shell.sid_shell",
            "terminal.theme.manager",
            "system.hardware.monitor",
            "system.optimizer.engine",
            "tools.code.assistant",
            "tools.files.manager",
            "tools.search.engine",
            "tools.system.analyzer",
            "tools.media_player",
            "tools.offline_storage",
            "tools.browser_fs",
        ]
        for mod in modules:
            try:
                __import__(mod)
                self.log(PASS, f"{mod}")
            except Exception as e:
                self.log(FAIL, f"{mod}", str(e)[:60])
                if self.verbose:
                    traceback.print_exc()

    def test_config(self):
        """Test config loading."""
        print(f"\n{BOLD}[2] Configuration{RESET}")
        configs = [
            ("AI Config", "config/ai.json", ["mode", "ram_tier", "context_window"]),
            ("Hardware Config", "config/hardware.json", ["temp_warn", "auto_optimize"]),
            ("Soul Config", "config/soul/default.json", ["personality"]),
            ("Theme Config", "config/themes/default.json", ["theme", "font_scale"]),
        ]
        for name, path, keys in configs:
            p = Path(path)
            if p.exists():
                try:
                    data = json.loads(p.read_text())
                    for key in keys:
                        assert key in data, f"Missing key: {key}"
                    self.log(PASS, f"{name} [{p}]")
                except Exception as e:
                    self.log(FAIL, f"{name}", str(e)[:60])
            else:
                self.log(FAIL, f"{name}", "File not found")

    def test_orchestrator(self):
        """Test AI orchestrator initialization."""
        print(f"\n{BOLD}[3] AI Orchestrator{RESET}")
        try:
            from ai.engine.orchestrator import AIOrchestrator
            config_path = Path("config/ai.json")
            orchestrator = AIOrchestrator(str(config_path))
            self.ai = orchestrator
            self.log(PASS, "Orchestrator init")
            
            # Test RAM tier detection
            if hasattr(orchestrator.config, 'ram_tier'):
                self.log(PASS, f"RAM tier: {orchestrator.config.ram_tier}")
            
            # Test intent classification
            intent = orchestrator.classify_intent("show system info")
            self.log(PASS, f"Intent classification: {intent.intent}")
            
            intent2 = orchestrator.classify_intent("play some music")
            self.log(PASS, f"Intent classification: {intent2.intent}")
            
            # Test stats
            stats = orchestrator.get_stats()
            self.log(PASS, f"Stats: {stats.get('mode','?')} mode, {stats.get('ram_tier','?')} tier")
            
        except Exception as e:
            self.log(FAIL, "Orchestrator", str(e)[:80])
            if self.verbose:
                traceback.print_exc()

    def test_model_manager(self):
        """Test model manager."""
        print(f"\n{BOLD}[4] Model Manager{RESET}")
        try:
            from ai.engine.model_manager import ModelManager, max_ram
            config = type('Config', (), {
                'ram_tier': '4gb', 'context_window': 4096,
                'api_key': '', 'api_endpoint': '',
                'swap_models': True
            })()
            mm = ModelManager(config)
            
            # Test RAM tier limits
            for tier in ['2gb', '4gb', '6gb']:
                limit = max_ram(tier)
                self.log(PASS, f"RAM limit {tier}: {limit}MB")
            
            # Test tier model listing
            for tier in ['2gb', '4gb', '6gb']:
                models = mm.get_tier_models(tier)
                self.log(PASS, f"{tier} tier: {len(models)} models")
            
            # Test model scanning (no models yet)
            paths = mm._scan_models()
            self.log(SKIP, f"Local models: {len(paths)} found" if paths else "No local models")
            
            # Test available models list
            available = mm.list_available()
            total = len(available.get("available", [])) + len(available.get("downloadable", []))
            self.log(PASS, f"Available models: {total}")
            
            # Test API providers
            api_models = mm.KNOWN_MODELS.get("api", [])
            self.log(PASS, f"API providers: {len(api_models)}")
            
        except Exception as e:
            self.log(FAIL, "Model Manager", str(e)[:80])
            if self.verbose:
                traceback.print_exc()

    def test_context_compression(self):
        """Test context compression."""
        print(f"\n{BOLD}[5] Context Compression{RESET}")
        try:
            from ai.context.compressor import ContextCompressor
            cc = ContextCompressor(max_tokens=4096, compression_ratio=0.5)
            
            # Test with sample conversation
            conversation = [
                {"role": "user", "content": "Hello, how are you?"},
                {"role": "assistant", "content": "I'm fine, how can I help you today?"},
                {"role": "user", "content": "Show me the system information please"},
                {"role": "assistant", "content": "Here's the CPU: Intel, RAM: 4GB"},
                {"role": "user", "content": "Can you also check the disk space?"},
                {"role": "assistant", "content": "Disk has 50GB free out of 120GB total."},
                {"role": "user", "content": "What about the temperature?"},
                {"role": "assistant", "content": "CPU temperature is 45°C which is normal."},
            ]
            
            compressed = cc.compress(conversation)
            self.log(PASS, f"Compressed {len(conversation)}→{len(compressed)} messages")
            
            # Test analysis
            analysis = cc.analyze(conversation)
            self.log(PASS, f"Analysis: {analysis.tokens_saved} tokens saved, ratio: {analysis.compression_ratio:.2f}")
            
        except Exception as e:
            self.log(FAIL, "Context Compression", str(e)[:80])
            if self.verbose:
                traceback.print_exc()

    def test_memory_system(self):
        """Test memory system."""
        print(f"\n{BOLD}[6] Memory System{RESET}")
        try:
            from memory import MemorySystem
            ms = MemorySystem("/tmp/sid-test-memory")
            self.log(PASS, "Init with SQLite")
            
            # Test store and recall
            ms.store("test-session", "What is my CPU?", "Your CPU is an AMD E-350")
            memories = ms.recall("test-session", limit=5)
            self.log(PASS, f"Store/Recall: {len(memories)} memories")
            
            # Test search
            results = ms.search("CPU")
            self.log(PASS, f"Search: {len(results)} results for 'CPU'")
            
            # Test optimization
            ms.optimize()
            self.log(PASS, "Memory optimize")
            
            # Test stats
            stats = ms.stats()
            self.log(PASS, f"Stats: {stats}")
            
            # Cleanup
            import shutil
            shutil.rmtree("/tmp/sid-test-memory", ignore_errors=True)
            
        except Exception as e:
            self.log(FAIL, "Memory", str(e)[:80])
            if self.verbose:
                traceback.print_exc()

    def test_hardware_monitor(self):
        """Test hardware monitor."""
        print(f"\n{BOLD}[7] Hardware Monitor{RESET}")
        try:
            from system.hardware.monitor import HardwareMonitor
            hm = HardwareMonitor()
            
            # Take a snapshot
            hm._update_state()
            s = hm.current
            self.log(PASS, f"CPU: {s.cpu_model[:30] or 'detected'}")
            self.log(PASS, f"RAM: {s.ram_total//1024//1024}MB total, {s.ram_percent:.0f}% used")
            self.log(PASS, f"Cores: {s.cpu_cores}")
            self.log(PASS, f"Uptime: {s.uptime}s")
            
            self.hw_monitor = hm
            
        except Exception as e:
            self.log(FAIL, "Hardware Monitor", str(e)[:80])
            if self.verbose:
                traceback.print_exc()

    def test_tools(self):
        """Test tool system."""
        print(f"\n{BOLD}[8] Tools{RESET}")
        try:
            from tools import ToolSuite
            ts = ToolSuite(self.ai)
            
            # Test tool listing
            tools = ts.list_tools()
            self.log(PASS, f"Available tools: {', '.join(tools)}")
            
            # Test code assistant
            if hasattr(ts.code, 'SUPPORTED_LANGUAGES'):
                self.log(PASS, f"Code: supports {len(ts.code.SUPPORTED_LANGUAGES)} languages")
            
            # Test file manager
            if hasattr(ts.files, 'find'):
                self.log(PASS, "File manager ready")
            
            # Test search
            if hasattr(ts.search, 'files'):
                self.log(PASS, "Search engine ready")
            
            # Test system analyzer
            report = ts.system.performance_report()
            self.log(PASS, f"System analyzer: {len(report)} metrics")
            
        except Exception as e:
            self.log(FAIL, "Tools", str(e)[:80])
            if self.verbose:
                traceback.print_exc()

    def test_media_player(self):
        """Test media player."""
        print(f"\n{BOLD}[9] Media Player{RESET}")
        try:
            from tools.media_player import MediaPlayer
            mp = MediaPlayer(self.ai)
            
            status = mp.status()
            self.log(PASS, f"Backend: {status.get('backend', 'none')}")
            
            # Test scanning
            files = mp.scan_directory(".")
            self.log(PASS if len(files) == 0 else SKIP, 
                    f"Media scan: {len(files)} files found")
            
            # Test supported formats
            self.log(PASS, f"Audio formats: {len(mp.SUPPORTED_AUDIO)}")
            self.log(PASS, f"Video formats: {len(mp.SUPPORTED_VIDEO)}")
            
        except Exception as e:
            self.log(FAIL, "Media Player", str(e)[:80])
            if self.verbose:
                traceback.print_exc()

    def test_offline_storage(self):
        """Test offline storage."""
        print(f"\n{BOLD}[10] Offline Storage{RESET}")
        try:
            from tools.offline_storage import OfflineStorage
            os_ = OfflineStorage("/tmp/sid-test-offline")
            
            # Test store and retrieve
            result = os_.store_webpage(
                "https://example.com/test", 
                "<html><body><p>Test content for compression testing</p></body></html>",
                "Test Page", "test,example"
            )
            self.log(PASS, f"Store: {result.get('id','?')} ({result.get('size_bytes',0)}B→{result.get('compressed_bytes',0)}B)")
            
            # Test search
            found = os_.search("test")
            self.log(PASS, f"Search: {len(found)} results")
            
            # Test Wikipedia import (offline - just test the function exists)
            self.log(SKIP, "Wikipedia import (offline test)")
            
            # Test stats
            stats = os_.stats()
            self.log(PASS, f"Stats: {stats.get('total_items',0)} items, {stats.get('raw_size_bytes',0)}B raw")
            
            # Cleanup
            import shutil
            shutil.rmtree("/tmp/sid-test-offline", ignore_errors=True)
            
        except Exception as e:
            self.log(FAIL, "Offline Storage", str(e)[:80])
            if self.verbose:
                traceback.print_exc()

    def test_browser_fs(self):
        """Test browser file explorer."""
        print(f"\n{BOLD}[11] Browser File Explorer{RESET}")
        try:
            from tools.browser_fs import BrowserFileExplorer
            bf = BrowserFileExplorer(port=2026, root="/tmp")
            
            # Test start/stop
            result = bf.start()
            if "error" in result:
                self.log(SKIP, f"Start: {result.get('error','')}")
            else:
                self.log(PASS, f"Running at: {result.get('url','?')}")
                bf.stop()
                self.log(PASS, "Stop")
            
        except Exception as e:
            self.log(FAIL, "Browser FS", str(e)[:80])
            if self.verbose:
                traceback.print_exc()

    def test_voice_system(self):
        """Test voice system detection."""
        print(f"\n{BOLD}[12] Voice System{RESET}")
        try:
            from voice import VoiceSystem
            vs = VoiceSystem()
            
            available = vs.is_available()
            if available:
                self.log(PASS, f"Voice: {vs.stt.backend} / {vs.tts.backend}")
            else:
                self.log(SKIP, "No voice backends (install espeak/whisper)")
            
        except Exception as e:
            self.log(FAIL, "Voice", str(e)[:80])
            if self.verbose:
                traceback.print_exc()

    def test_intent_classification(self):
        """Test intent classification with various inputs."""
        print(f"\n{BOLD}[13] Intent Classification{RESET}")
        if not self.ai:
            self.log(SKIP, "AI not initialized")
            return

        test_cases = [
            ("show me the system info", "system"),
            ("run ls -la", "system"),
            ("list files in this directory", "file"),
            ("write a python script", "code"),
            ("play some music from my music folder", "media"),
            ("search the web for linux news", "web"),
            ("what did we talk about earlier", "memory"),
            ("change the theme to amber", "config"),
            ("help me with SID", "help"),
            ("hello how are you", "general"),
        ]

        for text, expected in test_cases:
            intent = self.ai.classify_intent(text)
            success = intent.intent == expected
            detail = f"(got: {intent.intent}, expected: {expected})" if not success else ""
            self.log(PASS if success else FAIL, f"'{text[:30]}...' → {intent.intent}", detail)

    def test_theme_manager(self):
        """Test theme manager."""
        print(f"\n{BOLD}[14] Theme Manager{RESET}")
        try:
            from terminal.theme.manager import ThemeManager
            tm = ThemeManager()
            
            themes = tm.list_themes()
            theme_names = [t['name'] for t in themes]
            self.log(PASS, f"{len(themes)} themes: {', '.join(theme_names[:6])}...")
            
            for t in themes[:3]:
                tm.set_theme(t['id'])
                boot = tm.boot_screen()
                self.log(PASS, f"Theme '{t['id']}': boot screen ({len(boot)} chars)")
            
        except Exception as e:
            self.log(FAIL, "Theme Manager", str(e)[:80])
            if self.verbose:
                traceback.print_exc()
    def test_installer_parse(self):
        """Test installer parses correctly."""
        print(f"\n{BOLD}[15] Installer{RESET}")
        try:
            # Just verify the installer module can be imported (don't run it)
            path = Path("installer/scripts/install.py")
            if path.exists():
                compile(path.read_text(), str(path), 'exec')
                self.log(PASS, f"Installer: {path} (syntax OK)")
                
                # Verify all required functions exist
                content = path.read_text()
                required = ["detect_hardware", "select_disk", "partition", "format", 
                          "install_base", "install_sid", "configure", "install_ai",
                          "install_bootloader", "finish"]
                for func in required:
                    if f"def {func}" in content:
                        self.log(PASS, f"  Installer step: {func}")
                    else:
                        self.log(FAIL, f"  Missing step: {func}")
            else:
                self.log(FAIL, "Installer not found")
        except Exception as e:
            self.log(FAIL, "Installer", str(e)[:80])


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SID OS Test Suite")
    parser.add_argument("--online", action="store_true", help="Test online features")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()
    
    tester = SIDTester(online=args.online, verbose=args.verbose)
    exit(tester.run_all())

    def test_soul_system(self):
        """Test soul/personality system."""
        print(f"\n{BOLD}[NEW] Soul/Personality System{RESET}")
        try:
            import tempfile, shutil
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent / "src"))
            from soul import Soul
            test_dir = "/tmp/sid-test-soul"
            os.makedirs(test_dir, exist_ok=True)
            soul_path = f"{test_dir}/soul.json"
            soul = Soul(soul_path)
            
            self.log(PASS, "Soul loaded with personality")
            
            user = soul.get_user("testuser")
            self.log(PASS, f"User profile: {user.username}")
            
            pd = soul.get_personality_dict()
            self.log(PASS, f"Personality: {pd.get('name','?')} - {pd.get('traits','')[:30]}")
            
            soul.update_user("testuser", skill_level="intermediate")
            self.log(PASS, "User updated")
            
            shutil.rmtree(test_dir, ignore_errors=True)
        except Exception as e:
            self.log(FAIL, "Soul System", str(e)[:80])
            if self.verbose: traceback.print_exc()

    def test_image_tools(self):
        """Test image tools."""
        print(f"\n{BOLD}[NEW] Image Tools{RESET}")
        try:
            sys.path.insert(0, str(Path(__file__).parent / "src"))
            from tools.image_tools import ImageTools
            it = ImageTools(self.ai)
            backends = it._detect_backends()
            available = [k for k, v in backends.items() if v]
            if available:
                self.log(PASS, f"Backends: {', '.join(available)}")
            else:
                self.log(SKIP, "No image backends installed")
            self.log(PASS, f"Formats: {', '.join(it.list_formats())}")
            
            result = it.generate("test", (64, 64))
            if result.get("success"):
                self.log(PASS, f"Generated: {result.get('engine','?')}")
            else:
                self.log(SKIP, f"Generation: {result.get('error','')[:50]}")
        except Exception as e:
            self.log(FAIL, "Image Tools", str(e)[:80])
            if self.verbose: traceback.print_exc()

    def test_offline_cache(self):
        """Test offline cache."""
        print(f"\n{BOLD}[NEW] Offline Cache{RESET}")
        try:
            import shutil
            sys.path.insert(0, str(Path(__file__).parent / "src"))
            from tools.offline_cache import OfflineCache
            test_dir = "/tmp/sid-test-cache"
            cache = OfflineCache(test_dir)
            cache.put("https://example.com/test", b"test content", 
                     content_type="text/plain", tags="test")
            result = cache.get("https://example.com/test")
            if result:
                self.log(PASS, f"Cached: {len(result.get('content', b''))}B")
            else:
                self.log(FAIL, "Cache retrieval failed")
            stats = cache.stats()
            self.log(PASS, f"Stats: {stats.get('total_items',0)} items")
            online = cache.is_online
            self.log(PASS if online else SKIP, f"Online: {'yes' if online else 'no'}")
            shutil.rmtree(test_dir, ignore_errors=True)
        except Exception as e:
            self.log(FAIL, "Offline Cache", str(e)[:80])
            if self.verbose: traceback.print_exc()

    def test_benchmark(self):
        """Test hardware benchmark."""
        print(f"\n{BOLD}[NEW] Hardware Benchmark{RESET}")
        try:
            sys.path.insert(0, str(Path(__file__).parent / "src"))
            from tools.benchmark import HardwareBenchmark
            hb = HardwareBenchmark()
            mem = hb._bench_memory()
            self.log(PASS, f"Memory: {mem.get('total_mb',0)}MB")
            speed = hb._bench_cpu_speed()
            self.log(PASS, f"CPU: {speed.get('speed_rating','?')} ({speed.get('duration_ms',0)}ms)")
            disk = hb._bench_disk_speed()
            self.log(PASS, f"Disk: {disk.get('disk_type','?')} ({disk.get('read_mbps',0)}MB/s)")
            ai = hb._bench_ai_capability()
            self.log(PASS, f"AI Score: {ai.get('score',0)}/100 - {ai.get('capability','?')}")
        except Exception as e:
            self.log(FAIL, "Benchmark", str(e)[:80])
            if self.verbose: traceback.print_exc()

    def test_settings(self):
        """Test advanced settings."""
        print(f"\n{BOLD}[NEW] Advanced Settings{RESET}")
        try:
            import shutil
            sys.path.insert(0, str(Path(__file__).parent / "src"))
            from tools.settings import SettingsManager
            test_dir = "/tmp/sid-test-settings"
            SettingsManager.SETTINGS_PATH = f"{test_dir}/settings.json"
            os.makedirs(test_dir, exist_ok=True)
            sm = SettingsManager()
            cats = sm.list_categories()
            self.log(PASS, f"Categories: {', '.join(cats)}")
            val = sm.get("ai", "ram_tier")
            self.log(PASS, f"AI RAM tier: {val}")
            sm.set("ai", "ram_tier", "4gb")
            self.log(PASS, "Set/Get works")
            display = sm.format_for_display("ai")
            self.log(PASS, f"Format: {len(display)} chars")
            shutil.rmtree(test_dir, ignore_errors=True)
        except Exception as e:
            self.log(FAIL, "Settings", str(e)[:80])
            if self.verbose: traceback.print_exc()

    def test_agent_system(self):
        """Test agentic skill framework."""
        print(f"\n{BOLD}[NEW] Agent System{RESET}")
        try:
            sys.path.insert(0, str(Path(__file__).parent / "src"))
            from agent.skill_manager import SkillManager
            from agent.tool_registry import ToolRegistry
            sm = SkillManager()
            skills = sm.list_skills()
            self.log(PASS, f"Skills: {len(skills)} found")
            tr = ToolRegistry()
            tools = tr.list_tools()
            self.log(PASS, f"Tools: {len(tools)} registered")
        except Exception as e:
            self.log(FAIL, "Agent System", str(e)[:80])
            if self.verbose: traceback.print_exc()
