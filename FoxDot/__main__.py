"""
    FoxDot __main__.py
    ------------------

    Use FoxDot's interface by running this as a Python script, e.g.
    python __main__.py or python -m FoxDot if you have FoxDot correctly
    installed and Python on your path.

"""


from __future__ import absolute_import, division, print_function

from .lib import FoxDotCode, handle_stdin
from .lib.Settings import REPL_WEBSOCKET_PORT
from . import boot_supercollider as _boot_supercollider

import argparse

parser = argparse.ArgumentParser(
    prog="FoxDot", 
    description="Live coding with Python and SuperCollider", 
    epilog="More information: https://foxdot.org/")

parser.add_argument('-p', '--pipe', action='store_true', help="run FoxDot from the command line interface")
parser.add_argument('-d', '--dir', action='store', help="use an alternate directory for looking up samples")
parser.add_argument('-s', '--startup', action='store', help="use an alternate startup file")
parser.add_argument('-S', '--simple', action='store_true', help="run FoxDot in simple (accessible) mode")
parser.add_argument('-n', '--no-startup', action='store_true', help="does not load startup.py on boot")
parser.add_argument('-b', '--boot', action='store_true', help="Boot SuperCollider from the command line")
parser.add_argument('--repl', action='store_true', help='Start WebSocket REPL server (requires websockets package)')
parser.add_argument('--repl-port', type=int, default=REPL_WEBSOCKET_PORT, help='REPL WebSocket port (default: 5555)')
parser.add_argument('--post-process', metavar='RECORDING',
                    help='Run post-session processing on a recording (requires Audacity)')
parser.add_argument('--labels', help='Label file for post-processing (auto-discovered if omitted)')
parser.add_argument('--output', help='Output path for post-processed file')
parser.add_argument('--format', choices=['WAV', 'MP3', 'OGG', 'FLAC'], default='WAV',
                    help='Export format for post-processing (default: WAV)')
parser.add_argument('--no-master', action='store_true', help='Skip mastering macro during post-processing')

args = parser.parse_args()

if args.dir:

    try:

        # Use given directory

        FoxDotCode.use_sample_directory(args.dir)

    except OSError as e:

        # Exit with last error

        import sys, traceback
        traceback.print_exc(limit=1)
        sys.exit(1)

if args.startup:

    try:

        FoxDotCode.use_startup_file(args.startup)

    except OSError as e:

        import sys, traceback
        traceback.print_exc(limit=1)
        sys.exit(1)

if args.no_startup:

    FoxDotCode.no_startup()

if args.boot:

    _boot_supercollider()

if args.post_process:

    # Run post-session processing and exit — no GUI or REPL needed.
    import sys, os, subprocess
    _scripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts')
    _post_cmd = [sys.executable, os.path.join(_scripts_dir, 'post_session.py'), args.post_process]
    if args.labels:
        _post_cmd += ['--labels', args.labels]
    if args.output:
        _post_cmd += ['--output', args.output]
    if args.format:
        _post_cmd += ['--format', args.format]
    if args.no_master:
        _post_cmd.append('--no-master')
    sys.exit(subprocess.call(_post_cmd))

if args.repl:

    # Start WebSocket REPL server in the background, then open the GUI.
    from .lib.REPL import REPLServer
    from .lib import execute as _foxdot_execute, Clock
    _repl_server = REPLServer(_foxdot_execute, Clock, transport="websocket", port=args.repl_port)
    _repl_server.start()

if args.pipe:

    # Just take commands from the CLI

    handle_stdin()

else:

    # Open the GUI

    if args.simple:

        from .lib.Workspace.Simple import workspace

    else:

        from .lib.Workspace.Editor import workspace

    FoxDot = workspace(FoxDotCode).run()
