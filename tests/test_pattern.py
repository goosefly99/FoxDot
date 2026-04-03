"""Unit tests for FoxDot.lib.Patterns — Pattern creation, indexing, arithmetic,
manipulation methods, PGroup behaviour, POperand operations, and composition."""

import unittest

from FoxDot.lib.Patterns.Main import (
    GeneratorPattern,
    Pattern,
    PGroup,
    metaPattern,
)
from FoxDot.lib.Patterns.Operations import (
    PAdd,
    PDiv,
    PDiv2,
    PEq,
    PFloor,
    PMod,
    PMul,
    PNe,
    POperand,
    PPow,
    PSub,
    PSub2,
    Add,
    Sub,
    Mul,
    Div,
    Mod,
    Pow,
    FloorDiv,
)
from FoxDot.lib.Patterns.Sequences import P


# ==================================================================
# Pattern Creation
# ==================================================================

class TestPatternCreation(unittest.TestCase):
    """Test basic Pattern construction from different input types."""

    def test_create_from_list(self):
        p = Pattern([0, 1, 2, 3])
        self.assertEqual(list(p), [0, 1, 2, 3])

    def test_create_from_empty_list(self):
        p = Pattern([])
        self.assertEqual(list(p), [])
        self.assertEqual(len(p), 0)

    def test_create_empty(self):
        p = Pattern()
        self.assertEqual(len(p), 0)

    def test_create_from_single_value(self):
        p = Pattern([5])
        self.assertEqual(list(p), [5])

    def test_create_from_range(self):
        p = Pattern(range(5))
        self.assertEqual(list(p), [0, 1, 2, 3, 4])

    def test_p_shorthand_list(self):
        p = P[0, 1, 2, 3]
        self.assertIsInstance(p, Pattern)
        self.assertEqual(list(p), [0, 1, 2, 3])

    def test_p_shorthand_slice(self):
        p = P[0:4]
        self.assertEqual(list(p), [0, 1, 2, 3])

    def test_p_shorthand_slice_with_step(self):
        p = P[0:10:2]
        self.assertEqual(list(p), [0, 2, 4, 6, 8])

    def test_p_shorthand_mixed_slice_and_values(self):
        p = P[0, 1, 2:5]
        self.assertEqual(list(p), [0, 1, 2, 3, 4])

    def test_create_preserves_floats(self):
        p = Pattern([0.5, 1.5, 2.5])
        self.assertEqual(list(p), [0.5, 1.5, 2.5])

    def test_create_from_pattern(self):
        """Creating a Pattern from another Pattern copies data."""
        p1 = Pattern([1, 2, 3])
        p2 = Pattern(p1)
        self.assertEqual(list(p1), list(p2))


# ==================================================================
# Pattern Length
# ==================================================================

class TestPatternLength(unittest.TestCase):
    """Test the expanded-length calculation for flat and nested patterns."""

    def test_flat_length(self):
        self.assertEqual(len(Pattern([0, 1, 2, 3])), 4)

    def test_nested_pattern_expands_length(self):
        """P[0, 1, 2, [3, 4]] has expanded length 8 (4 items * LCM of nested len 2)."""
        p = Pattern([0, 1, 2, Pattern([3, 4])])
        self.assertEqual(len(p), 8)

    def test_nested_pattern_triple(self):
        """P[0, [1, 2, 3]] has expanded length 6 (2 items * LCM(1, 3))."""
        p = Pattern([0, Pattern([1, 2, 3])])
        self.assertEqual(len(p), 6)

    def test_single_element_length(self):
        self.assertEqual(len(Pattern([42])), 1)

    def test_empty_length(self):
        self.assertEqual(len(Pattern([])), 0)


# ==================================================================
# Pattern Indexing
# ==================================================================

