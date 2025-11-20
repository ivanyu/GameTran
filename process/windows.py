from .types import Process
import ctypes
from ctypes import wintypes


def get_active_process() -> Process:
    try:
        user32 = ctypes.windll.user32

        # Get the foreground window handle
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            raise Exception("Error getting active window PID")

        # Get the process ID
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return Process(pid=int(pid.value), window_handle=hwnd)
    except Exception as e:
        raise Exception("Error getting active window PID") from e


def focus_window(window_handle: int) -> None:
    try:
        user32 = ctypes.windll.user32
        user32.SetForegroundWindow(window_handle)
    except Exception as e:
        print(f"Warning: Failed to focus window: {e}")
