"""
Hook functions that patch into FoxDot's existing classes to emit events
to an EventLogger instance.

Uses a wrapper approach that preserves the original methods so hooks
can be cleanly removed.
"""

import threading

_originals = {}
_lock = threading.Lock()


def hook_clock_bpm(logger, clock):
    """Wrap Clock.__setattr__ to log tempo changes when bpm is set."""
    cls = type(clock)
    original = cls.__setattr__
    _originals['clock_setattr'] = original

    def logged_setattr(self, attr, value):
        original(self, attr, value)
        if attr == "bpm" and logger.start_time is not None:
            # value may be a TimeVar; get the current numeric bpm
            try:
                bpm_val = float(self.bpm) if hasattr(self.bpm, '__float__') else self.bpm
            except (TypeError, ValueError):
                bpm_val = value
            logger.log_event("BPM -> {}".format(bpm_val))

    cls.__setattr__ = logged_setattr


def hook_player_rshift(logger):
    """Wrap Player.__rshift__ to log new player assignments."""
    from ..Players import Player
    original = Player.__rshift__
    _originals['player_rshift'] = original

    def logged_rshift(self, other):
        result = original(self, other)
        if logger.start_time is not None:
            player_name = self.id
            synth_name = getattr(other, 'name', str(other))
            logger.log_region_start(player_name, "{}: {}".format(player_name, synth_name))
            logger.log_event("{} >> {}".format(player_name, synth_name))
        return result

    Player.__rshift__ = logged_rshift


def hook_player_stop(logger):
    """Wrap Player.stop() and Player.pause() to log player stops."""
    from ..Players import Player
    original_stop = Player.stop
    original_pause = Player.pause
    _originals['player_stop'] = original_stop
    _originals['player_pause'] = original_pause

    def logged_stop(self, N=0):
        result = original_stop(self, N)
        if logger.start_time is not None:
            logger.log_event("{} stopped".format(self.id))
            logger.log_region_end(self.id)
        return result

    def logged_pause(self):
        result = original_pause(self)
        if logger.start_time is not None:
            logger.log_event("{} paused".format(self.id))
            logger.log_region_end(self.id)
        return result

    Player.stop = logged_stop
    Player.pause = logged_pause


def install_hooks(logger, clock):
    """Install all hooks. Call once at startup.

    Raises RuntimeError if hooks are already installed.  Call
    remove_hooks() first to reinstall.

    The lock is held for the entire operation so that class
    modifications and ``_originals`` bookkeeping stay in sync.
    """
    with _lock:
        if _originals:
            raise RuntimeError(
                "EventLogger hooks are already installed. "
                "Call remove_hooks() before reinstalling."
            )
        # All hook functions mutate _originals and patch classes.
        # Keep them inside the lock to prevent races with remove_hooks().
        hook_clock_bpm(logger, clock)
        hook_player_rshift(logger)
        hook_player_stop(logger)


def remove_hooks():
    """Remove all hooks. Restore original methods."""
    with _lock:
        if 'clock_setattr' in _originals:
            from ..TempoClock import TempoClock
            TempoClock.__setattr__ = _originals.pop('clock_setattr')

        if 'player_rshift' in _originals:
            from ..Players import Player
            Player.__rshift__ = _originals.pop('player_rshift')

        if 'player_stop' in _originals:
            from ..Players import Player
            Player.stop = _originals.pop('player_stop')

        if 'player_pause' in _originals:
            from ..Players import Player
            Player.pause = _originals.pop('player_pause')
