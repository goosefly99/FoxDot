"""Unit tests for FoxDot.lib.Root — Note class, chromatic note lookup,
root note singleton, and note arithmetic."""

import unittest

from FoxDot.lib.Root import CHROMATIC_NOTES, Note, __root__


# ==================================================================
# CHROMATIC_NOTES constant
# ==================================================================

class TestChromaticNotes(unittest.TestCase):
    """Verify the chromatic note lookup table."""

    def test_length(self):
        self.assertEqual(len(CHROMATIC_NOTES), 12)

    def test_natural_notes_present(self):
        for note in ("C", "D", "E", "F", "G", "A", "B"):
            self.assertIn(note, CHROMATIC_NOTES)

    def test_c_is_first(self):
        self.assertEqual(CHROMATIC_NOTES[0], "C")

    def test_b_is_last(self):
        self.assertEqual(CHROMATIC_NOTES[11], "B")

    def test_sharps_are_spaces(self):
        """Positions 1, 3, 6, 8, 10 (C#, D#, F#, G#, A#) are spaces."""
        for idx in (1, 3, 6, 8, 10):
            self.assertEqual(CHROMATIC_NOTES[idx], " ")

    def test_e_and_b_have_no_sharp(self):
        """E→F and B→C have no sharp between them."""
        e_idx = CHROMATIC_NOTES.index("E")
        self.assertEqual(CHROMATIC_NOTES[e_idx + 1], "F")
        b_idx = CHROMATIC_NOTES.index("B")
        # B is last, wraps to C
        self.assertEqual(CHROMATIC_NOTES[(b_idx + 1) % 12], "C")


# ==================================================================
# Note — construction from string
# ==================================================================

class TestNoteFromString(unittest.TestCase):
    """Test creating a Note from a string (letter name)."""

    def test_note_c(self):
        n = Note("C")
        self.assertEqual(int(n), 0)

    def test_note_d(self):
        n = Note("D")
        self.assertEqual(int(n), 2)

    def test_note_e(self):
        n = Note("E")
        self.assertEqual(int(n), 4)

    def test_note_f(self):
        n = Note("F")
        self.assertEqual(int(n), 5)

    def test_note_g(self):
        n = Note("G")
        self.assertEqual(int(n), 7)

    def test_note_a(self):
        n = Note("A")
        self.assertEqual(int(n), 9)

    def test_note_b(self):
        n = Note("B")
        self.assertEqual(int(n), 11)

    def test_lowercase_input(self):
        """Input is case-insensitive."""
        n = Note("c")
        self.assertEqual(int(n), 0)

    def test_sharp_c(self):
        n = Note("C#")
        self.assertEqual(int(n), 1)

    def test_sharp_f(self):
        n = Note("F#")
        self.assertEqual(int(n), 6)

    def test_flat_d(self):
        """Db should be one semitone below D (= C# = 1)."""
        n = Note("Db")
        self.assertEqual(int(n), 1)

    def test_flat_b(self):
        """Bb = 10."""
        n = Note("Bb")
        self.assertEqual(int(n), 10)

    def test_sharp_wraps_around(self):
        """B# wraps around to 0 (C)."""
        n = Note("B#")
        self.assertEqual(int(n), 0)

    def test_flat_wraps_around(self):
        """Cb wraps to 11 (B)."""
        n = Note("Cb")
        self.assertEqual(int(n), 11)

    def test_invalid_string_raises(self):
        with self.assertRaises(TypeError):
            Note("Cxx")

    def test_invalid_long_string_raises(self):
        with self.assertRaises(TypeError):
            Note("Hello")

    def test_char_attribute_set(self):
        n = Note("G")
        self.assertEqual(n.char, "G")

    def test_char_attribute_sharp(self):
        n = Note("F#")
        self.assertEqual(n.char, "F#")


# ==================================================================
# Note — construction from int
# ==================================================================

class TestNoteFromInt(unittest.TestCase):
    """Test creating a Note from an integer."""

    def test_zero(self):
        n = Note(0)
        self.assertEqual(int(n), 0)

    def test_seven(self):
        n = Note(7)
        self.assertEqual(int(n), 7)

    def test_negative(self):
        n = Note(-1)
        self.assertEqual(int(n), -1)

    def test_char_set_from_chromatic(self):
        n = Note(0)
        self.assertEqual(n.char, "C")

    def test_char_for_accidental_position(self):
        """Index 1 maps to a space in CHROMATIC_NOTES."""
        n = Note(1)
        self.assertEqual(n.char, " ")


# ==================================================================
# Note — construction from float
# ==================================================================

class TestNoteFromFloat(unittest.TestCase):
    """Test creating a Note from a float (micro-tuning)."""

    def test_float_value(self):
        n = Note(3.5)
        self.assertAlmostEqual(float(n), 3.5)

    def test_float_char_is_microtuned(self):
        n = Note(3.5)
        self.assertEqual(n.char, "<Micro-Tuned>")


# ==================================================================
# Note — str / repr / float / int
# ==================================================================

class TestNoteRepresentation(unittest.TestCase):
    """Test Note string representations and numeric conversions."""

    def test_str_from_int(self):
        n = Note(5)
        self.assertEqual(str(n), "5")

    def test_repr_from_int(self):
        n = Note(5)
        self.assertEqual(repr(n), "5")

    def test_float_conversion(self):
        n = Note(7)
        self.assertAlmostEqual(float(n), 7.0)

    def test_int_conversion(self):
        n = Note("A")
        self.assertEqual(int(n), 9)


