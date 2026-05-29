import os
import sys
import time
import uuid
import re
import base64
import asyncio
import httpx
from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, File, UploadFile, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager, suppress
from threading import Lock

# Add project directory to sys.path
PROJE_DIZINI = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJE_DIZINI not in sys.path:
    sys.path.insert(0, PROJE_DIZINI)

from core.event_bus import get_event_bus
from core.ws_manager import get_ws_manager
from core.arac_rehberi import collect_capabilities

# Ensure upload directory exists
UPLOAD_FOLDER = os.path.join(PROJE_DIZINI, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# State lock for thread safety
state_lock = Lock()

# Global Unified State Store
STATE = {
    "telemetry": {
        "battery_percentage": -1.0,
        "battery_status": "UNKNOWN",
        "wifi_status": "DISCONNECTED",
        "wifi_ssid": "Unknown Network",
        "volume": 0,
        "cpu_usage": 0.0,
        "ram_usage": "0/0 MB",
        "cpu": 0.0,
        "ram": 0.0,
        "temp": 45.0,
        "charging": False,
        "audio_level": 0.0,
        "last_seen": 0.0,
        "last_update": 0.0,
        "screenshot_url": None,
        "photo_url": None,
        "audio_recordings": [],
        "clipboard": "",
        "command_logs": []
    },
    "last_mood": {
        "mood_code": "neutral",
        "intensity": 0.25,
        "ts": time.time()
    }
}

tablet_command_queue: List[dict] = []
camera_viewers: set[WebSocket] = set()

# ElevenLabs config loading
try:
    from core.config_loader import get_service_key, load_config
    ELEVENLABS_API_KEY = get_service_key("elevenlabs") or os.environ.get("ELEVENLABS_API_KEY", "")
except Exception:
    ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
    def load_config() -> dict: return {}

ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
ELEVENLABS_BASE = "https://api.elevenlabs.io/v1"
ELEVENLABS_MODEL = "eleven_multilingual_v2"

_MOOD_PATTERNS = [
    (re.compile(r"(heyecan|süper|harika|mükemmel|vay|wow|bayıl)", re.I), "excited"),
    (re.compile(r"(sinir|kız|öfke|saçma|berbat|problem|hata|bug|acil)", re.I), "serious"),
    (re.compile(r"(gizli|sır|merak|ilginç|tuhaf|garip)", re.I), "mysterious"),
    (re.compile(r"(teşekkür|sağol|güzel|sevdim|mutlu|iyi|memnun)", re.I), "warm"),
    (re.compile(r"(hadi ya|ciddi mi|dalga|şaka|komik)", re.I), "sarcastic"),
    (re.compile(r"(odaklan|konsantre|çalış|kod yaz|analiz|hesapla)", re.I), "focused"),
]

_MOOD_VOICE = {
    "neutral":    {"stability": 0.50, "similarity_boost": 0.75, "style": 0.30},
    "excited":    {"stability": 0.30, "similarity_boost": 0.70, "style": 0.85},
    "serious":    {"stability": 0.75, "similarity_boost": 0.80, "style": 0.15},
    "mysterious": {"stability": 0.40, "similarity_boost": 0.65, "style": 0.70},
    "warm":       {"stability": 0.55, "similarity_boost": 0.80, "style": 0.50},
    "sarcastic":  {"stability": 0.35, "similarity_boost": 0.70, "style": 0.80},
    "focused":    {"stability": 0.65, "similarity_boost": 0.75, "style": 0.20},
}

def queue_tablet_command(action: str, value: str = "") -> str:
    cmd_id = str(uuid.uuid4())[:8]
    cmd = {
        "command_id": cmd_id,
        "action": action,
        "value": value,
        "timestamp": time.time()
    }
    with state_lock:
        tablet_command_queue.append(cmd)
    
    bus = get_event_bus()
    bus.publish_sync("tablet.command_queued", "gateway", cmd)
    return cmd_id

def handle_natural_language_tablet_commands(komut: str) -> Optional[str]:
    cmd = komut.lower()
    if "feneri aç" in cmd or "flaşı aç" in cmd or "ışığı aç" in cmd:
        queue_tablet_command("torch_on", "")
        return "Tablet fenerini açtım efendim. 🔦"
    if "feneri kapat" in cmd or "flaşı kapat" in cmd or "ışığı kapat" in cmd:
        queue_tablet_command("torch_off", "")
        return "Tablet fenerini kapattım efendim. 🔦"
    if "titret" in cmd or "titreşim gönder" in cmd:
        queue_tablet_command("vibrate", "600")
        return "Tablete titreşim sinyali gönderildi efendim. 📳"
    if "sesini" in cmd or "ses seviyesini" in cmd:
        match = re.search(r"(\d+)", cmd)
        if match:
            vol = int(match.group(1))
            vol = max(0, min(100, vol))
            queue_tablet_command("volume", str(vol))
            return f"Tablet sesini yüzde {vol} yapıyorum efendim. 🔊"
    if "fotoğraf çek" in cmd or "resim çek" in cmd or "kamera resmi" in cmd:
        queue_tablet_command("photo", "0")
        return "Anlaşıldı, tablet kamerasıyla fotoğraf çekiyorum. 📸"
    if "ekran görüntüsü al" in cmd or "screenshot al" in cmd or "ekran resmi çek" in cmd:
        queue_tablet_command("screenshot", "")
        return "Tablet ekran görüntüsünü alıyorum efendim. 🖥️"
    if "ortamı dinle" in cmd or "ses kaydet" in cmd:
        match = re.search(r"(\d+)\s*saniye", cmd)
        if match:
            sec = match.group(1)
        else:
            sec = "5"
        queue_tablet_command("mic_record", sec)
        return f"Tablet ortam sesini {sec} saniye kaydediyor efendim. 🎙️"
    if "panoyu oku" in cmd or "clipboard oku" in cmd:
        queue_tablet_command("clipboard_get", "")
        return "Tablet panosundaki güncel metin çekiliyor. 📋"
    if "panoya yaz" in cmd:
        val = komut.split("panoya yaz")[-1].strip()
        if val:
            queue_tablet_command("clipboard_set", val)
            return f"Tablet panosuna yazıldı: '{val}'"
    return None

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

async def elevenlabs_seslendir_async(metin: str, mood: str = "neutral") -> Optional[str]:
    if not ELEVENLABS_API_KEY:
        return None
    params = _MOOD_VOICE.get(mood, _MOOD_VOICE["neutral"])
    url = f"{ELEVENLABS_BASE}/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": metin,
        "model_id": ELEVENLABS_MODEL,
        "voice_settings": {
            "stability": params["stability"],
            "similarity_boost": params["similarity_boost"],
            "style": params["style"],
            "use_speaker_boost": True,
        },
    }
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                return base64.b64encode(resp.content).decode("utf-8")
            return None
    except Exception as exc:
        print(f"[ElevenLabs] Async ses sentezi hatası: {exc}")
        return None

