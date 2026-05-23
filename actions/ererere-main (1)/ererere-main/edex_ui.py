# actions/edex_ui.py
# J.A.R.V.I.S. eDEX-UI Kontrol Paneli (ASUS VW193D ve diğer monitörler için)

import ctypes
import os
import subprocess
import time
import tkinter as tk
from ctypes import wintypes
from typing import Optional, Dict, Any

# Hedef monitor adı (varsayılan)
TARGET_MONITOR_NAME = "ASUS VW193D"

# eDEX-UI kurulum yolları (yaygın konumlar)
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
    """eDEX-UI.exe'nin yolunu arar."""
    for candidate in DEFAULT_EDEX_PATHS:
        if candidate and os.path.exists(candidate):
            return candidate
    return ""


def _list_monitors() -> list:
    """Sistemdeki tüm monitörleri listeler."""
    user32 = ctypes.windll.user32
    monitors = []

    monitor_enum_proc = ctypes.WINFUNCTYPE(
        ctypes.c_int,
        wintypes.HMONITOR,
        wintypes.HDC,
        ctypes.POINTER(RECT),
        wintypes.LPARAM,
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
    """
    Hedef monitörü seçer. 
    Önce isme göre arar, bulamazsa ikinci monitörü döner, yoksa birinciyi döner.
    """
    monitors = _list_monitors()
    if not monitors:
        return None

    normalized = (target_name or "").strip().lower()
    for monitor in monitors:
        haystack = f"{monitor['friendly_name']} {monitor['device_name']}".lower()
        if normalized and normalized in haystack:
            return monitor

    # İsimle bulunamazsa, birden fazla monitör varsa ikinciyi döndür
    if len(monitors) > 1:
        return monitors[1]
    return monitors[0]


def _move_window_to_monitor(title_hint: str, monitor: dict, timeout: float = 12.0) -> bool:
    """Belirtilen başlığa sahip pencereyi hedef monitöre taşır."""
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
        title = buffer.value.lower()
        if title_hint.lower() in title:
            target["hwnd"] = hwnd
            return False
        return True

    deadline = time.time() + timeout
    while time.time() < deadline:
        user32.EnumWindows(enum_proc(callback), 0)
        if target["hwnd"]:
            # Pencere boyutunu hedef monitöre göre ayarla
            width = min(1400, max(900, monitor["width"] - 40))
            height = min(900, max(650, monitor["height"] - 40))
            x = monitor["left"] + max(10, (monitor["width"] - width) // 2)
            y = monitor["top"] + max(10, (monitor["height"] - height) // 2)
            user32.ShowWindow(target["hwnd"], 9)  # SW_RESTORE
            user32.SetWindowPos(target["hwnd"], 0, x, y, width, height, 0x0040)  # SWP_NOZORDER
            return True
        time.sleep(0.35)
    return False


def edex_ui(parameters: Optional[Dict] = None, player=None, root=None, speak=None) -> str:
    """
    JARVIS kontrol panelini (eDEX-UI tarzı) hedef monitörde açar.
    
    Parametreler:
        monitor_name (str): Hedef monitör adı (varsayılan: "ASUS VW193D")
        launch_native (bool): eDEX-UI uygulamasını da başlat (varsayılan: True)
    """
    params = parameters or {}
    target_name = params.get("monitor_name", TARGET_MONITOR_NAME)
    launch_native = bool(params.get("launch_native", True))

    if root is None:
        return "Kontrol paneli için arayüz kökü bulunamadı, efendim."

    # Monitör seç
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
                if moved:
                    native_status = " Gerçek eDEX-UI uygulaması da hedef monitöre taşındı."
                else:
                    native_status = " eDEX-UI uygulaması açıldı ama pencere konumu otomatik doğrulanamadı."
            except Exception as exc:
                native_status = f" eDEX-UI başlatılırken hata: {exc}"
        else:
            native_status = " eDEX-UI.exe sistemde bulunamadı."

    # Tkinter paneli oluştur
    panel = tk.Toplevel(root)
    panel.title("JARVIS eDEX UI")
    panel.configure(bg="#04141b")
    panel.attributes("-topmost", True)

    width = min(1280, max(900, monitor["width"] - 80))
    height = min(820, max(620, monitor["height"] - 80))
    x = monitor["left"] + max(20, (monitor["width"] - width) // 2)
    y = monitor["top"] + max(20, (monitor["height"] - height) // 2)
    panel.geometry(f"{width}x{height}+{x}+{y}")

    # Başlık
    title = tk.Label(
        panel,
        text="JARVIS CONTROL GRID",
        fg="#5ffbf1",
        bg="#04141b",
        font=("Consolas", 24, "bold"),
    )
    title.pack(pady=(18, 8))

    # Alt başlık
    subtitle = tk.Label(
        panel,
        text=f"Target Monitor: {monitor['friendly_name']}",
        fg="#97b9c2",
        bg="#04141b",
        font=("Consolas", 11),
    )
    subtitle.pack(pady=(0, 18))

    # Grid çerçevesi
    grid = tk.Frame(panel, bg="#04141b")
    grid.pack(fill=tk.BOTH, expand=True, padx=24, pady=12)

    # Kartlar (kategori başlıkları ve komutlar)
    cards = [
        ("🛡️ Security", "biometric_shield | lockdown_protocol | security_mode"),
        ("⚙️ System", "system_status | system_maintenance | performance_boost"),
        ("🤖 Automation", "auto_pilot | macro_master | workspace_mode"),
        ("🎬 Media", "browser_control | youtube_video | media_controller"),
        ("💬 Comms", "send_message | share_location | social_ghost"),
        ("👁️ Vision", "vision_scan | screen_process | cyber_eye_control"),
    ]

    for index, (label, body) in enumerate(cards):
        card = tk.Frame(
            grid,
            bg="#0b1f29",
            highlightbackground="#1ee7d8",
            highlightthickness=1,
        )
        row, col = divmod(index, 2)
        card.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)

        tk.Label(
            card,
            text=label,
            fg="#1ee7d8",
            bg="#0b1f29",
            font=("Consolas", 16, "bold"),
        ).pack(anchor="w", padx=16, pady=(16, 8))

        tk.Label(
            card,
            text=body,
            fg="#d7f8ff",
            bg="#0b1f29",
            justify="left",
            wraplength=420,
            font=("Consolas", 11),
        ).pack(anchor="w", padx=16, pady=(0, 16))

    # Grid ağırlıkları
    for col in range(2):
        grid.grid_columnconfigure(col, weight=1)
    for row in range(3):
        grid.grid_rowconfigure(row, weight=1)

    # Footer
    footer = tk.Frame(panel, bg="#04141b")
    footer.pack(fill=tk.X, padx=24, pady=(0, 20))

    tk.Button(
        footer,
        text="KAPAT",
        command=panel.destroy,
        bg="#111f28",
        fg="#ff7676",
        activebackground="#17303c",
        activeforeground="#ffffff",
        font=("Consolas", 12, "bold"),
        relief="flat",
        padx=20,
        pady=10,
    ).pack(side=tk.RIGHT)

    return f"✅ eDEX UI kontrol paneli {monitor['friendly_name']} monitöründe açıldı.{native_status}"