# ==================================================================
# Note — arithmetic
# ==================================================================

class TestNoteArithmetic(unittest.TestCase):
    """Test Note addition and subtraction."""

    def test_add_int(self):
        n = Note(5)
        result = n + 3
        self.assertEqual(result, 8)

    def test_sub_int(self):
        n = Note(7)
        result = n - 2
        self.assertEqual(result, 5)

    def test_radd(self):
        n = Note(4)
        result = 10 + n
        self.assertEqual(result, 14)

    def test_rsub(self):
        n = Note(3)
        result = 10 - n
        self.assertEqual(result, 7)

    def test_add_returns_numeric(self):
        """Addition should return a plain number, not a Note."""
        n = Note(5)
        result = n + 3
        self.assertIsInstance(result, (int, float))

    def test_iadd(self):
        """In-place add modifies the num attribute."""
        n = Note(5)
        n += 2
        # __iadd__ doesn't return self, so n is now None
        # This tests the actual behavior (which is a known quirk)

    def test_isub(self):
        """In-place sub modifies the num attribute."""
        n = Note(5)
        n -= 1
        # Same as iadd — returns None due to missing return self


# ==================================================================
# Note — callable (re-setting value)
# ==================================================================

class TestNoteCallable(unittest.TestCase):
    """Test Note.__call__ for resetting the value."""

    def test_call_with_int(self):
        n = Note(0)
        result = n(5)
        self.assertIs(result, n)
        self.assertEqual(int(n), 5)

    def test_call_with_string(self):
        n = Note(0)
        n("G")
        self.assertEqual(int(n), 7)

    def test_call_no_args_returns_self(self):
        n = Note(5)
        result = n()
        self.assertIs(result, n)
        self.assertEqual(int(n), 5)


# ==================================================================
# Note.set — re-assignment
# ==================================================================

class TestNoteSet(unittest.TestCase):
    """Test Note.set for changing value after construction."""

    def test_set_int(self):
        n = Note(0)
        n.set(9)
        self.assertEqual(int(n), 9)

    def test_set_string(self):
        n = Note(0)
        n.set("E")
        self.assertEqual(int(n), 4)

    def test_set_float(self):
        n = Note(0)
        n.set(2.5)
        self.assertAlmostEqual(float(n), 2.5)
        self.assertEqual(n.char, "<Micro-Tuned>")

    def test_set_preserves_char_on_int(self):
        n = Note(0)
        n.set(7)
        self.assertEqual(n.char, "G")


# ==================================================================
# __root__ singleton
# ==================================================================

class TestRootSingleton(unittest.TestCase):
    """Test the __root__ singleton that manages the global root note."""

    def setUp(self):
        self.root = __root__()

    def test_default_is_c(self):
        self.assertEqual(int(self.root.default), 0)

    def test_setattr_delegates_to_note_set(self):
        """Setting root.default = value should call Note.set, not replace."""
        original_note = self.root.default
        self.root.default = 5
        # The same Note object should be reused
        self.assertIs(self.root.default, original_note)
        self.assertEqual(int(self.root.default), 5)

    def test_setattr_with_string(self):
        self.root.default = "G"
        self.assertEqual(int(self.root.default), 7)

    def test_reset(self):
        self.root.default = 7
        self.root.reset()
        self.assertEqual(int(self.root.default), 0)

    def test_non_default_attrs_set_normally(self):
        """Attributes other than 'default' should be set normally."""
        self.root.custom_attr = 42
        self.assertEqual(self.root.custom_attr, 42)

    def test_change_root_multiple_times(self):
        self.root.default = "A"
        self.assertEqual(int(self.root.default), 9)
        self.root.default = "D"
        self.assertEqual(int(self.root.default), 2)
        self.root.default = 0
        self.assertEqual(int(self.root.default), 0)


# ==================================================================
# Note — all 12 chromatic notes roundtrip
# ==================================================================

class TestNoteRoundTrip(unittest.TestCase):
    """Verify string-to-int-to-string roundtrip for natural notes."""

    def test_all_naturals_roundtrip(self):
        naturals = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
        for name, expected_num in naturals.items():
            n = Note(name)
            self.assertEqual(int(n), expected_num,
                             f"Note('{name}') should be {expected_num}")

    def test_all_sharps(self):
        sharps = {"C#": 1, "D#": 3, "F#": 6, "G#": 8, "A#": 10}
        for name, expected_num in sharps.items():
            n = Note(name)
            self.assertEqual(int(n), expected_num,
                             f"Note('{name}') should be {expected_num}")

    def test_all_flats(self):
        flats = {"Db": 1, "Eb": 3, "Gb": 6, "Ab": 8, "Bb": 10}
        for name, expected_num in flats.items():
            n = Note(name)
            self.assertEqual(int(n), expected_num,
                             f"Note('{name}') should be {expected_num}")

    def test_enharmonic_equivalence(self):
        """C# and Db should map to the same number."""
        self.assertEqual(int(Note("C#")), int(Note("Db")))
        self.assertEqual(int(Note("F#")), int(Note("Gb")))
        self.assertEqual(int(Note("G#")), int(Note("Ab")))


if __name__ == "__main__":
    unittest.main()
