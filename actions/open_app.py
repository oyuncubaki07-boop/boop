# actions/open_app.py
# MARK XXV — Cross-Platform App Launcher

import time
import subprocess
import platform
import shutil

try:
    import psutil
    _PSUTIL = True
except ImportError:
    _PSUTIL = False

_APP_ALIASES = {
    "whatsapp":           {"Windows": "WhatsApp",               "Darwin": "WhatsApp",            "Linux": "whatsapp"},
    "chrome":             {"Windows": "chrome",                 "Darwin": "Google Chrome",       "Linux": "google-chrome"},
    "google chrome":      {"Windows": "chrome",                 "Darwin": "Google Chrome",       "Linux": "google-chrome"},
    "firefox":            {"Windows": "firefox",                "Darwin": "Firefox",             "Linux": "firefox"},
    "spotify":            {"Windows": "Spotify",                "Darwin": "Spotify",             "Linux": "spotify"},
    "vscode":             {"Windows": "code",                   "Darwin": "Visual Studio Code",  "Linux": "code"},
    "visual studio code": {"Windows": "code",                   "Darwin": "Visual Studio Code",  "Linux": "code"},
    "discord":            {"Windows": "Discord",                "Darwin": "Discord",             "Linux": "discord"},
    "telegram":           {"Windows": "Telegram",               "Darwin": "Telegram",            "Linux": "telegram"},
    "instagram":          {"Windows": "Instagram",              "Darwin": "Instagram",           "Linux": "instagram"},
    "tiktok":             {"Windows": "TikTok",                 "Darwin": "TikTok",              "Linux": "tiktok"},
    "notepad":            {"Windows": "notepad.exe",            "Darwin": "TextEdit",            "Linux": "gedit"},
    "calculator":         {"Windows": "calc.exe",               "Darwin": "Calculator",          "Linux": "gnome-calculator"},
    "terminal":           {"Windows": "cmd.exe",                "Darwin": "Terminal",            "Linux": "gnome-terminal"},
    "cmd":                {"Windows": "cmd.exe",                "Darwin": "Terminal",            "Linux": "bash"},
    "explorer":           {"Windows": "explorer.exe",           "Darwin": "Finder",              "Linux": "nautilus"},
    "file explorer":      {"Windows": "explorer.exe",           "Darwin": "Finder",              "Linux": "nautilus"},
    "paint":              {"Windows": "mspaint.exe",            "Darwin": "Preview",             "Linux": "gimp"},
    "word":               {"Windows": "winword",                "Darwin": "Microsoft Word",      "Linux": "libreoffice --writer"},
    "excel":              {"Windows": "excel",                  "Darwin": "Microsoft Excel",     "Linux": "libreoffice --calc"},
    "powerpoint":         {"Windows": "powerpnt",               "Darwin": "Microsoft PowerPoint","Linux": "libreoffice --impress"},
    "vlc":                {"Windows": "vlc",                    "Darwin": "VLC",                 "Linux": "vlc"},
    "zoom":               {"Windows": "Zoom",                   "Darwin": "zoom.us",             "Linux": "zoom"},
    "slack":              {"Windows": "Slack",                  "Darwin": "Slack",               "Linux": "slack"},
    "steam":              {"Windows": "steam",                  "Darwin": "Steam",               "Linux": "steam"},
    "task manager":       {"Windows": "taskmgr.exe",            "Darwin": "Activity Monitor",    "Linux": "gnome-system-monitor"},
    "settings":           {"Windows": "ms-settings:",           "Darwin": "System Preferences",  "Linux": "gnome-control-center"},
    "powershell":         {"Windows": "powershell.exe",         "Darwin": "Terminal",            "Linux": "bash"},
    "edge":               {"Windows": "msedge",                 "Darwin": "Microsoft Edge",      "Linux": "microsoft-edge"},
    "brave":              {"Windows": "brave",                  "Darwin": "Brave Browser",       "Linux": "brave-browser"},
    "obsidian":           {"Windows": "Obsidian",               "Darwin": "Obsidian",            "Linux": "obsidian"},
    "notion":             {"Windows": "Notion",                 "Darwin": "Notion",              "Linux": "notion"},
    "blender":            {"Windows": "blender",                "Darwin": "Blender",             "Linux": "blender"},
    "capcut":             {"Windows": "CapCut",                 "Darwin": "CapCut",              "Linux": "capcut"},
    "postman":            {"Windows": "Postman",                "Darwin": "Postman",             "Linux": "postman"},
    "figma":              {"Windows": "Figma",                  "Darwin": "Figma",               "Linux": "figma"},
}


def _normalize(raw: str) -> str:
    system = platform.system()
    key    = raw.lower().strip()
    if key in _APP_ALIASES:
        return _APP_ALIASES[key].get(system, raw)
    for alias_key, os_map in _APP_ALIASES.items():
        if alias_key in key or key in alias_key:
            return os_map.get(system, raw)
    return raw


def _is_running(app_name: str) -> bool:
    if not _PSUTIL:
        return True
    app_lower = app_name.lower().replace(" ", "").replace(".exe", "")
    try:
        for proc in psutil.process_iter(["name"]):
            try:
                proc_name = proc.info["name"].lower().replace(" ", "").replace(".exe", "")
                if app_lower in proc_name or proc_name in app_lower:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception:
        pass
    return False


def _launch_windows(app_name: str) -> bool:
    try:
        import pyautogui
        pyautogui.PAUSE = 0.1
        pyautogui.press("win")
        time.sleep(0.6)
        pyautogui.write(app_name, interval=0.05)
        time.sleep(0.8)
        pyautogui.press("enter")
        time.sleep(3.0)
        return True
    except Exception as e:
        print(f"[open_app] ⚠️ Windows launch failed: {e}")
        return False

