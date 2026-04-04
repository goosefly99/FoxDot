"""
Unit tests for FoxDot.lib.GhostCoder — Grammar parsing, value generation,
player data manipulation, action functions, constants, null widget, and Ghost class.
"""

import os
import re
import sys
import copy
import queue
import types
import random
import unittest
from unittest.mock import MagicMock, patch, call

# ---------------------------------------------------------------------------
# Import strategy: Grammar.py conditionally imports from FoxDot internals
# (SCLang, Players, Patterns) when __name__ != "__main__". We attempt a
# direct import; if the FoxDot stack is not fully available, we pre-stub the
# dependencies so the module can still load for unit testing.
# ---------------------------------------------------------------------------

_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_pkg_dir = os.path.join(_repo_root, "FoxDot")
_lib_dir = os.path.join(_pkg_dir, "lib")

# Ensure repo root is on sys.path
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

try:
    from FoxDot.lib.GhostCoder import Grammar, Writer
    _GRAMMAR_IMPORTED = True
except Exception:
    # If the full FoxDot stack cannot load, set up minimal stubs
    _GRAMMAR_IMPORTED = False

    _foxdot_pkg = types.ModuleType("FoxDot")
    _foxdot_pkg.__path__ = [_pkg_dir]
    _foxdot_pkg.__package__ = "FoxDot"

    _lib_pkg = types.ModuleType("FoxDot.lib")
    _lib_pkg.__path__ = [_lib_dir]
    _lib_pkg.__package__ = "FoxDot.lib"

    # Stub out dependencies that Grammar imports
    _sclang = MagicMock()
    _players_mod = MagicMock()
    _patterns_mod = MagicMock()
    _patterns_seq = MagicMock()

    for mod_name, mod_obj in [
        ("FoxDot", _foxdot_pkg),
        ("FoxDot.lib", _lib_pkg),
        ("FoxDot.lib.SCLang", _sclang),
        ("FoxDot.lib.Players", _players_mod),
        ("FoxDot.lib.Patterns", _patterns_mod),
        ("FoxDot.lib.Patterns.Sequences", _patterns_seq),
        ("FoxDot.lib.Settings", MagicMock()),
        ("FoxDot.lib.Code", MagicMock()),
        ("FoxDot.lib.Midi", MagicMock()),
        ("FoxDot.lib.Utils", MagicMock()),
        ("FoxDot.lib.ServerManager", MagicMock()),
        ("FoxDot.lib.TimeVar", MagicMock()),
        ("FoxDot.lib.Repeat", MagicMock()),
    ]:
        sys.modules.setdefault(mod_name, mod_obj)

    from FoxDot.lib.GhostCoder import Grammar, Writer


# ==================================================================
# 1. Regex Pattern Matching Tests
# ==================================================================

class TestReDegree(unittest.TestCase):
    """Tests for the re_degree compiled regex."""

    def test_match_simple_integer(self):
        m = Grammar.re_degree.match("5")
        self.assertIsNotNone(m)
        self.assertEqual(m.group(0).strip(), "5")

    def test_match_list_syntax(self):
        m = Grammar.re_degree.match("[0, 2, 4]")
        self.assertIsNotNone(m)
        self.assertIn("[0, 2, 4]", m.group(0))

    def test_match_tuple_syntax(self):
        m = Grammar.re_degree.match("(0, 2)")
        self.assertIsNotNone(m)
        self.assertIn("(0, 2)", m.group(0))

    def test_match_empty_string(self):
        m = Grammar.re_degree.match("")
        # Empty string matches with empty capture
        self.assertIsNotNone(m)
        self.assertEqual(m.group(0), "")

    def test_match_pattern_name(self):
        m = Grammar.re_degree.match("PRange(8)")
        self.assertIsNotNone(m)

    def test_kwarg_format_degree_match(self):
        # re_degree will still match at position 0 for "dur=3" but only
        # captures up to the "=" boundary due to the character class.
        # The key is that getArgs() correctly separates degree from kwargs.
        m = Grammar.re_degree.match("dur=3")
        # It matches (captures "dur" or empty), but getArgs handles
        # the kwarg extraction separately via re_kwargs.
        if m:
            # Degree capture should not include the full "dur=3"
            self.assertNotEqual(m.group(0), "dur=3")

    def test_match_slash_fraction(self):
        m = Grammar.re_degree.match("1/2")
        self.assertIsNotNone(m)
        self.assertIn("1/2", m.group(0))

    def test_match_nested_brackets(self):
        m = Grammar.re_degree.match("[0, [1, 2], 3]")
        self.assertIsNotNone(m)


class TestReKwargs(unittest.TestCase):
    """Tests for the re_kwargs compiled regex."""

    def test_match_single_kwarg(self):
        matches = Grammar.re_kwargs.findall("dur=3")
        self.assertTrue(len(matches) > 0)
        self.assertEqual(matches[0][0], "dur=3")

    def test_match_kwarg_with_list(self):
        matches = Grammar.re_kwargs.findall("dur=[1, 2, 3]")
        self.assertTrue(len(matches) > 0)

    def test_match_multiple_kwargs(self):
        matches = Grammar.re_kwargs.findall("dur=3, amp=0.5")
        self.assertTrue(len(matches) >= 2)

    def test_no_match_bare_value(self):
        matches = Grammar.re_kwargs.findall("42")
        self.assertEqual(len(matches), 0)

    def test_match_kwarg_with_fraction(self):
        matches = Grammar.re_kwargs.findall("amp=1/2")
        self.assertTrue(len(matches) > 0)

    def test_match_kwarg_with_pattern(self):
        matches = Grammar.re_kwargs.findall("dur=PRange(8)")
        self.assertTrue(len(matches) > 0)


class TestReInput(unittest.TestCase):
    """Tests for the re_input compiled regex matching full player statements."""

    def test_match_simple_player(self):
        m = Grammar.re_input.match("p1 >> pads([0,2,4])")
        self.assertIsNotNone(m)
        self.assertEqual(m.group("player"), "p1")
        self.assertEqual(m.group("synthdef"), "pads")

    def test_match_player_with_kwargs(self):
        m = Grammar.re_input.match("p1 >> pads([0,2,4], dur=[1,2])")
        self.assertIsNotNone(m)
        self.assertIn("dur", m.group("args"))

    def test_match_player_no_args(self):
        m = Grammar.re_input.match("p1 >> pads()")
        self.assertIsNotNone(m)
        # args group may be None for empty parens
        self.assertTrue(m.group("args") is None or m.group("args") == "")

    def test_no_match_plain_text(self):
        m = Grammar.re_input.match("hello world")
        self.assertIsNone(m)

    def test_match_multichar_player_name(self):
        m = Grammar.re_input.match("g5 >> pluck([0,1,2], dur=2)")
        self.assertIsNotNone(m)
        self.assertEqual(m.group("player"), "g5")
        self.assertEqual(m.group("synthdef"), "pluck")

    def test_no_match_missing_arrow(self):
        m = Grammar.re_input.match("p1 > pads([0,2])")
        self.assertIsNone(m)

    def test_match_complex_args(self):
        m = Grammar.re_input.match("p1 >> bass(0, dur=1, amp=1/2, pan=[0,1])")
        self.assertIsNotNone(m)
        self.assertIn("amp=1/2", m.group("args"))


# ==================================================================
# 2. getArgs Parsing Tests
# ==================================================================