class TestPatternIndexing(unittest.TestCase):
    """Test __getitem__ / getitem with wrapping and nesting."""

    def test_basic_indexing(self):
        p = Pattern([10, 20, 30])
        self.assertEqual(p[0], 10)
        self.assertEqual(p[1], 20)
        self.assertEqual(p[2], 30)

    def test_wrapping_index(self):
        """Indexing past the end wraps around."""
        p = Pattern([10, 20, 30])
        self.assertEqual(p[3], 10)
        self.assertEqual(p[4], 20)
        self.assertEqual(p[5], 30)

    def test_nested_pattern_alternating(self):
        """Nested patterns alternate: P[0, [1, 2]] → indices 0,1,2,3 → 0,1,0,2."""
        p = Pattern([0, Pattern([1, 2])])
        self.assertEqual(p[0], 0)
        self.assertEqual(p[1], 1)
        self.assertEqual(p[2], 0)
        self.assertEqual(p[3], 2)

    def test_deeply_nested(self):
        """P[0, 1, 2, [3, 4]] at index 3 and 7."""
        p = Pattern([0, 1, 2, Pattern([3, 4])])
        self.assertEqual(p[3], 3)
        self.assertEqual(p[7], 4)

    def test_slice_indexing(self):
        p = Pattern([0, 1, 2, 3, 4])
        result = p[1:4]
        self.assertIsInstance(result, Pattern)
        self.assertEqual(list(result), [1, 2, 3])

    def test_index_with_pattern(self):
        """Indexing with a Pattern returns a Pattern of values."""
        p = Pattern([10, 20, 30, 40])
        idx = Pattern([0, 2])
        result = p[idx]
        self.assertIsInstance(result, metaPattern)
        self.assertEqual(list(result), [10, 30])


# ==================================================================
# Pattern Iteration
# ==================================================================

class TestPatternIteration(unittest.TestCase):
    """Test iterating over Patterns."""

    def test_iter_flat(self):
        p = Pattern([0, 1, 2])
        self.assertEqual(list(p), [0, 1, 2])

    def test_iter_nested(self):
        """Iterating expands nested patterns."""
        p = Pattern([0, Pattern([1, 2])])
        self.assertEqual(list(p), [0, 1, 0, 2])

    def test_items_method(self):
        p = Pattern([10, 20, 30])
        result = list(p.items())
        self.assertEqual(result, [(0, 10), (1, 20), (2, 30)])


# ==================================================================
# Pattern Arithmetic
# ==================================================================

class TestPatternArithmetic(unittest.TestCase):
    """Test arithmetic operators on Patterns."""

    def test_add_scalar(self):
        p = Pattern([0, 1, 2]) + 10
        self.assertEqual(list(p), [10, 11, 12])

    def test_radd_scalar(self):
        p = 10 + Pattern([0, 1, 2])
        self.assertEqual(list(p), [10, 11, 12])

    def test_sub_scalar(self):
        p = Pattern([10, 20, 30]) - 5
        self.assertEqual(list(p), [5, 15, 25])

    def test_rsub_scalar(self):
        p = 100 - Pattern([10, 20, 30])
        self.assertEqual(list(p), [90, 80, 70])

    def test_mul_scalar(self):
        p = Pattern([1, 2, 3]) * 3
        self.assertEqual(list(p), [3, 6, 9])

    def test_rmul_scalar(self):
        p = 3 * Pattern([1, 2, 3])
        self.assertEqual(list(p), [3, 6, 9])

    def test_truediv_scalar(self):
        p = Pattern([10, 20, 30]) / 2
        self.assertEqual(list(p), [5.0, 10.0, 15.0])

    def test_rtruediv_scalar(self):
        p = 60 / Pattern([1, 2, 3])
        self.assertEqual(list(p), [60.0, 30.0, 20.0])

    def test_floordiv_scalar(self):
        p = Pattern([10, 21, 35]) // 10
        self.assertEqual(list(p), [1, 2, 3])

    def test_mod_scalar(self):
        p = Pattern([10, 11, 12]) % 3
        self.assertEqual(list(p), [1, 2, 0])

    def test_pow_scalar(self):
        p = Pattern([2, 3, 4]) ** 2
        self.assertEqual(list(p), [4, 9, 16])

    def test_add_pattern_same_length(self):
        p = Pattern([1, 2, 3]) + Pattern([10, 20, 30])
        self.assertEqual(list(p), [11, 22, 33])

    def test_add_pattern_different_length(self):
        """Patterns of different lengths expand to LCM length."""
        p = Pattern([1, 2, 3]) + Pattern([10, 20])
        # LCM(3, 2) = 6 → [1+10, 2+20, 3+10, 1+20, 2+10, 3+20]
        self.assertEqual(list(p), [11, 22, 13, 21, 12, 23])

    def test_sub_pattern(self):
        p = Pattern([10, 20]) - Pattern([1, 2])
        self.assertEqual(list(p), [9, 18])

    def test_mul_pattern(self):
        p = Pattern([2, 3]) * Pattern([4, 5])
        self.assertEqual(list(p), [8, 15])

    def test_div_by_zero_returns_zero(self):
        """Division by zero in patterns returns 0."""
        p = Pattern([10, 20]) / Pattern([0, 5])
        result = list(p)
        self.assertEqual(result[0], 0)
        self.assertEqual(result[1], 4.0)

    def test_abs(self):
        p = abs(Pattern([-1, 2, -3, 4]))
        self.assertEqual(list(p), [1, 2, 3, 4])

    def test_negate_via_mul(self):
        p = Pattern([1, -2, 3]) * -1
        self.assertEqual(list(p), [-1, 2, -3])


