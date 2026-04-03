"""
Unit tests for OSC3 module — encoding, decoding, OSCMessage, OSCBundle, and utility functions.
"""

import struct
import math
import unittest

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from FoxDot.lib.OSC3 import (
    OSCString,
    OSCBlob,
    OSCArgument,
    OSCTimeTag,
    _readString,
    _readBlob,
    _readInt,
    _readLong,
    _readTimeTag,
    _readFloat,
    _readDouble,
    decodeOSC,
    getFilterStr,
    getRegEx,
    NTP_epoch,
    NTP_units_per_second,
    OSCMessage,
    OSCBundle,
    OSCError,
)


# ---------------------------------------------------------------------------
# Encoding functions
# ---------------------------------------------------------------------------

class TestOSCString(unittest.TestCase):
    """Tests for OSCString() — string to zero-padded OSC binary."""

    def test_empty_string(self):
        result = OSCString("")
        # Empty string + null terminator = 1 byte, padded to 4
        self.assertEqual(len(result) % 4, 0)
        self.assertEqual(result, b"\x00\x00\x00\x00")

    def test_short_string(self):
        result = OSCString("hi")
        # "hi" = 2 bytes + null = 3, padded to 4
        self.assertEqual(len(result) % 4, 0)
        self.assertTrue(result.startswith(b"hi\x00"))

    def test_four_char_string(self):
        result = OSCString("test")
        # "test" = 4 bytes + null = 5, padded to 8
        self.assertEqual(len(result), 8)
        self.assertTrue(result.startswith(b"test\x00"))

    def test_padding_always_multiple_of_four(self):
        for length in range(0, 20):
            s = "x" * length
            result = OSCString(s)
            self.assertEqual(len(result) % 4, 0,
                             f"OSCString of length {length} not padded to 4")

    def test_unicode_string(self):
        result = OSCString("café")
        self.assertEqual(len(result) % 4, 0)
        # Should contain the UTF-8 encoding
        self.assertIn("café".encode("utf-8"), result)

    def test_osc_address_string(self):
        result = OSCString("/synth/play")
        self.assertEqual(len(result) % 4, 0)
        self.assertTrue(result.startswith(b"/synth/play\x00"))


class TestOSCBlob(unittest.TestCase):
    """Tests for OSCBlob() — binary blob encoding."""

    def test_bytes_blob(self):
        data = b"\x01\x02\x03\x04"
        result = OSCBlob(data)
        # Size prefix (4 bytes) + data padded to multiple of 4
        self.assertIsInstance(result, bytes)
        size = struct.unpack(">i", result[:4])[0]
        self.assertEqual(size, 4)

    def test_empty_bytes_blob(self):
        result = OSCBlob(b"")
        size = struct.unpack(">i", result[:4])[0]
        self.assertEqual(size, 0)

    def test_non_bytes_returns_empty(self):
        result = OSCBlob(12345)
        self.assertEqual(result, "")

    def test_blob_padding(self):
        for length in range(1, 16):
            data = b"x" * length
            result = OSCBlob(data)
            # Total should be 4 (size int) + padded data
            padded_len = int(math.ceil(length / 4.0) * 4)
            self.assertEqual(len(result), 4 + padded_len)


