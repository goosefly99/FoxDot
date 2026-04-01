"""Tests for AudacityBridge bridge module — escape functions, pipe paths, and command formatting."""
import sys
import unittest
from unittest.mock import MagicMock, patch

from FoxDot.lib.AudacityBridge.bridge import (
    _escape_path, _get_pipe_paths, _PIPE_PATHS, AudacityBridge,
)


class TestEscapePath(unittest.TestCase):

    def test_plain_path(self):
        self.assertEqual(_escape_path("/home/user/file.wav"), "/home/user/file.wav")

    def test_windows_path(self):
        self.assertEqual(
            _escape_path(r"C:\Users\test\music.wav"),
            r"C:\Users\test\music.wav",
        )

    def test_path_with_double_quote(self):
        self.assertEqual(_escape_path('file"name.wav'), 'file\\"name.wav')

    def test_path_with_multiple_quotes(self):
        self.assertEqual(_escape_path('"a"b"'), '\\"a\\"b\\"')

    def test_path_object_converted_to_str(self):
        from pathlib import PurePosixPath
        p = PurePosixPath("/tmp/test.wav")
        result = _escape_path(p)
        self.assertIsInstance(result, str)
        self.assertIn("test.wav", result)

    def test_empty_string(self):
        self.assertEqual(_escape_path(""), "")

    def test_spaces_in_path(self):
        self.assertEqual(
            _escape_path("/home/user/my file.wav"),
            "/home/user/my file.wav",
        )


class TestGetPipePaths(unittest.TestCase):

    @patch("FoxDot.lib.AudacityBridge.bridge.sys")
    def test_win32(self, mock_sys):
        mock_sys.platform = "win32"
        result = _get_pipe_paths()
        self.assertEqual(result, _PIPE_PATHS['win32'])

    @patch("FoxDot.lib.AudacityBridge.bridge.sys")
    def test_darwin(self, mock_sys):
        mock_sys.platform = "darwin"
        result = _get_pipe_paths()
        self.assertEqual(result, _PIPE_PATHS['darwin'])

    @patch("FoxDot.lib.AudacityBridge.bridge.sys")
    def test_linux(self, mock_sys):
        mock_sys.platform = "linux"
        result = _get_pipe_paths()
        self.assertEqual(result, _PIPE_PATHS['linux'])

    @patch("FoxDot.lib.AudacityBridge.bridge.sys")
    def test_unknown_platform_falls_back_to_linux(self, mock_sys):
        mock_sys.platform = "freebsd12"
        result = _get_pipe_paths()
        self.assertEqual(result, _PIPE_PATHS['linux'])


