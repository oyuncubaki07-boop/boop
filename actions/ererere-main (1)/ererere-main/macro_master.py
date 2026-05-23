"""
macro_master.py - J.A.R.V.I.S. Gelişmiş Makro Yöneticisi
- Fare tıklama (mevcut konum veya belirtilen koordinat)
- Klavye tuşları ve metin yazma
- Makro kaydetme ve oynatma (basit)
- Bekleme süreleri
- Acil durdurma (ESC ile)
"""

import pyautogui
import time
import threading
import keyboard  # pip install keyboard (isteğe bağlı, durdurma için)
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

# Acil durdurma bayrağı
_stop_macro = False

def _stop_check():
    """Makroyu durdurma kontrolü (ESC tuşuna basılırsa)."""
    global _stop_macro
    try:
        if keyboard.is_pressed('esc'):
            _stop_macro = True
            return True
    except:
        pass
    return False

def _click_macro(clicks: int, delay: float, x: Optional[int] = None, y: Optional[int] = None, player=None):
    """Tıklama makrosu."""
    global _stop_macro
    _stop_macro = False
    if player:
        player.write_log(f"SYS: 🤖 Tıklama makrosu başlıyor: {clicks} kez, aralık {delay}s")
    
    time.sleep(2)  # Kullanıcıya hazırlık süresi
    
    for i in range(clicks):
        if _stop_check():
            if player:
                player.write_log("SYS: ⏹️ Makro kullanıcı tarafından durduruldu.")
            break
        if x is not None and y is not None:
            pyautogui.click(x, y)
        else:
            pyautogui.click()
        if delay > 0:
            time.sleep(delay)
    
    if player and not _stop_macro:
        player.write_log("SYS: ✅ Tıklama makrosu tamamlandı.")

def _key_macro(keys: List[str], delay: float, player=None):
    """Klavye makrosu (tuş kombinasyonları)."""
    global _stop_macro
    _stop_macro = False
    if player:
        player.write_log(f"SYS: ⌨️ Klavye makrosu başlıyor: {keys}, aralık {delay}s")
    
    time.sleep(2)
    
    for key in keys:
        if _stop_check():
            if player:
                player.write_log("SYS: ⏹️ Makro durduruldu.")
            break
        if '+' in key:
            # Kombinasyon tuşu (örn: ctrl+c)
            pyautogui.hotkey(*key.split('+'))
        else:
            pyautogui.press(key)
        if delay > 0:
            time.sleep(delay)
    
    if player and not _stop_macro:
        player.write_log("SYS: ✅ Klavye makrosu tamamlandı.")

def _type_macro(text: str, delay: float, player=None):
    """Metin yazma makrosu."""
    global _stop_macro
    _stop_macro = False
    if player:
        player.write_log(f"SYS: ✍️ Metin makrosu başlıyor: '{text[:50]}...'")
    
    time.sleep(2)
    
    for char in text:
        if _stop_check():
            if player:
                player.write_log("SYS: ⏹️ Makro durduruldu.")
            break
        pyautogui.write(char)
        if delay > 0:
            time.sleep(delay)
    
    if player and not _stop_macro:
        player.write_log("SYS: ✅ Metin makrosu tamamlandı.")

def _record_macro(duration: int, player=None) -> List[Dict]:
    """Belirtilen süre boyunca fare ve klavye olaylarını kaydeder (basit)."""
    if player:
        player.write_log(f"SYS: 📹 Makro kaydı başlıyor, {duration} saniye...")
    from pynput import mouse, keyboard as pynput_keyboard
    import threading
    
    events = []
    stop_event = threading.Event()
    
    def on_click(x, y, button, pressed):
        if pressed:
            events.append(('click', x, y, button.name, time.time()))
    
    def on_press(key):
        try:
            events.append(('key', key.char, time.time()))
        except AttributeError:
            events.append(('key', str(key), time.time()))
    
    mouse_listener = mouse.Listener(on_click=on_click)
    keyboard_listener = pynput_keyboard.Listener(on_press=on_press)
    
    mouse_listener.start()
    keyboard_listener.start()
    
    time.sleep(duration)
    stop_event.set()
    mouse_listener.stop()
    keyboard_listener.stop()
    
    if player:
        player.write_log(f"SYS: 📹 Kayıt tamamlandı, {len(events)} olay kaydedildi.")
    return events

def _save_macro(events: List[Dict], name: str, player=None):
    """Makroyu JSON dosyasına kaydeder."""
    macro_dir = Path(__file__).parent.parent / "macros"
    macro_dir.mkdir(exist_ok=True)
    file_path = macro_dir / f"{name}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2)
    if player:
        player.write_log(f"SYS: 💾 Makro kaydedildi: {file_path}")

def _load_macro(name: str, player=None) -> Optional[List[Dict]]:
    """Makroyu JSON dosyasından yükler."""
    macro_dir = Path(__file__).parent.parent / "macros"
    file_path = macro_dir / f"{name}.json"
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    if player:
        player.write_log(f"SYS: ❌ Makro bulunamadı: {name}")
    return None

