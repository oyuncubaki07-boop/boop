"""
news_briefing.py - J.A.R.V.I.S. Haber Özeti Modülü (PyQt6)
TRT Haber, NTV, CNN Türk gibi RSS kaynaklarından son dakika haberlerini çeker.
"""

import urllib.request
import xml.etree.ElementTree as ET
import winsound
import ssl
from datetime import datetime
from typing import List, Optional

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QScrollArea, QFrame
from PyQt6.QtCore import Qt, QTimer

# RSS kaynakları (öncelik sırasına göre)
RSS_SOURCES = [
    {
        "name": "TRT Haber",
        "url": "https://www.trthaber.com/manset_articles.rss",
        "encoding": "utf-8"
    },
    {
        "name": "NTV",
        "url": "https://www.ntv.com.tr/son-dakika.rss",
        "encoding": "utf-8"
    },
    {
        "name": "CNN Türk",
        "url": "https://www.cnnturk.com/feed/rss/all/news",
        "encoding": "utf-8"
    }
]


def get_news_from_source(source: dict, max_items: int) -> List[str]:
    """Tek bir RSS kaynağından haber çekmeyi dener."""
    try:
        req = urllib.request.Request(
            source["url"],
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(req, timeout=8, context=context) as response:
            xml_data = response.read()
            encoding = source.get("encoding", "utf-8")
            try:
                xml_str = xml_data.decode(encoding)
            except:
                xml_str = xml_data.decode('utf-8', errors='ignore')
            
            root = ET.fromstring(xml_str)
            items = root.findall('.//item')
            if not items:
                for ns in ['', 'http://purl.org/rss/1.0/', 'http://www.w3.org/2005/Atom']:
                    items = root.findall(f'.//{{{ns}}}item')
                    if items:
                        break
            news = []
            for item in items[:max_items]:
                title_elem = item.find('title')
                if title_elem is None:
                    title_elem = item.find('{http://purl.org/rss/1.0/}title')
                if title_elem is not None and title_elem.text:
                    news.append(title_elem.text.strip())
            return news
    except Exception as e:
        print(f"[NEWS] {source['name']} hatası: {e}")
        return []


def get_news(max_items: int = 3, fallback: bool = True) -> List[str]:
    """RSS kaynaklarından haber başlıklarını çeker. İlk başarılı kaynağı kullanır."""
    for source in RSS_SOURCES:
        try:
            news_list = get_news_from_source(source, max_items)
            if news_list:
                return news_list
        except Exception as e:
            print(f"[NEWS] {source['name']} hatası: {e}")
            continue
    
    if fallback:
        return ["Haber akışına şu an ulaşılamıyor. Daha sonra tekrar deneyin."]
    return []


def show_news_hud(root, news_list: List[str], source_name: str = ""):
    """Haber özetini gösteren PyQt6 HUD penceresi."""
    try:
        parent = root if isinstance(root, QWidget) else None
        hud = QWidget(parent)
        hud.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        hud.setWindowOpacity(0.92)
        hud.setGeometry(10, 10, 520, 220)
        hud.setStyleSheet("background-color: #00111a;")

        layout = QVBoxLayout(hud)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Başlık
        title_text = f"🌍 DÜNYA GÜNDEMİ - {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        if source_name:
            title_text += f" ({source_name})"
        title = QLabel(title_text)
        title.setStyleSheet("color: #00e6e6; font-family: 'Courier New'; font-size: 11px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Haber listesi için scroll alanı
        scroll = QScrollArea()
        scroll.setStyleSheet("QScrollArea { background-color: #00111a; border: none; }")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        news_frame = QFrame()
        news_frame.setStyleSheet("background-color: #00111a;")
        news_layout = QVBoxLayout(news_frame)
        news_layout.setContentsMargins(15, 5, 15, 5)
        news_layout.setSpacing(4)

        for i, news in enumerate(news_list, 1):
            label = QLabel(f"{i}. {news}")
            label.setStyleSheet("color: white; font-family: 'Courier New'; font-size: 9px;")
            label.setWordWrap(True)
            label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            news_layout.addWidget(label)

        scroll.setWidget(news_frame)
        layout.addWidget(scroll)

        hud.show()

        try:
            winsound.Beep(600, 150)
            winsound.Beep(900, 200)
        except:
            pass

        QTimer.singleShot(15000, hud.close)
    except Exception as e:
        print(f"HUD hatası: {e}")


def news_briefing(parameters: Optional[dict] = None, player=None, root=None) -> str:
    """
    Haber özeti oluşturur.
    parameters: {
        "count": 3,               # Kaç haber başlığı gösterilecek
        "silent": False,          # Sadece log, HUD gösterme
        "source_preference": None # Belirli bir kaynağı zorla (TRT Haber, NTV, CNN Türk)
    }
    """
    params = parameters or {}
    max_items = params.get("count", 3)
    silent = params.get("silent", False)
    source_pref = params.get("source_preference", None)
    
    if player:
        player.write_log("SYS: 📡 Haber kaynakları taranıyor...")
    
    # İstenen kaynağı öne al
    sources = RSS_SOURCES.copy()
    if source_pref:
        for i, src in enumerate(sources):
            if src["name"].lower() == source_pref.lower():
                sources.insert(0, sources.pop(i))
                break
    
    news_list = []
    used_source = ""
    for src in sources:
        news_list = get_news_from_source(src, max_items)
        if news_list and "ulaşılamıyor" not in news_list[0]:
            used_source = src["name"]
            break
    
    if not news_list:
        news_list = ["Haber akışına şu an ulaşılamıyor. Daha sonra tekrar deneyin."]
    
    if not silent and root:
        show_news_hud(root, news_list, used_source)
    
    if player:
        player.write_log(f"SYS: {len(news_list)} haber başlığı alındı.")
    
    if "ulaşılamıyor" in news_list[0]:
        return "Haber sunucularına bağlanamadım patron. Bağlantınızı kontrol edin."
    
    news_text = "Patron, güncel haber başlıkları şöyle: " + ". ".join(news_list) + " Daha fazla detay isterseniz, size özel bir haber derlemesi yapabilirim."
    return news_text