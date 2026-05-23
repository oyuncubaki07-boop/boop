"""
behavior_analyzer.py - J.A.R.V.I.S. Davranış Analizörü
Kullanıcının aktivite seviyesini izler, odak dağılması durumunda uyarı ve motivasyon mesajları verir.
"""

import time
from typing import Optional, List, Dict, Any
from datetime import datetime

class BehaviorAnalyzer:
    """
    Kullanıcı davranışlarını analiz eden sınıf.
    - Boşta kalma süresini takip eder
    - Belirli eşiklerde uyarı mesajları üretir
    - İlerleme kaydedildiğinde tebrik eder
    """

    def __init__(self, threshold_seconds: int = 1200, max_warnings: int = 3):
        """
        threshold_seconds: Boşta kalma eşiği (saniye, varsayılan 20 dakika = 1200)
        max_warnings: Maksimum uyarı sayısı (sonrasında daha sert uyarı)
        """
        self.threshold = threshold_seconds
        self.max_warnings = max_warnings
        self.idle_start_time: Optional[float] = None
        self.warnings_given = 0
        self.last_warning_time: Optional[float] = None
        self.total_idle_time = 0.0
        self.session_start = time.time()

        # Uyarı mesajları (seviye bazlı)
        self.warning_messages = {
            1: [
                "Komutan, eylem yok. Odaklanman gereken işten kaçıyorsun.",
                "Dikkat dağılması tespit edildi. Hedeflerine geri dön.",
                "Zaman akıyor, sen duruyorsun. Harekete geç!"
            ],
            2: [
                "Zaman akıyor, sen duruyorsun. Amerika'ya gitmek ve AI imparatorluğunu kurmak yatarak olmaz. Hemen işinin başına dön.",
                "Bu gidişle hedeflerine ulaşamayacaksın. Disiplin şart!",
                "İkinci uyarı: Lütfen işine odaklan. Başarıya giden yol çalışmaktan geçer."
            ],
            3: [
                "Sistem uyarısı: Disiplin ihlali tespit edildi. Mazeret üretmeyi bırak ve klavyenin başına geç!",
                "Son uyarı! Eğer devam edersen, performans puanın düşecek. Hemen toparlan!"
            ]
        }

        # Motivasyon mesajları (aktif hale dönünce)
        self.motivation_messages = [
            "İşte bu! Geri döndün. Şimdi devam et, başaracaksın! 💪",
            "Harika, tekrar odaklandın. Hedeflerine bir adım daha yaklaştın.",
            "Disiplinini topladın. İşte benim komutanım! 🚀"
        ]

    def log(self, message: str) -> None:
        """Sistem günlüğü için (isteğe bağlı)."""
        print(f"[BEHAVIOR] {message}")

    def check_activity(self, is_active: bool, current_task: str = "") -> Optional[str]:
        """
        Aktivite durumunu kontrol eder.
        - is_active: Kullanıcı aktif mi (True/False)
        - current_task: Şu anki görev (opsiyonel, mesajlarda kullanılabilir)
        Dönüş: Uyarı mesajı varsa string, yoksa None
        """
        now = time.time()

        if is_active:
            # Aktif duruma geçiş
            if self.idle_start_time is not None:
                idle_duration = now - self.idle_start_time
                self.total_idle_time += idle_duration
                self.idle_start_time = None
                
                # Eğer boşta kalma süresi eşiği geçmişse ve daha önce uyarı verilmişse, tebrik et
                if idle_duration > self.threshold and self.warnings_given > 0:
                    self.warnings_given = 0
                    return self._get_motivation_message()
            return None
        else:
            # Pasif durum
            if self.idle_start_time is None:
                self.idle_start_time = now
                return None
            
            idle_seconds = now - self.idle_start_time
            if idle_seconds > self.threshold:
                return self._trigger_warning()
            return None

    def _trigger_warning(self) -> str:
        """Uyarı tetikler. Seviyeye göre uygun mesajı seçer."""
        self.warnings_given += 1
        self.last_warning_time = time.time()
        # Sayacı sıfırlamak yerine, her uyarıda eşik kadar daha beklet
        self.idle_start_time = time.time()

        # Seviyeyi sınırla
        level = min(self.warnings_given, self.max_warnings)
        messages = self.warning_messages.get(level, self.warning_messages[3])
        import random
        return random.choice(messages)

    def _get_motivation_message(self) -> str:
        """Aktif duruma dönüşte motivasyon mesajı."""
        import random
        return random.choice(self.motivation_messages)

    def get_stats(self) -> Dict[str, Any]:
        """İstatistikleri döndürür."""
        total_session = time.time() - self.session_start
        return {
            "total_session_seconds": round(total_session, 1),
            "total_idle_seconds": round(self.total_idle_time, 1),
            "active_percentage": round((1 - self.total_idle_time / total_session) * 100, 1) if total_session > 0 else 100,
            "warnings_given": self.warnings_given,
            "last_warning_time": datetime.fromtimestamp(self.last_warning_time).strftime("%H:%M:%S") if self.last_warning_time else None
        }

    def reset(self) -> None:
        """Tüm sayaçları sıfırlar (yeni oturum başlangıcı)."""
        self.idle_start_time = None
        self.warnings_given = 0
        self.last_warning_time = None
        self.total_idle_time = 0.0
        self.session_start = time.time()