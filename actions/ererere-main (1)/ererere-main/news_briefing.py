"""
news_briefing.py - J.A.R.V.I.S. Haber Özeti Modülü
TRT Haber, NTV, CNN Türk gibi RSS kaynaklarından son dakika haberlerini çeker.
"""

import urllib.request
import xml.etree.ElementTree as ET
import tkinter as tk
import winsound
import ssl
from datetime import datetime
from typing import List, Optional

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

def get_news(max_items: int = 3, fallback: bool = True) -> List[str]:
    """
    RSS kaynaklarından haber başlıklarını çeker.
    İlk başarılı kaynağı kullanır.
    """
    for source in RSS_SOURCES:
        try:
            req = urllib.request.Request(
                source["url"],
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            # SSL sertifika sorunlarını aşmak için (gerekirse)
            context = ssl._create_unverified_context()
            with urllib.request.urlopen(req, timeout=8, context=context) as response:
                xml_data = response.read()
                # Encoding'i dene
                encoding = source.get("encoding", "utf-8")
                try:
                    xml_str = xml_data.decode(encoding)
                except:
                    xml_str = xml_data.decode('utf-8', errors='ignore')
                
                root = ET.fromstring(xml_str)
                news_list = []
                # Farklı RSS yapılarına uyum sağlamak için namespace'leri dikkate al
                # Çoğu RSS'de item'lar doğrudan altında
                items = root.findall('.//item')
                if not items:
                    # Farklı namespace denemesi
                    for ns in ['', 'http://purl.org/rss/1.0/', 'http://www.w3.org/2005/Atom']:
                        items = root.findall(f'.//{{{ns}}}item')
                        if items:
                            break
                
                for item in items[:max_items]:
                    title_elem = item.find('title')
                    if title_elem is None:
                        # Farklı namespace
                        title_elem = item.find('{http://purl.org/rss/1.0/}title')
                    if title_elem is not None:
                        title = title_elem.text
                        if title:
                            news_list.append(title.strip())
                if news_list:
                    return news_list
        except Exception as e:
            print(f"[NEWS] {source['name']} hatası: {e}")
            continue
    
    if fallback:
        return ["Haber akışına şu an ulaşılamıyor. Daha sonra tekrar deneyin."]
    return []

def show_news_hud(root, news_list: List[str], source_name: str = ""):
    """Haber özetini gösteren HUD penceresi."""
    try:
        hud = tk.Toplevel(root)
        hud.overrideredirect(True)
        hud.attributes("-topmost", True, "-alpha", 0.92)
        hud.geometry("520x220+10+10")
        hud.configure(bg="#00111a")
        
        # Başlık
        title_text = f"🌍 DÜNYA GÜNDEMİ - {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        if source_name:
            title_text += f" ({source_name})"
        tk.Label(hud, text=title_text, font=("Courier", 11, "bold"), fg="#00e6e6", bg="#00111a").pack(pady=8)
        
        # Haber listesi
        frame = tk.Frame(hud, bg="#00111a")
        frame.pack(fill="both", expand=True, padx=15, pady=5)
        
        for i, news in enumerate(news_list, 1):
            # Her haber için noktalı çizgiyle ayır
            tk.Label(frame, text=f"{i}. {news}", font=("Courier", 9), fg="white", bg="#00111a", 
                     wraplength=480, justify="left", anchor="w").pack(fill="x", pady=2)
        
        # Sesli bildirim
        try:
            winsound.Beep(600, 150)
            winsound.Beep(900, 200)
        except:
            pass
        
        # Otomatik kapanma (15 saniye)
        root.after(15000, lambda: hud.destroy() if hud.winfo_exists() else None)
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
    
    # J.A.R.V.I.S.'in okuyacağı metni oluştur
    if "ulaşılamıyor" in news_list[0]:
        return "Haber sunucularına bağlanamadım patron. Bağlantınızı kontrol edin."
    
    news_text = "Patron, güncel haber başlıkları şöyle: " + ". ".join(news_list) + " Daha fazla detay isterseniz, size özel bir haber derlemesi yapabilirim."
    return news_text

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
                # Namespace dene
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