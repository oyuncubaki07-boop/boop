# actions/ghost_mode.py
# J.A.R.V.I.S. Hayalet Modu - Hızlı Gizlilik

import pyautogui
import os
import time
import tkinter as tk
import winsound
import sys

def _show_hud(root, message, duration=2500):
    """HUD gösterimi."""
    if not root:
        return
    try:
        hud = tk.Toplevel(root)
        hud.overrideredirect(True)
        hud.attributes("-topmost", True, "-alpha", 0.88)
        hud.geometry("280x60+15+15")
        hud.configure(bg="#00050a")
        tk.Label(hud, text="🕵️ " + message, font=("Orbitron", 9, "bold"),
                 fg="#00e6e6", bg="#00050a").pack(expand=True)
        try:
            winsound.Beep(500, 100)
        except:
            pass
        root.after(duration, lambda: hud.destroy() if hud.winfo_exists() else None)
    except:
        pass

def ghost_mode(parameters=None, player=None, root=None, speak=None) -> str:
    """
    Hayalet modu - tüm pencereleri gizler, sesi kısar, kamuflaj sağlar.
    
    Parametreler:
        action (str): "activate", "deactivate" (varsayılan: "activate")
        mute_sound (bool): Sesi kıs (varsayılan: True)
        hide_windows (bool): Pencereleri gizle (varsayılan: True)
    """
    params = parameters or {}
    action = params.get("action", "activate").lower()
    mute_sound = params.get("mute_sound", True)
    hide_windows = params.get("hide_windows", True)
    
    try:
        if action in ["activate", "aç", "başlat", "enable"]:
            if player:
                player.write_log("SYS: 👻 PROTOKOL HAYALET DEVREDE.")
            
            if speak:
                speak("Hayalet protokolü aktif. Gizlilik sağlanıyor.")
            
            # 1. Ses kontrolü
            if mute_sound:
                try:
                    # Sesi tamamen kısma (sıfırlama)
                    for _ in range(30):
                        pyautogui.press("volumedown")
                    # Biraz aç (güvenli seviye)
                    for _ in range(5):
                        pyautogui.press("volumeup")
                    if player:
                        player.write_log("SYS: Ses seviyesi güvenli seviyeye ayarlandı.")
                except Exception as e:
                    if player:
                        player.write_log(f"SYS: Ses ayarı yapılamadı: {e}")
            
            # 2. Tüm pencereleri masaüstüne indir
            if hide_windows:
                pyautogui.hotkey('win', 'd')
                time.sleep(0.3)
            
            # 3. Kamuflaj: Opera veya Chrome aç (deneysel)
            try:
                if os.system("start opera") != 0:
                    os.system("start chrome")
                if player:
                    player.write_log("SYS: Kamuflaj tarayıcısı açıldı.")
            except:
                pass
            
            # HUD gösterimi
            _show_hud(root, "GİZLİLİK SAĞLANDI")
            
            return "Hayalet protokolü aktif. Ekran temizlendi, sesler güvenli seviyeye çekildi ve kamuflaj sağlandı patron."

        elif action in ["deactivate", "kapat", "stop", "disable"]:
            if player:
                player.write_log("SYS: Hayalet modu kapatılıyor.")
            
            if speak:
                speak("Hayalet protokolü kapatılıyor, efendim.")
            
            _show_hud(root, "HAYALET MODU KAPATILDI", duration=2000)
            return "Hayalet modu devre dışı bırakıldı."

        else:
            return f"Bilinmeyen aksiyon: {action}. Kullanılabilir: activate, deactivate"

    except Exception as e:
        error_msg = f"Hayalet modunda hata: {str(e)}"
        if player:
            player.write_log(f"SYS: {error_msg}")
        return error_msg