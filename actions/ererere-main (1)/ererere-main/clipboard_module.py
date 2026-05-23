import tkinter as tk

def read_clipboard(parameters=None, player=None, root=None) -> str:
    try:
        if not root:
            return "Arayüz bağlantısı yok, panoyu okuyamıyorum patron."
            
        if player: 
            player.write_log("SYS: 📋 Pano verisi analiz ediliyor...")
        
        # Panodaki metni almayı dene (Dosya/Resim kopyalandığında TclError fırlatır)
        try:
            pano_metni = root.clipboard_get()
        except tk.TclError:
            return "Patron, panoda okunabilir bir metin yok. Muhtemelen bir dosya veya resim kopyaladınız."
        except Exception as e:
            return f"Panoya erişilemedi: {e}"
            
        if not pano_metni or not pano_metni.strip():
            return "Pano şu anda tamamen boş."
            
        # Ekranda kısa bir HUD ile panoyu göster
        try:
            hud = tk.Toplevel(root)
            hud.overrideredirect(True)
            hud.attributes("-topmost", True, "-alpha", 0.95)
            hud.geometry("400x120+10+10")
            hud.configure(bg="#002233")
            
            tk.Label(hud, text="📋 PANO İÇERİĞİ", font=("Courier", 12, "bold"), fg="#33ccff", bg="#002233").pack(pady=5)
            
            # Ekrana taşmasın diye çok uzunsa metni kes
            gosterilecek = pano_metni.strip()
            if len(gosterilecek) > 80:
                gosterilecek = gosterilecek[:77] + "..."
                
            tk.Label(hud, text=gosterilecek, font=("Courier", 9), fg="white", bg="#002233", wraplength=380, justify="left").pack(pady=5)
            
            # 5 saniye sonra arayüzü kapat
            root.after(5000, lambda: hud.destroy() if hud.winfo_exists() else None)
        except Exception as hud_err:
            if player: player.write_log(f"SYS: Pano HUD gösterim hatası: {hud_err}")
            
        return f"Panoda şu metin var: {pano_metni[:100]}"
        
    except Exception as exc:
        if player: player.write_log(f"SYS: Pano modülü genel hatası: {exc}")
        return "Panoyu okurken beklenmedik bir hata oluştu."