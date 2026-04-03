"""Unit tests for FoxDot TimeVar module.

Tests cover: TimeVar, ChildTimeVar, linvar, expvar, sinvar, Pvar,
ChildPvar, PvarGenerator, mapvar, _var_dict, and the fetch() decorator.
"""

import math
import sys
import os
import unittest

# ---------------------------------------------------------------------------
# Bootstrap: ensure FoxDot package is importable
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from FoxDot.lib.Patterns.Main import Pattern, PGroup, asStream, PatternContainer
from FoxDot.lib.Patterns.Operations import (
    Nil, Add, rAdd, Sub, rSub, Mul, rMul, Div, rDiv,
    Mod, rMod, Pow, rPow, FloorDiv, rFloorDiv, rGet,
)
from FoxDot.lib.Constants import inf


# ---------------------------------------------------------------------------
# Mock clock — minimal stand-in for TempoClock
# ---------------------------------------------------------------------------
class MockClock:
    """Deterministic clock for TimeVar tests.

    Attributes:
        _beat:   current beat position (set manually)
        bpm:     beats per minute
        ticking: whether the clock is running
        time:    elapsed wall-clock seconds (set manually)
    """

    def __init__(self, bpm=120.0):
        self._beat = 0.0
        self.bpm = bpm
        self.ticking = True
        self.time = 0.0

    def now(self):
        return self._beat

    def bar_length(self):
        return 4

    def start(self):
        self.ticking = True


# ---------------------------------------------------------------------------
# Patch TimeVar.metro once for all tests
# ---------------------------------------------------------------------------
from FoxDot.lib.TimeVar import (
    TimeVar, ChildTimeVar, linvar, expvar, sinvar,
    Pvar, ChildPvar, PvarGenerator, PvarGeneratorEx,
    mapvar, _var_dict, var, fetch,
)

_shared_clock = MockClock()
TimeVar.set_clock(_shared_clock)


def _fresh_clock(beat=0.0, bpm=120.0):
    """Reset shared clock to known state and return it."""
    _shared_clock._beat = beat
    _shared_clock.bpm = bpm
    _shared_clock.ticking = True
    _shared_clock.time = 0.0
    return _shared_clock


# ═══════════════════════════════════════════════════════════════════════════
# fetch() decorator
# ═══════════════════════════════════════════════════════════════════════════
class TestFetch(unittest.TestCase):

    def test_plain_values(self):
        add_fetched = fetch(lambda a, b: a + b)
        self.assertEqual(add_fetched(3, 4), 7)

    def test_resolves_timevar_args(self):
        _fresh_clock(0)
        tv = TimeVar([10], dur=[4])
        add_fetched = fetch(lambda a, b: a + b)
        result = add_fetched(tv, 5)
        self.assertEqual(result, 15)

    def test_resolves_both_timevars(self):
        _fresh_clock(0)
        tv_a = TimeVar([10], dur=[4])
        tv_b = TimeVar([20], dur=[4])
        mul_fetched = fetch(lambda a, b: a * b)
        result = mul_fetched(tv_a, tv_b)
        self.assertEqual(result, 200)


# ═══════════════════════════════════════════════════════════════════════════
# TimeVar — creation and basic access
# ═══════════════════════════════════════════════════════════════════════════
class TestTimeVarCreation(unittest.TestCase):

    def setUp(self):
        _fresh_clock(0)

    def test_single_value(self):
        tv = TimeVar([42], dur=[4])
        self.assertEqual(tv.now(), 42)

    def test_two_values_initial(self):
        tv = TimeVar([0, 1], dur=[4, 4])
        self.assertEqual(tv.now(0), 0)

    def test_two_values_after_dur(self):
        """Value switches just past the duration boundary."""
        tv = TimeVar([0, 1], dur=[4, 4])
        # At exact boundary, still returns current value (proportion=1.0)
        self.assertEqual(tv.now(0), 0)
        # Just past boundary, switches to next value
        self.assertEqual(tv.now(4.01), 1)

    def test_two_values_wrap(self):
        """Values wrap around after cycling through all durations."""
        tv = TimeVar([0, 1], dur=[4, 4])
        self.assertEqual(tv.now(0), 0)
        self.assertEqual(tv.now(4.01), 1)
        self.assertEqual(tv.now(8.01), 0)

    def test_default_dur_is_bar_length(self):
        tv = TimeVar([5])
        self.assertEqual(len(tv.dur), 1)
        self.assertEqual(tv.dur[0], 4)  # MockClock.bar_length() == 4

    def test_update_values(self):
        tv = TimeVar([1], dur=[4])
        self.assertEqual(tv.now(0), 1)
        tv.update([99], dur=[4])
        self.assertEqual(tv.now(0), 99)

    def test_update_dur(self):
        tv = TimeVar([0, 1], dur=[2, 2])
        tv.update([0, 1], dur=[8, 8])
        self.assertEqual(tv.now(0), 0)
        # After 8 beats should switch
        self.assertEqual(tv.now(8), 1)


