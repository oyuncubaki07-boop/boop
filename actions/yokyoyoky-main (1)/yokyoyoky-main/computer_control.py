def computer_control(parameters=None, player=None) -> str:
    params = parameters or {}
    action = params.get("action", "").lower()

    if player: 
        player.write_log(f"SYS: ⌨️ Donanım Kontrolü -> {action}")

    try:
        import pyautogui
        
        # Güvenlik Kilidi: Fareyi ekranın bir köşesine (0,0) götürürsen işlemi anında durdurur.
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
                # Tuş kombinasyonlarını (örn: ctrl+c) boşluklardan temizleyip çalıştırır
                pyautogui.hotkey(*[k.strip().lower() for k in keys])
                return f"Şu kısayol tuşlandı: {params.get('keys')}"
            return "Kısayol tuşu belirtilmemiş."

        elif action == "click":
            pyautogui.click()
            return "Fare tıklaması yapıldı."

        elif action == "scroll":
            # Varsayılan değer -500 (Aşağıya kaydırır)
            amount = params.get("amount", -500) 
            pyautogui.scroll(int(amount))
            return f"Ekran {amount} birim kaydırıldı."

        elif action == "press":
            key = params.get("key", "")
            if key:
                pyautogui.press(key.lower())
                return f"'{key}' tuşuna basıldı."
            return "Basılacak tuş belirtilmemiş."

        else:
            return f"Geçersiz bilgisayar donanım komutu: '{action}'."
        
    except ImportError:
        if player: player.write_log("SYS: 'pyautogui' kütüphanesi eksik!")
        return "Sistemi kontrol edebilmem için 'pyautogui' modülünün yüklü olması gerekiyor."
    except pyautogui.FailSafeException:
        if player: player.write_log("SYS: FAILSAFE TETİKLENDİ! İşlem iptal edildi.")
        return "Kullanıcı fareyi köşeye çekerek işlemi acil olarak durdurdu."
    except Exception as e:
        if player: player.write_log(f"SYS: Donanım kontrol hatası: {e}")
        return f"Klavye/Fare otomasyonu sırasında bir hata oluştu: {e}"