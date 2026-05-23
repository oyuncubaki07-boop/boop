"""
memory_manager.py — MARK XXXIX Hafıza Sistemi
============================================
Kullanıcıya dair kişisel bilgileri, projeleri, tercihleri ve ilişkileri 
uzun vadeli JSON belleğinde (long_term.json) asenkron güvenlikle (Lock) saklar.
"""

import json
import re
import sys
from datetime import datetime
from threading import Lock
from pathlib import Path


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE_DIR         = get_base_dir()
MEMORY_PATH      = BASE_DIR / "memory" / "long_term.json"
_lock            = Lock()
MAX_VALUE_LENGTH = 400


def _empty_memory() -> dict:
    return {
        "identity":      {},
        "preferences":   {},
        "projects":      {},
        "relationships": {},
        "wishes":        {},
        "notes":         {}
    }


def load_memory() -> dict:
    if not MEMORY_PATH.exists():
        return _empty_memory()

    with _lock:
        try:
            data = json.loads(MEMORY_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                base = _empty_memory()
                for key in base:
                    if key not in data:
                        data[key] = {}
                return data
            return _empty_memory()
        except Exception as e:
            print(f"SYS: [Hafıza] ⚠️ Yükleme hatası: {e}")
            return _empty_memory()


def save_memory(memory: dict) -> None:
    if not isinstance(memory, dict):
        return
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        MEMORY_PATH.write_text(
            json.dumps(memory, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )


def _truncate_value(val: str) -> str:
    if isinstance(val, str) and len(val) > MAX_VALUE_LENGTH:
        return val[:MAX_VALUE_LENGTH].rstrip() + "…"
    return val


def _recursive_update(target: dict, updates: dict) -> bool:
    changed = False
    for key, value in updates.items():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue

        if isinstance(value, dict) and "value" not in value:
            if key not in target or not isinstance(target[key], dict):
                target[key] = {}
                changed = True
            if _recursive_update(target[key], value):
                changed = True
        else:
            if isinstance(value, dict) and "value" in value:
                new_val = _truncate_value(str(value["value"]))
            else:
                new_val = _truncate_value(str(value))

            entry    = {"value": new_val, "updated": datetime.now().strftime("%Y-%m-%d")}
            existing = target.get(key, {})
            if not isinstance(existing, dict) or existing.get("value") != new_val:
                target[key] = entry
                changed = True

    return changed


def update_memory(memory_update: dict) -> dict:
    if not isinstance(memory_update, dict) or not memory_update:
        return load_memory()

    memory = load_memory()
    if _recursive_update(memory, memory_update):
        save_memory(memory)
        print(f"SYS: [Hafıza] 💾 Kaydedildi: {list(memory_update.keys())}")
    return memory


def should_extract_memory(user_text: str, jarvis_text: str, api_key: str) -> bool:
    """
    Stage 1: Hızlı YES/NO kontrolü.
    Diyalogda kalıcı belleğe alınmaya değer bir bilgi var mı?
    """
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        combined = f"User: {user_text[:300]}\nJarvis: {jarvis_text[:200]}"

        check = model.generate_content(
            f"Does this conversation contain ANY of the following?\n"
            f"- Personal facts (name, age, city, job, birthday, nationality)\n"
            f"- Preferences or favorites (food, color, music, sport, game, film, book, etc.)\n"
            f"- Active projects or goals the user is working on\n"
            f"- People in the user's life (friends, family, partner, colleagues)\n"
            f"- Things the user wants to do or buy in the future\n"
            f"- Any other fact worth remembering long-term\n\n"
            f"Reply only YES or NO.\n\nConversation:\n{combined}"
        )
        return "YES" in check.text.upper()
    except Exception as e:
        print(f"SYS: [Hafıza] ⚠️ Stage1 kontrolü başarısız: {e}")
        return False


def extract_memory(user_text: str, jarvis_text: str, api_key: str) -> dict:
    """
    Stage 2: Detaylı çıkarım.
    JSON formatında belleğe işlenecek verileri çeker.
    """
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        combined = f"User: {user_text[:500]}\nJarvis: {jarvis_text[:300]}"

        response = model.generate_content(
            f"Extract ALL memorable personal facts from this conversation. Any language.\n"
            f"Return ONLY valid JSON. Use {{}} if truly nothing is worth saving.\n\n"
            f"Category guide:\n"
            f"  identity      → name, age, birthday, city, country, job, school, nationality, language\n"
            f"  preferences   → ANY favorite or preferred thing:\n"
            f"                  favorite_food, favorite_color, favorite_music, favorite_film,\n"
            f"                  favorite_game, favorite_sport, favorite_book, favorite_artist,\n"
            f"                  favorite_country, hobbies, interests, dislikes, etc.\n"
            f"  projects      → projects being built, ongoing work, goals, ideas in progress\n"
            f"                  (e.g. mark_xxxix: 'Building a JARVIS-like AI assistant')\n"
            f"  relationships → people mentioned: friends, family, partner, colleagues\n"
            f"                  (e.g. best_friend_ali: 'Best friend, met in university')\n"
            f"  wishes        → future plans, things to buy, travel plans, dreams\n"
            f"  notes         → anything else worth remembering (habits, schedule, etc.)\n\n"
            f"IMPORTANT:\n"
            f"- Be LIBERAL: if something MIGHT be worth remembering, include it.\n"
            f"- Extract from BOTH user and Jarvis turns.\n"
            f"- Skip: weather, reminders, search results, one-time commands.\n"
            f"- Use concise values in Turkish (or conversation language).\n\n"
            f"Format:\n"
            f'{{"identity":{{"name":{{"value":"Ali"}}}},\n'
            f' "preferences":{{"favorite_color":{{"value":"Mavi"}}, "hobby":{{"value":"Oyun oynamak"}}}},\n'
            f' "projects":{{"mark_xxxix":{{"value":"Windows üzerinde çalışan yapay zeka asistanı"}}}},\n'
            f' "relationships":{{"friend_yusuf":{{"value":"Yakın arkadaş"}}}},\n'
            f' "wishes":{{"buy_guitar":{{"value":"Akustik gitar almak istiyor"}}}},\n'
            f' "notes":{{"works_at_night":{{"value":"Genellikle gece geç saatlerde çalışır"}}}}}}\n\n'
            f"Conversation:\n{combined}\n\nJSON:"
        )
        raw = response.text.strip()

        # DÜZELTİLEN SATIR (188): ```json veya ``` işaretlerini temizle
        raw = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()

        # JSON olarak ayrıştırmayı dene
        try:
            extracted = json.loads(raw)
            return extracted if isinstance(extracted, dict) else {}
        except json.JSONDecodeError:
            print("SYS: [Hafıza] ⚠️ JSON parse hatası, ham çıktı:", raw[:100])
            return {}

    except Exception as e:
        print(f"SYS: [Hafıza] ⚠️ Bellek çıkarımı başarısız: {e}")
        return {}


def format_memory_for_prompt(memory: dict) -> str:
    """
    Belleği prompt'a eklenebilecek metne dönüştürür.
    (main.py'nin import ettiği fonksiyon)
    """
    if not memory:
        return ""
    lines = []
    for category, items in memory.items():
        if not items:
            continue
        lines.append(f"--- {category.upper()} ---")
        for key, info in items.items():
            if isinstance(info, dict) and "value" in info:
                lines.append(f"- {key}: {info['value']}")
            elif isinstance(info, str):
                lines.append(f"- {key}: {info}")
        lines.append("")
    return "\n".join(lines).strip()