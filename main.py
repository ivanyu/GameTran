import os
import signal
import sys
import webbrowser
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Final

from dotenv import load_dotenv
from pynput import keyboard
from PyQt6.QtCore import QStandardPaths, Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMenu,
    QMessageBox,
    QSystemTrayIcon,
)

import version
from assets import load_icon
from config import Config
from overlay_window import OverlayWindow
from process import (
    focus_window,
    get_active_process,
    resume_process,
    suspend_process,
    Process,
)
from screenshot import Screenshot, take_screenshot
from settings_window import SettingsWindow


@dataclass(slots=True, kw_only=True)
class _Session:
    process: Process
    screenshot: Screenshot | None = None
    suspended: bool = False


class Application(QApplication):
    _hotkey_pressed = pyqtSignal()

    def __init__(self, argv: list[str]) -> None:
        super().__init__(argv)
        self._session: _Session | None = None

        self.setApplicationName("GameTran")
        self.setWindowIcon(load_icon("icon_big.png"))
        self.setQuitOnLastWindowClosed(False)

        self._config = Config()
        self._setup_tray_menu()

        self._overlay_window = OverlayWindow(self._config)

        # This is a Linux hack to allow the cursor properly be passed to the overlay window.
        # On Windows, we just suspend directly.
        if sys.platform == "linux":
            self._overlay_window.got_focus.connect(
                self._on_overlay_window_focus_linux_only
            )

        self._overlay_window.save_screenshot_requested.connect(self._on_save_screenshot)
        self._overlay_window.showFullScreen()
        self._overlay_window.hide()
        # Connect only after first hide.
        self._overlay_window.before_overlay_hidden.connect(
            self._on_before_overlay_hidden
        )
        self._overlay_window.session_ended.connect(self._end_session_and_resume_game)

        self._global_hotkey_listener: keyboard.Listener | None = None
        self._setup_global_hotkey()

        self.aboutToQuit.connect(self._on_exit)

        self._hotkey_pressed.connect(self._on_hotkey)

        if not self._config.has_valid_api_key:
            self._show_settings()

    def _on_overlay_window_focus_linux_only(self) -> None:
        if self._session is not None and not self._session.suspended:
            print("Suspending game (overlay window got focus)")
            self._session.suspended = True
            suspend_process(self._session.process.pid)

    def _setup_tray_menu(self) -> None:
        tray_menu = QMenu()
        tray_menu.addAction("Settings").triggered.connect(self._show_settings)
        tray_menu.addAction("Report Bug").triggered.connect(
            self._on_systray_menu_report_bug
        )
        tray_menu.addAction("About").triggered.connect(self._on_systray_menu_about)
        tray_menu.addSeparator()
        tray_menu.addAction("Exit").triggered.connect(lambda: self.exit())

        tray_icon = QSystemTrayIcon(self)
        tray_icon.setIcon(load_icon("icon_big.png"))
        tray_icon.setContextMenu(tray_menu)

        tray_icon.show()

    def _setup_global_hotkey(self) -> None:
        if self._global_hotkey_listener is not None:
            self._global_hotkey_listener.stop()

        hotkey = keyboard.HotKey(
            keyboard.HotKey.parse(self._config.global_hotkey), self._hotkey_pressed.emit
        )

        def for_canonical(f):
            return lambda k: f(self._global_hotkey_listener.canonical(k))

        listener = keyboard.Listener(
            on_press=for_canonical(hotkey.press),
            on_release=for_canonical(hotkey.release),
        )
        self._global_hotkey_listener = listener
        listener.start()

    def _on_hotkey(self):
        if not self._config.has_valid_api_key:
            message_box = QMessageBox()
            message_box.setIcon(QMessageBox.Icon.Warning)
            message_box.setWindowTitle("Google Cloud API key required")
            message_box.setText("Google Cloud API key is not configured.")
            message_box.setInformativeText(
                "Please configure your API key in the settings."
            )
            message_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            message_box.exec()
            self._show_settings()
            return

        if self._session is None:
            process = get_active_process()
            if os.getpid() == process.pid:
                print("Not self-suspending")
                return
            self._session = _Session(process=process)
            print(process)
            self._session.screenshot = take_screenshot()

            self._overlay_window.start_session(self._session.screenshot)

            # Modern Windows apply complex rules to determine if an application can bring its window forward.
            # This hack tries to male sure we can.
            # https://stackoverflow.com/a/59659421
            if sys.platform == "win32":
                import ctypes
                import threading

                user32 = ctypes.windll.user32
                hwnd = user32.GetForegroundWindow()
                window_thread_process_id = user32.GetWindowThreadProcessId(hwnd, 0)
                # Effectively GetCurrentThreadId.
                current_thread_id = threading.get_ident()
                CONST_SW_SHOW: Final = 5
                user32.AttachThreadInput(
                    window_thread_process_id, current_thread_id, True
                )
                user32.BringWindowToTop(hwnd)
                user32.ShowWindow(hwnd, CONST_SW_SHOW)
                user32.AttachThreadInput(
                    window_thread_process_id, current_thread_id, False
                )

            # On Windows, we suspend directly. On Linux, there's a hack with the got_focus signal.
            if sys.platform == "win32":
                print("Suspending game (directly)")
                self._session.suspended = True
                suspend_process(self._session.process.pid)

            self._overlay_window.showFullScreen()
            self._overlay_window.raise_()
            self._overlay_window.activateWindow()
            self._overlay_window.setFocus()
        else:
            self._overlay_window.hide()
            self._end_session_and_resume_game()

    def _show_settings(self) -> None:
        settings_window = SettingsWindow(self._config)
        if settings_window.exec():
            # Settings were saved, update hotkey if it changed.
            self._setup_global_hotkey()

    @staticmethod
    def _on_systray_menu_report_bug() -> None:
        webbrowser.open("https://github.com/ivanyu/GameTran/issues/new")

    @staticmethod
    def _on_systray_menu_about() -> None:
        about_text = f"<h2>GameTran {version.get_version_human()}</h2>"
        about_text += "<p>Your language assistant in computer games.</p>"
        details = [f"Build: {version.get_version()}"]
        about_text += "<p style='font-size: small;'>" + "<br>".join(details) + "</p>"

        message_box = QMessageBox()
        message_box.setWindowTitle("About GameTran")
        message_box.setTextFormat(Qt.TextFormat.RichText)
        message_box.setText(about_text)
        message_box.setIconPixmap(load_icon("icon_big.png").pixmap(64, 64))
        message_box.exec()

    def _on_exit(self) -> None:
        if self._global_hotkey_listener is not None:
            self._global_hotkey_listener.stop()
        self._end_session_and_resume_game()
        if self._overlay_window is not None:
            self._overlay_window.close()
            self._overlay_window = None

    def _on_before_overlay_hidden(self) -> None:
        if self._session and self._session.suspended:
            print("Focusing game window")
            focus_window(self._session.process.window_handle)

    def _end_session_and_resume_game(self) -> None:
        if self._session and self._session.suspended:
            print("Focusing game window again")
            focus_window(self._session.process.window_handle)
            print("Resuming game")
            resume_process(self._session.process.pid)
        self._session = None

    def _on_save_screenshot(self) -> None:
        if self._session and self._session.screenshot is not None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            suggested_filename = f"gametran_screenshot_{timestamp}.png"

            pictures_path = QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.DocumentsLocation
            )
            suggested_path = str(Path(pictures_path) / suggested_filename)

            file_path, _ = QFileDialog.getSaveFileName(
                self._overlay_window,
                "Save Screenshot",
                suggested_path,
                "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg);;All Files (*)",
            )

            if file_path:
                success = self._session.screenshot.pixmap.save(file_path)
                if not success:
                    message_box = QMessageBox(self._overlay_window)
                    message_box.setIcon(QMessageBox.Icon.Critical)
                    message_box.setText(f"Failed to save screenshot to {file_path}")
                    message_box.setWindowTitle("Error")
                    message_box.setWindowModality(Qt.WindowModality.ApplicationModal)
                    message_box.exec()


def main() -> None:
    if load_dotenv(".env"):
        print(".env loaded")

    app = Application(sys.argv)

    if sys.platform not in {"win32", "linux"}:
        message_box = QMessageBox()
        message_box.setIcon(QMessageBox.Icon.Critical)
        message_box.setWindowTitle("Unsupported platform")
        message_box.setText("The application is supported on Windows and Linux.")
        message_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        message_box.exec()
        return

    if sys.platform == "linux":
        session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
        if session_type == "wayland":
            message_box = QMessageBox()
            message_box.setIcon(QMessageBox.Icon.Critical)
            message_box.setWindowTitle("Wayland not supported")
            message_box.setText("The application currently only supports X11 on Linux.")
            message_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            message_box.exec()
            return

    if os.environ.get("GT_DEV") == "true":
        signal.signal(signal.SIGINT, lambda *args: app.quit())
        signal.signal(signal.SIGTERM, lambda *args: app.quit())
        # Give the interpreter some opportunity to run.
        timer = QTimer()
        timer.start(500)
        timer.timeout.connect(lambda: None)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
