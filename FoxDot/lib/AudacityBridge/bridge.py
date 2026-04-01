"""
AudacityBridge — wraps Audacity's mod-script-pipe (or PyAudacity) to
provide transport control, label import, macro execution, and export.
"""

import sys
import time

# Pipe paths vary by platform
_PIPE_PATHS = {
    'win32': (r'\\.\pipe\ToSrvPipe', r'\\.\pipe\FromSrvPipe'),
    'darwin': ('/tmp/audacity_script_pipe.to.', '/tmp/audacity_script_pipe.from.'),
    'linux': ('/tmp/audacity_script_pipe.to.', '/tmp/audacity_script_pipe.from.'),
}

# Timeout for reading a response from the pipe (seconds)
_READ_TIMEOUT = 10.0


def _escape_path(filepath):
    """Escape a file path for use in Audacity pipe commands.

    Audacity commands use double-quoted strings.  A path containing a
    literal double-quote would break the command syntax and could cause
    unexpected behaviour.  We replace any embedded quotes with their
    escaped form.
    """
    return str(filepath).replace('"', '\\"')


def _get_pipe_paths():
    """Return (to_pipe, from_pipe) for the current platform."""
    for key in _PIPE_PATHS:
        if sys.platform.startswith(key):
            return _PIPE_PATHS[key]
    # Fallback to Linux-style paths
    return _PIPE_PATHS['linux']


class AudacityBridge:
    """Communicate with a running Audacity instance via mod-script-pipe.

    Falls back to the ``pyaudacity`` package when available, but the
    primary transport is the named pipe which works without extra
    dependencies.
    """

    def __init__(self):
        self._to_pipe = None
        self._from_pipe = None
        self._pyaudacity = None
        self._connect()

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def _connect(self):
        """Open the named pipes to Audacity, or fall back to PyAudacity."""
        to_path, from_path = _get_pipe_paths()

        try:
            self._to_pipe = open(to_path, 'w', encoding='utf-8')
            try:
                self._from_pipe = open(from_path, 'r', encoding='utf-8')
            except BaseException:
                self._to_pipe.close()
                self._to_pipe = None
                raise
            return
        except OSError:
            pass

        # Pipe unavailable — try PyAudacity
        try:
            import pyaudacity  # type: ignore
            self._pyaudacity = pyaudacity
            return
        except ImportError:
            pass

        raise ConnectionError(
            "Cannot connect to Audacity. Ensure Audacity is running with "
            "mod-script-pipe enabled, or install the pyaudacity package."
        )

    def is_connected(self):
        """Return True if we have an active connection to Audacity."""
        if self._pyaudacity is not None:
            return True
        return self._to_pipe is not None and self._from_pipe is not None

    def close(self):
        """Close pipe handles.  Always attempts both even if the first fails."""
        for attr in ('_to_pipe', '_from_pipe'):
            f = getattr(self, attr, None)
            if f is not None:
                try:
                    f.close()
                except OSError:
                    pass
                finally:
                    setattr(self, attr, None)

    # ------------------------------------------------------------------
    # Low-level pipe communication
    # ------------------------------------------------------------------

    def _send(self, command):
        """Send a command string and return the response text."""
        if self._pyaudacity is not None:
            return self._pyaudacity.do(command)

        if self._to_pipe is None or self._from_pipe is None:
            raise ConnectionError("Not connected to Audacity")

        self._to_pipe.write(command + '\n')
        self._to_pipe.flush()

        # Read response lines until we get an empty line or timeout.
        # Use rstrip('\r\n') instead of strip() to avoid treating
        # whitespace-only response lines as end-of-response markers.
        # Audacity terminates responses with a blank line ('\n').
        lines = []
        deadline = time.time() + _READ_TIMEOUT
        while time.time() < deadline:
            line = self._from_pipe.readline()
            if not line or line.rstrip('\r\n') == '':
                break
            lines.append(line.rstrip('\r\n'))

        return '\n'.join(lines)

    # ------------------------------------------------------------------
    # Transport Control
    # ------------------------------------------------------------------

    def record(self):
        """Start recording in Audacity."""
        return self._send('Record2ndChoice:')

    def stop(self):
        """Stop recording/playback."""
        return self._send('Stop:')

    def pause(self):
        """Pause recording/playback."""
        return self._send('Pause:')

    # ------------------------------------------------------------------
    # Label Operations
    # ------------------------------------------------------------------

    def import_labels(self, filepath):
        """Import a label track from a .txt file.

        Args:
            filepath: Absolute path to an Audacity-format label file.
        """
        return self._send('Import2: Filename="{}"'.format(_escape_path(filepath)))

    def export_labels(self, filepath):
        """Export current labels to a .txt file.

        Args:
            filepath: Destination path for the exported label file.
        """
        return self._send('ExportLabels: Filename="{}"'.format(_escape_path(filepath)))

    # ------------------------------------------------------------------
    # Macro Operations
    # ------------------------------------------------------------------

    def run_macro(self, macro_name):
        """Run a named Audacity macro on the current project.

        Args:
            macro_name: Name of an installed Audacity macro (e.g. "FoxDot-Master").
        """
        return self._send('ApplyMacrosPalette: MacroName="{}"'.format(
            _escape_path(macro_name)))

    def apply_foxdot_master(self):
        """Run the FoxDot-Master mastering macro."""
        return self.run_macro("FoxDot-Master")

    # ------------------------------------------------------------------
    # Export / File Operations
    # ------------------------------------------------------------------

    def export_audio(self, filepath, format="WAV"):
        """Export the current project to a file.

        Args:
            filepath: Output path for the exported audio.
            format: Audio format — WAV, MP3, OGG, or FLAC.
        """
        # Audacity's Export2 command accepts NumChannels and uses the
        # file extension to infer format when possible.
        ext_map = {'WAV': '.wav', 'MP3': '.mp3', 'OGG': '.ogg', 'FLAC': '.flac'}
        ext = ext_map.get(format.upper(), '.wav')
        if not filepath.lower().endswith(ext):
            filepath = filepath + ext
        return self._send('Export2: Filename="{}" NumChannels=2'.format(_escape_path(filepath)))

    def save_project(self, filepath):
        """Save the current Audacity project (.aup3).

        Args:
            filepath: Destination path for the project file.
        """
        return self._send('SaveProject2: Filename="{}"'.format(_escape_path(filepath)))

    def open_file(self, filepath):
        """Open an audio file in Audacity.

        Args:
            filepath: Path to the audio file to open.
        """
        return self._send('Import2: Filename="{}"'.format(_escape_path(filepath)))
