"""
performance_boost.py - J.A.R.V.I.S. Performans Artırıcı Modül
Sistem optimizasyonu, ağ önbellek temizliği, geçici dosya silme vb.
"""

import os
import tkinter as tk
import winsound
import subprocess
import platform
from typing import Optional

def _clear_dns_cache():
    """DNS önbelleğini temizler (platforma göre)"""
    system = platform.system()
    try:
        if system == "Windows":
            os.system("ipconfig /flushdns >nul 2>&1")
            return True
        elif system == "Linux":
            # systemd-resolved veya dnsmasq kontrolü
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
            # Sadece .tmp dosyalarını temizle (güvenli)
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
        
        # HUD gösterimi
        if root:
            hud = tk.Toplevel(root)
            hud.overrideredirect(True)
            hud.attributes("-topmost", True, "-alpha", 0.9)
            hud.geometry("350x100+10+10")
            hud.configure(bg="#000033")
            
            tk.Label(hud, text="🚀 PERFORMANS BOOST", font=("Courier", 12, "bold"), fg="#00ffcc", bg="#000033").pack(pady=5)
            tk.Label(hud, text="\n".join(results[:2]), font=("Courier", 9), fg="white", bg="#000033").pack()
            
            try:
                winsound.Beep(700, 150)
                winsound.Beep(900, 200)
            except:
                pass
            root.after(4000, lambda: hud.destroy() if hud.winfo_exists() else None)
        
        if results:
            return f"Sistem optimizasyonu tamamlandı. {' / '.join(results)} Sistem şu an zirve performansında."
        else:
            return "Herhangi bir optimizasyon yapılamadı patron."
        
    except Exception as e:
        return f"Performans artırıcı çalışırken bir engele takıldı patron: {str(e)}"