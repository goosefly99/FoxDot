"""Unit tests for FoxDot.lib.Scale — MIDI/frequency conversion, ScalePattern,
built-in scale definitions, tuning, pentatonic derivation, and the Scale singleton."""

import math
import unittest

from FoxDot.lib.Scale import (
    FreqScalePattern,
    PentatonicScalePattern,
    Scale,
    ScalePattern,
    ScaleType,
    Tuning,
    TuningType,
    _DefaultScale,
    freqtomidi,
    get_freq_and_midi,
    midi,
    miditofreq,
)


# ------------------------------------------------------------------
# Helper
# ------------------------------------------------------------------

def _approx(a, b, tol=0.01):
    """Return True if *a* and *b* are within *tol* of each other."""
    return abs(a - b) < tol


# ==================================================================
# miditofreq / freqtomidi
# ==================================================================

class TestMidiToFreq(unittest.TestCase):
    """Test the MIDI→frequency conversion."""

    def test_a440(self):
        self.assertAlmostEqual(miditofreq(69), 440.0, places=5)

    def test_middle_c(self):
        # MIDI 60 = Middle C ≈ 261.63 Hz
        self.assertAlmostEqual(miditofreq(60), 261.6256, places=3)

    def test_octave_doubles_frequency(self):
        for note in (48, 60, 72):
            self.assertAlmostEqual(
                miditofreq(note + 12), miditofreq(note) * 2, places=5
            )

    def test_zero(self):
        # MIDI 0 ≈ 8.176 Hz (sub-audible C-1)
        self.assertAlmostEqual(miditofreq(0), 8.1758, places=3)

    def test_high_note(self):
        # MIDI 127 ≈ 12543.85 Hz
        self.assertAlmostEqual(miditofreq(127), 12543.854, places=1)


class TestFreqToMidi(unittest.TestCase):
    """Test the frequency→MIDI conversion."""

    def test_a440(self):
        self.assertAlmostEqual(freqtomidi(440.0), 69.0, places=5)

    def test_middle_c(self):
        self.assertAlmostEqual(freqtomidi(261.6256), 60.0, places=2)

    def test_roundtrip(self):
        for m in (0, 48, 60, 69, 72, 100, 127):
            self.assertAlmostEqual(freqtomidi(miditofreq(m)), m, places=5)


# ==================================================================
# midi() — standalone function
# ==================================================================

class TestMidiFunction(unittest.TestCase):
    """Test the module-level midi() helper."""

    def test_middle_c_major(self):
        # Major scale, octave 5, degree 0, root 0 → MIDI 60
        major = [0, 2, 4, 5, 7, 9, 11]
        self.assertAlmostEqual(midi(major, 5, 0, root=0), 60.0)

    def test_root_shift(self):
        major = [0, 2, 4, 5, 7, 9, 11]
        # Root = 2 → two semitones above → MIDI 62
        self.assertAlmostEqual(midi(major, 5, 0, root=2), 62.0)

    def test_octave_shift(self):
        major = [0, 2, 4, 5, 7, 9, 11]
        # Octave 6 instead of 5 → +12
        self.assertAlmostEqual(midi(major, 6, 0), 72.0)

    def test_degree_wraps_octave(self):
        major = [0, 2, 4, 5, 7, 9, 11]
        # Degree 7 in a 7-note scale → wraps to next octave, degree 0
        result = midi(major, 5, 7)
        self.assertAlmostEqual(result, 72.0)

    def test_negative_degree(self):
        major = [0, 2, 4, 5, 7, 9, 11]
        # Degree -1 should go below the current octave
        result = midi(major, 5, -1)
        # -1 // 7 = -1, so octave becomes 4; index = -1 % 7 = 6 → semitone 11
        expected = 12 * 4 + 0 + 11  # 59
        self.assertAlmostEqual(result, expected)

    def test_microtonal_degree(self):
        major = [0, 2, 4, 5, 7, 9, 11]
        # Degree 0.5 → halfway between degree 0 (semitone 0) and degree 1 (semitone 2)
        result = midi(major, 5, 0.5)
        # micro = 0.5, diff = scale[1] - scale[0] = 2, micro * diff = 1.0
        expected = 60.0 + 1.0
        self.assertAlmostEqual(result, expected)

    def test_chromatic_scale(self):
        chromatic = list(range(12))
        for degree in range(12):
            self.assertAlmostEqual(midi(chromatic, 5, degree), 60.0 + degree)


