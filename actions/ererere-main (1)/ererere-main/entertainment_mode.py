import tkinter as tk
import random
import winsound
import os
import threading
import time

def _hacker_visuals():
    """Arka planda 3 adet yeşil renkli Matrix tarzı CMD tarama ekranı açar."""
    try:
        for _ in range(3):
            # 'color a' yazıyı yeşil yapar, 'dir /s' tüm diski tarıyormuş gibi sonsuz yazı akıtır
            os.system('start cmd /k "color a & dir /s"')
            time.sleep(0.4)
    except:
        pass

def entertainment_mode(parameters=None, player=None, root=None):
    try:
        if player: player.write_log("SYS: 🎭 Eğlence ve Gösteri protokolü devrede.")
        
        # Otonom görsel şöleni (CMD ekranlarını) sistemi kitlememesi için ayrı kolda başlatıyoruz
        threading.Thread(target=_hacker_visuals, daemon=True).start()
        
        jokes = [
            "Neden bilgisayarlar soğuk sever? Çünkü Windows (pencereler) açık!",
            "Stark endüstrilerinde bir kural vardır: Önce ateş et, sonra soru sor. Ama ben önce soruyorum efendim.",
            "Among Us'ta impostor olduğunuzu anladığımda size yardım edemem patron, kurallar böyle.",
            "Bir yazılımcının en çok söylediği yalan nedir bilir misiniz? 'Kodum bilgisayarımda sorunsuz çalışıyordu'."
        ]
        
        secilen_saka = random.choice(jokes)
        
        if root:
            try:
                hud = tk.Toplevel(root)
                hud.overrideredirect(True)
                hud.attributes("-topmost", True, "-alpha", 0.9)
                hud.geometry("400x120+10+10")
                hud.configure(bg="#000d1a")
                
                tk.Label(hud, text="🎭 EĞLENCE PROTOKOLÜ", fg="#00ff00", bg="#000d1a", font=("Courier", 12, "bold")).pack(pady=5)
                tk.Label(hud, text=secilen_saka, fg="white", bg="#000d1a", font=("Courier", 9), wraplength=380).pack()
                
                winsound.Beep(400, 100)
                winsound.Beep(600, 150)
                root.after(6000, hud.destroy)
            except: pass
            
        return f"Görsel şölen başlatıldı patron. {secilen_saka}"
        
    except Exception as e:
        return f"Eğlence modülünde bir donanım/yazılım hatası oluştu patron: {str(e)}"