"""
Macro management helpers for the FoxDot-Master Audacity macro.

Provides utilities for checking whether the mastering macro is installed
and installing it programmatically.
"""

import os
import sys

MACRO_NAME = "FoxDot-Master"

MACRO_CONTENTS = """\
Normalize:PeakLevel=-1.0
Compressor:Threshold=-18.0 NoiseFloor=-40.0 Ratio=4.0 AttackTime=0.2 ReleaseTime=1.0
Limiter:type="HardLimit" gainL=0.0 gainR=0.0 thresh=-3.0 hold=10
FilterCurve:f0=30 v0=-24 f1=80 v1=0 f2=16000 v2=0 f3=20000 v3=-6
"""


def get_macro_dir():
    """Return the platform-specific Audacity Macros directory."""
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA", "")
        if not appdata:
            raise RuntimeError("APPDATA environment variable not set")
        return os.path.join(appdata, "audacity", "Macros")
    elif sys.platform == "darwin":
        return os.path.expanduser(
            "~/Library/Application Support/audacity/Macros"
        )
    else:
        config_home = os.environ.get(
            "XDG_CONFIG_HOME", os.path.expanduser("~/.config")
        )
        xdg_path = os.path.join(config_home, "audacity", "Macros")
        legacy_path = os.path.expanduser("~/.audacity-data/Macros")
        if os.path.isdir(legacy_path):
            return legacy_path
        return xdg_path


def is_macro_installed(macro_name=MACRO_NAME):
    """Check whether a named macro exists in Audacity's Macros directory."""
    try:
        macro_dir = get_macro_dir()
    except RuntimeError:
        return False
    return os.path.isfile(os.path.join(macro_dir, macro_name + ".txt"))


def install_macro(macro_name=MACRO_NAME, contents=MACRO_CONTENTS):
    """Install a macro into Audacity's Macros directory.

    Returns the path to the installed macro file.
    """
    macro_dir = get_macro_dir()
    os.makedirs(macro_dir, exist_ok=True)
    macro_path = os.path.join(macro_dir, macro_name + ".txt")
    with open(macro_path, "w", encoding="utf-8") as f:
        f.write(contents)
    return macro_path
