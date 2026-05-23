"""
lockdown_protocol.py - J.A.R.V.I.S. Acil Durum ve Kilit Protokolü
- Ekran kilitleme (platform bağımsız)
- Kullanıcı oturumunu kapatma
- Sistemi askıya alma / yeniden başlatma
- Acil durum bildirimi (opsiyonel)
"""

import sys
import subprocess
import platform
import tkinter as tk
import winsound
from typing import Optional

def get_platform() -> str:
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    elif system == "darwin":
        return "macos"
    else:
        return "linux"

def lock_screen_windows():
    """Windows'ta ekranı kilitler."""
    try:
        import ctypes
        ctypes.windll.user32.LockWorkStation()
        return True, "Windows ekranı kilitlendi."
    except Exception as e:
        return False, str(e)

def lock_screen_macos():
    """macOS'ta ekranı kilitler."""
    try:
        # macOS'ta ekran kilitleme komutu (Caffeinate ile birlikte çalışır)
        subprocess.run(["osascript", "-e", 'tell application "System Events" to keystroke "q" using {command down, control down}'], 
                       capture_output=True, timeout=5)
        return True, "macOS ekranı kilitlendi."
    except Exception as e:
        return False, str(e)

def lock_screen_linux():
    """Linux'ta ekranı kilitler (GNOME, KDE, vb. için)."""
    try:
        # Önce gnome-screensaver-command, ardından loginctl lock-session dener
        result = subprocess.run(["gnome-screensaver-command", "-l"], capture_output=True)
        if result.returncode == 0:
            return True, "Linux ekranı kilitlendi (gnome-screensaver)."
        result = subprocess.run(["loginctl", "lock-session"], capture_output=True)
        if result.returncode == 0:
            return True, "Linux ekranı kilitlendi (loginctl)."
        # XScreenSaver
        subprocess.run(["xscreensaver-command", "-lock"], capture_output=True)
        return True, "Linux ekranı kilitlendi (xscreensaver)."
    except Exception as e:
        return False, str(e)

def lock_screen():
    """Platforma göre ekranı kilitler."""
    plat = get_platform()
    if plat == "windows":
        return lock_screen_windows()
    elif plat == "macos":
        return lock_screen_macos()
    else:
        return lock_screen_linux()

def logout_user():
    """Kullanıcı oturumunu kapatır."""
    plat = get_platform()
    try:
        if plat == "windows":
            subprocess.run(["shutdown", "-l"], timeout=5)
            return True, "Kullanıcı oturumu kapatılıyor..."
        elif plat == "macos":
            subprocess.run(["osascript", "-e", 'tell application "System Events" to log out'], timeout=5)
            return True, "macOS oturumu kapatılıyor..."
        else:  # Linux
            subprocess.run(["gnome-session-quit", "--no-prompt"], timeout=5)
            return True, "Linux oturumu kapatılıyor..."
    except Exception as e:
        return False, str(e)

def suspend_system():
    """Sistemi askıya alır (uyku modu)."""
    plat = get_platform()
    try:
        if plat == "windows":
            subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0", "1", "0"], timeout=5)
            return True, "Sistem askıya alınıyor..."
        elif plat == "macos":
            subprocess.run(["pmset", "sleepnow"], timeout=5)
            return True, "macOS uyku moduna geçiyor..."
        else:
            subprocess.run(["systemctl", "suspend"], timeout=5)
            return True, "Linux askıya alınıyor..."
    except Exception as e:
        return False, str(e)

def restart_system():
    """Sistemi yeniden başlatır."""
    plat = get_platform()
    try:
        if plat == "windows":
            subprocess.run(["shutdown", "/r", "/t", "0"], timeout=5)
        elif plat == "macos":
            subprocess.run(["shutdown", "-r", "now"], timeout=5)
        else:
            subprocess.run(["reboot"], timeout=5)
        return True, "Sistem yeniden başlatılıyor..."
    except Exception as e:
        return False, str(e)

def show_hud(root, title: str, message: str, color_bg: str = "#660000", beep_freqs: list = None):
    """HUD bildirimi gösterir."""
    if not root:
        return
    try:
        hud = tk.Toplevel(root)
        hud.overrideredirect(True)
        hud.attributes("-topmost", True, "-alpha", 0.95)
        hud.geometry("450x120+10+10")
        hud.configure(bg=color_bg)
        
        tk.Label(hud, text=title, font=("Courier", 12, "bold"), fg="white", bg=color_bg).pack(pady=10)
        tk.Label(hud, text=message, font=("Courier", 10), fg="#ffcccc", bg=color_bg, wraplength=420).pack(pady=5)
        
        if beep_freqs:
            for freq in beep_freqs:
                try:
                    winsound.Beep(freq, 300)
                except:
                    pass
        else:
            try:
                winsound.Beep(800, 200)
            except:
                pass
        
        root.after(4000, lambda: hud.destroy() if hud.winfo_exists() else None)
    except Exception:
        pass

def lockdown_protocol(parameters: Optional[dict] = None, player=None, root=None) -> str:
    """
    Acil durum ve kilit protokolü.
    
    parameters:
        level: "lock" (ekran kilidi), "logout" (oturum kapatma), 
               "suspend" (uyku), "restart" (yeniden başlatma) 
               (varsayılan: "lock")
        silent: False (HUD göster)
    """
    params = parameters or {}
    level = params.get("level", "lock").lower()
    silent = params.get("silent", False)
    
    if player:
        player.write_log(f"SYS: 🔒 LOCKDOWN PROTOCOL başlatıldı -> {level}")
    
    if not silent and root:
        show_hud(root, "🛑 LOCKDOWN PROTOKOLÜ", f"Aksiyon: {level.upper()} başlatılıyor...", "#660000", [1200, 1000, 800])
    
    if level == "lock":
        success, msg = lock_screen()
    elif level == "logout":
        success, msg = logout_user()
    elif level == "suspend":
        success, msg = suspend_system()
    elif level == "restart":
        success, msg = restart_system()
    else:
        return f"Geçersiz lockdown seviyesi: {level}. Kullanılabilir: lock, logout, suspend, restart"
    
    if success:
        return f"✅ {msg} Sistem güvende patron."
    else:
        if player:
            player.write_log(f"SYS: Lockdown hatası: {msg}")
        return f"❌ Lockdown protokolü başarısız: {msg}"