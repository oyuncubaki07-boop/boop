"""
performance_boost.py - J.A.R.V.I.S. Performans Artırıcı Modül (PyQt6)
Sistem optimizasyonu, ağ önbellek temizliği, geçici dosya silme vb.
"""

import os
import winsound
import subprocess
import platform
from typing import Optional

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer


def _clear_dns_cache():
    """DNS önbelleğini temizler (platforma göre)"""
    system = platform.system()
    try:
        if system == "Windows":
            os.system("ipconfig /flushdns >nul 2>&1")
            return True
        elif system == "Linux":
            subprocess.run(["sudo", "systemctl", "restart", "systemd-resolved"], capture_output=True)
            return True
        elif system == "Darwin":  # macOS
            subprocess.run(["sudo", "killall", "-HUP", "mDNSResponder"], capture_output=True)
            return True
    except:
        pass
    return False


def _clear_temp_files():
    """Geçici dosyaları temizler (Windows temp klasörü)"""
    try:
        temp_path = os.environ.get("TEMP", "")
        if temp_path and os.path.exists(temp_path):
            for file in os.listdir(temp_path):
                if file.endswith(".tmp"):
                    try:
                        os.remove(os.path.join(temp_path, file))
                    except:
                        pass
        return True
    except:
        return False


def performance_boost(parameters: Optional[dict] = None, player=None, root=None) -> str:
    """
    Sistem performansını artırır.
    parameters: {
        "action": "dns" (sadece DNS), "temp" (sadece temp), "all" (tümü - varsayılan)
    }
    """
    params = parameters or {}
    action = params.get("action", "all").lower()
    
    if player:
        player.write_log("SYS: 🚀 Performans artırıcı devreye giriyor...")
    
    results = []
    
    try:
        if action in ["all", "dns"]:
            if _clear_dns_cache():
                results.append("DNS önbelleği temizlendi")
            else:
                results.append("DNS temizleme başarısız")
        
        if action in ["all", "temp"]:
            if _clear_temp_files():
                results.append("Geçici dosyalar temizlendi")
            else:
                results.append("Geçici dosya temizleme başarısız")
        
        # PyQt6 HUD gösterimi
        if root and isinstance(root, QWidget):
            hud = QWidget(root)
            hud.setWindowFlags(
                Qt.WindowType.FramelessWindowHint |
                Qt.WindowType.WindowStaysOnTopHint
            )
            hud.setWindowOpacity(0.9)
            hud.setGeometry(10, 10, 350, 100)
            hud.setStyleSheet("background-color: #000033;")

            layout = QVBoxLayout(hud)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(4)

            title_label = QLabel("🚀 PERFORMANS BOOST")
            title_label.setStyleSheet("color: #00ffcc; font-family: 'Courier New'; font-size: 12px; font-weight: bold;")
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(title_label)

            results_label = QLabel("\n".join(results[:2]))
            results_label.setStyleSheet("color: white; font-family: 'Courier New'; font-size: 9px;")
            results_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(results_label)

            hud.show()

            try:
                winsound.Beep(700, 150)
                winsound.Beep(900, 200)
            except:
                pass
            
            QTimer.singleShot(4000, hud.close)
        
        if results:
            return f"Sistem optimizasyonu tamamlandı. {' / '.join(results)} Sistem şu an zirve performansında."
        else:
            return "Herhangi bir optimizasyon yapılamadı patron."
        
    except Exception as e:
        return f"Performans artırıcı çalışırken bir engele takıldı patron: {str(e)}"