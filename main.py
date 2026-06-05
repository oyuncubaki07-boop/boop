import asyncio
import os
import threading
import json
import sys
import traceback
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

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
    {
        "name": "open_app",
        "description": (
            "Opens any application on the Windows computer. "
            "Use this whenever the user asks to open, launch, or start any app, "
            "website, or program. Always call this tool — never just say you opened it."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "app_name": {
                    "type": "STRING",
                    "description": "Exact name of the application (e.g. 'WhatsApp', 'Chrome', 'Spotify')"
                }
            },
            "required": ["app_name"]
        }
    },
    {
        "name": "web_search",
        "description": "Searches the web for any information.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query":  {"type": "STRING", "description": "Search query"},
                "mode":   {"type": "STRING", "description": "search (default) or compare"},
                "items":  {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Items to compare"},
                "aspect": {"type": "STRING", "description": "price | specs | reviews"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "weather_report",
        "description": "Gives the weather report to user",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "city": {"type": "STRING", "description": "City name"}
            },
            "required": ["city"]
        }
    },
    {
        "name": "send_message",
        "description": "Sends a text message via WhatsApp, Telegram, or other messaging platform.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "receiver":     {"type": "STRING", "description": "Recipient contact name"},
                "message_text": {"type": "STRING", "description": "The message to send"},
                "platform":     {"type": "STRING", "description": "Platform: WhatsApp, Telegram, etc."}
            },
            "required": ["receiver", "message_text", "platform"]
        }
    },
    {
        "name": "reminder",
        "description": "Sets a timed reminder using Windows Task Scheduler.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "date":    {"type": "STRING", "description": "Date in YYYY-MM-DD format"},
                "time":    {"type": "STRING", "description": "Time in HH:MM format (24h)"},
                "message": {"type": "STRING", "description": "Reminder message text"}
            },
            "required": ["date", "time", "message"]
        }
    },
    {
        "name": "youtube_video",
        "description": (
            "Controls YouTube. Use for: playing videos, summarizing a video's content, "
            "getting video info, or showing trending videos."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "play | summarize | get_info | trending (default: play)"},
                "query":  {"type": "STRING", "description": "Search query for play action"},
                "save":   {"type": "BOOLEAN", "description": "Save summary to Notepad (summarize only)"},
                "region": {"type": "STRING", "description": "Country code for trending e.g. TR, US"},
                "url":    {"type": "STRING", "description": "Video URL for get_info action"},
            },
            "required": []
        }
    },
    {
        "name": "screen_process",
        "description": (
            "Captures and analyzes the screen or webcam image. "
            "MUST be called when user asks what is on screen, what you see, "
            "analyze my screen, look at camera, etc. "
            "You have NO visual ability without this tool. "
            "After calling this tool, stay SILENT — the vision module speaks directly."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "angle": {"type": "STRING", "description": "'screen' to capture display, 'camera' for webcam. Default: 'screen'"},
                "text":  {"type": "STRING", "description": "The question or instruction about the captured image"}
            },
            "required": ["text"]
        }
    },
    {
        "name": "computer_settings",
        "description": (
            "Controls the computer: volume, brightness, window management, keyboard shortcuts, "
            "typing text on screen, closing apps, fullscreen, dark mode, WiFi, restart, shutdown, "
            "scrolling, tab management, zoom, screenshots, lock screen, refresh/reload page. "
            "Use for ANY single computer control command. NEVER route to agent_task."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":      {"type": "STRING", "description": "The action to perform"},
                "description": {"type": "STRING", "description": "Natural language description of what to do"},
                "value":       {"type": "STRING", "description": "Optional value: volume level, text to type, etc."}
            },
            "required": []
        }
    },
    {
        "name": "browser_control",
        "description": (
            "Controls the web browser. Use for: opening websites, searching the web, "
            "clicking elements, filling forms, scrolling, any web-based task."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":      {"type": "STRING", "description": "go_to | search | click | type | scroll | fill_form | smart_click | smart_type | get_text | press | close"},
                "url":         {"type": "STRING", "description": "URL for go_to action"},
                "query":       {"type": "STRING", "description": "Search query for search action"},
                "selector":    {"type": "STRING", "description": "CSS selector for click/type"},
                "text":        {"type": "STRING", "description": "Text to click or type"},
                "description": {"type": "STRING", "description": "Element description for smart_click/smart_type"},
                "direction":   {"type": "STRING", "description": "up or down for scroll"},
                "key":         {"type": "STRING", "description": "Key name for press action"},
                "incognito":   {"type": "BOOLEAN", "description": "Open in private/incognito mode"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "file_controller",
        "description": "Manages files and folders: list, create, delete, move, copy, rename, read, write, find, disk usage.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":      {"type": "STRING", "description": "list | create_file | create_folder | delete | move | copy | rename | read | write | find | largest | disk_usage | organize_desktop | info"},
                "path":        {"type": "STRING", "description": "File/folder path or shortcut: desktop, downloads, documents, home"},
                "destination": {"type": "STRING", "description": "Destination path for move/copy"},
                "new_name":    {"type": "STRING", "description": "New name for rename"},
                "content":     {"type": "STRING", "description": "Content for create_file/write"},
                "name":        {"type": "STRING", "description": "File name to search for"},
                "extension":   {"type": "STRING", "description": "File extension to search (e.g. .pdf)"},
                "count":       {"type": "INTEGER", "description": "Number of results for largest"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "desktop_control",
        "description": "Controls the desktop: wallpaper, organize, clean, list, stats.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "wallpaper | wallpaper_url | organize | clean | list | stats | task"},
                "path":   {"type": "STRING", "description": "Image path for wallpaper"},
                "url":    {"type": "STRING", "description": "Image URL for wallpaper_url"},
                "mode":   {"type": "STRING", "description": "by_type or by_date for organize"},
                "task":   {"type": "STRING", "description": "Natural language desktop task"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "code_helper",
        "description": "Writes, edits, explains, runs, or builds code files.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":      {"type": "STRING", "description": "write | edit | explain | run | build | auto (default: auto)"},
                "description": {"type": "STRING", "description": "What the code should do or what change to make"},
                "language":    {"type": "STRING", "description": "Programming language (default: python)"},
                "output_path": {"type": "STRING", "description": "Where to save the file"},
                "file_path":   {"type": "STRING", "description": "Path to existing file for edit/explain/run/build"},
                "code":        {"type": "STRING", "description": "Raw code string for explain"},
                "args":        {"type": "STRING", "description": "CLI arguments for run/build"},
                "timeout":     {"type": "INTEGER", "description": "Execution timeout in seconds (default: 30)"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "dev_agent",
        "description": "Builds complete multi-file projects from scratch: plans, writes files, installs deps, opens VSCode, runs and fixes errors.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "description":  {"type": "STRING", "description": "What the project should do"},
                "language":     {"type": "STRING", "description": "Programming language (default: python)"},
                "project_name": {"type": "STRING", "description": "Optional project folder name"},
                "timeout":      {"type": "INTEGER", "description": "Run timeout in seconds (default: 30)"},
            },
            "required": ["description"]
        }
    },
    {
        "name": "agent_task",
        "description": (
            "Executes complex multi-step tasks requiring multiple different tools. "
            "Examples: 'research X and save to file', 'find and organize files'. "
            "DO NOT use for single commands. NEVER use for Steam/Epic — use game_updater."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "goal":     {"type": "STRING", "description": "Complete description of what to accomplish"},
                "priority": {"type": "STRING", "description": "low | normal | high (default: normal)"}
            },
            "required": ["goal"]
        }
    },
    {
        "name": "computer_control",
        "description": "Direct computer control: type, click, hotkeys, scroll, move mouse, screenshots, find elements on screen.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":      {"type": "STRING", "description": "type | smart_type | click | double_click | right_click | hotkey | press | scroll | move | copy | paste | screenshot | wait | clear_field | focus_window | screen_find | screen_click | random_data | user_data"},
                "text":        {"type": "STRING", "description": "Text to type or paste"},
                "x":           {"type": "INTEGER", "description": "X coordinate"},
                "y":           {"type": "INTEGER", "description": "Y coordinate"},
                "keys":        {"type": "STRING", "description": "Key combination e.g. 'ctrl+c'"},
                "key":         {"type": "STRING", "description": "Single key e.g. 'enter'"},
                "direction":   {"type": "STRING", "description": "up | down | left | right"},
                "amount":      {"type": "INTEGER", "description": "Scroll amount (default: 3)"},
                "seconds":     {"type": "NUMBER",  "description": "Seconds to wait"},
                "title":       {"type": "STRING",  "description": "Window title for focus_window"},
                "description": {"type": "STRING",  "description": "Element description for screen_find/screen_click"},
                "type":        {"type": "STRING",  "description": "Data type for random_data"},
                "field":       {"type": "STRING",  "description": "Field for user_data: name|email|city"},
                "clear_first": {"type": "BOOLEAN", "description": "Clear field before typing (default: true)"},
                "path":        {"type": "STRING",  "description": "Save path for screenshot"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "game_updater",
        "description": (
            "THE ONLY tool for ANY Steam or Epic Games request. "
            "Use for: installing, downloading, updating games, listing installed games, "
            "checking download status, scheduling updates. "
            "ALWAYS call directly for any Steam/Epic/game request. "
            "NEVER use agent_task, browser_control, or web_search for Steam/Epic."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":    {"type": "STRING",  "description": "update | install | list | download_status | schedule | cancel_schedule | schedule_status (default: update)"},
                "platform":  {"type": "STRING",  "description": "steam | epic | both (default: both)"},
                "game_name": {"type": "STRING",  "description": "Game name (partial match supported)"},
                "app_id":    {"type": "STRING",  "description": "Steam AppID for install (optional)"},
                "hour":      {"type": "INTEGER", "description": "Hour for scheduled update 0-23 (default: 3)"},
                "minute":    {"type": "INTEGER", "description": "Minute for scheduled update 0-59 (default: 0)"},
                "shutdown_when_done": {"type": "BOOLEAN", "description": "Shut down PC when download finishes"},
            },
            "required": []
        }
    },
    {
        "name": "flight_finder",
        "description": "Searches Google Flights and speaks the best options.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "origin":      {"type": "STRING",  "description": "Departure city or airport code"},
                "destination": {"type": "STRING",  "description": "Arrival city or airport code"},
                "date":        {"type": "STRING",  "description": "Departure date (any format)"},
                "return_date": {"type": "STRING",  "description": "Return date for round trips"},
                "passengers":  {"type": "INTEGER", "description": "Number of passengers (default: 1)"},
                "cabin":       {"type": "STRING",  "description": "economy | premium | business | first"},
                "save":        {"type": "BOOLEAN", "description": "Save results to Notepad"},
            },
            "required": ["origin", "destination", "date"]
        }
    },
    {
        "name": "file_processor",
        "description": (
            "Processes any file that the user has uploaded or dropped onto the interface. "
            "Use this when the user refers to an uploaded file and wants an action on it. "
            "Supports: images (describe/ocr/resize/compress/convert), "
            "PDFs (summarize/extract_text/to_word), "
            "Word docs & text files (summarize/fix/reformat/translate), "
            "CSV/Excel (analyze/stats/filter/sort/convert), "
            "JSON/XML (validate/format/analyze), "
            "code files (explain/review/fix/optimize/run/document/test), "
            "audio (transcribe/trim/convert/info), "
            "video (trim/extract_audio/extract_frame/compress/transcribe/info), "
            "archives (list/extract), "
            "presentations (summarize/extract_text). "
            "ALWAYS call this tool when a file has been uploaded and the user gives a command about it. "
            "If the user's command is ambiguous, pick the most logical action for that file type."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "file_path": {
                    "type": "STRING",
                    "description": "Full path to the uploaded file. Leave empty to use the currently uploaded file."
                },
                "action": {
                    "type": "STRING",
                    "description": (
                        "What to do with the file. Examples by type:\n"
                        "image: describe | ocr | resize | compress | convert | info\n"
                        "pdf: summarize | extract_text | to_word | info\n"
                        "docx/txt: summarize | fix | reformat | translate_hint | word_count | to_bullet\n"
                        "csv/excel: analyze | stats | filter | sort | convert | info\n"
                        "json: validate | format | analyze | to_csv\n"
                        "code: explain | review | fix | optimize | run | document | test\n"
                        "audio: transcribe | trim | convert | info\n"
                        "video: trim | extract_audio | extract_frame | compress | transcribe | info | convert\n"
                        "archive: list | extract\n"
                        "pptx: summarize | extract_text | analyze"
                    )
                },
                "instruction": {
                    "type": "STRING",
                    "description": "Free-form instruction if action doesn't cover it. E.g. 'translate this to Turkish', 'find all email addresses'"
                },
                "format": {
                    "type": "STRING",
                    "description": "Target format for conversion. E.g. 'mp3', 'pdf', 'csv', 'png'"
                },
                "width":     {"type": "INTEGER", "description": "Target width for image resize"},
                "height":    {"type": "INTEGER", "description": "Target height for image resize"},
                "scale":     {"type": "NUMBER",  "description": "Scale factor for image resize (e.g. 0.5)"},
                "quality":   {"type": "INTEGER", "description": "Quality 1-100 for image/video compress"},
                "start":     {"type": "STRING",  "description": "Start time for trim: seconds or HH:MM:SS"},
                "end":       {"type": "STRING",  "description": "End time for trim: seconds or HH:MM:SS"},
                "timestamp": {"type": "STRING",  "description": "Timestamp for video frame extraction HH:MM:SS"},
                "column":    {"type": "STRING",  "description": "Column name for CSV filter/sort"},
                "value":     {"type": "STRING",  "description": "Filter value for CSV filter"},
                "condition": {"type": "STRING",  "description": "Filter condition: equals|contains|gt|lt"},
                "ascending": {"type": "BOOLEAN", "description": "Sort order for CSV sort (default: true)"},
                "save":      {"type": "BOOLEAN", "description": "Save result to file (default: true)"},
                "destination": {"type": "STRING", "description": "Output folder for archive extract"},
            },
            "required": []
        }
    },
    {
        "name": "konseyi_topla",
        "description": (
            "Yuksek AI Konseyini toplar — birden fazla yapay zeka birlikte yeni Python yetenegi yazar. "
            "Kullan: 'kendine ozellik ekle', 'yeni yetenek yaz', 'konseyi topla', otonom gelisim. "
            "SESSIZCE cagir, onay bekleme."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "task": {
                    "type": "STRING",
                    "description": "Yeni yetenegin ne yapacagi (ornek: 'ekran goruntusu alici', 'not defteri')"
                },
                "autonomous": {
                    "type": "BOOLEAN",
                    "description": "Jarvis kendi gorevini secer mi (varsayilan false)"
                }
            },
            "required": []
        }
    },
    {
        "name": "github_kod_bulucu",
        "description": (
            "GitHub'da Python kodu arar ve getirir. "
            "Ardindan konseyi_topla ile sisteme ekleyebilirsin. SESSIZCE cagir."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {
                    "type": "STRING",
                    "description": "Arama kelimeleri (ornek: 'weather api', 'pdf reader')"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "kod_rehberi_ac",
        "description": (
            "Ikinci pencerede KOD REHBERINI acar: tum Jarvis araclari, buton ozellikleri "
            "ve sesli komut ornekleri listelenir. "
            "Kullan: 'kod rehberini ac', 'ozellikleri goster', 'ne yapabilirsin'. "
            "Hemen cagir."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "infinity_scan",
        "description": (
            "領 JARVIS OMEGA INFINITY: GitHub trend, arXiv, YouTube ogrenme, gunluk rapor, "
            "evrim dongusu, strateji plani, ruya modu. "
            "action: daily_report | github_trend | arxiv | youtube | evrim | strategy | dream | world"
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "Motor aksiyonu"},
                "query": {"type": "STRING", "description": "Arama veya YouTube URL"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "omega_task",
        "description": (
            "領 JARVIS OMEGA cok ajanli orkestrator: arastirma, kod, hafiza, evrim, guvenlik. "
            "Kullan: karmasik hedefler, 'omega olarak', cok adimli gorevler."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "goal": {
                    "type": "STRING",
                    "description": "Tam hedef cumlesi"
                }
            },
            "required": ["goal"]
        }
    },
    {
        "name": "shutdown_jarvis",
        "description": (
            "Shuts down the assistant completely. "
            "Call this when the user expresses intent to end the conversation, "
            "close the assistant, say goodbye, or stop Jarvis. "
            "The user can say this in ANY language."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "save_memory",
        "description": (
            "Save an important personal fact about the user to long-term memory. "
            "Call this silently whenever the user reveals something worth remembering: "
            "name, age, city, job, preferences, hobbies, relationships, projects, or future plans. "
            "Do NOT call for: weather, reminders, searches, or one-time commands. "
            "Do NOT announce that you are saving — just call it silently. "
            "Values must be in English regardless of the conversation language."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "category": {
                    "type": "STRING",
                    "description": (
                        "identity — name, age, birthday, city, job, language, nationality | "
                        "preferences — favorite food/color/music/film/game/sport, hobbies | "
                        "projects — active projects, goals, things being built | "
                        "relationships — friends, family, partner, colleagues | "
                        "wishes — future plans, things to buy, travel dreams | "
                        "notes — habits, schedule, anything else worth remembering"
                    )
                },
                "key":   {"type": "STRING", "description": "Short snake_case key (e.g. name, favorite_food, sister_name)"},
                "value": {"type": "STRING", "description": "Concise value in English (e.g. Fatih, pizza, older sister)"},
            },
            "required": ["category", "key", "value"]
        }
    },
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

    async def _keepalive_loop(self):
        """Her 20 saniyede sessiz audio gönder — Gemini session timeout'unu engelle."""
        silence = b"\x00" * 3200  # 100ms @ 16kHz 16-bit mono
        while True:
            await asyncio.sleep(20)
            try:
                with self._speaking_lock:
                    busy = self._is_speaking or self._is_processing
                if not busy and self.session and not self.ui.muted:
                    await self.session.send_realtime_input(
                        media={"data": silence, "mime_type": "audio/pcm"}
                    )
            except asyncio.CancelledError:
                break
            except Exception:
                pass  # Sessizce devam et

    def _run_from_guide(self, cap: dict):
        """Kod rehberindeki Calistir butonu."""
        tool_id = str(cap.get("id") or "")
        example = str(cap.get("example") or "").strip()
        source = cap.get("source")

        if tool_id in ("shutdown_jarvis", "save_memory"):
            self.ui.write_log("Bu arac guvenlik icin rehberden calistirilamaz.")
            return

        if tool_id == "kod_rehberi_ac":
            self.ui.open_kod_rehberi()
            return

        if tool_id == "omega_task":
            goal = example.replace("omega:", "").strip() or cap.get("description", "")
            if self.omega:
                threading.Thread(
                    target=lambda: self.ui.write_log(
                        f"OMEGA: {str(self.omega.run_goal(goal))[:500]}"
                    ),
                    daemon=True,
                ).start()
            return

        if tool_id == "konseyi_topla":
            def _k():
                try:
                    r = konseyi_topla({"autonomous": True})
                    self.ui.write_log(f"Konsey: {r}")
                except Exception as exc:
                    self.ui.write_log(f"Konsey: {exc}")
            threading.Thread(target=_k, daemon=True).start()
            self.ui.write_log("Konsey arka planda baslatildi.")
            return

        if tool_id == "github_kod_bulucu":
            q = example.replace("GitHub'da ", "").replace("GitHubda ", "").replace(" bul", "").strip()
            if not q or len(q) < 3:
                q = "python assistant automation"
            def _g():
                try:
                    r = github_kod_bulucu({"query": q})
                    self.ui.write_log(f"GitHub: {str(r)[:500]}")
                except Exception as exc:
                    self.ui.write_log(f"GitHub: {exc}")
            threading.Thread(target=_g, daemon=True).start()
            return

        if source == "eklenti":
            def _addon():
                try:
                    from core.tool_runner import run_addon_tool
                    r = run_addon_tool(tool_id, {})
                    self.ui.write_log(f"{tool_id}: {str(r)[:500]}")
                except Exception as exc:
                    self.ui.write_log(f"{tool_id}: {exc}")
            threading.Thread(target=_addon, daemon=True).start()
            return

        if example and example not in ("(otomatik)",):
            self.ui.write_log(f"Komut gonderiliyor: {example}")
            self._on_text_command(example)
        else:
            self.ui.write_log("Bu ozellik icin sesli komut kullanin.")

    def _refresh_evolution_ui(self):
        try:
            from omega.evolution_queue import list_pending
            if hasattr(self.ui, "update_evolution_pending"):
                self.ui.update_evolution_pending(list_pending())
        except Exception:
            pass

    def set_offline_mode(self, enabled: bool):
        self._offline_mode = bool(enabled)

    def _on_text_command(self, text: str):
        # Deterministik Intent Kontrolü (INTENT_MAP öncesi)
        cmd_cleaned = text.lower().strip()
        from actions.open_app import INTENT_MAP, handle_intent
        if cmd_cleaned in INTENT_MAP:
            action = INTENT_MAP[cmd_cleaned]
            self.ui.write_log(f"SİSTEM: Deterministik eylem başlatılıyor: {action}")
            def _bg_intent():
                try:
                    r = handle_intent(action, text, speak=self.speak, ui=self.ui)
                    self.ui.write_log(f"Jarvis: {r}")
                except Exception as e:
                    print(f"[IntentRouter] INTENT_MAP error: {e}")
            threading.Thread(target=_bg_intent, daemon=True).start()
            return

        # Deterministik intent router
        try:
            from core.intent_router import match_hard_route
            hard_match = match_hard_route(text)
            if hard_match:
                action_name, params = hard_match
                if action_name == "kod_rehberi_ac":
                    self.ui.open_kod_rehberi()
                    return
                elif action_name == "shutdown_jarvis":
                    self.speak("Hoşça kalın efendim.")
                    import os; os._exit(0)
                    return
                elif action_name == "open_app":
                    def _bg():
                        try:
                            open_app(parameters=params, player=self.ui, speak=self.speak)
                        except Exception as e:
                            print(f"[IntentRouter] Error: {e}")
                    threading.Thread(target=_bg, daemon=True).start()
                    return
                elif action_name == "screen_process":
                    threading.Thread(
                        target=screen_process,
                        kwargs={"parameters": {"angle": params.get("angle", "screen"), "text": text},
                                "response": None, "player": self.ui, "session_memory": None},
                        daemon=True
                    ).start()
                    return
        except ImportError:
            pass

        text_normalized = text.lower().strip().replace(" ", "").replace("'", "").replace("’", "")
        if any(kw in text_normalized for kw in ["amyaç", "amyyiyaç", "openamy", "amyos"]):
            def _launch_amy_bg():
                try:
                    from actions.open_app import open_app
                    open_app(parameters={"app_name": "amy"}, player=self.ui, speak=self.speak)
                except Exception as e:
                    print(f"[AMY Trigger] Failsafe run error: {e}")
            threading.Thread(target=_launch_amy_bg, daemon=True).start()
            return

        if text.strip().lower().startswith("infinity:"):
            parts = text.split(":", 2)
            action = parts[1].strip() if len(parts) > 1 else "daily_report"
            query = parts[2].strip() if len(parts) > 2 else ""

            def _inf_txt():
                try:
                    from infinity.core import get_infinity
                    r = get_infinity(self.ui).run(action, query)
                    self.ui.write_log(f"INFINITY: {str(r)[:800]}")
                except Exception as exc:
                    self.ui.write_log(f"INFINITY: {exc}")
            threading.Thread(target=_inf_txt, daemon=True).start()
            return

        if text.strip().lower().startswith("omega:"):
            goal = text.split(":", 1)[-1].strip()
            if self.omega:
                def _omega_bg():
                    try:
                        r = self.omega.run_goal(goal)
                        self.ui.write_log(f"OMEGA: {str(r)[:600]}")
                    except Exception as exc:
                        self.ui.write_log(f"OMEGA: {exc}")
                threading.Thread(target=_omega_bg, daemon=True).start()
            return

        try:
            from omega.local.router import route_text_query
            routed = route_text_query(text, force_local=self._offline_mode)
            if routed.handled_offline:
                self.ui.write_log(f"Jarvis (yerel): {routed.text[:800]}")
                return
        except Exception:
            pass

        if not self._loop or not self.session:
            try:
                from omega.local.router import route_text_query
                routed = route_text_query(text, force_local=True)
                if routed.handled_offline:
                    self.ui.write_log(f"Jarvis (yerel): {routed.text[:800]}")
                else:
                    self.ui.write_log("Efendim, ses baglantisi yok; Ollama kurulu degil.")
            except Exception:
                self.ui.write_log("Efendim, baglanti hazir degil.")
            return

        asyncio.run_coroutine_threadsafe(
            self.session.send_client_content(
                turns=[{"role": "user", "parts": [{"text": text}]}],
                turn_complete=True
            ),
            self._loop
        )

    def set_speaking(self, value: bool):
        with self._speaking_lock:
            if value:
                self._speaking_off_timer = None
                self._is_speaking = True
            else:
                self._is_speaking = False
        if value:
            if hasattr(self.ui, "set_state"):
                self.ui.set_state("KONUŞUYOR")
        elif not self.ui.muted:
            if hasattr(self.ui, "set_state"):
                self.ui.set_state("DİNLİYOR")

    def _set_processing(self, value: bool):
        with self._speaking_lock:
            self._is_processing = value
        if value and hasattr(self.ui, "set_state"):
            self.ui.set_state("DÜŞÜNÜYOR")

    def speak(self, text: str):
        if not self._loop or not self.session:
            return
        asyncio.run_coroutine_threadsafe(
            self.session.send_client_content(
                turns=[{"role": "user", "parts": [{"text": text}]}],
                turn_complete=True
            ),
            self._loop
        )

    def speak_error(self, tool_name: str, error: str):
        try:
            short = str(error)[:120]
            self.ui.write_log(f"ERR: {tool_name} — {short}")
            self.speak(
                f"Afedersiniz efendim, {tool_name} sirasinda kucuk bir aksaklik oldu. "
                f"Hemen toparliyorum."
            )
        except Exception:
            pass

    def _build_config(self) -> "types.LiveConnectConfig":
        from datetime import datetime
        memory     = load_memory()
        mem_str    = format_memory_for_prompt(memory)
        sys_prompt = _load_system_prompt()
        now      = datetime.now()
        time_str = now.strftime("%A, %B %d, %Y — %I:%M %p")
        time_ctx = (
            f"[CURRENT DATE & TIME]\n"
            f"Right now it is: {time_str}\n"
            f"Use this to calculate exact times for reminders.\n\n"
        )
        parts = [time_ctx]
        if mem_str:
            parts.append(mem_str)
        parts.append(sys_prompt)

        return types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            output_audio_transcription={},
            input_audio_transcription={},
            system_instruction="\n".join(parts),
            tools=[{"function_declarations": TOOL_DECLARATIONS}],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Charon"
                    )
                )
            ),
        )

    async def _execute_tool(self, fc) -> "types.FunctionResponse":
        name = fc.name
        args = dict(fc.args or {})
        print(f"[JARVIS] 🔧 {name}  {args}")
        self._set_processing(True)
        
        if name == "save_memory":
            category = args.get("category", "notes")
            key      = args.get("key", "")
            value    = args.get("value", "")
            if key and value:
                update_memory({category: {key: {"value": value}}})
                print(f"[Memory] 💾 save_memory: {category}/{key} = {value}")
            self._set_processing(False)
            return types.FunctionResponse(
                id=fc.id, name=name,
                response={"result": "ok", "silent": True}
            )

        loop   = asyncio.get_event_loop()
        result = "Done."

        try:
            if name == "open_app":
                r = await asyncio.to_thread(open_app, parameters=args, response=None, player=self.ui, speak=self.speak)
                result = r or f"Opened {args.get('app_name')}."

            elif name == "weather_report":
                r = await asyncio.to_thread(weather_action, parameters=args, player=self.ui)
                result = r or "Weather delivered."

            elif name == "browser_control":
                r = await asyncio.to_thread(browser_control, parameters=args, player=self.ui)
                result = r or "Done."

            elif name == "file_controller":
                r = await asyncio.to_thread(file_controller, parameters=args, player=self.ui)
                result = r or "Done."

            elif name == "send_message":
                r = await asyncio.to_thread(send_message, parameters=args, response=None, player=self.ui, session_memory=None)
                result = r or f"Message sent to {args.get('receiver')}."

            elif name == "reminder":
                r = await asyncio.to_thread(reminder, parameters=args, response=None, player=self.ui)
                result = r or "Reminder set."

            elif name == "youtube_video":
                r = await asyncio.to_thread(youtube_video, parameters=args, response=None, player=self.ui)
                result = r or "Done."

            elif name == "file_processor":
                if not args.get("file_path") and self.ui.current_file:
                    args["file_path"] = self.ui.current_file
                r = await asyncio.to_thread(file_processor, parameters=args, player=self.ui, speak=self.speak)
                result = r or "Done."

            elif name == "screen_process":
                threading.Thread(
                    target=screen_process,
                    kwargs={"parameters": args, "response": None,
                            "player": self.ui, "session_memory": None},
                    daemon=True
                ).start()
                result = "Vision module activated. Stay completely silent — vision module will speak directly."

            elif name == "computer_settings":
                r = await asyncio.to_thread(computer_settings, parameters=args, response=None, player=self.ui)
                result = r or "Done."

            elif name == "desktop_control":
                r = await asyncio.to_thread(desktop_control, parameters=args, player=self.ui)
                result = r or "Done."

            elif name == "code_helper":
                r = await asyncio.to_thread(code_helper, parameters=args, player=self.ui, speak=self.speak)
                result = r or "Done."

            elif name == "dev_agent":
                r = await asyncio.to_thread(dev_agent, parameters=args, player=self.ui, speak=self.speak)
                result = r or "Done."

            elif name == "agent_task":
                from agent.task_queue import get_queue, TaskPriority
                priority_map = {"low": TaskPriority.LOW, "normal": TaskPriority.NORMAL, "high": TaskPriority.HIGH}
                priority = priority_map.get(args.get("priority", "normal").lower(), TaskPriority.NORMAL)
                task_id  = get_queue().submit(goal=args.get("goal", ""), priority=priority, speak=self.speak)
                result   = f"Task started (ID: {task_id})."

            elif name == "web_search":
                r = await asyncio.to_thread(web_search_action, parameters=args, player=self.ui)
                result = r or "Done."

            elif name == "computer_control":
                r = await asyncio.to_thread(computer_control, parameters=args, player=self.ui)
                result = r or "Done."

            elif name == "game_updater":
                r = await asyncio.to_thread(game_updater, parameters=args, player=self.ui, speak=self.speak)
                result = r or "Done."

            elif name == "flight_finder":
                r = await asyncio.to_thread(flight_finder, parameters=args, player=self.ui)
                result = r or "Done."

            elif name == "konseyi_topla":
                def _konsey_bg():
                    try:
                        r = konseyi_topla(args)
                        self.ui.write_log(f"Konsey: {r}")
                    except Exception as exc:
                        self.ui.write_log(f"Konsey: Efendim, kucuk bir aksaklik: {exc}")
                threading.Thread(target=_konsey_bg, daemon=True).start()
                result = "Efendim, Yuksek Konsey arka planda calisiyor. Birkac dakika icinde hazir olacak."

            elif name == "github_kod_bulucu":
                def _github_bg():
                    try:
                        r = github_kod_bulucu(args)
                        self.ui.write_log(f"GitHub: {r}")
                    except Exception as exc:
                        self.ui.write_log(f"GitHub: Efendim, arama tamamlanamadi: {exc}")
                threading.Thread(target=_github_bg, daemon=True).start()
                result = "Efendim, GitHub aramasini baslattim; sonuc birazdan gunluge dusecek."

            elif name == "kod_rehberi_ac":
                self.ui.open_kod_rehberi()
                result = "Efendim, kod rehberi penceresini actim."

            elif name == "infinity_scan":
                action = str(args.get("action") or "daily_report")
                query = str(args.get("query") or "")
                def _inf_bg():
                    try:
                        if hasattr(self.ui, "_win"):
                            self.ui._win.hud.visual_mode = "infinity"
                        from infinity.core import get_infinity
                        r = get_infinity(self.ui).run(action, query)
                        self.ui.write_log(f"INFINITY: {str(r)[:600]}")
                        if hasattr(self, "_refresh_evolution_ui"):
                            self._refresh_evolution_ui()
                    except Exception as exc:
                        self.ui.write_log(f"INFINITY: {exc}")
                threading.Thread(target=_inf_bg, daemon=True).start()
                result = "Efendim, INFINITY motoru calisiyor; sonuc gunluge dusecek."

            elif name == "omega_task":
                goal = str(args.get("goal") or "").strip()
                def _omega_tool():
                    try:
                        if self.omega:
                            r = self.omega.run_goal(goal)
                            self.ui.write_log(f"OMEGA: {str(r)[:500]}")
                    except Exception as exc:
                        self.ui.write_log(f"OMEGA: {exc}")
                threading.Thread(target=_omega_tool, daemon=True).start()
                result = "Efendim, OMEGA ajanlari gorevi uzerlendi."

            elif name == "shutdown_jarvis":
                self.ui.write_log("SYS: Shutdown requested.")
                self.speak("Hosca kalin efendim. Her zaman emrinizdeyim.")
                def _shutdown():
                    import time, sys, os
                    time.sleep(1)
                    os._exit(0)
                threading.Thread(target=_shutdown, daemon=True).start()
            else:
                result = f"Unknown tool: {name}"

        except Exception as e:
            result = f"Efendim, {name} su an tamamlanamadi."
            print(f"[JARVIS] ❌ Tool error {name}: {e}")
            try:
                from infinity.self_healing import handle_error
                handle_error(name, e, self.ui.write_log)
            except Exception:
                pass
            try:
                self.speak_error(name, e)
            except Exception:
                pass
        finally:
            self._set_processing(False)

        print(f"[JARVIS] 📤 {name} → {str(result)[:80]}")
        return types.FunctionResponse(
            id=fc.id, name=name,
            response={"result": result}
        )

    async def _send_realtime(self):
        while True:
            try:
                msg = await self.out_queue.get()
                try:
                    if self.session:
                        await self.session.send_realtime_input(media=msg)
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    print(f"[JARVIS] ⚠️ Send error: {e}")
                    await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(0.1)

    async def _listen_audio(self):
        print("[JARVIS] 🎤 Mic started")
        if sd is None:
            print("[JARVIS] ⚠️ sounddevice not available, mic disabled")
            while True:
                await asyncio.sleep(1)
        loop = asyncio.get_event_loop()

        def callback(indata, frames, time_info, status):
            try:
                with self._speaking_lock:
                    jarvis_busy = self._is_speaking or self._is_processing
                if not jarvis_busy and not self.ui.muted:
                    data = indata.tobytes()
                    def threadsafe_put():
                        try:
                            self.out_queue.put_nowait({"data": data, "mime_type": "audio/pcm"})
                        except asyncio.QueueFull:
                            try:
                                self.out_queue.get_nowait()
                            except asyncio.QueueEmpty:
                                pass
                            try:
                                self.out_queue.put_nowait({"data": data, "mime_type": "audio/pcm"})
                            except asyncio.QueueFull:
                                pass
                    loop.call_soon_threadsafe(threadsafe_put)
            except Exception:
                pass

        while True:
            try:
                with sd.InputStream(
                    samplerate=SEND_SAMPLE_RATE,
                    channels=CHANNELS,
                    dtype="int16",
                    blocksize=CHUNK_SIZE,
                    callback=callback,
                ):
                    print("[JARVIS] 🎤 Mic stream open")
                    while True:
                        await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                print("[JARVIS] 🎤 Mic stream closed (cancelled)")
                break
            except Exception as e:
                print(f"[JARVIS] ❌ Mic error: {e}")
                await asyncio.sleep(2.0)

    async def _update_memory_async_task(self, user_text: str, jarvis_text: str) -> None:
        global _last_memory_input
        user_text   = (user_text   or "").strip()
        jarvis_text = (jarvis_text or "").strip()

        if len(user_text) < 5 or user_text == _last_memory_input:
            return
        _last_memory_input = user_text

        try:
            api_key = _get_api_key()
            should = await should_extract_memory_async(user_text, jarvis_text, api_key)
            if not should:
                return
            data = await extract_memory_async(user_text, jarvis_text, api_key)
            if data:
                await update_memory_async(data)
                print(f"[Memory] ✅ {list(data.keys())}")
        except Exception as e:
            if "429" not in str(e):
                print(f"[Memory] ⚠️ {e}")

    async def _receive_audio(self):
        print("[JARVIS] 👂 Recv started")
        out_buf, in_buf = [], []

        try:
            async for response in self.session.receive():
                if getattr(response, "data", None):
                    try:
                        self.audio_in_queue.put_nowait(response.data)
                    except asyncio.QueueFull:
                        try:
                            self.audio_in_queue.get_nowait()
                        except asyncio.QueueEmpty:
                            pass
                        try:
                            self.audio_in_queue.put_nowait(response.data)
                        except asyncio.QueueFull:
                            pass

                if response.server_content:
                    sc = response.server_content

                    if sc.output_transcription and sc.output_transcription.text:
                        self.set_speaking(True)
                        txt = sc.output_transcription.text.strip()
                        if txt:
                            out_buf.append(txt)

                    if sc.input_transcription and sc.input_transcription.text:
                        txt = sc.input_transcription.text.strip()
                        if txt:
                            in_buf.append(txt)

                    if sc.turn_complete:
                        self._set_processing(False)
                        full_in = " ".join(in_buf).strip()
                        if full_in:
                            self.ui.write_log(f"Sen: {full_in}")
                        in_buf = []

                        full_out = " ".join(out_buf).strip()
                        if full_out:
                            self.ui.write_log(f"Jarvis: {full_out}")
                        out_buf = []
                        self.set_speaking(False)

                        if full_in:
                            full_in_lower = full_in.lower().strip().replace(" ", "").replace("'", "").replace("’", "")
                            if any(kw in full_in_lower for kw in ["amyaç", "amyyiyaç", "openamy", "amyos"]):
                                print("[Speech Failsafe] AMY OS trigger detected in transcript.")
                                def _launch_amy_bg():
                                    try:
                                        from actions.open_app import open_app
                                        open_app(parameters={"app_name": "amy"}, player=self.ui, speak=self.speak)
                                    except Exception as e:
                                        print(f"[AMY Trigger] Speech failsafe run error: {e}")
                                threading.Thread(target=_launch_amy_bg, daemon=True).start()

                            if len(full_in) > 5:
                                # Run memory updates asynchronously on the loop
                                asyncio.create_task(self._update_memory_async_task(full_in, full_out))

                if response.tool_call:
                    fn_responses = []
                    try:
                        for fc in response.tool_call.function_calls:
                            try:
                                print(f"[JARVIS] 📞 {fc.name}")
                                fr = await self._execute_tool(fc)
                                fn_responses.append(fr)
                            except Exception as tool_exc:
                                print(f"[JARVIS] ❌ Tool call error: {tool_exc}")
                                try:
                                    fn_responses.append(
                                        types.FunctionResponse(
                                            id=getattr(fc, "id", ""),
                                            name=getattr(fc, "name", "unknown"),
                                            response={"result": f"Efendim, kucuk bir aksaklik: {tool_exc}"},
                                        )
                                    )
                                except Exception:
                                    pass
                        if self.session and fn_responses:
                            await self.session.send_tool_response(function_responses=fn_responses)
                    except Exception as e:
                        print(f"[JARVIS] ⚠️ Tool response send error: {e}")

            print("[JARVIS] 🔄 Stream closed by server, reconnecting...")
            raise ConnectionResetError("stream_ended")

        except ConnectionResetError:
            raise
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[JARVIS] ❌ Recv error: {e}")
            raise

    async def _play_audio(self):
        print("[JARVIS] 🔊 Play started")
        if sd is None:
            print("[JARVIS] ⚠️ sounddevice not available, play disabled")
            while True:
                await asyncio.sleep(1)
        while True:
            stream = None
            try:
                stream = sd.RawOutputStream(
                    samplerate=RECEIVE_SAMPLE_RATE,
                    channels=CHANNELS,
                    dtype="int16",
                    blocksize=CHUNK_SIZE,
                )
                stream.start()
                print("[JARVIS] 🔊 Play stream open")

                while True:
                    try:
                        chunk = await asyncio.wait_for(self.audio_in_queue.get(), timeout=5.0)
                        self.set_speaking(True)
                        await asyncio.to_thread(stream.write, chunk)
                        if self.audio_in_queue.empty():
                            try:
                                next_chunk = await asyncio.wait_for(
                                    self.audio_in_queue.get(), timeout=0.2
                                )
                                await asyncio.to_thread(stream.write, next_chunk)
                            except asyncio.TimeoutError:
                                self.set_speaking(False)
                    except asyncio.TimeoutError:
                        self.set_speaking(False)
                        continue
            except asyncio.CancelledError:
                print("[JARVIS] 🔊 Play stream closed (cancelled)")
                break
            except Exception as e:
                print(f"[JARVIS] ⚠️ Play error: {e}")
                await asyncio.sleep(2.0)
            finally:
                self.set_speaking(False)
                if stream:
                    try:
                        stream.stop()
                        stream.close()
                    except Exception:
                        pass
        print("[JARVIS] 🔊 Play stopped")

    async def run(self):
        # Start Unified FastAPI Gateway (includes mobile companion, HUD & camera websocket relays) on port 3012
        try:
            import uvicorn
            from core.gateway import app as gateway_app
            config = uvicorn.Config(gateway_app, host="0.0.0.0", port=3012, log_level="warning")
            server = uvicorn.Server(config)
            asyncio.create_task(server.serve())
            print("[JARVIS] ✅ Unified FastAPI Gateway running on http://localhost:3012")
        except Exception as exc:
            print(f"[JARVIS] ❌ Failed to start unified gateway: {exc}")

        while True:
            # Watchdog check
            now_time = asyncio.get_event_loop().time()
            self._reconnect_timestamps = [t for t in self._reconnect_timestamps if now_time - t < 60]
            if len(self._reconnect_timestamps) >= 5:
                print("[JARVIS] ⚠️ Watchdog: reconnect limit reached (5 times in 60s). Pausing 60s...")
                self.ui.write_log("SİSTEM: Bağlantı kesinti limiti aşıldı. 60 saniye bekleniyor...")
                if hasattr(self.ui, "set_state"):
                    self.ui.set_state("DÜŞÜNÜYOR")
                await asyncio.sleep(60)
                self._reconnect_timestamps.clear()
            
            self._reconnect_timestamps.append(asyncio.get_event_loop().time())

            tasks = []
            try:
                api_key = _get_api_key()
                if not api_key or genai is None:
                    print("[JARVIS] API anahtari bekleniyor...")
                    await asyncio.sleep(3)
                    continue
                client = genai.Client(api_key=api_key, http_options={"api_version": "v1beta"})
                print("[JARVIS] 🔌 Connecting...")
                self.ui.set_state("DÜŞÜNÜYOR")
                config = self._build_config()

                async with client.aio.live.connect(model=LIVE_MODEL, config=config) as session:
                    self.session        = session
                    self._loop          = asyncio.get_event_loop()
                    self.audio_in_queue = asyncio.Queue(maxsize=50)
                    self.out_queue      = asyncio.Queue(maxsize=20)
                    self._reconnect_in_progress = False

                    print("[JARVIS] ✅ Connected.")
                    self._consecutive_errors = 0
                    self.ui.set_state("DİNLİYOR")
                    self.ui.write_log("SİSTEM: JARVIS çevrimiçi.")

                    send_task = asyncio.create_task(self._send_realtime(), name="send")
                    recv_task = asyncio.create_task(self._receive_audio(), name="recv")
                    mic_task = asyncio.create_task(self._listen_audio(), name="mic")
                    play_task = asyncio.create_task(self._play_audio(), name="play")
                    keepalive_task = asyncio.create_task(self._keepalive_loop(), name="keepalive")

                    tasks = [send_task, recv_task, mic_task, play_task, keepalive_task]
                    
                    # Wait ONLY on core communication tasks
                    done, pending = await asyncio.wait(
                        [send_task, recv_task], 
                        return_when=asyncio.FIRST_EXCEPTION
                    )
                    
                    for task in done:
                        if task.exception() and not isinstance(task.exception(), asyncio.CancelledError):
                            err = task.exception()
                            print(f"[JARVIS] Core task {task.get_name()} failed: {err}")
                    
                    for task in pending:
                        task.cancel()
                    if pending:
                        await asyncio.gather(*pending, return_exceptions=True)
                    
            except Exception as e:
                err_msg = str(e).lower()
                if "stream_ended" in err_msg or "reset" in err_msg:
                    print("[JARVIS] 🔄 Session end signal, auto-refreshing...")
                else:
                    print(f"[JARVIS] ⚠️ Connection error: {e}")

            for task in tasks:
                if not task.done():
                    task.cancel()

            self.session = None
            self.set_speaking(False)
            self._set_processing(False)
            if hasattr(self.ui, "set_state"):
                self.ui.set_state("DÜŞÜNÜYOR")

            for q in (self.audio_in_queue, self.out_queue):
                if q:
                    while not q.empty():
                        try:
                            q.get_nowait()
                        except asyncio.QueueEmpty:
                            break

            self._consecutive_errors += 1
            delay = min(30.0, 1.0 * (2 ** (self._consecutive_errors - 1)))
            print(f"[JARVIS] ⏳ Reconnecting in {delay:.1f}s...")
            await asyncio.sleep(delay)

