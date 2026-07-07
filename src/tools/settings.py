"""SID Advanced Settings - Complete control over every aspect of the OS.
Advanced users can control: memory, tools, skills, models, context, caching, etc."""
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable

class SettingsManager:
    """Full system settings with categories for advanced users."""

    SETTINGS_PATH = "/etc/sid/settings.json"

    def __init__(self):
        self.settings_path = Path(self.SETTINGS_PATH)
        self.listeners: Dict[str, List[Callable]] = {}
        self._load()

    def _load(self):
        """Load all settings."""
        if self.settings_path.exists():
            try:
                self.data = json.loads(self.settings_path.read_text())
            except:
                self.data = self._defaults()
        else:
            self.data = self._defaults()
            self.save()

    def _defaults(self) -> Dict:
        """Factory defaults - full control for advanced users."""
        return {
            # === AI ENGINE ===
            "ai": {
                "mode": "auto",  # auto, offline, online, hybrid
                "ram_tier": "4gb",  # 2gb, 4gb, 6gb
                "context_window": 4096,
                "max_tokens": 256,
                "temperature": 0.7,
                "top_p": 0.9,
                "compression_enabled": True,
                "compression_ratio": 0.5,
                "compression_strategy": "smart",  # smart, aggressive, minimal
                "router_enabled": True,
                "deep_integration": True,
                "memory_optimizer_seed": True,
                "swap_models": True,
                "offline_first": True,
                "cache_all_responses": False,
            },

            # === MODELS ===
            "models": {
                "primary": "",
                "router": "",
                "specialists": [],
                "api_key": "",
                "api_endpoint": "https://api.openai.com/v1",
                "api_model": "gpt-4o-mini",
                "auto_download": False,
                "download_location": "/sid/models",
                "max_models_in_ram": 1,
                "gguf_parameters": {
                    "n_gpu_layers": 0,
                    "threads": 0,  # 0 = auto
                    "batch_size": 512,
                    "mlock": True,
                    "mmap": False,
                }
            },

            # === MEMORY SYSTEM ===
            "memory": {
                "enabled": True,
                "working_capacity": 50,
                "episodic_retention_days": 30,
                "semantic_enabled": True,
                "auto_compress": True,
                "compress_threshold": 100,  # interactions before compress
                "storage_path": "/var/lib/sid/memory",
                "max_memory_mb": 512,
                "prune_on_boot": False,
                "export_on_shutdown": False,
            },

            # === TOOLS ===
            "tools": {
                "code_assistant": True,
                "file_manager": True,
                "search_engine": True,
                "system_analyzer": True,
                "media_player": True,
                "offline_storage": True,
                "browser_explorer": True,
                "image_tools": True,
                "image_backend": "auto",  # auto, api, imagick, pil
                "web_search_enabled": True,
            },

            # === SKILLS ===
            "skills": {
                "auto_learn": False,
                "skill_directory": "/usr/share/sid/skills",
                "user_skill_directory": os.path.expanduser("~/.sid/skills"),
                "allowed_sources": ["built-in", "path", "url"],
                "max_skills_loaded": 10,
                "verify_signatures": False,
            },

            # === CACHE ===
            "cache": {
                "web_cache_enabled": True,
                "web_cache_max_age_hours": 168,
                "media_cache_enabled": True,
                "media_cache_max_age_hours": 720,
                "auto_preload": False,
                "preload_urls": [],
                "cache_path": "/var/lib/sid/cache",
                "max_cache_mb": 1024,
            },

            # === VOICE ===
            "voice": {
                "stt_enabled": True,
                "stt_backend": "auto",  # auto, whisper, google
                "tts_enabled": True,
                "tts_backend": "auto",  # auto, espeak, piper
                "wake_word": "",
                "voice_button": True,
                "auto_listen_timeout": 5,
                "language": "en-US",
            },

            # === PERSONALITY (SOUL) ===
            "personality": {
                "name": "SID",
                "style": "professional_retro",
                "formality": 0.4,
                "creativity": 0.6,
                "verbosity": 0.3,
                "system_caution": 0.3,
                "proactiveness": 0.5,
                "catchphrase": "Type anything. I understand.",
            },

            # === THEME ===
            "theme": {
                "active": "vt100",
                "font_scale": 1.0,
                "show_boot_logo": True,
                "animation_enabled": True,
                "scrollback_lines": 5000,
            },

            # === SECURITY ===
            "security": {
                "require_confirm_for": ["delete", "format", "install", "shutdown"],
                "sandbox_commands": False,
                "allowed_commands": [],
                "blocked_commands": [],
                "log_all_commands": True,
                "max_command_timeout": 300,
            },

            # === SYSTEM ===
            "system": {
                "auto_optimize": True,
                "optimizer_interval": 60,
                "temp_warn": 70,
                "temp_critical": 85,
                "ram_warn_percent": 75,
                "auto_update": False,
                "check_updates_on_boot": True,
                "default_terminal": "sid-shell",
            },

            # === NETWORK ===
            "network": {
                "auto_detect_proxy": True,
                "proxy": "",
                "dns": "",
                "offline_mode": False,
                "bandwidth_limit_kbps": 0,
            },

            # === BENCHMARK ===
            "benchmark": {
                "last_run": 0,
                "results_path": "/var/lib/sid/benchmark.json",
                "auto_tune": False,
            }
        }

    def save(self):
        """Save settings."""
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        self.data["_meta"] = {
            "saved_at": time.time(),
            "version": "1.2.0",
            "description": "SID Advanced Settings - Full system control"
        }
        self.settings_path.write_text(json.dumps(self.data, indent=2))

    def get(self, category: str, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self.data.get(category, {}).get(key, default)

    def set(self, category: str, key: str, value: Any):
        """Set a setting value."""
        if category not in self.data:
            self.data[category] = {}
        self.data[category][key] = value
        self.save()
        self._notify(category, key, value)

    def get_category(self, category: str) -> Dict:
        """Get entire category of settings."""
        return self.data.get(category, {})

    def list_categories(self) -> List[str]:
        """List all setting categories."""
        return [k for k in self.data.keys() if not k.startswith("_")]

    def reset_category(self, category: str):
        """Reset a category to defaults."""
        defaults = self._defaults()
        if category in defaults:
            self.data[category] = defaults[category]
            self.save()

    def reset_all(self):
        """Reset all settings to factory defaults."""
        self.data = self._defaults()
        self.save()

    def on_change(self, category: str, key: str, callback: Callable):
        """Register a callback for when a setting changes."""
        if category not in self.listeners:
            self.listeners[category] = []
        self.listeners[category].append((key, callback))

    def _notify(self, category: str, key: str, value: Any):
        """Notify listeners of a setting change."""
        for cb_key, callback in self.listeners.get(category, []):
            if cb_key == key or cb_key == "*":
                try:
                    callback(key, value)
                except Exception as e:
                    print(f"[SID Settings] Callback error: {e}")

    def export_config(self, path: str):
        """Export current settings to a file."""
        Path(path).write_text(json.dumps(self.data, indent=2))

    def import_config(self, path: str) -> bool:
        """Import settings from a file."""
        try:
            imported = json.loads(Path(path).read_text())
            if isinstance(imported, dict):
                self.data.update(imported)
                self.save()
                return True
        except Exception as e:
            print(f"[SID Settings] Import error: {e}")
        return False

    def format_for_display(self, category: Optional[str] = None) -> str:
        """Format settings for terminal display."""
        lines = ["═══ SID Advanced Settings ═══", ""]
        
        cats = [category] if category else self.list_categories()
        
        for cat in cats:
            if cat not in self.data:
                continue
            settings = self.data[cat]
            lines.append(f"[{cat.upper()}]")
            for key, value in settings.items():
                if key.startswith("_"):
                    continue
                lines.append(f"  {key}: {value}")
            lines.append("")
        
        return "\n".join(lines)
