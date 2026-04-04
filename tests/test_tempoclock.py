"""
Unit tests for TempoClock module: SoloPlayer, QueueObj, QueueBlock, Queue,
History, ScheduleError, Wrapper, and TempoClock pure computation methods.
"""

import os
import sys
import time
import types
import unittest
from unittest.mock import MagicMock, patch, PropertyMock
from types import FunctionType, MethodType


# ---------------------------------------------------------------------------
# Helpers – minimal stubs so we can import TempoClock classes without booting
# the full FoxDot stack.
# ---------------------------------------------------------------------------

# Create proper package stubs with __path__ so Python's import system can
# traverse FoxDot.lib and find TempoClock.py on disk.  Using MagicMock for
# the parent packages breaks import traversal because MagicMock lacks __path__.
_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_pkg_dir = os.path.join(_repo_root, "FoxDot")
_lib_dir = os.path.join(_pkg_dir, "lib")

_foxdot_pkg = types.ModuleType("FoxDot")
_foxdot_pkg.__path__ = [_pkg_dir]
_foxdot_pkg.__package__ = "FoxDot"

_lib_pkg = types.ModuleType("FoxDot.lib")
_lib_pkg.__path__ = [_lib_dir]
_lib_pkg.__package__ = "FoxDot.lib"

# Save original sys.modules state so we can restore after importing TempoClock.
# This prevents our mocks from poisoning other test modules (e.g., test_timevar).
_MOCKED_KEYS = [
    "FoxDot", "FoxDot.lib", "FoxDot.lib.Settings", "FoxDot.lib.Players",
    "FoxDot.lib.Repeat", "FoxDot.lib.Patterns", "FoxDot.lib.TimeVar",
    "FoxDot.lib.Midi", "FoxDot.lib.Utils", "FoxDot.lib.ServerManager",
    "FoxDot.lib.Code", "FoxDot.lib.TempoClock",
]
_saved_modules = {k: sys.modules.get(k) for k in _MOCKED_KEYS}

# Force-replace (not setdefault) to handle case where earlier tests already
# imported the real FoxDot.lib.  We need our mocks active during import.
sys.modules["FoxDot"] = _foxdot_pkg
sys.modules["FoxDot.lib"] = _lib_pkg

_settings_mod = MagicMock()
_settings_mod.CPU_USAGE = 0
_settings_mod.CLOCK_LATENCY = 0.25
sys.modules["FoxDot.lib.Settings"] = _settings_mod

# We need real classes for Players, Repeat, Patterns, TimeVar, Midi, Utils, ServerManager, Code
# but want to avoid their heavy side-effects.  Import selectively.

# Rather than importing TempoClock module directly (which triggers many
# cross-imports), we import the individual classes after careful patching.

# First, let's set up minimal mocks for the imports TempoClock needs
_players_mod = MagicMock()


class _FakePlayer:
    """Minimal Player stub for testing priority classification."""
    pass


_players_mod.Player = _FakePlayer
sys.modules["FoxDot.lib.Players"] = _players_mod

_repeat_mod = MagicMock()


class _FakeMethodCall:
    """Minimal MethodCall stub for testing priority classification."""
    pass


_repeat_mod.MethodCall = _FakeMethodCall
sys.modules["FoxDot.lib.Repeat"] = _repeat_mod

_patterns_mod = MagicMock()
_patterns_mod.asStream = lambda x: list(x) if hasattr(x, '__iter__') else [x]
sys.modules["FoxDot.lib.Patterns"] = _patterns_mod

_timevar_mod = MagicMock()


class _FakeTimeVar:
    """Minimal TimeVar stub."""
    def __init__(self, vals, dur):
        self.vals = vals
        self.dur = dur
    def now(self, beat):
        return self.vals[0]
    def json_value(self):
        return {"type": "TimeVar", "vals": self.vals}


_timevar_mod.TimeVar = _FakeTimeVar
sys.modules["FoxDot.lib.TimeVar"] = _timevar_mod

_midi_mod = MagicMock()
_midi_mod.MidiIn = MagicMock
_midi_mod.MIDIDeviceNotFound = type("MIDIDeviceNotFound", (Exception,), {})
sys.modules["FoxDot.lib.Midi"] = _midi_mod

_utils_mod = MagicMock()
_utils_mod.modi = lambda lst, n: lst[n % len(lst)] if isinstance(lst, (list, tuple)) and len(lst) > 0 else lst
sys.modules["FoxDot.lib.Utils"] = _utils_mod

_sm_mod = MagicMock()
_sm_mod.TempoClient = MagicMock
_sm_mod.ServerManager = type("ServerManager", (), {})
_sm_mod.RequestTimeout = type("RequestTimeout", (Exception,), {})
sys.modules["FoxDot.lib.ServerManager"] = _sm_mod

# Code module with LiveObject
_code_mod = MagicMock()


class _FakeLiveObject:
    def __call__(self):
        pass


_code_mod.LiveObject = _FakeLiveObject
sys.modules["FoxDot.lib.Code"] = _code_mod

# Remove any pre-cached TempoClock so we get a fresh import with our mocks
sys.modules.pop("FoxDot.lib.TempoClock", None)

# Now we can import TempoClock classes
from FoxDot.lib.TempoClock import (
    SoloPlayer, QueueObj, QueueBlock, Queue, History,
    ScheduleError, TempoClock, Wrapper,
)

# Restore sys.modules to prevent mock leakage into other test files
for _k in _MOCKED_KEYS:
    if _saved_modules[_k] is None:
        sys.modules.pop(_k, None)
    else:
        sys.modules[_k] = _saved_modules[_k]
