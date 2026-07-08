# ╔══════════════════════════════════════════════════════════╗
# ║  ███████╗██╗██╗     ██╗███████╗██████╗  ██████╗ ███████╗ ║
# ║  ██╔════╝██║██║     ██║██╔════╝██╔══██╗██╔═══██╗██╔════╝ ║
# ║  ███████╗██║██║     ██║█████╗  ██████╔╝██║   ██║███████╗ ║
# ║  ╚════██║██║██║     ██║██╔══╝  ██╔══██╗██║   ██║╚════██║ ║
# ║  ███████║██║███████╗██║██║     ██║  ██║╚██████╔╝███████║ ║
# ║  ╚══════╝╚═╝╚══════╝╚═╝╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚══════╝ ║
# ║                                                          ║
# ║     v1.2.0 — AI-First CLI OS for Old Hardware            ║
# ║     Fork of Alpine Linux                                 ║
# ╚══════════════════════════════════════════════════════════╝

**SID** (Super Intelligent Distro) is a lightweight CLI-based Linux distribution 
forked from Alpine Linux, designed for old hardware (4GB RAM target).  
AI is the primary interface — you navigate the OS by talking to it.

> *"The eyes of the world are upon you, and the hopes and the prayers 
>  of liberty-loving people everywhere march with you."*

