# actions/web_search.py
# J.A.R.V.I.S. Web Search Module - DDG (Scraping) + Gemini (Summarization)

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
    try:
        with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            key = data.get("gemini_api_key", "").strip()
            if not key:
                raise ValueError("Gemini API key bulunamadı.")
            return key
    except Exception as e:
        print(f"[WebSearch] API anahtarı okunamadı: {e}")
        return ""

def _ddg_search(query: str, max_results: int = 5) -> list:
    """DuckDuckGo araması yapar ve ham sonuçları döndürür."""
    try:
        from ddgs import DDGS
    except ImportError:
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            from duckduckgo_search import DDGS
            
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "snippet": r.get("body", ""),
                    "url": r.get("href", "")
                })
    except Exception as e:
        print(f"[WebSearch] DDG Arama Hatası: {e}")
    return results

def _format_ddg_results(query: str, results: list) -> str:
    """DDG sonuçlarını metin tabanlı okunabilir bir formata çevirir."""
    if not results:
        return f"🔍 '{query}' için web üzerinde sonuç bulunamadı."
    
    lines = [f"🔎 '{query}' arama sonuçları:\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['title']}")
        if r['snippet']:
            lines.append(f"   📝 {r['snippet'][:200]}...")
        if r['url']:
            lines.append(f"   🔗 {r['url']}")
        lines.append("")
    return "\n".join(lines).strip()

def _gemini_summarize(query: str, search_context: str) -> str:
    """Web'den alınan ham verileri Gemini ile özetler."""
    import google.generativeai as genai
    
    api_key = _get_api_key()
    if not api_key:
        raise ValueError("Gemini API anahtarı yok")
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    prompt = f"""Sen J.A.R.V.I.S.'sin. Kullanıcı şu aramayı yaptı: '{query}'
    
Aşağıda internetten çekilen en güncel ham arama sonuçları (snippet'ler) bulunuyor:
{search_context}

Lütfen yukarıdaki bilgileri kullanarak kullanıcının sorusuna doğrudan, net ve yararlı bir yanıt ver. (Eğer snippet'ler alakasızsa veya yetersizse bunu belirt.)"""

    response = model.generate_content(prompt)
    if not response.text:
        raise ValueError("Gemini boş yanıt döndü")
    return response.text.strip()

def web_search(parameters: dict, player=None, speak=None, **kwargs) -> str:
    """
    Web araması yapar. Önce DuckDuckGo ile verileri çeker, ardından Gemini ile özetler.
    Gemini başarısız olursa ham DDG sonuçlarını döndürür.
    
    Parametreler:
        query (str): Aranacak sorgu
        mode (str): "search" veya "compare" 
    """
    params = parameters or {}
    query = params.get("query", "").strip()
    
    if not query:
        return "Lütfen neyi aramamı istediğini belirt patron."

    if player:
        player.write_log(f"SYS: 🔍 Web'de aranıyor: {query}")

    # 1. Adım: İnternetten verileri çek (DuckDuckGo)
    raw_results = _ddg_search(query, max_results=5)
    formatted_context = _format_ddg_results(query, raw_results)
    
    if not raw_results:
        return formatted_context # Bulunamadı mesajı dönecek

    # 2. Adım: Gemini ile zekice özetle
    try:
        if player: player.write_log("SYS: 🧠 Arama sonuçları analiz ediliyor...")
        final_answer = _gemini_summarize(query, formatted_context)
        
        if player: player.write_log("SYS: ✅ Analiz başarılı.")
        if speak: speak(f"{query} hakkında web'de bulduklarımı özetliyorum patron.")
        
        return final_answer
        
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower():
            if player: player.write_log("SYS: ⚠️ Gemini API kota aşımı, ham sonuçlar listeleniyor.")
        else:
            if player: player.write_log(f"SYS: ⚠️ Analiz hatası: {e}, ham sonuçlara geçiliyor.")
            
        # Eğer Gemini bir şekilde çökerse, ham veriyi gösterelim ki cevapsız kalmayalım
        if speak: speak("Sonuçları özetlerken bir sorun oluştu patron, sana doğrudan bağlantıları iletiyorum.")
        return formatted_context