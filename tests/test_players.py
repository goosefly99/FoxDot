"""
Unit tests for FoxDot.lib.Players utility classes.

Tests cover:
- rest: silence duration object with arithmetic, comparison, and conversion
- EmptyPlayer: placeholder for lazily-initialized Player objects
- Group: collection of players with propagated attribute access
- GroupAttr: list subclass that forwards calls to callable items
- PlayerKeyException: custom exception type
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from FoxDot.lib.Players import rest, EmptyPlayer, Group, GroupAttr, PlayerKeyException


# ══════════════════════════════════════════════════
# rest
# ══════════════════════════════════════════════════


class TestRestConstruction:
    """Tests for rest.__init__."""

    def test_default_duration(self):
        r = rest()
        assert r.dur == 1

    def test_explicit_integer_duration(self):
        r = rest(4)
        assert r.dur == 4

    def test_explicit_float_duration(self):
        r = rest(0.5)
        assert r.dur == 0.5

    def test_zero_duration(self):
        r = rest(0)
        assert r.dur == 0

    def test_negative_duration(self):
        r = rest(-2)
        assert r.dur == -2

    def test_nested_rest_unwraps(self):
        inner = rest(3)
        outer = rest(inner)
        assert outer.dur == 3

    def test_double_nested_rest_unwraps(self):
        r = rest(rest(rest(7)))
        assert r.dur == 7

    def test_large_duration(self):
        r = rest(10000)
        assert r.dur == 10000

    def test_fractional_duration(self):
        r = rest(1 / 3)
        assert r.dur == pytest.approx(1 / 3)


class TestRestRepr:
    """Tests for rest.__repr__."""

    def test_repr_default(self):
        assert repr(rest()) == "<rest: 1>"

    def test_repr_integer(self):
        assert repr(rest(4)) == "<rest: 4>"

    def test_repr_float(self):
        assert repr(rest(0.5)) == "<rest: 0.5>"

    def test_repr_zero(self):
        assert repr(rest(0)) == "<rest: 0>"

    def test_repr_negative(self):
        assert repr(rest(-1)) == "<rest: -1>"


class TestRestAdd:
    """Tests for rest.__add__ and __radd__."""

    def test_add_integer(self):
        r = rest(2) + 3
        assert isinstance(r, rest)
        assert r.dur == 5

    def test_add_float(self):
        r = rest(1) + 0.5
        assert isinstance(r, rest)
        assert r.dur == 1.5

    def test_add_zero(self):
        r = rest(5) + 0
        assert r.dur == 5

    def test_radd_integer(self):
        r = 3 + rest(2)
        assert isinstance(r, rest)
        assert r.dur == 5

    def test_radd_float(self):
        r = 0.5 + rest(1)
        assert isinstance(r, rest)
        assert r.dur == 1.5

    def test_radd_zero(self):
        r = 0 + rest(5)
        assert r.dur == 5


class TestRestSub:
    """Tests for rest.__sub__ and __rsub__."""

    def test_sub_integer(self):
        r = rest(5) - 2
        assert isinstance(r, rest)
        assert r.dur == 3

    def test_sub_float(self):
        r = rest(3) - 0.5
        assert r.dur == 2.5

    def test_sub_results_negative(self):
        r = rest(1) - 5
        assert r.dur == -4

    def test_rsub_integer(self):
        r = 10 - rest(3)
        assert isinstance(r, rest)
        assert r.dur == 7

    def test_rsub_results_negative(self):
        r = 1 - rest(5)
        assert r.dur == -4


class TestRestMul:
    """Tests for rest.__mul__ and __rmul__."""

    def test_mul_integer(self):
        r = rest(3) * 4
        assert isinstance(r, rest)
        assert r.dur == 12

    def test_mul_float(self):
        r = rest(2) * 0.5
        assert r.dur == 1.0

    def test_mul_zero(self):
        r = rest(5) * 0
        assert r.dur == 0

    def test_rmul_integer(self):
        r = 4 * rest(3)
        assert isinstance(r, rest)
        assert r.dur == 12

    def test_rmul_float(self):
        r = 0.5 * rest(2)
        assert r.dur == 1.0


class TestRestDiv:
    """Tests for rest.__truediv__ and __rtruediv__."""

    def test_truediv_integer(self):
        r = rest(10) / 2
        assert isinstance(r, rest)
        assert r.dur == pytest.approx(5.0)

    def test_truediv_float(self):
        r = rest(3) / 0.5
        assert r.dur == pytest.approx(6.0)

    def test_truediv_results_fraction(self):
        r = rest(1) / 3
        assert r.dur == pytest.approx(1 / 3)

    def test_rtruediv_integer(self):
        r = 10 / rest(2)
        assert isinstance(r, rest)
        assert r.dur == pytest.approx(5.0)

    def test_rtruediv_fraction(self):
        r = 1 / rest(4)
        assert r.dur == pytest.approx(0.25)


class TestRestMod:
    """Tests for rest.__mod__ and __rmod__."""

    def test_mod_integer(self):
        r = rest(7) % 3
        assert isinstance(r, rest)
        assert r.dur == 1

    def test_mod_no_remainder(self):
        r = rest(6) % 3
        assert r.dur == 0

    def test_rmod_integer(self):
        r = 10 % rest(3)
        assert isinstance(r, rest)
        assert r.dur == 1

    def test_rmod_no_remainder(self):
        r = 9 % rest(3)
        assert r.dur == 0


class TestRestComparisons:
    """Tests for rest comparison operators."""

    def test_eq_true(self):
        assert rest(5) == 5

    def test_eq_false(self):
        assert not (rest(5) == 4)

    def test_eq_float(self):
        assert rest(1.5) == 1.5

    def test_ne_true(self):
        assert rest(5) != 4

    def test_ne_false(self):
        assert not (rest(5) != 5)

    def test_lt_true(self):
        assert rest(3) < 5

    def test_lt_false(self):
        assert not (rest(5) < 3)

    def test_lt_equal(self):
        assert not (rest(3) < 3)

    def test_le_true_less(self):
        assert rest(3) <= 5

    def test_le_true_equal(self):
        assert rest(3) <= 3

    def test_le_false(self):
        assert not (rest(5) <= 3)

    def test_gt_true(self):
        assert rest(5) > 3

    def test_gt_false(self):
        assert not (rest(3) > 5)

    def test_gt_equal(self):
        assert not (rest(3) > 3)

    def test_ge_true_greater(self):
        assert rest(5) >= 3

    def test_ge_true_equal(self):
        assert rest(3) >= 3

    def test_ge_false(self):
        assert not (rest(3) >= 5)


class TestRestTypeConversion:
    """Tests for rest.__int__ and __float__."""

    def test_int_from_integer(self):
        assert int(rest(5)) == 5

    def test_int_from_float_truncates(self):
        assert int(rest(3.9)) == 3

    def test_int_type(self):
        assert isinstance(int(rest(2)), int)

    def test_float_from_integer(self):
        assert float(rest(5)) == 5.0

    def test_float_from_float(self):
        assert float(rest(2.5)) == 2.5

    def test_float_type(self):
        assert isinstance(float(rest(2)), float)


class TestRestChainedArithmetic:
    """Tests for chaining multiple arithmetic operations on rest."""

    def test_add_then_mul(self):
        r = (rest(2) + 3) * 2
        assert isinstance(r, rest)
        assert r.dur == 10

    def test_mul_then_sub(self):
        r = (rest(3) * 4) - 2
        assert isinstance(r, rest)
        assert r.dur == 10

    def test_complex_chain(self):
        r = ((rest(10) - 4) * 2) + 1
        assert isinstance(r, rest)
        assert r.dur == 13

    def test_division_chain(self):
        r = (rest(12) / 3) / 2
        assert isinstance(r, rest)
        assert r.dur == pytest.approx(2.0)

    def test_mod_after_add(self):
        r = (rest(5) + 3) % 3
        assert isinstance(r, rest)
        assert r.dur == 2


class TestRestEdgeCases:
    """Edge case tests for rest."""

    def test_identity_add(self):
        r = rest(0) + 0
        assert r.dur == 0

    def test_identity_mul(self):
        r = rest(1) * 1
        assert r.dur == 1

    def test_negative_mul(self):
        r = rest(3) * -1
        assert r.dur == -3

    def test_negative_add(self):
        r = rest(3) + (-5)
        assert r.dur == -2

    def test_very_small_float(self):
        r = rest(0.001)
        assert r.dur == pytest.approx(0.001)

    def test_bool_of_rest_zero_eq(self):
        """rest(0) == 0 should be True."""
        assert rest(0) == 0

    def test_bool_of_rest_nonzero_ne(self):
        assert rest(5) != 0


# ══════════════════════════════════════════════════
# EmptyPlayer
# ══════════════════════════════════════════════════


class TestEmptyPlayerConstruction:
    """Tests for EmptyPlayer.__init__."""

    def test_name_stored(self):
        ep = EmptyPlayer.__new__(EmptyPlayer)
        ep.__init__("p1")
        assert ep.name == "p1"

    def test_name_string(self):
        ep = EmptyPlayer.__new__(EmptyPlayer)
        ep.__init__("ab")
        assert isinstance(ep.name, str)


class TestEmptyPlayerRepr:
    """Tests for EmptyPlayer.__repr__."""

    def test_repr_format(self):
        ep = EmptyPlayer.__new__(EmptyPlayer)
        ep.__init__("p1")
        assert repr(ep) == "<p1 - Unassigned>"

    def test_repr_different_name(self):
        ep = EmptyPlayer.__new__(EmptyPlayer)
        ep.__init__("xy")
        assert repr(ep) == "<xy - Unassigned>"

    def test_repr_long_name(self):
        ep = EmptyPlayer.__new__(EmptyPlayer)
        ep.__init__("longname")
        assert "longname" in repr(ep)


class TestEmptyPlayerClassType:
    """Tests for EmptyPlayer class identity."""

    def test_is_instance(self):
        ep = EmptyPlayer.__new__(EmptyPlayer)
        ep.__init__("p1")
        assert isinstance(ep, EmptyPlayer)

    def test_class_name(self):
        ep = EmptyPlayer.__new__(EmptyPlayer)
        ep.__init__("p1")
        assert ep.__class__.__name__ == "EmptyPlayer"


class TestEmptyPlayerAttributeAccess:
    """Tests for EmptyPlayer attribute access patterns."""

    def test_name_accessible(self):
        ep = EmptyPlayer.__new__(EmptyPlayer)
        ep.__init__("p1")
        assert ep.name == "p1"

    def test_repr_callable(self):
        ep = EmptyPlayer.__new__(EmptyPlayer)
        ep.__init__("p1")
        assert callable(ep.__repr__)

    def test_has_rshift(self):
        ep = EmptyPlayer.__new__(EmptyPlayer)
        ep.__init__("p1")
        assert hasattr(ep, "__rshift__")

    def test_has_invert(self):
        ep = EmptyPlayer.__new__(EmptyPlayer)
        ep.__init__("p1")
        assert hasattr(ep, "__invert__")

    def test_setting_custom_attr(self):
        """Setting a custom attribute directly on EmptyPlayer should work."""
        ep = EmptyPlayer.__new__(EmptyPlayer)
        ep.__init__("p1")
        ep.custom = 42
        assert ep.custom == 42

    def test_multiple_instances_independent(self):
        ep1 = EmptyPlayer.__new__(EmptyPlayer)
        ep1.__init__("a1")
        ep2 = EmptyPlayer.__new__(EmptyPlayer)
        ep2.__init__("b2")
        assert ep1.name != ep2.name

    def test_repr_after_name_change(self):
        ep = EmptyPlayer.__new__(EmptyPlayer)
        ep.__init__("p1")
        ep.name = "zz"
        assert repr(ep) == "<zz - Unassigned>"


# ══════════════════════════════════════════════════
# Group
# ══════════════════════════════════════════════════


class TestGroupConstruction:
    """Tests for Group.__init__."""

    def test_empty_group(self):
        g = Group()
        assert len(g) == 0

    def test_single_player(self):
        p = MagicMock()
        g = Group(p)
        assert len(g) == 1

    def test_multiple_players(self):
        p1, p2, p3 = MagicMock(), MagicMock(), MagicMock()
        g = Group(p1, p2, p3)
        assert len(g) == 3

    def test_players_stored_as_list(self):
        p = MagicMock()
        g = Group(p)
        assert isinstance(g.players, list)

    def test_players_order_preserved(self):
        players = [MagicMock(name="p{}".format(i)) for i in range(5)]
        g = Group(*players)
        assert g.players == players


class TestGroupAdd:
    """Tests for Group.add."""

    def test_add_increases_length(self):
        g = Group()
        p = MagicMock()
        g.add(p)
        assert len(g) == 1

    def test_add_multiple(self):
        g = Group()
        for _ in range(5):
            g.add(MagicMock())
        assert len(g) == 5

    def test_add_appends_to_end(self):
        p1, p2 = MagicMock(), MagicMock()
        g = Group(p1)
        g.add(p2)
        assert g.players[-1] is p2

    def test_add_same_player_twice(self):
        p = MagicMock()
        g = Group()
        g.add(p)
        g.add(p)
        assert len(g) == 2


class TestGroupLen:
    """Tests for Group.__len__."""

    def test_len_empty(self):
        assert len(Group()) == 0

    def test_len_one(self):
        assert len(Group(MagicMock())) == 1

    def test_len_after_add(self):
        g = Group()
        g.add(MagicMock())
        g.add(MagicMock())
        assert len(g) == 2


class TestGroupStr:
    """Tests for Group.__str__."""

    def test_str_empty(self):
        assert str(Group()) == "[]"

    def test_str_matches_list_repr(self):
        p1, p2 = MagicMock(), MagicMock()
        g = Group(p1, p2)
        assert str(g) == str([p1, p2])


class TestGroupSetattr:
    """Tests for Group.__setattr__ propagation."""

    def test_setattr_propagates_to_players(self):
        p1 = MagicMock()
        p2 = MagicMock()
        g = Group(p1, p2)
        g.degree = 5
        # setattr on MagicMock stores the attribute directly
        assert p1.degree == 5
        assert p2.degree == 5

    def test_setattr_propagates_value(self):
        """Verify the attribute is set on each mock player."""
        p1, p2 = MagicMock(), MagicMock()
        g = Group(p1, p2)
        g.degree = [0, 2, 4]
        assert p1.degree == [0, 2, 4]
        assert p2.degree == [0, 2, 4]

    def test_setattr_players_initialised_via_init(self):
        """The __init__ sets players through the KeyError path in __setattr__."""
        p = MagicMock()
        g = Group(p)
        assert g.players == [p]

    def test_setattr_on_empty_group_no_error(self):
        g = Group()
        # With empty player list, setting attr just iterates over nothing
        g.foo = "bar"
        # Should not raise


class TestGroupGetattr:
    """Tests for Group.__getattr__."""

    def test_getattr_returns_group_attr(self):
        p = MagicMock()
        p.degree = 5
        g = Group(p)
        result = g.degree
        assert isinstance(result, GroupAttr)

    def test_getattr_collects_attributes(self):
        p1, p2 = MagicMock(), MagicMock()
        p1.degree = 3
        p2.degree = 7
        g = Group(p1, p2)
        result = g.degree
        assert len(result) == 2
        assert 3 in result
        assert 7 in result

    def test_getattr_skips_missing(self):
        p1 = MagicMock(spec=["degree"])
        p1.degree = 5
        p2 = MagicMock(spec=[])  # no degree attribute
        g = Group(p1, p2)
        result = g.degree
        assert len(result) == 1

    def test_getattr_empty_group(self):
        g = Group()
        result = g.foo
        assert isinstance(result, GroupAttr)
        assert len(result) == 0


class TestGroupIterate:
    """Tests for Group.iterate."""

    def test_iterate_zero_dur_sets_amplify(self):
        p1, p2 = MagicMock(), MagicMock()
        g = Group(p1, p2)
        g.iterate(dur=0)
        # dur=0 branch sets self.amplify = 1, which propagates to players
        # Should not raise

    def test_iterate_none_dur_sets_amplify(self):
        p1, p2 = MagicMock(), MagicMock()
        g = Group(p1, p2)
        g.iterate(dur=None)
        # Same branch as dur=0

    def test_iterate_returns_none(self):
        p1, p2 = MagicMock(), MagicMock()
        g = Group(p1, p2)
        result = g.iterate(dur=0)
        assert result is None

    def test_iterate_positive_dur_sets_amplify_on_players(self):
        """With positive dur, iterate should set amplify on each player."""
        p1, p2 = MagicMock(), MagicMock()
        g = Group(p1, p2)
        # This will try to create TimeVar objects and set amplify
        # which requires setting attributes on mock players
        with patch("FoxDot.lib.Players.TimeVar") as mock_tv:
            mock_tv.return_value = "timevar_obj"
            g.iterate(dur=4)
            # amplify should have been set on each player
            assert mock_tv.call_count == 2


class TestGroupSolo:
    """Tests for Group.solo with mocked metro."""

    def test_solo_true_sets_metro_solo(self):
        p1, p2 = MagicMock(), MagicMock()
        g = Group(p1, p2)
        mock_metro = MagicMock()
        g.__class__.metro = mock_metro
        g.solo(True)
        mock_metro.solo.set.assert_called_once_with(p1)
        mock_metro.solo.add.assert_called_once_with(p2)
        # Reset class state
        Group.metro = None

    def test_solo_false_resets(self):
        p1 = MagicMock()
        g = Group(p1)
        mock_metro = MagicMock()
        g.__class__.metro = mock_metro
        g.solo(False)
        mock_metro.solo.reset.assert_called_once()
        Group.metro = None

    def test_solo_returns_self(self):
        p1 = MagicMock()
        g = Group(p1)
        mock_metro = MagicMock()
        g.__class__.metro = mock_metro
        result = g.solo(True)
        assert result is g
        Group.metro = None


class TestGroupOnly:
    """Tests for Group.only with mocked metro."""

    def test_only_stops_non_group_players(self):
        p1 = MagicMock()
        p2 = MagicMock()
        p3 = MagicMock()
        g = Group(p1, p2)
        mock_metro = MagicMock()
        mock_metro.playing = [p1, p2, p3]
        g.__class__.metro = mock_metro
        g.only()
        p3.stop.assert_called_once()
        p1.stop.assert_not_called()
        p2.stop.assert_not_called()
        Group.metro = None

    def test_only_returns_self(self):
        p1 = MagicMock()
        g = Group(p1)
        mock_metro = MagicMock()
        mock_metro.playing = [p1]
        g.__class__.metro = mock_metro
        result = g.only()
        assert result is g
        Group.metro = None


# ══════════════════════════════════════════════════
# GroupAttr
# ══════════════════════════════════════════════════


class TestGroupAttrIsListSubclass:
    """Tests for GroupAttr list inheritance."""

    def test_is_list_subclass(self):
        ga = GroupAttr()
        assert isinstance(ga, list)

    def test_empty_group_attr(self):
        ga = GroupAttr()
        assert len(ga) == 0

    def test_append_works(self):
        ga = GroupAttr()
        ga.append(42)
        assert len(ga) == 1
        assert ga[0] == 42

    def test_extend_works(self):
        ga = GroupAttr()
        ga.extend([1, 2, 3])
        assert list(ga) == [1, 2, 3]

    def test_indexing(self):
        ga = GroupAttr()
        ga.append("a")
        ga.append("b")
        assert ga[1] == "b"


class TestGroupAttrCall:
    """Tests for GroupAttr.__call__."""

    def test_call_invokes_callable_items(self):
        fn1 = MagicMock()
        fn2 = MagicMock()
        ga = GroupAttr()
        ga.append(fn1)
        ga.append(fn2)
        ga()
        fn1.assert_called_once()
        fn2.assert_called_once()

    def test_call_passes_args(self):
        fn = MagicMock()
        ga = GroupAttr()
        ga.append(fn)
        ga(1, 2, key="val")
        fn.assert_called_once_with(1, 2, key="val")

    def test_call_skips_non_callable(self):
        ga = GroupAttr()
        ga.append(42)  # not callable
        ga()  # should not raise

    def test_call_mixed_callable_and_non_callable(self):
        fn1 = MagicMock()
        fn2 = MagicMock()
        ga = GroupAttr()
        ga.append(fn1)
        ga.append("not callable")
        ga.append(fn2)
        ga()
        fn1.assert_called_once()
        fn2.assert_called_once()

    def test_call_empty_group_attr(self):
        ga = GroupAttr()
        ga()  # should not raise


# ══════════════════════════════════════════════════
# PlayerKeyException
# ══════════════════════════════════════════════════


class TestPlayerKeyException:
    """Tests for PlayerKeyException."""

    def test_is_exception_subclass(self):
        assert issubclass(PlayerKeyException, Exception)

    def test_can_be_raised(self):
        with pytest.raises(PlayerKeyException):
            raise PlayerKeyException()

    def test_can_be_raised_with_message(self):
        with pytest.raises(PlayerKeyException, match="test error"):
            raise PlayerKeyException("test error")

    def test_caught_as_exception(self):
        try:
            raise PlayerKeyException("err")
        except Exception as e:
            assert str(e) == "err"

    def test_instance_check(self):
        exc = PlayerKeyException("hello")
        assert isinstance(exc, PlayerKeyException)
        assert isinstance(exc, Exception)
