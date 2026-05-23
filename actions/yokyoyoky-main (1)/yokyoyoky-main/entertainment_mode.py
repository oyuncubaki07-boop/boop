# actions/entertainment_mode.py (PyQt6)
import random
import winsound
import os
import threading
import time

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer

def _hacker_visuals():
    """Arka planda 3 adet yeşil renkli Matrix tarzı CMD tarama ekranı açar."""
    try:
        for _ in range(3):
            os.system('start cmd /k "color a & dir /s"')
            time.sleep(0.4)
    except:
        pass

def entertainment_mode(parameters=None, player=None, root=None):
    try:
        if player:
            player.write_log("SYS: 🎭 Eğlence ve Gösteri protokolü devrede.")
        
        threading.Thread(target=_hacker_visuals, daemon=True).start()
        
        jokes = [
            "Neden bilgisayarlar soğuk sever? Çünkü Windows (pencereler) açık!",
            "Stark endüstrilerinde bir kural vardır: Önce ateş et, sonra soru sor. Ama ben önce soruyorum efendim.",
            "Among Us'ta impostor olduğunuzu anladığımda size yardım edemem patron, kurallar böyle.",
            "Bir yazılımcının en çok söylediği yalan nedir bilir misiniz? 'Kodum bilgisayarımda sorunsuz çalışıyordu'."
        ]
        
        secilen_saka = random.choice(jokes)
        
        if root and isinstance(root, QWidget):
            try:
                hud = QWidget(root)
                hud.setWindowFlags(
                    Qt.WindowType.FramelessWindowHint |
                    Qt.WindowType.WindowStaysOnTopHint
                )
                hud.setWindowOpacity(0.9)
                hud.setGeometry(10, 10, 400, 120)
                hud.setStyleSheet("background-color: #000d1a;")

                layout = QVBoxLayout(hud)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.setSpacing(4)

                title_label = QLabel("🎭 EĞLENCE PROTOKOLÜ")
                title_label.setStyleSheet(
                    "color: #00ff00; font-family: 'Courier New'; font-size: 12px; font-weight: bold;"
                )
                title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(title_label)

                joke_label = QLabel(secilen_saka)
                joke_label.setStyleSheet(
                    "color: white; font-family: 'Courier New'; font-size: 9px;"
                )
                joke_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                joke_label.setWordWrap(True)
                layout.addWidget(joke_label)

                hud.show()

                winsound.Beep(400, 100)
                winsound.Beep(600, 150)

                QTimer.singleShot(6000, hud.close)
            except:
                pass
            
        return f"Görsel şölen başlatıldı patron. {secilen_saka}"
        
    except Exception as e:
        return f"Eğlence modülünde bir donanım/yazılım hatası oluştu patron: {str(e)}"