"""
Comprehensive tests for the Buffers module.

Covers: _symbolToDir, Buffer, BufferManager (allocation, search, load/free,
path management, sizing, string representations), hasext, nonalpha/DESCRIPTIONS
data integrity, and Midi module (MidiInputHandler, MidiOut, exceptions).
"""

import os
import shutil
import struct
import tempfile
import unittest
import wave
from contextlib import closing
from os.path import join, isdir
from unittest.mock import MagicMock, patch, PropertyMock

from FoxDot.lib.Buffers import (
    Buffer,
    BufferManager,
    _symbolToDir,
    alpha,
    hasext,
    nil,
    nonalpha,
    DESCRIPTIONS,
    symbolToDir,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_wav(path, channels=1, sampwidth=2, framerate=44100, nframes=100):
    """Create a minimal valid .wav file at *path*."""
    with wave.open(path, "w") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(framerate)
        wf.writeframes(b"\x00" * sampwidth * channels * nframes)


class _TempDirMixin:
    """Mixin that creates a temp directory tree for sample searching."""

    def setUp(self):
        super().setUp()
        self.wd = tempfile.mkdtemp()

    def tearDown(self):
        super().tearDown()
        shutil.rmtree(self.wd, ignore_errors=True)

    # convenience helpers ------------------------------------------------
    def _mkdir(self, *parts):
        d = join(self.wd, *parts)
        os.makedirs(d, exist_ok=True)
        return d

    def _touch(self, *parts, wav=False, channels=1):
        full = join(self.wd, *parts)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        if wav:
            _make_wav(full, channels=channels)
        else:
            open(full, "w").close()
        return os.path.normpath(full)

    def _make_bm(self, paths=None):
        """Return a BufferManager whose server methods are no-ops."""
        mock_server = MagicMock()
        mock_server.max_buffers = 1024
        bm = BufferManager.__new__(BufferManager)
        bm._server = mock_server
        bm._max_buffers = 1024
        bm._nextbuf = 1
        bm._buffers = [None] * 1024
        bm._fn_to_buf = {}
        bm._paths = paths if paths is not None else [self.wd]
        bm._ext = ["wav", "wave", "aif", "aiff", "flac"]
        bm.loops = []
        return bm


# ===================================================================
# _symbolToDir
# ===================================================================

class TestSymbolToDir(_TempDirMixin, unittest.TestCase):
    """Tests for the _symbolToDir helper class."""

    def test_lowercase_alpha(self):
        s2d = _symbolToDir(self.wd)
        result = s2d("a")
        self.assertEqual(result, join(self.wd, "a", "lower"))

    def test_uppercase_alpha(self):
        s2d = _symbolToDir(self.wd)
        result = s2d("A")
        self.assertEqual(result, join(self.wd, "a", "upper"))

    def test_all_lowercase_letters(self):
        s2d = _symbolToDir(self.wd)
        for ch in alpha:
            result = s2d(ch)
            self.assertEqual(result, join(self.wd, ch, "lower"), msg=f"symbol={ch!r}")

    def test_all_uppercase_letters(self):
        s2d = _symbolToDir(self.wd)
        for ch in alpha.upper():
            result = s2d(ch)
            self.assertEqual(
                result, join(self.wd, ch.lower(), "upper"), msg=f"symbol={ch!r}"
            )

    def test_nonalpha_symbols(self):
        s2d = _symbolToDir(self.wd)
        for sym, longname in nonalpha.items():
            result = s2d(sym)
            self.assertEqual(
                result, join(self.wd, "_", longname), msg=f"symbol={sym!r}"
            )

    def test_unknown_symbol_returns_none(self):
        s2d = _symbolToDir(self.wd)
        self.assertIsNone(s2d("`"))

    def test_whitespace_returns_none(self):
        s2d = _symbolToDir(self.wd)
        # space is not in nonalpha and not alpha
        self.assertIsNone(s2d(" "))

    def test_set_root_valid(self):
        s2d = _symbolToDir(self.wd)
        new_dir = self._mkdir("new_root")
        s2d.set_root(new_dir)
        self.assertEqual(s2d.root, os.path.realpath(new_dir))

    def test_set_root_invalid_raises(self):
        s2d = _symbolToDir(self.wd)
        with self.assertRaises(OSError):
            s2d.set_root("/nonexistent/path/xyz")

    def test_set_root_preserves_functionality(self):
        new_dir = self._mkdir("alt_root")
        s2d = _symbolToDir(self.wd)
        s2d.set_root(new_dir)
        self.assertEqual(s2d("x"), join(os.path.realpath(new_dir), "x", "lower"))

    def test_digit_symbols(self):
        s2d = _symbolToDir(self.wd)
        for d in "1234":
            result = s2d(d)
            expected = join(self.wd, "_", d)
            self.assertEqual(result, expected, msg=f"digit={d!r}")

    def test_global_singleton_exists(self):
        self.assertIsInstance(symbolToDir, _symbolToDir)


# ===================================================================
# Buffer
# ===================================================================

class TestBuffer(unittest.TestCase):
    """Tests for the Buffer dataclass-like object."""

    def test_construction(self):
        b = Buffer("test.wav", 42, channels=2)
        self.assertEqual(b.fn, "test.wav")
        self.assertEqual(b.bufnum, 42)
        self.assertEqual(b.channels, 2)

    def test_default_channels(self):
        b = Buffer("test.wav", 1)
        self.assertEqual(b.channels, 1)

    def test_repr(self):
        b = Buffer("a.wav", 7)
        self.assertEqual(repr(b), "<Buffer num 7>")

    def test_int(self):
        b = Buffer("a.wav", 99)
        self.assertEqual(int(b), 99)

    def test_bufnum_coercion(self):
        b = Buffer("a.wav", 3.9)
        self.assertEqual(b.bufnum, 3)
        self.assertIsInstance(b.bufnum, int)

    def test_fromFile_mono_wav(self):
        td = tempfile.mkdtemp()
        try:
            path = join(td, "mono.wav")
            _make_wav(path, channels=1)
            b = Buffer.fromFile(path, 10)
            self.assertEqual(b.bufnum, 10)
            self.assertEqual(b.channels, 1)
            self.assertEqual(b.fn, path)
        finally:
            shutil.rmtree(td)

    def test_fromFile_stereo_wav(self):
        td = tempfile.mkdtemp()
        try:
            path = join(td, "stereo.wav")
            _make_wav(path, channels=2)
            b = Buffer.fromFile(path, 20)
            self.assertEqual(b.channels, 2)
        finally:
            shutil.rmtree(td)

    def test_fromFile_invalid_wav_falls_back_mono(self):
        td = tempfile.mkdtemp()
        try:
            path = join(td, "bad.wav")
            with open(path, "wb") as f:
                f.write(b"not a wav file")
            b = Buffer.fromFile(path, 5)
            self.assertEqual(b.channels, 1)
        finally:
            shutil.rmtree(td)


class TestNilBuffer(unittest.TestCase):
    """Tests for the module-level nil buffer."""

    def test_nil_bufnum(self):
        self.assertEqual(nil.bufnum, 0)

    def test_nil_fn(self):
        self.assertEqual(nil.fn, "")

    def test_nil_int(self):
        self.assertEqual(int(nil), 0)


# ===================================================================
# hasext
# ===================================================================

class TestHasExt(unittest.TestCase):
    """Tests for the hasext() utility."""

    def test_with_extension(self):
        self.assertTrue(hasext("foo.wav"))

    def test_without_extension(self):
        self.assertFalse(hasext("foo"))

    def test_hidden_file_no_ext(self):
        # On Unix-style, .hidden has ext ".hidden" per splitext
        # splitext(".hidden") -> (".hidden", "")
        self.assertFalse(hasext(".hidden"))

    def test_multiple_dots(self):
        self.assertTrue(hasext("my.sample.wav"))

    def test_empty_string(self):
        self.assertFalse(hasext(""))


# ===================================================================
# nonalpha / DESCRIPTIONS data integrity
# ===================================================================

class TestDataIntegrity(unittest.TestCase):
    """Verify consistency of nonalpha and DESCRIPTIONS dictionaries."""

    def test_nonalpha_keys_are_single_chars(self):
        for k in nonalpha:
            self.assertEqual(len(k), 1, msg=f"nonalpha key {k!r} is not single char")

    def test_nonalpha_values_are_nonempty_strings(self):
        for k, v in nonalpha.items():
            self.assertIsInstance(v, str)
            self.assertTrue(len(v) > 0, msg=f"nonalpha[{k!r}] is empty")

    def test_descriptions_keys_single_chars(self):
        for k in DESCRIPTIONS:
            self.assertEqual(len(k), 1, msg=f"DESCRIPTIONS key {k!r} is not single char")

    def test_descriptions_has_all_alpha(self):
        for ch in alpha:
            self.assertIn(ch, DESCRIPTIONS, msg=f"Missing lower {ch!r}")
            self.assertIn(ch.upper(), DESCRIPTIONS, msg=f"Missing upper {ch.upper()!r}")

    def test_descriptions_has_nonalpha_subset(self):
        # Not all nonalpha need descriptions but the common ones should
        for sym in "-=*/~^$#!+&@:":
            self.assertIn(sym, DESCRIPTIONS, msg=f"Missing DESCRIPTIONS for {sym!r}")

    def test_descriptions_values_nonempty(self):
        for k, v in DESCRIPTIONS.items():
            self.assertIsInstance(v, str)
            self.assertTrue(len(v) > 0, msg=f"DESCRIPTIONS[{k!r}] is empty")

    def test_nonalpha_contains_expected_symbols(self):
        expected = set("&*@^:$=!/#-%+?~\\1234")
        for sym in expected:
            self.assertIn(sym, nonalpha, msg=f"nonalpha missing {sym!r}")

    def test_alpha_constant(self):
        self.assertEqual(alpha, "abcdefghijklmnopqrstuvwxyz")
        self.assertEqual(len(alpha), 26)


# ===================================================================
# BufferManager — allocation internals
# ===================================================================

class TestBufferManagerAllocation(_TempDirMixin, unittest.TestCase):
    """Tests for buffer number allocation inside BufferManager."""

    def test_incr_nextbuf_simple(self):
        bm = self._make_bm()
        bm._nextbuf = 5
        bm._incr_nextbuf()
        self.assertEqual(bm._nextbuf, 6)

    def test_incr_nextbuf_wraps(self):
        bm = self._make_bm()
        bm._max_buffers = 10
        bm._nextbuf = 9
        bm._incr_nextbuf()
        self.assertEqual(bm._nextbuf, 1)

    def test_getNextBufnum_first(self):
        bm = self._make_bm()
        bm._nextbuf = 1
        n = bm._getNextBufnum()
        self.assertEqual(n, 1)
        self.assertEqual(bm._nextbuf, 2)

    def test_getNextBufnum_skips_occupied(self):
        bm = self._make_bm()
        bm._max_buffers = 5
        bm._buffers = [None] * 5
        bm._buffers[1] = Buffer("a.wav", 1)
        bm._buffers[2] = Buffer("b.wav", 2)
        bm._nextbuf = 1
        n = bm._getNextBufnum()
        self.assertEqual(n, 3)

    def test_getNextBufnum_wraps_around(self):
        bm = self._make_bm()
        bm._max_buffers = 5
        bm._buffers = [None] * 5
        bm._buffers[3] = Buffer("a.wav", 3)
        bm._buffers[4] = Buffer("b.wav", 4)
        bm._nextbuf = 3
        n = bm._getNextBufnum()
        self.assertEqual(n, 1)

    def test_getNextBufnum_full_raises(self):
        bm = self._make_bm()
        bm._max_buffers = 4
        bm._buffers = [None, Buffer("a.wav", 1), Buffer("b.wav", 2), Buffer("c.wav", 3)]
        bm._nextbuf = 1
        with self.assertRaises(RuntimeError) as ctx:
            bm._getNextBufnum()
        self.assertIn("Buffers full", str(ctx.exception))


# ===================================================================
# BufferManager — string / repr / getitem
# ===================================================================

class TestBufferManagerRepr(_TempDirMixin, unittest.TestCase):

    def test_repr(self):
        bm = self._make_bm()
        self.assertEqual(repr(bm), "<BufferManager>")

    def test_str_contains_descriptions(self):
        bm = self._make_bm()
        s = str(bm)
        # should contain at least some description entries
        self.assertIn("Gameboy hihat", s)
        self.assertIn("Bass drum", s)

    def test_getitem_with_string(self):
        bm = self._make_bm()
        # Patch symbolToDir so "x" maps to a non-existent dir
        with patch("FoxDot.lib.Buffers.symbolToDir") as mock_s2d:
            mock_s2d.return_value = join(self.wd, "x", "lower")
            result = bm["x"]
            self.assertEqual(int(result), 0)

    def test_getitem_with_tuple(self):
        bm = self._make_bm()
        with patch("FoxDot.lib.Buffers.symbolToDir") as mock_s2d:
            mock_s2d.return_value = join(self.wd, "x", "lower")
            result = bm[("x", 0)]
            self.assertEqual(int(result), 0)

    def test_getitem_whitespace_returns_nil(self):
        bm = self._make_bm()
        result = bm[" "]
        self.assertEqual(int(result), 0)


# ===================================================================
# BufferManager — path management
# ===================================================================

class TestBufferManagerPaths(_TempDirMixin, unittest.TestCase):

    def test_addPath(self):
        bm = self._make_bm(paths=[])
        self.assertEqual(len(bm._paths), 0)
        bm.addPath(self.wd)
        self.assertEqual(len(bm._paths), 1)

    def test_addPath_normalizes(self):
        bm = self._make_bm(paths=[])
        bm.addPath(self.wd)
        self.assertTrue(os.path.isabs(bm._paths[0]))

    def test_searchPaths_abspath(self):
        bm = self._make_bm()
        path = self._touch("sample.wav")
        found = bm._searchPaths(path)
        self.assertEqual(found, os.path.abspath(path))

    def test_searchPaths_relpath(self):
        bm = self._make_bm()
        self._touch("drum.wav")
        found = bm._searchPaths("drum.wav")
        self.assertIsNotNone(found)
        self.assertTrue(found.endswith("drum.wav"))

    def test_searchPaths_relpath_no_ext(self):
        bm = self._make_bm()
        self._touch("drum.wav")
        found = bm._searchPaths("drum")
        self.assertIsNotNone(found)

    def test_searchPaths_returns_none_for_missing(self):
        bm = self._make_bm()
        found = bm._searchPaths("nonexistent_sample")
        self.assertIsNone(found)

    def test_searchPaths_directory(self):
        bm = self._make_bm()
        self._mkdir("drums")
        found = bm._searchPaths("drums")
        self.assertIsNotNone(found)
        self.assertTrue(isdir(found))


# ===================================================================
# BufferManager — _getSoundFile / _getSoundFileOrDir
# ===================================================================

class TestBufferManagerFileSearch(_TempDirMixin, unittest.TestCase):

    def test_getSoundFile_with_ext(self):
        bm = self._make_bm()
        path = self._touch("a.wav")
        found = bm._getSoundFile(path)
        self.assertEqual(found, path)

    def test_getSoundFile_without_ext_finds_wav(self):
        bm = self._make_bm()
        path = self._touch("b.wav")
        base = path.replace(".wav", "")
        found = bm._getSoundFile(base)
        self.assertEqual(found, path)

    def test_getSoundFile_without_ext_finds_aif(self):
        bm = self._make_bm()
        path = self._touch("c.aif")
        base = path.replace(".aif", "")
        found = bm._getSoundFile(base)
        self.assertEqual(found, path)

    def test_getSoundFile_missing_returns_none(self):
        bm = self._make_bm()
        found = bm._getSoundFile(join(self.wd, "nope"))
        self.assertIsNone(found)

    def test_getSoundFile_wrong_ext_returns_none(self):
        bm = self._make_bm()
        self._touch("d.mp3")  # mp3 not in _ext
        found = bm._getSoundFile(join(self.wd, "d"))
        self.assertIsNone(found)

    def test_getSoundFileOrDir_file(self):
        bm = self._make_bm()
        path = self._touch("sample.wav")
        found = bm._getSoundFileOrDir(path)
        self.assertIsNotNone(found)
        self.assertTrue(os.path.isabs(found))

    def test_getSoundFileOrDir_dir(self):
        bm = self._make_bm()
        d = self._mkdir("mydir")
        found = bm._getSoundFileOrDir(d)
        self.assertEqual(found, os.path.abspath(d))

    def test_getSoundFileOrDir_none_for_missing(self):
        bm = self._make_bm()
        found = bm._getSoundFileOrDir(join(self.wd, "nofile"))
        self.assertIsNone(found)


# ===================================================================
# BufferManager — _getFileInDir
# ===================================================================

class TestGetFileInDir(_TempDirMixin, unittest.TestCase):

    def test_first_file(self):
        bm = self._make_bm()
        d = self._mkdir("snares")
        self._touch("snares", "a.wav")
        self._touch("snares", "b.wav")
        found = bm._getFileInDir(d, 0)
        self.assertTrue(found.endswith("a.wav"))

    def test_second_file(self):
        bm = self._make_bm()
        d = self._mkdir("snares")
        self._touch("snares", "a.wav")
        self._touch("snares", "b.wav")
        found = bm._getFileInDir(d, 1)
        self.assertTrue(found.endswith("b.wav"))

    def test_overflow_wraps(self):
        bm = self._make_bm()
        d = self._mkdir("snares")
        self._touch("snares", "a.wav")
        self._touch("snares", "b.wav")
        found = bm._getFileInDir(d, 2)
        self.assertTrue(found.endswith("a.wav"))

    def test_empty_dir_returns_none(self):
        bm = self._make_bm()
        d = self._mkdir("empty")
        found = bm._getFileInDir(d, 0)
        self.assertIsNone(found)

    def test_ignores_non_audio_files(self):
        bm = self._make_bm()
        d = self._mkdir("mixed")
        self._touch("mixed", "readme.txt")
        self._touch("mixed", "kick.wav")
        found = bm._getFileInDir(d, 0)
        self.assertTrue(found.endswith("kick.wav"))

    def test_sorted_order(self):
        bm = self._make_bm()
        d = self._mkdir("sorted")
        self._touch("sorted", "z.wav")
        self._touch("sorted", "a.wav")
        self._touch("sorted", "m.wav")
        found = bm._getFileInDir(d, 0)
        self.assertTrue(found.endswith("a.wav"))

    def test_flac_extension(self):
        bm = self._make_bm()
        d = self._mkdir("flacs")
        self._touch("flacs", "pad.flac")
        found = bm._getFileInDir(d, 0)
        self.assertTrue(found.endswith("pad.flac"))

    def test_upper_ext(self):
        bm = self._make_bm()
        d = self._mkdir("upper")
        self._touch("upper", "HIT.WAV")
        found = bm._getFileInDir(d, 0)
        self.assertTrue(found.endswith("HIT.WAV"))


# ===================================================================
# BufferManager — _patternSearch
# ===================================================================

class TestPatternSearch(_TempDirMixin, unittest.TestCase):

    def test_wildcard_filename(self):
        bm = self._make_bm()
        self._touch("drums", "kick01.wav")
        self._touch("drums", "kick02.wav")
        found = bm._patternSearch("drums/kick*", 0)
        self.assertIsNotNone(found)
        self.assertIn("kick01", found)

    def test_wildcard_second(self):
        bm = self._make_bm()
        self._touch("drums", "kick01.wav")
        self._touch("drums", "kick02.wav")
        found = bm._patternSearch("drums/kick*", 1)
        self.assertIn("kick02", found)

    def test_doublestar(self):
        bm = self._make_bm()
        self._touch("deep", "sub", "bass.wav")
        found = bm._patternSearch("**/bass*", 0)
        self.assertIsNotNone(found)
        self.assertIn("bass", found)

    def test_question_mark_wildcard(self):
        bm = self._make_bm()
        self._touch("hats", "hat1.wav")
        self._touch("hats", "hat2.wav")
        found = bm._patternSearch("hats/hat?", 0)
        self.assertIsNotNone(found)

    def test_pattern_no_match(self):
        bm = self._make_bm()
        found = bm._patternSearch("zzz*", 0)
        self.assertIsNone(found)

    def test_pattern_overflow_wraps(self):
        bm = self._make_bm()
        self._touch("perc", "snap.wav")
        found = bm._patternSearch("perc/*", 5)
        self.assertIsNotNone(found)
        self.assertIn("snap", found)

    def test_pattern_with_explicit_ext(self):
        bm = self._make_bm()
        self._touch("fx", "swoosh.wav")
        self._touch("fx", "swoosh.aif")
        found = bm._patternSearch("fx/swoosh.wav", 0)
        self.assertIsNotNone(found)
        self.assertIn("swoosh.wav", found)


# ===================================================================
# BufferManager — _allocateAndLoad / loadBuffer
# ===================================================================

class TestBufferManagerLoad(_TempDirMixin, unittest.TestCase):

    def test_allocateAndLoad_creates_buffer(self):
        bm = self._make_bm()
        path = self._touch("sample.wav", wav=True)
        buf = bm._allocateAndLoad(path)
        self.assertIsInstance(buf, Buffer)
        self.assertEqual(buf.fn, path)
        bm._server.bufferRead.assert_called_once_with(path, buf.bufnum)

    def test_allocateAndLoad_caches(self):
        bm = self._make_bm()
        path = self._touch("sample.wav", wav=True)
        buf1 = bm._allocateAndLoad(path)
        buf2 = bm._allocateAndLoad(path)
        self.assertIs(buf1, buf2)
        self.assertEqual(bm._server.bufferRead.call_count, 1)

    def test_allocateAndLoad_force_reloads(self):
        bm = self._make_bm()
        path = self._touch("sample.wav", wav=True)
        buf1 = bm._allocateAndLoad(path)
        buf2 = bm._allocateAndLoad(path, force=True)
        self.assertIs(buf1, buf2)
        self.assertEqual(bm._server.bufferRead.call_count, 2)

    def test_loadBuffer_returns_bufnum(self):
        bm = self._make_bm()
        self._touch("drum.wav", wav=True)
        n = bm.loadBuffer("drum.wav")
        self.assertIsInstance(n, int)
        self.assertGreater(n, 0)

    def test_loadBuffer_missing_returns_zero(self):
        bm = self._make_bm()
        n = bm.loadBuffer("nonexistent.wav")
        self.assertEqual(n, 0)

    def test_loadBuffer_stereo(self):
        bm = self._make_bm()
        path = self._touch("stereo.wav", wav=True, channels=2)
        n = bm.loadBuffer(path)
        buf = bm._buffers[n]
        self.assertEqual(buf.channels, 2)


# ===================================================================
# BufferManager — free / freeAll / reset
# ===================================================================

class TestBufferManagerFree(_TempDirMixin, unittest.TestCase):

    def test_free_by_bufnum(self):
        bm = self._make_bm()
        path = self._touch("kick.wav", wav=True)
        buf = bm._allocateAndLoad(path)
        bufnum = buf.bufnum
        bm.free(bufnum)
        self.assertIsNone(bm._buffers[bufnum])
        self.assertNotIn(path, bm._fn_to_buf)
        bm._server.bufferFree.assert_called_once_with(bufnum)

    def test_free_by_filename(self):
        bm = self._make_bm()
        path = self._touch("snare.wav", wav=True)
        buf = bm._allocateAndLoad(path)
        bufnum = buf.bufnum
        bm.free(path)
        self.assertIsNone(bm._buffers[bufnum])
        bm._server.bufferFree.assert_called_once_with(bufnum)

    def test_freeAll(self):
        bm = self._make_bm()
        p1 = self._touch("a.wav", wav=True)
        p2 = self._touch("b.wav", wav=True)
        bm._allocateAndLoad(p1)
        bm._allocateAndLoad(p2)
        bm.freeAll()
        self.assertEqual(len(bm._fn_to_buf), 0)
        self.assertEqual(bm._server.bufferFree.call_count, 2)

    def test_reset_reloads_buffers(self):
        bm = self._make_bm()
        p1 = self._touch("c.wav", wav=True)
        bm._allocateAndLoad(p1)
        bm._reset_buffers()
        # After reset, the file should be reloaded (bufferRead called again)
        self.assertEqual(bm._server.bufferRead.call_count, 2)

    def test_reset_method_delegates(self):
        bm = self._make_bm()
        p1 = self._touch("d.wav", wav=True)
        bm._allocateAndLoad(p1)
        bm.reset()
        self.assertEqual(bm._server.bufferRead.call_count, 2)


# ===================================================================
# BufferManager — setMaxBuffers
# ===================================================================

class TestBufferManagerMaxBuffers(_TempDirMixin, unittest.TestCase):

    def test_grow_buffers(self):
        bm = self._make_bm()
        bm._max_buffers = 10
        bm._buffers = [None] * 10
        bm.setMaxBuffers(20)
        self.assertEqual(bm._max_buffers, 20)
        self.assertEqual(len(bm._buffers), 20)

    def test_shrink_buffers_empty(self):
        bm = self._make_bm()
        bm._max_buffers = 20
        bm._buffers = [None] * 20
        bm._nextbuf = 5
        bm.setMaxBuffers(10)
        self.assertEqual(bm._max_buffers, 10)
        self.assertEqual(len(bm._buffers), 10)

    def test_shrink_buffers_occupied_raises(self):
        bm = self._make_bm()
        bm._max_buffers = 10
        bm._buffers = [None] * 10
        bm._buffers[8] = Buffer("x.wav", 8)
        with self.assertRaises(RuntimeError) as ctx:
            bm.setMaxBuffers(5)
        self.assertIn("Cannot shrink", str(ctx.exception))

    def test_same_size_noop(self):
        bm = self._make_bm()
        bm._max_buffers = 10
        bm._buffers = [None] * 10
        bm._nextbuf = 5
        bm.setMaxBuffers(10)
        self.assertEqual(bm._max_buffers, 10)

    def test_nextbuf_wraps_on_shrink(self):
        bm = self._make_bm()
        bm._max_buffers = 20
        bm._buffers = [None] * 20
        bm._nextbuf = 15
        bm.setMaxBuffers(10)
        self.assertEqual(bm._nextbuf, 15 % 10)


# ===================================================================
# BufferManager — getBufferFromSymbol / getBuffer
# ===================================================================

class TestBufferManagerSymbolAccess(_TempDirMixin, unittest.TestCase):

    def test_getBufferFromSymbol_whitespace_returns_nil(self):
        bm = self._make_bm()
        result = bm.getBufferFromSymbol(" ")
        self.assertEqual(int(result), 0)

    def test_getBufferFromSymbol_unknown_returns_nil(self):
        bm = self._make_bm()
        result = bm.getBufferFromSymbol("`")
        self.assertEqual(int(result), 0)

    def test_getBufferFromSymbol_no_files_returns_nil(self):
        bm = self._make_bm()
        # Patch symbolToDir to return a non-existent path
        with patch("FoxDot.lib.Buffers.symbolToDir") as mock_s2d:
            mock_s2d.return_value = join(self.wd, "x", "lower")
            result = bm.getBufferFromSymbol("x")
            self.assertEqual(int(result), 0)

    def test_getBufferFromSymbol_with_files(self):
        bm = self._make_bm()
        # Create the expected directory structure: x/lower/
        d = self._mkdir("x", "lower")
        self._touch("x", "lower", "kick.wav", wav=True)
        # Point symbolToDir to our temp root
        with patch("FoxDot.lib.Buffers.symbolToDir") as mock_s2d:
            mock_s2d.return_value = d
            result = bm.getBufferFromSymbol("x")
            self.assertIsInstance(result, Buffer)
            self.assertGreater(int(result), 0)

    def test_getBuffer_returns_buffer_at_index(self):
        bm = self._make_bm()
        b = Buffer("test.wav", 5)
        bm._buffers[5] = b
        self.assertIs(bm.getBuffer(5), b)

    def test_getBuffer_empty_returns_none(self):
        bm = self._make_bm()
        self.assertIsNone(bm.getBuffer(1))


# ===================================================================
# BufferManager — extended _findSample tests
# ===================================================================

class TestFindSampleExtended(_TempDirMixin, unittest.TestCase):

    def test_findSample_flac(self):
        bm = self._make_bm()
        self._touch("pad.flac")
        found = bm._findSample("pad.flac")
        self.assertIsNotNone(found)
        self.assertIn("pad.flac", found)

    def test_findSample_aiff(self):
        bm = self._make_bm()
        self._touch("bell.aiff")
        found = bm._findSample("bell.aiff")
        self.assertIsNotNone(found)

    def test_findSample_case_sensitive_ext(self):
        bm = self._make_bm()
        self._touch("HIT.WAV")
        # Without extension, should find .WAV via upper-case search
        found = bm._findSample("HIT")
        self.assertIsNotNone(found)

    def test_findSample_empty_dir_warns(self):
        bm = self._make_bm()
        self._mkdir("empty_dir")
        with patch("FoxDot.lib.Buffers.WarningMsg") as mock_warn:
            found = bm._findSample("empty_dir")
            self.assertIsNone(found)
            mock_warn.assert_called()

    def test_findSample_not_found_warns(self):
        bm = self._make_bm()
        with patch("FoxDot.lib.Buffers.WarningMsg") as mock_warn:
            found = bm._findSample("totally_nonexistent_xyz")
            self.assertIsNone(found)
            mock_warn.assert_called()


# ===================================================================
# Midi module tests
# ===================================================================

class TestMidiExceptions(unittest.TestCase):
    """Tests for MIDI exception classes."""

    def test_midi_device_not_found_str(self):
        from FoxDot.lib.Midi import MIDIDeviceNotFound
        e = MIDIDeviceNotFound()
        self.assertEqual(str(e), "MIDIDeviceNotFound Error")

    def test_rtmidi_not_found_str(self):
        from FoxDot.lib.Midi import rtMidiNotFound
        e = rtMidiNotFound()
        self.assertEqual(str(e), "rtMidiNotFound: Module 'rtmidi' not found")


class TestMidiInputHandler(unittest.TestCase):
    """Tests for MidiInputHandler callback logic."""

    TIMING_CLOCK_VALUE = 0xF8  # Standard MIDI timing clock byte

    @classmethod
    def setUpClass(cls):
        try:
            from FoxDot.lib.Midi import MidiInputHandler
            cls.MidiInputHandler = MidiInputHandler
            cls.available = True
        except ImportError:
            cls.available = False
        # Check if TIMING_CLOCK exists in module
        import FoxDot.lib.Midi as _midi_mod
        cls._midi_mod = _midi_mod
        cls._needs_patch = not hasattr(_midi_mod, "TIMING_CLOCK")

    def setUp(self):
        if not self.available:
            self.skipTest("MidiInputHandler not available (rtmidi not installed)")
        # Inject TIMING_CLOCK into the module if rtmidi is not installed
        if self._needs_patch:
            self._midi_mod.TIMING_CLOCK = self.TIMING_CLOCK_VALUE

    def tearDown(self):
        if self._needs_patch and hasattr(self._midi_mod, "TIMING_CLOCK"):
            del self._midi_mod.TIMING_CLOCK

    def _make_ctrl(self, ppqn=24):
        ctrl = MagicMock()
        ctrl.delta = 0.0
        ctrl.pulse = 0
        ctrl.ppqn = ppqn
        ctrl.bpm = 120.0
        return ctrl

    def test_handler_increments_pulse(self):
        ctrl = self._make_ctrl()
        handler = self.MidiInputHandler(ctrl)
        handler.played = False
        handler(([self.TIMING_CLOCK_VALUE], 0.01), None)
        self.assertEqual(ctrl.pulse, 1)

    def test_handler_accumulates_delta(self):
        ctrl = self._make_ctrl()
        handler = self.MidiInputHandler(ctrl)
        handler(([self.TIMING_CLOCK_VALUE], 0.025), None)
        self.assertEqual(ctrl.delta, 0.025)

    def test_handler_calculates_bpm_at_ppqn(self):
        ctrl = self._make_ctrl(ppqn=24)
        ctrl.pulse = 23  # one before ppqn
        ctrl.delta = 0.48  # accumulated over 23 pulses
        handler = self.MidiInputHandler(ctrl)
        handler.played = False
        # This pulse should trigger BPM calculation:
        # total delta = 0.48 + 0.02 = 0.50
        # BPM = 60.0 / 0.50 = 120.0
        handler(([self.TIMING_CLOCK_VALUE], 0.02), None)
        self.assertEqual(ctrl.bpm, 120.0)
        self.assertEqual(ctrl.pulse, 0)  # reset
        self.assertEqual(ctrl.delta, 0.0)  # reset

    def test_handler_skips_when_played(self):
        ctrl = self._make_ctrl()
        handler = self.MidiInputHandler(ctrl)
        handler.played = True
        handler(([self.TIMING_CLOCK_VALUE], 0.01), None)
        # pulse should not increment when played is True
        self.assertEqual(ctrl.pulse, 0)

    def test_handler_init(self):
        ctrl = self._make_ctrl()
        handler = self.MidiInputHandler(ctrl)
        self.assertIs(handler.midi_ctrl, ctrl)
        self.assertEqual(handler.bpm_group, [])
        self.assertFalse(handler.played)


class TestMidiOut(unittest.TestCase):
    """Tests for MidiOut class."""

    def test_midiout_is_synthdefproxy(self):
        from FoxDot.lib.Midi import MidiOut
        from FoxDot.lib.SCLang import SynthDefProxy
        self.assertTrue(issubclass(MidiOut, SynthDefProxy))

    def test_midi_alias(self):
        from FoxDot.lib.Midi import midi, MidiOut
        self.assertIs(midi, MidiOut)

    def test_midiin_set_clock(self):
        from FoxDot.lib.Midi import MidiIn
        mock_clock = MagicMock()
        MidiIn.set_clock(mock_clock)
        self.assertIs(MidiIn.metro, mock_clock)
        # cleanup
        MidiIn.metro = None


# ===================================================================
# Workspace/Format pure functions (import carefully)
# ===================================================================

class TestFormatFindComment(unittest.TestCase):
    """Tests for find_comment from Workspace.Format."""

    @classmethod
    def setUpClass(cls):
        # Import with careful handling of module dependencies
        try:
            from FoxDot.lib.Workspace.Format import find_comment
            cls.find_comment = staticmethod(find_comment)
            cls.available = True
        except Exception:
            cls.available = False

    def setUp(self):
        if not self.available:
            self.skipTest("Format module not importable (Tkinter dependency)")

    def test_simple_comment(self):
        self.assertEqual(self.find_comment("x = 1 # comment"), 6)

    def test_no_comment(self):
        self.assertIsNone(self.find_comment("x = 1"))

    def test_hash_in_string_ignored(self):
        self.assertIsNone(self.find_comment('x = "#not a comment"'))

    def test_hash_in_single_string_ignored(self):
        self.assertIsNone(self.find_comment("x = '#not a comment'"))

    def test_comment_after_string(self):
        result = self.find_comment('x = "hello" # real comment')
        self.assertEqual(result, 12)

    def test_only_comment(self):
        self.assertEqual(self.find_comment("# full line comment"), 0)

    def test_empty_line(self):
        self.assertIsNone(self.find_comment(""))


class TestFormatUserdefined(unittest.TestCase):
    """Tests for userdefined from Workspace.Format."""

    @classmethod
    def setUpClass(cls):
        try:
            from FoxDot.lib.Workspace.Format import userdefined
            cls.userdefined = staticmethod(userdefined)
            cls.available = True
        except Exception:
            cls.available = False

    def setUp(self):
        if not self.available:
            self.skipTest("Format module not importable")

    def test_simple_def(self):
        self.assertEqual(self.userdefined("def foo(x):"), "foo")

    def test_no_def(self):
        self.assertIsNone(self.userdefined("x = 1"))

    def test_def_with_underscores(self):
        self.assertEqual(self.userdefined("def my_func():"), "my_func")

    def test_class_not_matched(self):
        # userdefined only looks for 'def', not 'class'
        self.assertIsNone(self.userdefined("class MyClass:"))

    def test_indented_def(self):
        self.assertEqual(self.userdefined("    def inner():"), "inner")


class TestFormatReList(unittest.TestCase):
    """Tests for re_list bracket matching from Workspace.Format."""

    @classmethod
    def setUpClass(cls):
        try:
            from FoxDot.lib.Workspace.Format import re_list
            cls.re_list = staticmethod(re_list)
            cls.available = True
        except Exception:
            cls.available = False

    def setUp(self):
        if not self.available:
            self.skipTest("Format module not importable")

    def test_simple_list(self):
        result = self.re_list("[1,2,3]")
        self.assertEqual(result, "[1,2,3]")

    def test_nested_list(self):
        result = self.re_list("[1,[2,3],4]")
        self.assertEqual(result, "[1,[2,3],4]")

    def test_parens(self):
        result = self.re_list("(1,2)", br="()")
        self.assertEqual(result, "(1,2)")

    def test_no_brackets_returns_none(self):
        result = self.re_list("hello world")
        self.assertIsNone(result)


class TestFormatGetKeywords(unittest.TestCase):
    """Tests for get_keywords from Workspace.Format."""

    @classmethod
    def setUpClass(cls):
        try:
            from FoxDot.lib.Workspace.Format import get_keywords
            cls.get_keywords = staticmethod(get_keywords)
            cls.available = True
        except Exception:
            cls.available = False

    def setUp(self):
        if not self.available:
            self.skipTest("Format module not importable")

    def test_returns_list(self):
        result = self.get_keywords()
        self.assertIsInstance(result, list)

    def test_contains_python_keywords(self):
        result = self.get_keywords()
        for kw in ["if", "for", "def", "class", "while", "return"]:
            self.assertIn(kw, result, msg=f"Missing keyword: {kw}")

    def test_no_duplicates(self):
        result = self.get_keywords()
        self.assertEqual(len(result), len(set(result)))

    def test_nonempty(self):
        result = self.get_keywords()
        self.assertGreater(len(result), 50)  # should have many keywords


class TestFormatFindMultiline(unittest.TestCase):
    """Tests for find_multiline from Workspace.Format."""

    @classmethod
    def setUpClass(cls):
        try:
            from FoxDot.lib.Workspace.Format import find_multiline
            cls.find_multiline = staticmethod(find_multiline)
            cls.available = True
        except Exception:
            cls.available = False

    def setUp(self):
        if not self.available:
            self.skipTest("Format module not importable")

    def test_triple_double_quotes(self):
        text = 'x = """hello\nworld"""'
        result = self.find_multiline(text)
        self.assertEqual(len(result), 1)
        start, end = result[0]
        self.assertEqual(text[start:end], '"""hello\nworld"""')

    def test_triple_single_quotes(self):
        text = "x = '''hello\nworld'''"
        result = self.find_multiline(text)
        self.assertEqual(len(result), 1)

    def test_no_multiline(self):
        text = "x = 'hello'"
        result = self.find_multiline(text)
        self.assertEqual(len(result), 0)


# ===================================================================
# Patterns/Utils tests
# ===================================================================

class TestCalculateDelaysFromDur(unittest.TestCase):
    """Tests for CalculateDelaysFromDur."""

    def test_simple_durations(self):
        from FoxDot.lib.Patterns.Utils import CalculateDelaysFromDur
        from FoxDot.lib.Patterns import Pattern
        durs, dels = CalculateDelaysFromDur([1, 0.5, 0.25])
        self.assertEqual(list(durs), [1, 0.5, 0.25])
        self.assertEqual(list(dels), [0, 0, 0])

    def test_tuple_durations(self):
        from FoxDot.lib.Patterns.Utils import CalculateDelaysFromDur
        from FoxDot.lib.Patterns import PGroup
        durs, dels = CalculateDelaysFromDur([(0, 0.5)])
        # min of (0, 0.5) is 0, delays are offset - min
        self.assertEqual(float(durs[0]), 0.0)

    def test_single_element_tuple(self):
        from FoxDot.lib.Patterns.Utils import CalculateDelaysFromDur
        durs, dels = CalculateDelaysFromDur([(1,)])
        self.assertEqual(float(durs[0]), 1.0)
        self.assertEqual(float(dels[0]), 0)

    def test_empty_input(self):
        from FoxDot.lib.Patterns.Utils import CalculateDelaysFromDur
        durs, dels = CalculateDelaysFromDur([])
        self.assertEqual(len(durs), 0)
        self.assertEqual(len(dels), 0)


if __name__ == "__main__":
    unittest.main()
