# SID OS - Super Intelligent Distro (v1.0.0)

## Architecture Overview

SID is lightweight CLI-based Linux distribution for old hardware (4GB RAM)
with deeply integrated AI system that functions as primary OS interface.

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

## Key Features (v1.0.0)

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
| **BUGFIX** | Bug fixes, small tweaks, docs | `v1.0.0` → `v1.0.1` |
| **MINOR** | New features, non-breaking changes | `v1.0.0` → `v1.1.0` |
| **MAJOR** | Breaking changes, stable releases | `v1.0.0` → `v2.0.0` |

### Pushing new version
```bash
git tag -a v1.0.1 -m "Description of changes"
git push origin v1.0.1
```

### Release naming
- `v1.0.0` — First public release (Stable)
- `v1.x.x` — Production-ready

### Version history
- `v1.0.0` — First public release: bootable ISO, install guide, CI automation
- `v0.5.3` — Release candidate: bootable ISO with busybox initramfs
- `v0.5.2` — Beta: portable tarball and ISO builder, Windows bootstrap, persistent memory
- `v0.5.0` — Alpha: agentic framework, soul, retro themes, offline tools
- `v0.0.1` — Initial scaffold

## Releasing new version

### Automatic (GitHub Actions)
Push tag and CI builds everything:
```bash
git tag -a v1.0.1 -m "description"
git push origin v1.0.1
```
This triggers `.github/workflows/build-iso.yml` which:
1. Builds bootable `.iso` from Alpine base + SID OS
2. Creates portable `.tar.gz` for non-ISO use
3. Creates GitHub Release with all artifacts attached

### Manual (build portable tarball locally)
```bash
./build/scripts/make-portable.sh
# Output: build/output/sid-1.0.0-portable.tar.gz
```

### Manual (build full ISO — requires x86_64 + build tools)
```bash
./build/scripts/build-sid.sh
# Output: build/output/sid-1.0.0-x86_64.iso
```

### Portable tarball contents
```
sid-1.0.0-portable/
├── sid              # Launcher: ./sid --theme vt100
├── sid-install      # Installer: sudo ./sid-install
├── sid-test         # Test suite: ./sid-test --verbose
├── src/             # All source code
├── config/          # Configuration files
├── installer/       # Installation wizard
├── AGENTS.md        # Architecture documentation
├── README.md        # This file
├── BOOT_HELPER.md   # Quick start guide
└── test_sid.py      # Test suite
```

## ISO Build Reference (for Codex)

### Quick rebuild
```bash
# Dev: build locally (run from repo root)
bash build/scripts/build-live-iso.sh
# Output: build/output/sid-1.0.0-live-x86_64.iso

# Release: tag + push triggers CI
git tag -a v1.0.0 -m "description"
git push origin v1.0.0
# CI builds, uploads artifact, publishes Release
```

### Build process (file-based, no QEMU needed)
1. Download Alpine minirootfs → extract
2. Download APKINDEX → find package versions
3. Download .apk packages → extract into rootfs
4. Install SID OS source → /opt/sid
5. Configure inittab, profile, services
6. mksquashfs rootfs → sid.squashfs
7. Build initramfs with busybox + init script
8. Copy kernel, squashfs, initramfs → ISO dir
9. Get isolinux/syslinux for BIOS boot
10. xorriso → bootable sid-*.iso

### Key files
- `build/scripts/build-live-iso.sh` — ISO builder
- `build/scripts/make-portable.sh` — Portable tarball builder
- `.github/workflows/build-iso.yml` — CI pipeline
- `installer/sid-answers.conf` — Answer file for setup-alpine
