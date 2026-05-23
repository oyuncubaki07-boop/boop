# actions/welcome_screen.py (PyQt6)
from datetime import datetime
import math
import winsound

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QBrush


class HolographicSplash(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setStyleSheet("background-color: #000000;")
        self.setWindowOpacity(0.0)

        w, h = 550, 250
        self.resize(w, h)
        screen = self.screen().availableGeometry()
        self.move((screen.width() - w) // 2, (screen.height() - h) // 2)

        # Saat dilimine göre selamlama ve renk teması
        hour = datetime.now().hour
        if 5 <= hour < 12:
            self.greeting = "GÜNAYDIN EFENDİM 👋"
            self.accent_color = "#FFB347"
            self.glow_color = "#FFD700"
        elif 12 <= hour < 18:
            self.greeting = "TÜNAYDIN EFENDİM 👋"
            self.accent_color = "#4CAF50"
            self.glow_color = "#8BC34A"
        elif 18 <= hour < 22:
            self.greeting = "İYİ AKŞAMLAR EFENDİM 👋"
            self.accent_color = "#FF7043"
            self.glow_color = "#FF8A65"
        else:
            self.greeting = "İYİ GECELER EFENDİM 👋"
            self.accent_color = "#5C6BC0"
            self.glow_color = "#7986CB"

        # Animasyonlu çizgiler için değişkenler
        self.line_positions = [20 + i * 8 for i in range(10)]
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._move_lines)
        self.anim_timer.start(80)

        # Fade-in animasyonu
        self.fade_in_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_anim.setDuration(600)
        self.fade_in_anim.setStartValue(0.0)
        self.fade_in_anim.setEndValue(1.0)
        self.fade_in_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

        # Ses efekti
        try:
            for freq in [880, 1046, 1318, 1568]:
                winsound.Beep(freq, 40)
        except:
            pass

        self.show()
        self.fade_in_anim.start()

        # 5 saniye sonra fade-out yaparak kapat
        QTimer.singleShot(5000, self._start_fade_out)

    def _start_fade_out(self):
        self.fade_out_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out_anim.setDuration(500)
        self.fade_out_anim.setStartValue(1.0)
        self.fade_out_anim.setEndValue(0.0)
        self.fade_out_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_out_anim.finished.connect(self.close)
        self.fade_out_anim.start()

    def _move_lines(self):
        w, h = self.width(), self.height()
        for i in range(len(self.line_positions)):
            self.line_positions[i] += 1
            if self.line_positions[i] > h:
                self.line_positions[i] = 20 + i * 8
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Holografik arka plan ışıması (dairesel gradient taklidi)
        for i in range(1, 6):
            alpha = max(0, 15 - i * 2)
            color = QColor(self.accent_color)
            color.setAlpha(alpha)
            pen = QPen(color, 1)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(50 * i, 30 * i, w - 100 * i, h - 60 * i)

        # Dalgalanan holografik çizgiler
        line_color = QColor(self.accent_color)
        line_color.setAlpha(80)
        pen = QPen(line_color, 1)
        painter.setPen(pen)
        for y in self.line_positions:
            painter.drawLine(50, int(y), w - 50, int(y))

        # J.A.R.V.I.S. başlığı
        painter.setPen(QColor(self.accent_color))
        painter.setFont(QFont("Orbitron", 14, QFont.Weight.Bold))
        painter.drawText(0, 0, w, int(h * 0.4), Qt.AlignmentFlag.AlignCenter, "⚡ J.A.R.V.I.S. MARK-XXX ⚡")

        # Selamlama metni
        painter.setPen(QColor(self.glow_color))
        painter.setFont(QFont("Orbitron", 20, QFont.Weight.Bold))
        painter.drawText(0, int(h * 0.35), w, int(h * 0.4), Qt.AlignmentFlag.AlignCenter, self.greeting)

        # Alt bilgi
        painter.setPen(QColor("#888888"))
        painter.setFont(QFont("Consolas", 9))
        painter.drawText(0, int(h * 0.7), w, int(h * 0.3), Qt.AlignmentFlag.AlignCenter,
                         "Tüm sistemler çevrimiçi | Nöral bağlantı kuruldu")


def show_welcome_hologram(parent_root=None):
    """
    PyQt6 tabanlı holografik karşılama penceresi.
    'parent_root' parametresi PyQt6'da kullanılmaz, None bırakılabilir.
    """
    splash = HolographicSplash()
    return splash