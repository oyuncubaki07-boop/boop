# actions/cyber_sleep.py (PyQt6)
import os
import winsound
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer

def cyber_sleep(parameters=None, player=None, root=None) -> str:
    if player:
        player.write_log("SYS: 🌙 Siber Uyku Protokolü başlatılıyor...")
    
    try:
        if root and isinstance(root, QWidget):
            try:
                hud = QWidget(root)
                hud.setWindowFlags(
                    Qt.WindowType.FramelessWindowHint |
                    Qt.WindowType.WindowStaysOnTopHint
                )
                hud.setWindowOpacity(0.95)
                hud.setGeometry(10, 10, 300, 80)
                hud.setStyleSheet("background-color: #00001a;")

                layout = QVBoxLayout(hud)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.setSpacing(4)

                title = QLabel("🌙 SİBER UYKU")
                title.setStyleSheet("color: #99ccff; font-family: 'Courier New'; font-size: 14px; font-weight: bold;")
                title.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(title)

                subtitle = QLabel("Sistem derin uykuya geçiyor...")
                subtitle.setStyleSheet("color: white; font-family: 'Courier New'; font-size: 9px;")
                subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(subtitle)

                hud.show()

                winsound.Beep(500, 300)
                winsound.Beep(300, 400)

                QTimer.singleShot(3000, hud.close)
            except Exception:
                pass
                
        # Windows Uyku / Hazırda Beklet Komutu
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        
        return "Sistem uyku moduna alındı. Görüşmek üzere patron."
        
    except Exception as exc:
        if player:
            player.write_log(f"SYS: Uyku modu hatası: {exc}")
        return "Uyku moduna geçiş sırasında bir hata oluştu."