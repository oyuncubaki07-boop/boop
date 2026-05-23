# core/brain.py
# J.A.R.V.I.S. Bilinç ve Otonom Karar Motoru

import ctypes
import datetime
import json
import threading
import time
import sys
from pathlib import Path

import psutil

# Actions (fallback ile)
try:
    from actions.lockdown_protocol import lockdown_protocol
except ImportError:
    def lockdown_protocol(parameters=None, player=None, **kwargs):
        return "Kilitlenme protokolü modülü eksik."

try:
    from actions.morning_briefing import morning_briefing
except ImportError:
    def morning_briefing(parameters=None, player=None, **kwargs):
        return "Sabah brifingi modülü eksik."

try:
    from actions.night_mode import night_mode
except ImportError:
    def night_mode(parameters=None, player=None, **kwargs):
        return "Gece modu modülü eksik."

try:
    from actions.performance_boost import performance_boost
except ImportError:
    def performance_boost(parameters=None, player=None, **kwargs):
        return "Performans artırma modülü eksik."

try:
    from actions.workspace_mode import workspace_mode
except ImportError:
    def workspace_mode(parameters=None, player=None, **kwargs):
        return "Çalışma alanı modülü eksik."

# Core modüller (fallback ile)
try:
    from core.audit_engine import ProjectAuditEngine
except ImportError:
    ProjectAuditEngine = None
    print("[UYARI] core.audit_engine bulunamadı, proje denetimi devre dışı.")

try:
    from core.omni_directive import OmniDirective
except ImportError:
    OmniDirective = None
    print("[UYARI] core.omni_directive bulunamadı, direktif sistemi devre dışı.")

BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "memory"
CONFIG_CANDIDATES = [
    BASE_DIR / "config" / "api_keys.json",
    BASE_DIR / "ui" / "config" / "api_keys.json",
]

