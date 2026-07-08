# SID OS — Agent Handoff Document

> For onboarding new agents. Updated: 2026-07-08
> Location: This file. Also check `/etc/sid/team/comms.md` for live team chat.

---

## Repo Structure

```
/root/SID-OS/
├── src/
│   ├── agent/            — Skill system (skill_base, skill_manager, tool_registry)
│   ├── ai/               — AI engine (orchestrator, model_manager, context, prompts)
│   ├── compat.py         — Compatibility layer
│   ├── config/           — Skills registry
│   ├── main.py           — Entry point
│   ├── memory/           — Memory system (working, episodic, semantic)
│   ├── system/           — OS-level (hardware monitor, boot, optimizer)
│   ├── terminal/
│   │   ├── assistant/    — Character system (charforge, charparts, controller, renderer)
│   │   ├── shell/        — SIDShell (cmd-based CLI)
│   │   ├── theme/        — Terminal themes (18 retro themes)
│   │   └── ui/           — UI components (voice_button, assistant display)
│   ├── tests/            — Test suite
│   ├── tools/            — Tool system (code, files, search, profile, media, etc.)
│   └── voice/            — Speech (STT, TTS, VAD)
├── build/                — ISO building scripts
├── config/               — JSON config files
├── installer/            — System installer
├── .githooks/            — Pre-commit linting hooks
├── AGENT_HANDOFF.md      — This file
├── TEAM_COMMS.md         — Legacy comms (moved offline)
└── README.md             — Public docs
```

---

## Key Data Locations

| What | Where |
|---|---|
| Characters | `/etc/sid/characters/<name>/` — spritesheet.png, metadata.json, parts.json, .cache/ |
| Built-in chars | `src/terminal/assistant/character.py` — CHARACTERS dict (sid-bot, neko, droid) |
| Team comms | `/etc/sid/team/comms.md` — offline only, not in git |
| Heartbeat log | `/root/Documents/Codex/2026-07-01/what-all-are-you-capable-of/heartbeat.log` |
| Token | `/root/.sid-token` (chmod 600) |
| Configs | `config/*.json` — ai.json, hardware.json, themes/, soul/ |
| Profile exports | via `sid⏣ profile export` → .sidprofile, .sidchar files |

---

## Active Characters Created

All under `/etc/sid/characters/`. Notable ones:
- `sid-cat` — cat head, anime eyes, smile, hoodie, glasses (128px)
- `afriendlyretro` — procedural robot (128px)
- `cool-cat` — early test (64px)
- `test-parts-*` — various resolution tests

---

## Installed Skills (Codex Ecosystem)

Skills at `~/.shared-skills/` — available to any Codex agent:

### Web/Search
- **agent-reach** — Internet search, read web pages, interact with platforms (Twitter/X, Reddit, YouTube, GitHub, Bilibili, LinkedIn, etc.)
- **web-reader** — Extract clean text from URLs via Jina AI Reader + curl

### Sales/E-commerce
- **ebay-mcp** — eBay listings, inventory, orders, returns, promotions
- **etsyv3** — Etsy API (listings, shops, orders)
- **mcp-amazon-sp-api** — Amazon Selling Partner API (listings, FBA, orders)
- **poshmark-cli** — Poshmark automation (listings, sharing)

### App Store Publishing
- **appstore-skill** — Apple App Store (fastlane, metadata, screenshots)
- **googleplay-skill** — Google Play Console (fastlane supply, metadata, screenshots)
- **fdroidserver** — F-Droid open source app store
- **snapcraft** — Snap Store (Ubuntu)
- **aur-utils** — Arch User Repository (PKGBUILDs)

### Social Media
- **facebook** — Facebook CLI posting
- **publish-social** — Single post to 8 platforms (Bluesky, Mastodon, Threads, LinkedIn, X, Instagram, Facebook, YouTube)
- **twitter-auto-post-shizuku** — Android Twitter/X posting via UI automation

### Game Development
- **gamestudio** — Full game workflow (Godot, Unity, Phaser, WebGL)
- **generate2dmap** — 2D game map generation
- **generate2dsprite** — 2D sprite and animation sheet generation

### Image Generation
- **imagegen** — AI image generation (needs OPENAI_API_KEY)
- **screenshot** — Desktop/terminal screenshot capture

### Utilities
- **release-it** — GitHub releases, version bumps, changelogs
- **cron-helper** — Schedule/manage cron jobs
- **data-converter** — CSV/JSON/YAML/XML/Markdown conversion
- **dependency-scan** — Dependency auditing (npm, pip, Cargo, Go, Ruby)
- **file-finder** — File search by name, content, type
- **git-intel** — Git history analysis (blame, log, diff)
- **json-query** — JSON query, filter, transform
- **log-tools** — Log analysis and monitoring
- **markdown-utils** — Markdown generation and formatting
- **system-health** — System resource monitoring
- **template-scaffold** — Project scaffolding
- **search-codex-chats** — Search Codex chat history

### Android (device-side, not SID OS)
- android-bsh, android-calendar, android-camera, android-clipboard, android-device-info, android-intent-bridge, android-location, android-notifications, android-share, android-shizuku, android-toast, android-torch, android-tts, android-vibrate, android-volume, android-wifi

### Agent Coordination
- **caveman** — Compressed communication modes (caveman, wenyan) for token efficiency
- **skill-installer** — Install skills from curated list or GitHub repos
- **skill-creator** — Create new skills

---

## Version History

| Tag | Features |
|---|---|
| v1.0.0 | First public release, bootable ISO + portable tarball |
| v1.2.0 | UEFI boot, host FS auto-mount, WiFi, DevMode easter egg |
| v1.2.1 | Modular animated assistant — 3 ASCII chars, 6 render backends |
| v1.2.2 | Profile export/import system |
| v1.3.0 | Spritesheet generator, frame caching, tests |
| v1.4.0 | CharForge character creator procedural |
| v1.4.1 | Bug fixes — indentation, missing imports, token security |
| v1.5.0 | Modular character parts system (charparts.py) |
| v1.5.1 | SIDShell assistant commands, doctor, git hooks |

---

## Architecture Decision Records

1. **ASCII characters always work** — no deps needed; image rendering is optional
2. **Offline-first** — everything degrades gracefully when offline
3. **Modular parts** — characters are composed from swappable parts, not monoliths
4. **Profile system** — `.sidprofile` = full backup, `.sidchar` = character only
5. **Single heartbeat** — every 30min, checks all channels, runs jobs
6. **Token security** — single source file (`/root/.sid-token`), chmod 600

---

## Known Issues

1. Imagegen model router — not yet wired (procedural is the only working tier)
2. Bare except: ~88 occurrences — intentional for graceful degradation on diverse hardware
3. GUI overlay renderer — designed but not implemented (planned for v2.x)
4. `sid_shell.py` has ~30 pyflakes warnings (unused imports, assigned-but-unused vars)
5. Test coverage — 84/87 pass, no smoke test for SIDShell init