[![Download](https://img.shields.io/github/v/release/Ryuupyroxi/SID-OS?label=Download&color=brightgreen)](https://github.com/Ryuupyroxi/SID-OS/releases/latest)
[![Tests](https://img.shields.io/badge/tests-87%2F87-passing-brightgreen)](https://github.com/Ryuupyroxi/SID-OS/blob/main/test_sid.py)
[![UEFI](https://img.shields.io/badge/UEFI-BIOS%20%2B%20EFI-blueviolet)](https://github.com/Ryuupyroxi/SID-OS)
[![License](https://img.shields.io/badge/license-MIT-blue)](https://github.com/Ryuupyroxi/SID-OS/blob/main/LICENSE)

## 🚀 Quick Start

### Option 1: Linux/macOS — One-Command Bootstrap
> Requires Python 3.8+ (pre-installed on most systems)
```bash
# Requires Python 3.8+ (pre-installed on most Linux/macOS)
python3 -c "$(python3 -c "import urllib.request; print(urllib.request.urlopen('https://raw.githubusercontent.com/Ryuupyroxi/SID-OS/main/get-sid.py').read().decode())")" --setup

# Or download and run offline:
python3 -c "import urllib.request; open('get-sid.py','w').write(urllib.request.urlopen('https://raw.githubusercontent.com/Ryuupyroxi/SID-OS/main/get-sid.py').read().decode())"
python3 get-sid.py --setup
```

### Option 2: Windows (Python NOT included — get it first)
Windows doesn't ship with Python, so SID OS includes two bootstrap methods:

**Method A — Menu-driven launcher (recommended):**
Download `get-sid.bat` from the [Releases page](https://github.com/Ryuupyroxi/SID-OS/releases), place it in any folder,
and double-click. It will check for Python, guide you through installation if needed, then download and run SID.

**Method B — PowerShell bootstrap (built into Windows 7+):**
```powershell
# Open PowerShell and run:
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/Ryuupyroxi/SID-OS/main/get-sid.ps1" -OutFile "get-sid.ps1"
.\get-sid.ps1 -Setup
```

**Method C — Manual (if you already have Python):**
```batch
cd sid-1.2.0-portable
python src\main.py --theme vt100
```

> **Note**: Full AI features require Python 3.8+ (download from python.org). Windows does not ship with Python.
> The portable release includes `get-sid.bat`, `get-sid.ps1`, and Linux `./sid` launcher.

> **Note**: Windows support is limited to the Python-based AI features. Hardware monitoring, voice, and system commands are Linux-only.

### Option 3: Clone and Run (for developers/testers)
```bash
git clone https://github.com/Ryuupyroxi/SID-OS.git
cd SID-OS
python3 src/main.py --theme vt100

# Run the test suite
python3 test_sid.py --verbose


### Option 4: Bootable ISO — Full OS Installation (recommended for old hardware)
> Supports **BIOS (Legacy)** and **UEFI (x86_64)** boot
[![Download](https://img.shields.io/github/v/release/Ryuupyroxi/SID-OS?label=Download+ISO&color=brightgreen)](https://github.com/Ryuupyroxi/SID-OS/releases/latest)

Download `sid-*-live-x86_64.iso` from the [Releases page](https://github.com/Ryuupyroxi/SID-OS/releases/latest).

**On Windows — flash with Rufus:**
1. Download [Rufus](https://rufus.ie) (portable is fine)
2. Plug in a USB drive (8GB+, everything on it will be erased)
3. Open Rufus, select your USB, pick the ISO
4. Click START — when prompted, choose **"Write in DD Image mode"** (not ISO mode)
5. Wait for "Ready", then reboot

**On Linux — flash with dd:**
```bash
# Find your USB device (e.g. /dev/sdb) — be careful!
lsblk
sudo dd if=sid-1.2.0-live-x86_64.iso of=/dev/sdb bs=4M status=progress
```

**Boot & install:**
1. Plug the USB in, reboot, spam F9 (or F10/F12/Esc/Del) to enter boot menu
   - BIOS systems: Select USB from the menu
   - UEFI systems: Select the UEFI USB option (or disable Secure Boot if needed)
2. You'll see the ISOLINUX boot menu (BIOS) or GRUB menu (UEFI)
   - Choose "SID OS" for normal boot, "Safe Mode" for troubleshooting
3. Login as `root` (no password), connect phone via USB tether:
   ```bash
   ip link set usb0 up
   udhcpc -i usb0
   ```
4. Run the automated installer:
   ```bash
   wget -O /tmp/sid-answers.conf https://raw.githubusercontent.com/Ryuupyroxi/SID-OS/main/installer/sid-answers.conf
   setup-alpine -f /tmp/sid-answers.conf
   ```
5. Enter a root password, type `sda` for the disk, `sys` for filesystem, `y` to confirm
6. After install: `poweroff`, unplug USB, reboot — login as root, then:
   ```bash
   apk add curl python3
   curl -sL https://raw.githubusercontent.com/Ryuupyroxi/SID-OS/main/get-sid.py | python3
   ```
   SID auto-launches on every boot after that.

> **Need every detail?** See [`INSTALL.md`](INSTALL.md) for the full guide.

### Option 5: Persistent USB OS (full Alpine + SID)
> After boot, all host partitions are auto-mounted under `/mnt/host/`
> Access Windows (NTFS), Linux (ext4), and external drives (exFAT) immediately.
```bash
# Boot Alpine 3.24.1 from USB -> login as root
# Run setup-alpine, install to your USB (/dev/sda)
# Reboot into persistent Alpine USB, then:
apk add curl python3
curl -sL https://raw.githubusercontent.com/Ryuupyroxi/SID-OS/main/get-sid.py | python3
# SID auto-launches on every boot after that
```

### Option 6: Install to disk (advanced)
```bash
git clone https://github.com/Ryuupyroxi/SID-OS.git
cd SID-OS
python3 installer/scripts/install.py
```

## ✨ What's Inside

### 🖥️ Live ISO Features (v1.2.0)
| Feature | Status |
|---------|--------|
| **BIOS Boot** (ISOLINUX) | ✅ Legacy PC boot |
| **UEFI Boot** (GRUB x64) | ✅ Modern firmware boot |
| **Host FS Access** | ✅ Auto-mounts NTFS/ext4/exfat/HFS+ under `/mnt/host/` |
| **WiFi Connect** | ✅ `wifi-connect <SSID> [pass]` helper |
| **Live Installer** | ✅ `setup-alpine` + answer file |
| **SID Auto-Launch** | ✅ On tty1 login |
| **DevMode** | ✅ Hidden system diagnostics — type `devmode` at login |

[![ASCII Art](https://img.shields.io/badge/STYLE-Retro%20Hacker-brightgreen)](https://github.com/Ryuupyroxi/SID-OS)

### 🧠 Core AI Platform

- **🧠 AI Engine** — Local Qwen models (0.5B router to 7B specialist) + any API key (OpenAI, Anthropic, Gemini, Groq)
- **🎤 Voice Control** — Offline STT (whisper.cpp) + TTS (espeak/piper)
- **🗄️ 3-Tier Memory** — Working / Episodic (SQLite) / Semantic
- **🧩 Context Compression** — Sliding window, summarization, dedup, trimming
- **🔀 Router Model** — Tiny 468MB Qwen2.5-0.5B always-on conductor for intent routing
- **🤖 Agentic Framework** — Hermes-inspired skill learning & tool use
- **💾 Soul File** — Persistent personality (`/etc/sid/soul.json`)
- **🖥️ 18 Retro Themes** — VT100, Apple II, C64, NeXTSTEP, etc.
- **🌐 Web Viewer** — CLI browser with auto-offline cache
- **🎨 Image Tools** — Generation, editing, format conversion
- **📦 Offline Storage** — Web/wiki compression for offline access
- **⚡ Hardware Monitor** — CPU temp, RAM, disk, auto-optimization
- **🔧 Skills System** — `skills list/learn/execute/search`
- **📊 Benchmark** — `benchmark quick` to find the best model for your hardware

## 🥚 Hidden Features & Easter Eggs

```
SID OS v1.2.0 — Super Intelligent Distro
  Type 'devmode' for system diagnostics
```

When you boot the live ISO, you'll see this prompt. Type **`devmode`** at the login 
shell to enter the hidden diagnostic terminal — a tribute to the Apollo-era mission 
control aesthetic. It shows kernel version, memory, CPU, and all mounted host partitions.

Inside the SID shell, try:
```
sid⏣ help easter      # Show hidden commands
sid⏣ sys easter       # Another way to find secrets
```

## 🎮 Basic Usage

Once inside SID:

```
sid⏣ ai                    # AI assistant mode
sid⏣ sys info             # System information
sid⏣ sys mem              # Memory usage
sid⏣ sys temp             # CPU temperature
sid⏣ install quick 4gb    # Auto-setup AI for 4GB RAM
sid⏣ models list          # Available AI models
sid⏣ config set theme vt100  # Change theme
sid⏣ soul show            # View SID's personality
sid⏣ skills list          # List available skills
sid⏣ image generate "a retro computer"  # Generate image
sid⏣ web view http://example.com        # Browse with offline cache
sid⏣ cache status         # Offline cache stats
sid⏣ benchmark            # Hardware benchmark
sid⏣ settings show        # Advanced settings
sid⏣ help                 # Full command reference
```
Just type naturally — the AI understands:
```
sid⏣ what's my CPU temperature?
sid⏣ show me the disk space
sid⏣ play some music from ~/Music
sid⏣ search memory for that thing we talked about earlier
```

## 🧪 Testing

```bash
python3 test_sid.py                    # Quick test (87 tests)
python3 test_sid.py --verbose          # Detailed output
python3 test_sid.py --online           # Include network tests
```

## 📋 Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM       | 2GB     | **4GB**     |
| CPU       | Dual-core | Quad-core |
| Disk      | 4GB     | 8GB+        |
| Arch      | x86_64  | x86_64      |
| GPU       | Not required | Any    |

## 🎨 Retro Computer Themes

```
sid⏣ config set theme vt100       # DEC VT100 (1978) — default
sid⏣ config set theme ibm3270    # IBM 3270 (1971)
sid⏣ config set theme apple2     # Apple II (1977)
sid⏣ config set theme c64        # Commodore 64 (1982)
sid⏣ config set theme trs80      # TRS-80 (1977)
sid⏣ config set theme altair     # Altair 8800 (1975)
sid⏣ config set theme nextstep   # NeXT Computer (1988)
sid⏣ config set theme teletype   # ASR-33 Teletype (1963)
sid⏣ config set theme zx_spectrum # ZX Spectrum (1982)
sid⏣ config set theme amiga      # Amiga Workbench (1985)
theme list                         # See all 19 themes
```

## 🐛 Troubleshooting (HP Pavilion & similar)

**"python3 not found"** — Some old systems have `python` instead of `python3`:
```bash
python src/main.py --theme vt100
```

**"No module named ..."** — Make sure you're in the SID-OS directory:
```bash
cd SID-OS
python3 src/main.py --theme vt100
```

**Permission denied** — The main.py needs execute permission:
```bash
chmod +x src/main.py
```

**"Command not found" in shell** — Commands like `ai`, `sys`, `models` are typed *inside* SID's shell, not in bash. Run `python3 src/main.py` first.

**Black screen / no output** — Try the safe mode theme:
```bash
python3 src/main.py --theme terminal
```

## 🏷️ Labels
- **OS Name**: SID OS (Super Intelligent Distro)
- **Base**: Fork of Alpine Linux 3.24.1
- **License**: MIT
- **Versioning**: `vMAJOR.MINOR.BUGFIX`
- **Platform**: x86_64 (BIOS + UEFI)



## 🎭 Animated Assistant Mascot

A terminal-based animated character that sits above your prompt:

```
sid⏣ config set assistant on       # Enable mascot
sid⏣ config set assistant off      # Disable
sid⏣ config set character neko     # Switch character
```

Characters react to AI state: idle → thinking (eye narrow) → speaking (mouth animates).
Built-in: **sid-bot**, **neko** (cat), **droid**. Add custom ones via `.sidchar` files.

## 💾 Profile Export/Import

Share your entire SID OS assistant — settings, soul, memories, skills, and characters:

```
sid⏣ profile export                 # Export everything to .sidprofile
sid⏣ profile import <file>          # Import from .sidprofile
sid⏣ profile share <character>      # Export a character as .sidchar
sid⏣ profile load <file.sidchar>    # Import a shared character
sid⏣ profile dry-run <file>         # Preview import without writing
```

Share `.sidchar` files with other SID OS users — they get your character instantly.

## 📁 Project Structure

```
SID-OS/
├── src/                # All Python source
│   ├── main.py         # Entry point
│   ├── ai/             # Orchestrator, models, context, prompts
│   ├── agent/          # Hermes-inspired agentic framework
│   ├── soul/           # Personality/memory core
│   ├── voice/          # STT, TTS, VAD
│   ├── terminal/       # Shell, themes, voice button
│   ├── memory/         # 3-tier memory system
│   ├── system/         # Hardware monitor, optimizer, boot
│   └── tools/          # 10+ AI-powered tools
├── config/             # AI, hardware, soul, skills configuration
├── build/              # ISO builder
├── installer/          # Plug-and-play installer
├── test_sid.py         # 84-test suite
└── AGENTS.md           # Full architecture documentation
```

## 🔧 Config Files

| File | Purpose |
|------|---------|
| `/etc/sid/ai.json` | AI engine settings |
| `/etc/sid/soul.json` | Personality & user profiles |
| `/etc/sid/settings.json` | Advanced settings |
| `/var/lib/sid/memory/` | Episodic + semantic memory (SQLite) |
| `/var/lib/sid/cache/` | Offline web/media cache |
| `/sid/models/` | Downloaded GGUF models |

## 📄 License

MIT — free for everyone.

## ⚡ Powered By

- [llama.cpp](https://github.com/ggerganov/llama.cpp) — CPU-optimized LLM inference  
- [whisper.cpp](https://github.com/ggerganov/whisper.cpp) — Offline speech recognition  
- [SQLite](https://sqlite.org/) — Lightweight persistent storage
