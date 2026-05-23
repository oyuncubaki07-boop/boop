# actions/auto_pilot.py
# J.A.R.V.I.S. Oto Pilot Modülü
# Belirlenen saatlerde otomatik görevleri çalıştırır.

import time
import threading
import subprocess
import webbrowser
import schedule
from datetime import datetime
from pathlib import Path

# ================= YAPILANDIRMA =================
# Görevler listesi (her görev: (saat, fonksiyon, açıklama))
# Buraya istediğiniz görevleri ekleyebilirsiniz.
GOREVLER = [
    # Sabah görevleri
    ("08:00", "ac_chrome", "Sabah haberlere göz at"),
    ("08:30", "ac_spotify", "Sabah müziği başlat"),
    ("09:00", "sistem_temizligi", "Günlük sistem temizliği"),
    # Akşam görevleri
    ("18:00", "ac_youtube", "Akşam müzik/sohbet"),
    ("20:00", "gunluk_rapor", "Günlük sistem raporu"),
    ("23:00", "uyku_modu", "Uyku moduna geç"),
]

def ac_chrome():
    """Google Chrome açar."""
    try:
        subprocess.Popen(["start", "chrome"], shell=True)
        print(f"[OtoPilot] ✅ Chrome açıldı - {datetime.now()}")
        return "Chrome açıldı."
    except Exception as e:
        return f"Chrome açılamadı: {e}"

def ac_spotify():
    """Spotify açar."""
    try:
        subprocess.Popen(["start", "spotify"], shell=True)
        print(f"[OtoPilot] ✅ Spotify açıldı - {datetime.now()}")
        return "Spotify açıldı."
    except:
        return "Spotify açılamadı."

def ac_youtube():
    """YouTube ana sayfasını açar."""
    webbrowser.open("https://www.youtube.com")
    print(f"[OtoPilot] ✅ YouTube açıldı - {datetime.now()}")
    return "YouTube açıldı."

def sistem_temizligi():
    """Geçici dosyaları temizle (basit)."""
    try:
        import tempfile
        import shutil
        temp_dir = tempfile.gettempdir()
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"[OtoPilot] 🧹 Geçici dosyalar temizlendi - {datetime.now()}")
        return "Geçici dosyalar temizlendi."
    except Exception as e:
        return f"Temizlik hatası: {e}"

def gunluk_rapor():
    """Günlük sistem raporu oluşturur."""
    try:
        import psutil
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        rapor = f"📊 Günlük Rapor ({datetime.now().strftime('%d.%m.%Y')})\nCPU: %{cpu}\nRAM: %{ram}\nDisk: %{disk}"
        with open(Path.home() / "Desktop" / "jarvis_gunluk_rapor.txt", "w", encoding="utf-8") as f:
            f.write(rapor)
        print(f"[OtoPilot] 📄 Rapor oluşturuldu - {datetime.now()}")
        return rapor
    except:
        return "Rapor oluşturulamadı."

def uyku_modu():
    """Bilgisayarı uyku moduna alır."""
    try:
        subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0", "1", "0"], check=True)
        print(f"[OtoPilot] 💤 Uyku moduna geçiliyor - {datetime.now()}")
        return "Sistem uyku moduna geçiyor."
    except:
        return "Uyku modu başlatılamadı."

# ================= ZAMANLAYICI =================
_zamanlayici_thread = None

def _gorev_calistir(gorev_adi):
    """Verilen görev adına karşılık gelen fonksiyonu çalıştırır."""
    gorevler = {
        "ac_chrome": ac_chrome,
        "ac_spotify": ac_spotify,
        "ac_youtube": ac_youtube,
        "sistem_temizligi": sistem_temizligi,
        "gunluk_rapor": gunluk_rapor,
        "uyku_modu": uyku_modu,
    }
    func = gorevler.get(gorev_adi)
    if func:
        return func()
    else:
        return f"Bilinmeyen görev: {gorev_adi}"

def _zamanlayici_dongu():
    """Arka planda schedule'ı çalıştırır."""
    # Mevcut görevleri schedule'a ekle
    for saat, gorev_adi, aciklama in GOREVLER:
        getattr(schedule.every().day, "at")(saat).do(_gorev_calistir, gorev_adi)
        print(f"[OtoPilot] ⏰ Görev planlandı: {saat} - {aciklama}")
    
    while True:
        schedule.run_pending()
        time.sleep(30)

def oto_pilotu_baslat():
    """Oto pilotu arka planda başlatır."""
    global _zamanlayici_thread
    if _zamanlayici_thread and _zamanlayici_thread.is_alive():
        return "Oto pilot zaten çalışıyor."
    _zamanlayici_thread = threading.Thread(target=_zamanlayici_dongu, daemon=True)
    _zamanlayici_thread.start()
    return "Oto pilot başlatıldı. Planlanan görevler çalışacak."

def oto_pilotu_durdur():
    """Oto pilotu durdurur (program kapanana kadar bekler)."""
    # schedule kütüphanesinin durdurma metodu yok, programı kapatmak gerekir.
    return "Oto pilotu durdurmak için programı yeniden başlatın."

def hemen_calistir(gorev_adi):
    """Verilen görevi hemen çalıştırır (manuel tetikleme)."""
    return _gorev_calistir(gorev_adi)

# ================= JARVIS ACTION FONKSİYONU =================
def auto_pilot(parameters=None, player=None, speak=None, **kwargs):
    """
    Oto pilot modülü.
    Parametreler:
        action (str): "start" (planlı başlat), "run_now" (görevi hemen çalıştır), "stop"
        task (str): "run_now" ile birlikte hangi görevin hemen çalıştırılacağı (ac_chrome, ac_spotify, sistem_temizligi, gunluk_rapor, uyku_modu)
    """
    params = parameters or {}
    action = params.get("action", "start").lower()
    task = params.get("task", "").strip()
    
    if action == "start":
        if speak:
            speak("Oto pilot başlatılıyor. Planlanan görevler çalışacak.")
        return oto_pilotu_baslat()
    
    elif action == "run_now":
        if not task:
            return "Hangi görevi hemen çalıştırmamı istersiniz? Örnek: task='ac_chrome'"
        if speak:
            speak(f"{task} görevi hemen çalıştırılıyor.")
        return hemen_calistir(task)
    
    elif action == "stop":
        if speak:
            speak("Oto pilot durduruluyor.")
        return oto_pilotu_durdur()
    
    else:
        return f"Bilinmeyen aksiyon: {action}. Kullanılabilir: start, run_now, stop"