#!/usr/bin/env python3
"""
Post-session processing: import labels, apply mastering, export.

Usage:
    python scripts/post_session.py <recording.wav> [--labels <labels.txt>] [--output <output.wav>]
    python scripts/post_session.py --help

If --labels is not specified, the script looks in the default session
directory (~/foxdot-sessions/) for a label file matching the recording's
base name.  This is the same directory that EventLogger writes to.

Workflow:
    1. Connect to Audacity via mod-script-pipe (or PyAudacity)
    2. Open the recording in Audacity
    3. Import the label track (if provided or auto-discovered)
    4. Apply the FoxDot-Master mastering macro (unless --no-master)
    5. Export the mastered result
"""

import argparse
import glob
import os
import sys

# Ensure the FoxDot package is importable when running from the scripts/ dir
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


def _find_labels(recording_path, session_dir=None):
    """Try to auto-discover a label file matching the recording name.

    Looks for ``foxdot_labels_*<stem>*.txt`` in *session_dir*.
    Returns the path if found, otherwise None.
    """
    if session_dir is None:
        session_dir = os.path.expanduser("~/foxdot-sessions/")

    if not os.path.isdir(session_dir):
        return None

    stem = os.path.splitext(os.path.basename(recording_path))[0]

    # Exact name match first
    candidates = glob.glob(os.path.join(session_dir, "foxdot_labels_*.txt"))
    for c in sorted(candidates, key=os.path.getmtime, reverse=True):
        if stem in os.path.basename(c):
            return c

    # If no match on name, return the most recent label file
    if candidates:
        return max(candidates, key=os.path.getmtime)

    return None


def main():
    parser = argparse.ArgumentParser(
        description="FoxDot post-session processor — import labels, master, export"
    )
    parser.add_argument(
        "recording",
        help="Path to the recorded WAV file",
    )
    parser.add_argument(
        "--labels",
        help="Path to the Audacity label file (.txt). "
        "If omitted, looks in ~/foxdot-sessions/ for a matching file.",
    )
    parser.add_argument(
        "--output",
        help="Output path for mastered file (default: <recording>_mastered.<ext>)",
    )
    parser.add_argument(
        "--format",
        choices=["WAV", "MP3", "OGG", "FLAC"],
        default="WAV",
        help="Export format (default: WAV)",
    )
    parser.add_argument(
        "--no-master",
        action="store_true",
        help="Skip the mastering macro",
    )
    parser.add_argument(
        "--session-dir",
        default=None,
        help="Override the session directory for label auto-discovery",
    )
    args = parser.parse_args()

    recording = os.path.abspath(args.recording)
    if not os.path.isfile(recording):
        print("Error: recording file not found: {}".format(recording), file=sys.stderr)
        sys.exit(1)

    # Determine output path
    if args.output:
        output = os.path.abspath(args.output)
    else:
        base, ext = os.path.splitext(recording)
        fmt_ext = {"WAV": ".wav", "MP3": ".mp3", "OGG": ".ogg", "FLAC": ".flac"}
        output = base + "_mastered" + fmt_ext.get(args.format, ext)

    # Resolve labels
    labels = None
    if args.labels:
        labels = os.path.abspath(args.labels)
        if not os.path.isfile(labels):
            print("Error: label file not found: {}".format(labels), file=sys.stderr)
            sys.exit(1)
    else:
        labels = _find_labels(recording, session_dir=args.session_dir)
        if labels:
            print("Auto-discovered labels: {}".format(labels))
        else:
            print("No label file found — proceeding without labels.")

    # --- Connect to Audacity ---
    print("Connecting to Audacity...")
    try:
        from FoxDot.lib.AudacityBridge import AudacityBridge
        bridge = AudacityBridge()
    except ConnectionError as e:
        print("Error: {}".format(e), file=sys.stderr)
        sys.exit(1)

    # --- Open recording ---
    print("Opening recording: {}".format(recording))
    bridge.open_file(recording)

    # --- Import labels ---
    if labels:
        print("Importing labels: {}".format(labels))
        bridge.import_labels(labels)

    # --- Apply mastering ---
    if not args.no_master:
        from FoxDot.lib.AudacityBridge.macros import is_macro_installed
        if not is_macro_installed():
            print("Warning: FoxDot-Master macro not found in Audacity.")
            print("  Run: python scripts/install_mastering_macro.py")
            print("  Skipping mastering step.")
        else:
            print("Applying FoxDot-Master mastering macro...")
            bridge.apply_foxdot_master()
    else:
        print("Skipping mastering (--no-master).")

    # --- Export ---
    print("Exporting to: {} [{}]".format(output, args.format))
    bridge.export_audio(output, format=args.format)

    print()
    print("Post-session processing complete.")
    print("  Input:  {}".format(recording))
    if labels:
        print("  Labels: {}".format(labels))
    print("  Output: {}".format(output))


if __name__ == "__main__":
    main()
