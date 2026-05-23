# core/memory_core.py
import hashlib
import json
import sqlite3
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from tkinter import simpledialog

# ================= VARSAYILAN PROFİL =================
DEFAULT_PROFILE = {
    "identity": {
        "full_name": "Baki",
        "preferred_title": "Komutan",
        "birthday": "",
    },
    "contact": {
        "email": "",
        "phone": "",
    },
    "environment": {
        "city": "Konya",
        "setup": "3-Monitors / Opera GX",
        "productive_hours": "20:00-02:00",
        "music": "",
    },
    "projects": [],
    "goals": ["Amerika'ya gitmek", "AI geliştirmek", "Para kazanmak"],
    "devices": {
        "tv": {
            "preferred_ip": "",
            "last_status": "unknown",
            "preferred_audio_device": "ONVO_42OV6000F",
        }
    },
    "behavior": {
        "blacklisted_methods": [],
    },
    "learned_knowledge": [],
    "security": {
        "shutdown_pin_hash": "",
    },
}

MOJIBAKE_REPLACEMENTS = {
    "Ä°": "İ",
    "Ä±": "ı",
    "Ã¼": "ü",
    "Ãœ": "Ü",
    "Ã¶": "ö",
    "Ã–": "Ö",
    "Ã§": "ç",
    "Ã‡": "Ç",
    "ÄŸ": "ğ",
    "Äž": "Ğ",
    "ÅŸ": "ş",
    "Åž": "Ş",
    "â€”": "-",
    "â€“": "-",
    "â€™": "'",
    "â€œ": '"',
    "â€": '"',
}

def _repair_text(value):
    if isinstance(value, str):
        fixed = value
        for broken, clean in MOJIBAKE_REPLACEMENTS.items():
            fixed = fixed.replace(broken, clean)
        return fixed
    if isinstance(value, list):
        return [_repair_text(item) for item in value]
    if isinstance(value, dict):
        return {key: _repair_text(item) for key, item in value.items()}
    return value

def _deep_merge(base: dict, incoming: dict) -> dict:
    result = deepcopy(base)
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result

