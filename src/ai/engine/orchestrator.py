"""SID AI Orchestrator - Deeply integrated AI navigation and control system.
The AI is not just another program - it IS the OS interface. Every command
routes through the AI for natural language understanding and execution."""
import os
import json
import time
import hashlib
import threading
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum

class AIMode(Enum):
    OFFLINE = "offline"
    ONLINE = "online"
    HYBRID = "hybrid"
    AUTO = "auto"

@dataclass
class AIConfig:
    """AI engine configuration with memory-optimized defaults."""
    mode: AIMode = AIMode.AUTO
    model_path: str = ""
    router_model_path: str = ""  # Small model for intent classification
    api_key: str = ""
    api_endpoint: str = "https://api.openai.com/v1"
    api_model: str = "gpt-4o-mini"
    context_window: int = 4096  # Reduced for small models
    compression_enabled: bool = True
    memory_enabled: bool = True
    max_tokens: int = 256  # Keep responses short
    temperature: float = 0.7
    top_p: float = 0.9
    system_prompt: str = ""
    model_family: str = "auto"
    router_enabled: bool = True  # Use router model for intent classification
    deep_integration: bool = True  # Route all commands through AI
    memory_optimizer_seed: bool = True  # Use memory-optimized prompts
    auto_detect_ram: bool = True
    ram_tier: str = "4gb"  # Default to 4GB tier
    os_reserve_mb: int = 1024
    swap_models: bool = True  # Swap between router and specialist models

@dataclass
class IntentResult:
    """Result of intent classification."""
    intent: str  # system, file, code, media, web, chat, help, config
    confidence: float
    command: Optional[str] = None
    requires_specialist: bool = False
    specialist_model: str = ""
    tokens_saved: int = 0

from soul import Soul


