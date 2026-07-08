"""SID Model Manager - RAM-aware model loading with router + specialist models.
Supports automatic tier selection, dynamic swapping, and multi-model routing."""
import os
import json
import time
import subprocess
import threading
import urllib.request
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field

@dataclass
class ModelInfo:
    """Information about an available model."""
    name: str
    path: str
    family: str  # llama, phi, gemma, qwen, mistral, codellama, deepseek, router
    size: str  # tiny, small, medium, large, router
    ram_required: int  # MB
    context_length: int
    quantization: str
    description: str = ""
    is_online: bool = False
    api_endpoint: str = ""
    is_router: bool = False
    specialty: str = "general"  # general, coding, creative, reasoning, chat
    is_abliterated: bool = False
    tier: str = "4gb"  # Which RAM tier this model fits
    url: str = ""  # Download URL

class ModelManager:
    """Manages AI model loading with RAM awareness and dynamic swapping."""

    # Comprehensive model catalog with RAM tier awareness
    # Comprehensive model catalog with RAM tier awareness
    # ALL MODELS VERIFIED: URLs tested and confirmed accessible (Qwen official repos)
    KNOWN_MODELS = {
        "router": [
            ModelInfo("Qwen2.5-0.5B-Router", "qwen2.5-0.5b-instruct-q4_k_m.gguf", "qwen", "router", 256, 32768, "Q4_K_M",
                     "Tiny always-on conductor. Basic AI even without a big model loaded.",
                     is_router=True, tier="2gb",
                     url="https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf"),
        ],
        "2gb_tier": [
            ModelInfo("Qwen2.5-1.5B-Instruct", "qwen2.5-1.5b-instruct-q4_k_m.gguf", "qwen", "tiny", 512, 32768, "Q4_K_M",
                     "Good tiny model for 2GB systems. Works with swap.",
                     tier="2gb",
                     url="https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf"),
        ],
        "4gb_tier": [
            ModelInfo("Qwen2.5-3B-Instruct", "qwen2.5-3b-instruct-q4_k_m.gguf", "qwen", "small", 1024, 32768, "Q4_K_M",
                     "★ RECOMMENDED: Best balance for 4GB systems. Strong reasoning.",
                     tier="4gb",
                     url="https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf"),
        ],
        "6gb_tier": [
            ModelInfo("Qwen2.5-7B-Instruct", "qwen2.5-7b-instruct-q2_k.gguf", "qwen", "medium", 2048, 32768, "Q2_K",
                     "7B general model. Fits 6GB at Q2. Strong multilingual, math, coding.",
                     tier="6gb",
                     url="https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q2_k.gguf"),
            ModelInfo("Qwen2.5-Coder-7B-Instruct", "qwen2.5-coder-7b-instruct-q4_k_m.gguf", "qwen", "specialty", 3072, 32768, "Q4_K_M",
                     "Code specialist. Multi-language programming expert.",
                     tier="6gb", specialty="coding",
                     url="https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF/resolve/main/qwen2.5-coder-7b-instruct-q4_k_m.gguf"),
        ],
        "api": [
            ModelInfo("OpenAI GPT-4o-mini", "", "api", "large", 0, 128000, "api", "API: Best small online model", True, "https://api.openai.com/v1"),
            ModelInfo("OpenAI GPT-4o", "", "api", "large", 0, 128000, "api", "API: Full GPT-4o", True, "https://api.openai.com/v1"),
            ModelInfo("Claude 3.5 Haiku", "", "api", "large", 0, 200000, "api", "API: Anthropic fast model", True, "https://api.anthropic.com/v1"),
            ModelInfo("Claude 3.5 Sonnet", "", "api", "large", 0, 200000, "api", "API: Anthropic balanced model", True, "https://api.anthropic.com/v1"),
            ModelInfo("Gemini 1.5 Flash", "", "api", "large", 0, 1000000, "api", "API: Google Flash model", True, "https://generativelanguage.googleapis.com/v1beta"),
            ModelInfo("Gemini 2.0 Flash", "", "api", "large", 0, 1000000, "api", "API: Latest Google Flash", True, "https://generativelanguage.googleapis.com/v1beta"),
            ModelInfo("Groq Llama-3.1-8B", "", "api", "large", 0, 32768, "api", "API: Fast inference via Groq", True, "https://api.groq.com/openai/v1"),
        ]
    }

    def __init__(self, config):
        self.config = config
        self.current_model = None
        self.current_model_name = "none"
        self.router_model = None
        self.router_loaded = False
        self.specialist_model = None
        self.model_paths = self._scan_models()
        self._llama_process = None
        self._llama_python = None
        self._lock = threading.Lock()
        self._api_enabled = bool(config.api_key)
        self._ram_tier = getattr(config, 'ram_tier', '4gb')
        self._swap_enabled = getattr(config, 'swap_models', True)
        self._model_swap_lock = threading.Lock()

    def _scan_models(self) -> Dict[str, str]:
        """Scan standard directories for downloaded models."""
        paths = {}
        search_dirs = [
            "/sid/models",
            "/usr/share/sid/models",
            os.path.expanduser("~/.sid/models"),
            "/models",
            "/var/lib/sid/models",
        ]
        for d in search_dirs:
            p = Path(d)
            if p.exists():
                for f in p.glob("*.gguf"):
                    paths[f.stem] = str(f)
        return paths

    def get_tier_models(self, tier: str) -> List[ModelInfo]:
        """Get models appropriate for a specific RAM tier."""
        tier_map = {
            "2gb": ["2gb_tier"],
            "4gb": ["2gb_tier", "4gb_tier"],
            "6gb": ["2gb_tier", "4gb_tier", "6gb_tier"],
        }
        models = []
        for key in tier_map.get(tier, ["2gb_tier"]):
            models.extend(self.KNOWN_MODELS.get(key, []))
        
        # Filter by RAM requirement
        max_ram = {"2gb": 768, "4gb": 1536, "6gb": 4096}
        limit = max_ram.get(tier, 4096)
        return [m for m in models if m.ram_required <= limit]

    def get_recommended_model(self, tier: str, task: str = "general") -> ModelInfo:
        """Get the best model for a given RAM tier and task."""
        tier_models = self.get_tier_models(tier)
        
        if task == "coding":
            # Find code specialty models
            for m in tier_models:
                if m.specialty == "coding" and m.is_abliterated:
                    return m
        if task == "uncensored":
            for m in tier_models:
                if m.is_abliterated:
                    return m
        
        # Return tier-appropriate model
        tier_order = {"2gb": 0, "4gb": 1, "6gb": 2}
        idx = tier_order.get(tier, 1)
        tier_keys = ["2gb_tier", "4gb_tier", "6gb_tier"][:idx+1]
        
        for key in reversed(tier_keys):
            models = self.KNOWN_MODELS.get(key, [])
            # Prefer abliterated
            for m in models:
                if m.is_abliterated and m.ram_required <= max_ram(tier):
                    return m
            # Fallback to any
            for m in models:
                if m.ram_required <= max_ram(tier):
                    return m
        
        return self.KNOWN_MODELS["2gb_tier"][0]  # Safest fallback

    def load_local_model(self, model_path: str) -> bool:
        """Load a local GGUF model with RAM awareness."""
        with self._lock:
            try:
                if model_path in self.model_paths:
                    model_path = self.model_paths[model_path]

                if not os.path.exists(model_path):
                    print(f"[SID] Model not found: {model_path}")
                    return False

                self._cleanup()
                self.current_model_name = Path(model_path).stem
                
                # Try llama.cpp server first
                llama_server = self._find_llama_server()
                if llama_server:
                    return self._start_llama_server(model_path, llama_server)
                
                # Fallback to Python bindings
                return self._load_python_fallback(model_path)

            except Exception as e:
                print(f"[SID] Model load error: {e}")
                return False

    def load_router_model(self) -> bool:
        """Load the tiny router model (always-on conductor for SID).
        Auto-downloads if not found. The router handles basic AI even
        when no larger model is available."""
        if self.router_loaded:
            return True

        # Scan for an already-downloaded router model
        router_names = ["qwen2.5-0.5b", "0.5b-router", "router"]
        for name, path in self.model_paths.items():
            if any(r in name.lower() for r in router_names):
                self.router_model = path
                self.router_loaded = True
                print(f"[SID] Router model found: {path.name}")
                return True

        # Not found locally — try to auto-download the Qwen2.5-0.5B-Router (smallest, ~468MB)
        print(f"[SID] No router model found. Downloading tiny conductor model (~200MB)...")
        success = self.download_model("Qwen2.5-0.5B-Router")
        if success:
            # Re-scan paths
            self.model_paths = self._scan_models()
            for name, path in self.model_paths.items():
                if any(r in name.lower() for r in router_names):
                    self.router_model = path
                    self.router_loaded = True
                    print(f"[SID] Router conductor online: {path.name}")
                    return True

        print(f"[SID] Router model unavailable. Using keyword-based intent classification.")
        return False

    def swap_to_specialist(self, specialty: str) -> bool:
        """Swap from general model to a specialist model (e.g., for coding)."""
        with self._model_swap_lock:
            if not self._swap_enabled:
                return False
            
            # Find a specialist model
            for tier_key in [f"{self._ram_tier}_tier", "6gb_tier", "4gb_tier", "2gb_tier"]:
                for m in self.KNOWN_MODELS.get(tier_key, []):
                    if m.specialty == specialty and m.path:
                        path = self.model_paths.get(m.path)
                        if path:
                            print(f"[SID] Swapping to specialist: {m.name}")
                            return self.load_local_model(path)
            
            return False

    def _start_llama_server(self, model_path: str, server_bin: str) -> bool:
        """Start llama.cpp server with memory-optimized settings."""
        n_gpu_layers = 0
        
        # Optimize thread count for old hardware
        cpu_count = os.cpu_count() or 2
        threads = max(1, cpu_count - 1) if cpu_count > 1 else 1
        
        # Batch size for old CPUs
        batch_size = 256 if self._ram_tier == "2gb" else 512
        
        cmd = [
            server_bin,
            "-m", model_path,
            "--host", "127.0.0.1",
            "--port", "8787",
            "-c", str(self.config.context_window),
            "--mlock",
            "--no-mmap",
            "-t", str(threads),
            "-b", str(batch_size),
            "--cont-batching",
        ]
        
        # Only add GPU layers if GPU detected
        if self._has_gpu():
            cmd.extend(["-ngl", "99"])
        else:
            cmd.append("-ngl")
            cmd.append("0")

        try:
            self._llama_process = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            # Wait for server to start
            time.sleep(2)
            
            # Verify it started
            try:
                urllib.request.urlopen("http://127.0.0.1:8787/health", timeout=5)
                return True
            except:
                # Try alternative health check
                try:
                    req = urllib.request.Request(
                        "http://127.0.0.1:8787/completion",
                        data=json.dumps({"prompt": "test", "n_predict": 1}).encode(),
                        headers={"Content-Type": "application/json"}
                    )
                    urllib.request.urlopen(req, timeout=5)
                    return True
                except:
                    return False
        except Exception as e:
            print(f"[SID] Server start error: {e}")
            return False

    def set_api_mode(self, api_key: str, endpoint: str = ""):
        """Configure API-based inference."""
        self._api_enabled = True
        self.config.api_key = api_key
        if endpoint:
            self.config.api_endpoint = endpoint
        self._cleanup()

    def generate(self, 
                messages: List[Dict],
                max_tokens: int = 256,
                temperature: float = 0.7,
                top_p: float = 0.9) -> str:
        """Generate response using best available method."""
        if self._api_enabled:
            return self._api_generate(messages, max_tokens, temperature, top_p)
        elif self._llama_process and self._llama_process.poll() is None:
            return self._local_generate(messages, max_tokens, temperature, top_p)
        elif self._llama_python:
            return self._python_llama_generate(messages, max_tokens, temperature, top_p)
        else:
            return self._python_generate(messages, max_tokens, temperature, top_p)

    def _local_generate(self, messages, max_tokens, temperature, top_p) -> str:
        """Generate via local llama.cpp server with error handling."""
        prompt = self._messages_to_prompt(messages)

        payload = json.dumps({
            "prompt": prompt,
            "n_predict": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stop": ["</s>", "<|eot_id|>", "<|end|>", "<|assistant|>"],
            "cache_prompt": True,  # KV cache for efficiency
        }).encode()

        max_retries = 3
        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(
                    "http://127.0.0.1:8787/completion",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=120) as resp:
                    result = json.loads(resp.read())
                    content = result.get("content", "").strip()
                    if content:
                        return content
                    return "[SID] (empty response)"
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                raise RuntimeError(f"Local inference failed: {e}")

    def _api_generate(self, messages, max_tokens, temperature, top_p) -> str:
        """Generate via configured API (OpenAI-compatible)."""
        endpoint = self.config.api_endpoint.rstrip('/')
        
        payload = {
            "model": self.config.api_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}"
        }

        # Try OpenAI-compatible endpoint
        try:
            req = urllib.request.Request(
                f"{endpoint}/chat/completions",
                data=json.dumps(payload).encode(),
                headers=headers,
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read())
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"].strip()
                elif "content" in result:
                    return result["content"].strip()
                return "[SID] API returned unexpected format"
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"API error {e.code}: {e.reason}")
        except Exception as e:
            raise RuntimeError(f"API inference failed: {e}")

    def _python_llama_generate(self, messages, max_tokens, temperature, top_p) -> str:
        """Generate using llama-cpp-python bindings."""
        try:
            prompt = self._messages_to_prompt(messages)
            output = self._llama_python(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop=["</s>", "<|eot_id|>", "<|end|>"],
                echo=False
            )
            return output["choices"][0]["text"].strip()
        except Exception as e:
            raise RuntimeError(f"Python llama inference failed: {e}")

    def _python_generate(self, messages, max_tokens, temperature, top_p) -> str:
        """Python-only fallback with helpful message."""
        msg = messages[-1]["content"] if messages else ""
        return (
            f"[SID] No AI model loaded. Please:\n"
            f"  1. 'install model auto' - download recommended model\n"
            f"  2. 'config set api_key sk-...' - use cloud AI\n"
            f"  3. 'model use <name>' - load existing model\n"
            f"  Your input: \"{msg[:60]}...\""
        )

    def _messages_to_prompt(self, messages: List[Dict]) -> str:
        """Convert messages to llama.cpp prompt format."""
        prompt = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                prompt += f"<|system|>\n{content}\n"
            elif role == "user":
                prompt += f"<|user|>\n{content}\n"
            elif role == "assistant":
                prompt += f"<|assistant|>\n{content}\n"
        prompt += "<|assistant|>\n"
        return prompt

    def _find_llama_server(self) -> Optional[str]:
        """Find the llama.cpp server binary."""
        import shutil
        # Check shutil which first
        which_result = shutil.which("llama-server")
        if which_result:
            return which_result
        
        candidates = [
            "/usr/bin/llama-server",
            "/usr/local/bin/llama-server",
            "/usr/lib/llama/llama-server",
            "/sid/bin/llama-server",
            os.path.expanduser("~/.local/bin/llama-server"),
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        return None

    def _has_gpu(self) -> bool:
        """Check for GPU acceleration."""
        try:
            result = subprocess.run(["nvidia-smi"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return True
        except:
            pass
        try:
            result = subprocess.run(["vulkaninfo"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return True
        except:
            pass
        return False

    def _load_python_fallback(self, model_path: str) -> bool:
        """Try to load model using Python llama-cpp bindings."""
        try:
            from llama_cpp import Llama
            self._llama_python = Llama(
                model_path=model_path,
                n_ctx=self.config.context_window,
                n_threads=max(1, (os.cpu_count() or 2) - 1),
                n_gpu_layers=0,
                verbose=False,
                seed=42,
                use_mmap=False,  # Better for HDDs
                use_mlock=True,  # Keep in RAM
            )
            self.current_model_name = Path(model_path).stem
            return True
        except ImportError:
            print("[SID] llama-cpp-python not available. Install with: pip install llama-cpp-python")
            return False
        except Exception as e:
            print(f"[SID] Python fallback error: {e}")
            return False

    def _cleanup(self):
        """Clean up model processes."""
        if self._llama_process:
            try:
                self._llama_process.terminate()
                self._llama_process.wait(timeout=5)
            except:
                try:
                    self._llama_process.kill()
                except:
                    pass
            self._llama_process = None
        self._llama_python = None

    def list_available(self) -> Dict[str, List[ModelInfo]]:
        """List all models with download status, filtered by RAM tier."""
        result = {"available": [], "downloadable": []}
        
        # Get all models for current tier
        all_models = []
        for category in self.KNOWN_MODELS.values():
            if isinstance(category, list):
                all_models.extend(category)
        
        for m in all_models:
            info = m
            if m.path and m.path in self.model_paths.values():
                info.name += " ✅"
                result["available"].append(info)
            elif m.path and m.url:
                info.name += " ⬇️ (download)"
                result["downloadable"].append(info)
            elif m.path:
                info.name += " ❌ (not found)"
            else:
                result["available"].append(info)
        
        return result

    def download_model(self, model_name_or_url: str) -> bool:
        """Download a model from HuggingFace or custom URL."""
        dest_dir = Path("/sid/models")
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Check if it's a known model name
        for category in self.KNOWN_MODELS.values():
            if isinstance(category, list):
                for m in category:
                    if model_name_or_url.lower() in m.name.lower() and m.url:
                        url = m.url
                        filename = m.path
                        break
                else:
                    continue
                break
        else:
            # Try as direct URL
            if model_name_or_url.startswith("http"):
                url = model_name_or_url
                filename = url.split("/")[-1]
            else:
                print(f"[SID] Unknown model: {model_name_or_url}")
                return False

        dest = dest_dir / filename
        if dest.exists():
            print(f"[SID] Model already exists: {dest}")
            return True

        print(f"[SID] Downloading {filename}...")
        print(f"[SID] This may take a while on slow connections...")

        try:
            def report(block, blocksize, total):
                if block % 100 == 0:
                    pct = block * blocksize * 100 / max(total, 1)
                    print(f"\r[SID] Progress: {min(pct, 100):.0f}%", end="", flush=True)

            urllib.request.urlretrieve(url, dest, reporthook=report)
            print(f"\r[SID] ✓ Downloaded: {filename} ({dest.stat().st_size // 1024 // 1024}MB)")
            
            # Update model paths
            self.model_paths[filename.replace('.gguf', '')] = str(dest)
            return True
            
        except Exception as e:
            print(f"\n[SID] Download failed: {e}")
            if dest.exists():
                dest.unlink()
            return False

    def get_model_for_ram(self, tier: str) -> Optional[str]:
        """Get path to best model for a RAM tier."""
        for category in reversed([f"{tier}_tier", "4gb_tier", "2gb_tier"]):
            for m in self.KNOWN_MODELS.get(category, []):
                if m.path and m.path in self.model_paths:
                    return self.model_paths[m.path]
        return None


def max_ram(tier: str) -> int:
    """Get max RAM in MB for a tier."""
    limits = {"2gb": 768, "4gb": 1536, "6gb": 4096}
    return limits.get(tier, 1536)