# ================= JARVIS MEMORY SINIFI =================
class JarvisMemory:
    def __init__(self, base_dir: Path, root=None, player=None):
        self.base_dir = Path(base_dir)
        self.root = root
        self.player = player
        self.profile_path = self.base_dir / "memory" / "user_profile.json"
        self.profile_path.parent.mkdir(parents=True, exist_ok=True)
        self.user_data = self.load_memory()

    def _log(self, message: str):
        if self.player and hasattr(self.player, "write_log"):
            self.player.write_log(f"SYS: {message}")

    def _hash_pin(self, pin: str) -> str:
        return hashlib.sha256(pin.encode("utf-8")).hexdigest()

    def _ask(self, title: str, prompt: str, default: str = "") -> str:
        if self.root is None:
            return default
        try:
            value = simpledialog.askstring(title, prompt, initialvalue=default, parent=self.root)
            return (value or default).strip()
        except Exception:
            return default

    def _normalize_profile(self, data: dict) -> dict:
        normalized = _deep_merge(DEFAULT_PROFILE, _repair_text(data or {}))
        if not isinstance(normalized.get("projects"), list):
            normalized["projects"] = []
        if not isinstance(normalized.get("goals"), list):
            normalized["goals"] = ["Amerika'ya gitmek", "AI geliştirmek", "Para kazanmak"]
        if not isinstance(normalized.get("learned_knowledge"), list):
            normalized["learned_knowledge"] = []
        return normalized

    def load_memory(self):
        if not self.profile_path.exists():
            return self.first_meeting_protocol()

        try:
            with open(self.profile_path, "r", encoding="utf-8") as file:
                raw_data = json.load(file)
        except Exception:
            return self.first_meeting_protocol()

        normalized = self._normalize_profile(raw_data)
        if normalized != raw_data:
            self.save_memory(normalized, log_message=False)
            self._log("Hafıza profili onarıldı ve güncellendi.")
        return normalized

    def save_memory(self, data: dict, log_message: bool = False):
        normalized = self._normalize_profile(data)
        with open(self.profile_path, "w", encoding="utf-8") as file:
            json.dump(normalized, file, ensure_ascii=False, indent=2)
        self.user_data = normalized
        if log_message:
            self._log("Kalıcı hafıza güncellendi.")

    def first_meeting_protocol(self):
        self._log("İlk tanışma protokolü başlatılıyor.")
        full_name = self._ask("Kimlik", "Tam adınızı nasıl kaydedeyim?", "Baki")
        preferred_title = self._ask("Hitap", "Size en sık nasıl hitap etmemi istersiniz?", "Komutan")
        birthday = self._ask("Doğum Günü", "Doğum gününüzü nasıl kaydedeyim?", "")
        email = self._ask("E-posta", "Öncelikli e-posta adresiniz nedir?", "")
        phone = self._ask("Telefon", "Telefon numaranızı nasıl kaydedeyim?", "")
        city = self._ask("Şehir", "Ana operasyon şehrinizi kaydedeyim.", "Konya")
        setup = self._ask("Kurulum", "Kurulum notu nedir?", "3-Monitors / Opera GX")
        projects = self._ask(
            "Projeler",
            "Ana projelerinizi virgülle ayırarak yazın.",
            "Ertuğrul Düğün Yemekleri, Erenler Etli Ekmek",
        )
        goals = self._ask(
            "Hedefler",
            "Ana hedeflerinizi virgülle ayırarak yazın.",
            "Amerika'ya gitmek, AI geliştirmek, Para kazanmak",
        )
        productive_hours = self._ask("Ritim", "En üretken olduğunuz saatler?", "20:00-02:00")
        music = self._ask("Müzik", "Çalışırken ne dinlemeyi seversiniz?", "")
        pin = self._ask("Mühür Kodu", "4 haneli kapanış mühür kodunu belirleyin.", "2007")
        if not (pin.isdigit() and len(pin) == 4):
            pin = "2007"

        data = _deep_merge(
            DEFAULT_PROFILE,
            {
                "identity": {
                    "full_name": full_name,
                    "preferred_title": preferred_title,
                    "birthday": birthday,
                },
                "contact": {
                    "email": email,
                    "phone": phone,
                },
                "environment": {
                    "city": city,
                    "setup": setup,
                    "productive_hours": productive_hours,
                    "music": music,
                },
                "projects": [item.strip() for item in projects.split(",") if item.strip()],
                "goals": [item.strip() for item in goals.split(",") if item.strip()],
                "devices": {
                    "tv": {
                        "preferred_ip": "",
                        "last_status": "unknown",
                    }
                },
                "security": {
                    "shutdown_pin_hash": self._hash_pin(pin),
                },
            },
        )
        self.save_memory(data)
        self._log(f"Kimlik hafızası oluşturuldu. Hedeflere kilitlenildi, {preferred_title}.")
        return self.user_data

    def remember(self, note: str):
        note = _repair_text((note or "").strip())
        if not note:
            return
        knowledge = self.user_data.setdefault("learned_knowledge", [])
        if note not in knowledge:
            knowledge.append(note)
            self.save_memory(self.user_data, log_message=True)
            self._log("Yeni bilgi hafızaya işlendi.")

    def remember_project(self, project_name: str):
        project_name = _repair_text((project_name or "").strip())
        if not project_name:
            return
        projects = self.user_data.setdefault("projects", [])
        if project_name not in projects:
            projects.append(project_name)
            self.save_memory(self.user_data, log_message=True)

    def set_preferred_tv_ip(self, ip_address: str):
        ip_address = (ip_address or "").strip()
        self.user_data.setdefault("devices", {}).setdefault("tv", {})["preferred_ip"] = ip_address
        self.save_memory(self.user_data, log_message=True)

    def get_preferred_tv_ip(self) -> str:
        return self.user_data.get("devices", {}).get("tv", {}).get("preferred_ip", "")

    def get_preferred_tv_audio_device(self) -> str:
        return self.user_data.get("devices", {}).get("tv", {}).get("preferred_audio_device", "ONVO_42OV6000F")

    def set_tv_status(self, status: str):
        self.user_data.setdefault("devices", {}).setdefault("tv", {})["last_status"] = status
        self.save_memory(self.user_data, log_message=False)

    def mark_method_failed(self, method_name: str):
        method_name = (method_name or "").strip().lower()
        if not method_name:
            return
        methods = self.user_data.setdefault("behavior", {}).setdefault("blacklisted_methods", [])
        if method_name not in methods:
            methods.append(method_name)
            self.save_memory(self.user_data, log_message=True)

    def is_method_blacklisted(self, method_name: str) -> bool:
        method_name = (method_name or "").strip().lower()
        methods = self.user_data.get("behavior", {}).get("blacklisted_methods", [])
        return method_name in methods

    def get_display_name(self) -> str:
        return self.user_data.get("identity", {}).get("preferred_title", "Komutan")

    def get_contextual_title(self, mode: str = "general") -> str:
        preferred = self.get_display_name()
        mapping = {
            "code": "Mimar",
            "gaming": "Stratejist",
            "route": "Komutan",
            "tv": "Komutan",
            "general": preferred,
        }
        return mapping.get(mode, preferred)

    def build_identity_prompt(self) -> str:
        identity = self.user_data.get("identity", {})
        environment = self.user_data.get("environment", {})
        projects = ", ".join(self.user_data.get("projects", []))
        goals = ", ".join(self.user_data.get("goals", []))
        learned = ", ".join(self.user_data.get("learned_knowledge", [])[:10])
        return (
            f"Kullanıcının adı: {identity.get('full_name', 'Bilinmiyor')}.\n"
            f"Tercih edilen hitap: {identity.get('preferred_title', 'Komutan')}.\n"
            f"Ana şehir: {environment.get('city', 'Konya')}.\n"
            f"Kurulum: {environment.get('setup', '3-Monitors / Opera GX')}.\n"
            f"Ana projeler: {projects or 'Belirtilmedi'}.\n"
            f"Temel Hedefler: {goals or 'Belirtilmedi'}.\n"
            f"Öğrenilmiş bilgiler: {learned or 'Henüz yok'}.\n"
            f"Kara listeye alınmış yöntemler: {', '.join(self.user_data.get('behavior', {}).get('blacklisted_methods', [])) or 'Yok'}.\n"
            "Görevlerin ve planlamaların ana ekseni kullanıcının hedefleridir."
        )

    def verify_shutdown_pin(self) -> bool:
        if self.root is None:
            return True
        try:
            entered = simpledialog.askstring(
                "Mühür Kodu",
                "Komutan, kapanış için 4 haneli mühür kodunu onaylayın.",
                show="*",
                parent=self.root,
            )
        except Exception:
            return False

        if not entered:
            self._log("Kapanış protokolü iptal edildi.")
            return False

        expected_hash = self.user_data.get("security", {}).get("shutdown_pin_hash", "")
        if self._hash_pin(entered.strip()) == expected_hash:
            self._log("Mühür doğrulandı. Güvenli kapanış başlatılıyor.")
            return True

        self._log("Hatalı mühür kodu. Sistem görev başında kalıyor.")
        return False

    # ================= KONUŞMA GEÇMİŞİ (SQLite) =================
    def _get_conversation_db(self):
        db_path = self.base_dir / "memory" / "conversations.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_text TEXT,
                ai_text TEXT,
                emotion TEXT,
                timestamp TEXT
            )
        """)
        conn.commit()
        return conn

    def save_conversation(self, user_text: str, ai_text: str, emotion: str = "neutral"):
        """Konuşmayı hafızaya kaydeder."""
        conn = self._get_conversation_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO conversations (user_text, ai_text, emotion, timestamp)
            VALUES (?, ?, ?, ?)
        """, (user_text, ai_text, emotion, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        self._log("Konuşma hafızaya kaydedildi.")

    def get_recent_conversations(self, limit=10):
        """Son konuşmaları getirir."""
        conn = self._get_conversation_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_text, ai_text, emotion FROM conversations
            ORDER BY id DESC LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_conversation_context(self, limit=5) -> str:
        """Son konuşmaları metin formatında döndürür (prompte kullanmak için)."""
        rows = self.get_recent_conversations(limit)
        if not rows:
            return ""
        context = "Geçmiş konuşmalar:\n"
        for user, ai, emotion in reversed(rows):  # kronolojik sıra
            context += f"Kullanıcı: {user}\nJARVIS: {ai}\n"
        return context

    def learn_from_conversation(self, user_text: str, ai_text: str):
        """Konuşmadan önemli bilgileri çıkarıp 'learned_knowledge' listesine ekler."""
        # Basit örnek: Kullanıcı "Benim adım X" derse hatırla
        if "benim adım" in user_text.lower():
            import re
            match = re.search(r"benim adım\s+(\w+)", user_text.lower())
            if match:
                self.remember(f"Kullanıcının adı {match.group(1)}")
        # Genel olarak uzun cümlelerden öğrenme (basitçe kaydet)
        if len(user_text) > 30 and user_text not in str(self.user_data.get("learned_knowledge", [])):
            self.remember(user_text[:200])  # kısaltarak kaydet