import os
import sys

import psutil

from .types import Process

__all__ = [
    "Process",
    "get_active_process",
    "focus_window",
    "suspend_process",
    "resume_process",
]

if os.environ.get("GT_DEV") == "true":
    from .dev import get_active_process, focus_window
elif sys.platform == "win32":
    from .windows import get_active_process, focus_window
elif sys.platform == "linux":
    from .linux import get_active_process, focus_window
else:
    raise Exception("Unsupported platform")


def suspend_process(pid: int) -> None:
    if os.environ.get("GT_DEV") == "true":
        return
    psutil.Process(pid).suspend()


def resume_process(pid: int) -> None:
    if os.environ.get("GT_DEV") == "true":
        return
    psutil.Process(pid).resume()
