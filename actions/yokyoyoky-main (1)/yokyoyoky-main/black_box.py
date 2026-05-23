"""
black_box.py - J.A.R.V.I.S. Kara Kutu / Sistem Tanılama Modülü (PyQt6)
Sistem çalışma süresi, CPU, RAM, disk kullanımı ve kritik hata raporlarını gösterir.
"""

import winsound
import psutil
import datetime
import platform
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PyQt6.QtCore import Qt, QTimer


class BlackBox:
    """
    Sistem tanılama ve kara kutu verilerini toplar.
    - Çalışma süresi (uptime)
    - CPU, RAM, disk kullanımı
    - Kritik hata raporu (simüle)
    """

    def __init__(self, player=None, root=None):
        self.player = player
        self.root = root          # PyQt6 widget'ı veya None

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
        """Kara kutu bilgilerini içeren PyQt6 HUD penceresi."""
        if not self.root:
            return
        try:
            parent = self.root if isinstance(self.root, QWidget) else None
            hud = QWidget(parent)
            hud.setWindowFlags(
                Qt.WindowType.FramelessWindowHint |
                Qt.WindowType.WindowStaysOnTopHint
            )
            hud.setWindowOpacity(0.95)
            hud.setGeometry(10, 10, 450, 180)
            hud.setStyleSheet("background-color: #1a0000;")  # Koyu kırmızı tehlike teması

            layout = QVBoxLayout(hud)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(4)

            # Başlık
            title_label = QLabel("📦 KARA KUTU / SİSTEM TANILAMA")
            title_label.setStyleSheet("color: #ff3333; font-family: 'Courier New'; font-size: 12px; font-weight: bold;")
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(title_label)

            uptime = self.get_uptime_info()
            # Sistem açılış
            boot_label = QLabel(f"Sistem Açılış: {uptime['boot_time']}")
            boot_label.setStyleSheet("color: white; font-family: 'Courier New'; font-size: 10px;")
            boot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(boot_label)

            # Kesintisiz çalışma
            uptime_label = QLabel(f"Kesintisiz Çalışma: {uptime['uptime_str']}")
            uptime_label.setStyleSheet("color: white; font-family: 'Courier New'; font-size: 10px;")
            uptime_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(uptime_label)

            cpu = self.get_cpu_info()
            mem = self.get_memory_info()
            # CPU & RAM
            cpu_ram_label = QLabel(f"CPU: %{cpu['percent']}  |  RAM: %{mem['percent']}")
            cpu_ram_label.setStyleSheet("color: white; font-family: 'Courier New'; font-size: 10px;")
            cpu_ram_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(cpu_ram_label)

            disk = self.get_disk_info()
            # Disk
            disk_label = QLabel(f"Disk: %{disk['percent']} kullanımda")
            disk_label.setStyleSheet("color: white; font-family: 'Courier New'; font-size: 10px;")
            disk_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(disk_label)

            # Kritik rapor
            report_label = QLabel("Kritik Çökme Raporu: TEMİZ")
            report_label.setStyleSheet("color: #00ff00; font-family: 'Courier New'; font-size: 10px; font-weight: bold;")
            report_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(report_label)

            hud.show()

            self._beep(400, 300)

            # 5 saniye sonra kapat
            QTimer.singleShot(5000, hud.close)
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


def black_box(parameters: Optional[dict] = None, player=None, root=None) -> str:
    """main.py içinden çağrılan fonksiyon."""
    box = BlackBox(player=player, root=root)
    return box.run()