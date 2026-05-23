"""
keyboard.py - J.A.R.V.I.S. Akıllı Klavye ve Odak Kontrolü
Tuş gönderme, kısayol kombinasyonları, metin yazma ve otomatik pencere odaklama.
"""

import pyautogui
import time
import ctypes
import sys
import platform
from typing import Optional

# Güvenlik ayarları
pyautogui.PAUSE = 0.01
pyautogui.FAILSAFE = False

def get_platform():
    return platform.system().lower()

def focus_window_by_title(title_keywords: list):
    """Belirtilen anahtar kelimeleri içeren pencereyi öne getirir ve tıklar."""
    try:
        if get_platform() == "windows":
            import pygetwindow as gw
            windows = gw.getWindowsWithTitle('')
            for win in windows:
                if any(kw.lower() in win.title.lower() for kw in title_keywords):
                    if not win.isMinimized:
                        win.activate()
                        # Pencerenin sol üst köşesine tıkla (odak için)
                        old_x, old_y = pyautogui.position()
                        pyautogui.click(win.left + 10, win.top + 10)
                        pyautogui.moveTo(old_x, old_y)
                    else:
                        win.restore()
                    return True
    except Exception:
        # pygetwindow yoksa veya hata alınırsa alternatif
        try:
            ctypes.windll.user32.keybd_event(0, 0, 0, 0)
        except:
            pass
    return False

def keyboard_control(parameters: dict, player=None) -> str:
    """
    Klavye kontrolü.
    parameters: {
        "key": "a", "ctrl+c", "enter"  (tuş veya kombinasyon)
        "action": "press", "hotkey", "write"
        "text": "yazılacak metin"  (action=write için)
        "auto_focus": True/False  (otomatik odaklama)
        "focus_title": ["J.A.R.V.I.S", "main.py"]  (aranacak pencere başlıkları)
    }
    """
    key = parameters.get("key", "").strip().lower()
    action = parameters.get("action", "press").lower()
    text = parameters.get("text", "")
    auto_focus = parameters.get("auto_focus", True)
    focus_titles = parameters.get("focus_title", ["J.A.R.V.I.S", "main.py", "Jarvis"])

    if auto_focus:
        focus_window_by_title(focus_titles)
        # Küçük bir gecikme odaklanma için
        time.sleep(0.05)

    try:
        if action == "press":
            if not key:
                return "Tuş belirtilmedi."
            pyautogui.press(key)
            return f"'{key}' tuşuna basıldı Komutan."
        
        elif action == "hotkey":
            if not key:
                return "Kombinasyon belirtilmedi."
            keys = [k.strip() for k in key.split('+')]
            pyautogui.hotkey(*keys)
            return f"Kombinasyon '{key}' tetiklendi."
        
        elif action == "write":
            if not text:
                return "Yazılacak metin belirtilmedi."
            pyautogui.write(text, interval=0.02)
            return f"Metin girişi tamamlandı: '{text[:50]}...'"
        
        else:
            return f"Bilinmeyen aksiyon: {action}. Kullanılabilir: press, hotkey, write"
    
    except Exception as e:
        return f"Klavye/Odak Hatası: {str(e)}"