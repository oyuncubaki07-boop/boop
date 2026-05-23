import tkinter as tk
import winsound

# AÇIKLAMA: J.A.R.V.I.S.'in kullanıcının komutunu anlamadığı veya bir işlemde hata çıktığı durumlarda kullanıcıya görsel ve sesli geri bildirim vermesini sağlar.

def report_issue(parameters=None, player=None, root=None):
    params = parameters or {}
    issue_message = params.get("message", "Üzgünüm patron, ne demek istediğinizi veya komutu tam olarak anlayamadım.")
    
    try:
        if player: player.write_log(f"SYS-UYARI: {issue_message}")
        
        if root:
            try:
                hud = tk.Toplevel(root)
                hud.overrideredirect(True)
                hud.attributes("-topmost", True, "-alpha", 0.95)
                hud.geometry("400x100+10+10")
                hud.configure(bg="#330000") # Uyarı için Koyu Kırmızı
                
                tk.Label(hud, text="⚠️ SİSTEM GERİ BİLDİRİMİ", font=("Courier", 12, "bold"), fg="#ff3333", bg="#330000").pack(pady=5)
                tk.Label(hud, text=issue_message, font=("Courier", 9), fg="white", bg="#330000", wraplength=380).pack()
                
                # Anlamama / Hata Sesi
                winsound.Beep(300, 200)
                winsound.Beep(200, 300)
                root.after(5000, hud.destroy)
            except: pass
            
        return f"Geri bildirim kaydedildi: {issue_message}. Lütfen komutu tekrar edin patron."
        
    except Exception as e:
        return f"Geri bildirim modülünde hata: {str(e)}"