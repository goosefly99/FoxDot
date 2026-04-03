"""
stdin/stdout Transport
----------------------

Reads code blocks from stdin (terminated by a blank line) and writes
JSON result lines to stdout.  This replaces the original --pipe mode
with a structured protocol.

Protocol (line-delimited):
    Input:  one or more lines of code, followed by a single blank line.
    Output: one JSON result line, followed by a blank line.

Example session::

    d1 >> pluck([0,1,2,3])
                              ← blank line terminates input block
    {"type":"result","id":"","success":true,"stdout":"","stderr":""}
                              ← blank line after result
"""

import sys
import threading


class StdinTransport:
    """Blocking stdin/stdout transport.  Calling start() never returns."""

    def __init__(self, server):
        self._server = server
        self._stop_event = threading.Event()

    def start(self):
        """Read code blocks from stdin and write results to stdout.  Blocks."""
        while not self._stop_event.is_set():
            try:
                code = self._read_block()
            except EOFError:
                break
            except KeyboardInterrupt:
                break

            if not code.strip():
                continue

            result = self._server.evaluate(code)
            sys.stdout.write(result.to_json() + "\n\n")
            sys.stdout.flush()

    def stop(self):
        self._stop_event.set()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _read_block(self) -> str:
        """Read lines until a blank line is encountered.  Raises EOFError on EOF."""
        lines = []
        while True:
            line = sys.stdin.readline()
            if line == "":
                # EOF
                raise EOFError
            line = line.rstrip("\n")
            if line == "":
                # Blank line — end of block
                break
            lines.append(line)
        return "\n".join(lines)
