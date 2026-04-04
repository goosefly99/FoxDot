"""Unit tests for FoxDot.lib.Patterns — PlayString, Parse, and PGroups modules.

Covers:
- PlayString: construction, indexing, bracket matching, error handling
- Parse: ParsePlayString, feed, convert_to_int, arrow_zip
- PGroups: PGroupPrime subclasses, behavior, calculate_time, bracket_style
"""

import unittest

from FoxDot.lib.Patterns.PlayString import PlayString, ParseError
from FoxDot.lib.Patterns.Parse import (
    ParsePlayString,
    convert_to_int,
    arrow_zip,
    feed,
)
from FoxDot.lib.Patterns.Main import Pattern, PGroup, GeneratorPattern
from FoxDot.lib.Patterns.PGroups import (
    PGroupPrime,
    PGroupStar,
    PGroupPlus,
    PGroupPow,
    PGroupDiv,
    PGroupMod,
    PGroupOr,
    PGroupXor,
    metaPGroupPrime,
)
from FoxDot.lib.Patterns.Generators import PRand
from FoxDot.lib.Patterns.Operations import POperand, PAdd, PSub, PMul, PDiv, PEq


# ==================================================================
# PlayString Class
# ==================================================================


class TestPlayStringConstruction(unittest.TestCase):
    """Test PlayString construction and basic properties."""

    def test_create_from_simple_string(self):
        ps = PlayString("xoxo")
        self.assertEqual(len(ps), 4)

    def test_create_from_empty_string(self):
        ps = PlayString("")
        self.assertEqual(len(ps), 0)

    def test_string_is_stored_as_list(self):
        ps = PlayString("abc")
        self.assertEqual(ps.string, ["a", "b", "c"])

    def test_original_preserved(self):
        ps = PlayString("hello")
        self.assertEqual(ps.original, "hello")

    def test_repr(self):
        ps = PlayString("xy")
        self.assertEqual(repr(ps), repr(["x", "y"]))


class TestPlayStringIndexing(unittest.TestCase):
    """Test PlayString __getitem__ and __setitem__."""

    def test_getitem_single(self):
        ps = PlayString("abc")
        self.assertEqual(ps[0], "a")
        self.assertEqual(ps[1], "b")
        self.assertEqual(ps[2], "c")

    def test_getitem_negative(self):
        ps = PlayString("abc")
        self.assertEqual(ps[-1], "c")

    def test_getitem_slice(self):
        ps = PlayString("abcde")
        self.assertEqual(ps[1:3], ["b", "c"])

    def test_setitem(self):
        ps = PlayString("abc")
        ps[1] = "z"
        self.assertEqual(ps[1], "z")


class TestPlayStringBracketMatching(unittest.TestCase):
    """Test PlayString.index() for finding matching closing brackets."""

    def test_simple_parens(self):
        ps = PlayString("(abc)")
        # Start after '(', look for ')'
        idx = ps.index(")", start=1)
        self.assertEqual(idx, 4)

    def test_nested_parens(self):
        ps = PlayString("((ab)c)")
        idx = ps.index(")", start=1)
        self.assertEqual(idx, 6)

    def test_simple_square_brackets(self):
        ps = PlayString("[xy]")
        idx = ps.index("]", start=1)
        self.assertEqual(idx, 3)

    def test_nested_square_brackets(self):
        ps = PlayString("[x[yz]w]")
        idx = ps.index("]", start=1)
        self.assertEqual(idx, 7)

    def test_simple_curly_braces(self):
        ps = PlayString("{ab}")
        idx = ps.index("}", start=1)
        self.assertEqual(idx, 3)

    def test_nested_curly_braces(self):
        ps = PlayString("{a{bc}d}")
        idx = ps.index("}", start=1)
        self.assertEqual(idx, 7)

    def test_angle_brackets(self):
        ps = PlayString("<ab>")
        idx = ps.index(">", start=1)
        self.assertEqual(idx, 3)

    def test_missing_closing_bracket_raises(self):
        ps = PlayString("(abc")
        with self.assertRaises(ParseError):
            ps.index(")", start=1)

    def test_missing_closing_square_raises(self):
        ps = PlayString("[xyz")
        with self.assertRaises(ParseError):
            ps.index("]", start=1)

    def test_deeply_nested(self):
        ps = PlayString("(((x)))")
        idx = ps.index(")", start=1)
        self.assertEqual(idx, 6)

    def test_mixed_bracket_types(self):
        # Curly inside parens - searching for paren should skip curlies
        ps = PlayString("({ab})")
        idx = ps.index(")", start=1)
        self.assertEqual(idx, 5)


