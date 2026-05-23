import os
import tkinter as tk
import winsound

def cyber_sleep(parameters=None, player=None, root=None) -> str:
    if player: player.write_log("SYS: 🌙 Siber Uyku Protokolü başlatılıyor...")
    
    try:
        if root:
            try:
                hud = tk.Toplevel(root)
                hud.overrideredirect(True)
                hud.attributes("-topmost", True, "-alpha", 0.95)
                hud.geometry("300x80+10+10")
                hud.configure(bg="#00001a")
                
                tk.Label(hud, text="🌙 SİBER UYKU", font=("Courier", 14, "bold"), fg="#99ccff", bg="#00001a").pack(pady=5)
                tk.Label(hud, text="Sistem derin uykuya geçiyor...", font=("Courier", 9), fg="white", bg="#00001a").pack()
                
                winsound.Beep(500, 300)
                winsound.Beep(300, 400)
                
                root.after(3000, lambda: hud.destroy() if hud.winfo_exists() else None)
            except Exception:
                pass
                
        # Windows Uyku / Hazırda Beklet Komutu
        # Uyarı: Hibernate açık değilse bu komut sistemi Uyku moduna alır.
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        
        return "Sistem uyku moduna alındı. Görüşmek üzere patron."
        
    except Exception as exc:
        if player: player.write_log(f"SYS: Uyku modu hatası: {exc}")
        return "Uyku moduna geçiş sırasında bir hata oluştu."