# ==================================================================
# TuningType
# ==================================================================

class TestTuningType(unittest.TestCase):

    def test_et12_length(self):
        # ET12 has 12 semitones; the last entry (12) becomes .steps
        self.assertEqual(len(Tuning.ET12), 12)

    def test_et12_steps(self):
        self.assertEqual(Tuning.ET12.steps, 12)

    def test_et12_values(self):
        for i in range(12):
            self.assertEqual(Tuning.ET12[i], i)

    def test_just_intonation_steps(self):
        self.assertEqual(Tuning.just.steps, 12)

    def test_custom_tuning(self):
        t = TuningType([0, 3, 6, 9, 12])
        self.assertEqual(len(t), 4)
        self.assertEqual(t.steps, 12)
        self.assertEqual(list(t), [0, 3, 6, 9])


# ==================================================================
# ScalePattern
# ==================================================================

class TestScalePattern(unittest.TestCase):

    def test_creation(self):
        sp = ScalePattern([0, 2, 4, 5, 7, 9, 11], name="major")
        self.assertEqual(sp.name, "major")
        self.assertEqual(len(sp), 7)

    def test_data(self):
        sp = ScalePattern([0, 2, 4, 5, 7, 9, 11])
        self.assertEqual(list(sp.data), [0, 2, 4, 5, 7, 9, 11])

    def test_is_scale_type(self):
        sp = ScalePattern([0, 2, 4])
        self.assertIsInstance(sp, ScaleType)

    def test_default_tuning_is_et12(self):
        sp = ScalePattern([0, 2, 4, 5, 7, 9, 11])
        self.assertEqual(sp.tuning.steps, 12)

    def test_equality(self):
        a = ScalePattern([0, 2, 4, 5, 7, 9, 11], name="major")
        b = ScalePattern([0, 2, 4, 5, 7, 9, 11], name="major")
        self.assertEqual(a, b)

    def test_inequality_different_name(self):
        a = ScalePattern([0, 2, 4, 5, 7, 9, 11], name="major")
        b = ScalePattern([0, 2, 3, 5, 7, 8, 10], name="minor")
        self.assertNotEqual(a, b)

    def test_inequality_with_non_scale(self):
        sp = ScalePattern([0, 2, 4], name="test")
        self.assertNotEqual(sp, "not a scale")
        self.assertNotEqual(sp, 42)

    def test_has_pentatonic(self):
        sp = ScalePattern([0, 2, 4, 5, 7, 9, 11], name="major")
        self.assertIsInstance(sp.pentatonic, PentatonicScalePattern)

    def test_get_midi_note_c5(self):
        sp = ScalePattern([0, 2, 4, 5, 7, 9, 11])
        # Degree 0, octave 5, root 0 → MIDI 60
        self.assertAlmostEqual(sp.get_midi_note(0, octave=5, root=0), 60.0)

    def test_get_midi_note_with_root(self):
        sp = ScalePattern([0, 2, 4, 5, 7, 9, 11])
        # Root = 3 shifts everything up 3 semitones
        self.assertAlmostEqual(sp.get_midi_note(0, octave=5, root=3), 63.0)

    def test_get_freq_returns_float(self):
        sp = ScalePattern([0, 2, 4, 5, 7, 9, 11])
        freq = sp.get_freq(0, octave=5, root=0)
        self.assertIsInstance(freq, float)
        self.assertAlmostEqual(freq, miditofreq(60), places=3)

    def test_get_freq_with_midi(self):
        sp = ScalePattern([0, 2, 4, 5, 7, 9, 11])
        result = sp.get_freq(0, octave=5, root=0, get_midi=True)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        freq, midinote = result
        self.assertAlmostEqual(midinote, 60.0)
        self.assertAlmostEqual(freq, miditofreq(60), places=3)

    def test_note_to_semitone_basic(self):
        sp = ScalePattern([0, 2, 4, 5, 7, 9, 11])
        self.assertEqual(sp.note_to_semitone(0), 0)
        self.assertEqual(sp.note_to_semitone(1), 2)
        self.assertEqual(sp.note_to_semitone(2), 4)

    def test_note_to_semitone_wraps_octave(self):
        sp = ScalePattern([0, 2, 4, 5, 7, 9, 11])
        # Pitch 7 → wraps: 7 // 7 = 1 octave (12 semitones), 7 % 7 = 0 → semitone 0
        self.assertEqual(sp.note_to_semitone(7), 12)

    def test_custom_tuning(self):
        just = Tuning.just
        sp = ScalePattern([0, 2, 4, 5, 7, 9, 11], tuning=just)
        self.assertIs(sp.tuning, just)


