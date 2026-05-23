# actions/whatsapp_call.py
import time
import csv
import webbrowser
import difflib
import re
from pathlib import Path
import pyautogui

CSV_PATH = Path(__file__).resolve().parent.parent / "config" / "contacts.csv"

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
            for name, phone in contacts:
                if contact_name.lower() == name.lower():
                    return name, phone
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

def _clean_phone(phone: str) -> str:
    """Telefon numarasını sadece rakam ve + olarak temizler."""
    cleaned = re.sub(r"[^\d+]", "", phone)
    if not cleaned.startswith("+") and len(cleaned) == 10:
        cleaned = "+90" + cleaned
    return cleaned

def whatsapp_call(parameters=None, player=None, speak=None, **kwargs):
    params = parameters or {}
    receiver = params.get("receiver", "").strip()
    call_type = params.get("call_type", "voice").lower()

    if not receiver:
        return "Kimi arayacağımı belirtin, efendim."

    if player:
        player.write_log(f"[WhatsApp Arama] {receiver} ({call_type})")

    # CSV'den kişiyi bul
    found_name, phone = _find_contact_from_csv(receiver)
    if phone:
        search_number = _clean_phone(phone)
        if speak:
            speak(f"{found_name} için WhatsApp açılıyor, lütfen bekleyin.")
    else:
        search_number = _clean_phone(receiver)
        if speak:
            speak(f"{search_number} numarası için WhatsApp açılıyor.")

    if not search_number:
        return "Geçerli bir telefon numarası bulunamadı."

    # Doğrudan arama yerine sohbeti açıyoruz
    url = f"whatsapp://send?phone={search_number}"

    try:
        webbrowser.open(url)
        
        # WhatsApp'ın açılması ve sohbetin ekrana gelmesi için bekleme süresi
        time.sleep(5) 
        
        # PENCEREYE ODAKLANMA: Klavye girdilerinin boşa gitmemesi için chat'e tıklar gibi yapıyoruz
        pyautogui.press('enter')
        time.sleep(0.5) 
        
        # ARAMA TETİKLEME: İnsan hızında (interval) ve güncel kısayollarla (Alt+Shift)
        if call_type == "video":
            # Görüntülü arama kısayolu
            pyautogui.hotkey('alt', 'shift', 'v', interval=0.1)
        else:
            # Sesli arama kısayolu
            pyautogui.hotkey('alt', 'shift', 'c', interval=0.1)

        if speak:
            speak(f"{call_type} arama başlatıldı, efendim.")
        return f"{call_type} arama başlatılıyor: {search_number}"
        
    except Exception as e:
        return f"Arama başlatılamadı: {e}"