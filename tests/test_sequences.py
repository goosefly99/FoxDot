"""Unit tests for FoxDot.lib.Patterns.Sequences — pattern constructor P[],
pattern functions (PAlt, PStretch, PPairs, PZip, PStutter, PSq, PStep, PSum,
PRange, PTri, PSine, PEuclid, PBeat, PDur, PQuicken, PRhythm, PJoin), and
the Chords module constants."""

import math
import unittest

from FoxDot.lib.Patterns.Main import Pattern, PGroup, asStream
from FoxDot.lib.Patterns.Sequences import (
    P,
    PAlt,
    PBeat,
    PBern,
    PDur,
    PEuclid,
    PEuclid2,
    PJoin,
    PPairs,
    PQuicken,
    PRange,
    PRhythm,
    PShuf,
    PSine,
    PSq,
    PStep,
    PStretch,
    PStutter,
    PSum,
    PTri,
    PZip,
    PZip2,
)


# ==================================================================
# P[] — Pattern constructor
# ==================================================================

class TestPatternConstructorP(unittest.TestCase):
    """Test the P[] / P() shorthand for creating patterns."""

    def test_p_getitem_list(self):
        pat = P[1, 2, 3]
        self.assertIsInstance(pat, Pattern)
        self.assertEqual(list(pat), [1, 2, 3])

    def test_p_getitem_single(self):
        pat = P[5]
        self.assertIsInstance(pat, Pattern)
        self.assertEqual(list(pat), [5])

    def test_p_getitem_slice(self):
        """P[0:5] should create Pattern(range(0, 5))."""
        pat = P[0:5]
        self.assertEqual(list(pat), [0, 1, 2, 3, 4])

    def test_p_getitem_slice_with_step(self):
        pat = P[0:10:2]
        self.assertEqual(list(pat), [0, 2, 4, 6, 8])

    def test_p_getitem_mixed_values_and_slice(self):
        """P[0, 2, 5:8] should combine values and range."""
        pat = P[0, 2, 5:8]
        self.assertEqual(list(pat), [0, 2, 5, 6, 7])

    def test_p_call_creates_pgroup(self):
        grp = P(1, 2, 3)
        self.assertIsInstance(grp, PGroup)

    def test_p_call_single_value(self):
        grp = P(5)
        self.assertIsInstance(grp, PGroup)

    def test_p_getitem_with_pattern_returns_same(self):
        pat = Pattern([1, 2, 3])
        result = P[pat]
        self.assertIs(result, pat)


# ==================================================================
# PShuf — shuffled pattern
# ==================================================================

class TestPShuf(unittest.TestCase):
    """Test PShuf creates a shuffled version of a sequence."""

    def test_returns_pattern(self):
        pat = PShuf([1, 2, 3, 4])
        self.assertIsInstance(pat, Pattern)

    def test_same_length(self):
        pat = PShuf([1, 2, 3, 4, 5])
        self.assertEqual(len(pat), 5)

    def test_same_elements(self):
        pat = PShuf([10, 20, 30])
        self.assertEqual(sorted(list(pat)), [10, 20, 30])

    def test_empty_input(self):
        pat = PShuf([])
        self.assertEqual(len(pat), 0)


# ==================================================================
# PAlt — alternating patterns
# ==================================================================

class TestPAlt(unittest.TestCase):
    """Test PAlt interleaves values from multiple sequences."""

    def test_two_equal_length(self):
        pat = PAlt([1, 2], [3, 4])
        self.assertEqual(list(pat), [1, 3, 2, 4])

    def test_two_unequal_length(self):
        """LCM-based expansion: [1,2,3] and [10,20] → LCM(3,2)=6 items interleaved."""
        pat = PAlt([1, 2, 3], [10, 20])
        self.assertEqual(len(pat), 12)  # 6 * 2 patterns
        # First pair
        self.assertEqual(pat[0], 1)
        self.assertEqual(pat[1], 10)

    def test_three_patterns(self):
        pat = PAlt([1], [2], [3])
        self.assertEqual(list(pat), [1, 2, 3])

    def test_returns_pattern(self):
        pat = PAlt([0, 1], [2, 3])
        self.assertIsInstance(pat, Pattern)


# ==================================================================
# PStretch — stretch to size
# ==================================================================