class TestOSCArgument(unittest.TestCase):
    """Tests for OSCArgument() — type detection and encoding."""

    def test_int_auto(self):
        tag, binary = OSCArgument(42)
        self.assertEqual(tag, "i")
        self.assertEqual(struct.unpack(">i", binary)[0], 42)

    def test_float_auto(self):
        tag, binary = OSCArgument(3.14)
        self.assertEqual(tag, "f")
        value = struct.unpack(">f", binary)[0]
        self.assertAlmostEqual(value, 3.14, places=5)

    def test_string_auto(self):
        tag, binary = OSCArgument("hello")
        self.assertEqual(tag, "s")
        self.assertIn(b"hello", binary)

    def test_int_hint(self):
        tag, binary = OSCArgument(42, typehint="i")
        self.assertEqual(tag, "i")
        self.assertEqual(struct.unpack(">i", binary)[0], 42)

    def test_float_hint(self):
        tag, binary = OSCArgument(3.14, typehint="f")
        self.assertEqual(tag, "f")

    def test_double_hint(self):
        tag, binary = OSCArgument(3.14, typehint="d")
        self.assertEqual(tag, "d")
        value = struct.unpack(">d", binary)[0]
        self.assertAlmostEqual(value, 3.14, places=10)

    def test_string_fallback_on_invalid_int(self):
        tag, binary = OSCArgument("notanumber", typehint="i")
        self.assertEqual(tag, "s")

    def test_string_fallback_on_invalid_float(self):
        tag, binary = OSCArgument("notafloat", typehint="f")
        self.assertEqual(tag, "s")

    def test_string_fallback_on_invalid_double(self):
        tag, binary = OSCArgument("notadouble", typehint="d")
        self.assertEqual(tag, "s")

    def test_unknown_typehint(self):
        tag, binary = OSCArgument("value", typehint="z")
        self.assertEqual(tag, "s")

    def test_negative_int(self):
        tag, binary = OSCArgument(-100)
        self.assertEqual(tag, "i")
        self.assertEqual(struct.unpack(">i", binary)[0], -100)

    def test_zero_int(self):
        tag, binary = OSCArgument(0)
        self.assertEqual(tag, "i")
        self.assertEqual(struct.unpack(">i", binary)[0], 0)

    def test_zero_float(self):
        tag, binary = OSCArgument(0.0)
        self.assertEqual(tag, "f")
        self.assertAlmostEqual(struct.unpack(">f", binary)[0], 0.0)


class TestOSCTimeTag(unittest.TestCase):
    """Tests for OSCTimeTag() — time to NTP binary."""

    def test_zero_time(self):
        result = OSCTimeTag(0)
        self.assertEqual(len(result), 8)
        high, low = struct.unpack(">LL", result)
        self.assertEqual(high, 0)
        self.assertEqual(low, 1)

    def test_negative_time(self):
        result = OSCTimeTag(-1)
        high, low = struct.unpack(">LL", result)
        self.assertEqual(high, 0)
        self.assertEqual(low, 1)

    def test_positive_time(self):
        result = OSCTimeTag(1000000000.5)
        self.assertEqual(len(result), 8)
        high, low = struct.unpack(">LL", result)
        self.assertGreater(high, 0)
        self.assertGreater(low, 0)

    def test_timetag_always_8_bytes(self):
        for t in [0, 0.5, 1.0, 1000000000.0]:
            result = OSCTimeTag(t)
            self.assertEqual(len(result), 8)


# ---------------------------------------------------------------------------
# Decoding functions
# ---------------------------------------------------------------------------

class TestReadString(unittest.TestCase):
    """Tests for _readString() — read null-terminated string from binary."""

    def test_simple_string(self):
        data = b"hello\x00\x00\x00"
        s, rest = _readString(data)
        self.assertEqual(s, "hello")
        self.assertEqual(rest, b"")

    def test_string_with_trailing_data(self):
        data = b"hi\x00\x00" + b"extra"
        s, rest = _readString(data)
        self.assertEqual(s, "hi")
        self.assertEqual(rest, b"extra")

    def test_empty_string(self):
        data = b"\x00\x00\x00\x00"
        s, rest = _readString(data)
        self.assertEqual(s, "")

    def test_four_byte_string(self):
        data = b"test\x00\x00\x00\x00"
        s, rest = _readString(data)
        self.assertEqual(s, "test")

    def test_osc_address(self):
        data = b"/foo\x00\x00\x00\x00"
        s, rest = _readString(data)
        self.assertEqual(s, "/foo")


class TestReadBlob(unittest.TestCase):
    """Tests for _readBlob() — read length-prefixed blob from binary."""

    def test_simple_blob(self):
        # 4-byte blob: size=4, then 4 bytes of data
        data = struct.pack(">i", 4) + b"\x01\x02\x03\x04"
        blob, rest = _readBlob(data)
        self.assertEqual(blob, b"\x01\x02\x03\x04")
        self.assertEqual(rest, b"")

    def test_blob_with_trailing(self):
        data = struct.pack(">i", 2) + b"\x01\x02\x00\x00" + b"more"
        blob, rest = _readBlob(data)
        self.assertEqual(blob, b"\x01\x02")
        self.assertEqual(rest, b"more")


