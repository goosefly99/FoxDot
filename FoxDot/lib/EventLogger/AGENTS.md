# FoxDot EventLogger Module (`lib/EventLogger/`)

## Overview

Captures timestamped performance events during a FoxDot live coding session and writes them as Audacity-compatible label track files (`.txt`). Enables post-production workflows where recorded audio can be annotated with tempo changes, player assignments, and manual markers.

## Architecture

```
[FoxDot Runtime]
   │
   ├── Clock.__setattr__("bpm", ...) ──hook──▶ log "BPM -> 140"
   ├── Player.__rshift__(synth)      ──hook──▶ log "d1 >> pluck" + region start
   ├── Player.stop() / .pause()      ──hook──▶ log "d1 stopped" + region end
   └── mark("drop")                  ──────▶ log "[MARK] drop"
                                                    │
                                              ┌─────▼──────┐
                                              │ EventLogger │
                                              │  .events[]  │
                                              └─────┬──────┘
                                                    │ .export()
                                                    ▼
                                        foxdot_labels_YYYYMMDD_HHMMSS.txt
                                        (Audacity label format)
```

## Files

| File | Purpose |
|------|---------|
| `__init__.py` | Public API: `start_logging()`, `stop_logging()`, `mark()`, `install_hooks_deferred()`. Manages global `_global_logger` instance |
| `logger.py` | `EventLogger` class — records point labels and region labels, exports to Audacity tab-delimited format |
| `hooks.py` | Monkey-patch hooks for `TempoClock.__setattr__`, `Player.__rshift__`, `Player.stop()`, `Player.pause()`. Install/remove with thread safety |

## Audacity Label Format

Tab-delimited, one label per line:
- **Point label:** `12.500000\t12.500000\tBPM -> 140`
- **Region label:** `15.300000\t45.800000\td1: pluck section`

## Key Classes and Functions

### `EventLogger` (logger.py)
- `start()` — Record session start time, reset events list
- `stop()` — Close open player regions, log "SESSION END", call `export()`
- `log_event(label)` — Add a point label at current elapsed time
- `log_region_start(key, label)` — Begin a region (player start)
- `log_region_end(key)` — End a region (player stop)
- `write_labels(filepath)` — Write sorted events to Audacity format
- `export()` — Write to `output_dir/foxdot_labels_{session_name}.txt`

### Hooks (hooks.py)
- `hook_clock_bpm(logger, clock)` — Wraps `Clock.__setattr__` to log tempo changes
- `hook_player_rshift(logger)` — Wraps `Player.__rshift__` to log player assignments
- `hook_player_stop(logger)` — Wraps `Player.stop()` and `Player.pause()`
- `install_hooks(logger, clock)` — Install all hooks (raises if already installed)
- `remove_hooks()` — Restore original methods from `_originals` dict

### Module-level API (__init__.py)
- `start_logging(output_dir, session_name, clock)` — Create and start an EventLogger
- `install_hooks_deferred(clock)` — Called from `lib/__init__.py` after Clock is created
- `stop_logging()` — Stop logger, remove hooks, return label file path
- `mark(label)` — Add a manual marker during performance

## Thread Safety

- `_originals` dict in hooks.py is guarded by `threading.Lock`
- `install_hooks()` raises `RuntimeError` if hooks already installed (prevents double-patching)
- Label sanitization via `_sanitize_label()` strips tabs/newlines

## Integration Points

- `lib/__init__.py` — Calls `install_hooks_deferred(Clock)` after Clock creation
- `lib/Players.py` — Hooked methods: `__rshift__`, `stop()`, `pause()`
- `lib/TempoClock.py` — Hooked via `__setattr__` for BPM changes
- `lib/AudacityBridge/` — Label files are imported into Audacity for post-production

## Handoff Spec

See `docs/architecture/HANDOFF-03-event-logger.md` for original design spec.
