# actions/smart_reminder.py
# J.A.R.V.I.S. Akıllı Hatırlatıcı Modülü (Gelişmiş)

import time
import threading
import tkinter as tk
import winsound
import sys
from datetime import datetime, timedelta

def _reminder_thread(minutes, message, root, player, repeat=False):
    """Arka planda çalışan hatırlatıcı thread'i."""
    try:
        # Dakika -> saniye bekle
        time.sleep(minutes * 60)

        # Bildirim döngüsü (eğer tekrarlı ise 3 kez)
        repeats = 3 if repeat else 1
        for r in range(repeats):
            if player:
                player.write_log(f"⏰ HATIRLATMA ZAMANI: {message}")

            # Sesli uyarı (Windows'ta farklı frekanslar)
            if sys.platform == "win32":
                for freq in [1200, 1500, 1800]:
                    winsound.Beep(freq, 200)
                    time.sleep(0.05)
            else:
                # Linux/Mac için basit bir uyarı (terminal sesi)
                print("\a")  # ASCII bell
                time.sleep(0.5)

            # HUD gösterimi
            if root:
                try:
                    hud = tk.Toplevel(root)
                    hud.overrideredirect(True)
                    hud.attributes("-topmost", True, "-alpha", 0.95)
                    hud.geometry("420x130+15+15")
                    hud.configure(bg="#1a0033")  # Mor tema

                    tk.Label(hud, text="🔔 ZAMAN DOLDU PATRON!", font=("Orbitron", 12, "bold"),
                             fg="#ff66cc", bg="#1a0033").pack(pady=8)
                    tk.Label(hud, text=message.upper(), font=("Segoe UI", 10, "bold"),
                             fg="white", bg="#1a0033", wraplength=380).pack()
                    tk.Label(hud, text=f"⏱️ {datetime.now().strftime('%H:%M:%S')}", font=("Consolas", 8),
                             fg="#aaaaaa", bg="#1a0033").pack(pady=5)

                    # Kapatma butonu (isteğe bağlı)
                    def close_hud():
                        hud.destroy()
                    tk.Button(hud, text="Tamam", command=close_hud, bg="#6600cc", fg="white",
                              relief=tk.FLAT, padx=10).pack(pady=5)

                    root.after(10000, lambda: hud.destroy() if hud.winfo_exists() else None)  # 10 saniye sonra otomatik kapanır
                except Exception as e:
                    if player:
                        player.write_log(f"HUD hatası: {e}")

            if repeats > 1 and r < repeats-1:
                time.sleep(2)  # Tekrarlı bildirimler arasında 2 saniye

    except Exception as e:
        if player:
            player.write_log(f"Hatırlatıcı thread hatası: {e}")

def set_reminder(parameters=None, player=None, root=None, speak=None) -> str:
    """
    Akıllı hatırlatıcı kurar.
    
    Parametreler:
        minutes (int): Kaç dakika sonra hatırlatılacak (varsayılan: 1)
        message (str): Hatırlatma mesajı (varsayılan: "Bir hatırlatmanız var.")
        repeat (bool): 3 kez tekrarlı bildirim (varsayılan: False)
    """
    params = parameters or {}
    minutes = float(params.get("minutes", 1))
    message = params.get("message", "Bir hatırlatmanız var.")
    repeat = params.get("repeat", False)

    if minutes <= 0:
        return "Patron, süre pozitif bir sayı olmalı."

    if player:
        player.write_log(f"SYS: ⏲️ {minutes} dakika sonra hatırlatıcı kuruldu: {message}")

    # Thread başlat
    threading.Thread(target=_reminder_thread, args=(minutes, message, root, player, repeat), daemon=True).start()

    # Sesli onay
    if speak:
        speak(f"{minutes} dakika sonra size '{message}' konusunu hatırlatacağım.")

    # Anında HUD onayı
    if root:
        try:
            hud = tk.Toplevel(root)
            hud.overrideredirect(True)
            hud.attributes("-topmost", True, "-alpha", 0.9)
            hud.geometry("350x80+15+50")
            hud.configure(bg="#002233")
            tk.Label(hud, text="⏰ HATIRLATICI KURULDU", font=("Orbitron", 10, "bold"),
                     fg="#00ffcc", bg="#002233").pack(pady=5)
            tk.Label(hud, text=f"{minutes} dakika sonra: {message[:50]}", font=("Segoe UI", 9),
                     fg="white", bg="#002233").pack()
            try:
                winsound.Beep(800, 100)
            except:
                pass
            root.after(3000, hud.destroy)
        except:
            pass

    return f"✅ {minutes} dakika sonrasına hatırlatıcı kuruldu patron. Size '{message}' konusunu hatırlatacağım."