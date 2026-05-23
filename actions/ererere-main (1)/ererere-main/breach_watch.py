"""
breach_watch.py - J.A.R.V.I.S. Veri Sızıntısı İzleme Modülü
E-posta, telefon ve kullanıcı adlarının veri tabanı sızıntılarında olup olmadığını kontrol eder.
(Şu an simülasyon modunda, gerçek API için HaveIBeenPwned entegre edilebilir)
"""

import tkinter as tk
import winsound
import json
import hashlib
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

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
        self.root = root
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
        Gerçek API için:
        - pip install requests
        - API anahtarı al (HaveIBeenPwned v3 kullanır)
        - Buraya requests.get ile sorgu ekle
        """
        # SIMÜLASYON: Her zaman "güvende" döndür
        # Gerçek uygulamada buraya API çağrısı gelecek
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
        """Tarama sonuçlarını HUD penceresinde gösterir."""
        if not self.root:
            return
        try:
            # Kaç tane güvende, kaç tane riskli?
            breached_count = sum(1 for r in results if r.get("breached", False))
            safe_count = len(results) - breached_count

            hud = tk.Toplevel(self.root)
            hud.overrideredirect(True)
            hud.attributes("-topmost", True, "-alpha", 0.9)
            hud.geometry("450x120+10+10")
            hud.configure(bg="#1a0000" if breached_count > 0 else "#001a00")  # Kırmızı risk, yeşil güvenli

            title_color = "#ff3333" if breached_count > 0 else "#00ff00"
            tk.Label(hud, text="🛡️ SIZINTI TARAMASI", font=("Courier", 11, "bold"), fg=title_color, bg=hud["bg"]).pack(pady=5)

            if breached_count > 0:
                tk.Label(hud, text=f"⚠️ {breached_count} hesapta olası sızıntı tespit edildi!", font=("Courier", 9), fg="#ff6666", bg=hud["bg"]).pack()
            else:
                tk.Label(hud, text="✅ Tüm hesaplarınız güvende görünüyor.", font=("Courier", 9), fg="#00ff00", bg=hud["bg"]).pack()

            tk.Label(hud, text=f"Toplam {len(results)} hesap kontrol edildi.", font=("Courier", 9), fg="white", bg=hud["bg"]).pack()

            self._beep(600, 150)
            if breached_count > 0:
                self._beep(300, 300)  # riskli durumda farklı ses

            self.root.after(6000, lambda: hud.destroy() if hud.winfo_exists() else None)
        except Exception as e:
            self.log(f"HUD hatası: {e}")

    def run(self, emails: Optional[List[str]] = None, force_refresh: bool = False) -> str:
        """
        Veri sızıntısı taramasını başlatır.
        emails: taranacak e-posta listesi (None ise varsayılan listeyi kullanır)
        force_refresh: önbelleği yenileme zorunluluğu
        """
        if self.scan_in_progress:
            return "Zaten bir tarama devam ediyor, lütfen bekleyin."

        target_emails = emails if emails else DEFAULT_EMAILS
        if not target_emails:
            self.log("Taranacak e-posta adresi bulunamadı. Varsayılan liste boş.")
            # Simülasyon için örnek bir e-posta ekleyelim (isteğe bağlı)
            target_emails = ["ornek@kullanici.com"]  # Bu sadece demo için
            self.log("Demo modunda örnek e-posta taranıyor.")

        self.scan_in_progress = True
        self.log("🛡️ Veri sızıntısı taraması başlatılıyor...")

        # Arka planda tarama yap (UI donmasın)
        def do_scan():
            try:
                results = self.scan_multiple(target_emails)
                self.root.after(0, lambda: self._show_hud(results))
                self.scan_in_progress = False
            except Exception as e:
                self.log(f"Tarama hatası: {e}")
                self.scan_in_progress = False

        threading.Thread(target=do_scan, daemon=True).start()

        return f"Veri sızıntısı taraması başlatıldı. {len(target_emails)} hesap kontrol edilecek. Sonuçları bildireceğim."


# ------------------------------
# Ana fonksiyon (main.py'den çağrılmak için)
def breach_watch(parameters: Optional[dict] = None, player=None, root=None) -> str:
    """
    main.py içinden çağrılan fonksiyon.
    parameters: {
        "emails": ["ornek@gmail.com", "test@hotmail.com"],  # opsiyonel
        "force": False  # önbelleği yenilemek için
    }
    """
    if parameters is None:
        parameters = {}
    emails = parameters.get("emails")
    force = parameters.get("force", False)

    watch = BreachWatch(player=player, root=root)
    return watch.run(emails=emails, force_refresh=force)