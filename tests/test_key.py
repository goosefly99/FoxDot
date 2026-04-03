"""Unit tests for FoxDot.lib.Key — NumberKey, PlayerKey, convert_to_pattern,
Accompany, and related helper functions."""

import unittest

from FoxDot.lib.Key import NumberKey, PlayerKey, Accompany, convert_to_pattern
from FoxDot.lib.Patterns import Pattern, PGroup, metaPattern


# ==================================================================
# convert_to_pattern helper
# ==================================================================

class TestConvertToPattern(unittest.TestCase):
    """Test the convert_to_pattern utility function."""

    def test_list_becomes_pattern(self):
        result = convert_to_pattern([1, 2, 3])
        self.assertIsInstance(result, Pattern)

    def test_tuple_becomes_pgroup(self):
        result = convert_to_pattern((1, 2, 3))
        self.assertIsInstance(result, PGroup)

    def test_pattern_stays_pattern(self):
        p = Pattern([1, 2, 3])
        result = convert_to_pattern(p)
        self.assertIs(result, p)

    def test_scalar_becomes_pattern(self):
        result = convert_to_pattern(5)
        self.assertIsInstance(result, metaPattern)

    def test_string_becomes_pattern(self):
        result = convert_to_pattern("hello")
        self.assertIsInstance(result, metaPattern)


# ==================================================================
# NumberKey creation
# ==================================================================

class TestNumberKeyCreation(unittest.TestCase):
    """Test NumberKey initialization."""

    def test_default_value(self):
        k = NumberKey()
        self.assertEqual(k.value, 0)

    def test_int_value(self):
        k = NumberKey(5)
        self.assertEqual(k.value, 5)

    def test_float_value(self):
        k = NumberKey(3.14)
        self.assertAlmostEqual(k.value, 3.14)

    def test_negative_value(self):
        k = NumberKey(-10)
        self.assertEqual(k.value, -10)

    def test_custom_function(self):
        k = NumberKey(5, lambda x: x * 2)
        self.assertEqual(k.now(), 10)

    def test_default_function_is_identity(self):
        k = NumberKey(7)
        self.assertEqual(k.now(), 7)


# ==================================================================
# NumberKey.now()
# ==================================================================

class TestNumberKeyNow(unittest.TestCase):
    """Test the now() method for value retrieval."""

    def test_now_returns_value(self):
        k = NumberKey(42)
        self.assertEqual(k.now(), 42)

    def test_now_applies_function(self):
        k = NumberKey(10, lambda x: x + 1)
        self.assertEqual(k.now(), 11)

    def test_now_with_nested_key(self):
        parent = NumberKey(5)
        child = NumberKey(parent, lambda x: x * 3)
        self.assertEqual(child.now(), 15)

    def test_now_chain_depth_2(self):
        root = NumberKey(2)
        mid = NumberKey(root, lambda x: x + 10)
        leaf = NumberKey(mid, lambda x: x * 2)
        self.assertEqual(leaf.now(), 24)  # (2 + 10) * 2


# ==================================================================
# NumberKey type conversions
# ==================================================================

class TestNumberKeyTypeConversions(unittest.TestCase):
    """Test __int__, __float__, __str__, __repr__, __bool__."""

    def test_int(self):
        self.assertEqual(int(NumberKey(7)), 7)

    def test_int_truncates_float(self):
        self.assertEqual(int(NumberKey(3.9)), 3)

    def test_float(self):
        self.assertAlmostEqual(float(NumberKey(5)), 5.0)

    def test_str(self):
        self.assertEqual(str(NumberKey(42)), "42")

    def test_repr(self):
        self.assertEqual(repr(NumberKey(42)), "42")

    def test_bool_true(self):
        self.assertTrue(bool(NumberKey(1)))

    def test_bool_false(self):
        self.assertFalse(bool(NumberKey(0)))

    def test_bool_negative_is_true(self):
        self.assertTrue(bool(NumberKey(-1)))


# ==================================================================
# NumberKey parent/root relationships
# ==================================================================

