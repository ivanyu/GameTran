from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class Process:
    pid: int
    window_handle: int
    """HWND on Windows, window ID on Linux"""
