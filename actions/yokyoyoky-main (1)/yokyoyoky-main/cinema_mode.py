import os
import time
import winsound
import pyautogui
import webbrowser
import subprocess

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer

def cinema_mode(parameters=None, player=None, root=None) -> str:
    params = parameters or {}
    action = params.get("action", "on").lower()
    
    try:
        if action in ["on", "aç", "başlat", "aktive et"]:
            if player: 
                player.write_log("SYS: 🍿 Sinema Modu başlatılıyor...")
            
            # Masaüstünü temizle (Tüm pencereleri aşağı al) - Hata toleranslı
            try:
                pyautogui.hotkey('win', 'd')
                time.sleep(0.5)
            except Exception as e:
                if player: player.write_log(f"SYS: Masaüstü temizleme hatası: {e}")
            
            # Öncelik Windows Netflix uygulamasında, yoksa tarayıcıdan açar
            netflix_opened = False
            try:
                result = subprocess.run("start netflix:", shell=True, capture_output=True)
                if result.returncode == 0:
                    netflix_opened = True
            except:
                pass
                
            if not netflix_opened:
                webbrowser.open("https://www.netflix.com")
            
            if root:
                try:
                    # PyQt6 HUD penceresi
                    parent = root if isinstance(root, QWidget) else None
                    hud = QWidget(parent)
                    hud.setWindowFlags(
                        Qt.WindowType.FramelessWindowHint |
                        Qt.WindowType.WindowStaysOnTopHint
                    )
                    hud.setWindowOpacity(0.95)
                    hud.setGeometry(10, 10, 300, 80)
                    hud.setStyleSheet("background-color: #1a001a;")

                    layout = QVBoxLayout(hud)
                    layout.setContentsMargins(0, 0, 0, 0)
                    layout.setSpacing(4)

                    title_label = QLabel("🍿 SİNEMA MODU: AKTİF")
                    title_label.setStyleSheet(
                        "color: #ff00ff; font-family: 'Courier New'; font-size: 12px; font-weight: bold;"
                    )
                    title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    layout.addWidget(title_label)

                    sub_label = QLabel("Arkanıza yaslanın ve keyfini çıkarın.")
                    sub_label.setStyleSheet(
                        "color: white; font-family: 'Courier New'; font-size: 9px;"
                    )
                    sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    layout.addWidget(sub_label)

                    hud.show()

                    winsound.Beep(400, 200)
                    winsound.Beep(600, 300)

                    QTimer.singleShot(4000, hud.close)
                except Exception as hud_err:
                    if player: player.write_log(f"SYS: Sinema HUD hatası: {hud_err}")
                    
            return "Sinema modu aktif edildi. İyi seyirler patron."
        else:
            return "Sinema modu için geçersiz komut."
            
    except Exception as exc:
        if player: player.write_log(f"SYS: Sinema modu başlatılamadı: {exc}")
        return "Sinema modu başlatılırken bir sorun oluştu."