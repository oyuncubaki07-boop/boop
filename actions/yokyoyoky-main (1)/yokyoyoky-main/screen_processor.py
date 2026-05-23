# actions/screen_processor.py
# J.A.R.V.I.S. Ekran İşleme Modülü (OCR + Görsel Analiz) — PyQt6

import os
import json
import platform
from pathlib import Path

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer

# Cross-platform ses desteği
_OS = platform.system()
if _OS == "Windows":
    import winsound

def get_base_dir():
    import sys
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

def _get_api_key():
    config_path = get_base_dir() / "config" / "api_keys.json"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("gemini_api_key", "").strip()
    except Exception:
        return ""

def _show_hud(root, title, message, color="#1a1a00"):
    """PyQt6 HUD penceresi gösterir."""
    if not root or not isinstance(root, QWidget):
        return
    try:
        hud = QWidget(root)
        hud.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        hud.setWindowOpacity(0.92)
        hud.setGeometry(15, 15, 360, 90)
        hud.setStyleSheet(f"background-color: {color};")

        layout = QVBoxLayout(hud)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        title_color = "#ffff00" if color == "#1a1a00" else "#ff6666"
        title_label = QLabel(title)
        title_label.setStyleSheet(
            f"color: {title_color}; font-family: 'Orbitron', 'Courier New'; font-size: 10px; font-weight: bold;"
        )
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        msg_label = QLabel(message)
        msg_label.setStyleSheet("color: white; font-family: 'Segoe UI'; font-size: 9px;")
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)

        hud.show()

        try:
            if _OS == "Windows":
                winsound.Beep(500, 100)
            else:
                print('\a', end='', flush=True)
        except:
            pass

        QTimer.singleShot(3000, hud.close)
    except Exception as e:
        print(f"[ScreenProcessor] HUD hatası: {e}")

def screen_process(parameters=None, player=None, root=None, speak=None) -> str:
    """
    Ekran görüntüsü alır, Gemini ile analiz yapar.
    
    Parametreler:
        prompt (str): Analiz için özel soru (varsayılan: "Ekranda ne görüyorsun? Kısa ve net özetle.")
        save_image (bool): Görüntüyü kaydet (varsayılan: False)
    """
    params = parameters or {}
    prompt = params.get("prompt", "Ekranda ne görüyorsun? Kısa ve net özetle patron için anlat.")
    save_image = params.get("save_image", False)
    
    try:
        import pyautogui
        import google.generativeai as genai
        
        if player:
            player.write_log("SYS: 👁️ Ekran analizi başlatılıyor...")
        
        # UI işlemlerini ana thread'e yönlendiriyoruz
        if root:
            QTimer.singleShot(0, lambda: _show_hud(root, "👁️ GÖRSEL ANALİZ", "Ekran inceleniyor...", "#1a1a00"))
        
        # Ekran görüntüsü al
        screenshot = pyautogui.screenshot()
        
        # İsteğe bağlı kalıcı kayıt
        if save_image and player:
            save_dir = get_base_dir() / "screen_captures"
            save_dir.mkdir(exist_ok=True)
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            perm_path = save_dir / f"screen_{timestamp}.png"
            screenshot.save(perm_path)
            player.write_log(f"SYS: Ekran görüntüsü kaydedildi: {perm_path}")
        
        # Gemini analizi
        api_key = _get_api_key()
        if not api_key:
            return "API anahtarı bulunamadı. Lütfen config/api_keys.json dosyasını kontrol edin."
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        
        # Görseli doğrudan modele ilet
        response = model.generate_content([prompt, screenshot])
        
        result = response.text.strip()
        if not result:
            result = "Ekranda dikkat çekici bir şey göremedim patron."
        
        # Sesli çıktı
        if speak:
            speak(result[:300])
        
        # Başarı HUD'u
        if root:
            QTimer.singleShot(0, lambda: _show_hud(root, "✅ ANALİZ TAMAM", "Sonuç hazır", "#0a2a0a"))
        
        return f"👁️ Ekran analizi sonucu:\n\n{result}"
    
    except ImportError as e:
        return f"Gerekli kütüphane eksik canım: {e}. 'pip install pyautogui google-generativeai pillow' komutuyla kurabilirsin."
    except Exception as e:
        error_msg = f"Ekran işleme hatası: {str(e)}"
        if player:
            player.write_log(f"SYS: {error_msg}")
        if root:
            QTimer.singleShot(0, lambda: _show_hud(root, "❌ ANALİZ HATASI", error_msg[:50], "#2a0a0a"))
        return error_msg