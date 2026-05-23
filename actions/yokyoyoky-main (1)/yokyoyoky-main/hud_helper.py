# actions/hud_helper.py
# Thread-safe HUD ve Pencere Yönetimi - Kasılmayı Önleyici

import threading
import time
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PyQt6.QtCore import Qt, QTimer, QCoreApplication


def show_hud_safe(title: str, message: str, color: str = "#00ffcc", bg: str = "#000033", 
                  duration: int = 4000, parent=None):
    """
    Thread-safe HUD penceresi açar. Kasılmayı önleyen implementasyon.
    
    Args:
        title: HUD başlığı
        message: HUD mesajı
        color: Font rengi (hex)
        bg: Arka plan rengi (hex)
        duration: Pencere kaç ms kalacak (0 = kalıcı)
        parent: Parent widget
    """
    def create_hud():
        try:
            hud = QWidget(parent)
            hud.setWindowFlags(
                Qt.WindowType.FramelessWindowHint |
                Qt.WindowType.WindowStaysOnTopHint
            )
            hud.setWindowOpacity(0.92)
            hud.setGeometry(15, 15, 380, 120)
            hud.setStyleSheet(f"background-color: {bg};")

            layout = QVBoxLayout(hud)
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setSpacing(4)

            title_label = QLabel(title)
            title_label.setStyleSheet(
                f"color: {color}; font-family: 'Orbitron', 'Courier New'; font-size: 11px; font-weight: bold;"
            )
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(title_label)

            msg_label = QLabel(message)
            msg_label.setStyleSheet("color: #cccccc; font-family: 'Segoe UI'; font-size: 8px;")
            msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            msg_label.setWordWrap(True)
            layout.addWidget(msg_label)

            hud.show()
            
            # Non-blocking kapanış
            if duration > 0:
                QTimer.singleShot(duration, lambda: safe_close(hud))

        except Exception as e:
            print(f"[HUD ERROR] {e}")

    def safe_close(widget):
        try:
            if widget and widget.isVisible():
                widget.close()
        except:
            pass

    # Main event loop'a schedule et - async
    try:
        app = QCoreApplication.instance()
        if app:
            # 10ms delay ile call et - event loop donmasın
            QTimer.singleShot(10, create_hud)
        else:
            create_hud()
    except:
        # Fallback: thread'de calistiir
        threading.Thread(target=create_hud, daemon=True).start()


def show_window_safe(window_callable, *args, **kwargs):
    """
    Thread-safe pencere açar. Callable'ı main event loop'ta çalıştırır.
    
    Args:
        window_callable: Pencereyi açan function
        *args, **kwargs: Function'a geçecek parametreler
    
    Returns:
        Sonuç string
    """
    result = {"value": None}

    def create_window():
        try:
            result["value"] = window_callable(*args, **kwargs)
        except Exception as e:
            result["value"] = f"Pencere açılırken hata: {e}"
            print(f"[WINDOW ERROR] {e}")

    # Main event loop'a schedule et - async
    try:
        app = QCoreApplication.instance()
        if app:
            QTimer.singleShot(50, create_window)
            return "Pencere açılıyor..."
        else:
            create_window()
            return result["value"]
    except Exception as e:
        return f"Pencere hatası: {e}"


# Renk presets
HUD_COLORS = {
    "success": {"color": "#00ff88", "bg": "#003300"},
    "error": {"color": "#ff3333", "bg": "#330000"},
    "info": {"color": "#00ffcc", "bg": "#000033"},
    "warning": {"color": "#ffaa00", "bg": "#330a00"},
    "processing": {"color": "#0099ff", "bg": "#003366"},
}


def show_hud_preset(title: str, message: str, preset: str = "info", duration: int = 4000, parent=None):
    """
    Preset renkleriyle HUD göster.
    
    Args:
        title: HUD başlığı
        message: HUD mesajı
        preset: 'success', 'error', 'info', 'warning', 'processing'
        duration: Pencere kaç ms kalacak
        parent: Parent widget
    """
    colors = HUD_COLORS.get(preset, HUD_COLORS["info"])
    show_hud_safe(title, message, colors["color"], colors["bg"], duration, parent)
