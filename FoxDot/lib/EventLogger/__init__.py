"""
EventLogger — captures timestamped FoxDot performance events and writes
them as Audacity-compatible label track files.

Usage:
    from FoxDot.lib.EventLogger import start_logging, stop_logging, mark

    start_logging()          # begin capturing events
    mark("intro")            # manual marker
    filepath = stop_logging() # end session, write labels file
"""

import threading

from .logger import EventLogger
from .hooks import install_hooks, remove_hooks

_global_logger = None
_lock = threading.Lock()


def start_logging(output_dir=".", session_name=None, clock=None):
    """Start a new logging session.

    Args:
        output_dir: Directory where label files will be written.
        session_name: Optional session name; defaults to timestamp.
        clock: TempoClock instance. If None, hooks must be installed
               later via install_hooks_deferred().
    """
    global _global_logger

    with _lock:
        _global_logger = EventLogger(output_dir=output_dir, session_name=session_name)
        _global_logger.start()

        if clock is not None:
            install_hooks(_global_logger, clock)

    return _global_logger


def install_hooks_deferred(clock):
    """Install hooks after Clock is available. Called from lib/__init__.py."""
    with _lock:
        if _global_logger is not None:
            install_hooks(_global_logger, clock)


def stop_logging():
    """Stop the current logging session, write labels, and return filepath."""
    global _global_logger
    with _lock:
        if _global_logger is None:
            return None
        try:
            filepath = _global_logger.stop()
        finally:
            remove_hooks()
            _global_logger = None
    return filepath


def mark(label="marker"):
    """Add a manual marker at the current time. Use during performance.

    Example::

        mark("drop")
        mark("breakdown")
    """
    # Read the reference once to avoid TOCTOU race with stop_logging().
    logger = _global_logger
    if logger is not None and logger.start_time is not None:
        logger.log_event("[MARK] {}".format(label))
