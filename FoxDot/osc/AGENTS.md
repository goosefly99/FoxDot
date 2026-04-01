# OSC / SuperCollider Files (`osc/`)

## Overview

SuperCollider `.scd` source files that define the audio engine: synth definitions, effects, envelopes, buffer management, and OSC message handlers. These files are loaded by SuperCollider at boot time via `startup.scd`.

## Directory Structure

| Directory/File | Purpose | Count |
|---------------|---------|-------|
| `scsyndef/` | Synth definitions (one `.scd` per synth) | 72 files |
| `sceffects/` | Effect definitions (one `.scd` per effect) | 29 files |
| `scenvelopes/` | Envelope shapes | Several files |
| `Buffers.scd` (31KB) | Buffer loading and sample management | 1 file |
| `Info.scd` | Server info/stats retrieval | 1 file |
| `OscFunc.scd` | OSC message handler registration | 1 file |
| `Record.scd` | Audio recording functionality | 1 file |

## SynthDef Files (`scsyndef/`)

Each `.scd` file defines one SuperCollider SynthDef. These are the instruments FoxDot can play. Key conventions:
- Must accept `out` bus parameter for effect routing
- Must include amplitude envelope (typically `EnvGen` with `doneAction: 2`)
- Parameter names must match what FoxDot's `SynthDef` class expects
- Output should be written to `out` bus via `Out.ar()`

### Key Synths
- `play1.scd`, `play2.scd` — Mono/stereo sample playback (most-used for `play` SynthDef)
- `loop.scd` — Looping sample player
- `pluck.scd`, `bass.scd`, `sawbass.scd` — Melodic instruments
- `noise.scd`, `dab.scd`, `varsaw.scd` — Textural synths

## Effect Files (`sceffects/`)

Each `.scd` file defines one audio effect. Effects are inserted into the signal chain between synth output and final output. Key effects:
- `reverb.scd` — Reverb (`room`, `mix` params)
- `distortion.scd` — Distortion/overdrive (`drive` param)
- `highPassFilter.scd`, `lowPassFilter.scd` — Filter effects (`hpf`, `lpf` params)
- `combDelay.scd` — Comb delay effect
- `bitcrush.scd` — Bitcrusher
- `chop.scd` — Amplitude chopping

## Buffers.scd

Manages audio buffer allocation in SuperCollider:
- Loads sample files from FoxDot's `snd/` directory
- Maps characters to buffer indices
- Handles mono/stereo detection
- Manages buffer memory

## Implementation Requirements

### Adding External SynthDefs (Phase 2B)
To integrate SCLOrkSynths or other external SynthDef collections:
1. Either copy `.scd` files into `scsyndef/` following the naming convention
2. Or load them separately via SuperCollider Quarks (preferred — avoids file duplication)
3. Create matching Python `CompiledSynthDef` entries in `lib/SCLang/`

### VSTPlugin Integration (Phase 2B)
A new `.scd` file (e.g., `scsyndef/vstsynth.scd`) would:
1. Use the `VSTPlugin` UGen to host a VST instrument
2. Accept FoxDot's standard parameters (freq, amp, sus, out)
3. Convert freq to MIDI note for VSTi input
4. Route VSTi output to the `out` bus for effect processing

### New Effect Development
To add custom effects:
1. Create a new `.scd` file in `sceffects/`
2. Follow the pattern of existing effects (read from bus, process, write back)
3. FoxDot's `FxList` auto-discovers new files on reload

### Cross-Platform
SuperCollider `.scd` files are platform-independent — the same files work on Windows, Linux, and macOS. The only platform-specific concern is how SuperCollider itself is launched (handled in Python, not here).
