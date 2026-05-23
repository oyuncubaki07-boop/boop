"""
hologram_hud.py - J.A.R.V.I.S. HoloGrafik Sistem Arayüzü (HUD) (PyQt6)
Sistemin anlık CPU, RAM, disk, ağ, batarya ve çalışma süresi bilgilerini holografik bir panelde gösterir.
"""

import psutil
import platform
from datetime import datetime
import winsound
import threading
import time
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QLabel, QFrame, QVBoxLayout, QHBoxLayout, QGridLayout,
    QApplication
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QMouseEvent


class HologramHUD:
    """Holografik HUD penceresini yöneten sınıf."""

    def __init__(self, root, player=None, auto_refresh: bool = False, refresh_interval: int = 2000):
        self.root = root
        self.player = player
        self.auto_refresh = auto_refresh
        self.refresh_interval = refresh_interval
        self.hud: QWidget | None = None
        self.running = False
        self.widgets = {}
        self._drag_pos = None

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
        """PyQt6 HUD penceresini oluşturur."""
        if self.hud and self.hud.isVisible():
            return
        
        parent = self.root if isinstance(self.root, QWidget) else None
        self.hud = QWidget(parent)
        self.hud.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.hud.setWindowOpacity(0.92)
        self.hud.setGeometry(10, 10, 850, 480)
        self.hud.setStyleSheet("background-color: #000d1a;")

        # ESC ile kapatma
        self.hud.keyPressEvent = lambda e: self.close() if e.key() == Qt.Key.Key_Escape else None

        main_layout = QVBoxLayout(self.hud)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Başlık çubuğu (taşınabilir)
        title_bar = QFrame()
        title_bar.setFixedHeight(30)
        title_bar.setStyleSheet("background-color: #002244;")
        title_bar.mousePressEvent = self.start_move
        title_bar.mouseMoveEvent = self.on_move

        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)

        title_label = QLabel("🎛️ J.A.R.V.I.S. HOLOGRAM HUD")
        title_label.setStyleSheet("color: #00ffff; font-family: 'Courier New'; font-size: 12px; font-weight: bold;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        close_btn = QLabel("✖")
        close_btn.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.mousePressEvent = lambda e: self.close()
        title_layout.addWidget(close_btn)

        main_layout.addWidget(title_bar)

        # Ana içerik
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(20, 10, 20, 0)
        content_layout.setSpacing(20)

        # Sol taraf (sistem özeti)
        left_panel = QVBoxLayout()
        left_panel.setSpacing(5)

        self.widgets["time"] = QLabel()
        self.widgets["time"].setStyleSheet("color: white; font-family: 'Courier New'; font-size: 12px;")
        left_panel.addWidget(self.widgets["time"])

        self.widgets["host"] = QLabel()
        self.widgets["host"].setStyleSheet("color: #aaaaaa; font-family: 'Courier New'; font-size: 10px;")
        left_panel.addWidget(self.widgets["host"])

        self.widgets["os"] = QLabel()
        self.widgets["os"].setStyleSheet("color: #aaaaaa; font-family: 'Courier New'; font-size: 10px;")
        left_panel.addWidget(self.widgets["os"])

        self.widgets["uptime"] = QLabel()
        self.widgets["uptime"].setStyleSheet("color: #cccccc; font-family: 'Courier New'; font-size: 10px;")
        left_panel.addWidget(self.widgets["uptime"])

        # Ayırıcı
        sep = QLabel("─" * 30)
        sep.setStyleSheet("color: #00ffff; font-family: 'Courier New'; font-size: 10px;")
        left_panel.addWidget(sep)

        # CPU
        cpu_layout = QHBoxLayout()
        cpu_label = QLabel("CPU:")
        cpu_label.setStyleSheet("color: #00ffcc; font-family: 'Courier New'; font-size: 11px; font-weight: bold;")
        cpu_layout.addWidget(cpu_label)
        self.widgets["cpu"] = QLabel()
        self.widgets["cpu"].setStyleSheet("font-family: 'Courier New'; font-size: 11px; font-weight: bold;")
        cpu_layout.addWidget(self.widgets["cpu"])
        cpu_layout.addStretch()
        left_panel.addLayout(cpu_layout)

        # RAM
        ram_layout = QHBoxLayout()
        ram_label = QLabel("RAM:")
        ram_label.setStyleSheet("color: #00ffcc; font-family: 'Courier New'; font-size: 11px; font-weight: bold;")
        ram_layout.addWidget(ram_label)
        self.widgets["ram"] = QLabel()
        self.widgets["ram"].setStyleSheet("font-family: 'Courier New'; font-size: 11px; font-weight: bold;")
        ram_layout.addWidget(self.widgets["ram"])
        ram_layout.addStretch()
        left_panel.addLayout(ram_layout)

        # Disk
        disk_layout = QHBoxLayout()
        disk_label = QLabel("DISK:")
        disk_label.setStyleSheet("color: #00ffcc; font-family: 'Courier New'; font-size: 11px; font-weight: bold;")
        disk_layout.addWidget(disk_label)
        self.widgets["disk"] = QLabel()
        self.widgets["disk"].setStyleSheet("font-family: 'Courier New'; font-size: 11px; font-weight: bold;")
        disk_layout.addWidget(self.widgets["disk"])
        disk_layout.addStretch()
        left_panel.addLayout(disk_layout)

        # Ağ
        net_layout = QHBoxLayout()
        net_label = QLabel("AĞ:")
        net_label.setStyleSheet("color: #00ffcc; font-family: 'Courier New'; font-size: 11px; font-weight: bold;")
        net_layout.addWidget(net_label)
        self.widgets["net"] = QLabel()
        self.widgets["net"].setStyleSheet("color: white; font-family: 'Courier New'; font-size: 10px;")
        net_layout.addWidget(self.widgets["net"])
        net_layout.addStretch()
        left_panel.addLayout(net_layout)

        # Batarya
        bat_layout = QHBoxLayout()
        bat_label = QLabel("BATARYA:")
        bat_label.setStyleSheet("color: #00ffcc; font-family: 'Courier New'; font-size: 11px; font-weight: bold;")
        bat_layout.addWidget(bat_label)
        self.widgets["battery"] = QLabel()
        self.widgets["battery"].setStyleSheet("color: white; font-family: 'Courier New'; font-size: 10px;")
        bat_layout.addWidget(self.widgets["battery"])
        bat_layout.addStretch()
        left_panel.addLayout(bat_layout)

        # Sağ taraf
        right_panel = QFrame()
        right_panel.setMinimumWidth(300)
        right_panel.setStyleSheet("background-color: #001a33;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(15, 15, 15, 15)

        right_title = QLabel("🔧 SİSTEM DURUMU")
        right_title.setStyleSheet("color: #ffcc00; font-family: 'Courier New'; font-size: 12px; font-weight: bold;")
        right_layout.addWidget(right_title)

        self.widgets["status"] = QLabel("✅ Tüm sistemler çevrimiçi")
        self.widgets["status"].setStyleSheet("color: #00ff66; font-family: 'Courier New'; font-size: 10px;")
        right_layout.addWidget(self.widgets["status"])

        right_layout.addSpacing(10)

        mod_title = QLabel("⚡ AKTİF MODÜLLER")
        mod_title.setStyleSheet("color: #ffaa66; font-family: 'Courier New'; font-size: 10px; font-weight: bold;")
        right_layout.addWidget(mod_title)

        for mod in ["Güvenlik", "Ağ İzleme", "Hafıza", "Otomasyon", "Medya", "Ses"]:
            lbl = QLabel(f"• {mod}")
            lbl.setStyleSheet("color: white; font-family: 'Courier New'; font-size: 9px;")
            right_layout.addWidget(lbl)

        right_layout.addStretch()

        content_layout.addLayout(left_panel, 1)
        content_layout.addWidget(right_panel, 0)
        main_layout.addLayout(content_layout)

        # Alt bilgi
        footer = QLabel("Hologram HUD | ESC ile kapat")
        footer.setStyleSheet("color: #666666; font-family: 'Courier New'; font-size: 8px;")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(footer)

        self.hud.show()

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
            self._start_refresh_loop()

    def _start_refresh_loop(self):
        """Otomatik yenileme döngüsü."""
        if not self.running or not self.hud or not self.hud.isVisible():
            return
        self.update_info()
        QTimer.singleShot(self.refresh_interval, self._start_refresh_loop)

    def update_info(self):
        """Bilgileri günceller."""
        info = self.get_system_info()
        if not info:
            return

        cpu_color = "#ff3333" if info["cpu"] > 80 else ("#ffaa00" if info["cpu"] > 60 else "#00ff00")
        ram_color = "#ff3333" if info["ram"] > 85 else ("#ffaa00" if info["ram"] > 70 else "#00ff00")
        disk_color = "#ff3333" if info["disk"] > 90 else ("#ffaa00" if info["disk"] > 75 else "#00ff00")

        self.widgets["time"].setText(f"🕒 {info['time']}")
        self.widgets["host"].setText(f"🖥️ {info['hostname']}")
        self.widgets["os"].setText(f"💿 {info['os']}")
        self.widgets["uptime"].setText(f"⏱️ Çalışma: {info['uptime']}")
        self.widgets["cpu"].setText(f"%{info['cpu']:.1f}")
        self.widgets["cpu"].setStyleSheet(f"color: {cpu_color}; font-family: 'Courier New'; font-size: 11px; font-weight: bold;")
        self.widgets["ram"].setText(f"%{info['ram']:.1f}")
        self.widgets["ram"].setStyleSheet(f"color: {ram_color}; font-family: 'Courier New'; font-size: 11px; font-weight: bold;")
        self.widgets["disk"].setText(f"%{info['disk']:.1f}")
        self.widgets["disk"].setStyleSheet(f"color: {disk_color}; font-family: 'Courier New'; font-size: 11px; font-weight: bold;")
        self.widgets["net"].setText(f"⬇️ {info['net_recv']:.1f} MB / ⬆️ {info['net_sent']:.1f} MB")

        bat_text = "Yok"
        if info["battery"] is not None:
            bat_text = f"%{info['battery']:.0f}"
            bat_text += " (Şarjda)" if info["battery_plugged"] else " (Pil)"
        self.widgets["battery"].setText(bat_text)

        if info["cpu"] > 80 or info["ram"] > 85:
            self.widgets["status"].setText("⚠️ Yüksek sistem yükü!")
            self.widgets["status"].setStyleSheet("color: #ff6666; font-family: 'Courier New'; font-size: 10px;")
        else:
            self.widgets["status"].setText("✅ Tüm sistemler çevrimiçi")
            self.widgets["status"].setStyleSheet("color: #00ff66; font-family: 'Courier New'; font-size: 10px;")

    def start_move(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()

    def on_move(self, event: QMouseEvent):
        if self._drag_pos is not None and event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.hud.move(self.hud.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()

    def close(self):
        self.running = False
        if self.hud:
            self.hud.close()
        self.log("Hologram HUD kapatıldı.")


def hologram_hud(parameters: Optional[dict] = None, player=None, root=None) -> str:
    """
    Holografik HUD'u açar.
    parameters: {
        "auto_refresh": False,
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
        QTimer.singleShot(duration * 1000, hud_manager.close)
    
    return "Holografik sistem arayüzü ekrana yansıtıldı patron. ESC tuşu veya kapatma butonu ile kapatabilirsiniz."