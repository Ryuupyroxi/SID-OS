# SID OS - Super Intelligent Distro

## Architecture Overview

SID is a lightweight CLI-based Linux distribution designed for old hardware (4GB RAM) with embedded AI capabilities. The system is built around a modular Python-based AI engine that supports both local LLMs (via llama.cpp GGUF models) and cloud API providers.

## Directory Structure

```
sid/
├── src/                    # All source code
│   ├── main.py            # Entry point
│   ├── ai/                # AI engine
│   │   ├── engine/        # Orchestrator, Model Manager
│   │   ├── context/       # Context compression
│   │   └── prompts/       # Optimized prompt templates
│   ├── voice/             # Voice system
│   │   ├── stt/           # Speech-to-text (whisper.cpp)
│   │   ├── tts/           # Text-to-speech (espeak/piper)
│   │   └── vad/           # Voice activity detection
│   ├── terminal/          # CLI interface
│   │   ├── shell/         # SID Shell (cmd.Cmd-based)
│   │   ├── theme/         # 80s retro themes
│   │   └── ui/            # Voice button overlay
│   ├── system/            # System management
│   │   ├── hardware/      # Hardware monitoring
│   │   ├── optimizer/     # Performance optimization
│   │   └── init/          # Boot sequence
│   ├── memory/            # Memory system
│   │   ├── short/         # Working memory (FIFO)
│   │   ├── long/          # Episodic + Semantic memory (SQLite)
│   │   └── compression/   # Memory compression engine
│   └── tools/             # AI-powered tools
│       ├── code/          # Code assistant
│       ├── files/         # File manager
│       ├── search/        # Search engine
│       └── system/        # System analyzer
├── build/                 # Build system
│   ├── scripts/build-sid.sh  # Complete build script
│   └── docker/Dockerfile  # Build container
├── config/                # Configuration files
│   ├── ai.json           # AI engine config
│   ├── hardware.json     # Hardware monitoring config
│   ├── models/           # Model registry
│   └── themes/           # Theme settings
├── installer/            # Installation system
│   └── scripts/install.py # Interactive installer
├── isoprofile/           # ISO build profile
└── docs/                 # Documentation
```

## Coding Conventions

- **Python 3.12+** with type hints throughout
- **80s hacking terminal aesthetic**: green/amber phosphor themes, retro boot screen, matrix-style elements
- **Offline-first**: All AI features must work with local models first, API as enhancement
- **Memory-aware**: Never exceed `memory_limit_mb` from config; use context compression aggressively
- **Error-tolerant**: Graceful degradation when models not available

## AI Engine Rules

1. **Model Priority**: Local > API > Python fallback
2. **Context Management**: Always compress conversations >5 messages using sliding window + summarization
3. **Memory System**: Store every interaction; compress weekly; prioritize recent
4. **Prompt Optimization**: Use short, structured prompts optimized for small models (<3B params)
5. **Token Budgeting**: Never exceed context_window; warn user if approaching limit

## Key Design Decisions

- **Python for AI layer**: Maximizes flexibility and ease of modification
- **C/C++ for performance**: llama.cpp and whisper.cpp handle inference
- **SQLite for persistence**: No heavy database dependencies
- **cmd.Cmd for shell**: Built-in Python library, easy to extend
- **No GPU requirement**: Optimized for CPU inference on old hardware

## Performance Targets

- **Boot time**: <15 seconds on 4GB RAM hardware
- **AI response time**: <5 seconds for tiny models, <15s for medium
- **Memory usage**: <512MB for base system, <1GB for AI with tiny model
- **Disk space**: <2GB for base install, <4GB with one AI model

## Extension Guidelines

- Place new AI tools in `src/tools/` with a `process()` method
- Register new models in `config/models/registry.json`
- Add themes to `ThemeManager.THEMES` dict
- Voice backends auto-detected; add new ones to `STTEngine`/`TTSEngine`

## Build Instructions

```bash
# Quick development run
python3 src/main.py --theme green

# Full ISO build (requires Docker or Alpine build environment)
cd build && ./scripts/build-sid.sh

# Installation
python3 installer/scripts/install.py
```
