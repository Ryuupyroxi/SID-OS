# Animated Assistant — Coder Handoff (Alpine Session)

## What Exists

Located at `src/terminal/assistant/`:
- `__init__.py` — public API
- `character.py` — Character class + ASCII template registry (3 chars)
- `renderer.py` — 6 render backends (ASCII/Kitty/iTerm2/Sixel/Chafa/SDL2-future)
- `controller.py` — State machine + character switching + AI mode integration
- `generator.py` — **Stubbed** — needs your implementation

Integrated into `src/terminal/shell/sid_shell.py`:
- `config set assistant on|off` toggle
- Auto-state switching: idle → thinking → speaking → idle
- State indicator in `sid⏣ [◎]` prompt

## What Needs Building (Priority Order)

### 1. `generator.py` — Photo→Sprite→Character Pipeline
This is the main task. Hook into `imagegen` skill to:
- Accept a photo or prompt
- Generate a front-facing character portrait
- Create 6 mouth-shape variant frames
- Arrange into a 5-row × 6-column spritesheet PNG
- Output metadata JSON
- Auto-register into the CHARACTERS dict

See `generator.py` for the full pipeline spec and template format.

### 2. Sprite Sheet Loader
In `character.py`, implement loading logic for the `spritesheet` type:
```python
if char_data["type"] == "spritesheet":
    # Slice source PNG by grid coords
    # Cache individual frames as PIL Images or temp PNGs
    # Return frame data compatible with renderers
```

### 3. Terminal Detection
In `renderer.py`, improve `detect_best_renderer()`:
- Actually probe terminal capabilities (kitty env var, sixel query)
- Add auto-discovery for installed tools (chafa, catimg)
- Graceful fallback chain

### 4. Test Characters
Create test spritesheet PNGs with simple colored squares as frames.
Verify: frame cycling in all render backends, state transitions, edge cases.

## Key Constraints
- Zero external Python deps (stdlib only for core, imagegen for generation)
- Must work on TERM=dumb terminals (fallback to ASCII always)
- Characters must be swappable at runtime without restart
- AI state changes must not garble terminal output (no background threads)

## Reference
- Imagegen skill: `~/.shared-skills/.system/imagegen/SKILL.md`
- Sprite forge: `~/.shared-skills/generate2dsprite/SKILL.md`
- Existing test: `test_sid.py` (add assistant tests here)
