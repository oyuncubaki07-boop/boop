"""
hologram_hud.py - J.A.R.V.I.S. HoloGrafik Sistem Arayüzü (HUD)
Sistemin anlık CPU, RAM, disk, ağ, batarya ve çalışma süresi bilgilerini holografik bir panelde gösterir.
"""

import tkinter as tk
import psutil
import platform
from datetime import datetime
import winsound
import threading
import time
from typing import Optional

class HologramHUD:
    """Holografik HUD penceresini yöneten sınıf."""

    def __init__(self, root, player=None, auto_refresh: bool = False, refresh_interval: int = 2000):
        self.root = root
        self.player = player
        self.auto_refresh = auto_refresh
        self.refresh_interval = refresh_interval
        self.hud = None
        self.running = False
        self.widgets = {}

    def log(self, msg: str):
        if self.player and hasattr(self.player, "write_log"):
            self.player.write_log(f"SYS: {msg}")
        else:
            print(f"[HUD] {msg}")

    def get_system_info(self):
        """Sistem bilgilerini toplar."""
        try:
            cpu = psutil.cpu_percent(interval=0.2)
            ram = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            uptime_str = str(uptime).split('.')[0]
            
            # Ağ bilgisi (basit)
            net_io = psutil.net_io_counters()
            net_sent = net_io.bytes_sent / (1024 * 1024)  # MB
            net_recv = net_io.bytes_recv / (1024 * 1024)
            
            # Batarya (varsa)
            battery = psutil.sensors_battery()
            battery_percent = battery.percent if battery else None
            battery_plugged = battery.power_plugged if battery else None
            
            return {
                "cpu": cpu,
                "ram": ram,
                "disk": disk,
                "uptime": uptime_str,
                "net_sent": net_sent,
                "net_recv": net_recv,
                "battery": battery_percent,
                "battery_plugged": battery_plugged,
                "time": datetime.now().strftime("%H:%M:%S - %d.%m.%Y"),
                "hostname": platform.node(),
                "os": f"{platform.system()} {platform.release()}"
            }
        except Exception as e:
            self.log(f"Sistem bilgisi alınamadı: {e}")
            return None

    def create_hud(self):
        """HUD penceresini oluşturur."""
        if self.hud and self.hud.winfo_exists():
            return
        self.hud = tk.Toplevel(self.root)
        self.hud.overrideredirect(True)
        self.hud.attributes("-topmost", True, "-alpha", 0.92)
        self.hud.geometry("850x480+10+10")
        self.hud.configure(bg="#000d1a")
        self.hud.bind("<Escape>", lambda e: self.close())
        
        # Başlık çubuğu (sahte, taşıma için)
        title_bar = tk.Frame(self.hud, bg="#002244", height=30)
        title_bar.pack(fill="x")
        title_bar.bind("<Button-1>", self.start_move)
        title_bar.bind("<B1-Motion>", self.on_move)
        
        tk.Label(title_bar, text="🎛️ J.A.R.V.I.S. HOLOGRAM HUD", font=("Courier", 12, "bold"), fg="#00ffff", bg="#002244").pack(side="left", padx=10)
        close_btn = tk.Label(title_bar, text="✖", font=("Arial", 12, "bold"), fg="white", bg="#002244", cursor="hand2")
        close_btn.pack(side="right", padx=10)
        close_btn.bind("<Button-1>", lambda e: self.close())
        
        # Ana içerik çerçevesi
        main_frame = tk.Frame(self.hud, bg="#000d1a")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Sol taraf (sistem özeti)
        left_frame = tk.Frame(main_frame, bg="#000d1a")
        left_frame.pack(side="left", fill="both", expand=True)
        
        self.widgets["time"] = tk.Label(left_frame, font=("Courier", 12), fg="white", bg="#000d1a")
        self.widgets["time"].pack(pady=5)
        
        self.widgets["host"] = tk.Label(left_frame, font=("Courier", 10), fg="#aaaaaa", bg="#000d1a")
        self.widgets["host"].pack()
        
        self.widgets["os"] = tk.Label(left_frame, font=("Courier", 10), fg="#aaaaaa", bg="#000d1a")
        self.widgets["os"].pack()
        
        self.widgets["uptime"] = tk.Label(left_frame, font=("Courier", 10), fg="#cccccc", bg="#000d1a")
        self.widgets["uptime"].pack(pady=5)
        
        tk.Label(left_frame, text="─" * 30, fg="#00ffff", bg="#000d1a").pack(pady=5)
        
        # CPU
        cpu_frame = tk.Frame(left_frame, bg="#000d1a")
        cpu_frame.pack(fill="x", pady=3)
        tk.Label(cpu_frame, text="CPU:", font=("Courier", 11, "bold"), fg="#00ffcc", bg="#000d1a").pack(side="left")
        self.widgets["cpu"] = tk.Label(cpu_frame, font=("Courier", 11, "bold"), bg="#000d1a")
        self.widgets["cpu"].pack(side="left", padx=5)
        
        # RAM
        ram_frame = tk.Frame(left_frame, bg="#000d1a")
        ram_frame.pack(fill="x", pady=3)
        tk.Label(ram_frame, text="RAM:", font=("Courier", 11, "bold"), fg="#00ffcc", bg="#000d1a").pack(side="left")
        self.widgets["ram"] = tk.Label(ram_frame, font=("Courier", 11, "bold"), bg="#000d1a")
        self.widgets["ram"].pack(side="left", padx=5)
        
        # Disk
        disk_frame = tk.Frame(left_frame, bg="#000d1a")
        disk_frame.pack(fill="x", pady=3)
        tk.Label(disk_frame, text="DISK:", font=("Courier", 11, "bold"), fg="#00ffcc", bg="#000d1a").pack(side="left")
        self.widgets["disk"] = tk.Label(disk_frame, font=("Courier", 11, "bold"), bg="#000d1a")
        self.widgets["disk"].pack(side="left", padx=5)
        
        # Ağ
        net_frame = tk.Frame(left_frame, bg="#000d1a")
        net_frame.pack(fill="x", pady=3)
        tk.Label(net_frame, text="AĞ:", font=("Courier", 11, "bold"), fg="#00ffcc", bg="#000d1a").pack(side="left")
        self.widgets["net"] = tk.Label(net_frame, font=("Courier", 10), bg="#000d1a")
        self.widgets["net"].pack(side="left", padx=5)
        
        # Batarya
        bat_frame = tk.Frame(left_frame, bg="#000d1a")
        bat_frame.pack(fill="x", pady=3)
        tk.Label(bat_frame, text="BATARYA:", font=("Courier", 11, "bold"), fg="#00ffcc", bg="#000d1a").pack(side="left")
        self.widgets["battery"] = tk.Label(bat_frame, font=("Courier", 10), bg="#000d1a")
        self.widgets["battery"].pack(side="left", padx=5)
        
        # Sağ taraf (grafik veya mesaj)
        right_frame = tk.Frame(main_frame, bg="#001a33", width=300)
        right_frame.pack(side="right", fill="both", expand=True, padx=10)
        right_frame.pack_propagate(False)
        
        tk.Label(right_frame, text="🔧 SİSTEM DURUMU", font=("Courier", 12, "bold"), fg="#ffcc00", bg="#001a33").pack(pady=10)
        self.widgets["status"] = tk.Label(right_frame, text="✅ Tüm sistemler çevrimiçi", font=("Courier", 10), fg="#00ff66", bg="#001a33")
        self.widgets["status"].pack(pady=5)
        
        tk.Label(right_frame, text="⚡ AKTİF MODÜLLER", font=("Courier", 10, "bold"), fg="#ffaa66", bg="#001a33").pack(pady=5)
        modules = ["Güvenlik", "Ağ İzleme", "Hafıza", "Otomasyon", "Medya", "Ses"]
        for mod in modules:
            tk.Label(right_frame, text=f"• {mod}", font=("Courier", 9), fg="white", bg="#001a33").pack(anchor="w", padx=15)
        
        # Alt bilgi
        tk.Label(self.hud, text="Hologram HUD | ESC ile kapat", font=("Courier", 8), fg="#666666", bg="#000d1a").pack(side="bottom", pady=5)
        
        # İlk güncelleme
        self.update_info()
        
        # Sesli bildirim
        try:
            winsound.Beep(400, 100)
            winsound.Beep(600, 150)
        except:
            pass
        
        # Otomatik yenileme
        if self.auto_refresh:
            self.running = True
            self._refresh_loop()

    def _refresh_loop(self):
        """Otomatik yenileme döngüsü."""
        if not self.running or not self.hud or not self.hud.winfo_exists():
            return
        self.update_info()
        self.hud.after(self.refresh_interval, self._refresh_loop)

    def update_info(self):
        """Bilgileri günceller."""
        info = self.get_system_info()
        if not info:
            return
        
        # Renk belirleme
        cpu_color = "#ff3333" if info["cpu"] > 80 else ("#ffaa00" if info["cpu"] > 60 else "#00ff00")
        ram_color = "#ff3333" if info["ram"] > 85 else ("#ffaa00" if info["ram"] > 70 else "#00ff00")
        disk_color = "#ff3333" if info["disk"] > 90 else ("#ffaa00" if info["disk"] > 75 else "#00ff00")
        
        self.widgets["time"].config(text=f"🕒 {info['time']}")
        self.widgets["host"].config(text=f"🖥️ {info['hostname']}")
        self.widgets["os"].config(text=f"💿 {info['os']}")
        self.widgets["uptime"].config(text=f"⏱️ Çalışma: {info['uptime']}")
        self.widgets["cpu"].config(text=f"%{info['cpu']:.1f}", fg=cpu_color)
        self.widgets["ram"].config(text=f"%{info['ram']:.1f}", fg=ram_color)
        self.widgets["disk"].config(text=f"%{info['disk']:.1f}", fg=disk_color)
        self.widgets["net"].config(text=f"⬇️ {info['net_recv']:.1f} MB / ⬆️ {info['net_sent']:.1f} MB")
        
        bat_text = "Yok"
        if info["battery"] is not None:
            bat_text = f"%{info['battery']:.0f}"
            if info["battery_plugged"]:
                bat_text += " (Şarjda)"
            else:
                bat_text += " (Pil)"
        self.widgets["battery"].config(text=bat_text)
        
        # Durum mesajı
        if info["cpu"] > 80 or info["ram"] > 85:
            self.widgets["status"].config(text="⚠️ Yüksek sistem yükü!", fg="#ff6666")
        else:
            self.widgets["status"].config(text="✅ Tüm sistemler çevrimiçi", fg="#00ff66")

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.hud.winfo_x() + deltax
        y = self.hud.winfo_y() + deltay
        self.hud.geometry(f"+{x}+{y}")

    def close(self):
        self.running = False
        if self.hud and self.hud.winfo_exists():
            self.hud.destroy()
        self.log("Hologram HUD kapatıldı.")

def hologram_hud(parameters: Optional[dict] = None, player=None, root=None) -> str:
    """
    Holografik HUD'u açar.
    parameters: {
        "auto_refresh": False,   # otomatik yenileme (ms cinsinden refresh_interval)
        "refresh_interval": 2000,
        "duration": 10           # saniye cinsinden otomatik kapanma (0 ise kullanıcı kapatana kadar)
    }
    """
    params = parameters or {}
    auto_refresh = params.get("auto_refresh", False)
    refresh_interval = params.get("refresh_interval", 2000)
    duration = params.get("duration", 10)
    
    if player:
        player.write_log("SYS: 🎛️ Hologram HUD başlatılıyor...")
    
    if not root:
        return "HUD gösterilemedi: ana pencere bulunamadı."
    
    hud_manager = HologramHUD(root, player, auto_refresh, refresh_interval)
    hud_manager.create_hud()
    
    if duration > 0:
        root.after(duration * 1000, lambda: hud_manager.close() if hud_manager.hud and hud_manager.hud.winfo_exists() else None)
    
    return "Holografik sistem arayüzü ekrana yansıtıldı patron. ESC tuşu veya kapatma butonu ile kapatabilirsiniz."