def build_system_ghost_node() -> Dict[str, Any]:
    with state_lock:
        telemetry = dict(STATE["telemetry"])
    battery = telemetry.get("battery_percentage", 100)
    cpu = telemetry.get("cpu", 0.0)
    ram = telemetry.get("ram", 0.0)
    temp = telemetry.get("temp", 45.0)

    candidates = []
    if isinstance(battery, (int, float)) and battery > 0 and battery < 20:
        candidates.append({
            "kind": "warning",
            "title": "Power Drift Detected",
            "body": f"Termux battery is at {battery:.0f}%. Shall I dim the screen and lower the frame load?",
            "priority": 1.0,
        })
    if isinstance(cpu, (int, float)) and cpu > 85:
        candidates.append({
            "kind": "warning",
            "title": "CPU Pressure Rising",
            "body": f"System CPU is at {cpu:.0f}%. I can reduce particle density and background effects.",
            "priority": 0.95,
        })
    if isinstance(ram, (int, float)) and ram > 85:
        candidates.append({
            "kind": "warning",
            "title": "Memory Saturation",
            "body": f"System RAM is at {ram:.0f}%. I can collapse inactive UI clusters now.",
            "priority": 0.95,
        })
    if isinstance(temp, (int, float)) and temp > 42:
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
        "ttl_ms": 12000,
        "priority": chosen["priority"],
        "ts": time.time(),
        "telemetry_snapshot": telemetry,
    }

async def proactive_ghost_loop() -> None:
    import random
    while True:
        await asyncio.sleep(random.randint(120, 300))
        ws_manager = get_ws_manager()
        if len(ws_manager.active_connections) > 0:
            payload = build_system_ghost_node()
            await ws_manager.broadcast(payload)

