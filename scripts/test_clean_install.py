#!/usr/bin/env python3
"""
Test clean installation of the FoxDot fork.

Creates a temporary venv, installs the package, and runs verification checks.
"""

import subprocess
import sys
import tempfile
import os


def test_clean_install():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    with tempfile.TemporaryDirectory() as tmpdir:
        venv_dir = os.path.join(tmpdir, "venv")

        print(f"Creating venv in {venv_dir} ...")
        subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True, timeout=60)

        if sys.platform == "win32":
            pip = os.path.join(venv_dir, "Scripts", "pip")
            python = os.path.join(venv_dir, "Scripts", "python")
        else:
            pip = os.path.join(venv_dir, "bin", "pip")
            python = os.path.join(venv_dir, "bin", "python")

        print("Installing FoxDot from source ...")
        subprocess.run([pip, "install", project_root], check=True, timeout=120)

        checks = [
            "from FoxDot.lib.Patterns import Pattern; print('Patterns OK')",
            "from FoxDot.lib.Scale import Scale; print('Scale OK')",
            "from FoxDot.lib.Settings import SYSTEM; print(f'Platform: {SYSTEM}')",
            "import FoxDot; print(f'Version: {FoxDot.__version__}')",
        ]

        for check in checks:
            result = subprocess.run(
                [python, "-c", check],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                print(f"FAIL: {check}")
                print(result.stderr)
                sys.exit(1)
            print(f"  {result.stdout.strip()}")

        print("\nClean install verification PASSED")


if __name__ == "__main__":
    test_clean_install()
