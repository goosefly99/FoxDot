"""
Unit tests for FoxDot.lib.Utils

Tests cover:
- sliceToRange: convert Python slice objects to range lists
- LCM: lowest common multiple calculation
- EuclidsAlgorithm: Euclidean rhythm generation
- PulsesToDurations: convert pulse arrays to durations
- get_first_item: extract first scalar from nested lists
- modi: modulo-based array indexing
- get_expanded_len: expanded length of nested data
- max_length: largest length across patterns
- get_inverse_op: dunder method inversion (__add__ <-> __radd__)
- isiterable: check if object is iterable
- recursive_any: recursive truthiness check on nested sequences
- dots: class for representing truncated patterns
"""
import pytest
from FoxDot.lib.Utils import (
    sliceToRange,
    LCM,
    EuclidsAlgorithm,
    PulsesToDurations,
    get_first_item,
    modi,
    get_expanded_len,
    max_length,
    get_inverse_op,
    isiterable,
    recursive_any,
    dots,
)


# ──────────────────────────────────────────────
# sliceToRange
# ──────────────────────────────────────────────


class TestSliceToRange:
    def test_basic_slice(self):
        assert sliceToRange(slice(0, 5)) == [0, 1, 2, 3, 4]

    def test_with_step(self):
        assert sliceToRange(slice(0, 10, 2)) == [0, 2, 4, 6, 8]

    def test_none_start(self):
        assert sliceToRange(slice(None, 4)) == [0, 1, 2, 3]

    def test_none_step(self):
        assert sliceToRange(slice(2, 6, None)) == [2, 3, 4, 5]

    def test_negative_step(self):
        assert sliceToRange(slice(5, 0, -1)) == [5, 4, 3, 2, 1]

    def test_empty_range(self):
        assert sliceToRange(slice(5, 5)) == []

    def test_start_greater_than_stop(self):
        assert sliceToRange(slice(5, 2)) == []

    def test_none_stop_raises(self):
        with pytest.raises(TypeError):
            sliceToRange(slice(0, None))

    def test_single_element(self):
        assert sliceToRange(slice(3, 4)) == [3]

    def test_large_step(self):
        assert sliceToRange(slice(0, 100, 25)) == [0, 25, 50, 75]


# ──────────────────────────────────────────────
# LCM
# ──────────────────────────────────────────────


class TestLCM:
    def test_two_numbers(self):
        assert LCM(3, 4) == 12

    def test_same_numbers(self):
        assert LCM(5, 5) == 5

    def test_one_is_multiple(self):
        assert LCM(3, 6) == 6

    def test_coprime(self):
        assert LCM(7, 11) == 77

    def test_single_arg(self):
        assert LCM(7) == 7

    def test_no_args(self):
        assert LCM() == 1

    def test_three_numbers(self):
        assert LCM(2, 3, 4) == 12

    def test_with_one(self):
        assert LCM(1, 5) == 5

    def test_zero_ignored(self):
        assert LCM(0, 5) == 5

    def test_all_zeros(self):
        assert LCM(0, 0, 0) == 1

    def test_four_numbers(self):
        assert LCM(2, 3, 5, 7) == 210

    def test_two_and_three(self):
        assert LCM(2, 3) == 6

    def test_lcm_of_one(self):
        assert LCM(1) == 1


# ──────────────────────────────────────────────
# EuclidsAlgorithm
# ──────────────────────────────────────────────


