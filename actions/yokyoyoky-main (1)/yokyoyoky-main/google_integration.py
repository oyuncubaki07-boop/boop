# actions/google_integration.py
import csv
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parent.parent / "config" / "contacts.csv"

def google_contacts(parameters=None, player=None, speak=None):
    if not CSV_PATH.exists():
        return f"Kişi dosyası bulunamadı: {CSV_PATH}"
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
                    contacts.append(f"{name} → {phone}")
            if not contacts:
                return "CSV'de kayıtlı kişi bulunamadı."
            result = "📞 Yerel Kişi Rehberiniz:\n" + "\n".join(contacts[:50])
            if len(contacts) > 50:
                result += f"\n... ve {len(contacts)-50} kişi daha."
            return result
    except Exception as e:
        return f"CSV okuma hatası: {e}"

# Diğer Google servisleri placeholder
def google_drive(*args, **kwargs):
    return "Google Drive geçici olarak devre dışı."

def google_youtube(*args, **kwargs):
    return "YouTube yükleme geçici olarak devre dışı."

def google_gmail(*args, **kwargs):
    return "Gmail gönderme geçici olarak devre dışı."