class TestPStretch(unittest.TestCase):
    """Test PStretch loops a sequence until it reaches a given size."""

    def test_basic_stretch(self):
        pat = PStretch([0, 1, 2], 5)
        self.assertEqual(len(pat), 5)
        self.assertEqual(list(pat), [0, 1, 2, 0, 1])

    def test_exact_length(self):
        pat = PStretch([1, 2, 3], 3)
        self.assertEqual(list(pat), [1, 2, 3])

    def test_shorter(self):
        pat = PStretch([1, 2, 3, 4, 5], 2)
        self.assertEqual(len(pat), 2)
        self.assertEqual(list(pat), [1, 2])

    def test_returns_pattern(self):
        pat = PStretch([1], 4)
        self.assertIsInstance(pat, Pattern)


# ==================================================================
# PPairs — lace with function
# ==================================================================

class TestPPairs(unittest.TestCase):
    """Test PPairs laces a sequence with function-transformed values."""

    def test_default_function(self):
        """Default is lambda n: 8 - n."""
        pat = PPairs([1, 2, 3])
        self.assertEqual(list(pat), [1, 7, 2, 6, 3, 5])

    def test_custom_function(self):
        pat = PPairs([1, 2], func=lambda n: n * 2)
        self.assertEqual(list(pat), [1, 2, 2, 4])

    def test_single_element(self):
        pat = PPairs([5])
        self.assertEqual(list(pat), [5, 3])  # 8 - 5 = 3

    def test_returns_pattern(self):
        pat = PPairs([1])
        self.assertIsInstance(pat, Pattern)


# ==================================================================
# PZip — zip patterns into tuples
# ==================================================================

class TestPZip(unittest.TestCase):
    """Test PZip creates tuples from multiple patterns."""

    def test_equal_length(self):
        pat = PZip([1, 2], [3, 4])
        self.assertEqual(len(pat), 2)
        self.assertEqual(pat[0], (1, 3))
        self.assertEqual(pat[1], (2, 4))

    def test_unequal_length_lcm(self):
        """PZip([0,1,2], [3,4]) → LCM(3,2)=6 tuples."""
        pat = PZip([0, 1, 2], [3, 4])
        self.assertEqual(len(pat), 6)

    def test_three_patterns(self):
        pat = PZip([1], [2], [3])
        self.assertEqual(pat[0], (1, 2, 3))

    def test_returns_pattern(self):
        pat = PZip([0], [1])
        self.assertIsInstance(pat, Pattern)


# ==================================================================
# PZip2 — conditional zip
# ==================================================================

class TestPZip2(unittest.TestCase):
    """Test PZip2 zips two patterns with a rule."""

    def test_default_rule_always_true(self):
        pat = PZip2([1, 2], [3, 4])
        self.assertEqual(len(pat), 2)
        self.assertEqual(pat[0], (1, 3))
        self.assertEqual(pat[1], (2, 4))

    def test_custom_rule(self):
        """Only zip when a != b."""
        pat = PZip2([1, 2, 3], [1, 4, 3], rule=lambda a, b: a != b)
        self.assertEqual(len(pat), 1)
        self.assertEqual(pat[0], (2, 4))


# ==================================================================
# PStutter — repeat elements
# ==================================================================

class TestPStutter(unittest.TestCase):
    """Test PStutter repeats each element n times."""

    def test_default_n2(self):
        pat = PStutter([1, 2, 3])
        self.assertEqual(list(pat), [1, 1, 2, 2, 3, 3])

    def test_custom_n(self):
        pat = PStutter([1, 2], 3)
        self.assertEqual(list(pat), [1, 1, 1, 2, 2, 2])

    def test_n_equals_1(self):
        pat = PStutter([5, 10], 1)
        self.assertEqual(list(pat), [5, 10])

    def test_returns_pattern(self):
        pat = PStutter([1])
        self.assertIsInstance(pat, Pattern)


# ==================================================================
# PSq — square numbers
# ==================================================================

class TestPSq(unittest.TestCase):
    """Test PSq returns square number patterns."""

    def test_default(self):
        pat = PSq()  # a=1, b=2, c=3 → [1^2, 2^2, 3^2] = [1, 4, 9]
        self.assertEqual(list(pat), [1, 4, 9])

    def test_custom_range(self):
        pat = PSq(0, 2, 4)  # [0^2, 1^2, 2^2, 3^2]
        self.assertEqual(list(pat), [0, 1, 4, 9])

    def test_cubes(self):
        pat = PSq(1, 3, 3)  # [1^3, 2^3, 3^3]
        self.assertEqual(list(pat), [1, 8, 27])


# ==================================================================
# PStep — step pattern
# ==================================================================

