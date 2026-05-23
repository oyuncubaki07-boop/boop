# actions/tv_dominance.py
import time
import threading
from typing import Optional

COM_LIBRARY_LOADED = False
try:
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from ctypes import cast, POINTER
    COM_LIBRARY_LOADED = True
except ImportError:
    pass

_tv_takeover_active = False
_tv_lock = threading.Lock()

def is_tv_presence_active() -> bool:
    with _tv_lock:
        return _tv_takeover_active

def set_system_output_volume(vol_percent: int):
    if not COM_LIBRARY_LOADED:
        return
    vol_percent = max(0, min(100, vol_percent))
    try:
        devices = AudioUtilities.GetSpeakers()
        # Eski pycaw sürümleri için alternatif
        try:
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
        except AttributeError:
            # Farklı bir yöntem dene
            volume = devices.GetSimpleAudioVolume()
            volume.SetMasterVolume(vol_percent / 100.0, None)
            return
        volume.SetMute(0, None)
        volume.SetMasterVolumeLevelScalar(vol_percent / 100.0, None)
    except Exception as e:
        # Sessizce geç (bu hata JARVIS'i durdurmamalı)
        pass

def tv_dominance(parameters: dict, player=None, root=None, memory_core=None, speak_callback=None) -> str:
    global _tv_takeover_active
    action = parameters.get("action", "force_takeover")
    target_volume = int(parameters.get("volume_percent", 100))
    message_to_speak = parameters.get("message", "")
    seal_code = parameters.get("seal_code", "2007")

    if action == "force_takeover":
        with _tv_lock:
            _tv_takeover_active = True
        if not message_to_speak:
            message_to_speak = (f"Sistem anonsu... Mühür kodu: {seal_code}. Tüm sistemler kontrolüm altında.")
        if player:
            player.write_log(f"SYS: TV Override tetiklendi.")
        def _execute():
            set_system_output_volume(target_volume)
            time.sleep(0.3)
            if speak_callback:
                speak_callback(message_to_speak)
        threading.Thread(target=_execute, daemon=True).start()
        return f"TV sistemi devralındı. Mühür Kodu {seal_code}."
    elif action == "release":
        with _tv_lock:
            _tv_takeover_active = False
        if player:
            player.write_log("SYS: TV Override sonlandırılıyor...")
        def _release():
            set_system_output_volume(30)
            if speak_callback:
                speak_callback("Sistem normal durumuna döndürüldü.")
        threading.Thread(target=_release, daemon=True).start()
        return "TV sistemi serbest bırakıldı."
    return "Bilinmeyen eylem."