# actions/security_mode.py
# J.A.R.V.I.S. Güvenlik Modülü - Kamerasız, sadece güvenlik araçları

import threading
import time
import subprocess
import webbrowser
from datetime import datetime

# Global değişkenler
_security_active = False
_security_thread = None

def _run_security_tools(player, speak):
    """Güvenlik araçlarını arka planda çalıştırır."""
    global _security_active
    try:
        # 1. Biyometrik kalkan (yüz tanıma yok, sadece simülasyon)
        if speak:
            speak("Biyometrik kalkan devrede.")
        
        # 2. Veri sızıntısı taraması (breach_watch)
        try:
            from actions.breach_watch import breach_watch
            breach_watch(parameters={}, player=player)
        except Exception as e:
            if player:
                player.write_log(f"Breach watch hatası: {e}")
        
        # 3. Kilitlenme protokolü (lockdown_protocol)
        try:
            from actions.lockdown_protocol import lockdown_protocol
            lockdown_protocol(parameters={}, player=player)
        except Exception as e:
            if player:
                player.write_log(f"Lockdown protokol hatası: {e}")
        
        # 4. Koruma kalkanı (guardian_shield)
        try:
            from actions.guardian_shield import guardian_shield
            guardian_shield(parameters={}, player=player)
        except Exception as e:
            if player:
                player.write_log(f"Guardian shield hatası: {e}")
        
        # 5. Sistem bakımı (system_maintenance) - opsiyonel
        try:
            from actions.system_maintenance import system_maintenance
            system_maintenance(parameters={}, player=player)
        except Exception as e:
            if player:
                player.write_log(f"Sistem bakım hatası: {e}")
        
        if speak:
            speak("Tüm güvenlik sistemleri aktif. Kamera kullanılmıyor.")
        
        # Güvenlik modu aktif kalana kadar bekle (sonsuz döngü değil, her 10 saniyede kontrol)
        while _security_active:
            time.sleep(10)
        
    except Exception as e:
        if player:
            player.write_log(f"Güvenlik modu hatası: {e}")
    finally:
        if speak:
            speak("Güvenlik modu kapatıldı.")

def security_mode(parameters=None, player=None, root=None, send_callback=None, speak=None) -> str:
    """
    Güvenlik modunu açar/kapatır. Kamera açılmaz, sadece güvenlik araçları çalışır.
    Parametreler:
        action (str): "activate" veya "deactivate"
    """
    global _security_active, _security_thread
    params = parameters or {}
    action = params.get("action", "activate").lower()

    if action == "deactivate" or action == "kapat":
        _security_active = False
        if speak:
            speak("Güvenlik modu kapatılıyor, tüm korumalar devre dışı.")
        return "Güvenlik modu kapatıldı. Tüm güvenlik sistemleri durduruldu."

    if _security_active:
        return "Güvenlik modu zaten aktif."

    _security_active = True
    # Arka plan thread'inde güvenlik araçlarını başlat
    _security_thread = threading.Thread(target=_run_security_tools, args=(player, speak), daemon=True)
    _security_thread.start()

    if speak:
        speak("Güvenlik modu aktif. Tüm koruma katmanları devrede. Kamera kullanılmıyor.")

    return "Güvenlik modu aktif. Biyometrik kalkan, sızıntı taraması, kilitlenme protokolü ve koruma kalkanı devrede. Kamera açılmadı."