del _saved_modules, _MOCKED_KEYS, _k


# ============================================================================
# SoloPlayer Tests
# ============================================================================

class TestSoloPlayerInit(unittest.TestCase):
    def test_init_empty(self):
        sp = SoloPlayer()
        self.assertEqual(sp.data, [])

    def test_repr_empty(self):
        sp = SoloPlayer()
        self.assertEqual(repr(sp), "None")


class TestSoloPlayerAdd(unittest.TestCase):
    def test_add_single(self):
        sp = SoloPlayer()
        sp.add("player1")
        self.assertEqual(sp.data, ["player1"])

    def test_add_duplicate_ignored(self):
        sp = SoloPlayer()
        sp.add("player1")
        sp.add("player1")
        self.assertEqual(len(sp.data), 1)

    def test_add_multiple_unique(self):
        sp = SoloPlayer()
        sp.add("p1")
        sp.add("p2")
        sp.add("p3")
        self.assertEqual(sp.data, ["p1", "p2", "p3"])


class TestSoloPlayerSet(unittest.TestCase):
    def test_set_replaces_list(self):
        sp = SoloPlayer()
        sp.add("p1")
        sp.add("p2")
        sp.set("p3")
        self.assertEqual(sp.data, ["p3"])

    def test_set_on_empty(self):
        sp = SoloPlayer()
        sp.set("p1")
        self.assertEqual(sp.data, ["p1"])


class TestSoloPlayerReset(unittest.TestCase):
    def test_reset_clears(self):
        sp = SoloPlayer()
        sp.add("p1")
        sp.add("p2")
        sp.reset()
        self.assertEqual(sp.data, [])


class TestSoloPlayerActive(unittest.TestCase):
    def test_not_active_when_empty(self):
        sp = SoloPlayer()
        self.assertFalse(sp.active())

    def test_active_after_add(self):
        sp = SoloPlayer()
        sp.add("p1")
        self.assertTrue(sp.active())

    def test_not_active_after_reset(self):
        sp = SoloPlayer()
        sp.add("p1")
        sp.reset()
        self.assertFalse(sp.active())


class TestSoloPlayerEquality(unittest.TestCase):
    def test_eq_empty_always_true(self):
        """When no solo is set, every player is 'allowed'."""
        sp = SoloPlayer()
        self.assertTrue(sp == "any_player")
        self.assertTrue(sp == 42)

    def test_eq_with_solo_matching(self):
        sp = SoloPlayer()
        sp.add("p1")
        self.assertTrue(sp == "p1")

    def test_eq_with_solo_not_matching(self):
        sp = SoloPlayer()
        sp.add("p1")
        self.assertFalse(sp == "p2")

    def test_ne_empty_always_true(self):
        """When no solo is set, ne returns True (every player passes)."""
        sp = SoloPlayer()
        self.assertTrue(sp != "any_player")

    def test_ne_with_solo_matching(self):
        sp = SoloPlayer()
        sp.add("p1")
        self.assertFalse(sp != "p1")

    def test_ne_with_solo_not_matching(self):
        sp = SoloPlayer()
        sp.add("p1")
        self.assertTrue(sp != "p2")


class TestSoloPlayerRepr(unittest.TestCase):
    def test_repr_single(self):
        sp = SoloPlayer()
        sp.add("p1")
        self.assertEqual(repr(sp), repr("p1"))

    def test_repr_multiple(self):
        sp = SoloPlayer()
        sp.add("p1")
        sp.add("p2")
        self.assertEqual(repr(sp), repr(["p1", "p2"]))


# ============================================================================
# QueueObj Tests
# ============================================================================

class TestQueueObjInit(unittest.TestCase):
    def test_defaults(self):
        fn = lambda: 42
        qo = QueueObj(fn)
        self.assertIs(qo.obj, fn)
        self.assertEqual(qo.args, ())
        self.assertEqual(qo.kwargs, {})
        self.assertFalse(qo.called)

    def test_with_args_kwargs(self):
        fn = lambda x, y=1: x + y
        qo = QueueObj(fn, args=(10,), kwargs={"y": 5})
        self.assertEqual(qo.args, (10,))
        self.assertEqual(qo.kwargs, {"y": 5})

    def test_none_kwargs_becomes_empty_dict(self):
        fn = lambda: None
        qo = QueueObj(fn, kwargs=None)
        self.assertEqual(qo.kwargs, {})


class TestQueueObjEquality(unittest.TestCase):
    def test_eq_with_same_obj(self):
        fn = lambda: None
        qo = QueueObj(fn)
        self.assertTrue(qo == fn)

    def test_eq_with_different_obj(self):
        fn1 = lambda: 1
        fn2 = lambda: 2
        qo = QueueObj(fn1)
        self.assertFalse(qo == fn2)

    def test_ne_with_different_obj(self):
        fn1 = lambda: 1
        fn2 = lambda: 2
        qo = QueueObj(fn1)
        self.assertTrue(qo != fn2)

    def test_ne_with_same_obj(self):
        fn = lambda: None
        qo = QueueObj(fn)
        self.assertFalse(qo != fn)


class TestQueueObjRepr(unittest.TestCase):
    def test_repr_uses_obj_repr(self):
        class Named:
            def __repr__(self):
                return "<Named>"
        obj = Named()
        qo = QueueObj(obj)
        self.assertEqual(repr(qo), "<Named>")