# ==================================================================
# PentatonicScalePattern
# ==================================================================

class TestPentatonicScalePattern(unittest.TestCase):

    def test_length_is_five(self):
        sp = ScalePattern([0, 2, 4, 5, 7, 9, 11], name="major")
        self.assertEqual(len(sp.pentatonic), 5)

    def test_values_are_sorted(self):
        sp = ScalePattern([0, 2, 4, 5, 7, 9, 11], name="major")
        vals = list(sp.pentatonic)
        self.assertEqual(vals, sorted(vals))

    def test_values_subset_of_scale(self):
        sp = ScalePattern([0, 2, 4, 5, 7, 9, 11], name="major")
        scale_set = set(sp.data)
        for note in sp.pentatonic:
            self.assertIn(note, scale_set)

    def test_iteration(self):
        sp = ScalePattern([0, 2, 4, 5, 7, 9, 11], name="major")
        notes = [n for n in sp.pentatonic]
        self.assertEqual(len(notes), 5)


# ==================================================================
# FreqScalePattern
# ==================================================================

class TestFreqScalePattern(unittest.TestCase):

    def test_get_freq_passthrough(self):
        fsp = FreqScalePattern()
        # When using freq scale, the "degree" IS the frequency
        self.assertEqual(fsp.get_freq(440.0), 440.0)

    def test_get_freq_with_midi(self):
        fsp = FreqScalePattern()
        freq, midinote = fsp.get_freq(440.0, get_midi=True)
        self.assertEqual(freq, 440.0)
        self.assertAlmostEqual(midinote, 69.0, places=3)

    def test_get_midi_note(self):
        fsp = FreqScalePattern()
        self.assertAlmostEqual(fsp.get_midi_note(440.0), 69.0, places=3)

    def test_repr(self):
        fsp = FreqScalePattern()
        self.assertEqual(repr(fsp), "[inf]")


# ==================================================================
# Scale singleton
# ==================================================================

class TestScaleSingleton(unittest.TestCase):

    def test_singleton_has_major(self):
        self.assertIsInstance(Scale.major, ScalePattern)
        self.assertEqual(Scale.major.name, "major")

    def test_singleton_has_minor(self):
        self.assertIsInstance(Scale.minor, ScalePattern)
        self.assertEqual(Scale.minor.name, "minor")

    def test_library_returns_dict(self):
        lib = Scale.library()
        self.assertIsInstance(lib, dict)
        self.assertIn("major", lib)
        self.assertIn("minor", lib)

    def test_names_returns_sorted_list(self):
        names = Scale.names()
        self.assertIsInstance(names, list)
        self.assertEqual(names, sorted(names))
        self.assertIn("major", names)

    def test_get_scale_by_name(self):
        sp = Scale.get_scale("major")
        self.assertEqual(sp, Scale.major)

    def test_default_is_set(self):
        self.assertIsNotNone(Scale.default)

    def test_bracket_access(self):
        self.assertEqual(Scale["major"], Scale.major)

    def test_choose_returns_scale(self):
        chosen = Scale.choose()
        self.assertIsInstance(chosen, ScalePattern)

    def test_freq_scale_available(self):
        self.assertIsInstance(Scale.freq, FreqScalePattern)


# ==================================================================
# Built-in scale validation
# ==================================================================

