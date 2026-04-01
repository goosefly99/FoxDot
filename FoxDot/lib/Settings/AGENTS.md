# Settings Module (`lib/Settings/`)

## Overview

Configuration management, path definitions, and platform detection. This module defines all global constants used throughout FoxDot and loads user preferences from a config file.

## Files

| File | Purpose | Key Exports |
|------|---------|-------------|
| `__init__.py` | Main settings and paths; imports from `conf.py`, defines platform detection and directory constants | All configuration constants (see below) |
| `conf.py` | User-editable configuration values; loaded by `__init__.py` at import time | `ADDRESS`, `PORT`, `FONT`, `BPM`, etc. |
| `conf.txt` | Config file template for reference; not loaded at runtime | Default configuration reference |

### Settings Loading Mechanism

1. `Settings/__init__.py` is imported early in the `lib/__init__.py` chain
2. It performs platform detection (`SYSTEM` constant) and defines all directory paths
3. It then imports all values from `conf.py` (e.g., `from .conf import *`)
4. `conf.py` contains the actual runtime defaults (`ADDRESS = "localhost"`, `PORT = 57110`, etc.)
5. `conf.txt` is a human-readable template — it is NOT automatically parsed

**To add a new setting:** Add the default value to `conf.py`, then reference it via `from .Settings import MY_SETTING` in other modules. Do NOT add settings to `__init__.py` unless they are derived from platform detection or directory paths.

## Key Constants

### Platform Detection
```python
WINDOWS = 0
LINUX   = 1
MAC_OS  = 2
SYSTEM  = <detected at import>
```

### Paths
| Constant | Purpose |
|----------|---------|
| `FOXDOT_ROOT` | Package root directory |
| `FOXDOT_SND` | Sample directory (`snd/`) |
| `FOXDOT_SCD` | SuperCollider files (`osc/`) |
| `FOXDOT_ICON` | GUI icon path |
| `EFFECTS_DIR` | Effects `.scd` directory |
| `ENVELOPE_DIR` | Envelope `.scd` directory |
| `SYNTHDEF_DIR` | SynthDef `.scd` directory |
| `TUTORIAL_DIR` | Demo files directory |
| `RECORDING_DIR` | Recording output directory |
| `SAMPLES_DIR` | Additional samples directory |

### Configuration Values (from `conf.py`)
| Setting | Default | Purpose |
|---------|---------|---------|
| `ADDRESS` | `"localhost"` | SuperCollider OSC address |
| `PORT` | `57110` | SuperCollider OSC port |
| `PORT2` | `57120` | SuperCollider language port |
| `FONT` | `"Consolas"` | Editor font family |
| `BPM` | `120` | Default tempo |
| `SC3_PLUGINS` | `False` | Whether SC3 plugins are installed |
| `USE_ALPHA` | `False` | Alpha channel support |
| `RECOVER_WORK` | `True` | Auto-recovery on crash |
| `CHECK_FOR_UPDATE` | `True` | Version check on startup |

### Special Types
```python
_SamplePlayer  = namedtuple  # Identifies sample-playing SynthDefs
_LoopPlayer    = namedtuple  # Identifies loop-playing SynthDefs
_MidiPlayer    = namedtuple  # Identifies MIDI-output SynthDefs
```

## Python 3.13 Migration

> See `docs/architecture/HANDOFF-01-python313-migration.md` Task 2a for the exact cleanup steps.

### Must Fix
- **Lines 12–19:** Python 2 compatibility shims (`xrange = range`, `PY_VERSION` checks). Remove entirely.
- **Lines 35–37:** macOS matplotlib backend workaround. Verify still needed on 3.13.

### Config Additions for Fork
Add new settings for the fork's features:
- `AUDACITY_PIPE_ENABLED` — Whether to connect to Audacity's mod-script-pipe
- `AUDACITY_LABEL_DIR` — Directory for event label files
- `REPL_WEBSOCKET_PORT` — Port for the new REPL WebSocket interface
- `VIRTUAL_AUDIO_DEVICE` — Name of the virtual audio routing device

## Cross-Platform Concerns

The `SYSTEM` constant drives platform-specific behavior throughout FoxDot:
- SuperCollider boot method (subprocess on Windows, `os.system` with `&` on Unix)
- DPI awareness (Windows only)
- Path separators (handled by `os.path`)
- Audio routing documentation differs per platform
