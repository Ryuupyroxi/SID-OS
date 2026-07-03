"""SID Hardware Benchmark - Tests hardware capability and recommends optimal models.
Run during install or on demand to determine best AI configuration."""
import os
import json
import time
import math
import subprocess
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class HardwareBenchmark:
    """Benchmarks hardware and recommends optimal AI model configuration."""

    def __init__(self, model_registry_path: str = "config/models/registry.json"):
        self.registry_path = Path(model_registry_path)
        self.registry = self._load_registry()
        self.results = {}

    def _load_registry(self) -> Dict:
        if self.registry_path.exists():
            try:
                return json.loads(self.registry_path.read_text())
            except:
                pass
        return {"ram_tiers": {}, "recommended": {}}

    def run_all(self) -> Dict:
        """Run all benchmarks and return recommendations."""
        print("[SID] Running hardware benchmark...")
        print("  This will test your system to recommend the best AI setup.\n")
        
        results = {
            "timestamp": time.time(),
            "system": self._bench_cpu_info(),
            "memory": self._bench_memory(),
            "cpu_speed": self._bench_cpu_speed(),
            "disk_speed": self._bench_disk_speed(),
            "ai_capability": self._bench_ai_capability(),
            "recommendations": {}
        }
        
        results["recommendations"] = self._generate_recommendations(results)
        self.results = results
        
        return results

    def _bench_cpu_info(self) -> Dict:
        """Get detailed CPU information."""
        info = {
            "model": "Unknown",
            "cores": os.cpu_count() or 1,
            "arch": "Unknown",
            "features": []
        }
        
        try:
            result = subprocess.run(
                ["sh", "-c", "lscpu | grep 'Model name' | cut -d: -f2 | xargs"],
                capture_output=True, text=True, timeout=5
            )
            info["model"] = result.stdout.strip()
        except:
            pass
        
        try:
            result = subprocess.run(
                ["sh", "-c", "lscpu | grep 'Flags' | head -1"],
                capture_output=True, text=True, timeout=5
            )
            flags = result.stdout.strip()
            info["features"] = [f for f in ["avx2", "avx", "sse4_2", "sse4_1", "neon", "fma"] 
                              if f in flags.lower()]
        except:
            pass
        
        try:
            result = subprocess.run(["uname", "-m"], capture_output=True, text=True, timeout=5)
            info["arch"] = result.stdout.strip()
        except:
            pass
        
        return info

    def _bench_memory(self) -> Dict:
        """Benchmark memory performance."""
        try:
            import psutil
            mem = psutil.virtual_memory()
            return {
                "total_mb": mem.total // (1024 * 1024),
                "available_mb": mem.available // (1024 * 1024),
                "percent_used": mem.percent,
                "swap_mb": psutil.swap_memory().total // (1024 * 1024) if hasattr(psutil, 'swap_memory') else 0,
            }
        except:
            pass
        
        # Fallback to /proc/meminfo
        try:
            with open("/proc/meminfo") as f:
                data = {}
                for line in f:
                    parts = line.split()
                    if parts[0].rstrip(':') in ["MemTotal", "MemFree", "MemAvailable", "SwapTotal"]:
                        data[parts[0].rstrip(':')] = int(parts[1]) // 1024
                return {
                    "total_mb": data.get("MemTotal", 0),
                    "available_mb": data.get("MemAvailable", 0),
                    "swap_mb": data.get("SwapTotal", 0),
                }
        except:
            return {"total_mb": 0}

    def _bench_cpu_speed(self) -> Dict:
        """Benchmark raw CPU speed with a simple compute test."""
        # CPU-intensive calculation
        start = time.time()
        result = 0
        for i in range(1000000):
            result += math.sin(i) * math.cos(i)
        duration = time.time() - start
        
        ops_per_sec = 1000000 / max(duration, 0.001)
        
        return {
            "duration_ms": round(duration * 1000, 2),
            "ops_per_sec": round(ops_per_sec),
            "speed_rating": "fast" if ops_per_sec > 500000 else "medium" if ops_per_sec > 200000 else "slow",
            "single_thread_score": round(ops_per_sec / 1000, 1)
        }

    def _bench_disk_speed(self) -> Dict:
        """Test disk read/write speed."""
        test_file = "/tmp/sid_bench_test"
        
        # Write test
        data = os.urandom(64 * 1024 * 1024)  # 64MB
        start = time.time()
        with open(test_file, "wb") as f:
            f.write(data)
        write_duration = time.time() - start
        
        # Read test
        start = time.time()
        with open(test_file, "rb") as f:
            _ = f.read()
        read_duration = time.time() - start
        
        # Cleanup
        try:
            os.unlink(test_file)
        except:
            pass
        
        write_speed = (64 / max(write_duration, 0.001))  # MB/s
        read_speed = (64 / max(read_duration, 0.001))  # MB/s
        
        return {
            "write_mbps": round(write_speed, 1),
            "read_mbps": round(read_speed, 1),
            "disk_type": "ssd" if read_speed > 200 else "hdd",
            "duration_ms": round((write_duration + read_duration) * 1000, 1)
        }

    def _bench_ai_capability(self) -> Dict:
        """Assess AI model running capability."""
        cpu = self._bench_cpu_info() if not self.results.get("system") else self.results["system"]
        mem = self._bench_memory() if not self.results.get("memory") else self.results["memory"]
        disk = self._bench_disk_speed() if not self.results.get("disk_speed") else self.results["disk_speed"]
        
        # Determine AI capability level
        score = 0
        
        # CPU cores
        if cpu.get("cores", 0) >= 8:
            score += 30
        elif cpu.get("cores", 0) >= 4:
            score += 20
        elif cpu.get("cores", 0) >= 2:
            score += 10
        
        # RAM
        ram = mem.get("total_mb", 0)
        if ram >= 6144:
            score += 40
        elif ram >= 4096:
            score += 30
        elif ram >= 2048:
            score += 15
        
        # CPU features (AVX helps llama.cpp)
        if cpu.get("features"):
            score += 10
            if "avx2" in cpu.get("features", []):
                score += 10
        
        # Disk speed
        if disk.get("disk_type") == "ssd":
            score += 10
        
        capability = "minimal" if score < 30 else "basic" if score < 50 else "standard" if score < 70 else "enhanced" if score < 90 else "full"
        
        return {
            "score": score,
            "max_score": 100,
            "capability": capability,
            "can_run_1b": score >= 15,
            "can_run_3b": score >= 30,
            "can_run_7b": score >= 50,
            "can_run_8b": score >= 65,
            "can_run_multiple": score >= 70,
        }

    def _generate_recommendations(self, results: Dict) -> Dict:
        """Generate AI model recommendations based on benchmarks."""
        ai = results.get("ai_capability", {})
        mem = results.get("memory", {})
        cpu = results.get("system", {})
        
        ram = mem.get("total_mb", 0)
        
        # Determine RAM tier
        if ram < 2048:
            tier = "2gb"
            tier_name = "Ultra Light (2GB)"
        elif ram < 6144:
            tier = "4gb"
            tier_name = "Default (4GB)"
        else:
            tier = "6gb"
            tier_name = "Power User (6GB+)"
        
        # Get models for this tier
        tier_models = []
        registry = self.registry
        quick_setups = registry.get("quick_setups", {})
        setup_key = f"{tier}_plugandplay"
        
        if setup_key in quick_setups:
            setup = quick_setups[setup_key]
            tier_models = [setup.get("primary", "")]
            tier_models.extend(setup.get("specialty", []))
        
        # Model loading order recommendation
        if ai.get("can_run_multiple"):
            load_strategy = "router + primary + specialists (dynamic swap)"
        elif ai.get("can_run_7b"):
            load_strategy = "router + primary (swap specialists when needed)"
        else:
            load_strategy = "single model (no router, no swapping)"
        
        return {
            "ram_tier": tier,
            "tier_name": tier_name,
            "recommended_model": registry.get("ram_tiers", {}).get(tier, {}).get("recommended_model", ""),
            "recommended_models": tier_models,
            "load_strategy": load_strategy,
            "router_enabled": ai.get("score", 0) >= 30,
            "context_window": "2048" if tier == "2gb" else "4096" if tier == "4gb" else "8192",
            "max_tokens": "128" if tier == "2gb" else "256" if tier == "4gb" else "512",
            "notes": [
                f"System can {'run' if ai.get('can_run_1b') else 'struggle with'} 1B models",
                f"System can {'run' if ai.get('can_run_3b') else 'struggle with'} 3B models",
                f"System can {'run' if ai.get('can_run_7b') else 'struggle with'} 7B models",
                f"System can {'support' if ai.get('can_run_multiple') else 'not support'} multiple models simultaneously",
            ]
        }

    def format_report(self, results: Dict = None) -> str:
        """Format benchmark results as a readable report."""
        r = results or self.results
        if not r:
            return "No benchmark results. Run 'benchmark run' first."
        
        lines = ["═══ SID Hardware Benchmark Report ═══", ""]
        
        lines.append("CPU:")
        lines.append(f"  Model: {r.get('system', {}).get('model', 'Unknown')}")
        lines.append(f"  Cores: {r.get('system', {}).get('cores', 0)}")
        lines.append(f"  Features: {', '.join(r.get('system', {}).get('features', ['none']))}")
        lines.append(f"  Speed: {r.get('cpu_speed', {}).get('speed_rating', '?')} ({r.get('cpu_speed', {}).get('duration_ms', 0)}ms)")
        
        lines.append("")
        lines.append("Memory:")
        lines.append(f"  Total: {r.get('memory', {}).get('total_mb', 0)}MB")
        lines.append(f"  Available: {r.get('memory', {}).get('available_mb', 0)}MB")
        
        lines.append("")
        lines.append("Disk:")
        lines.append(f"  Type: {r.get('disk_speed', {}).get('disk_type', '?')}")
        lines.append(f"  Read: {r.get('disk_speed', {}).get('read_mbps', 0)} MB/s")
        lines.append(f"  Write: {r.get('disk_speed', {}).get('write_mbps', 0)} MB/s")
        
        ai = r.get("ai_capability", {})
        lines.append("")
        lines.append("AI Capability:")
        lines.append(f"  Score: {ai.get('score', 0)}/{ai.get('max_score', 100)}")
        lines.append(f"  Level: {ai.get('capability', '?')}")
        
        rec = r.get("recommendations", {})
        lines.append("")
        lines.append("Recommendation:")
        lines.append(f"  RAM Tier: {rec.get('tier_name', '?')}")
        lines.append(f"  Model: {rec.get('recommended_model', '?')}")
        lines.append(f"  Strategy: {rec.get('load_strategy', '?')}")
        
        return "\n".join(lines)

    def apply_recommendations(self, ai_config_path: str = "/etc/sid/ai.json") -> bool:
        """Apply benchmark recommendations to AI config."""
        if not self.results:
            self.run_all()
        
        recs = self.results.get("recommendations", {})
        if not recs:
            return False
        
        config_path = Path(ai_config_path)
        if config_path.exists():
            config = json.loads(config_path.read_text())
        else:
            config = {}
        
        # Update config with recommendations
        config["ram_tier"] = recs.get("ram_tier", "4gb")
        config["context_window"] = int(recs.get("context_window", 4096))
        config["max_tokens"] = int(recs.get("max_tokens", 256))
        config["router_enabled"] = recs.get("router_enabled", False)
        config["benchmarked_at"] = time.time()
        
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(config, indent=2))
        
        return True