class TestPStep(unittest.TestCase):
    """Test PStep places a value every n-th position."""

    def test_basic(self):
        pat = PStep(4, 1)  # [0, 0, 0, 1]
        self.assertEqual(list(pat), [0, 0, 0, 1])

    def test_custom_default(self):
        pat = PStep(3, 9, 5)  # [5, 5, 9]
        self.assertEqual(list(pat), [5, 5, 9])

    def test_n_equals_1(self):
        pat = PStep(1, 7)
        self.assertEqual(list(pat), [7])

    def test_returns_pattern(self):
        pat = PStep(2, 1)
        self.assertIsInstance(pat, Pattern)


# ==================================================================
# PSum — pattern summing to total
# ==================================================================

class TestPSum(unittest.TestCase):
    """Test PSum returns a pattern of n values summing to total."""

    def test_sum_equals_total(self):
        pat = PSum(3, 8)
        total = sum(list(pat))
        self.assertAlmostEqual(total, 8.0, places=5)

    def test_length(self):
        pat = PSum(5, 4)
        self.assertEqual(len(pat), 5)

    def test_all_positive(self):
        pat = PSum(4, 10)
        for val in pat:
            self.assertGreaterEqual(val, 0)

    def test_returns_pattern(self):
        pat = PSum(3, 6)
        self.assertIsInstance(pat, Pattern)


# ==================================================================
# PRange — range pattern
# ==================================================================

class TestPRange(unittest.TestCase):
    """Test PRange creates range-based patterns."""

    def test_single_arg(self):
        """PRange(5) → [0, 1, 2, 3, 4]."""
        pat = PRange(5)
        self.assertEqual(list(pat), [0, 1, 2, 3, 4])

    def test_start_stop(self):
        pat = PRange(2, 6)
        self.assertEqual(list(pat), [2, 3, 4, 5])

    def test_start_stop_step(self):
        pat = PRange(0, 10, 3)
        self.assertEqual(list(pat), [0, 3, 6, 9])

    def test_auto_flip_step(self):
        """If start > stop and step > 0, step should auto-negate."""
        pat = PRange(5, 0)
        self.assertEqual(list(pat), [5, 4, 3, 2, 1])

    def test_start_equals_stop(self):
        pat = PRange(3, 3)
        self.assertEqual(list(pat), [3])

    def test_returns_pattern(self):
        pat = PRange(3)
        self.assertIsInstance(pat, Pattern)


# ==================================================================
# PTri — triangle pattern
# ==================================================================

class TestPTri(unittest.TestCase):
    """Test PTri creates ascending-then-descending patterns."""

    def test_basic(self):
        """PTri(5) → [0, 1, 2, 3, 4, 3, 2, 1]."""
        pat = PTri(5)
        self.assertEqual(list(pat), [0, 1, 2, 3, 4, 3, 2, 1])

    def test_start_stop(self):
        pat = PTri(0, 4)
        self.assertEqual(list(pat), [0, 1, 2, 3, 2, 1])

    def test_ascending_then_descending(self):
        """PTri ascends then descends without repeating peak or start."""
        pat = PTri(4)
        # PTri(4) → [0,1,2,3] | [2,1] = [0,1,2,3,2,1]
        data = list(pat)
        self.assertEqual(data, [0, 1, 2, 3, 2, 1])

    def test_returns_pattern(self):
        pat = PTri(3)
        self.assertIsInstance(pat, Pattern)


# ==================================================================
# PSine — sine wave pattern
# ==================================================================

class TestPSine(unittest.TestCase):
    """Test PSine generates one cycle of a sine wave."""

    def test_length(self):
        pat = PSine(16)
        self.assertEqual(len(pat), 16)

    def test_starts_near_zero(self):
        pat = PSine(16)
        self.assertAlmostEqual(pat[0], 0.0, places=5)

    def test_peak_near_quarter(self):
        """Quarter way through should be near 1.0."""
        pat = PSine(16)
        self.assertAlmostEqual(pat[4], 1.0, places=5)

    def test_zero_at_half(self):
        pat = PSine(16)
        self.assertAlmostEqual(pat[8], 0.0, places=5)

    def test_trough_at_three_quarter(self):
        pat = PSine(16)
        self.assertAlmostEqual(pat[12], -1.0, places=5)

    def test_default_16(self):
        pat = PSine()
        self.assertEqual(len(pat), 16)

    def test_returns_pattern(self):
        pat = PSine(8)
        self.assertIsInstance(pat, Pattern)


# ==================================================================
# PEuclid — Euclidean rhythm
# ==================================================================

