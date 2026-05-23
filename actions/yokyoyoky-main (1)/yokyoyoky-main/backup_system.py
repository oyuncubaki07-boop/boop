"""
backup_system.py - J.A.R.V.I.S. Sistem Yedekleme Modülü (PyQt6)
Tüm J.A.R.V.I.S. ana klasörünü yedekler, platform bağımsız masaüstü hedefi kullanır.
"""

import os
import shutil
import datetime
import threading
import sys
from typing import Optional, Any

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PyQt6.QtCore import Qt, QTimer

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
    """Başarılı yedekleme HUD penceresini gösterir (PyQt6)."""
    if not root:
        return
    try:
        # PyQt6 penceresi
        hud = QWidget(root if isinstance(root, QWidget) else None)
        hud.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        hud.setWindowOpacity(0.9)
        hud.setGeometry(10, 10, 400, 90)
        hud.setStyleSheet("background-color: #002b00;")
        
        layout = QVBoxLayout(hud)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        title_label = QLabel("💾 SİSTEM YEDEKLENDİ")
        title_label.setStyleSheet("color: #00ff00; font-family: 'Courier New'; font-size: 12px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        target_label = QLabel(f"Hedef: {target_dir}")
        target_label.setStyleSheet("color: white; font-family: 'Courier New'; font-size: 9px;")
        target_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(target_label)
        
        hud.show()
        
        safe_beep(600, 150)
        safe_beep(800, 200)
        
        # 5 saniye sonra kapat
        QTimer.singleShot(5000, hud.close)
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
            # PyQt6 ana thread'de GUI güncellemesi
            if isinstance(root, QWidget):
                QTimer.singleShot(0, lambda: show_backup_success(root, target_dir))
            else:
                # Eğer root Tkinter ise (geriye dönük uyumluluk)
                try:
                    root.after(0, lambda: show_backup_success(root, target_dir))
                except:
                    pass
        
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