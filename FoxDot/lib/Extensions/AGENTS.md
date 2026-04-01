# Extensions Module (`lib/Extensions/`)

## Overview

Optional integrations that extend FoxDot's capabilities beyond core live coding. These are not loaded by default and can be imported selectively.

## Subdirectories

### `SonicPi/`
**Purpose:** Transpile FoxDot code to Sonic Pi syntax.
- `generate_sonic_pi()` — Converts FoxDot Player definitions to Sonic Pi `live_loop` code
- **Status:** Experimental. Low priority for the fork.

### `VRender/` (Voice Rendering)
**Purpose:** Integration with Sinsy singing synthesis service.
- `VRender` — Main voice rendering class
- `Composer` — MIDI composition for Sinsy input
- `MidiFactory` — MIDI message generation
- `Sinsy` — API client for Sinsy web service
- `VoiceSpecificator` — Voice configuration
- `tmp/` — Temporary files for rendering pipeline
- **Status:** Niche feature. Evaluate whether to keep in fork.

### `PArp.py`
**Purpose:** Arpeggio pattern generation.
- Provides arpeggio-style pattern helpers for Player objects.
- **Status:** Useful. Keep and ensure compatibility.

## Implementation Notes

### For the Fork
- These extensions are optional — they should not block the Python 3.13 migration
- The VRender module depends on an external web API (Sinsy) and `midiutil`
- PArp.py is self-contained and should work without changes
- Consider adding new extensions for:
  - **Audacity integration** (`AudacityBridge/`) — See `docs/architecture/HANDOFF-05-audacity-automation.md`
  - **Event logging** (`EventLogger/`) — See `docs/architecture/HANDOFF-03-event-logger.md`
  - **VST bridge** (`VSTBridge/`) — See `docs/architecture/HANDOFF-04-sound-libraries.md` Tier 3
