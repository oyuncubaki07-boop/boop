# actions/edex_ui.py (PyQt6)
# J.A.R.V.I.S. eDEX-UI Kontrol Paneli

import ctypes
import os
import subprocess
import time
from ctypes import wintypes
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QFrame, QApplication
)
from PyQt6.QtCore import Qt

TARGET_MONITOR_NAME = "ASUS VW193D"

DEFAULT_EDEX_PATHS = [
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "eDEX-UI", "eDEX-UI.exe"),
    os.path.join(os.environ.get("ProgramFiles", ""), "eDEX-UI", "eDEX-UI.exe"),
    os.path.join(os.environ.get("ProgramFiles(x86)", ""), "eDEX-UI", "eDEX-UI.exe"),
]


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


class MONITORINFOEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", wintypes.DWORD),
        ("szDevice", ctypes.c_wchar * 32),
    ]


class DISPLAY_DEVICEW(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("DeviceName", ctypes.c_wchar * 32),
        ("DeviceString", ctypes.c_wchar * 128),
        ("StateFlags", wintypes.DWORD),
        ("DeviceID", ctypes.c_wchar * 128),
        ("DeviceKey", ctypes.c_wchar * 128),
    ]


def _find_edex_executable() -> str:
    for candidate in DEFAULT_EDEX_PATHS:
        if candidate and os.path.exists(candidate):
            return candidate
    return ""


def _list_monitors() -> list:
    user32 = ctypes.windll.user32
    monitors = []

    monitor_enum_proc = ctypes.WINFUNCTYPE(
        ctypes.c_int, wintypes.HMONITOR, wintypes.HDC,
        ctypes.POINTER(RECT), wintypes.LPARAM,
    )

    def callback(hmonitor, _hdc, _lprect, _lparam):
        info = MONITORINFOEXW()
        info.cbSize = ctypes.sizeof(MONITORINFOEXW)
        user32.GetMonitorInfoW(hmonitor, ctypes.byref(info))
        device = DISPLAY_DEVICEW()
        device.cb = ctypes.sizeof(DISPLAY_DEVICEW)
        friendly_name = info.szDevice
        if user32.EnumDisplayDevicesW(info.szDevice, 0, ctypes.byref(device), 0):
            friendly_name = device.DeviceString or info.szDevice
        rect = info.rcMonitor
        monitors.append({
            "device_name": info.szDevice,
            "friendly_name": friendly_name,
            "left": rect.left,
            "top": rect.top,
            "width": rect.right - rect.left,
            "height": rect.bottom - rect.top,
        })
        return 1

    user32.EnumDisplayMonitors(0, 0, monitor_enum_proc(callback), 0)
    return monitors


def _pick_monitor(target_name: str) -> Optional[Dict[str, Any]]:
    monitors = _list_monitors()
    if not monitors:
        return None
    normalized = (target_name or "").strip().lower()
    for monitor in monitors:
        haystack = f"{monitor['friendly_name']} {monitor['device_name']}".lower()
        if normalized and normalized in haystack:
            return monitor
    if len(monitors) > 1:
        return monitors[1]
    return monitors[0]