class TestEuclidsAlgorithm:
    def test_basic_euclidean_3_8(self):
        result = EuclidsAlgorithm(3, 8)
        assert result == [1, 0, 0, 1, 0, 0, 1, 0]

    def test_basic_euclidean_5_8(self):
        result = EuclidsAlgorithm(5, 8)
        assert result == [1, 0, 1, 1, 0, 1, 1, 0]

    def test_all_pulses(self):
        result = EuclidsAlgorithm(4, 4)
        assert result == [1, 1, 1, 1]

    def test_no_pulses(self):
        result = EuclidsAlgorithm(0, 4)
        assert result == [0, 0, 0, 0]

    def test_one_pulse(self):
        result = EuclidsAlgorithm(1, 4)
        assert result == [1, 0, 0, 0]

    def test_two_of_four(self):
        result = EuclidsAlgorithm(2, 4)
        assert result == [1, 0, 1, 0]

    def test_correct_length(self):
        for k in range(1, 17):
            for n in range(0, k + 1):
                result = EuclidsAlgorithm(n, k)
                assert len(result) == k

    def test_correct_pulse_count(self):
        for k in range(1, 13):
            for n in range(0, k + 1):
                result = EuclidsAlgorithm(n, k)
                assert sum(result) == n

    def test_custom_lo_hi(self):
        result = EuclidsAlgorithm(2, 4, lo=".", hi="x")
        assert result == ["x", ".", "x", "."]

    def test_single_slot_with_pulse(self):
        result = EuclidsAlgorithm(1, 1)
        assert result == [1]

    def test_single_slot_no_pulse(self):
        result = EuclidsAlgorithm(0, 1)
        assert result == [0]

    def test_3_of_7(self):
        result = EuclidsAlgorithm(3, 7)
        assert len(result) == 7
        assert sum(result) == 3

    def test_4_of_12(self):
        result = EuclidsAlgorithm(4, 12)
        assert len(result) == 12
        assert sum(result) == 4


# ──────────────────────────────────────────────
# PulsesToDurations
# ──────────────────────────────────────────────


class TestPulsesToDurations:
    def test_basic_pattern(self):
        assert PulsesToDurations([1, 0, 0, 1, 0, 0, 1, 0]) == [3, 3, 2]

    def test_all_pulses(self):
        assert PulsesToDurations([1, 1, 1, 1]) == [1, 1, 1, 1]

    def test_single_pulse_then_rest(self):
        assert PulsesToDurations([1, 0, 0, 0]) == [4]

    def test_two_pulses(self):
        assert PulsesToDurations([1, 0, 1, 0]) == [2, 2]

    def test_single_element(self):
        assert PulsesToDurations([1]) == [1]

    def test_uneven_spacing(self):
        assert PulsesToDurations([1, 0, 1, 0, 0]) == [2, 3]

    def test_dense_sparse_pattern(self):
        assert PulsesToDurations([1, 1, 0, 0, 1]) == [1, 3, 1]

    def test_five_of_eight(self):
        # Euclidean rhythm E(5,8) = [1,0,1,1,0,1,1,0]
        data = [1, 0, 1, 1, 0, 1, 1, 0]
        result = PulsesToDurations(data)
        assert sum(result) == len(data)
        assert len(result) == 5

    def test_roundtrip_with_euclid(self):
        """PulsesToDurations of an Euclidean pattern should sum to the length."""
        for k in [4, 7, 8, 12, 16]:
            for n in range(1, k + 1):
                pattern = EuclidsAlgorithm(n, k)
                durations = PulsesToDurations(pattern)
                assert sum(durations) == k
                assert len(durations) == n


# ──────────────────────────────────────────────
# get_first_item
# ──────────────────────────────────────────────


class TestGetFirstItem:
    def test_flat_list(self):
        assert get_first_item([5, 6, 7]) == 5

    def test_nested_list(self):
        assert get_first_item([[1, 2], [3, 4]]) == 1

    def test_deeply_nested(self):
        assert get_first_item([[[[[42]]]]]) == 42

    def test_scalar(self):
        assert get_first_item(10) == 10

    def test_string_infinite_recursion(self):
        # Strings are infinitely indexable ("h"[0] == "h"), so get_first_item
        # recurses until hitting the recursion limit. This is a known edge case.
        with pytest.raises(RecursionError):
            get_first_item("hello")

    def test_empty_list_returns_itself(self):
        # Empty list triggers IndexError on array[0], caught and returns array
        assert get_first_item([]) == []

    def test_none(self):
        assert get_first_item(None) is None

    def test_tuple(self):
        assert get_first_item((3, 4, 5)) == 3

    def test_nested_tuple(self):
        assert get_first_item(((1, 2), (3, 4))) == 1

    def test_mixed_nesting(self):
        assert get_first_item([[10, 20], 30]) == 10

    def test_zero(self):
        assert get_first_item(0) == 0

    def test_float(self):
        assert get_first_item(3.14) == 3.14


