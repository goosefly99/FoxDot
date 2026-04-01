"""
AudacityBridge — control Audacity from FoxDot via mod-script-pipe.

Usage:
    from FoxDot.lib.AudacityBridge import AudacityBridge, connect, is_connected

    bridge = connect()         # connect to running Audacity
    bridge.open_file("rec.wav")
    bridge.import_labels("labels.txt")
    bridge.apply_foxdot_master()
    bridge.export_audio("mastered.wav")
"""

import threading

from .bridge import AudacityBridge
from .macros import is_macro_installed, install_macro

_global_bridge = None
_lock = threading.Lock()


def connect():
    """Connect to a running Audacity instance and return the bridge.

    Closes any existing connection before creating a new one.
    Raises ConnectionError if Audacity is not reachable.
    """
    global _global_bridge
    with _lock:
        if _global_bridge is not None:
            try:
                _global_bridge.close()
            except Exception:
                pass
        _global_bridge = AudacityBridge()
        return _global_bridge


def is_connected():
    """Return True if we have an active Audacity connection."""
    with _lock:
        return _global_bridge is not None and _global_bridge.is_connected()


def get_bridge():
    """Return the current bridge instance, or None."""
    with _lock:
        return _global_bridge
