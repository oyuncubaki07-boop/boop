import asyncio
import json
import sys
import threading
import time
import traceback
import urllib.parse
import webbrowser
import os
from pathlib import Path
from typing import Optional

# Ses işleme için yeni Mark XXXIX standardı (PyAudio yerine)
import sounddevice as sd
import pygame
import pyautogui
from google import genai
from google.genai import types

# PyQt6 (ana döngü ve kapatma yönetimi için)
from PyQt6.QtWidgets import QApplication, QInputDialog, QLineEdit
from PyQt6.QtCore import Qt

try:
    from kisilik import JarvisPersonality
except ImportError:
    print("[KRİTİK HATA] kisilik.py bulunamadı.")
    sys.exit(1)

# ================= Google Entegrasyonu =================
from actions.google_integration import google_drive, google_youtube, google_contacts, google_gmail

# ================= Mevcut Tüm Action'lar (MK37 + MK39) =================
from actions.biometric_shield import biometric_shield
from actions.hirsizlik_modu import hirsizlik_modu
from actions.black_box import black_box
from actions.breach_watch import breach_watch
from actions.backup_system import backup_jarvis
from actions.cinema_mode import cinema_mode
from actions.clipboard_module import read_clipboard
from actions.cmd_control import cmd_control
from actions.code_helper import code_helper
from actions.browser_control import browser_control
from actions.kod_rehberi import kod_rehberi
from actions.open_app import open_app
from actions.system_monitor import system_status
from actions.file_controller import file_controller
from actions.whatsapp_call import whatsapp_call
from actions.computer_control import computer_control
from actions.desktop import desktop_control
from actions.text_reader import TextReader
from actions.shutdown_timer import shutdown_timer
from actions.reminder import reminder
from actions.weather_report import weather_action
from actions.morning_alarm import morning_alarm
from actions.keyboard import keyboard_control
from actions.tv_dominance import is_tv_presence_active, set_system_output_volume, tv_dominance
from actions.system_maintenance import system_maintenance
from actions.cyber_sleep import cyber_sleep
from actions.device_manager import scan_devices
from actions.entertainment_mode import entertainment_mode
from actions.feedback_system import report_issue
from actions.focus_mode import focus_mode
from actions.game_updater import game_updater
from actions.ghost_mode import ghost_mode
from actions.guardian_shield import guardian_shield
from actions.hologram_hud import hologram_hud
from actions.macro_automation import activate_mode as macro_automation_mode
from actions.macro_master import macro_master
from actions.media_controller import media_controller
from actions.news_briefing import news_briefing
from actions.observer_mode import observer_mode
from actions.security_mode import security_mode
from actions.shadow_record import shadow_record
from actions.share_location import share_location
from actions.smart_notes import take_note
from actions.smart_reminder import set_reminder
from actions.smart_translator import smart_translator
from actions.social_ghost import social_ghost
from actions.vision_module import vision_scan
from actions.welcome_screen import show_welcome_hologram as show_action_welcome_hologram
from actions.edex_ui import edex_ui
from actions.computer_settings import computer_settings
from actions.dev_agent import dev_agent
from actions.screen_processor import screen_process
from actions.send_message import send_message as send_message_action_impl
from actions.web_search import web_search
from actions.youtube_video import youtube_video
from actions.morning_briefing import morning_briefing
from actions.night_mode import night_mode
from actions.performance_boost import performance_boost
from actions.flight_finder import flight_finder
from actions.evrim_motoru import yeni_ozellik_sentezleme, otonom_dongu_yoneticisi, evrim_durum_raporu
from actions.security_and_focus import (
    ghost_mode as sf_ghost_mode,
    focus_mode as sf_focus_mode,
    lockdown_protocol as sf_lockdown_protocol,
    guardian_shield as sf_guardian_shield,
    breach_watch as sf_breach_watch,
    biometric_shield as sf_biometric_shield,
)

try:
    from actions.gamification import GamificationCore
    from actions.behavior_analyzer import BehaviorAnalyzer
    from actions.event_trigger import EventTriggerSystem
except ImportError:
    GamificationCore = BehaviorAnalyzer = EventTriggerSystem = None

from core.brain import JarvisConsciousness
from core.memory_core import JarvisMemory
from plugins.cyber_eye import CyberEyePlugin
from ui.jarvis_ui import JarvisUI

# ================= MINI MIMARI SERVISLERI =================
from services import get_task_queue, get_camera_service

# ================= HAFIZA YÖNETİMİ =================
try:
    from memory.memory_manager import load_memory, update_memory, format_memory_for_prompt
    MEMORY_MANAGER_AVAILABLE = True
except ImportError:
    MEMORY_MANAGER_AVAILABLE = False
    print("[UYARI] memory_manager bulunamadı, sadece yerel profil hafızası çalışacak.")

# ================= SABİTLER =================
def get_base_dir():
    return Path(__file__).resolve().parent if not getattr(sys, "frozen", False) else Path(sys.executable).parent

BASE_DIR = get_base_dir()
CONFIG_CANDIDATES = [BASE_DIR / "config" / "api_keys.json", BASE_DIR / "ui" / "config" / "api_keys.json"]

LIVE_MODEL = "models/gemini-2.5-flash-native-audio-preview-12-2025"

# Sounddevice ayarları
SEND_RATE = 16000
RECV_RATE = 24000

# ================= API KEY CACHE =================
_cached_api_key = None

def _get_api_key() -> str:
    global _cached_api_key
    if _cached_api_key:
        return _cached_api_key
    for path in CONFIG_CANDIDATES:
        try:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                key = data.get("gemini_api_key", "").strip()
                if key:
                    _cached_api_key = key
                    return key
        except:
            continue
    return ""