class TestPEuclid(unittest.TestCase):
    """Test PEuclid generates Euclidean rhythms."""

    def test_3_8(self):
        """Classic Tresillo rhythm: 3 pulses over 8 steps."""
        pat = PEuclid(3, 8)
        self.assertEqual(len(pat), 8)
        self.assertEqual(sum(list(pat)), 3)

    def test_4_16(self):
        pat = PEuclid(4, 16)
        self.assertEqual(len(pat), 16)
        self.assertEqual(sum(list(pat)), 4)

    def test_1_4(self):
        pat = PEuclid(1, 4)
        self.assertEqual(sum(list(pat)), 1)

    def test_equal_n_k(self):
        pat = PEuclid(4, 4)
        self.assertEqual(list(pat), [1, 1, 1, 1])

    def test_returns_pattern(self):
        pat = PEuclid(2, 5)
        self.assertIsInstance(pat, Pattern)


# ==================================================================
# PEuclid2 — Euclidean rhythm with custom values
# ==================================================================

class TestPEuclid2(unittest.TestCase):
    """Test PEuclid2 with custom lo/hi values."""

    def test_custom_values(self):
        pat = PEuclid2(3, 8, "-", "X")
        self.assertEqual(len(pat), 8)
        self.assertEqual(list(pat).count("X"), 3)
        self.assertEqual(list(pat).count("-"), 5)

    def test_returns_pattern(self):
        pat = PEuclid2(2, 4, 0, 1)
        self.assertIsInstance(pat, Pattern)


# ==================================================================
# PBern — Bernoulli sequence
# ==================================================================

class TestPBern(unittest.TestCase):
    """Test PBern generates a binary Bernoulli sequence."""

    def test_length(self):
        pat = PBern(20)
        self.assertEqual(len(pat), 20)

    def test_values_binary(self):
        pat = PBern(100)
        for val in pat:
            self.assertIn(val, (0, 1))

    def test_ratio_zero(self):
        """With ratio=0, all values should be 0."""
        pat = PBern(50, 0)
        self.assertEqual(sum(list(pat)), 0)

    def test_ratio_one(self):
        """With ratio=1, all values should be 1."""
        pat = PBern(50, 1)
        self.assertEqual(sum(list(pat)), 50)

    def test_returns_pattern(self):
        pat = PBern(10)
        self.assertIsInstance(pat, Pattern)


# ==================================================================
# PBeat — duration from string
# ==================================================================

class TestPBeat(unittest.TestCase):
    """Test PBeat converts a beat string into durations."""

    def test_basic(self):
        pat = PBeat("x x")
        # "x x" → [1, 0, 1] → durations
        self.assertIsInstance(pat, Pattern)

    def test_all_pulses(self):
        pat = PBeat("xxxx", dur=1)
        self.assertEqual(list(pat), [1, 1, 1, 1])

    def test_with_spaces(self):
        pat = PBeat("x  x", dur=1)
        # [1, 0, 0, 1] → durations [3, 1]
        self.assertEqual(len(pat), 2)
        self.assertEqual(sum(list(pat)), 4)

    def test_returns_pattern(self):
        pat = PBeat("x x x")
        self.assertIsInstance(pat, Pattern)


# ==================================================================
# PDur — Euclidean durations
# ==================================================================

class TestPDur(unittest.TestCase):
    """Test PDur returns actual durations from Euclidean rhythms."""

    def test_3_8(self):
        """PDur(3, 8) should return 3 durations that sum to 2.0 (8 * 0.25)."""
        pat = PDur(3, 8)
        self.assertEqual(len(pat), 3)
        total = sum(list(pat))
        self.assertAlmostEqual(total, 2.0, places=5)

    def test_4_4(self):
        pat = PDur(4, 4)
        self.assertEqual(list(pat), [0.25, 0.25, 0.25, 0.25])

    def test_n_greater_than_k(self):
        """When n > k, k is doubled and dur halved."""
        pat = PDur(5, 4)
        self.assertIsNotNone(pat)
        total = sum(list(pat))
        # 5 pulses over 8 steps (doubled), dur=0.125 each, total = 8 * 0.125 = 1.0
        self.assertAlmostEqual(total, 1.0, places=5)

    def test_returns_pattern(self):
        pat = PDur(2, 8)
        self.assertIsInstance(pat, Pattern)


# ==================================================================
# PStep — step with value
# ==================================================================

class TestPStepDetailed(unittest.TestCase):
    """Additional PStep tests."""

    def test_large_n(self):
        pat = PStep(8, 1)
        self.assertEqual(len(pat), 8)
        self.assertEqual(pat[7], 1)
        self.assertEqual(sum(list(pat)), 1)

    def test_value_type_preserved(self):
        pat = PStep(3, "x", "-")
        self.assertEqual(list(pat), ["-", "-", "x"])


# ==================================================================
# PQuicken — decreasing delay amounts
# ==================================================================

