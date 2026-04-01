# FoxDot AudacityBridge Module (`lib/AudacityBridge/`)

## Overview

Controls Audacity from FoxDot via Audacity's mod-script-pipe (named pipes) or the `pyaudacity` Python package. Provides transport control, label import, macro execution, and audio export for post-production workflows.

## Architecture

```
[FoxDot]
   │
   ├── AudacityBridge._send(command)
   │       │
   │       ├──▶ Named Pipe (\\.\pipe\ToSrvPipe / FromSrvPipe on Windows)
   │       │        └──▶ [Audacity mod-script-pipe]
   │       │
   │       └──▶ pyaudacity.do(command)  (fallback)
   │                └──▶ [Audacity scripting API]
   │
   └── macros.py
           └──▶ Writes macro .txt files to Audacity's Macros directory
```

## Files

| File | Purpose |
|------|---------|
| `__init__.py` | Public API: `connect()`, `is_connected()`, `get_bridge()`. Manages global `_global_bridge` singleton |
| `bridge.py` | `AudacityBridge` class — pipe/pyaudacity communication, transport control, label import/export, macro execution, audio export |
| `macros.py` | Macro management: `get_macro_dir()`, `is_macro_installed()`, `install_macro()`. Defines the `FoxDot-Master` mastering macro |

## Key Classes and Functions

### `AudacityBridge` (bridge.py)
- **Connection:** `_connect()` tries named pipes first, falls back to `pyaudacity`. Raises `ConnectionError` if neither works.
- **Transport:** `record()`, `stop()`, `pause()` — Audacity transport control
- **Labels:** `import_labels(filepath)`, `export_labels(filepath)` — import/export label tracks
- **Macros:** `run_macro(name)`, `apply_foxdot_master()` — run Audacity macros
- **Export:** `export_audio(filepath, format)` — export as WAV/MP3/OGG/FLAC
- **File:** `open_file(filepath)`, `save_project(filepath)` — file operations

### Macro Helpers (macros.py)
- `get_macro_dir()` — Platform-specific Audacity Macros directory (Windows: `%APPDATA%/audacity/Macros`, macOS: `~/Library/Application Support/audacity/Macros`, Linux: XDG or `~/.audacity-data/Macros`)
- `is_macro_installed(name)` — Check if macro file exists
- `install_macro(name, contents)` — Write macro file to Audacity's directory

### FoxDot-Master Macro
Default mastering chain: Normalize (-1dB peak) -> Compressor (4:1, -18dB threshold) -> Hard Limiter (-3dB) -> EQ (high-pass 30Hz, low-pass rolloff at 20kHz)

## Platform-Specific Pipe Paths

| Platform | To-pipe | From-pipe |
|----------|---------|-----------|
| Windows | `\\.\pipe\ToSrvPipe` | `\\.\pipe\FromSrvPipe` |
| macOS | `/tmp/audacity_script_pipe.to.` | `/tmp/audacity_script_pipe.from.` |
| Linux | `/tmp/audacity_script_pipe.to.` | `/tmp/audacity_script_pipe.from.` |

## Dependencies

- `pyaudacity` (optional — fallback when named pipes unavailable, listed in `setup.py` extras_require)
- Audacity with mod-script-pipe enabled (primary transport)

## Integration Points

- `lib/EventLogger/` — Produces label files that `import_labels()` consumes
- `scripts/post_session.py` — Orchestrates: open audio -> import labels -> apply macro -> export
- `scripts/install_mastering_macro.py` — CLI tool using `macros.install_macro()`
- `__main__.py` — `--post-process` flag triggers post-session automation

## Handoff Spec

See `docs/architecture/HANDOFF-05-audacity-automation.md` for original design spec.
