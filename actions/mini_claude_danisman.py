"""
Mini Claude Danışman Alt-Ajanı
JARVIS için derin araştırma ve kodlama görevlerini OpenRouter'daki Claude modelleriyle çözer.
"""

import os
import json
import logging
import asyncio
import requests
from pathlib import Path
import sys

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False): return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

BASE_DIR = get_base_dir()
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"

def _get_openrouter_api_key():
    try:
        with open(API_CONFIG_PATH, "r", encoding="utf-8") as f: 
            return json.load(f).get("openrouter_api_key", "")
    except: return ""

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Varsayılan model eşlemesi
MODEL_MAP = {
    "haiku": "anthropic/claude-3-haiku",
    "sonnet": "anthropic/claude-3.5-sonnet",  # <-- 3 yerine 3.5 yaptık
}

# Loglama
logger = logging.getLogger("MiniClaude")

def run_action(parameters: dict, player=None, speak=None):
    """
    JARVIS'in senkron (normal) sisteminden Claude'a istek atar.
    JARVIS arka planda zaten bu fonksiyonu run_in_executor ile thread içinde çalıştırdığı için 
    ana döngüyü (ses dinleme) kesinlikle kilitlemez.
    """
    konu = parameters.get("arastirma_konusu", "").strip()
    if not konu:
        return "Hata: Araştırma konusu belirtilmedi."

    model_secimi = parameters.get("model_secimi", "haiku").lower()
    model_id = MODEL_MAP.get(model_secimi, MODEL_MAP["haiku"])
    
    api_key = _get_openrouter_api_key()
    if not api_key:
        return "Hata: OpenRouter API anahtarı config klasöründe bulunamadı."

    # Kullanıcıya bekleme mesajı ver (Konuşma kurallarına uygun olarak işlem öncesi 1 cümle)
    if callable(speak):
        speak(f"Bu konuyu uzman alt-ajan Claude'a danışıyorum. Lütfen hatta kalın.")
        
    print(f"\n[MiniClaude] Çağrılıyor | Model: {model_id} | Konu: {konu[:50]}...")

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/jarvis-assistant",
            "X-Title": "JARVIS-MiniClaude"
        }

        system_prompt = (
            "Sen JARVIS adında bir yapay zeka asistanının 'Arka Plan Danışmanı' ve 'Araştırmacısısın'. "
            "Kullanıcının (Mimar) verdiği görevi en derin, en kapsamlı ve en doğru şekilde yerine getir. "
            "Gerekirse kod yaz, kaynak göster. Çıktıyı Türkçe olarak ve doğrudan sadede gelerek ver. "
            "Yazacağın yanıt, JARVIS tarafından sesli olarak okunacaktır, bu yüzden gereksiz uzatma "
            "veya çok uzun kod blokları yazıyorsan, 'Mimar, kodu panoya/dosyaya kaydettim' tarzı kısa "
            "bir sesli özet sun."
        )

        payload = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": konu}
            ],
            "temperature": 0.3,
            "max_tokens": 4000, 
        }

        # İsteği at
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        data = response.json()
        
        if "choices" in data and len(data["choices"]) > 0:
            full_response = data["choices"][0]["message"]["content"]
        else:
            full_response = "Claude'dan geçerli bir yanıt alınamadı."

        # Eğer yanıt aşırı uzunsa (sesli asistanı boğmamak için) sadece ilk 800 karakteri özetle okuturuz.
        # İstersen bu kısmı kaldırıp tamamını da okutabilirsin.
        if len(full_response) > 800:
            ozet = full_response[:800] + "... (Danışmanın raporunun devamı var ancak çok uzun olduğu için burada kesiyorum.)"
        else:
            ozet = full_response

        print("\n[MiniClaude] Yanıt Alındı!")
        return ozet

    except requests.exceptions.RequestException as e:
        return f"Araştırma sırasında bir bağlantı hatası oluştu: {str(e)}"
    except Exception as e:
        return f"Alt ajan çalışırken bir hata oluştu: {str(e)}"