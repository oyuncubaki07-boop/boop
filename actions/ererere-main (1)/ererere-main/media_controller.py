"""
media_controller.py - J.A.R.V.I.S. Medya Kontrol Modülü
Müzik/video oynatma, durdurma, sonraki/önceki, ses aç/kıs/sustur işlemleri.
Platform: Windows, macOS, Linux (kısmi).
"""

import sys
import platform
import tkinter as tk
import winsound
from typing import Optional

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

def get_platform() -> str:
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    elif system == "darwin":
        return "macos"
    else:
        return "linux"

def _get_media_keys():
    """Platforma göre medya tuşlarını döndürür."""
    plat = get_platform()
    if plat == "windows":
        return {
            "playpause": "playpause",
            "nexttrack": "nexttrack",
            "prevtrack": "prevtrack",
            "volumeup": "volumeup",
            "volumedown": "volumedown",
            "volumemute": "volumemute"
        }
    elif plat == "macos":
        # macOS'te medya tuşları farklı: play/pause, next, previous genelde F7,F8,F9 gibi
        # pyautogui ile gönderilebilir mi? Çoğu durumda çalışır.
        return {
            "playpause": "playpause",
            "nexttrack": "nexttrack",
            "prevtrack": "prevtrack",
            "volumeup": "volumeup",
            "volumedown": "volumedown",
            "volumemute": "volumemute"
        }
    else:  # Linux
        # Çoğu Linux masaüstü XF86 medya tuşlarını anlar
        return {
            "playpause": "XF86AudioPlay",
            "nexttrack": "XF86AudioNext",
            "prevtrack": "XF86AudioPrev",
            "volumeup": "XF86AudioRaiseVolume",
            "volumedown": "XF86AudioLowerVolume",
            "volumemute": "XF86AudioMute"
        }

def media_controller(parameters: Optional[dict] = None, player=None, root=None) -> str:
    """
    Medya kontrolü yapar.
    parameters: {
        "command": "play", "pause", "next", "previous", "up", "down", "mute" (veya Türkçe karşılıkları)
        "volume_steps": 5   # ses aç/kıs için kaç adım (varsayılan 5)
    }
    """
    params = parameters or {}
    command = params.get("command", "").lower().strip()
    volume_steps = params.get("volume_steps", 5)
    
    if not command:
        return "Medya komutu belirtilmedi patron. Örnek: 'play', 'next', 'volume up'."
    
    if not PYAUTOGUI_AVAILABLE:
        return "PyAutoGUI kütüphanesi yüklü değil. Medya kontrolü için 'pip install pyautogui' gereklidir."
    
    if player:
        player.write_log(f"SYS: 🎵 Medya komutu: {command}")
    
    # Komut eşleme (çok dilli destek)
    action_map = {
        "play": "playpause",
        "oynat": "playpause",
        "başlat": "playpause",
        "pause": "playpause",
        "durdur": "playpause",
        "duraklat": "playpause",
        "next": "nexttrack",
        "geç": "nexttrack",
        "ileri": "nexttrack",
        "sonraki": "nexttrack",
        "previous": "prevtrack",
        "geri": "prevtrack",
        "önceki": "prevtrack",
        "up": "volumeup",
        "aç": "volumeup",
        "arttır": "volumeup",
        "yukarı": "volumeup",
        "down": "volumedown",
        "kıs": "volumedown",
        "azalt": "volumedown",
        "aşağı": "volumedown",
        "mute": "volumemute",
        "sustur": "volumemute",
        "sesi kapat": "volumemute"
    }
    
    # Komutu bul
    action = None
    for key, val in action_map.items():
        if key in command:
            action = val
            break
    
    if action is None:
        return f"Bilinmeyen medya komutu: '{command}'. Desteklenenler: play, pause, next, previous, volume up/down, mute."
    
    # Platforma özel tuş adlarını al
    media_keys = _get_media_keys()
    if action not in media_keys:
        return f"'{action}' işlemi bu platformda desteklenmiyor."
    
    key_to_press = media_keys[action]
    
    try:
        if action in ["volumeup", "volumedown"]:
            # Ses seviyesini belirtilen adım kadar değiştir (her basışta %2 civarı)
            steps = max(1, min(20, volume_steps))  # 1-20 arası
            for _ in range(steps):
                pyautogui.press(key_to_press)
        else:
            pyautogui.press(key_to_press)
    except Exception as e:
        if player:
            player.write_log(f"SYS: Medya tuş hatası: {e}")
        return f"Medya tuşu gönderilemedi. Sistem izinleri veya donanım desteği olmayabilir: {str(e)}"
    
    # HUD gösterimi
    if root:
        try:
            hud = tk.Toplevel(root)
            hud.overrideredirect(True)
            hud.attributes("-topmost", True, "-alpha", 0.85)
            hud.geometry("280x70+10+10")
            hud.configure(bg="#2b002b")
            
            # Komutun gösterim adı
            display_cmd = command.capitalize()
            tk.Label(hud, text="🎵 MEDYA KONTROLÜ", font=("Courier", 10, "bold"), fg="#ff33cc", bg="#2b002b").pack(pady=3)
            tk.Label(hud, text=f"{display_cmd}", font=("Courier", 9), fg="white", bg="#2b002b").pack()
            
            try:
                winsound.Beep(500, 150)
            except:
                pass
            
            root.after(2000, lambda: hud.destroy() if hud.winfo_exists() else None)
        except Exception as hud_err:
            # HUD hatası önemli değil, logla
            if player:
                player.write_log(f"SYS: HUD hatası: {hud_err}")
    
    return f"Medya kontrolü tamamlandı patron. '{command}' işlemi uygulandı."