class AIOrchestrator:
    """Main AI orchestrator - the primary OS interface.
    Every user action is interpreted, routed, and executed through AI."""

    # Memory-optimized seed prompts for different contexts
    MEMORY_SEED_PROMPTS = {
        "general": (
            "You are SID OS. You run on 4GB RAM. Be extremely concise. "
            "Use 1-2 sentences. Prefer showing command output. "
            "Compress your thoughts. User has limited context window."
        ),
        "system": (
            "SID system mode. Execute commands directly. "
            "Return ONLY the command and its output. No explanations."
        ),
        "file": (
            "SID file mode. Show file operations as commands. "
            "Be brief. Use find, ls, cat, grep. Prefer one-liners."
        ),
        "code": (
            "SID code mode. Return ONLY valid code. "
            "No markdown. No explanations. The code will be run directly."
        ),
        "media": (
            "SID media mode. Control playback. "
            "Supported: play <file>, pause, stop, volume <0-100>, next, list."
        ),
        "web": (
            "SID web mode. Search and summarize. "
            "Be concise. Extract key info. Save for offline use."
        ),
        "learning": (
            "SID learning mode. Teach concepts simply. "
            "Use analogies. Include one practical command. Max 3 sentences."
        ),
        "memory": (
            "SID memory mode. Recall, connect, and compress information. "
            "Identify patterns. Suggest what to remember. Be efficient."
        )
    }

    def __init__(self, config_path: str = "/etc/sid/ai.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.model_manager = None
        self.context_compressor = None
        self.memory_system = None
        self.offline_storage = None
        self.media_player = None
        self.browser_fs = None
        self.conversation_history: List[Dict] = []
        self.sessions: Dict[str, List[Dict]] = {}
        self.current_session_id: str = ""
        self.callbacks: Dict[str, List[Callable]] = {}
        self._lock = threading.RLock()
        self._ready = False
        self._router_active = False
        self._current_specialist = ""
        self.soul = None
        self.settings = None
        self._hardware_context = {}
        self._init_components()
        self._init_soul()
        self._auto_detect_hardware()

    def _init_components(self):
        """Initialize AI subcomponents lazily with memory optimization."""
        from ai.engine.model_manager import ModelManager
        from ai.context.compressor import ContextCompressor

        self.model_manager = ModelManager(self.config)
        self.context_compressor = ContextCompressor(
            max_tokens=self.config.context_window,
            compression_ratio=0.5
        )
        self.current_session_id = self._gen_session_id()
        self._init_soul()

    def _init_soul(self):
        """Initialize soul/personality system."""
        try:
            from soul import Soul
            self.soul = Soul("/etc/sid/soul.json")
        except Exception as e:
            print(f"[SID] Soul init: {e}")
            self.soul = None

    def _auto_detect_hardware(self):
        """Auto-detect RAM and configure tier."""
        if not self.config.auto_detect_ram:
            return

        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if "MemTotal" in line:
                        total_kb = int(line.split()[1])
                        total_mb = total_kb // 1024
                        
                        if total_mb < 2048:
                            self.config.ram_tier = "2gb"
                        elif total_mb < 6144:
                            self.config.ram_tier = "4gb"
                        else:
                            self.config.ram_tier = "6gb"
                        
                        # Adjust context window based on RAM
                        if self.config.ram_tier == "2gb":
                            self.config.context_window = 2048
                            self.config.max_tokens = 128
                        elif self.config.ram_tier == "4gb":
                            self.config.context_window = 4096
                            self.config.max_tokens = 256
                        else:  # 6gb+
                            self.config.context_window = 8192
                            self.config.max_tokens = 512
                        
                        self._hardware_context["ram_total_mb"] = total_mb
                        self._hardware_context["ram_tier"] = self.config.ram_tier
                        break
        except:
            pass  # Use defaults

    def _load_config(self) -> AIConfig:
        """Load AI configuration with memory-optimized defaults."""
        default = AIConfig()
        if self.config_path.exists():
            try:
                data = json.loads(self.config_path.read_text())
                for key, val in data.items():
                    if hasattr(default, key):
                        if key == "mode" and isinstance(val, str):
                            setattr(default, key, AIMode(val))
                        else:
                            setattr(default, key, val)
            except Exception as e:
                print(f"[SID] Config load error: {e}")
        return default

    def save_config(self):
        """Save current configuration with memory settings."""
        data = asdict(self.config)
        data['mode'] = self.config.mode.value
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(data, indent=2))

    def set_api_key(self, key: str, endpoint: str = ""):
        """Switch to online mode with API key."""
        self.config.api_key = key
        if endpoint:
            self.config.api_endpoint = endpoint
        self.config.mode = AIMode.ONLINE
        if self.model_manager:
            self.model_manager.set_api_mode(key, endpoint)
        self.save_config()

    def set_local_model(self, model_path: str):
        """Switch to offline mode with local model."""
        self.config.model_path = model_path
        self.config.mode = AIMode.OFFLINE
        if self.model_manager:
            self.model_manager.load_local_model(model_path)
        self.save_config()

    def set_ram_tier(self, tier: str):
        """Manually set RAM tier: 2gb, 4gb, 6gb."""
        if tier in ("2gb", "4gb", "6gb"):
            self.config.ram_tier = tier
            if tier == "2gb":
                self.config.context_window = 2048
                self.config.max_tokens = 128
            elif tier == "4gb":
                self.config.context_window = 4096
                self.config.max_tokens = 256
            else:
                self.config.context_window = 8192
                self.config.max_tokens = 512
            self.save_config()
            return True
        return False

    def _gen_session_id(self) -> str:
        return hashlib.md5(str(time.time()).encode()).hexdigest()[:8]

    def add_callback(self, event: str, callback: Callable):
        """Register event callback."""
        self.callbacks.setdefault(event, []).append(callback)

    def _trigger(self, event: str, **data):
        for cb in self.callbacks.get(event, []):
            try:
                cb(**data)
            except Exception as e:
                print(f"[SID] Callback error: {e}")

    def classify_intent(self, user_input: str) -> IntentResult:
        """Classify user intent using keyword matching.
        Routes user requests to the appropriate subsystem."""
        
        input_lower = user_input.lower().strip()
        
        # Direct command execution: system
        if (input_lower.startswith(('/')) or 
            any(input_lower.startswith(x) for x in 
                ['run ', 'exec ', 'install ', 'update ', 'sys ', 'system ']) or
            any(x in input_lower for x in ['system info', 'show system', 'system status'])):
            return IntentResult("system", 0.95, requires_specialist=False)
        
        # File operations
        if (any(input_lower.startswith(x) for x in 
                ['ls ', 'cd ', 'cat ', 'find ', 'grep ', 'open ', 'edit ', 
                 'create ', 'delete ', 'move ', 'copy ', 'list ', 'show file',
                 'show dir', 'rename ']) or
            any(x in input_lower for x in ['list files', 'show files', 'browse files',
                'file manager', 'file explorer', 'directory'])):
            return IntentResult("file", 0.9, requires_specialist=False)
        
        # Code
        if (any(x in input_lower for x in ['code', 'write ', 'program', 'script', 'function',
                'debug', 'compile', 'snippet']) and 
            any(x in input_lower for x in ['python', 'bash', 'c', 'js', 'shell', 'code',
                'function', 'rust', 'go', 'java', 'perl', 'ruby', 'lua'])):
            return IntentResult("code", 0.85, requires_specialist=True, specialist_model="code")
        
        # Media
        if (any(input_lower.startswith(x) for x in 
                ['play ', 'music ', 'media ', 'radio ', 'stream ', 'volume', 
                 'pause', 'stop', 'next song']) or
            any(x in input_lower for x in ['play music', 'play audio', 'start playing'])):
            return IntentResult("media", 0.9, requires_specialist=False)
        
        # Web/Offline storage
        if (any(x in input_lower for x in 
                ['search web', 'download', 'save page', 'offline', 'wiki ', 'wikipedia',
                 'browse ', 'store ', 'search the ', 'look up', 'find on', 'web search'])):
            return IntentResult("web", 0.85, requires_specialist=False)
        
        # Memory/Recall
        if any(x in input_lower for x in 
               ['remember', 'recall', 'what did', 'earlier', 'memory', 'find that',
                'search memory', 'what was', 'do you remember']):
            return IntentResult("memory", 0.9, requires_specialist=False)
        
        # Config
        if (any(input_lower.startswith(x) for x in 
                ['config ', 'setup ', 'settings', 'theme ', 'model ', 'api ',
                 'change ', 'set ']) or
            any(x in input_lower for x in ['configuration', 'preferences', 'settings'])):
            return IntentResult("config", 0.9, requires_specialist=False)
        
        # Help
        if any(x in input_lower for x in 
               ['help', 'what can', 'commands', 'guide', 'tutorial', 'how do',
                'what do', 'capabilities']):
            return IntentResult("help", 0.95, requires_specialist=False)
        
        # Default: general chat/assistance
        return IntentResult("general", 0.7, requires_specialist=False)

    def process(self, 
                user_input: str,
                session_id: Optional[str] = None,
                context: Optional[Dict] = None,
                force_intent: Optional[str] = None) -> Dict[str, Any]:
        """Process user input through the AI pipeline with intelligent routing.
        
        Architecture:
        1. Intent classification → determines subsystem
        2. Context building → with memory optimization
        3. Compression → maximizes small model capability
        4. Execution → direct command or AI generation
        5. Memory storage → with compression
        6. Response → minimized tokens
        """
        sid = session_id or self.current_session_id
        if sid not in self.sessions:
            self.sessions[sid] = []

        # === STEP 1: Intent Classification ===
        intent = force_intent if force_intent else self.classify_intent(user_input)
        
        # === STEP 2: Direct execution for system commands (faster) ===
        if intent.intent in ("system", "file") and intent.confidence > 0.9:
            result = self._execute_direct(user_input, intent)
            if result.get("direct") and not result.get("error"):
                return result

        # === STEP 3: Build optimized context ===
        system = self._build_optimized_prompt(intent, context or {})
        conversation = self.sessions[sid][-8:]  # Keep last 8 max

        # === STEP 4: Intelligent context compression ===
        if self.config.compression_enabled and len(conversation) > 4:
            compressed = self.context_compressor.compress(conversation)
            conversation = compressed + conversation[-2:]  # Keep only last 2 recent

        messages = [{"role": "system", "content": system}]
        for msg in conversation:
            messages.append(msg)
        messages.append({"role": "user", "content": user_input})

        self._trigger('before_process', input=user_input, intent=intent.intent)

        try:
            # === STEP 5: Route through available model ===
            # Priority: specialist model > router model > API fallback > error
            if self.model_manager.current_model_name != "none":
                # Full model available — use it
                response = self.model_manager.generate(
                    messages=messages,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature if intent.intent != "system" else 0.2,
                    top_p=self.config.top_p
                )
            elif self.model_manager.router_loaded:
                # No specialist model but router is online — use tiny conductor
                response = self._generate_with_router(user_input, intent)
            elif self.config.api_key:
                # API fallback
                response = self.model_manager.generate(
                    messages=messages,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                    top_p=self.config.top_p
                )
            else:
                # No model at all — give helpful message
                response = self._no_model_response(user_input, intent)

            result = {
                "response": response,
                "session_id": sid,
                "timestamp": time.time(),
                "model": self.model_manager.current_model_name,
                "intent": intent.intent,
                "confidence": intent.confidence
            }

            # === STEP 6: Store in conversation ===
            self.sessions[sid].append({"role": "user", "content": user_input})
            self.sessions[sid].append({"role": "assistant", "content": response})

            # === STEP 7: Intelligent memory storage ===
            if self.config.memory_enabled and self.memory_system:
                # Only store meaningful interactions
                if len(user_input) > 15 or intent.intent in ("learning", "code", "memory"):
                    self.memory_system.store(sid, user_input, response)
                elif self.memory_system.working:
                    # Always store in working memory for immediate context
                    self.memory_system.working.add({"user": user_input, "assistant": response})

            self._trigger('after_process', result=result)
            return result

        except Exception as e:
            err = {"error": str(e), "session_id": sid, "intent": intent.intent}
            self._trigger('on_error', error=e)
            return err

    def _execute_direct(self, user_input: str, intent: IntentResult) -> Dict:
        """Execute commands directly for known intents without model inference."""
        try:
            # System commands
            if intent.intent == "system":
                # Strip command prefix
                cmd = user_input
                for prefix in ['run ', 'exec ', '/']:
                    if cmd.startswith(prefix):
                        cmd = cmd[len(prefix):]
                        break
                
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                output = result.stdout.strip() or result.stderr.strip()
                return {
                    "response": output or f"Command executed (exit: {result.returncode})",
                    "direct": True,
                    "exit_code": result.returncode
                }
            
            # File operations
            if intent.intent == "file":
                result = subprocess.run(user_input, shell=True, capture_output=True, text=True, timeout=30)
                output = result.stdout.strip() or result.stderr.strip()
                return {
                    "response": output or f"Done (exit: {result.returncode})",
                    "direct": True,
                    "exit_code": result.returncode
                }
        except subprocess.TimeoutExpired:
            return {"response": "Command timed out", "direct": True, "error": "timeout"}
        except Exception as e:
            return {"response": f"Error: {e}", "direct": True, "error": str(e)}
        
        return {"direct": False}  # Not a direct command

    def _generate_with_router(self, user_input: str, intent: IntentResult) -> str:
        """Generate response using the router model or template fallback.
        Router handles basic navigation, system info, help, and model setup
        when no specialist model is loaded."""
        # Try to use the full pipeline — if router is the active model, generate works
        if self.model_manager.router_loaded and self.model_manager.current_model_name != "none":
            system = self._build_optimized_prompt(intent, {})
            messages = [{"role": "system", "content": system}, {"role": "user", "content": user_input}]
            try:
                response = self.model_manager.generate(messages, max_tokens=128, temperature=0.7, top_p=0.9)
                if response and not response.startswith("Error"):
                    return response
            except:
                pass
        
        # Fallback: templated responses for common intents
        return self._template_response(user_input, intent)

    def _template_response(self, user_input: str, intent: IntentResult) -> str:
        """Template-based fallback when no model is available at all.
        Provides useful functionality without any AI model loaded."""
        templates = {
            "system": "I can run system commands for you. Try: 'show system info', 'list files', 'disk usage'",
            "file": "File operations are available. Try: 'list files in /home', 'show directory'",
            "help": "SID OS Commands:\n  ai <question> - Ask the AI\n  sys <cmd> - Run system command\n  config - Settings\n  models - Manage AI models\n  install quick <tier> - Quick AI setup\n  benchmark - Test hardware\n  help - This message\n\nTo get started with AI, run: models download",
            "config": "Configuration available. Try: 'config set theme vt100', 'config show'",
            "general": "Hi! I'm SID OS. I'm running in basic mode without a full AI model loaded.\n\nTo enable full AI features:\n  1. models download - Download a local model\n  2. config set api_key <key> - Use an API provider\n  3. install quick 4gb - Auto-setup for 4GB RAM\n\nBasic commands still work: help, sys, config, theme, files"
        }
        return templates.get(intent.intent, templates["general"])

    def _no_model_response(self, user_input: str, intent: IntentResult) -> str:
        """Helpful response when no AI model is available."""
        return f"SID OS has no AI model loaded yet.\n\nTo get started:\n  1. Run 'python3 get-sid.py --setup' to use the setup wizard\n  2. Or inside SID: 'models download' to download one\n  3. Or set an API key: 'config set api_key <key>'\n\nBasic commands still work: help, sys info, config, theme"

    def _build_optimized_prompt(self, intent: IntentResult, context: Dict) -> str:
        """Build memory-optimized system prompt based on intent.
        
        This is the KEY optimization: different prompts for different tasks
        reduces cognitive load on small models and saves context tokens.
        """
        # Start with memory-optimized seed
        seed = self.MEMORY_SEED_PROMPTS.get(intent.intent, self.MEMORY_SEED_PROMPTS["general"])
        prompts = [seed]

        # Add hardware awareness (minimal)
        hw = context.get('hardware', self._hardware_context)
        if hw:
            prompts.append(
                f"[SYS] RAM:{hw.get('ram_tier', '4gb')} "
                f"CPU:{hw.get('cpu_usage', 0)}% "
                f"Temp:{hw.get('cpu_temp', 0)}°C"
            )

        # Add memory context (compressed)
        if self.config.memory_enabled and self.memory_system:
            memories = self.memory_system.recall(context.get('user_id', ''), limit=2)
            if memories:
                # Ultra-compressed memory format
                mem_str = "|".join(
                    f"{m.get('type','')}:{str(m.get('content',''))[:80]}"
                    for m in memories
                )
                prompts.append(f"[MEM] {mem_str[:200]}")

        return "\n".join(prompts)

    def process_natural(self, user_input: str, context: Optional[Dict] = None) -> str:
        """Natural language processing - the PRIMARY OS interface.
        Every command, question, or action goes through here.
        This is how users navigate the OS - through conversation."""
        
        intent = self.classify_intent(user_input)
        
        # Route to appropriate tool if available
        if intent.intent == "media" and self.media_player:
            result = self.media_player.ai_control(user_input)
            if result:
                return result
        
        if intent.intent == "web" and self.offline_storage:
            result = self.offline_storage.ai_search(user_input)
            if result:
                return result
        
        # Default AI processing
        result = self.process(user_input, context=context)
        
        if "error" in result:
            return f"[SID] {result['error']}"
        
        # Log token savings for optimization tracking
        if self.config.memory_enabled and self.memory_system:
            self.memory_system.optimize()
        
        return result.get("response", "[SID] No response generated")

    def system_command(self, command: str) -> Dict:
        """Convert natural language to system command."""
        intent = self.classify_intent(command)
        
        # If it's already a command, run directly  
        if intent.intent in ("system", "file") and intent.confidence > 0.9:
            result = self._execute_direct(command, intent)
            if result.get("direct"):
                return result

        # Otherwise use AI to translate
        prompt = (
            f"Convert to Linux command: {command}\n"
            f"Return ONLY the command, one line, no explanation."
        )
        return self.process(prompt, context={"tools_only": True})

    def get_stats(self) -> Dict:
        """Get comprehensive AI engine statistics."""
        stats = {
            "mode": self.config.mode.value,
            "model": self.model_manager.current_model_name if self.model_manager else "none",
            "ram_tier": self.config.ram_tier,
            "intents_processed": len(self.sessions),
            "total_interactions": sum(len(v) for v in self.sessions.values()),
            "memory_enabled": self.config.memory_enabled,
            "compression_enabled": self.config.compression_enabled,
            "context_window": self.config.context_window,
            "max_tokens": self.config.max_tokens,
            "router_enabled": self.config.router_enabled,
            "deep_integration": self.config.deep_integration,
            "memory_optimizer_seed": self.config.memory_optimizer_seed,
            "hardware": self._hardware_context,
            "memory_usage": self.memory_system.stats() if self.memory_system else {},
        }
        if self.model_manager:
            stats["available_models"] = len(self.model_manager.KNOWN_MODELS)
        return stats

    def get_intent_stats(self) -> Dict:
        """Get statistics on intent classification performance."""
        return {
            "router_active": self._router_active,
            "current_specialist": self._current_specialist,
            "available_intents": list(self.MEMORY_SEED_PROMPTS.keys()),
            "ram_tier": self.config.ram_tier,
            "config": {
                "context_window": self.config.context_window,
                "compression": self.config.compression_enabled,
                "memory": self.config.memory_enabled,
                "router": self.config.router_enabled,
            }
        }