def _move_window_to_monitor(title_hint: str, monitor: dict, timeout: float = 12.0) -> bool:
    user32 = ctypes.windll.user32
    target = {"hwnd": None}
    enum_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

    def callback(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        if title_hint.lower() in buffer.value.lower():
            target["hwnd"] = hwnd
            return False
        return True

    deadline = time.time() + timeout
    while time.time() < deadline:
        user32.EnumWindows(enum_proc(callback), 0)
        if target["hwnd"]:
            width = min(1400, max(900, monitor["width"] - 40))
            height = min(900, max(650, monitor["height"] - 40))
            x = monitor["left"] + max(10, (monitor["width"] - width) // 2)
            y = monitor["top"] + max(10, (monitor["height"] - height) // 2)
            user32.ShowWindow(target["hwnd"], 9)
            user32.SetWindowPos(target["hwnd"], 0, x, y, width, height, 0x0040)
            return True
        time.sleep(0.35)
    return False


def edex_ui(parameters: Optional[Dict] = None, player=None, root=None, speak=None) -> str:
    params = parameters or {}
    target_name = params.get("monitor_name", TARGET_MONITOR_NAME)
    launch_native = bool(params.get("launch_native", True))

    if root is None:
        return "Kontrol paneli için arayüz kökü bulunamadı, efendim."

    monitor = _pick_monitor(target_name)
    if monitor is None:
        return "Monitör bilgisi alınamadı. Kontrol paneli açılamadı."

    if player:
        player.write_log(f"SYS: eDEX UI kontrol paneli açılıyor -> {monitor['friendly_name']}")
    if speak:
        speak(f"Kontrol paneli {monitor['friendly_name']} monitöründe açılıyor, efendim.")

    native_status = ""
    if launch_native:
        exe_path = _find_edex_executable()
        if exe_path:
            try:
                subprocess.Popen([exe_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                moved = _move_window_to_monitor("edex-ui", monitor)
                native_status = " Gerçek eDEX-UI uygulaması da hedef monitöre taşındı." if moved else \
                                " eDEX-UI uygulaması açıldı ama pencere konumu otomatik doğrulanamadı."
            except Exception as exc:
                native_status = f" eDEX-UI başlatılırken hata: {exc}"
        else:
            native_status = " eDEX-UI.exe sistemde bulunamadı."

    # --- PyQt6 Paneli ---
    panel = QWidget(None)  # bağımsız pencere
    panel.setWindowTitle("JARVIS eDEX UI")
    panel.setStyleSheet("background-color: #04141b;")
    panel.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

    width = min(1280, max(900, monitor["width"] - 80))
    height = min(820, max(620, monitor["height"] - 80))
    x = monitor["left"] + max(20, (monitor["width"] - width) // 2)
    y = monitor["top"] + max(20, (monitor["height"] - height) // 2)
    panel.setGeometry(x, y, width, height)

    main_layout = QVBoxLayout(panel)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)

    # Başlık
    title = QLabel("JARVIS CONTROL GRID")
    title.setStyleSheet("color: #5ffbf1; font-family: 'Consolas'; font-size: 24px; font-weight: bold;")
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    main_layout.addWidget(title)
    main_layout.addSpacing(8)

    # Alt başlık
    subtitle = QLabel(f"Target Monitor: {monitor['friendly_name']}")
    subtitle.setStyleSheet("color: #97b9c2; font-family: 'Consolas'; font-size: 11px;")
    subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
    main_layout.addWidget(subtitle)
    main_layout.addSpacing(18)

    # Kartlar için grid
    grid = QGridLayout()
    grid.setContentsMargins(24, 12, 24, 12)
    grid.setSpacing(10)

    cards = [
        ("🛡️ Security", "biometric_shield | lockdown_protocol | security_mode"),
        ("⚙️ System", "system_status | system_maintenance | performance_boost"),
        ("🤖 Automation", "auto_pilot | macro_master | workspace_mode"),
        ("🎬 Media", "browser_control | youtube_video | media_controller"),
        ("💬 Comms", "send_message | share_location | social_ghost"),
        ("👁️ Vision", "vision_scan | screen_process | cyber_eye_control"),
    ]

    for index, (label, body) in enumerate(cards):
        card = QFrame()
        card.setStyleSheet(
            "QFrame { background-color: #0b1f29; border: 1px solid #1ee7d8; }"
        )
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(8)

        card_label = QLabel(label)
        card_label.setStyleSheet("color: #1ee7d8; font-family: 'Consolas'; font-size: 16px; font-weight: bold;")
        card_layout.addWidget(card_label)

        card_body = QLabel(body)
        card_body.setStyleSheet("color: #d7f8ff; font-family: 'Consolas'; font-size: 11px;")
        card_body.setWordWrap(True)
        card_layout.addWidget(card_body)

        row, col = divmod(index, 2)
        grid.addWidget(card, row, col)

    main_layout.addLayout(grid)

    # Footer
    footer = QHBoxLayout()
    footer.setContentsMargins(24, 0, 24, 20)
    footer.addStretch()

    close_btn = QPushButton("KAPAT")
    close_btn.setStyleSheet("""
        QPushButton {
            background-color: #111f28;
            color: #ff7676;
            font-family: 'Consolas';
            font-size: 12px;
            font-weight: bold;
            border: none;
            padding: 10px 20px;
        }
        QPushButton:hover {
            background-color: #17303c;
            color: #ffffff;
        }
    """)
    close_btn.clicked.connect(panel.close)
    footer.addWidget(close_btn)

    main_layout.addLayout(footer)
    panel.show()

    return f"✅ eDEX UI kontrol paneli {monitor['friendly_name']} monitöründe açıldı.{native_status}"