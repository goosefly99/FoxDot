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

args = parser.parse_args()

if args.dir:

    try:

        # Use given directory

        FoxDotCode.use_sample_directory(args.dir)

    except OSError as e:

        # Exit with last error

        import sys, traceback
        sys.exit(traceback.print_exc(limit=1))

if args.startup:

    try:

        FoxDotCode.use_startup_file(args.startup)

    except OSError as e:

        import sys, traceback
        sys.exit(traceback.print_exc(limit=1))

if args.no_startup:

    FoxDotCode.no_startup()

if args.boot:

    FoxDotCode.boot_supercollider()

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
