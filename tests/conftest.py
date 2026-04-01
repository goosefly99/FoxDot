import shutil

import pytest


def sc_is_running():
    """Check if SuperCollider (sclang or scsynth) is available on the system."""
    return shutil.which("sclang") is not None or shutil.which("scsynth") is not None


def pytest_collection_modifyitems(items):
    """Skip tests in 'integration' directories when SuperCollider is not available."""
    for item in items:
        if "integration" in item.nodeid:
            item.add_marker(
                pytest.mark.skipif(
                    not sc_is_running(),
                    reason="SuperCollider not running",
                )
            )