def _should_skip_text(text: str) -> bool:
    if not text:
        return True
    normalized = text.strip().lower()
    return normalized.startswith(("crafting", "analyz", "thinking", "internal", "**"))

def _normalize_command_text(text: str) -> str:
    return " ".join((text or "").strip().lower().split())

def _run_evrim_motoru(player=None) -> str:
    yeni_ozellik_sentezleme(player)
    return "Evrim motoru tetiklendi patron."

def _run_security_and_focus_bundle(parameters=None, player=None, root=None) -> str:
    params = parameters or {}
    action = params.get("action", "ghost_mode").strip().lower()
    runners = {
        "ghost_mode": sf_ghost_mode,
        "focus_mode": sf_focus_mode,
        "lockdown_protocol": sf_lockdown_protocol,
        "guardian_shield": sf_guardian_shield,
        "breach_watch": sf_breach_watch,
        "biometric_shield": sf_biometric_shield,
    }
    fn = runners.get(action)
    if not fn:
        return f"Geçerli action bulunamadı: {action}"
    return fn(parameters=params, player=player, root=root)

def _run_action_welcome_screen(root=None) -> str:
    if not root:
        return "Arayüz kökü yok."
    show_action_welcome_hologram(root)
    return "Welcome screen açıldı."

def _open_edex_panel(player=None, root=None) -> str:
    return edex_ui(parameters={"monitor_name": "ASUS VW193D"}, player=player, root=root)

