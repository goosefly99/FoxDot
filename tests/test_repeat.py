"""
Unit tests for Repeat module — MethodList, Repeatable.convert_cycles, and Repeatable helper methods.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from FoxDot.lib.Repeat import MethodList, Repeatable
from FoxDot.lib.Patterns import Pattern, Cycle
from FoxDot.lib.TimeVar import var


# ---------------------------------------------------------------------------
# MethodList
# ---------------------------------------------------------------------------

class TestMethodListInit(unittest.TestCase):
    """Tests for MethodList creation and root pattern management."""

    def test_create(self):
        ml = MethodList(Pattern([1, 2, 3]))
        self.assertIsInstance(ml.get_root_pattern(), Pattern)

    def test_get_root_pattern(self):
        root = Pattern([1, 2, 3])
        ml = MethodList(root)
        self.assertIs(ml.get_root_pattern(), root)

    def test_set_root_pattern(self):
        ml = MethodList(Pattern([1, 2, 3]))
        new_root = Pattern([4, 5, 6])
        ml.set_root_pattern(new_root)
        self.assertIs(ml.get_root_pattern(), new_root)

    def test_empty_list_of_methods(self):
        ml = MethodList(Pattern([1]))
        self.assertEqual(ml.list_of_methods, [])

    def test_root_with_int(self):
        ml = MethodList(42)
        self.assertEqual(ml.get_root_pattern(), 42)


class TestMethodListAdd(unittest.TestCase):
    """Tests for adding methods to the MethodList."""

    def test_add_method(self):
        ml = MethodList(Pattern([1, 2, 3]))
        ml.add_method("reverse", (), {})
        self.assertEqual(len(ml.list_of_methods), 1)
        self.assertEqual(ml.list_of_methods[0], ("reverse", (), {}))

    def test_add_multiple_methods(self):
        ml = MethodList(Pattern([1, 2, 3]))
        ml.add_method("reverse", (), {})
        ml.add_method("shuffle", (), {})
        self.assertEqual(len(ml.list_of_methods), 2)

    def test_add_method_with_args(self):
        ml = MethodList(Pattern([1, 2, 3]))
        ml.add_method("stutter", (4,), {"key": "val"})
        name, args, kwargs = ml.list_of_methods[0]
        self.assertEqual(name, "stutter")
        self.assertEqual(args, (4,))
        self.assertEqual(kwargs, {"key": "val"})


class TestMethodListUpdate(unittest.TestCase):
    """Tests for updating methods in the MethodList."""

    def test_update_existing(self):
        ml = MethodList(Pattern([1, 2, 3]))
        ml.add_method("reverse", (), {})
        ml.update("reverse", (1,), {"new": True})
        name, args, kwargs = ml.list_of_methods[0]
        self.assertEqual(args, (1,))
        self.assertEqual(kwargs, {"new": True})

    def test_update_nonexistent_raises(self):
        ml = MethodList(Pattern([1, 2, 3]))
        with self.assertRaises(ValueError):
            ml.update("nonexistent", (), {})

    def test_update_second_method(self):
        ml = MethodList(Pattern([1, 2, 3]))
        ml.add_method("reverse", (), {})
        ml.add_method("shuffle", (), {})
        ml.update("shuffle", (2,), {})
        self.assertEqual(ml.list_of_methods[1], ("shuffle", (2,), {}))
        self.assertEqual(ml.list_of_methods[0], ("reverse", (), {}))


class TestMethodListRemove(unittest.TestCase):
    """Tests for removing methods from the MethodList."""

    def test_remove_existing(self):
        ml = MethodList(Pattern([1, 2, 3]))
        ml.add_method("reverse", (), {})
        ml.remove("reverse")
        self.assertEqual(len(ml.list_of_methods), 0)

    def test_remove_nonexistent_raises(self):
        ml = MethodList(Pattern([1, 2, 3]))
        with self.assertRaises(ValueError):
            ml.remove("nonexistent")

    def test_remove_first_of_two(self):
        ml = MethodList(Pattern([1, 2, 3]))
        ml.add_method("reverse", (), {})
        ml.add_method("shuffle", (), {})
        ml.remove("reverse")
        self.assertEqual(len(ml.list_of_methods), 1)
        self.assertEqual(ml.list_of_methods[0][0], "shuffle")

    def test_remove_second_of_two(self):
        ml = MethodList(Pattern([1, 2, 3]))
        ml.add_method("reverse", (), {})
        ml.add_method("shuffle", (), {})
        ml.remove("shuffle")
        self.assertEqual(len(ml.list_of_methods), 1)
        self.assertEqual(ml.list_of_methods[0][0], "reverse")


class TestMethodListContains(unittest.TestCase):
    """Tests for __contains__ on MethodList."""

    def test_contains_true(self):
        ml = MethodList(Pattern([1]))
        ml.add_method("reverse", (), {})
        self.assertIn("reverse", ml)

    def test_contains_false(self):
        ml = MethodList(Pattern([1]))
        self.assertNotIn("reverse", ml)

    def test_contains_after_remove(self):
        ml = MethodList(Pattern([1]))
        ml.add_method("reverse", (), {})
        ml.remove("reverse")
        self.assertNotIn("reverse", ml)


class TestMethodListIter(unittest.TestCase):
    """Tests for iterating over MethodList."""

    def test_iter_empty(self):
        ml = MethodList(Pattern([1]))
        self.assertEqual(list(ml), [])

    def test_iter_populated(self):
        ml = MethodList(Pattern([1]))
        ml.add_method("reverse", (), {})
        ml.add_method("shuffle", (1,), {"x": 2})
        items = list(ml)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0], ("reverse", (), {}))
        self.assertEqual(items[1], ("shuffle", (1,), {"x": 2}))


class TestMethodListRepr(unittest.TestCase):
    """Tests for MethodList repr."""

    def test_repr_empty(self):
        ml = MethodList(Pattern([1]))
        self.assertEqual(repr(ml), "[]")

    def test_repr_populated(self):
        ml = MethodList(Pattern([1]))
        ml.add_method("reverse", (), {})
        r = repr(ml)
        self.assertIn("reverse", r)


# ---------------------------------------------------------------------------
# Repeatable (static methods + helper methods)
# ---------------------------------------------------------------------------

class TestConvertCycles(unittest.TestCase):
    """Tests for Repeatable.convert_cycles() static method."""

    def test_no_cycles(self):
        args = [1, 2, 3]
        kwargs = {"key": "val"}
        new_args, new_kwargs = Repeatable.convert_cycles(args, kwargs, 4)
        self.assertEqual(new_args, [1, 2, 3])
        self.assertEqual(new_kwargs, {"key": "val"})

    def test_cycle_in_args(self):
        c = Cycle([1, 2, 3])
        args = [c, 42]
        kwargs = {}
        new_args, new_kwargs = Repeatable.convert_cycles(args, kwargs, 4)
        # Cycle values are converted to var (TimeVar), so they should no longer be Cycle
        self.assertNotIsInstance(new_args[0], Cycle)
        self.assertEqual(new_args[1], 42)

    def test_cycle_in_kwargs(self):
        c = Cycle([1, 2, 3])
        args = []
        kwargs = {"x": c, "y": 5}
        new_args, new_kwargs = Repeatable.convert_cycles(args, kwargs, 4)
        self.assertNotIsInstance(new_kwargs["x"], Cycle)
        self.assertEqual(new_kwargs["y"], 5)

    def test_all_non_cycle(self):
        args = [1, "two", 3.0]
        kwargs = {"a": 10, "b": "hello"}
        new_args, new_kwargs = Repeatable.convert_cycles(args, kwargs, 8)
        self.assertEqual(new_args, [1, "two", 3.0])
        self.assertEqual(new_kwargs, {"a": 10, "b": "hello"})

    def test_empty(self):
        new_args, new_kwargs = Repeatable.convert_cycles([], {}, 4)
        self.assertEqual(new_args, [])
        self.assertEqual(new_kwargs, {})

    def test_multiple_cycles(self):
        c1 = Cycle([1, 2])
        c2 = Cycle([3, 4])
        args = [c1, c2]
        kwargs = {}
        new_args, new_kwargs = Repeatable.convert_cycles(args, kwargs, 2)
        self.assertNotIsInstance(new_args[0], Cycle)
        self.assertNotIsInstance(new_args[1], Cycle)


class TestRepeatableGetAttrAndMethodName(unittest.TestCase):
    """Tests for Repeatable.get_attr_and_method_name()."""

    def setUp(self):
        self.r = Repeatable()
        self.r.method_synonyms = {}

    def test_single_method(self):
        attr, method = self.r.get_attr_and_method_name("reverse")
        self.assertEqual(attr, "degree")
        self.assertEqual(method, "reverse")

    def test_attr_dot_method(self):
        attr, method = self.r.get_attr_and_method_name("oct.reverse")
        self.assertEqual(attr, "oct")
        self.assertEqual(method, "reverse")

    def test_synonym(self):
        self.r.method_synonyms = {"shuf": "shuffle"}
        attr, method = self.r.get_attr_and_method_name("shuf")
        self.assertEqual(attr, "degree")
        self.assertEqual(method, "shuffle")


class TestRepeatableIsPatternMethod(unittest.TestCase):
    """Tests for is_pattern_method() and is_player_method()."""

    def setUp(self):
        self.r = Repeatable()

    def test_known_pattern_method(self):
        self.assertTrue(self.r.is_pattern_method("reverse"))

    def test_unknown_method(self):
        self.assertFalse(self.r.is_pattern_method("nonexistent_xyzzy"))

    def test_is_player_method_false_by_default(self):
        # Repeatable base has no player-specific methods
        self.assertFalse(self.r.is_player_method("stop"))


class TestRepeatableInit(unittest.TestCase):
    """Tests for Repeatable initialization."""

    def test_init_sets_empty_dicts(self):
        r = Repeatable()
        self.assertEqual(r.repeat_events, {})
        self.assertEqual(r.previous_patterns, {})


if __name__ == "__main__":
    unittest.main()
