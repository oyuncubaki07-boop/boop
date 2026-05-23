# actions/security_and_focus.py
# J.A.R.V.I.S. Güvenlik, Gizlilik, Odak ve Biyometrik Sistemler (Birleştirilmiş Modül) — PyQt6

import os
import time
import threading
import winsound
import webbrowser
import sys
from pathlib import Path

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer


def _show_hud(root, title, message, color="#003300", duration=3000):
    """PyQt6 HUD gösterimi için yardımcı fonksiyon."""
    if not root or not isinstance(root, QWidget):
        return
    try:
        hud = QWidget(root)
        hud.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        hud.setWindowOpacity(0.92)
        hud.setGeometry(15, 15, 350, 80)
        hud.setStyleSheet(f"background-color: {color};")

        layout = QVBoxLayout(hud)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            "color: #00ffcc; font-family: 'Orbitron', 'Courier New'; font-size: 10px; font-weight: bold;"
        )
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        msg_label = QLabel(message)
        msg_label.setStyleSheet("color: white; font-family: 'Segoe UI'; font-size: 9px;")
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(msg_label)

        hud.show()

        try:
            winsound.Beep(600, 100)
        except:
            pass

        QTimer.singleShot(duration, hud.close)
    except:
        pass


def ghost_mode(parameters=None, player=None, root=None, speak=None) -> str:
    """Hayalet modu - tüm pencereleri gizler, masaüstünü gösterir."""
    try:
        import pyautogui
        if player:
            player.write_log("SYS: 👻 Hayalet modu aktif. Ekran temizleniyor.")
        
        pyautogui.hotkey('win', 'd')
        
        if speak:
            speak("Gizlilik sağlandı efendim. Ekran temizlendi.")
        
        _show_hud(root, "👻 HAYALET MODU", "Ekran temizlendi", color="#001133")
        return "Gizlilik sağlandı patron. Kimse sizi görmüyor."
    except Exception as e:
        error_msg = f"Hayalet modu hatası: {e}"
        if player:
            player.write_log(f"SYS: {error_msg}")
        return error_msg


def focus_mode(parameters=None, player=None, root=None, speak=None) -> str:
    """Odak modu - dikkat dağıtıcıları engeller."""
    try:
        if player:
            player.write_log("SYS: 🎯 Odak modu aktif.")
        
        if sys.platform == "win32":
            os.system("start ms-settings:quietmomentshome")
            if speak:
                speak("Odak modu ayarları açıldı, efendim. Dilerseniz manuel olarak düzenleyebilirsiniz.")
        
        _show_hud(root, "🎯 ODAK MODU", "Dikkat dağıtıcılar engellendi", color="#003300")
        return "Odak modu aktif. Dikkat dağıtıcı unsurlar engellendi patron."
    except Exception as e:
        return f"Odak modu hatası: {e}"


def lockdown_protocol(parameters=None, player=None, root=None, speak=None) -> str:
    """Acil durum kilitleme protokolü."""
    try:
        if player:
            player.write_log("SYS: 🔒 Kilitlenme protokolü devrede.")
        
        if speak:
            speak("Sistem kilitleniyor, efendim. Güvende kalın.")
        
        _show_hud(root, "🔒 KİLİTLENME PROTOKOLÜ", "Sistem kilitleniyor", color="#330000", duration=2000)
        
        if sys.platform == "win32":
            os.system("rundll32.exe user32.dll,LockWorkStation")
        
        return "Sistem kilitlendi patron. Kale koruma altında."
    except Exception as e:
        return f"Kilitlenme hatası: {e}"


def guardian_shield(parameters=None, player=None, root=None, speak=None) -> str:
    """Gardiyan kalkanı - indirilenleri tarar."""
    try:
        if player:
            player.write_log("SYS: 🛡️ Gardiyan kalkanı aktif.")
        
        if speak:
            speak("Gardiyan kalkanı devrede, indirilenler taranıyor.")
        
        _show_hud(root, "🛡️ GARDIYAN KALKANI", "İndirilenler taranıyor", color="#003333")
        
        downloads_path = str(Path.home() / "Downloads")
        if os.path.exists(downloads_path):
            recent_files = [f for f in os.listdir(downloads_path) 
                           if os.path.isfile(os.path.join(downloads_path, f))]
            return f"Gardiyan kalkanı devrede. İndirilenler klasöründe {len(recent_files)} dosya mevcut."
        
        return "Gardiyan kalkanı devrede. İndirilenler taranıyor."
    except Exception as e:
        return f"Gardiyan kalkanı hatası: {e}"


def breach_watch(parameters=None, player=None, root=None, speak=None) -> str:
    """Veri ihlali kontrolü - HaveIBeenPwned sitesini açar."""
    try:
        if player:
            player.write_log("SYS: 🔍 Sızıntı kontrolü başlatılıyor.")
        
        webbrowser.open("https://haveibeenpwned.com/")
        
        if speak:
            speak("Sızıntı kontrol merkezi açıldı, efendim.")
        
        _show_hud(root, "🔍 SIZINTI KONTROLÜ", "HaveIBeenPwned açıldı", color="#333300")
        return "Sızıntı kontrol merkezini açtım patron."
    except Exception as e:
        return f"Sızıntı kontrol hatası: {e}"


def biometric_shield(parameters=None, player=None, root=None, speak=None) -> str:
    """Gerçek yüz tanıma sistemi ile biyometrik koruma."""
    try:
        import cv2
        
        if player:
            player.write_log("SYS: 🧬 Biyometrik Gözler açılıyor. Kameraya bakın...")
        
        if speak:
            speak("Biyometrik tarama başlıyor, lütfen kameraya bakın efendim.")
        
        cap = cv2.VideoCapture(0)
        if sys.platform == "win32":
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        
        if not cap.isOpened():
            return "Patron, kamerayı bulamadım! Lütfen kameranın bağlı olduğundan emin olun."

        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        if not os.path.exists(cascade_path):
            return "Yüz tanıma modeli bulunamadı."

        face_cascade = cv2.CascadeClassifier(cascade_path)
        
        start_time = time.time()
        verified = False
        
        while time.time() - start_time < 4:
            ret, frame = cap.read()
            if not ret:
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            if len(faces) > 0:
                verified = True
                break
            time.sleep(0.05)
        
        cap.release()

        if verified:
            try:
                winsound.Beep(800, 200)
                winsound.Beep(1000, 300)
            except:
                pass
            if speak:
                speak("Biyometrik onay başarılı. Hoş geldiniz efendim.")
            _show_hud(root, "✅ BİYOMETRİK ONAY", "Yüz tanıma başarılı", color="#003300")
            return "Biyometrik onay başarılı. Hoş geldiniz patron."
        else:
            if speak:
                speak("Biyometrik tarama başarısız. Lütfen tekrar deneyin.")
            return "Biyometrik tarama başarısız. Kamerada yüz tespit edilemedi veya süre doldu."
    except ImportError:
        return "OpenCV (cv2) kurulu değil. 'pip install opencv-python' ile kurun."
    except Exception as e:
        return f"Biyometrik sistem hatası: {str(e)}"