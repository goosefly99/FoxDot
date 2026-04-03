#!/usr/bin/python

"""

FoxDot is a Python library and programming environment that provides a fast and
user-friendly abstraction to the powerful audio-engine, SuperCollider. It comes
with its own IDE, which means it can be used straight out of the box; all you need
is Python and SuperCollider and you're ready to go!

For more information on installation, check out [the guide](http://foxdot.org/installation),
or if you're already set up, you can also find a useful starter guide that introduces the
key components of FoxDot on [the website](http://foxdot.org/).

Please see the [documentation](http://docs.foxdot.org/) for more detailed information on
the FoxDot classes and how to implement them.

Copyright Ryan Kirkbride 2015
"""

import os as _os

with open(_os.path.join(_os.path.dirname(__file__), "lib", ".version")) as _f:
    __version__ = _f.read().strip()

def boot_supercollider():
    """ Uses subprocesses to boot supercollider from the cli """

    import platform
    import os
    import subprocess

    try:
        import psutil
    except ImportError:
        raise ImportError("psutil is required. Install it with: pip install psutil>=7.0")

    thisdir = os.getcwd()

    OS = platform.system()

    if(OS == "Windows"):

        sclangloc = subprocess.run(
            ['where', '/R', 'C:\\Program Files', 'sclang.exe'],
            capture_output=True, text=True, check=False
        ).stdout.strip()

        ourcwd = os.path.dirname(sclangloc)

        def is_proc_running(name):
            for p in psutil.process_iter(attrs=["name", "exe", "cmdline"]):
                info = p.info
                proc_name = info.get('name') or ''
                exe_name = os.path.basename(info.get('exe') or '')
                cmd_parts = info.get('cmdline') or []
                cmd_name = cmd_parts[0] if cmd_parts else ''
                if any(n.startswith(name) for n in (proc_name, exe_name, cmd_name) if n):
                    return True
            return False


        running = is_proc_running("sclang")

        if not running:
            startup = thisdir+"/FoxDot/startup.scd"
            subprocess.Popen([sclangloc, startup], cwd=ourcwd)

    elif(OS == "Linux"):

        def is_proc_running(name):
            for p in psutil.process_iter(attrs=["name", "cmdline"]):
                info = p.info
                proc_name = info.get('name') or ''
                cmd_parts = info.get('cmdline') or []
                cmd_name = cmd_parts[0] if cmd_parts else ''
                if any(n.startswith(name) for n in (proc_name, cmd_name) if n):
                    return True
            return False

        running = is_proc_running("sclang")

        if not running:
            startup = thisdir+"/FoxDot/startup.scd"
            subprocess.Popen(["sclang", startup])


    else:
        print("Operating system unrecognised")
        #Potentially get the user to choose their OS from a list?
        #Then run the corresponding functions

import sys

if "--boot" in sys.argv:

    boot_supercollider()

    sys.argv.remove("--boot")

from .lib import *

def main():
    """ Function for starting the GUI when importing the library """
    from .lib.Workspace.Editor import workspace
    FoxDot = workspace(FoxDotCode).run()

def Go():
    """ Function to be called at the end of Python files with FoxDot code in to keep
        the TempoClock thread alive. """
    try:
        import time
        while 1:
            time.sleep(100)
    except KeyboardInterrupt:
        return