# ═══════════════════════════════════════════════════════════════════════════
# TimeVar — string / repr / info
# ═══════════════════════════════════════════════════════════════════════════
class TestTimeVarDisplay(unittest.TestCase):

    def setUp(self):
        _fresh_clock(0)

    def test_str_returns_current_value(self):
        tv = TimeVar([7], dur=[4])
        self.assertEqual(str(tv), "7")

    def test_repr_returns_current_value(self):
        tv = TimeVar([7], dur=[4])
        self.assertEqual(repr(tv), "7")

    def test_int_conversion(self):
        tv = TimeVar([3.7], dur=[4])
        self.assertEqual(int(tv), 3)

    def test_float_conversion(self):
        tv = TimeVar([3], dur=[4])
        self.assertAlmostEqual(float(tv), 3.0)

    def test_abs(self):
        tv = TimeVar([-5], dur=[4])
        self.assertEqual(abs(tv), 5)

    def test_info(self):
        tv = TimeVar([1, 2], dur=[4, 4])
        info_str = tv.info()
        self.assertIn("TimeVar", info_str)

    def test_json_value(self):
        tv = TimeVar([1, 2], dur=[4, 4])
        j = tv.json_value()
        self.assertEqual(j[0], "TimeVar")
        self.assertEqual(list(j[1]), [1, 2])
        self.assertEqual(list(j[2]), [4, 4])


# ═══════════════════════════════════════════════════════════════════════════
# TimeVar — comparisons
# ═══════════════════════════════════════════════════════════════════════════
class TestTimeVarComparisons(unittest.TestCase):

    def setUp(self):
        _fresh_clock(0)

    def test_gt_true(self):
        tv = TimeVar([10], dur=[4])
        self.assertTrue(tv > 5)

    def test_gt_false(self):
        tv = TimeVar([3], dur=[4])
        self.assertFalse(tv > 5)

    def test_lt_true(self):
        tv = TimeVar([3], dur=[4])
        self.assertTrue(tv < 5)

    def test_lt_false(self):
        tv = TimeVar([10], dur=[4])
        self.assertFalse(tv < 5)

    def test_ge_true_equal(self):
        tv = TimeVar([5], dur=[4])
        self.assertTrue(tv >= 5)

    def test_ge_true_greater(self):
        tv = TimeVar([10], dur=[4])
        self.assertTrue(tv >= 5)

    def test_ge_false(self):
        tv = TimeVar([3], dur=[4])
        self.assertFalse(tv >= 5)

    def test_le_true_equal(self):
        tv = TimeVar([5], dur=[4])
        self.assertTrue(tv <= 5)

    def test_le_true_less(self):
        tv = TimeVar([3], dur=[4])
        self.assertTrue(tv <= 5)

    def test_le_false(self):
        tv = TimeVar([10], dur=[4])
        self.assertFalse(tv <= 5)

    def test_eq_true(self):
        tv = TimeVar([5], dur=[4])
        self.assertTrue(tv == 5)

    def test_eq_false(self):
        tv = TimeVar([5], dur=[4])
        self.assertFalse(tv == 6)

    def test_ne_true(self):
        tv = TimeVar([5], dur=[4])
        self.assertTrue(tv != 6)

    def test_ne_false(self):
        tv = TimeVar([5], dur=[4])
        self.assertFalse(tv != 5)


# ═══════════════════════════════════════════════════════════════════════════
# TimeVar — arithmetic operators
# ═══════════════════════════════════════════════════════════════════════════
class TestTimeVarArithmetic(unittest.TestCase):

    def setUp(self):
        _fresh_clock(0)

    def test_add_int(self):
        tv = TimeVar([10], dur=[4])
        result = tv + 5
        self.assertIsInstance(result, ChildTimeVar)
        self.assertEqual(result.now(), 15)

    def test_radd_int(self):
        tv = TimeVar([10], dur=[4])
        result = 5 + tv
        self.assertIsInstance(result, ChildTimeVar)
        self.assertEqual(result.now(), 15)

    def test_sub_int(self):
        tv = TimeVar([10], dur=[4])
        result = tv - 3
        self.assertIsInstance(result, ChildTimeVar)
        self.assertEqual(result.now(), 7)

    def test_rsub_int(self):
        tv = TimeVar([10], dur=[4])
        result = 20 - tv
        self.assertIsInstance(result, ChildTimeVar)
        self.assertEqual(result.now(), 10)

    def test_mul_int(self):
        tv = TimeVar([10], dur=[4])
        result = tv * 3
        self.assertIsInstance(result, ChildTimeVar)
        self.assertEqual(result.now(), 30)

    def test_rmul_int(self):
        tv = TimeVar([10], dur=[4])
        result = 3 * tv
        self.assertIsInstance(result, ChildTimeVar)
        self.assertEqual(result.now(), 30)

    def test_truediv_int(self):
        tv = TimeVar([10], dur=[4])
        result = tv / 2
        self.assertIsInstance(result, ChildTimeVar)
        self.assertAlmostEqual(result.now(), 5.0)

    def test_rtruediv_int(self):
        tv = TimeVar([10], dur=[4])
        result = 100 / tv
        self.assertIsInstance(result, ChildTimeVar)
        self.assertAlmostEqual(result.now(), 10.0)

    def test_floordiv_int(self):
        tv = TimeVar([7], dur=[4])
        result = tv // 2
        self.assertIsInstance(result, ChildTimeVar)
        self.assertEqual(result.now(), 3)

    def test_rfloordiv_int(self):
        tv = TimeVar([3], dur=[4])
        result = 7 // tv
        self.assertIsInstance(result, ChildTimeVar)
        self.assertEqual(result.now(), 2)

    def test_pow_int(self):
        tv = TimeVar([3], dur=[4])
        result = tv ** 2
        self.assertIsInstance(result, ChildTimeVar)
        self.assertEqual(result.now(), 9)

    def test_rpow_int(self):
        tv = TimeVar([3], dur=[4])
        result = 2 ** tv
        self.assertIsInstance(result, ChildTimeVar)
        self.assertEqual(result.now(), 8)

    def test_mod_int(self):
        tv = TimeVar([10], dur=[4])
        result = tv % 3
        self.assertIsInstance(result, ChildTimeVar)
        self.assertEqual(result.now(), 1)

    def test_rmod_int(self):
        tv = TimeVar([3], dur=[4])
        result = 10 % tv
        self.assertIsInstance(result, ChildTimeVar)
        self.assertEqual(result.now(), 1)