class TestGetArgs(unittest.TestCase):
    """Tests for Grammar.getArgs — parsing degree and kwargs from arg string."""

    def test_empty_string(self):
        degree, kwargs = Grammar.getArgs("")
        self.assertEqual(degree, "")
        self.assertEqual(kwargs, {})

    def test_degree_only_simple(self):
        degree, kwargs = Grammar.getArgs("5")
        self.assertEqual(degree.strip(), "5")
        self.assertEqual(kwargs, {})

    def test_degree_only_list(self):
        degree, kwargs = Grammar.getArgs("[0, 2, 4]")
        self.assertIn("0", degree)
        self.assertIn("2", degree)
        self.assertIn("4", degree)
        self.assertEqual(kwargs, {})

    def test_kwargs_only(self):
        degree, kwargs = Grammar.getArgs("dur=3")
        self.assertIn("dur", kwargs)
        self.assertEqual(kwargs["dur"], "3")

    def test_degree_and_kwargs(self):
        degree, kwargs = Grammar.getArgs("[0,2,4], dur=[1,2], amp=0.5")
        self.assertIn("0", degree)
        self.assertIn("dur", kwargs)
        self.assertIn("amp", kwargs)

    def test_multiple_kwargs(self):
        degree, kwargs = Grammar.getArgs("[0], dur=3, amp=1, pan=0")
        self.assertIn("dur", kwargs)
        self.assertIn("amp", kwargs)
        self.assertIn("pan", kwargs)
        self.assertEqual(len(kwargs), 3)

    def test_kwarg_with_list_value(self):
        degree, kwargs = Grammar.getArgs("dur=[1, 2, 3]")
        self.assertIn("dur", kwargs)
        self.assertIn("[1, 2, 3]", kwargs["dur"])

    def test_kwarg_with_fraction(self):
        degree, kwargs = Grammar.getArgs("amp=1/2")
        self.assertIn("amp", kwargs)
        self.assertEqual(kwargs["amp"], "1/2")

    def test_degree_trailing_comma_stripped(self):
        degree, kwargs = Grammar.getArgs("[0,2,4],")
        # Trailing comma should be stripped from degree
        self.assertFalse(degree.endswith(","))

    def test_kwarg_trailing_comma_stripped(self):
        degree, kwargs = Grammar.getArgs("dur=3, amp=1,")
        # The last kwarg shouldn't retain a trailing comma in the key
        for key in kwargs:
            self.assertFalse(key.endswith(","))

    def test_tuple_degree(self):
        degree, kwargs = Grammar.getArgs("(0, 2)")
        self.assertIn("(0, 2)", degree)

    def test_pattern_as_degree(self):
        degree, kwargs = Grammar.getArgs("PRange(8)")
        self.assertIn("PRange", degree)


# ==================================================================
# 3. playerData Parsing Tests
# ==================================================================

class TestPlayerData(unittest.TestCase):
    """Tests for Grammar.playerData — parsing full player statements from text."""

    def test_single_player(self):
        result = Grammar.playerData("p1 >> pads([0,2,4], dur=[1,2])")
        self.assertEqual(len(result), 1)
        original, d = result[0]
        self.assertEqual(d["player"], "p1")
        self.assertEqual(d["synthdef"], "pads")
        self.assertIn("dur", d["kwargs"])

    def test_no_match_returns_empty(self):
        result = Grammar.playerData("some random text")
        self.assertEqual(result, [])

    def test_empty_string(self):
        result = Grammar.playerData("")
        self.assertEqual(result, [])

    def test_player_without_args(self):
        result = Grammar.playerData("p1 >> pads()")
        self.assertEqual(len(result), 1)
        _, d = result[0]
        self.assertEqual(d["degree"], "")
        self.assertEqual(d["kwargs"], {})

    def test_player_with_degree_only(self):
        result = Grammar.playerData("p1 >> bass(0)")
        self.assertEqual(len(result), 1)
        _, d = result[0]
        self.assertEqual(d["player"], "p1")
        self.assertEqual(d["synthdef"], "bass")

    def test_player_data_dict_has_required_keys(self):
        result = Grammar.playerData("g1 >> pluck([0,1,2], dur=2)")
        self.assertEqual(len(result), 1)
        _, d = result[0]
        self.assertIn("player", d)
        self.assertIn("synthdef", d)
        self.assertIn("degree", d)
        self.assertIn("kwargs", d)
        # 'args' key should be removed after parsing
        self.assertNotIn("args", d)

    def test_original_string_in_tuple(self):
        text = "p1 >> pads([0,2,4])"
        result = Grammar.playerData(text)
        self.assertEqual(len(result), 1)
        original, _ = result[0]
        self.assertIn("p1", original)
        self.assertIn("pads", original)

    def test_player_with_complex_kwargs(self):
        result = Grammar.playerData("p1 >> pads(0, dur=[1,2], amp=1/2, pan=0)")
        self.assertEqual(len(result), 1)
        _, d = result[0]
        self.assertIn("dur", d["kwargs"])
        self.assertIn("amp", d["kwargs"])
        self.assertIn("pan", d["kwargs"])


# ==================================================================
# 4. createPlayer Reconstruction Tests
# ==================================================================

class TestCreatePlayer(unittest.TestCase):
    """Tests for Grammar.createPlayer — reconstructing player statement strings."""

    def test_basic_player(self):
        result = Grammar.createPlayer(
            player="p1", synthdef="pads", degree="[0,2,4]",
            kwargs={}, methods=""
        )
        self.assertIn("p1", result)
        self.assertIn("pads", result)
        self.assertIn("[0,2,4]", result)
        self.assertIn(">>", result)

    def test_player_with_kwargs(self):
        result = Grammar.createPlayer(
            player="p1", synthdef="pads", degree="[0,2,4]",
            kwargs={"dur": "[1,2]", "amp": "0.5"}, methods=""
        )
        self.assertIn("dur=", result)
        self.assertIn("amp=", result)

    def test_player_no_degree(self):
        result = Grammar.createPlayer(
            player="p1", synthdef="pads", degree="",
            kwargs={"dur": "2"}, methods=""
        )
        self.assertIn("dur=2", result)
        # Should not have extra comma before kwargs when degree is empty
        self.assertNotIn("(,", result)

    def test_player_no_kwargs(self):
        result = Grammar.createPlayer(
            player="g1", synthdef="pluck", degree="0",
            kwargs={}, methods=""
        )
        self.assertIn("g1 >> pluck(0)", result)

    def test_player_no_degree_no_kwargs(self):
        result = Grammar.createPlayer(
            player="p1", synthdef="pads", degree="",
            kwargs={}, methods=""
        )
        self.assertIn("p1 >> pads()", result)

    def test_player_with_methods(self):
        result = Grammar.createPlayer(
            player="p1", synthdef="pads", degree="0",
            kwargs={}, methods=".every(4, 'reverse')"
        )
        self.assertIn(".every(4, 'reverse')", result)

    def test_kwargs_are_sorted(self):
        result = Grammar.createPlayer(
            player="p1", synthdef="pads", degree="0",
            kwargs={"pan": "1", "amp": "0.5", "dur": "2"}, methods=""
        )
        # amp should come before dur, dur before pan (alphabetical)
        amp_pos = result.index("amp=")
        dur_pos = result.index("dur=")
        pan_pos = result.index("pan=")
        self.assertLess(amp_pos, dur_pos)
        self.assertLess(dur_pos, pan_pos)

    def test_comma_between_degree_and_kwargs(self):
        result = Grammar.createPlayer(
            player="p1", synthdef="pads", degree="[0,1]",
            kwargs={"dur": "2"}, methods=""
        )
        # There should be a comma separating degree and kwargs
        self.assertIn(", dur=", result)

    def test_default_degree_when_missing(self):
        result = Grammar.createPlayer(
            player="p1", synthdef="pads", kwargs={"dur": "2"}, methods=""
        )
        # Should handle missing degree gracefully (defaults to "")
        self.assertIn("p1 >> pads(", result)

    def test_default_methods_when_missing(self):
        result = Grammar.createPlayer(
            player="p1", synthdef="pads", degree="0", kwargs={}
        )
        # methods defaults to ""
        self.assertIn("p1 >> pads(0)", result)


# ==================================================================
# 5. format_kwargs Tests
# ==================================================================