class TestQueueObjCall(unittest.TestCase):
    def test_call_invokes_obj(self):
        fn = MagicMock(return_value=99)
        qo = QueueObj(fn, args=(1, 2), kwargs={"k": 3})
        result = qo()
        fn.assert_called_once_with(1, 2, k=3)
        self.assertTrue(qo.called)

    def test_call_returns_value(self):
        fn = lambda: 42
        qo = QueueObj(fn)
        self.assertEqual(qo(), 42)
        self.assertTrue(qo.called)

    def test_called_flag_starts_false(self):
        qo = QueueObj(lambda: None)
        self.assertFalse(qo.called)

    def test_called_flag_true_after_call(self):
        qo = QueueObj(lambda: None)
        qo()
        self.assertTrue(qo.called)


# ============================================================================
# History Tests
# ============================================================================

class TestHistory(unittest.TestCase):
    def test_init_empty(self):
        h = History()
        self.assertEqual(h.data, [])

    def test_add_stores_messages(self):
        h = History()
        h.add(0, ["msg1", "msg2"])
        h.add(1, ["msg3"])
        self.assertEqual(len(h.data), 2)
        self.assertEqual(h.data[0], ["msg1", "msg2"])
        self.assertEqual(h.data[1], ["msg3"])


# ============================================================================
# ScheduleError Tests
# ============================================================================

class TestScheduleError(unittest.TestCase):
    def test_str_includes_type(self):
        err = ScheduleError(42)
        self.assertIn("int", str(err))

    def test_str_for_string(self):
        err = ScheduleError("hello")
        self.assertIn("str", str(err))

    def test_is_exception(self):
        self.assertTrue(issubclass(ScheduleError, Exception))

    def test_str_format(self):
        err = ScheduleError([1, 2])
        self.assertTrue(str(err).startswith("Could not schedule object of"))


# ============================================================================
# Queue Tests (requires minimal parent mock)
# ============================================================================

def _make_mock_parent():
    """Create a mock parent clock for Queue/QueueBlock."""
    parent = MagicMock()
    parent.server = MagicMock()
    parent.server.sendOSC = MagicMock()
    parent.get_time = MagicMock(return_value=time.time())
    parent.beat = 0.0
    return parent


class TestQueueInit(unittest.TestCase):
    def test_init(self):
        parent = _make_mock_parent()
        q = Queue(parent)
        self.assertEqual(q.data, [])
        self.assertIs(q.parent, parent)


class TestQueueRepr(unittest.TestCase):
    def test_empty_repr(self):
        q = Queue(_make_mock_parent())
        self.assertEqual(repr(q), "[]")


class TestQueueClear(unittest.TestCase):
    def test_clear_empties_data(self):
        q = Queue(_make_mock_parent())
        # Manually add items
        q.data.append("item1")
        q.data.append("item2")
        q.clear()
        self.assertEqual(len(q.data), 0)


class TestQueuePop(unittest.TestCase):
    def test_pop_empty_returns_list(self):
        q = Queue(_make_mock_parent())
        result = q.pop()
        self.assertEqual(result, [])

    def test_pop_returns_last_item(self):
        q = Queue(_make_mock_parent())
        q.data.append("first")
        q.data.append("second")
        result = q.pop()
        self.assertEqual(result, "second")
        self.assertEqual(len(q.data), 1)


class TestQueueNext(unittest.TestCase):
    def test_next_empty_returns_maxsize(self):
        q = Queue(_make_mock_parent())
        self.assertEqual(q.next(), sys.maxsize)

    def test_next_returns_last_beat(self):
        q = Queue(_make_mock_parent())
        block = MagicMock()
        block.beat = 4.0
        q.data.append(block)
        self.assertEqual(q.next(), 4.0)


class TestQueueBeforeAfterNextEvent(unittest.TestCase):
    def test_before_next_event_empty_true(self):
        q = Queue(_make_mock_parent())
        self.assertTrue(q.before_next_event(0))

    def test_before_next_event_true(self):
        q = Queue(_make_mock_parent())
        block = MagicMock()
        block.beat = 8.0
        q.data.append(block)
        self.assertTrue(q.before_next_event(4.0))

    def test_before_next_event_false(self):
        q = Queue(_make_mock_parent())
        block = MagicMock()
        block.beat = 4.0
        q.data.append(block)
        self.assertFalse(q.before_next_event(8.0))

    def test_after_next_event_empty_false(self):
        q = Queue(_make_mock_parent())
        self.assertFalse(q.after_next_event(0))

    def test_after_next_event_true(self):
        q = Queue(_make_mock_parent())
        block = MagicMock()
        block.beat = 4.0
        q.data.append(block)
        self.assertTrue(q.after_next_event(4.0))

    def test_after_next_event_false(self):
        q = Queue(_make_mock_parent())
        block = MagicMock()
        block.beat = 8.0
        q.data.append(block)
        self.assertFalse(q.after_next_event(4.0))

    def test_after_next_event_equal_beat(self):
        q = Queue(_make_mock_parent())
        block = MagicMock()
        block.beat = 4.0
        q.data.append(block)
        self.assertTrue(q.after_next_event(4.0))


class TestQueueGetServerClock(unittest.TestCase):
    def test_get_server(self):
        parent = _make_mock_parent()
        q = Queue(parent)
        self.assertIs(q.get_server(), parent.server)

    def test_get_clock(self):
        parent = _make_mock_parent()
        q = Queue(parent)
        self.assertIs(q.get_clock(), parent)


# ============================================================================
# QueueBlock Tests
# ============================================================================

