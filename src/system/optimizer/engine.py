"""SID Optimizer - Continuous system optimization engine."""
import os
import time
import threading
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

class Optimizer:
    """System optimizer that continuously tunes settings for performance."""

    def __init__(self, hardware_monitor=None):
        self.hw = hardware_monitor
        self._running = False
        self._thread = None
        self.optimizations_applied = []
        self._profile = "auto"

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._optimize_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def _optimize_loop(self):
        while self._running:
            try:
                self._run_optimizations()
                time.sleep(60)  # Run every minute
            except:
                time.sleep(60)

    def _run_optimizations(self):
        hw = self.hw.current if self.hw else None
        if not hw:
            return

        actions = []

        # 1. Swappiness optimization based on RAM
        if hw.ram_total < 2 * (1024**3):
            self._set_sysctl("vm.swappiness", "10")
            actions.append("swappiness=10 (low RAM)")
        elif hw.ram_total < 4 * (1024**3):
            self._set_sysctl("vm.swappiness", "30")
            actions.append("swappiness=30")
        else:
            self._set_sysctl("vm.swappiness", "60")

        # 2. VM cache pressure
        if hw.ram_percent > 80:
            self._set_sysctl("vm.vfs_cache_pressure", "200")
            actions.append("increased cache pressure")
        else:
            self._set_sysctl("vm.vfs_cache_pressure", "100")

        # 3. Dirty ratio for old disks
        self._set_sysctl("vm.dirty_ratio", "20")
        self._set_sysctl("vm.dirty_background_ratio", "5")

        # 4. Network optimizations for old hardware
        self._set_sysctl("net.core.rmem_max", "16777216")
        self._set_sysctl("net.core.wmem_max", "16777216")

        # 5. Process priority for AI
        if hw.ai_memory_mb > 0:
            self._set_sysctl("kernel.sched_rt_runtime_us", "950000")

        if actions:
            self.optimizations_applied.extend(actions)

    def _set_sysctl(self, key: str, value: str):
        try:
            subprocess.run(
                ["sysctl", "-w", f"{key}={value}"],
                capture_output=True, timeout=5
            )
        except:
            pass

    def get_profile(self) -> Dict:
        return {
            "profile": self._profile,
            "optimizations": self.optimizations_applied[-20:],
            "count": len(self.optimizations_applied)
        }

    def set_profile(self, profile: str):
        """Set optimization profile: auto, powersave, performance, balanced."""
        self._profile = profile
        if profile == "powersave":
            self._set_governor("powersave")
        elif profile == "performance":
            self._set_governor("performance")
        else:
            self._set_governor("ondemand")

    def _set_governor(self, governor: str):
        try:
            for cpu in Path("/sys/devices/system/cpu").glob("cpu[0-9]*"):
                gov = cpu / "cpufreq/scaling_governor"
                if gov.exists():
                    gov.write_text(governor)
        except:
            pass
