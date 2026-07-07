# SID OS — Persistent Memory

## Current Versions (as of 2026-07-07)
- **SID OS**: v0.5.2 (last bumped from v0.5.1)
- **Alpine Base**: 3.24.1 (updated from 3.20.3)
- **All version strings** live in: `src/__init__.py`, `get-sid.py`, `get-sid.ps1`, `get-sid.bat`, `README.md`, `AGENTS.md`, build scripts, config files, installer

## Bump Checklist (both must match)
| What | Where to change |
|---|---|
| SID OS version (`X.Y.Z`) | ~25 files — grep for `0.X.Y` across repo (skip `127.0.0.1`) |
| Alpine version (`3.XX.Y`) | `build/scripts/build-live-iso.sh` (ALPINE_VERSION + MIRROR) |
| Alpine ISO URL | `build/scripts/create-usb.sh` |

## Key Architecture
- **SID = Alpine Linux + Python AI app** (Alpine is the hidden base OS)
- **Entry**: `src/main.py` → AI orchestrator
- **Models**: Qwen family (0.5B router, 1.5B/3B/7B tiers)
- **Memory**: 3-tier (Working → Episodic SQLite → Semantic SQLite)
- **Context**: 4 compression strategies (sliding window, summarization, dedup, trim)
- **Portable tarball**: primary distribution, works anywhere with Python 3.8+

## Build Files
- `build/scripts/build-live-iso.sh` — Full Alpine → ISO builder
- `build/scripts/make-portable.sh` — Portable tarball builder  
- `build/alpine-setup.sh` — One-liner to turn Alpine into SID
- `get-sid.py` — Bootstrap (stdlib only, downloads + runs SID)
- `get-sid.bat` / `get-sid.ps1` — Windows launchers

## Installer
- `installer/scripts/install.py` — Installation wizard
- Option for: API key entry, hardware test → auto-recommend models, or set up later
- Router model (Qwen 0.5B) included as offline fallback brain

## Notes
- Windows: Python is NOT built-in. `get-sid.bat` checks and guides user.
- Voice backends need system packages (espeak/whisper.cpp)
- CI ISO build needs admin log access to debug
