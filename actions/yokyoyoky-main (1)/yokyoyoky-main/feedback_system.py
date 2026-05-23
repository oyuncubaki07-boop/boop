# actions/feedback_system.py (PyQt6)
import winsound
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer

def report_issue(parameters=None, player=None, root=None):
    params = parameters or {}
    issue_message = params.get("message", "Üzgünüm patron, ne demek istediğinizi veya komutu tam olarak anlayamadım.")
    
    try:
        if player:
            player.write_log(f"SYS-UYARI: {issue_message}")
        
        if root and isinstance(root, QWidget):
            try:
                hud = QWidget(root)
                hud.setWindowFlags(
                    Qt.WindowType.FramelessWindowHint |
                    Qt.WindowType.WindowStaysOnTopHint
                )
                hud.setWindowOpacity(0.95)
                hud.setGeometry(10, 10, 400, 100)
                hud.setStyleSheet("background-color: #330000;")

                layout = QVBoxLayout(hud)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.setSpacing(4)

                title_label = QLabel("⚠️ SİSTEM GERİ BİLDİRİMİ")
                title_label.setStyleSheet(
                    "color: #ff3333; font-family: 'Courier New'; font-size: 12px; font-weight: bold;"
                )
                title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(title_label)

                message_label = QLabel(issue_message)
                message_label.setStyleSheet(
                    "color: white; font-family: 'Courier New'; font-size: 9px;"
                )
                message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                message_label.setWordWrap(True)
                layout.addWidget(message_label)

                hud.show()

                winsound.Beep(300, 200)
                winsound.Beep(200, 300)

                QTimer.singleShot(5000, hud.close)
            except:
                pass
            
        return f"Geri bildirim kaydedildi: {issue_message}. Lütfen komutu tekrar edin patron."
        
    except Exception as e:
        return f"Geri bildirim modülünde hata: {str(e)}"