# FoxDot REPL Module (`lib/REPL/`)

## Overview

Transport-agnostic REPL server that exposes FoxDot's code execution engine over WebSocket and stdin. Decouples FoxDot from any specific editor, enabling integration with Flok, custom editors, wscat, or simple pipe-based scripting.

## Architecture

```
[Editor / Flok / wscat]
        │
        ▼ (WebSocket :5555 or stdin)
  ┌─────────────┐
  │ Transport    │  stdin_transport.py  OR  websocket_transport.py
  └─────┬───────┘
        ▼
  ┌─────────────┐
  │ REPLServer   │  server.py — thread-safe evaluate(), stdout/stderr capture
  └─────┬───────┘
        ▼
  ┌──────────────┐
  │ FoxDotCode() │  lib/Code/ — actual code execution
  └──────────────┘
```

## Files

| File | Purpose |
|------|---------|
| `__init__.py` | Public API: `REPLServer`, `start_repl()` convenience function |
| `protocol.py` | Message dataclasses (`EvalMessage`, `ResultMessage`, `StateMessage`, `ProtocolErrorMessage`), JSON serialization, `parse_message()` |
| `server.py` | `REPLServer` class — transport-agnostic evaluate with stdout/stderr capture, clock/player snapshotting |
| `transports/__init__.py` | Transport subpackage |
| `transports/stdin_transport.py` | `StdinTransport` — reads code blocks from stdin (blank-line delimited), writes JSON results to stdout |
| `transports/websocket_transport.py` | `WebSocketTransport` — async WebSocket server (default port 5555), periodic state broadcast, multi-client support |

## Protocol

JSON messages over WebSocket or line-delimited JSON over stdin.

### Message Types

| Type | Direction | Purpose |
|------|-----------|---------|
| `eval` | Client -> Server | Request code evaluation |
| `result` | Server -> Client | Response with stdout/stderr/error/players |
| `state` | Server -> Client | Periodic broadcast (~2s) with clock + player state |
| `error` | Server -> Client | Protocol-level error (malformed JSON, unknown type) |

### Stdin Protocol

- **Input:** One code block per message, terminated by a blank line
- **Output:** JSON result on a single line, followed by a blank line

## Key Classes

- **`REPLServer`** — Main entry point. Takes `foxdot_code` and `clock` instances. Thread-safe `evaluate()` captures stdout/stderr via `io.StringIO` redirection. `get_state()` snapshots clock BPM/beat/bar and active player synths/amps.
- **`WebSocketTransport`** — Runs asyncio event loop in a daemon thread. Handles multiple concurrent clients. Broadcasts `StateMessage` every ~2 seconds.
- **`StdinTransport`** — Blocking transport for `--pipe` mode. Reads until blank line, evaluates, prints JSON result.

## Dependencies

- `websockets` package (optional — only needed for WebSocket transport)
- `asyncio` (stdlib)
- `threading` (stdlib)

## Integration Points

- `__main__.py` — `--pipe` flag triggers stdin transport
- `lib/Code/__init__.py` — `FoxDotCode.__call__()` is the execution target
- `lib/Settings/` — `REPL_STATE_BROADCAST_INTERVAL` controls broadcast frequency

## Handoff Spec

See `docs/architecture/HANDOFF-02-repl-interface.md` for original design spec.