# ──────────────────────────────────────────────
# modi (modulo index)
# ──────────────────────────────────────────────


class TestModi:
    def test_in_range(self):
        assert modi([10, 20, 30], 1) == 20

    def test_wrap_around(self):
        assert modi([10, 20, 30], 3) == 10

    def test_wrap_large_index(self):
        assert modi([10, 20, 30], 7) == 20

    def test_index_zero(self):
        assert modi([10, 20, 30], 0) == 10

    def test_negative_index(self):
        assert modi([10, 20, 30], -1) == 30

    def test_non_list_returns_itself(self):
        assert modi(42, 0) == 42

    def test_none_returns_itself(self):
        assert modi(None, 3) is None

    def test_tuple(self):
        assert modi((1, 2, 3), 4) == 2

    def test_string(self):
        assert modi("abc", 5) == "c"

    def test_empty_list_returns_list(self):
        # ZeroDivisionError from len(array)==0 -> returns array
        assert modi([], 0) == []


# ──────────────────────────────────────────────
# get_expanded_len
# ──────────────────────────────────────────────


class TestGetExpandedLen:
    def test_flat_tuple(self):
        assert get_expanded_len((0, 1, 2)) == 3

    def test_nested_tuple(self):
        # (0, (0, 2)) -> inner len 2, outer len 2, LCM(1,2)*2 = 4
        assert get_expanded_len((0, (0, 2))) == 4

    def test_single_int(self):
        assert get_expanded_len(5) == 1

    def test_single_char_string(self):
        assert get_expanded_len("a") == 1

    def test_flat_list(self):
        assert get_expanded_len([1, 2, 3, 4]) == 4

    def test_nested_list(self):
        assert get_expanded_len([1, [2, 3]]) == 4

    def test_deeply_nested(self):
        # [[1,2], [3,4,5]] -> inner lens 2, 3 -> LCM(2,3)*2 = 12
        assert get_expanded_len([[1, 2], [3, 4, 5]]) == 12

    def test_empty_list(self):
        # Empty iterable: LCM of no args = 1, times 0 = 0
        assert get_expanded_len([]) == 0

    def test_single_element_list(self):
        assert get_expanded_len([42]) == 1

    def test_none(self):
        assert get_expanded_len(None) == 1


# ──────────────────────────────────────────────
# max_length
# ──────────────────────────────────────────────


class TestMaxLength:
    def test_two_lists(self):
        assert max_length([1, 2, 3], [4, 5]) == 3

    def test_same_length(self):
        assert max_length([1, 2], [3, 4]) == 2

    def test_one_empty(self):
        assert max_length([1, 2, 3], []) == 3

    def test_single_arg(self):
        assert max_length([1, 2, 3, 4, 5]) == 5

    def test_many_lists(self):
        assert max_length([1], [1, 2], [1, 2, 3], [1, 2, 3, 4]) == 4

    def test_strings(self):
        assert max_length("abc", "de", "fghij") == 5


# ──────────────────────────────────────────────
# get_inverse_op
# ──────────────────────────────────────────────


