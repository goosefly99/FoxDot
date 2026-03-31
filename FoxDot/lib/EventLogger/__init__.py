"""
EventLogger — captures timestamped FoxDot performance events and writes
them as Audacity-compatible label track files.

Usage:
    from FoxDot.lib.EventLogger import start_logging, stop_logging, mark

    start_logging()          # begin capturing events
    mark("intro")            # manual marker
    filepath = stop_logging() # end session, write labels file
"""

from .logger import EventLogger
from .hooks import install_hooks, remove_hooks

_global_logger = None


def start_logging(output_dir=".", session_name=None, clock=None):
    """Start a new logging session.

    Args:
        output_dir: Directory where label files will be written.
        session_name: Optional session name; defaults to timestamp.
        clock: TempoClock instance. If None, imports the global Clock.
    """
    global _global_logger

    if clock is None:
        from .. import TempoClock as _tc_module
        # The global Clock is created in lib/__init__.py; we need
        # to defer hook installation until Clock exists.  When called
        # from lib/__init__.py the clock kwarg should be passed explicitly.
        clock = None  # hooks installed later via install_hooks_deferred

    _global_logger = EventLogger(output_dir=output_dir, session_name=session_name)
    _global_logger.start()

    if clock is not None:
        install_hooks(_global_logger, clock)

    return _global_logger


def install_hooks_deferred(clock):
    """Install hooks after Clock is available. Called from lib/__init__.py."""
    if _global_logger is not None:
        install_hooks(_global_logger, clock)


def stop_logging():
    """Stop the current logging session, write labels, and return filepath."""
    global _global_logger
    if _global_logger is None:
        return None
    filepath = _global_logger.stop()
    remove_hooks()
    _global_logger = None
    return filepath


def mark(label="marker"):
    """Add a manual marker at the current time. Use during performance.

    Example::

        mark("drop")
        mark("breakdown")
    """
    if _global_logger is not None and _global_logger.start_time is not None:
        _global_logger.log_event("[MARK] {}".format(label))
