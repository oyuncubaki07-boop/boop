import os
import re
import sys
import json
import time
import subprocess
import threading
import winreg
from pathlib import Path
from datetime import datetime


def _find_steam_path() -> Path | None:
    registry_keys = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam"),
        (winreg.HKEY_CURRENT_USER,  r"SOFTWARE\Valve\Steam"),
    ]
    for hive, key_path in registry_keys:
        try:
            key = winreg.OpenKey(hive, key_path)
            val, _ = winreg.QueryValueEx(key, "InstallPath")
            winreg.CloseKey(key)
            p = Path(val)
            if p.exists() and (p / "steam.exe").exists():
                return p
        except Exception:
            continue
    for p in [
        Path(os.environ.get("ProgramFiles(x86)", "")) / "Steam",
        Path(os.environ.get("ProgramFiles", "")) / "Steam",
        Path("C:/Steam"), Path("D:/Steam"), Path("E:/Steam"), Path("F:/Steam"),
    ]:
        if p.exists() and (p / "steam.exe").exists():
            return p
    return None


def _find_epic_path() -> Path | None:
    registry_keys = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\EpicGames\EpicGamesLauncher"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\EpicGames\EpicGamesLauncher"),
        (winreg.HKEY_CURRENT_USER,  r"SOFTWARE\EpicGames\EpicGamesLauncher"),
    ]
    for hive, key_path in registry_keys:
        try:
            key = winreg.OpenKey(hive, key_path)
            val, _ = winreg.QueryValueEx(key, "AppDataPath")
            winreg.CloseKey(key)
            exe = Path(val) / "Binaries" / "Win64" / "EpicGamesLauncher.exe"
            if exe.exists():
                return exe.parent
        except Exception:
            continue
    for p in [
        Path(os.environ.get("ProgramFiles(x86)", "")) / "Epic Games" / "Launcher" / "Portal" / "Binaries" / "Win64",
        Path(os.environ.get("ProgramFiles", "")) / "Epic Games" / "Launcher" / "Portal" / "Binaries" / "Win64",
        Path(os.environ.get("LOCALAPPDATA", "")) / "EpicGamesLauncher" / "Portal" / "Binaries" / "Win64",
    ]:
        if p.exists() and (p / "EpicGamesLauncher.exe").exists():
            return p
    return None


def _get_steam_libraries(steam_path: Path) -> list[Path]:
    libraries = [steam_path / "steamapps"]
    vdf_path  = steam_path / "steamapps" / "libraryfolders.vdf"
    if not vdf_path.exists():
        return libraries
    try:
        content = vdf_path.read_text(encoding="utf-8", errors="ignore")
        for raw_path in re.findall(r'"path"\s+"([^"]+)"', content):
            lib = Path(raw_path.replace("\\\\", "/")) / "steamapps"
            if lib.exists() and lib not in libraries:
                libraries.append(lib)
    except Exception:
        pass
    return libraries


def _get_steam_games(steam_path: Path) -> list[dict]:
    games = []
    for lib in _get_steam_libraries(steam_path):
        for acf in lib.glob("appmanifest_*.acf"):
            try:
                content = acf.read_text(encoding="utf-8", errors="ignore")
                app_id  = re.search(r'"appid"\s+"(\d+)"',      content)
                name    = re.search(r'"name"\s+"([^"]+)"',      content)
                state   = re.search(r'"StateFlags"\s+"(\d+)"', content)
                size    = re.search(r'"SizeOnDisk"\s+"(\d+)"', content)
                if app_id and name:
                    games.append({
                        "id":    app_id.group(1),
                        "name":  name.group(1),
                        "state": int(state.group(1)) if state else 0,
                        "size":  int(size.group(1))  if size  else 0,
                        "lib":   str(lib),
                    })
            except Exception:
                continue
    return games


def _is_steam_running() -> bool:
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq steam.exe"],
                             capture_output=True, text=True).stdout
        return "steam.exe" in out.lower()
    except Exception:
        return False