class TestGetInverseOp:
    def test_add_to_radd(self):
        assert get_inverse_op("__add__") == "__radd__"

    def test_radd_to_add(self):
        assert get_inverse_op("__radd__") == "__add__"

    def test_mul_to_rmul(self):
        assert get_inverse_op("__mul__") == "__rmul__"

    def test_rmul_to_mul(self):
        assert get_inverse_op("__rmul__") == "__mul__"

    def test_sub_to_rsub(self):
        assert get_inverse_op("__sub__") == "__rsub__"

    def test_rsub_to_sub(self):
        assert get_inverse_op("__rsub__") == "__sub__"

    def test_truediv_to_rtruediv(self):
        assert get_inverse_op("__truediv__") == "__rtruediv__"

    def test_rtruediv_to_truediv(self):
        assert get_inverse_op("__rtruediv__") == "__truediv__"

    def test_floordiv(self):
        assert get_inverse_op("__floordiv__") == "__rfloordiv__"

    def test_mod(self):
        assert get_inverse_op("__mod__") == "__rmod__"

    def test_pow(self):
        assert get_inverse_op("__pow__") == "__rpow__"

    def test_or(self):
        assert get_inverse_op("__or__") == "__ror__"

    def test_ror(self):
        assert get_inverse_op("__ror__") == "__or__"

    def test_non_dunder_passthrough(self):
        assert get_inverse_op("foo") == "foo"


# ──────────────────────────────────────────────
# isiterable
# ──────────────────────────────────────────────


class TestIsIterable:
    def test_list(self):
        assert isiterable([1, 2, 3]) is True

    def test_tuple(self):
        assert isiterable((1, 2)) is True

    def test_string(self):
        assert isiterable("hello") is True

    def test_set(self):
        assert isiterable({1, 2, 3}) is True

    def test_dict(self):
        assert isiterable({"a": 1}) is True

    def test_generator(self):
        assert isiterable(x for x in range(3)) is True

    def test_range(self):
        assert isiterable(range(10)) is True

    def test_int(self):
        assert isiterable(42) is False

    def test_float(self):
        assert isiterable(3.14) is False

    def test_none(self):
        assert isiterable(None) is False

    def test_bool(self):
        assert isiterable(True) is False

    def test_empty_list(self):
        assert isiterable([]) is True

    def test_bytes(self):
        assert isiterable(b"data") is True


# ──────────────────────────────────────────────
# recursive_any
# ──────────────────────────────────────────────


class TestRecursiveAny:
    def test_flat_truthy(self):
        assert recursive_any([0, 0, 1]) is True

    def test_flat_falsy(self):
        assert recursive_any([0, 0, 0]) is False

    def test_nested_truthy(self):
        assert recursive_any([[0, 0], [0, 1]]) is True

    def test_nested_falsy(self):
        assert recursive_any([[0, 0], [0, 0]]) is False

    def test_deeply_nested(self):
        assert recursive_any([[[0]], [[0, [0, [1]]]]]) is True

    def test_deeply_nested_all_false(self):
        assert recursive_any([[[0]], [[0, [0, [0]]]]]) is False

    def test_empty(self):
        assert recursive_any([]) is False

    def test_empty_nested(self):
        assert recursive_any([[], [[]]]) is False

    def test_with_strings_recursion(self):
        # Strings are iterable, so recursive_any descends into chars,
        # which are themselves iterable strings -> infinite recursion.
        # This is a known edge case in the implementation.
        with pytest.raises(RecursionError):
            recursive_any([0, "hello"])

    def test_with_none(self):
        assert recursive_any([None, None]) is False

    def test_single_true(self):
        assert recursive_any([True]) is True

    def test_single_false(self):
        assert recursive_any([False]) is False

    def test_mixed_types(self):
        assert recursive_any([0, 0.0, False, None, []]) is False


# ──────────────────────────────────────────────
# dots
# ──────────────────────────────────────────────


class TestDots:
    def test_repr(self):
        d = dots()
        assert repr(d) == "..."

    def test_str_uses_repr(self):
        d = dots()
        # str() falls back to __repr__ if no __str__
        assert str(d) == "..."

    def test_multiple_instances(self):
        d1 = dots()
        d2 = dots()
        assert repr(d1) == repr(d2)
