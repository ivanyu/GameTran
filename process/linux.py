from .types import Process
from Xlib import X, display
from Xlib.error import XError


def get_active_process() -> Process:
    try:
        disp = display.Display()
        root = disp.screen().root

        active_window_response = root.get_full_property(
            disp.intern_atom("_NET_ACTIVE_WINDOW"), X.AnyPropertyType
        )

        if not active_window_response:
            raise Exception("Error getting active window PID")

        window_id = active_window_response.value[0]
        window = disp.create_resource_object("window", window_id)
        pid_response = window.get_full_property(
            disp.intern_atom("_NET_WM_PID"), X.AnyPropertyType
        )

        if not pid_response:
            raise Exception("Error getting active window PID")
        return Process(pid=int(pid_response.value[0]), window_handle=int(window_id))
    except XError as e:
        raise Exception("Error getting active window PID") from e


def focus_window(window_handle: int) -> None:
    try:
        import Xlib.protocol.event

        disp = display.Display()
        root = disp.screen().root
        window = disp.create_resource_object("window", window_handle)

        # Send _NET_ACTIVE_WINDOW client message
        event = Xlib.protocol.event.ClientMessage(
            window=window,
            client_type=disp.intern_atom("_NET_ACTIVE_WINDOW"),
            data=(32, [1, X.CurrentTime, 0, 0, 0]),
        )
        root.send_event(event, event_mask=X.SubstructureRedirectMask)
        disp.flush()
    except Exception as e:
        print(f"Warning: Failed to focus window: {e}")
