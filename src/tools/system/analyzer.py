"""AI-powered system analysis and diagnostics."""
import os
import subprocess
from typing import Dict, List, Optional
from pathlib import Path

class SystemAnalyzer:
    """Analyze system health, performance, and issues."""

    def __init__(self, ai=None):
        self.ai = ai

    def diagnose(self, issue: str) -> str:
        """Diagnose a system issue with AI."""
        if not self.ai:
            return "[SID] AI engine not available"
        prompt = f"Diagnose this Linux system issue: {issue}\nProvide fix commands."
        result = self.ai.process(prompt)
        return result.get("response", "Error diagnosing issue")

    def performance_report(self) -> Dict:
        """Generate performance analysis report."""
        report = {}
        
        # CPU
        try:
            cpu = subprocess.run(
                ["sh", "-c", "top -bn1 | grep 'Cpu(s)' | awk '{print $2}'"],
                capture_output=True, text=True, timeout=5
            ).stdout.strip()
            report["cpu_usage"] = f"{cpu}%"
        except:
            report["cpu_usage"] = "N/A"

        # Memory
        try:
            mem = subprocess.run(
                ["sh", "-c", "free -m | grep Mem | awk '{print $3\"MB / \"$2\"MB\"}'"],
                capture_output=True, text=True, timeout=5
            ).stdout.strip()
            report["memory"] = mem
        except:
            report["memory"] = "N/A"

        # Top processes
        try:
            procs = subprocess.run(
                ["sh", "-c", "ps aux --sort=-%mem | head -5 | awk '{print $11, $4\"%\"}'"],
                capture_output=True, text=True, timeout=5
            ).stdout.strip().split('\n')
            report["top_processes"] = procs[:3]
        except:
            report["top_processes"] = []

        # Disk I/O
        try:
            io = subprocess.run(
                ["sh", "-c", "iostat -x 1 2 | tail -5"],
                capture_output=True, text=True, timeout=10
            ).stdout.strip()
            report["disk_io"] = io[:200]
        except:
            report["disk_io"] = "N/A"

        return report

    def security_check(self) -> List[str]:
        """Basic security checks."""
        issues = []
        
        # Check for updates
        try:
            updates = subprocess.run(
                ["sh", "-c", "apt-get --just-print upgrade 2>/dev/null | grep '^Inst' | wc -l"],
                capture_output=True, text=True, timeout=10
            ).stdout.strip()
            if int(updates) > 0:
                issues.append(f"{updates} pending updates")
        except:
            pass

        # Check firewall
        try:
            fw = subprocess.run(
                ["sh", "-c", "ufw status | grep -i active"],
                capture_output=True, text=True, timeout=5
            ).stdout.strip()
            if not fw:
                issues.append("Firewall not active")
        except:
            pass

        # Check SSH config
        try:
            ssh_config = Path("/etc/ssh/sshd_config")
            if ssh_config.exists():
                content = ssh_config.read_text()
                if "PermitRootLogin yes" in content:
                    issues.append("Root SSH login enabled")
        except:
            pass

        return issues

    def suggest_optimizations(self) -> List[str]:
        """Get AI suggestions for system optimization."""
        report = self.performance_report()
        if not self.ai:
            return ["AI not available for optimization suggestions"]
        
        prompt = f"Suggest 3 quick optimizations for this system:\n{report}"
        result = self.ai.process(prompt)
        response = result.get("response", "")
        return [r.strip() for r in response.split('\n') if r.strip()][:5]