def _make_queue_block(obj=None, beat=0.0):
    """Create a QueueBlock with a mock parent Queue."""
    parent = MagicMock()
    parent.get_server.return_value = MagicMock()
    parent.get_server.return_value.sendOSC = MagicMock()
    parent.get_clock.return_value = MagicMock()
    if obj is None:
        obj = lambda: None
    return QueueBlock(parent, obj, beat)


class TestQueueBlockInit(unittest.TestCase):
    def test_init_sets_beat(self):
        qb = _make_queue_block(beat=4.0)
        self.assertEqual(qb.beat, 4.0)

    def test_init_has_time_zero(self):
        qb = _make_queue_block()
        self.assertEqual(qb.time, 0)

    def test_init_adds_object(self):
        fn = lambda: 42
        qb = _make_queue_block(obj=fn)
        self.assertEqual(len(qb), 1)

    def test_init_contains_object(self):
        fn = lambda: 42
        qb = _make_queue_block(obj=fn)
        self.assertIn(fn, qb)


class TestQueueBlockAdd(unittest.TestCase):
    def test_add_increases_length(self):
        qb = _make_queue_block()
        fn2 = lambda: 99
        qb.add(fn2)
        self.assertEqual(len(qb), 2)

    def test_add_priority_inserts_at_front(self):
        fn1 = lambda: 1
        fn2 = lambda: 2
        qb = _make_queue_block(obj=fn1)
        qb.add(fn2, is_priority=True)
        # Both are FunctionType, so they go in the same priority level
        items = list(qb)
        # Priority item should be first
        self.assertEqual(items[0].obj, fn2)

    def test_add_function_goes_to_level_0(self):
        """Functions should be in the first priority level."""
        fn = lambda: None
        qb = _make_queue_block(obj=fn)
        self.assertEqual(len(qb.events[0]), 1)

    def test_add_method_call_goes_to_level_1(self):
        """MethodCall instances should be in the second priority level."""
        mc = _FakeMethodCall()
        mc.__call__ = lambda: None
        parent = MagicMock()
        parent.get_server.return_value = MagicMock()
        parent.get_clock.return_value = MagicMock()
        # Start with a function then add MethodCall
        qb = QueueBlock(parent, lambda: None, 0.0)
        qb.add(mc)
        self.assertEqual(len(qb.events[1]), 1)

    def test_add_player_goes_to_level_2(self):
        """Player instances should be in the third priority level."""
        p = _FakePlayer()
        p.__call__ = lambda: None
        parent = MagicMock()
        parent.get_server.return_value = MagicMock()
        parent.get_clock.return_value = MagicMock()
        qb = QueueBlock(parent, lambda: None, 0.0)
        qb.add(p)
        self.assertEqual(len(qb.events[2]), 1)


class TestQueueBlockIter(unittest.TestCase):
    def test_iter_all_items(self):
        fn1 = lambda: 1
        fn2 = lambda: 2
        qb = _make_queue_block(obj=fn1)
        qb.add(fn2)
        items = list(qb)
        self.assertEqual(len(items), 2)


class TestQueueBlockLen(unittest.TestCase):
    def test_len_single(self):
        qb = _make_queue_block()
        self.assertEqual(len(qb), 1)

    def test_len_multiple(self):
        qb = _make_queue_block()
        qb.add(lambda: 2)
        qb.add(lambda: 3)
        self.assertEqual(len(qb), 3)


class TestQueueBlockContains(unittest.TestCase):
    def test_contains_added_object(self):
        fn = lambda: 42
        qb = _make_queue_block(obj=fn)
        self.assertIn(fn, qb)

    def test_not_contains_other(self):
        fn1 = lambda: 1
        fn2 = lambda: 2
        qb = _make_queue_block(obj=fn1)
        self.assertNotIn(fn2, qb)


class TestQueueBlockPlayers(unittest.TestCase):
    def test_players_returns_level_1_and_2(self):
        """players() returns items from levels 1 (MethodCall) and 2 (Player)."""
        qb = _make_queue_block()
        mc = _FakeMethodCall()
        mc.__call__ = lambda: None
        p = _FakePlayer()
        p.__call__ = lambda: None
        qb.add(mc)
        qb.add(p)
        players = qb.players()
        self.assertEqual(len(players), 2)


class TestQueueBlockAllItems(unittest.TestCase):
    def test_all_items(self):
        fn = lambda: 1
        qb = _make_queue_block(obj=fn)
        qb.add(lambda: 2)
        self.assertEqual(len(qb.all_items()), 2)


class TestQueueBlockObjects(unittest.TestCase):
    def test_objects_returns_raw_callables(self):
        fn1 = lambda: 1
        fn2 = lambda: 2
        qb = _make_queue_block(obj=fn1)
        qb.add(fn2)
        objs = qb.objects()
        self.assertIn(fn1, objs)
        self.assertIn(fn2, objs)


class TestQueueBlockRepr(unittest.TestCase):
    def test_repr_contains_beat(self):
        qb = _make_queue_block(beat=4.5)
        r = repr(qb)
        self.assertIn("4.5", r)


class TestQueueBlockSendOSC(unittest.TestCase):
    def test_send_osc_messages_calls_server(self):
        qb = _make_queue_block()
        msg1 = MagicMock()
        msg2 = MagicMock()
        qb.osc_messages = [msg1, msg2]
        qb.send_osc_messages()
        self.assertEqual(qb.server.sendOSC.call_count, 2)


