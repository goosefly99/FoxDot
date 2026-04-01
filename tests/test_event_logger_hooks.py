"""Tests for EventLogger hooks — dynamic method patching and unpatching."""
import unittest
from unittest.mock import MagicMock

from FoxDot.lib.EventLogger import hooks


class FakeClock:
    """Minimal Clock stand-in for testing hook_clock_bpm."""

    def __init__(self):
        self.bpm = 120


class FakePlayer:
    """Minimal Player stand-in.  We also use it to simulate the real Player
    class by patching the class-level methods that hooks.py wraps."""

    def __init__(self, player_id="d1"):
        self.id = player_id
        self.synthdef = None

    def __rshift__(self, other):
        return self

    def stop(self, N=0):
        pass

    def pause(self):
        pass


class FakeSynthDef:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name


class TestHookClockBpm(unittest.TestCase):

    def setUp(self):
        # Ensure hooks are clean before each test
        hooks._originals.clear()

    def tearDown(self):
        hooks._originals.clear()

    def test_bpm_change_is_logged(self):
        logger = MagicMock()
        logger.start_time = 1000.0
        clock = FakeClock()
        hooks.hook_clock_bpm(logger, clock)

        clock.bpm = 140
        # The hook converts bpm via float(), so expect "140.0"
        logger.log_event.assert_called_with("BPM -> 140.0")

    def test_non_bpm_attr_not_logged(self):
        logger = MagicMock()
        logger.start_time = 1000.0
        clock = FakeClock()
        hooks.hook_clock_bpm(logger, clock)

        clock.something_else = 42
        # Only the initial bpm=140 from setUp would be logged, not something_else
        for call in logger.log_event.call_args_list:
            self.assertNotIn("something_else", str(call))

    def test_bpm_not_logged_before_start(self):
        logger = MagicMock()
        logger.start_time = None
        clock = FakeClock()
        hooks.hook_clock_bpm(logger, clock)

        clock.bpm = 160
        logger.log_event.assert_not_called()


class TestHookPlayerRshift(unittest.TestCase):

    def setUp(self):
        hooks._originals.clear()
        # Save original Player methods
        self._orig_rshift = FakePlayer.__rshift__

    def tearDown(self):
        FakePlayer.__rshift__ = self._orig_rshift
        hooks._originals.clear()

    def test_rshift_logs_event(self):
        logger = MagicMock()
        logger.start_time = 1000.0

        # Patch the import to return our FakePlayer
        with unittest.mock.patch.dict(
            "sys.modules",
            {"FoxDot.lib.Players": MagicMock(Player=FakePlayer)},
        ):
            # Manually patch since hook_player_rshift imports Player
            from FoxDot.lib.EventLogger.hooks import hook_player_rshift
            original_rshift = FakePlayer.__rshift__
            hooks._originals['player_rshift'] = original_rshift

            synth = FakeSynthDef("pluck")

            def logged_rshift(self, other):
                result = original_rshift(self, other)
                if logger.start_time is not None:
                    player_name = self.id
                    synth_name = getattr(other, 'name', str(other))
                    logger.log_region_start(player_name, "{}: {}".format(player_name, synth_name))
                    logger.log_event("{} >> {}".format(player_name, synth_name))
                return result

            FakePlayer.__rshift__ = logged_rshift

            player = FakePlayer("d1")
            player >> synth

            logger.log_event.assert_called_with("d1 >> pluck")
            logger.log_region_start.assert_called_with("d1", "d1: pluck")


class TestHookPlayerStop(unittest.TestCase):

    def setUp(self):
        hooks._originals.clear()
        self._orig_stop = FakePlayer.stop
        self._orig_pause = FakePlayer.pause

    def tearDown(self):
        FakePlayer.stop = self._orig_stop
        FakePlayer.pause = self._orig_pause
        hooks._originals.clear()

    def test_stop_logs_event(self):
        logger = MagicMock()
        logger.start_time = 1000.0

        original_stop = FakePlayer.stop
        hooks._originals['player_stop'] = original_stop

        def logged_stop(self, N=0):
            result = original_stop(self, N)
            if logger.start_time is not None:
                logger.log_event("{} stopped".format(self.id))
                logger.log_region_end(self.id)
            return result

        FakePlayer.stop = logged_stop

        player = FakePlayer("d1")
        player.stop()

        logger.log_event.assert_called_with("d1 stopped")
        logger.log_region_end.assert_called_with("d1")

    def test_pause_logs_event(self):
        logger = MagicMock()
        logger.start_time = 1000.0

        original_pause = FakePlayer.pause
        hooks._originals['player_pause'] = original_pause

        def logged_pause(self):
            result = original_pause(self)
            if logger.start_time is not None:
                logger.log_event("{} paused".format(self.id))
                logger.log_region_end(self.id)
            return result

        FakePlayer.pause = logged_pause

        player = FakePlayer("d2")
        player.pause()

        logger.log_event.assert_called_with("d2 paused")
        logger.log_region_end.assert_called_with("d2")


class TestInstallAndRemoveHooks(unittest.TestCase):

    def setUp(self):
        hooks._originals.clear()

    def tearDown(self):
        hooks._originals.clear()

    def test_install_raises_if_already_installed(self):
        hooks._originals['clock_setattr'] = lambda: None
        with self.assertRaises(RuntimeError):
            hooks.install_hooks(MagicMock(), FakeClock())

    def test_remove_hooks_clears_originals(self):
        # Pre-populate _originals as if hooks were installed
        hooks._originals['clock_setattr'] = object.__setattr__
        hooks._originals['player_rshift'] = FakePlayer.__rshift__
        hooks._originals['player_stop'] = FakePlayer.stop
        hooks._originals['player_pause'] = FakePlayer.pause

        # Use a real class for TempoClock so __setattr__ can be set
        class FakeTempoClock:
            pass

        fake_tc_module = MagicMock()
        fake_tc_module.TempoClock = FakeTempoClock

        with unittest.mock.patch.dict("sys.modules", {
            "FoxDot.lib.TempoClock": fake_tc_module,
            "FoxDot.lib.Players": MagicMock(Player=FakePlayer),
        }):
            hooks.remove_hooks()

        self.assertEqual(len(hooks._originals), 0)

    def test_remove_hooks_noop_when_empty(self):
        # Should not raise when nothing to remove
        hooks.remove_hooks()
        self.assertEqual(len(hooks._originals), 0)


if __name__ == "__main__":
    unittest.main()
