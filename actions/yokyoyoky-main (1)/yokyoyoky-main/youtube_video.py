import webbrowser
import urllib.parse
import platform

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer

_OS = platform.system()
if _OS == "Windows":
    import winsound


def _show_youtube_hud(root, query):
    """PyQt6 YouTube HUD penceresini ana iş parçacığında güvenli bir şekilde oluşturur."""
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
        hud.setStyleSheet("background-color: #0a0a2a;")

        layout = QVBoxLayout(hud)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        title = QLabel("🎬 YOUTUBE PROTOKOLÜ")
        title.setStyleSheet(
            "color: #00ffcc; font-family: 'Orbitron', 'Courier New'; font-size: 11px; font-weight: bold;"
        )
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        query_label = QLabel(f"Hedef: {query[:35]}...")
        query_label.setStyleSheet("color: white; font-family: 'Segoe UI'; font-size: 9px;")
        query_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(query_label)

        hud.show()

        try:
            if _OS == "Windows":
                winsound.Beep(800, 150)
            else:
                print('\a', end='', flush=True)
        except:
            pass

        QTimer.singleShot(3000, hud.close)
    except Exception as e:
        print(f"[YouTube] HUD Hatası: {e}")


def youtube_video(parameters=None, player=None, root=None, speak=None) -> str:
    """
    YouTube'da video açar veya direkt bir video URL'sini çalıştırır.
    
    Parametreler:
        query (str): Aranacak kelime veya video URL'si
    """
    params = parameters or {}
    query = params.get("query", "").strip()
    
    if not query:
        return "Hedef belirtilmedi. İşlem iptal edildi."
    
    if player:
        player.write_log(f"SYS: 🎵 YouTube arama protokolü devrede: {query}")
    
    if root:
        QTimer.singleShot(0, lambda: _show_youtube_hud(root, query))
    
    try:
        if query.startswith(("http://", "https://")):
            url = query
        else:
            encoded_query = urllib.parse.quote(query)
            url = f"https://www.youtube.com/results?search_query={encoded_query}"
        
        webbrowser.open_new_tab(url)
        
        msg = f"YouTube üzerinde '{query}' hedefine erişiliyor."
        if speak:
            speak(msg)
        return msg
    
    except Exception as e:
        error_msg = f"Bağlantı hatası: {str(e)}"
        if player:
            player.write_log(f"ERR: {error_msg}")
        return error_msg