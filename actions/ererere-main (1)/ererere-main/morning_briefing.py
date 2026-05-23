"""
morning_briefing.py - J.A.R.V.I.S. Sabah Raporu Modülü
Günaydın mesajı, sistem durumu, hava durumu, yaklaşan etkinlikler ve günlük özet.
"""

import datetime
import time
import tkinter as tk
import psutil
import winsound
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

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
        import json
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
    """Yaklaşan etkinlikleri döndürür (örnek olarak bir JSON dosyasından okuyabiliriz)."""
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
            return upcoming[:3]  # En fazla 3 etkinlik
        except:
            pass
    return []

def show_briefing_hud(root, cpu: float, ram: float, weather: Optional[str], events: list):
    """Sabah raporu HUD penceresi."""
    try:
        hud = tk.Toplevel(root)
        hud.overrideredirect(True)
        hud.attributes("-topmost", True, "-alpha", 0.92)
        hud.geometry("450x250+10+10")
        hud.configure(bg="#001a33")
        
        # Başlık
        tk.Label(hud, text="🌅 GÜNAYDIN PATRON", font=("Courier", 14, "bold"), fg="#ffcc00", bg="#001a33").pack(pady=8)
        
        # Saat ve tarih
        now = datetime.datetime.now()
        saat = now.strftime("%H:%M")
        tarih = now.strftime("%d.%m.%Y")
        tk.Label(hud, text=f"Saat: {saat}  |  Tarih: {tarih}", font=("Courier", 10), fg="white", bg="#001a33").pack()
        
        # Sistem durumu
        tk.Label(hud, text=f"🖥️ Sistem: CPU %{cpu:.0f}  |  RAM %{ram:.0f}", font=("Courier", 10), fg="#00ffff", bg="#001a33").pack(pady=5)
        
        # Hava durumu
        if weather:
            tk.Label(hud, text=f"🌤️ {weather}", font=("Courier", 9), fg="#99ff99", bg="#001a33", wraplength=420).pack(pady=3)
        
        # Yaklaşan etkinlikler
        if events:
            tk.Label(hud, text="📅 Bugün / Yakında:", font=("Courier", 10, "bold"), fg="#ffaa66", bg="#001a33").pack(pady=5)
            for ev in events[:2]:
                tk.Label(hud, text=f"   • {ev['date']}: {ev['title']}", font=("Courier", 9), fg="white", bg="#001a33").pack(anchor="w", padx=15)
        else:
            tk.Label(hud, text="📅 Bugün için planlanmış etkinlik yok.", font=("Courier", 9), fg="gray", bg="#001a33").pack(pady=3)
        
        # Motivasyon mesajı
        motivation = "Başarılı bir gün geçirmen dileğiyle! 🚀"
        tk.Label(hud, text=motivation, font=("Courier", 9, "italic"), fg="#ffcc99", bg="#001a33").pack(pady=8)
        
        # Sesli uyarı
        try:
            winsound.Beep(500, 300)
        except:
            pass
        
        # Otomatik kapanma (8 saniye)
        root.after(8000, lambda: hud.destroy() if hud.winfo_exists() else None)
    except Exception as e:
        print(f"HUD hatası: {e}")

def morning_briefing(parameters: Optional[dict] = None, player=None, root=None) -> str:
    """
    Sabah raporu oluşturur.
    parameters: {
        "city": "Istanbul",   # Hava durumu için şehir
        "silent": False,      # HUD gösterme, sadece metin döndür
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
    
    # Sistem verileri
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory().percent
    now = datetime.datetime.now()
    saat = now.strftime("%H:%M")
    tarih = now.strftime("%d/%m/%Y")
    
    # Hava durumu (isteğe bağlı)
    weather = None
    if include_weather:
        weather = get_weather(city)
    
    # Yaklaşan etkinlikler (isteğe bağlı)
    events = []
    if include_events:
        events = get_upcoming_events()
    
    # HUD gösterimi
    if not silent and root:
        show_briefing_hud(root, cpu, ram, weather, events)
    
    # Sesli okuma için metin oluştur
    summary = f"Günaydın patron. Saat {saat}, {tarih}. Sistem durumu: İşlemci yüzde {cpu:.0f}, bellek yüzde {ram:.0f}."
    if weather:
        summary += f" {weather}"
    if events:
        summary += " Bugün planlananlar: " + ". ".join([f"{e['date']} {e['title']}" for e in events[:2]])
    summary += " Başarılı bir gün geçirmen dileğiyle. Sizin için ne yapabilirim?"
    
    return summary