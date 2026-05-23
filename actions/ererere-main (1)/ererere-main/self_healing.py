"""
self_healing.py - J.A.R.V.I.S. Kendi Kendini İyileştirme ve Hata Düzeltme Sistemi
Hataları yakalar, analiz eder ve otomatik olarak düzeltmeye çalışır.
"""

import sys
import traceback
import importlib
import subprocess
from typing import Dict, Any, Optional, Callable
from pathlib import Path

class SelfHealingSystem:
    """
    J.A.R.V.I.S.'in hata yakalama ve kendi kendini düzeltme sistemi.
    - Hata loglama
    - Otomatik modül yeniden yükleme
    - Eksik bağımlılıkları yükleme
    - Kod düzeltme önerileri
    """
    
    def __init__(self, player=None):
        self.player = player
        self.error_log = []
        self.fixed_errors = []
        
    def log(self, msg: str):
        if self.player and hasattr(self.player, "write_log"):
            self.player.write_log(f"SYS: {msg}")
        else:
            print(f"[SELF-HEALING] {msg}")
    
    def capture_error(self, error: Exception, context: str = "") -> Dict[str, Any]:
        """Hatayı yakalar ve loglar."""
        error_info = {
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
            "context": context,
            "timestamp": __import__('time').time()
        }
        self.error_log.append(error_info)
        self.log(f"Hata yakalandı: {error_info['type']} - {error_info['message'][:100]}")
        return error_info
    
    def suggest_fix(self, error_info: Dict[str, Any]) -> Optional[str]:
        """Hata için olası çözüm önerir."""
        error_type = error_info["type"]
        error_msg = error_info["message"].lower()
        
        suggestions = {
            "ModuleNotFoundError": "Gerekli modül yüklü değil. 'pip install [modul_adi]' ile yükleyin.",
            "ImportError": "Modül veya sınıf bulunamadı. Dosya adını ve yolunu kontrol edin.",
            "FileNotFoundError": "Dosya bulunamadı. Dosya yolunu kontrol edin.",
            "KeyError": "Sözlükte anahtar bulunamadı. Anahtarın varlığını kontrol edin.",
            "AttributeError": "Nesne özelliği bulunamadı. Nesne tipini kontrol edin.",
            "TypeError": "Tip hatası. Değişken tiplerini kontrol edin.",
            "ValueError": "Değer hatası. Girilen değeri kontrol edin.",
            "ConnectionError": "Bağlantı hatası. İnternet bağlantınızı kontrol edin.",
            "TimeoutError": "Zaman aşımı. Bağlantı hızınızı kontrol edin.",
        }
        
        for err, suggestion in suggestions.items():
            if err in error_type:
                return suggestion
        
        if "api" in error_msg or "key" in error_msg:
            return "API anahtarı hatası. config/api_keys.json dosyasını kontrol edin."
        elif "permission" in error_msg:
            return "Yetki hatası. Programı yönetici olarak çalıştırmayı deneyin."
        elif "memory" in error_msg:
            return "Bellek hatası. Bilgisayarınızı yeniden başlatmayı deneyin."
        
        return None
    
    def auto_fix_module(self, module_name: str) -> bool:
        """Eksik modülü otomatik yüklemeye çalışır."""
        try:
            self.log(f"Modül yükleniyor: {module_name}")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", module_name],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                self.log(f"✅ Modül başarıyla yüklendi: {module_name}")
                return True
            else:
                self.log(f"❌ Modül yüklenemedi: {result.stderr[:200]}")
                return False
        except Exception as e:
            self.log(f"Modül yükleme hatası: {e}")
            return False
    
    def reload_module(self, module_path: str) -> bool:
        """Modülü yeniden yükler."""
        try:
            module_name = module_path.replace("/", ".").replace("\\", ".").replace(".py", "")
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
                self.log(f"✅ Modül yeniden yüklendi: {module_name}")
                return True
            else:
                self.log(f"Modül bulunamadı: {module_name}")
                return False
        except Exception as e:
            self.log(f"Modül yeniden yükleme hatası: {e}")
            return False
    
    def heal(self, error: Exception, context: str = "") -> Dict[str, Any]:
        """Hatayı iyileştirmeye çalışır."""
        error_info = self.capture_error(error, context)
        suggestion = self.suggest_fix(error_info)
        
        result = {
            "healed": False,
            "error": error_info,
            "suggestion": suggestion,
            "action_taken": None
        }
        
        # Modül bulunamadı hatasını düzeltmeyi dene
        if error_info["type"] == "ModuleNotFoundError":
            import re
            match = re.search(r"No module named '(\w+)'", error_info["message"])
            if match:
                module_name = match.group(1)
                if self.auto_fix_module(module_name):
                    result["healed"] = True
                    result["action_taken"] = f"Modül yüklendi: {module_name}"
        
        # İmport hatasını düzeltmeyi dene
        elif error_info["type"] == "ImportError":
            # Modül yeniden yüklemeyi dene
            if "context" in error_info and error_info["context"]:
                if self.reload_module(error_info["context"]):
                    result["healed"] = True
                    result["action_taken"] = f"Modül yeniden yüklendi: {error_info['context']}"
        
        if result["healed"]:
            self.fixed_errors.append(error_info)
            self.log(f"✅ Hata iyileştirildi: {error_info['type']}")
        else:
            self.log(f"❌ Hata iyileştirilemedi: {error_info['type']}")
        
        return result