class TestNumberKeyParentRoot(unittest.TestCase):
    """Test parent(), get_root(), is_root(), path_to_root()."""

    def test_root_has_no_parent(self):
        k = NumberKey(5)
        self.assertIsNone(k.parent())

    def test_is_root_true(self):
        k = NumberKey(5)
        self.assertTrue(k.is_root())

    def test_child_has_parent(self):
        parent = NumberKey(5)
        child = NumberKey(parent)
        self.assertIs(child.parent(), parent)

    def test_child_is_not_root(self):
        parent = NumberKey(5)
        child = NumberKey(parent)
        self.assertFalse(child.is_root())

    def test_get_root_returns_self_for_root(self):
        k = NumberKey(5)
        self.assertIs(k.get_root(), k)

    def test_get_root_returns_ancestor(self):
        root = NumberKey(5)
        mid = NumberKey(root)
        leaf = NumberKey(mid)
        self.assertIs(leaf.get_root(), root)

    def test_path_to_root(self):
        root = NumberKey(1)
        mid = NumberKey(root)
        leaf = NumberKey(mid)
        path = list(leaf.path_to_root())
        self.assertEqual(path, [mid, root])


# ==================================================================
# NumberKey arithmetic — returns child NumberKeys
# ==================================================================

class TestNumberKeyArithmetic(unittest.TestCase):
    """Test arithmetic operators produce new NumberKey objects."""

    def test_add_creates_child(self):
        k = NumberKey(10)
        result = k + 5
        self.assertIsInstance(result, NumberKey)
        self.assertEqual(result.now(), 15)

    def test_radd(self):
        k = NumberKey(10)
        result = 5 + k
        self.assertIsInstance(result, NumberKey)
        self.assertEqual(result.now(), 15)

    def test_sub(self):
        k = NumberKey(10)
        result = k - 3
        self.assertIsInstance(result, NumberKey)
        self.assertEqual(result.now(), 7)

    def test_rsub(self):
        k = NumberKey(3)
        result = 10 - k
        self.assertIsInstance(result, NumberKey)
        self.assertEqual(result.now(), 7)

    def test_mul(self):
        k = NumberKey(5)
        result = k * 3
        self.assertIsInstance(result, NumberKey)
        self.assertEqual(result.now(), 15)

    def test_rmul(self):
        k = NumberKey(5)
        result = 3 * k
        self.assertIsInstance(result, NumberKey)
        self.assertEqual(result.now(), 15)

    def test_truediv(self):
        k = NumberKey(10)
        result = k / 2
        self.assertIsInstance(result, NumberKey)
        self.assertAlmostEqual(result.now(), 5.0)

    def test_rtruediv(self):
        k = NumberKey(2)
        result = 10 / k
        self.assertIsInstance(result, NumberKey)
        self.assertAlmostEqual(result.now(), 5.0)

    def test_floordiv(self):
        k = NumberKey(10)
        result = k // 3
        self.assertIsInstance(result, NumberKey)
        self.assertEqual(result.now(), 3)

    def test_rfloordiv(self):
        k = NumberKey(3)
        result = 10 // k
        self.assertIsInstance(result, NumberKey)
        self.assertEqual(result.now(), 3)

    def test_mod(self):
        k = NumberKey(10)
        result = k % 3
        self.assertIsInstance(result, NumberKey)
        self.assertEqual(result.now(), 1)

    def test_rmod(self):
        k = NumberKey(3)
        result = 10 % k
        self.assertIsInstance(result, NumberKey)
        self.assertEqual(result.now(), 1)

    def test_pow(self):
        k = NumberKey(2)
        result = k ** 3
        self.assertIsInstance(result, NumberKey)
        self.assertEqual(result.now(), 8)

    def test_xor_is_pow(self):
        k = NumberKey(2)
        result = k ^ 3
        self.assertIsInstance(result, NumberKey)
        self.assertEqual(result.now(), 8)

    def test_abs(self):
        k = NumberKey(-5)
        result = abs(k)
        self.assertIsInstance(result, NumberKey)
        self.assertEqual(result.now(), 5)

    def test_abs_positive(self):
        k = NumberKey(5)
        result = abs(k)
        self.assertEqual(result.now(), 5)


class TestNumberKeyChainedArithmetic(unittest.TestCase):
    """Test chained arithmetic operations."""

    def test_add_then_mul(self):
        k = NumberKey(5)
        result = (k + 3) * 2
        self.assertIsInstance(result, NumberKey)
        self.assertEqual(result.now(), 16)  # (5 + 3) * 2

    def test_sub_then_add(self):
        k = NumberKey(10)
        result = (k - 3) + 1
        self.assertIsInstance(result, NumberKey)
        self.assertEqual(result.now(), 8)  # (10 - 3) + 1

    def test_mul_then_div(self):
        k = NumberKey(6)
        result = (k * 3) / 2
        self.assertIsInstance(result, NumberKey)
        self.assertAlmostEqual(result.now(), 9.0)  # (6 * 3) / 2

    def test_dynamic_value_propagates(self):
        """Child keys should see updated parent values when value changes."""
        parent = NumberKey(5)
        child = parent + 10
        self.assertEqual(child.now(), 15)
        # Change parent's value
        parent.value = 20
        self.assertEqual(child.now(), 30)