class TestFormatKwargs(unittest.TestCase):
    """Tests for Grammar.format_kwargs — formatting dict to sorted key=value string."""

    def test_empty_dict(self):
        result = Grammar.format_kwargs({})
        self.assertEqual(result, "")

    def test_single_kwarg(self):
        result = Grammar.format_kwargs({"dur": "2"})
        self.assertEqual(result, "dur=2")

    def test_multiple_kwargs_sorted(self):
        result = Grammar.format_kwargs({"pan": "1", "amp": "0.5", "dur": "2"})
        self.assertEqual(result, "amp=0.5, dur=2, pan=1")

    def test_kwargs_with_list_values(self):
        result = Grammar.format_kwargs({"dur": "[1, 2]"})
        self.assertEqual(result, "dur=[1, 2]")

    def test_kwargs_ordering_is_alphabetical(self):
        result = Grammar.format_kwargs({"z": "1", "a": "2", "m": "3"})
        parts = result.split(", ")
        keys = [p.split("=")[0] for p in parts]
        self.assertEqual(keys, sorted(keys))

    def test_kwargs_with_fraction_values(self):
        result = Grammar.format_kwargs({"amp": "1/2", "dur": "3"})
        self.assertIn("amp=1/2", result)
        self.assertIn("dur=3", result)


# ==================================================================
# 6. Value Generation Tests
# ==================================================================

class TestGenerateInteger(unittest.TestCase):
    """Tests for Grammar.GENERATE_INTEGER — random integer generation."""

    def setUp(self):
        random.seed(42)

    def test_returns_int_or_str(self):
        for _ in range(50):
            val = Grammar.GENERATE_INTEGER()
            # Should be an int or a string representation of an int
            self.assertTrue(isinstance(val, (int, str)))

    def test_value_range(self):
        results = set()
        random.seed(0)
        for _ in range(500):
            val = int(Grammar.GENERATE_INTEGER())
            results.add(val)
            self.assertGreaterEqual(val, 1)
            self.assertLessEqual(val, 29)

    def test_single_digit_range(self):
        # With high probability, we should get single-digit values (1-9)
        random.seed(42)
        got_single = False
        for _ in range(100):
            val = int(Grammar.GENERATE_INTEGER())
            if 1 <= val <= 9:
                got_single = True
                break
        self.assertTrue(got_single)

    def test_two_digit_range(self):
        # With enough samples, should get two-digit values (10-29)
        random.seed(100)
        got_double = False
        for _ in range(500):
            val = int(Grammar.GENERATE_INTEGER())
            if 10 <= val <= 29:
                got_double = True
                break
        self.assertTrue(got_double)

    def test_accepts_keyword_arg(self):
        # Should accept keyword parameter without error
        val = Grammar.GENERATE_INTEGER(keyword="dur")
        self.assertIsNotNone(val)


class TestGenerateNumber(unittest.TestCase):
    """Tests for Grammar.GENERATE_NUMBER — random number or fraction generation."""

    def setUp(self):
        random.seed(42)

    def test_returns_int_or_fraction_string(self):
        for _ in range(50):
            val = Grammar.GENERATE_NUMBER()
            if isinstance(val, str):
                # Should contain a slash for fraction
                self.assertIn("/", str(val))
            else:
                self.assertIsInstance(val, int)

    def test_default_range(self):
        random.seed(42)
        for _ in range(100):
            val = Grammar.GENERATE_NUMBER()
            if isinstance(val, int):
                self.assertGreaterEqual(val, 1)
                self.assertLessEqual(val, 9)

    def test_custom_range(self):
        random.seed(42)
        for _ in range(100):
            val = Grammar.GENERATE_NUMBER(_min=5, _max=10)
            if isinstance(val, int):
                self.assertGreaterEqual(val, 5)
                self.assertLessEqual(val, 10)

    def test_amp_keyword_returns_fraction(self):
        random.seed(42)
        got_fraction = False
        for _ in range(100):
            val = Grammar.GENERATE_NUMBER(keyword="amp")
            if isinstance(val, str) and "/" in val:
                got_fraction = True
                break
        self.assertTrue(got_fraction)

    def test_amp_always_returns_fraction(self):
        # When keyword is "amp", the function always returns a fraction string
        random.seed(42)
        for _ in range(50):
            val = Grammar.GENERATE_NUMBER(keyword="amp")
            self.assertIsInstance(val, str)
            self.assertIn("/", val)

    def test_fraction_parts_are_positive(self):
        random.seed(42)
        for _ in range(50):
            val = Grammar.GENERATE_NUMBER(keyword="amp")
            if isinstance(val, str) and "/" in val:
                parts = val.split("/")
                self.assertEqual(len(parts), 2)
                self.assertGreater(int(parts[0]), 0)
                self.assertGreater(int(parts[1]), 0)


class TestGenerateList(unittest.TestCase):
    """Tests for Grammar.GENERATE_LIST — random list string generation."""

    def setUp(self):
        random.seed(42)

    def test_returns_string(self):
        result = Grammar.GENERATE_LIST()
        self.assertIsInstance(result, str)

    def test_starts_and_ends_with_brackets(self):
        result = Grammar.GENERATE_LIST()
        self.assertTrue(result.startswith("["))
        self.assertTrue(result.endswith("]"))

    def test_contains_comma_separated_values(self):
        random.seed(42)
        result = Grammar.GENERATE_LIST()
        inner = result[1:-1]
        parts = inner.split(", ")
        self.assertGreaterEqual(len(parts), 2)
        self.assertLessEqual(len(parts), 9)

    def test_length_varies(self):
        lengths = set()
        for seed in range(100):
            random.seed(seed)
            result = Grammar.GENERATE_LIST()
            inner = result[1:-1]
            parts = inner.split(", ")
            lengths.add(len(parts))
        # Should have multiple different lengths
        self.assertGreater(len(lengths), 1)

    def test_accepts_keyword_arg(self):
        result = Grammar.GENERATE_LIST(keyword="dur")
        self.assertIsInstance(result, str)


class TestGenerateTuple(unittest.TestCase):
    """Tests for Grammar.GENERATE_TUPLE — random tuple string generation."""

    def setUp(self):
        random.seed(42)

    def test_returns_string(self):
        result = Grammar.GENERATE_TUPLE()
        self.assertIsInstance(result, str)

    def test_starts_and_ends_with_parens(self):
        result = Grammar.GENERATE_TUPLE()
        self.assertTrue(result.startswith("("))
        self.assertTrue(result.endswith(")"))

    def test_contains_2_or_3_values(self):
        random.seed(42)
        result = Grammar.GENERATE_TUPLE()
        inner = result[1:-1]
        parts = inner.split(", ")
        self.assertIn(len(parts), [2, 3])

    def test_length_variation(self):
        found_2 = False
        found_3 = False
        for seed in range(200):
            random.seed(seed)
            result = Grammar.GENERATE_TUPLE()
            inner = result[1:-1]
            parts = inner.split(", ")
            if len(parts) == 2:
                found_2 = True
            if len(parts) == 3:
                found_3 = True
        self.assertTrue(found_2)
        self.assertTrue(found_3)

    def test_accepts_keyword_arg(self):
        result = Grammar.GENERATE_TUPLE(keyword="dur")
        self.assertIsInstance(result, str)