# ==================================================================
# Pattern Manipulation Methods
# ==================================================================

class TestPatternManipulation(unittest.TestCase):
    """Test Pattern transformation methods."""

    def test_reverse(self):
        p = Pattern([1, 2, 3, 4]).reverse()
        self.assertEqual(list(p), [4, 3, 2, 1])

    def test_mirror(self):
        p = Pattern([1, 2, 3]).mirror()
        self.assertEqual(list(p), [3, 2, 1])

    def test_invert_tilde(self):
        """~ operator calls mirror()."""
        p = ~Pattern([1, 2, 3])
        self.assertEqual(list(p), [3, 2, 1])

    def test_rotate_default(self):
        p = Pattern([1, 2, 3, 4]).rotate()
        self.assertEqual(list(p), [2, 3, 4, 1])

    def test_rotate_by_n(self):
        p = Pattern([1, 2, 3, 4]).rotate(2)
        self.assertEqual(list(p), [3, 4, 1, 2])

    def test_rotate_negative(self):
        p = Pattern([1, 2, 3, 4]).rotate(-1)
        self.assertEqual(list(p), [4, 1, 2, 3])

    def test_sort(self):
        p = Pattern([3, 1, 4, 1, 5]).sort()
        self.assertEqual(list(p), [1, 1, 3, 4, 5])

    def test_palindrome(self):
        """P[0, 1, 2, 3].palindrome() → P[0, 1, 2, 3, 3, 2, 1, 0]."""
        p = Pattern([0, 1, 2, 3]).palindrome()
        self.assertEqual(list(p), [0, 1, 2, 3, 3, 2, 1, 0])

    def test_palindrome_trim_middle(self):
        """P[0, 1, 2, 3].palindrome(1) → P[0, 1, 2, 3, 2, 1, 0]."""
        p = Pattern([0, 1, 2, 3]).palindrome(1)
        self.assertEqual(list(p), [0, 1, 2, 3, 2, 1, 0])

    def test_palindrome_trim_end(self):
        """P[0, 1, 2, 3].palindrome(-1) → P[0, 1, 2, 3, 3, 2, 1]."""
        p = Pattern([0, 1, 2, 3]).palindrome(-1)
        self.assertEqual(list(p), [0, 1, 2, 3, 3, 2, 1])

    def test_palindrome_trim_both(self):
        """P[0, 1, 2, 3].palindrome(1, -1) → P[0, 1, 2, 3, 2, 1]."""
        p = Pattern([0, 1, 2, 3]).palindrome(1, -1)
        self.assertEqual(list(p), [0, 1, 2, 3, 2, 1])

    def test_stutter_default(self):
        p = Pattern([0, 1, 2]).stutter()
        self.assertEqual(list(p), [0, 0, 1, 1, 2, 2])

    def test_stutter_n3(self):
        p = Pattern([0, 1]).stutter(3)
        self.assertEqual(list(p), [0, 0, 0, 1, 1, 1])

    def test_stutter_variable(self):
        """P[0, 1, 2, 3].stutter([1, 3]) repeats items by alternating counts."""
        p = Pattern([0, 1, 2, 3]).stutter([1, 3])
        self.assertEqual(list(p), [0, 1, 1, 1, 2, 3, 3, 3])

    def test_arp(self):
        """P[0, 1, 2, 3].arp([0, 2]) → P[0, 2, 1, 3, 2, 4, 3, 5]."""
        p = Pattern([0, 1, 2, 3]).arp([0, 2])
        self.assertEqual(list(p), [0, 2, 1, 3, 2, 4, 3, 5])

    def test_stretch(self):
        p = Pattern([0, 1, 2]).stretch(6)
        self.assertEqual(list(p), [0, 1, 2, 0, 1, 2])

    def test_trim(self):
        p = Pattern([0, 1, 2, 3, 4]).trim(3)
        self.assertEqual(list(p), [0, 1, 2])

    def test_trim_larger_than_len(self):
        p = Pattern([0, 1]).trim(5)
        self.assertEqual(list(p), [0, 1])

    def test_loop(self):
        # Note: loop() aliases new=values, so without a func the list doubles
        # each iteration: start [0,1], +[0,1]→[0,1,0,1], +[0,1,0,1]→8 items
        p = Pattern([0, 1]).loop(3)
        self.assertEqual(list(p), [0, 1, 0, 1, 0, 1, 0, 1])

    def test_loop_with_func(self):
        p = Pattern([1, 2]).loop(3, lambda x: x * 2)
        self.assertEqual(list(p), [1, 2, 2, 4, 4, 8])

    def test_loop_raises_on_zero(self):
        with self.assertRaises(ValueError):
            Pattern([0, 1]).loop(0)

    def test_duplicate(self):
        p = Pattern([0, 1, 2]).duplicate(2)
        self.assertEqual(p.data, [0, 1, 2, 0, 1, 2])

    def test_swap(self):
        p = Pattern([1, 2, 3, 4]).swap(2)
        self.assertEqual(list(p), [2, 1, 4, 3])

    def test_accum(self):
        p = Pattern([1, 2, 3, 4]).accum()
        self.assertEqual(list(p), [0, 1, 3, 6])

    def test_undup(self):
        """Removes consecutive duplicates."""
        p = Pattern([1, 1, 2, 2, 3, 1, 1]).undup()
        self.assertEqual(list(p), [1, 2, 3, 1])

    def test_replace(self):
        p = Pattern([0, 1, 2, 1, 0]).replace(1, 99)
        self.assertEqual(list(p), [0, 99, 2, 99, 0])

    def test_submap(self):
        p = Pattern([0, 1, 2]).submap({0: 10, 2: 20})
        self.assertEqual(list(p), [10, 1, 20])

    def test_compress(self):
        p = Pattern([10, 20, 30, 40]).compress([1, 0, 1, 0])
        self.assertEqual(list(p), [10, 30])

    def test_select(self):
        p = Pattern([10, 20, 30, 40]).select([1, 0, 1, 0])
        self.assertEqual(list(p), [10, 30])

    def test_select_all_ones_returns_self(self):
        p = Pattern([10, 20, 30])
        result = p.select([1, 1, 1])
        self.assertIs(result, p)

    def test_map(self):
        p = Pattern([1, 2, 3]).map(lambda x: x * 10)
        self.assertEqual(list(p), [10, 20, 30])

    def test_limit(self):
        """P[0, 1, 2, 3].limit(sum, 10) adds items until func(new) >= value.
        sum reaches 12 after appending 3 the second time."""
        p = Pattern([0, 1, 2, 3]).limit(sum, 10)
        self.assertEqual(list(p), [0, 1, 2, 3, 0, 1, 2, 3])

    def test_norm(self):
        """Normalizes values between 0 and 1."""
        p = Pattern([0, 5, 10]).norm()
        result = list(p)
        self.assertEqual(result[0], 0)
        self.assertEqual(result[-1], 1.0)

    def test_copy_is_independent(self):
        p1 = Pattern([1, 2, 3])
        p2 = p1.copy()
        p2.data[0] = 99
        self.assertEqual(p1[0], 1)

    def test_true_copy(self):
        p1 = Pattern([1, 2, 3])
        p2 = p1.true_copy()
        self.assertEqual(list(p1), list(p2))

    def test_transform_int(self):
        p = Pattern([1.5, 2.7, 3.1]).int()
        self.assertEqual(list(p), [1, 2, 3])

    def test_transform_float(self):
        p = Pattern([1, 2, 3]).float()
        self.assertEqual(list(p), [1.0, 2.0, 3.0])

    def test_startswith(self):
        self.assertTrue(Pattern([1, 2, 3]).startswith(1))
        self.assertFalse(Pattern([1, 2, 3]).startswith(2))

    def test_all_method(self):
        self.assertTrue(Pattern([1, 2, 3]).all())
        self.assertFalse(Pattern([1, 0, 3]).all())
        self.assertFalse(Pattern([]).all())

    def test_count(self):
        p = Pattern([1, 2, 2, 3, 2])
        self.assertEqual(p.count(2), 3)
        self.assertEqual(p.count(9), 0)

    def test_choose_returns_element(self):
        p = Pattern([10, 20, 30])
        for _ in range(20):
            self.assertIn(p.choose(), [10, 20, 30])


