"""Tests for AudacityBridge macros module."""
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from FoxDot.lib.AudacityBridge.macros import (
    MACRO_NAME, MACRO_CONTENTS,
    get_macro_dir, is_macro_installed, install_macro,
)


class TestMacroConstants(unittest.TestCase):

    def test_macro_name(self):
        self.assertEqual(MACRO_NAME, "FoxDot-Master")

    def test_macro_contents_has_normalize(self):
        self.assertIn("Normalize", MACRO_CONTENTS)

    def test_macro_contents_has_compressor(self):
        self.assertIn("Compressor", MACRO_CONTENTS)

    def test_macro_contents_has_limiter(self):
        self.assertIn("Limiter", MACRO_CONTENTS)

    def test_macro_contents_has_filter_curve(self):
        self.assertIn("FilterCurve", MACRO_CONTENTS)


class TestGetMacroDir(unittest.TestCase):

    @patch("FoxDot.lib.AudacityBridge.macros.sys")
    @patch.dict(os.environ, {"APPDATA": "C:\\Users\\test\\AppData\\Roaming"})
    def test_windows(self, mock_sys):
        mock_sys.platform = "win32"
        result = get_macro_dir()
        self.assertEqual(result, "C:\\Users\\test\\AppData\\Roaming\\audacity\\Macros")

    @patch("FoxDot.lib.AudacityBridge.macros.sys")
    @patch.dict(os.environ, {}, clear=True)
    def test_windows_no_appdata_raises(self, mock_sys):
        mock_sys.platform = "win32"
        with self.assertRaises(RuntimeError):
            get_macro_dir()

    @patch("FoxDot.lib.AudacityBridge.macros.sys")
    def test_darwin(self, mock_sys):
        mock_sys.platform = "darwin"
        result = get_macro_dir()
        self.assertIn("Library/Application Support/audacity/Macros", result)

    @patch("FoxDot.lib.AudacityBridge.macros.sys")
    @patch("FoxDot.lib.AudacityBridge.macros.os.path.isdir", return_value=False)
    @patch.dict(os.environ, {"XDG_CONFIG_HOME": "/home/test/.config"})
    def test_linux_xdg(self, mock_isdir, mock_sys):
        mock_sys.platform = "linux"
        result = get_macro_dir()
        # os.path.join uses platform-specific separators
        expected = os.path.join("/home/test/.config", "audacity", "Macros")
        self.assertEqual(result, expected)

    @patch("FoxDot.lib.AudacityBridge.macros.sys")
    @patch("FoxDot.lib.AudacityBridge.macros.os.path.isdir", return_value=True)
    def test_linux_legacy_path(self, mock_isdir, mock_sys):
        mock_sys.platform = "linux"
        result = get_macro_dir()
        self.assertIn(".audacity-data/Macros", result)


class TestInstallMacro(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    @patch("FoxDot.lib.AudacityBridge.macros.get_macro_dir")
    def test_install_creates_file(self, mock_dir):
        mock_dir.return_value = self.tmpdir
        path = install_macro()
        self.assertTrue(os.path.exists(path))
        self.assertTrue(path.endswith("FoxDot-Master.txt"))
        with open(path) as f:
            content = f.read()
        self.assertEqual(content, MACRO_CONTENTS)

    @patch("FoxDot.lib.AudacityBridge.macros.get_macro_dir")
    def test_install_creates_subdirectory(self, mock_dir):
        subdir = os.path.join(self.tmpdir, "nested", "macros")
        mock_dir.return_value = subdir
        path = install_macro()
        self.assertTrue(os.path.exists(path))

    @patch("FoxDot.lib.AudacityBridge.macros.get_macro_dir")
    def test_install_custom_name(self, mock_dir):
        mock_dir.return_value = self.tmpdir
        path = install_macro(macro_name="MyMacro", contents="Test:param=1")
        self.assertTrue(path.endswith("MyMacro.txt"))
        with open(path) as f:
            self.assertEqual(f.read(), "Test:param=1")


class TestIsMacroInstalled(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    @patch("FoxDot.lib.AudacityBridge.macros.get_macro_dir")
    def test_not_installed(self, mock_dir):
        mock_dir.return_value = self.tmpdir
        self.assertFalse(is_macro_installed())

    @patch("FoxDot.lib.AudacityBridge.macros.get_macro_dir")
    def test_installed(self, mock_dir):
        mock_dir.return_value = self.tmpdir
        # Create the macro file
        with open(os.path.join(self.tmpdir, "FoxDot-Master.txt"), "w") as f:
            f.write("test")
        self.assertTrue(is_macro_installed())

    @patch("FoxDot.lib.AudacityBridge.macros.get_macro_dir")
    def test_runtime_error_returns_false(self, mock_dir):
        mock_dir.side_effect = RuntimeError("no APPDATA")
        self.assertFalse(is_macro_installed())


if __name__ == "__main__":
    unittest.main()
