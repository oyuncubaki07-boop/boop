"""
morning_briefing.py - J.A.R.V.I.S. Sabah Raporu Modülü (PyQt6)
Günaydın mesajı, sistem durumu, hava durumu, yaklaşan etkinlikler ve günlük özet.
"""

import datetime
import time
import psutil
import winsound
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer


def get_base_dir():
    if getattr(__import__('sys'), "frozen", False):
        return Path(__import__('sys').executable).parent
    return Path(__file__).resolve().parent.parent


def load_config() -> Dict[str, Any]:
    """Hava durumu API anahtarı gibi yapılandırmaları yükler."""
    base_dir = get_base_dir()
    config_path = base_dir / "config" / "api_keys.json"
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}


def get_weather(city: str = "Istanbul") -> Optional[str]:
    """OpenWeatherMap API'sinden hava durumu bilgisi alır (isteğe bağlı)."""
    config = load_config()
    api_key = config.get("openweather_api_key", "")
    if not api_key:
        return None
    
    try:
        import urllib.request
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=tr"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            temp = data['main']['temp']
            desc = data['weather'][0]['description']
            return f"{city}'de hava {desc}, sıcaklık {temp:.1f}°C."
    except Exception:
        return None


def get_upcoming_events() -> list:
    """Yaklaşan etkinlikleri döndürür."""
    base_dir = get_base_dir()
    events_file = base_dir / "data" / "events.json"
    if events_file.exists():
        try:
            with open(events_file, "r", encoding="utf-8") as f:
                events = json.load(f)
            now = datetime.datetime.now()
            upcoming = []
            for event in events:
                event_date = datetime.datetime.strptime(event['date'], "%Y-%m-%d")
                if event_date >= now:
                    upcoming.append(event)
            return upcoming[:3]
        except:
            pass
    return []


def show_briefing_hud(root, cpu: float, ram: float, weather: Optional[str], events: list):
    """Sabah raporu HUD penceresi (PyQt6)."""
    try:
        parent = root if isinstance(root, QWidget) else None
        hud = QWidget(parent)
        hud.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        hud.setWindowOpacity(0.92)
        hud.setGeometry(10, 10, 450, 250)
        hud.setStyleSheet("background-color: #001a33;")

        layout = QVBoxLayout(hud)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Başlık
        title = QLabel("🌅 GÜNAYDIN PATRON")
        title.setStyleSheet("color: #ffcc00; font-family: 'Courier New'; font-size: 14px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Saat ve tarih
        now = datetime.datetime.now()
        saat = now.strftime("%H:%M")
        tarih = now.strftime("%d.%m.%Y")
        date_label = QLabel(f"Saat: {saat}  |  Tarih: {tarih}")
        date_label.setStyleSheet("color: white; font-family: 'Courier New'; font-size: 10px;")
        date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(date_label)

        # Sistem durumu
        sys_label = QLabel(f"🖥️ Sistem: CPU %{cpu:.0f}  |  RAM %{ram:.0f}")
        sys_label.setStyleSheet("color: #00ffff; font-family: 'Courier New'; font-size: 10px;")
        sys_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sys_label)

        # Hava durumu
        if weather:
            weather_label = QLabel(f"🌤️ {weather}")
            weather_label.setStyleSheet("color: #99ff99; font-family: 'Courier New'; font-size: 9px;")
            weather_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            weather_label.setWordWrap(True)
            layout.addWidget(weather_label)

        # Yaklaşan etkinlikler
        if events:
            ev_title = QLabel("📅 Bugün / Yakında:")
            ev_title.setStyleSheet("color: #ffaa66; font-family: 'Courier New'; font-size: 10px; font-weight: bold;")
            layout.addWidget(ev_title)
            for ev in events[:2]:
                ev_label = QLabel(f"   • {ev['date']}: {ev['title']}")
                ev_label.setStyleSheet("color: white; font-family: 'Courier New'; font-size: 9px;")
                ev_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
                layout.addWidget(ev_label)
        else:
            no_event = QLabel("📅 Bugün için planlanmış etkinlik yok.")
            no_event.setStyleSheet("color: gray; font-family: 'Courier New'; font-size: 9px;")
            no_event.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(no_event)

        # Motivasyon
        motivation = QLabel("Başarılı bir gün geçirmen dileğiyle! 🚀")
        motivation.setStyleSheet("color: #ffcc99; font-family: 'Courier New'; font-size: 9px; font-style: italic;")
        motivation.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(motivation)

        hud.show()

        try:
            winsound.Beep(500, 300)
        except:
            pass

        QTimer.singleShot(8000, hud.close)
    except Exception as e:
        print(f"HUD hatası: {e}")


def morning_briefing(parameters: Optional[dict] = None, player=None, root=None) -> str:
    """
    Sabah raporu oluşturur.
    parameters: {
        "city": "Istanbul",
        "silent": False,
        "include_weather": True,
        "include_events": True
    }
    """
    params = parameters or {}
    city = params.get("city", "Istanbul")
    silent = params.get("silent", False)
    include_weather = params.get("include_weather", True)
    include_events = params.get("include_events", True)
    
    if player:
        player.write_log("SYS: 🌅 Sabah protokolü başlatılıyor...")
    
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory().percent
    now = datetime.datetime.now()
    saat = now.strftime("%H:%M")
    tarih = now.strftime("%d/%m/%Y")
    
    weather = None
    if include_weather:
        weather = get_weather(city)
    
    events = []
    if include_events:
        events = get_upcoming_events()
    
    if not silent and root:
        show_briefing_hud(root, cpu, ram, weather, events)
    
    summary = f"Günaydın patron. Saat {saat}, {tarih}. Sistem durumu: İşlemci yüzde {cpu:.0f}, bellek yüzde {ram:.0f}."
    if weather:
        summary += f" {weather}"
    if events:
        summary += " Bugün planlananlar: " + ". ".join([f"{e['date']} {e['title']}" for e in events[:2]])
    summary += " Başarılı bir gün geçirmen dileğiyle. Sizin için ne yapabilirim?"
    
    return summary