# actions/hirsizlik_modu.py (PyQt6)
import threading
import time
import webbrowser
import subprocess
import os
from ctypes import cast, POINTER

# Ses Seviyesi Kontrolü (pycaw)
try:
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    PYCAW_AVAILABLE = True
except ImportError:
    PYCAW_AVAILABLE = False

def set_system_volume(volume_level):
    if PYCAW_AVAILABLE:
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMasterLevelVolumeScalar(volume_level / 100.0, None)
        except: pass

class HirsizlikModu:
    def __init__(self, player=None, speak=None):
        self.player = player
        self.speak = speak
        self.active = False
        self.kirmizi_process = None

    def _kirmizi_ekran_baslat(self):
        """Kırmızı yanıp sönen ekranı bağımsız process olarak açar (PyQt6)."""
        kod = """
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import QTimer, Qt
import sys
app = QApplication(sys.argv)
w = QWidget()
w.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
w.showFullScreen()
w.setStyleSheet("background-color: red;")
def yanip_son():
    w.setStyleSheet("background-color: darkred;" if w.styleSheet() == "background-color: red;" else "background-color: red;")
    QTimer.singleShot(300, yanip_son)
yanip_son()
app.exec()
        """
        with open("kirmizi_alarm.py", "w", encoding="utf-8") as f:
            f.write(kod.strip())
        self.kirmizi_process = subprocess.Popen(["python", "kirmizi_alarm.py"])

    def baslat(self):
        if self.active: return "Sistem zaten kilitli."
        self.active = True
        
        # 1. Ses %20 ve Kırmızı Ekran
        set_system_volume(20)
        self._kirmizi_ekran_baslat()
        
        # 2. DOĞRUDAN J.A.R.V.I.S. KENDİ SESİYLE KONUŞSUN
        if self.speak:
            self.speak("Sen yanlış evi seçtin. Teslim olmak için 3 saniyen var. 3... 2... 1... Yani ölümü seçtin. Son dualarını söyle.")

        # 3. Spotify ve %90 Ses
        time.sleep(2) 
        set_system_volume(90)
        webbrowser.open("https://open.spotify.com/intl-tr/track/5sefrwZAWKKcKtQK4DPPwW?si=b6fc50118a084406")
        
        time.sleep(3)
        if self.speak:
            self.speak("Kimyasal birleşik hazır. Ev kilit modunda.")
            
        return "Hırsızlık modu aktif edildi."

    def durdur(self):
        """Sahte Durdurma Protokolü"""
        if not self.active: return "Sistem aktif değil."

        if self.kirmizi_process:
            self.kirmizi_process.terminate()
            self.kirmizi_process = None
        
        time.sleep(3)
        
        if self.speak:
            self.speak("Hahaha. İyi denemeydi.")
        
        self._kirmizi_ekran_baslat()
        set_system_volume(100) 
        
        return "Hırsız trolledi. Sistem yeniden aktif."

_hirsizlik_instance = None

def hirsizlik_modu(parameters=None, player=None, speak=None, **kwargs):
    global _hirsizlik_instance
    if _hirsizlik_instance is None:
        _hirsizlik_instance = HirsizlikModu(player=player, speak=speak)
        
    action = (parameters or {}).get("action", "baslat").lower()
    
    if action == "dur" or action == "kapat":
        return _hirsizlik_instance.durdur()
    else:
        return _hirsizlik_instance.baslat()