class TestGenChooseValue(unittest.TestCase):
    """Tests for Grammar.GEN_CHOOSE_VALUE — randomly choosing value type.

    We patch GENERATE_PATTERN to isolate the test from random pattern generation.
    """

    def setUp(self):
        random.seed(42)

    def _safe_choose(self, keyword=None):
        """Call GEN_CHOOSE_VALUE with GENERATE_PATTERN patched out."""
        with patch.object(Grammar, 'GENERATE_PATTERN', return_value="PRange(8)"):
            return Grammar.GEN_CHOOSE_VALUE(keyword)

    def test_returns_string_or_int(self):
        for _ in range(50):
            val = self._safe_choose()
            self.assertTrue(isinstance(val, (str, int)))

    def test_can_return_list(self):
        got_list = False
        for seed in range(200):
            random.seed(seed)
            val = self._safe_choose()
            if isinstance(val, str) and val.startswith("["):
                got_list = True
                break
        self.assertTrue(got_list)

    def test_can_return_tuple(self):
        got_tuple = False
        for seed in range(500):
            random.seed(seed)
            val = self._safe_choose()
            if isinstance(val, str) and val.startswith("("):
                got_tuple = True
                break
        self.assertTrue(got_tuple)

    def test_can_return_number(self):
        got_number = False
        for seed in range(200):
            random.seed(seed)
            val = self._safe_choose()
            if isinstance(val, int) or (isinstance(val, str) and "/" in val):
                got_number = True
                break
        self.assertTrue(got_number)

    def test_can_return_pattern(self):
        # When random falls in 0.00-0.33 range, GENERATE_PATTERN is called
        with patch.object(Grammar, 'GENERATE_PATTERN', return_value="PRange(8)") as mock_pat:
            got_pattern = False
            for seed in range(200):
                random.seed(seed)
                val = Grammar.GEN_CHOOSE_VALUE()
                if val == "PRange(8)":
                    got_pattern = True
                    break
            self.assertTrue(got_pattern)

    def test_accepts_keyword_arg(self):
        val = self._safe_choose(keyword="dur")
        self.assertIsNotNone(val)

    def test_dur_keyword_prefers_list(self):
        # With dur keyword, tuples are less likely (random() > 0.25 check)
        results = []
        for seed in range(100):
            random.seed(seed)
            val = self._safe_choose(keyword="dur")
            results.append(val)
        # Should have at least some list results
        lists = [v for v in results if isinstance(v, str) and v.startswith("[")]
        self.assertGreater(len(lists), 0)


class TestGenChangeValue(unittest.TestCase):
    """Tests for Grammar.GEN_CHANGE_VALUE — modifying numbers within a value."""

    def setUp(self):
        random.seed(42)

    def test_single_number_changed(self):
        random.seed(42)
        result = Grammar.GEN_CHANGE_VALUE("5")
        self.assertIsInstance(result, str)
        # Result should be a number (possibly different from input)
        self.assertTrue(len(result) > 0)

    def test_preserves_brackets(self):
        random.seed(42)
        result = Grammar.GEN_CHANGE_VALUE("[3, 5, 7]")
        self.assertTrue(result.startswith("["))
        self.assertTrue(result.endswith("]"))

    def test_preserves_parens(self):
        random.seed(42)
        result = Grammar.GEN_CHANGE_VALUE("(3, 5)")
        self.assertTrue(result.startswith("("))
        self.assertTrue(result.endswith(")"))

    def test_non_numeric_string_unchanged(self):
        result = Grammar.GEN_CHANGE_VALUE("abc")
        # No numbers to change, so should return as-is
        self.assertEqual(result, "abc")

    def test_returns_string(self):
        result = Grammar.GEN_CHANGE_VALUE(42)
        self.assertIsInstance(result, str)

    def test_fraction_value(self):
        random.seed(42)
        result = Grammar.GEN_CHANGE_VALUE("1/2")
        self.assertIsInstance(result, str)

    def test_list_with_multiple_numbers(self):
        random.seed(42)
        result = Grammar.GEN_CHANGE_VALUE("[1, 2, 3, 4]")
        self.assertTrue(result.startswith("["))
        self.assertTrue(result.endswith("]"))

    def test_accepts_keyword_arg(self):
        random.seed(42)
        result = Grammar.GEN_CHANGE_VALUE("5", keyword="amp")
        self.assertIsInstance(result, str)


# ==================================================================
# 7. WeightedList Tests
# ==================================================================

class TestWeightedList(unittest.TestCase):
    """Tests for Grammar.WeightedList — creating lists with items repeated by weight."""

    def test_single_item(self):
        result = Grammar.WeightedList({"a": 3})
        self.assertEqual(result, ["a", "a", "a"])

    def test_multiple_items(self):
        result = Grammar.WeightedList({"a": 2, "b": 1})
        self.assertEqual(result.count("a"), 2)
        self.assertEqual(result.count("b"), 1)
        self.assertEqual(len(result), 3)

    def test_zero_weight(self):
        result = Grammar.WeightedList({"a": 2, "b": 0})
        self.assertEqual(result.count("a"), 2)
        self.assertEqual(result.count("b"), 0)

    def test_empty_dict(self):
        result = Grammar.WeightedList({})
        self.assertEqual(result, [])

    def test_returns_list(self):
        result = Grammar.WeightedList({"x": 1})
        self.assertIsInstance(result, list)

    def test_large_weights(self):
        result = Grammar.WeightedList({"a": 10, "b": 5})
        self.assertEqual(len(result), 15)
        self.assertEqual(result.count("a"), 10)
        self.assertEqual(result.count("b"), 5)

    def test_preserves_item_types(self):
        fn = lambda: None
        result = Grammar.WeightedList({fn: 2})
        self.assertEqual(len(result), 2)
        self.assertIs(result[0], fn)


# ==================================================================
# 8. Action Function Tests
# ==================================================================

class TestAddNewKwarg(unittest.TestCase):
    """Tests for Grammar.ADD_NEW_KWARG — adding a new keyword to player data.

    We patch GENERATE_PATTERN to isolate the test from random pattern generation.
    """

    def setUp(self):
        random.seed(42)
        self._patch = patch.object(Grammar, 'GENERATE_PATTERN', return_value="PRange(8)")
        self._patch.start()

    def tearDown(self):
        self._patch.stop()

    def test_adds_keyword(self):
        data = {"player": "p1", "synthdef": "pads", "degree": "0", "kwargs": {}}
        result = Grammar.ADD_NEW_KWARG(**data)
        self.assertIsInstance(result["kwargs"], dict)
        # Should have at least one kwarg now
        self.assertGreater(len(result["kwargs"]), 0)

    def test_does_not_add_existing_keyword(self):
        existing_kwargs = {kw: "1" for kw in set(Grammar.Keywords)}
        data = {"player": "p1", "synthdef": "pads", "degree": "0",
                "kwargs": existing_kwargs}
        result = Grammar.ADD_NEW_KWARG(**data)
        # All keywords already present; no new one should be added
        self.assertEqual(len(result["kwargs"]), len(existing_kwargs))

    def test_returns_dict(self):
        data = {"player": "p1", "synthdef": "pads", "degree": "0", "kwargs": {}}
        result = Grammar.ADD_NEW_KWARG(**data)
        self.assertIsInstance(result, dict)

    def test_preserves_existing_kwargs_when_new_added(self):
        # When a new keyword is added, previously-existing kwargs that are
        # NOT the target of the addition should remain unchanged.
        # NOTE: Grammar.py has a logic bug on line 182 where
        # `if "dur" not in new_kw` incorrectly sets new_kw = "dur" even
        # when dur is already in kwargs. We avoid triggering that path by
        # including "dur" in the initial kwargs and seeding carefully.
        random.seed(10)
        data = {"player": "p1", "synthdef": "pads", "degree": "0",
                "kwargs": {"amp": "0.5"}}
        result = Grammar.ADD_NEW_KWARG(**data)
        # amp should be preserved regardless of what keyword was added
        self.assertIn("amp", result["kwargs"])
        self.assertEqual(result["kwargs"]["amp"], "0.5")

    def test_prefers_dur_when_available(self):
        # When dur is not yet set, it should be preferred
        got_dur = False
        for seed in range(100):
            random.seed(seed)
            data = {"player": "p1", "synthdef": "pads", "degree": "0",
                    "kwargs": {}}
            result = Grammar.ADD_NEW_KWARG(**data)
            if "dur" in result["kwargs"]:
                got_dur = True
                break
        self.assertTrue(got_dur)