class TestReadInt(unittest.TestCase):
    """Tests for _readInt() — read 32-bit big-endian int."""

    def test_positive_int(self):
        data = struct.pack(">i", 42)
        value, rest = _readInt(data)
        self.assertEqual(value, 42)
        self.assertEqual(rest, b"")

    def test_negative_int(self):
        data = struct.pack(">i", -100)
        value, rest = _readInt(data)
        self.assertEqual(value, -100)

    def test_zero(self):
        data = struct.pack(">i", 0)
        value, rest = _readInt(data)
        self.assertEqual(value, 0)

    def test_with_trailing_data(self):
        data = struct.pack(">i", 7) + b"tail"
        value, rest = _readInt(data)
        self.assertEqual(value, 7)
        self.assertEqual(rest, b"tail")

    def test_too_short(self):
        data = b"\x00\x01"
        value, rest = _readInt(data)
        self.assertEqual(value, 0)


class TestReadLong(unittest.TestCase):
    """Tests for _readLong() — read 64-bit big-endian signed integer."""

    def test_positive_long(self):
        data = struct.pack(">ll", 0, 42)
        value, rest = _readLong(data)
        self.assertEqual(value, 42)
        self.assertEqual(rest, b"")

    def test_large_long(self):
        data = struct.pack(">ll", 1, 0)
        value, rest = _readLong(data)
        self.assertEqual(value, (1 << 32))

    def test_with_trailing(self):
        data = struct.pack(">ll", 0, 5) + b"abc"
        value, rest = _readLong(data)
        self.assertEqual(value, 5)
        self.assertEqual(rest, b"abc")


class TestReadTimeTag(unittest.TestCase):
    """Tests for _readTimeTag() — read NTP timetag from binary."""

    def test_immediate(self):
        data = struct.pack(">LL", 0, 1)
        t, rest = _readTimeTag(data)
        self.assertEqual(t, 0.0)

    def test_zero_zero(self):
        data = struct.pack(">LL", 0, 0)
        t, rest = _readTimeTag(data)
        self.assertEqual(t, 0.0)

    def test_nonzero_timetag(self):
        secs = 1000000000 - NTP_epoch
        fract = int(0.5 * NTP_units_per_second)
        data = struct.pack(">LL", secs, fract)
        t, rest = _readTimeTag(data)
        self.assertAlmostEqual(t, 1000000000.5, places=2)

    def test_trailing_data(self):
        data = struct.pack(">LL", 0, 1) + b"more"
        t, rest = _readTimeTag(data)
        self.assertEqual(t, 0.0)
        self.assertEqual(rest, b"more")


class TestReadFloat(unittest.TestCase):
    """Tests for _readFloat() — read 32-bit big-endian float."""

    def test_positive_float(self):
        data = struct.pack(">f", 3.14)
        value, rest = _readFloat(data)
        self.assertAlmostEqual(value, 3.14, places=5)
        self.assertEqual(rest, b"")

    def test_zero_float(self):
        data = struct.pack(">f", 0.0)
        value, rest = _readFloat(data)
        self.assertEqual(value, 0.0)

    def test_negative_float(self):
        data = struct.pack(">f", -2.5)
        value, rest = _readFloat(data)
        self.assertAlmostEqual(value, -2.5, places=5)

    def test_too_short(self):
        data = b"\x00"
        value, rest = _readFloat(data)
        self.assertEqual(value, 0)

    def test_with_trailing(self):
        data = struct.pack(">f", 1.0) + b"tail"
        value, rest = _readFloat(data)
        self.assertAlmostEqual(value, 1.0, places=5)
        self.assertEqual(rest, b"tail")