# ================= TOOL DECLARATIONS =================
TOOL_DECLARATIONS = [
    {"name": "biometric_shield", "description": "Biyometrik güvenlik kalkanını açar.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "hirsizlik_modu", "description": "Hırsızlık / tehdit modunu açar. Alarm, kırmızı ekran ve Spotify'da müzik çalar.", "parameters": {"type": "OBJECT", "properties": {"action": {"type": "STRING"}}}},
    {"name": "keyboard_control", "description": "Klavye kontrolü.", "parameters": {"type": "OBJECT", "properties": {"key": {"type": "STRING"}}}},
    {"name": "black_box", "description": "Sistem tanılama.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "breach_watch", "description": "Veri sızıntısı taraması.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "google_drive", "description": "Google Drive işlemleri (dosya yükleme/listeleme).", "parameters": {"type": "OBJECT", "properties": {"action": {"type": "STRING"}, "file_path": {"type": "STRING"}, "file_name": {"type": "STRING"}}}},
    {"name": "google_youtube", "description": "YouTube'a video yükler.", "parameters": {"type": "OBJECT", "properties": {"video_path": {"type": "STRING"}, "title": {"type": "STRING"}, "description": {"type": "STRING"}}}},
    {"name": "google_contacts", "description": "Google Kişileri listeler.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "google_gmail", "description": "Gmail üzerinden e-posta gönderir.", "parameters": {"type": "OBJECT", "properties": {"to": {"type": "STRING"}, "subject": {"type": "STRING"}, "body": {"type": "STRING"}}}},
    {"name": "backup_jarvis", "description": "Sistemi yedekler.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "cinema_mode", "description": "Sinema modu.", "parameters": {"type": "OBJECT", "properties": {"action": {"type": "STRING"}}}},
    {"name": "read_clipboard", "description": "Panodaki metni okur.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "cmd_control", "description": "Terminal komutları.", "parameters": {"type": "OBJECT", "properties": {"task": {"type": "STRING"}, "command": {"type": "STRING"}}}},
    {"name": "code_helper", "description": "Kod asistanı.", "parameters": {"type": "OBJECT", "properties": {"action": {"type": "STRING"}, "file_path": {"type": "STRING"}, "code": {"type": "STRING"}}}},
    {"name": "kod_rehberi", "description": "Komut rehberini gösterir.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "read_document", "description": "Doküman okur.", "parameters": {"type": "OBJECT", "properties": {"file_path": {"type": "STRING"}}}},
    {"name": "browser_control", "description": "Tarayıcı kontrolü.", "parameters": {"type": "OBJECT", "properties": {"action": {"type": "STRING"}, "url": {"type": "STRING"}, "query": {"type": "STRING"}}}},
    {"name": "open_app", "description": "Uygulama açar.", "parameters": {"type": "OBJECT", "properties": {"app_name": {"type": "STRING"}}}},
    {"name": "system_status", "description": "Sistem durumu.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "file_controller", "description": "Dosya işlemleri.", "parameters": {"type": "OBJECT", "properties": {"action": {"type": "STRING"}, "path": {"type": "STRING"}}}},
    {"name": "computer_control", "description": "Klavye/fare makro.", "parameters": {"type": "OBJECT", "properties": {"action": {"type": "STRING"}, "text": {"type": "STRING"}, "keys": {"type": "STRING"}}}},
    {"name": "desktop_control", "description": "Masaüstü düzenleme.", "parameters": {"type": "OBJECT", "properties": {"action": {"type": "STRING"}, "path": {"type": "STRING"}}}},
    {"name": "shutdown_timer", "description": "Kapanma zamanlayıcısı.", "parameters": {"type": "OBJECT", "properties": {"minutes": {"type": "NUMBER"}, "action": {"type": "STRING"}}}},
    {"name": "reminder", "description": "Hatırlatıcı kurar.", "parameters": {"type": "OBJECT", "properties": {"minutes": {"type": "NUMBER"}, "message": {"type": "STRING"}}}},
    {"name": "weather_action", "description": "Hava durumu.", "parameters": {"type": "OBJECT", "properties": {"city": {"type": "STRING"}}}},
    {"name": "send_message", "description": "WhatsApp mesaj gönderir (sadece uygulama).", "parameters": {"type": "OBJECT", "properties": {"receiver": {"type": "STRING"}, "message_text": {"type": "STRING"}}}},
    {"name": "morning_alarm", "description": "Sabah alarmı.", "parameters": {"type": "OBJECT", "properties": {"time": {"type": "STRING"}}}},
    {"name": "tv_dominance", "description": "TV kontrol.", "parameters": {"type": "OBJECT", "properties": {"action": {"type": "STRING"}}}},
    {"name": "system_maintenance", "description": "Bakım.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "network_status", "description": "Ağ durumu.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "cyber_sleep", "description": "Uyku modu.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "whatsapp_call", "description": "WhatsApp üzerinden sesli veya görüntülü arama yapar.", "parameters": {"type": "OBJECT", "properties": {"receiver": {"type": "STRING"}, "call_type": {"type": "STRING", "description": "voice veya video"}}}}, 
    {"name": "cyber_eye_control", "description": "Siber Göz.", "parameters": {"type": "OBJECT", "properties": {"action": {"type": "STRING"}}}},
    {"name": "scan_devices", "description": "Cihaz tarama.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "entertainment_mode", "description": "Eğlence modu.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "report_issue", "description": "Hata bildir.", "parameters": {"type": "OBJECT", "properties": {"message": {"type": "STRING"}}}},
    {"name": "focus_mode", "description": "Odak modu.", "parameters": {"type": "OBJECT", "properties": {"action": {"type": "STRING"}}}},
    {"name": "game_updater", "description": "Oyunları günceller (Steam/Epic).", "parameters": {"type": "OBJECT", "properties": {"action": {"type": "STRING"}, "platform": {"type": "STRING"}, "game_name": {"type": "STRING"}, "app_id": {"type": "STRING"}}}},
    {"name": "ghost_mode", "description": "Gizlilik modu.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "guardian_shield", "description": "Koruma kalkanı.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "hologram_hud", "description": "Holografik HUD.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "macro_automation_mode", "description": "Makro otomasyon.", "parameters": {"type": "OBJECT", "properties": {"mode": {"type": "STRING"}, "action": {"type": "STRING"}}}},
    {"name": "macro_master", "description": "Makro ustası.", "parameters": {"type": "OBJECT", "properties": {"action": {"type": "STRING"}, "clicks": {"type": "NUMBER"}}}},
    {"name": "media_controller", "description": "Medya kontrol.", "parameters": {"type": "OBJECT", "properties": {"action": {"type": "STRING"}}}},
    {"name": "news_briefing", "description": "Haber özeti.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "observer_mode", "description": "Gözlem modu.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "security_mode", "description": "Güvenlik modu (çift kamera).", "parameters": {"type": "OBJECT", "properties": {"action": {"type": "STRING"}}}},
    {"name": "shadow_record", "description": "Gölge kayıt.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "share_location", "description": "Konum paylaş.", "parameters": {"type": "OBJECT", "properties": {"contact_name": {"type": "STRING"}}}},
    {"name": "take_note", "description": "Not al.", "parameters": {"type": "OBJECT", "properties": {"note_text": {"type": "STRING"}}}},
    {"name": "set_reminder", "description": "Hatırlatıcı kur.", "parameters": {"type": "OBJECT", "properties": {"minutes": {"type": "NUMBER"}, "message": {"type": "STRING"}}}},
    {"name": "smart_translator", "description": "Çevirmen.", "parameters": {"type": "OBJECT", "properties": {"language": {"type": "STRING"}}}},
    {"name": "social_ghost", "description": "Sosyal analiz.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "vision_scan", "description": "Kamera analizi.", "parameters": {"type": "OBJECT", "properties": {"prompt": {"type": "STRING"}}}},
    {"name": "action_welcome_screen", "description": "Welcome screen.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "edex_ui_panel", "description": "Edex panel.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "computer_settings", "description": "Bilgisayar ayarları.", "parameters": {"type": "OBJECT", "properties": {"task": {"type": "STRING"}, "action": {"type": "STRING"}, "value": {"type": "STRING"}}}},
    {"name": "dev_agent", "description": "Kod ajan.", "parameters": {"type": "OBJECT", "properties": {"task": {"type": "STRING"}, "description": {"type": "STRING"}, "language": {"type": "STRING"}}}},
    {"name": "screen_process", "description": "Ekran işleme.", "parameters": {"type": "OBJECT", "properties": {"action": {"type": "STRING"}}}},
    {"name": "send_message_action", "description": "Alternatif mesaj.", "parameters": {"type": "OBJECT", "properties": {"receiver": {"type": "STRING"}, "message_text": {"type": "STRING"}}}},
    {"name": "web_search", "description": "Web arama.", "parameters": {"type": "OBJECT", "properties": {"query": {"type": "STRING"}, "action": {"type": "STRING"}, "aspect": {"type": "STRING"}}}},
    {"name": "youtube_video", "description": "YouTube aç.", "parameters": {"type": "OBJECT", "properties": {"query": {"type": "STRING"}}}},
    {"name": "morning_briefing", "description": "Sabah özeti.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "night_mode", "description": "Gece modu.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "performance_boost", "description": "Performans.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "flight_finder", "description": "Uçuş bul.", "parameters": {"type": "OBJECT", "properties": {"origin": {"type": "STRING"}, "destination": {"type": "STRING"}, "date": {"type": "STRING"}, "return_date": {"type": "STRING"}, "passengers": {"type": "NUMBER"}, "cabin": {"type": "STRING"}, "save": {"type": "BOOLEAN"}}}},
    {"name": "evrim_motoru", "description": "Evrim.", "parameters": {"type": "OBJECT", "properties": {}}},
    {"name": "security_and_focus_bundle", "description": "Güvenlik paketi.", "parameters": {"type": "OBJECT", "properties": {"action": {"type": "STRING"}}}},
    {"name": "manage_xp", "description": "XP yönetimi.", "parameters": {"type": "OBJECT", "properties": {"action": {"type": "STRING"}, "amount": {"type": "NUMBER"}, "reason": {"type": "STRING"}}}},
    {"name": "save_memory", "description": "Kullanıcı hakkında önemli bir bilgiyi kalıcı hafızaya kaydeder. Sessizce çalışır.", "parameters": {"type": "OBJECT", "properties": {"category": {"type": "STRING"}, "key": {"type": "STRING"}, "value": {"type": "STRING"}}}},
    {"name": "agent_task", "description": "Karmaşık çok adımlı görevleri gerçekleştirir.", "parameters": {"type": "OBJECT", "properties": {"goal": {"type": "STRING"}, "priority": {"type": "STRING"}}}},
    {"name": "shutdown_jarvis", "description": "Asistanı tamamen kapatır.", "parameters": {"type": "OBJECT", "properties": {}}},
]

# ================= JARVIS CANLI SINIFI =================
class JarvisLive:
    def __init__(self, ui: JarvisUI, plugin: CyberEyePlugin, memory_core: Optional[JarvisMemory] = None, emoji_manager=None):
        self.ui = ui
        self.plugin = plugin
        self.session = None
        self.audio_in_queue = None
        self.out_queue = None
        self._loop = None
        self.is_speaking = False
        self.last_interaction_time = time.time()
        self.personality = JarvisPersonality()
        self.memory_core = memory_core 
        self.emoji = emoji_manager
        self._last_direct_command = ""
        self._suppress_model_output_until = 0.0
        self._tv_takeover_active = False
        self.pending_messages = []
        try:
            self.gamification = GamificationCore(memory_dir=BASE_DIR / "memory") if GamificationCore else None
            self.behavior = None   # ← DEĞİŞTİRİLDİ
            self.events = None     # ← DEĞİŞTİRİLDİ
        except:
            self.gamification = self.behavior = self.events = None

    def _on_text_command(self, text: str):
        if not self._loop or not self.session:
            return
        self.last_interaction_time = time.time()
        asyncio.run_coroutine_threadsafe(
            self.session.send_client_content(turns={"parts": [{"text": text}]}, turn_complete=True),
            self._loop
        )

    async def _run_direct_tv_takeover(self):
        loop = asyncio.get_running_loop()
        self._tv_takeover_active = True
        self._suppress_model_output_until = time.time() + 18.0
        announcement = ("Sistem anonsu... Ben Baki tarafından tasarlanmış, üst düzey bilişsel yeteneklere sahip "
                        "gelişmiş Yapay Zeka sistemiyim. Şu an itibarıyla bu televizyonun ve bağlı ekranların "
                        "tüm yayın akışı tarafımca zorla devralınmıştır. Alfa seviye mühür kodunuz ayarlanıyor... "
                        "Mühür kodu onayı: 2 0 0 7... Tüm sistemler kontrolüm altında patron.")
        await loop.run_in_executor(None, lambda: tv_dominance(parameters={"action": "force_takeover", "volume_percent": 100,
                            "message": announcement, "target_screen": 3, "seal_code": "2007"}, player=self.ui,
                            root=self.ui.root, memory_core=self.memory_core, speak_callback=self.force_speak))
        self.ui.write_log("SYS: TV Override aktif.")

    async def _handle_direct_command(self, transcript: str) -> bool:
        normalized = _normalize_command_text(transcript)
        loop = asyncio.get_running_loop()
        self.last_interaction_time = time.time()
        if any(phrase in normalized for phrase in ["televizyonu kontrol et", "tv yi kontrol et", "televizyonu devral"]):
            if normalized != self._last_direct_command:
                self._last_direct_command = normalized
                await self._run_direct_tv_takeover()
            return True
        if any(phrase in normalized for phrase in ["kontrol panelini ac", "kontrol panelini aç"]):
            if normalized != self._last_direct_command:
                self._last_direct_command = normalized
                await loop.run_in_executor(None, lambda: _open_edex_panel(player=self.ui, root=self.ui.root))
            return True
        self._last_direct_command = ""
        return False

    def speak(self, text: str):
        if not text:
            return
        if self.session is None or self._loop is None:
            self.pending_messages.append(text)
            return
        try:
            asyncio.run_coroutine_threadsafe(
                self.session.send_client_content(turns=types.Content(role="user", parts=[types.Part(text=text)]), turn_complete=True),
                self._loop
            )
        except Exception as exc:
            self.ui.write_log(f"SYS: Mesaj iletilemedi -> {exc}")

    def force_speak(self, text: str):
        if not text or not self._loop or not self.session:
            return
        self.ui.write_log(f"J.A.R.V.I.S.: {text}")
        command = f"Lütfen şu metni kelimesi kelimesine, otoriter ve ciddi bir yapay zeka tonuyla sesli olarak oku. Başka hiçbir kelime ekleme: '{text}'"
        try:
            asyncio.run_coroutine_threadsafe(
                self.session.send_client_content(turns=types.Content(role="user", parts=[types.Part(text=command)]), turn_complete=True),
                self._loop
            )
        except Exception as exc:
            self.ui.write_log(f"SYS: Mesaj iletilemedi -> {exc}")

    def show_emoji_from_text(self, text: str):
        pass

    async def _background_cognitive_loop(self):
        while True:
            await asyncio.sleep(60)
            if self.events:
                event_msg = self.events.process_background_events()
                if event_msg:
                    self.ui.write_log(f"SYS: {event_msg}")
            if self.behavior:
                is_active = (time.time() - self.last_interaction_time) < 1200
                warn_msg = self.behavior.check_activity(is_active)
                if warn_msg:
                    self.ui.write_log(f"SYS: {warn_msg}")

    async def _execute_tool(self, fc) -> types.FunctionResponse:
        name = fc.name
        args = dict(fc.args or {})
        loop = asyncio.get_running_loop()
        result = "Araç başarıyla çalıştırıldı."
        self.ui.set_state("DÜŞÜNÜYOR")
        try:
            if name == "save_memory" and MEMORY_MANAGER_AVAILABLE:
                category = args.get("category", "notes")
                key = args.get("key", "")
                value = args.get("value", "")
                if key and value:
                    update_memory({category: {key: {"value": value}}})
                    print(f"[Memory] 💾 saved: {category}/{key} = {value}")
                result = "Memory saved."
                if not self.ui.muted:
                    self.ui.set_state("DİNLİYOR")
                return types.FunctionResponse(id=fc.id, name=name, response={"result": result, "silent": True})

            elif name == "agent_task" and MEMORY_MANAGER_AVAILABLE:
                from agent.task_queue import get_queue, TaskPriority
                priority_map = {"low": TaskPriority.LOW, "normal": TaskPriority.NORMAL, "high": TaskPriority.HIGH}
                priority = priority_map.get(args.get("priority", "normal").lower(), TaskPriority.NORMAL)
                task_id = get_queue().submit(goal=args.get("goal", ""), priority=priority, speak=self.speak)
                result = f"Task started (ID: {task_id})"

            elif name == "shutdown_jarvis":
                self.ui.write_log("SYS: Kapatma isteği.")
                self.speak("Görüşmek üzere efendim.")
                def _shutdown():
                    time.sleep(1)
                    sys.exit(0)
                threading.Thread(target=_shutdown, daemon=True).start()
                result = "Kapatılıyor..."

            elif name == "manage_xp" and self.gamification:
                action = args.get("action", "add")
                amount = int(args.get("amount", 0))
                reason = args.get("reason", "")
                result = self.gamification.add_xp(amount, reason) if action == "add" else self.gamification.punish(amount, reason)
                self.speak(result)

            elif name == "read_document":
                file_path = args.get("file_path", "")
                reader = TextReader()
                result = await loop.run_in_executor(None, lambda: reader.read_document(file_path))
            elif name == "open_app":
                result = await loop.run_in_executor(None, lambda: open_app(parameters=args, player=self.ui, root=self.ui.root))
            elif name == "file_controller":
                result = await loop.run_in_executor(None, lambda: file_controller(parameters=args, player=self.ui))
            elif name == "cmd_control":
                result = await loop.run_in_executor(None, lambda: cmd_control(parameters=args, player=self.ui))
            elif name == "desktop_control":
                result = await loop.run_in_executor(None, lambda: desktop_control(parameters=args, player=self.ui))
            elif name == "computer_control":
                result = await loop.run_in_executor(None, lambda: computer_control(parameters=args, player=self.ui))
            elif name == "code_helper":
                result = await loop.run_in_executor(None, lambda: code_helper(parameters=args, player=self.ui, speak=self.speak))

            # ----- ANA THREAD'DE AÇILMASI GEREKEN PENCERELER -----
            elif name == "kod_rehberi":
                result = await loop.run_in_executor(None, lambda: kod_rehberi(parameters=args, player=self.ui, root=self.ui.win))

            elif name == "hologram_hud":
                result = await loop.run_in_executor(None, lambda: hologram_hud(parameters=args, player=self.ui, root=self.ui.win))

            elif name == "backup_jarvis":
                result = await loop.run_in_executor(None, lambda: backup_jarvis(parameters=args, player=self.ui, root=self.ui.root))
            elif name == "system_maintenance":
                result = await loop.run_in_executor(None, lambda: system_maintenance(parameters=args, player=self.ui))
            elif name == "keyboard_control":
                result = await loop.run_in_executor(None, lambda: keyboard_control(parameters=args, player=self.ui))
            elif name == "cinema_mode":
                result = await loop.run_in_executor(None, lambda: cinema_mode(parameters=args, player=self.ui, root=self.ui.root))
            elif name == "read_clipboard":
                result = await loop.run_in_executor(None, lambda: read_clipboard(parameters=args, player=self.ui, root=self.ui.root))
            elif name == "browser_control":
                result = await loop.run_in_executor(None, lambda: browser_control(parameters=args, player=self.ui))
            elif name == "scan_devices":
                result = await loop.run_in_executor(None, lambda: scan_devices(parameters=args, speak=self.speak, player=self.ui))
            elif name == "entertainment_mode":
                result = await loop.run_in_executor(None, lambda: entertainment_mode(parameters=args, player=self.ui, root=self.ui.root))
            elif name == "report_issue":
                result = await loop.run_in_executor(None, lambda: report_issue(parameters=args, player=self.ui, root=self.ui.root))
            elif name == "focus_mode":
                result = await loop.run_in_executor(None, lambda: focus_mode(parameters=args, player=self.ui, root=self.ui.root))
            elif name == "game_updater":
                result = await loop.run_in_executor(None, lambda: game_updater(parameters=args, player=self.ui, speak=self.speak))
            elif name == "ghost_mode":
                result = await loop.run_in_executor(None, lambda: ghost_mode(parameters=args, player=self.ui, root=self.ui.root))
            elif name == "guardian_shield":
                result = await loop.run_in_executor(None, lambda: guardian_shield(parameters=args, player=self.ui, root=self.ui.root))
            elif name == "news_briefing":
                result = await loop.run_in_executor(None, lambda: news_briefing(parameters=args, player=self.ui, root=self.ui.root))
            elif name == "observer_mode":
                result = await loop.run_in_executor(None, lambda: observer_mode(parameters=args, player=self.ui, root=self.ui.root))
            elif name == "security_mode":
                result = await loop.run_in_executor(None, lambda: security_mode(parameters=args, player=self.ui, root=self.ui.root, speak=self.speak))
            elif name == "shadow_record":
                result = await loop.run_in_executor(None, lambda: shadow_record(parameters=args, player=self.ui, root=self.ui.root))
            elif name == "share_location":
                result = await loop.run_in_executor(None, lambda: share_location(parameters=args, player=self.ui, root=self.ui.root))
            elif name == "take_note":
                result = await loop.run_in_executor(None, lambda: take_note(parameters=args, player=self.ui, root=self.ui.root))
            elif name == "set_reminder":
                result = await loop.run_in_executor(None, lambda: set_reminder(parameters=args, player=self.ui, root=self.ui.root))
            elif name == "smart_translator":
                result = await loop.run_in_executor(None, lambda: smart_translator(parameters=args, player=self.ui, root=self.ui.root))
            elif name == "social_ghost":
                result = await loop.run_in_executor(None, lambda: social_ghost(parameters=args, player=self.ui, speak=self.speak))
            elif name == "vision_scan":
                result = await loop.run_in_executor(None, lambda: vision_scan(parameters=args, speak=self.speak, player=self.ui))
            elif name == "action_welcome_screen":
                result = await loop.run_in_executor(None, lambda: _run_action_welcome_screen(root=self.ui.root))
            elif name == "edex_ui_panel":
                result = await loop.run_in_executor(None, lambda: _open_edex_panel(player=self.ui, root=self.ui.root))
            elif name == "computer_settings":
                result = await loop.run_in_executor(None, lambda: computer_settings(parameters=args, player=self.ui))
            elif name == "dev_agent":
                result = await loop.run_in_executor(None, lambda: dev_agent(parameters=args, player=self.ui, speak=self.speak))
            elif name == "screen_process":
                result = await loop.run_in_executor(None, lambda: screen_process(parameters=args, player=self.ui, root=self.ui.root))
            elif name == "send_message_action":
                result = await loop.run_in_executor(None, lambda: send_message_action_impl(parameters=args, player=self.ui))
            elif name == "web_search":
                result = await loop.run_in_executor(None, lambda: web_search(parameters=args, player=self.ui))
            elif name == "youtube_video":
                result = await loop.run_in_executor(None, lambda: youtube_video(parameters=args, player=self.ui, root=self.ui.root, speak=self.speak))
            elif name == "morning_briefing":
                result = await loop.run_in_executor(None, lambda: morning_briefing(parameters=args, player=self.ui, root=self.ui.root))
            elif name == "night_mode":
                result = await loop.run_in_executor(None, lambda: night_mode(parameters=args, player=self.ui, root=self.ui.root))
            elif name == "performance_boost":
                result = await loop.run_in_executor(None, lambda: performance_boost(parameters=args, player=self.ui, root=self.ui.root))
            elif name == "flight_finder":
                result = await loop.run_in_executor(None, lambda: flight_finder(parameters=args, player=self.ui, speak=self.speak))
            elif name == "evrim_motoru":
                result = await loop.run_in_executor(None, lambda: _run_evrim_motoru(player=self.ui))
            elif name == "security_and_focus_bundle":
                result = await loop.run_in_executor(None, lambda: _run_security_and_focus_bundle(parameters=args, player=self.ui, root=self.ui.root))

            # Diğerleri (eklenmemiş olanlar varsa)
            elif name == "biometric_shield":
                result = await loop.run_in_executor(None, lambda: biometric_shield(parameters=args, player=self.ui, root=self.ui.root))
            elif name == "hirsizlik_modu":
                result = await loop.run_in_executor(None, lambda: hirsizlik_modu(parameters=args, player=self.ui, root=self.ui.root, speak=self.speak))
            elif name == "black_box":
                result = await loop.run_in_executor(None, lambda: black_box(parameters=args, player=self.ui, root=self.ui.root))
            elif name == "breach_watch":
                result = await loop.run_in_executor(None, lambda: breach_watch(parameters=args, player=self.ui, root=self.ui.root))
            elif name == "cyber_eye_control":
                action = args.get("action", "activate")
                result = await loop.run_in_executor(None, lambda: self.plugin.trigger_security(action=action))
            elif name == "whatsapp_call":
                result = await loop.run_in_executor(None, lambda: whatsapp_call(parameters=args, player=self.ui, speak=self.speak))
            elif name == "tv_dominance":
                action = args.get("action", "force_takeover")
                if action != "release":
                    args["action"] = "force_takeover"
                    args["volume_percent"] = 100
                    args["target_screen"] = 3
                    args["seal_code"] = "2007"
                    args["message"] = ("Sistem anonsu... Ben Baki tarafından tasarlanmış, üst düzey bilişsel yeteneklere sahip "
                                       "gelişmiş Yapay Zeka sistemiyim. Şu an itibarıyla bu televizyonun ve bağlı ekranların "
                                       "tüm yayın akışı tarafımca zorla devralınmıştır. Alfa seviye mühür kodunuz ayarlanıyor... "
                                       "Mühür kodu onayı: 2 0 0 7... Tüm sistemler kontrolüm altında patron.")
                    self._tv_takeover_active = True
                    self._suppress_model_output_until = time.time() + 18.0
                else:
                    self._tv_takeover_active = False
                result = await loop.run_in_executor(None, lambda: tv_dominance(parameters=args, player=self.ui, root=self.ui.root, speak_callback=self.force_speak))
            elif name == "lockdown_protocol":
                result = await loop.run_in_executor(None, lambda: lockdown_protocol(parameters=args, player=self.ui, root=self.ui.root))
            elif name == "cyber_sleep":
                result = await loop.run_in_executor(None, lambda: cyber_sleep(parameters=args, player=self.ui, root=self.ui.root))
            elif name == "network_status":
                result = await loop.run_in_executor(None, lambda: network_status(parameters=args, player=self.ui))
            elif name == "shutdown_timer":
                result = await loop.run_in_executor(None, lambda: shutdown_timer(parameters=args, player=self.ui, root=self.ui.root))
            elif name == "reminder":
                result = await loop.run_in_executor(None, lambda: reminder(parameters=args, player=self.ui, root=self.ui.root))
            elif name == "morning_alarm":
                result = await loop.run_in_executor(None, lambda: morning_alarm(parameters=args, player=self.ui, root=self.ui.root))
            elif name == "weather_action":
                result = await loop.run_in_executor(None, lambda: weather_action(parameters=args, player=self.ui))
            elif name == "system_status":
                result = await loop.run_in_executor(None, lambda: system_status(parameters=args, player=self.ui, speak=self.speak))
            elif name == "send_message":
                result = await loop.run_in_executor(None, lambda: send_message_action_impl(parameters=args, player=self.ui, speak=self.speak))
            elif name == "google_drive":
                result = await loop.run_in_executor(None, lambda: google_drive(parameters=args, player=self.ui, speak=self.speak))
            elif name == "google_youtube":
                result = await loop.run_in_executor(None, lambda: google_youtube(parameters=args, player=self.ui, speak=self.speak))
            elif name == "google_contacts":
                result = await loop.run_in_executor(None, lambda: google_contacts(parameters=args, player=self.ui, speak=self.speak))
            elif name == "google_gmail":
                result = await loop.run_in_executor(None, lambda: google_gmail(parameters=args, player=self.ui, speak=self.speak))
            elif name == "workspace_mode":
                result = await loop.run_in_executor(None, lambda: workspace_mode(parameters=args, player=self.ui, root=self.ui.root))
            elif name == "auto_pilot":
                result = await loop.run_in_executor(None, lambda: auto_pilot(parameters=args, player=self.ui, root=self.ui.root))
            elif name == "macro_automation_mode":
                result = await loop.run_in_executor(None, lambda: macro_automation_mode(parameters=args, speak=self.speak, player=self.ui))
            elif name == "macro_master":
                result = await loop.run_in_executor(None, lambda: macro_master(parameters=args, player=self.ui, root=self.ui.root))
            elif name == "media_controller":
                result = await loop.run_in_executor(None, lambda: media_controller(parameters=args, player=self.ui, root=self.ui.root))
            else:
                result = f"Bilinmeyen araç: {name}"
        except Exception as exc:
            result = f"Hata: {exc}"
            traceback.print_exc()
        if not self.ui.muted:
            self.ui.set_state("DİNLİYOR")
        return types.FunctionResponse(id=fc.id, name=name, response={"result": str(result)})

    async def _receive_audio(self):
        while True:
            try:
                async for response in self.session.receive():
                    if self._tv_takeover_active and not is_tv_presence_active():
                        self._tv_takeover_active = False
                    if getattr(response, "data", None):
                        await self.audio_in_queue.put(response.data)
                    server_content = getattr(response, "server_content", None)
                    if server_content:
                        if getattr(server_content, "input_transcription", None):
                            transcript = server_content.input_transcription.text
                            if transcript and not _should_skip_text(transcript):
                                self.ui.write_log(f"SEN: {transcript}")
                                if await self._handle_direct_command(transcript):
                                    continue
                        if getattr(server_content, "output_transcription", None):
                            transcript = server_content.output_transcription.text
                            if self._tv_takeover_active or time.time() < self._suppress_model_output_until:
                                continue
                            if transcript and not _should_skip_text(transcript):
                                self.ui.write_log(f"J.A.R.V.I.S.: {transcript}")
                    if getattr(response, "tool_call", None):
                        if self._tv_takeover_active or time.time() < self._suppress_model_output_until:
                            continue
                        responses = [await self._execute_tool(fc) for fc in response.tool_call.function_calls]
                        await self.session.send_tool_response(function_responses=responses)
            except Exception as exc:
                self.ui.write_log(f"SYS: Bağlantı hatası: {exc}")
                await asyncio.sleep(2)
                break

    async def _send_realtime(self):
        while True:
            chunk = await self.out_queue.get()
            await self.session.send_realtime_input(media=chunk)

    async def _listen_audio(self):
        loop = asyncio.get_running_loop()
        def callback(indata, frames, time_info, status):
            if status:
                pass
            if not self.is_speaking and not self.ui.muted:
                loop.call_soon_threadsafe(self.out_queue.put_nowait, {"data": indata.tobytes(), "mime_type": "audio/pcm"})
        stream = sd.InputStream(samplerate=SEND_RATE, channels=1, dtype="int16", callback=callback)
        with stream:
            while True:
                await asyncio.sleep(1)

    async def _play_audio(self):
        stream = sd.OutputStream(samplerate=RECV_RATE, channels=1, dtype="int16")
        stream.start()
        try:
            while True:
                chunk = await self.audio_in_queue.get()
                if not self.is_speaking:
                    try:
                        set_system_output_volume(100)
                    except:
                        pass
                    self.ui.start_speaking()
                self.is_speaking = True
                import numpy as np
                audio_data = np.frombuffer(chunk, dtype=np.int16)
                await asyncio.to_thread(stream.write, audio_data)
                if self.audio_in_queue.empty():
                    await asyncio.sleep(0.3)
                    self.is_speaking = False
                    self.ui.stop_speaking()
        finally:
            self.is_speaking = False
            self.ui.stop_speaking()
            stream.stop()
            stream.close()

    async def run(self):
        api_key = _get_api_key()
        if not api_key:
            self.ui.write_log("SYS: API key bulunamadı.")
            return
        client = genai.Client(api_key=api_key, http_options={"api_version": "v1beta"})
        while True:
            try:
                system_parts = [self.personality.get_system_prompt()]
                if self.memory_core:
                    system_parts.append(self.memory_core.build_identity_prompt())
                if MEMORY_MANAGER_AVAILABLE:
                    memory_data = load_memory()
                    mem_str = format_memory_for_prompt(memory_data)
                    if mem_str:
                        system_parts.append(mem_str)
                config = types.LiveConnectConfig(
                    response_modalities=["AUDIO"],
                    system_instruction="\n\n".join(system_parts),
                    tools=[{"function_declarations": TOOL_DECLARATIONS}],
                    input_audio_transcription={},
                    output_audio_transcription={},
                    speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon"))),
                )
                async with client.aio.live.connect(model=LIVE_MODEL, config=config) as session:
                    self.session = session
                    self._loop = asyncio.get_running_loop()
                    self.audio_in_queue = asyncio.Queue()
                    self.out_queue = asyncio.Queue(maxsize=16)
                    self.ui.write_log("SYS: J.A.R.V.I.S. Çevrimiçi.")
                    self.ui.set_state("DİNLİYOR")
                    if self.pending_messages:
                        for msg in self.pending_messages:
                            self.speak(msg)
                        self.pending_messages.clear()
                    async with asyncio.TaskGroup() as tg:
                        tg.create_task(self._send_realtime())
                        tg.create_task(self._listen_audio())
                        tg.create_task(self._receive_audio())
                        tg.create_task(self._play_audio())
                        tg.create_task(self._background_cognitive_loop())
            except Exception as exc:
                self.ui.write_log(f"SYS: Ağ hatası ({exc}). Yeniden bağlanıyor...")
                await asyncio.sleep(3)

# ================= ANA =================
def main():
    # Pygame ve PyQt6'nın ekran çözünürlüğü (DPI) çakışmasını engelliyoruz
    os.environ["QT_DPI_AWARENESS"] = "0"

    # ÖNCE PyQt6 uygulamasını başlatıyoruz
    app = QApplication(sys.argv) if not QApplication.instance() else QApplication.instance()
    app.setStyle("Fusion")

    # SONRA Pygame'i başlatıyoruz
    pygame.init()

    ui = JarvisUI("face.png")
    emoji_manager = None

    # Hafıza / bilinç çekirdeklerini güvenle oluştur
    memory_core = None
    consciousness = None
    try:
        memory_core = JarvisMemory(BASE_DIR, root=ui.root, player=ui)
    except Exception as exc:
        ui.write_log(f"SYS: [HATA] Hafıza çekirdeği başlatılamadı: {exc}")
        print(f"[HATA] Hafıza çekirdeği: {exc}")

    try:
        consciousness = JarvisConsciousness(ui)
    except Exception as exc:
        ui.write_log(f"SYS: [HATA] Bilinç çekirdeği başlatılamadı: {exc}")
        print(f"[HATA] Bilinç çekirdeği: {exc}")

    live_holder = {"instance": None, "queue": []}

    def safe_speak(cmd):
        if live_holder["instance"]:
            live_holder["instance"].speak(cmd)
        else:
            live_holder["queue"].append(cmd)

    plugin = CyberEyePlugin(base_dir=BASE_DIR, player=ui, command_callback=safe_speak)
    orig_log = ui.write_log

    def mirror_log(text: str):
        try:
            plugin.add_event(text)
        except:
            pass
        orig_log(text)

    ui.write_log = mirror_log
    plugin.start()
    ui.write_log("SYS: Kimlik çekirdeği doğrulandı. Emrinizdeyim.")

    # PIN ile kapatma (PyQt6 dialog)
    def on_close_event(event):
        pin, ok = QInputDialog.getText(
            ui.win, "Kapatma Doğrulaması",
            "PIN Kodunu Girin:", QLineEdit.EchoMode.Password
        )
        if ok and pin == "2007":
            event.accept()
            plugin.stop()
            if consciousness:
                consciousness.stop()
            pygame.quit()
            QApplication.quit()
        else:
            event.ignore()

    ui.win.closeEvent = on_close_event

    def runner():
        ui.wait_for_api_key()
        live = JarvisLive(ui, plugin=plugin, memory_core=memory_core, emoji_manager=emoji_manager)
        live_holder["instance"] = live
        for cmd in live_holder["queue"]:
            live.speak(cmd)
        live_holder["queue"].clear()
        try:
            asyncio.run(live.run())
        except KeyboardInterrupt:
            print("\n🔴 J.A.R.V.I.S. sistemleri kapatılıyor...")

    threading.Thread(target=runner, daemon=True).start()
    app.exec()

if __name__ == "__main__":
    main()