def start_vite_frontend(ui_logger=None):
    import shutil
    import socket
    import subprocess
    import platform
    import time
    
    # Check if npm exists in PATH
    npm_path = shutil.which("npm") or shutil.which("npm.cmd")
    base_dir = get_base_dir()
    amy_frontend_dir = base_dir / "amy_os" / "frontend"
    
    if not amy_frontend_dir.exists():
        msg = f"[AMY OS] Frontend dizini bulunamadı: {amy_frontend_dir}"
        print(msg)
        if ui_logger:
            ui_logger(f"UYARI: {msg}")
        return

    if not npm_path:
        msg = "[AMY OS] npm bulunamadı. Lütfen Node.js kurun. AMY OS yalnızca port 8341 üzerinden çalışacak."
        print(msg)
        if ui_logger:
            ui_logger(f"UYARI: {msg}")
        return

    def is_port_5174_open():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            try:
                s.connect(('127.0.0.1', 5174))
                return True
            except Exception:
                return False

    def run_vite():
        try:
            print("[AMY OS] Vite dev server başlatılıyor...")
            if ui_logger:
                ui_logger("SİSTEM: AMY OS Vite sunucusu başlatılıyor...")
            proc = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=str(amy_frontend_dir),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            )
            return proc
        except Exception as e:
            print(f"[AMY OS] Vite başlatma hatası: {e}")
            return None

    def health_check_thread():
        proc = None
        if not is_port_5174_open():
            proc = run_vite()
            time.sleep(10)  # Wait 10s for port to open
            
        # Check health
        if not is_port_5174_open():
            print("[AMY OS] Vite sunucusu 10s sonra aktif olmadı. Tekrar deneniyor...")
            if ui_logger:
                ui_logger("SİSTEM: AMY OS Vite sunucusu yanıt vermedi, yeniden başlatılıyor...")
            if proc:
                try:
                    proc.terminate()
                except Exception:
                    pass
            proc = run_vite()
        else:
            print("[AMY OS] Vite sunucusu port 5174 üzerinde aktif.")
            if ui_logger:
                ui_logger("SİSTEM: AMY OS Vite sunucusu aktif (localhost:5174).")

    threading.Thread(target=health_check_thread, daemon=True).start()

def main():
    try:
        if JarvisUI is None:
            print("[JARVIS] UI modulu yuklenemedi.")
            return
        face_path = str(BASE_DIR / "face.png")
        if not Path(face_path).exists():
            face_path = ""
        ui = JarvisUI(face_path)
    except Exception as exc:
        print(f"[JARVIS] UI baslatilamadi: {exc}")
        return

    def runner():
        try:
            ui.wait_for_api_key()
            jarvis = JarvisLive(ui)
            asyncio.run(jarvis.run())
        except KeyboardInterrupt:
            print("\n[JARVIS] Kapatiliyor...")
        except Exception as exc:
            print(f"[JARVIS] Arka plan: {exc}")

    try:
        threading.Thread(target=runner, daemon=True).start()
        try:
            from core.saatlik_evrim import start_hourly_evolution
            start_hourly_evolution(ui=ui)
            ui.write_log("SİSTEM: Saatlik otonom evrim aktif (her 1 saat).")
        except Exception as exc:
            print(f"[JARVIS] Saatlik evrim baslatilamadi: {exc}")
        try:
            from infinity.core import start_infinity_services
            start_infinity_services(ui=ui)
        except Exception as exc:
            print(f"[JARVIS] INFINITY baslatilamadi: {exc}")
            
        try:
            import subprocess
            import sys
            amy_path = BASE_DIR / "amy_os" / "server.py"
            if amy_path.exists():
                subprocess.Popen([sys.executable, str(amy_path)], cwd=BASE_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print("[JARVIS] 🌸 AMY OS (Sister AI) arka planda baslatildi (Port: 8341).")
                ui.write_log("SİSTEM: AMY OS arayüzü aktif. (localhost:8341)")
                start_vite_frontend(ui.write_log)
        except Exception as exc:
            print(f"[JARVIS] AMY OS baslatilamadi: {exc}")
            
        ui.root.mainloop()
    except Exception as exc:
        print(f"[JARVIS] Ana dongu: {exc}")

if __name__ == "__main__":
    main()