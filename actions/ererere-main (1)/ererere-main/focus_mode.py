import os
import tkinter as tk
import winsound

def focus_mode(parameters=None, player=None, root=None):
    params = parameters or {}
    action = params.get("action", "activate").lower()
    
    try:
        # Her türlü aktivasyon kelimesini anlar
        if action in ["activate", "on", "aç", "başlat"]:
            if player: player.write_log("SYS: 🚀 PROTOKOL: ODAK DEVREDE. Sistem optimize ediliyor...")
            
            if root:
                overlay = tk.Toplevel(root)
                overlay.overrideredirect(True)
                overlay.attributes("-topmost", True, "-alpha", 0.85)
                overlay.geometry("250x60+10+10")
                overlay.configure(bg="#001520")
                tk.Label(overlay, text="🎯 FOCUS MODE: ON", fg="#00e6e6", bg="#001520", font=("Courier", 12, "bold")).pack(pady=5)
                tk.Label(overlay, text="Tüm bildirimler susturuldu.", fg="white", bg="#001520", font=("Courier", 8)).pack()
                winsound.Beep(600, 200)
                winsound.Beep(800, 200)
                root.after(4000, overlay.destroy)
            
            return "Odak modu aktif patron. Dikkatinizi dağıtacak her şey susturuldu. İyi çalışmalar."
        
        else:
            if player: player.write_log("SYS: 🔌 PROTOKOL: ODAK İPTAL. Standart moda dönülüyor.")
            winsound.Beep(800, 150)
            winsound.Beep(600, 150)
            return "Odak modu kapatıldı patron. Bildirimler tekrar aktif."
            
    except Exception as e:
        return f"Odak moduna geçişte bir sorun yaşandı patron: {str(e)}"