"""System environment helpers."""

from __future__ import annotations

import ctypes
import sys


def is_windows_admin() -> bool:
    """Return whether the current process is running as Windows administrator."""
    if sys.platform != "win32":
        return False

    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False