def _launch_macos(app_name: str) -> bool:
    try:
        result = subprocess.run(["open", "-a", app_name], capture_output=True, timeout=8)
        if result.returncode == 0:
            time.sleep(1.0)
            return True
    except Exception:
        pass

    try:
        result = subprocess.run(["open", "-a", f"{app_name}.app"], capture_output=True, timeout=8)
        if result.returncode == 0:
            time.sleep(1.0)
            return True
    except Exception:
        pass

    try:
        import pyautogui
        pyautogui.hotkey("command", "space")
        time.sleep(0.6)
        pyautogui.write(app_name, interval=0.05)
        time.sleep(0.8)
        pyautogui.press("enter")
        time.sleep(1.5)
        return True
    except Exception as e:
        print(f"[open_app] ⚠️ macOS Spotlight failed: {e}")
        return False



def _launch_linux(app_name: str) -> bool:
    binary = (
        shutil.which(app_name) or
        shutil.which(app_name.lower()) or
        shutil.which(app_name.lower().replace(" ", "-"))
    )
    if binary:
        try:
            subprocess.Popen([binary], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1.0)
            return True
        except Exception:
            pass

    try:
        subprocess.run(["xdg-open", app_name], capture_output=True, timeout=5)
        return True
    except Exception:
        pass

    try:
        desktop_name = app_name.lower().replace(" ", "-")
        subprocess.run(["gtk-launch", desktop_name], capture_output=True, timeout=5)
        return True
    except Exception:
        pass

    return False


_OS_LAUNCHERS = {
    "Windows": _launch_windows,
    "Darwin":  _launch_macos,
    "Linux":   _launch_linux,
}

INTENT_MAP = {
    "amy": "open_amy_ui",
    "amy aç": "open_amy_ui", 
    "amy os": "open_amy_ui",
    "kod rehberi": "open_kod_rehberi",
    "ekranı analiz et": "screen_process",
    "ekran analiz": "screen_process",
}

def open_amy_ui(speak=None) -> str:
    import webbrowser
    import os
    import subprocess
    import sys
    import socket
    import platform
    from pathlib import Path
    
    # 1. Start FastAPI server (if not already running on port 8341)
    is_server_running = _is_running("server.py") or _is_running("uvicorn")
    if not is_server_running:
        print("[open_app] 🌸 AMY FastAPI server is not running, launching silently...")
        base_dir = Path(__file__).resolve().parent.parent
        amy_path = base_dir / "amy_os" / "server.py"
        if amy_path.exists():
            subprocess.Popen(
                [sys.executable, str(amy_path)],
                cwd=str(base_dir),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            )
            time.sleep(1.5) # Wait for startup
            
    # 2. Check dynamically which port is open
    def is_port_open(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.25)
            try:
                s.connect(('127.0.0.1', port))
                return True
            except Exception:
                return False

    target_url = 'http://localhost:5174'
    if not is_port_open(5174):
        print("[open_app] 🌸 Vite port 5174 is closed (NPM missing/inactive). Routing to FastAPI port 8341...")
        target_url = 'http://localhost:8341'
        
    webbrowser.open(target_url)
    
    msg = "AMY OS sistemleri ekrana yansıtılıyor, efendim."
    if speak:
        try:
            speak(msg)
        except Exception as e:
            print(f"[open_app] ⚠️ Speak call failed: {e}")
            
    return msg

def handle_intent(action: str, query: str, speak=None, ui=None) -> str:
    if action == "open_amy_ui":
        return open_amy_ui(speak=speak)
    elif action == "open_kod_rehberi":
        from kod_rehberi_window import open_kod_rehberi_safe
        msg = open_kod_rehberi_safe()
        if speak:
            try:
                speak(msg)
            except Exception:
                pass
        return msg
    elif action == "screen_process":
        import threading
        from actions.screen_processor import screen_process
        threading.Thread(
            target=screen_process,
            kwargs={"parameters": {"angle": "screen", "text": query},
                    "response": None, "player": ui, "session_memory": None},
            daemon=True
        ).start()
        msg = "Ekranı analiz ediyorum efendim. Lütfen bekleyin."
        if speak:
            try:
                speak(msg)
            except Exception:
                pass
        return msg
    return f"Bilinmeyen eylem: {action}"

def open_app(
    parameters=None,
    response=None,
    player=None,
    session_memory=None,
    speak=None,
) -> str:
    app_name = (parameters or {}).get("app_name", "").strip()

    if not app_name:
        return "Please specify which application to open, sir."

    system   = platform.system()

    # Intercept AMY OS launch requests
    app_name_lower = app_name.lower().replace(" ", "").replace("'", "").replace("’", "")
    if any(keyword in app_name_lower for keyword in ["amy", "amyos", "amyiac", "openamy"]):
        return open_amy_ui(speak=speak)

    launcher = _OS_LAUNCHERS.get(system)

    if launcher is None:
        return f"Unsupported OS: {system}"

    normalized = _normalize(app_name)
    print(f"[open_app] 🚀 Launching: {app_name} → {normalized} ({system})")

    if player:
        player.write_log(f"[open_app] {app_name}")

    try:
        success = launcher(normalized)

        if success:
            return f"Opened {app_name} successfully, sir."

        if normalized != app_name:
            success = launcher(app_name)
            if success:
                return f"Opened {app_name} successfully, sir."

        return (
            f"I tried to open {app_name}, sir, but couldn't confirm it launched. "
            f"It may still be loading or might not be installed."
        )

    except Exception as e:
        return f"Failed to open {app_name}, sir: {e}"