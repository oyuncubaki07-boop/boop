import webbrowser
import tkinter as tk

def workspace_mode(parameters=None, player=None, root=None):
    """
    Çalışma ortamını hazırlar: varsayılan web tarayıcısını açar.
    Platform bağımsız çalışır.
    """
    if player:
        player.write_log("SYS: 🚀 Çalışma İstasyonu hazırlanıyor...")
    
    # Varsayılan tarayıcıyı aç
    try:
        webbrowser.open_new_tab("https://www.google.com")
    except Exception as e:
        hata = f"Tarayıcı açılamadı: {e}"
        if player:
            player.write_log(f"ERR: {hata}")
        return hata
    
    # Havalı HUD penceresi (opsiyonel, sadece root varsa)
    if root:
        try:
            hud = tk.Toplevel(root)
            hud.overrideredirect(True)
            hud.attributes("-topmost", True, "-alpha", 0.92)
            hud.geometry("360x80+15+15")
            hud.configure(bg="#0a0a2a")
            
            tk.Label(hud, text="🚀 ÇALIŞMA İSTASYONU", font=("Orbitron", 11, "bold"),
                     fg="#00ffcc", bg="#0a0a2a").pack(pady=5)
            tk.Label(hud, text="Tarayıcı hazır, üretim zamanı!", font=("Segoe UI", 9),
                     fg="white", bg="#0a0a2a").pack()
            
            # Hafif bip sesi (sadece Windows'ta çalışır, hata vermez)
            try:
                import winsound
                winsound.Beep(800, 100)
                winsound.Beep(1000, 150)
            except:
                pass
            
            root.after(2500, hud.destroy)
        except Exception as e:
            if player:
                player.write_log(f"HUD hatası: {e}")
    
    return "Çalışma ortamınız hazırlandı patron. Tarayıcı açıldı, projeleriniz için hazırsınız."