class TestReadDouble(unittest.TestCase):
    """Tests for _readDouble() — read 64-bit big-endian double."""

    def test_positive_double(self):
        data = struct.pack(">d", 3.141592653589793)
        value, rest = _readDouble(data)
        self.assertAlmostEqual(value, 3.141592653589793, places=12)
        self.assertEqual(rest, b"")

    def test_zero_double(self):
        data = struct.pack(">d", 0.0)
        value, rest = _readDouble(data)
        self.assertEqual(value, 0.0)

    def test_negative_double(self):
        data = struct.pack(">d", -99.99)
        value, rest = _readDouble(data)
        self.assertAlmostEqual(value, -99.99, places=10)

    def test_too_short(self):
        data = b"\x00\x01\x02"
        value, rest = _readDouble(data)
        self.assertEqual(value, 0)


# ---------------------------------------------------------------------------
# Roundtrip encode/decode
# ---------------------------------------------------------------------------

class TestEncodeDecodeRoundtrip(unittest.TestCase):
    """Verify that encoding then decoding produces the original values."""

    def test_string_roundtrip(self):
        encoded = OSCString("hello")
        s, rest = _readString(encoded)
        self.assertEqual(s, "hello")

    def test_int_roundtrip(self):
        tag, binary = OSCArgument(42)
        value, rest = _readInt(binary)
        self.assertEqual(value, 42)

    def test_float_roundtrip(self):
        tag, binary = OSCArgument(3.14)
        value, rest = _readFloat(binary)
        self.assertAlmostEqual(value, 3.14, places=5)

    def test_double_roundtrip(self):
        tag, binary = OSCArgument(3.14, typehint="d")
        value, rest = _readDouble(binary)
        self.assertAlmostEqual(value, 3.14, places=10)


# ---------------------------------------------------------------------------
# decodeOSC
# ---------------------------------------------------------------------------

class TestDecodeOSC(unittest.TestCase):
    """Tests for decodeOSC() — full message decoding."""

    def test_decode_simple_message(self):
        msg = OSCMessage("/test")
        msg.append(42)
        msg.append(3.14)
        msg.append("hello")
        decoded = decodeOSC(msg.getBinary())
        self.assertEqual(decoded[0], "/test")
        self.assertEqual(decoded[1], ",ifs")
        self.assertEqual(decoded[2], 42)
        self.assertAlmostEqual(decoded[3], 3.14, places=5)
        self.assertEqual(decoded[4], "hello")

    def test_decode_int_only(self):
        msg = OSCMessage("/int")
        msg.append(99)
        decoded = decodeOSC(msg.getBinary())
        self.assertEqual(decoded[0], "/int")
        self.assertEqual(decoded[2], 99)

    def test_decode_float_only(self):
        msg = OSCMessage("/float")
        msg.append(2.5)
        decoded = decodeOSC(msg.getBinary())
        self.assertEqual(decoded[0], "/float")
        self.assertAlmostEqual(decoded[2], 2.5, places=5)

    def test_decode_empty_message(self):
        msg = OSCMessage("/empty")
        decoded = decodeOSC(msg.getBinary())
        self.assertEqual(decoded[0], "/empty")
        self.assertEqual(decoded[1], ",")

    def test_decode_bundle(self):
        bundle = OSCBundle("/addr", time=0)
        bundle.append(OSCMessage("/sub1"))
        binary = bundle.getBinary()
        decoded = decodeOSC(binary)
        self.assertEqual(decoded[0], "#bundle")

    def test_decode_multiple_ints(self):
        msg = OSCMessage("/multi")
        for i in range(5):
            msg.append(i)
        decoded = decodeOSC(msg.getBinary())
        self.assertEqual(decoded[0], "/multi")
        for i in range(5):
            self.assertEqual(decoded[i + 2], i)

    def test_typetag_string_lacks_comma(self):
        # Manually construct a bad message: address + typetags without comma
        address = OSCString("/bad")
        typetags = OSCString("ifs")  # missing comma
        data = address + typetags
        with self.assertRaises(OSCError):
            decodeOSC(data)


# ---------------------------------------------------------------------------
# OSCMessage class
# ---------------------------------------------------------------------------

