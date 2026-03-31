# SuperCollider Language Module (`lib/SCLang/`)

## Overview

Provides Python representations of SuperCollider SynthDefs, envelopes, and language constructs. This module bridges FoxDot's Python code with SuperCollider's synthesis engine by generating `.scd` files and managing synth compilation.

## Files

| File | Purpose | Key Exports |
|------|---------|-------------|
| `SynthDef.py` (10KB) | SynthDef class hierarchy | `SynthDict`, `SynthDef`, `CompiledSynthDef`, `SynthDefProxy`, `SampleSynthDef` |
| `Env.py` | Envelope definitions | `Env`, `Env.perc()`, `Env.lin()`, `Env.adsr()` |
| `SCLang.py` | SC language bindings | `cls()`, `instance()`, SC class wrappers |
| `_SynthDefs.py` (15KB) | Pre-defined synth library | `play1`, `play2`, `audioin`, `noise`, `dab`, `varsaw`, `lazer`, etc. |
| `_ExternalSynthDefs.py` | External Quark synth wrappers | `QuarkSynthDef`, SCLOrkSynths wrappers (`cheappiano`, `rhodey`, etc.) |

## SynthDef System

### SynthDict
Global registry (`SynthDefs`) mapping synth names to their definitions. Methods:
- `reload()` — Re-read all `.scd` files from disk
- `set_server(server)` — Point all synths at the OSC server

### SynthDef Class Hierarchy

```
SynthDefBaseClass
├── SynthDef         — Full user-defined synth (generates .scd code)
├── CompiledSynthDef — Pre-compiled synth (loaded from .scd file)
├── QuarkSynthDef    — Quark-loaded synth (no file, loaded by SC class library)
├── SynthDefProxy    — Lazy-loading reference to a synth
└── SampleSynthDef   — Special synth for sample playback (play, play2, loop)
```

### How SynthDefs Work

1. A `SynthDef` stores its parameters (default values, argument names)
2. When a Player uses it (`d1 >> pluck(...)`), the Player calls `synth.instance()`
3. `instance()` generates an argument dict for the current beat
4. The dict is sent as an OSC `/s_new` message to SuperCollider
5. SC spawns the synth and routes audio through the effect chain

### Parameter Conventions
FoxDot SynthDefs must follow specific conventions to work with the Player system:
- `out` bus parameter (for effect routing)
- `amp`, `pan`, `freq` standard parameters
- Envelope handling via `sus` (sustain) and `Env` objects
- `buf` parameter for sample-based synths

## Integration with External SynthDefs

> See `docs/architecture/HANDOFF-04-sound-libraries.md` for the full integration spec.

### SCLOrkSynths / mk-synthlib (Phase 2B)
External SynthDef collections need adaptation to work with FoxDot:
1. Install as SuperCollider Quarks
2. Create `CompiledSynthDef` wrappers in Python with matching parameter names
3. Register in `SynthDefs` dict
4. Ensure `out` bus and envelope conventions are met

### VSTPlugin Integration (Phase 2B)
To host VST instruments:
1. Create a SuperCollider SynthDef that wraps the `VSTPlugin` UGen
2. Register it as a `CompiledSynthDef` in FoxDot
3. Map FoxDot parameters (freq, amp, dur) to VST MIDI/parameter messages
4. Reference: TidalVST project for the TidalCycles implementation pattern

## Pre-Defined Synths (`_SynthDefs.py`)

Key built-in synths:
- `play1`, `play2` — Mono/stereo sample playback
- `loop` — Looping sample player
- `audioin` — Live audio input
- `pluck`, `bass`, `sawbass`, `prophet` — Melodic synths
- `noise`, `dab`, `varsaw`, `lazer` — Textural synths
- `sitar`, `marimba`, `bell` — Acoustic-like synths

## Implementation Requirements

### Custom SynthDef Workflow (Phase 3C)
Document how to:
1. Write a SynthDef in Python using the `SynthDef` context manager
2. Write a SynthDef directly in SuperCollider `.scd` and load it
3. Adapt external SynthDefs (SCLOrkSynths) to FoxDot conventions
4. Test a SynthDef from the FoxDot REPL

### Python 3.13
No migration concerns — this module uses only string manipulation, dicts, and file I/O.
