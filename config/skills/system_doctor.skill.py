"""SID System Doctor - Diagnose and fix system issues."""
from src.agent.skill_base import BaseSkill, SkillMetadata
import subprocess
import os

class SystemDoctorSkill(BaseSkill):
    """Diagnose common system issues and suggest fixes."""

    def __init__(self):
        super().__init__()
        self.metadata = SkillMetadata(
            name="system_doctor",
            version="0.5.2",
            description="Diagnose system issues and suggest fixes",
            author="SID OS",
            dependencies=["bash", "python3"]
        )

    def execute(self, **params) -> dict:
        check_type = params.get("check", "all")
        results = {}
        
        if check_type in ("disk", "all"):
            results["disk"] = self._check_disk()
        if check_type in ("memory", "all"):
            results["memory"] = self._check_memory()
        if check_type in ("temp", "all"):
            results["temp"] = self._check_temp()
        if check_type in ("network", "all"):
            results["network"] = self._check_network()
        
        return results

    def _check_disk(self) -> dict:
        try:
            result = subprocess.run(
                ["df", "-h", "/"], capture_output=True, text=True, timeout=5
            )
            lines = result.stdout.strip().split('\n')[1].split()
            used_pct = int(lines[4].rstrip('%'))
            return {
                "status": "warning" if used_pct > 85 else "ok",
                "used_percent": used_pct,
                "total": lines[1],
                "used": lines[2],
                "available": lines[3],
                "advice": "Running low on disk space" if used_pct > 85 else "Disk space is healthy"
            }
        except:
            return {"status": "error", "message": "Could not check disk"}

    def _check_memory(self) -> dict:
        try:
            result = subprocess.run(
                ["free", "-m"], capture_output=True, text=True, timeout=5
            )
            lines = result.stdout.strip().split('\n')[1].split()
            total = int(lines[1])
            used = int(lines[2])
            pct = (used / total) * 100
            return {
                "status": "warning" if pct > 85 else "ok",
                "used_percent": round(pct, 1),
                "total_mb": total,
                "used_mb": used,
                "advice": "Close applications to free memory" if pct > 85 else "Memory usage healthy"
            }
        except:
            return {"status": "error", "message": "Could not check memory"}

    def _check_temp(self) -> dict:
        try:
            for path in ["/sys/class/thermal/thermal_zone0/temp"]:
                if os.path.exists(path):
                    temp = int(open(path).read().strip()) / 1000
                    return {
                        "status": "warning" if temp > 80 else "ok",
                        "temperature_c": temp,
                        "advice": "System overheating! Check cooling." if temp > 80 else "Temperature normal"
                    }
            return {"status": "unknown", "message": "No temperature sensors"}
        except:
            return {"status": "error", "message": "Could not read temperature"}

    def _check_network(self) -> dict:
        try:
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "2", "8.8.8.8"],
                capture_output=True, timeout=5
            )
            online = result.returncode == 0
            return {
                "status": "ok" if online else "offline",
                "online": online,
                "advice": "Network connectivity OK" if online else "No internet connection"
            }
        except:
            return {"status": "offline", "online": False, "advice": "Could not test network"}

    def validate(self, **params) -> bool:
        valid_checks = ["disk", "memory", "temp", "network", "all"]
        return params.get("check", "all") in valid_checks
