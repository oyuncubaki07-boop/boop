"""
night_mode.py - J.A.R.V.I.S. Gece Modu Protokolü
Sistem ses seviyesini düşürür, ekran parlaklığını azaltır (Windows'ta), 
bildirimleri kısar ve gece kullanımı için ortamı optimize eder.
"""

import pyautogui
import tkinter as tk
import winsound
import subprocess
import sys
import platform
from typing import Optional

def set_volume_windows(level: int):
    """Windows'ta ses seviyesini belirler (0-100 arası)."""
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMasterVolumeLevelScalar(level / 100.0, None)
        return True
    except ImportError:
        # pycaw yoksa eski yöntem: volume tuşları simülasyonu
        current = 50
        for _ in range(current // 2):
            pyautogui.press("volumedown")
        for _ in range(level // 2):
            pyautogui.press("volumeup")
        return True
    except Exception:
        return False

def set_brightness_windows(level: int):
    """Windows'ta ekran parlaklığını ayarlar (0-100 arası)."""
    try:
        import screen_brightness_control as sbc
        sbc.set_brightness(level)
        return True
    except ImportError:
        return False

def night_mode(parameters: Optional[dict] = None, player=None, root=None) -> str:
    """
    Gece modunu aktif eder.
    parameters: {
        "volume": 12,          # hedef ses seviyesi (0-100), varsayılan 12
        "brightness": 20,      # hedef parlaklık (0-100), varsayılan 20 (Windows + sbc)
        "mute": False,         # tamamen sessize al (ses seviyesi 0)
        "restore": False       # önceki ayarlara dön (ileride geliştirilecek)
    }
    """
    params = parameters or {}
    restore = params.get("restore", False)
    
    if restore:
        # İleride önceki ayarları döndürme eklenebilir
        return "Henüz geri yükleme desteği eklenmedi. Manuel olarak ses/parlaklık ayarlarını düzeltebilirsiniz patron."
    
    # Hedef ses seviyesi
    if params.get("mute", False):
        target_volume = 0
        volume_desc = "tamamen sessize alındı"
    else:
        target_volume = params.get("volume", 12)
        target_volume = max(0, min(100, target_volume))
        volume_desc = f"%{target_volume} seviyesine düşürüldü"
    
    if player:
        player.write_log(f"SYS: 🦇 Gece Kuşu protokolü başlatılıyor... (ses {volume_desc})")
    
    # Ses seviyesini ayarla
    system = platform.system()
    if system == "Windows":
        set_volume_windows(target_volume)
    else:
        # macOS/Linux için alternatif (pulsemixer veya osascript)
        if system == "Darwin":
            subprocess.run(["osascript", "-e", f"set volume output volume {target_volume}"], capture_output=True)
        else:  # Linux
            try:
                subprocess.run(["amixer", "set", "Master", f"{target_volume}%"], capture_output=True)
            except:
                pass
    
    # Parlaklık ayarı (sadece Windows + screen_brightness_control varsa)
    if system == "Windows":
        target_brightness = params.get("brightness", 20)
        target_brightness = max(0, min(100, target_brightness))
        if set_brightness_windows(target_brightness):
            brightness_msg = f" Parlaklık %{target_brightness} seviyesine ayarlandı."
        else:
            brightness_msg = " Parlaklık ayarı için 'screen-brightness-control' kütüphanesi gerekli (pip install screen-brightness-control)."
            if player:
                player.write_log(f"SYS: {brightness_msg}")
            brightness_msg = ""
    else:
        brightness_msg = ""
    
    # HUD gösterimi
    if root:
        try:
            hud = tk.Toplevel(root)
            hud.overrideredirect(True)
            hud.attributes("-topmost", True, "-alpha", 0.85)
            hud.geometry("320x90+10+10")
            hud.configure(bg="#000000")
            
            tk.Label(hud, text="🦇 GECE KUŞU PROTOKOLÜ", font=("Courier", 11, "bold"), fg="#6666ff", bg="#000000").pack(pady=5)
            tk.Label(hud, text=f"Ses {volume_desc}.{brightness_msg.split('.')[0] if brightness_msg else ''}", font=("Courier", 9), fg="gray", bg="#000000").pack()
            
            winsound.Beep(400, 100)
            root.after(4000, lambda: hud.destroy() if hud.winfo_exists() else None)
        except Exception as e:
            if player:
                player.write_log(f"SYS: HUD hatası: {e}")
    
    return f"Gece moduna geçildi patron. Ses {volume_desc}.{brightness_msg} Çevreyi rahatsız etmemek için gerekli düzenlemeler yapıldı."