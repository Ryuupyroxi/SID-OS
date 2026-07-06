#!/usr/bin/env python3
"""SID OS Bootstrap — Download, set up, and launch SID in one command.
Zero dependencies. Uses only Python standard library.
Works on: Linux, macOS, Windows (any system with Python 3.8+)

Usage:
  python3 get-sid.py                    # Download + run SID
  python3 get-sid.py --install-deps    # Download + install deps + run
  python3 get-sid.py --update          # Update to latest version
"""
import os
import sys
import json
import urllib.request
import urllib.error
import tarfile
import zipfile
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path

SID_VERSION = "0.0.4"
GITHUB_REPO = "Ryuupyroxi/SID-OS"
RELEASE_URL = f"https://github.com/{GITHUB_REPO}/releases/download/v{SID_VERSION}/sid-{SID_VERSION}-portable.tar.gz"
LATEST_URL = f"https://github.com/{GITHUB_REPO}/releases/latest/download/sid-portable.tar.gz"
API_LATEST = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

def main():
    args = set(sys.argv[1:])
    install_deps = "--install-deps" in args or "--setup" in args
    update_mode = "--update" in args
    help_mode = "--help" in args or "-h" in args

    if help_mode:
        show_help()
        return

    print_banner()
    
    # Step 1: Find or create install directory
    sid_dir = find_sid_dir()
    print(f"  📁 SID home: {sid_dir}")

    # Step 2: Download if not present or update requested
    if not (sid_dir / "sid").exists() or update_mode:
        download_sid(sid_dir)
    else:
        print(f"  ✓ SID already downloaded")

    # Step 3: Install dependencies (optional)
    if install_deps:
        install_all_deps(sid_dir)

    # Step 4: First-run auto-setup
    if not (sid_dir / ".sid_configured").exists():
        first_run_setup(sid_dir)

    # Step 5: Launch SID
    print(f"\n  {'='*50}")
    print(f"  🚀 Launching SID OS...")
    print(f"  {'='*50}\n")
    
    os.chdir(str(sid_dir))
    if sys.platform == "win32":
        os.execvp("python", ["python", "src/main.py", "--theme", "vt100"])
    else:
        os.execvp("python3", ["python3", "src/main.py", "--theme", "vt100"])

def find_sid_dir() -> Path:
    """Find or create SID install directory."""
    candidates = [
        Path.cwd() / "SID-OS",
        Path.cwd() / "sid",
        Path.home() / "SID-OS",
        Path.home() / "sid",
    ]
    for p in candidates:
        if (p / "sid").exists() or (p / "src/main.py").exists():
            return p
    # Default to current directory
    return Path.cwd() / "SID-OS"

def download_sid(target_dir: Path):
    """Download SID portable release using only stdlib."""
    print(f"  📥 Downloading SID OS v{SID_VERSION}...")
    
    target_dir.mkdir(parents=True, exist_ok=True)
    tmp = tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False)
    tmp.close()
    
    try:
        # Try latest release first, then fallback to specific version
        urls = [LATEST_URL, RELEASE_URL]
        downloaded = False
        
        for url in urls:
            try:
                print(f"     {url}")
                req = urllib.request.Request(url, headers={"User-Agent": "SID-OS-Bootstrap/1.0"})
                with urllib.request.urlopen(req, timeout=60) as resp:
                    total = int(resp.headers.get('content-length', 0))
                    written = 0
                    chunk_size = 8192
                    
                    with open(tmp.name, 'wb') as f:
                        while True:
                            chunk = resp.read(chunk_size)
                            if not chunk:
                                break
                            f.write(chunk)
                            written += len(chunk)
                            if total:
                                pct = written * 100 // total
                                print(f"\r     Progress: {pct}% ({written//1024}KB / {total//1024}KB)", end='', flush=True)
                            else:
                                print(f"\r     Downloaded: {written//1024}KB", end='', flush=True)
                    print()
                    downloaded = True
                    break
            except urllib.error.HTTPError as e:
                if e.code == 302:
                    # Follow redirect
                    url = e.headers.get('Location', url)
                    continue
                print(f"     HTTP {e.code}, trying next...")
                continue
            except Exception as e:
                print(f"     Error: {e}, trying next...")
                continue
        
        if not downloaded:
            print(f"\n  ❌ Could not download SID. Check internet or download manually:")
            print(f"     https://github.com/{GITHUB_REPO}/releases")
            sys.exit(1)
        
        # Extract
        print(f"  📦 Extracting...")
        with tarfile.open(tmp.name, 'r:gz') as tar:
            tar.extractall(path=str(target_dir))
        
        # Mark as configured
        (target_dir / ".sid_configured").write_text(f"version={SID_VERSION}\n")
        
        # Make launchers executable on Unix
        if sys.platform != "win32":
            for f in ["sid", "sid-test", "sid-install"]:
                p = target_dir / f
                if p.exists():
                    p.chmod(0o755)
        
        print(f"  ✓ Extracted to: {target_dir}")
        
    except Exception as e:
        print(f"\n  ❌ Download failed: {e}")
        print(f"  Try: python3 get-sid.py --install-deps")
        sys.exit(1)
    finally:
        os.unlink(tmp.name)

