# actions/social_ghost.py
# J.A.R.V.I.S. Sosyal Medya Analiz ve Asistan Modülü

import pyautogui
import pyperclip
import time
import random
from typing import Optional

def social_ghost(parameters: Optional[dict] = None, player=None, speak=None) -> str:
    """
    WhatsApp veya herhangi bir mesajlaşma uygulamasında son mesajı alır,
    kullanıcının tarzına uygun bir cevap önerisi hazırlar.
    """
    if player:
        player.write_log("SYS: 🛡️ Sosyal Ghost modu aktif - mesaj analizi başlıyor...")

    # Koordinatlar opsiyonel olarak parametrelerden alınabilir
    params = parameters or {}
    click_x = params.get("click_x", 1000)
    click_y = params.get("click_y", 900)
    use_clipboard = params.get("use_clipboard", True)

    incoming_msg = ""

    try:
        # Önce panoya bak (eğer kullanıcı manuel kopyalamışsa)
        if use_clipboard:
            incoming_msg = pyperclip.paste().strip()

        # Eğer panoda yoksa, ekrandaki mesaj alanını dene (koordinat bazlı)
        if not incoming_msg and click_x and click_y:
            pyautogui.click(click_x, click_y)
            time.sleep(0.3)
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.5)
            incoming_msg = pyperclip.paste().strip()

        if not incoming_msg:
            return "Patron, okunacak bir mesaj bulamadım. Lütfen mesaj kutusunu seçip tekrar deneyin."

        # Kısa analiz (basit bir AI simülasyonu)
        if player:
            player.write_log(f"SOSYAL: Gelen mesaj -> {incoming_msg[:80]}...")

        # Cevap önerisi (şimdilik birkaç hazır şablon, ileride Gemini bağlanabilir)
        if "merhaba" in incoming_msg.lower() or "selam" in incoming_msg.lower():
            suggestion = "Selam! Naber? Uzun zamandır görüşemedik."
        elif "nasılsın" in incoming_msg.lower():
            suggestion = "İyiyim, teşekkür ederim. Sen nasılsın? Ne yapıyorsun?"
        elif "toplantı" in incoming_msg.lower() or "iş" in incoming_msg.lower():
            suggestion = "Şu an biraz yoğunum, en kısa sürede dönüş yapayım."
        else:
            suggestions = [
                "Anladım, teşekkür ederim. Detaylandırabilir misin?",
                "Harika, bunu not aldım. Peki sen ne düşünüyorsun?",
                "İlginç, biraz düşüneyim. Cevabı yakında yazarım.",
                "Eyvallah. Sana da selamlar."
            ]
            suggestion = random.choice(suggestions)

        if speak:
            speak(f"Patron, gelen mesaj şöyle: {incoming_msg}. Benim önerim: {suggestion}")

        return f"📩 Gelen mesaj: {incoming_msg}\n💡 Önerilen cevap: {suggestion}"

    except Exception as e:
        error_msg = f"Sosyal Ghost hatası: {str(e)}"
        if player:
            player.write_log(f"SYS: {error_msg}")
        return f"Mesaj analizi yapılamadı: {error_msg}"