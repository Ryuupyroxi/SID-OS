# SID OS - Super Intelligent Distro (v0.0.2)

## Architecture Overview

SID is a lightweight CLI-based Linux distribution for old hardware (4GB RAM) 
with a deeply integrated AI system that functions as the primary OS interface.

## Core Architecture

```
sid/
├── src/
│   ├── ai/engine/          # AI Orchestrator, Model Manager, Agentic Framework
│   ├── ai/context/         # Context Compression Engine
│   ├── ai/prompts/         # Memory-Optimized Prompt Templates
│   ├── agent/              # Hermes-Inspired Agentic Framework
│   │   ├── skill_manager.py  # Dynamic skill learning & execution
│   │   ├── skill_base.py     # Base skill class
│   │   └── tool_registry.py  # Tool registration for AI
│   ├── soul/               # Personality/Memory Core ("Soul File")
│   ├── voice/              # Offline STT, TTS, VAD
│   ├── terminal/           # AI-First CLI Shell, Retro Computer Themes
│   ├── memory/             # 3-Tier Memory (Working/Episodic/Semantic)
│   ├── system/             # Hardware Monitor, Optimizer, Boot
│   └── tools/              # 10+ AI-Powered Tools
├── config/
│   ├── soul/default.json   # Default personality configuration
│   ├── skills_registry.py  # Built-in skills catalog
│   └── ...                  # AI, hardware, theme configs
├── installer/              # Plug-and-play installation wizard
├── build/                  # ISO builder (Docker + scripts)
└── test_sid.py             # 84-test validation suite
```

## Key Features (v0.0.2)

### AI & Intelligence
- AI-First OS navigation - every command routes through AI
- 20+ AI models across 3 RAM tiers (2GB/4GB/6GB)
- Abliterated/uncensored models for unrestricted use
- Specialty models (code, medical, creative, reasoning)
- Router model for intelligent intent classification
- Hardware benchmark for optimal model recommendations

### Memory & Context
- Memory-Optimized Prompts - wording that preserves intelligence while managing context
- Context Compression (4 strategies: sliding window, summarization, dedup, trimming)
- 3-Tier Memory: Working → Episodic (SQLite) → Semantic (SQLite)
- Soul File - persistent personality and user profiles
- Achievements system for learning progress

### Tools & Capabilities
- CLI Media Player (mpv/ffplay/mplayer with offline cache)
- CLI Web Viewer (w3m/lynx with auto-offline cache switching)
- Browser-based File Explorer (HTTP server on localhost:2025)
- Offline Web/Wiki Storage (zlib/gzip compression)
- Image Generation & Editing (DALL-E/Stability/pillow)
- Code Assistant (generate, explain, debug, refactor)
- System Analyzer & Security Auditor
- Skills System (learn, add, execute skills dynamically)
- Agentic Framework (plan-execute-observe-adapt loop)

### Voice
- Offline STT via whisper.cpp
- TTS via espeak/piper/pyttsx3
- Voice Activity Detection (WebRTC)
- System tray voice button

### Hardware Optimization
- Auto-detects RAM tier (2GB/4GB/6GB)
- CPU governor auto-tuning
- Memory cache management
- Temperature monitoring
- Swap optimization
- Compatibility mode for old hardware (HP Pavilion etc.)

### Themes
- 19 Iconic CLI Computer Themes:
  DEC VT100, IBM 3270, Apple II, Commodore 64, TRS-80,
  Altair 8800, Xerox Alto, SGI Iris, Sun Micro, NeXTSTEP,
  IBM PC-DOS, Amiga Workbench, TeleType ASR-33, Dragon 32,
  ZX Spectrum, BBC Micro, Macintosh 128K, CP/M Osborne 1

## Quick Start

```bash
# Development mode
python3 src/main.py --theme vt100

# Full test suite
python3 test_sid.py

# RAM-tier quick setup (inside SID shell)
sid⏣ install quick 4gb

# Hardware benchmark
sid⏣ benchmark

# View personality
sid⏣ soul show

# Generate image
sid⏣ image generate "a retro computer terminal"

# Learn a skill
sid⏣ skills learn system_doctor

# Browse web offline
sid⏣ browse

# Full ISO build
cd build && ./scripts/build-sid.sh
```

## Coding Conventions

- Python 3.12+ with type hints
- Offline-first architecture
- Memory-conscious design
- Graceful degradation when models/tools unavailable
- All imports should be absolute (from <module> import <Class>)

## Performance Targets (4GB RAM)

- Boot: <15 seconds
- AI Response: <5s (tiny models), <15s (medium)
- OS Memory: <512MB base, +1GB with AI model
- Disk: <2GB base install, +2GB with one model

## Versioning & Tagging Convention

### Semantic Versioning
SID OS follows `vMAJOR.MINOR.BUGFIX` — nothing fancy.

| Bump | When | Example |
|------|------|---------|
| **BUGFIX** | Bug fixes, small tweaks, docs | `v0.0.1` → `v0.0.2` |
| **MINOR** | New features, non-breaking changes | `v0.0.2` → `v0.1.0` |
| **MAJOR** | Breaking changes, stable releases | `v0.1.0` → `v1.0.0` |

### Pushing a new version
```bash
git tag -a v0.0.3 -m "Description of changes"
git push origin v0.0.3
```

### Release naming
- **Pre-release**: `v0.x.x` — testing, unstable, experimental
- **Stable**: `v1.0.0` and up — production-ready
- **Beta/Candidate**: Use the message body to note status, not the tag itself

### Current versions
- `v0.0.1` — Initial scaffold
- `v0.0.2` — Beta: agentic framework, soul, retro themes, offline tools