def _get_steam_window_rect() -> tuple[int, int, int, int] | None:
    try:
        import pygetwindow as gw
        for w in gw.getAllWindows():
            if "steam" in w.title.lower() and w.width > 200 and w.visible:
                return w.left, w.top, w.width, w.height
    except Exception:
        pass
    return None


def _click_first_profile_by_screenshot() -> bool:
    try:
        import pyautogui
        import numpy as np

        time.sleep(1.5)

        win = _get_steam_window_rect()
        if not win:
            print("[GameUpdater] ⚠️ Steam penceresi bulunamadı.")
            return False

        wx, wy, ww, wh = win
        screenshot = pyautogui.screenshot(region=(wx, wy, ww, wh))
        img        = np.array(screenshot)

        h, w = img.shape[:2]

        search_y1 = h // 3
        search_y2 = h * 3 // 4
        search_x1 = w // 5
        search_x2 = w * 4 // 5
        region = img[search_y1:search_y2, search_x1:search_x2]

        r = region[:, :, 0].astype(int)
        g = region[:, :, 1].astype(int)
        b = region[:, :, 2].astype(int)

        max_c = np.maximum(np.maximum(r, g), b)
        min_c = np.minimum(np.minimum(r, g), b)
        sat   = max_c - min_c

        colorful = (max_c > 60) & (sat > 40)

        if not colorful.any():
            print("[GameUpdater] ⚠️ Renkli profil bölgesi bulunamadı — tahmini sol merkeze tıklanıyor.")
            pyautogui.click(wx + ww // 2 - ww // 6, wy + wh // 2)
            return True

        cols = np.where(colorful.any(axis=0))[0]
        rows = np.where(colorful.any(axis=1))[0]

        if len(cols) == 0 or len(rows) == 0:
            return False

        avatar_w  = min(90, (region.shape[1]) // 4)
        first_col = int(cols[0])
        block_cols = cols[cols < first_col + avatar_w]

        center_x_local = int(block_cols.mean())
        center_y_local = int(rows.mean())

        abs_x = wx + search_x1 + center_x_local
        abs_y = wy + search_y1 + center_y_local

        print(f"[GameUpdater] 🎯 İlk profil ({abs_x}, {abs_y}) konumunda tespit edildi, tıklanıyor.")
        pyautogui.click(abs_x, abs_y)
        return True

    except ImportError as e:
        print(f"[GameUpdater] ⚠️ Kütüphane eksik: {e}")
        return False
    except Exception as e:
        print(f"[GameUpdater] ⚠️ Profil tespiti başarısız: {e}")
        return False


def _handle_steam_profile_selection() -> bool:
    print("[GameUpdater] 🔍 Profil seçim ekranı kontrol ediliyor...")

    win = _get_steam_window_rect()
    if not win:
        return False

    wx, wy, ww, wh = win

    try:
        import pyautogui
        import numpy as np

        screenshot = pyautogui.screenshot(region=(wx, wy, ww, wh))
        img        = np.array(screenshot)

        is_small_window = ww < 900 and wh < 700

        top_region   = img[:wh // 3, :, :]
        white_pixels = int(np.sum(
            (top_region[:, :, 0] > 200) &
            (top_region[:, :, 1] > 200) &
            (top_region[:, :, 2] > 200)
        ))
        has_white_text = white_pixels > 100

        if not is_small_window and not has_white_text:
            print("[GameUpdater] ℹ️ Profil ekranı tespit edilmedi — Steam zaten oturum açmış.")
            return False

    except ImportError:
        pass
    except Exception:
        pass

    print("[GameUpdater] 👤 Profil seçim ekranı tespit edildi — ilk profile tıklanıyor.")
    return _click_first_profile_by_screenshot()


def _ensure_steam_running(steam_path: Path) -> bool:
    if _is_steam_running():
        return True

    steam_exe = steam_path / "steam.exe"
    if not steam_exe.exists():
        print("[GameUpdater] ❌ steam.exe bulunamadı.")
        return False

    print("[GameUpdater] 🚀 Steam başlatılıyor...")
    subprocess.Popen([str(steam_exe)])

    for _ in range(20):
        time.sleep(1)
        if _is_steam_running():
            print("[GameUpdater] ✅ Steam çalışıyor.")
            time.sleep(4)
            _handle_steam_profile_selection()
            time.sleep(2)
            return True

    print("[GameUpdater] ⚠️ Steam belirlenen sürede başlatılamadı.")
    return False


def _update_steam_games(steam_path: Path, game_name: str = None) -> str:
    if not _ensure_steam_running(steam_path):
        return "Steam başlatılamadı."

    steam_exe = steam_path / "steam.exe"
    games     = _get_steam_games(steam_path)

    if not games:
        return "Hiçbir Steam oyunu bulunamadı."

    if game_name:
        name_lower = game_name.lower()
        matched    = [g for g in games if name_lower in g["name"].lower()]
        if not matched:
            available = ", ".join(g["name"] for g in games[:5])
            return f"'{game_name}' bulunamadı. Yüklü olanlar: {available}..."
        targets = matched
    else:
        targets = games

    already_updated, already_running, update_started, errors = [], [], [], []

    for game in targets:
        state = game["state"]
        name  = game["name"]
        if state == 4:
            already_updated.append(name)
        elif state == 1026:
            already_running.append(name)
        else:
            try:
                subprocess.Popen([str(steam_exe), f"steam://update/{game['id']}"])
                update_started.append(name)
                time.sleep(0.3)
            except Exception as e:
                errors.append(f"{name}: {e}")

    parts = []
    if update_started:
        names  = ", ".join(update_started[:3])
        suffix = f" ve {len(update_started) - 3} oyun daha" if len(update_started) > 3 else ""
        parts.append(f"Güncelleme başlatıldı: {names}{suffix}.")
    if already_running:
        parts.append(f"Zaten güncelleniyor: {', '.join(already_running)}.")
    if already_updated:
        parts.append(
            f"{already_updated[0]} güncel."
            if game_name else
            f"{len(already_updated)} oyun güncel durumda."
        )
    if errors:
        parts.append(f"Hatalar: {'; '.join(errors)}.")
    return " ".join(parts) if parts else "Güncellenecek oyun bulunamadı."


_KNOWN_APPIDS: dict[str, tuple[str, str]] = {
    "pubg":                ("578080",  "PUBG: Battlegrounds"),
    "pubg battlegrounds":  ("578080",  "PUBG: Battlegrounds"),
    "pubg: battlegrounds": ("578080",  "PUBG: Battlegrounds"),
    "battlegrounds":       ("578080",  "PUBG: Battlegrounds"),
    "gta5":                ("271590",  "Grand Theft Auto V"),
    "gta v":               ("271590",  "Grand Theft Auto V"),
    "grand theft auto v":  ("271590",  "Grand Theft Auto V"),
    "cs2":                 ("730",     "Counter-Strike 2"),
    "csgo":                ("730",     "Counter-Strike 2"),
    "counter-strike 2":    ("730",     "Counter-Strike 2"),
    "counter strike 2":    ("730",     "Counter-Strike 2"),
    "dota2":               ("570",     "Dota 2"),
    "dota 2":              ("570",     "Dota 2"),
    "rust":                ("252490",  "Rust"),
    "valheim":             ("892970",  "Valheim"),
    "cyberpunk":           ("1091500", "Cyberpunk 2077"),
    "cyberpunk 2077":      ("1091500", "Cyberpunk 2077"),
    "elden ring":          ("1245620", "ELDEN RING"),
    "minecraft":           ("1672970", "Minecraft Launcher"),
    "apex legends":        ("1172470", "Apex Legends"),
    "apex":                ("1172470", "Apex Legends"),
    "fortnite":            ("1517990", "Fortnite"),
    "goose goose duck":    ("1568590", "Goose Goose Duck"),
    "among us":            ("945360",  "Among Us"),
    "fall guys":           ("1097150", "Fall Guys"),
    "rocket league":       ("252950",  "Rocket League"),
    "warframe":            ("230410",  "Warframe"),
    "destiny 2":           ("1085660", "Destiny 2"),
    "team fortress 2":     ("440",     "Team Fortress 2"),
    "tf2":                 ("440",     "Team Fortress 2"),
    "left 4 dead 2":       ("550",     "Left 4 Dead 2"),
    "l4d2":                ("550",     "Left 4 Dead 2"),
    "paladins":            ("444090",  "Paladins"),
    "smite":               ("386360",  "SMITE"),
    "war thunder":         ("236390",  "War Thunder"),
    "world of warships":   ("552990",  "World of Warships"),
    "path of exile":       ("238960",  "Path of Exile"),
    "poe":                 ("238960",  "Path of Exile"),
    "lost ark":            ("1599340", "Lost Ark"),
    "new world":           ("1063730", "New World: Aeternum"),
}


def _search_steam_appid(game_name: str) -> tuple[str | None, str | None]:
    name_lower = game_name.lower().strip()

    steam_path = _find_steam_path()
    if steam_path:
        for g in _get_steam_games(steam_path):
            if name_lower in g["name"].lower():
                return g["id"], g["name"]

    if name_lower in _KNOWN_APPIDS:
        app_id, canonical = _KNOWN_APPIDS[name_lower]
        print(f"[GameUpdater] 📖 Bilinen ID: {canonical} ({app_id})")
        return app_id, canonical

    for key, (app_id, canonical) in _KNOWN_APPIDS.items():
        if name_lower in key or key in name_lower:
            print(f"[GameUpdater] 📖 Kısmi eşleşme: {canonical} ({app_id})")
            return app_id, canonical

    try:
        import urllib.request, urllib.parse
        query = urllib.parse.quote(game_name)
        url   = f"https://store.steampowered.com/api/storesearch/?term={query}&l=english&cc=US"
        req   = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            items = json.loads(resp.read().decode()).get("items", [])
        if items:
            best = items[0]
            print(f"[GameUpdater] 🌐 Mağaza API Tespit: {best['name']} ({best['id']})")
            return str(best["id"]), best["name"]
    except Exception as e:
        print(f"[GameUpdater] ⚠️ AppID araması başarısız: {e}")

    return None, None


def _find_best_drive() -> dict | None:
    import shutil, string
    drives = []
    for letter in string.ascii_uppercase:
        drive_path = f"{letter}:\\"
        if os.path.exists(drive_path):
            try:
                gb = shutil.disk_usage(drive_path).free / (1024 ** 3)
                if gb > 0:
                    drives.append({"letter": letter, "path": drive_path, "free_gb": gb})
            except Exception:
                continue
    return max(drives, key=lambda d: d["free_gb"]) if drives else None


def _select_drive_in_dialog(dialog, drive_letter: str) -> bool:
    target = drive_letter.upper()
    for control_type in ("ListItem", "RadioButton"):
        try:
            for ctrl in dialog.descendants(control_type=control_type):
                if target in ctrl.window_text().upper():
                    ctrl.click_input()
                    print(f"[GameUpdater] ✅ Disk seçimi: {ctrl.window_text()}")
                    return True
        except Exception:
            continue
    try:
        for combo in dialog.descendants(control_type="ComboBox"):
            try:
                combo.expand()
                time.sleep(0.15)
                for idx, txt in enumerate(combo.texts()):
                    if target in txt.upper():
                        combo.select(idx)
                        return True
                combo.collapse()
            except Exception:
                continue
    except Exception:
        pass
    try:
        for ctrl in dialog.descendants():
            txt = ctrl.window_text().upper()
            if f"{target}:" in txt and len(txt) < 80:
                ctrl.click_input()
                return True
    except Exception:
        pass
    return False


def _click_button(window, keywords: list[str]) -> bool:
    try:
        for btn in window.descendants(control_type="Button"):
            try:
                txt = btn.window_text().lower().strip()
                if txt in keywords or any(kw in txt for kw in keywords):
                    btn.click_input()
                    return True
            except Exception:
                continue
    except Exception:
        pass
    return False


def _handle_install_dialog(game_name: str) -> str:
    best_drive = _find_best_drive()
    if not best_drive:
        return f"Yükleme iletişim kutusu açıldı. Disk tespit edilemedi."

    drive_letter = best_drive["letter"]
    drive_label  = f"{drive_letter}:"
    print(f"[GameUpdater] 🏆 Hedef disk: {drive_label} ({best_drive['free_gb']:.1f} GB boş alan)")

    try:
        from pywinauto import Application, findwindows
        dialog = None
        for _ in range(40):
            time.sleep(0.5)
            try:
                for hwnd in findwindows.find_windows(title_re=r"(?i)(install|yükle|steam)", visible_only=True):
                    try:
                        app  = Application(backend="uia").connect(handle=hwnd)
                        win  = app.window(handle=hwnd)
                        rect = win.rectangle()
                        if win.is_visible() and rect.width() > 300 and rect.height() > 200:
                            all_text = " ".join(c.window_text() for c in win.descendants() if c.window_text()).upper()
                            if any(x in all_text for x in ("C:", "D:", "E:", "F:", "INSTALL", "YÜKLE")):
                                dialog = win
                                break
                    except Exception:
                        continue
            except Exception:
                pass
            if dialog:
                break

        if not dialog:
            raise RuntimeError("Dialog not found")

        dialog.set_focus()
        time.sleep(0.4)
        drive_selected  = _select_drive_in_dialog(dialog, drive_letter)
        install_clicked = _click_button(dialog, ["install", "yükle", "next", "ileri", "ok", "tamam"])

        if install_clicked:
            suffix = f"{drive_label} diski seçildi ve" if drive_selected else "Varsayılan disk ile"
            return f"{suffix} yükleme komutu verildi: '{game_name}'."
        return f"Lütfen Steam üzerinden yüklemeyi manuel olarak onaylayın: '{game_name}'."

    except ImportError:
        return _handle_install_dialog_pyautogui(game_name, best_drive)
    except Exception as e:
        print(f"[GameUpdater] ⚠️ pywinauto hatası: {e}")
        return _handle_install_dialog_pyautogui(game_name, best_drive)


def _handle_install_dialog_pyautogui(game_name: str, best_drive: dict) -> str:
    try:
        import pyautogui
        import pygetwindow as gw
    except ImportError:
        return f"Yükleme iletişim kutusu açıldı. Lütfen manuel olarak {best_drive['letter']}: diskini seçerek devam edin."

    pyautogui.FAILSAFE = False
    drive_label  = f"{best_drive['letter']}:"
    install_win  = None

    for _ in range(30):
        time.sleep(0.5)
        for w in gw.getAllWindows():
            if ("install" in w.title.lower() or "steam" in w.title.lower()) and w.width > 300 and w.visible:
                install_win = w
                break
        if install_win:
            break

    if not install_win:
        return f"Lütfen '{drive_label}' diskini seçip yüklemeyi manuel tamamlayın: '{game_name}'."

    try:
        install_win.activate()
        time.sleep(0.4)
    except Exception:
        pass

    wx, wy = install_win.left, install_win.top
    ww, wh = install_win.width, install_win.height
    pyautogui.click(wx + int(ww * 0.35), wy + int(wh * 0.45))
    time.sleep(0.2)
    pyautogui.typewrite(best_drive["letter"], interval=0.05)
    time.sleep(0.2)
    pyautogui.click(wx + int(ww * 0.72), wy + int(wh * 0.88))
    return f"Disk seçimi {drive_label} için denendi ve yükleme onaylandı: '{game_name}'."


def _install_steam_game(steam_path: Path, game_name: str = None, app_id: str = None) -> str:
    if not _ensure_steam_running(steam_path):
        return "Steam başlatılamadı."

    steam_exe       = steam_path / "steam.exe"
    installed_games = _get_steam_games(steam_path)

    already = None
    if app_id:
        already = next((g for g in installed_games if g["id"] == str(app_id)), None)
    elif game_name:
        name_lower = game_name.lower()
        already    = next((g for g in installed_games if name_lower in g["name"].lower()), None)
    else:
        return "Bir oyun ismi veya AppID belirtilmelidir."

    if already:
        state = already["state"]
        name  = already["name"]
        if state == 4:
            return f"'{name}' zaten yüklü ve güncel."
        if state == 1026:
            return f"'{name}' şu anda indiriliyor veya güncelleniyor."
        if state in (6, 516):
            subprocess.Popen([str(steam_exe), f"steam://update/{already['id']}"])
            return f"'{name}' için bekleyen güncelleme var. İşlem başlatıldı."
        return f"'{name}' zaten yüklü."

    if not app_id and game_name:
        found_id, found_name = _search_steam_appid(game_name)
        if not found_id:
            return f"'{game_name}' Steam üzerinde bulunamadı. AppID girerek tekrar deneyin."
        app_id    = found_id
        game_name = found_name or game_name
        print(f"[GameUpdater] 🔍 Yükleniyor: {game_name} (AppID: {app_id})")

    try:
        subprocess.Popen([str(steam_exe), f"steam://install/{app_id}"])
        threading.Thread(target=_handle_install_dialog, args=(game_name or str(app_id),), daemon=True).start()
        return f"'{game_name}' yüklemesi başlatıldı. İndirme onayı bekleniyor."
    except Exception as e:
        return f"Yükleme başarısız: {e}"


def _get_download_status(steam_path: Path) -> str:
    games   = _get_steam_games(steam_path)
    active  = [g for g in games if g["state"] == 1026]
    pending = [g for g in games if g["state"] in (6, 516)]
    lines   = []
    if active:
        lines.append(f"İndiriliyor: {', '.join(g['name'] for g in active)}.")
    if pending:
        names  = ", ".join(g["name"] for g in pending[:5])
        suffix = f" ve {len(pending) - 5} oyun daha" if len(pending) > 5 else ""
        lines.append(f"Bekleyen güncellemeler: {names}{suffix}.")
    return " ".join(lines) if lines else "Aktif bir indirme veya beklemede olan güncelleme bulunmamaktadır."


def _watch_and_shutdown(steam_path: Path, speak=None, check_interval: int = 30, timeout_hours: int = 12):
    print("[GameUpdater] 👁️ Kapanış izleme protokolü devrede...")
    deadline = time.time() + timeout_hours * 3600

    for _ in range(24):
        time.sleep(5)
        active = [g for g in _get_steam_games(steam_path) if g["state"] == 1026]
        if active:
            names = ", ".join(g["name"] for g in active)
            if speak: speak(f"{names} için indirme başlatıldı. İşlem tamamlandığında sistem otomatik olarak kapatılacaktır.")
            break
    else:
        return

    while time.time() < deadline:
        time.sleep(check_interval)
        if not any(g["state"] == 1026 for g in _get_steam_games(steam_path)):
            if speak: speak("İndirme işlemi tamamlandı. Sistem kapatılıyor.")
            time.sleep(5)
            subprocess.run(["shutdown", "/s", "/t", "10"])
            return

    if speak: speak("İndirme süresi aşıldı. Otomatik sistem kapatma protokolü iptal edildi.")


def _get_epic_games() -> list[dict]:
    manifests_path = (Path(os.environ.get("PROGRAMDATA", "C:/ProgramData"))
                      / "Epic" / "EpicGamesLauncher" / "Data" / "Manifests")
    if not manifests_path.exists():
        return []
    games = []
    for item_file in manifests_path.glob("*.item"):
        try:
            data = json.loads(item_file.read_text(encoding="utf-8"))
            name = data.get("DisplayName") or data.get("AppName", "")
            if name:
                games.append({"id": data.get("AppName", ""), "name": name})
        except Exception:
            continue
    return games


def _is_epic_running() -> bool:
    try:
        return "epicgameslauncher.exe" in subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq EpicGamesLauncher.exe"],
            capture_output=True, text=True
        ).stdout.lower()
    except Exception:
        return False


def _update_epic_games(epic_path: Path, game_name: str = None) -> str:
    epic_exe = epic_path / "EpicGamesLauncher.exe"
    if not epic_exe.exists():
        return "Epic Games Launcher tespit edilemedi."
    games = _get_epic_games()
    if game_name:
        name_lower = game_name.lower()
        matched    = [g for g in games if name_lower in g["name"].lower()]
        if not matched:
            return f"'{game_name}' Epic kütüphanesinde bulunamadı."
        try:
            subprocess.Popen([str(epic_exe), f"com.epicgames.launcher://apps/{matched[0]['id']}?action=launch&silent=true"])
            return f"'{matched[0]['name']}' Epic üzerinden başlatıldı."
        except Exception as e:
            return f"Epic güncelleme hatası: {e}"
    else:
        try:
            if _is_epic_running():
                for g in games[:10]:
                    subprocess.Popen([str(epic_exe), f"com.epicgames.launcher://apps/{g['id']}?action=launch&silent=true"])
                    time.sleep(0.5)
                return f"{len(games)} adet Epic oyunu için güncelleme kontrolü sağlandı."
            else:
                subprocess.Popen([str(epic_exe)])
                return f"Epic Games Launcher açıldı. {len(games)} oyun denetlenecek."
        except Exception as e:
            return f"Epic güncelleme hatası: {e}"


def _schedule_daily_update(hour: int = 3, minute: int = 0) -> str:
    task_name   = "JARVIS_GameUpdater"
    script_path = Path(__file__).resolve()
    subprocess.run(["schtasks", "/Delete", "/TN", task_name, "/F"], capture_output=True)
    for extra in (["/RL", "HIGHEST", "/RU", "SYSTEM"], []):
        cmd    = ["schtasks", "/Create", "/TN", task_name,
                  "/TR", f'"{sys.executable}" "{script_path}" --scheduled',
                  "/SC", "DAILY", "/ST", f"{hour:02d}:{minute:02d}", "/F", *extra]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return f"Günlük oyun güncelleme görevi {hour:02d}:{minute:02d} saatine zamanlandı."
    return f"Zamanlama başarısız: {result.stderr.strip()}"


def _cancel_scheduled_update() -> str:
    result = subprocess.run(["schtasks", "/Delete", "/TN", "JARVIS_GameUpdater", "/F"],
                            capture_output=True, text=True)
    return "Zamanlanmış güncelleme görevi iptal edildi." if result.returncode == 0 else "İptal edilecek bir görev bulunamadı."


def _get_schedule_status() -> str:
    result = subprocess.run(["schtasks", "/Query", "/TN", "JARVIS_GameUpdater", "/FO", "LIST"],
                            capture_output=True, text=True)
    if result.returncode != 0:
        return "Planlanmış oyun güncelleme görevi bulunmamaktadır."
    for line in result.stdout.strip().split("\n"):
        if any(k in line for k in ("Next Run", "Sonraki", "Prochaine", "Próxima", "Nächste")):
            return f"Oyun güncellemesi zamanlandı. {line.strip()}"
    return "Oyun güncelleme görevi aktiftir."


def game_updater(parameters: dict, player=None, speak=None) -> str:
    p         = parameters or {}
    action    = p.get("action",    "update").lower().strip()
    platform  = p.get("platform",  "both").lower().strip()
    game_name = (p.get("game_name") or "").strip() or None
    app_id    = (p.get("app_id")    or "").strip() or None
    hour      = int(p.get("hour",   3))
    minute    = int(p.get("minute", 0))
    shutdown  = str(p.get("shutdown_when_done", "false")).lower() == "true"

    results = []

    if action == "schedule":        return _schedule_daily_update(hour=hour, minute=minute)
    if action == "cancel_schedule": return _cancel_scheduled_update()
    if action == "schedule_status": return _get_schedule_status()

    if action == "list":
        if platform in ("steam", "both"):
            steam_path = _find_steam_path()
            if steam_path:
                games = _get_steam_games(steam_path)
                if games:
                    names  = ", ".join(g["name"] for g in games[:8])
                    suffix = f" ve {len(games) - 8} daha" if len(games) > 8 else ""
                    results.append(f"Steam ({len(games)} oyun): {names}{suffix}.")
                else:
                    results.append("Steam: Oyun bulunamadı.")
            else:
                results.append("Steam: Sistemde yüklü değil.")
        if platform in ("epic", "both"):
            games = _get_epic_games()
            if games:
                names  = ", ".join(g["name"] for g in games[:8])
                suffix = f" ve {len(games) - 8} daha" if len(games) > 8 else ""
                results.append(f"Epic ({len(games)} oyun): {names}{suffix}.")
            else:
                results.append("Epic: Oyun bulunamadı.")
        return " | ".join(results) or "Platform tespit edilemedi."

    if action == "download_status":
        if platform in ("steam", "both"):
            steam_path = _find_steam_path()
            results.append(_get_download_status(steam_path) if steam_path else "Steam: Yüklü değil.")
        if platform in ("epic", "both"):
            results.append("Epic doğrudan indirme durumu izlemesini desteklemiyor.")
        return " ".join(results)

    if action in ("install", "update"):
        if platform in ("steam", "both"):
            steam_path = _find_steam_path()
            if not steam_path:
                results.append("Steam: Yüklü değil.")
            else:
                if game_name:
                    installed    = _get_steam_games(steam_path)
                    name_lower   = game_name.lower()
                    is_installed = any(name_lower in g["name"].lower() for g in installed)

                    if not is_installed:
                        msg = _install_steam_game(steam_path, game_name=game_name, app_id=app_id)
                        if shutdown:
                            threading.Thread(target=_watch_and_shutdown,
                                             kwargs={"steam_path": steam_path, "speak": speak},
                                             daemon=True).start()
                            msg += " Otomatik kapatma protokolü aktifleştirildi."
                        if player: player.write_log(f"SYS: [GameUpdater] {msg[:100]}")
                        if speak: speak(msg)
                        return msg
                    else:
                        results.append(f"Steam: {_update_steam_games(steam_path, game_name=game_name)}")
                else:
                    if action == "install":
                        results.append("Steam: Yükleme için oyun adı belirtilmelidir.")
                    else:
                        results.append(f"Steam: {_update_steam_games(steam_path)}")

                if shutdown:
                    threading.Thread(target=_watch_and_shutdown,
                                     kwargs={"steam_path": steam_path, "speak": speak},
                                     daemon=True).start()
                    results.append("Otomatik kapatma devrede.")

        if platform in ("epic", "both"):
            epic_path = _find_epic_path()
            if epic_path:
                results.append(f"Epic: {_update_epic_games(epic_path, game_name=game_name)}")
            else:
                results.append("Epic: Yüklü değil.")

        output = " | ".join(results) or "Uygulanacak eylem bulunamadı."
        if player: player.write_log(f"SYS: [GameUpdater] {output[:100]}")
        if speak: speak(output)
        return output

    return f"Bilinmeyen komut reddedildi: '{action}'."


if __name__ == "__main__":
    if "--scheduled" in sys.argv:
        print(f"[GameUpdater] 🕐 Zamanlanmış görev tetiklendi: {datetime.now().strftime('%H:%M')}")
        print(f"[GameUpdater] ✅ {game_updater({'action': 'update', 'platform': 'both'})}")