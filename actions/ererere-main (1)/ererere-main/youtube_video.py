import webbrowser
import urllib.parse
import tkinter as tk
from threading import Thread

def youtube_video(parameters=None, player=None, root=None, speak=None):
    """
    YouTube'da video açar veya direkt bir video URL'sini açar.
    
    Parametreler:
        query (str): Aranacak kelime veya video URL'si (örn: "lofi hip hop" veya "https://youtu.be/...")
    
    Örnek komut: "Jarvis, YouTube'da şarkı aç" -> query = "şarkı"
    """
    params = parameters or {}
    query = params.get("query", "").strip()
    
    if not query:
        return "Patron, YouTube'da ne açmamı istediğinizi belirtmediniz."
    
    if player:
        player.write_log(f"SYS: 🎵 YouTube'da aranıyor: {query}")
    
    # Havalı bildirim penceresi (opsiyonel, sadece root varsa)
    if root:
        try:
            hud = tk.Toplevel(root)
            hud.overrideredirect(True)
            hud.attributes("-topmost", True, "-alpha", 0.92)
            hud.geometry("360x90+15+15")
            hud.configure(bg="#0a0a2a")
            tk.Label(hud, text="🎬 YOUTUBE BAĞLANTISI", font=("Orbitron", 11, "bold"), 
                     fg="#00ffcc", bg="#0a0a2a").pack(pady=5)
            tk.Label(hud, text=f"Aranıyor: {query[:35]}...", font=("Segoe UI", 9), 
                     fg="white", bg="#0a0a2a").pack()
            # Hafif bip sesi (sadece Windows'ta çalışır, hata vermez)
            try:
                import winsound
                winsound.Beep(800, 150)
            except:
                pass
            root.after(3000, hud.destroy)
        except Exception as e:
            if player:
                player.write_log(f"HUD hatası: {e}")
    
    # YouTube arama veya direkt URL açma
    try:
        if query.startswith(("http://", "https://")):
            url = query  # direkt link verilmiş
        else:
            # Özel karakterleri encode et
            encoded_query = urllib.parse.quote(query)
            url = f"https://www.youtube.com/results?search_query={encoded_query}"
        
        # Yeni sekmede aç (veya mevcut sekmeyi kullan)
        webbrowser.open_new_tab(url)
        
        if speak:
            speak(f"YouTube'da {query} aranıyor patron.")
        return f"YouTube'da '{query}' için arama sonuçları açılıyor patron."
    
    except Exception as e:
        hata_mesaji = f"YouTube bağlantısında sorun oluştu: {str(e)}"
        if player:
            player.write_log(f"ERR: {hata_mesaji}")
        return hata_mesaji