class JarvisConsciousness:
    """
    J.A.R.V.I.S. bilinç ve otonom karar motoru.
    Zaman farkındalığı, donanım refleksleri, davranış analizi ve periyodik raporlama yapar.
    """

    def __init__(self, ui_player, speak_callback=None):
        self.player = ui_player
        self.speak = speak_callback
        self.is_active = True
        self.current_state = "IDLE"
        self.last_report_at = None
        self.last_morning_greeted = None  # Bugün sabah brifingi yapıldı mı?
        self.last_night_mode_activated = None  # Bu gece gece modu aktif mi?
        
        # Opsiyonel modüller
        self.directive = None
        if OmniDirective is not None:
            try:
                self.directive = OmniDirective(BASE_DIR)
            except Exception as e:
                self._log(f"OmniDirective başlatılamadı: {e}")
        
        self.audit_engine = None
        if ProjectAuditEngine is not None:
            try:
                self.audit_engine = ProjectAuditEngine(BASE_DIR)
            except Exception as e:
                self._log(f"ProjectAuditEngine başlatılamadı: {e}")
        
        self._stop_event = threading.Event()
        
        # Windows'ta uyku modunu engelle (sadece Windows)
        if sys.platform == "win32":
            try:
                ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
            except Exception:
                pass
        
        self._start_background_tasks()
        self._log("Bilinç motoru çevrimiçi. Analiz ve koruma katmanları aktif.")
        if self.speak:
            self.speak("Bilinç motoru aktif, efendim. Her şey kontrolüm altında.")

    def _log(self, message: str):
        """Sistem logu yaz."""
        if hasattr(self.player, "write_log"):
            self.player.write_log(f"SYS: {message}")
        else:
            print(f"[BRAIN] {message}")

    def _start_background_tasks(self):
        """Arka plan thread'lerini başlat."""
        tasks = [
            self._time_awareness,
            self._behavior_analyzer,
            self._hardware_reflex,
            self._background_api_check,
            self._scheduled_reporting,
        ]
        for task in tasks:
            t = threading.Thread(target=task, daemon=True)
            t.start()

    def _wait_or_stop(self, seconds: float) -> bool:
        """Bekle veya durdurma sinyali gelirse çık."""
        return self._stop_event.wait(seconds)

    def _read_api_keys(self) -> dict:
        """API anahtarlarını config dosyasından okur."""
        for path in CONFIG_CANDIDATES:
            try:
                if path.exists():
                    with open(path, "r", encoding="utf-8") as f:
                        return json.load(f)
            except Exception:
                continue
        return {}

    def create_analysis_report(self) -> Path:
        """Sistem analiz raporu oluşturur."""
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        battery = psutil.sensors_battery()
        
        # Proje denetim özeti
        audit_summary = {}
        if self.audit_engine:
            try:
                audit_summary = self.audit_engine.run()
            except Exception as e:
                self._log(f"Audit hatası: {e}")
                audit_summary = {}
        
        payload = {
            "timestamp": datetime.datetime.now().isoformat(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
            "battery_percent": getattr(battery, "percent", None),
            "battery_plugged": getattr(battery, "power_plugged", None),
            "top_processes": [],
            "project_audit_summary": {
                "scanned_files": audit_summary.get("scanned_files", 0),
                "total_findings": audit_summary.get("total_findings", 0),
                "by_kind": audit_summary.get("by_kind", {}),
            },
        }
        
        # Opsiyonel direktif bilgileri
        if self.directive:
            try:
                payload["context_snapshot"] = self.directive.build_context_snapshot()
                payload["intent_matrix"] = self.directive.infer_intent_matrix("sistem durumunu analiz et")
                payload["fallback_protocols"] = {
                    "api": self.directive.build_fallback_protocol("api"),
                    "audio": self.directive.build_fallback_protocol("audio"),
                }
            except Exception as e:
                self._log(f"Direktif bilgisi alınamadı: {e}")
        
        # En çok kaynak tüketen işlemler
        try:
            processes = []
            for proc in psutil.process_iter(["name", "cpu_percent", "memory_percent"]):
                try:
                    info = proc.info
                    processes.append({
                        "name": info.get("name", "?"),
                        "cpu_percent": info.get("cpu_percent", 0),
                        "memory_percent": round(info.get("memory_percent") or 0, 2),
                    })
                except:
                    continue
            payload["top_processes"] = sorted(
                processes,
                key=lambda item: (item["cpu_percent"] or 0, item["memory_percent"] or 0),
                reverse=True,
            )[:10]
        except Exception as e:
            self._log(f"İşlem listesi alınamadı: {e}")
        
        # Raporu kaydet
        report_path = REPORTS_DIR / "jarvis_analysis_report.json"
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            self.last_report_at = payload["timestamp"]
            self._log(f"Analiz raporu oluşturuldu: {report_path.name}")
        except Exception as e:
            self._log(f"Rapor yazılamadı: {e}")
        
        return report_path

    def _background_api_check(self):
        """Arka planda API anahtarlarını kontrol eder (6 saatte bir)."""
        while self.is_active:
            try:
                api_keys = self._read_api_keys()
                missing = []
                required_keys = ["gemini_api_key", "openrouter_api_key", "mistral_api_key", "cohere_api_key"]
                for key_name in required_keys:
                    if not str(api_keys.get(key_name, "")).strip():
                        missing.append(key_name)
                if missing:
                    self._log(f"Eksik API anahtarları: {', '.join(missing)}")
                else:
                    self._log("API anahtarları kontrol edildi, tümü mevcut.")
            except Exception as e:
                self._log(f"API kontrol hatası: {e}")
            
            if self._wait_or_stop(21600):  # 6 saat
                break

    def _scheduled_reporting(self):
        """Periyodik raporlama (her 2 saatte bir)."""
        while self.is_active:
            try:
                self.create_analysis_report()
            except Exception as e:
                self._log(f"Rapor oluşturma hatası: {e}")
            
            if self._wait_or_stop(7200):  # 2 saat
                break

    def _time_awareness(self):
        """Zaman farkındalığı: sabah brifingi, gece modu."""
        while self.is_active:
            now = datetime.datetime.now()
            today = now.date()
            
            # Sabah brifingi (sabah 06:30, günde bir kere)
            if now.hour == 6 and now.minute >= 30 and now.minute < 35:
                if self.last_morning_greeted != today:
                    self._log("Sabah protokolü başlatılıyor.")
                    try:
                        morning_briefing(parameters={}, player=self.player)
                        if self.speak:
                            self.speak("Günaydın efendim. Sabah brifingi hazır.")
                    except Exception as e:
                        self._log(f"Sabah brifingi hatası: {e}")
                    self.last_morning_greeted = today
            
            # Gece modu (23:00 - 05:00 arasında, günde bir kere)
            if 23 <= now.hour or now.hour < 5:
                if self.last_night_mode_activated != today and self.current_state != "SLEEP":
                    self.current_state = "SLEEP"
                    try:
                        night_mode(parameters={}, player=self.player)
                        self._log("Gece sessizliği aktif.")
                        if self.speak:
                            self.speak("Gece moduna geçiliyor, efendim. Sessizlik korunacak.")
                    except Exception as e:
                        self._log(f"Gece modu hatası: {e}")
                    self.last_night_mode_activated = today
            else:
                if self.current_state == "SLEEP":
                    self.current_state = "IDLE"
                    self._log("Gece modu sona erdi, normal operasyon.")
            
            if self._wait_or_stop(60):
                break

    def _behavior_analyzer(self):
        """Davranış analizi: gece geç saatlerde oyun oynama tespiti."""
        while self.is_active:
            try:
                now = datetime.datetime.now()
                # Gece 01:00 - 05:00 arası kontrol
                if 1 <= now.hour <= 5:
                    # Oyun süreçlerini kontrol et
                    game_keywords = ["steam", "epicgames", "valorant", "league", "battle", "origin", "blizzard"]
                    open_apps = []
                    for proc in psutil.process_iter(["name"]):
                        try:
                            name = proc.info["name"]
                            if name:
                                open_apps.append(name.lower())
                        except:
                            continue
                    
                    is_gaming = any(keyword in " ".join(open_apps) for keyword in game_keywords)
                    if is_gaming:
                        self._log("Gece disiplini ihlali algılandı. Odak protokolü uygulanıyor.")
                        try:
                            lockdown_protocol(parameters={"level": "focus", "minutes": 60}, player=self.player)
                            workspace_mode(parameters={}, player=self.player)
                            if self.speak:
                                self.speak("Gece geç saatte oyun tespit ettim. Odak modunu etkinleştiriyorum.")
                        except Exception as e:
                            self._log(f"Disiplin protokolü hatası: {e}")
            except Exception as e:
                self._log(f"Davranış analizörü hatası: {e}")
            
            if self._wait_or_stop(60):  # her dakika kontrol et
                break

    def _hardware_reflex(self):
        """Donanım refleksi: yüksek CPU/RAM durumunda performans artırma."""
        boost_cooldown = 0  # saniye cinsinden cooldown
        while self.is_active:
            try:
                cpu = psutil.cpu_percent(interval=2)
                ram = psutil.virtual_memory().percent
                
                if (cpu > 90 or ram > 85) and boost_cooldown <= 0:
                    self._log(f"Darboğaz tespit edildi. CPU %{cpu}, RAM %{ram}. Performans protokolü başlatılıyor.")
                    try:
                        performance_boost(parameters={}, player=self.player)
                        self.create_analysis_report()
                        if self.speak:
                            self.speak("Sistem darboğazı algılandı, performans artırma yapılıyor.")
                        boost_cooldown = 300  # 5 dakika cooldown
                    except Exception as e:
                        self._log(f"Performans boost hatası: {e}")
                elif boost_cooldown > 0:
                    boost_cooldown -= 10
            except Exception as e:
                self._log(f"Donanım refleksi hatası: {e}")
            
            if self._wait_or_stop(10):
                break

    def manuel_guncelleme(self):
        """Manuel analiz ve rapor yenileme."""
        try:
            report_path = self.create_analysis_report()
            self._log(f"Manuel analiz tamamlandı: {report_path.name}")
            if self.speak:
                self.speak("Manuel sistem analizi tamamlandı efendim.")
        except Exception as e:
            self._log(f"Manuel güncelleme hatası: {e}")

    def stop(self):
        """Bilinç motorunu durdur."""
        self.is_active = False
        self._stop_event.set()
        self._log("Bilinç motoru güvenli kapanış moduna alındı.")
        if self.speak:
            self.speak("Bilinç motoru kapatılıyor, efendim.")