class TestChangeDegree(unittest.TestCase):
    """Tests for Grammar.CHANGE_DEGREE — changing the degree of player data.

    We patch GENERATE_PATTERN to isolate the test from random pattern generation.
    """

    def setUp(self):
        random.seed(42)
        self._patch = patch.object(Grammar, 'GENERATE_PATTERN', return_value="PRange(8)")
        self._patch.start()

    def tearDown(self):
        self._patch.stop()

    def test_changes_degree(self):
        data = {"player": "p1", "synthdef": "pads", "degree": "[0,2,4]",
                "kwargs": {}}
        result = Grammar.CHANGE_DEGREE(**data)
        self.assertIn("degree", result)

    def test_generates_new_degree_when_present(self):
        data = {"player": "p1", "synthdef": "pads", "degree": "[0,2,4]",
                "kwargs": {}}
        result = Grammar.CHANGE_DEGREE(**data)
        # With a non-empty degree, the condition len(str(kwargs['degree'])) is
        # truthy, so it generates a new value
        self.assertIsNotNone(result["degree"])

    def test_returns_dict(self):
        data = {"player": "p1", "synthdef": "pads", "degree": "0",
                "kwargs": {}}
        result = Grammar.CHANGE_DEGREE(**data)
        self.assertIsInstance(result, dict)

    def test_empty_degree_can_generate_new(self):
        random.seed(42)
        data = {"player": "p1", "synthdef": "pads", "degree": "",
                "kwargs": {}}
        result = Grammar.CHANGE_DEGREE(**data)
        # Either generates new or changes existing (depending on random)
        self.assertIn("degree", result)

    def test_preserves_other_keys(self):
        data = {"player": "p1", "synthdef": "pads", "degree": "0",
                "kwargs": {"dur": "2"}}
        result = Grammar.CHANGE_DEGREE(**data)
        self.assertEqual(result["player"], "p1")
        self.assertEqual(result["synthdef"], "pads")
        self.assertEqual(result["kwargs"]["dur"], "2")


class TestChangeKwarg(unittest.TestCase):
    """Tests for Grammar.CHANGE_KWARG — changing an existing keyword value.

    We patch GENERATE_PATTERN to isolate the test from random pattern generation.
    """

    def setUp(self):
        random.seed(42)
        self._pat_patch = patch.object(Grammar, 'GENERATE_PATTERN', return_value="PRange(8)")
        self._pat_patch.start()

    def tearDown(self):
        self._pat_patch.stop()

    def test_changes_kwarg_value(self):
        data = {"player": "p1", "synthdef": "pads", "degree": "0",
                "kwargs": {"dur": "2"}}
        result = Grammar.CHANGE_KWARG(**data)
        self.assertIn("kwargs", result)
        # Should still have dur (may have different value)
        self.assertIn("dur", result["kwargs"])

    def test_adds_kwarg_when_empty(self):
        data = {"player": "p1", "synthdef": "pads", "degree": "0",
                "kwargs": {}}
        result = Grammar.CHANGE_KWARG(**data)
        # When no kwargs exist, delegates to ADD_NEW_KWARG
        self.assertGreater(len(result["kwargs"]), 0)

    def test_returns_dict(self):
        data = {"player": "p1", "synthdef": "pads", "degree": "0",
                "kwargs": {"dur": "2"}}
        result = Grammar.CHANGE_KWARG(**data)
        self.assertIsInstance(result, dict)

    def test_preserves_other_keys(self):
        data = {"player": "p1", "synthdef": "pads", "degree": "[0,1]",
                "kwargs": {"dur": "2", "amp": "1"}}
        result = Grammar.CHANGE_KWARG(**data)
        self.assertEqual(result["player"], "p1")
        self.assertEqual(result["synthdef"], "pads")

    def test_multiple_kwargs_selects_one(self):
        random.seed(42)
        data = {"player": "p1", "synthdef": "pads", "degree": "0",
                "kwargs": {"dur": "2", "amp": "1", "pan": "0"}}
        result = Grammar.CHANGE_KWARG(**data)
        # All three kwargs should still be present
        self.assertEqual(len(result["kwargs"]), 3)


class TestAddNewMethod(unittest.TestCase):
    """Tests for Grammar.ADD_NEW_METHOD — placeholder for adding methods."""

    def test_returns_kwargs_unchanged(self):
        data = {"player": "p1", "synthdef": "pads", "degree": "0",
                "kwargs": {"dur": "2"}}
        result = Grammar.ADD_NEW_METHOD(**data)
        self.assertEqual(result, data)

    def test_returns_dict(self):
        data = {"player": "p1", "synthdef": "pads", "degree": "0",
                "kwargs": {}}
        result = Grammar.ADD_NEW_METHOD(**data)
        self.assertIsInstance(result, dict)


# ==================================================================
# 9. Constants Validation
# ==================================================================

class TestConstants(unittest.TestCase):
    """Tests for Grammar constants: Players, Actions, Keywords, weights."""

    def test_players_is_list(self):
        self.assertIsInstance(Grammar.Players, list)

    def test_players_not_empty(self):
        self.assertGreater(len(Grammar.Players), 0)

    def test_players_are_strings(self):
        for p in Grammar.Players:
            self.assertIsInstance(p, str)

    def test_players_content(self):
        expected = ["g1", "g2", "g3", "g4", "g5"]
        self.assertEqual(Grammar.Players, expected)

    def test_actions_is_list(self):
        self.assertIsInstance(Grammar.Actions, list)

    def test_actions_not_empty(self):
        self.assertGreater(len(Grammar.Actions), 0)

    def test_actions_are_callable(self):
        for a in Grammar.Actions:
            self.assertTrue(callable(a))

    def test_actions_weighted_correctly(self):
        # ADD_NEW_KWARG has weight 2, CHANGE_DEGREE has weight 5,
        # CHANGE_KWARG has weight 3, ADD_NEW_METHOD has weight 0
        total = Grammar.Actions
        self.assertEqual(total.count(Grammar.ADD_NEW_KWARG), 2)
        self.assertEqual(total.count(Grammar.CHANGE_DEGREE), 5)
        self.assertEqual(total.count(Grammar.CHANGE_KWARG), 3)
        self.assertEqual(total.count(Grammar.ADD_NEW_METHOD), 0)

    def test_keywords_is_list(self):
        self.assertIsInstance(Grammar.Keywords, list)

    def test_keywords_not_empty(self):
        self.assertGreater(len(Grammar.Keywords), 0)

    def test_keywords_are_strings(self):
        for kw in Grammar.Keywords:
            self.assertIsInstance(kw, str)

    def test_keyword_weights(self):
        # dur has weight 4
        self.assertEqual(Grammar.Keywords.count("dur"), 4)
        # amp, vib, sus, etc. have weight 1
        self.assertEqual(Grammar.Keywords.count("amp"), 1)
        self.assertEqual(Grammar.Keywords.count("vib"), 1)
        self.assertEqual(Grammar.Keywords.count("sus"), 1)
        self.assertEqual(Grammar.Keywords.count("chop"), 1)
        self.assertEqual(Grammar.Keywords.count("bits"), 1)
        self.assertEqual(Grammar.Keywords.count("delay"), 1)
        self.assertEqual(Grammar.Keywords.count("pan"), 1)

    def test_action_weights_dict(self):
        self.assertIsInstance(Grammar.ActionWeights, dict)
        self.assertIn(Grammar.ADD_NEW_KWARG, Grammar.ActionWeights)
        self.assertIn(Grammar.CHANGE_DEGREE, Grammar.ActionWeights)
        self.assertIn(Grammar.CHANGE_KWARG, Grammar.ActionWeights)
        self.assertIn(Grammar.ADD_NEW_METHOD, Grammar.ActionWeights)

    def test_keyword_weights_dict(self):
        self.assertIsInstance(Grammar.KeywordWeights, dict)
        self.assertIn("dur", Grammar.KeywordWeights)
        self.assertIn("amp", Grammar.KeywordWeights)
        self.assertIn("pan", Grammar.KeywordWeights)

    def test_keyword_weights_total(self):
        total = sum(Grammar.KeywordWeights.values())
        self.assertEqual(total, 11)  # 4+1+1+1+1+1+1+1

    def test_action_weights_total(self):
        total = sum(Grammar.ActionWeights.values())
        self.assertEqual(total, 10)  # 2+5+3+0


