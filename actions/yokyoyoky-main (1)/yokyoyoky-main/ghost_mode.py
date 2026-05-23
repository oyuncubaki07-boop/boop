# actions/ghost_mode.py (PyQt6)
import pyautogui
import os
import time
import winsound
import sys

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer

def _show_hud(root, message, duration=2500):
    """HUD gösterimi (PyQt6)."""
    if not root or not isinstance(root, QWidget):
        return
    try:
        hud = QWidget(root)
        hud.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        hud.setWindowOpacity(0.88)
        hud.setGeometry(15, 15, 280, 60)
        hud.setStyleSheet("background-color: #00050a;")

        layout = QVBoxLayout(hud)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel("🕵️ " + message)
        label.setStyleSheet(
            "color: #00e6e6; font-family: 'Orbitron', 'Courier New'; font-size: 9px; font-weight: bold;"
        )
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        hud.show()

        try:
            winsound.Beep(500, 100)
        except:
            pass

        QTimer.singleShot(duration, hud.close)
    except:
        pass

def ghost_mode(parameters=None, player=None, root=None, speak=None) -> str:
    params = parameters or {}
    action = params.get("action", "activate").lower()
    mute_sound = params.get("mute_sound", True)
    hide_windows = params.get("hide_windows", True)
    
    try:
        if action in ["activate", "aç", "başlat", "enable"]:
            if player:
                player.write_log("SYS: 👻 PROTOKOL HAYALET DEVREDE.")
            
            if speak:
                speak("Hayalet protokolü aktif. Gizlilik sağlanıyor.")
            
            if mute_sound:
                try:
                    for _ in range(30):
                        pyautogui.press("volumedown")
                    for _ in range(5):
                        pyautogui.press("volumeup")
                    if player:
                        player.write_log("SYS: Ses seviyesi güvenli seviyeye ayarlandı.")
                except Exception as e:
                    if player:
                        player.write_log(f"SYS: Ses ayarı yapılamadı: {e}")
            
            if hide_windows:
                pyautogui.hotkey('win', 'd')
                time.sleep(0.3)
            
            try:
                if os.system("start opera") != 0:
                    os.system("start chrome")
                if player:
                    player.write_log("SYS: Kamuflaj tarayıcısı açıldı.")
            except:
                pass
            
            _show_hud(root, "GİZLİLİK SAĞLANDI")
            
            return "Hayalet protokolü aktif. Ekran temizlendi, sesler güvenli seviyeye çekildi ve kamuflaj sağlandı patron."

        elif action in ["deactivate", "kapat", "stop", "disable"]:
            if player:
                player.write_log("SYS: Hayalet modu kapatılıyor.")
            
            if speak:
                speak("Hayalet protokolü kapatılıyor, efendim.")
            
            _show_hud(root, "HAYALET MODU KAPATILDI", duration=2000)
            return "Hayalet modu devre dışı bırakıldı."

        else:
            return f"Bilinmeyen aksiyon: {action}. Kullanılabilir: activate, deactivate"

    except Exception as e:
        error_msg = f"Hayalet modunda hata: {str(e)}"
        if player:
            player.write_log(f"SYS: {error_msg}")
        return error_msg