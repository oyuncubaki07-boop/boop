# actions/system_monitor.py
# J.A.R.V.I.S. Sistem Monitörü — PyQt6

import psutil
import platform
from datetime import datetime
from typing import Optional, Dict

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer


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
        
        # HUD göster (PyQt6)
        if player and hasattr(player, "win"):
            QTimer.singleShot(0, lambda: _show_hud(
                player.win, cpu_percent, ram.percent, disk.percent, warnings
            ))
        
        # Sesli çıktı (isteğe bağlı)
        if speak:
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


def _show_hud(root, cpu_percent, ram_percent, disk_percent, warnings):
    """PyQt6 HUD penceresi gösterir."""
    if not root or not isinstance(root, QWidget):
        return
    try:
        hud = QWidget(root)
        hud.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        hud.setWindowOpacity(0.92)
        hud.setGeometry(15, 15, 400, 180)
        hud.setStyleSheet("background-color: #0a0a2a;")

        layout = QVBoxLayout(hud)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        title = QLabel("📊 SİSTEM DURUMU")
        title.setStyleSheet("color: #00ffcc; font-family: 'Orbitron', 'Courier New'; font-size: 11px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        short_report = f"CPU: %{cpu_percent} | RAM: %{ram_percent} | Disk: %{disk_percent}"
        report_label = QLabel(short_report)
        report_label.setStyleSheet("color: white; font-family: 'Consolas'; font-size: 10px;")
        report_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(report_label)

        if warnings:
            warn_label = QLabel(warnings[0])
            warn_label.setStyleSheet("color: #ff6666; font-family: 'Segoe UI'; font-size: 9px;")
            warn_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(warn_label)

        hud.show()
        QTimer.singleShot(4000, hud.close)
    except:
        pass