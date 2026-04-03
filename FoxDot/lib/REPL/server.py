"""
FoxDot REPL Server
------------------

Transport-agnostic REPL server.  Delegates I/O to a Transport object
while providing a single evaluate() method that runs FoxDot code safely
from any thread.
"""

import io
import logging
import sys
import threading
import traceback

logger = logging.getLogger(__name__)

from .protocol import (
    EvalMessage, ResultMessage, StateMessage, ClockState, PlayerState,
    parse_message,
)


class REPLServer:
    """Transport-agnostic REPL server for FoxDot.

    Args:
        foxdot_code: FoxDotCode instance (from lib/Code/__init__.py).
        clock: TempoClock instance.
        transport: "websocket" or "stdin".
        port: WebSocket listen port (ignored for stdin transport).
    """

    def __init__(self, foxdot_code, clock, transport="websocket", port=5555):
        self._code = foxdot_code
        self._clock = clock
        self._port = port
        self._transport_name = transport
        self._transport = None
        self._lock = threading.Lock()
        self._stop_event = threading.Event()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self):
        """Start the REPL server.

        For WebSocket transport this launches a background thread and returns
        immediately.  For stdin transport this blocks until EOF or interrupt.
        """
        if self._transport_name == "websocket":
            self._start_websocket()
        elif self._transport_name == "stdin":
            self._start_stdin()
        else:
            raise ValueError(
                f"Unknown transport: {self._transport_name!r}. "
                "Use 'websocket' or 'stdin'."
            )

    def stop(self):
        """Gracefully shut down the server."""
        self._stop_event.set()
        if self._transport is not None:
            self._transport.stop()

    def evaluate(self, code: str, msg_id: str = "") -> ResultMessage:
        """Execute *code* via FoxDotCode and return a ResultMessage.

        Captures stdout/stderr produced during execution.  Thread-safe.
        """
        # Capture stdout/stderr for the duration of this call only.
        captured_out = io.StringIO()
        captured_err = io.StringIO()

        with self._lock:
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = captured_out
            sys.stderr = captured_err
            try:
                self._code(code, verbose=False, verbose_error=False)
                error_msg = ""
                tb_str = ""
                success = True
            except Exception as exc:
                error_msg = str(exc)
                tb_str = traceback.format_exc()
                success = False
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

        stdout_val = captured_out.getvalue()
        stderr_val = captured_err.getvalue()
        captured_out.close()
        captured_err.close()

        if not success:
            return ResultMessage.error_result(msg_id, error_msg, tb_str)

        # FoxDotCode.__call__ may catch exceptions internally and write the
        # traceback to stderr instead of re-raising.
        if stderr_val:
            return ResultMessage.error_result(msg_id, stderr_val.strip(), stderr_val)

        players = self._snapshot_players()
        return ResultMessage.success_result(
            msg_id, stdout=stdout_val, stderr=stderr_val, players=players
        )

    def get_state(self) -> StateMessage:
        """Return a StateMessage with current clock and player snapshot."""
        clock_state = self._snapshot_clock()
        players = self._snapshot_players()
        return StateMessage.from_runtime(clock_state, players)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _snapshot_clock(self) -> ClockState:
        try:
            bpm = float(self._clock.bpm)
            beat = float(self._clock.now())
            # bar = beat // time_signature numerator (default 4)
            meter_num = getattr(self._clock, "meter", (4, 4))[0]
            bar = int(beat // meter_num)
            return ClockState(bpm=bpm, beat=round(beat, 3), bar=bar)
        except Exception:
            logger.debug("Failed to snapshot clock state", exc_info=True)
            return ClockState()

    def _snapshot_players(self) -> dict[str, PlayerState]:
        """Walk FoxDotCode.namespace looking for active Player instances."""
        result = {}
        try:
            ns = self._code.namespace
            # Import Player lazily to avoid circular imports at module load time.
            from ..Players import Player
            for name, obj in list(ns.items()):
                if isinstance(obj, Player) and not name.startswith("_"):
                    synth_name = ""
                    if obj.synthdef is not None:
                        synth_name = getattr(obj.synthdef, "__name__", str(obj.synthdef))
                    amp = None
                    try:
                        raw_amp = obj.amp
                        amp = float(raw_amp.now() if hasattr(raw_amp, "now") else raw_amp)
                    except Exception:
                        logger.debug("Failed to read amp for player %s", name)
                    result[name] = PlayerState(
                        synth=synth_name,
                        active=bool(getattr(obj, "isAlive", True)),
                        amp=amp,
                    )
        except Exception:
            logger.debug("Failed to snapshot players", exc_info=True)
        return result

    # ------------------------------------------------------------------
    # Transport launchers
    # ------------------------------------------------------------------

    def _start_websocket(self):
        from .transports.websocket_transport import WebSocketTransport
        self._transport = WebSocketTransport(self, self._port)
        self._transport.start()

    def _start_stdin(self):
        from .transports.stdin_transport import StdinTransport
        self._transport = StdinTransport(self)
        self._transport.start()  # blocks
