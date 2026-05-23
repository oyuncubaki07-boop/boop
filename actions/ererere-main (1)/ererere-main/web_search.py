# actions/web_search.py
# J.A.R.V.I.S. Web Search Module
# Primary: Gemini with google_search tool
# Fallback: DuckDuckGo (duckduckgo_search)

import json
import sys
from pathlib import Path

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

BASE_DIR = get_base_dir()
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"

def _get_api_key() -> str:
    """Gemini API anahtarını config dosyasından güvenle okur."""
    try:
        with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            key = data.get("gemini_api_key", "").strip()
            if not key:
                raise ValueError("Gemini API key bulunamadı.")
            return key
    except Exception as e:
        raise RuntimeError(f"API anahtarı okunamadı: {e}")

def _gemini_search(query: str) -> str:
    """
    Gemini'nin google_search tool'unu kullanarak güncel web araması yapar.
    """
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=_get_api_key())
    # Google Search tool'unu ekle
    tools = [types.Tool(google_search=types.GoogleSearch())]
    
    response = client.models.generate_content(
        model="gemini-2.0-flash",  # veya gemini-2.5-flash-lite
        contents=query,
        config=types.GenerateContentConfig(tools=tools)
    )
    
    # Yanıtı parse et
    text_parts = []
    for part in response.candidates[0].content.parts:
        if part.text:
            text_parts.append(part.text)
    result = "\n".join(text_parts).strip()
    if not result:
        raise ValueError("Gemini boş yanıt döndü.")
    return result

def _ddg_search(query: str, max_results: int = 5) -> list:
    """DuckDuckGo üzerinden arama yapar, sonuç listesi döndürür."""
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        raise ImportError("duckduckgo_search kütüphanesi yüklü değil. 'pip install duckduckgo-search' ile kurun.")
    
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append({
                "title": r.get("title", ""),
                "snippet": r.get("body", ""),
                "url": r.get("href", "")
            })
    return results

def _format_ddg_results(query: str, results: list) -> str:
    """DDG sonuçlarını okunabilir metne dönüştürür."""
    if not results:
        return f"🔍 '{query}' için sonuç bulunamadı."
    
    lines = [f"🔎 '{query}' arama sonuçları:\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['title']}")
        if r['snippet']:
            lines.append(f"   📝 {r['snippet'][:200]}...")
        if r['url']:
            lines.append(f"   🔗 {r['url']}")
        lines.append("")
    return "\n".join(lines).strip()

def _compare_with_gemini(items: list, aspect: str) -> str:
    """Gemini kullanarak karşılaştırma yapar."""
    query = f"Compare {', '.join(items)} in terms of {aspect}. Provide specific facts, differences, and data."
    return _gemini_search(query)

def _compare_with_ddg(items: list, aspect: str) -> str:
    """DDG ile her bir öğe için ayrı arama yaparak karşılaştırma oluşturur."""
    lines = [f"📊 KARŞILAŞTIRMA: {', '.join(items)} - {aspect.upper()}\n" + "─"*50]
    for item in items:
        lines.append(f"\n▸ {item.upper()}")
        search_query = f"{item} {aspect}"
        try:
            results = _ddg_search(search_query, max_results=2)
            if results:
                for r in results:
                    if r['snippet']:
                        lines.append(f"   • {r['snippet'][:150]}...")
            else:
                lines.append("   • Bilgi bulunamadı.")
        except Exception as e:
            lines.append(f"   • Hata: {e}")
    return "\n".join(lines)

def web_search(parameters: dict, player=None, speak=None, **kwargs) -> str:
    """
    Ana web_search fonksiyonu.
    
    Parametreler:
        query (str): Arama sorgusu.
        mode (str): "search" veya "compare"
        items (list): Karşılaştırma yapılacak öğeler (mode='compare' ise)
        aspect (str): Karşılaştırma konusu (mode='compare' ise)
    """
    params = parameters or {}
    query = params.get("query", "").strip()
    mode = params.get("mode", "search").lower()
    items = params.get("items", [])
    aspect = params.get("aspect", "genel özellikler")
    
    if mode == "compare":
        if not items or len(items) < 2:
            return "Karşılaştırma için en az iki öğe belirtmelisiniz. Örnek: items=['iPhone', 'Samsung']"
        if player:
            player.write_log(f"[WebSearch] 🔍 Karşılaştırma: {items} - {aspect}")
        try:
            # Önce Gemini'yi dene
            result = _compare_with_gemini(items, aspect)
            if player:
                player.write_log("[WebSearch] ✅ Gemini karşılaştırma başarılı.")
            return result
        except Exception as e:
            if player:
                player.write_log(f"[WebSearch] ⚠️ Gemini karşılaştırma hatası: {e}, DDG'ye geçiliyor...")
            return _compare_with_ddg(items, aspect)
    
    # Normal arama modu
    if not query:
        return "Lütfen bir arama sorgusu girin, efendim."
    
    if player:
        player.write_log(f"[WebSearch] 🔍 Aranıyor: {query}")
    
    try:
        # Önce Gemini dene
        result = _gemini_search(query)
        if player:
            player.write_log("[WebSearch] ✅ Gemini arama başarılı.")
        return result
    except Exception as e:
        if player:
            player.write_log(f"[WebSearch] ⚠️ Gemini hatası: {e}, DuckDuckGo deneniyor...")
        try:
            results = _ddg_search(query)
            return _format_ddg_results(query, results)
        except Exception as ddg_e:
            error_msg = f"Tüm arama yöntemleri başarısız oldu: Gemini({e}), DDG({ddg_e})"
            if player:
                player.write_log(f"[WebSearch] ❌ {error_msg}")
            return f"Arama yapılamadı, efendim: {error_msg}"