async def on_optimization_found(event):
    """Callback triggered when AST code scanner finds an optimization."""
    payload = dict(event.payload)
    payload["type"] = "system.optimization.found"
    ws_manager = get_ws_manager()
    await ws_manager.broadcast(payload, role="hud")
    print(f"[Gateway] Broadcasted system.optimization.found to HUD clients: {payload['filename']}")

async def on_camera_activated(event):
    payload = {
        "type": "vision.camera.activated",
        "status": event.payload.get("status", "active"),
        "timestamp": event.payload.get("timestamp", time.time())
    }
    ws_manager = get_ws_manager()
    await ws_manager.broadcast(payload, role="hud")
    print(f"[Gateway] Broadcasted vision.camera.activated to HUD clients.")

async def on_camera_deactivated(event):
    payload = {
        "type": "vision.camera.deactivated",
        "status": "inactive",
        "timestamp": event.payload.get("timestamp", time.time())
    }
    ws_manager = get_ws_manager()
    await ws_manager.broadcast(payload, role="hud")
    print(f"[Gateway] Broadcasted vision.camera.deactivated to HUD clients.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    bus = get_event_bus()
    bus.start()
    bus.subscribe("system.optimization.found", on_optimization_found)
    bus.subscribe("vision.camera.activated", on_camera_activated)
    bus.subscribe("vision.camera.deactivated", on_camera_deactivated)
    
    ws = get_ws_manager()
    await ws.start_heartbeat_loop()
    
    ghost_task = asyncio.create_task(proactive_ghost_loop())
    
    yield
    # Shutdown actions
    ghost_task.cancel()
    with suppress(asyncio.CancelledError):
        await ghost_task
    bus.unsubscribe("system.optimization.found", on_optimization_found)
    bus.unsubscribe("vision.camera.activated", on_camera_activated)
    bus.unsubscribe("vision.camera.deactivated", on_camera_deactivated)
    bus.stop()

app = FastAPI(title="J.A.R.V.I.S. 2.0 Core Gateway", lifespan=lifespan)


# Enable CORS for HUD & multi-device compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static folder
app.mount("/static", StaticFiles(directory=os.path.join(PROJE_DIZINI, "static")), name="static")

# REST Endpoints (Backwards compatible with edge nodes)
@app.post("/api/cihaz_durumu")
async def api_cihaz_durumu(data: dict):
    with state_lock:
        STATE["telemetry"]["battery_percentage"] = data.get("battery_percentage", -1.0)
        STATE["telemetry"]["battery_status"] = data.get("battery_status", "UNKNOWN")
        STATE["telemetry"]["charging"] = data.get("charging", False)
        STATE["telemetry"]["wifi_status"] = data.get("wifi_status", "DISCONNECTED")
        STATE["telemetry"]["wifi_ssid"] = data.get("wifi_ssid", "Unknown Network")
        STATE["telemetry"]["volume"] = data.get("volume", 0)
        STATE["telemetry"]["cpu_usage"] = data.get("cpu_usage", 0.0)
        STATE["telemetry"]["ram_usage"] = data.get("ram_usage", "0/0 MB")
        STATE["telemetry"]["cpu"] = data.get("cpu_usage", 0.0)
        STATE["telemetry"]["ram"] = float(data.get("ram_usage", "0").split("/")[0].replace("MB", "").strip() or 0)
        STATE["telemetry"]["clipboard"] = data.get("clipboard", STATE["telemetry"]["clipboard"])
        STATE["telemetry"]["last_seen"] = time.time()
        STATE["telemetry"]["last_update"] = time.time()
    
    bus = get_event_bus()
    await bus.publish("device.telemetry_update", "gateway", dict(STATE["telemetry"]))
    
    # Broadcast updated telemetry to HUD
    ws_manager = get_ws_manager()
    await ws_manager.broadcast({"type": "telemetry", "telemetry": STATE["telemetry"]})
    return {"durum": "tamam"}

@app.get("/api/komut_al")
async def api_komut_al():
    with state_lock:
        if tablet_command_queue:
            return tablet_command_queue.pop(0)
    return {"action": "none"}

@app.post("/api/komut_sonuc")
async def api_komut_sonuc(data: dict):
    action = data.get("action", "unknown")
    result = data.get("result", "")
    success = data.get("success", True)
    
    log_entry = {
        "command_id": data.get("command_id", "unknown"),
        "action": action,
        "result": result,
        "success": success,
        "timestamp": time.time()
    }
    
    with state_lock:
        if action == "clipboard_get" and success:
            STATE["telemetry"]["clipboard"] = result
        STATE["telemetry"]["command_logs"].append(log_entry)
        if len(STATE["telemetry"]["command_logs"]) > 50:
            STATE["telemetry"]["command_logs"].pop(0)

    bus = get_event_bus()
    await bus.publish("device.command_result", "gateway", log_entry)
    return {"durum": "tamam"}

@app.post("/api/dosya_yukle")
async def api_dosya_yukle(file: UploadFile = File(...), type: str = Form("unknown")):
    ext = os.path.splitext(file.filename)[1]
    filename = f"{type}_{int(time.time())}{ext}"
    dest_path = os.path.join(UPLOAD_FOLDER, filename)
    
    content = await file.read()
    # Write file asynchronously using asyncio.to_thread
    await asyncio.to_thread(lambda: open(dest_path, "wb").write(content))
        
    rel_url = f"/static/uploads/{filename}"
    with state_lock:
        if type == "photo":
            STATE["telemetry"]["photo_url"] = rel_url
        elif type == "screenshot":
            STATE["telemetry"]["screenshot_url"] = rel_url
        elif type == "audio":
            STATE["telemetry"]["audio_recordings"].append(rel_url)
            if len(STATE["telemetry"]["audio_recordings"]) > 10:
                STATE["telemetry"]["audio_recordings"].pop(0)

    bus = get_event_bus()
    await bus.publish("device.file_uploaded", "gateway", {"type": type, "url": rel_url})
    return {"durum": "basarili", "url": rel_url}

@app.post("/api/cihaz_tetikle")
async def api_cihaz_tetikle(data: dict):
    action = data.get("action", "")
    value = data.get("value", "")
    if not action:
        return JSONResponse(status_code=400, content={"hata": "Boş aksiyon"})
    cmd_id = queue_tablet_command(action, value)
    return {"status": "queued", "command_id": cmd_id}

@app.post("/api/open_proposals")
async def api_open_proposals(data: dict):
    path_val = data.get("path")
    if not path_val:
        path_val = os.path.abspath(os.path.join(PROJE_DIZINI, "proposals"))
    
    # Ensure directory exists asynchronously (non-blocking)
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


@app.get("/api/cihaz_bilgisi")
async def api_cihaz_bilgisi():
    with state_lock:
        last_seen = STATE["telemetry"]["last_seen"]
        online = (time.time() - last_seen) < 12.0 if last_seen > 0 else False
        state_copy = dict(STATE["telemetry"])
        state_copy["online"] = online
    return state_copy

# Single Unified AI response processor
async def process_chat(command: str, client_ip: str) -> dict:
    try:
        from core.main_router import get_router
        router = get_router()
        router_response = await router.process(command)
        return {
            "reply": router_response.final_reply,
            "worker": router_response.worker_result.worker,
            "success": router_response.worker_result.success,
            "mood": router_response.intent.category.value
        }
    except Exception as exc:
        print(f"[Gateway Chat] AI Router error: {exc}")
        return {
            "reply": f"Efendim, sistemlerimde küçük bir aksaklık var: {exc}",
            "worker": "system_error",
            "success": False,
            "mood": "neutral"
        }

@app.post("/api/chat")
async def chat(request: Request, data: dict):
    command = str(data.get("command", "")).strip()
    if not command:
        return JSONResponse(status_code=400, content={"hata": "Boş komut"})
    client_ip = request.client.host if request.client else "Unknown_IP"
    return await process_chat(command, client_ip)

@app.post("/api/komut")
async def api_komut(data: dict):
    komut = str(data.get("komut", "")).strip()
    if not komut:
        return JSONResponse(status_code=400, content={"hata": "Boş komut"})
        
    jarvis_cevabi = handle_natural_language_tablet_commands(komut)
    mood = "neutral"
    
    if jarvis_cevabi is None:
        res = await process_chat(komut, "127.0.0.1")
        jarvis_cevabi = res["reply"]
        mood = res["mood"]

    ses_base64 = await elevenlabs_seslendir_async(jarvis_cevabi, mood=mood)
    return {
        "cevap": jarvis_cevabi,
        "ses_base64": ses_base64,
        "mood": mood
    }

@app.get("/api/system-stats")
async def api_system_stats():
    try:
        import psutil
        cpu = await asyncio.to_thread(psutil.cpu_percent)
        ram = (await asyncio.to_thread(psutil.virtual_memory)).percent
        disk = (await asyncio.to_thread(psutil.disk_usage, '/')).percent
    except ImportError:
        cpu, ram, disk = 23.4, 45.2, 57.1
    
    with state_lock:
        STATE["telemetry"]["cpu"] = cpu
        STATE["telemetry"]["ram"] = ram
        last_seen = STATE["telemetry"]["last_seen"]
        tablet_online = (time.time() - last_seen) < 15.0 if last_seen > 0 else False
        
    return {
        "cpu": cpu,
        "ram": ram,
        "disk": disk,
        "temperature": STATE["telemetry"].get("temp", 45.0),
        "tablet_status": "ÇEVRİMİÇİ" if tablet_online else "ÇEVRİMDIŞI"
    }

# --- SORUN BİLDİRİMİ SİSTEMİ ---
ISSUE_REPORTS_FILE = os.path.join(PROJE_DIZINI, "logs", "issue_reports.json")
WHATSAPP_PHONE = "905518439801"

def _load_issue_reports() -> list:
    try:
        with open(ISSUE_REPORTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def _save_issue_reports(reports: list) -> None:
    os.makedirs(os.path.dirname(ISSUE_REPORTS_FILE), exist_ok=True)
    with open(ISSUE_REPORTS_FILE, "w", encoding="utf-8") as f:
        json.dump(reports, f, indent=2, ensure_ascii=False)

@app.post("/api/issue-report")
async def api_issue_report(request: Request, data: dict):
    """Kullanıcı sorun bildirimi alır, kaydeder ve WhatsApp mesajı oluşturur."""
    import json as _json
    
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
    
    # Kaydet
    reports = await asyncio.to_thread(_load_issue_reports)
    reports.append(report)
    await asyncio.to_thread(_save_issue_reports, reports)
    
    # WhatsApp mesaj metnini hazırla
    wa_message = (
        f"🤖 *J.A.R.V.I.S. Sorun Bildirimi*\n\n"
        f"👤 Kullanıcı: {user_name}\n"
        f"📧 E-posta: {user_email or 'Belirtilmedi'}\n"
        f"🏷️ Tür: {issue_type}\n"
        f"⚠️ Öncelik: {severity}\n"
        f"📅 Tarih: {report['date']}\n\n"
        f"📝 Açıklama:\n{description}\n\n"
        f"Ne yapabiliriz efendim?"
    )
    
    # WhatsApp URL oluştur (wa.me API)
    import urllib.parse
    wa_url = f"https://wa.me/{WHATSAPP_PHONE}?text={urllib.parse.quote(wa_message)}"
    
    # Event bus üzerinden bildirim yayınla
    bus = get_event_bus()
    await bus.publish("system.issue_report", "gateway", {
        "report": report,
        "wa_url": wa_url
    })
    
    # HUD'a bildirim gönder
    ws_manager = get_ws_manager()
    await ws_manager.broadcast({
        "type": "issue_report_received",
        "report": report,
        "wa_url": wa_url
    })
    
    print(f"[Gateway] 📋 Yeni sorun bildirimi alındı: [{severity}] {user_name} — {description[:50]}...")
    
    return {
        "status": "success",
        "report_id": report["id"],
        "wa_url": wa_url,
        "message": "Sorun bildiriminiz alındı. Teşekkürler!"
    }

@app.get("/api/issue-reports")
async def api_get_issue_reports():
    """Admin: Tüm sorun bildirimlerini listele."""
    reports = await asyncio.to_thread(_load_issue_reports)
    return {"reports": reports, "total": len(reports)}

@app.post("/api/telemetry")
async def ingest_telemetry(data: dict) -> Dict[str, Any]:
    with state_lock:
        STATE["telemetry"].update(data)
        STATE["telemetry"]["last_update"] = time.time()
        
    ws_manager = get_ws_manager()
    await ws_manager.broadcast({
        "type": "telemetry",
        "telemetry": STATE["telemetry"],
    })
    return {"ok": True, "telemetry": STATE["telemetry"]}

# WebSocket Endpoints
@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    ws_manager = get_ws_manager()
    await ws_manager.connect(websocket, "hud")
    try:
        await websocket.send_json({
            "type": "hello",
            "state": STATE,
            "ts": time.time(),
        })

        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "invalid_json"})
                continue

            msg_type = data.get("type")
            if msg_type == "prompt":
                text = str(data.get("text", ""))
                mood = analyze_sentiment(text)
                
                with state_lock:
                    STATE["last_mood"] = mood

                await ws_manager.broadcast({
                    "type": "mood",
                    "mood": mood,
                    "text": text[:240],
                })

                res = await process_chat(text, "127.0.0.1")
                await ws_manager.broadcast({
                    "type": "response",
                    "mood_code": mood["mood_code"],
                    "content": res.get("reply", "Efendim, nöral bağlantımda pürüz çıktı.")
                })

            elif msg_type == "telemetry":
                telemetry = {k: v for k, v in data.items() if k != "type"}
                with state_lock:
                    STATE["telemetry"].update(telemetry)
                    STATE["telemetry"]["last_update"] = time.time()

                await websocket.send_json({
                    "type": "telemetry_ack",
                    "ok": True,
                    "telemetry": STATE["telemetry"],
                })

                await ws_manager.broadcast({
                    "type": "telemetry",
                    "telemetry": STATE["telemetry"],
                })

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong", "ts": time.time()})

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)

