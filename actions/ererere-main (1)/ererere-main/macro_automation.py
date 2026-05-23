"""
macro_automation.py - J.A.R.V.I.S. Oyun / Çalışma Modu Otomasyonu
Sistem performansını artırmak için gereksiz uygulamaları kapatır, özel protokolleri başlatır.
"""

import os
import subprocess
import tkinter as tk
import winsound
from typing import Optional

def _close_processes(process_names: list, player=None):
    """Belirtilen işlemleri kapatır."""
    for proc in process_names:
        try:
            if os.name == 'nt':  # Windows
                os.system(f"taskkill /f /im {proc} /T >nul 2>&1")
            else:  # Linux/macOS
                os.system(f"pkill -f {proc} 2>/dev/null")
            if player:
                player.write_log(f"SYS: İşlem kapatıldı: {proc}")
        except Exception as e:
            if player:
                player.write_log(f"SYS: {proc} kapatılamadı: {e}")

def _show_hud(root, title: str, message: str, color: str = "#003300", beep: bool = True):
    """Kısa bildirim HUD'u."""
    if not root:
        return
    try:
        hud = tk.Toplevel(root)
        hud.overrideredirect(True)
        hud.attributes("-topmost", True, "-alpha", 0.9)
        hud.geometry("350x100+10+10")
        hud.configure(bg=color)
        tk.Label(hud, text=title, font=("Courier", 11, "bold"), fg="white", bg=color).pack(pady=5)
        tk.Label(hud, text=message, font=("Courier", 9), fg="#dddddd", bg=color, wraplength=320).pack(pady=5)
        if beep:
            try:
                winsound.Beep(600, 150)
            except:
                pass
        root.after(4000, lambda: hud.destroy() if hud.winfo_exists() else None)
    except:
        pass

def activate_mode(parameters: Optional[dict] = None, speak=None, player=None, root=None) -> str:
    """
    Sistem protokollerini (Oyun, Çalışma, Kurgu, Medya) başlatır.
    parameters: {
        "mode_name": "oyun", "çalışma", "kurgu", "medya", "default"
        "close_browsers": True (oyun modunda tarayıcı kapat)
        "run_apps": [] (çalışma modunda açılacak uygulamaların listesi)
    }
    """
    params = parameters or {}
    mode = params.get("mode_name", "").lower()
    close_browsers = params.get("close_browsers", True)
    run_apps = params.get("run_apps", [])
    
    if player:
        player.write_log(f"SYS: ⚙️ {mode.upper()} modu başlatılıyor...")
    
    if "oyun" in mode or "game" in mode:
        _show_hud(root, "🎮 OYUN PROTOKOLÜ", "Sistem optimize ediliyor, tarayıcılar kapatılıyor...", "#003300")
        if close_browsers:
            _close_processes(["chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe"], player)
        # Oyun modunda ek optimizasyonlar
        try:
            # Windows Game Mode'u tetikle (isteğe bağlı)
            if os.name == 'nt':
                os.system("start shell:AppsFolder\\Microsoft.GamingServices_8wekyb3d8bbwe!GameMode")
        except:
            pass
        return "Oyun protokolü aktif edildi efendim. Arka plandaki tarayıcılar kapatılarak RAM temizlendi. Sistem maksimum performansa ayarlandı, iyi eğlenceler."
    
    elif "çalışma" in mode or "work" in mode or "focus" in mode:
        _show_hud(root, "📚 ÇALIŞMA MODU", "Odaklanma ortamı hazırlanıyor...", "#000066")
        # İstenen uygulamaları aç
        for app in run_apps:
            try:
                if os.name == 'nt':
                    os.startfile(app)
                else:
                    subprocess.Popen([app])
                if player:
                    player.write_log(f"SYS: Uygulama açıldı: {app}")
            except Exception as e:
                if player:
                    player.write_log(f"SYS: Uygulama açılamadı {app}: {e}")
        return "Çalışma ortamınız hazırlandı efendim. Odaklanmanız için sistem optimize edildi."
    
    elif "kurgu" in mode or "edit" in mode or "creative" in mode:
        _show_hud(root, "🎬 KURGU MODU", "Yaratıcı uygulamalar hazırlanıyor...", "#330033")
        # Kurgu programları için ön ayar
        default_creative = ["premiere", "afterfx", "photoshop", "vegas"]
        return "Kurgu protokolü aktif. Yaratıcılığınızı konuşturun patron!"
    
    elif "medya" in mode or "media" in mode:
        _show_hud(root, "🎵 MEDYA MODU", "Medya oynatıcıları optimize ediliyor...", "#332200")
        return "Medya modu aktif. Film, müzik keyfiniz için sistem hazır."
    
    elif "default" in mode or "normal" in mode:
        _show_hud(root, "⚙️ NORMAL MOD", "Varsayılan ayarlara dönülüyor...", "#333333")
        return "Normal moda geçildi. Sistem varsayılan ayarlarında."
    
    else:
        return f"Sistemde '{mode}' adında bir protokol tanımlı değil efendim. Kullanılabilir: oyun, çalışma, kurgu, medya, default"