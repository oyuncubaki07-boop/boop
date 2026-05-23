# actions/send_message.py
import time
import csv
import subprocess
import os
import platform
import difflib
import urllib.parse
import webbrowser
from pathlib import Path

# Cross-platform kontrolü
_OS = platform.system()

CSV_PATH = Path(__file__).resolve().parent.parent / "config" / "contacts.csv"
WHATSAPP_AUMID = "5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App"  # Windows UWP AppUserModelId

def _find_contact_from_csv(contact_name: str) -> tuple:
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
                
            # Birebir eşleşme
            for name, phone in contacts:
                if contact_name.lower() == name.lower():
                    return name, phone
                    
            # Yakın eşleşme (Fuzzy Matching)
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

def _open_whatsapp_gui():
    """Numara bulunamadığında veya isimle arama yapılacağında GUI açılışı."""
    try:
        if _OS == "Windows":
            subprocess.Popen(["explorer", f"shell:AppsFolder\\{WHATSAPP_AUMID}"])
        elif _OS == "Darwin":
            subprocess.run(["open", "-a", "WhatsApp"])
        else:
            subprocess.run(["xdg-open", "whatsapp://"])
        time.sleep(3)
        return True
    except Exception as e:
        print(f"[WhatsApp] GUI Açma hatası: {e}")
        return False

def send_message(parameters=None, player=None, speak=None, **kwargs) -> str:
    """
    WhatsApp mesaj gönderir veya arama başlatır.
    Parametreler:
        receiver (str): Kişi adı veya telefon numarası
        message_text (str): Mesaj içeriği (opsiyonel, arama için boş bırakın)
        call_type (str): "voice" veya "video" (arama başlatmak için)
    """
    params = parameters or {}
    receiver = params.get("receiver", "").strip()
    message = params.get("message_text", "").strip()
    call_type = params.get("call_type", "").lower()

    if not receiver:
        return "Lütfen kime mesaj göndereceğimi belirtin patron."

    try:
        import pyautogui
        pyautogui.FAILSAFE = True
    except ImportError:
        return "Gerekli kütüphane eksik. 'pip install pyautogui' komutunu çalıştırın."

    # CSV'den kişi bul
    found_name, phone = _find_contact_from_csv(receiver)
    
    if found_name and phone:
        log_msg = f"Kişi rehberde bulundu: {found_name} -> {phone}"
        search_text = phone
    else:
        log_msg = f"'{receiver}' rehberde tam eşleşmedi, arama çubuğunda manuel aranacak."
        search_text = receiver

    if player:
        player.write_log(f"SYS: 💬 [WhatsApp] {log_msg}")

    # EĞER TELEFON NUMARASI VARSA DERİN BAĞLANTI (DEEP LINK) KULLAN (ÇOK DAHA HIZLI VE GÜVENİLİR)
    if phone:
        # Numaradaki boşlukları temizle
        safe_phone = "".join(c for c in phone if c.isdigit() or c == '+')
        safe_msg = urllib.parse.quote(message) if message else ""
        link = f"whatsapp://send?phone={safe_phone}&text={safe_msg}"
        
        webbrowser.open(link)
        time.sleep(3.5) # WhatsApp'ın açılıp sohbeti odaklaması için bekle
        
        if message and not call_type:
            pyautogui.press('enter')
            if speak: speak(f"{found_name} kişisine mesaj iletildi patron.")
            return f"Mesaj başarıyla gönderildi: {message}"
            
    else:
        # NUMARA YOKSA ESKİ USUL GUI OTOMASYONU KULLAN
        if not _open_whatsapp_gui():
            return "WhatsApp uygulamasına ulaşılamadı."

        time.sleep(2)
        pyautogui.hotkey('ctrl', 'f')
        time.sleep(0.5)
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.write(search_text, interval=0.05)
        time.sleep(1.5)
        pyautogui.press('enter')
        time.sleep(1.5)

        if message and not call_type:
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.write(message, interval=0.05)
            time.sleep(0.5)
            pyautogui.press('enter')
            if speak: speak(f"{receiver} kişisine mesaj iletildi patron.")
            return f"Mesaj başarıyla gönderildi: {message}"

    # ARAMA (VOICE / VIDEO) İŞLEMLERİ
    if call_type in ("voice", "video"):
        if call_type == "voice":
            pyautogui.hotkey('ctrl', 'e')      # Sesli arama kısayolu
            result = f"{found_name or receiver} ile sesli arama başlatılıyor."
        else:
            pyautogui.hotkey('ctrl', 'shift', 'e')  # Görüntülü arama kısayolu
            result = f"{found_name or receiver} ile görüntülü arama başlatılıyor."
            
        if speak: speak(result)
        return result

    if not message and not call_type:
        return f"{found_name or receiver} için sohbet penceresi açıldı."