class TestOSCMessage(unittest.TestCase):
    """Tests for the OSCMessage container class."""

    def test_create_empty(self):
        msg = OSCMessage("/test")
        self.assertEqual(msg.address, "/test")
        self.assertEqual(len(msg), 0)

    def test_append_int(self):
        msg = OSCMessage("/test")
        msg.append(42)
        self.assertEqual(len(msg), 1)
        self.assertEqual(list(msg.values()), [42])

    def test_append_float(self):
        msg = OSCMessage("/test")
        msg.append(3.14)
        self.assertEqual(len(msg), 1)
        values = list(msg.values())
        self.assertAlmostEqual(values[0], 3.14, places=5)

    def test_append_string(self):
        msg = OSCMessage("/test")
        msg.append("hello")
        self.assertEqual(len(msg), 1)
        self.assertEqual(list(msg.values()), ["hello"])

    def test_append_multiple(self):
        msg = OSCMessage("/test")
        msg.append(1)
        msg.append(2.0)
        msg.append("three")
        self.assertEqual(len(msg), 3)

    def test_append_list(self):
        msg = OSCMessage("/test")
        msg.append([1, 2, 3])
        self.assertEqual(len(msg), 3)

    def test_tags(self):
        msg = OSCMessage("/test")
        msg.append(1)
        msg.append(2.0)
        msg.append("hi")
        self.assertEqual(msg.tags(), ["i", "f", "s"])

    def test_items(self):
        msg = OSCMessage("/test")
        msg.append(42)
        msg.append("world")
        items = msg.items()
        self.assertEqual(items[0], ("i", 42))
        self.assertEqual(items[1][0], "s")
        self.assertEqual(items[1][1], "world")

    def test_getitem(self):
        msg = OSCMessage("/test")
        msg.append(10)
        msg.append(20)
        msg.append(30)
        self.assertEqual(msg[0], 10)
        self.assertEqual(msg[1], 20)
        self.assertEqual(msg[2], 30)

    def test_getitem_slice(self):
        msg = OSCMessage("/test")
        msg.append(10)
        msg.append(20)
        msg.append(30)
        self.assertEqual(msg[0:2], [10, 20])

    def test_delitem(self):
        msg = OSCMessage("/test")
        msg.append(10)
        msg.append(20)
        msg.append(30)
        del msg[1]
        self.assertEqual(len(msg), 2)
        self.assertEqual(list(msg.values()), [10, 30])

    def test_setitem(self):
        msg = OSCMessage("/test")
        msg.append(10)
        msg.append(20)
        msg[0] = 99
        self.assertEqual(msg[0], 99)

    def test_contains(self):
        msg = OSCMessage("/test")
        msg.append(42)
        msg.append("hello")
        self.assertIn(42, msg)
        self.assertIn("hello", msg)
        self.assertNotIn(999, msg)

    def test_iter(self):
        msg = OSCMessage("/test")
        msg.append(1)
        msg.append(2)
        msg.append(3)
        self.assertEqual(list(msg), [1, 2, 3])

    def test_reversed(self):
        msg = OSCMessage("/test")
        msg.append(1)
        msg.append(2)
        msg.append(3)
        self.assertEqual(list(reversed(msg)), [3, 2, 1])

    def test_eq(self):
        msg1 = OSCMessage("/test")
        msg1.append(42)
        msg2 = OSCMessage("/test")
        msg2.append(42)
        self.assertEqual(msg1, msg2)

    def test_ne(self):
        msg1 = OSCMessage("/a")
        msg1.append(1)
        msg2 = OSCMessage("/b")
        msg2.append(1)
        self.assertNotEqual(msg1, msg2)

    def test_ne_different_data(self):
        msg1 = OSCMessage("/test")
        msg1.append(1)
        msg2 = OSCMessage("/test")
        msg2.append(2)
        self.assertNotEqual(msg1, msg2)

    def test_eq_not_oscmessage(self):
        msg = OSCMessage("/test")
        self.assertNotEqual(msg, "not an OSCMessage")

    def test_copy(self):
        msg = OSCMessage("/test")
        msg.append(42)
        copy = msg.copy()
        self.assertEqual(msg, copy)
        copy.append(99)
        self.assertNotEqual(msg, copy)

    def test_count(self):
        msg = OSCMessage("/test")
        msg.append(1)
        msg.append(2)
        msg.append(1)
        self.assertEqual(msg.count(1), 2)
        self.assertEqual(msg.count(2), 1)
        self.assertEqual(msg.count(3), 0)

    def test_index(self):
        msg = OSCMessage("/test")
        msg.append(10)
        msg.append(20)
        msg.append(30)
        self.assertEqual(msg.index(20), 1)

    def test_index_not_found(self):
        msg = OSCMessage("/test")
        msg.append(10)
        with self.assertRaises(ValueError):
            msg.index(999)

    def test_extend(self):
        msg = OSCMessage("/test")
        msg.append(1)
        msg.extend([2, 3])
        self.assertEqual(len(msg), 3)
        self.assertEqual(list(msg.values()), [1, 2, 3])

    def test_insert(self):
        msg = OSCMessage("/test")
        msg.append(1)
        msg.append(3)
        msg.insert(1, 2)
        self.assertEqual(list(msg.values()), [1, 2, 3])

    def test_pop(self):
        msg = OSCMessage("/test")
        msg.append(10)
        msg.append(20)
        msg.append(30)
        val = msg.pop(1)
        self.assertEqual(val, 20)
        self.assertEqual(len(msg), 2)

    def test_popitem(self):
        msg = OSCMessage("/test")
        msg.append(42)
        tag, val = msg.popitem(0)
        self.assertEqual(tag, "i")
        self.assertEqual(val, 42)

    def test_reverse(self):
        msg = OSCMessage("/test")
        msg.append(1)
        msg.append(2)
        msg.append(3)
        msg.reverse()
        self.assertEqual(list(msg.values()), [3, 2, 1])

    def test_remove(self):
        msg = OSCMessage("/test")
        msg.append(10)
        msg.append(20)
        msg.append(30)
        msg.remove(20)
        self.assertEqual(list(msg.values()), [10, 30])

    def test_remove_not_found(self):
        msg = OSCMessage("/test")
        msg.append(10)
        with self.assertRaises(ValueError):
            msg.remove(999)

    def test_add_returns_new(self):
        msg1 = OSCMessage("/test")
        msg1.append(1)
        msg2 = msg1 + [2, 3]
        self.assertEqual(len(msg2), 3)
        self.assertEqual(len(msg1), 1)

    def test_iadd(self):
        msg = OSCMessage("/test")
        msg.append(1)
        msg += [2, 3]
        self.assertEqual(len(msg), 3)

    def test_radd_list(self):
        msg = OSCMessage("/test")
        msg.append(2)
        result = [1] + msg
        self.assertEqual(result, [1, 2])

    def test_radd_tuple(self):
        msg = OSCMessage("/test")
        msg.append(2)
        result = (1,) + msg
        self.assertIsInstance(result, tuple)
        self.assertEqual(result, (1, 2))

    def test_str(self):
        msg = OSCMessage("/test")
        msg.append(42)
        s = str(msg)
        self.assertIn("/test", s)
        self.assertIn("42", s)

    def test_clear(self):
        msg = OSCMessage("/test")
        msg.append(1)
        msg.append(2)
        msg.clear("/new")
        self.assertEqual(msg.address, "/new")
        self.assertEqual(len(msg), 0)

    def test_clearData(self):
        msg = OSCMessage("/test")
        msg.append(1)
        msg.clearData()
        self.assertEqual(len(msg), 0)
        self.assertEqual(msg.address, "/test")

    def test_setAddress(self):
        msg = OSCMessage("/old")
        msg.setAddress("/new")
        self.assertEqual(msg.address, "/new")

    def test_getBinary_returns_bytes(self):
        msg = OSCMessage("/test")
        msg.append(42)
        binary = msg.getBinary()
        self.assertIsInstance(binary, bytes)

    def test_append_dict(self):
        msg = OSCMessage("/test")
        msg.append({"key": "value"})
        self.assertGreater(len(msg), 0)

    def test_append_oscmessage_raises(self):
        msg = OSCMessage("/test")
        other = OSCMessage("/other")
        with self.assertRaises(TypeError):
            msg.append(other)

    def test_setItem(self):
        msg = OSCMessage("/test")
        msg.append(10)
        msg.setItem(0, 20, typehint="i")
        self.assertEqual(msg[0], 20)

    def test_setitem_slice(self):
        msg = OSCMessage("/test")
        msg.append(1)
        msg.append(2)
        msg.append(3)
        msg[0:2] = [10, 20]
        vals = list(msg.values())
        self.assertEqual(vals[0], 10)
        self.assertEqual(vals[1], 20)

    def test_itervalues(self):
        msg = OSCMessage("/test")
        msg.append(1)
        msg.append(2)
        self.assertEqual(list(msg.itervalues()), [1, 2])

    def test_iteritems(self):
        msg = OSCMessage("/test")
        msg.append(42)
        items = list(msg.iteritems())
        self.assertEqual(items[0], ("i", 42))

    def test_itertags(self):
        msg = OSCMessage("/test")
        msg.append(1)
        msg.append(2.0)
        tags = list(msg.itertags())
        self.assertEqual(tags, ["i", "f"])

    def test_append_tuple(self):
        msg = OSCMessage("/test")
        msg.append((1, 2, 3))
        self.assertEqual(len(msg), 3)

    def test_repr(self):
        msg = OSCMessage("/test")
        msg.append(42)
        r = repr(msg)
        self.assertIn("/test", r)