class TestQueueBlockAppendOSC(unittest.TestCase):
    def test_append_future_message(self):
        qb = _make_queue_block()
        qb.metro.get_time.return_value = 1000.0
        msg = MagicMock()
        msg.timetag = 2000.0  # In the future
        qb.append_osc_message(msg)
        self.assertEqual(len(qb.osc_messages), 1)

    def test_reject_past_message(self):
        qb = _make_queue_block()
        qb.metro.get_time.return_value = 2000.0
        msg = MagicMock()
        msg.timetag = 1000.0  # In the past
        qb.append_osc_message(msg)
        self.assertEqual(len(qb.osc_messages), 0)


# ============================================================================
# TempoClock Tests – pure computation methods
# ============================================================================

def _make_clock(bpm=120.0, meter=(4, 4)):
    """Create a TempoClock with thread start suppressed."""
    with patch.object(TempoClock, 'start', return_value=None):
        clock = TempoClock.__new__(TempoClock)
        # Manually init without triggering full __init__ side effects
        clock._TempoClock__setup = False
        clock.largest_sleep_time = 0
        clock.last_block_dur = 0.0
        clock.dtype = float
        clock.beat = 0.0
        clock.last_now_call = 0.0
        clock.ticking = False
        clock.playing = []
        clock.history = History()
        clock.items = []
        clock.bpm = bpm
        clock.meter = meter
        clock.queue = Queue(clock)
        clock.current_block = None
        clock.midi_clock = None
        clock.espgrid = None
        clock.now_flag = False
        clock.latency_values = [0.25, 0.5, 0.75]
        clock.latency = 0.25
        clock.nudge = 0.0
        clock.hard_nudge = 0.0
        clock.bpm_start_time = time.time()
        clock.bpm_start_beat = 0
        clock.sleep_values = [0.01, 0.001, 0.0001]
        clock.sleep_time = clock.sleep_values[0]
        clock.midi_nudge = 0
        clock.debugging = False
        clock.solo = SoloPlayer()
        clock.thread = MagicMock()
        clock._TempoClock__setup = True
        # Mock server to avoid AttributeError
        clock.server = MagicMock()
        # Mock tempo_server/client
        clock.tempo_server = None
        clock.tempo_client = None
    return clock


class TestTempoClockBarLength(unittest.TestCase):
    def test_4_4_time(self):
        clock = _make_clock(meter=(4, 4))
        self.assertEqual(clock.bar_length(), 4.0)

    def test_3_4_time(self):
        clock = _make_clock(meter=(3, 4))
        self.assertEqual(clock.bar_length(), 3.0)

    def test_6_8_time(self):
        clock = _make_clock(meter=(6, 8))
        self.assertEqual(clock.bar_length(), 3.0)

    def test_5_4_time(self):
        clock = _make_clock(meter=(5, 4))
        self.assertEqual(clock.bar_length(), 5.0)

    def test_7_8_time(self):
        clock = _make_clock(meter=(7, 8))
        self.assertEqual(clock.bar_length(), 3.5)

    def test_2_4_time(self):
        clock = _make_clock(meter=(2, 4))
        self.assertEqual(clock.bar_length(), 2.0)


class TestTempoClockBars(unittest.TestCase):
    def test_single_bar(self):
        clock = _make_clock(meter=(4, 4))
        self.assertEqual(clock.bars(1), 4.0)

    def test_multiple_bars(self):
        clock = _make_clock(meter=(4, 4))
        self.assertEqual(clock.bars(3), 12.0)

    def test_default_one_bar(self):
        clock = _make_clock(meter=(4, 4))
        self.assertEqual(clock.bars(), 4.0)

    def test_bars_3_4_time(self):
        clock = _make_clock(meter=(3, 4))
        self.assertEqual(clock.bars(2), 6.0)


class TestTempoClockBeatDur(unittest.TestCase):
    def test_120bpm_one_beat(self):
        clock = _make_clock(bpm=120.0)
        self.assertAlmostEqual(clock.beat_dur(1), 0.5)

    def test_120bpm_four_beats(self):
        clock = _make_clock(bpm=120.0)
        self.assertAlmostEqual(clock.beat_dur(4), 2.0)

    def test_60bpm_one_beat(self):
        clock = _make_clock(bpm=60.0)
        self.assertAlmostEqual(clock.beat_dur(1), 1.0)

    def test_zero_beats(self):
        clock = _make_clock(bpm=120.0)
        self.assertEqual(clock.beat_dur(0), 0)

    def test_default_one_beat(self):
        clock = _make_clock(bpm=120.0)
        self.assertAlmostEqual(clock.beat_dur(), 0.5)

    def test_fractional_beats(self):
        clock = _make_clock(bpm=120.0)
        self.assertAlmostEqual(clock.beat_dur(0.5), 0.25)


class TestTempoClockBeatsToSeconds(unittest.TestCase):
    def test_alias(self):
        clock = _make_clock(bpm=120.0)
        self.assertEqual(clock.beats_to_seconds(4), clock.beat_dur(4))


class TestTempoClockSecondsToBeats(unittest.TestCase):
    def test_120bpm(self):
        clock = _make_clock(bpm=120.0)
        self.assertAlmostEqual(clock.seconds_to_beats(1.0), 2.0)

    def test_60bpm(self):
        clock = _make_clock(bpm=60.0)
        self.assertAlmostEqual(clock.seconds_to_beats(1.0), 1.0)

    def test_inverse_of_beat_dur(self):
        clock = _make_clock(bpm=120.0)
        secs = clock.beat_dur(3)
        self.assertAlmostEqual(clock.seconds_to_beats(secs), 3.0)


