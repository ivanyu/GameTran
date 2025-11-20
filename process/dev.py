from .types import Process


def get_active_process() -> Process:
    return Process(pid=0, window_handle=0)


def focus_window(window_handle: int) -> None:
    pass
