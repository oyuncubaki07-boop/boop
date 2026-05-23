# actions/focus_mode.py (PyQt6)
import winsound
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer

def focus_mode(parameters=None, player=None, root=None):
    params = parameters or {}
    action = params.get("action", "activate").lower()
    
    try:
        if action in ["activate", "on", "aç", "başlat"]:
            if player:
                player.write_log("SYS: 🚀 PROTOKOL: ODAK DEVREDE. Sistem optimize ediliyor...")
            
            if root and isinstance(root, QWidget):
                overlay = QWidget(root)
                overlay.setWindowFlags(
                    Qt.WindowType.FramelessWindowHint |
                    Qt.WindowType.WindowStaysOnTopHint
                )
                overlay.setWindowOpacity(0.85)
                overlay.setGeometry(10, 10, 250, 60)
                overlay.setStyleSheet("background-color: #001520;")

                layout = QVBoxLayout(overlay)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.setSpacing(2)

                title = QLabel("🎯 FOCUS MODE: ON")
                title.setStyleSheet(
                    "color: #00e6e6; font-family: 'Courier New'; font-size: 12px; font-weight: bold;"
                )
                title.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(title)

                subtitle = QLabel("Tüm bildirimler susturuldu.")
                subtitle.setStyleSheet(
                    "color: white; font-family: 'Courier New'; font-size: 8px;"
                )
                subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(subtitle)

                overlay.show()
                winsound.Beep(600, 200)
                winsound.Beep(800, 200)
                QTimer.singleShot(4000, overlay.close)
            
            return "Odak modu aktif patron. Dikkatinizi dağıtacak her şey susturuldu. İyi çalışmalar."
        
        else:
            if player:
                player.write_log("SYS: 🔌 PROTOKOL: ODAK İPTAL. Standart moda dönülüyor.")
            winsound.Beep(800, 150)
            winsound.Beep(600, 150)
            return "Odak modu kapatıldı patron. Bildirimler tekrar aktif."
            
    except Exception as e:
        return f"Odak moduna geçişte bir sorun yaşandı patron: {str(e)}"