# ---------------------------------------------------------------------------
# OSCBundle class
# ---------------------------------------------------------------------------

class TestOSCBundle(unittest.TestCase):
    """Tests for the OSCBundle class."""

    def test_create_empty(self):
        bundle = OSCBundle("/default")
        self.assertEqual(len(bundle), 0)

    def test_append_oscmessage(self):
        bundle = OSCBundle("/default")
        msg = OSCMessage("/sub")
        msg.append(42)
        bundle.append(msg)
        self.assertEqual(len(bundle), 1)

    def test_append_value(self):
        bundle = OSCBundle("/default")
        bundle.append(42)
        self.assertEqual(len(bundle), 1)

    def test_append_dict(self):
        bundle = OSCBundle("/default")
        bundle.append({"addr": "/custom", "args": 42})
        self.assertEqual(len(bundle), 1)

    def test_setTimeTag(self):
        bundle = OSCBundle("/default")
        bundle.setTimeTag(100.0)
        self.assertEqual(bundle.timetag, 100.0)

    def test_setTimeTag_negative_ignored(self):
        bundle = OSCBundle("/default", time=50.0)
        bundle.setTimeTag(-1)
        self.assertEqual(bundle.timetag, 50.0)

    def test_getTimeTagStr(self):
        bundle = OSCBundle("/default", time=1000000000.5)
        s = bundle.getTimeTagStr()
        self.assertIsInstance(s, str)
        self.assertGreater(len(s), 0)

    def test_getBinary(self):
        bundle = OSCBundle("/default")
        msg = OSCMessage("/sub")
        msg.append(1)
        bundle.append(msg)
        binary = bundle.getBinary()
        self.assertIsInstance(binary, bytes)
        self.assertTrue(binary.startswith(b"#bundle\x00"))

    def test_str_no_timetag(self):
        bundle = OSCBundle("/default", time=0)
        s = str(bundle)
        self.assertTrue(s.startswith("#bundle ["))

    def test_str_with_timetag(self):
        bundle = OSCBundle("/default", time=1000000000.0)
        s = str(bundle)
        self.assertIn("#bundle (", s)

    def test_eq(self):
        b1 = OSCBundle("/default", time=0)
        b2 = OSCBundle("/default", time=0)
        msg = OSCMessage("/sub")
        msg.append(42)
        b1.append(msg)
        b2.append(msg)
        self.assertEqual(b1, b2)

    def test_ne(self):
        b1 = OSCBundle("/default", time=0)
        b2 = OSCBundle("/default", time=1)
        self.assertNotEqual(b1, b2)

    def test_eq_not_bundle(self):
        b = OSCBundle("/default")
        self.assertNotEqual(b, "not a bundle")

    def test_copy(self):
        bundle = OSCBundle("/default", time=42.0)
        msg = OSCMessage("/sub")
        msg.append(1)
        bundle.append(msg)
        copy = bundle.copy()
        self.assertEqual(bundle, copy)
        self.assertEqual(copy.timetag, 42.0)

    def test_values_returns_oscmessages(self):
        bundle = OSCBundle("/default")
        msg = OSCMessage("/sub")
        msg.append(99)
        bundle.append(msg)
        values = bundle.values()
        self.assertEqual(len(values), 1)
        self.assertIsInstance(values[0], OSCMessage)

    def test_nested_bundle(self):
        inner = OSCBundle("/inner", time=0)
        inner_msg = OSCMessage("/inner/msg")
        inner_msg.append(42)
        inner.append(inner_msg)

        outer = OSCBundle("/outer", time=0)
        outer.append(inner)
        binary = outer.getBinary()
        decoded = decodeOSC(binary)
        self.assertEqual(decoded[0], "#bundle")

    def test_multiple_messages(self):
        bundle = OSCBundle("/default")
        for i in range(3):
            msg = OSCMessage(f"/sub{i}")
            msg.append(i)
            bundle.append(msg)
        self.assertEqual(len(bundle), 3)
        values = bundle.values()
        self.assertEqual(len(values), 3)


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