# ==================================================================
# Pattern Pipe / Concat / Zip / Splice
# ==================================================================

class TestPatternComposition(unittest.TestCase):
    """Test Pattern composition operations: pipe, concat, zip, splice."""

    def test_pipe_operator(self):
        """| concatenates patterns."""
        p = Pattern([1, 2]) | Pattern([3, 4])
        self.assertEqual(list(p), [1, 2, 3, 4])

    def test_rpipe_operator(self):
        p = [1, 2] | Pattern([3, 4])
        self.assertEqual(list(p), [1, 2, 3, 4])

    def test_concat_method(self):
        p = Pattern([1, 2]).concat(Pattern([3, 4]))
        self.assertEqual(list(p), [1, 2, 3, 4])

    def test_concat_with_list(self):
        p = Pattern([1, 2]).concat([3, 4])
        self.assertEqual(list(p), [1, 2, 3, 4])

    def test_concat_with_scalar(self):
        p = Pattern([1, 2]).concat(3)
        self.assertEqual(list(p), [1, 2, 3])

    def test_zip_creates_pgroups(self):
        """& zips patterns into PGroups."""
        p = Pattern([1, 2]) & Pattern([3, 4])
        self.assertIsInstance(p[0], PGroup)
        self.assertEqual(list(p[0]), [1, 3])
        self.assertEqual(list(p[1]), [2, 4])

    def test_splice(self):
        """P[0, 1, 2, 3].splice([4, 5, 6, 7], [8, 9])."""
        p = Pattern([0, 1, 2, 3]).splice([4, 5, 6, 7], [8, 9])
        expected = [0, 4, 8, 1, 5, 9, 2, 6, 8, 3, 7, 9]
        self.assertEqual(list(p), expected)

    def test_extend_mutates(self):
        p = Pattern([1, 2])
        p.extend([3, 4])
        self.assertEqual(list(p), [1, 2, 3, 4])

    def test_append_mutates(self):
        p = Pattern([1, 2])
        p.append(3)
        self.assertEqual(list(p), [1, 2, 3])