@app.websocket("/ws/core")
async def websocket_core(websocket: WebSocket, role: str = "unknown"):
    ws_manager = get_ws_manager()
    await ws_manager.connect(websocket, role)
    try:
        while True:
            data = await websocket.receive_json()
            bus = get_event_bus()
            await bus.publish(f"client.{role}.event", role, data)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        print(f"[WS-Core] Connection error: {e}")
        ws_manager.disconnect(websocket)

@app.websocket("/ws/telemetry")
async def websocket_telemetry_ws(websocket: WebSocket):
    await websocket.accept()
    ws_manager = get_ws_manager()
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                update = json.loads(raw)
                with state_lock:
                    STATE["telemetry"].update(update)
                    STATE["telemetry"]["last_update"] = time.time()
                await ws_manager.broadcast({
                    "type": "telemetry",
                    "telemetry": STATE["telemetry"],
                })
            except:
                pass
    except WebSocketDisconnect:
        pass

@app.websocket("/ws/camera")
async def websocket_camera_relay(websocket: WebSocket):
    await websocket.accept()
    role = "viewer"
    try:
        try:
            raw = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
            init = json.loads(raw)
            role = init.get("role", "viewer")
        except (asyncio.TimeoutError, Exception):
            role = "sender"

        if role == "sender":
            while True:
                frame = await websocket.receive_bytes()  # JPEG bytes
                viewers = list(camera_viewers)
                if viewers:
                    async def _send(v):
                        try:
                            await v.send_bytes(frame)
                        except Exception:
                            pass
                    await asyncio.gather(*[_send(v) for v in viewers], return_exceptions=True)
        else:
            camera_viewers.add(websocket)
            try:
                while True:
                    await websocket.receive_text()
            except WebSocketDisconnect:
                pass
            finally:
                camera_viewers.discard(websocket)
    except Exception:
        pass
    finally:
        camera_viewers.discard(websocket)

