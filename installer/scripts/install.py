#!/usr/bin/env python3
"""SID OS Installer v2.0 - Plug and play with AI setup."""
import os
import sys
import time
import json
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict

class SIDInstaller:
    """Interactive SID OS installer with AI model selection."""

    INSTALL_STEPS = [
        "detect_hardware",
        "select_disk",
        "partition",
        "format",
        "install_base",
        "install_sid",
        "configure",
        "install_ai",
        "benchmark_hardware",
        "install_bootloader",
        "finish"
    ]

    RAM_TIERS = {
        "2gb": {
            "label": "Ultra Light (2GB RAM)",
            "models": ["Llama-3.2-1B-Instruct-Abliterated"],
            "voice": "whisper_tiny",
            "features": "Basic AI, voice, system tools"
        },
        "4gb": {
            "label": "Default (4GB RAM) ★ Recommended",
            "models": ["Llama-3.2-3B-Instruct-Abliterated", "CodeLlama-7B-Python-Abliterated"],
            "voice": "whisper_tiny",
            "router": True,
            "features": "Full AI with routing, code specialist, voice, media"
        },
        "6gb": {
            "label": "Power User (6GB+ RAM)",
            "models": ["Qwen-2.5-7B-Instruct-Abliterated", "Dolphin-2.9.3-8B-Uncensored", "CodeLlama-7B-Python-Abliterated"],
            "voice": "whisper_small",
            "router": True,
            "features": "Multi-model, uncensored, code specialist, voice"
        }
    }

    def __init__(self):
        self.target_disk = None
        self.hostname = "sid-os"
        self.username = "sid"
        self.password = ""
        self.ram_tier = "4gb"
        self.download_models = True
        self.use_api = False
        self.api_key = ""

    def run(self):
        """Run the installation wizard."""
        print("\033[2J\033[H")
        print("\033[32m╔══════════════════════════════════════════╗\033[0m")
        print("\033[32m║    SID OS v0.0.2 - Installation Wizard    ║\033[0m")
        print("\033[32m║    AI-First OS for Old Hardware          ║\033[0m")
        print("\033[32m╚══════════════════════════════════════════╝\033[0m\n")

        for step in self.INSTALL_STEPS:
            print(f"\n\033[34m== {step.replace('_',' ').title()} ==\033[0m")
            getattr(self, step)()
            print(f"\033[32m  ✓\033[0m")
            time.sleep(0.3)

        print(f"\n\033[32m╔══════════════════════════════════════════╗\033[0m")
        print(f"\033[32m║     Installation Complete!               ║\033[0m")
        print(f"\033[32m║     Reboot and start using SID!          ║\033[0m")
        print(f"\033[32m║     Just type naturally to navigate      ║\033[0m")
        print(f"\033[32m╚══════════════════════════════════════════╝\033[0m\n")
        
        if self.download_models:
            print(f"\033[33mNote: AI model downloads will continue in background\033[0m")
            print(f"\033[33m      on first boot. Models will download based on\033[0m")
            print(f"\033[33m      your {self.ram_tier.upper()} RAM selection.\033[0m\n")
        
        if self.use_api:
            print(f"\033[33mAPI key configured. AI will use online mode by default.\033[0m")

    def detect_hardware(self):
        """Detect hardware and recommend RAM tier."""
        print("  Detecting hardware...")
        
        cpu = subprocess.run(
            ["sh", "-c", "lscpu | grep 'Model name' | head -1 | cut -d: -f2 | xargs"],
            capture_output=True, text=True
        ).stdout.strip() or "Unknown CPU"
        
        try:
            ram_mb = int(subprocess.run(
                ["sh", "-c", "free -m | grep Mem | awk '{print $2}'"],
                capture_output=True, text=True
            ).stdout.strip())
        except:
            ram_mb = 2048

        ram_gh = f"{ram_mb/1024:.1f}GB" if ram_mb > 1024 else f"{ram_mb}MB"

        # Detect specific hardware (like HP Pavilion)
        try:
            product = subprocess.run(
                ["sh", "-c", "cat /sys/class/dmi/id/product_name 2>/dev/null || cat /sys/devices/virtual/dmi/id/product_name 2>/dev/null || echo 'Unknown'"],
                capture_output=True, text=True
            ).stdout.strip()
        except:
            product = "Generic PC"

        # Recommend RAM tier
        if ram_mb < 2048:
            self.ram_tier = "2gb"
        elif ram_mb < 6144:
            self.ram_tier = "4gb"
        else:
            self.ram_tier = "6gb"

        print(f"  Hardware: {product}")
        print(f"  CPU:      {cpu}")
        print(f"  RAM:      {ram_gh} ({ram_mb}MB)")
        print(f"\n  \033[36mRecommended setup: {self.RAM_TIERS[self.ram_tier]['label']}\033[0m")
        print(f"  Features: {self.RAM_TIERS[self.ram_tier]['features']}")

        # Allow user to change tier
        print(f"\n  RAM tiers:")
        for tier, info in self.RAM_TIERS.items():
            marker = "★" if tier == self.ram_tier else " "
            print(f"    [{marker}] {tier}: {info['label']}")
        
        choice = input(f"\n  Select RAM tier [{'/'.join(self.RAM_TIERS.keys())}]: ").strip()
        if choice in self.RAM_TIERS:
            self.ram_tier = choice

    def select_disk(self):
        """Select installation disk."""
        print("\n  Available disks:")
        subprocess.run(
            ["sh", "-c", "lsblk -d -o NAME,SIZE,TYPE,MODEL | grep -v loop"],
        )
        
        disk = input("\n  Install to which disk? (e.g., sda): ").strip() or "sda"
        self.target_disk = f"/dev/{disk}"
        
        print(f"  Selected: {self.target_disk}")
        confirm = input("  This ERASES ALL DATA. Continue? (y/N): ")
        if confirm.lower() != 'y':
            print("  Cancelled.")
            sys.exit(0)

    def partition(self):
        """Create partitions."""
        print(f"  Partitioning {self.target_disk}...")
        try:
            subprocess.run([
                "sh", "-c",
                f"parted -s {self.target_disk} mklabel msdos "
                f"mkpart primary ext4 1MiB 512MiB "
                f"mkpart primary ext4 512MiB 100%"
            ], check=True, timeout=30)
            print("  Created: /boot (512MB) + root")
        except:
            # Fallback to single partition
            subprocess.run([
                "sh", "-c",
                f"parted -s {self.target_disk} mklabel msdos mkpart primary ext4 1MiB 100%"
            ], check=True, timeout=30)
            print("  Single partition created")

    def format(self):
        """Format partitions."""
        print("  Formatting...")
        boot = f"{self.target_disk}1"
        root = f"{self.target_disk}2"
        
        if not Path(root).exists():
            root = boot
            boot = None

        if boot:
            subprocess.run(["mkfs.ext4", "-F", boot], capture_output=True)
        subprocess.run(["mkfs.ext4", "-F", root], capture_output=True)
        print("  Partitions formatted (ext4)")

    def install_base(self):
        """Install base system."""
        print("  Installing base system...")
        
        root = f"{self.target_disk}2"
        if not Path(root).exists():
            root = f"{self.target_disk}1"
        
        mount = Path("/mnt/sid")
        mount.mkdir(parents=True, exist_ok=True)
        subprocess.run(["mount", root, mount], check=True)
        
        boot = f"{self.target_disk}1"
        if boot != root and Path(boot).exists():
            (mount / "boot").mkdir(exist_ok=True)
            subprocess.run(["mount", boot, mount / "boot"], check=True)

        # Install base packages
        for pkg_mgr, pkgs in [
            ("apk", "busybox musl libcrypto3 libssl3 ncurses-libs bash python3 sqlite-libs openssh dhcpcd"),
            ("apt-get", "bash python3 openssh-server"),
        ]:
            try:
                subprocess.run(
                    [pkg_mgr, "install", "-y"] + pkgs.split() + [f"--root={mount}"],
                    capture_output=True, timeout=120
                )
                break
            except:
                continue

    def install_sid(self):
        """Install SID OS files."""
        print("  Installing SID system...")
        
        mount = Path("/mnt/sid")
        sid_src = Path(__file__).parent.parent.parent

        # Create SID directories
        for d in ["/sid", "/sid/src", "/sid/config", "/sid/models", 
                  "/sid/memory", "/sid/logs", "/var/lib/sid",
                  "/usr/share/sid/models", "/usr/share/sid/voices"]:
            (mount / d.lstrip('/')).mkdir(parents=True, exist_ok=True)

        # Copy SID source files
        subprocess.run(["cp", "-r", str(sid_src / "src"), str(mount / "sid")])
        subprocess.run(["cp", "-r", str(sid_src / "config"), str(mount / "sid")])

        # Create main entry point
        entry = mount / "usr/bin/sid"
        entry.write_text("#!/bin/bash\npython3 /sid/src/main.py \"$@\"\n")
        entry.chmod(0o755)

        # Create symlinks
        (mount / "etc/sid").symlink_to("/sid/config")

    def configure(self):
        """Configure system."""
        print("  Configuring...")
        
        mount = Path("/mnt/sid")
        
        # Hostname
        (mount / "etc/hostname").write_text(f"{self.hostname}\n")
        
        # Network
        (mount / "etc/network/interfaces").write_text(
            "auto lo\niface lo inet loopback\n\nauto eth0\niface eth0 inet dhcp\n"
        )

        # User setup
        username = input("  Username [sid]: ").strip() or "sid"
        password = input("  Password: ").strip() or "sid"
        
        try:
            subprocess.run(
                ["chroot", mount, "adduser", "-D", "-s", "/bin/bash", username],
                capture_output=True
            )
            subprocess.run(
                ["chroot", mount, "sh", "-c", f"echo '{username}:{password}' | chpasswd"],
                capture_output=True
            )
        except:
            pass

        # Configure SID AI for detected RAM
        ai_config = {
            "mode": "auto",
            "ram_tier": self.ram_tier,
            "context_window": {"2gb": 2048, "4gb": 4096, "6gb": 8192}[self.ram_tier],
            "max_tokens": {"2gb": 128, "4gb": 256, "6gb": 512}[self.ram_tier],
            "compression_enabled": True,
            "memory_enabled": True,
            "router_enabled": self.ram_tier != "2gb",
            "deep_integration": True,
            "memory_optimizer_seed": True,
            "auto_detect_ram": True
        }
        (mount / "etc/sid/ai.json").write_text(json.dumps(ai_config, indent=2))

    def install_ai(self):
        """Configure AI models."""
        print("  Setting up AI...")
        
        mount = Path("/mnt/sid")
        
        # Ask about AI setup
        print("\n  AI Setup:")
        dl = input("  Download AI models? (recommended) [Y/n]: ").strip().lower()
        self.download_models = dl != 'n'
        
        api = input("  Configure API key for cloud AI? (optional) [y/N]: ").strip().lower()
        if api == 'y':
            self.api_key = input("  Enter API key: ").strip()
            self.use_api = True
            (mount / "etc/sid/ai.json").write_text(
                json.dumps(json.loads((mount / "etc/sid/ai.json").read_text()) | {
                    "api_key": self.api_key,
                    "mode": "hybrid"
                }, indent=2)
            )

        # Create model download script for first boot
        if self.download_models:
            download_script = mount / "etc/sid/download_models.sh"
            tier_info = self.RAM_TIERS[self.ram_tier]
            
            script = "#!/bin/bash\n"
            script += "# SID Auto Model Downloader\n"
            script += f"echo '[SID] Downloading models for {self.ram_tier.upper()} RAM...'\n"
            script += "mkdir -p /sid/models /usr/share/sid/models\n"
            
            for model in tier_info["models"]:
                script += f"python3 /sid/src/tools/download_model.py {model} &\n"
            
            download_script.write_text(script)
            download_script.chmod(0o755)


    def benchmark_hardware(self):
        """Benchmark hardware and recommend best AI setup."""
        print("  Benchmarking hardware for optimal AI configuration...")
        try:
            import sys as _sys
            _sys.path.insert(0, '/sid/src')
            from tools.benchmark import HardwareBenchmark
            hb = HardwareBenchmark()
            results = hb.run_all()
            hb.apply_recommendations()
            
            recs = results.get("recommendations", {})
            print(f"    RAM Tier: {recs.get('tier_name', '?')}")
            print(f"    Recommended Model: {recs.get('recommended_model', '?')}")
            print(f"    Strategy: {recs.get('load_strategy', '?')}")
            print(f"  \033[32m✓ Benchmark complete\033[0m")
        except Exception as e:
            print(f"  \033[33m⚠ Benchmark not available: {e}\033[0m")
            print(f"  \033[32m✓ Using default configuration\033[0m")

    def install_bootloader(self):
        """Install bootloader."""
        print("  Installing bootloader...")
        mount = Path("/mnt/sid")
        
        try:
            subprocess.run(
                ["chroot", mount, "grub-install", self.target_disk],
                capture_output=True, timeout=60
            )
            subprocess.run(
                ["chroot", mount, "update-grub"],
                capture_output=True, timeout=30
            )
        except:
            # Fallback to extlinux
            subprocess.run(
                ["extlinux", "--install", str(mount / "boot")],
                capture_output=True
            )

        # Create GRUB entry
        boot_entry = """timeout=3
menuentry "SID OS v0.0.2" {
    linux /boot/vmlinuz-sid root={root} console=tty0 quiet loglevel=3
    initrd /boot/initramfs-sid.gz
}
menuentry "SID OS (Safe Mode)" {
    linux /boot/vmlinuz-sid root={root} console=tty0 nomodeset acpi=off
    initrd /boot/initramfs-sid.gz
}
"""
        (mount / "boot/grub/grub.cfg").write_text(
            boot_entry.format(root=f"{self.target_disk}2")
        )

    def finish(self):
        """Clean up."""
        mount = Path("/mnt/sid")
        subprocess.run(["umount", "-R", mount], capture_output=True)
        
        print(f"\n  \033[32m✓ Installation complete!\033[0m")
        print(f"\n  \033[36mQuick Start Guide:\033[0m")
        print(f"  1. Reboot and remove installation media")
        print(f"  2. Login with your username/password")
        print(f"  3. Type anything - the AI understands natural language!")
        print(f"  4. For setup, type 'install quick {self.ram_tier}'")
        print(f"  5. For help, type 'help' or 'ai'")