def install_all_deps(sid_dir: Path):
    """Auto-detect and install all dependencies."""
    print(f"\n  🔧 Checking dependencies...")
    
    # Check Python version
    py_version = sys.version_info
    if py_version.major < 3 or (py_version.major == 3 and py_version.minor < 8):
        print(f"  ❌ Python 3.8+ required. You have {sys.version}")
        print(f"     Download from: https://python.org")
        return
    
    print(f"  ✓ Python {py_version.major}.{py_version.minor}.{py_version.micro}")
    
    # Check for pip
    pip_available = shutil.which("pip3") or shutil.which("pip")
    if not pip_available and sys.platform != "win32":
        print(f"  ⚠ pip not found. Trying to install...")
        subprocess.run([sys.executable, "-m", "ensurepip", "--upgrade"], 
                      capture_output=True)
        pip_available = True
    
    # Install Python packages (only if missing)
    required_packages = []
    try:
        import numpy
    except ImportError:
        required_packages.append("numpy")
    
    try:
        import psutil
    except ImportError:
        required_packages.append("psutil")
    
    try:
        import readline
    except ImportError:
        if sys.platform == "win32":
            required_packages.append("pyreadline3")
    
    if required_packages and pip_available:
        print(f"  📦 Installing Python packages: {', '.join(required_packages)}")
        pip = shutil.which("pip3") or shutil.which("pip") or "pip3"
        subprocess.run([pip, "install"] + required_packages, capture_output=False)
    
    # Check for system tools (non-critical, note what's missing)
    missing_tools = []
    for tool, purpose in [
        ("whisper-cli", "voice input (whisper.cpp)"),
        ("espeak-ng", "text-to-speech"),
        ("mpv", "media playback"),
        ("w3m", "web viewer (CLI browser)"),
    ]:
        if not shutil.which(tool):
            missing_tools.append((tool, purpose))
    
    if missing_tools:
        print(f"\n  ℹ Optional tools not found (features will be limited):")
        for tool, purpose in missing_tools:
            print(f"     • {tool} — {purpose}")
        
        # Auto-install on Linux via apt/apk
        if sys.platform == "linux":
            installable = [t for t, _ in missing_tools if t in 
                         ["espeak-ng", "mpv", "w3m", "lynx"]]
            if installable:
                print(f"     Attempting to install: {' '.join(installable)}")
                for pm in ["apt-get", "apk", "dnf", "yum", "pacman"]:
                    if shutil.which(pm):
                        install_cmd = {
                            "apt-get": ["apt-get", "install", "-y"],
                            "apk": ["apk", "add"],
                            "dnf": ["dnf", "install", "-y"],
                            "yum": ["yum", "install", "-y"],
                            "pacman": ["pacman", "-S", "--noconfirm"],
                        }.get(pm, [pm, "install"])
                        try:
                            subprocess.run(install_cmd + installable, 
                                         capture_output=False, timeout=120)
                        except:
                            pass
                        break
    
    print(f"  ✓ Dependencies checked")

def first_run_setup(sid_dir: Path):
    """Run first-time configuration."""
    print(f"\n  ⚙ First-run setup...")
    
    # Create SID directories
    for d in ["/sid/models", "/sid/memory", "/sid/logs"]:
        p = sid_dir / d.lstrip('/') if sys.platform != "win32" else sid_dir / d.strip('/')
        p.mkdir(parents=True, exist_ok=True)
    
    # Create default config files
    config_dir = sid_dir / "config"
    if not (config_dir / ".configured").exists():
        print(f"  • Creating default configuration...")
        (config_dir / ".configured").write_text("configured=true\n")
    
    # Try to download a tiny model for immediate use
    print(f"  • Would you like to download a small AI model now?")
    print(f"    This enables offline AI (no internet needed later)")
    try:
        resp = input(f"  Download tiny model (~500MB)? [Y/n]: ").strip().lower()
        if resp != 'n':
            print(f"  📥 Downloading Llama 3.2 1B (this may take a while)...")
            # Use the download_model helper
            if (sid_dir / "src/tools/download_model.py").exists():
                subprocess.run([sys.executable, "src/tools/download_model.py", 
                              "Llama-3.2-1B-Instruct"], cwd=str(sid_dir))
    except (EOFError, KeyboardInterrupt):
        print()
    
    print(f"  ✓ First-run setup complete")

def print_banner():
    banner = f"""
{'='*55}
   ███████╗██╗██████╗      ██████╗ ███████╗
   ██╔════╝██║██╔══██╗    ██╔═══██╗██╔════╝
   ███████╗██║██║  ██║    ██║   ██║███████╗
   ╚════██║██║██║  ██║    ██║   ██║╚════██║
   ███████║██║██████╔╝    ╚██████╔╝███████║
   ╚══════╝╚═╝╚═════╝      ╚═════╝ ╚══════╝
   SUPER INTELLIGENT DISTRO    v{SID_VERSION}
{'='*55}"""
    print(banner)

def show_help():
    print(f"""
SID OS Bootstrap — Zero-dependency launcher

USAGE:
  python3 get-sid.py              Download and launch SID
  python3 get-sid.py --setup      Download + install deps + launch  
  python3 get-sid.py --update     Update to latest version
  python3 get-sid.py --help       This help

EXAMPLES:
  # First time (download + run):
  python3 get-sid.py
  
  # Full setup with dependencies:
  python3 get-sid.py --setup

  # Already downloaded, just update:
  python3 get-sid.py --update

REQUIREMENTS:
  - Python 3.8+ (any OS)
  - Internet connection (first run only)
  - 4GB RAM recommended
  - No GPU required

That's it. No wget, no curl, no git, no nothing else.
""")

if __name__ == "__main__":
    main()
