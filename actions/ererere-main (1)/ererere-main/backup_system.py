"""
backup_system.py - J.A.R.V.I.S. Sistem Yedekleme Modülü
Tüm J.A.R.V.I.S. ana klasörünü yedekler, platform bağımsız masaüstü hedefi kullanır.
"""

import os
import shutil
import datetime
import threading
import sys
from typing import Optional, Any

# Platform bağımsız winsound alternatifi
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False
    try:
        import pygame
        pygame.mixer.init()
        HAS_PYGAME = True
    except:
        HAS_PYGAME = False

def get_desktop_path() -> str:
    """Platforma göre masaüstü yolunu döndürür (Windows, Linux, macOS)."""
    if sys.platform == "win32":
        return os.environ.get('USERPROFILE', 'C:\\') + '\\Desktop'
    elif sys.platform == "darwin":  # macOS
        return os.path.join(os.path.expanduser('~'), 'Desktop')
    else:  # Linux ve diğer Unix benzeri
        return os.path.join(os.path.expanduser('~'), 'Desktop')

def safe_beep(freq: int = 500, duration: int = 200):
    """Sesli bildirim (winsound veya pygame ile)."""
    try:
        if HAS_WINSOUND:
            winsound.Beep(freq, duration)
        elif HAS_PYGAME:
            # pygame ile basit bir beep sesi üretmek karmaşık, atlıyoruz
            pass
    except:
        pass

def show_backup_success(root: Any, target_dir: str):
    """Başarılı yedekleme HUD penceresini gösterir."""
    if not root:
        return
    try:
        hud = tk.Toplevel(root)
        hud.overrideredirect(True)
        hud.attributes("-topmost", True, "-alpha", 0.9)
        hud.geometry("400x90+10+10")
        hud.configure(bg="#002b00")
        
        tk.Label(hud, text="💾 SİSTEM YEDEKLENDİ", font=("Courier", 12, "bold"), fg="#00ff00", bg="#002b00").pack(pady=5)
        tk.Label(hud, text=f"Hedef: {target_dir}", font=("Courier", 9), fg="white", bg="#002b00").pack()
        
        safe_beep(600, 150)
        safe_beep(800, 200)
        
        root.after(5000, lambda: hud.destroy() if hud.winfo_exists() else None)
    except Exception:
        pass

def do_backup(player: Any, root: Any, source_dir: str, target_dir: str) -> str:
    """Asıl yedekleme işlemini yapar. (Thread içinde çalışır)"""
    try:
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_base = os.path.join(target_dir, f"JARVIS_Core_Backup_{timestamp}")
        
        # Yedekleme yapılırken geçici klasör sorunlarına karşı
        shutil.make_archive(archive_base, 'zip', source_dir)
        zip_path = archive_base + ".zip"
        
        if player:
            player.write_log(f"SYS: 💾 Sistem başarıyla yedeklendi: {zip_path}")
        
        if root:
            root.after(0, lambda: show_backup_success(root, target_dir))
        
        return zip_path
    except Exception as e:
        if player:
            player.write_log(f"SYS: Yedekleme Hatası: {e}")
        return ""

def backup_jarvis(parameters: Optional[dict] = None, player: Any = None, root: Any = None) -> str:
    """
    J.A.R.V.I.S. sistem yedekleme ana fonksiyonu.
    parameters: {
        "source": "/path/to/source" (isteğe bağlı, varsayılan J.A.R.V.I.S. ana dizini),
        "target": "/path/to/backup/folder" (isteğe bağlı, varsayılan masaüstü/JARVIS_Yedekler)
    }
    """
    # Kaynak dizin: parametreden veya mevcut çalışma dizini
    source_dir = parameters.get("source") if parameters else None
    if not source_dir:
        source_dir = os.getcwd()
    
    # Hedef dizin: parametreden veya masaüstü/JARVIS_Yedekler
    target_dir = parameters.get("target") if parameters else None
    if not target_dir:
        desktop = get_desktop_path()
        target_dir = os.path.join(desktop, "JARVIS_Yedekler")
    
    if player:
        player.write_log("SYS: 💾 Sistem yedekleme protokolü arka planda başlatılıyor...")
    
    safe_beep(500, 200)
    
    # Yedeklemeyi ayrı thread'de başlat (UI donmasın)
    def backup_task():
        do_backup(player, root, source_dir, target_dir)
    
    threading.Thread(target=backup_task, daemon=True).start()
    
    return "Sistem yedekleme protokolü arka planda başlatıldı. Tamamlandığında bildireceğim patron."