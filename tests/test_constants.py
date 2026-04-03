"""Unit tests for FoxDot.lib.Constants — const, _inf, NoneConst, and inf singleton."""

import unittest

from FoxDot.lib.Constants import const, _inf, inf, NoneConst


# ==================================================================
# const class — immutable numeric wrapper
# ==================================================================

class TestConstCreation(unittest.TestCase):
    """Test const object creation with scalar values."""

    def test_create_int(self):
        c = const(5)
        self.assertEqual(c.value, 5)

    def test_create_float(self):
        c = const(3.14)
        self.assertAlmostEqual(c.value, 3.14)

    def test_create_negative(self):
        c = const(-10)
        self.assertEqual(c.value, -10)

    def test_create_zero(self):
        c = const(0)
        self.assertEqual(c.value, 0)


class TestConstRepr(unittest.TestCase):
    """Test const string representation."""

    def test_repr_int(self):
        self.assertEqual(repr(const(42)), "42")

    def test_repr_float(self):
        self.assertEqual(repr(const(1.5)), "1.5")

    def test_repr_negative(self):
        self.assertEqual(repr(const(-7)), "-7")

    def test_repr_zero(self):
        self.assertEqual(repr(const(0)), "0")


class TestConstTypeConversion(unittest.TestCase):
    """Test int() and float() conversions."""

    def test_int_from_int(self):
        self.assertEqual(int(const(7)), 7)

    def test_int_from_float(self):
        self.assertEqual(int(const(3.9)), 3)

    def test_float_from_int(self):
        self.assertAlmostEqual(float(const(5)), 5.0)

    def test_float_from_float(self):
        self.assertAlmostEqual(float(const(2.5)), 2.5)


class TestConstArithmetic(unittest.TestCase):
    """const arithmetic always returns the original value (immutable)."""

    def test_add_returns_value(self):
        c = const(10)
        self.assertEqual(c + 5, 10)

    def test_radd_returns_value(self):
        c = const(10)
        self.assertEqual(5 + c, 10)

    def test_sub_returns_value(self):
        c = const(10)
        self.assertEqual(c - 3, 10)

    def test_rsub_returns_value(self):
        c = const(10)
        self.assertEqual(3 - c, 10)

    def test_mul_returns_value(self):
        c = const(10)
        self.assertEqual(c * 2, 10)

    def test_rmul_returns_value(self):
        c = const(10)
        self.assertEqual(2 * c, 10)

    def test_div_returns_value(self):
        c = const(10)
        self.assertEqual(c.__div__(2), 10)

    def test_rdiv_returns_value(self):
        c = const(10)
        self.assertEqual(c.__rdiv__(2), 10)

    def test_add_with_zero(self):
        c = const(0)
        self.assertEqual(c + 100, 0)

    def test_add_with_negative(self):
        c = const(-5)
        self.assertEqual(c + 10, -5)


class TestConstComparisons(unittest.TestCase):
    """Test comparison operators on const."""

    def test_gt_true(self):
        self.assertTrue(const(10) > 5)

    def test_gt_false(self):
        self.assertFalse(const(3) > 5)

    def test_gt_equal_false(self):
        self.assertFalse(const(5) > 5)

    def test_ge_true_greater(self):
        self.assertTrue(const(10) >= 5)

    def test_ge_true_equal(self):
        self.assertTrue(const(5) >= 5)

    def test_ge_false(self):
        self.assertFalse(const(3) >= 5)

    def test_lt_true(self):
        self.assertTrue(const(3) < 5)

    def test_lt_false(self):
        self.assertFalse(const(10) < 5)

    def test_lt_equal_false(self):
        self.assertFalse(const(5) < 5)

    def test_le_true_less(self):
        self.assertTrue(const(3) <= 5)

    def test_le_true_equal(self):
        self.assertTrue(const(5) <= 5)

    def test_le_false(self):
        self.assertFalse(const(10) <= 5)

    def test_eq_true(self):
        self.assertTrue(const(5) == 5)

    def test_eq_false(self):
        self.assertFalse(const(5) == 6)

    def test_ne_true(self):
        self.assertTrue(const(5) != 6)

    def test_ne_false(self):
        self.assertFalse(const(5) != 5)

    def test_eq_float(self):
        self.assertTrue(const(5.0) == 5.0)

    def test_ne_different_types(self):
        self.assertTrue(const(5) != "5")


# ==================================================================
# _inf class — infinite value
# ==================================================================

class TestInfRepr(unittest.TestCase):
    """Test _inf string representation."""

    def test_repr(self):
        self.assertEqual(repr(inf), "inf")

    def test_repr_constructed(self):
        self.assertEqual(repr(_inf(100)), "inf")


