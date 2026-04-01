# Code Execution Module (`lib/Code/`)

## Overview

Handles code compilation, execution, and live-reloadable function scheduling. This is the bridge between user input (from the editor or REPL) and the FoxDot runtime.

## Files

| File | Purpose | Key Exports |
|------|---------|-------------|
| `main_lib.py` | Core execution engine | `FoxDotCode`, `execute`, `LiveObject`, `CodeString`, `stdout`, `write_to_file` |
| `foxdot_live_function.py` | `@livefunction` decorator | `livefunction` — functions that can be redefined during performance |
| `foxdot_when_statement.py` | `@when` decorator | `when` — conditional scheduling (execute code when condition is true) |
| `foxdot_tokenize.py` | Custom tokenizer | Tokenization support for FoxDot syntax |

## FoxDotCode — Execution Engine

The `FoxDotCode` class manages a shared namespace where all FoxDot objects live. When the user evaluates code (Ctrl+Enter in editor, or via REPL), it flows through:

```
code string → FoxDotCode._compile(string) → exec(bytecode, namespace) → side effects
```

**Key methods:**
- `__call__(code, verbose=True)` — Compile and execute code in the shared namespace
- `_compile(string)` — Compile to bytecode with error handling
- `use_sample_directory(dir)` — Redirect sample loading path
- `use_startup_file(path)` — Load custom startup code
- `update_line_numbers()` — Track which editor line each Player was defined on

**Namespace:** `FoxDotCode.namespace` is set to `globals()` of `lib/__init__.py`, meaning all Players, Patterns, Clock, etc. are available to user code.

## LiveObject — Self-Scheduling Base

`LiveObject` is the base class for objects that schedule themselves on the Clock:
- Stores a reference to the global `Clock`
- Has `__call__()` method for execution at scheduled time
- Has `kill()` method for removal from scheduler

Both `livefunction` and `when` inherit from `LiveObject`.

## Implementation Requirements

> See `docs/architecture/HANDOFF-02-repl-interface.md` for the full REPL spec.
> See `docs/architecture/HANDOFF-03-event-logger.md` for the EventLogger hook spec.

### REPL Interface Hook
The new REPL interface (Phase 2A) should call `FoxDotCode.__call__()` directly. The existing `--pipe` mode in `__main__.py` already demonstrates this pattern — it reads from stdin and executes via `FoxDotCode`. Extend this to support WebSocket input.

### Event Logging Hook
Add an optional callback in `FoxDotCode.__call__()` that fires after successful execution. This callback should pass the executed code string and timestamp to the EventLogger for Audacity label generation.

### Python 3.13 Cleanup
- `main_lib.py` lines 10–16: Remove `TypeType` fallback (`TypeType = type` is the only path on Py3)
- `main_lib.py` lines 69–78: Remove Py2 string codec handling
- Remove any `from __future__ import` statements