class TestPlayStringNextCharIndex(unittest.TestCase):
    """Test PlayString.next_char_index()."""

    def test_find_pipe(self):
        ps = PlayString("|ab|")
        idx = ps.next_char_index("|", start=1)
        self.assertEqual(idx, 3)

    def test_find_from_start(self):
        ps = PlayString("xyx")
        idx = ps.next_char_index("x", start=0)
        self.assertEqual(idx, 0)

    def test_find_second_occurrence(self):
        ps = PlayString("abcabc")
        idx = ps.next_char_index("a", start=1)
        self.assertEqual(idx, 3)


# ==================================================================
# ParseError
# ==================================================================


class TestParseError(unittest.TestCase):
    """Test ParseError exception."""

    def test_is_exception(self):
        self.assertTrue(issubclass(ParseError, Exception))

    def test_can_raise_and_catch(self):
        with self.assertRaises(ParseError):
            raise ParseError("test error")

    def test_message_preserved(self):
        try:
            raise ParseError("bracket missing")
        except ParseError as e:
            self.assertIn("bracket missing", str(e))


# ==================================================================
# Parse — convert_to_int
# ==================================================================


class TestConvertToInt(unittest.TestCase):
    """Test convert_to_int recursive conversion."""

    def test_int_passthrough(self):
        self.assertEqual(convert_to_int(5), 5)

    def test_float_to_int(self):
        self.assertEqual(convert_to_int(3.7), 3)

    def test_string_digit_to_int(self):
        self.assertEqual(convert_to_int("2"), 2)

    def test_list_recursive(self):
        result = convert_to_int([1.5, 2.9, "3"])
        self.assertEqual(result, [1, 2, 3])

    def test_tuple_recursive(self):
        result = convert_to_int((1.1, 2.2))
        self.assertIsInstance(result, tuple)
        self.assertEqual(result, (1, 2))

    def test_nested_list(self):
        result = convert_to_int([[1.5, 2.5], [3.5]])
        self.assertEqual(result, [[1, 2], [3]])

    def test_mixed_nesting(self):
        result = convert_to_int([1.1, (2.2, 3.3)])
        self.assertEqual(result[0], 1)
        self.assertIsInstance(result[1], tuple)
        self.assertEqual(result[1], (2, 3))


# ==================================================================
# Parse — ParsePlayString / feed
# ==================================================================


