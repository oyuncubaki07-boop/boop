"""
observer_mode.py - J.A.R.V.I.S. Gözlemci Modülü (PyQt6)
Ekranı, sistem olaylarını ve hata pencerelerini izler, anormallikleri tespit eder.
"""

import threading
import time
import winsound
import psutil
import re
from datetime import datetime
from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QTextEdit, QApplication, QFrame
)
from PyQt6.QtCore import Qt, QTimer

try:
    import pyautogui
    import cv2
    import numpy as np
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False


class Observer:
    """Gözlemci sınıfı - ekran ve sistem izleme"""

    def __init__(self, player=None, root=None):
        self.player = player
        self.root = root
        self.is_running = False
        self.anomalies_found = []
        self.screenshot_enabled = False
        self.cpu_threshold = 80.0
        self.memory_threshold = 85.0

    def log(self, msg: str):
        if self.player and hasattr(self.player, "write_log"):
            self.player.write_log(f"SYS: {msg}")
        else:
            print(f"[OBSERVER] {msg}")

    def _beep(self, freq: int, duration: int = 150):
        try:
            winsound.Beep(freq, duration)
        except:
            pass

    def detect_error_windows(self) -> List[str]:
        """Ekranda hata penceresi olup olmadığını tespit eder."""
        if not PYAUTOGUI_AVAILABLE:
            return []
        try:
            import win32gui
            error_titles = []
            def enum_callback(hwnd, titles):
                if win32gui.IsWindowVisible(hwnd):
                    window_text = win32gui.GetWindowText(hwnd)
                    if any(keyword in window_text.lower() for keyword in
                           ['hata', 'error', 'fail', 'uyarı', 'critical', 'exception']):
                        titles.append(window_text)
            win32gui.EnumWindows(enum_callback, error_titles)
            return error_titles
        except:
            return []

    def get_system_anomalies(self) -> List[str]:
        """Sistem kaynaklarını kontrol eder, anormallikleri listeler."""
        anomalies = []
        cpu_percent = psutil.cpu_percent(interval=0.5)
        if cpu_percent > self.cpu_threshold:
            anomalies.append(f"Yüksek CPU kullanımı: %{cpu_percent}")
        mem = psutil.virtual_memory()
        if mem.percent > self.memory_threshold:
            anomalies.append(f"Yüksek RAM kullanımı: %{mem.percent}")
        disk = psutil.disk_usage('/')
        if disk.percent > 90:
            anomalies.append(f"Disk alanı kritik: %{disk.percent} dolu")
        return anomalies

    def run_observation(self, duration_seconds: int = 15, interactive: bool = True):
        """Belirtilen süre boyunca gözlem yapar."""
        self.is_running = True
        self.log("👁️ Gözlemci protokolü başladı. Ekran ve sistem izleniyor...")

        start_time = time.time()
        error_windows_seen = set()

        while self.is_running and (time.time() - start_time) < duration_seconds:
            errors = self.detect_error_windows()
            for err in errors:
                if err not in error_windows_seen:
                    error_windows_seen.add(err)
                    self.anomalies_found.append({
                        "type": "error_window",
                        "title": err,
                        "timestamp": datetime.now().isoformat()
                    })
                    self.log(f"⚠️ Hata penceresi tespit edildi: {err}")

            sys_anomalies = self.get_system_anomalies()
            for anom in sys_anomalies:
                if anom not in [a.get("message") for a in self.anomalies_found if a["type"] == "system"]:
                    self.anomalies_found.append({
                        "type": "system",
                        "message": anom,
                        "timestamp": datetime.now().isoformat()
                    })
                    self.log(f"⚠️ Sistem anormalliği: {anom}")

            time.sleep(2)

        self.is_running = False

        if self.anomalies_found:
            self._report_anomalies(interactive)
        else:
            self.log("✅ Gözlem tamamlandı. Herhangi bir anormallik tespit edilmedi.")
            if self.root:
                QTimer.singleShot(0, self._show_clear_hud)

    def _report_anomalies(self, interactive: bool = True):
        """Anormallikleri kullanıcıya bildirir."""
        anomaly_count = len(self.anomalies_found)
        self.log(f"🔔 {anomaly_count} anormallik tespit edildi.")

        if not self.root or not isinstance(self.root, QWidget):
            return

        def show():
            hud = QWidget(self.root)
            hud.setWindowFlags(
                Qt.WindowType.FramelessWindowHint |
                Qt.WindowType.WindowStaysOnTopHint
            )
            hud.setWindowOpacity(0.95)
            hud.setGeometry(10, 10, 500, 180)
            hud.setStyleSheet("background-color: #002b36;")

            layout = QVBoxLayout(hud)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(6)

            title = QLabel("👁️ GÖZLEMCİ UYARISI")
            title.setStyleSheet("color: #ff6600; font-family: 'Courier New'; font-size: 12px; font-weight: bold;")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(title)

            summary_text = f"Toplam {anomaly_count} anormallik tespit edildi:\n"
            for i, anom in enumerate(self.anomalies_found[:3]):
                if anom["type"] == "error_window":
                    summary_text += f"• Hata penceresi: {anom['title'][:40]}\n"
                else:
                    summary_text += f"• {anom['message']}\n"
            if anomaly_count > 3:
                summary_text += f"• +{anomaly_count - 3} diğer..."

            summary = QLabel(summary_text)
            summary.setStyleSheet("color: white; font-family: 'Courier New'; font-size: 9px;")
            summary.setAlignment(Qt.AlignmentFlag.AlignLeft)
            summary.setWordWrap(True)
            layout.addWidget(summary)

            self._beep(1200, 150)
            self._beep(1400, 200)

            if interactive:
                btn_layout = QHBoxLayout()
                btn_layout.addStretch()

                yes_btn = QPushButton("Çözüm öner")
                yes_btn.setStyleSheet(
                    "QPushButton { background-color: #006600; color: white; border: none; padding: 5px 15px; }"
                    "QPushButton:hover { background-color: #008800; }"
                )
                yes_btn.clicked.connect(lambda: (hud.close(), self._offer_solutions()))
                btn_layout.addWidget(yes_btn)

                no_btn = QPushButton("Kapat")
                no_btn.setStyleSheet(
                    "QPushButton { background-color: #660000; color: white; border: none; padding: 5px 10px; }"
                    "QPushButton:hover { background-color: #880000; }"
                )
                no_btn.clicked.connect(lambda: (hud.close(), self.log("Kullanıcı müdahale etmemeyi seçti.")))
                btn_layout.addWidget(no_btn)

                btn_layout.addStretch()
                layout.addLayout(btn_layout)

                QTimer.singleShot(20000, hud.close)
            else:
                QTimer.singleShot(8000, hud.close)

            hud.show()

        QTimer.singleShot(0, show)

    def _show_clear_hud(self):
        """Temiz rapor HUD'u."""
        if not self.root or not isinstance(self.root, QWidget):
            return

        hud = QWidget(self.root)
        hud.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        hud.setWindowOpacity(0.9)
        hud.setGeometry(10, 10, 350, 80)
        hud.setStyleSheet("background-color: #004d1a;")

        layout = QVBoxLayout(hud)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        title = QLabel("👁️ GÖZLEMCİ RAPORU")
        title.setStyleSheet("color: #00ff66; font-family: 'Courier New'; font-size: 11px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        msg = QLabel("✅ Anormallik tespit edilmedi. Sistem stabil.")
        msg.setStyleSheet("color: white; font-family: 'Courier New'; font-size: 9px;")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(msg)

        hud.show()
        self._beep(800, 100)
        QTimer.singleShot(4000, hud.close)

    def _offer_solutions(self):
        """Kullanıcıya çözüm önerileri sunar."""
        if not self.root or not isinstance(self.root, QWidget):
            return

        dialog = QWidget()
        dialog.setWindowTitle("J.A.R.V.I.S. - Çözüm Önerileri")
        dialog.setGeometry(100, 100, 500, 300)
        dialog.setStyleSheet("background-color: #1e1e2e;")
        dialog.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        title = QLabel("🔧 Tespit Edilen Sorunlara Çözüm Önerileri")
        title.setStyleSheet("color: #00ffcc; font-family: 'Arial'; font-size: 12px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        text_edit = QTextEdit()
        text_edit.setStyleSheet("background-color: #2d2d3a; color: white; font-family: 'Consolas'; font-size: 9px;")
        text_edit.setReadOnly(True)

        suggestions = []
        for anom in self.anomalies_found:
            if anom["type"] == "error_window":
                suggestions.append(f"• Hata penceresi: '{anom['title']}' → Görevi sonlandırmayı veya yazılımı güncellemeyi dene.")
            elif "CPU" in anom.get("message", ""):
                suggestions.append("• Yüksek CPU → Gereksiz uygulamaları kapat, virüs taraması yap.")
            elif "RAM" in anom.get("message", ""):
                suggestions.append("• Yüksek RAM → Bilgisayarı yeniden başlat, tarayıcı sekmelerini kısıtla.")
            elif "Disk" in anom.get("message", ""):
                suggestions.append("• Disk doldu → Gereksiz dosyaları temizle, Disk Temizleme çalıştır.")

        if not suggestions:
            suggestions.append("Genel öneri: Bilgisayarını yeniden başlat ve güncellemeleri kontrol et.")

        text_edit.setText("\n".join(suggestions))
        layout.addWidget(text_edit)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        web_btn = QPushButton("Web'de Ara")
        web_btn.setStyleSheet(
            "QPushButton { background-color: #004466; color: white; border: none; padding: 6px 12px; }"
            "QPushButton:hover { background-color: #005588; }"
        )
        web_btn.clicked.connect(lambda: self._open_web_search())
        btn_layout.addWidget(web_btn)

        close_btn = QPushButton("Kapat")
        close_btn.setStyleSheet(
            "QPushButton { background-color: #333; color: white; border: none; padding: 6px 12px; }"
            "QPushButton:hover { background-color: #555; }"
        )
        close_btn.clicked.connect(dialog.close)
        btn_layout.addWidget(close_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        dialog.show()
        self._beep(1000, 200)

    def _open_web_search(self):
        import webbrowser
        query = " ".join([a.get("title", a.get("message", "")) for a in self.anomalies_found[:2]])
        if query:
            webbrowser.open(f"https://www.google.com/search?q={query.replace(' ', '+')}+çözüm")


def observer_mode(parameters: Optional[dict] = None, player=None, root=None) -> str:
    """
    Gözlemci modunu başlatır.
    parameters: {
        "duration": 15,
        "interactive": True,
        "screenshot": False
    }
    """
    params = parameters or {}
    duration = params.get("duration", 15)
    interactive = params.get("interactive", True)

    observer = Observer(player=player, root=root)
    observer.screenshot_enabled = params.get("screenshot", False)

    def run():
        observer.run_observation(duration_seconds=duration, interactive=interactive)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()

    return f"Gözlemci protokolü başlatıldı patron. {duration} saniye boyunca sisteminizi ve ekranınızı izleyeceğim. Bir anormallik tespit edersem size bildireceğim."