# ═══════════════════════════════════════════════════════════════════════════
# TimeVar — arithmetic with another TimeVar
# ═══════════════════════════════════════════════════════════════════════════
class TestTimeVarArithmeticWithTimeVar(unittest.TestCase):

    def setUp(self):
        _fresh_clock(0)

    def test_add_timevar(self):
        tv_a = TimeVar([10], dur=[4])
        tv_b = TimeVar([5], dur=[4])
        result = tv_a + tv_b
        self.assertIsInstance(result, ChildTimeVar)
        self.assertEqual(result.now(), 15)

    def test_sub_timevar(self):
        tv_a = TimeVar([10], dur=[4])
        tv_b = TimeVar([3], dur=[4])
        result = tv_a - tv_b
        self.assertIsInstance(result, ChildTimeVar)
        self.assertEqual(result.now(), 7)

    def test_mul_timevar(self):
        tv_a = TimeVar([10], dur=[4])
        tv_b = TimeVar([3], dur=[4])
        result = tv_a * tv_b
        self.assertIsInstance(result, ChildTimeVar)
        self.assertEqual(result.now(), 30)


# ═══════════════════════════════════════════════════════════════════════════
# TimeVar — in-place operators
# ═══════════════════════════════════════════════════════════════════════════
class TestTimeVarInPlace(unittest.TestCase):

    def setUp(self):
        _fresh_clock(0)

    def test_iadd(self):
        tv = TimeVar([10], dur=[4])
        tv += 5
        # After iadd, values should be updated
        self.assertEqual(tv.now(0), 15)

    def test_isub(self):
        tv = TimeVar([10], dur=[4])
        tv -= 3
        self.assertEqual(tv.now(0), 7)

    def test_imul(self):
        tv = TimeVar([10], dur=[4])
        tv *= 2
        self.assertEqual(tv.now(0), 20)


# ═══════════════════════════════════════════════════════════════════════════
# TimeVar — time-based value switching
# ═══════════════════════════════════════════════════════════════════════════
class TestTimeVarTimeSwitching(unittest.TestCase):

    def setUp(self):
        _fresh_clock(0)

    def test_three_values(self):
        tv = TimeVar([10, 20, 30], dur=[2, 2, 2])
        self.assertEqual(tv.now(0), 10)
        self.assertEqual(tv.now(2), 20)
        self.assertEqual(tv.now(4), 30)

    def test_unequal_durations(self):
        tv = TimeVar([0, 1], dur=[1, 3])
        self.assertEqual(tv.now(0), 0)
        self.assertEqual(tv.now(1), 1)
        self.assertEqual(tv.now(3), 1)

    def test_wrap_around(self):
        tv = TimeVar([0, 1], dur=[2, 2])
        self.assertEqual(tv.now(0), 0)
        self.assertEqual(tv.now(2), 1)
        self.assertEqual(tv.now(4), 0)
        self.assertEqual(tv.now(6), 1)

    def test_start_offset(self):
        tv = TimeVar([100, 200], dur=[4, 4], start=2)
        # At beat 2, offset makes effective time = 0
        self.assertEqual(tv.now(2), 100)
        # At beat 6, effective time = 4
        self.assertEqual(tv.now(6), 200)