class TestParsePlayString(unittest.TestCase):
    """Test ParsePlayString for various input patterns."""

    def test_simple_string(self):
        """Simple characters are returned as list of single chars."""
        result = ParsePlayString("xo")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], "x")
        self.assertEqual(result[1], "o")

    def test_single_char(self):
        result = ParsePlayString("x")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "x")

    def test_empty_string(self):
        result = ParsePlayString("")
        self.assertEqual(len(result), 0)

    def test_parentheses_create_nested_list(self):
        """(ab) creates a nested sub-list."""
        result = ParsePlayString("x(ab)y")
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], "x")
        # The middle element should be a nested list of ['a', 'b']
        self.assertIsInstance(result[1], list)
        self.assertEqual(result[1], ["a", "b"])
        self.assertEqual(result[2], "y")

    def test_square_brackets_create_pgroup_plus(self):
        """[ab] creates a PGroupPlus."""
        result = ParsePlayString("[ab]")
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], PGroupPlus)

    def test_curly_braces_create_prand(self):
        """{ab} creates a PRand generator."""
        result = ParsePlayString("{ab}")
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], PRand)

    def test_angle_brackets_create_pattern(self):
        """<ab> creates a Pattern for layering."""
        result = ParsePlayString("<ab>")
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], Pattern)

    def test_multiple_chars_no_brackets(self):
        result = ParsePlayString("xo-x")
        self.assertEqual(len(result), 4)
        for item in result:
            self.assertIsInstance(item, str)

    def test_empty_parens_raise_error(self):
        with self.assertRaises(ParseError):
            ParsePlayString("()")

    def test_empty_square_brackets_raise_error(self):
        with self.assertRaises(ParseError):
            ParsePlayString("[]")

    def test_empty_curly_braces_raise_error(self):
        with self.assertRaises(ParseError):
            ParsePlayString("{}")

    def test_empty_angle_brackets_raise_error(self):
        with self.assertRaises(ParseError):
            ParsePlayString("<>")

    def test_unmatched_paren_raises_error(self):
        with self.assertRaises(ParseError):
            ParsePlayString("(abc")

    def test_unmatched_square_raises_error(self):
        with self.assertRaises(ParseError):
            ParsePlayString("[abc")

    def test_nested_parens(self):
        """x(a(bc)d)y — nested parens produce nested lists."""
        result = ParsePlayString("x(a(bc)d)y")
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], "x")
        inner = result[1]
        self.assertIsInstance(inner, list)
        # inner should be [a, [b,c], d]
        self.assertEqual(inner[0], "a")
        self.assertIsInstance(inner[1], list)
        self.assertEqual(inner[1], ["b", "c"])
        self.assertEqual(inner[2], "d")
        self.assertEqual(result[2], "y")

    def test_multiple_angle_brackets_layer(self):
        """<ab><cd> — second angle bracket zips with first."""
        result = ParsePlayString("<ab><cd>")
        self.assertEqual(len(result), 1)
        # Should be a zipped Pattern
        self.assertIsInstance(result[0], Pattern)

    def test_complex_string(self):
        """A typical FoxDot play string with mixed brackets."""
        result = ParsePlayString("x[oo](-x)")
        # 'x', PGroupPlus([o,o]), ['-', 'x']
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], "x")
        self.assertIsInstance(result[1], PGroupPlus)
        self.assertIsInstance(result[2], list)

    def test_square_brackets_with_nested_parens(self):
        """[a(bc)] — square brackets with nested parens inside."""
        result = ParsePlayString("[a(bc)]")
        self.assertEqual(len(result), 1)
        # This should produce a list (since contains_nest is True)
        # with PGroupPlus items from cross-product


class TestFeedFunction(unittest.TestCase):
    """Test the feed() function directly."""

    def test_returns_tuple(self):
        result = feed("abc")
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_simple_returns_no_nest(self):
        items, contains_nest = feed("abc")
        self.assertFalse(contains_nest)
        self.assertEqual(len(items), 3)

    def test_parens_set_contains_nest(self):
        items, contains_nest = feed("a(bc)d")
        self.assertTrue(contains_nest)

    def test_angle_brackets_set_contains_nest(self):
        items, contains_nest = feed("<ab>")
        self.assertTrue(contains_nest)

    def test_square_brackets_simple_no_nest(self):
        """[ab] without nested sublists doesn't set contains_nest at outer level."""
        items, contains_nest = feed("[ab]")
        self.assertFalse(contains_nest)

    def test_curly_braces_no_nest(self):
        items, contains_nest = feed("{ab}")
        self.assertFalse(contains_nest)


# ==================================================================
# Parse — arrow_zip
# ==================================================================


