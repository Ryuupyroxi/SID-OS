# ╔══════════════════════════════════════════╗
# ║     SID - Super Intelligent Distro       ║
# ║     v0.0.4 — AI-First CLI OS for Old Hardware            ║
# ╚══════════════════════════════════════════╝

SID is a lightweight CLI-based Linux distribution for old hardware (4GB RAM target).  
AI is the primary interface — you navigate the OS by talking to it.

[![Download](https://img.shields.io/github/v/release/Ryuupyroxi/SID-OS?label=Download&color=brightgreen)](https://github.com/Ryuupyroxi/SID-OS/releases/latest)
[![Tests](https://img.shields.io/badge/tests-84%2F84-passing-brightgreen)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()

## 🚀 Quick Start

### Option 1: One-Command Bootstrap (recommended — zero dependencies)
```bash
# Pure Python — no wget, curl, or git required:
# On Linux/macOS:
python3 -c "$(python3 -c "import urllib.request; print(urllib.request.urlopen('https://raw.githubusercontent.com/Ryuupyroxi/SID-OS/main/get-sid.py').read().decode())")" --setup

# Or save the script once, then run offline:
# python3 -c "import urllib.request; open('get-sid.py','w').write(urllib.request.urlopen('https://raw.githubusercontent.com/Ryuupyroxi/SID-OS/main/get-sid.py').read().decode())"
# python3 get-sid.py --setup
```

### Option 2: Windows
```batch
# Download the bootstrap script and run:
curl -O https://raw.githubusercontent.com/Ryuupyroxi/SID-OS/main/get-sid.py
python get-sid.py --setup

# Or download the portable .zip from the Releases page, extract, and run:
cd sid-0.0.4-portable
sid.bat --theme vt100

# Run tests:
sid-test.bat --verbose
```

> **Note**: Windows support is limited to the Python-based AI features. Hardware monitoring, voice, and system commands are Linux-only. The portable release includes both `sid.bat` (Windows) and `./sid` (Linux) launchers.

### Option 3: Clone and Run (for developers/testers)
```bash
git clone https://github.com/Ryuupyroxi/SID-OS.git
cd SID-OS
python3 src/main.py --theme vt100

# Run the test suite
python3 test_sid.py --verbose
```

### Option 4: Build a bootable ISO (advanced)
```bash
git clone https://github.com/Ryuupyroxi/SID-OS.git
cd SID-OS
./build/scripts/build-sid.sh
# Output: ./output/sid-0.0.4-x86_64.iso
```

### Option 5: Install to disk (advanced)
```bash
git clone https://github.com/Ryuupyroxi/SID-OS.git
cd SID-OS
python3 installer/scripts/install.py
```

## ✨ What's Inside

- **🧠 AI Engine** — Local models (Llama, Phi, Qwen, Gemma) + any API key
- **🎤 Voice Control** — Offline STT (whisper.cpp) + TTS (espeak/piper)
- **🗄️ 3-Tier Memory** — Working / Episodic (SQLite) / Semantic
- **🧩 Context Compression** — Sliding window, summarization, dedup, trimming
- **🤖 Agentic Framework** — Hermes-inspired skill learning & tool use
- **💾 Soul File** — Persistent personality (`/etc/sid/soul.json`)
- **🖥️ 19 Retro Themes** — VT100, Apple II, C64, NeXTSTEP, etc.
- **🌐 Web Viewer** — CLI browser with auto-offline cache
- **🎨 Image Tools** — Generation, editing, format conversion
- **📦 Offline Storage** — Web/wiki compression for offline access
- **⚡ Hardware Monitor** — CPU temp, RAM, disk, auto-optimization
- **🔧 Skills System** — `skills list/learn/execute/search`
- **📊 Benchmark** — `benchmark quick` to find the best model for your hardware

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
python3 test_sid.py                    # Quick test (84 tests)
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
