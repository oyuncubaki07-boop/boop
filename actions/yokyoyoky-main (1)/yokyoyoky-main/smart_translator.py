# actions/smart_translator.py
# J.A.R.V.I.S. Evrensel Çevirmen (deep-translator ile) — PyQt6

import winsound
from deep_translator import GoogleTranslator

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer


def _show_hud(root, target_lang):
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
        hud.setGeometry(15, 15, 320, 85)
        hud.setStyleSheet("background-color: #0a0a2a;")

        layout = QVBoxLayout(hud)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        title = QLabel("🌍 EVRENSEL ÇEVİRMEN")
        title.setStyleSheet("color: #00ffcc; font-family: 'Orbitron', 'Courier New'; font-size: 10px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        target_label = QLabel(f"Hedef: {target_lang.upper()}")
        target_label.setStyleSheet("color: white; font-family: 'Segoe UI'; font-size: 9px;")
        target_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(target_label)

        wait_label = QLabel("Çeviri bekleniyor...")
        wait_label.setStyleSheet("color: #aaaaaa; font-family: 'Segoe UI'; font-size: 8px;")
        wait_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(wait_label)

        hud.show()

        try:
            winsound.Beep(600, 100)
            winsound.Beep(800, 100)
        except:
            pass

        QTimer.singleShot(3000, hud.close)
    except:
        pass


def smart_translator(parameters=None, player=None, root=None, speak=None) -> str:
    params = parameters or {}
    target_lang = params.get("language", "İngilizce").strip()
    text_to_translate = params.get("text", "").strip()
    source_lang = params.get("source_lang", "auto")
    show_hud = params.get("show_hud", True)

    # Dil kodları (Türkçe isim -> ISO)
    lang_map = {
        "ingilizce": "en", "english": "en",
        "türkçe": "tr", "turkish": "tr",
        "almanca": "de", "german": "de",
        "fransızca": "fr", "french": "fr",
        "ispanyolca": "es", "spanish": "es",
        "italyanca": "it", "italian": "it",
        "rusça": "ru", "russian": "ru",
        "çince": "zh-cn", "chinese": "zh-cn",
        "japonca": "ja", "japanese": "ja",
        "arapça": "ar", "arabic": "ar",
        "portekizce": "pt", "portuguese": "pt",
        "hollandaca": "nl", "dutch": "nl",
        "korece": "ko", "korean": "ko"
    }
    target_code = lang_map.get(target_lang.lower(), target_lang.lower())

    if player:
        player.write_log(f"SYS: 🌍 Çevirmen -> {target_lang} ({target_code})")

    # HUD gösterimi
    if show_hud and root:
        _show_hud(root, target_lang)

    # Metin verilmişse hemen çevir
    if text_to_translate:
        try:
            translator = GoogleTranslator(source='auto', target=target_code)
            translated = translator.translate(text_to_translate)
            if speak:
                speak(f"Çeviri: {translated}")
            return f"📝 Çeviri ({source_lang} → {target_lang}):\nOrijinal: {text_to_translate}\nÇeviri: {translated}"
        except Exception as e:
            return f"Çeviri hatası: {e}. İnternet bağlantınızı kontrol edin."

    return f"Evrensel çevirmen hazır, patron. {target_lang} diline çeviri yapabilirim. Çevirmemi istediğiniz metni söyleyin."