class TestArrowZip(unittest.TestCase):
    """Test arrow_zip for merging patterns."""

    def test_simple_zip_two_single_items(self):
        pat1 = Pattern([0, 1])
        pat2 = Pattern([2, 3])
        result = arrow_zip(pat1, pat2)
        self.assertEqual(len(result), 2)

    def test_zip_creates_pgroups_or_tuples(self):
        pat1 = Pattern([0, 1])
        pat2 = Pattern([2, 3])
        result = arrow_zip(pat1, pat2)
        # Each item should be a tuple (since neither is a PGroup)
        for item in result:
            self.assertIsInstance(item, (tuple, PGroup))

    def test_zip_pgroup_extends(self):
        """When one item is a PGroup, it extends."""
        pat1 = Pattern([PGroup([0, 1]), 3])
        pat2 = Pattern([2, 4])
        result = arrow_zip(pat1, pat2)
        # First element: PGroup([0,1]) + 2 => PGroup([0,1,2])
        first = result[0]
        self.assertIsInstance(first, PGroup)
        self.assertEqual(len(first), 3)

    def test_zip_both_pgroups_merge(self):
        pat1 = Pattern([PGroup([0, 1])])
        pat2 = Pattern([PGroup([2, 3])])
        result = arrow_zip(pat1, pat2)
        first = result[0]
        self.assertIsInstance(first, PGroup)
        # Should merge: [0,1] + [2,3] => [0,1,2,3]
        self.assertEqual(len(first), 4)

    def test_zip_different_lengths_uses_lcm(self):
        """LCM-based cycling when patterns differ in length."""
        pat1 = Pattern([0, 1, 2])
        pat2 = Pattern([10, 20])
        result = arrow_zip(pat1, pat2)
        # LCM(3,2) = 6
        self.assertEqual(len(result), 6)

    def test_zip_same_length(self):
        pat1 = Pattern([1, 2, 3])
        pat2 = Pattern([4, 5, 6])
        result = arrow_zip(pat1, pat2)
        self.assertEqual(len(result), 3)


# ==================================================================
# PGroups — PGroupPrime base class
# ==================================================================


class TestPGroupPrime(unittest.TestCase):
    """Test PGroupPrime base class behavior."""

    def test_weight(self):
        pg = PGroupPrime([1, 2, 3])
        self.assertEqual(pg.WEIGHT, 1)

    def test_has_behaviour(self):
        pg = PGroupPrime([1, 2, 3])
        self.assertTrue(pg.has_behaviour())

    def test_data_stored(self):
        pg = PGroupPrime([1, 2, 3])
        self.assertEqual(len(pg), 3)

    def test_get_step(self):
        pg = PGroupPrime([1, 2, 3])
        # dur / len
        step = pg._get_step(1.0)
        self.assertAlmostEqual(step, 1.0 / 3)

    def test_get_delay_passthrough(self):
        pg = PGroupPrime([1, 2])
        self.assertEqual(pg._get_delay(0.5), 0.5)

    def test_change_state_is_noop(self):
        """Base class change_state does nothing."""
        pg = PGroupPrime([1, 2])
        pg.change_state()  # Should not raise


# ==================================================================
# PGroups — PGroupStar
# ==================================================================


class TestPGroupStar(unittest.TestCase):
    """Test PGroupStar (stutter over dur)."""

    def test_bracket_style(self):
        self.assertEqual(PGroupStar.bracket_style, "*()")

    def test_creation(self):
        pg = PGroupStar([1, 2, 3])
        self.assertEqual(len(pg), 3)

    def test_is_pgroup_prime(self):
        pg = PGroupStar([1, 2])
        self.assertIsInstance(pg, PGroupPrime)

    def test_has_behaviour(self):
        pg = PGroupStar([1, 2])
        self.assertTrue(pg.has_behaviour())


# ==================================================================
# PGroups — PGroupPlus
# ==================================================================


class TestPGroupPlus(unittest.TestCase):
    """Test PGroupPlus (stutter over sus)."""

    def test_bracket_style(self):
        self.assertEqual(PGroupPlus.bracket_style, "+()")

    def test_creation(self):
        pg = PGroupPlus([1, 2])
        self.assertEqual(len(pg), 2)

    def test_is_pgroup_prime(self):
        pg = PGroupPlus([1, 2])
        self.assertIsInstance(pg, PGroupPrime)

    def test_get_behaviour_returns_callable(self):
        pg = PGroupPlus([1, 2])
        behaviour = pg.get_behaviour()
        self.assertTrue(callable(behaviour))


# ==================================================================
# PGroups — PGroupPow
# ==================================================================


