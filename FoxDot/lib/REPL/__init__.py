"""
FoxDot REPL Module
------------------

Exposes FoxDot's code execution engine over multiple transports:
  - WebSocket (default port 5555) — for Flok, custom editors, wscat
  - stdin/stdout — for --pipe mode and simple integrations

Usage (WebSocket):
    from FoxDot.lib.REPL import REPLServer
    server = REPLServer(foxdot_code, clock, transport="websocket", port=5555)
    server.start()

Usage (stdin):
    from FoxDot.lib.REPL import REPLServer
    server = REPLServer(foxdot_code, clock, transport="stdin")
    server.start()  # blocks
"""

from .server import REPLServer

__all__ = ["REPLServer"]


def start_repl(foxdot_code, clock, transport="websocket", port=5555):
    """Convenience function: create and start a REPLServer.

    Args:
        foxdot_code: FoxDotCode instance.
        clock: TempoClock instance.
        transport: "websocket" or "stdin".
        port: WebSocket listen port (ignored for stdin).

    Returns:
        Running REPLServer instance.
    """
    server = REPLServer(foxdot_code, clock, transport=transport, port=port)
    server.start()
    return server
