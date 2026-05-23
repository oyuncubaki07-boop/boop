# actions/send_message.py
# WhatsApp Uygulaması ile mesaj gönderme - Tüm olasılıklar düşünülmüştür.

import time
import csv
import subprocess
import pyautogui
import difflib
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parent.parent / "config" / "contacts.csv"
WHATSAPP_AUMID = "5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App"  # Kendi AppUserModelId'niz ile değiştirin

def _find_contact_from_csv(contact_name: str) -> tuple:
    """CSV'de kişi adını arar. Tam eşleme yoksa en yakın eşleşmeyi döndürür."""
    if not CSV_PATH.exists():
        return None, None
    try:
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            contacts = []
            for row in reader:
                name = row.get('First Name', '').strip()
                if not name or name == '.':
                    name = row.get('Nickname', '').strip()
                if not name:
                    continue
                phone = row.get('Phone 1 - Value', '').strip()
                if not phone:
                    phone = row.get('Phone 2 - Value', '').strip()
                if phone:
                    contacts.append((name, phone))
            if not contacts:
                return None, None
            # Tam eşleme
            for name, phone in contacts:
                if contact_name.lower() == name.lower():
                    return name, phone
            # Yakın eşleme (difflib)
            names = [c[0] for c in contacts]
            matches = difflib.get_close_matches(contact_name.lower(), [n.lower() for n in names], n=1, cutoff=0.6)
            if matches:
                for name, phone in contacts:
                    if name.lower() == matches[0]:
                        return name, phone
            return None, None
    except Exception as e:
        print(f"[CSV] Hata: {e}")
        return None, None

def _is_whatsapp_running() -> bool:
    try:
        output = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq WhatsApp.exe'], capture_output=True, text=True)
        return "WhatsApp.exe" in output.stdout
    except:
        return False

def _open_whatsapp_app() -> bool:
    if _is_whatsapp_running():
        return True
    try:
        subprocess.Popen(["explorer", f"shell:AppsFolder\\{WHATSAPP_AUMID}"])
        time.sleep(5)  # Uygulamanın tam açılması için yeterli süre
        return True
    except Exception as e:
        print(f"[WhatsApp] Açma hatası: {e}")
        return False

def send_whatsapp_app(receiver: str, message: str, player=None, speak=None) -> str:
    """
    WhatsApp uygulamasında kişiyi bulur, mesajı yazar ve gönderir.
    Her adımda sesli geri bildirim verir.
    """
    # 1. CSV'den kişi ara
    found_name, phone = _find_contact_from_csv(receiver)
    search_text = phone if phone else receiver

    if found_name:
        log_msg = f"✅ Kişi bulundu: {found_name} → {phone}"
        if player: player.write_log(f"[CSV] {log_msg}")
        if speak: speak(log_msg)
    else:
        log_msg = f"⚠️ '{receiver}' tam eşleşmedi, '{search_text}' aranacak."
        if player: player.write_log(f"[CSV] {log_msg}")
        if speak: speak(log_msg)

    # 2. WhatsApp uygulamasını aç (gerekirse)
    if not _open_whatsapp_app():
        hata_msg = "WhatsApp uygulaması açılamadı. Lütfen manuel olarak açın."
        if speak: speak(hata_msg)
        return hata_msg

    time.sleep(1.5) # Uygulamanın öne gelmesi için kısa bir bekleme

    # 3. Arama kutusunu aç (Ctrl+F)
    pyautogui.hotkey('ctrl', 'f')
    time.sleep(0.5)
    
    # Kutudaki eski aramayı kesin olarak temizle
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.press('backspace')
    
    # Kişiyi yaz ve bulması için bekle
    pyautogui.write(search_text, interval=0.05)
    time.sleep(2.0) # Kişinin arama sonuçlarında çıkması için süre

    # 4. İlk sonucu seç (Enter)
    pyautogui.press('enter')
    time.sleep(1.5) # Sohbetin açılması ve imlecin GÖVDEYE (mesaj kutusuna) düşmesi için süre

    # 5. Mesaj kutusuna yazma
    # DİKKAT: Tab tuşları kaldırıldı. Sohbet açıldığında imleç zaten mesaj kutusundadır.
    # Sadece taslakta önceden kalmış bir metin varsa onu temizlemek için Ctrl+A yapıyoruz.
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.press('backspace')
    
    # Mesajı yaz
    pyautogui.write(message, interval=0.05)
    time.sleep(0.5)

    # 6. Gönder (Enter)
    pyautogui.press('enter')

    basari_msg = f"Mesajınız '{search_text}' kişisine gönderildi efendim."
    if speak: speak(basari_msg)
    return basari_msg

def send_message(parameters: dict, player=None, speak=None, **kwargs) -> str:
    params = parameters or {}
    receiver = params.get("receiver", "").strip()
    message = params.get("message_text", "").strip()
    platform = params.get("platform", "whatsapp").lower()

    if not receiver or not message:
        return "Lütfen alıcı ve mesaj belirtin."

    if player:
        player.write_log(f"[Mesaj] {platform} → {receiver}")

    if "whatsapp" in platform:
        # Önce sesli bildirim
        if speak:
            speak("Efendim, mesaj 3 saniye içinde gönderiliyor.")
        time.sleep(3)
        return send_whatsapp_app(receiver, message, player, speak)
    else:
        return f"{platform} desteği henüz eklenmedi (sadece WhatsApp uygulaması çalışır)."