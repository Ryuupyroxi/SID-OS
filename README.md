# ╔══════════════════════════════════════════╗
# ║     SID - Super Intelligent Distro       ║
# ║     v1.0 - For Old Hardware             ║
# ╚══════════════════════════════════════════╝

SID is an extremely lightweight, CLI-based Linux distribution designed to breathe new life into old hardware (4GB RAM minimum). It features a fully embedded AI system that works completely offline using small open-source models, with the ability to swap in any API key for cloud AI access.

## ✨ Features

- **🖥️ 80s Hacking Terminal Aesthetic** - Green/amber phosphor themes, retro boot screen, matrix-style UI
- **🤖 Embedded AI** - Runs locally with llama.cpp; supports Llama, Phi, Qwen, Gemma models
- **🎤 Voice Control** - Full voice operation via whisper.cpp (offline STT) + espeak/piper TTS
- **🧠 Intelligent Context Compression** - Multi-strategy compression maximizes small model context windows
- **💾 Persistent Memory** - SQLite-based episodic + semantic memory with automatic compression
- **⚡ Hardware Optimization** - Auto-tunes CPU governor, swappiness, cache pressure for old hardware
- **🔌 Plug & Play** - Simple installer with hardware detection; no technical knowledge needed
- **🌐 Online/Offline** - Works fully offline with local models; add API key for cloud AI
- **🔧 AI Tools Suite** - Code assistant, file manager, system analyzer, search engine

## 🚀 Quick Start

### Option 1: Install SID OS (Bare Metal)
```bash
# Download the SID ISO and write to USB
dd if=sid-1.0.0-x86_64.iso of=/dev/sdX bs=4M status=progress
# Boot from USB and follow the installer
```

### Option 2: Run in Development Mode
```bash
git clone [repo]/sid
cd sid
python3 src/main.py --theme green
```

### Option 3: Build Your Own ISO
```bash
cd build
./scripts/build-sid.sh
# Output: sid-1.0.0-x86_64.iso
```


## 🧪 Testing Guide (for Xander)

### Quick Smoke Test
```bash
# Clone and run in dev mode — no build needed
git clone https://github.com/Ryuupyroxi/SID-OS.git
cd SID-OS
python3 test_sid.py --verbose
```

### Run the Full Test Suite
```bash
python3 test_sid.py --online --verbose
```

Tests cover:
- AI Engine initialization & model management
- Context compression engine
- Memory system (working, episodic, semantic)
- Voice system (STT, TTS, VAD detection)
- Hardware monitor & system optimizer
- All AI tools (code assistant, file manager, search, system analyzer)
- Media player, offline storage, browser file explorer
- Theme manager, soul system, settings manager
- Agent skill framework & tool registry

### Dev Mode (interactive)
```bash
# Launch SID OS directly (no VM needed)
python3 src/main.py --theme green

# With debug logging
python3 src/main.py --theme green --verbose

# Commands to try inside SID:
ai              # Launch AI assistant
sys info        # System information
sys mem         # Memory usage
sys temp        # CPU temperature
sys optimize    # Run performance optimization
models list     # Available AI models
voice           # Voice control mode
```

### Building an ISO (for VM or bare metal)
```bash
./build/scripts/build-sid.sh
# Output: sid-1.0.0-x86_64.iso
```

### Tips for Xander 🎯
1. **Start with** `test_sid.py` — it validates every component without needing a VM
2. **Dev mode is your friend** — no need to build the ISO for functional testing
3. **Log issues clearly** — paste the test output + which component failed
4. **Check AGENTS.md** for the full architecture overview before diving into code
5. **PRs welcome** — bug fixes, new tools, theme tweaks, anything

## 📋 Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **RAM** | 2GB | **4GB** |
| **CPU** | Dual-core | Quad-core |
| **Disk** | 4GB | 8GB+ |
| **Arch** | x86_64 | x86_64 |
| **GPU** | Not required | Any |

## 🎮 Basic Usage

### AI Assistant
```
sid@sidOS:~$ ai
sid-ai> what files are in my home directory?
```

### Voice Control
```
sid@sidOS:~$ voice
[SID] Listening...
> "Show me system information"
```

### System Management
```
sid@sidOS:~$ sys info     # System information
sid@sidOS:~$ sys temp     # Temperature monitor
sid@sidOS:~$ sys mem      # Memory usage
sid@sidOS:~$ sys optimize # Run optimization
```

### Model Management
```
sid@sidOS:~$ models list              # Available models
sid@sidOS:~$ install model llama      # Download a model
sid@sidOS:~$ model use llama-3.2-1b   # Switch model
sid@sidOS:~$ config set api_key sk-... # Add API key
```

## 🎨 Themes

```
sid@sidOS:~$ config set theme green    # Classic green phosphor
sid@sidOS:~$ config set theme amber    # Amber terminal
sid@sidOS:~$ config set theme matrix   # Matrix rain
sid@sidOS:~$ config set theme blue     # Blue screen
sid@sidOS:~$ config set theme vintage  # Vintage Apple
```

## 🧠 How The AI Works

1. **Model Selection**: Auto-detects best available model (local GGUF > API > Python fallback)
2. **Context Compression**: Multiple strategies compress conversation history:
   - Sliding window with summarization of older messages
   - Key information extraction
   - Deduplication
   - Token-aware trimming
3. **Memory System**: Three-tier memory:
   - **Working**: FIFO queue for immediate context
   - **Episodic**: SQLite database of past interactions
   - **Semantic**: Extracted knowledge and patterns
4. **Hardware Awareness**: Monitors CPU temp, RAM, and disk; adjusts model size and optimization accordingly

## 🔧 Configuration Files

- `/etc/sid/ai.json` - AI engine configuration
- `/etc/sid/hardware.json` - Hardware monitoring settings
- `/sid/config/models/registry.json` - Model registry
- `~/.sid_history` - Command history

## 🤝 Contributing

1. Add new AI models to `config/models/registry.json`
2. Add themes to `src/terminal/theme/manager.py`
3. Add tools to `src/tools/`
4. Follow AGENTS.md guidelines

## 📄 License

MIT - Open source and free for everyone.

## ⚡ Powered By

- [llama.cpp](https://github.com/ggerganov/llama.cpp) - CPU-optimized LLM inference
- [whisper.cpp](https://github.com/ggerganov/whisper.cpp) - Offline speech recognition
- [Alpine Linux](https://alpinelinux.org/) - Minimal base system
- [SQLite](https://sqlite.org/) - Lightweight persistent storage