# ═══════════════════════════════════════════════════════════════════════════
# TimeVar — copy, lshift, rshift, extend
# ═══════════════════════════════════════════════════════════════════════════
class TestTimeVarManipulation(unittest.TestCase):

    def setUp(self):
        _fresh_clock(0)

    def test_copy(self):
        tv = TimeVar([1, 2], dur=[4, 4])
        tv_copy = tv.copy()
        self.assertEqual(tv_copy.now(0), 1)
        self.assertEqual(tv_copy.now(4), 2)
        # Modifying copy doesn't affect original
        tv_copy.update([99])
        self.assertEqual(tv.now(0), 1)

    def test_lshift(self):
        tv = TimeVar([0, 1], dur=[4, 4])
        shifted = tv.lshift(1)
        # First duration should be 3, last should be 1
        self.assertEqual(shifted.dur[0], 3)

    def test_rshift(self):
        tv = TimeVar([0, 1], dur=[4, 4])
        shifted = tv.rshift(1)
        # First duration should be 1
        self.assertEqual(shifted.dur[0], 1)

    def test_extend(self):
        tv = TimeVar([0, 1], dur=[4, 4])
        extended = tv.extend([2], dur=[4])
        self.assertEqual(extended.now(0), 0)
        self.assertEqual(extended.now(4), 1)
        self.assertEqual(extended.now(8), 2)


# ═══════════════════════════════════════════════════════════════════════════
# TimeVar — container emulation
# ═══════════════════════════════════════════════════════════════════════════
class TestTimeVarContainer(unittest.TestCase):

    def setUp(self):
        _fresh_clock(0)

    def test_getitem_returns_child(self):
        tv = TimeVar([10, 20], dur=[4, 4])
        child = tv[0]
        self.assertIsInstance(child, ChildTimeVar)

    def test_iter_with_iterable_value(self):
        """Iterating a Pvar whose current value is a Pattern yields elements."""
        pv = Pvar([[1, 2, 3], [4, 5]], dur=[4, 4])
        items = list(pv)
        self.assertEqual(items, [1, 2, 3])


# ═══════════════════════════════════════════════════════════════════════════
# TimeVar — transform
# ═══════════════════════════════════════════════════════════════════════════
class TestTimeVarTransform(unittest.TestCase):

    def setUp(self):
        _fresh_clock(0)

    def test_transform_doubles(self):
        tv = TimeVar([5], dur=[4])
        doubled = tv.transform(lambda x: x * 2)
        self.assertEqual(doubled.now(), 10)

    def test_transform_negate(self):
        tv = TimeVar([7], dur=[4])
        negated = tv.transform(lambda x: -x)
        self.assertEqual(negated.now(), -7)


# ═══════════════════════════════════════════════════════════════════════════
# TimeVar — new (creates ChildTimeVar with dependency)
# ═══════════════════════════════════════════════════════════════════════════
class TestTimeVarNew(unittest.TestCase):

    def setUp(self):
        _fresh_clock(0)

    def test_new_creates_child(self):
        tv = TimeVar([10], dur=[4])
        child = tv.new(5)
        self.assertIsInstance(child, ChildTimeVar)
        self.assertIs(child.dependency, tv)


# ═══════════════════════════════════════════════════════════════════════════
# TimeVar — get_durs / get_values
# ═══════════════════════════════════════════════════════════════════════════
class TestTimeVarAccessors(unittest.TestCase):

    def setUp(self):
        _fresh_clock(0)

    def test_get_durs(self):
        tv = TimeVar([1, 2], dur=[3, 5])
        durs = tv.get_durs()
        self.assertEqual(list(durs)[:2], [3, 5])

    def test_get_values(self):
        tv = TimeVar([1, 2], dur=[4, 4])
        vals = tv.get_values()
        self.assertEqual(list(vals)[:2], [1, 2])


# ═══════════════════════════════════════════════════════════════════════════
# TimeVar — set_clock classmethod
# ═══════════════════════════════════════════════════════════════════════════
class TestTimeVarSetClock(unittest.TestCase):

    def test_set_clock(self):
        new_clock = MockClock(bpm=140)
        TimeVar.set_clock(new_clock)
        self.assertIs(TimeVar.metro, new_clock)
        # Restore
        TimeVar.set_clock(_shared_clock)


# ═══════════════════════════════════════════════════════════════════════════
# TimeVar — seconds mode
# ═══════════════════════════════════════════════════════════════════════════
class TestTimeVarSecondsMode(unittest.TestCase):

    def setUp(self):
        _fresh_clock(0)

    def test_seconds_mode_uses_wall_time(self):
        _shared_clock.time = 0.0
        tv = TimeVar([100, 200], dur=[2.0, 2.0], seconds=True)
        self.assertEqual(tv.now(), 100)
        _shared_clock.time = 2.5
        self.assertEqual(tv.now(), 200)


# ═══════════════════════════════════════════════════════════════════════════
# TimeVar — bpm scaling
# ═══════════════════════════════════════════════════════════════════════════
class TestTimeVarBPMScaling(unittest.TestCase):

    def setUp(self):
        _fresh_clock(0, bpm=120)

    def test_bpm_scales_beat(self):
        # With bpm=60 and clock at 120, effective beat is halved
        tv = TimeVar([0, 1], dur=[4, 4], bpm=60)
        # At beat 0, effective = 0 * (60/120) = 0 → value 0
        self.assertEqual(tv.now(0), 0)
        # At beat 8, effective = 8 * (60/120) = 4 → value 1
        self.assertEqual(tv.now(8), 1)


