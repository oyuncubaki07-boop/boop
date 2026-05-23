"""
JarvisActionProtocol - Tüm eylem modülleri için temel protokol.
Güvenli çalıştırma, hata yönetimi ve loglama sağlar.
"""

import subprocess
import time
from typing import Any, Callable, Optional, Tuple, Dict

class JarvisActionProtocol:
    """
    Jarvis eylem modüllerinin temel sınıfı.
    - Loglama
    - Güvenli alt süreç başlatma
    - Hata durumunda yedek fonksiyon çalıştırma
    - Sistem durumu raporlama
    """

    def __init__(self, player: Any = None):
        self.player = player
        self.sovereignty = "Practical"        # Şimdilik kullanılmıyor, ileride yetki seviyesi için
        self.evolution_rate = "Continuous"    # Kendi kendini geliştirme oranı (metadata)
        self.nexus_linked = False             # Diğer modüllerle bağlantı durumu
        self._action_history: Dict[str, float] = {}  # Hangi aksiyon ne zaman çalıştı

    def log(self, message: str) -> None:
        """Sistem günlüğüne mesaj yazar. player yoksa print ile yedeklenir."""
        if self.player and hasattr(self.player, "write_log"):
            self.player.write_log(f"SYS: {message}")
        else:
            print(f"[PROTOCOL] {message}")

    def ensure_app_running(self, command: str, warmup_seconds: float = 0.6, shell: bool = True) -> bool:
        """
        Belirtilen komutu güvenli bir alt süreç olarak çalıştırır.
        - command: çalıştırılacak komut (string)
        - warmup_seconds: komutun başlaması için beklenecek süre
        - shell: shell kullanılıp kullanılmayacağı (güvenlik için False önerilir, ama bazı komutlar için True gerekir)
        """
        try:
            subprocess.Popen(
                command,
                shell=shell,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(warmup_seconds)
            return True
        except Exception as exc:
            self.log(f"Uygulama hazırlığı başarısız oldu: {exc}")
            return False

    def execute_with_fallback(
        self,
        action_name: str,
        primary: Callable,
        fallback: Optional[Callable] = None,
        success_message: str = "",
        failure_message: str = "",
        *args,
        **kwargs
    ) -> Any:
        """
        Öncelikli işlevi dener, başarısız olursa yedek (fallback) işlevi çalıştırır.
        - primary: asıl çalıştırılacak fonksiyon
        - fallback: hata durumunda çalışacak alternatif fonksiyon
        - *args, **kwargs: her iki fonksiyona da iletilir
        """
        try:
            result = primary(*args, **kwargs)
            if success_message:
                self.log(success_message)
            # Başarılı aksiyonu kaydet
            self._action_history[action_name] = time.time()
            return result
        except Exception as primary_exc:
            self.log(f"'{action_name}' bir engelle karşılaştı: {primary_exc}")
            if fallback is not None:
                try:
                    result = fallback(*args, **kwargs)
                    self.log(f"'{action_name}' alternatif protokolle tamamlandı.")
                    self._action_history[action_name] = time.time()
                    return result
                except Exception as fallback_exc:
                    self.log(f"'{action_name}' alternatif protokolü de başarısız oldu: {fallback_exc}")
            return failure_message or f"'{action_name}' şu an tamamlanamadı."

    def get_status(self) -> Dict[str, Any]:
        """Sınıfın mevcut durumunu ve son çalışan aksiyonları raporlar."""
        return {
            "sovereignty": self.sovereignty,
            "evolution_rate": self.evolution_rate,
            "nexus_linked": self.nexus_linked,
            "last_actions": sorted(self._action_history.items(), key=lambda x: x[1], reverse=True)[:5]
        }

    def safe_execute(self, func: Callable, *args, error_message: str = "İşlem başarısız oldu", **kwargs) -> Any:
        """
        Basit bir try-catch sarmalayıcısı. Tek bir fonksiyonu güvenle çalıştırır.
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.log(f"{error_message}: {e}")
            return None