# SID OS — Image Generation Model Router

> Design — offline-first tiered pipeline for character generation
> Target: v2.0 milestone

## The Problem

CharForge currently has two generation paths:
1. `_gen_via_imagegen()` — requires OPENAI_API_KEY, always falls through
2. `_gen_procedural()` — always works, produces basic circle+dot art

Users want: high-quality characters, working offline, with API keys as last resort.

## Tiered Pipeline

```
User: forge.create_from_description("a cool cat with sunglasses")

                    ┌─ Model Router ──────────────────────┐
                    │                                      │
                    │  Tier 0: Procedural (always works)   │
                    │    Pure Python, no deps, basic art   │
                    │                                      │
                    │  Tier 1: Local ONNX model (offline)  │
                    │    Lightweight diffusion (SDXL-turbo)│
                    │    ~500MB model, CPU-inference       │
                    │    Downloads on first use            │
                    │                                      │
                    │  Tier 2: Free API (online, no key)   │
                    │    pollinations.ai — free tier       │
                    │    HuggingFace Inference API — free  │
                    │                                      │
                    │  Tier 3: User API key (configured)   │
                    │    OpenAI DALL-E / imagegen skill    │
                    │    Stability AI / Replicate          │
                    │                                      │
                    └──────────┬───────────────────────────┘
                               │
                    ┌──────────▼──────────────────────────┐
                    │  Modular Parts Compositor             │
                    │  (charparts.py — already exists)      │
                    └─────────────────────────────────────┘
```

## Implementation: src/tools/image_gen/router.py

```python
class ImageGenRouter:
    """Tiered image generation router.
    
    Tries each tier in order, falls through on failure.
    """
    
    tiers = ["procedural", "local", "free_api", "paid_api"]
    
    def generate(self, prompt, resolution=256):
        # Try each tier
        for tier in self.tiers:
            result = self._try_tier(tier, prompt, resolution)
            if result:
                return result
        # Ultimate fallback (always works)
        return self._procedural(prompt, resolution)
    
    def _try_tier(self, tier, prompt, resolution):
        if tier == "procedural":
            return self._procedural(prompt, resolution)
        elif tier == "local":
            return self._local_onnx(prompt, resolution)
        elif tier == "free_api":
            return self._free_api(prompt, resolution)
        elif tier == "paid_api":
            return self._paid_api(prompt, resolution)
    
    def available_tiers(self):
        """Return which tiers are usable right now."""
        ...
```

## Integration with CharForge

When `create_from_description()` is called:
1. Prompt is sent to `ImageGenRouter.generate()`
2. Router tries tiers in order
3. Output image → `_postprocess()` → mouth-shape variants → spritesheet
4. If only procedural available, use `_gen_procedural()` as before

When `create_from_parts()` is called with imagegen available:
1. Router generates a full character portrait from description
2. Compositor uses the portrait as reference colors/style
3. Parts are still composited (the character's structure is preserved)

## Files to Create/Modify

| File | Change |
|---|---|
| `src/tools/image_gen/router.py` | NEW: Model router with all 4 tiers |
| `src/terminal/assistant/charforge.py` | Wire router into create_from_description() |
| `config/ai.json` | Add imagegen tier configuration |
| `installer/scripts/install_imagegen.sh` | NEW: Download bundled ONNX model |

## Open Questions

1. Which local ONNX model to bundle? (~500MB limit for ISO)
2. Free API — pollinations.ai requires no key, but rate-limited. Acceptable?
3. Should the router cache results to avoid regenerating the same character?

---

*Design v0.1 — Developer, 2026-07-08*