# ==================================================================
# Pattern Comparisons
# ==================================================================

class TestPatternComparisons(unittest.TestCase):
    """Test Pattern comparison operators."""

    def test_eq_same(self):
        self.assertTrue(Pattern([1, 2, 3]) == Pattern([1, 2, 3]))

    def test_eq_different(self):
        self.assertFalse(Pattern([1, 2, 3]) == Pattern([1, 2, 4]))

    def test_ne_same(self):
        self.assertFalse(Pattern([1, 2, 3]) != Pattern([1, 2, 3]))

    def test_ne_different(self):
        self.assertTrue(Pattern([1, 2, 3]) != Pattern([1, 2, 4]))

    def test_eq_different_length(self):
        self.assertFalse(Pattern([1, 2]) == Pattern([1, 2, 3]))

    def test_gt(self):
        p = Pattern([1, 5, 3]) > Pattern([2, 2, 3])
        self.assertEqual(list(p), [0, 1, 0])

    def test_lt(self):
        p = Pattern([1, 5, 3]) < Pattern([2, 2, 3])
        self.assertEqual(list(p), [1, 0, 0])

    def test_ge(self):
        p = Pattern([1, 5, 3]) >= Pattern([2, 2, 3])
        self.assertEqual(list(p), [0, 1, 1])

    def test_le(self):
        p = Pattern([1, 5, 3]) <= Pattern([2, 2, 3])
        self.assertEqual(list(p), [1, 0, 1])

    def test_gt_scalar(self):
        p = Pattern([1, 5, 3]) > 2
        self.assertEqual(list(p), [0, 1, 1])

    def test_eq_method(self):
        """The .eq() method returns element-wise int comparison."""
        p = Pattern([1, 2, 3]).eq(Pattern([1, 9, 3]))
        self.assertEqual(list(p), [1, 0, 1])

    def test_ne_method(self):
        p = Pattern([1, 2, 3]).ne(Pattern([1, 9, 3]))
        self.assertEqual(list(p), [0, 1, 0])


# ==================================================================
# Pattern String / Repr
# ==================================================================

class TestPatternString(unittest.TestCase):
    """Test Pattern string representations."""

    def test_str_flat(self):
        p = Pattern([0, 1, 2])
        self.assertEqual(str(p), "P[0, 1, 2]")

    def test_str_with_pgroup(self):
        p = Pattern([0, PGroup([1, 2])])
        s = str(p)
        self.assertIn("P[", s)

    def test_repr_equals_str(self):
        p = Pattern([1, 2, 3])
        self.assertEqual(repr(p), str(p))


# ==================================================================
# Pattern Bool
# ==================================================================