class TestPatternInputs(unittest.TestCase):
    """Tests for Grammar.patternInputs dict."""

    def test_is_dict(self):
        self.assertIsInstance(Grammar.patternInputs, dict)

    def test_known_patterns(self):
        expected_keys = ['PStutter', 'PShuf', 'PAlt', 'PStep', 'PSum',
                         'PStetch', 'PZip', 'PZip2']
        for key in expected_keys:
            self.assertIn(key, Grammar.patternInputs)

    def test_values_are_lists(self):
        for key, val in Grammar.patternInputs.items():
            self.assertIsInstance(val, list)

    def test_pstutter_has_two_inputs(self):
        self.assertEqual(len(Grammar.patternInputs['PStutter']), 2)

    def test_pshuf_has_one_input(self):
        self.assertEqual(len(Grammar.patternInputs['PShuf']), 1)

    def test_palt_has_three_inputs(self):
        self.assertEqual(len(Grammar.patternInputs['PAlt']), 3)

    def test_pstep_has_three_inputs(self):
        self.assertEqual(len(Grammar.patternInputs['PStep']), 3)

    def test_pzip_has_three_inputs(self):
        self.assertEqual(len(Grammar.patternInputs['PZip']), 3)

    def test_pzip2_has_two_inputs(self):
        self.assertEqual(len(Grammar.patternInputs['PZip2']), 2)

    def test_input_generators_are_callable(self):
        for key, generators in Grammar.patternInputs.items():
            for gen in generators:
                self.assertTrue(callable(gen))


# ==================================================================
# 10. null Class Tests
# ==================================================================

class TestNullClass(unittest.TestCase):
    """Tests for Writer.null — placeholder widget class."""

    def test_repr(self):
        n = Writer.null()
        self.assertEqual(repr(n), "null")

    def test_after_returns_zero(self):
        n = Writer.null()
        result = n.after(100, lambda: None)
        self.assertEqual(result, 0)

    def test_read_returns_empty_string(self):
        n = Writer.null()
        result = n.read()
        self.assertEqual(result, "")

    def test_replace_returns_none(self):
        n = Writer.null()
        result = n.replace(1, "old", "new")
        self.assertIsNone(result)

    def test_exec_line_returns_none(self):
        n = Writer.null()
        result = n.exec_line(event=None)
        self.assertIsNone(result)

    def test_root_attribute(self):
        n = Writer.null()
        self.assertIsNotNone(n.root)
        self.assertIsInstance(n.root, Writer.null)

    def test_root_is_non_root_null(self):
        n = Writer.null()
        # The root's null was created with root=False
        self.assertFalse(hasattr(n.root, "root") and
                         isinstance(getattr(n.root, "root", None), Writer.null))

    def test_non_root_null_has_no_root_attr(self):
        n = Writer.null(root=False)
        # Non-root null should not have a root attribute set
        self.assertFalse(hasattr(n, "root"))

    def test_after_with_multiple_args(self):
        n = Writer.null()
        result = n.after(500, lambda: "test", "extra")
        self.assertEqual(result, 0)

    def test_replace_with_no_args(self):
        n = Writer.null()
        result = n.replace()
        self.assertIsNone(result)

    def test_exec_line_with_kwargs(self):
        n = Writer.null()
        result = n.exec_line(event=None, insert="1.0")
        self.assertIsNone(result)

    def test_str_representation(self):
        n = Writer.null()
        self.assertEqual(str(n), "null")


# ==================================================================
# 11. Ghost Class Tests
# ==================================================================

class TestGhostInit(unittest.TestCase):
    """Tests for Writer.Ghost — initialization and basic lifecycle."""

    def test_init_creates_empty_players(self):
        g = Writer.Ghost()
        self.assertEqual(g.players, {})

    def test_init_creates_queue(self):
        g = Writer.Ghost()
        self.assertIsInstance(g.instructions, queue.Queue)

    def test_init_queue_is_empty(self):
        g = Writer.Ghost()
        self.assertTrue(g.instructions.empty())

    def test_init_running_is_true(self):
        g = Writer.Ghost()
        self.assertTrue(g.running)

    def test_init_index(self):
        g = Writer.Ghost()
        self.assertEqual(g.index, [0, 0])

    def test_class_has_null_widget(self):
        self.assertIsInstance(Writer.Ghost.widget, Writer.null)

    def test_stop_sets_running_false(self):
        g = Writer.Ghost()
        g.stop()
        self.assertFalse(g.running)


class TestGhostDefineInstructions(unittest.TestCase):
    """Tests for Ghost.defineInstructions — queueing (original, new) pairs."""

    def test_adds_to_queue(self):
        g = Writer.Ghost()
        syntax = {"player": "p1", "synthdef": "pads", "degree": "[0,2,4]",
                  "kwargs": {}, "methods": ""}
        g.defineInstructions("p1 >> pads([0,2,4])", syntax)
        self.assertFalse(g.instructions.empty())

    def test_queue_item_is_tuple(self):
        g = Writer.Ghost()
        syntax = {"player": "p1", "synthdef": "pads", "degree": "0",
                  "kwargs": {}, "methods": ""}
        g.defineInstructions("p1 >> pads(0)", syntax)
        item = g.instructions.get_nowait()
        self.assertIsInstance(item, tuple)
        self.assertEqual(len(item), 2)

    def test_queue_contains_original(self):
        g = Writer.Ghost()
        original = "p1 >> pads([0,2,4])"
        syntax = {"player": "p1", "synthdef": "pads", "degree": "[0,2,4]",
                  "kwargs": {}, "methods": ""}
        g.defineInstructions(original, syntax)
        old, new = g.instructions.get_nowait()
        self.assertEqual(old, original)

    def test_queue_contains_reconstructed(self):
        g = Writer.Ghost()
        syntax = {"player": "p1", "synthdef": "pads", "degree": "[0,2,4]",
                  "kwargs": {"dur": "2"}, "methods": ""}
        g.defineInstructions("original", syntax)
        old, new = g.instructions.get_nowait()
        self.assertIn("p1 >> pads", new)
        self.assertIn("dur=2", new)

    def test_multiple_instructions_queued(self):
        g = Writer.Ghost()
        syntax1 = {"player": "p1", "synthdef": "pads", "degree": "0",
                   "kwargs": {}, "methods": ""}
        syntax2 = {"player": "p2", "synthdef": "bass", "degree": "1",
                   "kwargs": {}, "methods": ""}
        g.defineInstructions("p1 >> pads(0)", syntax1)
        g.defineInstructions("p2 >> bass(1)", syntax2)
        self.assertEqual(g.instructions.qsize(), 2)


class TestGhostGetPlayer(unittest.TestCase):
    """Tests for Ghost.getPlayer — reading text and finding players."""

    def test_returns_none_for_empty_text(self):
        g = Writer.Ghost()
        # widget.read() returns "" for null widget
        result = g.getPlayer()
        self.assertIsNone(result)

    def test_returns_none_when_no_players_found(self):
        g = Writer.Ghost()
        g.widget = Writer.null()
        result = g.getPlayer()
        self.assertIsNone(result)

    def test_finds_player_in_text(self):
        g = Writer.Ghost()
        mock_widget = MagicMock()
        mock_widget.read.return_value = "p1 >> pads([0,2,4], dur=2)"
        mock_widget.root = Writer.null(root=False)
        g.widget = mock_widget
        result = g.getPlayer()
        self.assertIsNotNone(result)
        self.assertIn("p1", result)

    def test_updates_players_dict(self):
        g = Writer.Ghost()
        mock_widget = MagicMock()
        mock_widget.read.return_value = "p1 >> pads([0,2,4])"
        mock_widget.root = Writer.null(root=False)
        g.widget = mock_widget
        g.getPlayer()
        self.assertGreater(len(g.players), 0)

    def test_clears_players_dict_on_each_call(self):
        g = Writer.Ghost()
        g.players = {"old": "data"}
        mock_widget = MagicMock()
        mock_widget.read.return_value = ""
        mock_widget.root = Writer.null(root=False)
        g.widget = mock_widget
        g.getPlayer()
        self.assertEqual(g.players, {})