def _play_macro(events: List[Dict], speed: float = 1.0, player=None):
    """Kaydedilmiş makroyu oynatır."""
    global _stop_macro
    _stop_macro = False
    if not events:
        return
    start_time = None
    for event in events:
        if _stop_check():
            break
        if start_time is None:
            start_time = event[3] if len(event) > 3 else time.time()
        else:
            # Orijinal zaman farkını koru (basit)
            pass
        if event[0] == 'click':
            _, x, y, button, _ = event
            pyautogui.click(x, y, button=button)
        elif event[0] == 'key':
            _, key, _ = event
            pyautogui.press(key)
        time.sleep(0.05 / speed)  # hızlandırma/yavaşlatma
    if player:
        player.write_log("SYS: ✅ Makro oynatıldı.")

def macro_master(parameters: Optional[dict] = None, player=None, root=None) -> str:
    """
    Gelişmiş makro yöneticisi.
    
    parameters:
        action: "click", "key", "type", "record", "save", "load", "play"
        clicks: tıklama sayısı (action=click için)
        click_delay: tıklamalar arası bekleme (saniye)
        x, y: tıklama koordinatları (opsiyonel)
        keys: tuş listesi ["a", "b", "ctrl+c"] (action=key için)
        key_delay: tuşlar arası bekleme
        text: yazılacak metin (action=type için)
        type_delay: karakterler arası bekleme
        duration: kayıt süresi (saniye)
        macro_name: kaydetme/yükleme için isim
        speed: oynatma hızı (1.0 normal, >1 hızlı)
    """
    params = parameters or {}
    action = params.get("action", "click").lower()
    
    try:
        if action == "click":
            clicks = params.get("clicks", 50)
            delay = params.get("click_delay", 0.05)
            x = params.get("x")
            y = params.get("y")
            threading.Thread(target=_click_macro, args=(clicks, delay, x, y, player), daemon=True).start()
            coord_msg = f" koordinat ({x},{y})" if x is not None and y is not None else " mevcut fare konumunda"
            return f"Makro başlatıldı patron. 2 saniye içinde{coord_msg} {clicks} kez tıklanacak. Durdurmak için ESC tuşuna basın."
        
        elif action == "key":
            keys = params.get("keys", [])
            if not keys:
                return "Tuş listesi belirtilmedi. Örnek: ['ctrl+c', 'enter']"
            delay = params.get("key_delay", 0.1)
            threading.Thread(target=_key_macro, args=(keys, delay, player), daemon=True).start()
            return f"Klavye makrosu başlatıldı. Tuşlar: {keys}. Durdurmak için ESC."
        
        elif action == "type":
            text = params.get("text", "")
            if not text:
                return "Yazılacak metin belirtilmedi."
            delay = params.get("type_delay", 0.05)
            threading.Thread(target=_type_macro, args=(text, delay, player), daemon=True).start()
            return f"Metin makrosu başlatıldı. '{text[:50]}...' yazılacak. Durdurmak için ESC."
        
        elif action == "record":
            duration = params.get("duration", 10)
            events = _record_macro(duration, player)
            # Geçici olarak hafızada tut
            macro_master._last_recording = events
            return f"Kayıt tamamlandı. {len(events)} olay kaydedildi. 'save' ile kaydedebilirsiniz."
        
        elif action == "save":
            macro_name = params.get("macro_name", "")
            if not macro_name:
                return "Makro adı belirtilmedi (macro_name)."
            events = macro_master._last_recording if hasattr(macro_master, '_last_recording') else None
            if not events:
                return "Kaydedilecek makro yok. Önce 'record' yapın."
            _save_macro(events, macro_name, player)
            return f"Makro '{macro_name}' olarak kaydedildi."
        
        elif action == "load":
            macro_name = params.get("macro_name", "")
            if not macro_name:
                return "Makro adı belirtilmedi."
            events = _load_macro(macro_name, player)
            if events:
                macro_master._last_recording = events
                return f"Makro '{macro_name}' yüklendi. 'play' ile oynatabilirsiniz."
            else:
                return f"Makro '{macro_name}' bulunamadı."
        
        elif action == "play":
            events = macro_master._last_recording if hasattr(macro_master, '_last_recording') else None
            if not events:
                return "Oynatılacak makro yok. Önce 'load' veya 'record' yapın."
            speed = params.get("speed", 1.0)
            threading.Thread(target=_play_macro, args=(events, speed, player), daemon=True).start()
            return f"Makro oynatılıyor... Durdurmak için ESC."
        
        else:
            return f"Bilinmeyen aksiyon: {action}. Desteklenenler: click, key, type, record, save, load, play"
    
    except Exception as e:
        if player:
            player.write_log(f"SYS: Makro hatası: {e}")
        return f"Makro çalıştırılırken hata: {str(e)}"

# Geçici kayıt için
macro_master._last_recording = None