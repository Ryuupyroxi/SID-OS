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

SID_VERSION = "0.5.2"
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
    try:
        if sys.platform == "win32":
            os.execvp("python", ["python", "src/main.py", "--theme", "vt100"])
        else:
            os.execvp("python3", ["python3", "src/main.py", "--theme", "vt100"])
    except (FileNotFoundError, OSError):
        # Fallback: use subprocess
        import subprocess
        python_cmd = "python" if sys.platform == "win32" else "python3"
        subprocess.run([python_cmd, "src/main.py", "--theme", "vt100"])

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
    """Run first-time configuration with AI setup wizard."""
    print(f"\n  \u2699 First-run setup...")
    
    # Create SID directories
    for d in ["/sid/models", "/sid/memory", "/sid/logs"]:
        p = sid_dir / d.lstrip('/') if sys.platform != "win32" else sid_dir / d.strip('/')
        p.mkdir(parents=True, exist_ok=True)
    
    # Create default config files
    config_dir = sid_dir / "config"
    ai_config_path = config_dir / "ai.json"
    if not (config_dir / ".configured").exists():
        print(f"  \u2022 Creating default configuration...")
        (config_dir / ".configured").write_text("configured=true\n")
    
    # AI Setup Wizard
    print(f"\n  {'='*50}")
    print(f"  \U0001f916 AI Setup Wizard")
    print(f"  {'='*50}")
    print()
    print(f"  How would you like to configure AI for SID OS?")
    print()
    print(f"  [1] Enter API key  \u2014 Use an API provider (OpenAI, Groq, etc.)")
    print(f"                      Works immediately, requires internet")
    print()
    print(f"  [2] Download model \u2014 Hardware benchmark then download best model")
    print(f"                      Requires ~1-3GB download, then works fully offline")
    print()
    print(f"  [3] Set up later   \u2014 Skip AI config for now")
    print(f"                      Run 'sid' and configure manually later")
    print()
    
    try:
        resp = input(f"  Choose [1/2/3] (default: 3): ").strip()
        
        if resp == "1":
            print(f"\n  \U0001f510 API Key Setup")
            print(f"  Enter your API key (OpenAI, Groq, or any OpenAI-compatible provider)")
            api_key = input(f"  API key: ").strip()
            api_endpoint = input(f"  API endpoint [https://api.openai.com/v1]: ").strip() or "https://api.openai.com/v1"
            api_model = input(f"  Model name [gpt-4o-mini]: ").strip() or "gpt-4o-mini"
            
            import json
            cfg = json.loads(ai_config_path.read_text()) if ai_config_path.exists() else {}
            cfg.update({"mode": "api", "api_key": api_key, "api_endpoint": api_endpoint, "api_model": api_model, "offline_first": False})
            ai_config_path.write_text(json.dumps(cfg, indent=2))
            print(f"  \u2713 API key configured")
            if not api_key:
                print(f"  \u26a0 No key set. Fix with: sid config set api_key <key>")
        
        elif resp == "2":
            print(f"\n  \U0001f4e5 Model Download")
            print(f"  Checking hardware...")
            
            # Step 1: Let user pick which router model to download
            print(f"\n  \U0001f916 Step 1: Choose your conductor model")
            print(f"  The conductor is a tiny always-on AI that runs SID's basic")
            print(f"  functions even before you download a larger model.")
            print(f"")
            print(f"  [1] Qwen2.5-0.5B-Router  (468MB) - Tiny always-on conductor")
            print(f"  [2] Skip conductor      - No built-in AI, set up manually later")
            print(f"")
            try:
                router_choice = input(f"  Choose conductor [1]: ").strip() or "1"
            except:
                router_choice = "1"
            
            router_model = {"1": "Qwen2.5-0.5B-Router", "2": None}.get(router_choice)
            
            if router_model:
                print(f"\n  \U0001f4e5 Downloading {router_model}...")
                if (sid_dir / "src/tools/download_model.py").exists():
                    subprocess.run([sys.executable, "src/tools/download_model.py", router_model], 
                        cwd=str(sid_dir), capture_output=False)
                print(f"  \u2713 Conductor online!")
            else:
                print(f"  \u23f3 Skipping conductor. SID will use keyword-based mode.")
            
            # Step 2: Detect RAM tier for the main model
            try:
                import subprocess, json
                probe = subprocess.run([sys.executable, "-c", "import psutil; gb=psutil.virtual_memory().total//(1024**3); print('6gb' if gb>=6 else '4gb' if gb>=4 else '2gb')"], 
                    cwd=str(sid_dir), capture_output=True, text=True, timeout=15)
                detected = probe.stdout.strip()
                if detected not in ("2gb", "4gb", "6gb"):
                    detected = "4gb"
            except:
                detected = "4gb"
            
            print(f"\n  \U0001f4bb Step 2: Detected RAM: {detected.upper()} tier")
            
            # List available models for tier
            try:
                list_cmd = [sys.executable, "-c", f"""
import sys; sys.path.insert(0, "src")
from ai.engine.model_manager import ModelManager
class C: ram_tier="{detected}"; context_window=4096; api_key=""; api_endpoint=""
mm = ModelManager(C())
for m in mm.KNOWN_MODELS.get("{detected}_tier", []):
    if m.url: print(f"{{m.name}}|{{m.ram_required}}MB|{{m.context_length}}ctx|{{m.description}}")
"""]
                result = subprocess.run(list_cmd, cwd=str(sid_dir), capture_output=True, text=True, timeout=15)
                models = [l for l in result.stdout.strip().split("\n") if l]
            except:
                models = []
            
            print(f"\n  Now choose your main AI model (or skip to use just the conductor):")
            if models:
                default = models[0].split("|")[0]
                print(f"\n  Available models for {detected}:")
                for m in models:
                    parts = m.split("|")
                    print(f"    \u2022 {parts[0]} ({parts[1]}, {parts[2]})")
                chosen = input(f"\n  Download which model? (Enter to skip, or type name): ").strip()
                if chosen:
                    print(f"\n  \U0001f4e5 Downloading {chosen}...")
                    subprocess.run([sys.executable, "src/tools/download_model.py", chosen], cwd=str(sid_dir))
            else:
                print(f"  (no downloadable models listed for this tier)")
            
            import json
            cfg = json.loads(ai_config_path.read_text()) if ai_config_path.exists() else {}
            cfg.update({"mode": "local", "ram_tier": detected, "offline_first": True, "auto_download_models": False})
            ai_config_path.write_text(json.dumps(cfg, indent=2))
            print(f"  \u2713 Conductor model installed! SID can now run basic AI offline.")
            print(f"  Main model: {'ready' if chosen else 'skipped - run models download later'}")
        
        else:
            print(f"  \u23f3 Skipping. Configure later with: sid config, or re-run: python3 get-sid.py --setup")
    
    except (EOFError, KeyboardInterrupt):
        print()
    
    print(f"  \u2713 First-run setup complete")

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