# ═══════════════════════════════════════════════════════════════════════════
# TimeVar — proportion tracking
# ═══════════════════════════════════════════════════════════════════════════
class TestTimeVarProportion(unittest.TestCase):

    def setUp(self):
        _fresh_clock(0)

    def test_proportion_midpoint(self):
        tv = TimeVar([0, 1], dur=[4, 4])
        tv.now(2)  # Halfway through first value
        self.assertAlmostEqual(tv.proportion, 0.5)

    def test_proportion_start(self):
        tv = TimeVar([0, 1], dur=[4, 4])
        tv.now(0)
        self.assertAlmostEqual(tv.proportion, 0.0)


# ═══════════════════════════════════════════════════════════════════════════
# TimeVar — inf duration
# ═══════════════════════════════════════════════════════════════════════════
class TestTimeVarInfDuration(unittest.TestCase):

    def setUp(self):
        _fresh_clock(0)

    def test_inf_stops_progression(self):
        tv = TimeVar([0, 1], dur=[4, inf])
        self.assertEqual(tv.now(0), 0)
        self.assertEqual(tv.now(4), 1)
        # After inf, value should stay at 1
        self.assertEqual(tv.now(100), 1)
        self.assertEqual(tv.now(10000), 1)


# ═══════════════════════════════════════════════════════════════════════════
# ChildTimeVar
# ═══════════════════════════════════════════════════════════════════════════
class TestChildTimeVar(unittest.TestCase):

    def setUp(self):
        _fresh_clock(0)

    def test_now_returns_first_value(self):
        child = ChildTimeVar([42])
        self.assertEqual(child.now(), 42)

    def test_with_dependency(self):
        parent = TimeVar([10], dur=[4])
        child = ChildTimeVar([5])
        child.dependency = parent
        child.evaluate = fetch(Add)
        # calculate(5) => Add(5, parent.now()) => 5 + 10 = 15
        self.assertEqual(child.now(), 15)


# ═══════════════════════════════════════════════════════════════════════════
# linvar — linear interpolation
# ═══════════════════════════════════════════════════════════════════════════
class TestLinvar(unittest.TestCase):

    def setUp(self):
        _fresh_clock(0)

    def test_at_start(self):
        lv = linvar([0, 10], dur=[4, 4])
        self.assertAlmostEqual(lv.now(0), 0.0)

    def test_at_boundary(self):
        lv = linvar([0, 10], dur=[4, 4])
        val = lv.now(4)
        self.assertAlmostEqual(val, 10.0)

    def test_midpoint_interpolation(self):
        lv = linvar([0, 10], dur=[4, 4])
        val = lv.now(2)
        # At midpoint, proportion = 0.5
        # value = 0 * (1 - 0.5) + 10 * 0.5 = 5.0
        self.assertAlmostEqual(val, 5.0)

    def test_quarter_interpolation(self):
        lv = linvar([0, 10], dur=[4, 4])
        val = lv.now(1)
        # proportion = 0.25
        # value = 0 * 0.75 + 10 * 0.25 = 2.5
        self.assertAlmostEqual(val, 2.5)

    def test_three_quarter_interpolation(self):
        lv = linvar([0, 10], dur=[4, 4])
        val = lv.now(3)
        # proportion = 0.75
        # value = 0 * 0.25 + 10 * 0.75 = 7.5
        self.assertAlmostEqual(val, 7.5)


# ═══════════════════════════════════════════════════════════════════════════
# expvar — exponential interpolation
# ═══════════════════════════════════════════════════════════════════════════
class TestExpvar(unittest.TestCase):

    def setUp(self):
        _fresh_clock(0)

    def test_at_start(self):
        ev = expvar([0, 10], dur=[4, 4])
        self.assertAlmostEqual(ev.now(0), 0.0)

    def test_at_boundary(self):
        ev = expvar([0, 10], dur=[4, 4])
        val = ev.now(4)
        self.assertAlmostEqual(val, 10.0)

    def test_midpoint_exponential(self):
        ev = expvar([0, 10], dur=[4, 4])
        val = ev.now(2)
        # proportion = 0.5, squared = 0.25
        # value = 0 * 0.75 + 10 * 0.25 = 2.5
        self.assertAlmostEqual(val, 2.5)

    def test_exponential_is_slower_than_linear(self):
        ev = expvar([0, 10], dur=[4, 4])
        lv = linvar([0, 10], dur=[4, 4])
        # At midpoint, expvar should be less than linvar
        exp_val = ev.now(2)
        _fresh_clock(0)  # Reset for linvar
        lin_val = lv.now(2)
        self.assertLess(exp_val, lin_val)


