"""
breach_watch.py - J.A.R.V.I.S. Veri Sızıntısı İzleme Modülü (PyQt6)
E-posta, telefon ve kullanıcı adlarının veri tabanı sızıntılarında olup olmadığını kontrol eder.
(Şu an simülasyon modunda, gerçek API için HaveIBeenPwned entegre edilebilir)
"""

import winsound
import json
import hashlib
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PyQt6.QtCore import Qt, QTimer

# Yapılandırma
CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
BREACH_DATA_FILE = CONFIG_DIR / "breach_cache.json"
DEFAULT_EMAILS = []  # Kullanıcı buraya kendi e-postalarını ekleyebilir veya parametre ile gönderebilir


class BreachWatch:
    """
    Veri sızıntısı tarama ve izleme sınıfı.
    - E-posta, telefon, kullanıcı adı bazlı tarama
    - Önbellek ile tekrar eden sorguları azaltma
    - Gerçek API için hazır altyapı (HaveIBeenPwned vb.)
    """

    def __init__(self, player=None, root=None):
        self.player = player
        self.root = root          # PyQt6 widget'ı veya None
        self.cache = self._load_cache()
        self.scan_in_progress = False

    def log(self, msg: str):
        if self.player and hasattr(self.player, "write_log"):
            self.player.write_log(f"SYS: {msg}")
        else:
            print(f"[BREACH] {msg}")

    def _beep(self, freq: int, duration: int = 150):
        try:
            winsound.Beep(freq, duration)
        except:
            pass

    def _load_cache(self) -> Dict[str, Any]:
        """Önbellek dosyasını yükler."""
        if BREACH_DATA_FILE.exists():
            try:
                return json.loads(BREACH_DATA_FILE.read_text(encoding="utf-8"))
            except:
                return {"last_scan": None, "results": {}}
        return {"last_scan": None, "results": {}}

    def _save_cache(self):
        """Önbelleği kaydeder."""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            BREACH_DATA_FILE.write_text(json.dumps(self.cache, indent=2), encoding="utf-8")
        except Exception as e:
            self.log(f"Önbellek kaydedilemedi: {e}")

    def _check_hibp(self, email: str) -> Dict[str, Any]:
        """
        HaveIBeenPwned API'ye sorgu yapar (gerçek entegrasyon için).
        Şu an simülasyon modunda.
        """
        # SIMÜLASYON: Her zaman "güvende" döndür
        return {
            "breached": False,
            "breaches": [],
            "message": "Veritabanlarında eşleşme bulunamadı (simülasyon)"
        }

    def scan_email(self, email: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Tek bir e-posta adresini tarar."""
        email_lower = email.lower().strip()
        if not force_refresh and email_lower in self.cache["results"]:
            cached = self.cache["results"][email_lower]
            cached["cached"] = True
            return cached

        self.log(f"📧 E-posta taranıyor: {email_lower}")
        result = self._check_hibp(email_lower)
        result["email"] = email_lower
        result["scanned_at"] = datetime.now().isoformat()
        result["cached"] = False

        self.cache["results"][email_lower] = result
        self.cache["last_scan"] = datetime.now().isoformat()
        self._save_cache()
        return result

    def scan_multiple(self, emails: List[str]) -> List[Dict[str, Any]]:
        """Birden fazla e-postayı tarar."""
        results = []
        for email in emails:
            results.append(self.scan_email(email))
        return results

    def _show_hud(self, results: List[Dict[str, Any]]):
        """Tarama sonuçlarını PyQt6 HUD penceresinde gösterir."""
        if not self.root:
            return
        try:
            breached_count = sum(1 for r in results if r.get("breached", False))
            safe_count = len(results) - breached_count
            bg_color = "#1a0000" if breached_count > 0 else "#001a00"
            title_color = "#ff3333" if breached_count > 0 else "#00ff00"

            parent = self.root if isinstance(self.root, QWidget) else None
            hud = QWidget(parent)
            hud.setWindowFlags(
                Qt.WindowType.FramelessWindowHint |
                Qt.WindowType.WindowStaysOnTopHint
            )
            hud.setWindowOpacity(0.9)
            hud.setGeometry(10, 10, 450, 120)
            hud.setStyleSheet(f"background-color: {bg_color};")

            layout = QVBoxLayout(hud)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(4)

            # Başlık
            title_label = QLabel("🛡️ SIZINTI TARAMASI")
            title_label.setStyleSheet(
                f"color: {title_color}; font-family: 'Courier New'; font-size: 11px; font-weight: bold;"
            )
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(title_label)

            if breached_count > 0:
                warn_label = QLabel(f"⚠️ {breached_count} hesapta olası sızıntı tespit edildi!")
                warn_label.setStyleSheet("color: #ff6666; font-family: 'Courier New'; font-size: 9px;")
                warn_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(warn_label)
            else:
                safe_label = QLabel("✅ Tüm hesaplarınız güvende görünüyor.")
                safe_label.setStyleSheet("color: #00ff00; font-family: 'Courier New'; font-size: 9px;")
                safe_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(safe_label)

            summary_label = QLabel(f"Toplam {len(results)} hesap kontrol edildi.")
            summary_label.setStyleSheet("color: white; font-family: 'Courier New'; font-size: 9px;")
            summary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(summary_label)

            hud.show()

            self._beep(600, 150)
            if breached_count > 0:
                self._beep(300, 300)

            QTimer.singleShot(6000, hud.close)
        except Exception as e:
            self.log(f"HUD hatası: {e}")

    def run(self, emails: Optional[List[str]] = None, force_refresh: bool = False) -> str:
        """Veri sızıntısı taramasını başlatır."""
        if self.scan_in_progress:
            return "Zaten bir tarama devam ediyor, lütfen bekleyin."

        target_emails = emails if emails else DEFAULT_EMAILS
        if not target_emails:
            self.log("Taranacak e-posta adresi bulunamadı. Varsayılan liste boş.")
            target_emails = ["ornek@kullanici.com"]
            self.log("Demo modunda örnek e-posta taranıyor.")

        self.scan_in_progress = True
        self.log("🛡️ Veri sızıntısı taraması başlatılıyor...")

        def do_scan():
            try:
                results = self.scan_multiple(target_emails)
                # PyQt6 ana thread'de GUI güncellemesi
                QTimer.singleShot(0, lambda: self._show_hud(results))
                self.scan_in_progress = False
            except Exception as e:
                self.log(f"Tarama hatası: {e}")
                self.scan_in_progress = False

        threading.Thread(target=do_scan, daemon=True).start()

        return f"Veri sızıntısı taraması başlatıldı. {len(target_emails)} hesap kontrol edilecek. Sonuçları bildireceğim."


def breach_watch(parameters: Optional[dict] = None, player=None, root=None) -> str:
    """main.py içinden çağrılan fonksiyon."""
    if parameters is None:
        parameters = {}
    emails = parameters.get("emails")
    force = parameters.get("force", False)

    watch = BreachWatch(player=player, root=root)
    return watch.run(emails=emails, force_refresh=force)