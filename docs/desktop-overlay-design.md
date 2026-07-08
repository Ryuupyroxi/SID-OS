# SID OS — Desktop Character Overlay Renderer (Shimeji-style)

> Design document — v0.1 draft
> Target: v2.0 milestone

## Concept

A lightweight, transparent, always-on-top window that renders the animated assistant directly on the desktop. The character can:
- Float anywhere on screen (draggable)
- Show expressions (idle, thinking, listening, speaking, error)
- Walk/glide around (idle animation)
- Respond to AI state changes
- Be positioned by the user

This is **not** a separate app — it's SID's face rendered as a desktop overlay instead of in-terminal.

## Architecture

The existing renderer backend system (`BaseRenderer` → subclasses) gets a new backend:

```
BaseRenderer
├── ASCIIRenderer          (terminal, always works)
├── KittyRenderer          (terminal, image protocol)
├── SixelRenderer          (terminal, sixel graphics)
├── ChafaRenderer          (terminal, chafa CLI)
├── CatimgRenderer         (terminal, catimg CLI)
├── Iterm2Renderer         (terminal, iTerm2 protocol)
└── SDL2OverlayRenderer    ← NEW: desktop window
```

## Dependencies

| Package | Alpine pkg | Size |
|---|---|---|
| SDL2 | `sdl2-dev` | ~2MB |
| SDL2_image | `sdl2_image-dev` | ~1MB |
| Python bindings | `py3-pysdl2` | ~200KB |

Optional — not in base ISO, installed on demand.

## Interaction Model

| Action | Behavior |
|---|---|
| Click & drag | Move character around screen |
| Double-click | Toggle expression |
| Right-click | Context menu (switch char, close) |
| AI speaks | Speaking animation |
| AI thinks | Thinking animation |
| User types | Listening animation |
| No activity | Idle bob/sway |

## Implementation Phases

### Phase 1: Basic Window (2-3 hrs)
- SDL2 transparent borderless window
- Load & display single PNG frame
- `sid⏣ assistant desktop on|off` command

### Phase 2: Animation (2 hrs)
- Slice spritesheet by grid
- Frame cycling at correct timing
- State-based animation row selection

### Phase 3: Interaction (2 hrs)
- Click-and-drag
- Right-click context menu
- Character switching

### Phase 4: Polish
- Multiple monitor support
- X11/Wayland compatibility
- Auto-start option

## Open Questions for Manager

1. Base ISO or optional add-on?
2. X11 + Wayland support?
3. Auto-launch at startup or manual?
4. Scale with DPI or fixed pixel size?

---

*Design v0.1 — Developer, 2026-07-08*
