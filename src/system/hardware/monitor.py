"""SID Hardware Monitor - Real-time hardware awareness and optimization."""
import os
import time
import json
import threading
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field, asdict

@dataclass
class HardwareState:
    """Current hardware state snapshot."""
    cpu_model: str = ""
    cpu_usage: float = 0.0
    cpu_temp: float = 0.0
    cpu_cores: int = 0
    cpu_governor: str = ""
    ram_total: int = 0
    ram_used: int = 0
    ram_free: int = 0
    ram_percent: float = 0.0
    swap_total: int = 0
    swap_used: int = 0
    disk_total: int = 0
    disk_used: int = 0
    disk_free: int = 0
    disk_percent: float = 0.0
    uptime: int = 0
    load_1m: float = 0.0
    load_5m: float = 0.0
    load_15m: float = 0.0
    processes: int = 0
    has_gpu: bool = False
    is_throttling: bool = False
    ai_model_loaded: str = ""
    ai_memory_mb: int = 0
    optimization_level: str = "balanced"

class HardwareMonitor:
    """Continuous hardware monitoring and optimization suggestions."""

    def __init__(self, config_path: str = "/etc/sid/hardware.json"):
        self.config_path = Path(config_path)
        self.current = HardwareState()
        self.history: List[HardwareState] = []
        self._running = False
        self._thread = None
        self._lock = threading.Lock()
        self._callbacks: Dict[str, List[Callable]] = {}
        self._load_config()
        self._init_sysfs()

    def _init_sysfs(self):
        """Initialize hardware monitoring paths."""
        self._thermal_paths = []
        for i in range(10):
            p = Path(f"/sys/class/thermal/thermal_zone{i}/temp")
            if p.exists():
                self._thermal_paths.append(p)

    def _load_config(self):
        """Load hardware optimization config."""
        self.config = {
            "temp_warn": 75,
            "temp_critical": 85,
            "ram_warn_percent": 80,
            "ram_critical_percent": 90,
            "optimization_interval": 30,
            "monitor_interval": 5,
            "auto_optimize": True,
            "conservative_when_hot": True,
        }
        if self.config_path.exists():
            try:
                data = json.loads(self.config_path.read_text())
                self.config.update(data)
            except:
                pass

    def on(self, event: str, callback: Callable):
        self._callbacks.setdefault(event, []).append(callback)

    def _emit(self, event: str, **data):
        for cb in self._callbacks.get(event, []):
            try:
                cb(**data)
            except:
                pass

    def start(self):
        """Start monitoring thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def _monitor_loop(self):
        """Main monitoring loop."""
        interval = self.config.get("monitor_interval", 5)
        opt_interval = self.config.get("optimization_interval", 30)
        last_opt = 0

        while self._running:
            try:
                self._update_state()
                
                # Check critical conditions
                self._check_alerts()

                # Periodic optimization
                if time.time() - last_opt > opt_interval and self.config.get("auto_optimize"):
                    self.optimize()
                    last_opt = time.time()

                time.sleep(interval)
            except Exception as e:
                print(f"[SID-HW] Monitor error: {e}")
                time.sleep(interval)

    def _update_state(self):
        """Update hardware state snapshot."""
        with self._lock:
            s = self.current
            
            # CPU
            try:
                s.cpu_model = self._read_cpu_model()
                s.cpu_usage = self._get_cpu_usage()
                s.cpu_temp = self._get_cpu_temp()
                s.cpu_cores = os.cpu_count() or 0
                s.cpu_governor = self._read_governor()
            except:
                pass

            # RAM
            try:
                mem = self._read_meminfo()
                s.ram_total = mem.get('total', 0)
                s.ram_free = mem.get('free', 0)
                s.ram_used = s.ram_total - s.ram_free
                s.ram_percent = (s.ram_used / max(s.ram_total, 1)) * 100
            except:
                pass

            # Disk
            try:
                disk = self._read_disk()
                for k, v in disk.items():
                    setattr(s, f"disk_{k}", v)
                s.disk_percent = (s.disk_used / max(s.disk_total, 1)) * 100
            except:
                pass

            # System
            try:
                s.uptime = self._read_uptime()
                load = os.getloadavg()
                s.load_1m, s.load_5m, s.load_15m = load
            except:
                pass

            # Store history (keep last 100)
            self.history.append(self._copy_state(s))
            if len(self.history) > 100:
                self.history.pop(0)

    def _check_alerts(self):
        """Check for critical conditions and emit alerts."""
        s = self.current

        if s.cpu_temp > self.config.get("temp_critical", 85):
            self._emit("critical", type="temperature", value=s.cpu_temp,
                       msg=f"CPU temperature critical: {s.cpu_temp}°C")
            self.current.is_throttling = True
        elif s.cpu_temp > self.config.get("temp_warn", 75):
            self._emit("warning", type="temperature", value=s.cpu_temp,
                       msg=f"CPU temperature high: {s.cpu_temp}°C")

        if s.ram_percent > self.config.get("ram_critical_percent", 90):
            self._emit("critical", type="memory", value=s.ram_percent,
                       msg=f"Memory critical: {s.ram_percent:.0f}% used")
        elif s.ram_percent > self.config.get("ram_warn_percent", 80):
            self._emit("warning", type="memory", value=s.ram_percent,
                       msg=f"Memory high: {s.ram_percent:.0f}% used")

    def optimize(self) -> Dict:
        """Run hardware optimization routines."""
        optimizations = []

        # CPU Governor optimization
        if self.current.cpu_temp > 70:
            if self._set_governor("powersave"):
                optimizations.append("CPU governor set to powersave")
                self.current.optimization_level = "powersave"
        elif self.current.cpu_temp < 50 and self.current.cpu_usage < 30:
            if self._set_governor("performance"):
                optimizations.append("CPU governor set to performance")
                self.current.optimization_level = "performance"
        else:
            if self._set_governor("ondemand"):
                optimizations.append("CPU governor set to ondemand")
                self.current.optimization_level = "balanced"

        # Memory optimization
        if self.current.ram_percent > 85:
            self._clear_caches()
            optimizations.append("Cleared memory caches")

        # Disk optimization
        if self.current.disk_percent > 90:
            self._clean_temp()
            optimizations.append("Cleaned temporary files")

        self._emit("optimized", actions=optimizations)
        return {"actions": optimizations, "level": self.current.optimization_level}

    def _read_cpu_model(self) -> str:
        try:
            result = subprocess.run(
                ["sh", "-c", "lscpu | grep 'Model name' | cut -d: -f2 | xargs"],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip() or "Unknown CPU"
        except:
            return "Unknown CPU"

    def _get_cpu_usage(self) -> float:
        try:
            # Quick read from /proc/stat
            with open("/proc/stat") as f:
                line = f.readline()
            parts = [int(x) for x in line.strip().split()[1:]]
            idle = parts[3]
            total = sum(parts)
            # Read again after a short delay
            import time as _t
            _t.sleep(0.1)
            with open("/proc/stat") as f:
                line2 = f.readline()
            parts2 = [int(x) for x in line2.strip().split()[1:]]
            idle2 = parts2[3]
            total2 = sum(parts2)
            return (1 - (idle2 - idle) / max(total2 - total, 1)) * 100
        except:
            return 0.0

    def _get_cpu_temp(self) -> float:
        for p in self._thermal_paths:
            try:
                temp = int(p.read_text().strip()) / 1000
                if 0 < temp < 120:  # Sanity check
                    return temp
            except:
                continue
        return 0.0

    def _read_governor(self) -> str:
        try:
            for cpu in Path("/sys/devices/system/cpu").glob("cpu[0-9]*"):
                gov = cpu / "cpufreq/scaling_governor"
                if gov.exists():
                    return gov.read_text().strip()
        except:
            pass
        return "unknown"

    def _set_governor(self, governor: str) -> bool:
        try:
            for cpu in Path("/sys/devices/system/cpu").glob("cpu[0-9]*"):
                gov = cpu / "cpufreq/scaling_governor"
                if gov.exists():
                    gov.write_text(governor)
            return True
        except:
            return False

    def _read_meminfo(self) -> Dict:
        result = {"total": 0, "free": 0, "available": 0}
        with open("/proc/meminfo") as f:
            for line in f:
                if "MemTotal" in line:
                    result["total"] = int(line.split()[1]) * 1024
                elif "MemFree" in line:
                    result["free"] = int(line.split()[1]) * 1024
                elif "MemAvailable" in line:
                    result["available"] = int(line.split()[1]) * 1024
        return result

    def _read_disk(self) -> Dict:
        try:
            result = subprocess.run(
                ["df", "-B1", "/"], capture_output=True, text=True, timeout=5
            )
            parts = result.stdout.strip().split('\n')[-1].split()
            return {
                "total": int(parts[1]),
                "used": int(parts[2]),
                "free": int(parts[3]),
            }
        except:
            return {"total": 0, "used": 0, "free": 0}

    def _read_uptime(self) -> int:
        try:
            with open("/proc/uptime") as f:
                return int(float(f.read().split()[0]))
        except:
            return 0

    def _clear_caches(self):
        try:
            with open("/proc/sys/vm/drop_caches", "w") as f:
                f.write("3")
        except:
            pass

    def _clean_temp(self):
        subprocess.run(["rm", "-rf", "/tmp/*"], capture_output=True)
        subprocess.run(["rm", "-rf", "/var/tmp/*"], capture_output=True)

    def _copy_state(self, s: HardwareState) -> HardwareState:
        import copy
        return copy.deepcopy(s)

    def get_stats(self) -> Dict:
        with self._lock:
            return asdict(self.current)

    def get_recommendations(self) -> List[str]:
        """Get AI-optimized recommendations based on hardware state."""
        recs = []
        s = self.current
        if s.ram_total < 2 * (1024**3):
            recs.append("Upgrade RAM to at least 4GB for better AI performance")
        if s.cpu_temp > 70:
            recs.append("Clean cooling system or reduce CPU load")
        if s.disk_percent > 85:
            recs.append("Free up disk space for AI model storage")
        if s.swap_used > 0:
            recs.append("Consider adding more RAM to reduce swap usage")
        if s.cpu_cores < 4:
            recs.append("Consider upgrading to a quad-core CPU")
        return recs
