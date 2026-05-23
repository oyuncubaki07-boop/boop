# actions/smart_translator.py
# J.A.R.V.I.S. Evrensel Çevirmen (deep-translator ile)

import tkinter as tk
import winsound
from deep_translator import GoogleTranslator

def smart_translator(parameters=None, player=None, root=None, speak=None) -> str:
    params = parameters or {}
    target_lang = params.get("language", "İngilizce").strip()
    text_to_translate = params.get("text", "").strip()
    source_lang = params.get("source_lang", "auto")
    show_hud = params.get("show_hud", True)

    # Dil kodları (Türkçe isim -> ISO)
    lang_map = {
        "ingilizce": "en", "english": "en",
        "türkçe": "tr", "turkish": "tr",
        "almanca": "de", "german": "de",
        "fransızca": "fr", "french": "fr",
        "ispanyolca": "es", "spanish": "es",
        "italyanca": "it", "italian": "it",
        "rusça": "ru", "russian": "ru",
        "çince": "zh-cn", "chinese": "zh-cn",
        "japonca": "ja", "japanese": "ja",
        "arapça": "ar", "arabic": "ar",
        "portekizce": "pt", "portuguese": "pt",
        "hollandaca": "nl", "dutch": "nl",
        "korece": "ko", "korean": "ko"
    }
    target_code = lang_map.get(target_lang.lower(), target_lang.lower())

    if player:
        player.write_log(f"SYS: 🌍 Çevirmen -> {target_lang} ({target_code})")

    # HUD gösterimi
    if show_hud and root:
        try:
            hud = tk.Toplevel(root)
            hud.overrideredirect(True)
            hud.attributes("-topmost", True, "-alpha", 0.92)
            hud.geometry("320x85+15+15")
            hud.configure(bg="#0a0a2a")
            tk.Label(hud, text="🌍 EVRENSEL ÇEVİRMEN", font=("Orbitron", 10, "bold"),
                     fg="#00ffcc", bg="#0a0a2a").pack(pady=5)
            tk.Label(hud, text=f"Hedef: {target_lang.upper()}", font=("Segoe UI", 9),
                     fg="white", bg="#0a0a2a").pack()
            tk.Label(hud, text="Çeviri bekleniyor...", font=("Segoe UI", 8),
                     fg="#aaaaaa", bg="#0a0a2a").pack()
            try:
                winsound.Beep(600, 100)
                winsound.Beep(800, 100)
            except:
                pass
            root.after(3000, hud.destroy)
        except:
            pass

    # Metin verilmişse hemen çevir
    if text_to_translate:
        try:
            translator = GoogleTranslator(source='auto', target=target_code)
            translated = translator.translate(text_to_translate)
            if speak:
                speak(f"Çeviri: {translated}")
            return f"📝 Çeviri ({source_lang} → {target_lang}):\nOrijinal: {text_to_translate}\nÇeviri: {translated}"
        except Exception as e:
            return f"Çeviri hatası: {e}. İnternet bağlantınızı kontrol edin."

    return f"Evrensel çevirmen hazır, patron. {target_lang} diline çeviri yapabilirim. Çevirmemi istediğiniz metni söyleyin."