class TestTempoClockGetBPM(unittest.TestCase):
    def test_static_bpm(self):
        clock = _make_clock(bpm=140.0)
        self.assertEqual(clock.get_bpm(), 140.0)

    def test_returns_float(self):
        clock = _make_clock(bpm=120)
        self.assertIsInstance(clock.get_bpm(), float)

    def test_timevar_bpm(self):
        clock = _make_clock(bpm=120.0)
        tv = _FakeTimeVar([90, 120], 4)
        object.__setattr__(clock, "bpm", tv)
        result = clock.get_bpm()
        self.assertEqual(result, 90.0)


class TestTempoClockGetLatency(unittest.TestCase):
    def test_converts_to_beats(self):
        clock = _make_clock(bpm=120.0)
        clock.latency = 0.5  # seconds
        # At 120 bpm, 0.5 seconds = 1 beat
        lat = clock.get_latency()
        self.assertAlmostEqual(lat, 1.0)


class TestTempoClockSetCpuUsage(unittest.TestCase):
    def test_low_cpu(self):
        clock = _make_clock()
        clock.set_cpu_usage(0)
        self.assertEqual(clock.sleep_time, 0.01)

    def test_medium_cpu(self):
        clock = _make_clock()
        clock.set_cpu_usage(1)
        self.assertEqual(clock.sleep_time, 0.001)

    def test_high_cpu(self):
        clock = _make_clock()
        clock.set_cpu_usage(2)
        self.assertEqual(clock.sleep_time, 0.0001)

    def test_invalid_low(self):
        clock = _make_clock()
        with self.assertRaises(ValueError):
            clock.set_cpu_usage(-1)

    def test_invalid_high(self):
        clock = _make_clock()
        with self.assertRaises(ValueError):
            clock.set_cpu_usage(3)


class TestTempoClockSetLatency(unittest.TestCase):
    def test_low_latency(self):
        clock = _make_clock()
        clock.set_latency(0)
        self.assertEqual(clock.latency, 0.25)

    def test_medium_latency(self):
        clock = _make_clock()
        clock.set_latency(1)
        self.assertEqual(clock.latency, 0.5)

    def test_high_latency(self):
        clock = _make_clock()
        clock.set_latency(2)
        self.assertEqual(clock.latency, 0.75)

    def test_invalid_low(self):
        clock = _make_clock()
        with self.assertRaises(ValueError):
            clock.set_latency(-1)

    def test_invalid_high(self):
        clock = _make_clock()
        with self.assertRaises(ValueError):
            clock.set_latency(3)


class TestTempoClockNextBar(unittest.TestCase):
    def test_from_beat_zero(self):
        clock = _make_clock(meter=(4, 4))
        clock.ticking = True
        clock.beat = 0.0
        nb = clock.next_bar()
        self.assertAlmostEqual(nb, 4.0)

    def test_from_mid_bar(self):
        clock = _make_clock(meter=(4, 4))
        clock.ticking = True
        clock.beat = 2.5
        nb = clock.next_bar()
        self.assertAlmostEqual(nb, 4.0, places=1)

    def test_from_bar_boundary(self):
        clock = _make_clock(meter=(4, 4))
        clock.ticking = True
        clock.beat = 4.0
        nb = clock.next_bar()
        self.assertAlmostEqual(nb, 8.0)

    def test_3_4_time(self):
        clock = _make_clock(meter=(3, 4))
        clock.ticking = True
        clock.beat = 1.0
        nb = clock.next_bar()
        self.assertAlmostEqual(nb, 3.0, places=1)


class TestTempoClockMod(unittest.TestCase):
    def test_mod_basic(self):
        clock = _make_clock()
        clock.ticking = True
        clock.beat = 5.0
        result = clock.mod(4)
        # 5 // 4 = 1, (1 + 1) * 4 + 0 = 8
        self.assertAlmostEqual(result, 8.0)

    def test_mod_with_offset(self):
        clock = _make_clock()
        clock.ticking = True
        clock.beat = 5.0
        result = clock.mod(4, t=1)
        # 5 // 4 = 1, (1 + 1) * 4 + 1 = 9
        self.assertAlmostEqual(result, 9.0)


class TestTempoClockShift(unittest.TestCase):
    def test_shift_forward(self):
        clock = _make_clock()
        clock.beat = 4.0
        clock.shift(2)
        self.assertEqual(clock.beat, 6.0)

    def test_shift_backward(self):
        clock = _make_clock()
        clock.beat = 4.0
        clock.shift(-1.5)
        self.assertEqual(clock.beat, 2.5)


class TestTempoClockNow(unittest.TestCase):
    def test_now_returns_float(self):
        clock = _make_clock()
        result = clock.now()
        self.assertIsInstance(result, float)

    def test_now_when_not_ticking(self):
        clock = _make_clock()
        clock.ticking = False
        # Should call _now() internally
        result = clock.now()
        self.assertIsInstance(result, float)


class TestTempoClockCalculateNudge(unittest.TestCase):
    def test_basic_calculation(self):
        clock = _make_clock()
        clock.calculate_nudge(100.0, 100.5, 0.1)
        # hard_nudge = time1 - time2 - latency = 100 - 100.5 - 0.1 = -0.6
        self.assertAlmostEqual(clock.hard_nudge, -0.6)

    def test_zero_latency(self):
        clock = _make_clock()
        clock.calculate_nudge(100.0, 99.5, 0.0)
        self.assertAlmostEqual(clock.hard_nudge, 0.5)


