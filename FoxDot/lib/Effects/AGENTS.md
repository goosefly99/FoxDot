# Effects Module (`lib/Effects/`)

## Overview

Manages audio effects applied to Player outputs in SuperCollider. Effects are defined as `.scd` files and registered in a global `FxList` registry. Each Player can have multiple effects chained together.

## Files

| File | Purpose | Key Exports |
|------|---------|-------------|
| `Util.py` (14KB) | Main effects management | `EffectManager`, `FxList` (global instance of `EffectManager`), `Effect` decorator |
| `NewEffects.py` (3KB) | Experimental effect system | `_Effect` base class (partially implemented) |
| `__init__.py` | Re-exports from Util.py | All exports from Util |

## How Effects Work

1. Effects are defined as `.scd` files in `osc/sceffects/`
2. At startup, `FxList` loads all `.scd` files and registers their parameters
3. When a Player has an effect parameter set (e.g., `d1 >> pluck(..., room=0.5)`), the corresponding effect is applied in SuperCollider's signal chain
4. Effects are ordered by the `FxList` and applied sequentially

### Effect Parameters
Each effect exposes named parameters with defaults. For example:
- `room` / `mix` — Reverb
- `drive` — Distortion
- `hpf` / `lpf` — High/low pass filter
- `chop` — Amplitude chopping
- `delay` / `delaytime` / `delayfeedback` — Delay

### Corresponding SuperCollider Files
The `.scd` files in `osc/sceffects/` define the actual DSP:
- `sceffects/reverb.scd`
- `sceffects/distortion.scd`
- `sceffects/highPassFilter.scd`
- `sceffects/combDelay.scd`
- ~35+ effect definitions total

## FxList Registry

`FxList` (global instance of `EffectManager`) maintains:
- Effect name → parameter mapping
- Effect ordering for signal chain
- Methods: `add()`, `remove()`, `reload()`, `reset()`

## Implementation Requirements

### Adding New Effects
To add a custom effect:
1. Write a `.scd` file in `osc/sceffects/` following the existing pattern
2. The effect will auto-register in `FxList` on next startup/reload
3. Use the effect by setting its parameter on any Player

### Event Logger Integration (Phase 2C)
Hook into `FxList` changes (add/remove) to log effect modifications for Audacity label tracks. See `docs/architecture/HANDOFF-03-event-logger.md` for the hook pattern.

### NewEffects.py
The `NewEffects.py` file contains a partially implemented experimental effect system using `_Effect` base class with EnvGen/Env utilities. Evaluate whether to complete this or remove it during the fork cleanup.
