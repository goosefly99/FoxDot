"""Tests for REPLServer — evaluate(), snapshots, and transport selection."""
import unittest
from unittest.mock import MagicMock, patch

from FoxDot.lib.REPL.protocol import ResultMessage, StateMessage, ClockState, PlayerState
from FoxDot.lib.REPL.server import REPLServer


class FakeCode:
    """Minimal stand-in for FoxDotCode."""

    def __init__(self):
        self.namespace = {}
        self.last_code = None

    def __call__(self, code, verbose=True, verbose_error=True):
        self.last_code = code
        exec(code, self.namespace)


class FakeClock:
    def __init__(self, bpm=120.0):
        self.bpm = bpm
        self.meter = (4, 4)
        self._beat = 0.0

    def now(self):
        return self._beat


class TestREPLServerEvaluate(unittest.TestCase):

    def setUp(self):
        self.code = FakeCode()
        self.clock = FakeClock()
        self.server = REPLServer(self.code, self.clock)

    def test_evaluate_success(self):
        result = self.server.evaluate("x = 42")
        self.assertIsInstance(result, ResultMessage)
        self.assertTrue(result.success)
        self.assertEqual(result.error, "")

    def test_evaluate_captures_stdout(self):
        result = self.server.evaluate("print('hello')")
        self.assertIn("hello", result.stdout)

    def test_evaluate_captures_exception(self):
        # FakeCode's exec will raise NameError
        result = self.server.evaluate("undefined_var")
        self.assertFalse(result.success)
        self.assertIn("NameError", result.error + result.traceback)

    def test_evaluate_with_msg_id(self):
        result = self.server.evaluate("x = 1", msg_id="abc123")
        self.assertEqual(result.id, "abc123")

    def test_evaluate_restores_stdout_stderr(self):
        import sys
        orig_stdout = sys.stdout
        orig_stderr = sys.stderr
        self.server.evaluate("print('test')")
        self.assertIs(sys.stdout, orig_stdout)
        self.assertIs(sys.stderr, orig_stderr)

    def test_evaluate_restores_streams_on_exception(self):
        import sys
        orig_stdout = sys.stdout
        orig_stderr = sys.stderr

        # Make code raise
        def raising_code(code, verbose=True, verbose_error=True):
            raise RuntimeError("boom")

        self.code.__call__ = raising_code
        self.server._code = self.code
        result = self.server.evaluate("anything")

        self.assertIs(sys.stdout, orig_stdout)
        self.assertIs(sys.stderr, orig_stderr)
        self.assertFalse(result.success)


class TestREPLServerSnapshots(unittest.TestCase):

    def setUp(self):
        self.code = FakeCode()
        self.clock = FakeClock(bpm=140.0)
        self.clock._beat = 16.5
        self.server = REPLServer(self.code, self.clock)

    def test_snapshot_clock(self):
        state = self.server._snapshot_clock()
        self.assertIsInstance(state, ClockState)
        self.assertEqual(state.bpm, 140.0)
        self.assertEqual(state.beat, 16.5)
        self.assertEqual(state.bar, 4)  # 16.5 // 4 = 4

    def test_snapshot_clock_handles_exception(self):
        self.server._clock = MagicMock()
        self.server._clock.bpm = "not a number"
        # float("not a number") raises ValueError — should return default
        state = self.server._snapshot_clock()
        self.assertIsInstance(state, ClockState)

    def test_snapshot_players_empty(self):
        result = self.server._snapshot_players()
        self.assertEqual(result, {})

    def test_get_state_returns_state_message(self):
        state = self.server.get_state()
        self.assertIsInstance(state, StateMessage)


class TestREPLServerTransport(unittest.TestCase):

    def setUp(self):
        self.code = FakeCode()
        self.clock = FakeClock()

    def test_unknown_transport_raises(self):
        server = REPLServer(self.code, self.clock, transport="unknown")
        with self.assertRaises(ValueError):
            server.start()

    def test_stop_sets_flag(self):
        server = REPLServer(self.code, self.clock)
        server.stop()
        self.assertTrue(server._stop_event.is_set())

    def test_stop_calls_transport_stop(self):
        server = REPLServer(self.code, self.clock)
        mock_transport = MagicMock()
        server._transport = mock_transport
        server.stop()
        mock_transport.stop.assert_called_once()


class TestStdinTransportReadBlock(unittest.TestCase):

    def test_read_block_single_line(self):
        from FoxDot.lib.REPL.transports.stdin_transport import StdinTransport
        server = MagicMock()
        transport = StdinTransport(server)

        lines = ["d1 >> pluck()\n", "\n"]
        with patch("sys.stdin") as mock_stdin:
            mock_stdin.readline.side_effect = lines
            result = transport._read_block()
        self.assertEqual(result, "d1 >> pluck()")

    def test_read_block_multi_line(self):
        from FoxDot.lib.REPL.transports.stdin_transport import StdinTransport
        server = MagicMock()
        transport = StdinTransport(server)

        lines = ["d1 >> pluck()\n", "d2 >> bass()\n", "\n"]
        with patch("sys.stdin") as mock_stdin:
            mock_stdin.readline.side_effect = lines
            result = transport._read_block()
        self.assertEqual(result, "d1 >> pluck()\nd2 >> bass()")

    def test_read_block_eof_raises(self):
        from FoxDot.lib.REPL.transports.stdin_transport import StdinTransport
        server = MagicMock()
        transport = StdinTransport(server)

        with patch("sys.stdin") as mock_stdin:
            mock_stdin.readline.return_value = ""
            with self.assertRaises(EOFError):
                transport._read_block()


if __name__ == "__main__":
    unittest.main()
