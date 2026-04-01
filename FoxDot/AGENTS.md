# FoxDot — Package Root

## Overview

This is the top-level Python package for FoxDot, an algorithmic music production library for live coding. FoxDot sends OSC messages to SuperCollider for real-time audio synthesis.

## Architecture

```
[Editor / REPL] → [FoxDot Python Core] → [OSC over UDP] → [SuperCollider (scsynth)]
                         │                                         ↓ audio
                    [Event Logger]                        [Virtual Audio Device]
                         │                                         ↓
                         └── labels ──────────────────→ [Audacity DAW]
```

### Entry Points

- `__init__.py` — Library entry point. Contains `boot_supercollider()` for launching SC via subprocess, and `main()` which starts the Tkinter GUI workspace. Also exposes `Go()` for keeping the Clock thread alive in headless/script mode.
- `__main__.py` — CLI entry point with argparse. Flags: `--pipe` (headless REPL), `--dir` (working directory), `--startup` (custom startup file), `--simple` (wxPython GUI), `--boot` (auto-start SC), `--no-startup`.

### Key Global State

The `lib/__init__.py` module creates these singletons at import time:
- `Clock` — `TempoClock()` instance, started immediately
- `Server` — `ServerManager` OSC client connected to SC
- `FoxDotCode` — Code execution engine with shared namespace
- `Samples` — Global sample buffer bank
- Pre-instantiated Player objects: `p1`–`p9`, `a1`–`z9`, etc.

### Module Map

| Directory | Responsibility |
|-----------|---------------|
| `lib/` | Core Python library (all music logic) |
| `lib/Code/` | Code execution engine, live functions, when statements |
| `lib/Patterns/` | Pattern containers, generators, sequences, parsing |
| `lib/SCLang/` | SynthDef compilation, SC language bindings, envelope definitions |
| `lib/Effects/` | Audio effect definitions and management |
| `lib/Workspace/` | Tkinter GUI editor (to be replaced — see ADR-001) |
| `lib/Settings/` | Configuration, paths, platform detection |
| `lib/Utils/` | General utilities (LCM, Euclidean rhythms, version check) |
| `lib/Extensions/` | Optional integrations (SonicPi, VRender, PArp) |
| `lib/REPL/` | Transport-agnostic REPL server (WebSocket + stdin) |
| `lib/EventLogger/` | Session event capture, Audacity label file export |
| `lib/AudacityBridge/` | Audacity control via mod-script-pipe / PyAudacity |
| `lib/EspGrid/` | Network ensemble sync (UDP-based) |
| `lib/GhostCoder/` | Grammar-based code generation |
| `lib/Custom/` | User extension hooks (`startup.py`) |
| `osc/` | SuperCollider `.scd` files (SynthDefs, effects, envelopes, buffers) |
| `snd/` | Audio samples organized by character (a-z, A-Z, symbols) |
| `demo/` | 16 numbered tutorial files |
| `rec/` | Recording output directory |

## Fork Migration Requirements (Python 3.13)

### PEP 594 Removed Modules — Audit Required
Grep the entire codebase (including transitive dependencies) for these removed imports:
- `audioop`, `aifc`, `sunau`, `sndhdr`, `chunk` — audio-related removals
- `pipes` — replaced by `subprocess`
- `tkinter.tix` — removed (use `ttk`)
- `cgi`, `cgitb` — unlikely but check

### Already Handled (Py2/Py3 Compatibility)
These patterns exist throughout but are safe on 3.13:
- `queue` vs `Queue` — conditional import in `ServerManager.py`
- `urllib.request` vs `urllib2` — conditional import in `Utils/__init__.py`
- `tkinter` vs `Tkinter` — handled in `Workspace/tkimport.py`
- `reload()` — uses `importlib.reload` in `lib/__init__.py`

### Dependency Pins
- `python_requires='>=3.13.1'` (avoid Windows tkinter venv bug in 3.13.0)
- `psutil>=7.0` (3.13 wheel support)
- `wxPython>=4.2.2` (if Simple editor mode is kept)
- `packaging` — no version pin needed

### Legacy Code to Remove
- Python 2 compatibility shims in `Settings/__init__.py` (lines 12–19): `xrange`, `PY_VERSION` checks
- Python 2 OSC module (`lib/OSC.py`) — only `OSC3.py` is needed
- `TypeType` fallback in `Code/main_lib.py`

## Cross-Platform Concerns

| Area | Windows | Linux | macOS |
|------|---------|-------|-------|
| SC boot | `where /R "C:\Program Files"` for sclang.exe | `os.system("sclang ... &")` | `os.system("sclang ... &")` |
| DPI | `windll.shcore.SetProcessDpiAwareness` in Editor.py | N/A | matplotlib backend to TkAgg |
| Audio routing | VB-CABLE | PipeWire / JACK | BlackHole |
| Process detection | psutil with Windows process names | psutil with Unix process names | psutil with Unix process names |

## Design Decisions

See `docs/architecture/ADR-001-foxdot-fork-architecture.md` for full context on:
1. Python 3.13 migration strategy
2. Frontend editor replacement (Flok now, custom Tauri+CM6 later)
3. Sound library integration (Dirt-Samples, SCLOrkSynths, VSTPlugin)
4. Audacity DAW integration (recording pipeline, label tracks, post-production)

See `docs/architecture/ROADMAP.md` for phased implementation plan.

### Developer Handoff Specs

| Spec | Phase | Modules Affected |
|------|-------|-----------------|
| `HANDOFF-01-python313-migration.md` | 1 | Settings, Code, ServerManager, Utils, Workspace, OSC, `__init__.py`, setup.py |
| `HANDOFF-02-repl-interface.md` | 2A | New `lib/REPL/`, Code, Settings, `__main__.py` |
| `HANDOFF-03-event-logger.md` | 2C | New `lib/EventLogger/`, Players, TempoClock, Effects, Settings |
| `HANDOFF-04-sound-libraries.md` | 2B | New `lib/SCLang/_ExternalSynthDefs.py`, new `osc/scsyndef/` files, Settings |
| `HANDOFF-05-audacity-automation.md` | 2C+3A | New `lib/AudacityBridge/`, new `scripts/`, Settings, `__main__.py` |
| `HANDOFF-06-packaging-ci.md` | 3B | New `pyproject.toml`, new `.github/workflows/`, new `tests/`, setup.py |
