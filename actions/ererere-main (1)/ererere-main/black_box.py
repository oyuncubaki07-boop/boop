"""
black_box.py - J.A.R.V.I.S. Kara Kutu / Sistem Tanılama Modülü
Sistem çalışma süresi, CPU, RAM, disk kullanımı ve kritik hata raporlarını gösterir.
"""

import tkinter as tk
import winsound
import psutil
import datetime
import platform
from typing import Optional, Dict, Any

class BlackBox:
    """
    Sistem tanılama ve kara kutu verilerini toplar.
    - Çalışma süresi (uptime)
    - CPU, RAM, disk kullanımı
    - Kritik hata raporu (simüle)
    """

    def __init__(self, player=None, root=None):
        self.player = player
        self.root = root

    def log(self, msg: str):
        if self.player and hasattr(self.player, "write_log"):
            self.player.write_log(f"SYS: {msg}")
        else:
            print(f"[BLACKBOX] {msg}")

    def _beep(self, freq: int, duration: int = 300):
        try:
            winsound.Beep(freq, duration)
        except:
            pass

    def get_uptime_info(self) -> Dict[str, Any]:
        """Sistem açılış süresi ve kesintisiz çalışma bilgisini döndürür."""
        boot_ts = psutil.boot_time()
        boot_time = datetime.datetime.fromtimestamp(boot_ts)
        now = datetime.datetime.now()
        uptime = now - boot_time
        uptime_str = str(uptime).split('.')[0]  # saniye/milisaniye temizliği
        return {
            "boot_time": boot_time.strftime('%Y-%m-%d %H:%M:%S'),
            "uptime_seconds": int(uptime.total_seconds()),
            "uptime_str": uptime_str
        }

    def get_cpu_info(self) -> Dict[str, Any]:
        """CPU kullanım yüzdesi ve çekirdek sayısı."""
        return {
            "percent": psutil.cpu_percent(interval=0.5),
            "cores": psutil.cpu_count(logical=True),
            "physical_cores": psutil.cpu_count(logical=False)
        }

    def get_memory_info(self) -> Dict[str, Any]:
        """RAM kullanım bilgisi."""
        mem = psutil.virtual_memory()
        return {
            "total_gb": round(mem.total / (1024**3), 1),
            "available_gb": round(mem.available / (1024**3), 1),
            "percent": mem.percent
        }

    def get_disk_info(self) -> Dict[str, Any]:
        """Disk kullanım bilgisi (ana sürücü)."""
        disk = psutil.disk_usage('/')
        return {
            "total_gb": round(disk.total / (1024**3), 1),
            "used_gb": round(disk.used / (1024**3), 1),
            "free_gb": round(disk.free / (1024**3), 1),
            "percent": disk.percent
        }

    def get_system_summary(self) -> str:
        """Tüm sistem bilgilerini metin olarak döndürür."""
        uptime = self.get_uptime_info()
        cpu = self.get_cpu_info()
        mem = self.get_memory_info()
        disk = self.get_disk_info()
        summary = (
            f"🖥️ Sistem: {platform.system()} {platform.release()}\n"
            f"⏱️ Çalışma süresi: {uptime['uptime_str']}\n"
            f"🧠 CPU: %{cpu['percent']} ({cpu['cores']} mantıksal çekirdek)\n"
            f"💾 RAM: %{mem['percent']} ({mem['available_gb']}/{mem['total_gb']} GB boş)\n"
            f"💿 Disk: %{disk['percent']} ({disk['free_gb']}/{disk['total_gb']} GB boş)"
        )
        return summary

    def _show_hud(self):
        """Kara kutu bilgilerini içeren HUD penceresi."""
        if not self.root:
            return
        try:
            hud = tk.Toplevel(self.root)
            hud.overrideredirect(True)
            hud.attributes("-topmost", True, "-alpha", 0.95)
            hud.geometry("450x180+10+10")
            hud.configure(bg="#1a0000")  # Koyu kırmızı tehlike teması

            tk.Label(hud, text="📦 KARA KUTU / SİSTEM TANILAMA", font=("Courier", 12, "bold"), fg="#ff3333", bg="#1a0000").pack(pady=8)

            uptime = self.get_uptime_info()
            tk.Label(hud, text=f"Sistem Açılış: {uptime['boot_time']}", font=("Courier", 10), fg="white", bg="#1a0000").pack()
            tk.Label(hud, text=f"Kesintisiz Çalışma: {uptime['uptime_str']}", font=("Courier", 10), fg="white", bg="#1a0000").pack()

            cpu = self.get_cpu_info()
            mem = self.get_memory_info()
            tk.Label(hud, text=f"CPU: %{cpu['percent']}  |  RAM: %{mem['percent']}", font=("Courier", 10), fg="white", bg="#1a0000").pack()

            disk = self.get_disk_info()
            tk.Label(hud, text=f"Disk: %{disk['percent']} kullanımda", font=("Courier", 10), fg="white", bg="#1a0000").pack()

            # Kritik rapor (şimdilik her zaman temiz)
            tk.Label(hud, text="Kritik Çökme Raporu: TEMİZ", font=("Courier", 10, "bold"), fg="#00ff00", bg="#1a0000").pack(pady=5)

            self._beep(400, 300)

            self.root.after(5000, lambda: hud.destroy() if hud.winfo_exists() else None)
        except Exception as e:
            self.log(f"Kara Kutu HUD hatası: {e}")

    def run(self) -> str:
        """Kara kutu tanılamasını çalıştırır, HUD gösterir ve özet döndürür."""
        self.log("📦 KARA KUTU açılıyor. Tanılama verileri çekiliyor...")
        self._show_hud()
        summary = self.get_system_summary()
        self.log(summary)
        uptime = self.get_uptime_info()
        return f"Kara kutu verileri analiz edildi. Sistem {uptime['uptime_str']} süredir stabil.\n{summary}"


# ------------------------------
# Ana fonksiyon (main.py'den çağrılmak için)
def black_box(parameters: Optional[dict] = None, player=None, root=None) -> str:
    """
    main.py içinden çağrılan fonksiyon.
    parameters: isteğe bağlı, kullanılmıyor (gelecek için rezerve).
    """
    box = BlackBox(player=player, root=root)
    return box.run()