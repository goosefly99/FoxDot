"""Tests for EventLogger module."""
import os
import tempfile
import time
import unittest
from unittest.mock import patch

from FoxDot.lib.EventLogger.logger import EventLogger


class TestEventLogger(unittest.TestCase):
    """Test EventLogger point labels, regions, and export."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.logger = EventLogger(output_dir=self.tmpdir, session_name="test_session")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_start_sets_time_and_clears_state(self):
        self.logger.start()
        self.assertIsNotNone(self.logger.start_time)
        # SESSION START event should be recorded
        self.assertEqual(len(self.logger.events), 1)
        self.assertEqual(self.logger.events[0][2], "SESSION START")

    def test_start_uses_provided_session_name(self):
        self.logger.start()
        self.assertEqual(self.logger.session_name, "test_session")

    def test_start_generates_session_name_when_none(self):
        logger = EventLogger(output_dir=self.tmpdir)
        logger.start()
        self.assertIsNotNone(logger.session_name)
        # Should be a timestamp string like 20260331_120000
        self.assertRegex(logger.session_name, r"^\d{8}_\d{6}$")

    def test_log_event_adds_point_label(self):
        self.logger.start()
        self.logger.log_event("BPM -> 140")
        # events: SESSION START + BPM -> 140
        self.assertEqual(len(self.logger.events), 2)
        start, end, label = self.logger.events[1]
        self.assertEqual(label, "BPM -> 140")
        self.assertEqual(start, end)  # point label: start == end

    def test_elapsed_returns_zero_before_start(self):
        self.assertEqual(self.logger._elapsed(), 0.0)

    @patch("FoxDot.lib.EventLogger.logger.time")
    def test_elapsed_returns_difference(self, mock_time):
        mock_time.time.return_value = 100.0
        mock_time.strftime = time.strftime
        self.logger.start()
        mock_time.time.return_value = 105.5
        self.assertAlmostEqual(self.logger._elapsed(), 5.5)

    def test_region_start_and_end(self):
        self.logger.start()
        self.logger.log_region_start("d1", "d1: pluck")
        self.assertIn("d1", self.logger.active_players)
        self.logger.log_region_end("d1")
        self.assertNotIn("d1", self.logger.active_players)
        # Should have SESSION START + the region
        region_events = [e for e in self.logger.events if e[2] == "d1: pluck"]
        self.assertEqual(len(region_events), 1)
        start, end, label = region_events[0]
        self.assertLessEqual(start, end)

    def test_region_end_without_start_is_noop(self):
        self.logger.start()
        initial_count = len(self.logger.events)
        self.logger.log_region_end("nonexistent")
        self.assertEqual(len(self.logger.events), initial_count)

    @patch("FoxDot.lib.EventLogger.logger.time")
    def test_write_labels_audacity_format(self, mock_time):
        mock_time.time.return_value = 1000.0
        mock_time.strftime = time.strftime
        self.logger.start()

        mock_time.time.return_value = 1001.5
        self.logger.log_event("BPM -> 120")

        mock_time.time.return_value = 1002.0
        self.logger.log_region_start("d1", "d1: pluck")

        mock_time.time.return_value = 1005.0
        self.logger.log_region_end("d1")

        filepath = os.path.join(self.tmpdir, "test_labels.txt")
        self.logger.write_labels(filepath)

        with open(filepath) as f:
            lines = f.readlines()

        # Should have: SESSION START, BPM -> 120, d1: pluck region
        self.assertEqual(len(lines), 3)

        # Verify tab-delimited format
        for line in lines:
            parts = line.strip().split("\t")
            self.assertEqual(len(parts), 3)
            float(parts[0])  # should be valid float
            float(parts[1])

        # Check sorted by start time
        starts = [float(line.split("\t")[0]) for line in lines]
        self.assertEqual(starts, sorted(starts))

    def test_stop_closes_open_regions_and_exports(self):
        self.logger.start()
        self.logger.log_region_start("d1", "d1: pluck")
        filepath = self.logger.stop()

        self.assertIsNotNone(filepath)
        self.assertTrue(os.path.exists(filepath))
        self.assertNotIn("d1", self.logger.active_players)

        # File should contain SESSION START, d1 region, SESSION END
        with open(filepath) as f:
            lines = f.readlines()
        labels = [line.strip().split("\t")[2] for line in lines]
        self.assertIn("SESSION START", labels)
        self.assertIn("SESSION END", labels)
        self.assertIn("d1: pluck", labels)

    def test_stop_before_start_returns_none(self):
        result = self.logger.stop()
        self.assertIsNone(result)

    def test_export_creates_output_dir(self):
        subdir = os.path.join(self.tmpdir, "nested", "dir")
        logger = EventLogger(output_dir=subdir, session_name="test")
        logger.start()
        filepath = logger.export()
        self.assertTrue(os.path.exists(filepath))
        self.assertEqual(os.path.dirname(filepath), subdir)

    def test_export_filename_includes_session_name(self):
        self.logger.start()
        filepath = self.logger.export()
        self.assertIn("test_session", os.path.basename(filepath))
        self.assertTrue(filepath.endswith(".txt"))


    def test_label_sanitizes_tabs_and_newlines(self):
        """Labels with tab or newline chars must not break Audacity format."""
        self.logger.start()
        self.logger.log_event("has\ttab")
        self.logger.log_event("has\nnewline")
        self.logger.log_region_start("d1", "region\twith\ttabs")
        self.logger.log_region_end("d1")

        filepath = os.path.join(self.tmpdir, "sanitize_test.txt")
        self.logger.write_labels(filepath)

        with open(filepath) as f:
            lines = f.readlines()

        for line in lines:
            parts = line.strip().split("\t")
            # Each line should have exactly 3 tab-separated fields
            self.assertEqual(len(parts), 3,
                             f"Label broke format: {line!r}")


if __name__ == "__main__":
    unittest.main()