class TestTempoClockConvertBpmJson(unittest.TestCase):
    def test_int_bpm(self):
        clock = _make_clock()
        result = clock._convert_bpm_json(120)
        self.assertEqual(result, 120.0)
        self.assertIsInstance(result, float)

    def test_float_bpm(self):
        clock = _make_clock()
        result = clock._convert_bpm_json(140.5)
        self.assertEqual(result, 140.5)

    def test_timevar_bpm(self):
        clock = _make_clock()
        tv = _FakeTimeVar([90, 120], 4)
        result = clock._convert_bpm_json(tv)
        self.assertEqual(result, {"type": "TimeVar", "vals": [90, 120]})


class TestTempoClockJsonBpm(unittest.TestCase):
    def test_json_bpm_static(self):
        clock = _make_clock(bpm=130.0)
        result = clock.json_bpm()
        self.assertEqual(result, 130.0)


class TestTempoClockGetSyncInfo(unittest.TestCase):
    def test_returns_dict_with_sync_key(self):
        clock = _make_clock(bpm=120.0)
        info = clock.get_sync_info()
        self.assertIn("sync", info)

    def test_sync_has_required_keys(self):
        clock = _make_clock(bpm=120.0)
        info = clock.get_sync_info()
        sync = info["sync"]
        self.assertIn("bpm_start_time", sync)
        self.assertIn("bpm_start_beat", sync)
        self.assertIn("bpm", sync)

    def test_sync_bpm_value(self):
        clock = _make_clock(bpm=140.0)
        info = clock.get_sync_info()
        self.assertEqual(info["sync"]["bpm"], 140.0)


class TestTempoClockPlayers(unittest.TestCase):
    def test_players_returns_all(self):
        clock = _make_clock()
        p1, p2, p3 = "p1", "p2", "p3"
        clock.playing = [p1, p2, p3]
        self.assertEqual(clock.players(), [p1, p2, p3])

    def test_players_excludes(self):
        clock = _make_clock()
        p1, p2, p3 = "p1", "p2", "p3"
        clock.playing = [p1, p2, p3]
        result = clock.players(ex=("p2",))
        self.assertEqual(result, [p1, p3])

    def test_players_empty(self):
        clock = _make_clock()
        self.assertEqual(clock.players(), [])


class TestTempoClockDebug(unittest.TestCase):
    def test_debug_on(self):
        clock = _make_clock()
        clock.debug(True)
        self.assertTrue(clock.debugging)

    def test_debug_off(self):
        clock = _make_clock()
        clock.debug(False)
        self.assertFalse(clock.debugging)

    def test_debug_default_on(self):
        clock = _make_clock()
        clock.debug()
        self.assertTrue(clock.debugging)


class TestTempoClockStr(unittest.TestCase):
    def test_str_returns_queue_repr(self):
        clock = _make_clock()
        self.assertEqual(str(clock), "[]")


class TestTempoClockLen(unittest.TestCase):
    def test_len_empty(self):
        clock = _make_clock()
        self.assertEqual(len(clock), 0)


class TestTempoClockContains(unittest.TestCase):
    def test_contains_item(self):
        clock = _make_clock()
        clock.items.append("obj1")
        self.assertIn("obj1", clock)

    def test_not_contains(self):
        clock = _make_clock()
        self.assertNotIn("obj1", clock)


class TestTempoClockIter(unittest.TestCase):
    def test_iter_delegates_to_queue(self):
        clock = _make_clock()
        result = list(clock)
        self.assertEqual(result, [])


class TestTempoClockSwing(unittest.TestCase):
    def test_swing_zero_resets(self):
        clock = _make_clock()
        clock.swing(0)
        self.assertEqual(clock.nudge, 0)


class TestTempoClockStop(unittest.TestCase):
    def test_stop_sets_ticking_false(self):
        clock = _make_clock()
        clock.ticking = True
        clock.stop()
        self.assertFalse(clock.ticking)

    def test_stop_clears_items(self):
        clock = _make_clock()
        clock.items = ["a", "b"]
        clock.playing = []  # avoid kill() on non-player objects
        clock.stop()
        self.assertEqual(clock.items, [])


class TestTempoClockClear(unittest.TestCase):
    def test_clear_empties_items(self):
        clock = _make_clock()
        clock.items = ["a", "b"]
        clock.playing = []
        clock.clear()
        self.assertEqual(clock.items, [])

    def test_clear_resets_solo(self):
        clock = _make_clock()
        clock.solo.add("p1")
        clock.playing = []
        clock.clear()
        self.assertFalse(clock.solo.active())


class TestTempoClockUpdateTempo(unittest.TestCase):
    def test_update_tempo_rejects_zero(self):
        clock = _make_clock()
        with self.assertRaises(ValueError):
            clock.update_tempo(0)

    def test_update_tempo_rejects_negative(self):
        clock = _make_clock()
        with self.assertRaises(ValueError):
            clock.update_tempo(-10)

    def test_update_tempo_returns_tuple(self):
        clock = _make_clock()
        result = clock.update_tempo(140)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)


class TestTempoClockSetTempo(unittest.TestCase):
    def test_set_tempo_no_override(self):
        clock = _make_clock()
        result = clock.set_tempo(140)
        # Returns tuple from update_tempo
        self.assertIsInstance(result, tuple)


class TestTempoClockSetServer(unittest.TestCase):
    def test_set_server_rejects_non_server(self):
        with self.assertRaises(TypeError):
            TempoClock.set_server("not_a_server")


