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

# Ensure the FoxDot package is importable when running from the scripts/ dir
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from FoxDot.lib.AudacityBridge.macros import (
    MACRO_NAME, MACRO_CONTENTS, get_macro_dir,
)


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
