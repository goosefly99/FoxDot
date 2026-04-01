"""
EventLogger — captures timestamped FoxDot performance events and writes
them as Audacity-compatible label track files (.txt).

Audacity label format (tab-delimited):
  Point label:   12.500000\t12.500000\tBPM -> 140
  Region label:  15.300000\t45.800000\td1: pluck section
"""

import logging
import os
import time

_logger = logging.getLogger(__name__)


def _sanitize_label(label):
    """Remove tab and newline characters that would break Audacity label format."""
    return str(label).replace('\t', ' ').replace('\n', ' ').replace('\r', '')


class EventLogger:

    def __init__(self, output_dir=".", session_name=None):
        self.output_dir = os.path.expanduser(output_dir)
        self.session_name = session_name
        self.events = []            # List of (start, end, label) tuples
        self.start_time = None      # Set when logging begins (time.time())
        self.active_players = {}    # Track player start times for regions

    def start(self):
        """Begin a logging session. Records the reference start time."""
        self.start_time = time.time()
        self.events = []
        self.active_players = {}
        if self.session_name is None:
            self.session_name = time.strftime("%Y%m%d_%H%M%S")
        self.log_event("SESSION START")

    def stop(self):
        """End the session. Close any open player regions and write labels."""
        if self.start_time is None:
            return None
        # Close all open player regions
        for key in list(self.active_players.keys()):
            self.log_region_end(key)
        self.log_event("SESSION END")
        return self.export()

    def _elapsed(self):
        """Seconds since session start."""
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time

    def log_event(self, label):
        """Add a point label at the current time."""
        t = self._elapsed()
        self.events.append((t, t, _sanitize_label(label)))

    def log_region_start(self, key, label):
        """Begin a region label (e.g., player start)."""
        self.active_players[key] = (self._elapsed(), _sanitize_label(label))

    def log_region_end(self, key):
        """End a region label (e.g., player stop)."""
        if key in self.active_players:
            start, label = self.active_players.pop(key)
            self.events.append((start, self._elapsed(), label))

    def write_labels(self, filepath):
        """Write all events to Audacity label format.

        Raises OSError if the file cannot be written.
        """
        sorted_events = sorted(self.events, key=lambda e: e[0])
        try:
            with open(filepath, 'w') as f:
                for start, end, label in sorted_events:
                    f.write("{:.6f}\t{:.6f}\t{}\n".format(start, end, label))
        except OSError:
            _logger.error("Failed to write labels to %s", filepath)
            raise

    def export(self):
        """Write labels to output_dir and return the filepath.

        Returns None if the file could not be written.
        """
        try:
            os.makedirs(self.output_dir, exist_ok=True)
        except OSError:
            _logger.error("Failed to create output directory %s", self.output_dir)
            return None
        filename = "foxdot_labels_{}.txt".format(self.session_name)
        filepath = os.path.join(self.output_dir, filename)
        try:
            self.write_labels(filepath)
        except OSError:
            return None
        return filepath