KOD_REHBERI_HTML = r"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>J.A.R.V.I.S. — Yetenek Matrisi</title>
    <link href="https://fonts.googleapis.com/css2?family=Courier+Prime:wght@400;700&family=Orbitron:wght@400;700;900&family=Rajdhani:wght@500;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #030712;
            --card-bg: rgba(17, 24, 39, 0.7);
            --border-color: rgba(6, 182, 212, 0.25);
            --border-hover: rgba(6, 182, 212, 0.6);
            --cyan: #06b6d4;
            --purple: #a855f7;
            --green: #10b981;
            --amber: #f59e0b;
            --text-main: #f8fafc;
            --text-dim: #94a3b8;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-color);
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(6, 182, 212, 0.05) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(168, 85, 247, 0.05) 0%, transparent 40%);
            color: var(--text-main);
            font-family: 'Rajdhani', sans-serif;
            min-height: 100vh;
            padding: 2rem;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        header {
            text-align: center;
            margin-bottom: 2.5rem;
            width: 100%;
            max-width: 1200px;
        }

        h1 {
            font-family: 'Orbitron', sans-serif;
            font-size: 2.2rem;
            font-weight: 900;
            color: var(--cyan);
            letter-spacing: 3px;
            text-shadow: 0 0 15px rgba(6, 182, 212, 0.4);
            margin-bottom: 0.5rem;
        }

        .subtitle {
            color: var(--text-dim);
            font-size: 1.1rem;
            letter-spacing: 1px;
            margin-bottom: 1.5rem;
        }

        .search-container {
            width: 100%;
            max-width: 500px;
            margin: 0 auto;
            position: relative;
        }

        .search-input {
            width: 100%;
            padding: 0.75rem 1.5rem;
            font-size: 1rem;
            font-family: 'Courier Prime', monospace;
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: var(--text-main);
            outline: none;
            transition: all 0.3s ease;
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.6);
        }

        .search-input:focus {
            border-color: var(--cyan);
            box-shadow: 0 0 15px rgba(6, 182, 212, 0.3), inset 0 2px 4px rgba(0, 0, 0, 0.6);
        }

        .matrix-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
            gap: 1.5rem;
            width: 100%;
            max-width: 1200px;
            margin-top: 1rem;
        }

        .card {
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }

        .card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: var(--cyan);
            opacity: 0.8;
        }

        .card.eklenti::before {
            background: var(--green);
        }

        .card:hover {
            border-color: var(--border-hover);
            transform: translateY(-4px);
            box-shadow: 0 10px 20px rgba(6, 182, 212, 0.15);
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .card-title {
            font-size: 1.3rem;
            font-weight: 700;
            letter-spacing: 0.5px;
        }

        .card-tag {
            font-family: 'Orbitron', sans-serif;
            font-size: 0.65rem;
            font-weight: 700;
            padding: 2px 6px;
            border-radius: 4px;
            background: var(--cyan);
            color: #030712;
            letter-spacing: 0.5px;
        }

        .card.eklenti .card-tag {
            background: var(--green);
        }

        .card-id {
            font-family: 'Courier Prime', monospace;
            font-size: 0.8rem;
            color: var(--cyan);
        }

        .card.eklenti .card-id {
            color: var(--green);
        }

        .card-desc {
            color: var(--text-dim);
            font-size: 0.95rem;
            line-height: 1.4;
            flex-grow: 1;
        }

        .card-example {
            font-family: 'Courier Prime', monospace;
            font-size: 0.85rem;
            color: var(--amber);
            background: rgba(245, 158, 11, 0.05);
            padding: 6px 10px;
            border-radius: 6px;
            border-left: 2px solid var(--amber);
        }

        .card-action {
            display: flex;
            justify-content: flex-end;
            margin-top: 0.5rem;
        }

        .run-btn {
            background: rgba(16, 185, 129, 0.1);
            color: var(--green);
            border: 1px solid var(--green);
            border-radius: 6px;
            padding: 6px 16px;
            font-family: 'Orbitron', sans-serif;
            font-size: 0.8rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .run-btn:hover {
            background: var(--green);
            color: #030712;
            box-shadow: 0 0 10px rgba(16, 185, 129, 0.4);
        }

        .run-btn:disabled {
            background: rgba(255, 255, 255, 0.02);
            color: var(--text-dim);
            border-color: rgba(255, 255, 255, 0.1);
            cursor: not-allowed;
            box-shadow: none;
        }

        .output-console {
            margin-top: 1rem;
            font-family: 'Courier Prime', monospace;
            font-size: 0.8rem;
            padding: 8px;
            background: rgba(0, 0, 0, 0.4);
            border-radius: 6px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            display: none;
            word-break: break-all;
        }

        .output-console.active {
            display: block;
        }

        .output-console.success {
            color: var(--green);
            border-color: rgba(16, 185, 129, 0.2);
        }

        .output-console.error {
            color: #ef4444;
            border-color: rgba(239, 68, 68, 0.2);
        }

        .footer {
            margin-top: 3rem;
            color: var(--text-dim);
            font-family: 'Courier Prime', monospace;
            font-size: 0.8rem;
            text-align: center;
        }
    </style>
</head>
<body>
    <header>
        <h1>◈ J.A.R.V.I.S. YETENEK MATRİSİ ◈</h1>
        <div class="subtitle">Sesli komut örnekleri ve otonom çekirdek/eklenti yetenek rehberi</div>
        <div class="search-container">
            <input type="text" id="searchInput" class="search-input" placeholder="Yetenek ara... (Örn: spotify, ekran)">
        </div>
    </header>

    <main class="matrix-grid" id="matrixGrid">
        <!-- Cards dynamic generation -->
    </main>

    <footer class="footer">
        J.A.R.V.I.S. 2.0 // OMEGA INFINITY OS // SYSTEM ONLINE
    </footer>

    <script>
        const capabilities = $CAPABILITIES_JSON$;

        const grid = document.getElementById('matrixGrid');
        const searchInput = document.getElementById('searchInput');

        function render(items) {
            grid.innerHTML = '';
            items.forEach(cap => {
                const card = document.createElement('div');
                card.className = `card \${cap.source === 'eklenti' ? 'eklenti' : ''}`;
                
                const isExecutable = cap.id !== 'shutdown_jarvis' && cap.id !== 'save_memory' && cap.example !== '(otomatik)';
                
                card.innerHTML = `
                    <div class="card-header">
                        <span class="card-title">\${cap.title || cap.id}</span>
                        <span class="card-tag">\${cap.source.toUpperCase()}</span>
                    </div>
                    <div class="card-id">Araç Kodu: \${cap.id}</div>
                    <div class="card-desc">\${cap.description}</div>
                    <div class="card-example">🎙️ Örnek: "\${cap.example}"</div>
                    <div class="card-action">
                        <button class="run-btn" \${isExecutable ? '' : 'disabled'} onclick="runCommand('\${cap.example}', this)">
                            \${isExecutable ? '▶ ÇALIŞTIR' : 'KİLİTLİ'}
                        </button>
                    </div>
                    <div class="output-console"></div>
                `;
                grid.appendChild(card);
            });
        }

        async function runCommand(cmdText, btn) {
            const consoleDiv = btn.parentElement.parentElement.querySelector('.output-console');
            consoleDiv.className = 'output-console active';
            consoleDiv.textContent = '> Komut gönderiliyor: "' + cmdText + '"...';
            btn.disabled = true;

            try {
                const res = await fetch('/api/komut', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ komut: cmdText })
                });
                const data = await res.json();
                consoleDiv.className = 'output-console active success';
                consoleDiv.textContent = 'Jarvis: ' + (data.cevap || 'İşlem tamamlandı.');
            } catch (err) {
                consoleDiv.className = 'output-console active error';
                consoleDiv.textContent = 'Hata: Bağlantı kurulamadı. (' + err.message + ')';
            } finally {
                btn.disabled = false;
            }
        }

        searchInput.addEventListener('input', (e) => {
            const val = e.target.value.toLowerCase();
            const filtered = capabilities.filter(c => 
                (c.title && c.title.toLowerCase().includes(val)) ||
                c.id.toLowerCase().includes(val) ||
                c.description.toLowerCase().includes(val) ||
                c.example.toLowerCase().includes(val)
            );
            render(filtered);
        });

        render(capabilities);
    </script>