# ═══════════════════════════════════════════════════════════════════════════
# sinvar — sinusoidal interpolation
# ═══════════════════════════════════════════════════════════════════════════
class TestSinvar(unittest.TestCase):

    def setUp(self):
        _fresh_clock(0)

    def test_at_start(self):
        sv = sinvar([0, 10], dur=[4, 4])
        self.assertAlmostEqual(sv.now(0), 0.0)

    def test_at_boundary(self):
        sv = sinvar([0, 10], dur=[4, 4])
        val = sv.now(4)
        self.assertAlmostEqual(val, 10.0)

    def test_midpoint_sinusoidal(self):
        sv = sinvar([0, 10], dur=[4, 4])
        val = sv.now(2)
        # With current_value=0 < next_value=10, d=0
        # x = 0.5 * 90 + 0 * 270 = 45
        # proportion = sin(45°) + 0 = sqrt(2)/2 ≈ 0.707
        # value = 0 * (1-0.707) + 10 * 0.707 ≈ 7.07
        expected = 10 * math.sin(math.radians(45))
        self.assertAlmostEqual(val, expected, places=3)


# ═══════════════════════════════════════════════════════════════════════════
# Pvar — Pattern-based TimeVar
# ═══════════════════════════════════════════════════════════════════════════
class TestPvar(unittest.TestCase):

    def setUp(self):
        _fresh_clock(0)

    def test_single_pattern_flattens(self):
        """Pvar with one pattern: PatternContainer flattens it to individual values."""
        pv = Pvar([[1, 2, 3]], dur=[4])
        result = pv.now(0)
        # Single pattern gets flattened by PatternContainer, so values cycle individually
        self.assertEqual(result, 1)

    def test_two_patterns(self):
        """Pvar with two patterns switches between them over time."""
        pv = Pvar([[1, 2, 3], [4, 5]], dur=[4, 4])
        r1 = pv.now(0)
        self.assertIsInstance(r1, Pattern)
        self.assertEqual(list(r1), [1, 2, 3])
        r2 = pv.now(4.01)
        self.assertIsInstance(r2, Pattern)
        self.assertEqual(list(r2), [4, 5])

    def test_add_scalar(self):
        pv = Pvar([[1, 2, 3], [4, 5]], dur=[4, 4])
        result = pv + 10
        self.assertIsInstance(result, ChildPvar)

    def test_sub_scalar(self):
        pv = Pvar([[10, 20, 30], [1, 2]], dur=[4, 4])
        result = pv - 5
        self.assertIsInstance(result, ChildPvar)

    def test_mul_scalar(self):
        pv = Pvar([[1, 2, 3], [4, 5]], dur=[4, 4])
        result = pv * 2
        self.assertIsInstance(result, ChildPvar)

    def test_truediv_scalar(self):
        pv = Pvar([[10, 20], [30, 40]], dur=[4, 4])
        result = pv / 2
        self.assertIsInstance(result, ChildPvar)

    def test_floordiv_scalar(self):
        pv = Pvar([[10, 20], [30, 40]], dur=[4, 4])
        result = pv // 3
        self.assertIsInstance(result, ChildPvar)

    def test_pow_scalar(self):
        pv = Pvar([[2, 3], [4, 5]], dur=[4, 4])
        result = pv ** 2
        self.assertIsInstance(result, ChildPvar)

    def test_mod_scalar(self):
        pv = Pvar([[10, 20], [30, 40]], dur=[4, 4])
        result = pv % 3
        self.assertIsInstance(result, ChildPvar)

    def test_getitem_returns_timevar(self):
        pv = Pvar([[1, 2, 3], [4, 5]], dur=[4, 4])
        item = pv[0]
        self.assertIsInstance(item, ChildTimeVar)

    def test_json_value(self):
        pv = Pvar([[1, 2], [3, 4]], dur=[4, 4])
        j = pv.json_value()
        self.assertEqual(j[0], "Pvar")


# ═══════════════════════════════════════════════════════════════════════════
# ChildPvar
# ═══════════════════════════════════════════════════════════════════════════
class TestChildPvar(unittest.TestCase):

    def setUp(self):
        _fresh_clock(0)

    def test_now_returns_calculated_value(self):
        """ChildPvar.now() returns calculate(values[0])."""
        cp = ChildPvar([42])
        # Without dependency, calculate returns the value itself
        result = cp.now()
        self.assertEqual(result, 42)


# ═══════════════════════════════════════════════════════════════════════════
# PvarGenerator
# ═══════════════════════════════════════════════════════════════════════════
class TestPvarGenerator(unittest.TestCase):

    def setUp(self):
        _fresh_clock(0)

    def test_static_args(self):
        # PvarGenerator with a simple function
        gen = PvarGenerator(lambda x: Pattern([x, x + 1, x + 2]), 5)
        result = gen.now()
        self.assertIsInstance(result, Pattern)
        self.assertEqual(list(result), [5, 6, 7])

    def test_caches_result(self):
        call_count = [0]

        def counting_func(x):
            call_count[0] += 1
            return Pattern([x])

        gen = PvarGenerator(counting_func, 5)
        gen.now()
        gen.now()
        # Should only call the function once since args didn't change
        self.assertEqual(call_count[0], 1)

    def test_recalculates_on_change(self):
        tv_arg = TimeVar([1, 2], dur=[4, 4])
        gen = PvarGenerator(lambda x: Pattern([x * 10]), tv_arg)
        r1 = gen.now()
        self.assertEqual(list(r1), [10])