class TestPGroupPow(unittest.TestCase):
    """Test PGroupPow (shuffled stutter)."""

    def test_bracket_style(self):
        self.assertEqual(PGroupPow.bracket_style, "**()")

    def test_is_pgroup_prime(self):
        pg = PGroupPow([1, 2, 3])
        self.assertIsInstance(pg, PGroupPrime)


# ==================================================================
# PGroups — PGroupDiv
# ==================================================================


class TestPGroupDiv(unittest.TestCase):
    """Test PGroupDiv (alternating stutter)."""

    def test_bracket_style(self):
        self.assertEqual(PGroupDiv.bracket_style, "/()")

    def test_counter_starts_at_zero(self):
        pg = PGroupDiv([1, 2])
        self.assertEqual(pg.counter, 0)

    def test_change_state_increments_counter(self):
        pg = PGroupDiv([1, 2])
        pg.change_state()
        self.assertEqual(pg.counter, 1)
        pg.change_state()
        self.assertEqual(pg.counter, 2)

    def test_even_counter_returns_zero_time(self):
        pg = PGroupDiv([1, 2])
        # counter=0 (even) -> should return 0
        result = pg.calculate_time(1.0)
        self.assertEqual(result, 0)

    def test_odd_counter_returns_stutter_time(self):
        pg = PGroupDiv([1, 2])
        pg.change_state()  # counter=1 (odd)
        result = pg.calculate_time(1.0)
        # Should return a PGroup with delay values
        self.assertIsInstance(result, PGroup)


# ==================================================================
# PGroups — PGroupMod
# ==================================================================


class TestPGroupMod(unittest.TestCase):
    """Test PGroupMod (flattened nested groups)."""

    def test_bracket_style(self):
        self.assertEqual(PGroupMod.bracket_style, "%()")

    def test_is_pgroup_plus(self):
        pg = PGroupMod([1, 2, 3])
        self.assertIsInstance(pg, PGroupPlus)

    def test_iter_flattens(self):
        """PGroupMod should iterate through flattened data."""
        pg = PGroupMod([1, 2, 3])
        items = list(pg)
        self.assertEqual(items, [1, 2, 3])

    def test_iter_flattens_nested_pgroup(self):
        """PGroupMod with nested PGroup should flatten."""
        inner = PGroup([3, 4])
        pg = PGroupMod([1, 2, inner])
        items = list(pg)
        self.assertEqual(items, [1, 2, 3, 4])

    def test_len_counts_flattened(self):
        inner = PGroup([3, 4])
        pg = PGroupMod([1, 2, inner])
        self.assertEqual(len(pg), 4)

    def test_calculate_time_returns_pgroup(self):
        pg = PGroupMod([1, 2, 3])
        result = pg.calculate_time(1.0)
        self.assertIsInstance(result, PGroup)

    def test_calculate_time_length(self):
        pg = PGroupMod([1, 2, 3])
        result = pg.calculate_time(1.0)
        # Should have same number of entries as flattened data
        self.assertEqual(len(result), 3)

    def test_get_step_uses_data_length(self):
        pg = PGroupMod([1, 2, 3])
        # data length is 3
        step = pg._get_step(1.0)
        self.assertAlmostEqual(step, 1.0 / 3)

    def test_get_iter_static_method(self):
        """Test the static get_iter method directly."""
        items = list(PGroupMod.get_iter([1, 2, PGroup([3, 4])]))
        self.assertEqual(items, [1, 2, 3, 4])

    def test_get_iter_deeply_nested(self):
        inner_inner = PGroup([5, 6])
        inner = PGroup([3, 4, inner_inner])
        items = list(PGroupMod.get_iter([1, 2, inner]))
        self.assertEqual(items, [1, 2, 3, 4, 5, 6])


# ==================================================================
# PGroups — PGroupOr
# ==================================================================


