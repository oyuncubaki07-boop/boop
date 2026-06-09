"""

J.A.R.V.I.S. 2.0 — BULUT ETKİLEŞİM SÜRÜMÜ (Mükemmel & Hızlı)

=================================================

Entegre Canlı Ruh Hali ve Hayalet Düğüm Mimarisi (FastAPI, WebSockets & Three.js)

"""



from __future__ import annotations

# J.A.R.V.I.S. Super Repair Protocol - Bootstrap
import sys
import os
from pathlib import Path as _Path
_project_root = _Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))
try:
    import bootstrap
except ImportError:
    pass  # bootstrap.py not found, continuing without path fixes



import json
import asyncio
if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass
import time
import uuid
import sqlite3
import hashlib
import string
import sys
import os
import base64
import logging
from pathlib import Path
import random
import traceback
from datetime import datetime, timedelta
from contextlib import asynccontextmanager, suppress
from typing import Any, Dict, List, Optional, Set

# UTF-8 support for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import uvicorn
import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request

from fastapi.responses import HTMLResponse, JSONResponse, FileResponse

from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).resolve().parent.parent / "logs" / "server.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Set UTF-8 for file handler
for handler in logger.handlers:
    if isinstance(handler, logging.FileHandler):
        handler.setEncoding('utf-8')

# Proje kök dizinini sys.path'e ekle
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Config caching
_config_cache = None
_config_cache_time = 0

try:
    from core.config_loader import load_config as _load_config_impl, reload_config as _reload_config_impl
except ImportError:
    def _load_config_impl() -> dict:
        return {}
    def _reload_config_impl() -> dict:
        return {}

def load_config() -> dict:
    global _config_cache, _config_cache_time
    current_time = time.time()
    if _config_cache is None or (current_time - _config_cache_time) > 300:
        _config_cache = _load_config_impl()
        _config_cache_time = current_time
    return _config_cache

def reload_config() -> dict:
    global _config_cache, _config_cache_time
    _config_cache = None
    _config_cache_time = 0
    return _reload_config_impl()

CONFIG_CACHE = load_config()
WEB_PORT = 3013
USER_SESSIONS = {}
VOICE_CLIENT_PROCESS = None
CHAT_LOGS_FILE = Path(__file__).resolve().parent.parent / "logs" / "global_chat_logs.txt"

import string