# ═══════════════════════════════════════════════════════════════════════════
# PvarGeneratorEx
# ═══════════════════════════════════════════════════════════════════════════
class TestPvarGeneratorEx(unittest.TestCase):

    def test_creation(self):
        gen = PvarGeneratorEx(lambda x: x, 1, 2, 3)
        self.assertEqual(len(gen.args), 3)
        self.assertEqual(gen.dependency, 1)


# ═══════════════════════════════════════════════════════════════════════════
# mapvar
# ═══════════════════════════════════════════════════════════════════════════
class TestMapvar(unittest.TestCase):

    def setUp(self):
        _fresh_clock(0)

    def test_maps_key_to_value(self):
        # mapvar reads from the clock via key.now(), not from the time argument
        key = TimeVar([0, 1], dur=[4, 4])
        mv = mapvar(key, {0: [1, 2, 3], 1: [4, 5, 6]})
        _shared_clock._beat = 0
        r0 = mv.now()
        self.assertEqual(list(r0), [1, 2, 3])
        # Advance the clock so the key switches
        _shared_clock._beat = 4.01
        r1 = mv.now()
        self.assertEqual(list(r1), [4, 5, 6])

    def test_default_value(self):
        key = TimeVar([99], dur=[4])
        mv = mapvar(key, {0: [1, 2]}, default=42)
        result = mv.now(0)
        # key=99 not in mapping, should return default
        self.assertEqual(list(result), [42])


# ═══════════════════════════════════════════════════════════════════════════
# _var_dict — the var() registry
# ═══════════════════════════════════════════════════════════════════════════
class TestVarDict(unittest.TestCase):

    def setUp(self):
        _fresh_clock(0)

    def test_call_creates_timevar(self):
        tv = var([1, 2], dur=[4, 4])
        self.assertIsInstance(tv, TimeVar)

    def test_setattr_stores_timevar(self):
        vd = _var_dict()
        vd.foo = TimeVar([10], dur=[4])
        self.assertIsInstance(vd.foo, TimeVar)
        self.assertEqual(vd.foo.now(), 10)

    def test_setattr_updates_existing(self):
        vd = _var_dict()
        vd.bar = TimeVar([10], dur=[4])
        original = vd.bar
        vd.bar = TimeVar([20], dur=[4])
        # Should be the same object (updated in place)
        self.assertIs(vd.bar, original)
        self.assertEqual(vd.bar.now(), 20)

    def test_getattr_nonexistent_raises(self):
        vd = _var_dict()
        with self.assertRaises(NameError):
            _ = vd.nonexistent_var

    def test_class_change_on_update(self):
        vd = _var_dict()
        vd.x = TimeVar([10], dur=[4])
        # Replace with linvar — should update class
        vd.x = linvar([0, 10], dur=[4, 4])
        self.assertIsInstance(vd.x, linvar)


# ═══════════════════════════════════════════════════════════════════════════
# TimeVar — math_op with lists and tuples
# ═══════════════════════════════════════════════════════════════════════════
class TestTimeVarMathOpSpecialTypes(unittest.TestCase):

    def setUp(self):
        _fresh_clock(0)

    def test_add_list(self):
        tv = TimeVar([10], dur=[4])
        result = tv + [1, 2, 3]
        self.assertIsInstance(result, Pattern)

    def test_add_tuple(self):
        tv = TimeVar([10], dur=[4])
        result = tv + (1, 2)
        self.assertIsInstance(result, PGroup)

    def test_mul_list(self):
        tv = TimeVar([10], dur=[4])
        result = tv * [2, 3]
        self.assertIsInstance(result, Pattern)


# ═══════════════════════════════════════════════════════════════════════════
# TimeVar — len, iter on Pattern-valued TimeVars
# ═══════════════════════════════════════════════════════════════════════════
class TestTimeVarLen(unittest.TestCase):

    def setUp(self):
        _fresh_clock(0)

    def test_len_of_pvar(self):
        """len() works on a Pvar whose current value is a Pattern."""
        pv = Pvar([[1, 2, 3], [4, 5]], dur=[4, 4])
        self.assertEqual(len(pv), 3)


