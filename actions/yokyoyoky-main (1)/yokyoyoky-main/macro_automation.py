"""
macro_automation.py - J.A.R.V.I.S. Oyun / Çalışma Modu Otomasyonu (PyQt6)
Sistem performansını artırmak için gereksiz uygulamaları kapatır, özel protokolleri başlatır.
"""

import os
import subprocess
import winsound
from typing import Optional

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer


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
    """Kısa bildirim HUD'u (PyQt6)."""
    if not root or not isinstance(root, QWidget):
        return
    try:
        hud = QWidget(root)
        hud.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        hud.setWindowOpacity(0.9)
        hud.setGeometry(10, 10, 350, 100)
        hud.setStyleSheet(f"background-color: {color};")

        layout = QVBoxLayout(hud)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: white; font-family: 'Courier New'; font-size: 11px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        msg_label = QLabel(message)
        msg_label.setStyleSheet("color: #dddddd; font-family: 'Courier New'; font-size: 9px;")
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)

        hud.show()

        if beep:
            try:
                winsound.Beep(600, 150)
            except:
                pass

        QTimer.singleShot(4000, hud.close)
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
        try:
            if os.name == 'nt':
                os.system("start shell:AppsFolder\\Microsoft.GamingServices_8wekyb3d8bbwe!GameMode")
        except:
            pass
        return "Oyun protokolü aktif edildi efendim. Arka plandaki tarayıcılar kapatılarak RAM temizlendi. Sistem maksimum performansa ayarlandı, iyi eğlenceler."
    
    elif "çalışma" in mode or "work" in mode or "focus" in mode:
        _show_hud(root, "📚 ÇALIŞMA MODU", "Odaklanma ortamı hazırlanıyor...", "#000066")
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
        return "Kurgu protokolü aktif. Yaratıcılığınızı konuşturun patron!"
    
    elif "medya" in mode or "media" in mode:
        _show_hud(root, "🎵 MEDYA MODU", "Medya oynatıcıları optimize ediliyor...", "#332200")
        return "Medya modu aktif. Film, müzik keyfiniz için sistem hazır."
    
    elif "default" in mode or "normal" in mode:
        _show_hud(root, "⚙️ NORMAL MOD", "Varsayılan ayarlara dönülüyor...", "#333333")
        return "Normal moda geçildi. Sistem varsayılan ayarlarında."
    
    else:
        return f"Sistemde '{mode}' adında bir protokol tanımlı değil efendim. Kullanılabilir: oyun, çalışma, kurgu, medya, default"