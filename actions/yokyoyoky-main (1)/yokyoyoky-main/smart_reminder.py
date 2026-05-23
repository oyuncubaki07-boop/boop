# actions/smart_reminder.py
# J.A.R.V.I.S. Akıllı Hatırlatıcı Modülü (Gelişmiş) — PyQt6

import time
import threading
import winsound
import sys
from datetime import datetime, timedelta

from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer


def _reminder_thread(minutes, message, root, player, repeat=False):
    """Arka planda çalışan hatırlatıcı thread'i."""
    try:
        time.sleep(minutes * 60)

        repeats = 3 if repeat else 1
        for r in range(repeats):
            if player:
                player.write_log(f"⏰ HATIRLATMA ZAMANI: {message}")

            if sys.platform == "win32":
                for freq in [1200, 1500, 1800]:
                    winsound.Beep(freq, 200)
                    time.sleep(0.05)
            else:
                print("\a")
                time.sleep(0.5)

            if root:
                QTimer.singleShot(0, lambda: _show_reminder_hud(message, root))

            if repeats > 1 and r < repeats-1:
                time.sleep(2)

    except Exception as e:
        if player:
            player.write_log(f"Hatırlatıcı thread hatası: {e}")


def _show_reminder_hud(message, root):
    """PyQt6 Hatırlatma HUD penceresi."""
    if not root or not isinstance(root, QWidget):
        return
    try:
        hud = QWidget(root)
        hud.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        hud.setWindowOpacity(0.95)
        hud.setGeometry(15, 15, 420, 130)
        hud.setStyleSheet("background-color: #1a0033;")

        layout = QVBoxLayout(hud)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        title = QLabel("🔔 ZAMAN DOLDU PATRON!")
        title.setStyleSheet("color: #ff66cc; font-family: 'Orbitron', 'Courier New'; font-size: 12px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        msg_label = QLabel(message.upper())
        msg_label.setStyleSheet("color: white; font-family: 'Segoe UI'; font-size: 10px; font-weight: bold;")
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)

        time_label = QLabel(f"⏱️ {datetime.now().strftime('%H:%M:%S')}")
        time_label.setStyleSheet("color: #aaaaaa; font-family: 'Consolas'; font-size: 8px;")
        time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(time_label)

        close_btn = QPushButton("Tamam")
        close_btn.setStyleSheet(
            "QPushButton { background-color: #6600cc; color: white; border: none; padding: 5px 15px; }"
            "QPushButton:hover { background-color: #8800ff; }"
        )
        close_btn.clicked.connect(hud.close)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        hud.show()

        QTimer.singleShot(10000, hud.close)
    except:
        pass


def set_reminder(parameters=None, player=None, root=None, speak=None) -> str:
    """
    Akıllı hatırlatıcı kurar.
    
    Parametreler:
        minutes (int): Kaç dakika sonra hatırlatılacak (varsayılan: 1)
        message (str): Hatırlatma mesajı (varsayılan: "Bir hatırlatmanız var.")
        repeat (bool): 3 kez tekrarlı bildirim (varsayılan: False)
    """
    params = parameters or {}
    minutes = float(params.get("minutes", 1))
    message = params.get("message", "Bir hatırlatmanız var.")
    repeat = params.get("repeat", False)

    if minutes <= 0:
        return "Patron, süre pozitif bir sayı olmalı."

    if player:
        player.write_log(f"SYS: ⏲️ {minutes} dakika sonra hatırlatıcı kuruldu: {message}")

    threading.Thread(target=_reminder_thread, args=(minutes, message, root, player, repeat), daemon=True).start()

    if speak:
        speak(f"{minutes} dakika sonra size '{message}' konusunu hatırlatacağım.")

    # Anında HUD onayı
    if root and isinstance(root, QWidget):
        QTimer.singleShot(0, lambda: _show_set_hud(root, minutes, message))

    return f"✅ {minutes} dakika sonrasına hatırlatıcı kuruldu patron. Size '{message}' konusunu hatırlatacağım."


def _show_set_hud(root, minutes, message):
    """Hatırlatıcı kuruldu onay HUD'u."""
    try:
        hud = QWidget(root)
        hud.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        hud.setWindowOpacity(0.9)
        hud.setGeometry(15, 50, 350, 80)
        hud.setStyleSheet("background-color: #002233;")

        layout = QVBoxLayout(hud)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        title = QLabel("⏰ HATIRLATICI KURULDU")
        title.setStyleSheet("color: #00ffcc; font-family: 'Orbitron', 'Courier New'; font-size: 10px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        msg = QLabel(f"{minutes} dakika sonra: {message[:50]}")
        msg.setStyleSheet("color: white; font-family: 'Segoe UI'; font-size: 9px;")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(msg)

        hud.show()

        try:
            winsound.Beep(800, 100)
        except:
            pass

        QTimer.singleShot(3000, hud.close)
    except:
        pass