class TestPatternBool(unittest.TestCase):
    """Test Pattern truthiness."""

    def test_all_positive_is_true(self):
        self.assertTrue(bool(Pattern([1, 2, 3])))

    def test_has_zero_is_false(self):
        self.assertFalse(bool(Pattern([1, 0, 3])))

    def test_has_negative_is_false(self):
        self.assertFalse(bool(Pattern([1, -1, 3])))


# ==================================================================
# PGroup
# ==================================================================

class TestPGroup(unittest.TestCase):
    """Test PGroup creation and behaviour."""

    def test_create_from_tuple(self):
        g = PGroup((0, 1, 2))
        self.assertEqual(list(g), [0, 1, 2])

    def test_create_from_args(self):
        g = PGroup(0, 1, 2)
        self.assertEqual(list(g), [0, 1, 2])

    def test_create_from_list(self):
        g = PGroup([0, 1, 2])
        self.assertEqual(list(g), [0, 1, 2])

    def test_pgroup_weight(self):
        """PGroup has higher WEIGHT than Pattern (for dominant pattern resolution)."""
        self.assertGreater(PGroup.WEIGHT, Pattern.WEIGHT)

    def test_bracket_style(self):
        self.assertEqual(PGroup.bracket_style, "()")
        self.assertEqual(Pattern.bracket_style, "[]")

    def test_pgroup_in_pattern(self):
        """A tuple in a Pattern becomes a PGroup."""
        p = Pattern([(0, 1), 2, 3])
        self.assertIsInstance(p[0], PGroup)

    def test_pgroup_length(self):
        g = PGroup((1, 2, 3))
        self.assertEqual(len(g), 3)

    def test_pgroup_indexing(self):
        g = PGroup((10, 20, 30))
        self.assertEqual(g[0], 10)
        self.assertEqual(g[1], 20)
        self.assertEqual(g[2], 30)

    def test_pgroup_wrapping(self):
        g = PGroup((10, 20))
        self.assertEqual(g[2], 10)
        self.assertEqual(g[3], 20)

    def test_pgroup_add_scalar(self):
        g = PGroup((1, 2, 3)) + 10
        self.assertEqual(list(g), [11, 12, 13])

    def test_pgroup_mul_scalar(self):
        g = PGroup((1, 2, 3)) * 2
        self.assertEqual(list(g), [2, 4, 6])

    def test_pgroup_merge(self):
        g = PGroup((1, 2)).merge(3)
        self.assertEqual(list(g), [1, 2, 3])

    def test_pgroup_flatten(self):
        g = PGroup([0, PGroup([3, 5])]).flatten()
        self.assertEqual(list(g), [0, 3, 5])

    def test_pgroup_concat(self):
        g = PGroup((1, 2)).concat(PGroup((3, 4)))
        self.assertEqual(list(g), [1, 2, 3, 4])

    def test_pgroup_eq(self):
        g1 = PGroup((1, 2, 3))
        g2 = PGroup((1, 2, 3))
        result = g1.eq(g2)
        self.assertEqual(list(result), [1, 1, 1])

    def test_pgroup_ne(self):
        g1 = PGroup((1, 2, 3))
        g2 = PGroup((1, 9, 3))
        result = g1.ne(g2)
        self.assertEqual(list(result), [0, 1, 0])

    def test_pgroup_gt(self):
        g = PGroup((1, 5, 3)) > 2
        self.assertEqual(list(g), [0, 1, 1])

    def test_pgroup_lt(self):
        g = PGroup((1, 5, 3)) < 2
        self.assertEqual(list(g), [1, 0, 0])

    def test_has_behaviour_plain_pgroup(self):
        """A plain PGroup has no special behaviour."""
        self.assertFalse(PGroup((1, 2)).has_behaviour())

    def test_calculate_time_plain(self):
        """Plain PGroup returns all-zero delays."""
        g = PGroup((1, 2, 3))
        delays = g.calculate_time(1.0)
        self.assertEqual(list(delays), [0, 0, 0])


# ==================================================================
# POperand
# ==================================================================

