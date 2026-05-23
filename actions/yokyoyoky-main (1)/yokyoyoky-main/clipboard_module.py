# actions/read_clipboard.py (PyQt6)
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PyQt6.QtCore import Qt, QTimer

def read_clipboard(parameters=None, player=None, root=None) -> str:
    try:
        if player:
            player.write_log("SYS: 📋 Pano verisi analiz ediliyor...")

        # PyQt6 panosundan metni al
        clipboard = QApplication.clipboard()
        pano_metni = clipboard.text()

        if not pano_metni or not pano_metni.strip():
            return "Pano şu anda tamamen boş."

        # Eğer root bir PyQt6 widget'ı ise HUD göster
        if root and isinstance(root, QWidget):
            try:
                hud = QWidget(root)
                hud.setWindowFlags(
                    Qt.WindowType.FramelessWindowHint |
                    Qt.WindowType.WindowStaysOnTopHint
                )
                hud.setWindowOpacity(0.95)
                hud.setGeometry(10, 10, 400, 120)
                hud.setStyleSheet("background-color: #002233;")

                layout = QVBoxLayout(hud)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.setSpacing(4)

                title = QLabel("📋 PANO İÇERİĞİ")
                title.setStyleSheet("color: #33ccff; font-family: 'Courier New'; font-size: 12px; font-weight: bold;")
                title.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(title)

                gosterilecek = pano_metni.strip()
                if len(gosterilecek) > 80:
                    gosterilecek = gosterilecek[:77] + "..."

                content = QLabel(gosterilecek)
                content.setStyleSheet("color: white; font-family: 'Courier New'; font-size: 9px;")
                content.setAlignment(Qt.AlignmentFlag.AlignLeft)
                content.setWordWrap(True)
                layout.addWidget(content)

                hud.show()
                QTimer.singleShot(5000, hud.close)
            except Exception as hud_err:
                if player:
                    player.write_log(f"SYS: Pano HUD gösterim hatası: {hud_err}")

        return f"Panoda şu metin var: {pano_metni[:100]}"

    except Exception as exc:
        if player:
            player.write_log(f"SYS: Pano modülü genel hatası: {exc}")
        return "Panoyu okurken beklenmedik bir hata oluştu."