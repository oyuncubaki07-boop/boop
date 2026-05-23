# actions/screen_processor.py
# J.A.R.V.I.S. Ekran İşleme Modülü (OCR + Görsel Analiz)

import os
import tkinter as tk
import winsound
import tempfile
import json
from pathlib import Path

def get_base_dir():
    return Path(__file__).resolve().parent.parent

def _get_api_key():
    config_path = get_base_dir() / "config" / "api_keys.json"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("gemini_api_key", "").strip()
    except:
        return ""

def _show_hud(root, title, message, color="#1a1a00"):
    if not root:
        return
    try:
        hud = tk.Toplevel(root)
        hud.overrideredirect(True)
        hud.attributes("-topmost", True, "-alpha", 0.92)
        hud.geometry("360x90+15+15")
        hud.configure(bg=color)
        tk.Label(hud, text=title, font=("Orbitron", 10, "bold"),
                 fg="#ffff00" if color == "#1a1a00" else "#ff6666", bg=color).pack(pady=5)
        tk.Label(hud, text=message, font=("Segoe UI", 9),
                 fg="white", bg=color, wraplength=340).pack()
        try:
            winsound.Beep(500, 100)
        except:
            pass
        root.after(3000, lambda: hud.destroy() if hud.winfo_exists() else None)
    except:
        pass

def screen_process(parameters=None, player=None, root=None, speak=None) -> str:
    """
    Ekran görüntüsü alır, Gemini ile analiz yapar.
    
    Parametreler:
        prompt (str): Analiz için özel soru (varsayılan: "Ekranda ne görüyorsun? Kısa ve net özetle.")
        save_image (bool): Görüntüyü kaydet (varsayılan: False)
    """
    params = parameters or {}
    prompt = params.get("prompt", "Ekranda ne görüyorsun? Kısa ve net özetle.")
    save_image = params.get("save_image", False)
    
    try:
        import pyautogui
        from google import genai
        from google.genai import types
        
        if player:
            player.write_log("SYS: 👁️ Ekran analizi başlatılıyor...")
        
        _show_hud(root, "👁️ GÖRSEL ANALİZ", "Ekran inceleniyor...", "#1a1a00")
        
        # Geçici dosya
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            temp_path = tmp.name
        
        # Ekran görüntüsü al
        screenshot = pyautogui.screenshot()
        screenshot.save(temp_path)
        
        # İsteğe bağlı kalıcı kayıt
        if save_image and player:
            save_dir = get_base_dir() / "screen_captures"
            save_dir.mkdir(exist_ok=True)
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            perm_path = save_dir / f"screen_{timestamp}.png"
            screenshot.save(perm_path)
            player.write_log(f"SYS: Ekran görüntüsü kaydedildi: {perm_path}")
        
        # Gemini analizi
        api_key = _get_api_key()
        if not api_key:
            return "API anahtarı bulunamadı. Lütfen config/api_keys.json dosyasını kontrol edin."
        
        client = genai.Client(api_key=api_key)
        with open(temp_path, "rb") as f:
            image_data = f.read()
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                prompt,
                types.Part.from_bytes(data=image_data, mime_type="image/png")
            ]
        )
        
        result = response.text.strip()
        if not result:
            result = "Analiz sonucu boş."
        
        # Sesli çıktı
        if speak:
            speak(result[:200])  # Uzun mesajı kısalt
        
        # Başarı HUD'u
        _show_hud(root, "✅ ANALİZ TAMAM", "Sonuç hazır", "#0a2a0a")
        
        return f"👁️ Ekran analizi sonucu:\n\n{result}"
    
    except ImportError as e:
        return f"Gerekli kütüphane yok: {e}. 'pip install pyautogui google-generativeai' ile kurun."
    except Exception as e:
        error_msg = f"Ekran işleme hatası: {str(e)}"
        if player:
            player.write_log(f"SYS: {error_msg}")
        _show_hud(root, "❌ ANALİZ HATASI", error_msg[:50], "#2a0a0a")
        return error_msg
    finally:
        # Geçici dosyayı temizle
        if 'temp_path' in locals() and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass