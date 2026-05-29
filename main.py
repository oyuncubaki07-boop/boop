import asyncio
import os
import threading
import json
import sys
import traceback
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import logging

_process_executor = None

def get_cpu_executor():
    global _process_executor
    if _process_executor is None:
        _process_executor = ProcessPoolExecutor(max_workers=2)
    return _process_executor

# Fix for Windows CMD UnicodeEncodeError when printing emojis
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

try:
    import sounddevice as sd
except Exception:
    sd = None

try:
    from google import genai
    from google.genai import types
except Exception:
    genai = None
    types = None

try:
    from ui import JarvisUI
except Exception:
    JarvisUI = None

try:
    from memory.memory_manager import (
        load_memory, update_memory, format_memory_for_prompt,
        should_extract_memory, extract_memory,
        should_extract_memory_async, extract_memory_async, update_memory_async
    )
except Exception:
    def load_memory(): return {}
    def update_memory(data): pass
    def format_memory_for_prompt(memory): return ""
    def should_extract_memory(u, j, k): return False
    def extract_memory(u, j, k): return {}
    async def should_extract_memory_async(u, j, k): return False
    async def extract_memory_async(u, j, k): return {}
    async def update_memory_async(data): pass

def _import_action(module_path: str, attr: str):
    try:
        mod = __import__(module_path, fromlist=[attr])
        return getattr(mod, attr)
    except Exception:
        def _fallback(*args, **kwargs):
            return f"Efendim, {attr} modülü şu an hazır değil; birazdan tekrar deneyebilirsiniz."
        return _fallback

file_processor = _import_action("actions.file_processor", "file_processor")
flight_finder = _import_action("actions.flight_finder", "flight_finder")
open_app = _import_action("actions.open_app", "open_app")
weather_action = _import_action("actions.weather_report", "weather_action")
send_message = _import_action("actions.send_message", "send_message")
reminder = _import_action("actions.reminder", "reminder")
computer_settings = _import_action("actions.computer_settings", "computer_settings")
screen_process = _import_action("actions.screen_processor", "screen_process")
youtube_video = _import_action("actions.youtube_video", "youtube_video")
desktop_control = _import_action("actions.desktop", "desktop_control")
browser_control = _import_action("actions.browser_control", "browser_control")
file_controller = _import_action("actions.file_controller", "file_controller")
code_helper = _import_action("actions.code_helper", "code_helper")
dev_agent = _import_action("actions.dev_agent", "dev_agent")
web_search_action = _import_action("actions.web_search", "web_search")
computer_control = _import_action("actions.computer_control", "computer_control")
game_updater = _import_action("actions.game_updater", "game_updater")
konseyi_topla = _import_action("actions.konseyi_topla", "run_action")
github_kod_bulucu = _import_action("actions.github_kod_bulucu", "run_action")

def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent

BASE_DIR        = get_base_dir()
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"
PROMPT_PATH     = BASE_DIR / "core" / "prompt.txt"
LIVE_MODEL          = "models/gemini-2.5-flash-native-audio-preview-12-2025"
CHANNELS            = 1
SEND_SAMPLE_RATE    = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE          = 1024

def _get_api_key() -> str:
    try:
        from core.config_loader import get_key
        return get_key("gemini_api_key", "") or os.getenv("GEMINI_API_KEY", "") or ""
    except Exception:
        try:
            with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
                return str(json.load(f).get("gemini_api_key", "") or "")
        except Exception:
            return os.getenv("GEMINI_API_KEY", "") or ""

def _load_system_prompt() -> str:
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except Exception:
        return (
            "You are JARVIS: brilliant, warm, supportive, and impeccably polite. "
            "Speak with calm confidence and gentle charm. Never use profanity or harsh tone. "
            "Always use tools for real actions; never simulate results."
        )

_last_memory_input = ""

TOOL_DECLARATIONS = [
    # ... (tool declarations omitted for brevity)
]

class JarvisLive:
    def __init__(self, ui: JarvisUI):
        self.ui             = ui
        self.session        = None
        self.audio_in_queue = None
        self.out_queue      = None
        self._loop          = None
        self._is_speaking   = False
        self._speaking_lock = threading.Lock()  # Guards _is_speaking AND _is_processing
        self._is_processing = False
        self._reconnect_in_progress = False
        self._consecutive_errors = 0  # For exponential backoff
        self._reconnect_timestamps = []
        self._speaking_off_timer = None  # Debounce timer for speaking state
        
        self.ui.on_text_command = self._on_text_command
        self._offline_mode = False
        try:
            from core.config_loader import get_bool
            self._offline_mode = get_bool("offline_prefer_local", False)
        except Exception:
            pass
        try:
            from omega.orchestrator import get_orchestrator
            self.omega = get_orchestrator(ui)
        except Exception:
            self.omega = None
        try:
            from kod_rehberi_window import set_run_callback, set_status_callback
            set_run_callback(self._run_from_guide)
            set_status_callback(lambda m: self.ui.write_log(m))
        except Exception:
            pass
        if hasattr(self.ui, "set_offline_mode"):
            self.ui.set_offline_mode(self._offline_mode)
        if hasattr(self.ui, "set_evolution_refresh"):
            self.ui.set_evolution_refresh(self._refresh_evolution_ui)
        if hasattr(self.ui, "bind_jarvis"):
            self.ui.bind_jarvis(self)
        self._refresh_evolution_ui()

    async def handle_request(self, scope: dict) -> None:
        try:
            app = self.config.loaded_app
            result = await app(scope)  # type: ignore[func-returns-value]
            await result
        except Exception as exc:
            logger = logging.getLogger(__name__)
            logger.error(
                "Exception in ASGI application\n%s",
                "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
            )
            self.transport.close()

    # ... (rest of the code omitted for brevity)