class TestPGroupOr(unittest.TestCase):
    """Test PGroupOr (sample value specification from || in play strings)."""

    def test_bracket_style(self):
        self.assertEqual(PGroupOr.bracket_style, "|()")

    def test_is_meta_pgroup_prime(self):
        pg = PGroupOr(["x", 2])
        self.assertIsInstance(pg, metaPGroupPrime)

    def test_data_limited_to_one(self):
        """PGroupOr data should only contain 1 element."""
        pg = PGroupOr(["x", 2])
        self.assertEqual(len(pg.data), 1)

    def test_meta_stores_remainder(self):
        pg = PGroupOr(["x", 2])
        self.assertEqual(len(pg.meta), 1)

    def test_default_none_seq(self):
        pg = PGroupOr()
        self.assertEqual(len(pg.data), 0)

    def test_calculate_sample(self):
        pg = PGroupOr(["x", 2])
        sample = pg.calculate_sample()
        self.assertEqual(sample, 2)

    def test_get_delay_returns_zero(self):
        pg = PGroupOr(["x", 2])
        self.assertEqual(pg._get_delay(0.5), 0)

    def test_get_step_returns_full_dur(self):
        pg = PGroupOr(["x", 2])
        self.assertEqual(pg._get_step(1.0), 1.0)


# ==================================================================
# PGroups — PGroupXor
# ==================================================================


class TestPGroupXor(unittest.TestCase):
    """Test PGroupXor (delay specified by last value)."""

    def test_bracket_style(self):
        self.assertEqual(PGroupXor.bracket_style, "^()")

    def test_is_meta_pgroup_prime(self):
        pg = PGroupXor([1, 2, 0.5])
        self.assertIsInstance(pg, metaPGroupPrime)

    def test_data_and_meta_split(self):
        pg = PGroupXor([1, 2, 0.5])
        # data = [1, 2], meta = [0.5]
        self.assertEqual(list(pg.data), [1, 2])
        self.assertEqual(list(pg.meta), [0.5])

    def test_single_value_becomes_data(self):
        """If only one value, it should be in data with meta=[0]."""
        pg = PGroupXor([5])
        self.assertEqual(list(pg.data), [5])
        self.assertEqual(list(pg.meta), [0])

    def test_get_step_returns_meta(self):
        pg = PGroupXor([1, 2, 0.25])
        self.assertEqual(pg._get_step(1.0), 0.25)

    def test_get_delay_passthrough(self):
        pg = PGroupXor([1, 2, 0.5])
        self.assertEqual(pg._get_delay(0.3), 0.3)

    def test_copy_constructor(self):
        """PGroupXor can be constructed from another PGroupXor."""
        original = PGroupXor([1, 2, 0.5])
        copy = PGroupXor(original)
        self.assertEqual(list(copy.data), list(original.data))
        self.assertEqual(list(copy.meta), list(original.meta))

    def test_default_none_seq(self):
        pg = PGroupXor()
        self.assertIsNotNone(pg.data)


# ==================================================================
# PGroups — metaPGroupPrime
# ==================================================================


class TestMetaPGroupPrime(unittest.TestCase):
    """Test metaPGroupPrime base class."""

    def test_weight(self):
        self.assertEqual(metaPGroupPrime.WEIGHT, 3)

    def test_is_pgroup_prime(self):
        pg = metaPGroupPrime([1, 2])
        self.assertIsInstance(pg, PGroupPrime)


# ==================================================================
# Operations — POperand with Patterns
# ==================================================================