class TestBuiltInScales(unittest.TestCase):
    """Verify well-known music theory properties of built-in scales."""

    def test_major_semitones(self):
        self.assertEqual(list(Scale.major.data), [0, 2, 4, 5, 7, 9, 11])

    def test_minor_semitones(self):
        self.assertEqual(list(Scale.minor.data), [0, 2, 3, 5, 7, 8, 10])

    def test_chromatic_has_12_notes(self):
        self.assertEqual(len(Scale.chromatic), 12)
        self.assertEqual(list(Scale.chromatic.data), list(range(12)))

    def test_blues_semitones(self):
        self.assertEqual(list(Scale.blues.data), [0, 3, 5, 6, 7, 10])

    def test_dorian_semitones(self):
        self.assertEqual(list(Scale.dorian.data), [0, 2, 3, 5, 7, 9, 10])

    def test_mixolydian_semitones(self):
        self.assertEqual(list(Scale.mixolydian.data), [0, 2, 4, 5, 7, 9, 10])

    def test_phrygian_semitones(self):
        self.assertEqual(list(Scale.phrygian.data), [0, 1, 3, 5, 7, 8, 10])

    def test_lydian_semitones(self):
        self.assertEqual(list(Scale.lydian.data), [0, 2, 4, 6, 7, 9, 11])

    def test_locrian_semitones(self):
        self.assertEqual(list(Scale.locrian.data), [0, 1, 3, 5, 6, 8, 10])

    def test_harmonic_minor_semitones(self):
        self.assertEqual(list(Scale.harmonicMinor.data), [0, 2, 3, 5, 7, 8, 11])

    def test_melodic_minor_semitones(self):
        self.assertEqual(list(Scale.melodicMinor.data), [0, 2, 3, 5, 7, 9, 11])

    def test_whole_tone_semitones(self):
        self.assertEqual(list(Scale.wholeTone.data), [0, 2, 4, 6, 8, 10])

    def test_pentatonic_scales(self):
        self.assertEqual(list(Scale.majorPentatonic.data), [0, 2, 4, 7, 9])
        self.assertEqual(list(Scale.minorPentatonic.data), [0, 3, 5, 7, 10])

    def test_all_scales_start_at_zero(self):
        """Every scale should start on the tonic (semitone 0)."""
        for name, scale in Scale.library().items():
            if name == "freq":
                continue  # FreqScalePattern is special
            self.assertEqual(
                scale.data[0], 0,
                f"Scale '{name}' does not start at 0: {list(scale.data)}"
            )

    def test_all_scales_ascending(self):
        """Every scale's semitone values should be in ascending order."""
        for name, scale in Scale.library().items():
            if name == "freq":
                continue
            data = list(scale.data)
            self.assertEqual(
                data, sorted(data),
                f"Scale '{name}' is not ascending: {data}"
            )

    def test_all_scales_within_octave(self):
        """All semitone values should be in [0, 12)."""
        for name, scale in Scale.library().items():
            if name == "freq":
                continue
            for s in scale.data:
                self.assertGreaterEqual(
                    s, 0, f"Scale '{name}' has semitone < 0: {s}"
                )
                self.assertLess(
                    s, 12, f"Scale '{name}' has semitone >= 12: {s}"
                )

    def test_aeolian_equals_minor(self):
        """Aeolian mode and natural minor are the same intervals."""
        self.assertEqual(list(Scale.aeolian.data), list(Scale.minor.data))


# ==================================================================
# get_freq_and_midi()
# ==================================================================

class TestGetFreqAndMidi(unittest.TestCase):

    def test_with_scale_pattern(self):
        freq, midinote = get_freq_and_midi(0, 5, 0, Scale.major)
        self.assertAlmostEqual(midinote, 60.0)
        self.assertAlmostEqual(freq, miditofreq(60), places=3)

    def test_with_plain_list(self):
        freq, midinote = get_freq_and_midi(0, 5, 0, [0, 2, 4, 5, 7, 9, 11])
        self.assertAlmostEqual(midinote, 60.0)
        self.assertAlmostEqual(freq, miditofreq(60), places=3)


# ==================================================================
# _DefaultScale
# ==================================================================

class TestDefaultScale(unittest.TestCase):

    def test_default_length(self):
        self.assertEqual(len(Scale.default), len(Scale.major))

    def test_default_iteration(self):
        notes = list(Scale.default)
        self.assertEqual(notes, list(Scale.major))


if __name__ == "__main__":
    unittest.main()