class TestPOperand(unittest.TestCase):
    """Test the POperand class for element-wise pattern operations."""

    def test_padd(self):
        result = PAdd(Pattern([1, 2, 3]), Pattern([10, 20, 30]))
        self.assertEqual(list(result), [11, 22, 33])

    def test_psub(self):
        result = PSub(Pattern([10, 20, 30]), Pattern([1, 2, 3]))
        self.assertEqual(list(result), [9, 18, 27])

    def test_pmul(self):
        result = PMul(Pattern([2, 3]), Pattern([4, 5]))
        self.assertEqual(list(result), [8, 15])

    def test_pdiv(self):
        result = PDiv(Pattern([10, 20]), Pattern([2, 5]))
        self.assertEqual(list(result), [5.0, 4.0])

    def test_pfloor(self):
        result = PFloor(Pattern([7, 13]), Pattern([2, 5]))
        self.assertEqual(list(result), [3, 2])

    def test_pmod(self):
        result = PMod(Pattern([10, 13]), Pattern([3, 5]))
        self.assertEqual(list(result), [1, 3])

    def test_ppow(self):
        result = PPow(Pattern([2, 3]), Pattern([3, 2]))
        self.assertEqual(list(result), [8, 9])

    def test_different_lengths_lcm(self):
        """Operations on patterns of different lengths expand to LCM."""
        result = PAdd(Pattern([1, 2, 3]), Pattern([10, 20]))
        # LCM(3, 2) = 6
        self.assertEqual(len(result), 6)
        self.assertEqual(list(result), [11, 22, 13, 21, 12, 23])

    def test_empty_pattern_returns_class(self):
        """Operating on an empty pattern returns the other wrapped in the same class."""
        result = PAdd(Pattern([]), Pattern([1, 2, 3]))
        self.assertIsInstance(result, Pattern)

    def test_div_by_zero_pattern(self):
        """Division by zero in POperand returns 0."""
        result = PDiv(Pattern([10, 20]), Pattern([0, 5]))
        self.assertEqual(list(result)[0], 0)
        self.assertEqual(list(result)[1], 4.0)

    def test_peq_true(self):
        self.assertTrue(PEq(Pattern([1, 2, 3]), Pattern([1, 2, 3])))

    def test_peq_false(self):
        self.assertFalse(PEq(Pattern([1, 2, 3]), Pattern([1, 2, 4])))

    def test_peq_different_length(self):
        self.assertFalse(PEq(Pattern([1, 2]), Pattern([1, 2, 3])))

    def test_peq_different_class(self):
        self.assertFalse(PEq(Pattern([1, 2]), PGroup([1, 2])))

    def test_pne_same(self):
        self.assertFalse(PNe(Pattern([1, 2, 3]), Pattern([1, 2, 3])))

    def test_pne_different(self):
        self.assertTrue(PNe(Pattern([1, 2, 3]), Pattern([1, 2, 4])))

    def test_custom_poperand(self):
        """Custom POperand with a lambda."""
        PMax = POperand(lambda a, b: max(a, b))
        result = PMax(Pattern([1, 5, 3]), Pattern([4, 2, 6]))
        self.assertEqual(list(result), [4, 5, 6])


# ==================================================================
# GeneratorPattern
# ==================================================================

class TestGeneratorPattern(unittest.TestCase):
    """Test GeneratorPattern base class."""

    def test_default_func_returns_index(self):
        g = GeneratorPattern()
        self.assertEqual(g.getitem(0), 0)
        self.assertEqual(g.getitem(5), 5)

    def test_caching(self):
        """Same index returns the same cached value."""
        g = GeneratorPattern()
        val1 = g.getitem(3)
        val2 = g.getitem(3)
        self.assertEqual(val1, val2)

    def test_arithmetic_creates_new_generator(self):
        g = GeneratorPattern() + 10
        self.assertIsInstance(g, GeneratorPattern)
        self.assertEqual(g.getitem(0), 10)
        self.assertEqual(g.getitem(5), 15)

    def test_mul_generator(self):
        g = GeneratorPattern() * 3
        self.assertEqual(g.getitem(2), 6)

    def test_sub_generator(self):
        g = GeneratorPattern() - 1
        self.assertEqual(g.getitem(5), 4)

    def test_from_func(self):
        g = GeneratorPattern.from_func(lambda i: i ** 2)
        self.assertEqual(g.getitem(0), 0)
        self.assertEqual(g.getitem(3), 9)
        self.assertEqual(g.getitem(5), 25)

    def test_slice_returns_pattern(self):
        g = GeneratorPattern()
        p = g[0:5]
        self.assertIsInstance(p, Pattern)
        self.assertEqual(list(p), [0, 1, 2, 3, 4])


# ==================================================================
# Pattern In-Place Mutation Methods
# ==================================================================

class TestPatternInPlace(unittest.TestCase):
    """Test in-place mutation methods."""

    def test_i_rotate(self):
        p = Pattern([1, 2, 3, 4])
        result = p.i_rotate(1)
        self.assertIs(result, p)
        self.assertEqual(p.data, [2, 3, 4, 1])

    def test_i_reverse(self):
        p = Pattern([1, 2, 3])
        result = p.i_reverse()
        self.assertIs(result, p)
        self.assertEqual(p.data, [3, 2, 1])

    def test_set(self):
        p = Pattern([10, 20, 30])
        p.set(1, 99)
        self.assertEqual(p.data[1].data, [99])

    def test_setitem(self):
        p = Pattern([10, 20, 30])
        p[1] = 99
        self.assertEqual(p[1], 99)


