# FoxDot Core Library (`lib/`)

## Overview

This is the core Python library containing all music logic for FoxDot. The `__init__.py` aggregates all submodules into a single namespace and creates global singletons (Clock, Server, Players).

## Initialization Order (Critical)

The import order in `__init__.py` matters — later modules depend on earlier ones:

```python
1. Code         → FoxDotCode (execution engine, namespace)
2. TempoClock   → Clock (global scheduler singleton)
3. Buffers      → Samples (sample bank)
4. Players      → Player, EmptyPlayer, Group
5. Patterns     → Pattern, PGroup, generators
6. Effects      → FxList
7. TimeVar      → var, Pvar
8. Constants    → const, _inf
9. Midi         → MidiIn, MidiOut (optional)
10. Settings    → configuration values
11. SCLang      → SynthDefs, Env, SynthDef
12. ServerManager → Server (OSC client singleton)
13. Scale       → Scale, Tuning
```

After imports, `instantiate_player_objects()` creates all 2-character player variables (p1–p9, a1–z9, etc.) in the shared namespace.

**Note:** `lib/__init__.py` lines ~153–154 also contain reload-time re-imports of `SCLang` and `Effects` inside a function. These are not part of the startup sequence above — they only run when `reload()` is called to hot-reload the library during a session.

## Key Singletons

| Name | Type | Created In | Purpose |
|------|------|-----------|---------|
| `Clock` | `TempoClock` | `lib/__init__.py` | Master scheduler, runs in background thread |
| `Server` | `ServerManager` | `lib/__init__.py` | OSC client to SuperCollider |
| `FoxDotCode` | `FoxDotCode` | `Code/main_lib.py` | Code execution with shared namespace |
| `Samples` | `_symbolToDir` | `Buffers.py` | Global sample bank |
| `FxList` | `_FxList` | `Effects/Util.py` | Effects registry |
| `SynthDefs` | `SynthDict` | `SCLang/SynthDef.py` | SynthDef registry |

## Music Generation Flow

```
User code: d1 >> pluck([0,1,2,3], dur=1, amp=0.8)

1. Player.__rshift__(SynthDef) → Player stores synth reference
2. Clock.schedule(Player) → Player queued at next beat
3. Clock thread wakes → calls Player.osc_message()
4. Player resolves Patterns at current beat index
5. Player applies Scale, Root, Octave to get MIDI notes
6. Player generates OSC /s_new message dict
7. Server.sendNote(dict) → OSC packet to SuperCollider
8. SC spawns synth instance with given parameters
9. Effects applied in SC signal chain
```

## Standalone Modules (No Subpackage)

| File | Purpose | Key Exports |
|------|---------|-------------|
| `Players.py` (65KB) | Musical voice instances | `Player`, `EmptyPlayer`, `Group`, `rest`, `player_method` |
| `TempoClock.py` (34KB) | Beat scheduling and timing | `TempoClock`, `Queue`, `QueueBlock` |
| `ServerManager.py` (33KB) | OSC communication with SC | `ServerManager`, `TempoServer`, `TempoClient`, `BidirectionalOSCServer` |
| `Buffers.py` (18KB) | Sample buffer management | `Buffer`, `Samples`, `DESCRIPTIONS` |
| `TimeVar.py` (26KB) | Time-varying parameter values | `TimeVar` (aliased as `var`), `Pvar`, `linvar`, `expvar` |
| `Scale.py` (15KB) | Musical scales and tuning | `Scale`, `Tuning`, `midi()`, `miditofreq()`, `freqtomidi()` |
| `Root.py` | Root note management | `Root`, `Note` |
| `Chords.py` | Chord definitions | Chord lookup tables |
| `Repeat.py` (15KB) | Method chaining and replay | `Repeatable`, `MethodList`, `MethodCall` |
| `Key.py` (15KB) | Player attribute tracking | `NumberKey`, `PlayerKey` |
| `Midi.py` | MIDI I/O (optional) | `MidiIn`, `MidiOut` |
| `Constants.py` | Immutable values | `const`, `_inf`, `NoneConst` |
| `Logging.py` | Performance profiling | `Timing` context manager/decorator |
| `OSC3.py` (109KB) | Pure Python OSC for Py3 | `OSCClient`, `OSCServer`, `OSCMessage`, `OSCBundle` |

## Implemented Fork Modules

### REPL Interface (Phase 2A) — `lib/REPL/`
Transport-agnostic REPL server decoupled from the Tkinter editor:
- Accepts code via WebSocket (port 5555) or stdin
- Executes through `FoxDotCode.__call__()`
- Returns stdout/stderr and player state snapshots
- Supports `--pipe` mode via stdin transport
- See `lib/REPL/AGENTS.md` for details

### Event Logger (Phase 2C) — `lib/EventLogger/`
Hooks into FoxDot runtime to capture performance events:
- `Clock.bpm` setter — logs tempo changes
- `Player.__rshift__` — logs player assignments (region start)
- `Player.stop()` / `Player.pause()` — logs player stops (region end)
- Manual markers via `mark("label")`
- Output: Audacity-format label `.txt` files
- See `lib/EventLogger/AGENTS.md` for details

### Audacity Bridge (Phase 2C+3A) — `lib/AudacityBridge/`
Controls Audacity via mod-script-pipe or PyAudacity:
- Transport control, label import/export, macro execution
- FoxDot-Master mastering macro management
- Audio export (WAV/MP3/OGG/FLAC)
- See `lib/AudacityBridge/AGENTS.md` for details

### Python 3.13 Cleanup (Phase 1) — Complete
- Removed `OSC.py` (Python 2 module)
- Removed Py2/Py3 conditional imports throughout
- Cleaned up `TypeType` handling in `Code/main_lib.py`
- Removed `xrange` shim in `Settings/__init__.py`
