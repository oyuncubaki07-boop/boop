# actions/biometric_shield.py
# J.A.R.V.I.S. Biyometrik Kalkan - OpenCV Cascade ile Basit Yüz Tanıma

import tkinter as tk
import cv2
import threading
import time
import winsound
from pathlib import Path
from datetime import datetime
from typing import Optional

class BiometricShield:
    def __init__(self, player=None, root=None):
        self.player = player
        self.root = root
        self.is_active = False
        self.camera = None
        self.scan_thread = None
        self.face_cascade = None
        self._load_cascade()

    def _log(self, msg):
        if self.player and hasattr(self.player, "write_log"):
            self.player.write_log(f"🛡️ {msg}")
        else:
            print(f"[BIOMETRIC] {msg}")

    def _beep(self, freq, duration=150):
        try:
            winsound.Beep(freq, duration)
        except:
            pass

    def _play_success_sound(self):
        for freq in [880, 1046, 1318]:
            self._beep(freq, 100)
            time.sleep(0.05)

    def _play_fail_sound(self):
        self._beep(440, 300)
        self._beep(330, 200)

    def _show_hud(self, title, message, color="#00ffcc", bg="#000033"):
        if not self.root:
            return
        try:
            hud = tk.Toplevel(self.root)
            hud.overrideredirect(True)
            hud.attributes("-topmost", True, "-alpha", 0.92)
            hud.geometry("380x110+15+15")
            hud.configure(bg=bg)

            tk.Label(hud, text=title, font=("Orbitron", 12, "bold"), fg=color, bg=bg).pack(pady=8)
            tk.Label(hud, text=message, font=("Segoe UI", 9), fg="white", bg=bg, wraplength=350).pack()
            tk.Label(hud, text=datetime.now().strftime("%H:%M:%S"), font=("Consolas", 8), fg="#888888", bg=bg).pack(pady=5)

            self.root.after(4000, lambda: hud.destroy() if hud.winfo_exists() else None)
        except Exception as e:
            self._log(f"HUD hatası: {e}")

    def _load_cascade(self):
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        if self.face_cascade.empty():
            self._log("Yüz cascade dosyası yüklenemedi!")

    def _scan_face(self, stop_event):
        """Kamerayı açar, yüz arar. Yüz bulunca başarılı sayar."""
        self._log("🔍 Kamera başlatılıyor...")
        
        # Kamera için birden fazla backend dene
        for backend in [cv2.CAP_DSHOW, cv2.CAP_ANY]:
            self.camera = cv2.VideoCapture(0, backend)
            if self.camera.isOpened():
                self._log(f"Kamera açıldı (backend={backend})")
                break
        
        if not self.camera or not self.camera.isOpened():
            self._show_hud("❌ KAMERA HATASI", "Kamera bulunamadı veya başka bir uygulama kullanıyor.", "#ff3333", "#330000")
            self.deactivate()
            return

        start_time = time.time()
        face_detected = False

        while not stop_event.is_set() and self.is_active:
            ret, frame = self.camera.read()
            if not ret:
                self._log("Kamera görüntüsü alınamıyor")
                break

            frame = cv2.flip(frame, 1)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)

            if len(faces) > 0:
                face_detected = True
                break

            if time.time() - start_time > 8:
                break

            time.sleep(0.05)

        self.camera.release()
        self.camera = None

        if face_detected:
            self._play_success_sound()
            self._show_hud("✅ ERİŞİM ONAYLANDI", "Yüz tanıma başarılı. Hoş geldiniz.", "#00ff88", "#003300")
            self.deactivate()
        else:
            self._play_fail_sound()
            self._show_hud("❌ ERİŞİM REDDEDİLDİ", "Yüz algılanamadı veya süre doldu.", "#ff3333", "#330000")
            self.deactivate()

    def activate(self, stop_music=False) -> str:
        if self.is_active:
            return "Biyometrik kalkan zaten aktif."
        if self.face_cascade is None or self.face_cascade.empty():
            return "Yüz tanıma modeli yüklenemedi. OpenCV kurulumunu kontrol edin."

        self.is_active = True
        self._log("🛡️ Biyometrik Kalkan AKTİF - Basit yüz tanıma modu")
        self._show_hud("🧬 BİYOMETRİK KALKAN AKTİF", "Lütfen kameraya doğruca bakın. 8 saniye içinde yüzünüz taranacak.", "#00ffcc", "#000033")
        self._beep(800, 100)
        self._beep(1000, 100)

        if stop_music:
            try:
                import pyautogui
                pyautogui.press('playpause')
            except:
                pass

        stop_event = threading.Event()
        self.scan_thread = threading.Thread(target=self._scan_face, args=(stop_event,), daemon=True)
        self.scan_thread.start()
        return "Biyometrik kalkan devrede. Yüzünüz kameraya gösterin."

    def deactivate(self) -> str:
        if not self.is_active:
            return "Biyometrik kalkan zaten pasif."
        self.is_active = False
        if self.camera:
            self.camera.release()
        self._log("🛡️ Biyometrik Kalkan KAPATILDI")
        return "Biyometrik kalkan kapatıldı."

    def register_face(self, name="user") -> str:
        return "Bu basit modda yüz kaydı gerekmez. Herhangi bir yüz algılandığında başarılı sayılır."

def biometric_shield(parameters: Optional[dict] = None, player=None, root=None) -> str:
    if parameters is None:
        parameters = {}
    action = parameters.get("action", "activate")
    stop_music = parameters.get("stop_music", False)

    shield = BiometricShield(player=player, root=root)

    if action == "activate":
        return shield.activate(stop_music=stop_music)
    elif action == "deactivate":
        return shield.deactivate()
    elif action == "register":
        return shield.register_face()
    else:
        return f"Bilinmeyen aksiyon: {action}"