# ==================================================================
# NumberKey comparisons
# ==================================================================

class TestNumberKeyComparisons(unittest.TestCase):
    """Test comparison operators return NumberKey children."""

    def test_eq(self):
        k = NumberKey(5)
        result = k == 5
        self.assertIsInstance(result, NumberKey)
        self.assertTrue(result.now())

    def test_eq_false(self):
        k = NumberKey(5)
        result = k == 6
        self.assertFalse(result.now())

    def test_ne(self):
        k = NumberKey(5)
        result = k != 6
        self.assertTrue(result.now())

    def test_gt(self):
        k = NumberKey(10)
        result = k > 5
        self.assertTrue(result.now())

    def test_gt_false(self):
        k = NumberKey(3)
        result = k > 5
        self.assertFalse(result.now())

    def test_ge(self):
        k = NumberKey(5)
        result = k >= 5
        self.assertTrue(result.now())

    def test_lt(self):
        k = NumberKey(3)
        result = k < 5
        self.assertTrue(result.now())

    def test_le(self):
        k = NumberKey(5)
        result = k <= 5
        self.assertTrue(result.now())


# ==================================================================
# NumberKey iteration
# ==================================================================

class TestNumberKeyIteration(unittest.TestCase):
    """Test __iter__ and __len__."""

    def test_iter_scalar_yields_value(self):
        k = NumberKey(5)
        items = list(k)
        self.assertEqual(items, [5])

    def test_getitem(self):
        k = NumberKey([10, 20, 30])
        result = k[1]
        self.assertIsInstance(result, NumberKey)
        self.assertEqual(result.now(), 20)


# ==================================================================
# NumberKey.transform
# ==================================================================

class TestNumberKeyTransform(unittest.TestCase):
    """Test the transform() method."""

    def test_transform_simple(self):
        k = NumberKey(5)
        result = k.transform(lambda x: x ** 2)
        self.assertEqual(result.now(), 25)

    def test_transform_returns_child(self):
        k = NumberKey(5)
        result = k.transform(lambda x: x + 1)
        self.assertIsInstance(result, NumberKey)

    def test_transform_chained(self):
        k = NumberKey(2)
        result = k.transform(lambda x: x + 3).transform(lambda x: x * 10)
        self.assertEqual(result.now(), 50)  # (2 + 3) * 10


# ==================================================================
# NumberKey.spawn_child
# ==================================================================

class TestNumberKeySpawnChild(unittest.TestCase):
    """Test spawn_child method."""

    def test_spawn_child_returns_number_key(self):
        k = NumberKey(10)
        child = k.spawn_child(lambda x: x * 2)
        self.assertIsInstance(child, NumberKey)
        self.assertEqual(child.now(), 20)

    def test_spawn_child_links_to_parent(self):
        parent = NumberKey(10)
        child = parent.spawn_child(lambda x: x + 1)
        self.assertIs(child.parent(), parent)


# ==================================================================
# NumberKey.simple_map
# ==================================================================

class TestNumberKeySimpleMap(unittest.TestCase):
    """Test the simple_map method."""

    def test_simple_map_raises_on_non_dict(self):
        k = NumberKey(5)
        with self.assertRaises(TypeError):
            k.simple_map([1, 2, 3])

    def test_simple_map_returns_number_key(self):
        k = NumberKey(1)
        result = k.simple_map({1: 10, 2: 20})
        self.assertIsInstance(result, NumberKey)


# ==================================================================
# NumberKey.map
# ==================================================================

class TestNumberKeyMap(unittest.TestCase):
    """Test the map method."""

    def test_map_returns_number_key(self):
        k = NumberKey(5)
        result = k.map({5: 100}, default=0)
        self.assertIsInstance(result, NumberKey)

    def test_map_matching_key(self):
        k = NumberKey(5)
        result = k.map({5: 100}, default=0)
        self.assertEqual(result.now(), 100)

    def test_map_default_value(self):
        k = NumberKey(3)
        result = k.map({5: 100}, default=-1)
        self.assertEqual(result.now(), -1)

    def test_map_with_callable_value(self):
        k = NumberKey(5)
        result = k.map({5: lambda x: x * 10}, default=0)
        self.assertEqual(result.now(), 50)


# ==================================================================
# NumberKey.get_min / get_max
# ==================================================================

