"""
media_controller.py - J.A.R.V.I.S. Medya Kontrol Modülü (PyQt6 + HUD Simge)
Müzik/video oynatma, durdurma, sonraki/önceki, ses aç/kıs/sustur işlemleri.
Platform: Windows, macOS, Linux (kısmi).
"""

import sys
import platform
import winsound
from typing import Optional

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer


def get_platform() -> str:
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    elif system == "darwin":
        return "macos"
    else:
        return "linux"


def _get_media_keys():
    """Platforma göre medya tuşlarını döndürür."""
    plat = get_platform()
    if plat == "windows":
        return {
            "playpause": "playpause",
            "nexttrack": "nexttrack",
            "prevtrack": "prevtrack",
            "volumeup": "volumeup",
            "volumedown": "volumedown",
            "volumemute": "volumemute"
        }
    elif plat == "macos":
        return {
            "playpause": "playpause",
            "nexttrack": "nexttrack",
            "prevtrack": "prevtrack",
            "volumeup": "volumeup",
            "volumedown": "volumedown",
            "volumemute": "volumemute"
        }
    else:  # Linux
        return {
            "playpause": "XF86AudioPlay",
            "nexttrack": "XF86AudioNext",
            "prevtrack": "XF86AudioPrev",
            "volumeup": "XF86AudioRaiseVolume",
            "volumedown": "XF86AudioLowerVolume",
            "volumemute": "XF86AudioMute"
        }


# Simge sözlüğü – her komut için bir ikon ve başlık
_HUD_ICONS = {
    "playpause":  ("▶⏸", "PLAY / PAUSE"),
    "nexttrack":  ("⏭️", "NEXT TRACK"),
    "prevtrack":  ("⏮️", "PREVIOUS TRACK"),
    "volumeup":   ("🔊", "VOLUME UP"),
    "volumedown": ("🔉", "VOLUME DOWN"),
    "volumemute": ("🔇", "MUTE / UNMUTE"),
}


def _show_hud(root, action: str):
    """PyQt6 küçük hologram HUD – ikon ve metin gösterir."""
    if not root or not isinstance(root, QWidget):
        return
    try:
        icon, text = _HUD_ICONS.get(action, ("🎵", action.upper()))

        hud = QWidget(root)
        hud.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        hud.setWindowOpacity(0.88)
        hud.setGeometry(10, 10, 280, 80)
        hud.setStyleSheet("background-color: #2b002b;")

        layout = QVBoxLayout(hud)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("color: #ff33cc; font-size: 22px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        text_label = QLabel(text)
        text_label.setStyleSheet("color: white; font-family: 'Courier New'; font-size: 9px;")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(text_label)

        hud.show()

        try:
            winsound.Beep(500, 120)
        except:
            pass

        QTimer.singleShot(2000, hud.close)
    except:
        pass


def media_controller(parameters: Optional[dict] = None, player=None, root=None) -> str:
    params = parameters or {}
    command = params.get("command", "").lower().strip()
    volume_steps = params.get("volume_steps", 5)

    if not command:
        return "Medya komutu belirtilmedi patron. Örnek: 'play', 'next', 'volume up'."

    if not PYAUTOGUI_AVAILABLE:
        return "PyAutoGUI kütüphanesi yüklü değil. Medya kontrolü için 'pip install pyautogui' gereklidir."

    if player:
        player.write_log(f"SYS: 🎵 Medya komutu: {command}")

    action_map = {
        "play": "playpause", "oynat": "playpause", "başlat": "playpause",
        "pause": "playpause", "durdur": "playpause", "duraklat": "playpause",
        "next": "nexttrack", "geç": "nexttrack", "ileri": "nexttrack", "sonraki": "nexttrack",
        "previous": "prevtrack", "geri": "prevtrack", "önceki": "prevtrack",
        "up": "volumeup", "aç": "volumeup", "arttır": "volumeup", "yukarı": "volumeup",
        "down": "volumedown", "kıs": "volumedown", "azalt": "volumedown", "aşağı": "volumedown",
        "mute": "volumemute", "sustur": "volumemute", "sesi kapat": "volumemute"
    }

    action = None
    for key, val in action_map.items():
        if key in command:
            action = val
            break

    if action is None:
        return f"Bilinmeyen medya komutu: '{command}'. Desteklenenler: play, pause, next, previous, volume up/down, mute."

    media_keys = _get_media_keys()
    if action not in media_keys:
        return f"'{action}' işlemi bu platformda desteklenmiyor."

    key_to_press = media_keys[action]

    try:
        if action in ["volumeup", "volumedown"]:
            steps = max(1, min(20, volume_steps))
            for _ in range(steps):
                pyautogui.press(key_to_press)
        else:
            pyautogui.press(key_to_press)
    except Exception as e:
        if player:
            player.write_log(f"SYS: Medya tuş hatası: {e}")
        return f"Medya tuşu gönderilemedi: {str(e)}"

    # HUD gösterimi (simge + yazı)
    _show_hud(root, action)

    return f"Medya kontrolü tamamlandı patron. '{command}' işlemi uygulandı."