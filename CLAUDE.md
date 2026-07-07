# SID OS — Persistent Memory

## Current Versions
- SID OS: v1.2.0
- Alpine: 3.24.1
- Versions in: `src/__init__.py`, `get-sid.py`, `get-sid.ps1`, `get-sid.bat`, `README.md`, `AGENTS.md`, build scripts, config, installer

## Bump Checklist
| What | Where |
|---|---|
| SID OS version | grep `0.X.Y` across ~25 files (skip `127.0.0.1`) |
| Alpine version | `build/scripts/build-live-iso.sh` (VERSION + MIRROR) |
| Alpine ISO URL | `build/scripts/create-usb.sh` |

## Architecture
- SID = Alpine + Python AI app (Alpine hidden)
- Entry: `src/main.py` → AI orchestrator
- Models: Qwen (0.5B router, 1.5B/3B/7B)
- Memory: 3-tier (Working → Episodic SQLite → Semantic SQLite)
- Context: 4 compression strategies (sliding window, summarization, dedup, trim)
- Portable tarball: primary dist, works Python 3.8+

## Build Files
- `build/scripts/build-live-iso.sh` — ISO builder
- `build/scripts/make-portable.sh` — Tarball builder
- `build/alpine-setup.sh` — Alpine → SID one-liner
- `get-sid.py` — Bootstrap (stdlib only)
- `get-sid.bat` / `get-sid.ps1` — Windows

## Installer
- `installer/scripts/install.py` — Wizard
- Options: API key, hardware test → auto-recommend models, or later
- Router model (Qwen 0.5B) included offline

## Notes
- Windows: Python NOT built-in. `get-sid.bat` guides user
- Voice: needs espeak/whisper.cpp system packages
- CI ISO build: needs admin log access