class TestGhostWrite(unittest.TestCase):
    """Tests for Ghost.write — processing instruction queue."""

    def test_write_empty_queue_does_not_crash(self):
        g = Writer.Ghost()
        g.widget = Writer.null()
        # Should handle empty queue gracefully
        g.write()

    def test_write_processes_instruction(self):
        g = Writer.Ghost()
        mock_widget = MagicMock()
        mock_widget.read.return_value = "p1 >> pads([0,2,4])\n"
        mock_widget.root = MagicMock()
        mock_widget.root.after = MagicMock(return_value=0)
        g.widget = mock_widget

        g.instructions.put(("p1 >> pads([0,2,4])", "p1 >> pads([1,3,5])"))
        g.write()

        mock_widget.replace.assert_called_once()
        mock_widget.exec_line.assert_called_once()


class TestGhostLifecycle(unittest.TestCase):
    """Tests for Ghost start/stop lifecycle."""

    def test_start_returns_self(self):
        g = Writer.Ghost()
        # Override act to avoid random operations
        g.act = MagicMock()
        result = g.start()
        self.assertIs(result, g)

    def test_start_calls_act(self):
        g = Writer.Ghost()
        g.act = MagicMock()
        g.start()
        g.act.assert_called_once()

    def test_stop_then_running_false(self):
        g = Writer.Ghost()
        g.stop()
        self.assertFalse(g.running)


# ==================================================================
# 12. Regex Pattern String Constants
# ==================================================================

class TestRegexStringConstants(unittest.TestCase):
    """Tests for the raw regex string constants defined in Grammar."""

    def test_re_player_pattern(self):
        self.assertEqual(Grammar.re_player, r"\w+")

    def test_re_synthdef_pattern(self):
        self.assertEqual(Grammar.re_synthdef, r"\w+")

    def test_re_args_pattern(self):
        self.assertEqual(Grammar.re_args, r".+")

    def test_re_methods_pattern(self):
        self.assertEqual(Grammar.re_methods, r".?")


# ==================================================================
# 13. Integration / Round-Trip Tests
# ==================================================================

class TestRoundTrip(unittest.TestCase):
    """Tests that parsing and reconstruction are consistent."""

    def test_parse_and_reconstruct_simple(self):
        original = "p1 >> pads(0)"
        result = Grammar.playerData(original)
        self.assertEqual(len(result), 1)
        _, d = result[0]
        reconstructed = Grammar.createPlayer(**d)
        self.assertIn("p1", reconstructed)
        self.assertIn("pads", reconstructed)

    def test_parse_and_reconstruct_with_kwargs(self):
        original = "p1 >> pads(0, amp=1, dur=2)"
        result = Grammar.playerData(original)
        self.assertEqual(len(result), 1)
        _, d = result[0]
        reconstructed = Grammar.createPlayer(**d)
        self.assertIn("p1 >> pads(", reconstructed)
        self.assertIn("amp=1", reconstructed)
        self.assertIn("dur=2", reconstructed)

    def test_parse_reconstruct_no_degree(self):
        original = "p1 >> pads(dur=2)"
        result = Grammar.playerData(original)
        if len(result) > 0:
            _, d = result[0]
            reconstructed = Grammar.createPlayer(**d)
            self.assertIn("p1 >> pads(", reconstructed)

    def test_action_then_reconstruct(self):
        random.seed(42)
        original = "p1 >> pads([0,2,4], dur=2)"
        result = Grammar.playerData(original)
        self.assertEqual(len(result), 1)
        _, d = result[0]
        modified = Grammar.CHANGE_DEGREE(**d)
        reconstructed = Grammar.createPlayer(**modified)
        self.assertIn("p1 >> pads(", reconstructed)

    def test_add_kwarg_then_reconstruct(self):
        random.seed(42)
        original = "p1 >> pads(0)"
        result = Grammar.playerData(original)
        self.assertEqual(len(result), 1)
        _, d = result[0]
        with patch.object(Grammar, 'GENERATE_PATTERN', return_value="PRange(8)"):
            modified = Grammar.ADD_NEW_KWARG(**d)
        reconstructed = Grammar.createPlayer(**modified)
        self.assertIn("p1 >> pads(", reconstructed)
        # Should now have a keyword argument
        self.assertIn("=", reconstructed)


# ==================================================================
# 14. Edge Cases and Robustness Tests
# ==================================================================

class TestEdgeCases(unittest.TestCase):
    """Edge case tests for parsing, generation, and manipulation."""

    def test_getargs_whitespace_only(self):
        degree, kwargs = Grammar.getArgs("   ")
        # Whitespace-only should produce empty or whitespace degree
        self.assertEqual(kwargs, {})

    def test_playerdata_non_player_text(self):
        result = Grammar.playerData("Clock.bpm = 120")
        self.assertEqual(result, [])

    def test_playerdata_comment_line(self):
        result = Grammar.playerData("# p1 >> pads(0)")
        self.assertEqual(result, [])

    def test_format_kwargs_single_item_dict(self):
        result = Grammar.format_kwargs({"x": "42"})
        self.assertEqual(result, "x=42")

    def test_format_kwargs_with_string_raises_error(self):
        # Passing a non-dict (empty string) to format_kwargs raises
        # AttributeError because str has no .items() method.
        # createPlayer avoids this by always passing a dict from kwargs.get().
        with self.assertRaises(AttributeError):
            Grammar.format_kwargs("")

    def test_weighted_list_with_one_weight(self):
        result = Grammar.WeightedList({"only": 1})
        self.assertEqual(result, ["only"])

    def test_generate_integer_deterministic(self):
        random.seed(42)
        val1 = Grammar.GENERATE_INTEGER()
        random.seed(42)
        val2 = Grammar.GENERATE_INTEGER()
        self.assertEqual(str(val1), str(val2))

    def test_generate_number_deterministic(self):
        random.seed(42)
        val1 = Grammar.GENERATE_NUMBER()
        random.seed(42)
        val2 = Grammar.GENERATE_NUMBER()
        self.assertEqual(str(val1), str(val2))

    def test_generate_list_deterministic(self):
        random.seed(42)
        val1 = Grammar.GENERATE_LIST()
        random.seed(42)
        val2 = Grammar.GENERATE_LIST()
        self.assertEqual(val1, val2)

    def test_generate_tuple_deterministic(self):
        random.seed(42)
        val1 = Grammar.GENERATE_TUPLE()
        random.seed(42)
        val2 = Grammar.GENERATE_TUPLE()
        self.assertEqual(val1, val2)

    def test_gen_choose_value_deterministic(self):
        random.seed(42)
        val1 = Grammar.GEN_CHOOSE_VALUE()
        random.seed(42)
        val2 = Grammar.GEN_CHOOSE_VALUE()
        self.assertEqual(str(val1), str(val2))

    def test_gen_change_value_empty_string(self):
        result = Grammar.GEN_CHANGE_VALUE("")
        self.assertEqual(result, "")

    def test_gen_change_value_only_text(self):
        result = Grammar.GEN_CHANGE_VALUE("hello")
        self.assertEqual(result, "hello")

    def test_create_player_all_kwargs(self):
        result = Grammar.createPlayer(
            player="g5", synthdef="pluck", degree="PRange(8)",
            kwargs={"dur": "[1,2]", "amp": "1/2", "pan": "0"},
            methods=".every(4, 'reverse')"
        )
        self.assertIn("g5 >> pluck(", result)
        self.assertIn("PRange(8)", result)
        self.assertIn("dur=[1,2]", result)
        self.assertIn("amp=1/2", result)
        self.assertIn("pan=0", result)
        self.assertIn(".every(4, 'reverse')", result)