class TestInfArithmetic(unittest.TestCase):
    """_inf arithmetic returns new _inf objects (unlike const)."""

    def test_add_returns_inf(self):
        result = inf + 5
        self.assertIsInstance(result, _inf)

    def test_radd_returns_inf(self):
        result = 5 + inf
        self.assertIsInstance(result, _inf)

    def test_sub_returns_inf(self):
        result = inf - 3
        self.assertIsInstance(result, _inf)

    def test_rsub_returns_inf(self):
        result = 3 - inf
        self.assertIsInstance(result, _inf)

    def test_mul_returns_inf(self):
        result = inf * 2
        self.assertIsInstance(result, _inf)

    def test_rmul_returns_inf(self):
        result = 2 * inf
        self.assertIsInstance(result, _inf)

    def test_div_returns_inf(self):
        result = inf.__div__(2)
        self.assertIsInstance(result, _inf)

    def test_rdiv_returns_inf(self):
        result = inf.__rdiv__(2)
        self.assertIsInstance(result, _inf)

    def test_truediv_returns_inf(self):
        result = inf / 2
        self.assertIsInstance(result, _inf)

    def test_rtruediv_returns_inf(self):
        result = 2 / inf
        self.assertIsInstance(result, _inf)

    def test_add_preserves_value(self):
        result = _inf(10) + 5
        self.assertEqual(result.value, 15)

    def test_sub_preserves_value(self):
        result = _inf(10) - 3
        self.assertEqual(result.value, 7)

    def test_mul_preserves_value(self):
        result = _inf(10) * 2
        self.assertEqual(result.value, 20)

    def test_truediv_preserves_value(self):
        result = _inf(10) / 2
        self.assertAlmostEqual(result.value, 5.0)

    def test_radd_preserves_value(self):
        result = 5 + _inf(10)
        self.assertEqual(result.value, 15)

    def test_rsub_preserves_value(self):
        result = 20 - _inf(10)
        self.assertEqual(result.value, 10)

    def test_rmul_preserves_value(self):
        result = 3 * _inf(10)
        self.assertEqual(result.value, 30)

    def test_rtruediv_preserves_value(self):
        result = 20 / _inf(10)
        self.assertAlmostEqual(result.value, 2.0)


class TestInfComparisons(unittest.TestCase):
    """Test _inf comparison behavior."""

    def test_eq_inf_equals_inf(self):
        self.assertTrue(inf == inf)

    def test_eq_inf_equals_other_inf(self):
        self.assertTrue(inf == _inf(100))

    def test_eq_inf_not_equals_number(self):
        self.assertFalse(inf == 999999)

    def test_eq_inf_not_equals_string(self):
        self.assertFalse(inf == "inf")

    def test_gt_inf_greater_than_number(self):
        self.assertTrue(inf > 999999)

    def test_gt_inf_not_greater_than_inf(self):
        self.assertFalse(inf > _inf(0))

    def test_ge_always_true(self):
        self.assertTrue(inf >= 999999)

    def test_ge_true_for_inf(self):
        self.assertTrue(inf >= _inf(0))

    def test_lt_always_false(self):
        self.assertFalse(inf < 999999)

    def test_lt_false_for_inf(self):
        self.assertFalse(inf < _inf(0))

    def test_le_true_for_inf(self):
        self.assertTrue(inf <= _inf(0))

    def test_le_false_for_number(self):
        self.assertFalse(inf <= 999999)


class TestInfSingleton(unittest.TestCase):
    """Test the inf module-level singleton."""

    def test_inf_is_inf_type(self):
        self.assertIsInstance(inf, _inf)

    def test_inf_value_is_zero(self):
        self.assertEqual(inf.value, 0)


# ==================================================================
# NoneConst class
# ==================================================================

class TestNoneConst(unittest.TestCase):
    """Test NoneConst — a const wrapping None."""

    def test_value_is_none(self):
        nc = NoneConst()
        self.assertIsNone(nc.value)

    def test_repr(self):
        nc = NoneConst()
        self.assertEqual(repr(nc), "None")

    def test_add_returns_none(self):
        nc = NoneConst()
        self.assertIsNone(nc + 5)

    def test_sub_returns_none(self):
        nc = NoneConst()
        self.assertIsNone(nc - 3)

    def test_mul_returns_none(self):
        nc = NoneConst()
        self.assertIsNone(nc * 2)

    def test_eq_none(self):
        nc = NoneConst()
        self.assertTrue(nc == None)  # noqa: E711 — intentional test of __eq__

    def test_ne_number(self):
        nc = NoneConst()
        self.assertTrue(nc != 5)

    def test_is_subclass_of_const(self):
        self.assertTrue(issubclass(NoneConst, const))


# ==================================================================
# const with collection types (Pattern/PGroup promotion)
# ==================================================================

class TestConstWithCollections(unittest.TestCase):
    """Test that const promotes lists and tuples to Pattern/PGroup."""

    def test_list_becomes_pattern(self):
        from FoxDot.lib.Patterns import Pattern
        c = const([1, 2, 3])
        self.assertIsInstance(c, Pattern)

    def test_tuple_becomes_pgroup(self):
        from FoxDot.lib.Patterns import PGroup
        c = const((1, 2, 3))
        self.assertIsInstance(c, PGroup)

    def test_list_elements_are_const(self):
        from FoxDot.lib.Patterns import Pattern
        c = const([10, 20])
        self.assertIsInstance(c, Pattern)
        for item in c:
            self.assertIsInstance(item, const)

    def test_tuple_elements_are_const(self):
        from FoxDot.lib.Patterns import PGroup
        c = const((10, 20))
        self.assertIsInstance(c, PGroup)
        for item in c:
            self.assertIsInstance(item, const)

    def test_list_const_elements_are_immutable(self):
        from FoxDot.lib.Patterns import Pattern
        c = const([5, 10])
        self.assertIsInstance(c, Pattern)
        # Each element should be a const that ignores arithmetic
        elem = c[0]
        if isinstance(elem, const):
            self.assertEqual(elem + 100, elem.value)


# ==================================================================
# Edge cases
# ==================================================================

class TestConstEdgeCases(unittest.TestCase):
    """Edge case testing for const."""

    def test_const_with_large_value(self):
        c = const(10**18)
        self.assertEqual(c.value, 10**18)

    def test_const_add_returns_same_regardless_of_operand(self):
        c = const(42)
        self.assertEqual(c + 0, 42)
        self.assertEqual(c + 100, 42)
        self.assertEqual(c + (-100), 42)

    def test_inf_chained_operations(self):
        result = (inf + 5) * 2
        self.assertIsInstance(result, _inf)

    def test_inf_chained_value(self):
        result = (_inf(10) + 5) * 2
        self.assertEqual(result.value, 30)


if __name__ == "__main__":
    unittest.main()