class TestPOperandWithPatterns(unittest.TestCase):
    """Test POperand operations applied to Patterns.

    Note: basic POperand tests exist in test_pattern.py;
    these test additional edge cases and pattern interactions.
    """

    def test_add_empty_pattern(self):
        """Adding to an empty pattern returns the other converted to same class."""
        p = Pattern([])
        result = PAdd(p, Pattern([1, 2, 3]))
        # Empty pattern + other => converts other to Pattern class
        self.assertEqual(len(result), 3)
        self.assertIsInstance(result, Pattern)

    def test_patterns_of_different_length_lcm(self):
        """Operations on patterns of different lengths use LCM."""
        p1 = Pattern([1, 2])
        p2 = Pattern([10, 20, 30])
        result = PAdd(p1, p2)
        # LCM(2,3) = 6
        self.assertEqual(len(result), 6)

    def test_add_result_values(self):
        p1 = Pattern([1, 2, 3])
        p2 = Pattern([10, 20, 30])
        result = PAdd(p1, p2)
        self.assertEqual(list(result), [11, 22, 33])

    def test_sub_result_values(self):
        p1 = Pattern([10, 20, 30])
        p2 = Pattern([1, 2, 3])
        result = PSub(p1, p2)
        self.assertEqual(list(result), [9, 18, 27])

    def test_mul_result_values(self):
        p1 = Pattern([2, 3, 4])
        p2 = Pattern([10, 10, 10])
        result = PMul(p1, p2)
        self.assertEqual(list(result), [20, 30, 40])

    def test_div_result_values(self):
        p1 = Pattern([10, 20, 30])
        p2 = Pattern([2, 5, 10])
        result = PDiv(p1, p2)
        self.assertEqual(list(result), [5.0, 4.0, 3.0])

    def test_div_by_zero_returns_zero(self):
        """Division by zero should return 0, not raise."""
        p1 = Pattern([10])
        p2 = Pattern([0])
        result = PDiv(p1, p2)
        self.assertEqual(list(result), [0])

    def test_peq_equal_patterns(self):
        p1 = Pattern([1, 2, 3])
        p2 = Pattern([1, 2, 3])
        self.assertTrue(PEq(p1, p2))

    def test_peq_unequal_patterns(self):
        p1 = Pattern([1, 2, 3])
        p2 = Pattern([1, 2, 4])
        self.assertFalse(PEq(p1, p2))

    def test_peq_different_lengths(self):
        p1 = Pattern([1, 2])
        p2 = Pattern([1, 2, 3])
        self.assertFalse(PEq(p1, p2))

    def test_peq_different_types(self):
        p1 = Pattern([1, 2])
        self.assertFalse(PEq(p1, [1, 2]))


# ==================================================================
# Integration — Parse with PGroups
# ==================================================================


class TestParseWithPGroups(unittest.TestCase):
    """Test that parsing produces correct PGroup types."""

    def test_square_brackets_produce_pgroup_plus(self):
        result = ParsePlayString("[abc]")
        self.assertIsInstance(result[0], PGroupPlus)
        self.assertEqual(len(result[0]), 3)

    def test_curly_brackets_produce_prand(self):
        result = ParsePlayString("{abc}")
        self.assertIsInstance(result[0], PRand)

    def test_mixed_brackets(self):
        """x[ab]{cd} — produces char, PGroupPlus, PRand."""
        result = ParsePlayString("x[ab]{cd}")
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], "x")
        self.assertIsInstance(result[1], PGroupPlus)
        self.assertIsInstance(result[2], PRand)

    def test_nested_square_parens(self):
        """[(ab)(cd)] — nested parens inside square brackets."""
        result = ParsePlayString("[(ab)(cd)]")
        self.assertEqual(len(result), 1)
        # Should produce a list due to nesting
        self.assertIsInstance(result[0], list)

    def test_typical_drum_pattern(self):
        """Parse a typical FoxDot drum pattern."""
        result = ParsePlayString("x-o-")
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0], "x")
        self.assertEqual(result[1], "-")
        self.assertEqual(result[2], "o")
        self.assertEqual(result[3], "-")

    def test_drum_pattern_with_groups(self):
        """x-o[--] — common stuttered hi-hat pattern."""
        result = ParsePlayString("x-o[--]")
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0], "x")
        self.assertIsInstance(result[3], PGroupPlus)

    def test_drum_with_parens(self):
        """(xo)-o- — alternating kick pattern."""
        result = ParsePlayString("(xo)-o-")
        self.assertEqual(len(result), 4)
        self.assertIsInstance(result[0], list)
        self.assertEqual(result[0], ["x", "o"])


# ==================================================================
# PGroups — Pattern methods (offadd, offmul)
# ==================================================================


