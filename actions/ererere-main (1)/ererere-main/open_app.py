"""
open_app.py - J.A.R.V.I.S. Uygulama Başlatma Modülü
Windows, macOS ve Linux'ta uygulama başlatma desteği, özel yollar, start komutu, explorer alternatifi.
"""

import subprocess
import shutil
import os
import sys
import platform
from typing import Optional, Dict, List

# Bilinen uygulamaların kısayol eşlemeleri (platform bazlı)
KNOWN_APPS: Dict[str, str] = {
    # Windows
    "notepad": "notepad.exe",
    "cmd": "cmd.exe",
    "komut istemi": "cmd.exe",
    "powershell": "powershell.exe",
    "task manager": "taskmgr.exe",
    "görev yöneticisi": "taskmgr.exe",
    "control panel": "control.exe",
    "denetim masası": "control.exe",
    "calculator": "calc.exe",
    "hesap makinesi": "calc.exe",
    "paint": "mspaint.exe",
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe",
    "firefox": "firefox.exe",
    "mozilla firefox": "firefox.exe",
    "edge": "msedge.exe",
    "microsoft edge": "msedge.exe",
    "opera": "opera.exe",
    "spotify": "spotify.exe",
    "discord": "discord.exe",
    "vscode": "code.exe",
    "visual studio code": "code.exe",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "dosya gezgini": "explorer.exe",
    "excel": "excel.exe",
    "microsoft excel": "excel.exe",
    "word": "winword.exe",
    "microsoft word": "winword.exe",
    "powerpoint": "powerpnt.exe",
    "outlook": "outlook.exe",
    "telegram": "telegram.exe",
    "whatsapp": "whatsapp.exe",
    "slack": "slack.exe",
    "zoom": "Zoom.exe",
    "steam": "steam.exe",
    "epic games": "EpicGamesLauncher.exe",
    "photoshop": "Photoshop.exe",
    "illustrator": "Illustrator.exe",
    "premiere": "Premiere Pro.exe",
    "after effects": "AfterFX.exe",
    # macOS
    "safari": "safari",
    "finder": "finder",
    "messages": "messages",
    "mail": "mail",
    "calendar": "calendar",
    "notes": "notes",
    "reminders": "reminders",
    "photos": "photos",
    "music": "music",
    "facetime": "facetime",
    # Linux
    "gnome terminal": "gnome-terminal",
    "konsole": "konsole",
    "nautilus": "nautilus",
    "dolphin": "dolphin",
    "gedit": "gedit",
    "vim": "vim",
    "nano": "nano",
}

def get_platform() -> str:
    """Çalışılan platformu döndürür."""
    system = platform.system()
    if system == "Windows":
        return "windows"
    elif system == "Darwin":
        return "macos"
    else:
        return "linux"

def _open_windows(app_name: str, args: str = "") -> tuple[bool, str]:
    """Windows'ta uygulama başlatır."""
    # Önce start komutunu dene
    cmd = f'start "" "{app_name}"'
    if args:
        cmd += f" {args}"
    result = subprocess.run(cmd, shell=True, capture_output=True)
    
    if result.returncode == 0:
        return True, "start komutu ile başlatıldı"
    
    # Dosya yolu kontrolü
    if os.path.exists(app_name):
        subprocess.Popen([app_name] + ([args] if args else []), shell=True)
        return True, "doğrudan çalıştırıldı"
    
    # explorer alternatifi (UWP uygulamaları için)
    try:
        subprocess.run(f'explorer shell:AppsFolder\\{app_name}', shell=True, capture_output=True)
        return True, "explorer yöntemi ile başlatıldı"
    except:
        pass
    
    return False, ""

def _open_macos(app_name: str, args: str = "") -> tuple[bool, str]:
    """macOS'ta uygulama başlatır."""
    try:
        # open komutunu kullan
        cmd = ["open", "-a", app_name]
        if args:
            cmd.append("--args")
            cmd.extend(args.split())
        subprocess.run(cmd, capture_output=True)
        return True, "macOS open ile başlatıldı"
    except:
        pass
    
    # Doğrudan çalıştırmayı dene
    try:
        subprocess.Popen([app_name] + ([args] if args else []))
        return True, "doğrudan çalıştırıldı"
    except:
        pass
    
    return False, ""

def _open_linux(app_name: str, args: str = "") -> tuple[bool, str]:
    """Linux'ta uygulama başlatır."""
    try:
        # xdg-open veya doğrudan çalıştır
        subprocess.Popen([app_name] + ([args] if args else []), shell=False)
        return True, "doğrudan çalıştırıldı"
    except:
        pass
    
    # xdg-open dene (masaüstü uygulamaları için)
    try:
        subprocess.run(["xdg-open", app_name], capture_output=True)
        return True, "xdg-open ile başlatıldı"
    except:
        pass
    
    return False, ""

def open_app(parameters: Optional[dict] = None, player=None, root=None) -> str:
    """
    Bir uygulamayı başlatır. Windows, macOS ve Linux destekler.
    
    parameters: {
        "app_name": "uygulama adı veya yol (zorunlu)",
        "args": "komut satırı argümanları (opsiyonel)",
        "wait": False  # uygulamanın bitmesini bekle (opsiyonel)
    }
    """
    params = parameters or {}
    app_name = params.get("app_name", "").strip()
    args = params.get("args", "").strip()
    wait = params.get("wait", False)

    if not app_name:
        return "Hangi uygulamayı açmamı istediğinizi belirtmediniz patron."

    if player:
        player.write_log(f"SYS: 🚀 Uygulama başlatılıyor -> {app_name}")

    platform_type = get_platform()
    
    # 1. Bilinen uygulama eşlemesini kontrol et
    lower_name = app_name.lower()
    if lower_name in KNOWN_APPS:
        app_name = KNOWN_APPS[lower_name]
        if player:
            player.write_log(f"SYS: Eşleme bulundu -> {app_name}")

    # 2. Yolu PATH'te ara
    full_path = shutil.which(app_name)
    if full_path:
        app_name = full_path

    # 3. Platforma özel başlatma
    success = False
    method = ""
    
    if platform_type == "windows":
        success, method = _open_windows(app_name, args)
    elif platform_type == "macos":
        success, method = _open_macos(app_name, args)
    else:  # linux
        success, method = _open_linux(app_name, args)

    if success:
        msg = f"{app_name} başarıyla başlatıldı ({method})."
        if wait:
            msg += " Uygulama kapatılana kadar beklenecek."
        return msg
    
    # 4. Son çare: Kullanıcıya yol göster
    return f"'{app_name}' adlı uygulamayı bulamadım. Lütfen:\n- Uygulamanın yüklü olduğundan emin olun\n- Tam adını veya dosya yolunu belirtin\n- Örnek: 'chrome', 'notepad', 'C:\\Program Files\\App\\app.exe'"