</body>
</html>
"""

@app.get("/kod_rehberi", response_class=HTMLResponse)
async def serve_kod_rehberi():
    try:
        caps = await asyncio.to_thread(collect_capabilities)
        import json
        caps_json = json.dumps(caps, ensure_ascii=False)
        html_content = KOD_REHBERI_HTML.replace("$CAPABILITIES_JSON$", caps_json)
        return html_content
    except Exception as e:
        return f"<html><body><h1>Kod Rehberi Yuklenemedi</h1><p>{e}</p></body></html>"

@app.get("/", response_class=HTMLResponse)
async def serve_hud():
    # Attempt to read from web/index.html
    html_path = os.path.join(PROJE_DIZINI, "web", "index.html")
    if await asyncio.to_thread(os.path.exists, html_path):
        try:
            def _read():
                with open(html_path, "r", encoding="utf-8") as f:
                    return f.read()
            html_content = await asyncio.to_thread(_read)
            return html_content
        except Exception as e:
            print(f"[Gateway HUD] Error reading web/index.html: {e}")
            
    # Try backup HTML from jarvis_sunucu
    try:
        from jarvis_sunucu import ARAYUZ_HTML
        return ARAYUZ_HTML
    except ImportError:
        return "<html><body><h1>J.A.R.V.I.S. Core Gateway Running</h1></body></html>"

@app.get("/index.html", response_class=HTMLResponse)
async def index():
    return await serve_hud()