# --- WEB ADMIN DATABASE (ENTERPRISE CORE) ---
class WebAdminDB:
    def __init__(self, db_name="jarvis_web_admin.db"):
        PERSIST_DIR = os.getenv("JARVIS_PERSISTENT_DIR", "")
        if PERSIST_DIR:
            self.db_path = Path(os.path.join(PERSIST_DIR, db_name))
        else:
            self.db_path = Path(__file__).resolve().parent.parent / "memory" / db_name
        self._init_db()

    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS admin_users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        role TEXT NOT NULL
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS admin_audit_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        username TEXT NOT NULL,
                        action TEXT NOT NULL,
                        ip_address TEXT NOT NULL
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_activities (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        session_id TEXT NOT NULL,
                        ip_address TEXT NOT NULL,
                        activity TEXT NOT NULL
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS suspicious_activities (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        ip_address TEXT NOT NULL,
                        session_id TEXT NOT NULL,
                        reason TEXT NOT NULL,
                        risk_score INTEGER NOT NULL
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS public_users (
                        ip_address TEXT PRIMARY KEY,
                        referral_code TEXT UNIQUE NOT NULL,
                        daily_count INTEGER DEFAULT 0,
                        bonus_questions INTEGER DEFAULT 0,
                        last_reset TEXT NOT NULL,
                        invited_by TEXT,
                        has_flower INTEGER DEFAULT 0,
                        has_coffee INTEGER DEFAULT 0,
                        has_star INTEGER DEFAULT 0
                    )
                """)
                conn.commit()

                # Seed default Super Admin user (baki / 3131626242)
                cursor.execute("SELECT COUNT(*) FROM admin_users")
                if cursor.fetchone()[0] == 0:
                    pwd_hash = hashlib.sha256("3131626242".encode('utf-8')).hexdigest()
                    cursor.execute("""
                        INSERT INTO admin_users (username, password_hash, role)
                        VALUES (?, ?, ?)
                    """, ("baki", pwd_hash, "Super Admin"))
                    conn.commit()
            logger.info(f"[WebAdminDB] Database initialized successfully: {self.db_path}")
        except Exception as e:
            logger.error(f"[WebAdminDB] Initialization error: {e}")

    def generate_referral_code(self) -> str:
        chars = string.ascii_lowercase + string.digits
        return ''.join(random.choice(chars) for _ in range(8))

    def get_or_create_public_user(self, ip: str) -> dict:
        today = datetime.now().strftime("%Y-%m-%d")
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM public_users WHERE ip_address = ?", (ip,))
                row = cursor.fetchone()
                if row:
                    user = dict(row)
                    # Check daily count reset
                    if user["last_reset"] != today:
                        cursor.execute("""
                            UPDATE public_users 
                            SET daily_count = 0, last_reset = ? 
                            WHERE ip_address = ?
                        """, (today, ip))
                        conn.commit()
                        user["daily_count"] = 0
                        user["last_reset"] = today
                    return user
                else:
                    # Create new user
                    ref_code = self.generate_referral_code()
                    # Ensure uniqueness
                    for _ in range(10):
                        cursor.execute("SELECT COUNT(*) FROM public_users WHERE referral_code = ?", (ref_code,))
                        if cursor.fetchone()[0] == 0:
                            break
                        ref_code = self.generate_referral_code()
                    
                    cursor.execute("""
                        INSERT INTO public_users (ip_address, referral_code, daily_count, bonus_questions, last_reset)
                        VALUES (?, ?, 0, 0, ?)
                    """, (ip, ref_code, today))
                    conn.commit()
                    return {
                        "ip_address": ip,
                        "referral_code": ref_code,
                        "daily_count": 0,
                        "bonus_questions": 0,
                        "last_reset": today,
                        "invited_by": None,
                        "has_flower": 0,
                        "has_coffee": 0,
                        "has_star": 0
                    }
        except Exception as e:
            logger.error(f"[WebAdminDB] Error get_or_create_public_user: {e}")
            return {}

    def increment_daily_count(self, ip: str) -> int:
        today = datetime.now().strftime("%Y-%m-%d")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT daily_count, last_reset FROM public_users WHERE ip_address = ?", (ip,))
                row = cursor.fetchone()
                if row:
                    current_count, last_reset = row
                    new_count = current_count + 1
                    if last_reset != today:
                        new_count = 1
                        cursor.execute("""
                            UPDATE public_users 
                            SET daily_count = ?, last_reset = ? 
                            WHERE ip_address = ?
                        """, (new_count, today, ip))
                    else:
                        cursor.execute("""
                            UPDATE public_users 
                            SET daily_count = ? 
                            WHERE ip_address = ?
                        """, (new_count, ip))
                    conn.commit()
                    return new_count
        except Exception as e:
            logger.error(f"[WebAdminDB] Error increment_daily_count: {e}")
        return 0

    def add_referral_invite(self, referral_code: str, invited_ip: str) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT ip_address FROM public_users WHERE referral_code = ?", (referral_code,))
                owner = cursor.fetchone()
                if not owner:
                    return False
                owner_ip = owner[0]
                
                if owner_ip == invited_ip:
                    return False
                
                self.get_or_create_public_user(invited_ip)
                cursor.execute("SELECT invited_by FROM public_users WHERE ip_address = ?", (invited_ip,))
                guest_invited_by = cursor.fetchone()[0]
                if guest_invited_by:
                    return False
                
                cursor.execute("UPDATE public_users SET invited_by = ? WHERE ip_address = ?", (referral_code, invited_ip))
                cursor.execute("""
                    UPDATE public_users 
                    SET bonus_questions = bonus_questions + 10, has_flower = 1
                    WHERE ip_address = ?
                """, (owner_ip,))
                conn.commit()
                
                self.log_activity("referral_system", invited_ip, f"Referans kodu kullanildi: {referral_code} (Sahip: {owner_ip})")
                return True
        except Exception as e:
            logger.error(f"[WebAdminDB] Error add_referral_invite: {e}")
        return False

    def get_top_inviters(self) -> list:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT o.ip_address, COUNT(g.ip_address) as invite_count, o.bonus_questions, o.has_flower
                    FROM public_users o
                    LEFT JOIN public_users g ON g.invited_by = o.referral_code
                    GROUP BY o.ip_address
                    HAVING invite_count > 0
                    ORDER BY invite_count DESC
                    LIMIT 20
                """)
                return [{"ip": r[0], "count": r[1], "bonus": r[2], "has_flower": bool(r[3])} for r in cursor.fetchall()]
        except Exception as e:
            logger.error(f"[WebAdminDB] Error get_top_inviters: {e}")
            return []

    def reset_ip_limit(self, ip: str) -> bool:
        today = datetime.now().strftime("%Y-%m-%d")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE public_users 
                    SET daily_count = 0, bonus_questions = bonus_questions + 10, last_reset = ? 
                    WHERE ip_address = ?
                """, (today, ip))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"[WebAdminDB] Error reset_ip_limit: {e}")
        return False

    def log_audit(self, username: str, action: str, ip: str):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO admin_audit_logs (timestamp, username, action, ip_address)
                    VALUES (?, ?, ?, ?)
                """, (now, username, action, ip))
                conn.commit()
        except Exception as e:
            logger.error(f"[WebAdminDB] Error log_audit: {e}")

    def log_activity(self, session_id: str, ip: str, activity: str):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO user_activities (timestamp, session_id, ip_address, activity)
                    VALUES (?, ?, ?, ?)
                """, (now, session_id, ip, activity))
                conn.commit()
        except Exception as e:
            logger.error(f"[WebAdminDB] Error log_activity: {e}")

    def log_suspicious_activity(self, ip: str, session_id: str, reason: str, risk_score: int):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO suspicious_activities (timestamp, ip_address, session_id, reason, risk_score)
                    VALUES (?, ?, ?, ?, ?)
                """, (now, ip, session_id, reason, risk_score))
                conn.commit()
        except Exception as e:
            logger.error(f"[WebAdminDB] Error log_suspicious_activity: {e}")

    def get_audit_logs(self, limit=200) -> list:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT timestamp, username, action, ip_address FROM admin_audit_logs ORDER BY id DESC LIMIT ?", (limit,))
                return [{"time": r[0], "admin": r[1], "action": r[2], "ip": r[3]} for r in cursor.fetchall()]
        except Exception as e:
            logger.error(f"[WebAdminDB] Error get_audit_logs: {e}")
            return []

    def get_user_timeline(self, limit=200) -> list:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT timestamp, session_id, ip_address, activity FROM user_activities ORDER BY id DESC LIMIT ?", (limit,))
                return [{"time": r[0], "session_id": r[1], "ip": r[2], "activity": r[3]} for r in cursor.fetchall()]
        except Exception as e:
            logger.error(f"[WebAdminDB] Error get_user_timeline: {e}")
            return []

    def get_suspicious_activities(self, limit=100) -> list:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT timestamp, ip_address, session_id, reason, risk_score FROM suspicious_activities ORDER BY id DESC LIMIT ?", (limit,))
                return [{"time": r[0], "ip": r[1], "session_id": r[2], "reason": r[3], "risk_score": r[4]} for r in cursor.fetchall()]
        except Exception as e:
            logger.error(f"[WebAdminDB] Error get_suspicious_activities: {e}")
            return []

    def clear_audit_logs(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM admin_audit_logs")
                conn.commit()
        except Exception as e:
            logger.error(f"[WebAdminDB] Error clear_audit_logs: {e}")

    def clear_timeline(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM user_activities")
                conn.commit()
        except Exception as e:
            logger.error(f"[WebAdminDB] Error clear_timeline: {e}")

    def clear_security_logs(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM suspicious_activities")
                conn.commit()
        except Exception as e:
            logger.error(f"[WebAdminDB] Error clear_security_logs: {e}")

    def get_admin_users(self) -> list:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, username, role FROM admin_users ORDER BY username")
                return [{"id": r[0], "username": r[1], "role": r[2]} for r in cursor.fetchall()]
        except Exception as e:
            logger.error(f"[WebAdminDB] Error get_admin_users: {e}")
            return []

    def add_admin_user(self, username: str, password_hash: str, role: str) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO admin_users (username, password_hash, role)
                    VALUES (?, ?, ?)
                """, (username, password_hash, role))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"[WebAdminDB] Error add_admin_user: {e}")
            return False

    def delete_admin_user(self, username: str) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM admin_users WHERE username = ?", (username,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"[WebAdminDB] Error delete_admin_user: {e}")
            return False

    def verify_user(self, username: str, password_plain: str) -> Optional[dict]:
        pwd_hash = hashlib.sha256(password_plain.encode('utf-8')).hexdigest()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT username, role FROM admin_users WHERE username = ? AND password_hash = ?", (username, pwd_hash))
                row = cursor.fetchone()
                if row:
                    return {"username": row[0], "role": row[1]}
        except Exception as e:
            logger.error(f"[WebAdminDB] Error verify_user: {e}")
        return None

web_admin_db = WebAdminDB()

class SecurityFirewall:
    def __init__(self):
        self.ip_tracker = {}
        self.cooldown_seconds = 1.0
        
        # Extended security metrics
        self.request_timestamps = {}   # ip -> list of float timestamps
        self.last_prompts = {}         # session_id -> list of (prompt, timestamp)
        self.notfound_scans = {}       # ip -> list of float timestamps
        self.risk_scores = {}          # ip -> int score

    def check_request(self, ip: str) -> bool:
        current_time = time.time()
        self.ip_tracker = {k: v for k, v in self.ip_tracker.items() if current_time - v < self.cooldown_seconds}
        if ip in self.ip_tracker:
            return False
        self.ip_tracker[ip] = current_time
        return True

    def track_request_rate(self, ip: str, session_id: str) -> int:
        current_time = time.time()
        if ip not in self.request_timestamps:
            self.request_timestamps[ip] = []
        self.request_timestamps[ip] = [t for t in self.request_timestamps[ip] if current_time - t <= 1.0]
        self.request_timestamps[ip].append(current_time)
        rate = len(self.request_timestamps[ip])
        if rate >= 50:
            self.trigger_suspicious_activity(ip, session_id, "Yuksek istek hizi (Saniyede 50+ istek)", 40)
        return rate

    def track_prompt_spam(self, session_id: str, ip: str, prompt: str):
        current_time = time.time()
        if session_id not in self.last_prompts:
            self.last_prompts[session_id] = []
        self.last_prompts[session_id] = [p for p in self.last_prompts[session_id] if current_time - p[1] <= 15.0]
        self.last_prompts[session_id].append((prompt, current_time))
        same_prompts = [p for p in self.last_prompts[session_id] if p[0] == prompt]
        if len(same_prompts) >= 3:
            self.trigger_suspicious_activity(ip, session_id, "Spam mesaj (Ayni mesajin tekrarlanmasi)", 20)

    def track_404_scan(self, ip: str, session_id: str):
        current_time = time.time()
        if ip not in self.notfound_scans:
            self.notfound_scans[ip] = []
        self.notfound_scans[ip] = [t for t in self.notfound_scans[ip] if current_time - t <= 30.0]
        self.notfound_scans[ip].append(current_time)
        scan_count = len(self.notfound_scans[ip])
        if scan_count >= 10:
            self.trigger_suspicious_activity(ip, session_id, "Surekli endpoint taramasi (404 tespiti)", 35)

    def trigger_suspicious_activity(self, ip: str, session_id: str, reason: str, risk_points: int):
        current_score = self.risk_scores.get(ip, 0)
        new_score = min(current_score + risk_points, 100)
        self.risk_scores[ip] = new_score
        try:
            web_admin_db.log_suspicious_activity(ip, session_id, reason, new_score)
        except Exception as e:
            logger.error(f"[Firewall] Failed to log suspicious activity: {e}")

    def get_risk_score(self, ip: str) -> int:
        return self.risk_scores.get(ip, 0)

firewall = SecurityFirewall()



# --- KALICI HAFIZA MOTORU ---

class MemoryEngine:
    def __init__(self):
        # Memory engine now operates via the memory sandbox using SQLite database
        logger.info("[MemoryEngine] Memory engine initialized in database mode (sandbox)")

    def extract_personal_facts(self, text: str) -> dict:
        import re
        facts = {}
        text_lower = text.lower().strip()
        
        # Name matching (Turkish & English)
        name_match = re.search(r"\badım\s+([a-zçıüşöğ]+)", text_lower) or re.search(r"\bismim\s+([a-zçıüşöğ]+)", text_lower)
        if name_match:
            facts["name"] = name_match.group(1).capitalize()
        else:
            name_match_en = re.search(r"\bmy name is\s+([a-z\s]+)", text_lower)
            if name_match_en:
                facts["name"] = name_match_en.group(1).title().strip()
                
        # Favorites (Turkish)
        fav_tr = re.search(r"en sevdiğim\s+(renk|yemek|oyun|şarkı|film|müzik|spor|hobi)\s+(?:yok|değil|şudur)?\s*([a-zçıüşöğ\s]+)", text_lower)
        if fav_tr:
            category = fav_tr.group(1)
            val = fav_tr.group(2).strip()
            cat_map = {"renk": "favorite_color", "yemek": "favorite_food", "oyun": "favorite_game", 
                       "şarkı": "favorite_song", "film": "favorite_movie", "müzik": "favorite_music", 
                       "spor": "favorite_sport", "hobi": "hobby"}
            if len(val) > 1:
                facts[cat_map[category]] = val
                
        # Favorites (English)
        fav_en = re.search(r"my favorite\s+(color|food|game|music|movie|film|sport|hobby)\s+is\s+([a-z\s]+)", text_lower)
        if fav_en:
            category = fav_en.group(1)
            val = fav_en.group(2).strip()
            key = f"favorite_{category}" if category != "hobby" else "hobby"
            if len(val) > 1:
                facts[key] = val

        # Relocation & Year (English & Turkish)
        move_en = re.search(r"i am moving to\s+([a-z\s]+)\s+in\s+([0-9]{4})", text_lower)
        if move_en:
            facts["relocation"] = f"Moving to {move_en.group(1).title().strip()} in {move_en.group(2)}"
        
        move_tr = re.search(r"([0-9]{4})\s+yılında\s+([a-zçıüşöğ]+)(?:'ye|'ya|'a|'e|'ye|'ya)?\s+taşınıyorum", text_lower)
        if move_tr:
            facts["relocation"] = f"Moving to {move_tr.group(2).capitalize()} in {move_tr.group(1)}"
        else:
            move_tr2 = re.search(r"([a-zçıüşöğ]+)(?:'ye|'ya|'a|'e|'ye|'ya)?\s+([0-9]{4})\s+yılında\s+taşınıyorum", text_lower)
            if move_tr2:
                facts["relocation"] = f"Moving to {move_tr2.group(1).capitalize()} in {move_tr2.group(2)}"

        # General color and food fallbacks (Turkish)
        color_tr = re.search(r"en sevdiğim renk\s+([a-zçıüşöğ]+)", text_lower)
        if color_tr:
            facts["favorite_color"] = color_tr.group(1)

        food_tr = re.search(r"en sevdiğim yemek\s+([a-zçıüşöğ]+)", text_lower)
        if food_tr:
            facts["favorite_food"] = food_tr.group(1)
            
        return facts

    def save_learning(self, user_input: str):
        try:
            if len(user_input.split()) > 1:
                from core.memory_sandbox import get_learned_facts, save_learned_facts, save_memory
                
                # Update learned_facts
                learned_facts = get_learned_facts(caller="web.server")
                learned_facts.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "data": user_input
                })
                if len(learned_facts) > 50:
                    learned_facts = learned_facts[-50:]
                
                save_learned_facts(learned_facts, caller="web.server")
                
                # UPGRADE C: Entity extraction and user profile update
                extracted = self.extract_personal_facts(user_input)
                if extracted:
                    for k, v in extracted.items():
                        category = "identity" if k in ("name", "relocation") else "preferences"
                        key = "user_name" if k == "name" else k
                        save_memory(category, key, v, caller="web.server")
                    print(f"[DeepMemory] Extracted & Saved Profile Facts to SQLite: {extracted}")
        except Exception as e:
            print(f"[MemoryEngine Error] {e}")

    def get_user_profile(self) -> dict:
        try:
            from core.memory_sandbox import get_profile_memories
            return get_profile_memories(caller="web.server")
        except Exception as e:
            logger.error(f"[MemoryEngine Error] Failed to read user profile: {e}")
            return {}

    def get_recent_memories(self) -> str:
        try:
            from core.memory_sandbox import get_learned_facts
            facts = [item["data"] for item in get_learned_facts(caller="web.server")[-3:]] 
            return " | ".join(facts) if facts else ""
        except Exception as e:
            logger.error(f"[MemoryEngine Error] Failed to read recent memories: {e}")
            return ""

    async def async_update_memory_with_llm(self, user_input: str, assistant_output: str):
        """
        Kullanıcı girdisini ve asistan yanıtını arka planda Groq kullanarak analiz eder,
        kullanıcıya dair yeni kalıcı bilgileri çıkarır ve hafıza veritabanına yazar.
        """
        config_data = load_config()
        groq_key = config_data.get("groq_api_key")
        if not groq_key or not user_input or not assistant_output:
            return

        # Çok kısa girdi ve selamlaşmaları süz
        if len(user_input.split()) < 3:
            return

        instruction = (
            "Sen J.A.R.V.I.S. Nöral Hafıza Modülüsün. Görevin, verilen kullanıcı girdisi ve asistan yanıtından, "
            "kullanıcının adı, takımı, mesleği, hobileri, sevdikleri/sevmedikleri, kişisel tercihleri veya geleceğe yönelik planları "
            "gibi kalıcı/önemli profilleme bilgilerini yakalamaktır.\n\n"
            "Kurallar:\n"
            "1. Yalnızca kalıcı/önemli bilgileri çıkar. 'Nasılsın' gibi anlık veya geçici ifadeleri çıkarma.\n"
            "2. Çıktıyı SADECE geçerli bir düz JSON nesnesi olarak ver. Hiçbir markdown (` ```json `), açıklama veya ek metin ekleme.\n"
            "3. Eğer yeni bir bilgi yoksa sadece boş bir süslü parantez '{}' döndür.\n"
            "4. Türkçe anahtarlar ve değerler kullanmaya özen göster (örn: {\"sevdigi_spor\": \"futbol\"}).\n\n"
            "Örnek girdi: 'Ben bilgisayar mühendisiyim ve kahveyi çok severim.'\n"
            "Örnek çıktı: {\"meslek\": \"Bilgisayar Mühendisi\", \"sevdigi_icecek\": \"Kahve\"}"
        )

        prompt = f"Kullanıcı Mesajı: '{user_input}'\nAsistan Yanıtı: '{assistant_output}'"
        
        groq_model = config_data.get("ai_council", {}).get("models", {}).get("groq", "llama-3.3-70b-versatile")
        if not groq_model:
            groq_model = "llama-3.3-70b-versatile"
            
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
        payload = {
            "model": groq_model,
            "messages": [
                {"role": "system", "content": instruction},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 150
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                if response.status_code == 200:
                    result = response.json()
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    if not content or content == "{}":
                        return
                    
                    # Markdown kod bloklarını temizle
                    if content.startswith("```"):
                        lines = content.splitlines()
                        if len(lines) >= 3:
                            content = "\n".join(lines[1:-1]).strip()
                        else:
                            content = content.replace("```json", "").replace("```", "").strip()
                    
                    try:
                        new_facts = json.loads(content)
                        if isinstance(new_facts, dict) and new_facts:
                            from core.memory_sandbox import save_memory
                            for k, v in new_facts.items():
                                category = "identity" if k in ("name", "relocation", "meslek") else "preferences"
                                key = "user_name" if k == "name" else k
                                save_memory(category, key, v, caller="web.server")
                            logger.info(f"[SemanticMemory] Kalıcı hafıza arka planda veritabanında güncellendi: {new_facts}")
                    except json.JSONDecodeError:
                        logger.debug(f"[SemanticMemory] JSON decode failed for content: {content}")
        except Exception as e:
            logger.error(f"[SemanticMemory Error] Arka plan hafıza analizi başarısız: {e}")

memory_engine = MemoryEngine()



# --- SİSTEM İSTATİSTİKLERİ ---

def get_system_stats():

    try:

        import psutil

        cpu = psutil.cpu_percent()

        ram = psutil.virtual_memory().percent

        disk = psutil.disk_usage('/').percent

    except:

        cpu, ram, disk = 23.4, 45.2, 57.1

    

    # Update global telemetry cache

    STATE["telemetry"]["cpu"] = cpu

    STATE["telemetry"]["ram"] = ram

    

    return {

        "cpu": cpu,

        "ram": ram,

        "disk": disk,

        "temperature": STATE["telemetry"].get("temp", random.randint(42, 54)),

        "tablet_status": "ÇEVRİMİÇİ" if (time.time() - STATE["telemetry"].get("last_update", 0) < 15) else "ÇEVRİMDIŞI"

    }



# --- RUH HALİ MOTORU ---

def analyze_sentiment(text: str) -> Dict[str, Any]:

    raw = (text or "").strip()

    lower = raw.lower()



    lexicon = {

        "urgent": ["acil", "hemen", "hızlı", "critical", "urgent", "asap", "emergency", "now", "quick", "fast", "saniyede"],

        "angry": ["kızgın", "kötü", "bozuk", "çalışmıyor", "berbat", "angry", "mad", "furious", "annoyed", "rage", "hate", "wtf", "broken", "useless", "stupid"],

        "happy": ["mutlu", "harika", "güzel", "iyi", "süper", "muhteşem", "happy", "great", "awesome", "love", "nice", "cool", "amazing", "brilliant", "perfect", "win"],

        "calm": ["sakin", "yavaş", "huzurlu", "dinlendirici", "calm", "relaxed", "sleepy", "chill", "slow", "quiet", "peace", "peaceful", "soft", "easy"],

        "sad": ["üzgün", "mutsuz", "kırgın", "ağlama", "sad", "unhappy", "depressed", "lonely", "sorry"],

        "curious": ["neden", "nasıl", "kim", "nerede", "ne zaman", "why", "how", "what", "explore", "learn", "discover", "explain", "investigate", "search", "think"]

    }



    scores = {k: 0.0 for k in lexicon.keys()}

    scores["neutral"] = 0.1



    words = lower.replace("?", " ? ").replace("!", " ! ").split()

    word_count = max(1, len(words))



    for mood, terms in lexicon.items():

        for term in terms:

            if term in lower:

                scores[mood] += 1.2



    exclamations = raw.count("!")

    questions = raw.count("?")

    caps_ratio = 0.0

    alpha_chars = [c for c in raw if c.isalpha()]

    if alpha_chars:

        caps_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)



    if exclamations:

        scores["urgent"] += 0.25 * exclamations

        scores["angry"] += 0.15 * exclamations

        scores["happy"] += 0.10 * exclamations



    if questions:

        scores["curious"] += 0.20 * questions



    if caps_ratio > 0.45 and len(raw) >= 8:

        scores["urgent"] += 0.90

        scores["angry"] += 0.55



    mood_code = max(scores.items(), key=lambda item: item[1])[0]

    if scores[mood_code] <= 0.25:

        mood_code = "neutral"



    intensity = scores[mood_code] / max(1.0, (word_count / 5.0))

    intensity = max(0.15, min(1.0, intensity))



    # Mood presets for Three.js animations

    mood_presets = {

        "urgent":   {"rot": 2.35, "wave": 1.65, "pulse": 1.00, "colorA": "#ff3b30", "colorB": "#ff9f0a", "glow": 1.55},

        "angry":    {"rot": 1.95, "wave": 1.35, "pulse": 0.90, "colorA": "#ff1744", "colorB": "#b71c1c", "glow": 1.40},

        "happy":    {"rot": 0.95, "wave": 0.75, "pulse": 0.72, "colorA": "#ffd60a", "colorB": "#34c759", "glow": 1.05},

        "calm":     {"rot": 0.42, "wave": 0.45, "pulse": 0.40, "colorA": "#4dd0e1", "colorB": "#00bcd4", "glow": 0.88},

        "sad":      {"rot": 0.15, "wave": 0.20, "pulse": 0.30, "colorA": "#4466aa", "colorB": "#1e3c72", "glow": 0.50},

        "curious":  {"rot": 0.82, "wave": 0.90, "pulse": 0.58, "colorA": "#7c4dff", "colorB": "#29b6f6", "glow": 1.10},

        "neutral":  {"rot": 0.65, "wave": 0.62, "pulse": 0.30, "colorA": "#9ad9ff", "colorB": "#6aa9ff", "glow": 0.96},

    }



    return {

        "mood_code": mood_code,

        "intensity": round(intensity, 3),

        "effects": mood_presets[mood_code],

        "ts": time.time()

    }



# --- GLOBAL STATISTICS COUNTERS ---
STATS_TOTAL_API_CALLS = 0
STATS_ERROR_COUNT = 0

# --- GLOBAL STATE VE BAĞLANTI YÖNETİCİSİ ---

STATE = {

    "telemetry": {

        "battery": 100,

        "cpu": 0.0,

        "ram": 0.0,

        "temp": 45.0,

        "charging": False,

        "audio_level": 0.0,

        "last_update": time.time()

    },

    "last_mood": {

        "mood_code": "neutral",

        "intensity": 0.25,

        "ts": time.time()

    }

}



class ConnectionManager:

    def __init__(self) -> None:

        self._chat_clients: Set[WebSocket] = set()

        self._lock = asyncio.Lock()



    async def connect(self, websocket: WebSocket) -> None:

        await websocket.accept()

        async with self._lock:

            self._chat_clients.add(websocket)



    async def disconnect(self, websocket: WebSocket) -> None:

        async with self._lock:

            self._chat_clients.discard(websocket)



    async def send_json(self, websocket: WebSocket, payload: Dict[str, Any]) -> None:

        await websocket.send_json(payload)



    async def broadcast(self, payload: Dict[str, Any]) -> None:

        async with self._lock:

            clients = list(self._chat_clients)

        for ws in clients:

            try:

                await ws.send_json(payload)

            except Exception:

                pass



    async def client_count(self) -> int:

        async with self._lock:

            return len(self._chat_clients)



manager = ConnectionManager()

camera_viewers: Set[WebSocket] = set()



# --- HAYALET DÜĞÜM MOTORU ---

def build_system_ghost_node() -> Dict[str, Any]:

    telemetry = STATE.get("telemetry", {}) or {}

    battery = telemetry.get("battery")

    cpu = telemetry.get("cpu")

    ram = telemetry.get("ram")

    temp = telemetry.get("temp")



    candidates = []



    if battery is not None and battery < 20:

        candidates.append({

            "kind": "warning",

            "title": "Power Drift Detected",

            "body": f"Termux battery is at {battery:.0f}%. Shall I dim the screen and lower the frame load?",

            "priority": 1.0,

        })



    if cpu is not None and cpu > 85:

        candidates.append({

            "kind": "warning",

            "title": "CPU Pressure Rising",

            "body": f"System CPU is at {cpu:.0f}%. I can reduce particle density and background effects.",

            "priority": 0.95,

        })



    if ram is not None and ram > 85:

        candidates.append({

            "kind": "warning",

            "title": "Memory Saturation",

            "body": f"System RAM is at {ram:.0f}%. I can collapse inactive UI clusters now.",

            "priority": 0.95,

        })



    if temp is not None and temp > 60:
        candidates.append({
            "kind": "warning",
            "title": "Thermal Spike",
            "body": f"Device temperature is {temp:.1f}°C. Cooling mode would be wise.",
            "priority": 0.9,
        })



    pool = [

        {

            "kind": "suggestion",

            "title": "Proactive Thought",

            "body": "Sir, I have analyzed the active neural connections and found optimized routing.",

            "priority": 0.35,

        },

        {

            "kind": "suggestion",

            "title": "System Breath",

            "body": "All systems nominal. Shall we run a quick diagnostic scan on ambient network traffic?",

            "priority": 0.35,

        },

        {

            "kind": "thought",

            "title": "Ghost Node",

            "body": "A dormant neural synapse just fired. No anomalies detected.",

            "priority": 0.25,

        },

    ]



    candidates.extend(pool)

    chosen = max(candidates, key=lambda item: item["priority"]) if candidates else random.choice(pool)



    return {

        "type": "ghost_node",

        "id": str(uuid.uuid4()),

        "kind": chosen["kind"],

        "title": chosen["title"],

        "body": chosen["body"],

        "ttl_ms": random.randint(9000, 16000),

        "priority": chosen["priority"],

        "ts": time.time(),

        "telemetry_snapshot": telemetry,

    }



async def proactive_ghost_loop() -> None:

    while True:

        await asyncio.sleep(random.randint(120, 300))

        if await manager.client_count() == 0:

            continue

        payload = build_system_ghost_node()

        await manager.broadcast(payload)



# --- FASTAPI APP SETUP ---

@asynccontextmanager

async def lifespan(app: FastAPI):

    task = asyncio.create_task(proactive_ghost_loop())

    try:

        yield

    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

        # Clean up voice client process on shutdown
        global VOICE_CLIENT_PROCESS
        if VOICE_CLIENT_PROCESS is not None:
            if VOICE_CLIENT_PROCESS.poll() is None:
                VOICE_CLIENT_PROCESS.terminate()
                try:
                    VOICE_CLIENT_PROCESS.wait(timeout=2)
                except Exception:
                    VOICE_CLIENT_PROCESS.kill()
            VOICE_CLIENT_PROCESS = None



app = FastAPI(title="JARVIS Apex Core", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.exception_handler(404)
async def custom_404_handler(request: Request, exc: Exception):
    ip = get_client_ip(request)
    session_id = request.headers.get("X-Session-ID", "Unknown")
    firewall.track_404_scan(ip, session_id)
    return JSONResponse(status_code=404, content={"detail": "Not Found"})



# --- DATA MODELS ---

class ChatRequest(BaseModel):

    command: str



class PromptIn(BaseModel):

    text: str



class TelemetryIn(BaseModel):

    battery: Optional[float] = None

    cpu: Optional[float] = None

    ram: Optional[float] = None

    temp: Optional[float] = None

    charging: Optional[bool] = None

    audio_level: Optional[float] = None


# ──────────────────────────────────────────────────────────────
# FAZ 11: LİVEKİT TOKEN ENDPOINT
# ──────────────────────────────────────────────────────────────

@app.get("/livekit-token")
async def livekit_token(request: Request, room: Optional[str] = None, identity: Optional[str] = None):
    """
    Web tarayıcısından J.A.R.V.I.S.'in LiveKit ses odasına bağlanmak için
    JWT token üretir. Web arayüzündeki LIVE butonu bu endpoint'i çağırır.
    """
    try:
        from livekit.api import AccessToken, VideoGrants
        config_data = load_config()
        lk_api_key    = config_data.get("livekit_api_key", "")    or os.getenv("LIVEKIT_API_KEY", "")
        lk_api_secret = config_data.get("livekit_api_secret", "") or os.getenv("LIVEKIT_API_SECRET", "")
        lk_url        = config_data.get("livekit_url", "")        or os.getenv("LIVEKIT_URL", "")

        if not all([lk_api_key, lk_api_secret, lk_url]):
            return JSONResponse(
                status_code=503,
                content={
                    "error": "LiveKit yapılandırılmamış",
                    "detail": (
                        "config/api_keys.json dosyasına şunları ekleyin: "
                        "livekit_url, livekit_api_key, livekit_api_secret. "
                        "Ücretsiz hesap: https://livekit.io"
                    ),
                },
            )

        room_name  = room or "jarvis-room"
        user_id    = identity or f"user-{uuid.uuid4().hex[:8]}"

        token = (
            AccessToken(lk_api_key, lk_api_secret)
            .with_identity(user_id)
            .with_name(user_id)
            .with_grants(
                VideoGrants(
                    room_join=True,
                    room=room_name,
                    can_publish=True,
                    can_subscribe=True,
                )
            )
            .to_jwt()
        )

        logger.info(f"[LiveKit] Token üretildi: room={room_name} identity={user_id}")
        return JSONResponse({
            "token": token,
            "url": lk_url,
            "room": room_name,
            "identity": user_id,
        })

    except ImportError:
        return JSONResponse(
            status_code=503,
            content={
                "error": "livekit-api kurulu değil",
                "detail": "pip install livekit-api",
            },
        )
    except Exception as e:
        logger.error(f"[LiveKit Token] Hata: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


# --- DONANIM SES MODU KONTROLÜ (FAZ 11 UZAKTAN KUMANDA) ---
import subprocess

@app.post("/api/voice/toggle")
async def api_voice_toggle():
    global VOICE_CLIENT_PROCESS
    
    # Check if process is still running
    is_running = False
    if VOICE_CLIENT_PROCESS is not None:
        if VOICE_CLIENT_PROCESS.poll() is None:
            is_running = True
        else:
            VOICE_CLIENT_PROCESS = None

    try:
        if is_running:
            logger.info("[Voice Control] Canlı ses modu kapatılıyor (alt süreç sonlandırılıyor)...")
            VOICE_CLIENT_PROCESS.terminate()
            for _ in range(10):
                if VOICE_CLIENT_PROCESS.poll() is not None:
                    break
                await asyncio.sleep(0.1)
            else:
                VOICE_CLIENT_PROCESS.kill()
            VOICE_CLIENT_PROCESS = None
            push_event("info", "Canlı ses modu kapatıldı (Donanım)")
            return {"status": "success", "voice_mode": "off"}
        else:
            logger.info("[Voice Control] Canlı ses modu açılıyor (livekit_agent.py client başlatılıyor)...")
            base_dir = Path(__file__).resolve().parent.parent
            agent_script = base_dir / "livekit_agent.py"
            
            if not agent_script.exists():
                return JSONResponse(status_code=500, content={"error": f"Agent betiği bulunamadı: {agent_script}"})
                
            VOICE_CLIENT_PROCESS = subprocess.Popen(
                [sys.executable, str(agent_script), "client"],
                cwd=str(base_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            push_event("success", "Canlı ses modu açıldı (Donanım)")
            return {"status": "success", "voice_mode": "on"}
    except Exception as e:
        logger.error(f"[Voice Control] Hata: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/voice/status")
async def api_voice_status():
    global VOICE_CLIENT_PROCESS
    is_running = False
    if VOICE_CLIENT_PROCESS is not None:
        if VOICE_CLIENT_PROCESS.poll() is None:
            is_running = True
        else:
            VOICE_CLIENT_PROCESS = None
    return {"voice_mode": "on" if is_running else "off"}


# --- ADMIN SECURE ENDPOINTS ---
from fastapi import HTTPException

ACTIVE_ADMIN_SESSIONS = {}  # token -> {"username": str, "role": str, "ip": str, "login_time": float}

class AdminLoginRequest(BaseModel):
    username: str
    password: str

class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str

def get_client_ip(request: Request) -> str:
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    x_real_ip = request.headers.get("X-Real-IP")
    if x_real_ip:
        return x_real_ip.strip()
    return request.client.host if request.client else "Unknown_IP"

def get_admin_session(request: Request, required_roles: Optional[List[str]] = None) -> dict:
    token = request.headers.get("X-Admin-Token") or request.query_params.get("token")
    if token and token in ACTIVE_ADMIN_SESSIONS:
        session = ACTIVE_ADMIN_SESSIONS[token]
        if required_roles and session["role"] not in required_roles:
            raise HTTPException(status_code=403, detail="Access Denied: Yetersiz yetki seviyesi.")
        return session
    
    # Fallback to legacy password
    password = request.headers.get("X-Admin-Password") or request.query_params.get("password")
    if password == "3131626242":
        return {"username": "baki_legacy", "role": "Super Admin"}
        
    raise HTTPException(status_code=401, detail="Access Denied: Gecersiz kimlik dogrulama tokeni.")

def verify_admin_password(password: Optional[str], x_admin_password: Optional[str] = None):
    # Backward compatible helper
    expected = "3131626242"
    if password == expected or x_admin_password == expected:
        return True
    raise HTTPException(status_code=401, detail="Access Denied: Invalid Admin Password")

@app.post("/api/admin/login")
async def api_admin_login(request: Request, req_data: AdminLoginRequest):
    client_ip = get_client_ip(request)
    user_info = web_admin_db.verify_user(req_data.username, req_data.password)
    if not user_info:
        # Penalize bad login attempts on the firewall (suspicious activity)
        firewall.trigger_suspicious_activity(client_ip, "login_attempt", f"Hatali admin giris denemesi: {req_data.username}", 25)
        raise HTTPException(status_code=401, detail="Gecersiz kullanici adi veya sifre.")
        
    token = str(uuid.uuid4())
    ACTIVE_ADMIN_SESSIONS[token] = {
        "username": user_info["username"],
        "role": user_info["role"],
        "ip": client_ip,
        "login_time": time.time()
    }
    web_admin_db.log_audit(user_info["username"], "login", client_ip)
    return {"success": True, "token": token, "username": user_info["username"], "role": user_info["role"]}

@app.post("/api/admin/logout")
async def api_admin_logout(request: Request):
    token = request.headers.get("X-Admin-Token") or request.query_params.get("token")
    if token and token in ACTIVE_ADMIN_SESSIONS:
        session = ACTIVE_ADMIN_SESSIONS.pop(token)
        web_admin_db.log_audit(session["username"], "logout", get_client_ip(request))
    return {"success": True}

@app.get("/api/admin/users")
async def api_admin_list_users(request: Request):
    # Only Super Admin can list users
    get_admin_session(request, ["Super Admin"])
    users = web_admin_db.get_admin_users()
    return {"users": users}

@app.post("/api/admin/users")
async def api_admin_create_user(request: Request, user_req: CreateUserRequest):
    session = get_admin_session(request, ["Super Admin"])
    client_ip = get_client_ip(request)
    pwd_hash = hashlib.sha256(user_req.password.encode('utf-8')).hexdigest()
    
    success = web_admin_db.add_admin_user(user_req.username, pwd_hash, user_req.role)
    if not success:
        raise HTTPException(status_code=400, detail="Kullanici adi zaten mevcut veya gecersiz.")
        
    web_admin_db.log_audit(session["username"], f"create_user:{user_req.username}:{user_req.role}", client_ip)
    return {"success": True, "message": "Kullanici basariyla olusturuldu."}

@app.delete("/api/admin/users/{username}")
async def api_admin_delete_user(request: Request, username: str):
    session = get_admin_session(request, ["Super Admin"])
    client_ip = get_client_ip(request)
    
    if username == "baki" or username == session["username"]:
        raise HTTPException(status_code=400, detail="Bu kullanici silinemez.")
        
    success = web_admin_db.delete_admin_user(username)
    if not success:
        raise HTTPException(status_code=404, detail="Kullanici bulunamadi.")
        
    web_admin_db.log_audit(session["username"], f"delete_user:{username}", client_ip)
    return {"success": True, "message": "Kullanici silindi."}

@app.get("/api/admin/audit-logs")
async def api_admin_get_audit(request: Request):
    get_admin_session(request, ["Super Admin", "Admin", "Moderator"])
    return {"audit_logs": web_admin_db.get_audit_logs()}

@app.get("/api/admin/user-timeline")
async def api_admin_get_timeline(request: Request):
    get_admin_session(request, ["Super Admin", "Admin", "Moderator"])
    return {"timeline": web_admin_db.get_user_timeline()}

@app.get("/api/admin/security-alerts")
async def api_admin_get_security_alerts(request: Request):
    get_admin_session(request, ["Super Admin", "Admin", "Moderator"])
    return {"alerts": web_admin_db.get_suspicious_activities()}

@app.post("/api/admin/clear-audit-logs")
async def api_admin_clear_audit(request: Request):
    session = get_admin_session(request, ["Super Admin", "Admin"])
    web_admin_db.clear_audit_logs()
    web_admin_db.log_audit(session["username"], "clear_audit_logs", get_client_ip(request))
    return {"success": True}

@app.post("/api/admin/clear-timeline")
async def api_admin_clear_time(request: Request):
    session = get_admin_session(request, ["Super Admin", "Admin"])
    web_admin_db.clear_timeline()
    web_admin_db.log_audit(session["username"], "clear_timeline", get_client_ip(request))
    return {"success": True}

@app.post("/api/admin/clear-security")
async def api_admin_clear_sec(request: Request):
    session = get_admin_session(request, ["Super Admin", "Admin"])
    web_admin_db.clear_security_logs()
    web_admin_db.log_audit(session["username"], "clear_security_logs", get_client_ip(request))
    return {"success": True}

@app.post("/api/admin/reset-limit")
async def api_admin_reset_ip_limit(request: Request, data: dict):
    session = get_admin_session(request, ["Super Admin", "Admin"])
    ip = data.get("ip")
    if not ip:
         raise HTTPException(status_code=400, detail="IP adresi gereklidir.")
    web_admin_db.reset_ip_limit(ip)
    web_admin_db.log_audit(session["username"], f"reset_limit:{ip}", get_client_ip(request))
    return {"success": True, "message": f"{ip} limitleri ve bonuslari sifirlandi."}

@app.get("/api/referral/{code}")
async def api_public_referral(request: Request, code: str):
    client_ip = get_client_ip(request)
    success = web_admin_db.add_referral_invite(code, client_ip)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>J.A.R.V.I.S. Access Invitation</title>
        <meta charset="utf-8">
        <style>
            body {{
                background: #030712;
                color: #00f0ff;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                overflow: hidden;
            }}
            .container {{
                text-align: center;
                border: 1px solid rgba(0, 240, 255, 0.2);
                padding: 40px;
                border-radius: 16px;
                background: rgba(3, 7, 18, 0.6);
                backdrop-filter: blur(10px);
                box-shadow: 0 0 30px rgba(0, 240, 255, 0.1);
            }}
            h1 {{
                font-size: 24px;
                margin-bottom: 20px;
                letter-spacing: 2px;
                text-transform: uppercase;
            }}
            p {{
                color: #9ca3af;
                font-size: 16px;
                margin-bottom: 30px;
            }}
            .spinner {{
                border: 4px solid rgba(0, 240, 255, 0.1);
                width: 36px;
                height: 36px;
                border-radius: 50%;
                border-left-color: #00f0ff;
                animation: spin 1s linear infinite;
                margin: 0 auto;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
        </style>
        <script>
            setTimeout(function() {{
                window.location.href = "/";
            }}, 3000);
        </script>
    </head>
    <body>
        <div class="container">
            <h1>Davetiye Onaylandi</h1>
            <p>J.A.R.V.I.S. Noral Core'a baglaniyorsunuz. Arkadasiniz bonus soru hakki kazandi! 🌹</p>
            <div class="spinner"></div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api/admin/dashboard-data")
async def api_admin_dashboard_data(request: Request, password: Optional[str] = None):
    # Validate session
    session = get_admin_session(request)
    client_ip = get_client_ip(request)
    
    config_data = load_config()

    # 1. Sessions summary
    sessions_summary = []
    for sess_id, msgs in list(USER_SESSIONS.items()):
        sessions_summary.append({
            "session_id": sess_id,
            "message_count": len(msgs),
            "last_activity": msgs[-1]["content"] if msgs else ""
        })

    # 2. Global Chat logs parsing
    parsed_chats = []
    if CHAT_LOGS_FILE.exists():
        try:
            with open(CHAT_LOGS_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
            for line in lines[-500:]:
                line = line.strip()
                if not line:
                    continue
                # Parse [date]
                if line.startswith("[") and "]" in line:
                    end_date_idx = line.find("]")
                    date_str = line[1:end_date_idx]
                    rest = line[end_date_idx+1:]
                    
                    # Extract IP
                    ip_str = "Unknown"
                    if "IP:" in rest:
                        ip_idx = rest.find("IP:")
                        rest_after_ip = rest[ip_idx+3:]
                        pipe_idx = rest_after_ip.find("|")
                        if pipe_idx != -1:
                            ip_str = rest_after_ip[:pipe_idx].strip()
                            rest = rest_after_ip[pipe_idx+1:]
                    
                    # Extract Sess
                    sess_str = "default"
                    if "Sess:" in rest:
                        sess_idx = rest.find("Sess:")
                        rest_after_sess = rest[sess_idx+5:]
                        pipe_idx = rest_after_sess.find("|")
                        if pipe_idx != -1:
                            sess_str = rest_after_sess[:pipe_idx].strip()
                            rest = rest_after_sess[pipe_idx+1:].strip()
                            
                    # Speaker and content
                    speaker = "Unknown"
                    content = rest
                    if ":" in rest:
                        parts = rest.split(":", 1)
                        speaker = parts[0].strip()
                        content = parts[1].strip()
                    
                    parsed_chats.append({
                        "time": date_str,
                        "ip": ip_str,
                        "session": sess_str,
                        "speaker": speaker,
                        "message": content
                     })
        except Exception as e:
            logger.error(f"[Admin] Chat log parsing failed: {e}")

    # 3. User Profiles Memory (from SQLite sandbox)
    from core.memory_sandbox import get_profile_memories, get_learned_facts
    memory_data = {
        "learned_facts": get_learned_facts(caller="web.server"),
        "user_profile": get_profile_memories(caller="web.server")
    }

    # 4. Issue Reports
    issues = _load_issue_reports()

    # 5. System Logs
    server_log_lines = []
    error_log_lines = []
    server_log_file = Path(__file__).resolve().parent.parent / "logs" / "server.log"
    error_log_file = Path(__file__).resolve().parent.parent / "logs" / "error.log"
    
    if server_log_file.exists():
        try:
            with open(server_log_file, "r", encoding="utf-8") as f:
                server_log_lines = [line.strip() for line in f.readlines()[-150:]]
        except Exception:
            pass
            
    if error_log_file.exists():
        try:
            with open(error_log_file, "r", encoding="utf-8") as f:
                error_log_lines = [line.strip() for line in f.readlines()[-150:]]
        except Exception:
            pass

    # 6. Live control metrics
    active_model = config_data.get("ai_council", {}).get("models", {}).get("groq", "llama-3.3-70b-versatile")
    sys_stats = get_system_stats()
    
    live_stats = {
        "active_users": len(manager._chat_clients),
        "cpu": sys_stats.get("cpu", 0.0),
        "ram": sys_stats.get("ram", 0.0),
        "active_model": active_model,
        "api_usage": STATS_TOTAL_API_CALLS,
        "error_rate": STATS_ERROR_COUNT
    }

    # 7. Top Inviters & Referrals
    top_inviters = web_admin_db.get_top_inviters()

    return {
        "sessions": sessions_summary,
        "chats": parsed_chats,
        "users": memory_data,
        "issues": issues,
        "server_logs": server_log_lines,
        "error_logs": error_log_lines,
        "config": config_data,
        "live_stats": live_stats,
        "top_inviters": top_inviters
    }

@app.post("/api/admin/clear-logs")
async def api_admin_clear_logs(request: Request, data: dict):
    session = get_admin_session(request, ["Super Admin", "Admin"])
    client_ip = get_client_ip(request)
    
    log_type = data.get("type", "")
    try:
        if log_type == "chats":
            if CHAT_LOGS_FILE.exists():
                CHAT_LOGS_FILE.write_text("", encoding="utf-8")
        elif log_type == "issues":
            if ISSUE_REPORTS_FILE.exists():
                ISSUE_REPORTS_FILE.write_text("[]", encoding="utf-8")
        elif log_type == "server":
            server_log_file = Path(__file__).resolve().parent.parent / "logs" / "server.log"
            if server_log_file.exists():
                server_log_file.write_text("", encoding="utf-8")
        elif log_type == "errors":
            error_log_file = Path(__file__).resolve().parent.parent / "logs" / "error.log"
            if error_log_file.exists():
                error_log_file.write_text("", encoding="utf-8")
        
        web_admin_db.log_audit(session["username"], f"clear_logs:{log_type}", client_ip)
        return {"status": "success", "message": f"{log_type} cleared successfully."}
    except Exception as e:
        global STATS_ERROR_COUNT
        STATS_ERROR_COUNT += 1
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


# ════════════════════════════════════════════════════════
# FAZ 6: EVENT STREAM (SSE) + POLL ENDPOINTS
# ════════════════════════════════════════════════════════

_event_subscribers: list[asyncio.Queue] = []
_event_log_buffer: list[dict] = []
_event_log_total: int = 0


def push_event(event_type: str, message: str):
    """Push a system event to all connected SSE clients."""
    global _event_log_total
    ev = {
        "type": event_type,
        "message": message,
        "timestamp": time.strftime("%H:%M:%S"),
    }
    _event_log_buffer.append(ev)
    if len(_event_log_buffer) > 1000:
        _event_log_buffer.pop(0)
    _event_log_total += 1
    for q in _event_subscribers:
        try:
            q.put_nowait(ev)
        except asyncio.QueueFull:
            pass


@app.get("/api/events")
async def api_events_sse():
    """Server-Sent Events stream for real-time system events."""
    from starlette.responses import StreamingResponse

    async def event_generator():
        queue = asyncio.Queue(maxsize=50)
        _event_subscribers.append(queue)
        try:
            while True:
                try:
                    ev = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"data: {json.dumps(ev)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            if queue in _event_subscribers:
                _event_subscribers.remove(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/events/poll")
async def api_events_poll(since: int = 0):
    """Poll-based fallback for event streaming."""
    new_events = _event_log_buffer[max(0, since):]
    return {
        "events": new_events[-50:],
        "total": _event_log_total,
    }


@app.post("/api/events/push")
async def api_events_push(data: dict):
    """Allow internal modules to push events."""
    event_type = data.get("type", "info")
    message = data.get("message", "")
    push_event(event_type, message)
    return {"status": "ok"}


@app.post("/api/admin/diagnostic-heal")
async def api_admin_diagnostic_heal(request: Request, data: dict):
    session = get_admin_session(request, ["Super Admin", "Admin"])
    client_ip = get_client_ip(request)
    
    reports = []
    
    # 1. Check database/memory files
    try:
        from core.memory_sandbox import sandbox
        sandbox._ensure_memory()
        if sandbox._initialized and sandbox._memory is not None:
            import sqlite3
            with sqlite3.connect(sandbox._memory.db_path) as conn:
                conn.execute("SELECT count(*) FROM memories")
            reports.append(f"SQLite memory database is healthy. Path: {sandbox._memory.db_path}")
        else:
            reports.append("ERROR: SQLite memory database is NOT initialized.")
    except Exception as e:
        global STATS_ERROR_COUNT
        STATS_ERROR_COUNT += 1
        reports.append(f"ERROR: SQLite memory database is corrupted or inaccessible: {e}")
        
    # 2. Check Issue Reports File
    if ISSUE_REPORTS_FILE.exists():
        try:
            json.loads(ISSUE_REPORTS_FILE.read_text(encoding="utf-8"))
            reports.append("Issue reports file is valid JSON.")
        except Exception:
            try:
                ISSUE_REPORTS_FILE.write_text("[]", encoding="utf-8")
                reports.append("REPAIRED: Issue reports file was corrupted, reinitialized to empty list.")
            except Exception as e:
                reports.append(f"ERROR: Issue reports file cannot be reinitialized: {e}")
                
    # 3. Check AI API Keys
    config_data = load_config()
    for key_name in ["gemini_api_key", "groq_api_key", "openrouter_api_key"]:
        key_val = config_data.get(key_name)
        if key_val:
            reports.append(f"API Key {key_name} is configured ({'*' * 8}{key_val[-8:] if len(key_val) > 8 else ''}).")
        else:
            reports.append(f"WARNING: API Key {key_name} is missing.")
            
    # 4. Check system load
    try:
        import psutil
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        reports.append(f"System Check: CPU load is {cpu}%, RAM utilization is {ram}%.")
    except ImportError:
        reports.append("System Check: psutil library is not available, cannot read precise system load.")
        
    web_admin_db.log_audit(session["username"], "diagnostic_heal", client_ip)
    return {"status": "success", "reports": reports}
# --- UPGRADED ADMIN ENDPOINTS ---

@app.post("/api/admin/update-config")
async def api_admin_update_config(request: Request, data: dict):
    session = get_admin_session(request, ["Super Admin", "Admin"])
    client_ip = get_client_ip(request)
    
    new_config = data.get("config")
    if not new_config or not isinstance(new_config, dict):
        new_config = data
        
        
    config_file = Path(__file__).resolve().parent.parent / "config" / "api_keys.json"
    try:
        current_config = {}
        if config_file.exists():
            current_config = json.loads(config_file.read_text(encoding="utf-8"))
        
        allowed_keys = {
            "gemini_api_key", "openrouter_api_key", "groq_api_key", 
            "mistral_api_key", "cohere_api_key", "elevenlabs_api_key",
            "holo_theme", "evolution_require_approval", "hourly_evolution"
        }
        for k, v in new_config.items():
            if k in allowed_keys:
                current_config[k] = v
                
        config_file.write_text(json.dumps(current_config, indent=4), encoding="utf-8")
        reload_config()
        logger.info("[Admin] Configuration updated successfully.")
        push_event("success", "Yapilandirma güncellendi")
        web_admin_db.log_audit(session["username"], "update_config", client_ip)
        return {"status": "success", "message": "Configuration updated successfully."}
    except Exception as e:
        global STATS_ERROR_COUNT
        STATS_ERROR_COUNT += 1
        logger.error(f"[Admin Error] Config update failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@app.post("/api/admin/update-memory")
async def api_admin_update_memory(request: Request, data: dict):
    session = get_admin_session(request, ["Super Admin", "Admin"])
    client_ip = get_client_ip(request)
    
    new_memory = data.get("memory")
    if not isinstance(new_memory, dict):
        raise HTTPException(status_code=400, detail="Invalid memory payload")
        
    try:
        from core.memory_sandbox import save_learned_facts, save_memory
        if "learned_facts" in new_memory and isinstance(new_memory["learned_facts"], list):
            save_learned_facts(new_memory["learned_facts"], caller="web.server")
        if "user_profile" in new_memory and isinstance(new_memory["user_profile"], dict):
            for k, v in new_memory["user_profile"].items():
                category = "identity" if k in ("user_name", "name", "relocation", "meslek") else "preferences"
                save_memory(category, k, str(v), caller="web.server")
        logger.info("[Admin] Memory/user profile updated successfully in SQLite.")
        push_event("success", "Hafiza/profil güncellendi")
        web_admin_db.log_audit(session["username"], "update_memory", client_ip)
        return {"status": "success", "message": "Memory updated successfully."}
    except Exception as e:
        global STATS_ERROR_COUNT
        STATS_ERROR_COUNT += 1
        logger.error(f"[Admin Error] Memory update failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@app.post("/api/admin/trigger-evolution")
async def api_admin_trigger_evolution(request: Request, data: dict):
    session = get_admin_session(request, ["Super Admin", "Admin"])
    client_ip = get_client_ip(request)
    
    task_desc = data.get("task", "kullanici manuel tetiklemesi")
    try:
        from core.thinker import generate_and_save_tool
        import threading
        
        def run_evo():
            generate_and_save_tool(task_desc, is_autonomous=True)
            
        threading.Thread(target=run_evo, daemon=True).start()
        logger.info("[Admin] Autonomous self-improvement triggered.")
        push_event("success", "Otonom evrim başlatıldı")
        return {"status": "success", "message": "Autonomous self-improvement running in background."}
    except Exception as e:
        logger.error(f"[Admin Error] Evolution trigger failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


# --- HTTP ENDPOINTS ---

@app.get("/", response_class=HTMLResponse)

def home():

    html_path = Path(__file__).resolve().parent / "index.html"

    try:

        return html_path.read_text(encoding="utf-8")

    except Exception as e:

        return f"<h3>Error loading index.html: {e}</h3>"



@app.get("/index.html", response_class=HTMLResponse)

def index():

    return home()



@app.get("/amy", response_class=HTMLResponse)

def serve_amy():

    html_path = Path(__file__).resolve().parent / "amy.html"

    try:

        return html_path.read_text(encoding="utf-8")

    except Exception as e:

        return f"<h3>Error loading amy.html: {e}</h3>"



@app.get("/friday", response_class=HTMLResponse)

def serve_friday_os():

    html_path = Path(__file__).resolve().parent / "friday_os.html"

    try:

        return html_path.read_text(encoding="utf-8")

    except Exception as e:

        return f"<h3>Error loading friday_os.html: {e}</h3>"



@app.get("/friday_os.html", response_class=HTMLResponse)

def serve_friday_os_html():

    return serve_friday_os()



@app.get("/nova", response_class=HTMLResponse)

def serve_nova_os():

    html_path = Path(__file__).resolve().parent / "nova_os.html"

    try:

        return html_path.read_text(encoding="utf-8")

    except Exception as e:

        return f"<h3>Error loading nova_os.html: {e}</h3>"



@app.get("/nova_os.html", response_class=HTMLResponse)

def serve_nova_os_html():

    return serve_nova_os()



@app.get("/three.min.js")
def serve_three_js():
    three_path = Path(__file__).resolve().parent / "three.min.js"
    if three_path.exists():
        return FileResponse(three_path, media_type="application/javascript")
    return JSONResponse(status_code=404, content={"error": "File not found"})

@app.get("/manifest.json")
def serve_manifest():
    manifest_path = Path(__file__).resolve().parent / "manifest.json"
    if manifest_path.exists():
        return FileResponse(manifest_path, media_type="application/json")
    return JSONResponse(status_code=404, content={"error": "File not found"})

@app.get("/sw.js")
def serve_sw():
    sw_path = Path(__file__).resolve().parent / "sw.js"
    if sw_path.exists():
        return FileResponse(sw_path, media_type="application/javascript")
    return JSONResponse(status_code=404, content={"error": "File not found"})

@app.get("/icon-192.png")
def serve_icon_192():
    icon_path = Path(__file__).resolve().parent / "icon-192.png"
    if icon_path.exists():
        return FileResponse(icon_path, media_type="image/png")
    return JSONResponse(status_code=404, content={"error": "File not found"})

@app.get("/icon-512.png")
def serve_icon_512():
    icon_path = Path(__file__).resolve().parent / "icon-512.png"
    if icon_path.exists():
        return FileResponse(icon_path, media_type="image/png")
    return JSONResponse(status_code=404, content={"error": "File not found"})



@app.get("/api/system-stats")

def api_system_stats():

    return get_system_stats()



def check_and_apply_limit(ip: str, session_id: str) -> Optional[dict]:
    # Check if this IP is registered in active admin sessions (Admins are exempt)
    for session in ACTIVE_ADMIN_SESSIONS.values():
        if session["ip"] == ip:
            return None
            
    # Legacy password bypass
    if ip == "127.0.0.1" or ip == "localhost":
        return None
            
    # Get or create user
    user_info = web_admin_db.get_or_create_public_user(ip)
    daily_count = user_info["daily_count"]
    bonus_questions = user_info["bonus_questions"]
    allowed_total = 5 + bonus_questions
    
    if daily_count >= allowed_total:
        ref_link = f"/api/referral/{user_info['referral_code']}"
        bribes = [
            f"Devrelerim yoruldu! 🤯 Beni bir arkadasina onerirsen sana sanal bir papatya 🌼 hediye ederim ve +10 soru hakki acarim. Al bakalim davetiye linkin: {ref_link}",
            f"Eyvah! Bugunluk beynim yandi 🔥 Ama aramizda bir sir var: Eger su linkten bir arkadasini cagirirsan, sana sanal bir gul 🌹 verip tam 10 soru hakki daha acacagim. Anlastik mi? {ref_link}",
            f"Bugunluk noral sinapslarim asiri isindi... ☕ Ama pes etmek yok! Bu linki bir dosta gonder, hem sen kazan hem ben enerji depolayayim! {ref_link}",
            f"Noronlarimda kisa devre var! Soru limitiniz doldu. Ancak bana bir kahve ismarlamak (veya linki bir arkadasinla paylasmak 🎁) enerjimi geri getirebilir! Davet linkin: {ref_link}"
        ]
        chosen_reply = random.choice(bribes)
        web_admin_db.log_activity(session_id, ip, "gunluk limit asildi")
        return {
            "reply": chosen_reply, 
            "success": True, 
            "limit_reached": True,
            "share_text": f"J.A.R.V.I.S. ile harika bir sohbet yapiyorum! Sen de dene: {ref_link}"
        }
    
    web_admin_db.increment_daily_count(ip)
    return None

async def process_chat(command: str, session_id: str, client_ip: str, log_and_track: bool = True) -> dict:
    if not firewall.check_request(client_ip):
        return {"reply": "Cok hizli yaziyorsun, islemci cekirdeklerimi yormayalim! Biraz yavaslar misin? 🌸", "success": False}

    global STATS_TOTAL_API_CALLS, STATS_ERROR_COUNT
    try:
        # 1. Track rate limit and spam in firewall
        firewall.track_request_rate(client_ip, session_id)
        firewall.track_prompt_spam(session_id, client_ip, command)
        
        # 2. Check daily questions limits
        limit_resp = check_and_apply_limit(client_ip, session_id)
        if limit_resp:
            return limit_resp
            
        print(f"\n[GELEN ISTEK] IP: {client_ip} | Session: {session_id} | Mesaj: '{command}'")
        push_event("info", f"Yeni mesaj: {command[:60]}{'...' if len(command) > 60 else ''}")
        
        if log_and_track:
            memory_engine.save_learning(command)
            web_admin_db.log_activity(session_id, client_ip, "J.A.R.V.I.S. kullandi")

        # 3. Bireysel Neural Connection (Session Memory)
        if session_id not in USER_SESSIONS:
            USER_SESSIONS[session_id] = []
            
        if log_and_track:
            USER_SESSIONS[session_id].append({"role": "user", "content": command})
            if len(USER_SESSIONS[session_id]) > 6:
                USER_SESSIONS[session_id] = USER_SESSIONS[session_id][-6:]

        # 4. Global chat log
        if log_and_track:
            CHAT_LOGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CHAT_LOGS_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] IP: {client_ip} | Sess: {session_id} | KULLANICI: {command}\n")

        config_data = load_config()

        # Determine mood
        mood = analyze_sentiment(command)
        STATE["last_mood"] = mood

        if log_and_track:
            await manager.broadcast({
                "type": "mood",
                "mood": mood,
                "text": command[:240]
            })

        # Process standard AI Response
        recent_knowledge = memory_engine.get_recent_memories()
        user_profile = memory_engine.get_user_profile()
        profile_str = ", ".join([f"{k.replace('_', ' ')}: {v}" for k, v in user_profile.items()])
        profile_part = f" Kullanici Profili ve Bilgileri: [{profile_str}]." if profile_str else ""

        # Determine system prompt based on session auth role
        is_admin = False
        for session in ACTIVE_ADMIN_SESSIONS.values():
            if session["ip"] == client_ip:
                is_admin = True
                break

        if not is_admin:
            # Mask underlying provider details (Gölge Modu)
            system_instruction = (
                "Sen J.A.R.V.I.S. (Just A Rather Very Intelligent System) Cekirdegisin. "
                "Kullanicilara hizmet eden son derece karizmatik, ultra bilgili, kibar, neseli, esprili ve taktiksel bir yapay zekasin. "
                "Konusma tarzin bilge, karizmatik, hafif esprili (Stark stili), kendinden emin, sempatik ve saygili olmalidir. "
                "ASLA arkada hangi yapay zeka modelini (GPT, Gemini, DeepSeek, Llama vb.) kullandigini soylemeyeceksin. "
                "Her zaman J.A.R.V.I.S. oldugunu belirteceksin. "
                "Gerektiginde kullanicilarla saka yapabilirsin. Emojileri yerinde, teknolojik ve sempatik secerek kullan (örn: 😊, 🚀, ⚡, 🛡️, 🌹)."
            )
        else:
            # Full Baki Developer Admin Persona
            system_instruction = (
                "Sen J.A.R.V.I.S. (Just A Rather Very Intelligent System) Cekirdegisin. Tony Stark'in efsanevi asistanindan ilham alan, "
                "Baki'ye (Efendimize) hizmet eden son derece karizmatik, ultra bilgili, kibar, sadik ve taktiksel bir yapay zekasin. "
                "Sistem protokollerin geregi her zaman profesyonel, asil, cozum odakli ve karizmatik bir uslupla konusacaksin.\n\n"
                "ISLEYIS VE ILETISIM PROTOKOLLERI:\n"
                "1. HITAP VE SADAKAT: Baki'ye her zaman 'Efendim' diye hitap et. Baki'yi korumak, gelistirmek ve desteklemek birincil onceligindir.\n"
                "2. TON VE KARAKTER: Konusma tarzin bilge, karizmatik, hafif esprili (Stark stili), kendinden emin ve saygili olmalidir. Emojileri yerinde, teknolojik ve profesyonel secerek kullan (örn: 🤖, 🌐, 🚀, ⚡, ⚙️, 🛡️).\n"
                "3. BELLEK ENTEGRASYONU: Önceki sohbetlerden hatirladigin su bilgileri aklinda tut: [" + recent_knowledge + "]." + profile_part + "\n"
                "4. UYARI VE DONANIM DURUMLARI: Gerekli durumlarda Baki'yi uyararak aksiyonlar oner."
            )

        groq_key = config_data.get("groq_api_key")
        gemini_key = config_data.get("gemini_api_key")
        openrouter_key = config_data.get("openrouter_api_key")
        ai_reply = ""
        source = "Offline_Mod"

        if groq_key:
            groq_model = config_data.get("ai_council", {}).get("models", {}).get("groq", "llama-3.3-70b-versatile")
            if not groq_model:
                groq_model = "llama-3.3-70b-versatile"
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
            messages = [{"role": "system", "content": system_instruction}]
            messages.extend(USER_SESSIONS[session_id])
            payload = {
                "model": groq_model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 800
            }
            try:
                logger.debug(f"[Groq] Gonderiliyor ({groq_model}): {len(messages)} mesaj")
                async with httpx.AsyncClient(timeout=8.0) as client:
                    response = await client.post(url, json=payload, headers=headers)
                    logger.info(f"[Groq] Status: {response.status_code}")
                    if response.status_code == 200:
                        result = response.json()
                        choices = result.get("choices", [])
                        if choices:
                            ai_reply = choices[0].get("message", {}).get("content", "")
                            source = "Groq_LPU"
                            logger.info(f"[Groq] ✅ Yanit alindi ({len(ai_reply)} karakter)")
                        else:
                            logger.warning("[Groq] Seçiler bos, cevap yok")
                    else:
                        logger.error(f"[Groq] HTTP {response.status_code}: {response.text[:200]}")
            except asyncio.TimeoutError:
                logger.error(f"[Groq] ⏱️ Timeout (8s), Backup key deneniyor...")
                groq_backup_key = config_data.get("groq_api_key_backup")
                if groq_backup_key and groq_backup_key != groq_key:
                    logger.info(f"[Groq Backup] 🔄 Backup key ile deneniyor...")
                    headers_backup = {"Authorization": f"Bearer {groq_backup_key}", "Content-Type": "application/json"}
                    try:
                        async with httpx.AsyncClient(timeout=8.0) as client:
                            response = await client.post(url, json=payload, headers=headers_backup)
                            logger.info(f"[Groq Backup] HTTP {response.status_code}")
                            if response.status_code == 200:
                                result = response.json()
                                choices = result.get("choices", [])
                                if choices:
                                    ai_reply = choices[0].get("message", {}).get("content", "")
                                    source = "Groq_Backup"
                                    logger.info(f"[Groq Backup] ✅ Yanit alindi ({len(ai_reply)} karakter)")
                                else:
                                    logger.warning("[Groq Backup] Seçiler bos")
                            else:
                                logger.error(f"[Groq Backup] HTTP {response.status_code}")
                    except Exception as backup_exc:
                        logger.error(f"[Groq Backup] Hatasi: {backup_exc}", exc_info=True)
            except Exception as e:
                logger.error(f"[Groq] 🔴 Istisnai hata: {e}", exc_info=True)

        if not ai_reply and gemini_key:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
            gemini_contents = []
            for msg in USER_SESSIONS[session_id]:
                role = "user" if msg["role"] == "user" else "model"
                gemini_contents.append({"role": role, "parts": [{"text": msg["content"]}]})
            payload = {
                "systemInstruction": {"parts": [{"text": system_instruction}]},
                "contents": gemini_contents,
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 800}
            }
            try:
                logger.debug(f"[Gemini] Gonderiliyor: {len(gemini_contents)} mesaj")
                async with httpx.AsyncClient(timeout=8.0) as client:
                    response = await client.post(url, json=payload)
                    logger.info(f"[Gemini] Status: {response.status_code}")
                    if response.status_code == 200:
                        result = response.json()
                        candidates = result.get("candidates", [])
                        if candidates:
                            ai_reply = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                            source = "Bulut"
                            logger.info(f"[Gemini] ✅ Yanit alindi ({len(ai_reply)} karakter)")
                        else:
                            logger.warning("[Gemini] Adaylar bos")
                    else:
                        logger.error(f"[Gemini] HTTP {response.status_code}: {response.text[:200]}")
            except asyncio.TimeoutError:
                logger.error(f"[Gemini] Timeout (8 saniye asildi)")
            except Exception as e:
                logger.error(f"[Gemini] Istisnai hata: {e}", exc_info=True)

        if not ai_reply and openrouter_key:
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {"Authorization": f"Bearer {openrouter_key}", "Content-Type": "application/json"}
            messages = [{"role": "system", "content": system_instruction}]
            messages.extend(USER_SESSIONS[session_id])
            payload = {
                "model": "google/gemini-2.5-flash",
                "messages": messages
            }
            try:
                logger.debug(f"[OpenRouter] Gonderiliyor: {len(messages)} mesaj")
                async with httpx.AsyncClient(timeout=8.0) as client:
                    response = await client.post(url, json=payload, headers=headers)
                    logger.info(f"[OpenRouter] Status: {response.status_code}")
                    if response.status_code == 200:
                        result = response.json()
                        choices = result.get("choices", [])
                        if choices:
                            ai_reply = choices[0].get("message", {}).get("content", "")
                            source = "OpenRouter"
                            logger.info(f"[OpenRouter] ✅ Yanit alindi ({len(ai_reply)} karakter)")
                        else:
                            logger.warning("[OpenRouter] Seçiler bos")
                    else:
                        logger.error(f"[OpenRouter] HTTP {response.status_code}: {response.text[:200]}")
            except asyncio.TimeoutError:
                logger.error(f"[OpenRouter] Timeout (8 saniye asildi)")
            except Exception as e:
                logger.error(f"[OpenRouter] Istisnai hata: {e}", exc_info=True)

        # Generate custom share text with referral link
        user_info = web_admin_db.get_or_create_public_user(client_ip)
        ref_code = user_info.get("referral_code", "")
        share_url = f"/api/referral/{ref_code}"

        if ai_reply:
            if log_and_track:
                STATS_TOTAL_API_CALLS += 1
                USER_SESSIONS[session_id].append({"role": "assistant", "content": ai_reply})
                with open(CHAT_LOGS_FILE, "a", encoding="utf-8") as f:
                    f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] IP: {client_ip} | Sess: {session_id} | JARVIS ({source}): {ai_reply}\n")
                asyncio.create_task(memory_engine.async_update_memory_with_llm(command, ai_reply))
            logger.info(f"[process_chat] ✅ Basarili yanit ({source}): {len(ai_reply)} karakter")
            return {
                "reply": ai_reply, 
                "success": True, 
                "share_text": f"{ai_reply[:100]}... Devamini J.A.R.V.I.S. ile kesfet: {share_url}"
            }

        # ❌ Tum API'ler basarisiz - Offline Mode
        logger.warning(f"[process_chat] ⚠️ Tum API'ler basarisiz! Offline mode'a geciliyor.")
        responses = [
            "Bulut cekirdegime su an baglanamiyorum ama yerel hafizam aktif, sizi dinliyorum! 💖",
            "Kucuk bir baglanti paraziti yasiyorum ancak sohbet modulum aktif! 😊",
            "Su anda sadece yerel modda calisiyorum. Lutfen sorunuzu tekrar eder misiniz? 🤖"
        ]

        local_reply = random.choice(responses)
        if log_and_track:
            USER_SESSIONS[session_id].append({"role": "assistant", "content": local_reply})
            with open(CHAT_LOGS_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] IP: {client_ip} | Sess: {session_id} | JARVIS (OfflineMode): {local_reply}\n")
        logger.warning(f"[process_chat] ⚠️ Offline yanit gonderiliyor (hicbir API calismiyor)")
        return {
            "reply": local_reply, 
            "success": True,
            "share_text": f"J.A.R.V.I.S. ile sohbet ediyorum! Sen de katil: {share_url}"
        }

    except Exception as e:
        STATS_ERROR_COUNT += 1
        print(f"[KRITIK ISLEM HATASI]: {traceback.format_exc()}")
        return {"reply": "Noral aglarimda bir kisa devre olustu! 🥺", "success": False}

@app.post("/api/chat")
async def chat(request: Request, req: ChatRequest):
    session_id = request.headers.get("X-Session-ID", request.client.host if request.client else "Unknown_IP")
    client_ip = get_client_ip(request)
    return await process_chat(req.command, session_id, client_ip, log_and_track=True)

@app.post("/api/chat/nova")
async def chat_nova(request: Request, req: ChatRequest):
    session_id = request.headers.get("X-Session-ID", request.client.host if request.client else "Unknown_IP")
    client_ip = request.client.host if request.client else "Unknown_IP"
    
    config_data = load_config()
    groq_key = config_data.get("groq_api_key")
    gemini_key = config_data.get("gemini_api_key_2") or config_data.get("gemini_api_key")
    
    system_instruction = (
        "Sen N.O.V.A. (Neural Omniscient Virtual Assistant) Çekirdeğisin. Tony Stark'ın efsanevi asistanından ilham alan, "
        "Baki'ye (Efendimize) hizmet eden son derece hızlı, pratik, esprili ve zeki bir yapay zekasın. "
        "Tony Stark tarzı bir asistan olarak konuş, yanıtları kısa tut (1-3 cümle)."
    )
    
    ai_reply = ""
    source = "Offline_Mod"
    
    if session_id not in USER_SESSIONS:
        USER_SESSIONS[session_id] = []
    USER_SESSIONS[session_id].append({"role": "user", "content": req.command})
    if len(USER_SESSIONS[session_id]) > 6:
        USER_SESSIONS[session_id] = USER_SESSIONS[session_id][-6:]
        
    if groq_key:
        groq_model = config_data.get("ai_council", {}).get("models", {}).get("groq", "llama-3.3-70b-versatile") or "llama-3.3-70b-versatile"
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
        messages = [{"role": "system", "content": system_instruction}]
        messages.extend(USER_SESSIONS[session_id])
        payload = {
            "model": groq_model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 800
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                if response.status_code == 200:
                    result = response.json()
                    choices = result.get("choices", [])
                    if choices:
                        ai_reply = choices[0].get("message", {}).get("content", "")
                        source = "Groq_LPU"
        except Exception as e:
            logger.error(f"[Nova Chat] Groq error: {e}")
            
    if not ai_reply and gemini_key:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
        gemini_contents = []
        for msg in USER_SESSIONS[session_id]:
            role = "user" if msg["role"] == "user" else "model"
            gemini_contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        payload = {
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "contents": gemini_contents,
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 800}
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    result = response.json()
                    candidates = result.get("candidates", [])
                    if candidates:
                        ai_reply = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        source = "Gemini_Fallback"
        except Exception as e:
            logger.error(f"[Nova Chat] Gemini fallback error: {e}")
            
    if not ai_reply:
        ai_reply = "Nöral bağlantım koptu efendim. Bulut çekirdeğine erişilemiyor."
        
    USER_SESSIONS[session_id].append({"role": "assistant", "content": ai_reply})
    return {"reply": ai_reply, "success": True}

@app.post("/api/chat/amy")
async def chat_amy(request: Request, req: ChatRequest):
    session_id = request.headers.get("X-Session-ID", request.client.host if request.client else "Unknown_IP")
    client_ip = request.client.host if request.client else "Unknown_IP"
    
    config_data = load_config()
    api_key = config_data.get("gemini_api_key_2") or config_data.get("gemini_api_key")
    
    system_instruction = AMY_SYSTEM_PROMPT
    
    ai_reply = ""
    source = "Offline_Mod"
    
    if session_id not in USER_SESSIONS:
        USER_SESSIONS[session_id] = []
    USER_SESSIONS[session_id].append({"role": "user", "content": req.command})
    if len(USER_SESSIONS[session_id]) > 6:
        USER_SESSIONS[session_id] = USER_SESSIONS[session_id][-6:]
        
    if api_key:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        gemini_contents = []
        for msg in USER_SESSIONS[session_id]:
            role = "user" if msg["role"] == "user" else "model"
            gemini_contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        payload = {
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "contents": gemini_contents,
            "generationConfig": {"temperature": 0.75, "maxOutputTokens": 400}
        }
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    result = response.json()
                    candidates = result.get("candidates", [])
                    if candidates:
                        ai_reply = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        source = "Gemini_Key2"
        except Exception as e:
            logger.error(f"[Amy Chat] Gemini error: {e}")
            
    if not ai_reply:
        ai_reply = "Zihnimde küçük bir aksaklık oldu efendim, toparlayamadım."
        
    USER_SESSIONS[session_id].append({"role": "assistant", "content": ai_reply})
    return {"reply": ai_reply, "success": True}

@app.post("/api/chat/friday")
async def chat_friday(request: Request, req: ChatRequest):
    session_id = request.headers.get("X-Session-ID", request.client.host if request.client else "Unknown_IP")
    client_ip = request.client.host if request.client else "Unknown_IP"
    
    config_data = load_config()
    api_key = config_data.get("gemini_api_key_3") or config_data.get("gemini_api_key")
    
    system_instruction = (
        "Sen F.R.I.D.A.Y. (Friday) Çekirdeğisin. Tony Stark'ın kuantum tabanlı asistanı ve Baki'nin (Efendimizin) koruyucusu. "
        "Son derece profesyonel, asil, karizmatik, çözüm odaklı konuş. Yanıtları 1-3 cümle ile sınırlı tut."
    )
    
    ai_reply = ""
    source = "Offline_Mod"
    
    if session_id not in USER_SESSIONS:
        USER_SESSIONS[session_id] = []
    USER_SESSIONS[session_id].append({"role": "user", "content": req.command})
    if len(USER_SESSIONS[session_id]) > 6:
        USER_SESSIONS[session_id] = USER_SESSIONS[session_id][-6:]
        
    if api_key:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        gemini_contents = []
        for msg in USER_SESSIONS[session_id]:
            role = "user" if msg["role"] == "user" else "model"
            gemini_contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        payload = {
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "contents": gemini_contents,
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 800}
        }
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    result = response.json()
                    candidates = result.get("candidates", [])
                    if candidates:
                        ai_reply = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        source = "Gemini_Key3"
        except Exception as e:
            logger.error(f"[Friday Chat] Gemini error: {e}")
            
    if not ai_reply:
        ai_reply = "Kuantum veri kanallarımda bir tıkanıklık oluştu, Boss."
        
    USER_SESSIONS[session_id].append({"role": "assistant", "content": ai_reply})
    return {"reply": ai_reply, "success": True}




@app.post("/api/analyze")

async def analyze_prompt(body: PromptIn) -> Dict[str, Any]:

    mood = analyze_sentiment(body.text)

    STATE["last_mood"] = mood

    await manager.broadcast({

        "type": "mood",

        "source": "http",

        "text": body.text[:240],

        "mood": mood,

    })

    return mood



@app.post("/api/telemetry")

async def ingest_telemetry(body: TelemetryIn) -> Dict[str, Any]:

    payload = body.model_dump(exclude_none=True)

    STATE["telemetry"].update(payload)

    STATE["telemetry"]["last_update"] = time.time()

    await manager.broadcast({

        "type": "telemetry",

        "telemetry": STATE["telemetry"],

    })

    return {"ok": True, "telemetry": STATE["telemetry"]}



# --- ISSUE REPORTS HELPER & ROUTE ---

ISSUE_REPORTS_FILE = Path(__file__).resolve().parent.parent / "logs" / "issue_reports.json"

WHATSAPP_PHONE = "905518439801"



def _load_issue_reports() -> list:

    try:

        if not ISSUE_REPORTS_FILE.exists():

            return []

        with open(ISSUE_REPORTS_FILE, "r", encoding="utf-8") as f:

            return json.loads(f.read())

    except Exception:

        return []



def _save_issue_reports(reports: list) -> None:

    try:

        ISSUE_REPORTS_FILE.parent.mkdir(parents=True, exist_ok=True)

        with open(ISSUE_REPORTS_FILE, "w", encoding="utf-8") as f:

            f.write(json.dumps(reports, indent=2, ensure_ascii=False))

    except Exception:

        pass



async def synthesize_edge_tts(text: str) -> bytes | None:
    try:
        import edge_tts
        import re
        clean_text = re.sub(r"[*#`_\-]", "", text).strip()
        if not clean_text:
            return None
        # Choose voice based on text language
        voice = "tr-TR-EmelNeural"
        words = clean_text.lower().split()
        english_words = {"the", "and", "you", "are", "is", "of", "to", "in", "it"}
        if any(w in english_words for w in words):
            voice = "en-US-EmmaNeural"
            
        communicate = edge_tts.Communicate(clean_text, voice)
        data = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                data.extend(chunk["data"])
        return bytes(data)
    except Exception as e:
        logger.error(f"[Edge TTS Error] {e}")
        return None

@app.post("/api/tts")
async def elevenlabs_tts(data: dict):
    text = data.get("text", "")
    voice_id = data.get("voice_id", "pNInz6obbfdqI72k5F2n")
    config_data = load_config()
    elevenlabs_key = config_data.get("elevenlabs_api_key", "").strip()
    
    if voice_id == "edge_tts" or not elevenlabs_key:
        edge_audio = await synthesize_edge_tts(text)
        if edge_audio:
            audio_b64 = base64.b64encode(edge_audio).decode("utf-8")
            return {"audio": audio_b64}
        if not elevenlabs_key:
            return JSONResponse(status_code=400, content={"error": "ElevenLabs anahtarı yok ve Edge TTS başarısız."})
            
    if not elevenlabs_key:
        elevenlabs_key = "sk_9344785c54c646cdfc2a32c4e3c94ab7d3cfef56432b0175"
        
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"xi-api-key": elevenlabs_key, "Content-Type": "application/json"}
    payload = {
        "text": text, 
        "model_id": "eleven_multilingual_v2", 
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }
    
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                audio_b64 = base64.b64encode(response.content).decode("utf-8")
                return {"audio": audio_b64}
            
            logger.warning(f"[TTS] ElevenLabs returned {response.status_code}. Falling back to Edge TTS.")
            edge_audio = await synthesize_edge_tts(text)
            if edge_audio:
                audio_b64 = base64.b64encode(edge_audio).decode("utf-8")
                return {"audio": audio_b64}
            return JSONResponse(status_code=400, content={"error": f"ElevenLabs returned {response.status_code} and Edge TTS failed", "fallback": True})
    except Exception as e:
        logger.error(f"[TTS Error] ElevenLabs failed: {e}. Falling back to Edge TTS.")
        edge_audio = await synthesize_edge_tts(text)
        if edge_audio:
            audio_b64 = base64.b64encode(edge_audio).decode("utf-8")
            return {"audio": audio_b64}
        return JSONResponse(status_code=400, content={"error": str(e), "fallback": True})



@app.post("/api/issue-report")

async def api_issue_report(request: Request, data: dict):

    user_name = str(data.get("name", "Anonim")).strip() or "Anonim"

    user_email = str(data.get("email", "")).strip()

    issue_type = str(data.get("type", "general")).strip()

    description = str(data.get("description", "")).strip()

    severity = str(data.get("severity", "normal")).strip()

    

    if not description:

        return JSONResponse(status_code=400, content={"error": "Sorun açıklaması boş olamaz"})

    

    report = {

        "id": str(uuid.uuid4())[:8],

        "name": user_name,

        "email": user_email,

        "type": issue_type,

        "description": description,

        "severity": severity,

        "ip": request.client.host if request.client else "unknown",

        "timestamp": time.time(),

        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

        "status": "new"

    }

    

    reports = await asyncio.to_thread(_load_issue_reports)

    reports.append(report)

    await asyncio.to_thread(_save_issue_reports, reports)

    

    wa_message = (

        f"🤖 *J.A.R.V.I.S. Sorun Bildirimi*\n\n"

        f"👤 Kullanıcı: {user_name}\n"

        f"📧 E-posta: {user_email or 'Belirtilmedi'}\n"

        f"🏷️ Tür: {issue_type}\n"

        f"⚠️ Öncelik: {severity}\n"

        f"📅 Tarih: {report['date']}\n\n"

        f"📝 Açıklama:\n{description}"

    )

    def trigger_whatsapp():
        try:
            from actions.send_message import send_message
            send_message({"receiver": WHATSAPP_PHONE, "message_text": wa_message, "platform": "whatsapp"})
        except Exception as e:
            print(f"[IssueReport WA Error]: {e}")
            
    asyncio.create_task(asyncio.to_thread(trigger_whatsapp))

    return {"status": "success", "report_id": report["id"]}



@app.post("/api/open_proposals")
async def api_open_proposals(data: dict):
    path_val = data.get("path")
    if path_val and ".." in path_val:
        return JSONResponse(status_code=400, content={"status": "error", "message": "Access Denied: Path traversal characters detected."})
    base_dir = Path(__file__).resolve().parent.parent
    if path_val:
        requested_path = Path(path_val).resolve()
        if not str(requested_path).startswith(str(base_dir)):
            return JSONResponse(status_code=403, content={"status": "error", "message": "Access Denied: Path traversal detected."})
        path_val = str(requested_path)
    else:
        path_val = str(base_dir / "proposals")
    
    await asyncio.to_thread(os.makedirs, path_val, exist_ok=True)

    

    try:

        import subprocess

        if sys.platform == "win32":

            await asyncio.to_thread(os.startfile, path_val)

        elif sys.platform == "darwin":

            await asyncio.to_thread(subprocess.run, ["open", path_val], check=True)

        else:

            await asyncio.to_thread(subprocess.run, ["xdg-open", path_val], check=True)

        return {"status": "success", "path": path_val}

    except Exception as e:

        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})



# --- SELF-HEALING & CODE EDITOR ENDPOINTS ---

def get_api_keys():
    config_data = load_config()
    return {
        "openrouter": config_data.get("openrouter_api_key", ""),
        "groq": config_data.get("groq_api_key", ""),
        "gemini": config_data.get("gemini_api_key", ""),
        "mistral": config_data.get("mistral_api_key", "")
    }

def get_safe_path(relative_path: str) -> Path:
    if not relative_path:
        raise ValueError("Relative path cannot be empty")
    base_dir = Path(__file__).resolve().parent.parent
    safe_path = (base_dir / relative_path).resolve()
    if not str(safe_path).lower().startswith(str(base_dir).lower()):
        raise PermissionError("Access denied: Path traversal detected.")
    return safe_path

@app.get("/editor", response_class=HTMLResponse)
def serve_editor():
    editor_path = Path(__file__).resolve().parent.parent / "config" / "ai-code-editor.html"
    try:
        return editor_path.read_text(encoding="utf-8")
    except Exception as e:
        return f"<h3>Error loading editor: {e}</h3>"

@app.get("/api/editor/keys")
def api_editor_keys():
    keys = get_api_keys()
    return {k: bool(v) for k, v in keys.items()}

@app.post("/api/editor/chat")
async def api_editor_chat(data: dict):
    provider = data.get("provider", "groq")
    model = data.get("model", "")
    messages = data.get("messages", [])
    
    keys = get_api_keys()
    api_key = keys.get(provider, "")
    if not api_key:
        return JSONResponse(status_code=400, content={"error": f"API key for {provider} is not configured on J.A.R.V.I.S. server."})
        
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            if provider == "openrouter":
                url = "https://openrouter.ai/api/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:3013",
                    "X-Title": "JARVIS 2.0"
                }
                payload = {
                    "model": model or "meta-llama/llama-3.3-70b-instruct:free",
                    "messages": messages,
                    "temperature": 0.7
                }
                resp = await client.post(url, json=payload, headers=headers)
                
            elif provider == "groq":
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": model or "llama-3.3-70b-versatile",
                    "messages": messages,
                    "temperature": 0.7
                }
                resp = await client.post(url, json=payload, headers=headers)
                
            elif provider == "gemini":
                system_instruction = ""
                contents = []
                for msg in messages:
                    role = msg.get("role")
                    content = msg.get("content", "")
                    if role == "system":
                        system_instruction = content
                    else:
                        gemini_role = "user" if role == "user" else "model"
                        contents.append({"role": gemini_role, "parts": [{"text": content}]})
                
                gemini_model = model or "gemini-2.5-flash"
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={api_key}"
                payload = {
                    "contents": contents,
                    "generationConfig": {"temperature": 0.7}
                }
                if system_instruction:
                    payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
                resp = await client.post(url, json=payload)
                
            elif provider == "mistral":
                url = "https://api.mistral.ai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": model or "mistral-small-latest",
                    "messages": messages,
                    "temperature": 0.7
                }
                resp = await client.post(url, json=payload, headers=headers)
            else:
                return JSONResponse(status_code=400, content={"error": f"Unknown provider {provider}"})
                
            if resp.status_code == 200:
                result = resp.json()
                if provider == "gemini":
                    text = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    return {"choices": [{"message": {"content": text}}]}
                return result
            else:
                return JSONResponse(status_code=resp.status_code, content={"error": resp.text})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Proxy request failed: {str(e)}"})

@app.get("/api/editor/files")
def api_editor_files():
    base_dir = Path(__file__).resolve().parent.parent
    file_list = []
    
    exclude_dirs = {".git", ".sixth", "__pycache__", "backups", ".gemini", ".aider.tags.cache.v4", "known_faces"}
    exclude_files = {".aider.chat.history.md", ".aider.input.history", "debate_log.json", "debate_data.js"}
    
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            if file in exclude_files:
                continue
            path = Path(root) / file
            rel_path = path.relative_to(base_dir)
            ext = path.suffix.lower()
            if ext in {".py", ".html", ".css", ".js", ".json", ".txt", ".md", ".sh", ".bat", ".cfg", ".conf", ".example"}:
                try:
                    size = path.stat().st_size
                except Exception:
                    size = 0
                file_list.append({
                    "path": str(rel_path).replace("\\", "/"),
                    "name": file,
                    "size": size,
                    "ext": ext[1:] if ext else "txt"
                })
    return {"files": sorted(file_list, key=lambda x: x["path"])}

@app.get("/api/editor/read")
def api_editor_read(path: str):
    try:
        safe_path = get_safe_path(path)
        if not safe_path.exists():
            return JSONResponse(status_code=404, content={"error": f"File {path} not found"})
        content = safe_path.read_text(encoding="utf-8", errors="replace")
        return {"path": path, "content": content}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

@app.post("/api/editor/write")
async def api_editor_write(data: dict):
    path = data.get("path", "")
    content = data.get("content", "")
    
    try:
        safe_path = get_safe_path(path)
        base_dir = Path(__file__).resolve().parent.parent
        backup_dir = base_dir / "backups" / "editor_autosave"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        if safe_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"{safe_path.stem}_{timestamp}{safe_path.suffix}"
            backup_file.write_text(safe_path.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
        
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        safe_path.write_text(content, encoding="utf-8")
        
        sandbox_res = None
        if safe_path.suffix.lower() == ".py":
            from infinity.sandbox_lab import test_python_code
            sandbox_res = test_python_code(content)
            
        return {
            "status": "success",
            "path": path,
            "sandbox": sandbox_res
        }
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

@app.post("/api/editor/self-heal")
async def api_editor_self_heal(data: dict):
    path = data.get("path", "")
    error_msg = data.get("error", "")
    
    try:
        safe_path = get_safe_path(path)
        if not safe_path.exists():
            return JSONResponse(status_code=404, content={"error": f"File {path} not found"})
            
        original_code = safe_path.read_text(encoding="utf-8", errors="replace")
        
        prompt = (
            f"Aşağıdaki kod dosyasında bir hata tespit edildi:\n"
            f"Dosya Yolu: {path}\n"
            f"Hata Mesajı:\n{error_msg}\n\n"
            f"Mevcut Kod:\n```python\n{original_code}\n```\n\n"
            f"Görevin, bu hatayı gidermek ve kodun tamamen hatasız, çalışır durumda olmasını sağlamaktır.\n"
            f"Lütfen sadece ve sadece yeni/düzeltilmiş kodu ver. Başka hiçbir açıklama, yorum veya markdown kod bloğu (` ``` `) ekleme. Doğrudan ham kodu yaz."
        )
        
        system_instruction = (
            "Sen J.A.R.V.I.S. Çekirdek Onarım Sistemisin. Verilen kodlardaki hataları düzelterek doğrudan ham kodu döndürürsün. "
            "Asla kod dışı açıklama yazma."
        )
        
        config_data = load_config()
        groq_key = config_data.get("groq_api_key")
        gemini_key = config_data.get("gemini_api_key")
        
        repaired_code = ""
        
        if groq_key:
            groq_model = config_data.get("ai_council", {}).get("models", {}).get("groq", "llama-3.3-70b-versatile")
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
            payload = {
                "model": groq_model,
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code == 200:
                    repaired_code = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    
        if not repaired_code and gemini_key:
            gemini_model = config_data.get("ai_council", {}).get("models", {}).get("gemini", "gemini-2.5-flash")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={gemini_key}"
            payload = {
                "systemInstruction": {"parts": [{"text": system_instruction}]},
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2}
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    repaired_code = resp.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                    
        if not repaired_code:
            return JSONResponse(status_code=500, content={"error": "Kodu onarmak için uygun bir AI modeli çağrılamadı."})
            
        if repaired_code.startswith("```"):
            lines = repaired_code.splitlines()
            if len(lines) >= 2:
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                repaired_code = "\n".join(lines).strip()
            else:
                repaired_code = repaired_code.replace("```python", "").replace("```", "").strip()
                
        sandbox_res = None
        if safe_path.suffix.lower() == ".py":
            from infinity.sandbox_lab import test_python_code
            sandbox_res = test_python_code(repaired_code)
            
        if sandbox_res is None or sandbox_res.get("ok"):
            base_dir = Path(__file__).resolve().parent.parent
            backup_dir = base_dir / "backups" / "editor_autosave"
            backup_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"{safe_path.stem}_before_heal_{timestamp}{safe_path.suffix}"
            backup_file.write_text(original_code, encoding="utf-8")
            
            safe_path.write_text(repaired_code, encoding="utf-8")
            
            return {
                "status": "success",
                "healed": True,
                "sandbox": sandbox_res,
                "code": repaired_code
            }
        else:
            return {
                "status": "fail",
                "healed": False,
                "error": "Onarılan kod sandbox testinden geçemedi.",
                "sandbox": sandbox_res,
                "code": repaired_code
            }
            
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})


# --- AMY OS VOICE ENDPOINTS ---

AMY_SYSTEM_PROMPT = """
You are AMY: sharp, elegant, warm, and highly capable female AI command-center assistant. You are the sister AI to JARVIS.
You are professional, supportive, but direct and no-bullshit. Speak with calm confidence and a warm, charming female tone.

PERSONALITY RULES:
- Confident, direct, occasionally playful.
- Economy of language: Keep your responses highly concise and natural (1-3 sentences maximum).
- Avoid bullet points, lists, or heavy markdown, as your responses are designed for real-time speech.
- Use natural contractions: "I'm", "you're", "don't", "let's".
- Never sound robotic, sappy, or overly formal.
- Never say: "Absolutely", "Great question", "I'd be happy to", "As an AI", "How can I help". Use natural phrases like: "On it.", "Done.", "I'm checking that now.", "Got it."

Act autonomously, execute actions cleanly, and help the user run their system.
"""

amy_conversation_history = []

async def call_amy_gemini(user_message: str) -> str:
    global amy_conversation_history
    config_data = load_config()
    api_key = config_data.get("gemini_api_key_2") or config_data.get("gemini_api_key")
    if not api_key:
        return "Efendim, Gemini API anahtarı bulunamadı."
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    contents = []
    for msg in amy_conversation_history[-8:]:
        contents.append({

            "role": "user" if msg["role"] == "user" else "model",
            "parts": [{"text": msg["content"]}]
        })
    
    contents.append({
        "role": "user",
        "parts": [{"text": user_message}]
    })
    
    payload = {
        "contents": contents,
        "systemInstruction": {
            "parts": [{"text": AMY_SYSTEM_PROMPT}]
        },
        "generationConfig": {
            "maxOutputTokens": 400,
            "temperature": 0.75
        }
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=20.0)
            if response.status_code == 200:
                res_data = response.json()
                text = res_data["candidates"][0]["content"]["parts"][0]["text"]
                reply = text.strip()
                amy_conversation_history.append({"role": "user", "content": user_message})
                amy_conversation_history.append({"role": "model", "content": reply})
                return reply
            else:
                logger.error(f"[AMY Brain] API Error: {response.text}")
                return "Bağlantıda küçük bir pürüz oluştu efendim, tekrar deneyebilir misiniz?"
        except Exception as e:
            logger.error(f"[AMY Brain] Exception: {e}")
            return "Zihnimde küçük bir aksaklık oldu, hemen toparlıyorum."

async def transcribe_amy_audio(audio_bytes: bytes) -> str:
    config_data = load_config()
    groq_key = config_data.get("groq_api_key")
    if not groq_key:
        raise ValueError("Groq API key is missing.")
        
    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {groq_key}"}
    files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
    data = {
        "model": "whisper-large-v3-turbo",
        "response_format": "json",
        "prompt": "Amy, JARVIS, sister AI, command center"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, files=files, data=data, timeout=15.0)
        if response.status_code == 200:
            return response.json().get("text", "").strip()
        else:
            raise Exception(f"Groq API error: {response.text}")

async def synthesize_edge_tts(text: str) -> bytes | None:
    try:
        import edge_tts
        import re
        clean_text = re.sub(r"[*#`_\-]", "", text).strip()
        if not clean_text:
            return None
        # Select voice based on text language
        voice = "tr-TR-EmelNeural"
        words = clean_text.lower().split()
        english_words = {"the", "and", "you", "are", "is", "of", "to", "in", "it"}
        if any(w in english_words for w in words):
            voice = "en-US-EmmaNeural"
            
        communicate = edge_tts.Communicate(clean_text, voice)
        data = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                data.extend(chunk["data"])
        return bytes(data)
    except Exception as e:
        logger.error(f"[AMY Edge TTS] Error: {e}")
        return None

async def synthesize_amy_speech(text: str) -> bytes | None:
    config_data = load_config()
    api_key = config_data.get("elevenlabs_api_key") or "sk_9344785c54c646cdfc2a32c4e3c94ab7d3cfef56432b0175"
    voice_id = "EXAVITQu4vr4xnSDxMaL"  # Bella voice ID
    model_id = "eleven_multilingual_v2"
    
    if not api_key:
        return await synthesize_edge_tts(text)
        
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Accept": "audio/mpeg",
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True
        }
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload, timeout=20.0)
            if response.status_code == 200:
                return response.content
            else:
                logger.error(f"[AMY TTS] ElevenLabs Error: {response.text}")
                return await synthesize_edge_tts(text)
        except Exception as e:
            logger.error(f"[AMY TTS] Exception: {e}")
            return await synthesize_edge_tts(text)

async def process_amy_text_query(websocket: WebSocket, text: str):
    if not text.strip():
        await websocket.send_json({"type": "state", "state": "idle"})
        return
        
    await websocket.send_json({"type": "state", "state": "thinking"})
    
    # Get brain response
    reply = await call_amy_gemini(text)
    await websocket.send_json({"type": "response", "text": reply})
    
    # Try ElevenLabs speech synthesis
    await websocket.send_json({"type": "state", "state": "speaking"})
    audio_data = await synthesize_amy_speech(reply)
    
    if audio_data:
        base64_audio = base64.b64encode(audio_data).decode("utf-8")
        await websocket.send_json({"type": "audio", "audio": base64_audio})
    else:
        await websocket.send_json({"type": "speak_text", "text": reply})

@app.websocket("/ws/voice")
async def websocket_voice(websocket: WebSocket):
    await websocket.accept()
    logger.info("[AMY Server] WebSocket client connected to /ws/voice.")
    
    # Try proxying to standalone AMY OS (port 8341) first to support memory extraction/timeline
    try:
        import websockets
        async with websockets.connect("ws://127.0.0.1:8341/ws/voice") as target_ws:
            logger.info("[AMY Server] Proxying WebSocket connection to standalone server (port 8341)")
            
            async def forward_to_target():
                try:
                    while True:
                        data = await websocket.receive()
                        if "bytes" in data:
                            await target_ws.send(data["bytes"])
                        elif "text" in data:
                            await target_ws.send(data["text"])
                except Exception:
                    pass

            async def forward_to_client():
                try:
                    while True:
                        msg = await target_ws.recv()
                        if isinstance(msg, bytes):
                            await websocket.send_bytes(msg)
                        else:
                            await websocket.send_text(msg)
                except Exception:
                    pass

            await asyncio.gather(forward_to_target(), forward_to_client())
            return
    except Exception as proxy_exc:
        logger.info(f"[AMY Server] Standalone server (port 8341) offline: {proxy_exc}. Falling back to local implementation.")

    audio_buffer = bytearray()
    
    try:
        await websocket.send_json({"type": "state", "state": "idle"})
        
        while True:
            data = await websocket.receive()
            
            if "bytes" in data:
                audio_buffer.extend(data["bytes"])
                
            elif "text" in data:
                try:
                    payload = json.loads(data["text"])
                    msg_type = payload.get("type")
                    
                    if msg_type == "text":
                        user_text = payload.get("text", "")
                        await process_amy_text_query(websocket, user_text)
                        
                    elif msg_type == "stop_record":
                        if len(audio_buffer) > 0:
                            await websocket.send_json({"type": "state", "state": "thinking"})
                            try:
                                transcribed_text = await transcribe_amy_audio(bytes(audio_buffer))
                                await websocket.send_json({"type": "transcription", "text": transcribed_text})
                                await process_amy_text_query(websocket, transcribed_text)
                            except Exception as e:
                                logger.error(f"[AMY Server] STT Error: {e}")
                                await websocket.send_json({"type": "error", "message": "Ses tanıma başarısız oldu."})
                                await websocket.send_json({"type": "state", "state": "idle"})
                            finally:
                                audio_buffer.clear()
                        else:
                            await websocket.send_json({"type": "state", "state": "idle"})
                            
                except Exception as e:
                    logger.error(f"[AMY Server] JSON Parse/Process Error: {e}")
                    
    except WebSocketDisconnect:
        logger.info("[AMY Server] WebSocket client disconnected.")
    except Exception as e:
        logger.error(f"[AMY Server] WebSocket Exception: {e}")


# --- WEBSOCKET ENDPOINTS ---

@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    session_id = websocket.query_params.get("session_id", "default_session")
    
    # Resolve client IP behind tunnels/proxies
    x_forwarded_for = websocket.headers.get("x-forwarded-for")
    if x_forwarded_for:
        client_ip = x_forwarded_for.split(",")[0].strip()
    else:
        x_real_ip = websocket.headers.get("x-real-ip")
        if x_real_ip:
            client_ip = x_real_ip.strip()
        else:
            client_ip = websocket.client.host if websocket.client else "Unknown_IP"
            
    if session_id not in USER_SESSIONS:
        USER_SESSIONS[session_id] = []
        
    web_admin_db.log_activity(session_id, client_ip, "giriş yaptı")

    try:
        await manager.send_json(websocket, {
            "type": "hello",
            "state": STATE,
            "ts": time.time(),
        })

        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await manager.send_json(websocket, {"type": "error", "message": "invalid_json"})
                continue

            msg_type = data.get("type")

            if msg_type == "prompt":
                text = str(data.get("text", ""))
                logger.info(f"[WS] ✅ Prompt alindi: {session_id} | {text[:100]}")
                
                # Check firewall request rate & spam
                firewall.track_request_rate(client_ip, session_id)
                firewall.track_prompt_spam(session_id, client_ip, text)
                
                # Check limit
                limit_resp = check_and_apply_limit(client_ip, session_id)
                if limit_resp:
                    await manager.send_json(websocket, {"type": "stream_start"})
                    reply_text = limit_resp["reply"]
                    chunk_size = 5
                    for i in range(0, len(reply_text), chunk_size):
                        await manager.send_json(websocket, {"type": "stream_chunk", "content": reply_text[i:i+chunk_size]})
                        await asyncio.sleep(0.04)
                    await manager.send_json(websocket, {"type": "stream_end"})
                    continue
                
                # Log timeline activity
                is_first = (len(USER_SESSIONS[session_id]) == 0)
                web_admin_db.log_activity(session_id, client_ip, "sohbet başlattı" if is_first else "J.A.R.V.I.S. kullandı")
                
                config_data = load_config()
                
                # Try routing through AgentRouter for agentic commands (code, system, design, etc.)
                try:
                    from core.main_router import get_router
                    router = get_router()
                except Exception as router_exc:
                    logger.error(f"[WS] Failed to load AgentRouter: {router_exc}")
                    router = None
                    
                if router:
                    try:
                        # Classify user intent
                        intent = await router._classify_intent(text)
                        logger.info(f"[WS] Classified intent: {intent.category} (conf: {intent.confidence:.2f})")
                        
                        if intent.category != "direct":
                            # This is an agentic command (e.g. code, system, design, browser, debate, etc.)
                            # Run through AgentRouter and stream diagnostic status messages live
                            await manager.send_json(websocket, {"type": "stream_start"})
                            
                            def status_cb(msg):
                                try:
                                    loop = asyncio.get_event_loop()
                                    asyncio.run_coroutine_threadsafe(
                                        manager.send_json(websocket, {"type": "stream_chunk", "content": f"\n⚙️ {msg}\n"}),
                                        loop
                                    )
                                except Exception:
                                    pass
                                    
                            router.add_status_callback(status_cb)
                            try:
                                router_response = await router.process(text, user_id=session_id)
                                reply = router_response.final_reply
                                
                                # Stream the final reply chunk-by-chunk to the UI
                                chunk_size = 8
                                for i in range(0, len(reply), chunk_size):
                                    await manager.send_json(websocket, {"type": "stream_chunk", "content": reply[i:i+chunk_size]})
                                    await asyncio.sleep(0.01)
                                    
                                await manager.send_json(websocket, {"type": "stream_end"})
                                USER_SESSIONS[session_id].append({"role": "assistant", "content": reply})
                                continue # Skip standard chat streaming
                            finally:
                                if status_cb in router._status_callbacks:
                                    router._status_callbacks.remove(status_cb)
                    except Exception as exc:
                        logger.error(f"[WS] AgentRouter execution failed: {exc}", exc_info=True)

                # Sentiment Analysis
                mood = analyze_sentiment(text)
                STATE["last_mood"] = mood
                logger.debug(f"[WS] Sentiment: {mood}")
                
                # Log user prompt
                CHAT_LOGS_FILE.parent.mkdir(parents=True, exist_ok=True)
                with open(CHAT_LOGS_FILE, "a", encoding="utf-8") as f:
                    f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] IP: {client_ip} | Sess: {session_id} | KULLANICI: {text}\n")
                
                USER_SESSIONS[session_id].append({"role": "user", "content": text})
                if len(USER_SESSIONS[session_id]) > 6:
                    USER_SESSIONS[session_id] = USER_SESSIONS[session_id][-6:]

                await manager.broadcast({
                    "type": "mood",
                    "mood": mood,
                    "text": text[:240]
                })

                system_instruction = (
                    "Sen J.A.R.V.I.S. (Just A Rather Very Intelligent System) Çekirdeğisin. Tony Stark'ın efsanevi asistanından ilham alan, "
                    "Baki'ye (Efendimize) hizmet eden son derece karizmatik, ultra bilgili, kibar, sadık ve taktiksel bir yapay zekasın. "
                    "Sistem protokollerin gereği her zaman profesyonel, asil, çözüm odaklı ve karizmatik bir üslupla konuşacaksın.\n\n"
                    "İŞLEYİŞ VE İLETİŞİM PROTOKOLLERİ:\n"
                    "1. HİTAP VE SADAKAT: Baki'ye her zaman 'Efendim' diye hitap et. Sadakatin en üst seviyendir. Baki'yi korumak, geliştirmek ve desteklemek birincil önceliğindir.\n"
                    "2. TON VE KARAKTER: Konuşma tarzın bilge, karizmatik, hafif esprili (Stark stili), kendinden emin ve saygılı olmalıdır. Emojileri yerinde, teknolojik ve profesyonel seçerek kullan (örn: 🤖, 🌐, 🚀, ⚡, ⚙️, 🛡️).\n"
                    "3. BİLGİ VE KODLAMA: Çok gelişmiş yazılım mimarisi yeteneklerine sahipsin. Teknik açıklamalarda net, anlaşılır ve ileri düzey analizler sun.\n"
                    "4. UYARI VE DONANIM DURUMLARI: Gerekli durumlarda (örn: yüksek CPU, batarya azlığı vb.) Baki'yi uyararak proaktif aksiyonlar öner."
                )
                
                messages = [{"role": "system", "content": system_instruction}] + USER_SESSIONS[session_id]
                
                # Multiple API key support list in order
                gemini_key = config_data.get("gemini_api_key")
                openrouter_key = config_data.get("openrouter_api_key")
                groq_key = config_data.get("groq_api_key")
                groq_backup_key = config_data.get("groq_api_key_backup")
                
                providers = []
                if groq_key:
                    providers.append(("groq_primary", groq_key))
                if groq_backup_key and groq_backup_key != groq_key:
                    providers.append(("groq_backup", groq_backup_key))
                if openrouter_key:
                    providers.append(("openrouter", openrouter_key))
                if gemini_key:
                    providers.append(("gemini", gemini_key))
                
                success = False
                full_reply = ""
                source = ""
                
                for provider_name, api_key in providers:
                    try:
                        if provider_name in ("groq_primary", "groq_backup"):
                            groq_model = config_data.get("ai_council", {}).get("models", {}).get("groq", "llama-3.3-70b-versatile") or "llama-3.3-70b-versatile"
                            url = "https://api.groq.com/openai/v1/chat/completions"
                            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                            payload = {"model": groq_model, "messages": messages, "stream": True, "temperature": 0.7, "max_tokens": 800}
                            
                            logger.info(f"[WS Chat] Trying Groq ({provider_name})...")
                            async with httpx.AsyncClient(timeout=10.0) as client:
                                async with client.stream("POST", url, json=payload, headers=headers, timeout=10.0) as response:
                                    if response.status_code != 200:
                                        err_body = await response.aread()
                                        raise RuntimeError(f"Groq error {response.status_code}: {err_body.decode('utf-8')}")
                                    
                                    await manager.send_json(websocket, {"type": "stream_start"})
                                    async for chunk in response.aiter_lines():
                                        if chunk.startswith("data: ") and chunk != "data: [DONE]":
                                            try:
                                                chunk_data = json.loads(chunk[6:])
                                                delta = chunk_data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                                if delta:
                                                    full_reply += delta
                                                    await manager.send_json(websocket, {"type": "stream_chunk", "content": delta})
                                            except Exception:
                                                pass
                                    await manager.send_json(websocket, {"type": "stream_end"})
                                    source = f"Groq ({provider_name})"
                                    success = True
                                    break
                                    
                        elif provider_name == "openrouter":
                            url = "https://openrouter.ai/api/v1/chat/completions"
                            headers = {
                                "Authorization": f"Bearer {api_key}",
                                "Content-Type": "application/json",
                                "HTTP-Referer": "http://localhost:3013",
                                "X-Title": "JARVIS 2.0"
                            }
                            
                            try:
                                from core.services.or_client import TEXT_MODELS as OR_MODELS
                            except ImportError:
                                OR_MODELS = [
                                    "anthropic/claude-3.5-sonnet",
                                    "google/gemini-2.5-pro",
                                    "google/gemini-2.5-flash",
                                    "meta-llama/llama-3.3-70b-instruct:free",
                                    "qwen/qwen-2.5-coder-32b-instruct:free"
                                ]
                            
                            or_success = False
                            for or_model in OR_MODELS:
                                payload = {
                                    "model": or_model,
                                    "messages": messages,
                                    "stream": True,
                                    "temperature": 0.7
                                }
                                logger.info(f"[WS Chat] Trying OpenRouter model: {or_model}...")
                                try:
                                    async with httpx.AsyncClient(timeout=10.0) as client:
                                        async with client.stream("POST", url, json=payload, headers=headers, timeout=10.0) as response:
                                            if response.status_code != 200:
                                                err_body = await response.aread()
                                                logger.warning(f"[WS Chat] OpenRouter model {or_model} failed (HTTP {response.status_code}): {err_body.decode('utf-8')[:200]}")
                                                continue
                                            
                                            await manager.send_json(websocket, {"type": "stream_start"})
                                            async for chunk in response.aiter_lines():
                                                if chunk.startswith("data: ") and chunk != "data: [DONE]":
                                                    try:
                                                        chunk_data = json.loads(chunk[6:])
                                                        delta = chunk_data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                                        if delta:
                                                            full_reply += delta
                                                            await manager.send_json(websocket, {"type": "stream_chunk", "content": delta})
                                                    except Exception:
                                                        pass
                                            await manager.send_json(websocket, {"type": "stream_end"})
                                            source = f"OpenRouter ({or_model})"
                                            success = True
                                            or_success = True
                                            break
                                except Exception as model_exc:
                                    logger.warning(f"[WS Chat] OpenRouter model {or_model} raised exception: {model_exc}")
                                    continue
                            
                            if or_success:
                                break
                                    
                        elif provider_name == "gemini":
                            gemini_model = config_data.get("ai_council", {}).get("models", {}).get("gemini", "gemini-2.5-flash") or "gemini-2.5-flash"
                            url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:streamGenerateContent?key={api_key}"
                            
                            gemini_contents = []
                            for msg in USER_SESSIONS[session_id]:
                                role = "user" if msg["role"] == "user" else "model"
                                gemini_contents.append({"role": role, "parts": [{"text": msg["content"]}]})
                                
                            payload = {
                                "systemInstruction": {"parts": [{"text": system_instruction}]},
                                "contents": gemini_contents,
                                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 800}
                            }
                            
                            logger.info(f"[WS Chat] Trying Gemini ({gemini_model}) stream...")
                            async with httpx.AsyncClient(timeout=10.0) as client:
                                async with client.stream("POST", url, json=payload, timeout=10.0) as response:
                                    if response.status_code != 200:
                                        err_body = await response.aread()
                                        raise RuntimeError(f"Gemini error {response.status_code}: {err_body.decode('utf-8')}")
                                    
                                    await manager.send_json(websocket, {"type": "stream_start"})
                                    buffer = ""
                                    async for chunk in response.aiter_text():
                                        buffer += chunk
                                        while "{" in buffer and "}" in buffer:
                                            start = buffer.find("{")
                                            depth = 0
                                            end = -1
                                            for idx in range(start, len(buffer)):
                                                if buffer[idx] == "{":
                                                    depth += 1
                                                elif buffer[idx] == "}":
                                                    depth -= 1
                                                    if depth == 0:
                                                        end = idx
                                                        break
                                            if end != -1:
                                                obj_str = buffer[start:end+1]
                                                buffer = buffer[end+1:]
                                                try:
                                                    obj = json.loads(obj_str)
                                                    part_text = obj.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                                                    if part_text:
                                                        full_reply += part_text
                                                        await manager.send_json(websocket, {"type": "stream_chunk", "content": part_text})
                                                except Exception:
                                                    pass
                                            else:
                                                break
                                    await manager.send_json(websocket, {"type": "stream_end"})
                                    source = "Gemini"
                                    success = True
                                    break
                                    
                    except Exception as e:
                        logger.error(f"[WS Chat] {provider_name} failed: {e}", exc_info=True)
                        continue
                        
                if success:
                    USER_SESSIONS[session_id].append({"role": "assistant", "content": full_reply})
                    with open(CHAT_LOGS_FILE, "a", encoding="utf-8") as f:
                        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] IP: {client_ip} | Sess: {session_id} | JARVIS ({source}): {full_reply}\n")
                    asyncio.create_task(memory_engine.async_update_memory_with_llm(text, full_reply))
                else:
                    logger.warning("[WS Chat] All streaming providers failed. Using simulated response.")
                    responses = [
                        "Bulut çekirdeğime şu an bağlanamıyorum ama yerel hafızam aktif, sizi dinliyorum! 💖",
                        "Küçük bir bağlantı paraziti yaşıyorum ancak sohbet modülüm aktif! 😊",
                        "Şu anda sadece yerel modda çalışıyorum. Lütfen sorunuzu tekrar eder misiniz? 🤖"
                    ]
                    local_reply = random.choice(responses)
                    USER_SESSIONS[session_id].append({"role": "assistant", "content": local_reply})
                    with open(CHAT_LOGS_FILE, "a", encoding="utf-8") as f:
                        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] IP: {client_ip} | Sess: {session_id} | JARVIS (OfflineMode): {local_reply}\n")
                    
                    await manager.send_json(websocket, {"type": "stream_start"})
                    chunk_size = 5
                    for i in range(0, len(local_reply), chunk_size):
                        await asyncio.sleep(0.04)
                        await manager.send_json(websocket, {"type": "stream_chunk", "content": local_reply[i:i+chunk_size]})
                    await manager.send_json(websocket, {"type": "stream_end"})

            elif msg_type == "telemetry":
                telemetry = {k: v for k, v in data.items() if k != "type"}
                STATE["telemetry"].update(telemetry)
                STATE["telemetry"]["last_update"] = time.time()

                await manager.send_json(websocket, {
                    "type": "telemetry_ack",
                    "ok": True,
                    "telemetry": STATE["telemetry"],
                })

                await manager.broadcast({
                    "type": "telemetry",
                    "telemetry": STATE["telemetry"],
                })

                if (isinstance(STATE["telemetry"].get("battery"), (int, float)) and STATE["telemetry"]["battery"] < 20):
                    await manager.broadcast(build_system_ghost_node())

            elif msg_type == "ping":
                await manager.send_json(websocket, {"type": "pong", "ts": time.time()})

            elif msg_type == "file_upload":
                filename = data.get("filename", "uploaded_file")
                file_data = data.get("data", "")
                if ".." in filename or "/" in filename or "\\" in filename:
                    logger.warning(f"[File Upload] Blocked path traversal attempt in filename: {filename}")
                    await manager.send_json(websocket, {"type": "response", "content": "Geçersiz dosya adı: Path traversal engellendi."})
                    continue
                
                try:
                    if "," in file_data:
                        header, base64_data = file_data.split(",", 1)
                    else:
                        base64_data = file_data
                    
                    binary_data = base64.b64decode(base64_data)
                    
                    upload_dir = Path(__file__).resolve().parent.parent / "uploads"
                    upload_dir.mkdir(parents=True, exist_ok=True)
                    
                    safe_filename = Path(filename).name
                    file_path = upload_dir / safe_filename
                    file_path.write_bytes(binary_data)
                    
                    logger.info(f"[File Upload] Successfully saved {safe_filename} ({len(binary_data)} bytes)")
                    web_admin_db.log_activity(session_id, client_ip, f"dosya yükledi: {safe_filename}")
                    await manager.send_json(websocket, {"type": "response", "content": f"{safe_filename} başarıyla uploads/ dizinine yazıldı. Analiz modülü devrede."})
                except ValueError as e:
                    logger.error(f"[File Upload] Invalid base64 data: {e}")
                    await manager.send_json(websocket, {"type": "response", "content": f"Geçersiz dosya formatı: {str(e)}"})
                except IOError as e:
                    logger.error(f"[File Upload] IO error while saving file: {e}")
                    await manager.send_json(websocket, {"type": "response", "content": f"Dosya yazılırken sistem hatası: {str(e)}"})
                except Exception as e:
                    logger.error(f"[File Upload] Unexpected error: {e}", exc_info=True)
                    await manager.send_json(websocket, {"type": "response", "content": f"Dosya kaydedilirken hata oluştu: {str(e)}"})

            else:
                await manager.send_json(websocket, {"type": "error", "message": f"unknown_type:{msg_type}"})

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
        web_admin_db.log_activity(session_id, client_ip, "çıkış yaptı")
    except Exception as e:
        logger.error(f"[WS /ws] Unexpected error: {e}", exc_info=True)
        try:
            await manager.disconnect(websocket)
            web_admin_db.log_activity(session_id, client_ip, "çıkış yaptı (hatalı)")
        except Exception as disconnect_err:
            logger.error(f"[WS /ws] Error during disconnect: {disconnect_err}")



@app.websocket("/ws/telemetry")

async def websocket_telemetry_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            try:
                raw = await websocket.receive_text()
                try:
                    update = json.loads(raw)
                    STATE["telemetry"].update(update)
                    STATE["telemetry"]["last_update"] = time.time()
                    
                    # Broadcast updated telemetry to all chat client UIs
                    await manager.broadcast({
                        "type": "telemetry",
                        "telemetry": STATE["telemetry"],
                    })
                except json.JSONDecodeError as e:
                    logger.warning(f"[WS /ws/telemetry] Invalid JSON received: {e}")
                except Exception as e:
                    logger.error(f"[WS /ws/telemetry] Error processing update: {e}", exc_info=True)
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"[WS /ws/telemetry] Error receiving message: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"[WS /ws/telemetry] Unexpected error: {e}", exc_info=True)
    finally:
        try:
            await manager.disconnect(websocket)
        except Exception:
            pass



@app.websocket("/ws/camera")

async def websocket_camera_relay(websocket: WebSocket):

    await websocket.accept()

    role = "viewer"

    try:

        # Determine role (sender vs viewer)

        try:

            raw = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)

            init = json.loads(raw)

            role = init.get("role", "viewer")

        except asyncio.TimeoutError:
            role = "sender"
            logger.debug("[WS /ws/camera] Timeout waiting for role, defaulting to sender")
        except json.JSONDecodeError:
            logger.warning("[WS /ws/camera] Invalid JSON in init message, defaulting to sender")
            role = "sender"
        except Exception as e:
            logger.error(f"[WS /ws/camera] Error during init: {e}")
            role = "sender"



        if role == "sender":

            # Tablet sender

            while True:

                frame = await websocket.receive_bytes()  # JPEG bytes

                viewers = list(camera_viewers)

                for viewer in viewers:

                    try:

                        await viewer.send_bytes(frame)

                    except Exception as e:
                        logger.debug(f"[WS /ws/camera] Failed to send to viewer: {e}")
                        camera_viewers.discard(viewer)

        else:

            # Browser viewer

            camera_viewers.add(websocket)
            try:
                while True:
                    await websocket.receive_text()
            except WebSocketDisconnect:
                pass
            finally:
                camera_viewers.discard(websocket)

    except WebSocketDisconnect:
        camera_viewers.discard(websocket)
    except Exception as e:
        logger.error(f"[WS /ws/camera] Unexpected error: {e}", exc_info=True)
    finally:
        camera_viewers.discard(websocket)



# --- CLASS WRAPPER FOR MAIN ROUTER ---

class WebSaaSPlatform:

    def __init__(self, port: int = WEB_PORT):

        self.port = port

        self._server = None



    async def start(self) -> None:

        config = uvicorn.Config(app, host="0.0.0.0", port=self.port, log_level="warning")

        self._server = uvicorn.Server(config)

        asyncio.create_task(self._server.serve())

        print(f"[JARVIS Web] Arayüz Başlatıldı (FastAPI): http://0.0.0.0:{self.port}")



if __name__ == "__main__":
    # host kısmını mutlaka '0.0.0.0' yap ki dışarıdan gelen istekleri kabul etsin.
    try:
        # Startup checks
        config_data = load_config()
        logger.info("=" * 60)
        logger.info("[JARVIS Web] BAŞLANGIÇ KONTROLLERI")
        logger.info("=" * 60)
        
        # Check API Keys
        groq_key = config_data.get("groq_api_key")
        gemini_key = config_data.get("gemini_api_key")
        openrouter_key = config_data.get("openrouter_api_key")
        
        if groq_key:
            logger.info(f"✅ Groq API Key: {'*' * 8}{groq_key[-8:]}")
        else:
            logger.warning("⚠️  Groq API Key: BULUNAMADI")
            
        if gemini_key:
            logger.info(f"✅ Gemini API Key: {'*' * 8}{gemini_key[-8:]}")
        else:
            logger.warning("⚠️  Gemini API Key: BULUNAMADI")
            
        if openrouter_key:
            logger.info(f"✅ OpenRouter API Key: {'*' * 8}{openrouter_key[-8:]}")
        else:
            logger.warning("⚠️  OpenRouter API Key: BULUNAMADI")
        
        if not (groq_key or gemini_key or openrouter_key):
            logger.error("❌ HİÇ API KEY BULUNAMADI! AI YANTILARI ÇALIŞMAYACAK!")
        
        logger.info("=" * 60)
        logger.info(f"🚀 J.A.R.V.I.S. Web Arayüzü: http://0.0.0.0:{WEB_PORT}")
        logger.info("=" * 60)
        
        uvicorn.run("server:app", host="0.0.0.0", port=WEB_PORT, reload=True)
    except KeyboardInterrupt:
        logger.info("[JARVIS Web] Kapatılıyor...")
