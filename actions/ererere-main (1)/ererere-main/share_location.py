# actions/share_location.py
# J.A.R.V.I.S. Konum Paylaşım Modülü

import time
import urllib.parse
import webbrowser
import sys
from pathlib import Path

try:
    import pyautogui
    import pyperclip
except ImportError:
    print("[UYARI] pyautogui veya pyperclip kurulu değil. Bazı özellikler çalışmayabilir.")

# Önceki modüldeki JarvisActionProtocol'ü import et (eğer varsa)
try:
    from actions.action_protocol import JarvisActionProtocol
    PROTOCOL_AVAILABLE = True
except ImportError:
    PROTOCOL_AVAILABLE = False
    class JarvisActionProtocol:
        def __init__(self, player=None):
            self.player = player
        def log(self, msg):
            if self.player:
                self.player.write_log(msg)
        def ensure_app_running(self, app, warmup_seconds=1.0):
            # Basit bir uygulama başlatma (WhatsApp Web için zaten gerekmez)
            pass
        def execute_with_fallback(self, name, primary, success_message, failure_message):
            try:
                result = primary()
                return result
            except Exception as e:
                if self.player:
                    self.player.write_log(f"{name} hatası: {e}")
                return failure_message

def get_location_manually(address: str) -> str:
    """Verilen adres için Google Maps linki oluşturur."""
    encoded = urllib.parse.quote(address)
    return f"https://www.google.com/maps/search/?api=1&query={encoded}"

def share_location(parameters=None, player=None, root=None, speak=None) -> str:
    """
    Konum paylaşır.
    
    Parametreler:
        contact_name (str): Alıcının adı (WhatsApp'ta kişi adı)
        address (str): Paylaşılacak adres (varsayılan: "Konya Karatay")
        method (str): "whatsapp" veya "link" (varsayılan: "whatsapp")
        auto_send (bool): Otomatik gönder (WhatsApp için)
    """
    params = parameters or {}
    contact_name = params.get("contact_name", "Aslan oğlum")
    address = params.get("address", "Konya Karatay")
    method = params.get("method", "whatsapp").lower()
    auto_send = params.get("auto_send", True)

    if player:
        player.write_log(f"SYS: 📍 Konum paylaşımı başlatıldı -> {contact_name}")

    # Google Maps linki oluştur
    maps_link = get_location_manually(address)
    message = (
        "📍 J.A.R.V.I.S. Konum Paylaşımı\n\n"
        f"Adres: {address}\n"
        f"Harita: {maps_link}\n\n"
        "Bu mesaj J.A.R.V.I.S. tarafından otomatik gönderilmiştir."
    )

    # 1. Yöntem: Sadece linki panoya kopyala ve tarayıcıda aç
    if method == "link":
        pyperclip.copy(maps_link)
        webbrowser.open(maps_link)
        if speak:
            speak(f"Konum linki panoya kopyalandı ve tarayıcıda açıldı, efendim. {contact_name} kişisine manuel olarak iletebilirsiniz.")
        return f"📍 Konum linki oluşturuldu ve panoya kopyalandı.\nAdres: {address}\nLink: {maps_link}"

    # 2. Yöntem: WhatsApp üzerinden gönder (eski yöntem, protocol kullanarak)
    protocol = JarvisActionProtocol(player=player)

    def primary_whatsapp():
        protocol.log(f"WhatsApp üzerinden {contact_name} hedefine konum iletiliyor...")
        # WhatsApp Web aç
        webbrowser.open("https://web.whatsapp.com")
        time.sleep(3)  # Sayfanın yüklenmesi için
        # Kişiyi bul
        pyautogui.hotkey("ctrl", "f")
        time.sleep(0.3)
        pyperclip.copy(contact_name)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.5)
        pyautogui.press("down")
        pyautogui.press("enter")
        time.sleep(0.5)
        # Mesajı yapıştır
        pyperclip.copy(message)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.5)
        if auto_send:
            pyautogui.press("enter")
        # WhatsApp'ı küçült
        pyautogui.hotkey("win", "down")
        return f"Ana üs koordinatları {contact_name} kişisine WhatsApp üzerinden {'gönderildi' if auto_send else 'hazırlandı'}."

    if PROTOCOL_AVAILABLE:
        return protocol.execute_with_fallback(
            "Konum paylaşımı",
            primary=primary_whatsapp,
            success_message=f"Konum iletimi tamamlandı: {contact_name}",
            failure_message="Konum gönderilirken WhatsApp protokolünde bir sorun oluştu.",
        )
    else:
        # Protocol modülü yoksa doğrudan dene
        try:
            result = primary_whatsapp()
            if speak:
                speak(result)
            return result
        except Exception as e:
            error_msg = f"Konum paylaşılamadı: {e}"
            if player:
                player.write_log(error_msg)
            return error_msg