class TestGetFilterStr(unittest.TestCase):
    """Tests for getFilterStr()."""

    def test_empty_filters(self):
        self.assertEqual(getFilterStr({}), [])

    def test_all_pass(self):
        result = getFilterStr({"/*": True})
        self.assertIn("+/*", result)

    def test_all_block(self):
        result = getFilterStr({"/*": False})
        self.assertIn("-/*", result)

    def test_specific_filter(self):
        result = getFilterStr({"/foo": True, "/bar": False})
        self.assertTrue(any("+/foo" in s for s in result))
        self.assertTrue(any("-/bar" in s for s in result))

    def test_mixed_with_wildcard(self):
        result = getFilterStr({"/*": True, "/specific": False})
        self.assertIn("+/*", result)
        self.assertTrue(any("-/specific" in s for s in result))


class TestGetRegEx(unittest.TestCase):
    """Tests for getRegEx() — OSC address pattern to regex."""

    def test_literal_address(self):
        regex = getRegEx("/foo/bar")
        self.assertIsNotNone(regex.match("/foo/bar"))
        self.assertIsNone(regex.match("/foo/baz"))

    def test_wildcard_star(self):
        regex = getRegEx("/foo/*")
        self.assertIsNotNone(regex.match("/foo/bar"))
        self.assertIsNotNone(regex.match("/foo/anything"))

    def test_wildcard_question(self):
        regex = getRegEx("/foo/ba?")
        self.assertIsNotNone(regex.match("/foo/bar"))
        self.assertIsNotNone(regex.match("/foo/baz"))
        self.assertIsNone(regex.match("/foo/ba"))

    def test_braces_alternation(self):
        regex = getRegEx("/foo/{bar,baz}")
        self.assertIsNotNone(regex.match("/foo/bar"))
        self.assertIsNotNone(regex.match("/foo/baz"))
        self.assertIsNone(regex.match("/foo/qux"))

    def test_bytes_pattern(self):
        regex = getRegEx(b"/foo/bar")
        self.assertIsNotNone(regex.match("/foo/bar"))

    def test_dot_escaped(self):
        regex = getRegEx("/foo.bar")
        self.assertIsNotNone(regex.match("/foo.bar"))
        self.assertIsNone(regex.match("/fooXbar"))

    def test_parens_escaped(self):
        regex = getRegEx("/foo(bar)")
        self.assertIsNotNone(regex.match("/foo(bar)"))


if __name__ == "__main__":
    unittest.main()