class TestTempoClockAddMethod(unittest.TestCase):
    def test_add_method(self):
        def my_func():
            return 42
        TempoClock.add_method(my_func)
        self.assertTrue(hasattr(TempoClock, "my_func"))
        # Cleanup
        delattr(TempoClock, "my_func")


class TestTempoClockGetTimeAtBeat(unittest.TestCase):
    def test_future_beat(self):
        clock = _make_clock(bpm=120.0)
        t_now = clock.bpm_start_time
        # At beat 0, getting time at beat 4 should be 2 seconds later (120 bpm)
        t = clock.get_time_at_beat(4)
        self.assertAlmostEqual(t - t_now, 2.0, places=1)

    def test_current_beat(self):
        clock = _make_clock(bpm=120.0)
        t_now = clock.bpm_start_time
        t = clock.get_time_at_beat(0)
        self.assertAlmostEqual(t, t_now, places=1)


class TestTempoClockGetElapsed(unittest.TestCase):
    def test_elapsed_seconds(self):
        clock = _make_clock()
        clock.bpm_start_time = time.time() - 2.0
        elapsed = clock.get_elapsed_seconds_from_last_bpm_change()
        self.assertAlmostEqual(elapsed, 2.0, places=1)

    def test_elapsed_beats(self):
        clock = _make_clock(bpm=120.0)
        clock.bpm_start_time = time.time() - 1.0
        beats = clock.get_elapsed_beats_from_last_bpm_change()
        # 120 bpm = 2 beats/sec, 1 second = ~2 beats
        self.assertAlmostEqual(beats, 2.0, places=0)


class TestTempoClockOscMessageTime(unittest.TestCase):
    def test_osc_time_is_future(self):
        clock = _make_clock()
        now = time.time()
        osc_time = clock.osc_message_time()
        self.assertGreater(osc_time, now)
        self.assertAlmostEqual(osc_time - now, clock.latency, places=1)


class TestTempoClockFlagWaitForSync(unittest.TestCase):
    def test_flag_true(self):
        clock = _make_clock()
        clock.flag_wait_for_sync(True)
        self.assertTrue(clock.waiting_for_sync)

    def test_flag_false(self):
        clock = _make_clock()
        clock.flag_wait_for_sync(False)
        self.assertFalse(clock.waiting_for_sync)

    def test_flag_truthy(self):
        clock = _make_clock()
        clock.flag_wait_for_sync(1)
        self.assertTrue(clock.waiting_for_sync)


class TestTempoClockScheduleError(unittest.TestCase):
    def test_schedule_uncallable_raises(self):
        clock = _make_clock()
        clock.ticking = True
        with self.assertRaises(ScheduleError):
            clock.schedule(42)


class TestTempoClockReset(unittest.TestCase):
    def test_reset_resets_beat(self):
        clock = _make_clock()
        clock.beat = 100.0
        clock.reset()
        self.assertEqual(clock.beat, 0.0)


class TestTempoClockKillTempoServer(unittest.TestCase):
    def test_kill_when_none(self):
        clock = _make_clock()
        clock.tempo_server = None
        # Should not raise
        clock.kill_tempo_server()

    def test_kill_when_exists(self):
        clock = _make_clock()
        server = MagicMock()
        clock.tempo_server = server
        clock.kill_tempo_server()
        server.kill.assert_called_once()


class TestTempoClockKillTempoClient(unittest.TestCase):
    def test_kill_when_none(self):
        clock = _make_clock()
        clock.tempo_client = None
        clock.kill_tempo_client()

    def test_kill_when_exists(self):
        clock = _make_clock()
        client = MagicMock()
        clock.tempo_client = client
        clock.kill_tempo_client()
        client.kill.assert_called_once()


# ============================================================================
# Queue.add integration tests (with real QueueBlock creation)
# ============================================================================

class TestQueueAddIntegration(unittest.TestCase):
    """Test Queue.add which creates real QueueBlock instances."""

    def _make_queue_with_server(self):
        parent = MagicMock()
        parent.server = MagicMock()
        q = Queue(parent)
        return q

    def test_add_to_empty_queue(self):
        q = self._make_queue_with_server()
        fn = lambda: 42
        q.add(fn, beat=4.0)
        self.assertEqual(len(q.data), 1)
        self.assertEqual(q.data[0].beat, 4.0)

    def test_add_same_beat_groups_together(self):
        q = self._make_queue_with_server()
        fn1 = lambda: 1
        fn2 = lambda: 2
        q.add(fn1, beat=4.0)
        q.add(fn2, beat=4.0)
        self.assertEqual(len(q.data), 1)
        self.assertEqual(len(q.data[0]), 2)

    def test_add_earlier_beat_appends(self):
        q = self._make_queue_with_server()
        fn1 = lambda: 1
        fn2 = lambda: 2
        q.add(fn1, beat=8.0)
        q.add(fn2, beat=4.0)
        self.assertEqual(len(q.data), 2)


# ============================================================================
# Wrapper Tests
# ============================================================================

class TestWrapper(unittest.TestCase):
    def test_str(self):
        metro = MagicMock()

        class MyObj:
            def __call__(self):
                pass

        w = Wrapper(metro, MyObj(), dur=1)
        self.assertIn("MyObj", str(w))

    def test_repr(self):
        metro = MagicMock()

        class MyObj:
            def __call__(self):
                pass

        w = Wrapper(metro, MyObj(), dur=1)
        self.assertEqual(repr(w), str(w))


if __name__ == "__main__":
    unittest.main()