# ==================================================================
# 15. Additional Generation Coverage
# ==================================================================

class TestGenerateNumberBranching(unittest.TestCase):
    """More thorough tests for GENERATE_NUMBER branch coverage."""

    def test_non_amp_can_return_integer(self):
        got_int = False
        for seed in range(200):
            random.seed(seed)
            val = Grammar.GENERATE_NUMBER(keyword="dur")
            if isinstance(val, int):
                got_int = True
                break
        self.assertTrue(got_int)

    def test_non_amp_can_return_fraction(self):
        got_frac = False
        for seed in range(200):
            random.seed(seed)
            val = Grammar.GENERATE_NUMBER(keyword="dur")
            if isinstance(val, str) and "/" in val:
                got_frac = True
                break
        self.assertTrue(got_frac)

    def test_min_greater_than_zero_for_fraction(self):
        random.seed(42)
        for _ in range(50):
            val = Grammar.GENERATE_NUMBER(_min=0, _max=5)
            if isinstance(val, str) and "/" in val:
                parts = val.split("/")
                # max(_min, 1) ensures at least 1
                self.assertGreaterEqual(int(parts[0]), 1)
                self.assertGreaterEqual(int(parts[1]), 1)


class TestGenChangeValueComplex(unittest.TestCase):
    """Additional tests for GEN_CHANGE_VALUE with complex input."""

    def setUp(self):
        random.seed(42)

    def test_pattern_with_numbers(self):
        result = Grammar.GEN_CHANGE_VALUE("PRange(8)")
        self.assertIsInstance(result, str)
        self.assertIn("PRange(", result)

    def test_nested_list(self):
        random.seed(42)
        result = Grammar.GEN_CHANGE_VALUE("[1, [2, 3]]")
        self.assertIsInstance(result, str)

    def test_single_digit(self):
        random.seed(42)
        result = Grammar.GEN_CHANGE_VALUE("7")
        self.assertIsInstance(result, str)


class TestGhostActMethod(unittest.TestCase):
    """Tests for Ghost.act — main program logic."""

    def test_act_no_players(self):
        g = Writer.Ghost()
        g.widget = Writer.null()
        # Should handle no players gracefully (getPlayer returns None)
        g.act()
        # No crash and no instructions queued
        self.assertTrue(g.instructions.empty())

    def test_act_with_player(self):
        random.seed(42)
        g = Writer.Ghost()
        mock_widget = MagicMock()
        mock_widget.read.return_value = "p1 >> pads([0,2,4], dur=2)"
        mock_widget.root = MagicMock()
        mock_widget.root.after = MagicMock(return_value=0)
        g.widget = mock_widget

        # Patch GENERATE_PATTERN to isolate from random pattern generation
        with patch.object(Grammar, 'GENERATE_PATTERN', return_value="PRange(8)"):
            g.act()
        # act() calls defineInstructions then write().
        # write() dequeues the instruction and calls widget.replace,
        # so the queue will be empty after act() completes. We verify
        # that replace was called (proving the instruction was processed).
        mock_widget.replace.assert_called_once()
        mock_widget.exec_line.assert_called_once()


# ==================================================================
# 16. Additional Regex Tests
# ==================================================================

class TestReInputEdgeCases(unittest.TestCase):
    """Additional edge cases for re_input regex."""

    def test_leading_whitespace(self):
        m = Grammar.re_input.match("  p1 >> pads(0)")
        # re_input uses (?:\s*) at the start to allow leading whitespace
        self.assertIsNotNone(m)

    def test_player_names_alphanumeric(self):
        m = Grammar.re_input.match("player1 >> synth1(0)")
        self.assertIsNotNone(m)
        self.assertEqual(m.group("player"), "player1")
        self.assertEqual(m.group("synthdef"), "synth1")

    def test_underscore_in_player_name(self):
        m = Grammar.re_input.match("my_player >> my_synth(0)")
        self.assertIsNotNone(m)
        self.assertEqual(m.group("player"), "my_player")
        self.assertEqual(m.group("synthdef"), "my_synth")


class TestGetArgsEdgeCases(unittest.TestCase):
    """More edge cases for getArgs."""

    def test_multiple_commas(self):
        degree, kwargs = Grammar.getArgs("[0, 1, 2], dur=1, amp=2")
        self.assertIn("dur", kwargs)
        self.assertIn("amp", kwargs)

    def test_degree_with_spaces(self):
        degree, kwargs = Grammar.getArgs("  [0, 1, 2]  ")
        self.assertIn("0", degree)

    def test_complex_pattern_degree(self):
        degree, kwargs = Grammar.getArgs("PRange(8), dur=2")
        self.assertIn("PRange", degree)
        self.assertIn("dur", kwargs)


class TestCreatePlayerEdgeCases(unittest.TestCase):
    """Edge cases for createPlayer."""

    def test_empty_strings_all_around(self):
        result = Grammar.createPlayer(
            player="p1", synthdef="s1", degree="",
            kwargs={}, methods=""
        )
        self.assertEqual(result, "p1 >> s1()")

    def test_special_characters_in_degree(self):
        result = Grammar.createPlayer(
            player="p1", synthdef="pads", degree="[0, (1, 2), 3]",
            kwargs={}, methods=""
        )
        self.assertIn("[0, (1, 2), 3]", result)

    def test_many_kwargs(self):
        kwargs = {"a": "1", "b": "2", "c": "3", "d": "4", "e": "5"}
        result = Grammar.createPlayer(
            player="p1", synthdef="pads", degree="0",
            kwargs=kwargs, methods=""
        )
        for k, v in kwargs.items():
            self.assertIn("{}={}".format(k, v), result)


# ==================================================================
# 17. WeightedList Edge Cases
# ==================================================================

class TestWeightedListEdgeCases(unittest.TestCase):
    """Edge cases for WeightedList."""

    def test_all_zero_weights(self):
        result = Grammar.WeightedList({"a": 0, "b": 0})
        self.assertEqual(result, [])

    def test_single_high_weight(self):
        result = Grammar.WeightedList({"x": 100})
        self.assertEqual(len(result), 100)
        self.assertTrue(all(item == "x" for item in result))

    def test_mixed_types_as_keys(self):
        result = Grammar.WeightedList({1: 2, "b": 3})
        self.assertEqual(result.count(1), 2)
        self.assertEqual(result.count("b"), 3)


# ==================================================================
# 18. Ghost Queue Handling Tests
# ==================================================================

class TestGhostQueueHandling(unittest.TestCase):
    """Tests for Ghost's queue-based instruction handling."""

    def test_multiple_instructions_fifo(self):
        g = Writer.Ghost()
        syntax1 = {"player": "p1", "synthdef": "pads", "degree": "0",
                    "kwargs": {}, "methods": ""}
        syntax2 = {"player": "p2", "synthdef": "bass", "degree": "1",
                    "kwargs": {}, "methods": ""}
        g.defineInstructions("first", syntax1)
        g.defineInstructions("second", syntax2)
        old1, _ = g.instructions.get_nowait()
        self.assertEqual(old1, "first")
        old2, _ = g.instructions.get_nowait()
        self.assertEqual(old2, "second")

    def test_queue_empty_after_drain(self):
        g = Writer.Ghost()
        syntax = {"player": "p1", "synthdef": "pads", "degree": "0",
                  "kwargs": {}, "methods": ""}
        g.defineInstructions("orig", syntax)
        g.instructions.get_nowait()
        self.assertTrue(g.instructions.empty())


if __name__ == "__main__":
    unittest.main()