class TestNumberKeyMinMax(unittest.TestCase):
    """Test get_min and get_max methods."""

    def test_get_min_with_list(self):
        k = NumberKey([3, 1, 4, 1, 5])
        result = k.get_min()
        self.assertEqual(result.now(), 1)

    def test_get_max_with_list(self):
        k = NumberKey([3, 1, 4, 1, 5])
        result = k.get_max()
        self.assertEqual(result.now(), 5)

    def test_get_min_scalar_returns_scalar(self):
        k = NumberKey(7)
        result = k.get_min()
        self.assertEqual(result.now(), 7)

    def test_get_max_scalar_returns_scalar(self):
        k = NumberKey(7)
        result = k.get_max()
        self.assertEqual(result.now(), 7)


# ==================================================================
# Accompany class
# ==================================================================

class TestAccompany(unittest.TestCase):
    """Test the Accompany helper class."""

    def test_default_relations(self):
        a = Accompany()
        self.assertEqual(a.relations, [0, 2, 4])

    def test_custom_relations(self):
        a = Accompany(rel=[0, 3, 5])
        self.assertEqual(a.relations, [0, 3, 5])

    def test_callable(self):
        a = Accompany()
        # Should return an integer when called with a note value
        result = a(3)
        self.assertIsInstance(result, (int, float))

    def test_same_input_returns_same_output(self):
        a = Accompany()
        r1 = a(3)
        r2 = a(3)
        self.assertEqual(r1, r2)

    def test_different_input_may_change_output(self):
        a = Accompany()
        _ = a(0)  # Initialize
        _ = a(7)  # Different input — may or may not change


# ==================================================================
# PlayerKey
# ==================================================================

class TestPlayerKeyCreation(unittest.TestCase):
    """Test PlayerKey initialization."""

    def test_create_with_value(self):
        pk = PlayerKey(5, player=None, attr="degree")
        self.assertEqual(pk.value, 5)
        self.assertEqual(pk.attr, "degree")

    def test_inherits_from_numberkey(self):
        pk = PlayerKey(5, player=None, attr="degree")
        self.assertIsInstance(pk, NumberKey)

    def test_last_updated_initial(self):
        pk = PlayerKey(5, player=None, attr="degree")
        self.assertEqual(pk.last_updated, 0)

    def test_set_method(self):
        pk = PlayerKey(5, player=None, attr="degree")
        pk.set(10, 1.0)
        self.assertEqual(pk.value, 10)
        self.assertEqual(pk.last_updated, 1.0)

    def test_update_different_time(self):
        pk = PlayerKey(5, player=None, attr="degree")
        pk.set(5, 0.0)
        pk.update(10, 1.0)
        self.assertEqual(pk.value, 10)
        self.assertEqual(pk.last_updated, 1.0)

    def test_update_same_time_creates_pgroup(self):
        pk = PlayerKey(5, player=None, attr="degree")
        pk.set(5, 1.0)
        pk.update(10, 1.0)
        self.assertIsInstance(pk.value, PGroup)


class TestPlayerKeyInheritance(unittest.TestCase):
    """Test that PlayerKey inherits attr/player from parent PlayerKey."""

    def test_inherits_attr_from_parent(self):
        parent = PlayerKey(5, player="p1", attr="degree")
        child = PlayerKey(parent)
        self.assertEqual(child.attr, "degree")
        self.assertEqual(child.player, "p1")

    def test_explicit_player_attr_overrides(self):
        parent = PlayerKey(5, player="p1", attr="degree")
        child = PlayerKey(parent, player="p2", attr="dur")
        self.assertEqual(child.attr, "dur")
        self.assertEqual(child.player, "p2")


class TestPlayerKeyCmp(unittest.TestCase):
    """Test the cmp method."""

    def test_cmp_matching(self):
        pk = PlayerKey(5, player="p1", attr="degree")
        self.assertTrue(pk.cmp("p1", "degree"))

    def test_cmp_wrong_player(self):
        pk = PlayerKey(5, player="p1", attr="degree")
        self.assertFalse(pk.cmp("p2", "degree"))

    def test_cmp_wrong_attr(self):
        pk = PlayerKey(5, player="p1", attr="degree")
        self.assertFalse(pk.cmp("p1", "dur"))


class TestPlayerKeyName(unittest.TestCase):
    """Test name() method."""

    def test_name_format(self):
        pk = PlayerKey(5, player=type("FakePlayer", (), {"id": "p1"})(), attr="degree")
        self.assertEqual(pk.name(), "p1.degree")


if __name__ == "__main__":
    unittest.main()
