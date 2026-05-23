"""
morning_alarm.py - J.A.R.V.I.S. Sabah Alarmı Modülü (PyQt6)
Belirtilen saatte alarm çalar, erteleme seçeneği sunar.
"""

import threading
import time
import winsound
import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QApplication
)
from PyQt6.QtCore import Qt, QTimer


def _parse_time(time_str: str) -> tuple:
    """HH:MM formatını (saat, dakika) tamsayıya çevirir."""
    parts = time_str.strip().split(":")
    if len(parts) == 2:
        try:
            hour = int(parts[0])
            minute = int(parts[1])
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return hour, minute
        except ValueError:
            pass
    return None, None


def _calculate_wait_seconds(target_hour: int, target_minute: int) -> int:
    """Hedef saate kadar beklenmesi gereken saniye sayısını döndürür."""
    now = datetime.datetime.now()
    target = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
    if target <= now:
        target += datetime.timedelta(days=1)
    return int((target - now).total_seconds())


def _alarm_thread(target_time_str: str, root, player, snooze_minutes: int = 5):
    """Alarm thread'i, hedef saati bekler ve çaldırır."""
    hour, minute = _parse_time(target_time_str)
    if hour is None:
        return

    wait_seconds = _calculate_wait_seconds(hour, minute)

    if player:
        player.write_log(f"SYS: ⏰ Alarm kuruldu. {wait_seconds // 60} dakika sonra çalacak.")

    time.sleep(wait_seconds)

    # Alarmı tetikle (ana thread'de GUI işlemleri)
    if root:
        QTimer.singleShot(0, lambda: _play_alarm(root, player, snooze_minutes, target_time_str))


def _play_alarm(root, player, snooze_minutes: int, original_time: str):
    """Alarm penceresini gösterir, ses çalar ve erteleme seçeneği sunar."""
    try:
        # Önceki alarm penceresi varsa kapat
        for widget in QApplication.topLevelWidgets():
            if widget.windowTitle() == "Alarm" and widget.isVisible():
                widget.close()

        parent = root if isinstance(root, QWidget) else None
        hud = QWidget(parent)
        hud.setWindowTitle("Alarm")
        hud.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        hud.setWindowOpacity(0.95)
        hud.setGeometry(10, 10, 400, 180)
        hud.setStyleSheet("background-color: #e65c00;")

        layout = QVBoxLayout(hud)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        title = QLabel("🌅 GÜNAYDIN PATRON")
        title.setStyleSheet("color: white; font-family: 'Courier New'; font-size: 16px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        msg = QLabel("Sabah alarmınız çalıyor.\nYeni bir güne hazırız.")
        msg.setStyleSheet("color: white; font-family: 'Courier New'; font-size: 11px;")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(msg)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        btn_layout.addStretch()

        snooze_btn = QPushButton(f"Ertele ({snooze_minutes} dk)")
        snooze_btn.setStyleSheet(
            "QPushButton { background-color: #ff9933; color: white; font-family: 'Arial'; "
            "font-size: 10px; font-weight: bold; border: none; padding: 8px 15px; }"
            "QPushButton:hover { background-color: #ffaa55; }"
        )
        snooze_btn.clicked.connect(lambda: _on_snooze(hud, root, player, snooze_minutes))
        btn_layout.addWidget(snooze_btn)

        dismiss_btn = QPushButton("Kapat")
        dismiss_btn.setStyleSheet(
            "QPushButton { background-color: #cc4400; color: white; font-family: 'Arial'; "
            "font-size: 10px; font-weight: bold; border: none; padding: 8px 15px; }"
            "QPushButton:hover { background-color: #dd5522; }"
        )
        dismiss_btn.clicked.connect(lambda: _on_dismiss(hud, player))
        btn_layout.addWidget(dismiss_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        hud.show()

        # Ses döngüsü (10 kez)
        def beep_loop(count=10):
            if count > 0 and hud.isVisible():
                try:
                    winsound.Beep(900, 400)
                except:
                    pass
                QTimer.singleShot(600, lambda: beep_loop(count - 1))

        beep_loop(10)

        # 60 saniye sonra otomatik kapat
        QTimer.singleShot(60000, lambda: hud.close() if hud.isVisible() else None)

    except Exception as e:
        print(f"Alarm hatası: {e}")


def _on_snooze(hud, root, player, snooze_minutes):
    """Erteleme butonu."""
    if player:
        player.write_log(f"SYS: ⏰ Alarm {snooze_minutes} dakika ertelendi.")
    hud.close()
    new_time = (datetime.datetime.now() + datetime.timedelta(minutes=snooze_minutes)).strftime("%H:%M")
    threading.Thread(target=_alarm_thread, args=(new_time, root, player, snooze_minutes), daemon=True).start()
    _show_snooze_confirmation(root, snooze_minutes)


def _on_dismiss(hud, player):
    """Kapatma butonu."""
    if player:
        player.write_log("SYS: ✅ Alarm kapatıldı.")
    hud.close()


def _show_snooze_confirmation(root, minutes: int):
    """Erteleme onayı için küçük bir bildirim gösterir."""
    try:
        parent = root if isinstance(root, QWidget) else None
        hud = QWidget(parent)
        hud.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        hud.setWindowOpacity(0.9)
        hud.setGeometry(10, 70, 250, 60)
        hud.setStyleSheet("background-color: #333;")

        layout = QVBoxLayout(hud)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(f"⏰ Alarm {minutes} dakika ertelendi.")
        label.setStyleSheet("color: #ffcc00; font-family: 'Courier New'; font-size: 10px;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        hud.show()
        QTimer.singleShot(2000, hud.close)
    except:
        pass


def morning_alarm(parameters: Optional[dict] = None, player=None, root=None) -> str:
    params = parameters or {}
    target_time = params.get("time", "").strip()
    snooze_minutes = params.get("snooze", 5)

    if not target_time or ":" not in target_time:
        return "Alarm kurabilmem için lütfen saati (Örneğin 07:30) şeklinde belirtin."

    hour, minute = _parse_time(target_time)
    if hour is None:
        return "Geçersiz saat formatı. Lütfen HH:MM (00:00 ile 23:59 arası) girin."

    now = datetime.datetime.now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    day_info = "yarın" if target <= now else "bugün"
    if target <= now:
        target += datetime.timedelta(days=1)

    if player:
        player.write_log(f"SYS: 🌅 Sabah alarmı kuruluyor -> {target_time} ({day_info})")

    try:
        threading.Thread(target=_alarm_thread, args=(target_time, root, player, snooze_minutes), daemon=True).start()
        return f"Sabah alarmı {target_time} için {day_info} {target.strftime('%H:%M')}'de çalacak şekilde ayarlandı patron. Erteleme süresi {snooze_minutes} dakika. İyi uykular dilerim."
    except Exception as exc:
        if player:
            player.write_log(f"SYS: Alarm kurma hatası: {exc}")
        return "Sabah alarmını kurarken bir arıza meydana geldi."