class TestPGroupPatternMethods(unittest.TestCase):
    """Test Pattern methods that use PGroups."""

    def test_offadd_returns_pattern(self):
        p = Pattern([0, 1, 2])
        result = p.offadd(1, dur=0.5)
        self.assertIsInstance(result, Pattern)

    def test_offadd_length_preserved(self):
        p = Pattern([0, 1, 2])
        result = p.offadd(1, dur=0.5)
        self.assertEqual(len(result), 3)

    def test_offadd_creates_pgroup_xor(self):
        """Each element should become a PGroup with offset value."""
        p = Pattern([0, 1])
        result = p.offadd(10, dur=0.5)
        for item in result:
            self.assertIsInstance(item, PGroup)

    def test_offmul_returns_pattern(self):
        p = Pattern([1, 2, 3])
        result = p.offmul(2, dur=0.5)
        self.assertIsInstance(result, Pattern)

    def test_offmul_creates_pgroup_xor(self):
        p = Pattern([1, 2])
        result = p.offmul(2, dur=0.5)
        for item in result:
            self.assertIsInstance(item, PGroup)

    def test_amen_returns_pattern(self):
        p = Pattern(["x", "-", "o", "-"])
        result = p.amen(size=2)
        self.assertIsInstance(result, Pattern)

    def test_amen_length(self):
        p = Pattern(["x", "-", "o", "-"])
        result = p.amen(size=2)
        # amen produces nested lists that get flattened by Pattern constructor
        self.assertGreater(len(result), 0)

    def test_bubble_returns_pattern(self):
        p = Pattern(["x", "-", "o", "-"])
        result = p.bubble(size=2)
        self.assertIsInstance(result, Pattern)

    def test_bubble_length(self):
        p = Pattern(["x", "-", "o", "-"])
        result = p.bubble(size=2)
        # bubble produces nested lists that get flattened by Pattern constructor
        self.assertGreater(len(result), 0)


# ==================================================================
# PGroups — Edge cases
# ==================================================================


class TestPGroupEdgeCases(unittest.TestCase):
    """Test edge cases for PGroup subclasses."""

    def test_pgroup_prime_empty(self):
        pg = PGroupPrime([])
        self.assertEqual(len(pg), 0)

    def test_pgroup_plus_single_element(self):
        pg = PGroupPlus([1])
        self.assertEqual(len(pg), 1)
        self.assertTrue(pg.has_behaviour())

    def test_pgroup_div_alternation(self):
        """PGroupDiv alternates between zero and stutter on each access."""
        pg = PGroupDiv([1, 2])
        # Even counter (0): zero
        self.assertEqual(pg.calculate_time(1.0), 0)
        pg.change_state()
        # Odd counter (1): stutter
        result = pg.calculate_time(1.0)
        self.assertIsInstance(result, PGroup)

    def test_pgroup_xor_two_elements(self):
        """Two elements: first is data, second is meta (delay)."""
        pg = PGroupXor([5, 0.25])
        self.assertEqual(list(pg.data), [5])
        self.assertEqual(list(pg.meta), [0.25])

    def test_pgroup_or_with_pgroup_sample(self):
        """PGroupOr where the meta is a PGroup."""
        inner = PGroup([1, 2])
        pg = PGroupOr(["x", inner])
        sample = pg.calculate_sample()
        self.assertIsInstance(sample, PGroup)

    def test_pgroup_mod_empty_data(self):
        pg = PGroupMod([])
        self.assertEqual(len(pg), 0)
        self.assertEqual(list(pg), [])

    def test_pgroup_star_inherits_prime(self):
        self.assertTrue(issubclass(PGroupStar, PGroupPrime))

    def test_pgroup_pow_inherits_prime(self):
        self.assertTrue(issubclass(PGroupPow, PGroupPrime))

    def test_pgroup_div_inherits_prime(self):
        self.assertTrue(issubclass(PGroupDiv, PGroupPrime))

    def test_pgroup_mod_inherits_plus(self):
        self.assertTrue(issubclass(PGroupMod, PGroupPlus))

    def test_pgroup_or_inherits_meta_prime(self):
        self.assertTrue(issubclass(PGroupOr, metaPGroupPrime))

    def test_pgroup_xor_inherits_meta_prime(self):
        self.assertTrue(issubclass(PGroupXor, metaPGroupPrime))


if __name__ == "__main__":
    unittest.main()