# ═══════════════════════════════════════════════════════════════════════════
# Edge cases and regression tests
# ═══════════════════════════════════════════════════════════════════════════
class TestTimeVarEdgeCases(unittest.TestCase):

    def setUp(self):
        _fresh_clock(0)

    def test_single_value_constant(self):
        """A TimeVar with one value should always return that value."""
        tv = TimeVar([42], dur=[4])
        for beat in [0, 1, 2, 3, 4, 5, 10, 100]:
            self.assertEqual(tv.now(beat), 42)

    def test_zero_start_offset(self):
        """start=0 should be the same as no offset."""
        tv1 = TimeVar([1, 2], dur=[4, 4])
        tv2 = TimeVar([1, 2], dur=[4, 4], start=0)
        self.assertEqual(tv1.now(0), tv2.now(0))
        self.assertEqual(tv1.now(4), tv2.now(4))

    def test_negative_values(self):
        tv = TimeVar([-5, -10], dur=[4, 4])
        self.assertEqual(tv.now(0), -5)
        self.assertEqual(tv.now(4), -10)

    def test_float_values(self):
        tv = TimeVar([1.5, 2.7], dur=[4, 4])
        self.assertAlmostEqual(tv.now(0), 1.5)
        self.assertAlmostEqual(tv.now(4), 2.7)

    def test_le_bug_fix_regression(self):
        """Regression test: __le__ previously used >= instead of <=."""
        tv = TimeVar([3], dur=[4])
        self.assertTrue(tv <= 5)   # 3 <= 5 is True
        self.assertTrue(tv <= 3)   # 3 <= 3 is True
        self.assertFalse(tv <= 2)  # 3 <= 2 is False

    def test_chained_arithmetic(self):
        tv = TimeVar([10], dur=[4])
        result = (tv + 5) * 2
        self.assertEqual(result.now(), 30)


# ═══════════════════════════════════════════════════════════════════════════
# Pvar — reverse arithmetic
# ═══════════════════════════════════════════════════════════════════════════
class TestPvarReverseArithmetic(unittest.TestCase):

    def setUp(self):
        _fresh_clock(0)

    def test_radd(self):
        pv = Pvar([[1, 2], [3, 4]], dur=[4, 4])
        result = 10 + pv
        self.assertIsInstance(result, ChildPvar)

    def test_rsub(self):
        pv = Pvar([[1, 2], [3, 4]], dur=[4, 4])
        result = 10 - pv
        self.assertIsInstance(result, ChildPvar)

    def test_rmul(self):
        pv = Pvar([[1, 2], [3, 4]], dur=[4, 4])
        result = 10 * pv
        self.assertIsInstance(result, ChildPvar)

    def test_rtruediv(self):
        pv = Pvar([[1, 2], [3, 4]], dur=[4, 4])
        result = 10 / pv
        self.assertIsInstance(result, ChildPvar)

    def test_rfloordiv(self):
        pv = Pvar([[1, 2], [3, 4]], dur=[4, 4])
        result = 10 // pv
        self.assertIsInstance(result, ChildPvar)

    def test_rpow(self):
        pv = Pvar([[1, 2], [3, 4]], dur=[4, 4])
        result = 10 ** pv
        self.assertIsInstance(result, ChildPvar)

    def test_rmod(self):
        pv = Pvar([[1, 2], [3, 4]], dur=[4, 4])
        result = 10 % pv
        self.assertIsInstance(result, ChildPvar)


# ═══════════════════════════════════════════════════════════════════════════
# linvar — descending interpolation
# ═══════════════════════════════════════════════════════════════════════════
class TestLinvarDescending(unittest.TestCase):

    def setUp(self):
        _fresh_clock(0)

    def test_descending_interpolation(self):
        lv = linvar([10, 0], dur=[4, 4])
        self.assertAlmostEqual(lv.now(0), 10.0)
        self.assertAlmostEqual(lv.now(2), 5.0)
        self.assertAlmostEqual(lv.now(4), 0.0)


# ═══════════════════════════════════════════════════════════════════════════
# Pvar — or (pipe) operator
# ═══════════════════════════════════════════════════════════════════════════
class TestPvarOrOperator(unittest.TestCase):

    def setUp(self):
        _fresh_clock(0)

    def test_or_operator(self):
        pv = Pvar([[1, 2], [3, 4]], dur=[4, 4])
        result = pv | [5, 6]
        self.assertIsInstance(result, ChildPvar)

    def test_ror_operator(self):
        pv = Pvar([[1, 2], [3, 4]], dur=[4, 4])
        result = [5, 6] | pv
        self.assertIsInstance(result, ChildPvar)


# ═══════════════════════════════════════════════════════════════════════════
# Pvar — getitem via index
# ═══════════════════════════════════════════════════════════════════════════
class TestPvarGetitem(unittest.TestCase):

    def setUp(self):
        _fresh_clock(0)

    def test_getitem_via_method(self):
        pv = Pvar([[10, 20, 30], [40, 50]], dur=[4, 4])
        item = pv.getitem(0)
        self.assertIsInstance(item, TimeVar)


# ═══════════════════════════════════════════════════════════════════════════
# Pvar — transform
# ═══════════════════════════════════════════════════════════════════════════
class TestPvarTransform(unittest.TestCase):

    def setUp(self):
        _fresh_clock(0)

    def test_transform(self):
        pv = Pvar([[1, 2, 3], [4, 5]], dur=[4, 4])
        transformed = pv.transform(lambda p: p * 2)
        self.assertIsInstance(transformed, ChildPvar)


if __name__ == "__main__":
    unittest.main()
