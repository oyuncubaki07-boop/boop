# actions/welcome_screen.py
import tkinter as tk
from datetime import datetime
import math
import threading

def show_welcome_hologram(parent_root):
    splash = tk.Toplevel(parent_root)
    splash.overrideredirect(True)
    splash.attributes("-topmost", True)
    splash.attributes("-alpha", 0.0)
    splash.configure(bg="#000000")
    
    w, h = 550, 250
    sw, sh = splash.winfo_screenwidth(), splash.winfo_screenheight()
    splash.geometry(f"{w}x{h}+{(sw//2)-(w//2)}+{(sh//2)-(h//2)}")
    
    # Saat dilimine göre selamlama ve renk teması
    hour = datetime.now().hour
    if 5 <= hour < 12:
        greeting = "GÜNAYDIN EFENDİM 👋"
        accent_color = "#FFB347"  # turuncu
        glow_color = "#FFD700"
    elif 12 <= hour < 18:
        greeting = "TÜNAYDIN EFENDİM 👋"
        accent_color = "#4CAF50"
        glow_color = "#8BC34A"
    elif 18 <= hour < 22:
        greeting = "İYİ AKŞAMLAR EFENDİM 👋"
        accent_color = "#FF7043"
        glow_color = "#FF8A65"
    else:
        greeting = "İYİ GECELER EFENDİM 👋"
        accent_color = "#5C6BC0"
        glow_color = "#7986CB"
    
    # Holografik arka plan ışıması için Canvas
    canvas = tk.Canvas(splash, width=w, height=h, bg="#000000", highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)
    
    # Işın efekti (dairesel gradient taklidi)
    for i in range(1, 6):
        alpha = hex(int(15 - i*2))[2:]  # 0-15 arası opaklık
        color = f"#{accent_color[1:]}{alpha}" if len(alpha)==2 else f"#{accent_color[1:]}0{alpha}"
        canvas.create_oval(50*i, 30*i, w-50*i, h-30*i, outline=color, width=1)
    
    # J.A.R.V.I.S. başlığı (glow efekti)
    title_text = "⚡ J.A.R.V.I.S. MARK-XXX ⚡"
    title_label = tk.Label(canvas, text=title_text, font=("Orbitron", 14, "bold"),
                           fg=accent_color, bg="#000000")
    title_label.place(relx=0.5, rely=0.3, anchor="center")
    
    # Selamlama metni (daha büyük)
    greet_label = tk.Label(canvas, text=greeting, font=("Orbitron", 20, "bold"),
                           fg=glow_color, bg="#000000")
    greet_label.place(relx=0.5, rely=0.6, anchor="center")
    
    # Alt bilgi - sistem durumu
    status_text = "Tüm sistemler çevrimiçi | Nöral bağlantı kuruldu"
    status_label = tk.Label(canvas, text=status_text, font=("Consolas", 9),
                            fg="#888888", bg="#000000")
    status_label.place(relx=0.5, rely=0.85, anchor="center")
    
    # Dalgalanan holografik çizgiler (animasyon)
    def animate_lines():
        for i in range(10):
            y_offset = 20 + i * 8
            line = canvas.create_line(50, y_offset, w-50, y_offset, fill=accent_color, width=1, tags=f"line{i}")
            # Hareket efekti için her 50ms'de bir y değiştir
        # Basit animasyon döngüsü
        def move_lines():
            for i in range(10):
                canvas.move(f"line{i}", 0, 1)
                # sınırlara gelince sıfırla
                if canvas.coords(f"line{i}")[1] > h:
                    canvas.coords(f"line{i}", 50, 20 + i*8, w-50, 20 + i*8)
            canvas.after(80, move_lines)
        move_lines()
    
    # Ses efekti – daha havalı (arpej)
    try:
        import winsound
        # Kısa bir arpej
        for freq in [880, 1046, 1318, 1568]:
            winsound.Beep(freq, 40)
    except:
        pass
    
    # Fade-in efekti (daha yumuşak)
    def fade_in(alpha=0.0):
        if alpha < 0.95:
            alpha += 0.05
            splash.attributes("-alpha", alpha)
            splash.after(25, lambda: fade_in(alpha))
        else:
            # Hafif titreşim efekti için bir kez daha parlat
            splash.attributes("-alpha", 1.0)
    
    fade_in()
    
    # Animasyon çizgilerini başlat
    animate_lines()
    
    # Ekranı 5 saniye göster, sonra fade-out yaparak kapat
    def fade_out(alpha=1.0):
        if alpha > 0.05:
            alpha -= 0.05
            splash.attributes("-alpha", alpha)
            splash.after(25, lambda: fade_out(alpha))
        else:
            splash.destroy()
    
    splash.after(5000, lambda: fade_out(1.0))