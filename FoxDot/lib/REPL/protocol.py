"""
FoxDot REPL Protocol Definitions
---------------------------------

Defines the message format for communication between the FoxDot REPL server
and any connected editor (Flok, custom editor, wscat, etc.).

Transport: JSON over WebSocket (port 5555 by default)
Fallback:  Line-delimited JSON over stdin/stdout (--pipe mode)

Message flow:
    Client  ──eval──▶  REPLServer  ──▶  FoxDotCode.__call__()
    Client  ◀─result──  REPLServer  ◀──  stdout/stderr capture
    Client  ◀─state──   REPLServer  (periodic broadcast, every ~2s)

Stdin transport protocol:
    Input:  One code block per message, terminated by a blank line.
    Output: JSON result on a single line, followed by a blank line.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Message type constants
# ---------------------------------------------------------------------------

MSG_EVAL   = "eval"     # Client → Server
MSG_RESULT = "result"   # Server → Client (response to eval)
MSG_STATE  = "state"    # Server → Client (periodic broadcast)
MSG_ERROR  = "error"    # Server → Client (protocol-level error, not eval error)

# ---------------------------------------------------------------------------
# Inbound messages (Client → Server)
# ---------------------------------------------------------------------------

@dataclass
class EvalMessage:
    """Sent by the editor to request code evaluation.

    Fields:
        type:  Always "eval".
        id:    Opaque string echoed back in the result so the client can
               correlate async responses.  Use "" if correlation is not needed.
        code:  The Python/FoxDot source to execute.
    """

    type: str = MSG_EVAL
    id: str = ""
    code: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_dict(cls, d: dict) -> "EvalMessage":
        return cls(
            type=d.get("type", MSG_EVAL),
            id=d.get("id", ""),
            code=d.get("code", ""),
        )


# ---------------------------------------------------------------------------
# Outbound messages (Server → Client)
# ---------------------------------------------------------------------------

@dataclass
class PlayerState:
    """Snapshot of a single active Player.

    Fields:
        synth:   SynthDef name (e.g. "pluck", "play").
        active:  False when the player has been silenced with ``stop()``.
        amp:     Last known amplitude (optional).
    """

    synth: str = ""
    active: bool = True
    amp: Optional[float] = None

    def to_dict(self) -> dict:
        d = {"synth": self.synth, "active": self.active}
        if self.amp is not None:
            d["amp"] = self.amp
        return d


@dataclass
class ClockState:
    """Snapshot of the TempoClock.

    Fields:
        bpm:   Current beats per minute.
        beat:  Fractional beat position since the clock was started.
        bar:   Current bar number (beat / time_signature numerator).
    """

    bpm: float = 120.0
    beat: float = 0.0
    bar: int = 0


@dataclass
class ResultMessage:
    """Sent after each code evaluation, successful or not.

    On success:
        success=True, stdout/stderr capture any print() output.
        players is a snapshot of all active players after evaluation.

    On eval error:
        success=False, error contains the exception message,
        traceback contains the full traceback string.
    """

    type: str = MSG_RESULT
    id: str = ""
    success: bool = True
    stdout: str = ""
    stderr: str = ""
    error: str = ""
    traceback: str = ""
    players: dict = field(default_factory=dict)

    def to_json(self) -> str:
        d = {
            "type": self.type,
            "id": self.id,
            "success": self.success,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }
        if not self.success:
            d["error"] = self.error
            d["traceback"] = self.traceback
        if self.players:
            d["players"] = self.players
        return json.dumps(d)

    @classmethod
    def success_result(cls, id: str, stdout: str = "", stderr: str = "",
                       players: Optional[dict] = None) -> "ResultMessage":
        return cls(id=id, success=True, stdout=stdout, stderr=stderr,
                   players=players or {})

    @classmethod
    def error_result(cls, id: str, error: str, traceback: str = "") -> "ResultMessage":
        return cls(id=id, success=False, error=error, traceback=traceback)


@dataclass
class StateMessage:
    """Periodic broadcast of FoxDot runtime state.

    Sent approximately every REPL_STATE_BROADCAST_INTERVAL seconds to all
    connected WebSocket clients.  Not sent over stdin transport.

    Fields:
        clock:    Current clock snapshot.
        players:  Dict mapping player name → PlayerState dict.
    """

    type: str = MSG_STATE
    clock: dict = field(default_factory=dict)
    players: dict = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps({
            "type": self.type,
            "clock": self.clock,
            "players": self.players,
        })

    @classmethod
    def from_runtime(cls, clock_state: ClockState,
                     players: dict[str, PlayerState]) -> "StateMessage":
        return cls(
            clock={
                "bpm": clock_state.bpm,
                "beat": clock_state.beat,
                "bar": clock_state.bar,
            },
            players={name: ps.to_dict() for name, ps in players.items()},
        )


@dataclass
class ProtocolErrorMessage:
    """Sent when the server cannot parse an inbound message.

    This is a protocol-level error (malformed JSON, unknown type), distinct
    from a Python evaluation error which is reported via ResultMessage.
    """

    type: str = MSG_ERROR
    reason: str = ""

    def to_json(self) -> str:
        return json.dumps({"type": self.type, "reason": self.reason})


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def parse_message(raw: str) -> EvalMessage:
    """Parse a raw JSON string from the client into an EvalMessage.

    Raises:
        ValueError: if the JSON is malformed or the message type is not "eval".
    """
    try:
        d = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Malformed JSON: {exc}") from exc

    msg_type = d.get("type")
    if msg_type != MSG_EVAL:
        raise ValueError(f"Unknown message type: {msg_type!r}")

    return EvalMessage.from_dict(d)


