"""
observer_mode.py - J.A.R.V.I.S. Gözlemci Modülü
Ekranı, sistem olaylarını ve hata pencerelerini izler, anormallikleri tespit eder.
"""

import threading
import time
import tkinter as tk
import winsound
import psutil
import re
from datetime import datetime
from typing import Optional, List, Dict, Any

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
        self.screenshot_enabled = False  # Varsayılan kapalı, performans için
        self.cpu_threshold = 80.0  # CPU %80 üzeri anomali
        self.memory_threshold = 85.0  # RAM %85 üzeri anomali

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
        """Ekranda hata penceresi olup olmadığını tespit eder (OCR benzeri basit metin araması)."""
        if not PYAUTOGUI_AVAILABLE:
            return []
        
        try:
            screenshot = pyautogui.screenshot()
            # Basit metin araması için görüntüyü işleme (gerçek OCR için pytesseract gerekir, burada simülasyon)
            # Simülasyon: belirli hata kelimelerini içeren pencere başlıklarına bakalım
            import win32gui
            import win32con
            
            error_titles = []
            def enum_callback(hwnd, titles):
                if win32gui.IsWindowVisible(hwnd):
                    window_text = win32gui.GetWindowText(hwnd)
                    if any(keyword in window_text.lower() for keyword in ['hata', 'error', 'fail', 'uyarı', 'critical', 'exception']):
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
        
        # Disk kullanımı
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
            # Hata pencerelerini kontrol et
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
            
            # Sistem anormalliklerini kontrol et
            sys_anomalies = self.get_system_anomalies()
            for anom in sys_anomalies:
                if anom not in [a.get("message") for a in self.anomalies_found if a["type"]=="system"]:
                    self.anomalies_found.append({
                        "type": "system",
                        "message": anom,
                        "timestamp": datetime.now().isoformat()
                    })
                    self.log(f"⚠️ Sistem anormalliği: {anom}")
            
            time.sleep(2)  # 2 saniyede bir kontrol
        
        self.is_running = False
        
        # Sonuçları raporla
        if self.anomalies_found:
            self._report_anomalies(interactive)
        else:
            self.log("✅ Gözlem tamamlandı. Herhangi bir anormallik tespit edilmedi.")
            if self.root:
                self._show_clear_hud()

    def _report_anomalies(self, interactive: bool = True):
        """Anormallikleri kullanıcıya bildirir."""
        anomaly_count = len(self.anomalies_found)
        self.log(f"🔔 {anomaly_count} anormallik tespit edildi.")
        
        if not self.root:
            return
        
        # HUD gösterimi
        try:
            hud = tk.Toplevel(self.root)
            hud.overrideredirect(True)
            hud.attributes("-topmost", True, "-alpha", 0.95)
            hud.geometry("500x180+10+10")
            hud.configure(bg="#002b36")
            
            tk.Label(hud, text="👁️ GÖZLEMCİ UYARISI", font=("Courier", 12, "bold"), fg="#ff6600", bg="#002b36").pack(pady=5)
            
            # Anomali özeti
            summary_text = f"Toplam {anomaly_count} anormallik tespit edildi:\n"
            for i, anom in enumerate(self.anomalies_found[:3]):  # İlk 3'ü göster
                if anom["type"] == "error_window":
                    summary_text += f"• Hata penceresi: {anom['title'][:40]}\n"
                else:
                    summary_text += f"• {anom['message']}\n"
            if anomaly_count > 3:
                summary_text += f"• +{anomaly_count - 3} diğer..."
            
            tk.Label(hud, text=summary_text, font=("Courier", 9), fg="white", bg="#002b36", justify="left", wraplength=480).pack(pady=5)
            
            # Sesli uyarı
            self._beep(1200, 150)
            self._beep(1400, 200)
            
            if interactive:
                # Kullanıcıya aksiyon sorusu
                def on_yes():
                    hud.destroy()
                    self._offer_solutions()
                
                def on_no():
                    hud.destroy()
                    self.log("Kullanıcı müdahale etmemeyi seçti.")
                
                btn_frame = tk.Frame(hud, bg="#002b36")
                btn_frame.pack(pady=5)
                tk.Button(btn_frame, text="Çözüm öner", command=on_yes, bg="#006600", fg="white", relief="flat", width=12).pack(side="left", padx=5)
                tk.Button(btn_frame, text="Kapat", command=on_no, bg="#660000", fg="white", relief="flat", width=8).pack(side="left", padx=5)
                
                # Otomatik kapanma (20 saniye)
                self.root.after(20000, lambda: hud.destroy() if hud.winfo_exists() else None)
            else:
                self.root.after(8000, lambda: hud.destroy() if hud.winfo_exists() else None)
                
        except Exception as e:
            self.log(f"HUD hatası: {e}")

    def _show_clear_hud(self):
        """Temiz rapor HUD'u."""
        try:
            hud = tk.Toplevel(self.root)
            hud.overrideredirect(True)
            hud.attributes("-topmost", True, "-alpha", 0.9)
            hud.geometry("350x80+10+10")
            hud.configure(bg="#004d1a")
            tk.Label(hud, text="👁️ GÖZLEMCİ RAPORU", font=("Courier", 11, "bold"), fg="#00ff66", bg="#004d1a").pack(pady=5)
            tk.Label(hud, text="✅ Anormallik tespit edilmedi. Sistem stabil.", font=("Courier", 9), fg="white", bg="#004d1a").pack()
            self._beep(800, 100)
            self.root.after(4000, lambda: hud.destroy() if hud.winfo_exists() else None)
        except:
            pass

    def _offer_solutions(self):
        """Kullanıcıya çözüm önerileri sunar."""
        try:
            dialog = tk.Toplevel(self.root)
            dialog.title("J.A.R.V.I.S. - Çözüm Önerileri")
            dialog.geometry("500x300+100+100")
            dialog.configure(bg="#1e1e2e")
            dialog.attributes("-topmost", True)
            
            tk.Label(dialog, text="🔧 Tespit Edilen Sorunlara Çözüm Önerileri", font=("Arial", 12, "bold"), fg="#00ffcc", bg="#1e1e2e").pack(pady=10)
            
            text_widget = tk.Text(dialog, wrap="word", width=60, height=12, bg="#2d2d3a", fg="white", font=("Consolas", 9))
            text_widget.pack(padx=10, pady=5)
            
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
            
            text_widget.insert("1.0", "\n".join(suggestions))
            text_widget.config(state="disabled")
            
            def open_web_search():
                import webbrowser
                query = " ".join([a.get("title", a.get("message", "")) for a in self.anomalies_found[:2]])
                if query:
                    webbrowser.open(f"https://www.google.com/search?q={query.replace(' ', '+')}+çözüm")
            
            btn_frame = tk.Frame(dialog, bg="#1e1e2e")
            btn_frame.pack(pady=10)
            tk.Button(btn_frame, text="Web'de Ara", command=open_web_search, bg="#004466", fg="white", relief="flat", padx=10).pack(side="left", padx=5)
            tk.Button(btn_frame, text="Kapat", command=dialog.destroy, bg="#333", fg="white", relief="flat", padx=10).pack(side="left", padx=5)
            
            # Sesli uyarı
            self._beep(1000, 200)
            
        except Exception as e:
            self.log(f"Çözüm penceresi hatası: {e}")

def observer_mode(parameters: Optional[dict] = None, player=None, root=None) -> str:
    """
    Gözlemci modunu başlatır.
    parameters: {
        "duration": 15,  # saniye cinsinden gözlem süresi
        "interactive": True,  # çözüm önerileri gösterilsin mi
        "screenshot": False  # ekran görüntüsü alınsın mı (performans)
    }
    """
    params = parameters or {}
    duration = params.get("duration", 15)
    interactive = params.get("interactive", True)
    
    observer = Observer(player=player, root=root)
    observer.screenshot_enabled = params.get("screenshot", False)
    
    # Arka planda çalıştır
    def run():
        observer.run_observation(duration_seconds=duration, interactive=interactive)
    
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    
    return f"Gözlemci protokolü başlatıldı patron. {duration} saniye boyunca sisteminizi ve ekranınızı izleyeceğim. Bir anormallik tespit edersem size bildireceğim."