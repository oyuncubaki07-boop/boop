# actions/shadow_record.py
# J.A.R.V.I.S. Gölge Kayıt Modülü (Seri Ekran Görüntüsü)

import os
import time
import threading
import tkinter as tk
import winsound
from pathlib import Path
from datetime import datetime

def get_base_dir():
    return Path(__file__).resolve().parent.parent

def _record_sequence(player, root, count, interval, save_dir, compress, speak):
    try:
        import pyautogui
        from PIL import Image

        # Klasör yoksa oluştur
        save_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        files = []

        for i in range(count):
            # Tam ekran görüntüsü al
            img = pyautogui.screenshot()
            if compress:
                # Görüntüyü yarı boyuta küçült (hız ve alan kazancı)
                img = img.resize((img.width // 2, img.height // 2), Image.Resampling.LANCZOS)
            filename = save_dir / f"shadow_{timestamp}_{i+1:02d}.png"
            img.save(filename, optimize=True)
            files.append(filename)
            
            # Deklanşör sesi (her karede farklı frekans)
            try:
                winsound.Beep(800 + (i * 100), 80)
            except:
                pass
            
            if i < count - 1:
                time.sleep(interval)

        if player:
            player.write_log(f"SYS: 🎥 Gölge Kayıt tamamlandı. {count} görüntü kaydedildi.")

        # Sesli bildirim
        if speak:
            speak(f"{count} görüntü başarıyla kaydedildi, efendim.")

        # Başarı HUD'u
        if root:
            try:
                hud = tk.Toplevel(root)
                hud.overrideredirect(True)
                hud.attributes("-topmost", True, "-alpha", 0.92)
                hud.geometry("360x110+15+15")
                hud.configure(bg="#0a1a2a")
                
                tk.Label(hud, text="🎥 GÖLGE KAYIT TAMAM", font=("Orbitron", 10, "bold"),
                         fg="#00ccff", bg="#0a1a2a").pack(pady=5)
                tk.Label(hud, text=f"{count} görüntü kaydedildi", font=("Segoe UI", 9),
                         fg="white", bg="#0a1a2a").pack()
                tk.Label(hud, text=f"📁 {save_dir.name}", font=("Consolas", 8), 
                         fg="#aaaaaa", bg="#0a1a2a").pack()
                
                # Başarı sesi
                try:
                    winsound.Beep(600, 200)
                    winsound.Beep(800, 150)
                except:
                    pass
                
                root.after(4000, lambda: hud.destroy() if hud.winfo_exists() else None)
            except Exception as hud_e:
                if player:
                    player.write_log(f"HUD hatası: {hud_e}")

    except ImportError as e:
        error_msg = f"Gerekli kütüphane yok: {e}. 'pip install pyautogui pillow' ile kurun."
        if player:
            player.write_log(f"SYS: {error_msg}")
        if speak:
            speak(error_msg)
    except Exception as e:
        error_msg = f"Gölge Kayıt Hatası: {str(e)}"
        if player:
            player.write_log(f"SYS: {error_msg}")
        if speak:
            speak("Kayıt sırasında bir hata oluştu, efendim.")
        
        # Hata HUD'u
        if root:
            try:
                hud = tk.Toplevel(root)
                hud.overrideredirect(True)
                hud.attributes("-topmost", True, "-alpha", 0.9)
                hud.geometry("320x80+15+15")
                hud.configure(bg="#330000")
                tk.Label(hud, text="❌ KAYIT HATASI", font=("Orbitron", 10, "bold"),
                         fg="#ff6666", bg="#330000").pack(pady=5)
                tk.Label(hud, text=str(e)[:50], font=("Segoe UI", 8), 
                         fg="white", bg="#330000").pack()
                try:
                    winsound.Beep(300, 300)
                except:
                    pass
                root.after(3000, lambda: hud.destroy() if hud.winfo_exists() else None)
            except:
                pass

def shadow_record(parameters=None, player=None, root=None, speak=None) -> str:
    """
    Seri ekran görüntüsü alır (gölge kayıt).
    
    Parametreler:
        count (int): Kaç adet görüntü alınacağı (varsayılan: 3)
        interval (float): Görüntüler arası saniye (varsayılan: 1.0)
        compress (bool): Görüntüyü küçült (varsayılan: False)
        save_dir (str): Kayıt dizini (varsayılan: BASE_DIR/kayitlar)
    """
    params = parameters or {}
    count = int(params.get("count", 3))
    interval = float(params.get("interval", 1.0))
    compress = params.get("compress", False)
    custom_dir = params.get("save_dir", "")

    if count < 1:
        return "Patron, en az 1 görüntü almalıyım."
    if interval < 0.2:
        return "Aralık en az 0.2 saniye olabilir, efendim."

    # Kayıt dizini
    if custom_dir:
        save_dir = Path(custom_dir)
    else:
        save_dir = get_base_dir() / "kayitlar"

    if player:
        player.write_log(f"SYS: 🎥 Gölge Kayıt başlatılıyor... ({count} görüntü, {interval}s aralık)")

    # Başlangıç bip sesi
    try:
        winsound.Beep(400, 150)
    except:
        pass

    # Thread başlat
    threading.Thread(target=_record_sequence, 
                     args=(player, root, count, interval, save_dir, compress, speak), 
                     daemon=True).start()

    if speak:
        speak(f"{count} görüntü alınıyor, efendim. Kayıtlar tamamlandığında haber vereceğim.")

    # Anında HUD bildirimi (başlangıç)
    if root:
        try:
            hud = tk.Toplevel(root)
            hud.overrideredirect(True)
            hud.attributes("-topmost", True, "-alpha", 0.9)
            hud.geometry("320x80+15+15")
            hud.configure(bg="#0a2a2a")
            tk.Label(hud, text="🎥 GÖLGE KAYIT BAŞLADI", font=("Orbitron", 10, "bold"),
                     fg="#00ffcc", bg="#0a2a2a").pack(pady=5)
            tk.Label(hud, text=f"{count} görüntü, {interval}s aralık", font=("Segoe UI", 9),
                     fg="white", bg="#0a2a2a").pack()
            root.after(2000, lambda: hud.destroy() if hud.winfo_exists() else None)
        except:
            pass

    return f"🎥 Gölge kayıt protokolü başlatıldı. {count} adet ekran görüntüsü {interval} saniye aralıklarla alınacak. Dosyalar '{save_dir}' klasörüne kaydedilecek."