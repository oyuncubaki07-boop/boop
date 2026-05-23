def computer_control(parameters=None, player=None) -> str:
    params = parameters or {}
    action = params.get("action", "").lower()

    if player: player.write_log(f"SYS: ⌨️ Donanım Kontrolü -> {action}")

    try:
        import pyautogui
        # Fareyi köşeye götürürsen işlemi durdurma güvenlik kilidi:
        pyautogui.FAILSAFE = True 

        if action == "type":
            text = params.get("text", "")
            if text:
                pyautogui.write(text, interval=0.01)
                return "Metin klavye üzerinden yazıldı."
            return "Yazılacak metin boş."

        elif action == "hotkey":
            keys = params.get("keys", "").split("+")
            if keys:
                pyautogui.hotkey(*[k.strip().lower() for k in keys])
                return f"Şu kısayol tuşlandı: {params.get('keys')}"

        elif action == "click":
            pyautogui.click()
            return "Fare tıklaması yapıldı."

        elif action == "scroll":
            amount = params.get("amount", -500) # Negatif değer aşağıya kaydırır
            pyautogui.scroll(amount)
            return "Ekran kaydırıldı."

        elif action == "press":
            key = params.get("key", "")
            if key:
                pyautogui.press(key.lower())
                return f"{key} tuşuna basıldı."

        return "Geçersiz bilgisayar donanım komutu."
        
    except Exception as e:
        if player: player.write_log(f"SYS: Donanım kontrol hatası: {e}")
        return "Klavye/Fare otomasyonu sırasında bir hata oluştu veya kütüphane eksik."