class TestPQuicken(unittest.TestCase):
    """Test PQuicken creates a PGroup of decreasing delays."""

    def test_returns_pgroup(self):
        result = PQuicken()
        self.assertIsInstance(result, PGroup)

    def test_starts_at_zero(self):
        result = PQuicken()
        self.assertEqual(result[0], 0)

    def test_delays_increase(self):
        """Delay values should be non-decreasing."""
        result = PQuicken()
        data = list(result)
        for i in range(1, len(data)):
            self.assertGreaterEqual(data[i], data[i - 1])


# ==================================================================
# PJoin — join patterns
# ==================================================================

class TestPJoin(unittest.TestCase):
    """Test PJoin concatenates multiple patterns."""

    def test_two_patterns(self):
        p1 = Pattern([1, 2])
        p2 = Pattern([3, 4])
        result = PJoin([p1, p2])
        self.assertEqual(list(result), [1, 2, 3, 4])

    def test_three_patterns(self):
        result = PJoin([Pattern([1]), Pattern([2]), Pattern([3])])
        self.assertEqual(list(result), [1, 2, 3])

    def test_empty_patterns(self):
        result = PJoin([Pattern([]), Pattern([1])])
        self.assertEqual(list(result), [1])

    def test_returns_pattern(self):
        result = PJoin([Pattern([1])])
        self.assertIsInstance(result, Pattern)


# ==================================================================
# PRhythm — rhythm from mixed input
# ==================================================================

class TestPRhythm(unittest.TestCase):
    """Test PRhythm converts mixed duration/tuple input."""

    def test_single_number(self):
        pat = PRhythm([1])
        self.assertEqual(list(pat), [1])

    def test_returns_pattern(self):
        pat = PRhythm([1, 2])
        self.assertIsInstance(pat, Pattern)

    def test_with_tuple_input(self):
        """A tuple should be expanded via PDur."""
        pat = PRhythm([1, (3, 8)])
        self.assertEqual(len(pat), 2)


# ==================================================================
# Chords module — constants
# ==================================================================

class TestChords(unittest.TestCase):
    """Test chord constant definitions from FoxDot.lib.Chords."""

    @classmethod
    def setUpClass(cls):
        from FoxDot.lib.Chords import I, II, III, IV, V, VI, VII
        from FoxDot.lib.Chords import I7, II7, III7, IV7, V7, VI7, VII7
        cls.I, cls.II, cls.III, cls.IV = I, II, III, IV
        cls.V, cls.VI, cls.VII = V, VI, VII
        cls.I7, cls.II7, cls.III7, cls.IV7 = I7, II7, III7, IV7
        cls.V7, cls.VI7, cls.VII7 = V7, VI7, VII7

    def test_I_is_pgroup(self):
        self.assertIsInstance(self.I, PGroup)

    def test_I_values(self):
        """I = (0, 2, 4) — root triad in scale degrees."""
        self.assertEqual(tuple(self.I), (0, 2, 4))

    def test_II_values(self):
        self.assertEqual(tuple(self.II), (1, 3, 5))

    def test_III_values(self):
        self.assertEqual(tuple(self.III), (2, 4, -1))

    def test_IV_values(self):
        self.assertEqual(tuple(self.IV), (3, 5, 0))

    def test_V_values(self):
        self.assertEqual(tuple(self.V), (4, -1, 1))

    def test_VI_values(self):
        self.assertEqual(tuple(self.VI), (5, 0, 2))

    def test_VII_values(self):
        self.assertEqual(tuple(self.VII), (-1, 1, 3))

    def test_all_triads_are_pgroups(self):
        for chord in (self.I, self.II, self.III, self.IV,
                      self.V, self.VI, self.VII):
            self.assertIsInstance(chord, PGroup)

    def test_seventh_chords_are_pgroups(self):
        for chord in (self.I7, self.II7, self.III7, self.IV7,
                      self.V7, self.VI7, self.VII7):
            self.assertIsInstance(chord, PGroup)

    def test_seventh_chords_have_four_notes(self):
        for chord in (self.I7, self.II7, self.III7, self.IV7,
                      self.V7, self.VI7, self.VII7):
            self.assertEqual(len(chord), 4,
                             f"Seventh chord should have 4 notes, got {len(chord)}")

    def test_I7_extends_I(self):
        """I7 should be I plus the 7th degree (6)."""
        i7_data = list(self.I7)
        self.assertEqual(i7_data[:3], [0, 2, 4])
        self.assertEqual(i7_data[3], 6)

    def test_V7_extends_V(self):
        v7_data = list(self.V7)
        self.assertEqual(v7_data[:3], [4, -1, 1])
        self.assertEqual(v7_data[3], 10)


if __name__ == "__main__":
    unittest.main()
