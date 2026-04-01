"""
WebSocket Transport
-------------------

Serves a WebSocket endpoint that accepts EvalMessage JSON and returns
ResultMessage JSON.  Also broadcasts periodic StateMessage JSON to all
connected clients.

Requires the ``websockets`` package (pip install websockets>=12.0).

The server runs in its own daemon thread so it does not block the main
FoxDot thread.  A second timer thread handles state broadcasts.
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
import time

logger = logging.getLogger(__name__)

try:
    import websockets
    import websockets.server
    _WEBSOCKETS_AVAILABLE = True
except ImportError:
    _WEBSOCKETS_AVAILABLE = False


class WebSocketTransport:
    """Async WebSocket server running in a background thread.

    Args:
        server: REPLServer instance.
        port: TCP port to listen on.
    """

    def __init__(self, server, port: int = 5555):
        if not _WEBSOCKETS_AVAILABLE:
            raise ImportError(
                "The 'websockets' package is required for WebSocket transport. "
                "Install it with: pip install 'FoxDot[repl]'"
            )
        self._server = server
        self._port = port
        self._loop: asyncio.AbstractEventLoop | None = None
        self._ws_server = None
        self._clients: set = set()
        self._clients_lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._broadcast_thread: threading.Thread | None = None
        self._stopped = False

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def start(self):
        """Launch the WebSocket server in a background daemon thread."""
        self._thread = threading.Thread(
            target=self._run_event_loop,
            name="FoxDot-REPL-WS",
            daemon=True,
        )
        self._thread.start()

        # Give the event loop a moment to bind before we return.
        time.sleep(0.1)

        # State broadcast in a separate daemon thread.
        self._broadcast_thread = threading.Thread(
            target=self._broadcast_loop,
            name="FoxDot-REPL-Broadcast",
            daemon=True,
        )
        self._broadcast_thread.start()

        logger.info("FoxDot REPL WebSocket server started on ws://localhost:%d", self._port)

    def stop(self):
        """Signal the server to stop."""
        self._stopped = True
        if self._loop is not None and self._ws_server is not None:
            self._loop.call_soon_threadsafe(self._ws_server.close)

    # ------------------------------------------------------------------
    # Async internals
    # ------------------------------------------------------------------

    def _run_event_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._serve())
        finally:
            self._loop.close()

    async def _serve(self):
        async with websockets.server.serve(
            self._handle_client, "localhost", self._port
        ) as ws_server:
            self._ws_server = ws_server
            await ws_server.wait_closed()

    async def _handle_client(self, websocket):
        """Handle one WebSocket connection for its lifetime."""
        with self._clients_lock:
            self._clients.add(websocket)
        try:
            async for raw in websocket:
                response = await self._handle_message(raw)
                await websocket.send(response)
        except Exception:
            pass
        finally:
            with self._clients_lock:
                self._clients.discard(websocket)

    async def _handle_message(self, raw: str) -> str:
        from ..protocol import parse_message, ProtocolErrorMessage
        try:
            eval_msg = parse_message(raw)
        except ValueError as exc:
            return ProtocolErrorMessage(reason=str(exc)).to_json()

        # evaluate() is synchronous and holds self._server._lock, so run it
        # in the default executor to avoid blocking the event loop.
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, self._server.evaluate, eval_msg.code, eval_msg.id
        )
        return result.to_json()

    # ------------------------------------------------------------------
    # State broadcast
    # ------------------------------------------------------------------

    def _broadcast_loop(self):
        """Periodically broadcast state to all connected clients."""
        from ..protocol import StateMessage
        try:
            from ...Settings import REPL_STATE_BROADCAST_INTERVAL
            interval = float(REPL_STATE_BROADCAST_INTERVAL)
        except Exception:
            interval = 2.0

        while not self._stopped:
            time.sleep(interval)
            with self._clients_lock:
                has_clients = bool(self._clients)
            if not has_clients:
                continue
            try:
                state_msg = self._server.get_state().to_json()
                self._broadcast_sync(state_msg)
            except Exception as exc:
                logger.debug("State broadcast error: %s", exc)

    def _broadcast_sync(self, message: str):
        """Send *message* to all connected clients from a non-async context."""
        with self._clients_lock:
            has_clients = bool(self._clients)
        if self._loop is None or not has_clients:
            return
        asyncio.run_coroutine_threadsafe(
            self._broadcast_async(message), self._loop
        )

    async def _broadcast_async(self, message: str):
        dead = set()
        with self._clients_lock:
            snapshot = list(self._clients)
        for client in snapshot:
            try:
                await client.send(message)
            except Exception:
                dead.add(client)
        if dead:
            with self._clients_lock:
                self._clients -= dead
