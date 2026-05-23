import os
import time
import tkinter as tk
import winsound
import pyautogui
import webbrowser
import subprocess

def cinema_mode(parameters=None, player=None, root=None) -> str:
    params = parameters or {}
    action = params.get("action", "on").lower()
    
    try:
        if action in ["on", "aç", "başlat", "aktive et"]:
            if player: 
                player.write_log("SYS: 🍿 Sinema Modu başlatılıyor...")
            
            # Masaüstünü temizle (Tüm pencereleri aşağı al) - Hata toleranslı
            try:
                pyautogui.hotkey('win', 'd')
                time.sleep(0.5)
            except Exception as e:
                if player: player.write_log(f"SYS: Masaüstü temizleme hatası: {e}")
            
            # Öncelik Windows Netflix uygulamasında, yoksa tarayıcıdan açar
            netflix_opened = False
            try:
                # subprocess ile güvenli çağırma
                result = subprocess.run("start netflix:", shell=True, capture_output=True)
                if result.returncode == 0:
                    netflix_opened = True
            except Exception:
                pass
                
            if not netflix_opened:
                webbrowser.open("https://www.netflix.com")
            
            if root:
                try:
                    hud = tk.Toplevel(root)
                    hud.overrideredirect(True)
                    hud.attributes("-topmost", True, "-alpha", 0.95)
                    hud.geometry("300x80+10+10")
                    hud.configure(bg="#1a001a")
                    
                    tk.Label(hud, text="🍿 SİNEMA MODU: AKTİF", font=("Courier", 12, "bold"), fg="#ff00ff", bg="#1a001a").pack(pady=5)
                    tk.Label(hud, text="Arkanıza yaslanın ve keyfini çıkarın.", font=("Courier", 9), fg="white", bg="#1a001a").pack()
                    
                    winsound.Beep(400, 200)
                    winsound.Beep(600, 300)
                    
                    root.after(4000, lambda: hud.destroy() if hud.winfo_exists() else None)
                except Exception as hud_err:
                    if player: player.write_log(f"SYS: Sinema HUD hatası: {hud_err}")
                    
            return "Sinema modu aktif edildi. İyi seyirler patron."
        else:
            return "Sinema modu için geçersiz komut."
            
    except Exception as exc:
        if player: player.write_log(f"SYS: Sinema modu başlatılamadı: {exc}")
        return "Sinema modu başlatılırken bir sorun oluştu."