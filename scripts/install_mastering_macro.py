#!/usr/bin/env python3
"""
Install the FoxDot-Master mastering macro into Audacity.

Usage:
    python scripts/install_mastering_macro.py [--dry-run]

The macro applies the following processing chain:
    1. Normalize to -1dB peak
    2. Compressor (threshold -18dB, ratio 4:1)
    3. Hard Limiter (ceiling -3dB)
    4. Filter Curve EQ (roll off sub-30Hz, gentle HF rolloff above 16kHz)

The macro file is written to Audacity's platform-specific Macros directory.
"""

import argparse
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
        # Linux — check XDG first, fall back to legacy paths
        config_home = os.environ.get(
            "XDG_CONFIG_HOME", os.path.expanduser("~/.config")
        )
        xdg_path = os.path.join(config_home, "audacity", "Macros")
        legacy_path = os.path.expanduser("~/.audacity-data/Macros")
        if os.path.isdir(legacy_path):
            return legacy_path
        return xdg_path


def install_macro(dry_run=False):
    """Install the FoxDot-Master macro into Audacity's Macros directory."""
    macro_dir = get_macro_dir()
    macro_path = os.path.join(macro_dir, MACRO_NAME + ".txt")

    print(f"Macro directory: {macro_dir}")
    print(f"Macro file:      {macro_path}")
    print()

    if dry_run:
        print("[dry-run] Would write the following macro:")
        print(MACRO_CONTENTS)
        return

    os.makedirs(macro_dir, exist_ok=True)

    if os.path.exists(macro_path):
        print(f"Overwriting existing macro at {macro_path}")
    else:
        print(f"Creating new macro at {macro_path}")

    with open(macro_path, "w", encoding="utf-8") as f:
        f.write(MACRO_CONTENTS)

    print()
    print("Macro installed successfully.")
    print("To use it in Audacity: Tools > Macros > FoxDot-Master")
    print()
    print("Processing chain:")
    print("  1. Normalize to -1dB peak")
    print("  2. Compressor (threshold -18dB, ratio 4:1)")
    print("  3. Hard Limiter (ceiling -3dB)")
    print("  4. Filter Curve EQ (sub-30Hz rolloff, gentle HF rolloff)")


def main():
    parser = argparse.ArgumentParser(
        description="Install the FoxDot-Master mastering macro into Audacity"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without writing any files",
    )
    args = parser.parse_args()

    try:
        install_macro(dry_run=args.dry_run)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
