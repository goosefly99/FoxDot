# Custom Module (`lib/Custom/`)

## Overview

User extension hooks for personalizing FoxDot. Code placed here runs at startup and persists across sessions.

## Files

| File | Purpose |
|------|---------|
| `__init__.py` | Module initialization |
| `startup.py` | User startup code — executed when FoxDot boots |

## How startup.py Works

1. FoxDot loads `startup.py` during initialization (via `load_startup_file()` in `Code/main_lib.py`)
2. Code executes in the shared FoxDot namespace (all Players, Clock, Patterns, etc. are available)
3. Common uses:
   - Define per-user custom SynthDefs (fork-bundled synths go in `lib/SCLang/_ExternalSynthDefs.py` instead)
   - Set default BPM, scale, root
   - Load additional sample directories
   - Define helper functions for live performance

## Implementation Notes

### For the Fork
This is the primary place for per-user customization. In the fork, consider:

- **Default startup for the fork:** Pre-load Dirt-Samples path, SCLOrkSynths, and any fork-specific defaults
- **Event logger initialization:** Start the Audacity event logger in startup.py
- **Audio routing config:** Set SuperCollider output device for virtual audio routing
- **Multiple startup files:** Consider supporting a `startup.d/` directory for modular startup scripts

### Example Fork Startup
```python
# Custom startup for our FoxDot fork

# Set default tempo and scale
Clock.bpm = 120
Scale.default = "minor"
Root.default = "C"

# Load Dirt-Samples
FoxDotCode.use_sample_directory("/path/to/Dirt-Samples")

# Start event logger for Audacity labels
from lib.EventLogger import start_logging
start_logging(output_dir="~/foxdot-sessions/")
```
