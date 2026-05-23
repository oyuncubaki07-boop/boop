import threading
import time
import datetime
import re
import platform
from typing import Optional, Union

from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QApplication
from PyQt6.QtCore import Qt, QTimer

# Cross-platform ses desteği
_OS = platform.system()
if _OS == "Windows":
    import winsound

def _parse_time_input(time_str: str) -> Optional[int]:
    """
    Zaman girdisini saniyeye çevirir.
    Desteklenen formatlar:
    - "5" -> 5 dakika (300 saniye)
    - "5 dakika" -> 5 dakika
    - "2 saat" -> 2 saat (7200 saniye)
    - "1.5 saat" -> 1.5 saat
    - "10:30" -> bugün saat 10:30'a kalan süre
    - "14:45:00" -> bugün 14:45:00'a kalan süre
    - "2025-12-31 23:59" -> belirtilen tarihe kalan süre
    """
    time_str = time_str.strip().lower()
    
    # Dakika olarak direkt sayı (sadece rakam)
    if time_str.isdigit():
        return int(time_str) * 60
    
    # Dakika belirtilmiş: "5 dakika", "10 dk", "15 minute"
    match = re.match(r'(\d+(?:\.\d+)?)\s*(?:dk|dakika|minute|minutes|min)', time_str)
    if match:
        minutes = float(match.group(1))
        return int(minutes * 60)
    
    # Saat belirtilmiş: "2 saat", "1.5 hour"
    match = re.match(r'(\d+(?:\.\d+)?)\s*(?:saat|hour|hours|hr)', time_str)
    if match:
        hours = float(match.group(1))
        return int(hours * 3600)
    
    # Saat:dakika formatı: "10:30", "14:45:00"
    match = re.match(r'(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?', time_str)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        second = int(match.group(3)) if match.group(3) else 0
        now = datetime.datetime.now()
        target = now.replace(hour=hour, minute=minute, second=second, microsecond=0)
        if target <= now:
            target += datetime.timedelta(days=1)
        return int((target - now).total_seconds())
    
    # Tarih ve saat: "2025-12-31 23:59"
    try:
        target = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        now = datetime.datetime.now()
        if target <= now:
            return None
        return int((target - now).total_seconds())
    except ValueError:
        pass
    
    return None

def _reminder_thread(delay_seconds: int, message: str, root, player, repeat: bool = False):
    """Arka planda çalışan hatırlatıcı thread'i"""
    if delay_seconds <= 0:
        delay_seconds = 1
    time.sleep(delay_seconds)
    
    # Ana thread'de bildirim göster (PyQt6)
    if root:
        QTimer.singleShot(0, lambda: _show_reminder_hud(message, root, repeat))
    
    # Log mesajı
    if player:
        player.write_log(f"SYS: ⏰ HATIRLATMA: {message}")
    
    # Eğer tekrarlı hatırlatıcı ise her 5 dakikada bir tekrarla
    if repeat:
        while True:
            time.sleep(300)  # 5 dakika
            if root:
                QTimer.singleShot(0, lambda: _show_reminder_hud(f"[TEKRAR] {message}", root, repeat=False))

def _show_reminder_hud(message: str, root, repeat: bool = False):
    """Hatırlatıcı penceresini gösterir (PyQt6)"""
    try:
        parent = root if isinstance(root, QWidget) else None
        hud = QWidget(parent)
        hud.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        hud.setWindowOpacity(0.95)
        hud.setGeometry(10, 10, 450, 120)
        hud.setStyleSheet("background-color: #001a33;")

        layout = QVBoxLayout(hud)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        title_color = "#ff9900" if repeat else "#00ccff"
        title_text = "⏰ TEKRARLI HATIRLATICI" if repeat else "⏰ HATIRLATICI"
        
        title = QLabel(title_text)
        title.setStyleSheet(f"color: {title_color}; font-family: 'Courier New'; font-size: 12px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        msg_label = QLabel(message)
        msg_label.setStyleSheet("color: white; font-family: 'Courier New'; font-size: 10px;")
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)

        close_btn = QPushButton("Kapat")
        close_btn.setStyleSheet("QPushButton { background-color: #333; color: white; border: none; padding: 5px 15px; }")
        close_btn.clicked.connect(hud.close)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        hud.show()

        # Alarm sesi (Cross-platform)
        try:
            if _OS == "Windows":
                for _ in range(3):
                    winsound.Beep(800, 200)
                    time.sleep(0.1)
            else:
                print('\a', end='', flush=True) 
        except:
            pass
        
        # Otomatik kapanma (15 saniye sonra)
        QTimer.singleShot(15000, hud.close)
    except Exception as e:
        print(f"[Reminder] HUD hatası: {e}")

def reminder(parameters: Optional[dict] = None, response=None, player=None, root=None, session_memory=None) -> str:
    """
    Hatırlatıcı kurar.
    Parametreler:
    - message: Hatırlatma mesajı (zorunlu)
    - minutes: Dakika cinsinden süre (isteğe bağlı, alternatif)
    - time: Zaman ifadesi (isteğe bağlı, örn: "10:30", "5 dakika", "2 saat")
    - repeat: True ise tekrarlı hatırlatıcı (her 5 dakikada bir)
    """
    params = parameters or {}
    message = params.get("message", "").strip()
    if not message:
        return "Hatırlatıcı için bir mesaj belirtmelisiniz patron."
    
    # Süre hesaplama
    delay_seconds = None
    
    # Önce 'minutes' parametresine bak
    minutes = params.get("minutes", 0)
    if isinstance(minutes, (int, float)) and minutes > 0:
        delay_seconds = int(minutes * 60)
    
    # Eğer 'time' parametresi varsa onu kullan
    time_str = params.get("time", "")
    if time_str and delay_seconds is None:
        delay_seconds = _parse_time_input(str(time_str))
        if delay_seconds is None:
            return f"'{time_str}' zaman formatını anlayamadım. Örnek: '5 dakika', '2 saat', '10:30' veya '2025-12-31 23:59'."
    
    # Hala süre yoksa hata
    if delay_seconds is None or delay_seconds <= 0:
        return "Lütfen geçerli bir süre belirtin (örnek: 'minutes': 5, 'time': '10:30' veya '5 dakika')."
    
    repeat = params.get("repeat", False)
    
    if player:
        player.write_log(f"SYS: ⏰ Hatırlatıcı kuruldu: {message} ({delay_seconds} sn sonra)")
    
    # Thread başlat
    threading.Thread(target=_reminder_thread, args=(delay_seconds, message, root, player, repeat), daemon=True).start()
    
    # Süreyi insan okuyabilir formata çevir
    if delay_seconds < 60:
        time_desc = f"{delay_seconds} saniye"
    elif delay_seconds < 3600:
        minutes_val = delay_seconds // 60
        time_desc = f"{minutes_val} dakika"
    else:
        hours_val = delay_seconds // 3600
        minutes_rem = (delay_seconds % 3600) // 60
        if minutes_rem > 0:
            time_desc = f"{hours_val} saat {minutes_rem} dakika"
        else:
            time_desc = f"{hours_val} saat"
    
    repeat_msg = " (tekrarlı)" if repeat else ""
    return f"Tamamdır patron, {time_desc} sonra size '{message}' konusunu hatırlatacağım{repeat_msg}."