# actions/system_monitor.py
# J.A.R.V.I.S. Sistem Monitörü - Detaylı Donanım Takibi

import psutil
import platform
import tkinter as tk
from datetime import datetime
from typing import Optional, Dict

def system_status(parameters: Optional[Dict] = None, player=None, speak=None) -> str:
    """
    Sistem durumunu analiz eder ve raporlar.
    
    Parametreler:
        detailed (bool): Detaylı rapor (sıcaklık, batarya, ağ) varsayılan: False
        alert_threshold (int): CPU yüzdesi eşiği (varsayılan: 80)
    """
    params = parameters or {}
    detailed = params.get("detailed", False)
    alert_threshold = int(params.get("alert_threshold", 80))
    
    if player:
        player.write_log("SYS: 📊 Sistem monitörü analiz yapıyor...")
    
    try:
        # Temel veriler
        cpu_percent = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # CPU detayları (çekirdek bazlı)
        cpu_per_core = psutil.cpu_percent(percpu=True)
        cpu_freq = psutil.cpu_freq()
        
        # Rapor metni oluştur
        report_lines = []
        
        # Uyarı kontrolü
        warnings = []
        if cpu_percent > alert_threshold:
            warnings.append(f"⚠️ CPU kullanımı yüksek: %{cpu_percent}")
        if ram.percent > 90:
            warnings.append(f"⚠️ RAM kritik seviyede: %{ram.percent}")
        if disk.percent > 95:
            warnings.append(f"⚠️ Disk alanı çok düşük: %{disk.percent}")
        
        # Temel rapor
        report_lines.append(f"🖥️ İşlemci: %{cpu_percent} | RAM: %{ram.percent} | Disk: %{disk.percent}")
        
        if detailed:
            # Detaylı CPU
            report_lines.append(f"\n📊 CPU Çekirdekleri:")
            for i, core in enumerate(cpu_per_core):
                report_lines.append(f"   Çekirdek {i}: %{core}")
            if cpu_freq:
                report_lines.append(f"⚡ Frekans: {cpu_freq.current:.0f} MHz (max: {cpu_freq.max:.0f} MHz)")
            
            # RAM detayı
            ram_gb = ram.total / (1024**3)
            used_gb = ram.used / (1024**3)
            report_lines.append(f"💾 RAM: {used_gb:.1f}/{ram_gb:.1f} GB kullanımda")
            
            # Disk detayı
            disk_gb = disk.total / (1024**3)
            free_gb = disk.free / (1024**3)
            report_lines.append(f"💿 Disk: {free_gb:.1f}/{disk_gb:.1f} GB boş")
            
            # Batarya bilgisi (varsa)
            battery = psutil.sensors_battery()
            if battery:
                percent = battery.percent
                plugged = "Şarjda" if battery.power_plugged else "Pilde"
                report_lines.append(f"🔋 Batarya: %{percent} ({plugged})")
            
            # Ağ bilgisi
            net_io = psutil.net_io_counters()
            sent_mb = net_io.bytes_sent / (1024**2)
            recv_mb = net_io.bytes_recv / (1024**2)
            report_lines.append(f"🌐 Ağ: ↓{recv_mb:.1f} MB / ↑{sent_mb:.1f} MB (toplam)")
            
            # Sistem bilgisi
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            report_lines.append(f"⏱️ Çalışma süresi: {days}g {hours}s {minutes}d")
            report_lines.append(f"🖥️ Sistem: {platform.system()} {platform.release()}")
        
        # Uyarıları ekle
        if warnings:
            report_lines.append("\n" + "\n".join(warnings))
        
        final_report = "\n".join(report_lines)
        
        # HUD göster (opsiyonel)
        if player and hasattr(player, "root") and player.root:
            try:
                hud = tk.Toplevel(player.root)
                hud.overrideredirect(True)
                hud.attributes("-topmost", True, "-alpha", 0.92)
                hud.geometry("400x180+15+15")
                hud.configure(bg="#0a0a2a")
                
                tk.Label(hud, text="📊 SİSTEM DURUMU", font=("Orbitron", 11, "bold"),
                         fg="#00ffcc", bg="#0a0a2a").pack(pady=5)
                
                # Kısa rapor için Label
                short_report = f"CPU: %{cpu_percent} | RAM: %{ram.percent} | Disk: %{disk.percent}"
                tk.Label(hud, text=short_report, font=("Consolas", 10),
                         fg="white", bg="#0a0a2a").pack(pady=5)
                
                if warnings:
                    warn_color = "#ff6666"
                    tk.Label(hud, text=warnings[0], font=("Segoe UI", 9),
                             fg=warn_color, bg="#0a0a2a").pack(pady=2)
                
                player.root.after(4000, lambda: hud.destroy() if hud.winfo_exists() else None)
            except Exception as e:
                if player:
                    player.write_log(f"SYS: Monitör HUD hatası: {e}")
        
        # Sesli çıktı (isteğe bağlı)
        if speak:
            # Kısa ve öz sesli mesaj
            short_msg = f"Sistem durumu: İşlemci yüzde {cpu_percent}, RAM yüzde {ram.percent}"
            if warnings:
                short_msg += f". Uyarı: {warnings[0]}"
            speak(short_msg)
        
        return final_report
        
    except Exception as e:
        error_msg = f"Sistem verileri okunamadı: {str(e)}"
        if player:
            player.write_log(f"SYS: Sistem durum hatası: {e}")
        return error_msg