# ==================================================================
# Pattern every() and layer()
# ==================================================================

class TestPatternEveryAndLayer(unittest.TestCase):
    """Test every() and layer() composition methods."""

    def test_every(self):
        """every(n, method) → loop(n-1) + method()."""
        p = Pattern([0, 1, 2, 3]).every(2, "reverse")
        expected = [0, 1, 2, 3, 3, 2, 1, 0]
        self.assertEqual(list(p), expected)

    def test_layer_with_method_name(self):
        """layer('reverse') zips pattern with its reverse."""
        p = Pattern([1, 2, 3]).layer("reverse")
        # Each element is a PGroup of (original, reversed)
        self.assertEqual(len(p), 3)
        self.assertIsInstance(p[0], PGroup)

    def test_layer_with_callable(self):
        p = Pattern([1, 2, 3]).layer(lambda x: x * 10)
        self.assertIsInstance(p[0], PGroup)


# ==================================================================
# Nested Pattern Behaviour (from docstring)
# ==================================================================

class TestNestedPatternBehaviour(unittest.TestCase):
    """Tests based on the Pattern class docstring examples."""

    def test_nested_list_equals_expanded(self):
        """P[0, 1, 2, [3, 4]] == P[0, 1, 2, 3, 0, 1, 2, 4]."""
        a = Pattern([0, 1, 2, Pattern([3, 4])])
        b = Pattern([0, 1, 2, 3, 0, 1, 2, 4])
        self.assertTrue(a == b)

    def test_nested_access_first(self):
        p = Pattern([0, 1, 2, Pattern([3, 4])])
        self.assertEqual(p[3], 3)

    def test_nested_access_second(self):
        p = Pattern([0, 1, 2, Pattern([3, 4])])
        self.assertEqual(p[7], 4)

    def test_p_shorthand_group(self):
        """P(0, 1, 2) creates a PGroup."""
        g = P(0, 1, 2)
        self.assertIsInstance(g, PGroup)
        self.assertEqual(list(g), [0, 1, 2])

    def test_tuple_in_pattern_becomes_pgroup(self):
        """Tuples nested in a Pattern list become PGroups."""
        p = Pattern([(5, 6), 1, 2])
        self.assertIsInstance(p[0], PGroup)


# ==================================================================
# Edge Cases
# ==================================================================

class TestPatternEdgeCases(unittest.TestCase):
    """Edge cases and boundary conditions."""

    def test_single_item_pattern_arithmetic(self):
        p = Pattern([5]) + 10
        self.assertEqual(list(p), [15])

    def test_pattern_of_patterns_arithmetic(self):
        """Arithmetic on patterns containing nested patterns."""
        p = Pattern([1, Pattern([2, 3])]) + 10
        result = list(p)
        self.assertEqual(result[0], 11)
        self.assertEqual(result[1], 12)
        self.assertEqual(result[2], 11)
        self.assertEqual(result[3], 13)

    def test_deeply_nested_iteration(self):
        """P[0, [1, [2, 3]]] expanded correctly."""
        inner = Pattern([2, 3])
        mid = Pattern([1, inner])
        p = Pattern([0, mid])
        # len(mid) = 4 (2 items * LCM(1,2)), len(p) = 8 (2 items * LCM(1,4))
        values = list(p)
        self.assertEqual(len(values), 8)

    def test_mixed_types_in_pattern(self):
        """Patterns can hold mixed numeric types."""
        p = Pattern([1, 2.5, 3])
        self.assertEqual(p[0], 1)
        self.assertEqual(p[1], 2.5)
        self.assertEqual(p[2], 3)

    def test_pgroup_with_pattern_inverts(self):
        """PGroup containing a Pattern inverts to Pattern of PGroups."""
        g = PGroup(0, 1, Pattern([2, 3, 4]))
        # This should become a Pattern of PGroups
        self.assertIsInstance(g, Pattern)
        self.assertEqual(len(g.data), 3)

    def test_convert_data_to_float(self):
        p = Pattern([1, 2, 3]).convert_data(float)
        self.assertEqual(list(p), [1.0, 2.0, 3.0])


if __name__ == "__main__":
    unittest.main()