class TestAudacityBridgeCommands(unittest.TestCase):
    """Test command formatting without requiring a real Audacity connection."""

    def _make_bridge(self):
        """Create a bridge with a mock _send method (bypass __init__ connection)."""
        bridge = object.__new__(AudacityBridge)
        bridge._to_pipe = None
        bridge._from_pipe = None
        bridge._pyaudacity = None
        bridge._sent_commands = []

        def fake_send(cmd):
            bridge._sent_commands.append(cmd)
            return "OK"

        bridge._send = fake_send
        return bridge

    def test_record_command(self):
        bridge = self._make_bridge()
        bridge.record()
        self.assertEqual(bridge._sent_commands[-1], "Record2ndChoice:")

    def test_stop_command(self):
        bridge = self._make_bridge()
        bridge.stop()
        self.assertEqual(bridge._sent_commands[-1], "Stop:")

    def test_pause_command(self):
        bridge = self._make_bridge()
        bridge.pause()
        self.assertEqual(bridge._sent_commands[-1], "Pause:")

    def test_import_labels_escapes_path(self):
        bridge = self._make_bridge()
        bridge.import_labels('/tmp/my "labels".txt')
        cmd = bridge._sent_commands[-1]
        self.assertIn('Import2:', cmd)
        self.assertIn('my \\"labels\\"', cmd)

    def test_export_labels_escapes_path(self):
        bridge = self._make_bridge()
        bridge.export_labels("/tmp/output.txt")
        cmd = bridge._sent_commands[-1]
        self.assertIn("ExportLabels:", cmd)
        self.assertIn("/tmp/output.txt", cmd)

    def test_run_macro_escapes_name(self):
        bridge = self._make_bridge()
        bridge.run_macro('My"Macro')
        cmd = bridge._sent_commands[-1]
        self.assertIn("ApplyMacrosPalette:", cmd)
        self.assertIn('My\\"Macro', cmd)

    def test_apply_foxdot_master(self):
        bridge = self._make_bridge()
        bridge.apply_foxdot_master()
        cmd = bridge._sent_commands[-1]
        self.assertIn("FoxDot-Master", cmd)

    def test_export_audio_wav(self):
        bridge = self._make_bridge()
        bridge.export_audio("/tmp/output", "WAV")
        cmd = bridge._sent_commands[-1]
        self.assertIn("Export2:", cmd)
        self.assertIn("/tmp/output.wav", cmd)
        self.assertIn("NumChannels=2", cmd)

    def test_export_audio_mp3(self):
        bridge = self._make_bridge()
        bridge.export_audio("/tmp/output", "MP3")
        cmd = bridge._sent_commands[-1]
        self.assertIn("/tmp/output.mp3", cmd)

    def test_export_audio_already_has_extension(self):
        bridge = self._make_bridge()
        bridge.export_audio("/tmp/output.wav", "WAV")
        cmd = bridge._sent_commands[-1]
        # Should NOT double the extension
        self.assertNotIn(".wav.wav", cmd)
        self.assertIn("/tmp/output.wav", cmd)

    def test_export_audio_unknown_format_defaults_wav(self):
        bridge = self._make_bridge()
        bridge.export_audio("/tmp/output", "AIFF")
        cmd = bridge._sent_commands[-1]
        self.assertIn("/tmp/output.wav", cmd)

    def test_export_audio_case_insensitive_format(self):
        bridge = self._make_bridge()
        bridge.export_audio("/tmp/output", "flac")
        cmd = bridge._sent_commands[-1]
        self.assertIn("/tmp/output.flac", cmd)

    def test_save_project(self):
        bridge = self._make_bridge()
        bridge.save_project("/tmp/session.aup3")
        cmd = bridge._sent_commands[-1]
        self.assertIn("SaveProject2:", cmd)
        self.assertIn("/tmp/session.aup3", cmd)

    def test_open_file(self):
        bridge = self._make_bridge()
        bridge.open_file("/tmp/audio.wav")
        cmd = bridge._sent_commands[-1]
        self.assertIn("Import2:", cmd)
        self.assertIn("/tmp/audio.wav", cmd)


class TestAudacityBridgeConnection(unittest.TestCase):

    def test_is_connected_with_pyaudacity(self):
        bridge = object.__new__(AudacityBridge)
        bridge._to_pipe = None
        bridge._from_pipe = None
        bridge._pyaudacity = MagicMock()
        self.assertTrue(bridge.is_connected())

    def test_is_connected_with_pipes(self):
        bridge = object.__new__(AudacityBridge)
        bridge._to_pipe = MagicMock()
        bridge._from_pipe = MagicMock()
        bridge._pyaudacity = None
        self.assertTrue(bridge.is_connected())

    def test_not_connected(self):
        bridge = object.__new__(AudacityBridge)
        bridge._to_pipe = None
        bridge._from_pipe = None
        bridge._pyaudacity = None
        self.assertFalse(bridge.is_connected())

    def test_close_clears_pipes(self):
        bridge = object.__new__(AudacityBridge)
        bridge._to_pipe = MagicMock()
        bridge._from_pipe = MagicMock()
        bridge._pyaudacity = None
        bridge.close()
        self.assertIsNone(bridge._to_pipe)
        self.assertIsNone(bridge._from_pipe)

    def test_close_handles_os_error(self):
        bridge = object.__new__(AudacityBridge)
        mock_pipe = MagicMock()
        mock_pipe.close.side_effect = OSError("broken pipe")
        bridge._to_pipe = mock_pipe
        bridge._from_pipe = None
        bridge._pyaudacity = None
        # Should not raise
        bridge.close()
        self.assertIsNone(bridge._to_pipe)

    def test_send_via_pyaudacity(self):
        bridge = object.__new__(AudacityBridge)
        bridge._to_pipe = None
        bridge._from_pipe = None
        bridge._pyaudacity = MagicMock()
        bridge._pyaudacity.do.return_value = "OK"
        result = bridge._send("Stop:")
        bridge._pyaudacity.do.assert_called_once_with("Stop:")
        self.assertEqual(result, "OK")

    def test_send_without_connection_raises(self):
        bridge = object.__new__(AudacityBridge)
        bridge._to_pipe = None
        bridge._from_pipe = None
        bridge._pyaudacity = None
        with self.assertRaises(ConnectionError):
            bridge._send("Stop:")

    def test_connect_raises_when_no_pipe_no_pyaudacity(self):
        with patch("builtins.open", side_effect=OSError("not found")):
            with patch.dict("sys.modules", {"pyaudacity": None}):
                with self.assertRaises(ConnectionError):
                    AudacityBridge()


if __name__ == "__main__":
    unittest.main()
